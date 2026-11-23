"""Decision Contract v1 — deterministic decision layer.

Produces explanation["decision"]:
  semantic   → tier / label / secondary   (system voice, sans)
  criteria[] → confirmed | conflict | unknown  (epistemic states)
  next_action→ apply | investigate | skip  (decision engine)
reasoning (serif narrator) is filled on-demand by /api/jobs/reasoning/{url}
with an LLM, falling back to template_reasoning().
"""

import re
import logging
from typing import Any, Dict, List, Optional, Tuple

from careeros.shared.llm import get_llm_client

logger = logging.getLogger(__name__)


# ── Vocabulary lock (English product voice) ──────────────────────────────
TIER_LABELS = {"strong": "Strong match", "look": "Worth a look", "low": "Low fit"}

_REASON_NOUNS = {
    "work_style": "work arrangement",
    "location": "location",
    "compensation": "salary",
    "visa": "visa status",
}

_COUNTRY_NAMES = [
    ("United States", "US"), ("Canada", "CA"), ("Mexico", "MX"),
    ("Germany", "DE"), ("United Kingdom", "GB"), ("France", "FR"),
    ("Netherlands", "NL"), ("Switzerland", "CH"), ("Sweden", "SE"),
    ("Norway", "NO"), ("Denmark", "DK"), ("Finland", "FI"), ("Spain", "ES"),
    ("Portugal", "PT"), ("Italy", "IT"), ("Poland", "PL"), ("Austria", "AT"),
    ("Belgium", "BE"), ("Ireland", "IE"), ("Czech Republic", "CZ"),
    ("Estonia", "EE"), ("Romania", "RO"), ("Hungary", "HU"), ("Ukraine", "UA"),
    ("United Arab Emirates", "AE"), ("Saudi Arabia", "SA"), ("Turkey", "TR"),
    ("Israel", "IL"), ("Qatar", "QA"), ("Uzbekistan", "UZ"), ("Kazakhstan", "KZ"),
    ("Azerbaijan", "AZ"), ("Georgia", "GE"), ("Singapore", "SG"), ("Japan", "JP"),
    ("South Korea", "KR"), ("Australia", "AU"), ("New Zealand", "NZ"),
    ("India", "IN"), ("China", "CN"), ("Hong Kong", "HK"), ("Taiwan", "TW"),
    ("Vietnam", "VN"), ("Indonesia", "ID"), ("Thailand", "TH"), ("Malaysia", "MY"),
    ("Philippines", "PH"), ("Brazil", "BR"), ("Argentina", "AR"),
    ("Colombia", "CO"), ("Chile", "CL"), ("South Africa", "ZA"),
    ("Nigeria", "NG"), ("Kenya", "KE"), ("Egypt", "EG"),
]

_EUROPE_CODES = {
    "DE", "GB", "FR", "NL", "CH", "SE", "NO", "DK", "FI", "ES", "PT", "IT",
    "PL", "AT", "BE", "IE", "CZ", "EE", "RO", "HU", "UA",
}

_US_STATE_RE = re.compile(r",\s*(CA|NY|TX|WA|MA|IL|CO|GA|NC|VA|AZ|FL|OH|PA|OR|UT|NV)\b")


# ── semantic ─────────────────────────────────────────────────────────────

def derive_tier(recommendation: Optional[str], career_score: float) -> str:
    rec = (recommendation or "").split(" - ")[0].strip().upper()
    if rec == "APPLY":
        return "strong"
    if rec == "SKIP":
        return "low"
    if rec == "CONSIDER":
        return "look"
    # fallback when recommendation missing
    return "strong" if (career_score or 0) >= 75 else "look" if (career_score or 0) >= 60 else "low"


def _secondary(career_value: float, market_demand: float) -> Optional[str]:
    if (career_value or 0) >= 70:
        return "High career value"
    if (career_value or 0) >= 50:
        return "Solid career value"
    if (market_demand or 0) >= 70:
        return "In-demand role"
    return None


