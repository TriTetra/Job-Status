"""
ApplyPilot Excel Exporter
-------------------------
Başvurulan işleri aylık Excel raporlarına dönüştürür.

Kullanım:
    python export_to_excel.py
    python export_to_excel.py --month 2026-06  # Sadece Haziran 2026
"""

import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
import json

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:
    print("❌ openpyxl kütüphanesi gerekli!")
    print("📦 Kurulum: pip install openpyxl")
    exit(1)


def get_database_path():
    """ApplyPilot veritabanı yolunu bul"""
    db_path = Path.home() / ".applypilot" / "applypilot.db"
    if not db_path.exists():
        db_path = Path("applypilot.db")
    return db_path


def get_month_name_tr(month):
    """Türkçe ay isimleri"""
    months = {
        1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
        5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
        9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
    }
    return months.get(month, str(month))


def extract_key_requirements(full_description, max_items=5):
    """İş açıklamasından önemli gereksinimleri çıkar"""
    if not full_description:
        return ""

    import re

    requirements = []

    # Requirements bölümünü bul
    patterns = [
        r"(?i)requirements?:?\s*\n(.*?)(?:\n\n|\Z)",
        r"(?i)qualifications?:?\s*\n(.*?)(?:\n\n|\Z)",
        r"(?i)must have:?\s*\n(.*?)(?:\n\n|\Z)",
    ]

    for pattern in patterns:
        matches = re.findall(pattern, full_description, re.DOTALL)
        for match in matches:
            bullets = re.findall(r"[•\-\*]\s*(.+)", match)
            if bullets:
                requirements.extend(bullets[:max_items])
                break

    # Tekrarlananları temizle ve kısalt
    unique_reqs = []
    for req in requirements[:max_items]:
        cleaned = req.strip()[:200]  # Max 200 karakter
        if cleaned and cleaned not in unique_reqs:
            unique_reqs.append(cleaned)

    return "\n".join(f"• {req}" for req in unique_reqs[:max_items])


def export_to_excel(month_filter=None):
    """
    Başvuruları Excel'e aktar

    Args:
        month_filter: YYYY-MM formatında (örn: "2026-06"), None ise tümü
    """
    db_path = get_database_path()

    if not db_path.exists():
        print(f"❌ Veritabanı bulunamadı: {db_path}")
        print("💡 Önce ApplyPilot çalıştırılmalı: applypilot run")
        return

    print(f"📂 Veritabanı: {db_path}")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Veriyi çek
    if month_filter:
        # Belirli bir ay
        query = """
            SELECT
                url, title, site, location, salary,
                full_description, fit_score, score_reasoning,
                discovered_at, scored_at, applied_at,
                apply_status, apply_error,
                tailored_resume_path, cover_letter_path
            FROM jobs
            WHERE strftime('%Y-%m', discovered_at) = ?
            ORDER BY discovered_at DESC
        """
        cursor.execute(query, (month_filter,))
        jobs = cursor.fetchall()
        filename_suffix = month_filter
    else:
        # Tüm veriler
        query = """
            SELECT
                url, title, site, location, salary,
                full_description, fit_score, score_reasoning,
                discovered_at, scored_at, applied_at,
                apply_status, apply_error,
                tailored_resume_path, cover_letter_path
            FROM jobs
            ORDER BY discovered_at DESC
        """
        cursor.execute(query)
        jobs = cursor.fetchall()
        filename_suffix = "all"

    if not jobs:
        print(f"❌ {month_filter or 'Hiçbir'} ayına ait iş bulunamadı!")
        conn.close()
        return

    print(f"✅ {len(jobs)} iş bulundu")

    # Excel dosyası oluştur
    wb = openpyxl.Workbook()

    # 1. Sayfa: Özet (Summary)
    ws_summary = wb.active
    ws_summary.title = "Özet"
    create_summary_sheet(ws_summary, jobs, month_filter)

    # 2. Sayfa: Tüm Başvurular (All Applications)
    ws_all = wb.create_sheet("Tüm Başvurular")
    create_applications_sheet(ws_all, jobs, show_all=True)

    # 3. Sayfa: Başvurulan İşler (Applied Only)
    applied_jobs = [j for j in jobs if j['applied_at']]
    if applied_jobs:
        ws_applied = wb.create_sheet("Başvurulanlar")
        create_applications_sheet(ws_applied, applied_jobs, show_all=False)

    # 4. Sayfa: Yüksek Skorlular (High Score)
    high_score = [j for j in jobs if j['fit_score'] and j['fit_score'] >= 8]
    if high_score:
        ws_high = wb.create_sheet("Yüksek Skor (8+)")
        create_applications_sheet(ws_high, high_score, show_all=False)

    # Dosyayı kaydet
    output_dir = Path("excel_exports")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"applypilot_basvurular_{filename_suffix}_{timestamp}.xlsx"

    wb.save(output_file)
    print(f"📊 Excel dosyası oluşturuldu: {output_file}")

    conn.close()
    return output_file


