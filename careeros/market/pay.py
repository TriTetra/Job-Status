"""What tech roles pay, by country and role family, from postings that state their salary,
set next to official statistics where Aplio has a verified figure.

Every number says where it comes from: how many postings (each can be opened), the period
they were seen in, or the official publication, its reference period and link.

Only pay the employer stated is used:
- the LLM's reading of the posting (it records the currency and the period), or
- the posting's own salary fields, when their currency is the job country's currency.
  Amounts read from free text by the keyword extractor are stored as USD without knowing the
  currency, so a "USD" salary on a job in Germany is not trusted.
Yearly amounts only; ranges count by their midpoint. Medians need at least MIN_POSTINGS.
"""

import re
import statistics
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Iterable, Optional

import yaml
from sqlalchemy import or_
from sqlalchemy.orm import Session, load_only

from careeros.jobs.models.job import Job
from careeros.shared.config import ROOT
from careeros.shared.money import to_usd_year

WINDOW_DAYS = 180
MIN_POSTINGS = 5        # a median from fewer postings isn't shown
MIN_QUARTILES = 8       # nor a middle half from fewer than this
EXAMPLES = 5
OFFICIAL_FILE = ROOT / "infra" / "config" / "pay_official.yaml"

CURRENCY = {
    "US": "USD", "GB": "GBP", "CA": "CAD", "CH": "CHF", "PL": "PLN", "TR": "TRY", "SE": "SEK", "DK": "DKK",
    "NO": "NOK", "CZ": "CZK", "RO": "RON", "HU": "HUF", "IN": "INR", "AU": "AUD", "NZ": "NZD", "SG": "SGD",
    "AE": "AED", "IL": "ILS", "BR": "BRL", "JP": "JPY", "MX": "MXN", "ZA": "ZAR", "UA": "UAH", "SA": "SAR",
    **{c: "EUR" for c in ("DE", "NL", "ES", "FR", "IT", "AT", "BE", "IE", "FI", "PT", "GR", "LU", "EE", "LV",
                          "LT", "SK", "SI", "HR", "MT", "CY")},
}

# (family, title pattern), first match wins: "Machine Learning Platform Engineer" is ML / AI
FAMILIES = [
    ("ML / AI", r"machine learning|\bml\b|\bai\b|\bllm|\bnlp\b|computer vision|deep learning|applied scien|mlops"),
    ("Data", r"\bdata\b|analytics|\banalyst\b|\bbi\b|business intelligence|statistic"),
    ("Full stack", r"full[\s-]?stack"),
    ("Frontend", r"front[\s-]?end|\breact\b|\bui engineer|web developer"),
    ("Mobile", r"\bios\b|android|mobile|flutter"),
    ("DevOps / Platform", r"devops|\bsre\b|site reliability|platform|infrastructure|\bcloud\b|kubernetes"),
    ("Security", r"security|\bsecops\b|penetration|appsec"),
    ("Backend", r"back[\s-]?end|server|\bapi\b|java\b|golang|\bgo\b|python|\.net|node"),
    ("Software", r"software|developer|engineer|programmer|entwickler|yazılım|geliştirici|ingénieur|desarroll"),
]
_FAMILY_RX = [(f, re.compile(p, re.I)) for f, p in FAMILIES]
_NOT_TECH = re.compile(r"sales|account (executive|manager)|recruit|marketing|legal|counsel|finance|accountant|"
                       r"customer success|support specialist|hr\b|people partner|mechanical|civil|electrical|"
                       r"manufacturing|technician", re.I)


def family_of(title: str) -> Optional[str]:
    t = title or ""
    if _NOT_TECH.search(t):
        return None
    return next((f for f, rx in _FAMILY_RX if rx.search(t)), None)


def _facts(job: Job) -> Optional[dict]:
    f = job.llm_facts
    return f if f and job.llm_facts_hash and job.llm_facts_hash == job.content_hash else None


def stated_range(job: Job, country: Optional[str]) -> Optional[tuple[Optional[float], Optional[float], str]]:
    """(low, high, currency) per year the employer stated for this job, or None.
    Without one country (remote across several), only the LLM's reading counts: it records the currency."""
    local = CURRENCY.get(country or "")
    f = _facts(job)
    if f and (f.get("salary_min") or f.get("salary_max")) and f.get("salary_currency"):
        if f.get("salary_period") not in ("year", None):
            return None
        lo, hi, cur = f.get("salary_min"), f.get("salary_max"), str(f["salary_currency"]).upper()
    elif job.salary_min or job.salary_max:
        lo, hi, cur = job.salary_min, job.salary_max, (job.salary_currency or "").upper()
        if not local or cur != local:   # a keyword-extracted amount stored as USD: currency unknown
            return None
    else:
        return None
    vals = [float(v) for v in (lo, hi) if v]
    if not vals:
        return None
    usd = to_usd_year(sum(vals) / len(vals), cur)
    if usd is None or not 8_000 <= usd <= 1_500_000:   # not a yearly salary (hourly, a typo, a budget)
        return None
    return (float(lo) if lo else None), (float(hi) if hi else None), cur


