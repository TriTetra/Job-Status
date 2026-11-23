"""Employers directory (careeros/companies/employers.py): cleaning, sectors, logo guard."""

from careeros.companies import employers as emp
from careeros.companies import logos


def _write(tmp_path, monkeypatch, text):
    (tmp_path / "employers_xx.yaml").write_text(text, encoding="utf-8")
    monkeypatch.setattr(emp, "DIR", tmp_path)
    emp.load.cache_clear()


def test_entries_are_cleaned(tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, """
employers:
  - {name: Zeta, domain: www.zeta.com.tr, sector: fintech, city: Istanbul, careers_url: https://zeta.com.tr/careers}
  - {name: Alpha, sector: rockets, careers_url: alpha.io/jobs}
  - {name: NoLink, sector: saas}
  - {name: Bad, careers_url: "javascript:alert(1)"}
""")
    rows = emp.load("xx")
    assert [r["name"] for r in rows] == ["Alpha", "Zeta"]                 # sorted; no link / bad link dropped
    assert rows[0]["careers_url"] == "https://alpha.io/jobs" and rows[0]["sector"] == "other"
    assert rows[1]["domain"] == "zeta.com.tr" and rows[1]["sector"] == "fintech"
    emp.load.cache_clear()


def test_the_turkey_directory_is_valid():
    rows = emp.load("tr")
    assert len(rows) >= 50
    assert all(r["careers_url"].startswith("https://") for r in rows)
    assert all(r["sector"] in emp.SECTORS for r in rows)
    assert len({r["name"] for r in rows}) == len(rows)                    # no duplicates


def test_logo_endpoint_only_serves_directory_domains(monkeypatch):
    monkeypatch.setattr(emp, "domains", lambda country="tr": {"trendyol.com"})
    calls = []
    monkeypatch.setattr(logos, "_favicon", lambda d, http=None: calls.append(d) or (b"png", "image/png"))
    assert logos.logo_for_domain("evil.example") is None and calls == []
    assert logos.logo_for_domain("www.Trendyol.com") == (b"png", "image/png") and calls == ["trendyol.com"]
