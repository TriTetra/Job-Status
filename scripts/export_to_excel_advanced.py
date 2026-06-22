"""
ApplyPilot Advanced Excel Exporter
-----------------------------------
Süper detaylı, analitik Excel raporu oluşturur.

Features:
- 6 farklı sayfa (Summary, Perfect Match, Good Match, Skills, Companies, Full DB)
- Her iş için 18+ kolon
- Skill matching analizi
- Renklendirme ve formatlama
- Grafikler ve istatistikler
- Clickable links

Kullanım:
    python export_to_excel_advanced.py
"""

import sqlite3
import re
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import json

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, Reference, PieChart
except ImportError:
    print("❌ openpyxl kütüphanesi gerekli!")
    print("📦 Kurulum: pip install openpyxl")
    exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Senin becerileriniz (config.yaml'dan)
YOUR_SKILLS = {
    'ml_ai': [
        'Machine Learning', 'Deep Learning', 'Computer Vision', 'PyTorch',
        'YOLOv8', 'OpenCV', 'NLP', 'LLM', 'Transformers', 'TensorFlow',
        'Neural Networks', 'CNN', 'RNN', 'Object Detection', 'MLOps'
    ],
    'backend': [
        'Python', 'Rust', 'Java', 'Go', 'Spring Boot', 'gRPC', 'REST API',
        'Microservices', 'FastAPI', 'Flask', 'Django', 'PostgreSQL', 'MongoDB',
        'Redis', 'Docker', 'Kubernetes'
    ],
    'full_stack': [
        'Next.js', 'React', 'TypeScript', 'JavaScript', 'Node.js',
        'HTML', 'CSS', 'Tailwind', 'API Design', 'Frontend'
    ],
    'tools': [
        'Git', 'Linux', 'AWS', 'GCP', 'Azure', 'CI/CD', 'GitHub Actions',
        'Jupyter', 'Pandas', 'NumPy', 'ROS', 'ROS2'
    ]
}

ALL_YOUR_SKILLS = []
for category in YOUR_SKILLS.values():
    ALL_YOUR_SKILLS.extend([s.lower() for s in category])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_database_path():
    """ApplyPilot veritabanı yolunu bul"""
    db_path = Path.home() / ".applypilot" / "applypilot.db"
    if not db_path.exists():
        db_path = Path("applypilot.db")
    return db_path


def extract_requirements(description):
    """İş açıklamasından gereksinimleri çıkar"""
    if not description:
        return []

    requirements = []

    # Requirements bölümünü bul
    patterns = [
        r"(?i)requirements?:?\s*\n(.*?)(?:\n\n|\Z)",
        r"(?i)qualifications?:?\s*\n(.*?)(?:\n\n|\Z)",
        r"(?i)must have:?\s*\n(.*?)(?:\n\n|\Z)",
        r"(?i)what you.?ll need:?\s*\n(.*?)(?:\n\n|\Z)",
        r"(?i)what we.?re looking for:?\s*\n(.*?)(?:\n\n|\Z)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, description, re.DOTALL)
        for match in matches:
            bullets = re.findall(r"[•\-\*]\s*(.+)", match)
            if bullets:
                requirements.extend([b.strip() for b in bullets[:15]])
                break

    # Eğer bulamazsa, "experience with", "proficiency in" gibi ifadeleri ara
    if not requirements:
        tech_patterns = [
            r"(?i)experience (?:with|in)\s+([^,\.\n]+)",
            r"(?i)proficiency (?:with|in)\s+([^,\.\n]+)",
            r"(?i)knowledge of\s+([^,\.\n]+)",
            r"(?i)skilled in\s+([^,\.\n]+)",
        ]

        for pattern in tech_patterns:
            matches = re.findall(pattern, description)
            requirements.extend([m.strip() for m in matches[:10]])

    # Temizle ve unique yap
    cleaned = []
    seen = set()
    for req in requirements:
        req_clean = req[:200].strip()
        req_lower = req_clean.lower()
        if req_clean and req_lower not in seen and len(req_clean) > 10:
            cleaned.append(req_clean)
            seen.add(req_lower)

    return cleaned[:10]  # İlk 10


def match_skills(requirements_text):
    """Gereksinimlerle becerilerini eşleştir"""
    if not requirements_text:
        return [], [], 0

    text_lower = requirements_text.lower()

    matched = []
    missing = []

    # Eşleşenleri bul
    for skill in ALL_YOUR_SKILLS:
        if skill in text_lower:
            matched.append(skill)

    # Yaygın teknolojileri ara (eksik olanlar için)
    common_techs = [
        'java', 'c++', 'scala', 'ruby', 'php', 'swift', 'kotlin',
        'angular', 'vue', 'svelte', 'spark', 'hadoop', 'airflow',
        'tableau', 'power bi', 'jenkins', 'terraform', 'ansible'
    ]

    for tech in common_techs:
        if tech in text_lower and tech not in ALL_YOUR_SKILLS:
            missing.append(tech)

    # Match percentage
    total_skills_mentioned = len(matched) + len(missing)
    match_pct = (len(matched) / total_skills_mentioned * 100) if total_skills_mentioned > 0 else 0

    return matched, missing, match_pct


def extract_years_experience(description):
    """İş açıklamasından deneyim gereksinimini çıkar"""
    if not description:
        return None

    patterns = [
        r'(\d+)\+?\s*years?.*(experience|background)',
        r'(\d+)\s*-\s*(\d+)\s*years',
        r'minimum.*(\d+).*years',
        r'at least.*(\d+).*years',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, description.lower())
        if matches:
            if isinstance(matches[0], tuple):
                return int(matches[0][0])
            return int(matches[0])

    return None


def is_remote(location):
    """Remote iş mi kontrol et"""
    if not location:
        return "Unknown"

    location_lower = location.lower()

    if any(word in location_lower for word in ['remote', 'work from home', 'anywhere']):
        return "Remote"
    elif 'hybrid' in location_lower:
        return "Hybrid"
    else:
        return "Onsite"


def extract_salary_range(salary_str):
    """Maaş string'inden min-max çıkar"""
    if not salary_str:
        return None, None

    # Sayıları bul
    numbers = re.findall(r'[\d,]+', salary_str)
    numbers = [int(n.replace(',', '')) for n in numbers]

    if len(numbers) >= 2:
        return min(numbers), max(numbers)
    elif len(numbers) == 1:
        return numbers[0], numbers[0]

    return None, None


# ============================================================================
# EXCEL BUILDERS
# ============================================================================

def create_summary_sheet(ws, jobs):
    """Executive Summary sayfası"""
    # Başlık
    ws['A1'] = "ApplyPilot - Executive Summary"
    ws['A1'].font = Font(size=18, bold=True, color="1F4E78")
    ws.merge_cells('A1:F1')

    # Tarih
    ws['A3'] = f"Report Date: {datetime.now().strftime('%B %d, %Y %H:%M')}"
    ws['A3'].font = Font(size=11, italic=True)

    # Temel İstatistikler
    total = len(jobs)
    score_8_plus = sum(1 for j in jobs if j['fit_score'] and j['fit_score'] >= 8)
    score_7 = sum(1 for j in jobs if j['fit_score'] and j['fit_score'] == 7)
    remote = sum(1 for j in jobs if 'remote' in (j['location'] or '').lower())

    ws['A5'] = "KEY METRICS"
    ws['A5'].font = Font(size=14, bold=True)

    metrics = [
        ("Total Jobs Discovered:", total),
        ("Perfect Match (8+ score):", score_8_plus),
        ("Good Match (7 score):", score_7),
        ("Remote Positions:", remote),
        ("Applications Ready:", score_8_plus + score_7),
    ]

    row = 6
    for label, value in metrics:
        ws[f'A{row}'] = label
        ws[f'B{row}'] = value
        ws[f'A{row}'].font = Font(bold=True)
        ws[f'B{row}'].font = Font(size=12, bold=True, color="0070C0")
        row += 1

    # Site breakdown
    ws['A12'] = "JOBS BY SITE"
    ws['A12'].font = Font(size=14, bold=True)

    site_counts = Counter(j['site'] for j in jobs)
    row = 13
    for site, count in site_counts.most_common():
        ws[f'A{row}'] = site
        ws[f'B{row}'] = count
        row += 1

    # Score distribution
    ws['D5'] = "SCORE DISTRIBUTION"
    ws['D5'].font = Font(size=14, bold=True)

    score_dist = Counter(j['fit_score'] for j in jobs if j['fit_score'])
    row = 6
    for score in sorted(score_dist.keys(), reverse=True):
        ws[f'D{row}'] = f"Score {score}"
        ws[f'E{row}'] = score_dist[score]

        # Color code
        if score >= 8:
            ws[f'E{row}'].fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        elif score == 7:
            ws[f'E{row}'].fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

        row += 1

    # Column widths
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['D'].width = 20
    ws.column_dimensions['E'].width = 15


def create_jobs_detail_sheet(ws, jobs, title="Jobs"):
    """Detaylı iş listesi sayfası"""

    # Headers
    headers = [
        "Posted", "Job Title", "Company", "Site", "Location",
        "Remote?", "Salary Range", "Fit Score", "Why This Score?",
        "Top Requirements", "✅ Your Skills", "❌ Missing Skills",
        "Match %", "Years Exp", "Sponsorship?", "Description",
        "Apply Link", "Notes"
    ]

    # Header row
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True, color="FFFFFF", size=11)
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Data rows
    for row_idx, job in enumerate(jobs, start=2):
        # Extract data
        posted_date = ""
        if job['discovered_at']:
            try:
                dt = datetime.fromisoformat(job['discovered_at'].replace('Z', '+00:00'))
                posted_date = dt.strftime("%Y-%m-%d")
            except:
                posted_date = job['discovered_at'][:10] if job['discovered_at'] else ""

        requirements = extract_requirements(job['full_description'])
        requirements_text = "\n".join(f"• {r}" for r in requirements) if requirements else "N/A"

        full_req_text = job['full_description'] or ""
        matched_skills, missing_skills, match_pct = match_skills(full_req_text)

        matched_text = ", ".join(matched_skills[:10]) if matched_skills else "None"
        missing_text = ", ".join(missing_skills[:5]) if missing_skills else "None"

        years_exp = extract_years_experience(job['full_description'])
        remote_status = is_remote(job['location'])

        # Sponsorship guess
        sponsorship = "Likely" if remote_status == "Remote" else "Ask"

        # Description summary (first 200 words)
        desc_summary = ""
        if job['full_description']:
            words = job['full_description'].split()[:200]
            desc_summary = ' '.join(words) + "..."

        salary_min, salary_max = extract_salary_range(job['salary'])
        salary_display = ""
        if salary_min and salary_max:
            if salary_min == salary_max:
                salary_display = f"${salary_min:,}"
            else:
                salary_display = f"${salary_min:,} - ${salary_max:,}"
        elif job['salary']:
            salary_display = job['salary']
        else:
            salary_display = "Not specified"

        # Row data
        row_data = [
            posted_date,
            job['title'],
            job['site'],  # We don't have company, use site
            job['site'],
            job['location'] or "Not specified",
            remote_status,
            salary_display,
            job['fit_score'] or "-",
            job['score_reasoning'] or "N/A",
            requirements_text,
            matched_text,
            missing_text,
            f"{match_pct:.0f}%" if match_pct > 0 else "0%",
            f"{years_exp}+ years" if years_exp else "Not specified",
            sponsorship,
            desc_summary,
            job['url'],
            ""  # Notes (empty for user to fill)
        ]

        # Write row
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = value

            # Alignment
            if col_idx in [8, 13]:  # Score, Match %
                cell.alignment = Alignment(horizontal="center", vertical="top")
            elif col_idx in [10, 11, 12, 16]:  # Long text columns
                cell.alignment = Alignment(wrap_text=True, vertical="top")
            else:
                cell.alignment = Alignment(vertical="top")

            # URL column - make clickable
            if col_idx == 17 and value:
                cell.hyperlink = value
                cell.font = Font(color="0563C1", underline="single")

        # Color coding by score
        score_cell = ws.cell(row=row_idx, column=8)
        if isinstance(score_cell.value, int):
            if score_cell.value >= 9:
                score_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                score_cell.font = Font(bold=True, color="006100")
            elif score_cell.value >= 8:
                score_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            elif score_cell.value == 7:
                score_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

        # Highlight remote jobs
        if remote_status == "Remote":
            ws.cell(row=row_idx, column=6).fill = PatternFill(start_color="DDEBF7", end_color="DDEBF7", fill_type="solid")

        # Highlight high salary
        if salary_max and salary_max >= 100000:
            ws.cell(row=row_idx, column=7).font = Font(bold=True, color="0070C0")

        # Highlight high match %
        if match_pct >= 70:
            ws.cell(row=row_idx, column=13).fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            ws.cell(row=row_idx, column=13).font = Font(bold=True, color="006100")

    # Column widths
    widths = [12, 40, 20, 12, 25, 10, 20, 10, 40, 50, 40, 30, 10, 15, 12, 60, 15, 30]
    for i, width in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = width

    # Row heights
    ws.row_dimensions[1].height = 40
    for row in range(2, len(jobs) + 2):
        ws.row_dimensions[row].height = 100

    # Freeze header
    ws.freeze_panes = "A2"


def create_skills_analysis_sheet(ws, jobs):
    """Skill analizi sayfası"""

    # Tüm job description'ları birleştir
    all_descriptions = " ".join([j['full_description'] or "" for j in jobs]).lower()

    # Skill frequency
    skill_freq = {}
    for category, skills in YOUR_SKILLS.items():
        for skill in skills:
            count = all_descriptions.count(skill.lower())
            if count > 0:
                skill_freq[skill] = count

    # Header
    ws['A1'] = "Skills Demand Analysis"
    ws['A1'].font = Font(size=16, bold=True)
    ws.merge_cells('A1:C1')

    ws['A3'] = "Skill"
    ws['B3'] = "Frequency"
    ws['C3'] = "Category"

    for col in ['A', 'B', 'C']:
        ws[f'{col}3'].font = Font(bold=True)
        ws[f'{col}3'].fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        ws[f'{col}3'].font = Font(bold=True, color="FFFFFF")

    # Data
    row = 4
    for skill, freq in sorted(skill_freq.items(), key=lambda x: x[1], reverse=True):
        # Find category
        category = ""
        for cat, skills in YOUR_SKILLS.items():
            if skill in skills:
                category = cat.replace('_', ' ').title()
                break

        ws[f'A{row}'] = skill
        ws[f'B{row}'] = freq
        ws[f'C{row}'] = category

        # Color code by frequency
        if freq >= 50:
            ws[f'B{row}'].fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
        elif freq >= 20:
            ws[f'B{row}'].fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

        row += 1

    # Column widths
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 20


def create_company_sheet(ws, jobs):
    """Şirket/site bazlı gruplandırma"""

    # Group by site
    by_site = defaultdict(list)
    for job in jobs:
        by_site[job['site']].append(job)

    # Header
    ws['A1'] = "Jobs by Company/Site"
    ws['A1'].font = Font(size=16, bold=True)
    ws.merge_cells('A1:D1')

    row = 3
    for site in sorted(by_site.keys()):
        site_jobs = by_site[site]

        ws[f'A{row}'] = site
        ws[f'A{row}'].font = Font(size=14, bold=True, color="0070C0")
        ws[f'B{row}'] = f"({len(site_jobs)} jobs)"
        row += 1

        # Sub-header
        ws[f'A{row}'] = "Job Title"
        ws[f'B{row}'] = "Location"
        ws[f'C{row}'] = "Score"
        ws[f'D{row}'] = "Link"

        for col in ['A', 'B', 'C', 'D']:
            ws[f'{col}{row}'].font = Font(bold=True)
            ws[f'{col}{row}'].fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")

        row += 1

        # Jobs
        for job in sorted(site_jobs, key=lambda x: x['fit_score'] or 0, reverse=True):
            ws[f'A{row}'] = job['title']
            ws[f'B{row}'] = job['location'] or "N/A"
            ws[f'C{row}'] = job['fit_score'] or "-"
            ws[f'D{row}'] = job['url']
            ws[f'D{row}'].hyperlink = job['url']
            ws[f'D{row}'].font = Font(color="0563C1", underline="single")

            # Color code score
            if job['fit_score'] and job['fit_score'] >= 8:
                ws[f'C{row}'].fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            elif job['fit_score'] and job['fit_score'] == 7:
                ws[f'C{row}'].fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

            row += 1

        row += 1  # Empty row between sites

    # Column widths
    ws.column_dimensions['A'].width = 50
    ws.column_dimensions['B'].width = 30
    ws.column_dimensions['C'].width = 10
    ws.column_dimensions['D'].width = 15


# ============================================================================
# MAIN EXPORT FUNCTION
# ============================================================================

def export_advanced_excel():
    """Ana export fonksiyonu"""

    db_path = get_database_path()

    if not db_path.exists():
        print(f"❌ Veritabanı bulunamadı: {db_path}")
        print("💡 Önce ApplyPilot çalıştırılmalı")
        return

    print(f"📂 Veritabanı: {db_path}")

    # Connect and fetch data
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM jobs
        WHERE fit_score >= 7
        ORDER BY fit_score DESC, discovered_at DESC
    """)

    jobs = [dict(row) for row in cursor.fetchall()]

    if not jobs:
        print("❌ 7+ puanlı iş bulunamadı!")
        conn.close()
        return

    print(f"✅ {len(jobs)} iş bulundu (7+ puan)")

    # Separate by score
    jobs_8_plus = [j for j in jobs if j['fit_score'] >= 8]
    jobs_7 = [j for j in jobs if j['fit_score'] == 7]

    print(f"   • 8+ puan: {len(jobs_8_plus)} iş")
    print(f"   • 7 puan: {len(jobs_7)} iş")

    # Create workbook
    print("\n📊 Excel oluşturuluyor...")
    wb = openpyxl.Workbook()

    # Remove default sheet
    wb.remove(wb.active)

    # 1. Executive Summary
    print("   1/6 Executive Summary...")
    ws_summary = wb.create_sheet("📊 Executive Summary")
    create_summary_sheet(ws_summary, jobs)

    # 2. Perfect Match (8+)
    print("   2/6 Perfect Match (8+)...")
    ws_perfect = wb.create_sheet("🎯 Perfect Match (8+)")
    create_jobs_detail_sheet(ws_perfect, jobs_8_plus, "Perfect Match")

    # 3. Good Match (7)
    print("   3/6 Good Match (7)...")
    ws_good = wb.create_sheet("✅ Good Match (7)")
    create_jobs_detail_sheet(ws_good, jobs_7, "Good Match")

    # 4. Skills Analysis
    print("   4/6 Skills Analysis...")
    ws_skills = wb.create_sheet("📈 Skills Analysis")
    create_skills_analysis_sheet(ws_skills, jobs)

    # 5. By Company
    print("   5/6 Company Breakdown...")
    ws_company = wb.create_sheet("🏢 By Company")
    create_company_sheet(ws_company, jobs)

    # 6. Full Database (all 7+ jobs)
    print("   6/6 Full Database...")
    ws_full = wb.create_sheet("📁 Full Database")
    create_jobs_detail_sheet(ws_full, jobs, "All Jobs")

    # Save
    output_dir = Path("excel_exports")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"applypilot_advanced_{timestamp}.xlsx"

    wb.save(output_file)

    print(f"\n🎉 BAŞARILI!")
    print(f"📊 Excel dosyası: {output_file}")
    print(f"\n📋 İçerik:")
    print(f"   • Executive Summary: Genel bakış ve istatistikler")
    print(f"   • Perfect Match (8+): {len(jobs_8_plus)} süper uygun iş")
    print(f"   • Good Match (7): {len(jobs_7)} iyi iş")
    print(f"   • Skills Analysis: Hangi beceriler popüler")
    print(f"   • By Company: Şirket bazlı gruplandırma")
    print(f"   • Full Database: Tüm işler")
    print(f"\n🎯 Sonraki adım: Excel'i aç ve başvurmaya başla!")

    conn.close()
    return output_file


if __name__ == "__main__":
    export_advanced_excel()
