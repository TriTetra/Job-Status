"""Apply kit: everything to send one application, prepared so the person only reviews and submits.

- The form's questions: Greenhouse publishes them (boards-api, `?questions=true`); other job
  systems don't, so a standard set of the questions most forms ask is used.
- Suggested answers from what Aplio knows (name, e-mail, CV, links, sponsorship, salary floor,
  where you live) and short drafts for free-text questions, written only from the person's
  evidence. Legal agreements, demographic questions and anything about the company's AI policy
  are never answered for them.
- The CV to send (the current one; CV variants come with phase 4) and a short note.

Nothing is submitted: submission APIs need the employer's own key, forms are behind CAPTCHAs,
and agreeing to terms is the person's act.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

import requests
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from careeros.applications.models.apply_kit import ApplyKit
from careeros.jobs.models.job import Job

logger = logging.getLogger(__name__)

KIT_VERSION = 1
GREENHOUSE_FORM = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{job_id}?questions=true"
HTTP_TIMEOUT = 10
MAX_COVER_WORDS = 130
MAX_ANSWER_CHARS = 900


class UnknownJob(LookupError):
    pass


# ── what each question is about (by its label) ───────────────────────────

_LEGAL = re.compile(r"arbitrat|agreement|consent|acknowledg|privacy|terms|certif(y|ication that)|attest|gdpr|"
                    r"data (processing|protection)|background check|i understand|i agree|declar", re.I)
_DEMOGRAPHIC = re.compile(r"gender|race|ethnic|veteran|disab|pronoun|sexual orientation|hispanic|latino|"
                          r"demographic|age range|date of birth", re.I)
_AI_POLICY = re.compile(r"\bai\b.{0,20}polic|polic.{0,20}\bai\b|use of (ai|artificial intelligence|generative)|"
                        r"artificial intelligence", re.I)
_AI_RULE_IN_TEXT = re.compile(r"(use|using) (of )?(ai|artificial intelligence|generative ai|chatgpt|llms?|ai tools)"
                              r".{0,60}(application|interview|cover letter|answers)", re.I)
_TOPICS = [
    ("first_name", re.compile(r"^first name|given name|preferred first", re.I)),
    ("last_name", re.compile(r"^last name|family name|surname", re.I)),
    ("full_name", re.compile(r"^(full )?name$", re.I)),
    ("email", re.compile(r"e-?mail", re.I)),
    ("phone", re.compile(r"phone|mobile", re.I)),
    ("cv", re.compile(r"resume|\bcv\b|curriculum", re.I)),
    ("cover_letter", re.compile(r"cover letter|motivation letter", re.I)),
    ("linkedin", re.compile(r"linkedin", re.I)),
    ("github", re.compile(r"github|gitlab", re.I)),
    ("website", re.compile(r"website|portfolio|personal (site|page)|blog", re.I)),
    ("sponsorship", re.compile(r"sponsor|visa", re.I)),
    ("authorized", re.compile(r"authori[sz]ed to work|right to work|work permit|eligible to work|legally", re.I)),
    ("relocation", re.compile(r"relocat|move to", re.I)),
    ("office", re.compile(r"in[- ]person|on[- ]?site|in (the|our) office|office.{0,20}(days|week|time)|hybrid", re.I)),
    ("salary", re.compile(r"salary|compensation|pay expectation|expected (pay|rate)|desired pay", re.I)),
    ("start", re.compile(r"start date|earliest|notice period|when can you start|availability|available to start", re.I)),
    ("location", re.compile(r"where (are you|do you) (based|live)|current location|city|country of residence|"
                            r"address|location", re.I)),
    ("years", re.compile(r"years of (professional )?experience|how many years", re.I)),
    ("heard", re.compile(r"how did you (hear|find)|where did you (hear|find)|referr", re.I)),
    ("before", re.compile(r"(previously|ever|before).{0,30}(work|interview|appl)|(work|interview|appl).{0,30}before", re.I)),
]
_FREE_TEXT = re.compile(r"why|tell us|describe|additional|anything else|motivat|what (excites|interests)|"
                        r"share|example|project|about you", re.I)

# Most forms ask these; used where the job system doesn't publish its form
STANDARD_FORM = [
    {"label": "First Name", "required": True, "fields": [{"type": "input_text"}]},
    {"label": "Last Name", "required": True, "fields": [{"type": "input_text"}]},
    {"label": "Email", "required": True, "fields": [{"type": "input_text"}]},
    {"label": "Phone", "required": False, "fields": [{"type": "input_text"}]},
    {"label": "Resume/CV", "required": True, "fields": [{"type": "input_file"}]},
    {"label": "LinkedIn Profile", "required": False, "fields": [{"type": "input_text"}]},
    {"label": "GitHub or portfolio", "required": False, "fields": [{"type": "input_text"}]},
    {"label": "Will you now or in the future require visa sponsorship?", "required": True, "fields": [{"type": "input_text"}]},
    {"label": "Are you open to relocation?", "required": False, "fields": [{"type": "input_text"}]},
    {"label": "Salary expectation", "required": False, "fields": [{"type": "input_text"}]},
    {"label": "When can you start?", "required": False, "fields": [{"type": "input_text"}]},
    {"label": "Why are you interested in this role?", "required": False, "fields": [{"type": "textarea"}]},
]
_KIND = {"input_text": "text", "textarea": "textarea", "input_file": "file",
         "multi_value_single_select": "select", "multi_value_multi_select": "multiselect"}


def topic_of(label: str) -> Optional[str]:
    for topic, rx in _TOPICS:
        if rx.search(label):
            return topic
    return None


def _pick(options: list[str], wanted: str) -> str:
    """The option that says `wanted` ("Yes" / "No"), else `wanted` itself."""
    for o in options:
        if o.strip().lower().startswith(wanted.lower()):
            return o
    return wanted


def _answer(topic: Optional[str], kind: str, options: list[str], facts: dict, job: dict,
            label: str = "") -> tuple[Optional[str], str, Optional[str]]:
    """(suggested answer, where it comes from, note) for one question. source "you" = the person answers."""
    sponsor = facts.get("requires_sponsorship")
    job_codes = set(job.get("countries") or [])
    if topic == "first_name" and facts.get("first_name"):
        return facts["first_name"], "profile", None
    if topic == "last_name" and facts.get("last_name"):
        return facts["last_name"], "profile", None
    if topic == "full_name" and facts.get("first_name"):
        return " ".join(x for x in (facts.get("first_name"), facts.get("last_name")) if x), "profile", None
    if topic == "email" and facts.get("email"):
        return facts["email"], "profile", None
    if topic == "cv":
        cv = facts.get("cv")
        return ((f"{cv['filename']} (version {cv['version']})", "profile", None) if cv
                else (None, "you", "Upload your CV in Aplio so it can be tracked with this application"))
    if topic == "cover_letter":
        return None, "llm", "A short note is drafted below"
    if topic in ("linkedin", "github", "website"):
        link = (facts.get("links") or {}).get(topic) or ((facts.get("links") or {}).get("github") if topic == "website" else None)
        return (link, "profile", None) if link else (None, "you", None)
    if topic == "sponsorship" and sponsor is not None:
        return _pick(options, "Yes" if sponsor else "No"), "preferences", None
    if topic == "authorized" and sponsor is not None:
        if not sponsor:
            return _pick(options, "Yes"), "preferences", None
        home = facts.get("country_code")
        if home and job_codes and home in job_codes:
            return _pick(options, "Yes"), "preferences", "The job is in the country you live in"
        return _pick(options, "No"), "preferences", "You need sponsorship for this country; check the exact wording"
    if topic == "relocation":
        targets = set(facts.get("preferred_country_codes") or [])
        if job_codes and job_codes & targets:
            return _pick(options, "Yes"), "preferences", "It's in one of your target countries"
        return None, "you", None
    if topic == "office":
        wa = set(facts.get("work_arrangements") or [])
        if "onsite" in wa or "hybrid" in wa:
            return _pick(options, "Yes"), "preferences", "You accept hybrid or on-site work; check how many days"
        return _pick(options, "No"), "preferences", "You chose remote only"
    if topic == "salary" and facts.get("salary_min"):
        amount = f"{int(facts['salary_min']):,} {facts.get('salary_currency') or ''}".strip()
        text = f"From {amount} a year" + (", negotiable" if facts.get("salary_negotiable") else "")
        return text, "preferences", "Your minimum; adjust to the role and country"
    if topic == "start":
        return None, "you", "For example: \"Two weeks after an offer\""
    if topic == "location" and facts.get("country"):
        return facts["country"], "profile", "Add your city if they ask for it"
    if topic == "years" and facts.get("years") is not None:
        return str(facts["years"]), "profile", None
    if topic == "heard":
        return _pick(options, "Company website"), "suggestion", None
    if topic == "before":
        return None, "you", None
    if kind == "textarea" or (kind == "text" and _FREE_TEXT.search(label)):
        return None, "llm", None
    return None, "you", None


def map_questions(raw: list[dict], facts: dict, job: dict) -> tuple[list[dict], bool]:
    """Form questions → [{id, label, kind, required, options, suggested, source, note}], and whether
    the form asks about AI use (then nothing is drafted)."""
    out, ai_policy = [], False
    for i, q in enumerate(raw):
        fields = [f for f in q.get("fields") or [] if f.get("type") != "input_hidden"]
        if not fields:
            continue
        label = " ".join(str(q.get("label") or "").split())[:300]
        types = [f.get("type") for f in fields]
        kind = next((_KIND[t] for t in types if t in _KIND and t != "textarea"), None) or _KIND.get(types[0], "text")
        if "input_file" in types:
            kind = "file"
        options = [str(v.get("label")) for f in fields for v in (f.get("values") or []) if v.get("label")][:30]
        item = {"id": f"q{i}", "label": label, "kind": kind, "required": bool(q.get("required")), "options": options}
        if _AI_POLICY.search(label):
            ai_policy = True
            item.update(suggested=None, source="you", note="The company sets rules on using AI in applications: read them and answer yourself")
        elif _LEGAL.search(label):
            item.update(suggested=None, source="you", note="A legal agreement: read it and answer it yourself")
        elif _DEMOGRAPHIC.search(label):
            item.update(suggested=None, source="you", note="Voluntary and personal: your choice")
        else:
            topic = topic_of(label)
            suggested, source, note = _answer(topic, kind, options, facts, job, label)
            item.update(suggested=suggested, source=source, note=note)
        out.append(item)
    return out, ai_policy


# ── where the form comes from ────────────────────────────────────────────

_GH_URL = re.compile(r"greenhouse\.io/(?:embed/job_app\?for=)?([A-Za-z0-9_-]+)/jobs/(\d+)")
_GH_ID = re.compile(r"(?:gh_jid=|/jobs/)(\d+)")


def greenhouse_ref(job: Job, boards: dict[str, str]) -> Optional[tuple[str, str]]:
    """(board token, job id) for a Greenhouse posting, from the board list or the URL."""
    if (job.ats or "") != "greenhouse":
        return None
    m = _GH_URL.search(job.url or "")
    board = boards.get(job.company_key or "") or (m.group(1) if m else None)
    job_id = job.external_id or (m.group(2) if m else None)
    if not job_id:
        mi = _GH_ID.search(job.url or "")
        job_id = mi.group(1) if mi else None
    return (board, str(job_id)) if board and job_id else None


def fetch_greenhouse_form(board: str, job_id: str) -> Optional[list[dict]]:
    """The posting's questions (public API); None if it can't be read."""
    try:
        r = requests.get(GREENHOUSE_FORM.format(board=board, job_id=job_id), timeout=HTTP_TIMEOUT,
                         headers={"User-Agent": "Aplio/1.0 (job application helper)"})
        if r.status_code != 200:
            return None
        data = r.json()
        return (data.get("questions") or []) + (data.get("location_questions") or [])
    except (requests.RequestException, ValueError):
        return None


def _boards(session: Session) -> dict[str, str]:
    from careeros.jobs.boards import all_boards

    try:
        return {b.key: b.board for b in all_boards(session) if b.ats == "greenhouse"}
    except Exception:
        return {}


# ── who is applying ──────────────────────────────────────────────────────

def _display(name: Optional[str]) -> Optional[str]:
    """"ABDULLOKH" (as read from a CV) → "Abdullokh"; mixed case is kept."""
    name = (name or "").strip()
    return (name.title() if name.isupper() else name) or None


def applicant_facts(session: Session, user_id: str) -> dict:
    """What Aplio may fill in for the person: name, e-mail, links, preferences, CV, where they live."""
    from careeros.identity.models.connected_account import ConnectedAccount
    from careeros.identity.models.user import User
    from careeros.jobs.geo import countries_in
    from careeros.jobs.opportunities import _person_facts
    from careeros.memory.cv import current_cv

    facts = _person_facts(session, user_id)
    user = session.get(User, user_id)
    data = (user.profile_data or {}) if user else {}
    first = data.get("first_name") or (user.first_name if user else None)
    last = data.get("last_name") or (user.last_name if user else None)
    facts.update(
        first_name=_display(first), last_name=_display(last),
        email=user.email if user else None,
        cv=current_cv(session, user_id),
        country_code=(countries_in(facts.get("country") or "") or [(None, None)])[0][0],
    )
    from careeros.identity.models.career_preferences import CareerPreferences

    prefs = session.query(CareerPreferences).filter(CareerPreferences.user_id == user_id).first()
    facts["salary_negotiable"] = bool(getattr(prefs, "salary_negotiable", False)) if prefs else False
    links: dict[str, str] = {}
    for acc in session.query(ConnectedAccount).filter(ConnectedAccount.user_id == user_id,
                                                      ConnectedAccount.is_active.is_(True)).all():
        url = (acc.account_metadata or {}).get("url")
        if acc.provider == "github" and acc.provider_username:
            links["github"] = url or f"https://github.com/{acc.provider_username}"
        elif acc.provider == "portfolio" and acc.provider_username:
            links["website"] = acc.provider_username
        elif acc.provider == "linkedin" and url:
            links["linkedin"] = url
    for key in ("linkedin", "website", "github"):
        if data.get(f"{key}_url") and key not in links:
            links[key] = data[f"{key}_url"]
    facts["links"] = links
    return facts


def evidence_brief(session: Session, user_id: str, limit: int = 25) -> str:
    """The person's evidence as short lines for a drafting prompt (experience, projects, results, skills)."""
    from careeros.evidence.items import list_for_review

    g = list_for_review(session, user_id)
    lines = []
    for kind in ("experiences", "projects", "achievements", "certifications", "education"):
        for it in g.get(kind, [])[:6]:
            text = " ".join(str(it.get("evidence_text") or "").split())[:220]
            lines.append(f"- {kind[:-1]}: {it['name']}" + (f" — {text}" if text else ""))
    skills = [s["name"] for s in g.get("skills", [])[:limit]]
    if skills:
        lines.append("- skills: " + ", ".join(skills))
    return "\n".join(lines) or "- (no evidence yet)"


