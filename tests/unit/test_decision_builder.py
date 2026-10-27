"""Decision Contract v1 — pure, deterministic layer (no LLM calls here)."""

import pytest

from services.job_intelligence.application.decision_builder import (
    build_criteria,
    build_decision,
    build_next_action,
    derive_tier,
    template_reasoning,
)


def _state(criteria, key):
    return next(c["state"] for c in criteria if c["key"] == key)


@pytest.mark.parametrize(
    "recommendation, score, expected",
    [
        ("APPLY - strong overlap", 10, "strong"),
        ("consider", 99, "look"),
        ("SKIP", 99, "low"),
        (None, 80, "strong"),
        (None, 65, "look"),
        (None, 10, "low"),
        ("", None, "low"),
    ],
)
def test_derive_tier(recommendation, score, expected):
    assert derive_tier(recommendation, score) == expected


def test_work_style_matches_preference():
    criteria = build_criteria({"remote": True}, {"work_arrangements": ["remote"]})
    assert _state(criteria, "work_style") == "confirmed"


def test_work_style_conflict_for_onsite_when_remote_only():
    criteria = build_criteria({"remote": False}, {"work_arrangements": ["remote"]})
    assert _state(criteria, "work_style") == "conflict"


def test_work_style_unknown_without_preferences():
    criteria = build_criteria({"remote": True}, {})
    assert _state(criteria, "work_style") == "unknown"


def test_location_country_in_target_market():
    criteria = build_criteria({"location": "Berlin, Germany"}, {"preferred_country_codes": ["DE"]})
    assert _state(criteria, "location") == "confirmed"


def test_location_us_state_resolves_to_us():
    criteria = build_criteria({"location": "Austin, TX"}, {"preferred_country_codes": ["DE"]})
    assert _state(criteria, "location") == "conflict"


def test_remote_region_europe_covers_eu_country():
    criteria = build_criteria(
        {"location": "Remote", "remote_region": "Europe"}, {"preferred_country_codes": ["NL"]}
    )
    assert _state(criteria, "location") == "confirmed"


def test_compensation_below_minimum_is_conflict():
    criteria = build_criteria({"salary_min": 50_000, "salary_max": 60_000}, {"salary_min": 90_000})
    assert _state(criteria, "compensation") == "conflict"


def test_compensation_hidden_when_neither_side_has_numbers():
    criteria = build_criteria({}, {})
    assert all(c["key"] != "compensation" for c in criteria)


def test_visa_only_shown_when_sponsorship_required():
    assert all(c["key"] != "visa" for c in build_criteria({"sponsors_visa": True}, {}))
    criteria = build_criteria({"sponsors_visa": False}, {"requires_sponsorship": True})
    assert _state(criteria, "visa") == "conflict"


def test_next_action_low_tier_is_skip():
    assert build_next_action("low", [])["type"] == "skip"


def test_next_action_strong_without_conflicts_is_apply():
    assert build_next_action("strong", [{"key": "location", "label": "Location", "state": "confirmed"}])["type"] == "apply"


def test_next_action_two_unknowns_is_investigate():
    criteria = [
        {"key": "work_style", "label": "Work style", "state": "unknown"},
        {"key": "location", "label": "Location", "state": "unknown"},
    ]
    assert build_next_action("strong", criteria)["type"] == "investigate"


def test_build_decision_shape():
    decision = build_decision("APPLY", 90, 75, 40, {"remote": True}, {"work_arrangements": ["remote"]})
    assert decision["v"] == 1
    assert decision["semantic"] == {"tier": "strong", "label": "Strong match", "secondary": "High career value"}
    assert decision["next_action"]["type"] == "apply"


def test_template_reasoning_mentions_top_skill_and_company():
    text = template_reasoning("strong", {"company": "Acme"}, [], [{"name": "Python"}], [])
    assert "Python" in text and "Acme" in text
