"""Building the v8 model's inputs from stored jobs and the user's profile (model_v8.py)."""

import re
from datetime import datetime, timezone
from statistics import median
from typing import Iterable, Optional

from careeros.jobs.scoring.model_v8 import Seeker, Signals, VALUE_WEIGHTS
from careeros.knowledge.skill_names import key as skill_key
from careeros.shared.money import to_usd_year

LANG_CODES = {
    "english": "en", "german": "de", "deutsch": "de", "turkish": "tr", "türkçe": "tr", "turkce": "tr",
    "spanish": "es", "español": "es", "french": "fr", "français": "fr", "dutch": "nl", "italian": "it",
    "portuguese": "pt", "polish": "pl", "russian": "ru", "uzbek": "uz", "arabic": "ar", "kazakh": "kk",
    "azerbaijani": "az", "swedish": "sv", "danish": "da", "norwegian": "no", "finnish": "fi",
}
WORKING_LEVELS = {"b2", "c1", "c2", "native", "fluent", "professional", ""}
EFFORT_BY_NUMBER = {1: "quick", 2: "normal", 3: "tailored"}

_LANG_NAMES = {"de": "German", "nl": "Dutch", "fr": "French", "es": "Spanish", "it": "Italian", "pl": "Polish",
               "sv": "Swedish", "da": "Danish", "no": "Norwegian", "fi": "Finnish", "tr": "Turkish", "pt": "Portuguese"}
_LEVEL_WORD = r"(?:fluent|fluency|native|business[- ]level|business[- ]fluent|proficient|excellent|very good|strong|C1|C2)"
_NEEDS_LANG = {
    code: re.compile(
        rf"{_LEVEL_WORD}\W+(?:\w+\W+){{0,3}}{name}\b|\b{name}\W+(?:\w+\W+){{0,3}}(?:required|is a must|mandatory|essential|C1|C2)",
        re.I)
    for code, name in _LANG_NAMES.items()
}
_NEEDS_LANG["de"] = re.compile(_NEEDS_LANG["de"].pattern + r"|fließende?s?\s+Deutsch|verhandlungssichere?s?\s+Deutsch|"
                               r"Deutschkenntnisse\W+(?:\w+\W+){0,4}(?:fließend|verhandlungssicher|C1|C2|zwingend|erforderlich)",
                               re.I)
_GERMAN_WORDS = re.compile(r"\b(und|die|der|wir|mit|für|sie|ihre|deine|bei|unser|aufgaben|kenntnisse)\b", re.I)
_RELOCATION = re.compile(r"relocation (?:support|package|assistance|bonus)|we (?:will )?(?:help|support) (?:you )?(?:with )?relocat|"
                         r"umzugs(?:hilfe|unterstützung)|relocate to", re.I)
_SPONSOR_YES = re.compile(r"visa sponsorship (?:is )?(?:available|provided|offered|possible)|we (?:can |will |do )?sponsor|"
                          r"sponsorship (?:is )?available|blue card", re.I)
_EVERGREEN = re.compile(r"talent (?:pool|community|network)|general application|open application|initiativbewerbung|"
                        r"future (?:opportunities|openings|roles)|always (?:hiring|looking)", re.I)


def language_codes(langs: Iterable) -> set[str]:
    out = set()
    for item in langs or []:
        name = (item.get("code") if isinstance(item, dict) else str(item) or "").strip().lower()
        level = (item.get("level") if isinstance(item, dict) else "") or ""
        if level.strip().lower() not in WORKING_LEVELS and not level.upper().startswith(("B2", "C1", "C2")):
            continue
        code = LANG_CODES.get(name) or (name if len(name) == 2 else None)
        if code:
            out.add(code)
    return out


# Every pattern for a language needs one of these words in the text: a cheap check first
# (the patterns backtrack, and most postings name no other language)
_LANG_WORDS = {code: (name.lower(),) for code, name in _LANG_NAMES.items()}
_LANG_WORDS["de"] = ("german", "deutsch")


def languages_required(text: str, title: str) -> list[str]:
    lower = (text or "").lower()
    found = [code for code, rx in _NEEDS_LANG.items()
             if any(w in lower for w in _LANG_WORDS[code]) and rx.search(text or "")]
    # A posting written in German needs German
    words = re.findall(r"\w+", (text or "")[:2500])
    if "de" not in found and words and len(_GERMAN_WORDS.findall((text or "")[:2500])) / len(words) > 0.06:
        found.append("de")
    return found


