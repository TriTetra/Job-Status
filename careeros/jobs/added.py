"""Add any job: give its link, and its page is read where the site allows it; or paste the
posting's text, for sites that don't allow reading (LinkedIn, Kariyer.net, Indeed…).

A job added this way is the person's alone (`jobs.added_by`): it is scored for them, shows
in their Opportunities and Search, can enter their ready-to-apply queue and get a kit, and no
one else sees it. Its row key is the link plus a per-person fragment (`#aplio-…`), so two
people adding the same link never share a row, and the link still opens the same page.

Reading a page: only public addresses (careeros/evidence/portfolio.check_url: no localhost,
private networks or cloud metadata, redirects re-checked), robots.txt honoured for our user
agent, sites whose terms forbid automated reading never fetched, responses size-capped.
The posting comes from the company's job system when the link is on one Aplio reads
(Greenhouse, Lever, Ashby, Workable, Personio, Recruitee: their public APIs), else from the
page's schema.org JobPosting data, else from the page text read by the LLM.
"""

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional
from urllib import robotparser
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from careeros.evidence.portfolio import PortfolioCrawlError, check_url
from careeros.jobs.discovery import board_from_url, company_site, links
from careeros.jobs.extraction import TextExtractor
from careeros.jobs.models.job import Job
from careeros.jobs.sources.ats.base import html_to_text, parse_time
from careeros.jobs.sources.feeds.base import yearly

logger = logging.getLogger(__name__)

SOURCE = "added"
USER_AGENT = "AplioBot/1.0 (+reads one job page a person asked for)"
ROBOTS_AGENT = "AplioBot"
MAX_BYTES = 2_000_000
MAX_REDIRECTS = 3
TIMEOUT = 12
MAX_TEXT = 20_000      # characters of posting text kept
MIN_TEXT = 200         # less than this: not a posting (or a page drawn by JavaScript)

# Sites whose terms forbid automated reading: never fetched, the person pastes the text
NO_READING = {"linkedin", "kariyer", "indeed", "glassdoor", "kununu", "xing"}


class AddJobError(Exception):
    """The job could not be added (message is safe to show the person)."""


def private_key(url: str, user_id: str) -> str:
    """The row key of a person's own copy: the link plus a fragment only they have."""
    return f"{url}#aplio-{hashlib.sha256(user_id.encode()).hexdigest()[:10]}"


def normalize(url: str) -> str:
    url = (url or "").strip()
    if not url:
        raise AddJobError("Paste the job's link.")
    if re.match(r"^[a-z][a-z0-9+.-]*:(?!\d)", url, re.I) and not re.match(r"^https?://", url, re.I):
        raise AddJobError("Paste a web link (https://…).")   # javascript:, data:, file:, ftp://…
    if "://" not in url:
        url = "https://" + url
    p = urlparse(url)
    try:
        p.port
    except ValueError:
        raise AddJobError("Paste a web link (https://…).") from None
    if p.scheme not in ("http", "https") or "." not in (p.hostname or ""):
        raise AddJobError("Paste a web link (https://…).")
    url = urldefrag(url)[0]
    if len(url) > 1900:
        raise AddJobError("That link is too long.")
    return url