def create_summary_sheet(ws, jobs, month_filter):
    """Özet sayfası oluştur"""
    # Başlık
    ws['A1'] = "ApplyPilot - İş Başvuruları Özet Raporu"
    ws['A1'].font = Font(size=16, bold=True)
    ws.merge_cells('A1:D1')

    # Tarih
    ws['A3'] = "Rapor Tarihi:"
    ws['B3'] = datetime.now().strftime("%d.%m.%Y %H:%M")

    if month_filter:
        year, month = month_filter.split('-')
        month_name = get_month_name_tr(int(month))
        ws['A4'] = "Dönem:"
        ws['B4'] = f"{month_name} {year}"

    # İstatistikler
    total = len(jobs)
    applied = sum(1 for j in jobs if j['applied_at'])
    pending = total - applied
    high_score = sum(1 for j in jobs if j['fit_score'] and j['fit_score'] >= 8)

    stats_start = 6
    ws[f'A{stats_start}'] = "📊 İSTATİSTİKLER"
    ws[f'A{stats_start}'].font = Font(bold=True, size=12)

    stats = [
        ("Toplam İş İlanı:", total),
        ("✅ Başvurulan:", applied),
        ("⏳ Bekleyen:", pending),
        ("⭐ Yüksek Skor (8+):", high_score),
    ]

    for i, (label, value) in enumerate(stats, start=stats_start + 1):
        ws[f'A{i}'] = label
        ws[f'B{i}'] = value
        ws[f'A{i}'].font = Font(bold=True)

    # Site bazında dağılım
    site_start = stats_start + len(stats) + 2
    ws[f'A{site_start}'] = "🌐 SİTE BAZINDA DAĞILIM"
    ws[f'A{site_start}'].font = Font(bold=True, size=12)

    from collections import Counter
    site_counts = Counter(j['site'] for j in jobs)

    for i, (site, count) in enumerate(site_counts.most_common(), start=site_start + 1):
        ws[f'A{i}'] = site
        ws[f'B{i}'] = count

    # Sütun genişlikleri
    ws.column_dimensions['A'].width = 30
    ws.column_dimensions['B'].width = 20


def create_applications_sheet(ws, jobs, show_all=True):
    """Başvuru detayları sayfası oluştur"""
    # Başlıklar
    headers = [
        "Başvuru Tarihi",
        "İş Unvanı",
        "Şirket/Site",
        "Lokasyon",
        "Ülke",
        "Maaş",
        "Fit Skoru",
        "Durum",
        "Önemli Gereksinimler",
        "Link",
    ]

    # Başlık satırı
    for col, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col)
        cell.value = header
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Veri satırları
    for row_idx, job in enumerate(jobs, start=2):
        # Tarihi parse et
        applied_date = ""
        if job['applied_at']:
            try:
                dt = datetime.fromisoformat(job['applied_at'].replace('Z', '+00:00'))
                applied_date = dt.strftime("%d.%m.%Y %H:%M")
            except:
                applied_date = job['applied_at'][:10] if job['applied_at'] else ""
        elif job['discovered_at']:
            try:
                dt = datetime.fromisoformat(job['discovered_at'].replace('Z', '+00:00'))
                applied_date = dt.strftime("%d.%m.%Y")
            except:
                applied_date = job['discovered_at'][:10] if job['discovered_at'] else ""

        # Lokasyon ve ülke ayır
        location = job['location'] or ""
        country = ""
        if location and ',' in location:
            parts = location.split(',')
            country = parts[-1].strip()
            location = ','.join(parts[:-1]).strip()

        # Durum
        if job['applied_at']:
            status = job['apply_status'] or "✅ Başvuruldu"
        else:
            status = "⏳ Bekliyor"

        # Gereksinimler
        requirements = extract_key_requirements(job['full_description'])

        # Satırı doldur
        row_data = [
            applied_date,
            job['title'],
            job['site'],
            location,
            country,
            job['salary'] or "Belirtilmemiş",
            job['fit_score'] or "-",
            status,
            requirements,
            job['url'],
        ]

        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.value = value

            # Alignment
            if col_idx in [7]:  # Skor ortala
                cell.alignment = Alignment(horizontal="center")
            elif col_idx == 9:  # Gereksinimler
                cell.alignment = Alignment(wrap_text=True, vertical="top")

            # Renklendirme
            if col_idx == 7 and isinstance(value, int):  # Skor
                if value >= 9:
                    cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                elif value >= 7:
                    cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")

    # Sütun genişlikleri
    ws.column_dimensions['A'].width = 18  # Tarih
    ws.column_dimensions['B'].width = 35  # İş Unvanı
    ws.column_dimensions['C'].width = 15  # Site
    ws.column_dimensions['D'].width = 25  # Lokasyon
    ws.column_dimensions['E'].width = 15  # Ülke
    ws.column_dimensions['F'].width = 20  # Maaş
    ws.column_dimensions['G'].width = 10  # Skor
    ws.column_dimensions['H'].width = 20  # Durum
    ws.column_dimensions['I'].width = 60  # Gereksinimler
    ws.column_dimensions['J'].width = 15  # Link

    # Satır yükseklikleri
    ws.row_dimensions[1].height = 30
    for row in range(2, len(jobs) + 2):
        ws.row_dimensions[row].height = 80

    # Freeze başlık
    ws.freeze_panes = "A2"


def main():
    parser = argparse.ArgumentParser(description="ApplyPilot verilerini Excel'e aktar")
    parser.add_argument(
        "--month",
        "-m",
        help="Belirli bir ay için filtrele (YYYY-MM formatında, örn: 2026-06)",
        type=str,
        default=None
    )

    args = parser.parse_args()

    export_to_excel(month_filter=args.month)


if __name__ == "__main__":
    main()
