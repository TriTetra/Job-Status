"""Add any job (careeros/jobs/added.py): link or pasted text, read only where allowed, private to its adder."""

import json

import pytest

import careeros.db.models  # noqa: F401  (all mappers, for Job's relationships)
from careeros.jobs import added
from careeros.jobs.models.job import Job

POSTING = {
    "@context": "https://schema.org", "@type": "JobPosting", "title": "Machine Learning Engineer",
    "hiringOrganization": {"@type": "Organization", "name": "Acme AI", "sameAs": "https://acme.ai"},
    "jobLocation": {"@type": "Place", "address": {"addressLocality": "Berlin", "addressCountry": "DE"}},
    "datePosted": "2026-11-20", "employmentType": ["FULL_TIME"],
    "baseSalary": {"currency": "EUR", "value": {"minValue": 70000, "maxValue": 90000, "unitText": "YEAR"}},
    "description": "<p>" + "Build and ship models with Python and PyTorch. " * 12 + "</p>",
}
PAGE = f'<html><head><script type="application/ld+json">{json.dumps({"@graph": [{"@type": "WebPage"}, POSTING]})}</script></head><body>x</body></html>'
TEXT = ("Senior Backend Engineer\nGlobex · Istanbul, Türkiye (Hybrid)\n\nAbout the role\n"
        + "You will design APIs in Go and PostgreSQL and run them on Kubernetes. " * 6)


class _Resp:
    def __init__(self, status=200, body="", kind="text/html"):
        self.status_code, self._body, self.headers = status, body.encode(), {"content-type": kind}
        self.is_redirect, self.encoding = False, "utf-8"

    def iter_content(self, n):
        yield self._body

    def close(self):
        pass


class _Http:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, **kw):
        self.calls.append(url)
        for part, resp in self.routes.items():
            if part in url:
                return resp
        return _Resp(404)


class _Session:
    def __init__(self, rows=()):
        self.rows = {r.url: r for r in rows}

    def get(self, model, key):
        return self.rows.get(key)

    def add(self, row):
        self.rows[row.url] = row

    def flush(self):
        pass


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setattr(added, "check_url", lambda u: u)          # no DNS in tests
    monkeypatch.setattr(added, "_facts", lambda row: None)        # no LLM in tests


def test_links_and_private_keys():
    assert added.normalize("acme.ai/jobs/1#apply") == "https://acme.ai/jobs/1"
    with pytest.raises(added.AddJobError):
        added.normalize("javascript:alert(1)")
    assert added.reading_forbidden("https://www.linkedin.com/jobs/view/1")
    assert added.reading_forbidden("https://www.kariyer.net/is-ilani/x") and added.reading_forbidden("https://de.indeed.com/x")
    assert not added.reading_forbidden("https://boards.greenhouse.io/acme/jobs/1")
    a, b = added.private_key("https://x.io/j", "u1"), added.private_key("https://x.io/j", "u2")
    assert a != b and a.startswith("https://x.io/j#aplio-") and a == added.private_key("https://x.io/j", "u1")


def test_jobposting_from_page_data():
    d = added.jobposting(PAGE)
    f = added.from_jobposting(d)
    assert (f["title"], f["company"], f["location"]) == ("Machine Learning Engineer", "Acme AI", "Berlin, DE")
    assert f["salary"] == (70000, 90000, "EUR") and f["employment_type"] == "FULL_TIME"
    assert f["posted_at"].year == 2026 and f["company_url"] == "https://acme.ai"
    remote = added.from_jobposting({**POSTING, "jobLocationType": "TELECOMMUTE",
                                    "applicantLocationRequirements": {"@type": "Country", "name": "Germany"}})
    assert remote["remote"] is True and remote["location"] == "Remote (Germany)"
    hourly = added.from_jobposting({**POSTING, "baseSalary": {"currency": "EUR", "value": {"value": 50, "unitText": "HOUR"}}})
    assert hourly["salary"] == (None, None, None)


def test_robots_rules():
    ok = _Http({"robots.txt": _Resp(200, "User-agent: *\nDisallow: /private\n", "text/plain")})
    assert added.robots_allows("https://acme.ai/jobs/1", ok)
    assert not added.robots_allows("https://acme.ai/private/1", ok)
    us = _Http({"robots.txt": _Resp(200, "User-agent: AplioBot\nDisallow: /\n", "text/plain")})
    assert not added.robots_allows("https://acme.ai/jobs/1", us)
    assert added.robots_allows("https://acme.ai/jobs/1", _Http({"robots.txt": _Resp(404)}))     # none: allowed
    assert not added.robots_allows("https://acme.ai/jobs/1", _Http({"robots.txt": _Resp(503)}))  # unreachable: not


