#!/usr/bin/env python3
"""
ApplyPilot Schedule Helper
---------------------------
Ne zaman tarama yapman gerektiğini gösterir.

Kullanım:
    python scripts/schedule_info.py
"""

import json
from pathlib import Path
from datetime import datetime, timedelta


def get_last_run():
    """Son tarama zamanını bul"""
    history_file = Path(__file__).parent.parent / "logs" / "run_history.json"

    if not history_file.exists():
        return None

    with open(history_file, 'r', encoding='utf-8') as f:
        history = json.load(f)

    if not history:
        return None

    last_run = history[-1]
    return datetime.fromisoformat(last_run['timestamp'])


def main():
    """Ana fonksiyon"""
    print("\n" + "=" * 70)
    print("  📅 ApplyPilot Schedule Information")
    print("=" * 70 + "\n")

    last_run = get_last_run()

    if not last_run:
        print("❌ No previous scans found!")
        print("💡 Run your first scan: python scripts/run_full_scan.py\n")
        return

    # Calculate time since last run
    now = datetime.now()
    time_since = now - last_run
    hours_since = time_since.total_seconds() / 3600
    days_since = time_since.days

    print(f"📊 Last Scan: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Time Since: {days_since} days, {int(hours_since % 24)} hours ago\n")

    # Recommendation
    print("📋 RECOMMENDATION:\n")

    if hours_since < 72:
        # Too soon
        next_recommended = last_run + timedelta(days=3)
        hours_until = (next_recommended - now).total_seconds() / 3600

        print(f"⏳ Next scan recommended: {next_recommended.strftime('%Y-%m-%d %H:%M')}")
        print(f"   ({int(hours_until)} hours from now)")
        print(f"\n💡 Wait a bit - most jobs update every 3 days!")

    elif hours_since < 96:
        # Good time
        print("✅ GOOD TIME TO SCAN!")
        print(f"   It's been {days_since} days since last scan")
        print(f"\n🚀 Run: python scripts/run_full_scan.py")

    else:
        # Overdue
        print("⚠️  SCAN OVERDUE!")
        print(f"   It's been {days_since} days - you might miss new jobs!")
        print(f"\n🚀 Run NOW: python scripts/run_full_scan.py")

    # Schedule suggestion
    print("\n" + "-" * 70)
    print("📅 SUGGESTED SCHEDULE (3-day cycle):\n")

    print("   • Monday 9 AM    → New week jobs")
    print("   • Thursday 9 AM  → Mid-week updates")
    print("   • Sunday 6 PM    → Weekend preparation")

    print("\n💡 TIP: Set Windows Task Scheduler to auto-run every 3 days!")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
