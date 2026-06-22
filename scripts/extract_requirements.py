"""
ApplyPilot Requirements Extractor
----------------------------------
Başvurulan her iş ilanından istenen gereksinimleri çıkarır ve analiz eder.

Kullanım:
    python extract_requirements.py
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from collections import Counter
import re


def get_database_path():
    """ApplyPilot veritabanı yolunu bul"""
    # ApplyPilot'un varsayılan yolu
    db_path = Path.home() / ".applypilot" / "jobs.db"

    # Eğer burada değilse, yerel dizinde ara
    if not db_path.exists():
        db_path = Path("jobs.db")

    return db_path


def extract_requirements_from_description(description):
    """
    İş ilanı açıklamasından gereksinimleri çıkar
    """
    if not description:
        return []

    requirements = []

    # Yaygın requirement bölümü başlıkları
    section_patterns = [
        r"(?i)requirements?:?\s*\n(.*?)(?:\n\n|\Z)",
        r"(?i)qualifications?:?\s*\n(.*?)(?:\n\n|\Z)",
        r"(?i)what (?:we're|we are) looking for:?\s*\n(.*?)(?:\n\n|\Z)",
        r"(?i)you have:?\s*\n(.*?)(?:\n\n|\Z)",
        r"(?i)minimum qualifications?:?\s*\n(.*?)(?:\n\n|\Z)",
        r"(?i)required skills?:?\s*\n(.*?)(?:\n\n|\Z)",
        r"(?i)must have:?\s*\n(.*?)(?:\n\n|\Z)",
    ]

    for pattern in section_patterns:
        matches = re.findall(pattern, description, re.DOTALL)
        for match in matches:
            # Bullet pointleri ayıkla
            bullets = re.findall(r"[•\-\*]\s*(.+)", match)
            if bullets:
                requirements.extend(bullets)
            else:
                # Bullet yoksa satır satır al
                lines = [line.strip() for line in match.split('\n') if line.strip()]
                requirements.extend(lines[:10])  # Maksimum 10 satır

    # Tekrarlananları temizle
    requirements = list(dict.fromkeys(requirements))

    return requirements


def extract_skills_keywords(requirements_list):
    """
    Tüm gereksinimlerden beceri ve anahtar kelimeleri çıkar
    """
    # Yaygın teknik beceriler ve araçlar
    tech_keywords = [
        # Programlama Dilleri
        'python', 'rust', 'c++', 'java', 'javascript', 'typescript', 'go', 'scala',

        # ML/AI Frameworks
        'pytorch', 'tensorflow', 'keras', 'scikit-learn', 'transformers', 'hugging face',
        'opencv', 'yolo', 'detectron', 'mmdetection',

        # MLOps & Cloud
        'docker', 'kubernetes', 'aws', 'azure', 'gcp', 'mlflow', 'kubeflow',
        'terraform', 'airflow', 'dagster',

        # Databases
        'postgresql', 'mongodb', 'redis', 'elasticsearch', 'sql', 'nosql',

        # Web & Backend
        'fastapi', 'flask', 'django', 'react', 'node.js', 'express',

        # Concepts
        'machine learning', 'deep learning', 'computer vision', 'nlp',
        'transformers', 'llm', 'reinforcement learning', 'cv', 'ml',
        'generative ai', 'rag', 'fine-tuning', 'prompt engineering',

        # Other
        'git', 'ci/cd', 'agile', 'scrum', 'rest api', 'microservices',
        'linux', 'bash', 'cuda', 'optimization'
    ]

    all_text = ' '.join(requirements_list).lower()

    found_skills = {}
    for keyword in tech_keywords:
        pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        count = len(re.findall(pattern, all_text))
        if count > 0:
            found_skills[keyword] = count

    return found_skills


def analyze_jobs():
    """
    Veritabanından işleri analiz et
    """
    db_path = get_database_path()

    if not db_path.exists():
        print(f"❌ Veritabanı bulunamadı: {db_path}")
        print("💡 Önce ApplyPilot çalıştırılmalı: applypilot run")
        return

    print(f"📂 Veritabanı: {db_path}")
    print()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Skorlanmış işleri çek (en azından enrichment yapılmış)
    cursor.execute("""
        SELECT
            url, title, site, location, salary,
            full_description, fit_score, score_reasoning,
            applied_at, apply_status
        FROM jobs
        WHERE full_description IS NOT NULL
        ORDER BY fit_score DESC
    """)

    jobs = cursor.fetchall()

    if not jobs:
        print("❌ Henüz hiç iş bulunamadı!")
        print("💡 Önce ApplyPilot'u çalıştır: applypilot run")
        conn.close()
        return

    print(f"✅ Toplam {len(jobs)} iş bulundu")
    print()

    # Her iş için gereksinimleri çıkar
    all_requirements = []
    job_data = []

    for job in jobs:
        requirements = extract_requirements_from_description(job['full_description'])

        job_info = {
            'title': job['title'],
            'site': job['site'],
            'location': job['location'],
            'salary': job['salary'],
            'fit_score': job['fit_score'],
            'url': job['url'],
            'requirements': requirements,
            'applied': job['applied_at'] is not None,
            'apply_status': job['apply_status']
        }

        job_data.append(job_info)
        all_requirements.extend(requirements)

    # Sonuçları kaydet
    output_dir = Path("job_requirements_analysis")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Her işin detaylı gereksinimleri
    detailed_file = output_dir / f"detailed_requirements_{timestamp}.json"
    with open(detailed_file, 'w', encoding='utf-8') as f:
        json.dump(job_data, f, indent=2, ensure_ascii=False)

    print(f"📄 Detaylı gereksinimler kaydedildi: {detailed_file}")

    # 2. Beceri analizi
    skills = extract_skills_keywords(all_requirements)
    skills_sorted = sorted(skills.items(), key=lambda x: x[1], reverse=True)

    skills_file = output_dir / f"skills_analysis_{timestamp}.json"
    with open(skills_file, 'w', encoding='utf-8') as f:
        json.dump(dict(skills_sorted), f, indent=2, ensure_ascii=False)

    print(f"📊 Beceri analizi kaydedildi: {skills_file}")

    # 3. İnsan tarafından okunabilir özet
    summary_file = output_dir / f"summary_{timestamp}.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("ApplyPilot - İş İlanları Gereksinim Analizi\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"📅 Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"📊 Toplam İş İlanı: {len(jobs)}\n")
        f.write(f"✅ Başvurulan: {sum(1 for j in job_data if j['applied'])}\n")
        f.write(f"⏳ Bekleyen: {sum(1 for j in job_data if not j['applied'])}\n")
        f.write("\n" + "=" * 80 + "\n\n")

        # En çok istenen beceriler
        f.write("🔥 EN ÇOK İSTENEN BECERİLER (Top 20)\n")
        f.write("-" * 80 + "\n")
        for i, (skill, count) in enumerate(skills_sorted[:20], 1):
            f.write(f"{i:2d}. {skill.upper():<30} → {count} kez bahsedildi\n")

        f.write("\n" + "=" * 80 + "\n\n")

        # Yüksek skorlu işler
        f.write("⭐ YÜKSEK SKORLU İŞLER (Fit Score >= 8)\n")
        f.write("-" * 80 + "\n")
        high_score_jobs = [j for j in job_data if j['fit_score'] and j['fit_score'] >= 8]

        for i, job in enumerate(high_score_jobs[:15], 1):
            f.write(f"\n{i}. {job['title']}\n")
            f.write(f"   📍 {job['location']} | 💰 {job['salary'] or 'N/A'} | ⭐ Score: {job['fit_score']}\n")
            f.write(f"   🌐 {job['site']}\n")
            if job['applied']:
                f.write(f"   ✅ Başvuruldu ({job['apply_status']})\n")
            if job['requirements']:
                f.write(f"   📋 Gereksinimler:\n")
                for req in job['requirements'][:5]:
                    f.write(f"      • {req[:100]}\n")

        f.write("\n" + "=" * 80 + "\n\n")

        # İşletme bazında analiz
        f.write("🏢 SİTE BAZINDA DAĞILIM\n")
        f.write("-" * 80 + "\n")
        site_counts = Counter(j['site'] for j in job_data)
        for site, count in site_counts.most_common():
            f.write(f"  {site:<20} → {count} iş\n")

    print(f"📋 Özet rapor kaydedildi: {summary_file}")
    print()

    # Konsola da özet yazdır
    print("=" * 80)
    print("🔥 EN ÇOK İSTENEN BECERİLER (Top 15)")
    print("=" * 80)
    for i, (skill, count) in enumerate(skills_sorted[:15], 1):
        bar = "█" * min(count, 50)
        print(f"{i:2d}. {skill.upper():<25} {bar} {count}")

    print()
    print("=" * 80)
    print(f"✅ Analiz tamamlandı! Tüm sonuçlar '{output_dir}' klasöründe.")
    print("=" * 80)

    conn.close()


if __name__ == "__main__":
    analyze_jobs()
