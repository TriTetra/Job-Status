#!/usr/bin/env python3
"""
ApplyPilot Full Scan
--------------------
Tam otomatik iş tarama sistemi.

3 günde bir çalıştır:
- Yeni işleri bul
- Puanla
- Filtrele
- Excel raporu oluştur
- Backup al

Kullanım:
    python scripts/scan/run_full_scan.py
"""

import subprocess
import sqlite3
import shutil
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = Path(__file__).parent.parent.parent
APPLYPILOT_DB = Path.home() / ".applypilot" / "applypilot.db"
APPLYPILOT_EXE = PROJECT_ROOT / "venv" / "Scripts" / "applypilot.exe"

REPORTS_DIR = PROJECT_ROOT / "reports"
LOGS_DIR = PROJECT_ROOT / "logs"
BACKUPS_DIR = PROJECT_ROOT / "backups"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def log(message, level="INFO"):
    """Log mesajı hem ekrana hem dosyaya yaz"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] [{level}] {message}"

    print(log_msg)

    # Log dosyasına yaz
    log_file = LOGS_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_msg + "\n")


def run_command(cmd, description):
    """Komutu çalıştır ve sonucu logla"""
    log(f"Starting: {description}")
    log(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        log(f"✅ Success: {description}")
        return True, result.stdout

    except subprocess.CalledProcessError as e:
        log(f"❌ Failed: {description}", "ERROR")
        log(f"Error: {e.stderr}", "ERROR")
        return False, e.stderr


def get_db_stats():
    """Veritabanı istatistikleri"""
    if not APPLYPILOT_DB.exists():
        return None

    conn = sqlite3.connect(str(APPLYPILOT_DB))
    cursor = conn.cursor()

    stats = {}

    # Total jobs
    cursor.execute("SELECT COUNT(*) FROM jobs")
    stats['total'] = cursor.fetchone()[0]

    # By score
    cursor.execute("SELECT fit_score, COUNT(*) FROM jobs WHERE fit_score IS NOT NULL GROUP BY fit_score")
    stats['by_score'] = {row[0]: row[1] for row in cursor.fetchall()}

    # Recent (last 3 days)
    three_days_ago = (datetime.now() - timedelta(days=3)).isoformat()
    cursor.execute("SELECT COUNT(*) FROM jobs WHERE discovered_at >= ?", (three_days_ago,))
    stats['recent'] = cursor.fetchone()[0]

    conn.close()
    return stats


def load_jobs_from_applypilot() -> list:
    """Load all scored jobs from ApplyPilot DB for scan_history tracking."""
    if not APPLYPILOT_DB.exists():
        log("ApplyPilot DB not found", "WARNING")
        return []
    try:
        conn = sqlite3.connect(str(APPLYPILOT_DB))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT url, fit_score
            FROM jobs
            WHERE fit_score IS NOT NULL
            ORDER BY fit_score DESC
        """)
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        log(f"Loaded {len(jobs)} jobs from ApplyPilot DB")
        return jobs
    except Exception as e:
        log(f"Failed to load jobs from ApplyPilot: {e}", "ERROR")
        return []


def _get_user_id() -> str:
    try:
        from career_os.config_loader import load_config
        return load_config().get("user", {}).get("id", "default")
    except Exception:
        return "default"


def track_scan_history(jobs: list, scanned_at: datetime):
    """Record which jobs appeared in this scan, marking new vs known."""
    from packages.db.connection import db
    from packages.db.repositories import ScanHistoryRepository

    if not jobs:
        log("No jobs to track", "WARNING")
        return

    user_id = _get_user_id()

    with db.session_scope() as session:
        repo = ScanHistoryRepository(session)
        known_urls = repo.get_all_known_urls(user_id=user_id)

        saved_count = 0
        new_count = 0
        failed_count = 0

        for job in jobs:
            sp = session.begin_nested()
            try:
                url = job["url"]
                is_new = url not in known_urls
                repo.record_scan(
                    user_id=user_id,
                    url=url,
                    applypilot_score=job.get("fit_score"),
                    career_os_score=None,
                    discovered_in_this_scan=is_new,
                    scanned_at=scanned_at,
                )
                sp.commit()
                saved_count += 1
                if is_new:
                    new_count += 1
            except Exception as e:
                sp.rollback()
                failed_count += 1
                if failed_count <= 5:
                    log(f"Failed to track {job.get('url', '?')[:60]}: {e}", "WARNING")

    log(f"Tracked {saved_count} jobs ({new_count} new, {failed_count} failed)")


