"""Company boards: ATS parsers, text extraction, board config, incremental sync (all offline)."""

import pytest

from careeros.jobs import ingest
from careeros.jobs.boards import BoardConfigError, TitleFilter, load_boards, parse
from careeros.jobs.extraction import TextExtractor
from careeros.jobs.sources.ats import ashby, greenhouse, lever, workday
from careeros.jobs.sources.ats.base import Board, FetchResult, Posting, html_to_text


class FakeHTTP:
    """requests.Session stand-in: routes by URL substring, records calls."""

    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def _resp(self, url, payload):
        class R:
            def raise_for_status(self):
                pass

            def json(self):
                return payload(url) if callable(payload) else payload
        return R()

    def get(self, url, timeout=None):
        self.calls.append(("GET", url))
        return self._resp(url, next(v for k, v in self.routes.items() if k in url))

    def post(self, url, json=None, timeout=None):
        self.calls.append(("POST", url, json))
        return self._resp(json, next(v for k, v in self.routes.items() if k in url))


# ── parsers ───────────────────────────────────────────────────────────────

def test_greenhouse_parses_escaped_html_and_department():
    payload = {"jobs": [{
        "id": 42, "absolute_url": "https://boards.greenhouse.io/acme/jobs/42", "title": " Backend Engineer ",
        "location": {"name": "Berlin"}, "content": "&lt;p&gt;Build &amp;amp; ship&lt;/p&gt;&lt;ul&gt;&lt;li&gt;Python&lt;/li&gt;&lt;/ul&gt;",
        "departments": [{"name": "Engineering"}], "first_published": "2026-10-01T10:00:00-04:00",
    }]}
    [p] = greenhouse.fetch(Board("acme", "Acme", "greenhouse", board="acme"), FakeHTTP({"greenhouse": payload}), set()).postings
    assert p.external_id == "42" and p.title == "Backend Engineer" and p.location == "Berlin"
    assert "Build & ship" in p.description and "Python" in p.description and "<" not in p.description
    assert p.department == "Engineering" and p.posted_at.utcoffset() is not None


def test_lever_joins_sections_and_reads_workplace_and_salary():
    payload = [{
        "id": "abc", "text": "Data Engineer", "hostedUrl": "https://jobs.lever.co/acme/abc",
        "applyUrl": "https://jobs.lever.co/acme/abc/apply", "categories": {"location": "Remote", "team": "Data", "commitment": "Full-time"},
        "descriptionPlain": "Intro.", "lists": [{"text": "Requirements", "content": "<li>SQL</li>"}],
        "additionalPlain": "Benefits.", "createdAt": 1792767640768, "workplaceType": "remote",
        "salaryRange": {"min": 120000, "max": 150000, "currency": "USD"},
    }]
    [p] = lever.fetch(Board("acme", "Acme", "lever", board="acme"), FakeHTTP({"lever": payload}), set()).postings
    assert p.apply_url.endswith("/apply") and p.remote is True
    assert "Requirements:\nSQL" in p.description and p.description.endswith("Benefits.")
    assert (p.salary_min, p.salary_max, p.salary_currency) == (120000, 150000, "USD")


def test_ashby_skips_unlisted_and_reads_compensation():
    payload = {"jobs": [
        {"id": "1", "title": "ML Engineer", "jobUrl": "https://jobs.ashbyhq.com/acme/1", "location": "NYC",
         "secondaryLocations": [{"location": "SF"}], "isRemote": False, "descriptionPlain": "Hi",
         "compensation": {"summaryComponents": [
             {"compensationType": "EquityPercentage", "minValue": 0.1},
             {"compensationType": "Salary", "interval": "1 YEAR", "minValue": 180000.0, "maxValue": 220000.0, "currencyCode": "USD"},
         ]}},
        {"id": "2", "title": "Hidden", "jobUrl": "https://jobs.ashbyhq.com/acme/2", "isListed": False},
    ]}
    [p] = ashby.fetch(Board("acme", "Acme", "ashby", board="acme"), FakeHTTP({"ashby": payload}), set()).postings
    assert p.location == "NYC • SF" and p.remote is False
    assert (p.salary_min, p.salary_max) == (180000, 220000)


WD = Board("acme", "Acme", "workday", host="acme.wd1.myworkdayjobs.com", tenant="acme", site="Careers")


def _workday_http(titles):
    listing = {"total": len(titles), "jobPostings": [
        {"title": t, "externalPath": f"/job/X/{i}", "locationsText": "Austin"} for i, t in enumerate(titles)
    ]}
    detail = lambda url: {"jobPostingInfo": {  # noqa: E731
        "title": "T", "jobDescription": "<p>Go and Python</p>", "jobReqId": "R" + url[-1], "timeType": "Full time",
        "startDate": "2026-10-01", "externalUrl": "https://acme.wd1.myworkdayjobs.com/en-US/Careers" + url[-8:],
    }}
    return FakeHTTP({"/jobs": listing, "/job/": detail})


