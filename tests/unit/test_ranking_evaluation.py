"""Ranking evaluation (careeros/jobs/evaluation.py): AUC and the label sheet."""

from careeros.jobs.evaluation import auc, read_label_sheet


def test_auc_counts_good_above_bad():
    assert auc([(90, True), (10, False)]) == 1.0
    assert auc([(10, True), (90, False)]) == 0.0
    assert auc([(50, True), (50, False)]) == 0.5
    assert auc([(80, True), (60, False), (70, True), (90, False)]) == 0.5
    assert auc([(80, True)]) is None


def test_label_sheet_reads_turkish_and_english(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text("label,url\niyi,a\nbad,b\n,c\nEVET,d\nkötü,e\n", encoding="utf-8")
    assert read_label_sheet(p) == {"a": True, "b": False, "d": True, "e": False}


def test_cli_uses_career_os_email_when_none_is_given(monkeypatch):
    import typer
    import pytest

    from careeros.jobs import cli
    from careeros.shared.config import get_settings

    monkeypatch.delenv("CAREER_OS_EMAIL", raising=False)
    monkeypatch.setattr("careeros.shared.config.load_env", lambda *a, **k: None)
    get_settings.cache_clear()
    try:
        with pytest.raises(typer.Exit):        # neither an argument nor the setting
            cli._user_id(None)
        monkeypatch.setenv("CAREER_OS_EMAIL", "  me@example.test ")
        get_settings.cache_clear()
        assert get_settings().cli_user_email == "me@example.test"
    finally:
        get_settings.cache_clear()
