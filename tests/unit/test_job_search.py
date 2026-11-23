"""Job search (careeros/jobs/search.py): query words, filters, reachability, pay reference."""

from types import SimpleNamespace

from careeros.jobs import search as s
from careeros.jobs.scoring.model_v8 import Signals
from careeros.jobs.scoring.signals import languages_required


def job(**kw):
    base = dict(url="u", remote=False, hybrid=False, sponsors_visa=None,
                signals=Signals(title="x", must=[], nice=[], required_years=0, countries=["DE"], offer_usd=70_000))
    return SimpleNamespace(**{**base, **kw})


def meta(**kw):
    base = dict(location="Berlin, Germany", remote_regions=[], company_size="midsize",
                trust={"level": "verified", "agency": False})
    return {**base, **kw}


def test_query_words_are_cleaned_and_capped():
    assert s._words("  machine   learning ") == ["machine", "learning"]
    assert s._words("100%_ai \\x") == ["100", "ai"]        # LIKE wildcards never reach the query
    assert len(s._words("a b c d e f g h i j k l m n o p")) == 0  # one-letter words are noise
    assert len(s._words(" ".join(["word"] * 10))) == 6


def test_country_names_include_cities():
    names = s._place_names("TR")
    assert "Turkey" in names and "Türkiye" in names and "istanbul" in names


def test_country_filter_uses_geography():
    f = s.SearchFilters(country="DE")
    assert s.keeps(job(), meta(), f)
    assert not s.keeps(job(), meta(location="Paris, France"), f)
    assert s.keeps(job(remote=True), meta(location="Remote", remote_regions=["Europe"]), f)     # open to Germany
    assert not s.keeps(job(remote=True), meta(location="Remote", remote_regions=["United States"]), f)
    assert not s.keeps(job(remote=True), meta(location="Remote", remote_regions=[]), f)          # can't tell: left out


def test_work_size_trust_visa_and_pay_filters():
    assert s.keeps(job(hybrid=True), meta(), s.SearchFilters(work=["hybrid"]))
    assert not s.keeps(job(), meta(), s.SearchFilters(work=["remote", "hybrid"]))               # on-site
    assert s.keeps(job(), meta(company_size="big_tech"), s.SearchFilters(sizes=["large"]))
    assert not s.keeps(job(), meta(company_size="unknown"), s.SearchFilters(sizes=["startup"]))
    assert not s.keeps(job(), meta(trust={"level": "ok", "agency": True}), s.SearchFilters(reliable=True))
    assert not s.keeps(job(), meta(trust={"level": "risk", "agency": False}), s.SearchFilters(reliable=True))
    assert not s.keeps(job(), meta(), s.SearchFilters(visa=True))
    assert s.keeps(job(sponsors_visa=True), meta(), s.SearchFilters(visa=True))
    assert s.keeps(job(), meta(), s.SearchFilters(min_salary_usd=60_000))
    assert not s.keeps(job(), meta(), s.SearchFilters(min_salary_usd=90_000))
    no_pay = job(signals=Signals(title="x", must=[], nice=[], required_years=0, offer_usd=None))
    assert not s.keeps(no_pay, meta(), s.SearchFilters(min_salary_usd=1))                     # pay not stated


def test_reachable_hides_gated_and_remote_for_other_countries():
    model = lambda **kw: {"explanation": {"model": {"gates": [], "chance_factors": {"location": 1}, **kw}}}
    assert s.reachable(model())
    assert not s.reachable(model(gates=["Needs DE"]))
    assert not s.reachable(model(chance_factors={"location": 0.1}))
    assert s.reachable({"explanation": {}})                                                     # unscored: shown


def test_pay_reference_is_set_on_copies():
    j = SimpleNamespace(signals=Signals(title="x", must=[], nice=[], required_years=0, countries=["DE"]))
    from dataclasses import dataclass

    @dataclass
    class J:
        signals: Signals

    original = J(signals=j.signals)
    out = s.with_pay_reference([original], {"DE": 80_000, "*": 60_000})
    assert out[0].signals.market_median_usd == 80_000 and original.signals.market_median_usd is None
    elsewhere = J(signals=Signals(title="x", must=[], nice=[], required_years=0, countries=["FR"]))
    assert s.with_pay_reference([elsewhere], {"DE": 80_000, "*": 60_000})[0].signals.market_median_usd == 60_000


def test_language_check_is_unchanged_by_the_fast_path():
    assert languages_required("Fluent German is required.", "") == ["de"]
    assert languages_required("Verhandlungssicheres Deutsch", "") == ["de"]
    assert languages_required("Based in Germany, English only.", "") == []
    assert languages_required("Native Turkish speaker, C1", "") == ["tr"]