def test_add_from_a_readable_page_is_private_to_its_adder():
    http = _Http({"robots.txt": _Resp(404), "/jobs/1": _Resp(200, PAGE)})
    s = _Session()
    row = added.add_job(s, "u1", "https://acme.ai/jobs/1", http=http)
    assert row.url == added.private_key("https://acme.ai/jobs/1", "u1") and row.added_by == "u1"
    assert row.application_url == "https://acme.ai/jobs/1" and row.source == "added" and row.company_key is None
    assert (row.title, row.company, row.salary_min, row.salary_currency) == ("Machine Learning Engineer", "Acme AI", 70000, "EUR")
    assert "PyTorch" in row.required_skills or "Python" in row.required_skills
    assert row.company_domain == "acme.ai" and row.content_hash


def test_never_reads_forbidden_sites_and_asks_for_the_text(monkeypatch):
    http = _Http({})
    with pytest.raises(added.AddJobError, match="paste the posting text"):
        added.add_job(_Session(), "u1", "https://www.linkedin.com/jobs/view/42", http=http)
    assert http.calls == []                                       # not even robots.txt

    monkeypatch.setattr(added, "read_header", lambda text: added.PostingHeader(
        title="Senior Backend Engineer", company="Globex", location="Istanbul, Türkiye"))
    row = added.add_job(_Session(), "u1", "https://www.linkedin.com/jobs/view/42", TEXT, http=http)
    assert http.calls == [] and row.title == "Senior Backend Engineer" and row.company == "Globex"
    assert row.application_url == "https://www.linkedin.com/jobs/view/42" and row.description.startswith("Senior Backend")


def test_robots_disallow_and_unreadable_pages_ask_for_the_text():
    no = _Http({"robots.txt": _Resp(200, "User-agent: *\nDisallow: /\n", "text/plain")})
    with pytest.raises(added.AddJobError, match="asks bots not to read"):
        added.add_job(_Session(), "u1", "https://acme.ai/jobs/1", http=no)
    js = _Http({"robots.txt": _Resp(404), "/jobs/1": _Resp(200, "<html><body><div id=root></div></body></html>")})
    with pytest.raises(added.AddJobError, match="JavaScript"):
        added.add_job(_Session(), "u1", "https://acme.ai/jobs/1", http=js)


def test_not_a_posting_is_refused(monkeypatch):
    monkeypatch.setattr(added, "read_header", lambda text: added.PostingHeader(is_job_posting=False))
    with pytest.raises(added.AddJobError, match="one job posting"):
        added.add_job(_Session(), "u1", "https://x.io/j", TEXT, http=_Http({}))
    with pytest.raises(added.AddJobError, match="too short"):
        added.add_job(_Session(), "u1", "https://x.io/j", "Engineer wanted", http=_Http({}))


def test_a_known_shared_job_is_reused_not_copied():
    shared = Job(url="https://boards.greenhouse.io/acme/jobs/1", title="ML Engineer", company="Acme", added_by=None)
    http = _Http({})
    row = added.add_job(_Session([shared]), "u1", "https://boards.greenhouse.io/acme/jobs/1", http=http)
    assert row is shared and http.calls == []


def test_others_never_see_an_added_job():
    from sqlalchemy.dialects import postgresql

    sql = str(Job.visible_to("u1").compile(dialect=postgresql.dialect()))
    assert "added_by IS NULL" in sql and "added_by =" in sql
    assert "=" not in str(Job.visible_to(None).compile(dialect=postgresql.dialect()))

    from careeros.jobs.posting import get_posting

    own = Job(url="https://x.io/j#aplio-1", title="T", company="C", location="", description="d", added_by="u1")
    s = _Session([own])
    assert get_posting(s, own.url, "u2") is None and get_posting(s, own.url) is None
    assert get_posting(s, own.url, "u1")["added"] is True


def test_a_link_on_a_known_job_system_is_read_from_its_api(monkeypatch):
    from careeros.jobs.sources import ats
    from careeros.jobs.sources.ats.base import FetchResult, Posting

    seen = []

    def fake_fetch(board, http, known, keep):
        seen.append((board.ats, board.board))
        return FetchResult(postings=[
            Posting(external_id="111", url="https://job-boards.greenhouse.io/acme/jobs/111", title="Data Engineer",
                    location="Remote - Europe", description="Pipelines in Python and Spark. " * 20),
            Posting(external_id="222", url="https://job-boards.greenhouse.io/acme/jobs/222", title="Designer")])

    monkeypatch.setitem(ats.FETCHERS, "greenhouse", fake_fetch)
    http = _Http({})
    row = added.add_job(_Session(), "u1", "https://boards.greenhouse.io/acme/jobs/111?gh_src=x", http=http)
    assert seen == [("greenhouse", "acme")] and http.calls == []          # the API, not the page
    assert (row.title, row.company, row.location) == ("Data Engineer", "Acme", "Remote - Europe")

    shared = Job(url="https://job-boards.greenhouse.io/acme/jobs/111", title="Data Engineer", company="Acme", added_by=None)
    again = added.add_job(_Session([shared]), "u1", "https://boards.greenhouse.io/acme/jobs/111", http=http)
    assert again is shared                                                  # the same job under its board's link
