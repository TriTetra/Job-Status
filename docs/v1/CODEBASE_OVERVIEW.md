# Codebase Overview — applypilot-jobs

> **Amaç:** Bu repo, iş tarama, filtreleme, puanlama ve başvuru stratejisi üretme işlemlerini otomatize eden iki katmanlı bir sistemdir.

---

## Sistem Mimarisi

```
ApplyPilot CLI (dış paket, venv içinde)
       ↓
  ~/.applypilot/applypilot.db  (SQLite — tüm iş verileri)
       ↓
  scripts/scan/  →  filtrele, puanla, Excel'e aktar
       ↓
  career_os/     →  kişisel profile göre yeniden sırala, strateji üret
       ↓
  career_os_output/  (txt dosyaları: bugün başvur, bu hafta, öğrenme planı)
```

Sistem ikiye ayrılır: **ApplyPilot** (dış araç, iş bulur) ve **Career OS** (bu repodaki kod, bulunanları analiz eder).

---

## 1. Katman: ApplyPilot (Dış Paket)

`pip install applypilot` ile yüklenir, `venv/` altında durur. Bu paketin kaynak kodu bu repoda **yoktur**.

**Ne yapar:**
- LinkedIn, Indeed, Glassdoor'u tarar
- Sorgu tanımları `~/.applypilot/searches.yaml` dosyasından gelir (bu repoda takip edilmez, `applypilot init` ile oluşturulur)
- Her ilanı `~/.applypilot/.env` içindeki LLM ile 1–10 arası puanlar (varsayılan: `openai/gpt-4o-mini` via OpenRouter)
- Sonuçları `~/.applypilot/applypilot.db` SQLite veritabanına yazar

**Veritabanı şeması (ilgili sütunlar):**

| Sütun | Açıklama |
|---|---|
| `url` | İş ilanı URL'si (birincil anahtar olarak kullanılır) |
| `title` | Pozisyon başlığı |
| `company` | Şirket adı |
| `location` | Lokasyon metni |
| `description` | Kısa açıklama |
| `full_description` | Tam açıklama (varsa) |
| `fit_score` | ApplyPilot'un LLM skoru (1–10) |
| `score_reasoning` | Neden bu skoru aldığına dair açıklama |
| `salary` | Maaş aralığı string (parse edilir) |
| `site` | Kaynak (linkedin, indeed, vb.) |
| `discovered_at` | Keşfedilme zamanı (ISO string) |
| `application_url` | Doğrudan başvuru linki |

---

## 2. Katman: scripts/ — Glue Kodu

ApplyPilot'un ham çıktısını filtreler, raporlar, dışa aktarır.

### `scripts/scan/run_full_scan.py`

Ana giriş noktası. `run_scan.bat` bunu çağırır. Sıralı 6 adım:

1. **Backup** — `~/.applypilot/applypilot.db` dosyasını `backups/` altına kopyalar, son 10'u tutar
2. **Discover** — `applypilot run discover --hours-old 72` çalıştırır
3. **Score** — `applypilot run score --min-score 7` çalıştırır
4. **Filter** — `filter_jobs.py` çağırır
5. **Excel** — `export_to_excel_advanced.py` çağırır, üretilen dosyayı `reports/<tarih>/` klasörüne taşır
6. **Summary** — `logs/run_history.json` günceller, `reports/<tarih>/summary.txt` yazar

Tarama süresi ve istatistikler `logs/YYYY-MM-DD.log` dosyasına yazılır.

### `scripts/scan/filter_jobs.py`

Veritabanındaki `fit_score` sütununu doğrudan günceller (silmez, skoru düşürür). 8 filtre:

| Filtre | Aksiyon |
|---|---|
| Senior / Lead / Principal / Staff / Director | `fit_score = 4` |
| Standalone Frontend (Full Stack hariç) | `fit_score = 4` |
| Freelance / Contract | `fit_score = 3` |
| Intern / Internship | `fit_score = 3` |
| Standalone JavaScript Developer | `fit_score = 5` |
| Analytics Engineer | `fit_score = 6` |
| Paris (onsite) | `fit_score = 6` |
| 4+ yıl deneyim / Security Clearance (açıklamadan regex ile) | `fit_score = 5` |

> **Dikkat:** Filtreler mevcut skoru kontrol ederek çalışır (`WHERE fit_score >= 7`). Zaten düşük skoru olan ilanlar etkilenmez.

### `scripts/scan/export_to_excel_advanced.py`

6 sayfalık, 18 sütunlu Excel çalışma kitabı üretir:
- Executive Summary
- Perfect Match (8+)
- Good Match (7)
- Skills Analysis
- By Company
- Full Database

