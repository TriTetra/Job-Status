"""
Phase 1B doğrulama — apply_strategy.py'nin DB'ye yazdıklarını oku.

Kullanım:
    python scripts/test_db_integration.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from sqlalchemy import func, select, text

from core.db.connection import db
from core.db.repositories import CareerScoreRepository


def main():
    print("=" * 70)
    print("  DB INTEGRATION TEST")
    print("=" * 70)

    with db.session_scope() as session:
        repo = CareerScoreRepository(session)

        # 1. Toplam kayıt
        total = session.execute(select(func.count()).select_from(repo.model)).scalar()
        print(f"\nToplam kayit: {total}")

        if total == 0:
            print("DB bos! Once apply_strategy.py calistir.")
            return

        # 2. Son scan zamanı
        latest = session.execute(select(func.max(repo.model.scanned_at))).scalar()
        print(f"Son scan: {latest}")

        # 3. Recommendation dağılımı
        print("\nRecommendation dagilimi:")
        rows = session.execute(
            select(repo.model.recommendation, func.count().label("n"))
            .group_by(repo.model.recommendation)
            .order_by(func.count().label("n").desc())
        ).all()
        for rec, n in rows:
            print(f"  {rec:15} {n:4}")

        # 4. Top 10 APPLY
        print("\nTop 10 APPLY firsati:")
        print("-" * 70)
        top = repo.get_top_opportunities(min_score=0, recommendation="APPLY", limit=10)

        if not top:
            # APPLY yoksa en yüksek skorluları al
            top = list(session.execute(
                select(repo.model).order_by(repo.model.career_score.desc()).limit(10)
            ).scalars().all())

        for i, s in enumerate(top, 1):
            company = s.explanation.get("company", "?") if s.explanation else "?"
            print(f"\n{i:2}. {company} — {s.career_score:.1f}/100")
            print(f"    Fit:{s.fit_score:.1f} Accept:{s.acceptance_probability:.1f}% "
                  f"Career:{s.career_value:.1f} Market:{s.market_demand:.1f}")
            print(f"    EV:{s.expected_value:.1f} | {s.recommendation}")
            if s.skill_gaps:
                print(f"    Gaps: {', '.join(s.skill_gaps[:5])}")
            print(f"    {s.url[:80]}")

        # 5. Skill gap aggregation (JSONB unnest)
        print("\n\nEn sik eksik skill'ler (son scan):")
        print("-" * 70)
        rows = session.execute(text("""
            WITH gaps AS (
                SELECT jsonb_array_elements_text(skill_gaps) AS skill
                FROM career_scores
                WHERE scanned_at = (SELECT MAX(scanned_at) FROM career_scores)
            )
            SELECT skill, COUNT(*) AS freq
            FROM gaps
            GROUP BY skill
            ORDER BY freq DESC
            LIMIT 10
        """)).all()
        for skill, freq in rows:
            print(f"  {skill:25} {freq:3} is ilaninda eksik")

        # 6. Örnek tam kayıt
        if top:
            s = top[0]
            print("\n\nOrnek kayit detayi:")
            print("-" * 70)
            print(f"URL:         {s.url}")
            print(f"Scanned at:  {s.scanned_at}")
            print(f"Scores:      career={s.career_score:.2f} fit={s.fit_score:.2f} "
                  f"accept={s.acceptance_probability:.2f} value={s.career_value:.2f}")
            print(f"Expected EV: {s.expected_value:.2f}")
            print(f"Rec:         {s.recommendation}")
            print(f"Skill gaps:  {s.skill_gaps}")
            print(f"Explanation: {s.explanation}")


if __name__ == "__main__":
    main()
