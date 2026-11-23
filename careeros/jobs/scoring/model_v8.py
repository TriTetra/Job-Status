"""Scoring v8: rank by chance-weighted surplus (research report
"reports/İş puanlama algoritması araştırması.md").

  1. Gates — conditions that make a job impossible for this person (scam signs, a work
     arrangement they refuse, a required language they lack, "no sponsorship" when they
     need it, a UK salary below the sponsorship floor). A gated job gets chance 0.
  2. Chance of an interview — a cold application starts near 8% and is multiplied by:
       must-have skill coverage (logistic, midpoint 55%), title family and level, years
       short of the requirement, posting age, competition (worldwide remote draws ~8.8x the
       applicants), and the visa / relocation rules of the job's country for this person.
     Then × the chance the posting is real (ghost jobs: by how long it has been up).
  3. Value of the job if you get it — log pay against your reference, growth, stability,
     work style; pay below your minimum caps it.
  4. Rank — Bied et al. (2026): Γ = P · σ · softplus((V − v0 − c/P) / σ). A long shot must
     be much better to be worth an application; c is the effort an application costs.

Most multipliers are evidence-anchored design choices, not measured effects: log outcomes
and calibrate (Platt scaling on "any response") once there are enough.
"""

import math
import re
from dataclasses import asdict, dataclass, field
from typing import Optional

BASE_INTERVIEW = 0.08     # cold application → interview, knowledge work
MAX_INTERVIEW = 0.60
SIGMA = 0.05
RESERVATION = 0.40        # v0: a job must beat this value to be worth anything
# Cost of one application in value units. Calibrated so that at a typical cold chance (~1%)
# the bar rises by ~0.06 and a 0.3% long shot needs ~0.2 more value: the report's
# 0.001–0.003 assumed chances near 5%, which real postings for this profile rarely reach.
EFFORT_COST = {"quick": 0.0003, "normal": 0.0006, "tailored": 0.0012}
# Score scale: log of Γ between a hopeless job and an excellent one (≈6% chance, value 0.85) → 0..100
# The floor is low on purpose: below the reservation line Γ falls off exponentially, and a
# log scale keeps those jobs ordered (instead of all reading 0).
GAMMA_LO, GAMMA_HI = 1e-7, 0.025

VALUE_WEIGHTS = {"pay": 0.35, "growth": 0.22, "stability": 0.18, "work_style": 0.13}

# Visa / work-permit floors (2026), in USD a year
UK_SPONSOR_FLOOR_USD = 52_960      # £41,700 Skilled Worker general threshold
DE_BLUE_CARD_SHORTAGE_USD = 49_610  # €45,934 (IT is a shortage occupation)
ES_BLUE_CARD_USD = 42_410          # €39,270

EU = {"DE", "FR", "NL", "SE", "NO", "DK", "FI", "ES", "PT", "IT", "PL", "AT", "BE", "IE", "CZ", "EE", "LV",
      "LT", "RO", "BG", "HU", "GR", "HR", "SI", "SK", "LU", "MT", "CY"}

LEVELS = {"intern": 0, "junior": 1, "mid": 2, "senior": 3, "staff": 4, "principal": 4, "lead": 4, "head": 5, "director": 5}
_LEVEL_WORDS = [(re.compile(r"\b(intern|internship|praktikum|stajyer)\b", re.I), 0),
                (re.compile(r"\b(junior|jr\.?|graduate|entry[- ]level|new grad)\b", re.I), 1),
                (re.compile(r"\b(senior|sr\.?|kıdemli)\b", re.I), 3),
                (re.compile(r"\b(staff|principal|lead|architect)\b", re.I), 4),
                (re.compile(r"\b(head of|director|vp|vice president|chief)\b", re.I), 5)]
_STOP = {"and", "or", "the", "of", "for", "in", "at", "to", "with", "a", "an", "m", "f", "d", "w", "x", "remote",
         "hybrid", "senior", "junior", "lead", "staff", "principal", "sr", "jr", "mid", "level", "i", "ii", "iii", "iv"}


@dataclass
class Seeker:
    skills: set[str]                      # skill keys the person shows
    years: float
    target_roles: list[str] = field(default_factory=list)
    residence: Optional[str] = None       # country code where they live
    languages: set[str] = field(default_factory=set)  # ISO 639-1 codes they work in
    needs_sponsorship: bool = False
    remote_ok: bool = True
    hybrid_ok: bool = True
    onsite_ok: bool = True
    min_salary_usd: Optional[int] = None
    value_weights: dict = field(default_factory=lambda: dict(VALUE_WEIGHTS))
    effort: str = "normal"