### `scripts/strategy/apply_strategy.py`

Career OS'i tetikleyen ana script. 4 aşama:

1. `ApplyPilotLoader` ile veritabanından `fit_score >= 7` olan ilanları yükle
2. `config.yaml` okuyarak `UserProfile` oluştur
3. `SemanticMatcher + GapAnalyzer + OpportunityScorer + CareerDecisionEngine` ile tam analiz
4. `career_os_output/` altına 5 dosya yaz

### `scripts/strategy/cold_email_generator.py`

Şirkete özel soğuk e-posta taslakları üretir.

### `scripts/strategy/skills_gap_analyzer.py`

Career OS'un `GapAnalyzer`'ını tek başına çalıştıran script.

### `scripts/tracking/track_applications.py`

`docs/tracking/JOB_APPLICATIONS.md` dosyasını günceller.

### `scripts/tracking/sync_to_github.py`

Başvuruları GitHub Issues'a senkronize eder (PyGithub kullanır, opsiyonel).

---

## 3. Katman: career_os/ — Stratejik Puanlama Motoru

Bu repo'nun asıl kodu. ApplyPilot'un 1–10 skorunun üstüne kişisel profile göre ikinci bir analiz katmanı ekler.

### Veri Modelleri (`career_os/models/`)

**`skill.py`**

`SkillLevel` enum: `UNKNOWN(0)` → `AI_ASSISTED(1)` → `WORKING(2)` → `INDEPENDENT(3)` → `ADVANCED(4)` → `EXPERT(5)`

`Skill` dataclass:
- `name`, `level` (SkillLevel)
- `ai_multiplier` (0.0–1.0): AI yardımı olmadan ne kadar yapabilirsin
- `base_hours_to_next_level`: Bir sonraki seviyeye geçiş süresi
- `transferability`: İlgili beceriler ve transfer katsayıları
- `learning_cost(target_level)`: Hedefe ulaşmak için toplam saat (üstel)
- `transfer_discount(related_skills)`: Transfer öğrenmesi indirimi (maks %70)
- `effective_level()`: `level × ai_multiplier`

**`profile.py`**

`UserProfile` dataclass: isim, email, skill listesi, tecrübe listesi, `years_experience`, `ai_proficiency` (0–1), tercihler (`UserPreferences`), hedef roller.

`Job` dataclass: `id`, `title`, `company`, `description`, `url`, `location`, `remote`, `required_skills`, `preferred_skills`, `required_years`, `salary_min/max`, `company_size`, `sponsors_visa`.

`MatchResult`: Eşleştirme sonucu — `overall_score`, `breakdown` (5 bileşen), `skill_gaps`, `confidence`, `explanation`.

`OpportunityScore`: Kapsamlı fırsat değerlendirmesi — `fit_score`, `acceptance_probability`, `career_value`, `market_demand`, `career_score`, `expected_value`, `recommendation`.

---

### Çekirdek (`career_os/core/`)

**`skill_graph.py` — SkillGraph**

68 beceri, 74 ağırlıklı kenar içeren yönlü bir graph (`networkx.DiGraph`). Transfer öğrenmesini modellar.

Transfer ağırlık aralıkları:
- `0.9+` — Neredeyse aynı (React → Next.js)
- `0.7–0.9` — Güçlü transfer (Python → FastAPI)
- `0.5–0.7` — Orta transfer (Python → Go)
- `0.3–0.5` — Zayıf transfer (Java → Python)
- `<0.3` — Minimal transfer (Python → Rust)

Aile grupları: Python ailesi, Java ailesi, JavaScript ailesi, TypeScript ailesi, Docker ailesi, AWS ailesi, PostgreSQL ailesi, PyTorch ailesi, LLM ailesi, vb.

Ana metodlar:
- `get_transfer_factor(from, to)` — İki beceri arasındaki transfer katsayısı
- `shortest_learning_path(known_skills, target)` — En iyi öğrenme yolu (Dijkstra, `1 - weight` maliyet)
- `get_related_skills(skill, max_distance=2)` — BFS ile ilgili beceriler
- `calculate_learning_discount(known_skills, target)` — Toplam indirim katsayısı (min 0.3)

---

### Zeka Katmanı (`career_os/intelligence/`)

**`semantic_matcher.py` — SemanticMatcher**

Kütüphane: `sentence-transformers`  
Model: `all-MiniLM-L6-v2` (80MB, hızlı) veya `all-mpnet-base-v2` (420MB, kaliteli)

5 bileşenli eşleştirme:

