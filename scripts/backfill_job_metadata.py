"""Backfill career_scores.explanation with job metadata from ApplyPilot DB.

Fixes old rows scored before explanation enrichment existed:
- company / title / location / remote / description / required_skills
- matched_skills + gap_skills (user evidence vs required)
- recommendation normalized to APPLY | CONSIDER | SKIP
Run once:  python scripts/backfill_job_metadata.py [--force]
"""

import sys


from plugins.plugin_loader import load_job_source_plugin
from core.db.connection import db
from core.db.models.career_score import CareerScore
from core.db.models.company import Company
from apps.api.app.core.evidence.confidence_aggregator import aggregate_user_skills

FORCE = "--force" in sys.argv


def main():
    plugin = load_job_source_plugin("applypilot")
    jobs = plugin.scan_and_normalize(hours_old=0, min_score=0)
    by_url = {j["url"]: j for j in jobs}
    print(f"ApplyPilot jobs loaded: {len(by_url)}")

    with db.session_scope() as s:
        tier_by_name = {c.name.lower(): c.tier for c in s.query(Company).all()}
        scores = s.query(CareerScore).all()
        user_skills_cache: dict[str, list[str]] = {}
        updated = 0

        for sc in scores:
            # ── 1) recommendation normalize (her satır) ─────────────────
            norm = (sc.recommendation or "CONSIDER").split(" - ")[0].strip().upper()
            if norm not in ("APPLY", "CONSIDER", "SKIP"):
                norm = "CONSIDER"
            if norm != sc.recommendation:
                sc.recommendation = norm

            # ── 2) metadata backfill ────────────────────
            job = by_url.get(sc.url)
            ex = dict(sc.explanation or {})
            if not job:
                continue

            # Skip if already enriched, unless FORCE mode is enabled
            if ex.get("company") and not FORCE:
                continue

            req = [r for r in (job.get("required_skills") or []) if isinstance(r, str)]

            if sc.user_id not in user_skills_cache:
                try:
                    user_skills_cache[sc.user_id] = [
                        a["skill_name"].lower() for a in aggregate_user_skills(sc.user_id, s)
                    ]
                except Exception:
                    user_skills_cache[sc.user_id] = []
            mine = user_skills_cache[sc.user_id]
            matched = [r for r in req if r.lower() in mine or any(m in r.lower() for m in mine)]
            gaps = [r for r in req if r not in matched][:5]

            company = job.get("company", "") or ""
            ex.update({
                "title": job.get("title", ""),
                "location": job.get("location", ""),
                "remote": bool(job.get("remote", False)),
                "remote_region": job.get("remote_region"),
                "source": job.get("source", "unknown"),
                "sponsors_visa": bool(job.get("sponsors_visa", False)),
                "description": (job.get("description") or "")[:500],
                "required_skills": req,
                "matched_skills": [{"name": m, "confidence": 75} for m in matched[:5]],
                "tier": tier_by_name.get(company.lower()),
            })

            if company and company != "Unknown":
                ex["company"] = company
            else:
                ex.pop("company", None)  # Let frontend host fallback work

            sc.explanation = ex
            if not sc.skill_gaps or FORCE:
                sc.skill_gaps = gaps
            updated += 1

        s.commit()
        print(f"[OK] Backfilled {updated} career_scores rows")


if __name__ == "__main__":
    from shared.logging import configure_logging

    configure_logging()
    main()
