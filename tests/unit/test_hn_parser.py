"""HN 'Who is hiring?' comment parser.

The xfail(strict=True) tests document known bugs: they fail today, and will
start "passing" (→ XPASS → test failure) once the bug is fixed, forcing the
marker to be removed.
"""

import pytest

from plugins.market_signals.hackernews.who_is_hiring_parser import WhoIsHiringParser


@pytest.fixture
def parser():
    return WhoIsHiringParser()


def test_pipe_format_extracts_company_role_and_remote(parser):
    out = parser.parse_comment({
        "id": 123,
        "text": "Acme Corp | Senior Backend Engineer | REMOTE (US) | Python, PostgreSQL, Kubernetes",
    })
    assert out["company"] == "Acme Corp"
    assert out["role"] == "Senior Backend Engineer"
    assert out["remote"] is True
    assert {"Python", "PostgreSQL", "Kubernetes"} <= set(out["skills"])
    assert out["url"] == "https://news.ycombinator.com/item?id=123"


def test_html_is_stripped(parser):
    out = parser.parse_comment({"id": 1, "text": "Foo<p>We use <i>Rust</i> &amp; Go"})
    assert "<" not in out["description"]
    assert "Rust" in out["skills"]


def test_empty_comment_returns_empty_dict(parser):
    assert parser.parse_comment({"id": 1, "text": ""}) == {}


@pytest.mark.xfail(strict=True, reason="known bug: substring matching ('good' → Go, 'storage' → RAG)")
def test_no_false_positive_skills_from_plain_words(parser):
    out = parser.parse_comment({"id": 1, "text": "Good people. Interested? We do storage."})
    assert out["skills"] == []


@pytest.mark.xfail(strict=True, reason="known bug: 'no visa sponsorship' is read as sponsoring")
def test_negated_visa_is_not_sponsorship(parser):
    out = parser.parse_comment({"id": 1, "text": "Acme | Engineer | Onsite | No visa sponsorship"})
    assert out["sponsors_visa"] is False
