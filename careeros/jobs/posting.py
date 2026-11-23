"""One job posting as the reader shows it: clean text blocks + the facts read from it.

Boards return the posting as HTML (often HTML-escaped). It becomes a short list of
blocks — headings, paragraphs, list items — with no markup, so the web renders it
as text (nothing from a scraped page is ever injected as HTML).
"""

import html
import re
from typing import Optional

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from careeros.companies.directory import job_skills
from careeros.jobs.models.job import Job

MAX_BLOCKS = 160
MAX_CHARS = 14000
_HEADING = re.compile(r"^[A-Z][^.!?]{2,70}:?$")


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([.,;:!?)])", lambda m: m.group(1), text)  # "ledger ." -> "ledger."
    return text.replace("( ", "(")


def posting_blocks(raw: str) -> list[dict]:
    """HTML or plain text → [{"type": "h" | "p" | "li", "text"}]."""
    if not raw or not raw.strip():
        return []
    text = html.unescape(raw) if "&lt;" in raw else raw
    blocks: list[dict] = []
    total = 0

    def add(kind: str, value: str) -> None:
        nonlocal total
        value = _clean(value)
        if not value or total > MAX_CHARS or len(blocks) >= MAX_BLOCKS:
            return
        if blocks and blocks[-1]["text"] == value:
            return
        blocks.append({"type": kind, "text": value})
        total += len(value)

    if "<" in text and ">" in text:
        soup = BeautifulSoup(text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "p", "li", "strong", "b"]):
            if el.name in ("strong", "b"):
                # A paragraph made only of bold text is a heading in most postings
                parent = el.parent
                if parent and parent.name == "p" and _clean(parent.get_text()) == _clean(el.get_text()):
                    continue
                continue
            if el.name == "p":
                only_bold = el.find(["strong", "b"])
                if only_bold and _clean(only_bold.get_text()) == _clean(el.get_text()) and len(el.get_text()) < 90:
                    add("h", el.get_text(" "))
                    continue
                if el.find_parent("li"):
                    continue
                add("p", el.get_text(" "))
            elif el.name == "li":
                add("li", el.get_text(" "))
            else:
                add("h", el.get_text(" "))
        if blocks:
            return blocks
        text = soup.get_text("\n")

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[:1] in "•-*–" and len(line) > 2:
            add("li", line.lstrip("•-*– "))
        elif _HEADING.match(line) and len(line.split()) <= 8:
            add("h", line.rstrip(":"))
        else:
            add("p", line)
    return blocks


def _facts(job: Job) -> dict:
    """Claude's reading of this version of the posting (llm_extract.JobFacts), else keyword fields."""
    f = job.llm_facts if job.llm_facts and job.llm_facts_hash == job.content_hash else {}
    known = lambda v: v if v not in (None, "", "unknown") else None  # noqa: E731
    if f.get("salary_min") or f.get("salary_max"):
        salary = {"min": f.get("salary_min"), "max": f.get("salary_max"),
                  "currency": f.get("salary_currency") or "USD", "period": known(f.get("salary_period")) or "year"}
    elif job.salary_min or job.salary_max:
        salary = {"min": job.salary_min, "max": job.salary_max, "currency": job.salary_currency or "USD", "period": "year"}
    else:
        salary = None
    visa = known(f.get("visa_sponsorship")) or ("yes" if job.sponsors_visa else "no" if job.sponsors_visa is False else None)
    return {
        "summary": known(f.get("summary")),
        "seniority": known(f.get("seniority")),
        "min_years": f.get("min_years") if f.get("min_years") is not None else job.required_years,
        "workplace": known(f.get("workplace")) or ("remote" if job.remote else None),
        "remote_regions": f.get("remote_regions") or ([job.remote_region] if job.remote_region else []),
        "visa": visa,
        "salary": salary,
        "required_skills": job_skills(job),
        "nice_to_have": [x for x in (f.get("nice_to_have_skills") or []) if isinstance(x, str)][:10],
        "read_by": "claude" if f else "keywords",
    }


def _feed_label(job: Job) -> Optional[dict]:
    if job.source != "feed":
        return None
    from careeros.jobs.sources.feeds import LABELS

    return {"name": LABELS.get(job.site or "", job.site or "a job feed"), "url": job.url}


def get_posting(session: Session, url: str, user_id: Optional[str] = None) -> Optional[dict]:
    job = session.get(Job, url)
    if job is None or (job.added_by and job.added_by != user_id):  # someone else's own job
        return None
    return {
        "url": job.url,
        "company": job.company,
        "company_key": job.company_key,
        "title": job.title,
        "location": job.location,
        "department": job.department,
        "employment_type": job.employment_type,
        "posted_at": (job.posted_at or job.discovered_at).isoformat() if (job.posted_at or job.discovered_at) else None,
        "closed": job.closed_at is not None,
        "application_url": job.application_url or job.url,
        # Found through a job feed: credit it and link back to its page
        "via": _feed_label(job),
        "added": bool(job.added_by),
        "facts": _facts(job),
        "blocks": posting_blocks(job.full_description or job.description or ""),
    }
