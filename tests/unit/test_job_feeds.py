"""Job feeds and board discovery: link parsing, the HN comment format, the new ATS readers."""

from types import SimpleNamespace

import pytest

from careeros.jobs.discovery import FoundBoard, board_from_url, boards_in, company_site, key_for
from careeros.jobs.sources.ats import FETCHERS, Board
from careeros.jobs.sources.feeds import hackernews
from careeros.jobs.sources.feeds.base import yearly


@pytest.mark.parametrize("url, expected", [
    ("https://jobs.ashbyhq.com/acme-ai/5b0d?utm_source=hn", FoundBoard("ashby", "acme-ai")),
    ("https://jobs.ashbyhq.com/Acme%20Labs", FoundBoard("ashby", "Acme Labs")),
    ("https://job-boards.greenhouse.io/acme/jobs/123", FoundBoard("greenhouse", "acme")),
    ("https://job-boards.eu.greenhouse.io/controlplane/jobs/5017247101", FoundBoard("greenhouse", "controlplane")),
    ("https://boards.greenhouse.io/embed/job_board?for=acme", FoundBoard("greenhouse", "acme")),
    ("https://jobs.lever.co/acme/abc-123", FoundBoard("lever", "acme")),
    ("https://jobs.eu.lever.co/acme", FoundBoard("lever", "acme", "api.eu.lever.co")),
    ("https://acme.jobs.personio.de/job/1", FoundBoard("personio", "acme", "acme.jobs.personio.de")),
    ("https://acme-gmbh.jobs.personio.com", FoundBoard("personio", "acme-gmbh", "acme-gmbh.jobs.personio.com")),
    ("https://acme.recruitee.com/o/ml-engineer", FoundBoard("recruitee", "acme")),
    ("https://apply.workable.com/acme/j/ABC123/", FoundBoard("workable", "acme")),
    ("https://jobs.smartrecruiters.com/CERN/744000162453369", FoundBoard("smartrecruiters", "CERN")),
    # not boards
    ("https://apply.workable.com/j/2FAA7C0BC6", None),
    ("https://www.recruitee.com/pricing", None),
    ("https://jobs.ashbyhq.com/", None),
    ("https://example.com/careers", None),
    ("not a url", None),
])
def test_board_from_url(url, expected):
    assert board_from_url(url) == expected


def test_boards_in_dedupes_and_company_site_skips_job_sites():
    urls = ["https://jobs.lever.co/acme/1", "https://jobs.lever.co/acme/2", "https://news.ycombinator.com/item?id=1"]
    assert boards_in(urls) == [FoundBoard("lever", "acme")]
    assert company_site(["https://jobs.lever.co/acme", "https://www.linkedin.com/x", "https://www.acme.ai/about"]) == "acme.ai"


def test_key_for_avoids_clashes():
    assert key_for(FoundBoard("ashby", "Acme Labs"), set()) == "acme-labs"
    assert key_for(FoundBoard("ashby", "stripe"), {"stripe"}) == "stripe-ashby"
    assert key_for(FoundBoard("ashby", "stripe"), {"stripe", "stripe-ashby"}) == "stripe-ashby-2"


def test_hn_comment_parses_company_role_and_board_link():
    c = {"id": 42, "author": "founder", "created_at": "2026-11-02T16:01:43Z",
         "text": "Acme AI (YC W25) | Senior ML Engineer | Berlin, London | REMOTE (EU) | VISA<p>We build agents."
                 " Apply: <a href=\"https:&#x2F;&#x2F;jobs.ashbyhq.com&#x2F;acme-ai\">jobs.ashbyhq.com&#x2F;acme-ai</a>"
                 " or see https://acme.ai"}
    p = hackernews.parse_comment(c)
    assert p.company == "Acme AI"
    assert p.title == "Senior ML Engineer"
    assert "Berlin, London" in p.location and "REMOTE (EU)" in p.location
    assert p.remote is True
    assert p.url == "https://news.ycombinator.com/item?id=42"
    assert p.apply_url == "https://jobs.ashbyhq.com/acme-ai"
    assert FoundBoard("ashby", "acme-ai") in boards_in(p.links)


def test_hn_comment_without_the_pipe_format_is_skipped():
    assert hackernews.parse_comment({"id": 1, "author": "x", "text": "Great thread, thanks!"}) is None
    assert hackernews.parse_comment({"id": 2, "author": None, "text": "A | B"}) is None


def test_yearly_salary_only():
    assert yearly(90000, 120000, "EUR", "annual") == (90000, 120000, "EUR")
    assert yearly(40, 60, "USD", "hour") == (None, None, None)
    assert yearly(None, None, "USD", "") == (None, None, None)


class _Resp:
    def __init__(self, payload=None, content=b""):
        self._payload, self.content, self.status_code = payload, content, 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


class _Http:
    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def get(self, url, params=None, **kw):
        self.calls.append(url)
        for prefix, resp in self.routes.items():
            if url.startswith(prefix):
                return resp
        raise AssertionError(f"unexpected GET {url}")


