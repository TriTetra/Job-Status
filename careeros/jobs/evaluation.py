"""How good is the ranking for this person? Measured against what they said about jobs.

Labels come from the person's own decisions (Shortlist / Applied / later stages = good,
Skip = bad) and, optionally, a sheet they filled in (url,label with good/bad). The current
scores rank the labelled jobs; we report how often a good job ranks above a bad one (AUC)
and how many of the top 10 are good. Run it before and after a scoring change: without it,
changes are guesses.
"""

import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from careeros.applications.models.application import Application
from careeros.jobs.models.career_score import CareerScore

GOOD_STATUSES = {"to_apply", "applied", "interview", "offer"}
BAD_STATUSES = {"skipped"}
GOOD_WORDS = {"good", "yes", "1", "iyi", "evet", "+"}
BAD_WORDS = {"bad", "no", "0", "kötü", "kotu", "hayır", "hayir", "-"}


@dataclass
class Report:
    labelled: int
    good: int
    bad: int
    scored: int
    auc: Optional[float]           # P(a good job scores above a bad one); 0.5 = no better than chance
    precision_at_10: Optional[float]
    top: list[tuple[str, float, bool]]  # (url, score, good) — the first 10 labelled jobs as ranked


def labels_from_decisions(session: Session, user_id: str) -> dict[str, bool]:
    rows = session.query(Application.url, Application.status).filter(Application.user_id == user_id).all()
    out = {}
    for url, status in rows:
        if status in GOOD_STATUSES:
            out[url] = True
        elif status in BAD_STATUSES:
            out[url] = False
    return out


def read_label_sheet(path: Path) -> dict[str, bool]:
    """A CSV with `url` and `label` columns (good/bad, iyi/kötü, 1/0); blank labels are skipped."""
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            word = (row.get("label") or "").strip().lower()
            if word in GOOD_WORDS:
                out[row["url"]] = True
            elif word in BAD_WORDS:
                out[row["url"]] = False
    return out


def auc(scored: Iterable[tuple[float, bool]]) -> Optional[float]:
    """Mann–Whitney: share of (good, bad) pairs where the good one scores higher (ties count half)."""
    items = list(scored)
    good = [s for s, g in items if g]
    bad = [s for s, g in items if not g]
    if not good or not bad:
        return None
    wins = sum(1.0 if g > b else 0.5 if g == b else 0.0 for g in good for b in bad)
    return wins / (len(good) * len(bad))


def evaluate(session: Session, user_id: str, labels: dict[str, bool]) -> Report:
    scores = dict(session.query(CareerScore.url, CareerScore.career_score)
                  .filter(CareerScore.user_id == user_id, CareerScore.url.in_(list(labels))).all()) if labels else {}
    ranked = sorted(((u, scores[u] or 0.0, labels[u]) for u in labels if u in scores), key=lambda x: -x[1])
    top = ranked[:10]
    return Report(
        labelled=len(labels), good=sum(labels.values()), bad=len(labels) - sum(labels.values()), scored=len(ranked),
        auc=auc((s, g) for _, s, g in ranked),
        precision_at_10=(sum(g for _, _, g in top) / len(top)) if top else None,
        top=top,
    )


def export_label_sheet(session: Session, user_id: str, path: Path, n: int = 50, seed: int = 7) -> int:
    """Half the current top jobs, half a random draw from the rest (so the sheet tests both ends)."""
    from careeros.jobs.models.job import Job

    rows = (session.query(CareerScore.url, CareerScore.career_score, Job.title, Job.company, Job.location)
            .join(Job, Job.url == CareerScore.url)
            .filter(CareerScore.user_id == user_id, Job.closed_at.is_(None))
            .order_by(CareerScore.career_score.desc().nullslast()).all())
    top, rest = rows[: n // 2], rows[n // 2:]
    picked = top + random.Random(seed).sample(rest, min(len(rest), n - len(top)))
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["label", "score", "title", "company", "location", "url"])
        for url, score, title, company, location in picked:
            w.writerow(["", round(score or 0, 1), title, company, location, url])
    return len(picked)
