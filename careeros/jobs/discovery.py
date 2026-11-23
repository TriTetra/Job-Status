"""Find company job boards in links: a startup's posting on Hacker News or a job feed
often points at its own Ashby / Lever / Greenhouse / Personio / Recruitee / Workable /
SmartRecruiters board. Every board found this way is read like the ones in
companies.yaml from then on, so the company's *other* openings show up too.
"""

import re
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import parse_qs, unquote, urlparse

# Path segments that are part of the ATS site, not a company slug
_NOT_SLUGS = {"", "embed", "j", "api", "o", "v0", "v1", "jobs", "job", "oneclick-ui", "careers", "companies", "search"}
_HOST_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
_LINK = re.compile(r"https?://[^\s\"'<>)\]]+", re.I)


@dataclass(frozen=True)
class FoundBoard:
    ats: str
    board: str        # slug the ATS API takes
    host: str = ""    # API / feed host when it isn't the default (Lever EU, Personio .com)


def links(text: Optional[str]) -> list[str]:
    """Every http(s) link in a piece of text or HTML, trailing punctuation trimmed."""
    return [m.rstrip(".,;:!?") for m in _LINK.findall(text or "")]


def board_from_url(url: str) -> Optional[FoundBoard]:
    try:
        u = urlparse(url.strip())
    except ValueError:
        return None
    host = (u.hostname or "").lower()
    parts = [unquote(p) for p in u.path.split("/") if p]
    first = parts[0] if parts else ""

    if host in ("boards.greenhouse.io", "job-boards.greenhouse.io", "boards.eu.greenhouse.io", "job-boards.eu.greenhouse.io"):
        slug = (parse_qs(u.query).get("for") or [first])[0] if first in ("embed", "") else first
        return FoundBoard("greenhouse", slug) if _ok(slug) else None
    if host == "jobs.lever.co" and _ok(first):
        return FoundBoard("lever", first)
    if host == "jobs.eu.lever.co" and _ok(first):
        return FoundBoard("lever", first, "api.eu.lever.co")
    if host == "jobs.ashbyhq.com" and _ok(first):
        return FoundBoard("ashby", first)
    if host == "apply.workable.com" and _ok(first):
        return FoundBoard("workable", first)
    if host in ("jobs.smartrecruiters.com", "careers.smartrecruiters.com") and _ok(first):
        return FoundBoard("smartrecruiters", first)
    m = re.match(r"^([a-z0-9-]+)\.jobs\.personio\.(de|com)$", host)
    if m and _HOST_SLUG.match(m.group(1)):
        return FoundBoard("personio", m.group(1), host)
    m = re.match(r"^([a-z0-9-]+)\.recruitee\.com$", host)
    if m and m.group(1) not in ("www", "app", "api", "careers") and _HOST_SLUG.match(m.group(1)):
        return FoundBoard("recruitee", m.group(1))
    return None


_SLUG = re.compile(r"[\w.\- ]{1,120}")  # Ashby names may contain spaces or dots


def _ok(slug: str) -> bool:
    return slug.lower() not in _NOT_SLUGS and _SLUG.fullmatch(slug) is not None


def boards_in(urls: Iterable[str]) -> list[FoundBoard]:
    found = [board_from_url(u) for u in urls]
    return list(dict.fromkeys(b for b in found if b))


_NOT_COMPANY_SITES = (
    "ycombinator.com", "greenhouse.io", "lever.co", "ashbyhq.com", "workable.com", "smartrecruiters.com",
    "personio.de", "personio.com", "recruitee.com", "linkedin.com", "github.com", "twitter.com", "x.com",
    "google.com", "notion.site", "notion.so", "youtube.com", "medium.com", "wellfound.com", "join.com",
    "teamtailor.com", "calendly.com", "forms.gle", "typeform.com", "facebook.com", "instagram.com",
    "arxiv.org", "wikipedia.org", "apple.com", "microsoft.com", "amazon.com", "bit.ly", "glassdoor.com",
    # job feeds and their CDNs
    "himalayas.app", "jobicy.com", "remotive.com", "remotive.io", "arbeitnow.com", "eightfold.ai",
    # personal mail
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "proton.me", "protonmail.com", "icloud.com",
)
_EMAIL_DOMAIN = re.compile(r"[\w.+-]+@([a-z0-9-]+(?:\.[a-z0-9-]+)+)", re.I)


def _company_host(host: str) -> Optional[str]:
    host = host.lower().removeprefix("www.").strip(".")
    if host and "." in host and not any(host == s or host.endswith("." + s) for s in _NOT_COMPANY_SITES):
        return host
    return None


def company_site(urls: Iterable[str], text: Optional[str] = None) -> Optional[str]:
    """The company's own website: the first link that isn't a job board / social / feed site,
    else the domain of an e-mail address in the text (jobs@acme.ai → acme.ai)."""
    for url in urls:
        host = _company_host(urlparse(url).hostname or "")
        if host:
            return host
    for domain in _EMAIL_DOMAIN.findall(text or ""):
        host = _company_host(domain)
        if host:
            return host
    return None


def key_for(found: FoundBoard, taken: set[str]) -> str:
    """A stable, readable key that doesn't clash with companies.yaml or other discovered boards."""
    base = re.sub(r"[^a-z0-9]+", "-", found.board.lower()).strip("-")[:48] or found.ats
    for candidate in (base, f"{base}-{found.ats}"):
        if candidate not in taken:
            return candidate
    n = 2
    while f"{base}-{found.ats}-{n}" in taken:
        n += 1
    return f"{base}-{found.ats}-{n}"