def reading_forbidden(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return bool(set(host.split(".")[:-1]) & NO_READING)


# ── reading a page ───────────────────────────────────────────────────────

def _get(url: str, http: requests.Session, kinds: tuple[str, ...]) -> tuple[str, int, str]:
    """(final URL, status, text) from a public address, following redirects safely."""
    for _ in range(MAX_REDIRECTS + 1):
        try:
            url = check_url(url)
        except PortfolioCrawlError as e:
            raise AddJobError(str(e).replace("websites can be added", "web pages can be read")) from None
        try:
            resp = http.get(url, headers={"User-Agent": USER_AGENT, "Accept": ", ".join(kinds)},
                            timeout=TIMEOUT, allow_redirects=False, stream=True)
        except requests.exceptions.Timeout:
            raise AddJobError("The site took too long to answer: paste the posting text instead.") from None
        except requests.exceptions.RequestException:
            raise AddJobError("The site could not be reached: paste the posting text instead.") from None
        try:
            if resp.is_redirect and resp.headers.get("location"):
                url = urljoin(url, resp.headers["location"])
                continue
            if resp.status_code >= 400:
                return url, resp.status_code, ""
            kind = resp.headers.get("content-type", "text/html").lower()
            if not any(k in kind for k in kinds):
                raise AddJobError("That link isn't a web page: paste the posting text instead.")
            body = b""
            for chunk in resp.iter_content(64 * 1024):
                body += chunk
                if len(body) > MAX_BYTES:
                    break
            return url, resp.status_code, body[:MAX_BYTES].decode(resp.encoding or "utf-8", errors="replace")
        finally:
            resp.close()
    raise AddJobError("The site redirects too many times: paste the posting text instead.")


def robots_allows(url: str, http: requests.Session) -> bool:
    """RFC 9309: no robots.txt (4xx) = allowed; an unreachable one (5xx, no answer) = not."""
    p = urlparse(url)
    try:
        _, status, body = _get(f"{p.scheme}://{p.netloc}/robots.txt", http, ("text/plain", "text/html"))
    except AddJobError:
        return False
    if 400 <= status < 500:
        return True
    if status >= 500:
        return False
    rp = robotparser.RobotFileParser()
    rp.parse(body.splitlines())
    return rp.can_fetch(ROBOTS_AGENT, url)


def jobposting(html: str) -> Optional[dict]:
    """The page's schema.org JobPosting (JSON-LD), if it has one."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or tag.get_text() or "")
        except (ValueError, TypeError):
            continue
        stack = [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
            elif isinstance(d, dict):
                kinds = d.get("@type")
                if "JobPosting" in (kinds if isinstance(kinds, list) else [kinds]):
                    return d
                if "@graph" in d:
                    stack.append(d["@graph"])
    return None


def page_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer", "svg", "form"]):
        tag.decompose()
    root = soup.find("main") or soup.find("article") or soup.body or soup
    text = root.get_text("\n")
    return re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t]+", " ", text)).strip()[:MAX_TEXT]


def _name(v) -> str:
    if isinstance(v, dict):
        return str(v.get("name") or "").strip()
    return str(v or "").strip()


def _place(loc) -> str:
    if isinstance(loc, list):
        return "; ".join(p for p in (_place(x) for x in loc[:3]) if p)
    if not isinstance(loc, dict):
        return _name(loc)
    a = loc.get("address")
    if not isinstance(a, dict):
        return _name(a) or _name(loc)
    parts = [_name(a.get("addressLocality")), _name(a.get("addressRegion")), _name(a.get("addressCountry"))]
    return ", ".join(dict.fromkeys(p for p in parts if p))


def from_jobposting(d: dict) -> dict:
    """schema.org JobPosting → the fields a job row needs."""
    org = d.get("hiringOrganization") or {}
    org = org[0] if isinstance(org, list) and org else org
    org = org if isinstance(org, (dict, str)) else {}
    where = _place(d.get("jobLocation"))
    remote = str(d.get("jobLocationType") or "").upper() == "TELECOMMUTE"
    who = d.get("applicantLocationRequirements")
    if remote:
        allowed = _place(who) if who else ""
        where = f"Remote ({allowed})" if allowed else ("Remote" + (f", {where}" if where else ""))
    pay = d.get("baseSalary") or {}
    value = pay.get("value") if isinstance(pay, dict) else None
    low = high = cur = None
    if isinstance(value, dict):
        low, high, cur = yearly(value.get("minValue") or value.get("value"), value.get("maxValue"),
                                pay.get("currency"), value.get("unitText") or "")
    kinds = d.get("employmentType")
    site = org.get("sameAs") or org.get("url") if isinstance(org, dict) else None
    return {
        "title": html_to_text(str(d.get("title") or "")).strip(),
        "company": _name(org),
        "location": where,
        "description": str(d.get("description") or ""),
        "posted_at": parse_time(d.get("datePosted")),
        "employment_type": ", ".join(kinds) if isinstance(kinds, list) else (kinds or None),
        "remote": True if remote else None,
        "salary": (low, high, cur),
        "company_url": site if isinstance(site, str) else None,
    }


# ── a link on a job system Aplio reads ───────────────────────────────────

BOARD_ATS = ("greenhouse", "lever", "ashby", "workable", "personio", "recruitee")  # one list call each


def _company_name(ats: str, slug: str) -> str:
    from careeros.jobs.boards import load_boards

    for b in load_boards().boards:
        if b.ats == ats and b.board.lower() == slug.lower():
            return b.name
    return re.sub(r"[-_]+", " ", slug).strip().title() or slug


def from_board(url: str):
    """(Posting, company) from the company's job system API when the link is on one, else None."""
    from careeros.jobs.sources.ats import FETCHERS, Board, http_session

    found = board_from_url(url)
    if found is None or found.ats not in BOARD_ATS:
        return None
    board = Board(key=f"added:{found.ats}:{found.board}"[:64], name=found.board, ats=found.ats,
                  board=found.board, host=found.host)
    try:
        postings = FETCHERS[found.ats](board, http_session(), set(), None).postings
    except Exception as e:
        logger.info("Board read for an added job failed (%s/%s): %s", found.ats, found.board, e)
        return None
    path = [seg for seg in urlparse(url).path.split("/") if seg]
    want = url.rstrip("/")
    for posting in postings:
        if posting.url.rstrip("/") == want or (posting.apply_url or "").rstrip("/") == want                 or (posting.external_id and str(posting.external_id) in path):
            return posting, _company_name(found.ats, found.board)
    return None


# ── reading pasted text ──────────────────────────────────────────────────

class PostingHeader(BaseModel):
    is_job_posting: bool = True
    title: str = ""
    company: str = ""
    location: str = ""

    @field_validator("title", "company", "location")
    @classmethod
    def _short(cls, v: str) -> str:
        return " ".join((v or "").split())[:200]


HEADER_PROMPT = """A person copied this from a job posting page; it may include the site's menus, other jobs and buttons.

{text}

Return JSON with exactly these keys:
- is_job_posting: false if this is not one job posting (e.g. a list of jobs, a login page, an error page).
- title: the job's title as written.
- company: the hiring company (not the job site, not a recruiting agency's platform).
- location: where the job is, as written (city, country), or "Remote" plus where remote hires may live; "" if not stated."""


def read_header(text: str) -> PostingHeader:
    from careeros.shared.llm import LLMError, LLMNotConfiguredError, get_llm_client

    try:
        return get_llm_client().complete_model(
            HEADER_PROMPT.format(text=text[:8000]), PostingHeader, task="job_add", temperature=0.0,
            max_tokens=200, timeout=60,
            system="You read job postings. State only what the text says. Return one JSON object.")
    except LLMNotConfiguredError:
        raise AddJobError("Reading this posting needs the AI reader, which isn't set up here.") from None
    except LLMError as e:
        logger.info("Posting header failed: %s", e)
        raise AddJobError("The posting couldn't be read. Try pasting just the job's own text.") from None


# ── adding ───────────────────────────────────────────────────────────────

def _fields(url: str, text: str, http: requests.Session) -> dict:
    """What the posting says, from the pasted text or (where allowed) its page."""
    if not text:
        if reading_forbidden(url):
            host = urlparse(url).hostname or "This site"
            raise AddJobError(f"{host} doesn't allow its pages to be read automatically: "
                              "paste the posting text below.")
        if not robots_allows(url, http):
            raise AddJobError("This site asks bots not to read that page: paste the posting text below.")
        _, status, html = _get(url, http, ("text/html", "application/xhtml"))
        if status >= 400:
            raise AddJobError(f"The page answered with an error (HTTP {status}): paste the posting text below.")
        data = jobposting(html)
        if data:
            f = from_jobposting(data)
            if f["title"] and f["company"] and len(html_to_text(f["description"])) >= MIN_TEXT // 2:
                return f
        text = page_text(html)
        if len(text) < MIN_TEXT:
            raise AddJobError("That page has too little text to be a job posting (it may be drawn by "
                              "JavaScript): paste the posting text below.")
    if len(text) < MIN_TEXT:
        raise AddJobError("That's too short for a job posting: paste the whole posting.")
    head = read_header(text)
    if not head.is_job_posting or not head.title:
        raise AddJobError("That doesn't look like one job posting: paste the text of a single job.")
    return {"title": head.title, "company": head.company or "Unknown", "location": head.location,
            "description": text, "posted_at": None, "employment_type": None, "remote": None,
            "salary": (None, None, None), "company_url": None}


def content_hash(f: dict) -> str:
    raw = "\x1f".join([f["title"], f["company"], f["location"], f["description"]])
    return hashlib.sha256(raw.encode()).hexdigest()


def _facts(row: Job) -> None:
    """LLM facts now, so the first score already uses them; keywords when the reader is off."""
    from careeros.jobs.llm_extract import extract_facts
    from careeros.shared.llm import get_llm_client

    try:
        facts = extract_facts(row.title, row.company, row.location, row.description)
        row.llm_facts, row.llm_facts_hash = facts.model_dump(), row.content_hash
        row.llm_model = get_llm_client().model_for("job_extract")[:128]
    except Exception as e:  # not configured, budget, bad output: keyword extraction stands in
        logger.info("Facts for an added job not read: %s", e)


def add_job(session: Session, user_id: str, url: str, text: Optional[str] = None, *,
            http: Optional[requests.Session] = None, now: Optional[datetime] = None) -> Job:
    """Add (or refresh) a job for this person and return its row. Scoring is the caller's step."""
    now = now or datetime.now(timezone.utc)
    url = normalize(url)
    text = (text or "").strip()[:MAX_TEXT]
    shared = session.get(Job, url)
    if shared is not None and shared.added_by is None:
        return shared  # already known from a board or feed: it only needs scoring for this person
    on_board = None if text else from_board(url)
    if on_board is not None:
        posting, company = on_board
        known = session.get(Job, posting.url)
        if known is not None and known.added_by is None:
            return known  # the same job under its board's own link
        f = {"title": posting.title, "company": company, "location": posting.location,
             "description": posting.description, "posted_at": posting.posted_at,
             "employment_type": posting.employment_type, "remote": posting.remote,
             "salary": (posting.salary_min, posting.salary_max, posting.salary_currency), "company_url": None}
    else:
        f = _fields(url, text, http or requests.Session())
    extract = TextExtractor()
    desc = f["description"]
    plain = html_to_text(desc) if "<" in desc else desc
    low, high, cur = f["salary"]
    if not (low or high):
        low, high = extract.salary(plain)
        cur = "USD" if low else None
    remote = f["remote"] if f["remote"] is not None else extract.is_remote(f["location"], plain)
    key = private_key(url, user_id)
    row = session.get(Job, key)
    if row is None:
        row = Job(url=key, discovered_at=now)
        session.add(row)
    row.title, row.company, row.location = f["title"][:512], f["company"][:256], f["location"][:256]
    row.description = desc
    row.employment_type = (f["employment_type"] or None) and str(f["employment_type"])[:64]
    row.source, row.site, row.company_key, row.ats, row.added_by = SOURCE, None, None, None, user_id
    row.external_id = hashlib.sha256(url.encode()).hexdigest()[:32]
    row.application_url = url
    row.company_domain = company_site([u for u in [f["company_url"], *links(plain)] if u], plain)
    row.salary_min, row.salary_max, row.salary_currency = low, high, cur
    row.required_years = extract.required_years(row.title, plain)
    row.company_size = extract.company_size(row.company)
    row.remote = remote
    row.remote_region = extract.remote_region(row.location, plain) if remote else None
    row.sponsors_visa = extract.sponsors_visa(plain)
    row.required_skills = extract.skills(plain, row.title)
    changed = row.content_hash != content_hash({**f, "description": desc})
    row.content_hash = content_hash({**f, "description": desc})
    row.posted_at = f["posted_at"]
    row.last_seen_at, row.closed_at = now, None
    if changed or not row.llm_facts:
        _facts(row)
    session.flush()
    return row


def score_for(user_id: str, url: str) -> Optional[dict]:
    """Score one job for one person and save it (their Opportunities). None without a profile."""
    from careeros.db.connection import db
    from careeros.jobs.models.career_score import CareerScore
    from careeros.jobs.scan import company_open_counts, load_profile, load_weights, to_scoring_input
    from careeros.jobs.scoring.signals import seeker_for
    from careeros.jobs.scoring_service import ScoringService

    profile = load_profile(user_id)
    if profile is None:
        return None
    weights = load_weights(user_id)
    profile.seeker = seeker_for(profile, weights)
    with db.session_scope() as s:
        rows = s.query(Job).filter(Job.url == url).all()
        counts = company_open_counts(s)
        s.expunge_all()
    if not rows:
        return None
    jobs, meta = to_scoring_input(rows, counts, profile.preferences.preferred_locations)
    ScoringService(user_id=user_id).run_pipeline(jobs, profile, weights=weights, semantic=False, job_meta=meta)
    with db.session_scope() as s:
        sc = s.get(CareerScore, (user_id, url))
        return None if sc is None else {"career_score": sc.career_score, "recommendation": sc.recommendation}


def add_and_score(session: Session, user_id: str, url: str, text: Optional[str] = None, *,
                  http: Optional[requests.Session] = None) -> dict:
    """The "Add a job" action: add it, remember it, score it for this person."""
    from careeros.memory.events import job_stream, remember

    row = add_job(session, user_id, url, text, http=http)
    remember(session, user_id, "JobAdded", {"url": row.url, "title": row.title, "company": row.company,
                                            "how": "text" if (text or "").strip() and row.added_by else "link"},
             stream=job_stream(row.url), actor="user")
    out = {"url": row.url, "title": row.title, "company": row.company, "location": row.location,
           "own": bool(row.added_by)}
    session.commit()
    scored = score_for(user_id, out["url"]) or {}
    return {**out, "career_score": scored.get("career_score"), "recommendation": scored.get("recommendation")}