@dataclass
class Signals:
    title: str
    must: list[str]                       # skill keys, most important first
    nice: list[str]
    required_years: float = 0.0
    seniority: Optional[str] = None       # junior | mid | senior | staff | principal | lead…
    remote: bool = False
    hybrid: bool = False
    workplace: Optional[str] = None       # remote | hybrid | onsite when the posting says; None = not stated
    regions: list[str] = field(default_factory=list)   # who may take a remote job
    countries: list[str] = field(default_factory=list)  # where the job is (codes)
    offer_usd: Optional[int] = None       # expected offer, a year
    age_days: Optional[int] = None        # since first seen / posted, whichever is older
    company_size: str = "unknown"
    trust: str = "unknown"
    agency: bool = False
    sponsors_visa: Optional[bool] = None
    relocation: bool = False              # "relocation support" mentioned
    languages_required: list[str] = field(default_factory=list)
    evergreen: bool = False               # talent-pool / always-open wording
    remote_scope: Optional[str] = None    # worldwide | region | country (remote jobs)
    market_median_usd: Optional[int] = None  # typical pay for matched jobs in that country


@dataclass
class Result:
    score: float                 # 0..100 for ranking and the ring
    recommendation: str
    p_interview: float
    p_real: float
    p_effective: float
    value: float
    gamma: float
    fit: float                   # skills × title × years, 0..1 (display)
    gates: list[str]
    chance_factors: dict
    value_parts: dict

    def explain(self) -> dict:
        d = asdict(self)
        return {"v": 8, **{k: (round(v, 4) if isinstance(v, float) else v) for k, v in d.items()}}


# ── helpers ──────────────────────────────────────────────────────────────