# ── drafts (LLM, evidence only) ──────────────────────────────────────────

class Drafts(BaseModel):
    cover_note: str = ""
    answers: dict[str, str] = Field(default_factory=dict)


DRAFT_RULES = (
    "You draft parts of a job application for the person, in first person, in plain English.\n"
    "Rules:\n"
    "- Use only facts from THE PERSON'S EVIDENCE. Never invent employers, numbers, dates, degrees or results.\n"
    "- If a question can't be answered from the evidence, return an empty string for it.\n"
    f"- cover_note: at most {MAX_COVER_WORDS} words: why this role, two concrete matches from the evidence, "
    "one honest line on a gap if there is a big one. No greetings or sign-off, no clichés.\n"
    "- Each answer: at most 120 words, specific to this company and role.\n"
    "Return JSON: {\"cover_note\": \"...\", \"answers\": {\"<question id>\": \"...\"}}"
)


def draft_prompt(job: dict, questions: list[dict], evidence: str, facts: dict) -> str:
    asked = "\n".join(f"- {q['id']}: {q['label']}" for q in questions) or "- (none)"
    return (
        "THE JOB\n"
        f"- {job.get('title')} at {job.get('company')} — {job.get('location') or 'location not stated'}\n"
        f"- Summary: {(job.get('summary') or '')[:600] or 'not available'}\n"
        f"- Skills it asks for: {', '.join(job.get('required_skills') or []) or 'not listed'}\n"
        f"- Skills the person shows of those: {', '.join(job.get('matched') or []) or 'none'}\n"
        f"- Skills the person doesn't show yet: {', '.join(job.get('gaps') or []) or 'none'}\n"
        "THE PERSON'S EVIDENCE\n"
        f"{evidence}\n"
        f"- target role: {', '.join(facts.get('target_roles') or []) or 'not stated'}; "
        f"years of experience: {facts.get('years') if facts.get('years') is not None else 'not stated'}\n"
        "QUESTIONS TO DRAFT\n"
        f"{asked}"
    )