def test_personio_reader_builds_urls_and_text():
    xml = b"""<?xml version="1.0"?><workzag-jobs><position><id>7</id><office>Berlin</office>
      <department>AI</department><name>ML Engineer (m/f/d)</name>
      <jobDescriptions><jobDescription><name>Your role</name><value><![CDATA[<p>Train models</p>]]></value></jobDescription></jobDescriptions>
      <employmentType>permanent</employmentType><schedule>full-time</schedule><createdAt>2026-11-11T17:43:42+00:00</createdAt>
      </position></workzag-jobs>"""
    board = Board("acme", "Acme", "personio", board="acme", host="acme.jobs.personio.com")
    r = FETCHERS["personio"](board, _Http({"https://acme.jobs.personio.com/xml": _Resp(content=xml)}), set())
    p = r.postings[0]
    assert p.url == "https://acme.jobs.personio.com/job/7?language=en"
    assert p.title == "ML Engineer (m/f/d)" and p.location == "Berlin"
    assert "Your role" in p.description and "Train models" in p.description


def test_recruitee_and_workable_readers():
    offer = {"id": 5, "status": "published", "title": "AI Engineer", "careers_url": "https://acme.recruitee.com/o/ai",
             "careers_apply_url": "https://acme.recruitee.com/o/ai/c/new", "description": "<p>Build</p>", "requirements": "<p>Python</p>",
             "remote": True, "locations": [{"name": "Amsterdam, Netherlands"}], "published_at": "2026-11-20 11:15:31 UTC",
             "salary": {"min": "70000", "max": "90000", "period": "year", "currency": "EUR"}}
    r = FETCHERS["recruitee"](Board("acme", "Acme", "recruitee", board="acme"),
                              _Http({"https://acme.recruitee.com/api/offers/": _Resp({"offers": [offer]})}), set())
    p = r.postings[0]
    assert (p.remote, p.salary_min, p.salary_max, p.salary_currency) == (True, 70000, 90000, "EUR")
    assert p.posted_at.year == 2026 and "Python" in p.description

    job = {"title": "LLM Engineer (remote, Europe)", "shortcode": "AB12", "url": "https://apply.workable.com/j/AB12",
           "application_url": "https://apply.workable.com/j/AB12/apply", "telecommuting": True, "description": "<p>Agents</p>",
           "locations": [{"city": "Tallinn", "country": "Estonia"}], "published_on": "2026-10-02"}
    r = FETCHERS["workable"](Board("modash", "Modash", "workable", board="modash"),
                             _Http({"https://apply.workable.com/api/v1/widget/accounts/modash": _Resp({"jobs": [job]})}), set())
    assert r.postings[0].location == "Tallinn, Estonia" and r.postings[0].remote is True


def test_smartrecruiters_reads_details_only_for_relevant_new_postings():
    listing = {"totalFound": 3, "content": [
        {"id": "1", "name": "ML Engineer", "ref": "https://api.smartrecruiters.com/v1/companies/ACME/postings/1"},
        {"id": "2", "name": "Office Manager", "ref": "https://api.smartrecruiters.com/v1/companies/ACME/postings/2"},
        {"id": "3", "name": "Data Engineer", "ref": "https://api.smartrecruiters.com/v1/companies/ACME/postings/3"},
    ]}
    detail = {"id": "1", "name": "ML Engineer", "location": {"city": "Zurich", "country": "ch", "remote": True},
              "jobAd": {"sections": {"jobDescription": {"title": "About", "text": "<p>Models</p>"}}}, "releasedDate": "2026-11-20T07:44:55Z"}
    http = _Http({"https://api.smartrecruiters.com/v1/companies/ACME/postings/1": _Resp(detail),
                  "https://api.smartrecruiters.com/v1/companies/ACME/postings": _Resp(listing)})
    known = {"https://jobs.smartrecruiters.com/ACME/3"}
    r = FETCHERS["smartrecruiters"](Board("acme", "Acme", "smartrecruiters", board="ACME"), http, known,
                                    lambda t: "engineer" in t.lower())
    assert [p.title for p in r.postings] == ["ML Engineer"]          # 2 filtered by title, 3 already stored
    assert r.postings[0].location == "Zurich, CH" and r.postings[0].remote is True
    assert len(r.seen_urls) == 3 and r.complete


def test_feed_row_keeps_link_back_and_no_board_key():
    from careeros.jobs.feeds import dedupe_key, to_row
    from careeros.jobs.sources.feeds.base import FeedPosting

    extract = SimpleNamespace(is_remote=lambda l, d: True, salary=lambda d: (None, None), required_years=lambda t, d: None,
                              company_size=lambda n: None, remote_region=lambda l, d: "Europe", sponsors_visa=lambda d: None,
                              skills=lambda d, t: ["Python"])
    p = FeedPosting(source="remotive", external_id="9", url="https://remotive.com/remote-jobs/x-9", title="ML Engineer",
                    company="Acme", location="Europe", description="Python", apply_url="javascript:alert(1)")
    row = to_row(p, extract)
    assert row["source"] == "feed" and row["site"] == "remotive"
    assert row["company_key"] is None                      # board syncs must never close it
    assert row["application_url"] == p.url                 # unsafe links are dropped, the feed page is kept
    assert dedupe_key("  ACME ", "ML  Engineer") == dedupe_key("acme", "ml engineer")
