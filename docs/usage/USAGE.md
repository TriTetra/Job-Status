# Career OS - Kullanım Kılavuzu

Bu doküman, `career_os/` katmanının günlük kullanımını açıklar. ApplyPilot'un
kendisi nasıl çalıştırılır sorusu için [QUICK_START.md](../setup/QUICK_START.md)'a
bakın.

## İçindekiler

1. [Career OS ne ekliyor?](#career-os-ne-ekliyor)
2. [Dizin yapısı](#dizin-yapısı)
3. [Kullanım seçenekleri](#kullanım-seçenekleri)
4. [Gerçek kullanım senaryoları](#gerçek-kullanım-senaryoları)
5. [Sorun giderme](#sorun-giderme)

## Career OS ne ekliyor?

ApplyPilot zaten işleri buluyor, skorluyor ve Excel'e döküyor — bu temel akış
kendi başına yeterli. Career OS (`career_os/`), bu sonuçların üzerine ikinci bir
analiz katmanı ekliyor:

- Skill seviyelerini (L0-L5) ve bu seviyelerin ne kadarının AI yardımıyla
  ulaşıldığını modelliyor ([career_os/models/skill.py](../../career_os/models/skill.py))
- İş kabul edilme olasılığını şirket büyüklüğü, deneyim farkı, visa ve rekabet
  durumuna göre tahmin ediyor ([career_os/intelligence/opportunity_scorer.py](../../career_os/intelligence/opportunity_scorer.py))
- Eksik skill'leri ROI'ye (öğrenme süresine oranlı etki) göre sıralayıp 8 haftalık
  bir öğrenme planı çıkarıyor ([career_os/intelligence/gap_analyzer.py](../../career_os/intelligence/gap_analyzer.py))

Bu skorlama formülleri elle belirlenmiş ağırlıklara dayanıyor; gerçek başvuru
sonuçlarına karşı henüz doğrulanmadı (`../tracking/JOB_APPLICATIONS.md`'de şu an 0 başvuru
var). Yani "acceptance probability %44" gibi bir sayı, gerçek bir istatistik değil,
kod içindeki sabit ağırlıklardan hesaplanan bir tahmin.

**Pratik sonuç:** Sadece başvuru yapmak istiyorsan ApplyPilot'un Excel çıktısı
yeterli. Career OS, hangi işe önce bakman gerektiği konusunda ek bir görüş verir
ve hangi skill'i öğrenmenin daha değerli olduğunu gösterir.

## Dizin yapısı

```
applypilot-jobs/
├── career_os/              Career OS motoru
│   ├── models/             Skill, Profile, Job veri modelleri
│   ├── core/                skill_graph.py - transfer learning grafiği
│   ├── intelligence/        semantic_matcher, gap_analyzer, opportunity_scorer
│   └── data/                 applypilot_loader.py - ApplyPilot DB'sinden veri çekme
│
├── scripts/                 ApplyPilot etrafındaki yardımcı scriptler
│   ├── apply_strategy.py     Career OS analizini çalıştırıp çıktı dosyaları üretir
│   ├── cold_email_generator.py
│   └── export_to_excel_advanced.py
│
├── docs/                     Kurulum ve süreç dokümantasyonu
├── test_*.py                  career_os modülleri için manuel doğrulama scriptleri
└── README.md
```

## Kullanım seçenekleri

### Seçenek 1: Sadece ApplyPilot (en basit)

```bash
sqlite3 ~/.applypilot/applypilot.db "SELECT title, company, fit_score, url FROM jobs WHERE fit_score >= 8 LIMIT 10;"
```

URL'leri aç, başvur, `../tracking/JOB_APPLICATIONS.md`'ye kaydet. Career OS'a hiç gerek yok.

### Seçenek 2: Career OS ile strateji üretmek

```bash
python scripts/strategy/apply_strategy.py
```

`career_os_output/` klasörüne `apply_today_*.txt`, `apply_this_week_*.txt`,
`prioritized_applications_*.txt`, `learning_plan_*.txt` ve `summary_*.txt`
dosyalarını yazar. Detaylı akış için [APPLY_NOW.md](APPLY_NOW.md)'ye bakın.

### Seçenek 3: Python'dan doğrudan kullanmak

```python
from career_os.data import ApplyPilotLoader, create_user_profile_from_config
from career_os.intelligence import CareerDecisionEngine, SemanticMatcher, GapAnalyzer, OpportunityScorer

loader = ApplyPilotLoader()
jobs = loader.load_jobs(min_score=7, limit=50)
profile = create_user_profile_from_config()

matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')
analyzer = GapAnalyzer()
scorer = OpportunityScorer(matcher=matcher)
engine = CareerDecisionEngine(matcher, analyzer, scorer)

result = engine.analyze_opportunities(jobs, profile, min_score=60)

for opp in result['apply_now'][:5]:
    print(f"{opp.job.title} @ {opp.job.company} - score {opp.career_score:.1f}, "
          f"acceptance {opp.acceptance_probability:.1f}%")
```

### tests/test_production.py nedir?

`tests/test_production.py`, `career_os/` ile ApplyPilot verisinin gerçekten uyumlu
çalıştığını doğrulamak için yazılmış bir entegrasyon testidir — sonuçları
konsola yazdırır, dosyaya kaydetmez. Günlük kullanım için `apply_strategy.py`
kullanın; `tests/test_production.py`'yi sadece bir değişiklik yaptıktan sonra her
şeyin hâlâ çalıştığını kontrol etmek için çalıştırın.

## Gerçek kullanım senaryoları

### Senaryo 1: Hızlı başvuru (5 dakika)

```bash
sqlite3 ~/.applypilot/applypilot.db \
  "SELECT url FROM jobs WHERE fit_score >= 8 LIMIT 5;" \
  > jobs_to_apply.txt
```

URL'leri aç ve başvur. Hiçbir analiz gerekmez.

### Senaryo 2: Stratejik başvuru (30 dakika)

```bash
python scripts/strategy/apply_strategy.py
cat career_os_output/apply_today_*.txt
```

### Senaryo 3: Skill öğrenme planı (1 saat)

```python
from career_os.data import ApplyPilotLoader, create_user_profile_from_config
from career_os.intelligence import GapAnalyzer

loader = ApplyPilotLoader()
jobs = loader.load_jobs(min_score=7)
profile = create_user_profile_from_config()

analyzer = GapAnalyzer()
gaps = analyzer.analyze(profile, jobs)

for gap in gaps[:5]:
    print(f"{gap.skill}: {gap.learning_cost_hours}h, ROI {gap.roi:.2f}")

roadmap = analyzer.create_roadmap(gaps, hours_per_week=10, max_weeks=8)
print(roadmap.summary())
```

### Senaryo 4: Cold email

```bash
python scripts/strategy/cold_email_generator.py
```

5 hazır şablondan birini seçip (`value_first`, `problem_solution`,
`mutual_interest`, `direct_value`, `sponsorship_upfront`) işe özel email üretir.

## Sorun giderme

### "ModuleNotFoundError: career_os"

```bash
cd ~/Desktop/applypilot-jobs
export PYTHONPATH=$PYTHONPATH:$(pwd)
python tests/test_production.py
```

### "FileNotFoundError: applypilot.db"

ApplyPilot taraması henüz yapılmamış. Önce `run_scan.bat` çalıştırın, ya da DB
yolunu manuel verin:

```python
from career_os.data import ApplyPilotLoader
loader = ApplyPilotLoader(db_path='/path/to/applypilot.db')
```

### Model indirme yavaş

`SemanticMatcher`, ilk çalıştırmada bir sentence-transformers modeli indirir.
Varsayılan `all-mpnet-base-v2` 420MB; `all-MiniLM-L6-v2` 80MB ve daha hızlıdır,
doğruluktan küçük bir ödün verir:

```python
matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')
```

### Test çok uzun sürüyor

Daha az iş yükleyerek test edin:

```python
jobs = loader.load_jobs(min_score=8, limit=10)
```
