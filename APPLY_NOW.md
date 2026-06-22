# BAŞVURU KILAVUZU

**ApplyPilot işlerini Career OS ile analiz et ve başvur.**

## Hızlı Başlangıç (5 dakika)

### 1. Strateji Oluştur

```bash
python scripts/apply_strategy.py
```

**Ne yapar:**
- ApplyPilot'un bulduğu işleri yükler
- Career OS ile analiz eder
- Başvuru stratejisi oluşturur
- Dosyalara kaydeder

**Çıktı:**
```
career_os_output/
├── apply_today_2026-06-23_15-30.txt       ← Bugün başvur (10 iş)
├── apply_this_week_2026-06-23_15-30.txt   ← Bu hafta (20 iş)
├── prioritized_applications_*.txt         ← Stratejik portföy (15 iş)
├── learning_plan_*.txt                    ← 8 haftalık plan
└── summary_*.txt                          ← Özet
```

---

### 2. Bugün Başvur

```bash
# Dosyayı aç
cat career_os_output/apply_today_*.txt

# Veya Windows'ta
notepad career_os_output/apply_today_*.txt
```

**İçinde ne var:**
```
1. ML Engineer @ AI Startup
   URL: https://linkedin.com/jobs/...
   Location: Remote
   Career Score: 87.3/100
   Acceptance: 44.2%
   Recommendation: APPLY - Strong opportunity
   Salary: $120,000 - $160,000

2. Backend Engineer @ Tech Co
   URL: https://...
   ...
```

**Her iş için:**
1. URL'yi aç
2. Apply tıkla
3. CV upload et
4. JOB_APPLICATIONS.md'ye kaydet

---

### 3. Başvuruları Takip Et

```bash
# JOB_APPLICATIONS.md'yi aç
notepad JOB_APPLICATIONS.md
```

**Format:**
```markdown
## 2026-06-23

### Applied (10)
1. [ML Engineer @ AI Startup](url) - Applied, waiting
2. [Backend Engineer @ Tech Co](url) - Applied, waiting
...

### Follow-up Needed
- None yet

### Interview Schedule
- None yet
```

---

## Detaylı Kullanım

### Strateji Dosyaları

#### apply_today_*.txt
**Ne:** Bugün başvurulacak top 10 iş

**Neden:** En yüksek career score + acceptance probability

**Nasıl kullan:**
1. Dosyayı aç
2. Her URL'yi aç
3. Başvur
4. İşaretle (checkbox veya ✓)

**Hedef:** 10 başvuru bugün

---

#### apply_this_week_*.txt
**Ne:** Bu hafta başvurulacak 20 iş

**Neden:** Top 20 by career score

**Nasıl kullan:**
- Günde 5-10 iş
- Pazartesi-Cuma dağıt
- Weekend'de follow-up

**Hedef:** 20 başvuru bu hafta

---

#### prioritized_applications_*.txt
**Ne:** Stratejik portföy (diversified)

**Neden:** 
- Company size balance (startup, midsize, big_tech)
- Risk balance (reach, target, safety)
- Expected value optimized

**Nasıl kullan:**
- Reach jobs: Denemeye değer (acceptance düşük ama value yüksek)
- Target jobs: Ana hedef (good fit + acceptance)
- Safety jobs: Backup (high acceptance)

---

#### learning_plan_*.txt
**Ne:** 8 haftalık skill öğrenme planı

**Neden:** ROI-optimized (impact per hour)

**İçerik:**
```
Hafta 1-2: AWS (20 saat)
  Kaynaklar:
    - AWS Free Tier
    - AWS Skill Builder
  Validation:
    Deploy YOLOv8 to AWS Lambda

Hafta 3-4: Kubernetes (28 saat)
  ...
```

**Nasıl kullan:**
1. Hafta 1'den başla
2. Her gün 1.5-2 saat
3. Validation project yap
4. GitHub'a commit

---

## Workflow

### Günlük Rutin (30 dakika)

**Sabah (15 dakika):**
```bash
# Bugünkü listeyi aç
cat career_os_output/apply_today_*.txt

# İlk 5 işe başvur
```

**Akşam (15 dakika):**
```bash
# Kalan 5 işe başvur
# JOB_APPLICATIONS.md güncelle
```

---

### Haftalık Rutin (2 saat)