def test_workday_fetches_details_only_for_new_relevant_postings():
    http = _workday_http(["Software Engineer", "Sales Lead", "Data Engineer"])
    known = {workday.public_url(WD, "/job/X/2")}
    keep = TitleFilter(("engineer",), ())
    res = workday.fetch(WD, http, known, keep.keeps)
    detail_calls = [c for c in http.calls if c[0] == "GET"]
    assert len(detail_calls) == 1 and detail_calls[0][1].endswith("/job/X/0")  # not the sales job, not the known one
    assert len(res.postings) == 1 and len(res.seen_urls) == 3 and res.complete


def test_workday_detail_cap_marks_run_partial(monkeypatch):
    monkeypatch.setattr(workday, "MAX_DETAILS", 1)
    res = workday.fetch(WD, _workday_http(["Engineer A", "Engineer B"]), set(), None)
    assert len(res.postings) == 1 and res.complete is False


def test_html_to_text_collapses_blank_lines():
    assert html_to_text("<p>a</p>\n\n\n\n<p>b&nbsp;c</p>") == "a\n\nb c"


# ── extraction ────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def ex():
    return TextExtractor()


def test_two_letter_skills_are_case_sensitive(ex):
    assert "Go" not in ex.skills("Ready to go? Join Google.", "Engineer")
    assert "Go" in ex.skills("We write Go and Python.", "Engineer")
    assert "AI" not in ex.skills("We said hi to the maintainers", "Engineer")


@pytest.mark.parametrize("text, expected", [
    ("The base range is $153,000 - $376,000 USD.", (153000, 376000)),
    ("Pay: $120k–$160k", (120000, 160000)),
    ("Raised $50 to $100 million", (None, None)),        # out of salary range
    ("No numbers here", (None, None)),
])
def test_salary_from_text(ex, text, expected):
    assert ex.salary(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("We are unable to sponsor visas for this role.", False),
    ("This position does not offer visa sponsorship.", False),
    ("Visa sponsorship is available.", True),
    ("Great team, great snacks.", None),
])
def test_visa_reading_respects_negation(ex, text, expected):
    assert ex.sponsors_visa(text) is expected


# ── board config ──────────────────────────────────────────────────────────

def test_shipped_company_list_is_valid():
    config = load_boards()
    assert len(config.boards) >= 50
    assert {b.ats for b in config.boards} == {"greenhouse", "lever", "ashby", "workday"}
    assert all(b.search for b in config.boards if b.ats == "workday")


@pytest.mark.parametrize("entry, msg", [
    ({"key": "x", "name": "X", "ats": "taleo", "board": "x"}, "unknown ats"),
    ({"key": "x", "name": "X", "ats": "greenhouse"}, "needs board"),
    ({"key": "x", "name": "X", "ats": "workday", "host": "h"}, "needs tenant, site"),
])
def test_bad_company_entries_are_rejected(entry, msg):
    with pytest.raises(BoardConfigError, match=msg):
        parse({"companies": [entry]})


def test_unknown_company_key_is_an_error():
    with pytest.raises(BoardConfigError, match="nope"):
        load_boards().select(["nope"])


def test_title_filter():
    f = TitleFilter(("engineer", "ML", "full stack"), ("recruiter",))
    assert f.keeps("Senior Software Engineer") and f.keeps("Staff ML Platform") and f.keeps("Full-Stack Dev")
    assert not f.keeps("Technical Recruiter, Engineering")   # exclude wins
    assert not f.keeps("HTML Specialist")                     # ML is a whole word, case-sensitive
    assert f.with_terms(["Product Manager"]).keeps("Senior Product Manager")


# ── sync_board (DB calls faked) ───────────────────────────────────────────

GH = Board("acme", "Acme", "greenhouse", board="acme")


def _post(url, title="Backend Engineer", desc="Python"):
    return Posting(external_id=url, url=url, title=title, location="Remote", description=desc)


@pytest.fixture
def fake_db(monkeypatch):
    state = {"known": {}, "writes": [], "runs": []}
    monkeypatch.setattr(ingest, "_known", lambda key: state["known"])
    monkeypatch.setattr(ingest, "_write", lambda b, rows, touched, close, now: state["writes"].append((rows, touched, close)))
    monkeypatch.setattr(ingest, "_record", lambda r, now: state["runs"].append(r))
    return state


def _fetcher(monkeypatch, result):
    monkeypatch.setitem(ingest.FETCHERS, "greenhouse", lambda board, http, known, keep: result)


