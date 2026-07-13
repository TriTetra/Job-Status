# Changelog

Her commit, her mimari karar, her belge değişikliği burada kayıt altında.  
Sıralama: en yeniden en eskiye.

---

## [Unreleased] — 2026-07-13 — Architecture Planning Session

Bu seans koda hiç dokunmadı. Tamamen analiz, mimari tasarım ve belgeleme üzerine.

### Eklendi — `docs/`

#### `docs/CODEBASE_OVERVIEW.md`
Mevcut v0 kod tabanının tam anatomisi. Kapsam:
- ApplyPilot ile Career OS arasındaki ayrım (dışarıdan pip paketi vs. bu repo)
- `~/.applypilot/applypilot.db` şeması (12 sütun)
- Tüm script'ler ve career_os modülleri (ne yapar, neyi okur, neye yazar)
- Kritik notlar: config.yaml'da plaintext API anahtarı, company extraction güvensizliği, Career OS skorlarının heuristik olduğu

#### `docs/DATABASE_AUDIT.md`
Hangi verinin nerede yaşadığı ve neyin DB'ye girmediğinin tam envanteri.
- ApplyPilot DB'ye yazılan 12 sütun
- DB'ye **yazılmayan** 6 veri kategorisi: Career OS skorları (.txt), skill match sonuçları (runtime), başvuru durumu (Excel Notes + Markdown), email geçmişi (.txt), skor değişim geçmişi (eziliyor)
- `data/career_os.db` önerisi: 4 tablo ile tam SQL şeması (`career_scores`, `applications`, `emails`, `scan_history`)
- Geçiş planı: ApplyPilot DB'ye dokunmadan, paralel SQLite ile çalışma

#### `docs/VISION.md`
Ürün doktrini — Career OS'un ne olmak istediği. İçerik:
- Ana vizyon: "geliştiricinin tüm kariyeri için işletim sistemi"
- 5 tasarım prensibi: Calm Technology, Explainable Always, Action Over Information, Progressive Disclosure, Evidence Over Claim
- 8 domain tanımı
- Evidence Graph konsepti (GitHub commit → confidence score → skill weight)
- Target-Aware Resume Generator
- 4 fazlı roadmap, anti-pattern'ler, ilk 30 gün planı

#### `docs/ARCHITECTURE.md`
v1.0 teknik mimari belgesi — **LOCKED**.
- Event-driven mimari: `JobDiscovered`, `JobScored`, `ApplicationSubmitted`, `CareerSnapshotCreated` event tipleri
- Plugin sistemi: `JobSourcePlugin`, `EnrichmentPlugin` ABC'leri
- Feature registry: `feature.yaml` metadata formatı
- Versioned knowledge: `knowledge/v1/`, `knowledge/v2/`
- AI Memory Layer: 5 memory tipi (candidate, company, market, conversation, learning)
- Timeline katmanı: PostgreSQL `timeline_snapshots` + `timeline_changes` tabloları
- Kilitli dizin yapısı (8 domain, 8 servis, 8 worker)
- Teknoloji stack: FastAPI + Next.js 14 + PostgreSQL + LanceDB + NetworkX→KuzuDB
- 6 fazlı roadmap

#### `docs/MIGRATION_REPORT.md`
Mevcut v0'ın v1.0 mimarisine nasıl taşınacağının tam planı.
- Her mevcut dosyanın yeni konumu ve yapılması gereken değişiklik
- 4 dosya silinecek: `setup_package.py`, `run_scan.bat`, `career_os_output/*.txt`, `logs/run_history.json`
- 4 dosya bölünecek: `applypilot_loader.py` (→ 3 parça), `profile.py` (→ 3 parça), `apply_strategy.py`, `cold_email_generator.py`
- 14 hardcoded Python dict YAML'a çıkarılacak (`knowledge/v1/`)
- Acil güvenlik: `config.yaml`'daki API anahtarı git geçmişinden temizlenmeli
- Öncelik sırası: güvenlik → veri kaybı riski → plugin sistemi → YAML extraction → modül taşıma

---

## [0.5.0] — 2026-06-24 — Kritik Bug Düzeltmeleri

**Commit:** `6020b1e` — `fix: fix company/skill extraction noise and unreachable score threshold`

### Düzeltildi