# ── location helpers ─────────────────────────────────────────────────────

def _country_from_location(location: Optional[str]) -> Optional[Tuple[str, str]]:
    if not location or location == "Unknown":
        return None
    lo = location.lower()
    for name, code in _COUNTRY_NAMES:
        if name.lower() in lo:
            return (code, name)
    if _US_STATE_RE.search(location):
        return ("US", "United States")
    return None


def _region_covers(region: Optional[str], preferred: List[str]) -> Optional[bool]:
    """True/False/None(unknown) — does a remote region cover preferred markets?"""
    if not region:
        return None
    r = str(region).strip().lower()
    if r in ("worldwide", "global", "anywhere"):
        return True if preferred else None
    if r in ("us", "usa", "united states"):
        return "US" in preferred
    if r in ("europe", "eu", "emea", "european union"):
        return bool(_EUROPE_CODES & set(preferred))
    return None


def _location_criterion(job: Dict[str, Any], pref_countries: List[str]) -> Dict[str, str]:
    from careeros.jobs.geo import countries_in, location_match

    remote = job.get("remote") is True or "remote" in str(job.get("location") or "").lower()
    regions = job.get("remote_regions") or ([job["remote_region"]] if job.get("remote_region") else [])
    named = countries_in(job.get("location"))
    if remote and regions:
        shown = ", ".join(regions[:3]) + (f" +{len(regions) - 3}" if len(regions) > 3 else "")
        where = f"Remote ({shown})"
    elif named:
        where = ", ".join(name for _, name in named[:2])
    else:
        where = "Remote" if remote else ""
    raw = str(job.get("location") or "").strip()
    if not where and raw and raw.lower() != "unknown":
        # named, but not a place we recognise: say what the posting says instead of "not stated"
        return {"key": "location", "label": "Location", "state": "unknown", "detail": f"{raw[:60]} — check the country"}
    if not pref_countries:
        detail = f"{where} — set your target markets in Settings" if where else "Not stated"
        return {"key": "location", "label": "Location", "state": "unknown", "detail": detail}
    match = location_match(job.get("location"), regions, pref_countries, remote)
    if match is True:
        return {"key": "location", "label": "Location", "state": "confirmed", "detail": f"{where} — in your target markets"}
    if match is False:
        return {"key": "location", "label": "Location", "state": "conflict", "detail": f"{where} — outside your target markets"}
    return {"key": "location", "label": "Location", "state": "unknown", "detail": f"{where} — unclear for your markets" if where else "Not stated"}


# ── criteria matrix ──────────────────────────────────────────────────────