def backup_database():
    """Veritabanını yedekle"""
    if not APPLYPILOT_DB.exists():
        log("No database to backup", "WARNING")
        return False

    backup_file = BACKUPS_DIR / f"db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite"

    try:
        shutil.copy2(APPLYPILOT_DB, backup_file)
        log(f"✅ Database backed up: {backup_file}")

        # Keep only last 10 backups
        backups = sorted(BACKUPS_DIR.glob("db_*.sqlite"), reverse=True)
        for old_backup in backups[10:]:
            old_backup.unlink()
            log(f"Deleted old backup: {old_backup.name}")

        return True
    except Exception as e:
        log(f"❌ Backup failed: {e}", "ERROR")
        return False


def create_report_directory():
    """Bugünün rapor klasörünü oluştur"""
    today = datetime.now().strftime("%Y-%m-%d")
    report_dir = REPORTS_DIR / today
    report_dir.mkdir(parents=True, exist_ok=True)

    # Latest symlink güncelle (Windows'ta shortcut)
    latest_link = REPORTS_DIR / "latest"
    if latest_link.exists():
        latest_link.unlink()

    # Windows'ta symlink yerine text file ile yönlendirme
    with open(latest_link.with_suffix('.txt'), 'w') as f:
        f.write(f"Latest report: {today}\n")
        f.write(f"Path: {report_dir}\n")

    return report_dir


def save_run_history(stats, duration, success):
    """Çalıştırma geçmişini kaydet"""
    history_file = LOGS_DIR / "run_history.json"

    # Load existing
    history = []
    if history_file.exists():
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)

    # Add new entry
    entry = {
        'timestamp': datetime.now().isoformat(),
        'duration_seconds': duration,
        'success': success,
        'stats': stats
    }

    history.append(entry)

    # Keep last 100 runs
    history = history[-100:]

    # Save
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def create_summary(stats, report_dir):
    """Özet rapor oluştur"""
    summary_file = report_dir / "summary.txt"

    content = f"""
ApplyPilot Scan Summary
=======================
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

DATABASE STATS:
--------------
Total Jobs: {stats['total']}
Recent (3 days): {stats['recent']}

Score Distribution:
"""

    for score in sorted(stats['by_score'].keys(), reverse=True):
        count = stats['by_score'][score]
        content += f"  Score {score}: {count} jobs\n"

    content += f"""

HIGH-PRIORITY JOBS:
------------------
Perfect Match (8+): {sum(v for k, v in stats['by_score'].items() if k >= 8)} jobs
Good Match (7): {stats['by_score'].get(7, 0)} jobs

NEXT STEPS:
----------
1. Open Excel report: {report_dir / 'applypilot_advanced_*.xlsx'}
2. Start with "Perfect Match (8+)" sheet
3. Apply to top jobs!

---
Generated by ApplyPilot Auto-Scan System
"""

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(content)

    log(f"✅ Summary saved: {summary_file}")


# ============================================================================
# MAIN SCAN FUNCTION
# ============================================================================

