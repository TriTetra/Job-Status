#!/usr/bin/env python3
"""
Job Application Tracker
------------------------
Excel ve Markdown'dan başvuru takibi yapar.

Kullanım:
    python scripts/track_applications.py
"""

import openpyxl
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# ============================================================================
# CONFIG
# ============================================================================

REPORTS_DIR = Path(__file__).parent.parent / "reports"
TRACKER_MD = Path(__file__).parent.parent / "JOB_APPLICATIONS.md"


# ============================================================================
# FUNCTIONS
# ============================================================================

def find_latest_excel():
    """En son Excel raporunu bul"""
    excel_files = list(REPORTS_DIR.rglob("applypilot_advanced_*.xlsx"))
    if not excel_files:
        return None

    return max(excel_files, key=lambda p: p.stat().st_mtime)


def read_applications_from_excel(excel_path):
    """Excel'den başvuru yapılacak işleri oku"""

    wb = openpyxl.load_workbook(excel_path, read_only=True)

    # Perfect Match sheet
    ws = wb["🎯 Perfect Match (8+)"]

    jobs = []

    # Skip header
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[1]:  # Job title boşsa skip
            continue

        job = {
            'title': row[1],  # Job Title
            'company': row[3],  # Site (company bilgisi yok, site kullan)
            'location': row[4],  # Location
            'remote': row[5],  # Remote?
            'salary': row[6],  # Salary
            'score': row[7],  # Score
            'apply_link': row[16],  # Apply Link
            'notes': row[17] or "",  # Notes
        }

        jobs.append(job)

    wb.close()
    return jobs


def analyze_status(jobs):
    """İşlerin durumunu analiz et (Notes kolonundan)"""

    stats = defaultdict(int)
    categorized = {
        'to_apply': [],
        'applied': [],
        'response': [],
        'interview': [],
        'offer': [],
        'rejected': []
    }

    for job in jobs:
        notes = job['notes'].lower() if job['notes'] else ""

        # Kategorize et
        if 'applied' in notes or 'başvur' in notes:
            categorized['applied'].append(job)
            stats['applied'] += 1
        elif 'reject' in notes or 'red' in notes:
            categorized['rejected'].append(job)
            stats['rejected'] += 1
        elif 'interview' in notes or 'görüşme' in notes:
            categorized['interview'].append(job)
            stats['interview'] += 1
        elif 'offer' in notes or 'teklif' in notes:
            categorized['offer'].append(job)
            stats['offer'] += 1
        elif 'response' in notes or 'cevap' in notes:
            categorized['response'].append(job)
            stats['response'] += 1
        else:
            categorized['to_apply'].append(job)
            stats['to_apply'] += 1

    return stats, categorized


def update_tracker_md(stats, categorized):
    """JOB_APPLICATIONS.md dosyasını güncelle"""

    # Read template
    with open(TRACKER_MD, 'r', encoding='utf-8') as f:
        content = f.read()

    # Update overview stats
    overview = f"""| Status | Count |
|--------|-------|
| 📝 To Apply | {stats['to_apply']} |
| ✉️ Applied | {stats['applied']} |
| 📧 Response Received | {stats['response']} |
| 📞 Interview Scheduled | {stats['interview']} |
| ✅ Offer Received | {stats['offer']} |
| ❌ Rejected | {stats['rejected']} |"""

    # Find and replace overview section
    import re
    content = re.sub(
        r'\| Status \| Count \|.*?\| ❌ Rejected \| \d+ \|',
        overview,
        content,
        flags=re.DOTALL
    )

    # Update last updated
    today = datetime.now().strftime("%Y-%m-%d")
    content = re.sub(
        r'\*\*Last Updated:\*\* \d{4}-\d{2}-\d{2}',
        f'**Last Updated:** {today}',
        content
    )

    # Write back
    with open(TRACKER_MD, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ JOB_APPLICATIONS.md updated!")


def generate_summary():
    """Özet rapor oluştur"""

    excel_path = find_latest_excel()

    if not excel_path:
        print("❌ No Excel report found!")
        print("💡 Run: python scripts/run_full_scan.py")
        return

    print(f"📊 Reading: {excel_path.name}\n")

    jobs = read_applications_from_excel(excel_path)
    stats, categorized = analyze_status(jobs)

    print("=" * 70)
    print("  📋 APPLICATION TRACKER SUMMARY")
    print("=" * 70)
    print()

    print("📊 CURRENT STATUS:")
    print("-" * 70)
    print(f"  📝 To Apply:             {stats['to_apply']:3} jobs")
    print(f"  ✉️  Applied:              {stats['applied']:3} jobs")
    print(f"  📧 Response Received:    {stats['response']:3} jobs")
    print(f"  📞 Interview Scheduled:  {stats['interview']:3} jobs")
    print(f"  ✅ Offer Received:       {stats['offer']:3} jobs")
    print(f"  ❌ Rejected:             {stats['rejected']:3} jobs")
    print()

    # Response rate
    if stats['applied'] > 0:
        response_rate = (stats['response'] + stats['interview']) / stats['applied'] * 100
        print(f"  📈 Response Rate:        {response_rate:.1f}%")

    # Interview rate
    if stats['applied'] > 0:
        interview_rate = stats['interview'] / stats['applied'] * 100
        print(f"  📈 Interview Rate:       {interview_rate:.1f}%")

    print()

    # Next actions
    print("🎯 NEXT ACTIONS:")
    print("-" * 70)

    if stats['to_apply'] > 0:
        print(f"  1. Apply to {min(10, stats['to_apply'])} jobs from To Apply list")

    if stats['applied'] > 0:
        days_since = 3  # Example
        print(f"  2. Follow up on {stats['applied']} applications (if >7 days)")

    if stats['interview'] > 0:
        print(f"  3. Prepare for {stats['interview']} upcoming interviews")

    print()

    # Top priority jobs
    if categorized['to_apply']:
        print("🔥 TOP PRIORITY (To Apply):")
        print("-" * 70)

        for i, job in enumerate(categorized['to_apply'][:5], 1):
            print(f"  {i}. {job['title'][:45]:<45} | Score: {job['score']}")

        if len(categorized['to_apply']) > 5:
            print(f"     ... and {len(categorized['to_apply']) - 5} more")

    print()
    print("=" * 70)
    print()

    # Update markdown
    update_tracker_md(stats, categorized)

    print("💡 Next steps:")
    print("   1. Open Excel and add notes to 'Notes' column")
    print("   2. Mark applied jobs: 'Applied 2026-06-23'")
    print("   3. Run this script again to update tracker")
    print()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    generate_summary()
