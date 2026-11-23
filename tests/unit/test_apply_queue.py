"""Ready to apply (B): apply kits, the daily queue, the daily report."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

import careeros.db.models  # noqa: F401  (every model registered, as in the app)

from careeros.applications import kit as k
from careeros.applications import queue as q
from careeros.applications import report as rep

FACTS = {"first_name": "Ada", "last_name": "Test", "email": "ada@example.test", "requires_sponsorship": True,
         "work_arrangements": ["remote", "hybrid"], "preferred_country_codes": ["GB", "PL"], "salary_min": 40000,
         "salary_currency": "EUR", "salary_negotiable": True, "country": "Uzbekistan", "country_code": "UZ",
         "years": 3, "cv": {"filename": "cv.pdf", "version": 2, "ref": "doc:1@v2"},
         "links": {"github": "https://github.com/ada"}}


def gh(label, ftype="input_text", required=False, values=None):
    return {"label": label, "required": required, "fields": [{"type": ftype, "values": [{"label": v} for v in values or []]}]}


def mapped(*questions, job=None):
    out, ai = k.map_questions(list(questions), FACTS, job or {"countries": ["PL"]})
    return {x["label"]: x for x in out}, ai


# ── the kit ──────────────────────────────────────────────────────────────

def test_profile_facts_are_filled_in():
    qs, _ = mapped(gh("First Name"), gh("Email"), gh("Resume/CV", "input_file"), gh("Website"))
    assert qs["First Name"]["suggested"] == "Ada" and qs["First Name"]["source"] == "profile"
    assert qs["Email"]["suggested"] == "ada@example.test"
    assert qs["Resume/CV"]["suggested"] == "cv.pdf (version 2)" and qs["Resume/CV"]["kind"] == "file"
    assert qs["Website"]["suggested"] == "https://github.com/ada"


def test_preferences_answer_sponsorship_office_and_salary():
    qs, _ = mapped(gh("Do you require visa sponsorship?", "multi_value_single_select", values=["Yes", "No"]),
                   gh("Are you open to working in-person in one of our offices 25% of the time?",
                      "multi_value_single_select", values=["Yes", "No"]),
                   gh("What are your salary expectations?"),
                   gh("Are you open to relocation?", "multi_value_single_select", values=["Yes", "No"]))
    assert qs["Do you require visa sponsorship?"]["suggested"] == "Yes"
    assert qs["Are you open to working in-person in one of our offices 25% of the time?"]["suggested"] == "Yes"
    assert qs["What are your salary expectations?"]["suggested"] == "From 40,000 EUR a year, negotiable"
    assert qs["Are you open to relocation?"]["suggested"] == "Yes"   # Poland is a target country


def test_work_authorisation_depends_on_the_country():
    q_ = gh("Are you legally authorized to work in the country of this job?", "multi_value_single_select", values=["Yes", "No"])
    abroad, _ = mapped(q_, job={"countries": ["PL"]})
    home, _ = mapped(q_, job={"countries": ["UZ"]})
    assert next(iter(abroad.values()))["suggested"] == "No"
    assert next(iter(home.values()))["suggested"] == "Yes"


def test_legal_demographic_and_ai_policy_are_never_answered():
    qs, ai = mapped(gh("Please read the arbitration agreement below", "multi_value_single_select", True, ["I agree"]),
                    gh("Gender", "multi_value_single_select", values=["Woman", "Man"]),
                    gh("AI Policy for Application", "multi_value_single_select", True, ["Yes"]))
    assert ai is True
    for x in qs.values():
        assert x["suggested"] is None and x["source"] == "you" and x["note"]


def test_free_text_questions_are_drafted_others_left_to_you():
    qs, _ = mapped(gh("Why Anthropic?", "textarea"), gh("When can you start?"), gh("Phone"),
                   gh("Have you ever interviewed here before?", "multi_value_single_select", values=["Yes", "No"]))
    assert qs["Why Anthropic?"]["source"] == "llm"
    assert qs["When can you start?"]["source"] == "you" and "offer" in qs["When can you start?"]["note"]
    assert qs["Phone"]["source"] == "you"
    assert qs["Have you ever interviewed here before?"]["suggested"] is None


def test_greenhouse_reference_from_url_and_board_list():
    job = SimpleNamespace(ats="greenhouse", company_key="acme", external_id=None,
                          url="https://job-boards.greenhouse.io/acme/jobs/123")
    assert k.greenhouse_ref(job, {}) == ("acme", "123")
    custom = SimpleNamespace(ats="greenhouse", company_key="nuro", external_id="8122990",
                             url="https://nuro.ai/careersitem?gh_jid=8122990")
    assert k.greenhouse_ref(custom, {"nuro": "nuro"}) == ("nuro", "8122990")
    assert k.greenhouse_ref(SimpleNamespace(ats="lever", company_key="x", external_id="1", url="u"), {}) is None


def test_drafts_use_only_evidence_and_are_trimmed(monkeypatch):
    prompt = k.draft_prompt({"title": "AI Engineer", "company": "Acme", "matched": ["Python"], "gaps": ["AWS"]},
                            [{"id": "q3", "label": "Why Acme?"}], "- project: Sentropy", {"years": 3})
    assert "THE PERSON'S EVIDENCE" in prompt and "- project: Sentropy" in prompt and "q3: Why Acme?" in prompt
    assert "Never invent" in k.DRAFT_RULES

    class Fake:
        def complete_model(self, prompt, schema, **kw):
            assert kw["task"] == "apply_kit"
            return schema(cover_note="word " * 400, answers={"q3": "x" * 5000})

    monkeypatch.setattr("careeros.shared.llm.get_llm_client", lambda: Fake())
    d = k.draft_texts({}, [], "", {}, "u")
    assert len(d.cover_note.split()) == k.MAX_COVER_WORDS and len(d.answers["q3"]) == k.MAX_ANSWER_CHARS


def test_ai_rules_in_the_posting_text_are_noticed():
    assert k._AI_RULE_IN_TEXT.search("Please don't use AI tools to write your application answers.")
    assert not k._AI_RULE_IN_TEXT.search("You will build AI tools for our customers.")


# ── the queue ────────────────────────────────────────────────────────────

NOW = datetime(2026, 11, 23, tzinfo=timezone.utc)


def score(rec="APPLY - fit", value=80, gates=None, trust=None):
    return SimpleNamespace(recommendation=rec, career_score=value,
                           explanation={"model": {"gates": gates or []}, "trust": trust or {"level": "verified"}})


def job(days=3):
    return SimpleNamespace(posted_at=NOW - timedelta(days=days), discovered_at=None)


@pytest.mark.parametrize("s, j, ok", [
    (score(), job(), True),
    (score(rec="SKIP"), job(), False),
    (score(value=50), job(), False),
    (score(gates=["On-site role"]), job(), False),
    (score(trust={"level": "risk"}), job(), False),
    (score(trust={"level": "ok", "agency": True}), job(), False),
    (score(), job(days=60), False),                         # probably filled by now
])
def test_queue_eligibility(s, j, ok):
    assert q.eligible(s, j, NOW) is ok


# ── the report ───────────────────────────────────────────────────────────

def test_silence_lowers_the_chance_of_an_answer():
    p = 0.08
    assert rep.chance_after_silence(p, 0) == pytest.approx(p)
    assert rep.chance_after_silence(p, 6) < p * 0.6        # half the replies come within ~6 days
    assert rep.chance_after_silence(p, 30) < rep.chance_after_silence(p, 10) < rep.chance_after_silence(p, 3)
    assert 0.45 < rep.replied_by(6) < 0.55


@pytest.mark.parametrize("days, label", [(3, "waiting"), (15, "follow up"), (25, "probably ghosted"),
                                         (50, "closed (no answer)"), (None, "waiting")])
def test_waiting_labels(days, label):
    assert rep.waiting_label(days) == label


def test_report_text_is_short_and_escaped():
    r = {"date": "2026-11-23", "sent_this_week": 2, "active": [
        {"company": "A&B", "state": "waiting", "days": 4, "chance_now": 0.012}],
        "queue": [{"title": "AI <Engineer>", "company": "Clera", "score": 89.2}], "learn": [{"skill": "LLM", "jobs": 17}],
        "new_good_matches": 3}
    t = rep.report_text(r, "https://app.test")
    assert "1 ready to apply" in t and "AI &lt;Engineer&gt;" in t and "A&amp;B" in t
    assert "1.2% chance of an answer" in t and "Learn next:</b> LLM" in t and "https://app.test/apply" in t
