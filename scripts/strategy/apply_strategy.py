"""
ApplyPilot işlerini Career OS ile analiz et ve başvuru stratejisi oluştur.

Kullanım:
    python scripts/strategy/apply_strategy.py

Çıktı:
    - apply_today.txt: Bugün başvurulacak 10 iş
    - apply_this_week.txt: Bu hafta başvurulacak 20 iş
    - learning_plan.txt: 8 haftalık öğrenme planı
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from career_os.data import ApplyPilotLoader, create_user_profile_from_config
from packages.intelligence import SemanticMatcher, GapAnalyzer, OpportunityScorer, CareerDecisionEngine
from packages.db.connection import db
from packages.db.repositories import CareerScoreRepository


def main():
    print("=" * 70)
    print("  CAREER OS - BAŞVURU STRATEJİSİ")
    print("=" * 70)

    # 1. Veri yükle
    print("\n[1/4] ApplyPilot verilerini yüklüyorum...")
    try:
        loader = ApplyPilotLoader()
        # Sadece 7+ skor alanları yükle (zaten iyiler)
        jobs = loader.load_jobs(min_score=7, limit=100)

        if not jobs:
            print("❌ Hiç iş bulunamadı. ApplyPilot taraması yaptın mı?")
            return

        print(f"✓ {len(jobs)} iş yüklendi (ApplyPilot skor >= 7)")

    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\n💡 Önce ApplyPilot taraması yap:")
        print("   run_scan.bat")
        return

    # 2. Profile yükle
    print("\n[2/4] Profilini yüklüyorum...")
    profile = create_user_profile_from_config()
    print(f"✓ Profil: {profile.name}")
    print(f"  - {len(profile.skills)} skill")
    print(f"  - {profile.years_experience} yıl tecrübe")
    print(f"  - AI proficiency: {profile.ai_proficiency:.0%}")

    # 3. Career OS analizi
    print("\n[3/4] Career OS analizi yapıyorum...")
    print("  (Bu 10-30 saniye sürebilir, model yükleniyor...)")

    matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')  # Hızlı model
    analyzer = GapAnalyzer()
    scorer = OpportunityScorer(matcher=matcher)
    engine = CareerDecisionEngine(matcher, analyzer, scorer)

    # Full analiz
    result = engine.analyze_opportunities(jobs, profile, min_score=50.0)

    print(f"\n✓ Analiz tamamlandı!")
    print(f"  - {result['viable_count']} viable iş (skor >= 50)")
    print(f"  - {len(result['apply_now'])} APPLY NOW")
    print(f"  - {len(result['consider'])} CONSIDER")

    # 4. Başvuru stratejisi oluştur
    print("\n[4/4] Başvuru stratejisi oluşturuyorum...")

    # Bugün başvurulacaklar (top 10)
    today_jobs = result['apply_now'][:10]

    # Bu hafta başvurulacaklar (top 20)
    week_jobs = result['apply_now'][:20]

    # Prioritized list (diversified)
    all_opportunities = scorer.rank_opportunities(jobs, profile)
    prioritized = engine.prioritize_applications(all_opportunities, max_applications=15)

    # 4.5. PostgreSQL'e kaydet
    print("\n[4.5/5] Skorları PostgreSQL'e kaydediyorum...")
    scanned_at = datetime.utcnow()
    saved_count = 0
    failed_count = 0

    user_skill_names = {s.name.lower() for s in profile.skills}

    with db.session_scope() as session:
        repo = CareerScoreRepository(session)

        for opp in all_opportunities:
            sp = session.begin_nested()  # SAVEPOINT — bir job hatası diğerlerini etkilemez
            try:
                job_skills = [s.lower() for s in opp.job.required_skills]
                skill_gaps = [s for s in job_skills if s not in user_skill_names]

                explanation = {
                    "company": opp.job.company,
                    "company_size": opp.job.company_size,
                    "location": opp.job.location,
                    "remote": opp.job.remote,
                    "required_years": opp.job.required_years,
                    "user_years": profile.years_experience,
                    "salary_range": {"min": opp.job.salary_min, "max": opp.job.salary_max},
                    "matched_skills": [s for s in job_skills if s in user_skill_names],
                    "sponsors_visa": opp.job.sponsors_visa,
                }

                repo.save_score(
                    url=opp.job.url,
                    career_score=float(opp.career_score),
                    fit_score=float(opp.fit_score),
                    acceptance_probability=float(opp.acceptance_probability),
                    career_value=float(opp.career_value),
                    market_demand=float(opp.market_demand),
                    expected_value=float(opp.expected_value),
                    recommendation=str(opp.recommendation)[:100],
                    skill_gaps=skill_gaps,
                    explanation=explanation,
                    scanned_at=scanned_at,
                )
                sp.commit()
                saved_count += 1

                # Publish event (fire-and-forget, does not affect DB transaction)
                from events import event_bus as _bus
                from events.job_events import JobScored as _JobScored
                _bus.publish(_JobScored(
                    job_id=opp.job.url,
                    url=opp.job.url,
                    title=opp.job.title,
                    company=opp.job.company,
                    career_score=float(opp.career_score),
                    fit_score=float(opp.fit_score),
                    acceptance_probability=float(opp.acceptance_probability),
                    career_value=float(opp.career_value),
                    market_demand=float(opp.market_demand),
                    expected_value=float(opp.expected_value),
                    recommendation=str(opp.recommendation),
                    skill_gaps=skill_gaps,
                    explanation=explanation,
                    source="apply_strategy",
                ))

            except Exception as e:
                sp.rollback()
                failed_count += 1
                if failed_count <= 3:
                    print(f"   ! {opp.job.url[:60]}... — {e}")

    print(f"   OK {saved_count} skor kaydedildi" +
          (f" ({failed_count} basarisiz)" if failed_count else ""))

    # 5. Dosyalara kaydet
    output_dir = Path("career_os_output")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")

    # apply_today.txt
    with open(output_dir / f"apply_today_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("BUGÜN BAŞVURILACAK İŞLER (Top 10)\n")
        f.write("=" * 70 + "\n\n")

        for i, opp in enumerate(today_jobs, 1):
            f.write(f"{i}. {opp.job.title} @ {opp.job.company}\n")
            f.write(f"   URL: {opp.job.url}\n")
            f.write(f"   Location: {opp.job.location} ({'Remote' if opp.job.remote else 'Onsite'})\n")
            f.write(f"   Career Score: {opp.career_score:.1f}/100\n")
            f.write(f"   Acceptance: {opp.acceptance_probability:.1f}%\n")
            f.write(f"   Recommendation: {opp.recommendation}\n")

            if opp.job.salary_min:
                f.write(f"   Salary: ${opp.job.salary_min:,}")
                if opp.job.salary_max:
                    f.write(f" - ${opp.job.salary_max:,}")
                f.write("\n")

            f.write("\n")

        f.write("\n" + "=" * 70 + "\n")
        f.write("NASIL BAŞVURACAĞIM?\n")
        f.write("=" * 70 + "\n\n")
        f.write("1. URL'yi aç\n")
        f.write("2. LinkedIn/Indeed/Glassdoor'da apply tıkla\n")
        f.write("3. CV'ni upload et\n")
        f.write("4. docs/tracking/JOB_APPLICATIONS.md'ye kaydet\n\n")

    # apply_this_week.txt
    with open(output_dir / f"apply_this_week_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("BU HAFTA BAŞVURILACAK İŞLER (Top 20)\n")
        f.write("=" * 70 + "\n\n")

        for i, opp in enumerate(week_jobs, 1):
            f.write(f"{i}. {opp.job.title} @ {opp.job.company}\n")
            f.write(f"   URL: {opp.job.url}\n")
            f.write(f"   Score: {opp.career_score:.1f} | Accept: {opp.acceptance_probability:.1f}%\n")
            f.write("\n")

    # learning_plan.txt
    if result['learning_roadmap']:
        roadmap = result['learning_roadmap']

        with open(output_dir / f"learning_plan_{timestamp}.txt", "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("8 HAFTALIK ÖĞRENME PLANI\n")
            f.write("=" * 70 + "\n\n")

            f.write(f"Toplam süre: {roadmap.total_weeks} hafta ({roadmap.total_hours} saat)\n")
            f.write(f"Beklenen gelişme: +{roadmap.expected_fit_improvement:.0f}% fit score\n\n")

            f.write("PROGRAM:\n")
            f.write("-" * 70 + "\n\n")

            for task in roadmap.tasks:
                f.write(f"Hafta {task.start_week}-{task.start_week + task.duration_weeks - 1}: {task.skill}\n")
                f.write(f"  Süre: {task.total_hours} saat ({task.hours_per_week}h/hafta)\n")
                f.write(f"  Impact: +{task.impact:.1f}\n")
                f.write(f"\n  Kaynaklar:\n")
                for resource in task.resources:
                    f.write(f"    - {resource}\n")
                f.write(f"\n  Validation Project:\n")
                f.write(f"    {task.validation}\n")
                f.write("\n" + "-" * 70 + "\n\n")

    # prioritized_applications.txt (diversified portfolio)
    with open(output_dir / f"prioritized_applications_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("STRATEJİK BAŞVURU PORTFÖYÜ (Diversified Top 15)\n")
        f.write("=" * 70 + "\n\n")

        f.write("Bu liste şunları dengeler:\n")
        f.write("- Expected value (fit × acceptance × career value)\n")
        f.write("- Company size diversification\n")
        f.write("- Risk balance (reach / target / safety)\n\n")

        f.write("-" * 70 + "\n\n")

        company_distribution = {}

        for i, opp in enumerate(prioritized, 1):
            size = opp.job.company_size
            company_distribution[size] = company_distribution.get(size, 0) + 1

            f.write(f"{i:2}. {opp.job.title}\n")
            f.write(f"    Company: {opp.job.company} ({size})\n")
            f.write(f"    Career Score: {opp.career_score:.1f}\n")
            f.write(f"    Expected Value: {opp.expected_value:.1f}\n")
            f.write(f"    Acceptance: {opp.acceptance_probability:.1f}%\n")
            f.write(f"    URL: {opp.job.url}\n")
            f.write(f"    Strategy: {opp.recommendation}\n\n")

        f.write("-" * 70 + "\n\n")
        f.write("PORTFOLIO DAĞILIMI:\n\n")
        for size, count in company_distribution.items():
            f.write(f"  {size:12}: {count:2} başvuru ({count/len(prioritized)*100:.0f}%)\n")

    # Summary
    with open(output_dir / f"summary_{timestamp}.txt", "w", encoding="utf-8") as f:
        f.write("=" * 70 + "\n")
        f.write("CAREER OS ANALİZ SONUÇLARI\n")
        f.write("=" * 70 + "\n\n")

        f.write(f"Tarih: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")

        f.write(f"TOPLAM İŞ: {result['total_jobs']}\n")
        f.write(f"VİABLE (>= 60): {result['viable_count']}\n")
        f.write(f"APPLY NOW: {len(result['apply_now'])}\n")
        f.write(f"CONSIDER: {len(result['consider'])}\n\n")

        f.write("İSTATİSTİKLER:\n")
        f.write(f"  Avg Fit Score:      {result['stats']['avg_fit']:.1f}/100\n")
        f.write(f"  Avg Acceptance:     {result['stats']['avg_acceptance']:.1f}%\n")
        f.write(f"  Avg Career Score:   {result['stats']['avg_career_score']:.1f}/100\n\n")

        if result['top_gaps']:
            f.write("ÖNCELİKLİ ÖĞRENİLECEK SKİLLLER:\n")
            for gap in result['top_gaps']:
                f.write(f"  {gap.skill:15} | ROI: {gap.roi:5.2f} | Cost: {gap.learning_cost_hours:3}h | Jobs: {gap.jobs_unlocked}\n")
            f.write("\n")

        f.write("\nÜRETİLEN DOSYALAR:\n")
        f.write(f"  - apply_today_{timestamp}.txt (Bugün başvur)\n")
        f.write(f"  - apply_this_week_{timestamp}.txt (Bu hafta başvur)\n")
        f.write(f"  - prioritized_applications_{timestamp}.txt (Stratejik portföy)\n")
        if result['learning_roadmap']:
            f.write(f"  - learning_plan_{timestamp}.txt (8 haftalık plan)\n")

    # 6. Ekrana özet
    print("\n" + "=" * 70)
    print("  ✓ BAŞVURU STRATEJİSİ HAZIR!")
    print("=" * 70)

    print(f"\n📁 Dosyalar: career_os_output/")
    print(f"\n📋 BUGÜN BAŞVUR ({len(today_jobs)} iş):")
    for i, opp in enumerate(today_jobs[:5], 1):
        print(f"  {i}. {opp.job.title} @ {opp.job.company}")
        print(f"     Score: {opp.career_score:.1f}, Accept: {opp.acceptance_probability:.1f}%")

    if len(today_jobs) > 5:
        print(f"  ... ve {len(today_jobs) - 5} iş daha")

    print(f"\n📚 ÖNCELİKLE ÖĞREN:")
    if result['top_gaps']:
        for gap in result['top_gaps'][:3]:
            print(f"  - {gap.skill} (ROI {gap.roi:.2f}, {gap.learning_cost_hours}h)")

    print(f"\n📈 İSTATİSTİKLER:")
    print(f"  Avg Career Score: {result['stats']['avg_career_score']:.1f}/100")
    print(f"  Avg Acceptance:   {result['stats']['avg_acceptance']:.1f}%")

    print("\n" + "=" * 70)
    print("SONRAKİ ADIMLAR:")
    print("=" * 70)
    print("\n1. career_os_output/apply_today_*.txt dosyasını aç")
    print("2. URL'leri aç ve başvur (hedef: 10 başvuru bugün)")
    print("3. docs/tracking/JOB_APPLICATIONS.md'ye kaydet")
    print("4. Yarın devam et!\n")


if __name__ == "__main__":
    main()
