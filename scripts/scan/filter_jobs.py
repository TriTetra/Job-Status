"""
ApplyPilot Job Filter
---------------------
Senin profiline uygun olmayan işleri otomatik filtreler.

Filtrelenenler:
- Senior/Lead/Principal pozisyonlar
- Standalone Frontend işler
- Freelance/Contract işler
- Intern/Internship işler
- Standalone JavaScript işler
- Analytics Engineer işler
- Onsite-only işler
- 4+ yıl deneyim gerektiren işler
- Security Clearance gerektiren işler

Kullanım:
    python scripts/scan/filter_jobs.py
"""

import sqlite3
import re
from pathlib import Path
from collections import defaultdict


def get_database_path():
    """ApplyPilot veritabanı yolunu bul"""
    db_path = Path.home() / ".applypilot" / "applypilot.db"
    if not db_path.exists():
        db_path = Path("applypilot.db")
    return db_path


def print_separator():
    print("=" * 80)


def filter_jobs():
    """Tüm filtreleri uygula"""
    db_path = get_database_path()

    if not db_path.exists():
        print(f"❌ Veritabanı bulunamadı: {db_path}")
        print("💡 Önce ApplyPilot çalıştırılmalı: applypilot run")
        return

    print(f"📂 Veritabanı: {db_path}")
    print()

    conn = sqlite3.connect(str(db_path))

    # Başlangıç durumu
    cursor = conn.execute('SELECT COUNT(*) FROM jobs WHERE fit_score >= 8')
    initial_8_count = cursor.fetchone()[0]
    cursor = conn.execute('SELECT COUNT(*) FROM jobs WHERE fit_score >= 7')
    initial_7_count = cursor.fetchone()[0]

    print("📊 BAŞLANGIÇ DURUMU:")
    print_separator()
    print(f"8+ puan: {initial_8_count} iş")
    print(f"7+ puan: {initial_7_count} iş")
    print()

    filtered_count = defaultdict(int)

    # =========================================================================
    # FİLTRE 1: SENIORITY (Senior/Lead/Principal/Staff/Director)
    # =========================================================================
    print("🔍 FİLTRE 1: Seniority (Senior/Lead/Principal...)")
    cursor = conn.execute('''
        SELECT COUNT(*) FROM jobs
        WHERE (
            title LIKE '%Senior%' OR
            title LIKE '%Lead %' OR
            title LIKE '%Principal%' OR
            title LIKE '%Staff Engineer%' OR
            title LIKE '%Director%'
        ) AND fit_score >= 7
    ''')
    count = cursor.fetchone()[0]
    filtered_count['seniority'] = count

    conn.execute('''
        UPDATE jobs SET fit_score = 4
        WHERE (
            title LIKE '%Senior%' OR
            title LIKE '%Lead %' OR
            title LIKE '%Principal%' OR
            title LIKE '%Staff Engineer%' OR
            title LIKE '%Director%'
        ) AND fit_score >= 7
    ''')
    print(f"   ✅ {count} iş filtrelendi")
    print()

    # =========================================================================
    # FİLTRE 2: STANDALONE FRONTEND
    # =========================================================================
    print("🔍 FİLTRE 2: Standalone Frontend (Full Stack hariç)")
    cursor = conn.execute('''
        SELECT COUNT(*) FROM jobs
        WHERE (
            (title LIKE '%Frontend%' OR title LIKE '%Front-End%' OR title LIKE '%React Developer%')
            AND title NOT LIKE '%Full%'
        ) AND fit_score >= 7
    ''')
    count = cursor.fetchone()[0]
    filtered_count['frontend'] = count

    conn.execute('''
        UPDATE jobs SET fit_score = 4
        WHERE (
            (title LIKE '%Frontend%' OR title LIKE '%Front-End%' OR title LIKE '%React Developer%')
            AND title NOT LIKE '%Full%'
        ) AND fit_score >= 7
    ''')
    print(f"   ✅ {count} iş filtrelendi")
    print()

    # =========================================================================
    # FİLTRE 3: FREELANCE/CONTRACT
    # =========================================================================
    print("🔍 FİLTRE 3: Freelance/Contract (sponsorship yok)")
    cursor = conn.execute('''
        SELECT COUNT(*) FROM jobs
        WHERE (title LIKE '%Freelance%' OR title LIKE '%Contract%')
        AND fit_score >= 7
    ''')
    count = cursor.fetchone()[0]
    filtered_count['freelance'] = count

    conn.execute('''
        UPDATE jobs SET fit_score = 3
        WHERE (title LIKE '%Freelance%' OR title LIKE '%Contract%')
        AND fit_score >= 7
    ''')
    print(f"   ✅ {count} iş filtrelendi")
    print()

    # =========================================================================
    # FİLTRE 4: INTERN/INTERNSHIP
    # =========================================================================
    print("🔍 FİLTRE 4: Intern/Internship")
    cursor = conn.execute('''
        SELECT COUNT(*) FROM jobs
        WHERE (title LIKE '%Intern%' OR title LIKE '%Internship%')
        AND fit_score >= 7
    ''')
    count = cursor.fetchone()[0]
    filtered_count['intern'] = count

    conn.execute('''
        UPDATE jobs SET fit_score = 3
        WHERE (title LIKE '%Intern%' OR title LIKE '%Internship%')
        AND fit_score >= 7
    ''')
    print(f"   ✅ {count} iş filtrelendi")
    print()

    # =========================================================================
    # FİLTRE 5: STANDALONE JAVASCRIPT
    # =========================================================================
    print("🔍 FİLTRE 5: Standalone JavaScript Developer (Backend Node.js hariç)")
    cursor = conn.execute('''
        SELECT COUNT(*) FROM jobs
        WHERE (
            (title LIKE '%JavaScript Developer%' OR title LIKE '%Javascript Developer%')
            AND title NOT LIKE '%Full%'
            AND title NOT LIKE '%Backend%'
        ) AND fit_score >= 7
    ''')
    count = cursor.fetchone()[0]
    filtered_count['javascript'] = count

    conn.execute('''
        UPDATE jobs SET fit_score = 5
        WHERE (
            (title LIKE '%JavaScript Developer%' OR title LIKE '%Javascript Developer%')
            AND title NOT LIKE '%Full%'
            AND title NOT LIKE '%Backend%'
        ) AND fit_score >= 7
    ''')
    print(f"   ✅ {count} iş filtrelendi")
    print()

    # =========================================================================
    # FİLTRE 6: ANALYTICS ENGINEER
    # =========================================================================
    print("🔍 FİLTRE 6: Analytics Engineer (sen ML, Analytics değil)")
    cursor = conn.execute('''
        SELECT COUNT(*) FROM jobs
        WHERE title LIKE '%Analytics Engineer%' AND fit_score >= 7
    ''')
    count = cursor.fetchone()[0]
    filtered_count['analytics'] = count

    conn.execute('''
        UPDATE jobs SET fit_score = 6
        WHERE title LIKE '%Analytics Engineer%' AND fit_score >= 7
    ''')
    print(f"   ✅ {count} iş filtrelendi")
    print()

    # =========================================================================
    # FİLTRE 7: ONSITE (Paris vb.)
    # =========================================================================
    print("🔍 FİLTRE 7: Onsite işler (Paris vb.)")
    cursor = conn.execute('''
        SELECT COUNT(*) FROM jobs
        WHERE title LIKE '%Paris%' AND fit_score >= 7
    ''')
    count = cursor.fetchone()[0]
    filtered_count['onsite'] = count

    conn.execute('''
        UPDATE jobs SET fit_score = 6
        WHERE title LIKE '%Paris%' AND fit_score >= 7
    ''')
    print(f"   ✅ {count} iş filtrelendi")
    print()

    # =========================================================================
    # FİLTRE 8: 4+ YIL DENEYİM GEREKSİNİMİ (Açıklamada)
    # =========================================================================
    print("🔍 FİLTRE 8: 4+ yıl deneyim gerektiren işler (açıklamada)")

    cursor = conn.execute('''
        SELECT url, title, description
        FROM jobs
        WHERE fit_score >= 7 AND description IS NOT NULL
    ''')
    rows = cursor.fetchall()

    urls_to_downgrade = []

    for row in rows:
        url = row[0]
        title = row[1]
        desc = row[2].lower() if row[2] else ''

        # 4+ yıl deneyim ara
        year_matches = re.findall(r'(\d+)\+?\s*years?.*(experience|background|required)', desc)
        for match in year_matches:
            years = int(match[0])
            if years >= 4:
                urls_to_downgrade.append(url)
                break

        # Security Clearance (ABD vatandaşlığı gerektirir)
        if 'clearance required' in desc or 'top secret' in desc:
            if url not in urls_to_downgrade:
                urls_to_downgrade.append(url)

    if urls_to_downgrade:
        placeholders = ','.join('?' * len(urls_to_downgrade))
        conn.execute(f'''
            UPDATE jobs SET fit_score = 5
            WHERE url IN ({placeholders})
        ''', urls_to_downgrade)

    filtered_count['experience'] = len(urls_to_downgrade)
    print(f"   ✅ {len(urls_to_downgrade)} iş filtrelendi")
    print()

    # Commit all changes
    conn.commit()

    # =========================================================================
    # SON DURUM
    # =========================================================================
    cursor = conn.execute('SELECT COUNT(*) FROM jobs WHERE fit_score >= 8')
    final_8_count = cursor.fetchone()[0]
    cursor = conn.execute('SELECT COUNT(*) FROM jobs WHERE fit_score >= 7')
    final_7_count = cursor.fetchone()[0]

    print_separator()
    print("📊 SON DURUM:")
    print_separator()
    print(f"8+ puan: {final_8_count} iş ({initial_8_count} → {final_8_count}, {initial_8_count - final_8_count} filtrelendi)")
    print(f"7+ puan: {final_7_count} iş ({initial_7_count} → {final_7_count}, {initial_7_count - final_7_count} filtrelendi)")
    print()

    # =========================================================================
    # ÖZET RAPOR
    # =========================================================================
    print_separator()
    print("📋 FİLTRELEME ÖZETI:")
    print_separator()
    total_filtered = sum(filtered_count.values())

    print(f"Toplam filtrelenen: {total_filtered} iş")
    print()
    print("Kategori bazında:")
    for category, count in sorted(filtered_count.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            category_names = {
                'seniority': 'Senior/Lead/Principal',
                'frontend': 'Standalone Frontend',
                'freelance': 'Freelance/Contract',
                'intern': 'Intern/Internship',
                'javascript': 'JavaScript Developer',
                'analytics': 'Analytics Engineer',
                'onsite': 'Onsite işler',
                'experience': '4+ yıl deneyim/Clearance'
            }
            print(f"  • {category_names.get(category, category):<30}: {count} iş")

    print()
    print_separator()
    print(f"✅ Filtreleme tamamlandı!")
    print(f"✅ {final_8_count} perfect iş + {final_7_count - final_8_count} iyi iş kaldı!")
    print_separator()

    conn.close()


if __name__ == "__main__":
    filter_jobs()
