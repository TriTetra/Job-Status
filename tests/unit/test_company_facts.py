"""Company card (careeros/companies/facts.py): matched by website, never a namesake; every fact sourced."""

from datetime import datetime, timezone
from types import SimpleNamespace

import careeros.db.models  # noqa: F401
from careeros.companies import facts
from careeros.jobs.trust import assess

NOW = datetime(2026, 11, 23, tzinfo=timezone.utc)


class _Resp:
    def __init__(self, data, status=200):
        self._d, self.status_code = data, status

    def json(self):
        return self._d


def _claim(value, rank="normal", qualifiers=None):
    return {"rank": rank, "mainsnak": {"datavalue": {"value": value}}, "qualifiers": qualifiers or {}}


ENTITY = {
    "id": "Q2", "labels": {"en": {"value": "Acme"}}, "descriptions": {"en": {"value": "software company"}},
    "claims": {
        "P856": [_claim("https://www.acme.io/")],
        "P571": [_claim({"time": "+2014-05-01T00:00:00Z"})],
        "P1128": [_claim({"amount": "+120"}, qualifiers={"P585": [{"datavalue": {"value": {"time": "+2020-01-01T00:00:00Z"}}}]}),
                  _claim({"amount": "+340"}, qualifiers={"P585": [{"datavalue": {"value": {"time": "+2024-01-01T00:00:00Z"}}}]})],
        "P17": [_claim({"id": "Q183"})], "P159": [_claim({"id": "Q64"})], "P452": [_claim({"id": "Q7397"})],
    },
}
NAMESAKE = {"id": "Q1", "labels": {"en": {"value": "Acme"}}, "claims": {"P856": [_claim("https://acme-paints.com")]}}


class _Http:
    def __init__(self):
        self.calls = []

    def get(self, url, params=None, **kw):
        self.calls.append(params.get("action") or params.get("q") or params.get("query"))
        if params.get("action") == "wbsearchentities":
            return _Resp({"search": [{"id": "Q1"}, {"id": "Q2"}]})
        if params.get("props") == "labels":
            return _Resp({"entities": {"Q183": {"labels": {"en": {"value": "Germany"}}},
                                       "Q64": {"labels": {"en": {"value": "Berlin"}}},
                                       "Q7397": {"labels": {"en": {"value": "software"}}}}})
        return _Resp({"entities": {"Q1": NAMESAKE, "Q2": ENTITY}})


def test_names_and_domains():
    assert facts.key_of("Acme GmbH") == facts.key_of("ACME") == "acme"
    assert facts._base("careers.acme.co.uk") == "acme.co.uk" and facts._base("www.jobs.acme.com") == "acme.com"


def test_wikidata_is_matched_by_website_never_by_name_alone():
    w = facts.wikidata("Acme", "jobs.acme.io", _Http())
    assert w["id"] == "Q2" and w["founded"] == 2014 and w["employees"] == {"count": 340, "year": 2024}
    assert (w["country"], w["headquarters"], w["industry"]) == ("Germany", "Berlin", ["software"])
    assert w["url"] == "https://www.wikidata.org/wiki/Q2" and "CC0" in w["source"]
    assert facts.wikidata("Acme", "acme-robots.ai", _Http()) == {}      # no entity with that website
    http = _Http()
    assert facts.wikidata("Acme", None, http) == {} and http.calls == []  # no website: not guessed


def test_companies_house_only_an_exact_single_match():
    class CH:
        def __init__(self, items):
            self.items = items

        def get(self, url, **kw):
            return _Resp({"items": self.items})
    one = [{"title": "ACME LTD", "company_number": "123", "company_status": "active", "date_of_creation": "2016-02-01"},
           {"title": "ACME HOLDINGS LIMITED", "company_number": "9", "company_status": "active"}]
    ch = facts.companies_house("Acme", "key", CH(one))
    assert ch["number"] == "123" and ch["url"].endswith("/company/123") and ch["incorporated"] == "2016-02-01"
    two = one[:1] + [{"title": "Acme Limited", "company_number": "7", "company_status": "active"}]
    assert facts.companies_house("Acme", "key", CH(two)) == {}                   # ambiguous: not guessed
    assert facts.companies_house("Acme", None, CH(one)) == {}                    # no key: off


def test_trust_notes_and_the_trust_check():
    good, concerns = facts.trust_notes({"founded": 2014}, {"status": "active", "incorporated": "2016-02-01"},
                                       [{"type": "layoff", "date": "2026-10-01", "source": "techcrunch"}], NOW)
    assert good == ["Founded in 2014 (Wikidata)", "Registered in the UK since 2016 (Companies House)"]
    assert concerns == ["Layoffs reported 2026-10-01 (techcrunch)"]
    _, gone = facts.trust_notes({"dissolved": 2023}, {"status": "liquidation"}, [], NOW)
    assert gone == ["Dissolved in 2023 (Wikidata)", "UK register status: liquidation (Companies House)"]
    t = assess(company="Acme", description="", ats="greenhouse", company_domain="acme.io", salary_stated=True,
               posted_at=NOW, now=NOW, public={"good": good, "concerns": concerns})
    assert t.level == "caution" and "Layoffs reported 2026-10-01 (techcrunch)" in t.concerns
    assert "Founded in 2014 (Wikidata)" in t.good


def test_people_summary_keeps_only_sourced_points(monkeypatch):
    comments = [{"id": str(i), "text": f"I worked at Acme {i}", "at": "2026-01-01",
                 "url": f"https://news.ycombinator.com/item?id={i}"} for i in range(1, 5)]
    monkeypatch.setattr(facts, "hn_comments", lambda name, http=None, now=None: comments)
    got = facts._People(points=[facts._Point(text="Several say on-call is heavy.", refs=["c1", "c3"]),
                                facts._Point(text="Unsourced claim.", refs=["c99"])])
    import careeros.shared.llm as llm
    monkeypatch.setattr(llm, "get_llm_client", lambda: SimpleNamespace(complete_model=lambda *a, **k: got))
    p = facts.people("Acme")
    assert p["comments"] == 4 and len(p["points"]) == 1
    assert p["points"][0]["sources"] == ["https://news.ycombinator.com/item?id=1", "https://news.ycombinator.com/item?id=3"]
    monkeypatch.setattr(facts, "hn_comments", lambda name, http=None, now=None: comments[:2])
    assert "points" not in facts.people("Acme")                                  # too little to summarise


def test_card_reads_once_then_serves_the_cache(monkeypatch):
    rows = {}

    class S:
        def get(self, model, key):
            return rows.get(key)

        def add(self, row):
            rows[row.key] = row

        def flush(self):
            pass
    calls = []
    monkeypatch.setattr(facts, "wikidata", lambda name, domain, http: calls.append(domain) or {"founded": 2014})
    monkeypatch.setattr(facts, "news", lambda session, name, now=None: [])
    out = facts.card(S(), "Acme GmbH", "careers.acme.io", now=NOW, http=object())
    assert out["wikidata"] == {"founded": 2014} and out["good"] == ["Founded in 2014 (Wikidata)"] and calls == ["acme.io"]
    facts.card(S(), "ACME", None, now=NOW, http=object())
    assert calls == ["acme.io"]                                                  # same company, fresh: not re-read