| Bileşen | Ağırlık | Nasıl Hesaplanır |
|---|---|---|
| Teknik beceriler | %40 | Seviye bazlı skor: INDEPENDENT+=1.0, WORKING=0.7, AI_ASSISTED=0.4; eksikler için transfer skoru (maks 0.5) |
| Domain deneyimi | %25 | Kullanıcı deneyimi metni + CV ile iş açıklaması arasında cosine similarity (sentence embeddings) |
| Kıdem seviyesi | %20 | `user_years / required_years` oranı; fazla deneyim → 0.9/0.8 ceza, az → üstel düşüş |
| Çalışma modu | %10 | Remote tam uyum=1.0, hybrid kabul=0.8, onsite kabul=0.6, uyumsuz=0.3 |
| AI kapasitesi | %5 | İş açıklamasında AI anahtar kelimeler varsa `ai_proficiency × (mentions/3)` |

**`opportunity_scorer.py` — OpportunityScorer + CareerDecisionEngine**

`OpportunityScorer` 4 bileşeni birleştirir:

| Bileşen | Ağırlık |
|---|---|
| Fit Score (SemanticMatcher'dan) | %30 |
| Acceptance Probability | %25 |
| Career Value | %25 |
| Market Demand | %20 |

**Acceptance Probability** nasıl hesaplanır:

Başlangıç: `0.5`
- Şirket tipi çarpanı: big_tech=0.25, large=0.45, midsize=0.7, startup=1.2
- Deneyim uyumu: tam uyum=1.0, fazla=0.8, çok fazla=0.5, az=üstel düşüş
- Remote match: +%30, mismatch: ×0.3
- Visa sponsorship gerekli ama yok: ×0.4
- Rekabet tahmini: remote ×0.7, yüksek maaş ×0.7, big_tech ×0.5
- Kıdem uyumsuzluğu: senior iş + <5 yıl = ×0.6

**Career Value** nasıl hesaplanır:

Başlangıç: `0.5`
- Eksik beceri sayısı: +0.06/beceri (maks +0.3)
- Maaş: +(salary_min - 100k) / 666k (maks +0.3)
- Şirket prestiji: big_tech +0.2, large +0.1
- Hedef rol uyumu: +0.1
- Kariyer ilerleme fırsatı: +0.1

**Market Demand:** Hardcoded sözlük (Python=0.95, AWS=0.9, LLM=0.9, ... PHP=0.4)

**Expected Value:** `fit × acceptance × career_value × 100`

`CareerDecisionEngine` bunları koordine eder:
1. Tüm işleri puanla ve sırala
2. `min_score=50.0` eşiğinin altını at
3. "APPLY" vs "CONSIDER" kategorisine ayır
4. Viable işler üzerinde gap analizi yap
5. Öğrenme roadmap'i oluştur

Portföy diversifikasyonu: `prioritize_applications()` şirket büyüklüğüne göre en fazla `max_applications/3` kuralını uygular.

**`gap_analyzer.py` — GapAnalyzer**

ROI bazlı skill gap analizi.

`SkillGap` dataclass:
- `skill`, `current_level`, `target_level`
- `learning_cost_hours` (transfer indiriminden sonra)
- `learning_path` (skill graph'tan)
- `impact_score`, `roi` (impact/saat)
- `resources`, `validation_project`
- `jobs_unlocked` (bu beceriyi gerektiren iş sayısı)

Seviye bazı taban saat maliyeti:
- AI_ASSISTED: 10h
- WORKING: 20h
- INDEPENDENT: 40h
- ADVANCED: 80h
- EXPERT: 160h

`create_roadmap()`: Önce topological sort (bağımlı beceriler önce), sonra 8 haftalık programa yerleştir (10h/hafta varsayılan).

---

### Veri Katmanı (`career_os/data/`)

**`applypilot_loader.py` — ApplyPilotLoader + create_user_profile_from_config()**

`ApplyPilotLoader`: SQLite'dan iş yükler, her satırı `Job` objesine çevirir.

Dönüşüm sırasında yapılan çıkarımlar:
- **Şirket adı:** LinkedIn URL → title'daki ` - ` / ` at ` → application_url domain → description'daki "At X, we" / "Join X!" pattern → "Unknown"
- **Remote:** location/description'da `remote`, `anywhere`, `work from home`, `wfh` keyword arama
- **Maaş:** regex ile sayı çekme
- **Şirket büyüklüğü:** hardcoded isim listesi (google, meta, amazon, ...)
- **Beceriler:** Requirements/Qualifications heading varsa sadece o bölüm, yoksa tam metin; 40 skill keyword
- **Gereken yıl:** title'da Senior=5, Junior=1, Lead=7; yoksa description'da `X years experience` regex; default 2.0

`create_user_profile_from_config()`: `config.yaml` okur, `UserProfile` döndürür. Skill seviyeleri `_SKILL_PROFILES` sözlüğünden gelir (config.yaml sadece isimleri saklar, seviyeleri değil).

---

## config.yaml

Sistemin kişiselleştirilmiş konfigürasyon dosyası. Gitignore'da, `config.yaml.example`'dan kopyalanır.

Temel bölümler:

| Bölüm | İçerik |
|---|---|
| `llm` | Provider (OpenRouter), model (gpt-4o-mini), API key |
| `job_search` | Remote only, 72 saatlik tarama, site başına 50 sonuç, min_score=8 |
| `candidate` | İsim, email, 2 yıl tecrübe, Özbekistan/sponsorship gerekli, $40–80k maaş |
| `candidate.core_skills` | ML/AI (PyTorch, YOLO, CV, NLP, LLM) + Backend (Python, Rust, Java, Go) + Full Stack (React, Next.js, TS) |
| `candidate.target_roles` | ML/AI/CV/Backend/Full Stack Engineer — Junior/Mid |
| `candidate.avoid` | Senior, Lead, standalone Frontend, Mobile, DevOps, Data Analyst, QA |

---

## Kütüphaneler (requirements.txt)

| Paket | Nerede Kullanılır | Amaç |
|---|---|---|
| `applypilot>=0.3.0` | venv | İş tarama ve LLM puanlama (dış araç) |
| `openpyxl>=3.1.0` | scripts/scan | Excel dosyası oluşturma |
| `networkx>=3.0` | career_os/core | Skill graph ve Dijkstra en kısa yol |
| `numpy>=1.24` | career_os/intelligence | Ortalama hesaplama, array ops |
| `sentence-transformers>=2.2` | career_os/intelligence | Semantik embedding (BERT tabanlı) |
| `scikit-learn>=1.3` | career_os/intelligence | Cosine similarity |
| `pyyaml>=6.0` | career_os/data | config.yaml okuma |
| `PyGithub>=2.0` | scripts/tracking | GitHub Issues senkronizasyonu (opsiyonel) |
| `pytest>=7.0` | tests/ | Test çalıştırma |

---

## Testler (`tests/`)

4 test dosyası, manuel verification scripti olarak tasarlanmış:
- `test_career_os.py` — Temel modeller
- `test_day2.py` — Skill graph ve semantic matcher
- `test_day3.py` — Opportunity scorer ve gap analyzer
- `test_production.py` — Gerçek ApplyPilot veritabanına karşı uçtan uca test

`pytest tests/` ile çalıştırılır.

---

## Çalışma Akışı (Günlük Kullanım)

```
1. Tarama (her 3 günde bir):
   run_scan.bat
   → ApplyPilot tarar, filtreler, Excel üretir → reports/<tarih>/

2. Strateji (isteğe bağlı, ek analiz):
   python scripts/strategy/apply_strategy.py
   → Career OS yeniden sıralar, dosyalar → career_os_output/

3. Başvuru:
   apply_today_*.txt aç → URL'leri aç → başvur
   → docs/tracking/JOB_APPLICATIONS.md güncelle

4. Yeni scan ihtiyaç yoksa Excel'i direkt kullan:
   reports/<tarih>/applypilot_advanced_*.xlsx → "Perfect Match (8+)" sayfası
```

---

## Kritik Notlar

- **Filtreleme silmez, puanı düşürür.** `filter_jobs.py` `fit_score`'u yazar, ilanı veritabanından kaldırmaz. Bu sayede eski çalışmalar tekrar çalıştırıldığında birikimleri kaybolmaz.
- **Career OS skorları heuristic, veri ile doğrulanmamış.** Acceptance probability formülü, ağırlıklar ve eşikler el ile ayarlanmıştır. Gerçek başvuru sonuçlarıyla henüz kalibre edilmemiştir.
- **Semantic matcher ilk çalıştırmada modeli indirir.** `all-MiniLM-L6-v2` ~80MB, `all-mpnet-base-v2` ~420MB. Sonraki çalıştırmalarda cache'ten gelir.
- **config.yaml'daki API key commit edilmiş.** Bu OpenRouter key'i şu anda `config.yaml` içinde açık duruyor. Gitignore'da olduğu için remote'a gitmez, ama local güvenlik açısından dikkatli olunmalı.
- **Şirket adı çıkarımı güvenilmez.** `_extract_company()` birden fazla sinyal dener ama çoğu gerçek ilan için "Unknown" döner. Bu Career OS'un acceptance probability hesabını etkiler (company_size="unknown" → 0.6 çarpanı).
