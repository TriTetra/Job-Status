"""Pay by country (careeros/market/pay.py): only pay the employer stated, local currency, sourced."""

from types import SimpleNamespace

import careeros.db.models  # noqa: F401
from careeros.jobs.scan import pool_medians
from careeros.market import pay


def _job(title, location, lo=None, hi=None, cur=None, facts=None, url=None):
    return SimpleNamespace(url=url or f"https://x/{title}/{location}/{lo}", title=title, location=location,
                           salary_min=lo, salary_max=hi, salary_currency=cur,
                           llm_facts=facts, llm_facts_hash="h" if facts else None, content_hash="h")


def test_role_families():
    assert pay.family_of("Senior Machine Learning Platform Engineer") == "ML / AI"
    assert pay.family_of("Data Engineer") == "Data"
    assert pay.family_of("Full-Stack Developer") == "Full stack"
    assert pay.family_of("Backend Engineer (Go)") == "Backend"
    assert pay.family_of("Site Reliability Engineer") == "DevOps / Platform"
    assert pay.family_of("Kıdemli Yazılım Geliştirici") == "Software"
    assert pay.family_of("Enterprise Account Executive") is None
    assert pay.family_of("Mechanical Engineer") is None


def test_only_stated_pay_in_the_right_currency():
    assert pay.stated_pay(_job("Backend Engineer", "Berlin, Germany", 60000, 80000, "EUR"), "DE") == (70000, "EUR")
    # the keyword extractor stores amounts as USD without knowing the currency: not trusted outside the US
    assert pay.stated_pay(_job("Backend Engineer", "Berlin, Germany", 60000, 80000, "USD"), "DE") is None
    assert pay.stated_pay(_job("Backend Engineer", "Austin, TX", 150000, None, "USD"), "US") == (150000, "USD")
    # the LLM's reading records the currency and the period
    facts = {"salary_min": 55000, "salary_max": 65000, "salary_currency": "gbp", "salary_period": "year"}
    assert pay.stated_pay(_job("ML Engineer", "London, UK", facts=facts), "GB") == (60000, "GBP")
    monthly = {**facts, "salary_period": "month"}
    assert pay.stated_pay(_job("ML Engineer", "London, UK", facts=monthly), "GB") is None
    assert pay.stated_pay(_job("Backend Engineer", "Austin, TX", 45, 60, "USD"), "US") is None   # hourly
    stale = _job("ML Engineer", "London, UK", facts=facts)
    stale.content_hash = "changed"                                                               # facts outdated
    assert pay.stated_pay(stale, "GB") is None


def test_pay_by_country_needs_enough_postings_and_shows_where_it_comes_from():
    rows = [_job("Backend Engineer", "Berlin, Germany", 60000 + i * 2000, 80000 + i * 2000, "EUR") for i in range(8)]
    rows += [_job("ML Engineer", "Munich, Germany", 90000, 110000, "EUR")]
    rows += [_job("Backend Engineer", "Remote - Germany or Poland", 70000, 90000, "EUR")]   # two countries: skipped
    rows += [_job("Account Executive", "Berlin, Germany", 90000, 120000, "EUR")]           # not a tech role
    out = pay.pay_by_country(rows, preferred=["de"])
    de = out["countries"][0]
    assert de["code"] == "DE" and de["currency"] == "EUR" and de["all"]["postings"] == 9
    backend = next(f for f in de["families"] if f["family"] == "Backend")
    assert backend["postings"] == 8 and backend["median"] == 77000 and "p25" in backend and len(backend["examples"]) == 5
    ml = next(f for f in de["families"] if f["family"] == "ML / AI")
    assert ml["postings"] == 1 and "median" not in ml                                       # too few to say


def test_official_figures_are_verified_and_linked():
    figs = pay.official()
    assert figs and all(f["url"].startswith("https://") and f["source"] and f["reference"] for f in figs)
    us = pay.pay_by_country([], preferred=["US"])["countries"]
    assert us and us[0]["code"] == "US" and us[0]["official"][0]["median"] == 135980


def test_score_pay_reference_ignores_currency_guesses():
    rows = [_job("Backend Engineer", "Berlin, Germany", 60000, 80000, "EUR", url=f"https://d/{i}") for i in range(5)]
    rows += [_job("Backend Engineer", "Berlin, Germany", 300000, 400000, "USD", url=f"https://g/{i}") for i in range(5)]
    medians = pool_medians(rows)
    assert 70000 < medians["DE"] < 80000          # €60–80k as an expected offer in USD; the "USD" guesses left out