def stated_pay(job: Job, country: str) -> Optional[tuple[float, str]]:
    """(yearly amount: the range's midpoint, currency) the employer stated, or None."""
    r = stated_range(job, country)
    if r is None:
        return None
    vals = [v for v in r[:2] if v]
    return sum(vals) / len(vals), r[2]


def _summary(amounts: list[float]) -> dict:
    out: dict = {"postings": len(amounts)}
    if len(amounts) >= MIN_POSTINGS:
        out["median"] = int(round(statistics.median(amounts), -2))
    if len(amounts) >= MIN_QUARTILES:
        q = statistics.quantiles(amounts, n=4)
        out["p25"], out["p75"] = int(round(q[0], -2)), int(round(q[2], -2))
    return out


@lru_cache(maxsize=1)
def official() -> list[dict]:
    """Verified official figures (infra/config/pay_official.yaml): each with its publication and link."""
    if not OFFICIAL_FILE.exists():
        return []
    rows = yaml.safe_load(OFFICIAL_FILE.read_text(encoding="utf-8")) or {}
    return [r for r in rows.get("figures") or [] if r.get("url", "").startswith("https://") and r.get("median")]


def pay_by_country(rows: Iterable[Job], preferred: Optional[list[str]] = None, now: Optional[datetime] = None) -> dict:
    """{countries: [{code, currency, all: {...}, families: [{family, postings, median, p25, p75, examples}]}]}"""
    from careeros.jobs.geo import countries_in

    now = now or datetime.now(timezone.utc)
    by: dict[tuple[str, str], list[tuple[float, str]]] = defaultdict(list)
    for j in rows:
        fam = family_of(j.title)
        codes = [c for c, _ in countries_in(j.location or "")]
        if not fam or len(codes) != 1:   # remote across countries: no one country's pay
            continue
        pay = stated_pay(j, codes[0])
        if pay:
            by[(codes[0], fam)].append((pay[0], j.url))
    countries: dict[str, dict] = {}
    for (code, fam), items in by.items():
        c = countries.setdefault(code, {"code": code, "currency": CURRENCY.get(code), "families": [], "_all": []})
        c["_all"] += [a for a, _ in items]
        c["families"].append({"family": fam, **_summary([a for a, _ in items]),
                              "examples": [u for _, u in items[:EXAMPLES]]})
    preferred = [p.upper() for p in preferred or []]
    out = []
    for c in countries.values():
        c["all"] = _summary(c.pop("_all"))
        c["families"].sort(key=lambda f: -f["postings"])
        c["official"] = [o for o in official() if o.get("country") == c["code"]]
        out.append(c)
    out.sort(key=lambda c: (c["code"] not in preferred, -c["all"]["postings"]))
    for code in preferred:  # a target country with official figures but no stated pay still shows them
        if code not in countries and any(o.get("country") == code for o in official()):
            out.append({"code": code, "currency": CURRENCY.get(code), "families": [], "all": {"postings": 0},
                        "official": [o for o in official() if o.get("country") == code]})
    return {"window_days": WINDOW_DAYS, "min_postings": MIN_POSTINGS, "countries": out,
            "as_of": now.date().isoformat()}


def snapshot(session: Session, user_id: str, now: Optional[datetime] = None) -> dict:
    """Pay by country for the market page: shared postings seen in the last WINDOW_DAYS."""
    from careeros.identity.models.career_preferences import CareerPreferences

    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=WINDOW_DAYS)
    rows = (session.query(Job)
            .options(load_only(Job.url, Job.title, Job.location, Job.salary_min, Job.salary_max, Job.salary_currency,
                               Job.llm_facts, Job.llm_facts_hash, Job.content_hash))
            .filter(Job.added_by.is_(None), Job.discovered_at >= since,
                    or_(Job.salary_min.isnot(None), Job.salary_max.isnot(None),
                        Job.llm_facts["salary_min"].astext.isnot(None), Job.llm_facts["salary_max"].astext.isnot(None)))
            .all())
    prefs = session.query(CareerPreferences).filter(CareerPreferences.user_id == user_id).first()
    preferred = list(getattr(prefs, "preferred_country_codes", None) or [])
    return pay_by_country(rows, preferred, now)