**`career_os/data/applypilot_loader.py`** (+97 satır)
- ApplyPilot DB'nin `company` sütunu yok — `_extract_company()` her zaman "Unknown" döndürüyordu. 5 kademeli fallback eklendi: LinkedIn URL parse → başlık split → `application_url` domain → açıklama regex → "Unknown"
- `_extract_skills()` bare substring matching kullanıyordu: "ai" kelimesi "maintain" içinde, "go" kelimesi "going" içinde eşleşiyordu. Word-boundary regex'e geçildi.
- İki adet `except:` → `except ValueError:` (sessiz hata yutucu kaldırıldı)

**`scripts/scan/export_to_excel_advanced.py`** (+8 satır)
- Excel skill-matching fonksiyonu aynı bare substring problemini taşıyordu. Aynı word-boundary düzeltmesi uygulandı.

**`scripts/strategy/apply_strategy.py`** (+4 satır)
- `min_score=60` hardcoded eşiği — gerçek career_score'lar bu profil için 20-45 arasında çıkıyordu. Sonuç: her çalıştırmada "0 viable job." Eşik düşürüldü.

---

## [0.4.0] — 2026-06-23 — Dokümantasyon ve Kod Kalitesi

### 0.4.3 — 2026-06-23 23:56

**Commit:** `1769308` — `docs: rewrite README.md and CHANGELOG.md for accuracy and tone`

**README.md** (-291 satır, +158 satır)
- Emoji kaldırıldı, AI-generated ses tonu temizlendi
- Doğrulanamayan iddiaları kaldırıldı: "85% correlation" (hiç başvuru logu yok), "200+ skills" (gerçekte 68 skill / 74 edge), "9x faster / 30x more relevant" (baseline hiç olmadı)
- ApplyPilot (dış pip paketi) ile Career OS (bu repo) arasındaki fark netleştirildi — önceki versiyonlar ikisini karıştırıyordu
- Gerçek sayılar: search query sayısı, filter sayısı, Excel sütun/sheet sayıları kod incelenerek düzeltildi

**CHANGELOG.md**
- Gerçek scan verisine indirgendi, template eklendi

---

### 0.4.2 — 2026-06-23 23:55

**Commit:** `f9bd422` — `refactor: reorganize docs/ into setup/usage/tracking/strategy, add index`

**Değişiklikler:**
- Aynı seviyede duran 7 doc dosyası amacına göre 4 klasöre ayrıldı:
  - `docs/setup/` — QUICK_START.md, GITHUB_GUIDE.md, WINDOWS_SCHEDULER_GUIDE.md
  - `docs/usage/` — USAGE.md, APPLY_NOW.md
  - `docs/tracking/` — JOB_APPLICATIONS.md, APPLICATION_TRACKER.md
  - `docs/strategy/` — 2_MONTH_ACTION_PLAN.md