def draft_texts(job: dict, questions: list[dict], evidence: str, facts: dict, user_id: str) -> Optional[Drafts]:
    from careeros.shared.llm import LLMError, get_llm_client

    try:
        d = get_llm_client().complete_model(draft_prompt(job, questions, evidence, facts), Drafts, system=DRAFT_RULES,
                                            task="apply_kit", user_id=user_id, temperature=0.3, max_tokens=1200)
    except (LLMError, Exception) as e:  # no key, over budget, provider down: the person writes these
        logger.info("Apply kit drafts unavailable for %s: %s", user_id, e)
        return None
    words = d.cover_note.split()
    d.cover_note = " ".join(words[:MAX_COVER_WORDS])
    d.answers = {k: v.strip()[:MAX_ANSWER_CHARS] for k, v in d.answers.items() if isinstance(v, str)}
    return d


# ── the kit ──────────────────────────────────────────────────────────────

def _job_context(session: Session, user_id: str, job: Job) -> dict:
    from careeros.jobs.geo import countries_in
    from careeros.jobs.models.career_score import CareerScore

    score = (session.query(CareerScore).filter(CareerScore.user_id == user_id, CareerScore.url == job.url).first())
    ex = (score.explanation or {}) if score else {}
    facts = job.llm_facts or {}
    return {
        "title": job.title, "company": job.company, "location": job.location,
        "countries": [c for c, _ in countries_in(job.location)],
        "summary": ex.get("summary") or facts.get("summary"),
        "required_skills": ex.get("required_skills") or facts.get("required_skills") or job.required_skills or [],
        "matched": [m.get("name") for m in ex.get("matched_skills") or [] if isinstance(m, dict)],
        "gaps": (score.skill_gaps or []) if score else [],
        "score": score.career_score if score else None,
        "p_interview": (ex.get("model") or {}).get("p_effective"),
        "trust": ex.get("trust"),
    }


