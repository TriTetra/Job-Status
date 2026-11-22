"""Personio public job feed (XML), popular with German and European startups.

https://developer.personio.de/docs/retrieving-open-job-positions
The board host is <company>.jobs.personio.de (or .com); postings live at /job/<id>.
"""

import xml.etree.ElementTree as ET

from careeros.jobs.sources.ats.base import TIMEOUT, Board, FetchResult, Posting, html_to_text, parse_time


def host(board: Board) -> str:
    return board.host or f"{board.board}.jobs.personio.de"


def fetch(board: Board, http, known_urls: set[str], keep_title=None) -> FetchResult:
    resp = http.get(f"https://{host(board)}/xml?language=en", timeout=TIMEOUT, headers={"Accept": "application/xml"})
    resp.raise_for_status()
    root = ET.fromstring(resp.content)
    return FetchResult(postings=[_posting(board, p) for p in root.findall("position") if p.findtext("id")])


def _text(node, tag: str) -> str:
    return (node.findtext(tag) or "").strip()


def _posting(board: Board, p) -> Posting:
    sections = []
    for d in p.findall("jobDescriptions/jobDescription"):
        name, body = _text(d, "name"), html_to_text(d.findtext("value"))
        sections.append(f"{name}\n{body}" if name else body)
    offices = [_text(p, "office")] + [(o.text or "").strip() for o in p.findall("additionalOffices/office")]
    job_id = _text(p, "id")
    url = f"https://{host(board)}/job/{job_id}?language=en"
    kind = " ".join(x for x in (_text(p, "employmentType"), _text(p, "schedule")) if x)
    return Posting(
        external_id=job_id,
        url=url,
        apply_url=url,
        title=_text(p, "name"),
        location=" • ".join(o for o in offices if o),
        description="\n\n".join(s for s in sections if s),
        department=_text(p, "department") or None,
        employment_type=kind or None,
        posted_at=parse_time(_text(p, "createdAt")),
    )