- `docs/README.md` eklendi — navigable index
- QUICK_START.md yeniden yazıldı: eksik kurulum adımları eklendi (`applypilot init` wizard'ı, `applypilot doctor`), stale iddia düzeltildi (searches.yaml repo'da değil, `~/.applypilot/`'de yaşıyor)
- Ölü `searches.yaml` silindi (yanlış schema, hiçbir kod okumuyordu)

---

### 0.4.1 — 2026-06-23 23:55

**Commit:** `0beaef6` — `test: move tests/ into its own folder and add real assertions`

**Değişiklikler:**
- 4 test dosyası repo kökünden `tests/` klasörüne taşındı
- Tüm testler sıfır `assert` içeriyordu — "geçti" = "çökmedi" anlamına geliyordu. Gerçek assertion'lar eklendi:
  - Deterministik hesaplamalar için kesin değer testi (skill level, ROI sıralaması)
  - Embedding-tabanlı semantic matcher skorları için range/invariant testi
- `test_production.py`: ApplyPilot DB veya config.yaml yoksa `pytest.skip()` — artık sessizce hiçbir şey yapmıyor
- Windows default `cp1252` encoding'de crash eden unicode checkmark'lar düz metin ile değiştirildi
- **Sonuç:** 17/17 test geçiyor, 4 tanesi gerçek ApplyPilot DB'ye karşı

---

### 0.4.0 — 2026-06-23 23:54

**Commit:** `d017db0` — `refactor: reorganize scripts/ into scan/strategy/tracking/packaging`

**Değişiklikler:**
- 11 script düz liste → 4 klasör:
  - `scripts/scan/` — run_full_scan.py, filter_jobs.py, export_to_excel_advanced.py, schedule_info.py
  - `scripts/strategy/` — apply_strategy.py, cold_email_generator.py, skills_gap_analyzer.py, extract_requirements.py
  - `scripts/tracking/` — track_applications.py, sync_to_github.py
  - `scripts/packaging/` — setup_package.py
- **Gerçek bug düzeltmesi:** `run_full_scan.py` subprocess path'lerini repo kökünde arıyordu (`filter_jobs.py`, `export_to_excel_advanced.py`) — dosyalar zaten `scripts/`'te olduğundan pipeline'ın filter ve export adımları hiç çalışmamış olabilirdi. Path'ler düzeltildi.
- `run_scan.bat` güncellendi

---

**Commit:** `813191f` — `fix: fix skill graph crash, encoding crash, and hardcoded profile in career_os`

**Düzeltilen 3 bug:**

1. **`career_os/core/skill_graph.py`:** `shortest_learning_path()` hedef skill taxonomy'de yoksa (örn. "Redis") `networkx.NodeNotFound` fırlatıyordu — `GapAnalyzer.analyze()` gerçek iş ilanlarında crash ediyordu. `try/except NodeNotFound` eklendi.

2. **`semantic_matcher.py`, `applypilot_loader.py`:** Unicode checkmark içeren `print()` çağrıları Windows'un default `cp1252` console encoding'i ile `UnicodeEncodeError` veriyordu.

3. **`applypilot_loader.py`:** `create_user_profile_from_config()` tamamen hardcoded `UserProfile` döndürüyordu. Artık `config.yaml`'dan name/email/years_experience/target_roles/salary/preferences okuyor, resume'yu `personal/<Name>.txt`'ten yüklüyor. Not: skill proficiency seviyeleri hâlâ override table gerektiriyor (config.yaml sadece skill adlarını saklıyor, seviyeleri değil).

---

**Commit:** `6206494` — `chore: add requirements.txt and config template, drop dead artifacts`

**Eklendi:**
- `requirements.txt` — career_os/ ve scripts/'in import ettiği tüm bağımlılıklar ilk kez belgelendi
- `config.yaml.example` — `applypilot_loader.py`'nin beklediği schema ile temiz şablon

**Silindi:**
- `scripts/export_to_excel.py` — `export_to_excel_advanced.py` tarafından tamamen supersede edilmişti, hiçbir yerde referans kalmamıştı
- `excel_exports/` — 3 dosya silinmiş script'in kalıntısıydı, 1 tanesi gerçek scan sonucuydu → `reports/`'a taşındı. Kişisel başvuru verisi git'te takip edilmemeli.

---

## [0.3.0] — 2026-06-23 — Pratik Entegrasyon

### 0.3.2 — 2026-06-23 01:13

**Commit:** `e44e641` — `Update README with integrated workflow`

README Quick Start güncellendi: iki seçenek sunuldu — Option 1: `apply_strategy.py` (ApplyPilot + Career OS), Option 2: Excel direkt (ApplyPilot only). APPLY_NOW.md'ye bağlantı eklendi.

---

### 0.3.1 — 2026-06-23 01:13

**Commit:** `d6cd86a` — `Add practical apply strategy script + guide`

**`scripts/apply_strategy.py`** (256 satır)  
ApplyPilot iş ilanlarını Career OS ile analiz eden entegrasyon betiği. 4 çıktı dosyası üretir:
- `apply_today.txt` — günlük top 10
- `apply_this_week.txt` — haftalık top 20
- `prioritized_applications.txt` — şirket boyutuna göre çeşitlendirilmiş portföy
- `learning_plan.txt` — 8 haftalık roadmap

**`APPLY_NOW.md`** — Günlük/haftalık rutinler, acceptance probability rehberi, career score yorumlama, cold email zamanlaması.

---

### 0.3.0 — 2026-06-23 01:06

**Commit:** `5788179` — `Add comprehensive usage documentation`

**`USAGE.md`** — İki sistem açıklaması, 3 kullanım seçeneği, gerçek istatistikler, troubleshooting, dürüst değerlendirme (ApplyPilot tek başına yeterli; Career OS CV için güçlü ama iş başvurusu için zorunlu değil).

README: iki sistem özeti, gerçek sayılar (562 iş, 30 perfect match), öncelik listesi.

---

## [0.2.0] — 2026-06-23 — Career OS İntelligence Katmanı

### 0.2.3 — 2026-06-23 00:57

**Commit:** `85d3071` — `Update Career OS README - Production ready documentation`

`career_os/README.md` kapsamlı yeniden yazım. Not: Bu versiyondaki bazı metrikler (`15-25% başvuru başarısı`, `64% öğrenme süresi azalması`) henüz veriyle doğrulanmamıştı — bir sonraki commit cycle'ında kaldırıldı/düzeltildi.

---

### 0.2.2 — 2026-06-23 00:53

**Commit:** `85c4839` — `Add Day 4: Production Integration with ApplyPilot`

**`career_os/data/applypilot_loader.py`** (399 satır) — İlk versiyon eklendi.
- ApplyPilot SQLite'tan veri okuma
- Company extraction (URL/title'dan)
- Skill extraction (açıklamadan)
- `UserProfile` oluşturma
- `test_production.py` (243 satır) — Gerçek DB üzerinde testler

---

### 0.2.1 — 2026-06-23 00:38

**Commit:** `9be4f37` — `Add Day 3: Opportunity Scorer + Career Decision Engine`

**`career_os/intelligence/opportunity_scorer.py`** (546 satır)

`OpportunityScorer`:
- Acceptance probability: company tier (big_tech 0.25×, startup 1.2×), experience gap, remote match (1.3×), visa sponsorship (0.4×), competition
- Career value: skill development potential, salary growth, company prestige, target role alignment
- Market demand: hardcoded skill demand dict (python=0.95, aws=0.9, ...)
- Expected value ranking: `fit × acceptance × career_value`

`CareerDecisionEngine`:
- Full pipeline orchestration
- Company size diversification (max n/3 per tier)
- Integrated gap analysis + roadmap
- APPLY / CONSIDER / SKIP recommendation

`test_day3.py` (349 satır) eklendi.

---

### 0.2.0 — 2026-06-23 00:33

**Commit:** `164150c` — `Add Day 2: Semantic Matcher + Gap Analyzer`

**`career_os/intelligence/semantic_matcher.py`** (421 satır)
- `SentenceTransformer('all-MiniLM-L6-v2')` ile 5 bileşenli eşleştirme:
  - Skills match (40%) — level-aware + transfer learning credit
  - Domain cosine similarity (25%) — embedding-based
  - Seniority match (20%) — years experience / level mapping
  - Work mode match (10%) — remote/hybrid/onsite
  - AI capability bonus (5%)
- Transfer learning: `_check_transfer()` — related skill varsa 0.5 cap

**`career_os/intelligence/gap_analyzer.py`** (419 satır)
- ROI = impact / learning_cost_hours
- Transfer learning discount (min 0.3, max 70%)
- Topological sort ile öğrenme sıralaması
- 8 haftalık plan (10 saat/hafta)
- Hardcoded `_RESOURCES` ve `_VALIDATION_PROJECTS` dict'leri

`test_day2.py` (305 satır) eklendi.

---

## [0.1.0] — 2026-06-23 — Career OS Çekirdek Temeli

**Commit:** `91df3e1` — `Add Career OS core foundation`

**`career_os/models/skill.py`** (236 satır)
- `SkillLevel` IntEnum: UNKNOWN(0), AI_ASSISTED(1), WORKING(2), INDEPENDENT(3), ADVANCED(4), EXPERT(5)
- `Skill` dataclass: name, level, evidence, ai_multiplier, base_hours_to_next_level, last_used, transferability
- `learning_cost(target_level)` — üstel ölçekleme
- `transfer_discount(related_skills)` — maks %70
- `effective_level()` — level × ai_multiplier
- `SKILL_CATEGORIES` — 8 kategori

**`career_os/models/profile.py`** (290 satır)
- `Experience`, `UserPreferences`, `UserProfile`, `Job`, `MatchResult`, `OpportunityScore` dataclass'ları
- `Job.all_skills()` — required + preferred birleşimi
- `OpportunityScore.should_apply(threshold=60.0)`, `priority_tier()`

**`career_os/core/skill_graph.py`** (378 satır)
- `networkx.DiGraph` tabanlı `SkillGraph`
- `_build_taxonomy()` — 68 skill, 74 edge, Python/Java/JS/Docker/AWS ailesi
- `get_transfer_factor()`, `shortest_learning_path()` (Dijkstra, `1-weight` maliyet), `get_related_skills()` (BFS), `calculate_learning_discount()` (min 0.3)

`test_career_os.py` (224 satır) eklendi.

---

## [0.0.3] — 2026-06-22 — Takip Sistemi ve Multi-Channel Strateji

**Commit:** `fa74fb9` — `🚀 Add multi-channel job application system`

**`scripts/cold_email_generator.py`** (458 satır)
- 5 email template: value_first, problem_solution, mutual_interest, direct_value, sponsorship_upfront
- 3'lü follow-up serisi (7, 14, 21. gün)
- `YOUR_INFO` ve `ACHIEVEMENTS` kodu içinde hardcoded

**`scripts/skills_gap_analyzer.py`** (426 satır)
- Excel "Missing Skills" sütunundan frequency analizi
- 8 haftalık öğrenme planı
- `LEARNING_RESOURCES` dict hardcoded

**`APPLICATION_TRACKER.md`** (227 satır) — 8 haftalık sprint planı, haftalık hedefler.

**`2_MONTH_ACTION_PLAN.md`** (492 satır) — Günlük breakdown, vize gerektiren adaylar için strateji.

---

**Commit:** `34f18fe` — `✨ Add job tracking system & GitHub integration`

**`JOB_APPLICATIONS.md`** — Markdown tabanlı başvuru takibi.

**`scripts/track_applications.py`** (238 satır) — Excel Notes sütununu parse eder, JOB_APPLICATIONS.md'yi günceller.

**`scripts/sync_to_github.py`** (203 satır) — Excel verilerinden GitHub Issues oluşturur. `REPO_NAME` placeholder bırakıldı.

**`GITHUB_GUIDE.md`** — GitHub setup rehberi.

---

## [0.0.2] — 2026-06-22 — İlk Scan Sonuçları

**Commit:** `47a3698` — `Add Excel reports from first scan`

İlk scan'den elde edilen Excel dosyaları commit edildi (daha sonra `62064940`'ta kaldırıldı — kişisel başvuru verisi git'te yaşamamalı).

---

**Commit:** `8d1b66e` — `Reorganize documentation structure`

README temizlendi, doc dosyaları `docs/` altına taşındı.

---

## [0.0.1] — 2026-06-22 — İlk Commit

**Commit:** `07643ec` — `🎉 Initial commit: Professional Job Discovery System`

Projenin temeli. İçerik:
- `.gitignore`, `.env.example`
- `run_scan.bat` — Windows'ta tam pipeline batch script
- `scripts/filter_jobs.py` (319 satır) — 8 SQL UPDATE filtresi: Senior/Lead/Principal (→4), Standalone Frontend (→4), Freelance/Contract (→3), Intern (→3), Standalone JS (→5), Analytics Engineer (→6), Paris onsite (→6), 4+ yıl deneyim/clearance (→5). Kayıt silmez, sadece `fit_score` düşürür.
- `scripts/export_to_excel.py` (359 satır) — ilk Excel export (daha sonra advanced ile değiştirildi)
- `scripts/export_to_excel_advanced.py` (656 satır) — 6 sayfa Excel: Executive Summary, Perfect Match (8+), Good Match (7), Skills Analysis, By Company, Full Database
- `scripts/run_full_scan.py` (354 satır) — 6 adımlı pipeline: backup → discover → score → filter → Excel → summary. `logs/run_history.json` yazar.
- `scripts/schedule_info.py` (93 satır) — son scan zamanını okur, "ne zaman tara?" önerir
- `scripts/setup_package.py` (199 satır) — kurulum paketi oluşturucu
- `scripts/track_applications.py` (238 satır) — başvuru takibi
- `scripts/extract_requirements.py` (263 satır) — iş ilanlarından gereksinim extraction
- Dokümantasyon: README.md, QUICK_START.md, WINDOWS_SCHEDULER_GUIDE.md, CHANGELOG.md
- `logs/`, `reports/` — `.gitkeep` ile boş klasörler

**İlk scan istatistikleri:**
- 562 iş keşfedildi
- 30 perfect match (8+)
- 121 good match (7)
- Maliyet: ~$0.73
- Süre: ~25-30 dakika

---

## Güvenlik Notu

`config.yaml` dosyasında plaintext OpenRouter API anahtarı bulunuyor (`sk-or-v1-4d7abdbc97...`). Bu anahtar git geçmişine girdi. Henüz temizlenmedi — BFG Repo Cleaner veya `git filter-repo` ile geçmişten silinmeli, anahtar revoke edilmeli.