def build_criteria(job: Dict[str, Any], prefs: Dict[str, Any]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    wa = prefs.get("work_arrangements") or []
    remote = job.get("remote")

    # work_style — always shown
    if remote is True:
        if not wa:
            out.append({"key": "work_style", "label": "Work style", "state": "unknown", "detail": "Set in Settings"})
        elif "remote" in wa:
            out.append({"key": "work_style", "label": "Work style", "state": "confirmed", "detail": "Remote — matches your preference"})
        else:
            out.append({"key": "work_style", "label": "Work style", "state": "conflict", "detail": "Remote role, but you didn't select remote"})
    elif remote is False:
        # what the posting says: on-site and hybrid are different answers
        wp = job.get("workplace") or ("hybrid" if job.get("hybrid") else None)
        if not wa:
            out.append({"key": "work_style", "label": "Work style", "state": "unknown", "detail": "Set in Settings"})
        elif wp == "onsite":
            if "onsite" in wa:
                out.append({"key": "work_style", "label": "Work style", "state": "confirmed", "detail": "On-site — within your selection"})
            else:
                out.append({"key": "work_style", "label": "Work style", "state": "conflict",
                            "detail": "On-site every day; you chose " + " or ".join(w for w in ("remote", "hybrid") if w in wa)})
        elif wp == "hybrid":
            if "hybrid" in wa or "onsite" in wa:
                out.append({"key": "work_style", "label": "Work style", "state": "confirmed", "detail": "Hybrid — within your selection"})
            else:
                out.append({"key": "work_style", "label": "Work style", "state": "conflict", "detail": "Hybrid role conflicts with your remote-only preference"})
        elif "onsite" in wa:
            out.append({"key": "work_style", "label": "Work style", "state": "confirmed", "detail": "Not remote — within your selection"})
        elif "hybrid" in wa:
            out.append({"key": "work_style", "label": "Work style", "state": "unknown", "detail": "Not remote; on-site or hybrid isn't stated"})
        else:
            out.append({"key": "work_style", "label": "Work style", "state": "conflict", "detail": "Not remote; you want remote only"})
    else:
        out.append({"key": "work_style", "label": "Work style", "state": "unknown", "detail": "Not stated"})

    # location — always shown (careeros/jobs/geo.py, the same rule the score uses)
    out.append(_location_criterion(job, prefs.get("preferred_country_codes") or []))

    # compensation — shown if either side has a number (compared in USD a year)
    from careeros.shared.money import to_usd_year

    u_min = to_usd_year(prefs.get("salary_min"), prefs.get("salary_currency") or "USD") if prefs.get("salary_min") else None
    j_min = to_usd_year(job.get("salary_min"), job.get("salary_currency") or "USD") if job.get("salary_min") else None
    j_max = to_usd_year(job.get("salary_max"), job.get("salary_currency") or "USD") if job.get("salary_max") else None
    has_job_salary = j_min is not None or j_max is not None
    has_user_range = u_min is not None or prefs.get("salary_max") is not None
    if has_job_salary or has_user_range:
        if not has_job_salary:
            out.append({"key": "compensation", "label": "Compensation", "state": "unknown", "detail": "Not disclosed"})
        elif u_min is not None and (j_max or j_min or 0) >= u_min:
            out.append({"key": "compensation", "label": "Compensation", "state": "confirmed", "detail": "Meets your minimum"})
        elif u_min is not None:
            out.append({"key": "compensation", "label": "Compensation", "state": "conflict", "detail": "Below your minimum"})
        else:
            out.append({"key": "compensation", "label": "Compensation", "state": "unknown", "detail": "Set your range in Settings"})

    # visa — shown only when the user needs sponsorship
    if prefs.get("requires_sponsorship") is True:
        sv = job.get("sponsors_visa")
        if sv is True:
            out.append({"key": "visa", "label": "Visa", "state": "confirmed", "detail": "Sponsorship offered"})
        elif sv is False:
            out.append({"key": "visa", "label": "Visa", "state": "conflict", "detail": "No sponsorship"})
        else:
            out.append({"key": "visa", "label": "Visa", "state": "unknown", "detail": "Not stated"})

    return out


# ── next action (decision engine) ────────────────────────────────────────

def build_next_action(tier: str, criteria: List[Dict[str, str]]) -> Dict[str, str]:
    conflicts = [c for c in criteria if c["state"] == "conflict"]
    unknowns = [c for c in criteria if c["state"] == "unknown"]

    if tier == "low":
        return {"type": "skip", "label": "Skip", "reason": "Low fit against your profile."}
    if conflicts and tier != "strong":
        return {"type": "skip", "label": "Skip", "reason": f"{conflicts[0]['label']} conflicts with your preferences."}
    if len(unknowns) >= 2:
        a = _REASON_NOUNS.get(unknowns[0]["key"], unknowns[0]["label"].lower())
        b = _REASON_NOUNS.get(unknowns[1]["key"], unknowns[1]["label"].lower())
        return {"type": "investigate", "label": "Investigate first", "reason": f"{a.capitalize()} and {b} are unclear."}
    if tier == "strong" and not conflicts:
        return {"type": "apply", "label": "Apply now", "reason": "Strong fit, low uncertainty."}
    if tier == "look" and not unknowns:
        return {"type": "apply", "label": "Apply now", "reason": "Solid fit — worth applying."}
    if tier == "look":
        noun = _REASON_NOUNS.get(unknowns[0]["key"], unknowns[0]["label"].lower())
        return {"type": "investigate", "label": "Investigate first", "reason": f"Worth a look once {noun} is clear."}
    return {"type": "investigate", "label": "Investigate first", "reason": "Strong fit, but one preference conflicts."}


# ── reasoning: template fallback + on-demand LLM ─────────────────────────

def template_reasoning(
    tier: str,
    job: Dict[str, Any],
    criteria: List[Dict[str, str]],
    matched_skills: List[Any],
    gap_skills: List[str],
) -> str:
    company = job.get("company") or "this team"
    top = None
    if matched_skills:
        m0 = matched_skills[0]
        top = m0.get("name") if isinstance(m0, dict) else str(m0)

    unknowns = [c for c in criteria if c["state"] == "unknown"]
    conflicts = [c for c in criteria if c["state"] == "conflict"]
    unc = ""
    if unknowns:
        noun = _REASON_NOUNS.get(unknowns[0]["key"], unknowns[0]["label"].lower())
        unc = f" The main open question is {noun}, which the posting doesn't state."
    elif conflicts:
        unc = f" The one friction point: {conflicts[0]['detail']}."

    if tier == "strong":
        lead = (
            f"A strong technical fit — your {top} experience maps directly to what {company} needs."
            if top else f"A strong fit — your background maps directly to what {company} needs."
        )
    elif tier == "look":
        lead = (
            f"Worth a look — your {top} gives you a real edge at {company}, though the fit isn't airtight."
            if top else f"Worth a look at {company}, though the fit isn't airtight."
        )
    else:
        gap = gap_skills[0] if gap_skills else None
        lead = (
            f"This one is a stretch — the role leans on {gap} more than your evidence shows."
            if gap else "This one is a stretch against your current evidence."
        )
    return (lead + unc).strip()


REASONING_RULES = (
    "You are Aplio's career copilot. First check the job's facts against the person's facts, then write "
    "2-3 sentences in second person (\"you\", \"your\") on whether this job is worth their time.\n"
    "Rules:\n"
    "- Use only the facts given. Never claim something they don't state; say \"not stated\" instead.\n"
    "- If the facts conflict with each other or with Aplio's verdict (for example an on-site job when they want "
    "remote or hybrid, a country they'd need a visa for, a level far above their experience, pay below their "
    "minimum), lead with that conflict plainly.\n"
    "- Then one concrete positive from their evidence, and the single biggest open question.\n"
    "- No lists, no headers, never say \"the candidate\"."
)


def _fmt_pay(ex: Dict[str, Any]) -> str:
    lo, hi, cur = ex.get("salary_min"), ex.get("salary_max"), ex.get("salary_currency") or ""
    if not lo and not hi:
        return "not stated"
    return f"{lo or '?'}–{hi or '?'} {cur} a year".strip()


def reasoning_prompt(ex: Dict[str, Any], decision: Dict[str, Any], matched: List[Any], gaps: List[str],
                     person: Optional[Dict[str, Any]] = None) -> str:
    """The posting's own facts and the person's, side by side, plus Aplio's verdict to check."""
    from careeros.jobs.geo import countries_in

    person = person or {}
    names = [m.get("name") if isinstance(m, dict) else str(m) for m in matched[:5]]
    model = ex.get("model") or {}
    cf = model.get("chance_factors") or {}
    codes = [c for c, _ in countries_in(ex.get("location"))]
    workplace = ex.get("workplace") or ("remote" if ex.get("remote") else "not stated")
    visa = {True: "offered", False: "not offered"}.get(ex.get("sponsors_visa"), "not stated")
    crit_lines = "\n".join(f"  - {c['label']}: {c['state']} ({c['detail']})" for c in decision.get("criteria") or [])
    chance = model.get("p_effective")
    return (
        "THE JOB (as posted)\n"
        f"- Role: {ex.get('title') or 'Unknown'} at {ex.get('company') or 'Unknown'}\n"
        f"- Location: {ex.get('location') or 'not stated'} (countries: {', '.join(codes) or 'not recognised'})\n"
        f"- Workplace: {workplace}"
        + (f"; remote open to: {', '.join((ex.get('remote_regions') or [])[:6])}" if ex.get("remote_regions") else "")
        + "\n"
        f"- Pay: {_fmt_pay(ex)}\n"
        f"- Visa sponsorship: {visa}\n"
        f"- Experience asked: {cf.get('experience_note') or 'within range or not stated'}\n"
        f"- Skills you show that it asks for: {', '.join(names) or 'none matched'}\n"
        f"- Skills it asks for that your evidence doesn't show: {', '.join(gaps[:8]) or 'none'}\n"
        "THE PERSON\n"
        f"- Lives in: {person.get('country') or 'not stated'}; needs visa sponsorship: "
        f"{ {True: 'yes', False: 'no'}.get(person.get('requires_sponsorship'), 'not stated') }\n"
        f"- Wants to work: {', '.join(person.get('work_arrangements') or []) or 'not stated'}; "
        f"target countries: {', '.join(person.get('preferred_country_codes') or []) or 'not stated'}\n"
        f"- Experience: {person.get('years') if person.get('years') is not None else 'not stated'} years"
        + (f" ({person['level']})" if person.get("level") else "") + "\n"
        f"- Minimum pay: {person.get('salary_min') or 'not set'} {person.get('salary_currency') or ''}".rstrip() + "\n"
        "APLIO'S VERDICT (check it)\n"
        f"- {decision.get('semantic', {}).get('label', 'n/a')}"
        + (f"; score {model.get('score')}" if model.get("score") is not None else "")
        + (f"; chance of an interview {chance * 100:.1f}%" if isinstance(chance, (int, float)) else "")
        + (f"; location: {cf.get('location_note')}" if cf.get("location_note") else "")
        + (f"; ruled out: {'; '.join(model.get('gates'))}" if model.get("gates") else "") + "\n"
        f"- Checklist:\n{crit_lines}"
    )


def _llm_reasoning(ex: Dict[str, Any], decision: Dict[str, Any], matched: List[Any], gaps: List[str],
                   user_id: Optional[str] = None, person: Optional[Dict[str, Any]] = None) -> str:
    return get_llm_client().complete(
        reasoning_prompt(ex, decision, matched, gaps, person),
        system=REASONING_RULES + "\nYou write calm, precise, editorial prose. Return plain text only.",
        task="reasoning",
        user_id=user_id,
        temperature=0.2,
        max_tokens=260,
    )


def reasoning_for(ex: Dict[str, Any], decision: Dict[str, Any], matched: List[Any], gaps: List[str],
                  user_id: Optional[str] = None, person: Optional[Dict[str, Any]] = None) -> Tuple[str, str]:
    """Try LLM (locked prompt); fall back to template (no key, over budget, error). Returns (text, source)."""
    try:
        return _llm_reasoning(ex, decision, matched, gaps, user_id, person), "llm"
    except Exception as e:
        logger.info("[reasoning] LLM unavailable (%s) — using template", e)
        return (
            template_reasoning(decision["semantic"]["tier"], ex, decision["criteria"], matched, gaps),
            "template",
        )


# ── contract root ────────────────────────────────────────────────────────

def build_decision(
    recommendation: Optional[str],
    career_score: float,
    career_value: float,
    market_demand: float,
    job: Dict[str, Any],
    prefs: Dict[str, Any],
    matched_skills: Optional[List[Any]] = None,
    gap_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    tier = derive_tier(recommendation, career_score or 0)
    criteria = build_criteria(job or {}, prefs or {})
    return {
        "v": 1,
        "semantic": {
            "tier": tier,
            "label": TIER_LABELS[tier],
            "secondary": _secondary(career_value or 0, market_demand or 0),
        },
        "criteria": criteria,
        "next_action": build_next_action(tier, criteria),
        "reasoning": None,
        "reasoning_source": None,
        "generated_at": None,
    }
