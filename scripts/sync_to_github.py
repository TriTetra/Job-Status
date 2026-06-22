#!/usr/bin/env python3
"""
Sync Jobs to GitHub Issues
---------------------------
Excel'deki işleri GitHub Issues'a senkronize eder.

Requires:
    pip install PyGithub

Kullanım:
    python scripts/sync_to_github.py
"""

import openpyxl
from pathlib import Path
import os

try:
    from github import Github
except ImportError:
    print("❌ PyGithub gerekli!")
    print("📦 Kurulum: pip install PyGithub")
    exit(1)


# ============================================================================
# CONFIG
# ============================================================================

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_NAME = "YOUR_USERNAME/applypilot-jobs"  # Değiştir!

REPORTS_DIR = Path(__file__).parent.parent / "reports"


# ============================================================================
# FUNCTIONS
# ============================================================================

def find_latest_excel():
    """En son Excel'i bul"""
    excel_files = list(REPORTS_DIR.rglob("applypilot_advanced_*.xlsx"))
    if not excel_files:
        return None
    return max(excel_files, key=lambda p: p.stat().st_mtime)


def create_issue_for_job(repo, job):
    """Bir iş için GitHub Issue oluştur"""

    # Issue title
    title = f"{job['title']} - {job['company']}"

    # Issue body
    body = f"""
## 📋 Job Details

- **Company:** {job['company']}
- **Location:** {job['location']}
- **Remote:** {job['remote']}
- **Salary:** {job['salary']}
- **Fit Score:** {job['score']}/10

## 🎯 Why Good Match

{job['why_score']}

## ✅ Matching Skills

{job['your_skills']}

## ❌ Missing Skills

{job['missing_skills']}

## 📊 Match Percentage

{job['match_pct']}

## 📝 Requirements

{job['requirements']}

## 🔗 Apply

[Apply Here]({job['apply_link']})

---

**Found:** {job['posted_date']}
**Source:** ApplyPilot Auto-Scan
"""

    # Labels
    labels = []

    if job['score'] >= 8:
        labels.append('score-8+')
    elif job['score'] >= 7:
        labels.append('score-7')

    if job['remote'] == 'Remote':
        labels.append('remote')

    # Determine job type
    title_lower = job['title'].lower()
    if any(word in title_lower for word in ['ml', 'ai', 'machine learning', 'computer vision']):
        labels.append('ml-ai')
    elif 'backend' in title_lower:
        labels.append('backend')
    elif 'full stack' in title_lower or 'fullstack' in title_lower:
        labels.append('full-stack')

    # Create issue
    issue = repo.create_issue(
        title=title,
        body=body,
        labels=labels
    )

    return issue


def sync_jobs():
    """Excel'den GitHub Issues'a senkronize et"""

    if not GITHUB_TOKEN:
        print("❌ GITHUB_TOKEN environment variable gerekli!")
        print("💡 GitHub → Settings → Developer settings → Personal access tokens")
        print("💡 Scopes: repo (full)")
        print()
        print("Kullanım:")
        print("  export GITHUB_TOKEN=your_token")
        print("  python scripts/sync_to_github.py")
        return

    excel_path = find_latest_excel()
    if not excel_path:
        print("❌ Excel bulunamadı!")
        return

    print(f"📊 Reading: {excel_path.name}")

    # Connect to GitHub
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)

    print(f"✅ Connected to: {REPO_NAME}")

    # Read Excel
    wb = openpyxl.load_workbook(excel_path, read_only=True)
    ws = wb["🎯 Perfect Match (8+)"]

    jobs_created = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row[1]:  # No title
            continue

        job = {
            'posted_date': row[0],
            'title': row[1],
            'company': row[3],
            'location': row[4],
            'remote': row[5],
            'salary': row[6],
            'score': row[7],
            'why_score': row[8],
            'requirements': row[9],
            'your_skills': row[10],
            'missing_skills': row[11],
            'match_pct': row[12],
            'apply_link': row[16],
        }

        # Check if issue already exists
        existing = list(repo.get_issues(state='all', labels=['applypilot']))

        exists = False
        for issue in existing:
            if job['title'] in issue.title:
                exists = True
                break

        if exists:
            print(f"⏭️  Skip (exists): {job['title'][:50]}")
            continue

        # Create issue
        issue = create_issue_for_job(repo, job)
        jobs_created += 1

        print(f"✅ Created #{issue.number}: {job['title'][:50]}")

    wb.close()

    print()
    print(f"🎉 Done! Created {jobs_created} issues")
    print(f"🔗 View: https://github.com/{REPO_NAME}/issues")


if __name__ == "__main__":
    sync_jobs()