def _logistic(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def _softplus(x: float) -> float:
    return x if x > 30 else math.log1p(math.exp(x))


_SYNONYMS = [(re.compile(r"machine[\s-]+learning", re.I), "ml"), (re.compile(r"artificial[\s-]+intelligence", re.I), "ai"),
             (re.compile(r"front[\s-]+end", re.I), "frontend"), (re.compile(r"back[\s-]+end", re.I), "backend"),
             (re.compile(r"full[\s-]+stack", re.I), "fullstack"), (re.compile(r"\bdeveloper\b", re.I), "engineer"),
             (re.compile(r"\bmühendis(?:i)?\b", re.I), "engineer"), (re.compile(r"\bgeliştirici(?:si)?\b", re.I), "engineer"),
             (re.compile(r"\byazılım\b", re.I), "software"), (re.compile(r"\bveri\b", re.I), "data"),
             (re.compile(r"\byapay zeka\b", re.I), "ai")]


def _tokens(text: str) -> set[str]:
    text = (text or "").lower()
    for rx, short in _SYNONYMS:
        text = rx.sub(short, text)
    return {t for t in re.findall(r"[a-zçğıöşü0-9+#]+", text) if t not in _STOP and len(t) > 1}


def job_level(title: str, seniority: Optional[str], required_years: float) -> int:
    for rx, level in reversed(_LEVEL_WORDS):  # strongest word wins (head of > lead > senior)
        if rx.search(title or ""):
            return level
    if seniority and seniority.lower() in LEVELS:
        return LEVELS[seniority.lower()]
    if required_years >= 8:
        return 4
    if required_years >= 5:
        return 3
    return 2  # mid-level when nothing says otherwise


def person_level(years: float) -> int:
    return 1 if years < 2 else 2 if years < 5 else 3 if years < 8 else 4 if years < 12 else 5


# ── 2a. how well you match what they ask ─────────────────────────────────

def skill_match(must: list[str], nice: list[str], have: set[str]) -> tuple[float, float, float]:
    """(f_match, must coverage, nice coverage). Earlier must-haves weigh more (postings list the
    important ones first); the curve has no 60%/100% cliff — that rule has no reliable source."""
    if must:
        weights = [max(0.5, 1 - 0.07 * i) for i in range(len(must[:12]))]
        covered = sum(w for w, s in zip(weights, must[:12]) if s in have)
        c_must = covered / sum(weights)
    else:
        c_must = 0.6  # the posting lists none: neutral
    c_nice = (sum(1 for s in nice if s in have) / len(nice)) if nice else 0.5
    return _logistic(10 * (c_must - 0.55)) * (0.9 + 0.1 * c_nice), c_must, c_nice


# Words every role shares: they say nothing about which role it is ("Cryogenics Engineer" is
# not a backend role because both titles end in "Engineer")
_GENERIC = {"engineer", "engineering", "specialist", "expert", "associate", "consultant", "intern", "kıdemli"}
# Role families by the words that name them; a title can touch several
_FAMILY_WORDS = {
    "software": {"software", "backend", "server", "api", "fullstack", "python", "java", "golang", "go", "node",
                 "ruby", "php", "scala", "kotlin", "rust", "c++", "c#", ".net", "dotnet", "programmer", "sde", "swe"},
    "ml": {"ml", "ai", "llm", "nlp", "mlops", "genai", "vision", "deep", "scientist", "research"},
    "data": {"data", "analytics", "analyst", "etl", "bi", "warehouse"},
    "frontend": {"frontend", "ui", "web", "react", "angular", "vue"},
    "devops": {"devops", "sre", "reliability", "infrastructure", "cloud", "platform", "kubernetes", "systems"},
    "mobile": {"mobile", "ios", "android", "flutter"},
    "security": {"security", "appsec", "pentest", "secops"},
}
# Families one step apart: the same skills mostly carry over
_NEAR_FAMILIES = {frozenset(p) for p in (("ml", "data"), ("software", "devops"), ("software", "frontend"),
                                         ("software", "ml"), ("software", "mobile"), ("data", "software"))}


def _families(words: set[str]) -> set[str]:
    return {f for f, ws in _FAMILY_WORDS.items() if words & ws}


def title_match(title: str, targets: list[str]) -> float:
    """Same role 1.0, same or a near role family 0.6, unrelated 0.25 (titles dominate the first
    screen). Shared generic words ("Engineer", "Developer") don't make two roles related."""
    if not targets:
        return 0.8
    words = _tokens(title)
    core = words - _GENERIC
    fam = _families(core)
    best = 0.25
    for t in targets:
        tw = _tokens(t)
        tcore = tw - _GENERIC
        if not tcore:  # the target is only a generic word ("Engineer"): match on it
            if tw and tw <= words:
                best = max(best, 0.6)
            continue
        if tcore <= core:
            return 1.0
        tfam = _families(tcore)
        if len(tcore & core) / len(tcore) >= 0.5 or (fam & tfam):
            best = max(best, 0.6)
        elif any(frozenset((a, b)) in _NEAR_FAMILIES for a in fam for b in tfam):
            best = max(best, 0.4)
    return best


def qualification(sig: Signals, me: Seeker) -> tuple[float, str]:
    """Years short cost ×0.75 each; one level over is fine, two or more look like flight risk."""
    m, note = 1.0, ""
    short = (sig.required_years or 0) - me.years
    if short > 0.5:
        m *= max(0.15, 0.75 ** short)
        note = f"{short:.0f} year(s) short of the {sig.required_years:.0f} asked"
    gap = job_level(sig.title, sig.seniority, sig.required_years) - person_level(me.years)
    if gap <= -2:
        m *= 0.7
        note = note or "well above the level of the role"
    elif gap >= 2:
        m *= 0.6
        note = note or "two levels above your experience"
    return m, note


# ── 2b. when, how crowded, and is it real ────────────────────────────────

def timing(age_days: Optional[int]) -> float:
    if age_days is None or age_days <= 4:
        return 1.0
    return max(0.3, 0.88 ** (age_days - 4))


def p_real(age_days: Optional[int], evergreen: bool) -> float:
    if age_days is None:
        p = 0.85
    elif age_days <= 14:
        p = 0.90
    elif age_days <= 30:
        p = 0.85
    elif age_days <= 60:
        p = 0.70
    elif age_days <= 120:
        p = 0.50
    else:
        p = 0.30
    return p * (0.5 if evergreen else 1.0)


def competition(sig: Signals) -> float:
    m = 1.0
    if sig.remote:
        m = {"worldwide": 0.27, "region": 0.42, "country": 0.85}.get(sig.remote_scope or "", 0.6)
    if sig.company_size == "big_tech":
        m *= 0.6
    return m


# ── 2c. can you legally take it from where you live ──────────────────────

def _country_factor(code: str, sig: Signals, me: Seeker, gates: list[str]) -> float:
    if me.residence and code == me.residence:
        return 1.0
    if not me.needs_sponsorship:
        return 0.9  # free to move there: a small relocation discount
    if sig.sponsors_visa is False:
        gates.append("States no visa sponsorship")
        return 0.0
    offer = sig.offer_usd
    if code == "GB":
        if offer and offer < UK_SPONSOR_FLOOR_USD:
            gates.append("Pay below the UK sponsorship floor (£41,700)")
            return 0.0
        return 0.8 if sig.sponsors_visa else 0.25
    if code == "DE":
        return 0.3 if offer and offer < DE_BLUE_CARD_SHORTAGE_USD else (0.8 if sig.sponsors_visa else 0.7)
    if code == "CH":
        return 0.35 if (sig.relocation or sig.sponsors_visa or sig.company_size in ("large", "big_tech")) else 0.05
    if code == "ES":
        return 0.3 if offer and offer < ES_BLUE_CARD_USD else 0.6
    if code in EU:
        return 0.75 if sig.sponsors_visa else 0.5
    if code == "US":
        return 0.3 if sig.sponsors_visa else 0.08
    return 0.6 if sig.sponsors_visa else 0.4


def market(sig: Signals, me: Seeker, gates: list[str]) -> tuple[float, str]:
    """How realistic the job's location is for someone living in `me.residence`."""
    from careeros.jobs.geo import region_codes

    if sig.remote:
        if sig.remote_scope == "worldwide":
            return 1.0, "Remote, open worldwide"
        if not sig.regions:
            if me.residence and me.residence in sig.countries:
                return 1.0, "Remote, in your country"
            # Only ~2–4% of remote postings truly hire anywhere; most are single-country (often US)
            return (0.35, "Remote, but where you can live isn't stated") if me.residence else (1.0, "Remote")
        if me.residence:
            covered = set()
            for r in sig.regions:
                codes = region_codes(r)
                if codes is None:
                    return 1.0, "Remote, open worldwide"
                covered |= codes
            if me.residence in covered:
                broad = any(r.strip().lower() in ("emea", "europe", "eu") for r in sig.regions)
                return (0.6 if broad else 1.0), ("Remote, open to your country" if not broad else "Remote across EMEA")
            # remote, but only for people living elsewhere: you'd have to move there first
            return 0.1, "Remote only for residents of other countries"
        return 1.0, "Remote"
    if not sig.countries:
        # Where it is isn't known: not a free pass. Someone who needs a visa can't assume it's reachable.
        if not me.residence:
            return 1.0, ""
        if me.needs_sponsorship:
            return 0.4, "Location unclear: check where it's based"
        return 0.8, "Location unclear"
    best = max(_country_factor(c, sig, me, gates) for c in sig.countries)
    note = "" if best >= 0.9 else "Needs a work visa" if best > 0 else ""
    return best, note


def gates_for(sig: Signals, me: Seeker) -> list[str]:
    out = []
    if sig.trust == "risk":
        out.append("Posting shows scam warning signs")
    if not sig.remote:
        if sig.workplace == "onsite" and not me.onsite_ok:
            # the posting says on-site: accepting hybrid doesn't mean accepting the office every day
            out.append("On-site role; you want remote or hybrid" if me.hybrid_ok else "On-site role; you only want remote")
        elif sig.hybrid and not (me.hybrid_ok or me.onsite_ok):
            out.append("Hybrid role; you only want remote")
        elif not sig.hybrid and sig.workplace is None and not me.onsite_ok and not me.hybrid_ok:
            out.append("Not remote; you only want remote")
    missing = [lang for lang in sig.languages_required if me.languages and lang not in me.languages]
    if missing:
        out.append(f"Requires {', '.join(missing).upper()} you haven't listed")
    return out


# ── 3. value of the job if you get it ────────────────────────────────────

def pay_value(offer: Optional[int], ref: Optional[int]) -> float:
    if not offer or not ref:
        return 0.5
    x = math.log(offer / ref)
    k = math.log(1.5)
    return min(1.0, max(0.0, 0.5 + x / (2 * k) if x >= 0 else 0.5 + x / k))


def value(sig: Signals, me: Seeker, c_must: float) -> tuple[float, dict]:
    ref = me.min_salary_usd or sig.market_median_usd
    parts = {"pay": pay_value(sig.offer_usd, ref)}
    missing = len(sig.must) - round(c_must * len(sig.must)) if sig.must else 0
    growth = 0.5 + {"big_tech": 0.15, "large": 0.15, "midsize": 0.05}.get(sig.company_size, 0.0)
    growth += 0.15 if 1 <= missing <= 3 else (-0.1 if missing >= 5 else 0.0)
    if job_level(sig.title, sig.seniority, sig.required_years) - person_level(me.years) == 1:
        growth += 0.1
    parts["growth"] = min(1.0, max(0.0, growth))
    stability = {"startup": 0.35, "midsize": 0.6, "large": 0.8, "big_tech": 0.85}.get(sig.company_size, 0.55)
    stability += {"verified": 0.05, "caution": -0.1}.get(sig.trust, 0.0)
    parts["stability"] = min(1.0, max(0.0, stability))
    if sig.remote:
        style = 1.0 if me.remote_ok else 0.6
    elif sig.hybrid:
        style = 1.0 if me.hybrid_ok else (0.6 if me.remote_ok or me.onsite_ok else 0.2)
    elif sig.workplace == "onsite":
        style = 1.0 if me.onsite_ok else 0.2
    else:  # not remote, arrangement not stated: could be on-site or hybrid
        style = 1.0 if me.onsite_ok else (0.6 if me.hybrid_ok else 0.2)
    parts["work_style"] = style
    weights = {k: max(0.0, float(me.value_weights.get(k, w))) for k, w in VALUE_WEIGHTS.items()}
    total = sum(weights.values()) or 1.0
    v = sum(parts[k] * w for k, w in weights.items()) / total
    if me.min_salary_usd and sig.offer_usd and sig.offer_usd < me.min_salary_usd:
        v = min(v, 0.3)  # below your minimum: the floor rule
        parts["below_minimum"] = True
    return v, parts


# ── 4. putting it together ───────────────────────────────────────────────

def surplus(p: float, v: float, effort: str = "normal") -> float:
    if p <= 0:
        return 0.0
    c = EFFORT_COST.get(effort, EFFORT_COST["normal"])
    return p * SIGMA * _softplus((v - RESERVATION - c / p) / SIGMA)


def to_score(gamma: float) -> float:
    if gamma <= 0:
        return 0.0
    x = (math.log(gamma) - math.log(GAMMA_LO)) / (math.log(GAMMA_HI) - math.log(GAMMA_LO))
    return round(100 * min(1.0, max(0.0, x)), 1)


def recommend(score: float, gates: list[str], p_eff: float) -> str:
    if gates:
        return f"SKIP - {gates[0]}"
    if score >= 75 and p_eff >= 0.01:
        return "APPLY - Strong opportunity"
    if score >= 58:
        return "CONSIDER - Worth a look"
    return "SKIP - Better opportunities available"


def evaluate(sig: Signals, me: Seeker) -> Result:
    gates = gates_for(sig, me)
    f_match, c_must, c_nice = skill_match(sig.must, sig.nice, me.skills)
    m_title = title_match(sig.title, me.target_roles)
    m_qual, qual_note = qualification(sig, me)
    m_time = timing(sig.age_days)
    m_comp = competition(sig)
    m_market, market_note = market(sig, me, gates)
    m_agency = 0.8 if sig.agency else 1.0
    pr = p_real(sig.age_days, sig.evergreen)
    if m_time * pr < 0.1:  # both read posting age: don't let them compound below 0.1
        pr = 0.1 / m_time
    p_int = 0.0 if gates else min(MAX_INTERVIEW, BASE_INTERVIEW * f_match * m_title * m_qual * m_time
                                  * m_comp * m_market * m_agency)
    p_eff = pr * p_int
    v, parts = value(sig, me, c_must)
    gamma = surplus(p_eff, v, me.effort)
    score = min(10.0, to_score(gamma)) if gates else to_score(gamma)
    return Result(
        score=score, recommendation=recommend(score, gates, p_eff), p_interview=p_int, p_real=pr,
        p_effective=p_eff, value=v, gamma=gamma, fit=min(1.0, f_match * m_title * m_qual), gates=gates,
        chance_factors={"skills": round(f_match, 3), "must_coverage": round(c_must, 3), "nice_coverage": round(c_nice, 3),
                        "title": m_title, "experience": round(m_qual, 3), "experience_note": qual_note,
                        "timing": round(m_time, 3), "competition": round(m_comp, 3), "location": round(m_market, 3),
                        "location_note": market_note, "agency": m_agency},
        value_parts={k: (round(x, 3) if isinstance(x, float) else x) for k, x in parts.items()},
    )
