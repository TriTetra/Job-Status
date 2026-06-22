# Career OS - Kullanım Kılavuzu

**5 dakikada iş başvurusuna hazır.**

## 📋 İÇİNDEKİLER

1. [Ne Yaptık?](#ne-yaptık)
2. [Dizin Yapısı](#dizin-yapısı)
3. [Nasıl Kullanılır?](#nasıl-kullanılır)
4. [Gerçek Kullanım Senaryoları](#gerçek-kullanım-senaryoları)
5. [Sorun Giderme](#sorun-giderme)

---

## NE YAPTIK?

### ApplyPilot (Zaten Vardı)
- ✅ 562 iş buldu
- ✅ Skorladı (1-10)
- ✅ Excel'e export etti
- ✅ **ÇOK İYİYDİ**

### Career OS (4 Günde Ekledik)
- ✅ AI-adjusted skill levels (L0-L5)
- ✅ Semantic matching (5 component)
- ✅ Acceptance probability (gerçekçi tahmin)
- ✅ ROI-optimized learning
- ✅ **BELKİ GEREKSIZ**

### Sonuç
ApplyPilot **zaten yeterliydi**. Career OS **CV için güzel**, ama başvuru için **gereksiz**.

---

## DİZİN YAPISI

```
applypilot-jobs/
│
├── career_os/              # YENİ SISTEM (4 günlük iş)
│   ├── models/             # Skill, Profile, Job modelleri
│   ├── core/               # Skill graph, transfer learning
│   ├── intelligence/       # Semantic matching, scoring
│   └── data/               # ApplyPilot DB loader
│
├── scripts/                # ESKİ YARDIMCI SCRIPTLER
│   ├── cold_email_generator.py   # ← BU İŞE YARAR
│   ├── skills_gap_analyzer.py    # ← BU İŞE YARAR
│   └── export_to_excel.py
│
├── docs/                   # Dokümantasyon
│   ├── guides/
│   │   └── 2_MONTH_ACTION_PLAN.md  # ← BU İŞE YARAR
│   ├── APPLICATION_TRACKER.md       # ← BU İŞE YARAR
│   └── QUICK_START.md
│
├── test_*.py               # Testler (Career OS için)
└── README.md               # Ana README
```

---

## NASIL KULLANILIR?

### Option 1: ApplyPilot Kullan (BASİT - ÖNERİLEN)

**1. İşleri Listele:**
```bash
sqlite3 ~/.applypilot/applypilot.db "SELECT title, company, fit_score, url FROM jobs WHERE fit_score >= 8 LIMIT 10;"
```

**2. Başvur:**
- URL'leri aç
- Apply butonuna tıkla
- CV gönder
- **BİTTİ**

**Süre:** 30 dakika, 10 başvuru.

---

### Option 2: Career OS Kullan (KARMAŞIK)

**1. Gerçek Veriyi Yükle:**
```bash
cd ~/Desktop/applypilot-jobs
python test_production.py
```

**Çıktı:**
```
✓ Loaded 50 jobs from ApplyPilot
✓ Career OS scoring...

APPLY NOW: 12 jobs
  1. ML Engineer @ Startup (Score: 87.3, Acceptance: 44%)
  2. Backend Engineer @ Company (Score: 82.1, Acceptance: 38%)
  ...

TOP SKILLS TO LEARN:
  AWS        | ROI: 2.50 | Cost: 20h
  Kubernetes | ROI: 1.80 | Cost: 28h
```

**2. Sonuçları Kullan:**
- "APPLY NOW" listesindeki işlere başvur
- Top skills'i öğrenmeye başla

**Süre:** 10 dakika analiz + 30 dakika başvuru.

---

### Option 3: Python'da Kullan (GELİŞTİRİCİ)

```python
from career_os.data import ApplyPilotLoader, create_user_profile_from_config
from career_os.intelligence import CareerDecisionEngine, SemanticMatcher, GapAnalyzer, OpportunityScorer

# 1. Veri yükle
loader = ApplyPilotLoader()
jobs = loader.load_jobs(min_score=7, limit=50)
profile = create_user_profile_from_config()

# 2. Engine başlat
matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')
analyzer = GapAnalyzer()
scorer = OpportunityScorer(matcher=matcher)
engine = CareerDecisionEngine(matcher, analyzer, scorer)

# 3. Analiz yap
result = engine.analyze_opportunities(jobs, profile, min_score=60)

# 4. Sonuçları gör
print(f"Apply to: {len(result['apply_now'])} jobs")
for opp in result['apply_now'][:5]:
    print(f"- {opp.job.title} @ {opp.job.company}")
    print(f"  Score: {opp.career_score:.1f}, Acceptance: {opp.acceptance_probability:.1f}%")

# 5. Learning plan
if result['top_gaps']:
    print(f"\nLearn first: {result['top_gaps'][0].skill} (ROI: {result['top_gaps'][0].roi:.2f})")
```

**Çıktı:**
```
Apply to: 12 jobs
- ML Engineer @ AI Startup
  Score: 87.3, Acceptance: 44.2%
- Backend Engineer @ Tech Co
  Score: 82.1, Acceptance: 38.5%

Learn first: AWS (ROI: 2.50)
```

---

## GERÇEK KULLANIM SENARYOLARI

### Senaryo 1: Hızlı Başvuru (5 dakika)

**Amaç:** Bugün 5 işe başvur.

```bash
# ApplyPilot DB'den en iyi 5'i al
sqlite3 ~/.applypilot/applypilot.db \
  "SELECT url FROM jobs WHERE fit_score >= 8 LIMIT 5;" \
  > jobs_to_apply.txt

# URL'leri aç ve başvur
cat jobs_to_apply.txt
```

**Sonuç:** 5 başvuru, sıfır analiz.

---

### Senaryo 2: Stratejik Başvuru (30 dakika)

**Amaç:** En iyi 15 işi bul, acceptance probability'ye göre sırala.

```bash
python test_production.py > analysis.txt

# "APPLY NOW" listesini kontrol et
grep -A 20 "APPLY NOW" analysis.txt
```

**Sonuç:** 15 stratejik başvuru.

---

### Senaryo 3: Skill Öğrenme Planı (1 saat)

**Amaç:** 8 haftalık learning roadmap.

```python
from career_os.data import ApplyPilotLoader, create_user_profile_from_config
from career_os.intelligence import GapAnalyzer

loader = ApplyPilotLoader()
jobs = loader.load_jobs(min_score=7)
profile = create_user_profile_from_config()

analyzer = GapAnalyzer()
gaps = analyzer.analyze(profile, jobs)

# Top 5 by ROI
for gap in gaps[:5]:
    print(f"{gap.skill}: {gap.learning_cost_hours}h, ROI {gap.roi:.2f}")

# 8-week roadmap
roadmap = analyzer.create_roadmap(gaps, hours_per_week=10, max_weeks=8)
print(roadmap.summary())
```

**Sonuç:**
```
AWS: 20h, ROI 2.50
Kubernetes: 28h, ROI 1.80

Roadmap: 8 weeks, 70 hours
Week 1-2: AWS (20h)
Week 3-4: Kubernetes (28h)
Week 5-6: Advanced PyTorch (22h)
```

---

### Senaryo 4: Cold Email (30 dakika)

**Amaç:** 10 hiring manager'a email gönder.

```bash
# Email template'leri al
python scripts/cold_email_generator.py

# LinkedIn'de hiring manager bul
# Email gönder (template'leri kullan)
```

**Template örneği:**
```
Subject: YOLOv8 Edge Deployment → Your ML Team

Hi [Name],

I built a YOLOv8 system achieving 92% mAP on Raspberry Pi 5 
(40ms latency). Noticed [Company] is hiring for ML roles.

My edge deployment experience might fit your needs.

Quick chat?

Abdullokh
```

---

## SORUN GİDERME

### "ModuleNotFoundError: career_os"

**Sorun:** Python modülü bulunamıyor.

**Çözüm:**
```bash
cd ~/Desktop/applypilot-jobs
export PYTHONPATH=$PYTHONPATH:$(pwd)
python test_production.py
```

---

### "FileNotFoundError: applypilot.db"

**Sorun:** ApplyPilot database yok.

**Çözüm:**
```bash
# ApplyPilot'u çalıştır
cd ~/.applypilot
applypilot scan

# Veya manuel path ver
python -c "
from career_os.data import ApplyPilotLoader
loader = ApplyPilotLoader(db_path='/path/to/applypilot.db')
"
```

---

### "Model download çok yavaş"

**Sorun:** sentence-transformers model indirme 420MB.

**Çözüm:**
```python
# Daha küçük model kullan
from career_os.intelligence import SemanticMatcher

matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')  # 80MB
# matcher = SemanticMatcher(model_name='all-mpnet-base-v2')  # 420MB
```

---

### "Test çok uzun sürüyor"

**Sorun:** test_production.py 5 dakika+ sürüyor.

**Çözüm:**
```bash
# Daha az iş yükle
python -c "
from career_os.data import ApplyPilotLoader
loader = ApplyPilotLoader()
jobs = loader.load_jobs(min_score=8, limit=10)  # Sadece 10 iş
"
```

---

## NE YAPMALIYIM?

### ✅ YAPILMASI GEREKENLER (ÖNCELIK)

1. **Bugün:** 10 başvuru yap (ApplyPilot Excel kullan)
2. **Bu hafta:** 30 başvuru + 10 cold email
3. **Bu ay:** AWS öğren (20 saat)

### ❌ YAPILMAMASI GEREKENLER

1. Career OS'i "geliştir"
2. Daha fazla feature ekle
3. "Perfect system" kur

---

## ÖZET

**Basit yol (Önerilen):**
```bash
# ApplyPilot zaten işleri buldu
sqlite3 ~/.applypilot/applypilot.db "SELECT url FROM jobs WHERE fit_score >= 8;"

# URL'leri aç, başvur
# BİTTİ
```

**Karmaşık yol (CV için güzel):**
```bash
# Career OS kullan
python test_production.py

# Sonuçları oku, başvur
```

**Gerçek sonuç:**
- ApplyPilot: 562 iş buldu ✅
- Career OS: Fancy scoring yaptı ✅
- **Başvuru sayısı: 0** ❌

---

**ŞİMDİ NE YAPACAĞIZ?**

Excel'i aç → 10 işe başvur → BU KADAR.

Career OS GitHub'da dursun, CV'de güzel görünür.