def test_sync_inserts_new_touches_unchanged_updates_changed_and_closes_missing(monkeypatch, fake_db, ex):
    same, edited = _post("https://b.example/u-same"), _post("https://b.example/u-edit", desc="Python and Rust")
    fake_db["known"] = {
        "https://b.example/u-same": (ingest.content_hash(same), None),
        "https://b.example/u-edit": ("old-hash", None),
        "https://b.example/u-gone": ("h", None),
        "https://b.example/u-already-closed": ("h", "2026-01-01"),
    }
    _fetcher(monkeypatch, FetchResult(postings=[same, edited, _post("https://b.example/u-new"), _post("https://b.example/u-sales", title="Account Executive")]))
    r = ingest.sync_board(GH, TitleFilter(("engineer",), ()), extract=ex)
    assert (r.new, r.updated, r.unchanged, r.closed, r.kept, r.error) == (1, 1, 1, 1, 3, None)
    rows, touched, closed = fake_db["writes"][0]
    assert {row["url"] for row in rows} == {"https://b.example/u-new", "https://b.example/u-edit"} and touched == ["https://b.example/u-same"] and closed == ["https://b.example/u-gone"]
    assert rows[0]["company_key"] == "acme" and rows[0]["ats"] == "greenhouse"
    assert fake_db["runs"][0] is r


def test_partial_fetch_closes_nothing(monkeypatch, fake_db, ex):
    fake_db["known"] = {"https://b.example/u-gone": ("h", None)}
    _fetcher(monkeypatch, FetchResult(postings=[], complete=False))
    r = ingest.sync_board(GH, TitleFilter(("engineer",), ()), extract=ex)
    assert r.closed == 0 and fake_db["writes"][0][2] == []


def test_failed_board_is_recorded_not_raised(monkeypatch, fake_db, ex):
    def boom(*a):
        raise ConnectionError("board down")
    monkeypatch.setitem(ingest.FETCHERS, "greenhouse", boom)
    r = ingest.sync_board(GH, TitleFilter(("engineer",), ()), extract=ex)
    assert "board down" in r.error and fake_db["writes"] == [] and fake_db["runs"] == [r]


def test_reopened_posting_is_updated(monkeypatch, fake_db, ex):
    p = _post("https://b.example/u1")
    fake_db["known"] = {"https://b.example/u1": (ingest.content_hash(p), "2026-10-01")}  # closed earlier, back on the board
    _fetcher(monkeypatch, FetchResult(postings=[p]))
    r = ingest.sync_board(GH, TitleFilter(("engineer",), ()), extract=ex)
    assert r.updated == 1 and fake_db["writes"][0][0][0]["url"] == "https://b.example/u1"


def test_dry_run_writes_nothing(monkeypatch, fake_db, ex):
    _fetcher(monkeypatch, FetchResult(postings=[_post("https://b.example/u1")]))
    r = ingest.sync_board(GH, TitleFilter(("engineer",), ()), dry_run=True, extract=ex)
    assert r.new == 1 and fake_db["writes"] == [] and fake_db["runs"] == []


def test_non_http_links_are_never_stored(monkeypatch, fake_db, ex):
    evil = _post("javascript:alert(1)")
    sneaky = Posting(external_id="2", url="https://ok.example/2", title="Engineer", apply_url="javascript:alert(1)")
    _fetcher(monkeypatch, FetchResult(postings=[evil, sneaky]))
    r = ingest.sync_board(GH, TitleFilter(("engineer",), ()), extract=ex)
    [row] = fake_db["writes"][0][0]
    assert r.new == 1 and row["url"] == "https://ok.example/2" and row["application_url"] == "https://ok.example/2"


# ── scheduler ─────────────────────────────────────────────────────────────

def test_scheduled_cycle_syncs_then_rescores_every_active_user(monkeypatch):
    from contextlib import contextmanager

    from careeros.jobs import scan, scheduler

    calls = []
    monkeypatch.setattr(ingest, "sync_all", lambda: calls.append("sync") or ingest.SyncSummary())

    class Q:
        def filter(self, *a):
            return self

        def all(self):
            return [("u1",), ("u2",)]

    class S:
        def query(self, *a):
            return Q()

    @contextmanager
    def scope():
        yield S()

    monkeypatch.setattr(scheduler.db, "session_scope", scope)
    monkeypatch.setattr(scan, "run_scan", lambda job, uid: calls.append(uid) or job.update(status="completed", result={}))
    assert scheduler.run_cycle() == ingest.SyncSummary().totals
    assert calls == ["sync", "u1", "u2"]


def test_scheduled_cycle_skips_when_a_sync_is_running(monkeypatch):
    from careeros.jobs import scheduler

    def busy():
        raise ingest.SyncBusy("running")
    monkeypatch.setattr(ingest, "sync_all", busy)
    assert scheduler.run_cycle() is None
