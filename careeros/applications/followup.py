"""Follow-ups for applications that wait: a short, evidence-based e-mail draft the person sends.

When: an application still at "applied" with no answer
  - 14 days after it was sent: the first follow-up;
  - 21 days after it was sent and a week after the first follow-up went out: the last one.
Then Aplio stops asking. "Don't follow up" stops it for that application at any point; an
answer (from the mailbox or a move on the board) takes it off the list by itself.

Drafts use only the person's evidence (careeros/applications/kit.py: items with ids, checked
by check_grounding, one repair pass), else a plain template. Aplio never sends them: the person
copies or opens the draft in their mail and marks it sent. Drafts and sends are kept in the
`emails` table (follow_up_1 / follow_up_2; follow_up_skipped means "don't ask again").
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from careeros.applications.models.application import Application
from careeros.applications.models.email import Email

logger = logging.getLogger(__name__)

FIRST_AFTER = timedelta(days=14)
LAST_AFTER = timedelta(days=21)
GAP = timedelta(days=7)
STEPS = {1: "follow_up_1", 2: "follow_up_2"}
SKIPPED = "follow_up_skipped"
MAX_WORDS = {1: 110, 2: 70}


def _aware(d: Optional[datetime]) -> Optional[datetime]:
    return d if d is None or d.tzinfo else d.replace(tzinfo=timezone.utc)


def sent_at(app: Application) -> Optional[datetime]:
    """When the application went out: applied_at, else when it entered "applied"."""
    if app.applied_at:
        return _aware(app.applied_at)
    from careeros.applications.pipeline import since_last_move

    return since_last_move(app) if app.status == "applied" else None


def state(app: Application, emails: list[Email], now: datetime) -> dict:
    """{due: 1 | 2 | None, sent: n, last_sent_at, draft: id of the unsent draft for the due step}."""
    rows = [e for e in emails if e.url == app.url]
    done = sorted((e for e in rows if e.template_type in STEPS.values() and e.sent_at), key=lambda e: e.sent_at)
    skipped = any(e.template_type == SKIPPED for e in rows)
    went = sent_at(app)
    due = None
    if app.status == "applied" and not skipped and went is not None:
        waited = now - went
        if not done and waited >= FIRST_AFTER:
            due = 1
        elif len(done) == 1 and waited >= LAST_AFTER and now - _aware(done[0].sent_at) >= GAP:
            due = 2
    draft = next((e for e in rows if due and e.template_type == STEPS[due] and not e.sent_at), None)
    return {
        "due": due, "sent": len(done), "skipped": skipped,
        "last_sent_at": _aware(done[-1].sent_at).isoformat() if done else None,
        "draft_id": draft.id if draft else None,
        "days_waiting": int((now - went).days) if went else None,
    }


def states(session: Session, user_id: str, apps: list[Application], now: Optional[datetime] = None) -> dict[str, dict]:
    now = now or datetime.now(timezone.utc)
    emails = session.query(Email).filter(Email.user_id == user_id).all()
    return {a.url: state(a, emails, now) for a in apps}


def due(session: Session, user_id: str, now: Optional[datetime] = None) -> list[dict]:
    """Applications with a follow-up due now, longest wait first."""
    now = now or datetime.now(timezone.utc)
    apps = session.query(Application).filter(Application.user_id == user_id, Application.status == "applied").all()
    st = states(session, user_id, apps, now)
    out = [{"url": a.url, "title": a.title, "company": a.company, **st[a.url]} for a in apps if st[a.url]["due"]]
    return sorted(out, key=lambda r: -(r["days_waiting"] or 0))


# ── the draft ────────────────────────────────────────────────────────────

class FollowUp(BaseModel):
    subject: str = ""
    body: str = ""


RULES = (
    "You draft a short follow-up e-mail a job seeker sends about an application that got no answer. "
    "First person, plain and warm, no pressure, no flattery, no clichés.\n"
    "Rules:\n"
    "- Use only facts from THE PERSON'S EVIDENCE; never invent employers, numbers, dates or results.\n"
    "- A tool may be tied to a job or project ONLY if it is listed under that item's \"used:\".\n"
    "- End every sentence that states a fact about the person with the ids it relies on, like [E1] or [P2].\n"
    "- Mention the role and when they applied; give ONE concrete reason they fit, from the evidence; "
    "ask whether there is an update on the timeline; offer to share anything that helps.\n"
    "- {length}\n"
    "- Start with \"Hello,\" (the recipient's name isn't known) and end with \"Best regards,\" and the person's first name.\n"
    "Return JSON: {{\"subject\": \"...\", \"body\": \"...\"}}"
)


def _prompt(ctx: dict, step: int, applied_on: str, evidence: str) -> str:
    kind = "the first follow-up" if step == 1 else "the last, brief check-in (a first follow-up got no answer)"
    return (
        f"This is {kind}.\n"
        f"THE APPLICATION: {ctx.get('title')} at {ctx.get('company')}, applied on {applied_on}.\n"
        f"What the role is about: {(ctx.get('summary') or '')[:400] or 'not available'}\n"
        f"Skills it asks for that the person shows: {', '.join(ctx.get('matched') or []) or 'none listed'}\n"
        f"THE PERSON'S EVIDENCE (ids in brackets)\n{evidence}"
    )


def template(ctx: dict, step: int, applied_on: str, first_name: Optional[str]) -> FollowUp:
    title, company = ctx.get("title") or "the role", ctx.get("company") or "your team"
    matched = [m for m in ctx.get("matched") or [] if m][:2]
    fit = f" My experience with {' and '.join(matched)} fits what the role asks for." if matched else ""
    sign = f"Best regards,\n{first_name}" if first_name else "Best regards,"
    if step == 1:
        body = (f"Hello,\n\nI applied for the {title} role at {company} on {applied_on} and wanted to ask whether "
                f"there is any update on the timeline. I'm still very interested in the position.{fit} "
                f"I'm happy to share anything else that would help.\n\n{sign}")
        return FollowUp(subject=f"Following up on my {title} application", body=body)
    body = (f"Hello,\n\nI'm checking in once more about my application for the {title} role, sent on {applied_on}. "
            f"If the position is still open, I'd be glad to talk; if it has been filled, a short note would help me "
            f"plan. Thank you for your time.\n\n{sign}")
    return FollowUp(subject=f"Checking in: {title} application", body=body)


def _trim(text: str, words: int) -> str:
    """At most `words` words, keeping the paragraph breaks."""
    out, n = [], 0
    for para in text.split("\n"):
        w = para.split()
        if n + len(w) > words + 12:   # greeting and sign-off don't count much
            w = w[:max(0, words + 12 - n)]
        out.append(" ".join(w))
        n += len(w)
    return "\n".join(out).strip()


def write(session: Session, user_id: str, app: Application, step: int, now: datetime) -> tuple[FollowUp, list[str], str]:
    """(draft, claims the evidence doesn't support, "llm" | "template")."""
    from careeros.applications.kit import (
        _job_context, applicant_facts, check_grounding, evidence_brief, evidence_items, strip_citations,
    )
    from careeros.jobs.models.job import Job
    from careeros.shared.llm import get_llm_client

    job = session.get(Job, app.url)
    ctx = _job_context(session, user_id, job) if job else {"title": app.title, "company": app.company}
    ctx["title"], ctx["company"] = app.title or ctx.get("title"), app.company or ctx.get("company")
    went = sent_at(app) or now
    applied_on = f"{went:%B} {went.day}"
    first = applicant_facts(session, user_id).get("first_name")
    items, skills = evidence_items(session, user_id)
    evidence = evidence_brief(items, skills)
    length = f"The body is at most {MAX_WORDS[step]} words."
    try:
        client = get_llm_client()
        kwargs = dict(system=RULES.format(length=length), task="apply_kit", user_id=user_id,
                      temperature=0.3, max_tokens=500)
        d = client.complete_model(_prompt(ctx, step, applied_on, evidence), FollowUp, **kwargs)
        problems = check_grounding(d.body, items, skills)
        if problems:
            fix = (f"This follow-up makes claims the evidence doesn't support: {'; '.join(problems)}. Remove or fix "
                   f"only those; keep the rest.\nTHE PERSON'S EVIDENCE\n{evidence}\nDRAFT\n{d.model_dump_json()}")
            try:
                d = client.complete_model(fix, FollowUp, **kwargs)
                problems = check_grounding(d.body, items, skills)
            except Exception as e:
                logger.info("Follow-up repair failed for %s: %s", user_id, e)
        body = _trim(strip_citations(d.body), MAX_WORDS[step])
        if not body.strip():
            raise ValueError("empty draft")
        return FollowUp(subject=d.subject.strip()[:200] or template(ctx, step, applied_on, first).subject,
                        body=body), problems, "llm"
    except Exception as e:  # no key, budget, bad output: the template, which states nothing unsupported
        logger.info("Follow-up draft from the template for %s: %s", user_id, type(e).__name__)
        return template(ctx, step, applied_on, first), [], "template"


def _dict(e: Email, step: int, check: Optional[list[str]] = None, by: Optional[str] = None) -> dict:
    return {"id": e.id, "url": e.url, "step": step, "subject": e.subject, "body": e.body,
            "generated_at": _aware(e.generated_at).isoformat() if e.generated_at else None,
            "sent_at": _aware(e.sent_at).isoformat() if e.sent_at else None,
            "check": check or [], "drafted_by": by}


def _app(session: Session, user_id: str, url: str) -> Application:
    app = session.query(Application).filter(Application.user_id == user_id, Application.url == url).first()
    if app is None:
        raise LookupError("application not found")
    return app


def draft(session: Session, user_id: str, url: str, *, refresh: bool = False, now: Optional[datetime] = None) -> dict:
    """The draft for the follow-up that is due (kept, so it isn't rewritten each time it is opened)."""
    now = now or datetime.now(timezone.utc)
    app = _app(session, user_id, url)
    emails = session.query(Email).filter(Email.user_id == user_id, Email.url == url).all()
    st = state(app, emails, now)
    step = st["due"]
    if step is None:
        raise ValueError("no follow-up is due for this application")
    existing = next((e for e in emails if e.template_type == STEPS[step] and not e.sent_at), None)
    if existing is not None and not refresh:
        return _dict(existing, step)
    text, problems, by = write(session, user_id, app, step, now)
    row = existing or Email(user_id=user_id, url=url, template_type=STEPS[step], sequence_num=step)
    row.subject, row.body, row.generated_at = text.subject[:500], text.body, now
    session.add(row)
    session.flush()
    return _dict(row, step, problems, by)


def mark_sent(session: Session, user_id: str, email_id: int, now: Optional[datetime] = None) -> dict:
    from careeros.memory.events import job_stream, remember

    now = now or datetime.now(timezone.utc)
    row = session.get(Email, email_id)
    if row is None or row.user_id != user_id or row.template_type not in STEPS.values():
        raise LookupError("draft not found")
    if row.sent_at is None:
        row.sent_at = now
        step = row.sequence_num or 1
        remember(session, user_id, "FollowUpSent", {"url": row.url, "step": step}, stream=job_stream(row.url))
    session.flush()
    return _dict(row, row.sequence_num or 1)


def skip(session: Session, user_id: str, url: str, now: Optional[datetime] = None) -> None:
    """Don't suggest follow-ups for this application again."""
    _app(session, user_id, url)
    exists = session.query(Email).filter(Email.user_id == user_id, Email.url == url,
                                         Email.template_type == SKIPPED).first()
    if exists is None:
        session.add(Email(user_id=user_id, url=url, template_type=SKIPPED, sequence_num=0, subject="", body="",
                          generated_at=now or datetime.now(timezone.utc)))
    session.flush()