def run_full_scan():
    """Ana tarama fonksiyonu"""

    start_time = datetime.now()
    scan_timestamp = datetime.utcnow()

    log("=" * 80)
    log("🚀 APPLYPILOT FULL SCAN STARTED")
    log("=" * 80)

    success_overall = True

    # ========================================================================
    # STEP 1: Backup existing database
    # ========================================================================
    log("\n📦 STEP 1/7: Backing up database...")
    backup_database()

    # ========================================================================
    # STEP 2: Run discovery (find new jobs)
    # ========================================================================
    log("\n🔍 STEP 2/7: Discovering new jobs...")

    cmd = [str(APPLYPILOT_EXE), "run", "discover", "--hours-old", "72"]
    success, output = run_command(cmd, "Job Discovery")

    if not success:
        log("❌ Discovery failed, aborting scan", "ERROR")
        return False

    # ========================================================================
    # STEP 3: Run scoring (score all jobs)
    # ========================================================================
    log("\n⭐ STEP 3/7: Scoring jobs with AI...")

    cmd = [str(APPLYPILOT_EXE), "run", "score", "--min-score", "7"]
    success, output = run_command(cmd, "Job Scoring")

    if not success:
        log("❌ Scoring failed, but continuing...", "WARNING")
        success_overall = False

    # ========================================================================
    # STEP 4: Run filters (remove unwanted jobs)
    # ========================================================================
    log("\n🔧 STEP 4/7: Filtering jobs...")

    cmd = ["python", str(SCRIPT_DIR / "filter_jobs.py")]
    success, output = run_command(cmd, "Job Filtering")

    if not success:
        log("❌ Filtering failed, but continuing...", "WARNING")
        success_overall = False

    # ========================================================================
    # STEP 4.5: Track scan history
    # ========================================================================
    log("\n📋 STEP 4.5/7: Tracking scan history...")

    jobs = load_jobs_from_applypilot()
    if jobs:
        track_scan_history(jobs, scan_timestamp)
    else:
        log("No jobs to track in scan_history", "WARNING")

    # ========================================================================
    # STEP 5: Generate Excel report
    # ========================================================================
    log("\n📊 STEP 5/7: Generating Excel report...")

    report_dir = create_report_directory()

    cmd = ["python", str(SCRIPT_DIR / "export_to_excel_advanced.py")]
    success, output = run_command(cmd, "Excel Generation")

    if success:
        excel_files = list((PROJECT_ROOT / "excel_exports").glob("applypilot_advanced_*.xlsx"))
        if excel_files:
            latest_excel = max(excel_files, key=lambda p: p.stat().st_mtime)
            target = report_dir / latest_excel.name
            shutil.move(str(latest_excel), str(target))
            log(f"✅ Excel moved to: {target}")
    else:
        log("❌ Excel generation failed", "WARNING")
        success_overall = False

    # ========================================================================
    # STEP 6: Create summary and save history
    # ========================================================================
    log("\n📝 STEP 6/7: Creating summary...")

    stats = get_db_stats()
    if stats:
        create_summary(stats, report_dir)

    duration = (datetime.now() - start_time).total_seconds()
    save_run_history(stats, duration, success_overall)

    # ========================================================================
    # STEP 7: Scan history statistics
    # ========================================================================
    log("\n📈 STEP 7/7: Scan history statistics...")

    try:
        from packages.db.connection import db
        from packages.db.repositories import ScanHistoryRepository

        with db.session_scope() as session:
            repo = ScanHistoryRepository(session)
            new_jobs = repo.get_new_this_scan(scan_timestamp, user_id=_get_user_id())

            if new_jobs:
                log(f"New jobs in this scan: {len(new_jobs)}")
                top_new = sorted(new_jobs, key=lambda x: x.applypilot_score or 0, reverse=True)[:5]
                for job in top_new:
                    log(f"   • score {job.applypilot_score}: {job.url[:70]}")
            else:
                log("No new jobs this scan (all already known)")

    except Exception as e:
        log(f"Failed to show scan history stats: {e}", "WARNING")

    # ========================================================================
    # DONE
    # ========================================================================
    log("\n" + "=" * 80)

    if success_overall:
        log("✅ SCAN COMPLETED SUCCESSFULLY!")
    else:
        log("⚠️  SCAN COMPLETED WITH WARNINGS", "WARNING")

    log(f"⏱️  Duration: {duration:.1f} seconds")
    log(f"📊 Report: {report_dir}")

    if stats:
        log(f"\n📈 RESULTS:")
        log(f"   Total Jobs: {stats['total']}")
        log(f"   Perfect Match (8+): {sum(v for k, v in stats['by_score'].items() if k >= 8)}")
        log(f"   Good Match (7): {stats['by_score'].get(7, 0)}")

    log("=" * 80)

    return success_overall


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Create directories if needed
    REPORTS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    BACKUPS_DIR.mkdir(exist_ok=True)

    # Run scan
    try:
        success = run_full_scan()
        exit(0 if success else 1)
    except Exception as e:
        log(f"💥 FATAL ERROR: {e}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")
        exit(2)
