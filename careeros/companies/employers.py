"""Employers directory: the main employers of software, data and AI people in a country, with a
link to each one's own careers page (infra/config/employers_<cc>.yaml).

Links only. Where an employer's job system has a public feed, its board is also in
companies.yaml and Aplio reads its jobs ("tracked"); for the rest the person opens the careers
page themselves (many Turkish employers post only on their own portal, Kariyer.net or LinkedIn,
whose terms forbid automated collection).
"""

from functools import lru_cache
from typing import Optional
from urllib.parse import urlparse

import yaml

from careeros.shared.config import ROOT

DIR = ROOT / "infra" / "config"
SECTORS = ("ecommerce", "fintech", "banking", "saas", "games", "telecom", "defence", "mobility", "consulting",
           "global-hub", "other")
SECTOR_LABEL = {
    "ecommerce": "E-commerce and marketplaces", "fintech": "Fintech and payments", "banking": "Banks and their tech arms",
    "saas": "Software and SaaS", "games": "Games", "telecom": "Telecom", "defence": "Defence and aerospace",
    "mobility": "Mobility and automotive", "consulting": "Consulting and IT services",
    "global-hub": "Global companies' hubs", "other": "Other",
}


def _https(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    u = url.strip()
    if "://" not in u and ":" in u.split("/")[0]:
        return None  # "javascript:…", "mailto:…": not a web page
    p = urlparse(u if "://" in u else f"https://{u}")
    host = p.hostname or ""
    return p.geturl() if p.scheme in ("http", "https") and "." in host else None


def _domain(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    host = urlparse(value if "://" in value else f"https://{value}").netloc.lower()
    return host.removeprefix("www.") or None


@lru_cache(maxsize=8)
def load(country: str = "tr") -> tuple[dict, ...]:
    """The directory for a country, cleaned: valid https links, known sectors, sorted by name."""
    path = DIR / f"employers_{country.lower()}.yaml"
    if not path.exists():
        return ()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out = []
    for e in data.get("employers") or []:
        name = str(e.get("name") or "").strip()
        careers = _https(e.get("careers_url"))
        if not name or not careers:
            continue
        sector = e.get("sector") if e.get("sector") in SECTORS else "other"
        out.append({
            "name": name, "domain": _domain(e.get("domain")) or _domain(careers), "sector": sector,
            "city": e.get("city") or None, "careers_url": careers, "ats": e.get("ats") or None,
            "board_key": e.get("board_key") or None, "note": e.get("note") or None,
        })
    return tuple(sorted(out, key=lambda x: x["name"].lower()))


def domains(country: str = "tr") -> set[str]:
    return {e["domain"] for e in load(country) if e["domain"]}


def open_in_country(session, keys: set[str], country: str) -> dict[str, int]:
    """Open jobs per board located in the country (a global employer's board counts only its jobs there)."""
    from sqlalchemy import func, or_

    from careeros.jobs.models.job import Job
    from careeros.jobs.search import _place_names

    if not keys:
        return {}
    here = or_(*[Job.location.ilike(f"%{n}%") for n in _place_names(country.upper())])
    return dict(session.query(Job.company_key, func.count()).filter(
        Job.closed_at.is_(None), Job.company_key.in_(list(keys)), here).group_by(Job.company_key).all())


def directory(session, country: str = "tr") -> dict:
    """The directory with which employers Aplio reads jobs for, and how many are open there now."""
    from careeros.jobs.boards import load_boards

    boards = {b.key: b for b in load_boards().boards}
    by_domain = {b.domain.lower(): b.key for b in boards.values() if b.domain}
    keys = {e["board_key"] if e["board_key"] in boards else by_domain.get(e["domain"] or "") for e in load(country)}
    open_counts = open_in_country(session, {k for k in keys if k}, country)
    items = []
    for e in load(country):
        key = e["board_key"] if e["board_key"] in boards else by_domain.get(e["domain"] or "")
        items.append({**e, "board_key": key, "tracked": bool(key), "open_roles": open_counts.get(key, 0) if key else 0})
    return {
        "country": country.upper(), "count": len(items), "tracked": sum(1 for i in items if i["tracked"]),
        "sectors": [{"id": s, "label": SECTOR_LABEL[s]} for s in SECTORS if any(i["sector"] == s for i in items)],
        "employers": items,
    }
