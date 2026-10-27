"""Backfill explanation.decision for existing career_scores rows.

Rules-only (no LLM): criteria + next_action + template reasoning.
Run: python scripts/backfill_decisions.py
"""

from datetime import datetime


from careeros.db.connection import db
from careeros.jobs.models.career_score import CareerScore
from careeros.identity.repositories.career_preferences_repo import CareerPreferencesRepository
from careeros.jobs.decision_builder import build_decision, template_reasoning


def _prefs_for(session, user_id: str) -> dict:
    p = CareerPreferencesRepository(session).get_by_user_id(user_id)
    if not p:
        return {}
    return {
        "work_arrangements": p.work_arrangements or [],
        "preferred_country_codes": p.preferred_country_codes or [],
        "requires_sponsorship": p.requires_sponsorship,
        "salary_min": p.salary_min,
        "salary_max": p.salary_max,
    }


def main():
    with db.session_scope() as s:
        prefs_cache: dict[str, dict] = {}
        rows = s.query(CareerScore).all()
        n = 0
        for sc in rows:
            if sc.user_id not in prefs_cache:
                prefs_cache[sc.user_id] = _prefs_for(s, sc.user_id)
            ex = dict(sc.explanation or {})
            dec = build_decision(
                recommendation=sc.recommendation,
                career_score=sc.career_score or 0,
                career_value=sc.career_value or 0,
                market_demand=sc.market_demand or 0,
                job=ex,
                prefs=prefs_cache[sc.user_id],
                matched_skills=ex.get("matched_skills") or [],
                gap_skills=sc.skill_gaps or [],
            )
            dec["reasoning"] = template_reasoning(
                dec["semantic"]["tier"],
                ex,
                dec["criteria"],
                ex.get("matched_skills") or [],
                sc.skill_gaps or [],
            )
            dec["reasoning_source"] = "template"
            dec["generated_at"] = datetime.utcnow().isoformat()
            ex["decision"] = dec
            sc.explanation = ex
            n += 1
        s.commit()
        print(f"[OK] decision backfilled for {n} rows")


if __name__ == "__main__":
    from careeros.shared.logging import configure_logging

    configure_logging()
    main()