**Pazartesi:**
- Yeni strateji oluştur: `python scripts/apply_strategy.py`
- Bu haftanın 20 işini gözden geçir

**Salı-Cuma:**
- Günde 5 başvuru
- Follow-up email'ler (Day 7, 14)

**Weekend:**
- Learning plan (AWS/Kubernetes/vb)
- Portfolio güncelle
- Cold email hazırla

---

## Acceptance Probability Nedir?

**Career OS'in tahmin ettiği kabul edilme olasılığı.**

**Faktörler:**
- Company tier (big_tech 25%, startup 120%)
- Experience gap (tam uyum 100%, eksik 50%↓)
- Remote match (30% boost)
- Visa sponsorship (40% penalty if needed)
- Competition (remote + high salary = harder)

**Örnekler:**
```
Startup, exact exp, remote, visa → 44% acceptance
Google, exact exp, onsite, visa → 15% acceptance
Startup, under-exp, remote, no visa → 18% acceptance
```

**Nasıl kullan:**
- 40%+: Apply immediately (high chance)
- 20-40%: Apply (good chance)
- 10-20%: Apply but don't count on it (reach)
- <10%: Skip unless very high value

---

## Career Score Nedir?

**Weighted combination of:**
- Fit (30%): Technical skills match
- Acceptance (25%): Chance of getting hired
- Career Value (25%): Long-term benefit
- Market Demand (20%): Skill value

**Örnekler:**
```
Score 85+: Excellent, apply immediately
Score 75-85: Strong, definitely apply
Score 65-75: Good, apply
Score 60-65: Moderate, consider
Score <60: Weak, skip
```

---

## Tips

### Başvuru Sırası

**1. High acceptance + high score (40%+ accept, 80+ score):**
- En kolay kabul edilenler
- Confidence builder
- Practice için iyi

**2. High value + moderate acceptance (20-40% accept, 85+ score):**
- Main targets
- En çok effort buraya

**3. Reach jobs (10-20% accept, 90+ score):**
- Long shot ama worth it
- Çok hazırlık yapma, quick apply

---

### Cold Email Timing

**Best practice:**
- Day 0: Apply
- Day 3: LinkedIn connection request
- Day 7: Follow-up email (if no response)
- Day 14: Second follow-up
- Day 21: Final follow-up

**Script için:**
```bash
python scripts/cold_email_generator.py
```

---

### Learning Plan Execution

**Weekly cycle:**
- Mon-Fri: 1.5h/day learning
- Weekend: 3-4h validation project

**Example (AWS Week 1-2):**
- Mon-Fri: AWS tutorials (1.5h × 5 = 7.5h)
- Weekend 1: Start Lambda project (4h)
- Mon-Fri: Continue tutorials (7.5h)
- Weekend 2: Finish + deploy (4h)
- **Total:** 23h (target: 20h) ✓

---

## Troubleshooting

### "Script çok yavaş"

**Problem:** Model download 80-420MB

**Solution:**
```python
# Script'in ilk çalışmasında model indirilir
# Sonraki çalışmalarda hızlı (cache'den)

# İlk çalışma: 1-5 dakika (model download)
# Sonraki: 10-20 saniye
```

---

### "Dosyalar nerede?"

**Problem:** career_os_output/ klasörü görünmüyor

**Solution:**
```bash
# Mevcut dizini kontrol et
pwd

# career_os_output/ oluştur
mkdir -p career_os_output

# Script'i tekrar çalıştır
python scripts/apply_strategy.py
```

---

### "Job'lar yüklenmiyor"

**Problem:** ApplyPilot DB bulunamıyor

**Solution:**
```bash
# DB'yi kontrol et
ls ~/.applypilot/applypilot.db

# Yoksa ApplyPilot taraması yap
run_scan.bat

# Sonra tekrar dene
python scripts/apply_strategy.py
```

---

## Özet

**1 komut:**
```bash
python scripts/apply_strategy.py
```

**Çıktı:**
- Bugün başvurulacak 10 iş
- Bu hafta başvurulacak 20 iş
- 8 haftalık öğrenme planı
- Stratejik portföy analizi

**Hedef:**
- 10 başvuru bugün
- 30 başvuru bu hafta
- 100 başvuru bu ay

**Sonuç:**
- 3-5 phone screen bu ay
- 1-2 onsite
- 1 offer (8 hafta içinde)

---

**Başarılar! 🚀**