def seeker_for(profile, weights: dict) -> Seeker:
    p = profile.preferences
    value_weights = {k: float(weights.get(k, w)) for k, w in VALUE_WEIGHTS.items()}
    effort = EFFORT_BY_NUMBER.get(int(round(float(weights.get("effort", 2) or 2))), "normal")
    return Seeker(
        skills={skill_key(s.name) for s in profile.skills},
        years=float(profile.years_experience or 0),
        target_roles=list(profile.target_roles or []),
        residence=getattr(p, "residence_country", None),
        languages=set(getattr(p, "languages", []) or []),
        needs_sponsorship=bool(p.work_visa_required),
        remote_ok=bool(p.remote), hybrid_ok=bool(p.hybrid_acceptable), onsite_ok=bool(p.onsite_acceptable),
        min_salary_usd=to_usd_year(p.min_salary, getattr(p, "salary_currency", "USD")) if p.min_salary else None,
        value_weights=value_weights, effort=effort,
    )


def offer_usd(low, high, currency) -> Optional[int]:
    """Expected offer: the lower third of a posted range (posted ranges run above what's paid)."""
    lo = to_usd_year(low, currency) if low else None
    hi = to_usd_year(high, currency) if high else None
    if lo and hi:
        return int(lo + (hi - lo) / 3)
    return lo or hi


def remote_scope(remote: bool, regions: list[str], location: str) -> Optional[str]:
    from careeros.jobs.geo import region_codes

    if not remote:
        return None
    if not regions:
        return "worldwide" if re.search(r"anywhere|worldwide|global", location or "", re.I) else None
    covered: set[str] = set()
    for r in regions:
        codes = region_codes(r)
        if codes is None:
            return "worldwide"
        covered |= codes
    if len(covered) >= 10 or any(r.strip().lower() in ("europe", "eu", "emea", "eea") for r in regions):
        return "region"
    return "country"


def build_signals(*, title: str, fields: dict, regions: list[str], location: str, description: str,
                  discovered_at: Optional[datetime], posted_at: Optional[datetime], company_size: str,
                  trust, market_medians: dict[str, int], now: Optional[datetime] = None,
                  seniority: Optional[str] = None) -> Signals:
    from careeros.jobs.geo import countries_in

    now = now or datetime.now(timezone.utc)

    def days(d: Optional[datetime]) -> Optional[int]:
        if not d:
            return None
        d = d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        return max(0, (now - d).days)

    ages = [a for a in (days(discovered_at), days(posted_at)) if a is not None]
    countries = [code for code, _ in countries_in(location)]
    offer = offer_usd(fields.get("salary_min"), fields.get("salary_max"), fields.get("salary_currency"))
    text = description or ""
    sponsors = fields.get("sponsors_visa")
    if sponsors is None and _SPONSOR_YES.search(text):
        sponsors = True
    return Signals(
        title=title,
        must=[skill_key(s) for s in fields.get("required_skills") or []],
        nice=[skill_key(s) for s in fields.get("preferred_skills") or []],
        required_years=float(fields.get("required_years") or 0),
        seniority=seniority,
        remote=bool(fields.get("remote")),
        hybrid=bool(fields.get("hybrid")),
        workplace=fields.get("workplace"),
        regions=regions,
        countries=countries,
        offer_usd=offer,
        age_days=max(ages) if ages else None,
        company_size=company_size or "unknown",
        trust=trust.level,
        agency=trust.agency,
        sponsors_visa=sponsors,
        relocation=bool(_RELOCATION.search(text)),
        languages_required=languages_required(text, title),
        evergreen=bool(_EVERGREEN.search(text[:3000]) or _EVERGREEN.search(title)),
        remote_scope=remote_scope(bool(fields.get("remote")), regions, location),
        market_median_usd=next((market_medians[c] for c in countries if c in market_medians), market_medians.get("*")),
    )


def market_medians(rows_offers: Iterable[tuple[list[str], Optional[int]]]) -> dict[str, int]:
    """Country code → median expected offer among the user's matching jobs ("*" = all)."""
    by: dict[str, list[int]] = {}
    for countries, offer in rows_offers:
        if not offer:
            continue
        by.setdefault("*", []).append(offer)
        for c in countries:
            by.setdefault(c, []).append(offer)
    return {c: int(median(v)) for c, v in by.items() if len(v) >= 5}
