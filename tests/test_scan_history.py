"""
Phase 1C doğrulama — scan_history tablosunu kontrol et.

Kullanım:
    python scripts/test_scan_history.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import Integer, cast, func, select

from core.db.connection import db
from core.db.repositories import ScanHistoryRepository


def main():
    print("=" * 70)
    print("  SCAN HISTORY TEST")
    print("=" * 70)

    with db.session_scope() as session:
        repo = ScanHistoryRepository(session)

        # 1. Toplam kayıt
        total = session.execute(
            select(func.count()).select_from(repo.model)
        ).scalar()
        print(f"\nToplam scan_history kaydi: {total}")

        if total == 0:
            print("scan_history bos! Once run_full_scan.py calistir.")
            return

        # 2. Kac farkli scan?
        unique_scans = session.execute(
            select(func.count(func.distinct(repo.model.scanned_at)))
        ).scalar()
        print(f"Farkli scan sayisi:        {unique_scans}")

        # 3. Son scan zamani
        latest_scan = session.execute(
            select(func.max(repo.model.scanned_at))
        ).scalar()
        print(f"Son scan:                  {latest_scan}")

        # 4. Son scan'de yeni job'lar
        if latest_scan:
            new_jobs = repo.get_new_this_scan(latest_scan)
            print(f"\nSon scan'de yeni:   {len(new_jobs)} job")

            if new_jobs:
                print("   Top 5 yeni job (score sirasi):")
                for job in sorted(new_jobs, key=lambda x: x.applypilot_score or 0, reverse=True)[:5]:
                    print(f"   - score {job.applypilot_score}: {job.url[:65]}")

        # 5. Son 7 gunun ozeti
        print("\nSon 7 gun:")
        print("-" * 70)
        cutoff = datetime.utcnow() - timedelta(days=7)

        scans_last_7 = session.execute(
            select(func.count(func.distinct(repo.model.scanned_at)))
            .where(repo.model.scanned_at >= cutoff)
        ).scalar()

        new_last_7 = session.execute(
            select(func.count())
            .where(repo.model.scanned_at >= cutoff)
            .where(repo.model.discovered_in_this_scan.is_(True))
        ).scalar()

        avg_score = session.execute(
            select(func.avg(repo.model.applypilot_score))
            .where(repo.model.scanned_at >= cutoff)
        ).scalar()

        print(f"  Scan sayisi:        {scans_last_7}")
        print(f"  Yeni job sayisi:    {new_last_7}")
        if avg_score:
            print(f"  Avg ApplyPilot sk.: {avg_score:.1f}")

        # 6. Scan basina ozet (son 3 scan)
        if unique_scans > 1:
            print("\nScan trendi (son 3 scan):")
            print("-" * 70)
            rows = session.execute(
                select(
                    repo.model.scanned_at,
                    func.count().label("total"),
                    func.sum(cast(repo.model.discovered_in_this_scan, Integer)).label("new"),
                )
                .group_by(repo.model.scanned_at)
                .order_by(repo.model.scanned_at.desc())
                .limit(3)
            ).all()

            for scan_time, total_jobs, new_count in rows:
                print(f"  {scan_time.strftime('%Y-%m-%d %H:%M')} | "
                      f"total={total_jobs:3}  new={new_count or 0:3}")

        # 7. Persistent job'lar (3+ scan'de gorulen)
        print("\nPersistent jobs (3+ scan'de gorulen):")
        print("-" * 70)
        persistent = session.execute(
            select(
                repo.model.url,
                func.count().label("scan_count"),
                func.max(repo.model.applypilot_score).label("max_score"),
            )
            .group_by(repo.model.url)
            .having(func.count() >= 3)
            .order_by(func.count().desc())
            .limit(10)
        ).all()

        if persistent:
            for url, scan_count, max_score in persistent:
                print(f"  {scan_count}x | score {max_score} | {url[:55]}...")
        else:
            print("  (Henuz 3+ scan'de gorulen job yok)")


if __name__ == "__main__":
    main()
