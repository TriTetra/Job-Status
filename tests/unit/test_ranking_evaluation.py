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
