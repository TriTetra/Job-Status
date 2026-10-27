"""Decision Contract v1 — deterministic decision layer.

Produces explanation["decision"]:
  semantic   → tier / label / secondary   (system voice, sans)
  criteria[] → confirmed | conflict | unknown  (epistemic states)
  next_action→ apply | investigate | skip  (decision engine)
reasoning (serif narrator) is filled on-demand by /api/jobs/reasoning/{url}
with an LLM, falling back to template_reasoning().
"""

import os
import re
import logging
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.environ.get("DEFAULT_MODEL", "openai/gpt-4o-mini")

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
        if not wa:
            out.append({"key": "work_style", "label": "Work style", "state": "unknown", "detail": "Set in Settings"})
        elif "onsite" in wa or "hybrid" in wa:
            out.append({"key": "work_style", "label": "Work style", "state": "confirmed", "detail": "On-site — within your selection"})
        else:
            out.append({"key": "work_style", "label": "Work style", "state": "conflict", "detail": "On-site role conflicts with your remote-only preference"})
    else:
        out.append({"key": "work_style", "label": "Work style", "state": "unknown", "detail": "Not stated"})

    # location — always shown
    pref_countries = prefs.get("preferred_country_codes") or []
    c = _country_from_location(job.get("location"))
    if c:
        code, name = c
        if not pref_countries:
            out.append({"key": "location", "label": "Location", "state": "unknown", "detail": f"{name} — set your target markets in Settings"})
        elif code in pref_countries:
            out.append({"key": "location", "label": "Location", "state": "confirmed", "detail": f"{name} — target market"})
        else:
            out.append({"key": "location", "label": "Location", "state": "conflict", "detail": f"{name} — outside your target markets"})
    else:
        region = job.get("remote_region")
        covers = _region_covers(region, pref_countries)
        if covers is True:
            out.append({"key": "location", "label": "Location", "state": "confirmed", "detail": f"Remote ({region}) — covers your markets"})
        elif covers is False:
            out.append({"key": "location", "label": "Location", "state": "conflict", "detail": f"Remote ({region}) — outside your target markets"})
        else:
            out.append({"key": "location", "label": "Location", "state": "unknown", "detail": "Not stated"})

    # compensation — shown if either side has a number
    u_min = prefs.get("salary_min")
    j_min, j_max = job.get("salary_min"), job.get("salary_max")
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


def _llm_reasoning(ex: Dict[str, Any], decision: Dict[str, Any], matched: List[Any], gaps: List[str]) -> str:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    names = [m.get("name") if isinstance(m, dict) else str(m) for m in matched[:3]]
    crit_lines = "\n".join(f"- {c['label']}: {c['state']} ({c['detail']})" for c in decision["criteria"])
    prompt = (
        "You are the career copilot of a product called Aplio. Write 2-3 sentences in second person "
        "(\"your\") explaining why this opportunity is or isn't worth the user's attention. Include one "
        "concrete positive and, if present, one uncertainty. No lists, no headers, never say \"the candidate\".\n"
        f"Role: {ex.get('title') or 'Unknown'} at {ex.get('company') or 'Unknown'}\n"
        f"System verdict: {decision['semantic']['label']}\n"
        f"Criteria:\n{crit_lines}\n"
        f"Strongest evidence: {', '.join(names) or 'n/a'}\n"
        f"Gaps: {', '.join(gaps) or 'none'}\n"
        f"Career value: {ex.get('career_value')} / Market demand: {ex.get('market_demand')}"
    )
    resp = requests.post(
        OPENROUTER_URL,
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You write calm, precise, editorial prose. Return plain text only."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
            "max_tokens": 220,
        },
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://applypilot.local",
            "X-Title": "Aplio",
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def reasoning_for(ex: Dict[str, Any], decision: Dict[str, Any], matched: List[Any], gaps: List[str]) -> Tuple[str, str]:
    """Try LLM (locked prompt); fall back to template. Returns (text, source)."""
    try:
        return _llm_reasoning(ex, decision, matched, gaps), "llm"
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