def get_kit(session: Session, user_id: str, url: str) -> Optional[dict]:
    row = session.get(ApplyKit, (user_id, url))
    return row.payload if row else None


def build_kit(session: Session, user_id: str, url: str, *, refresh: bool = False, draft: bool = True,
              now: Optional[datetime] = None) -> dict:
    """Prepare (or return the stored) kit for this job. Never submits anything."""
    from careeros.memory.events import job_stream, remember

    job = session.get(Job, url)
    if job is None:
        raise UnknownJob(url)
    row = session.get(ApplyKit, (user_id, url))
    if row and not refresh and row.content_hash == job.content_hash and (row.payload or {}).get("v") == KIT_VERSION:
        return row.payload

    now = now or datetime.now(timezone.utc)
    facts = applicant_facts(session, user_id)
    ctx = _job_context(session, user_id, job)
    raw, form = None, "standard"
    ref = greenhouse_ref(job, _boards(session))
    if ref:
        raw = fetch_greenhouse_form(*ref)
        form = "greenhouse" if raw else "standard"
    questions, ai_policy = map_questions(raw or STANDARD_FORM, facts, ctx)
    ai_policy = ai_policy or bool(_AI_RULE_IN_TEXT.search(job.description or job.full_description or ""))

    warnings = []
    if ai_policy:
        warnings.append("This company sets rules on using AI in applications. Aplio drafted nothing: write the "
                        "free-text answers and the note yourself.")
    trust = ctx.get("trust") or {}
    if trust.get("level") in ("risk", "caution") or trust.get("agency"):
        warnings.extend(trust.get("concerns") or [])
    if not facts.get("cv"):
        warnings.append("No CV uploaded to Aplio: upload it so each application records which CV you sent.")

    drafts = None
    to_draft = [q for q in questions if q["source"] == "llm"]
    if draft and not ai_policy:
        from careeros.jobs.scan import load_profile

        try:
            profile = load_profile(user_id)
            facts["target_roles"] = list(getattr(profile, "target_roles", None) or [])
        except Exception:
            facts["target_roles"] = []
        drafts = draft_texts(ctx, to_draft, evidence_brief(session, user_id), facts, user_id)
    for q in questions:
        if q["source"] == "llm":
            text = (drafts.answers.get(q["id"]) if drafts else None) or None
            q.update(suggested=text, source="draft" if text else "you",
                     note=q.get("note") if text else ("Write this yourself" if ai_policy or not drafts
                                                      else "Not enough in your evidence to draft this"))

    payload: dict[str, Any] = {
        "v": KIT_VERSION, "url": url, "title": job.title, "company": job.company, "location": job.location,
        "apply_url": job.application_url or url, "form": form, "cv": facts.get("cv"),
        "score": ctx.get("score"), "p_interview": ctx.get("p_interview"),
        "matched": ctx.get("matched"), "gaps": ctx.get("gaps"),
        "warnings": warnings, "ai_policy": ai_policy, "questions": questions,
        "cover_note": drafts.cover_note if drafts and drafts.cover_note else None,
        "drafted": bool(drafts), "created_at": now.isoformat(),
    }
    if row is None:
        row = ApplyKit(user_id=user_id, url=url)
        session.add(row)
    row.payload, row.content_hash, row.created_at = payload, job.content_hash, now
    remember(session, user_id, "KitPrepared", {"url": url, "title": job.title, "company": job.company, "form": form,
                                               "questions": len(questions), "drafted": bool(drafts),
                                               "ai_policy": ai_policy}, stream=job_stream(url), actor="agent:apply_kit")
    session.flush()
    return payload
