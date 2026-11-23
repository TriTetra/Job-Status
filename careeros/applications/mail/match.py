"""Which application (if any) an e-mail is about, from its sender and subject only.

Only a message that names a company the person applied to, or comes from that company's
domain, is read any further. Everything else in the mailbox is left alone.
"""

import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

from careeros.applications.mail.reader import Header

# Hiring systems and job sites that send mail on a company's behalf: the company is in the
# sender's name or the subject, not in the domain
SENDER_SYSTEMS = (
    "greenhouse.io", "greenhouse-mail.io", "lever.co", "hire.lever.co", "ashbyhq.com", "workablemail.com",
    "workable.com", "smartrecruiters.com", "myworkday.com", "workday.com", "personio.de", "personio.com",
    "recruitee.com", "teamtailor.com", "teamtailor-mail.com", "bamboohr.com", "icims.com", "jobvite.com",
    "successfactors.com", "successfactors.eu", "sap.com", "eightfold.ai", "pinpointhq.com", "join.com",
    "linkedin.com", "kariyer.net", "indeed.com", "breezy.hr", "jazzhr.com", "recruitcrm.io", "rippling.com",
)
_SUFFIXES = {"inc", "inc.", "gmbh", "ltd", "ltd.", "llc", "bv", "b.v.", "ag", "sa", "s.a.", "as", "a.s.", "a.ş.",
             "corp", "corporation", "co", "company", "plc", "se", "srl", "sas", "oy", "ab", "aps", "kg", "teknoloji",
             "technologies", "technology", "labs", "group", "holding", "software", "yazilim", "yazılım"}
_GENERIC = {"remote", "global", "jobs", "careers", "career", "team", "hr", "talent", "people", "unknown", "the",
            "app", "ai", "data", "cloud", "systems", "digital", "solutions", "services"}


def company_words(company: str) -> str:
    """"Acme GmbH" → "acme"; "Delivery Hero SE" → "delivery hero"."""
    words = [w for w in re.split(r"[^\w.&'-]+", (company or "").lower()) if w]
    while words and words[-1].strip(".,") in _SUFFIXES:
        words.pop()
    name = " ".join(words).strip(" .,-")
    return "" if len(name) < 3 or name in _GENERIC else name


def _named(name: str, text: str) -> bool:
    return bool(name) and re.search(r"(?<![\w])" + re.escape(name) + r"(?![\w])", text.lower()) is not None


def _host(url: Optional[str]) -> str:
    return (urlparse(url or "").hostname or "").lower().removeprefix("www.")


def _within(domain: str, site: str) -> bool:
    return bool(site) and (domain == site or domain.endswith("." + site))


@dataclass
class AppRef:
    url: str
    title: str
    company: str
    status: str
    domains: set = field(default_factory=set)   # the company's own sites (not job boards)

    @property
    def name(self) -> str:
        return company_words(self.company)


def own_domains(company_domain: Optional[str], *urls: Optional[str]) -> set:
    """The company's own domains: its website, and job links that aren't on a hiring system."""
    out = {d for d in [(company_domain or "").lower().removeprefix("www.")] if d}
    for u in urls:
        h = _host(u)
        if h and not any(_within(h, s) for s in SENDER_SYSTEMS) and h.count(".") >= 1:
            parts = h.split(".")
            out.add(".".join(parts[-3:]) if len(parts[-1]) == 2 and len(parts) >= 3 and len(parts[-2]) <= 3
                    else ".".join(parts[-2:]))  # careers.acme.co.uk → acme.co.uk; jobs.acme.com → acme.com
    return out


@dataclass
class Match:
    app: AppRef
    score: int
    ambiguous: bool


def match(h: Header, apps: list[AppRef]) -> Optional[Match]:
    """The application this message is about, or None (then it isn't read)."""
    domain = h.from_domain
    if not domain:
        return None
    scored = []
    for a in apps:
        score = 0
        if any(_within(domain, d) for d in a.domains):
            score += 3
        if _named(a.name, h.from_name):
            score += 2
        if _named(a.name, h.subject):
            score += 2
        if score < 2:
            continue
        title_words = {w for w in re.findall(r"[a-z]{4,}", (a.title or "").lower())}
        score += 1 if title_words & set(re.findall(r"[a-z]{4,}", h.subject.lower())) else 0
        scored.append((score, a))
    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    best, app = scored[0]
    ambiguous = len(scored) > 1 and scored[1][0] == best and scored[1][1].url != app.url
    return Match(app=app, score=best, ambiguous=ambiguous)
