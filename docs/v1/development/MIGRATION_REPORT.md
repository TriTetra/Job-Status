# Migration Report — v0 → v1.0 Architecture

Mevcut `v0` kod tabanının, kilitlenmiş `ARCHITECTURE.md` v1.0 yapısına nasıl taşınacağını gösteren tam envanter. Her dosya için mevcut konum, yeni konum, yapılması gereken değişiklik ve öncelik belirtilmiştir.

---

## 1. Dosya Göç Haritası

### 1.1 `career_os/models/` — Domain Modelleri

#### `career_os/models/skill.py`
**Şu anki görev:** `SkillLevel` enum, `Skill` dataclass, `SKILL_CATEGORIES` sabit sözlüğü.

**Sorunlar:**
- `_SKILL_PROFILES` dict (68 entry) `applypilot_loader.py` içinde hardcoded — buraya ait değil.
- `SKILL_CATEGORIES` dict de buraya hardcoded — YAML'a çıkarılmalı.

**Yeni konum:** `packages/domain/identity/skill.py`

**Yapılacak:**
1. `SkillLevel`, `Skill` dataclass'ını taşı — bunlar saf model, tutulabilir.
2. `SKILL_CATEGORIES` dict'i `knowledge/v1/skills/categories.yaml`'a çıkar, buraya sadece yükleyici bırak.
3. `_SKILL_PROFILES` dict (şu an `applypilot_loader.py`'de) → `knowledge/v1/skills/profiles.yaml`'a taşı.

**Öncelik:** Orta — bağımlı her yerde import path'i değiştirir.

---

#### `career_os/models/profile.py`
**Şu anki görev:** `Experience`, `UserPreferences`, `UserProfile`, `Job`, `MatchResult`, `OpportunityScore` dataclass'ları.

**Sorunlar:**
- `Job` modeli "job domain"e ait, `UserProfile` "identity domain"e ait — aynı dosyada tutulmamalı.
- `OpportunityScore.should_apply(threshold=60.0)` eşiği hardcoded — config'den okunmalı.
- `priority_tier()` metodu company tier bilgisini kullanıyor ama bu bilgi `opportunity_scorer.py`'de hardcoded.

**Yeni konum:**
- `UserProfile`, `UserPreferences`, `Experience` → `packages/domain/identity/profile.py`
- `Job` → `packages/domain/job/job.py`
- `MatchResult`, `OpportunityScore` → `packages/domain/intelligence/scoring.py`

**Yapılacak:**
1. Dosyayı 3'e böl, import'ları güncelle.
2. `should_apply` eşiğini config'den çek (`~/.career-os/config.yaml`).

**Öncelik:** Yüksek — hemen hemen her modül bunu import eder.

---

### 1.2 `career_os/core/` — Çekirdek Motor

#### `career_os/core/skill_graph.py`
**Şu anki görev:** 68 skill, 74 edge içeren NetworkX DiGraph. `_build_taxonomy()` tüm kenarları hardcoded Python listesiyle tanımlar.

**Sorunlar (kritik):**
- Tüm taxonomy hardcoded Python kodu — yeni skill veya edge eklemek için kodu değiştirmek gerekiyor.
- ARCHITECTURE.md NetworkX → KuzuDB geçişini öngörüyor (Phase 3), ama bu Phase 3 işi.
- Şimdilik: graph mantığı `packages/graph/`'e, veri YAML'a.

**Yeni konum:**
- `SkillGraph` sınıfı → `packages/graph/skill_graph.py`
- `_build_taxonomy()` içindeki edge listesi → `knowledge/v1/skills/skill_graph.yaml`

**Yapılacak:**
1. `skill_graph.py`'i `packages/graph/`'e taşı.
2. `_build_taxonomy()` içindeki her `add_edge(a, b, weight=x)` çağrısını YAML'a al:
   ```yaml
   edges:
     - from: python
       to: pyspark
       weight: 0.6
     - from: pytorch
       to: tensorflow
       weight: 0.7
   ```
3. `SkillGraph.__init__` YAML'ı okuyup graph'i build etsin.
4. KuzuDB geçişini Phase 3'e ertele.

**Öncelik:** Yüksek — hem kod kalitesi hem de veri/mantık ayrımı açısından kritik.

---

### 1.3 `career_os/intelligence/` — Zeka Katmanı

#### `career_os/intelligence/semantic_matcher.py`
**Şu anki görev:** `SentenceTransformer('all-MiniLM-L6-v2')` ile 5 bileşenli skill matching.

**Sorunlar:**
- Model adı hardcoded string — config'den okunmalı.
- `_check_transfer()` 0.5'te caps — bu eşik niçin 0.5? Açıklama yok, YAML'a taşınmalı.

**Yeni konum:** `packages/intelligence/semantic_matcher.py`

**Yapılacak:**
1. Dosyayı taşı, import path'leri güncelle.
2. `SentenceTransformer('all-MiniLM-L6-v2')` → config'den oku.
3. Transfer cap eşiğini `knowledge/v1/skills/matching_config.yaml`'a çıkar.

**Öncelik:** Düşük — büyük yapısal değişiklik yok, sadece taşı + küçük refactor.

---

#### `career_os/intelligence/opportunity_scorer.py`
**Şu anki görev:** `OpportunityScorer` + `CareerDecisionEngine`. Fit, acceptance, career_value, market_demand skorlarını hesaplar.

**Sorunlar (kritik):**
- `_COMPANY_TIERS` dict hardcoded: `{'Google': 'big_tech', 'Anthropic': 'big_tech', ...}` — 15+ şirket Python'da saklanıyor.
- `_SKILL_DEMAND` dict hardcoded: `{'python': 0.95, 'aws': 0.9, ...}` — market verisi kod içinde.
- `_estimate_acceptance()` içindeki `big_tech=0.25` acceptance oranı gibi tüm katsayılar inline — bunların kaynağı ya referans yok ya da bu sayılar rastgele seçilmiş.

**Yeni konum:** `packages/intelligence/opportunity_scorer.py`

**Yapılacak:**
1. `_COMPANY_TIERS` → `knowledge/v1/companies/tiers.yaml`
2. `_SKILL_DEMAND` → `knowledge/v1/skills/market_demand.yaml`
3. Acceptance katsayılarını `knowledge/v1/scoring/acceptance_config.yaml`'a çıkar.
4. `CareerDecisionEngine` → `services/job-intelligence/application/decision_engine.py`

**Öncelik:** Yüksek — bu dosya en fazla hardcoded veri içeren dosya.

---

#### `career_os/intelligence/gap_analyzer.py`
**Şu anki görev:** `GapAnalyzer` + `LearningRoadmap`. ROI hesaplama, 8 haftalık plan, topological sort.

**Sorunlar:**
- `_RESOURCES` ve `_VALIDATION_PROJECTS` dict'leri hardcoded — yüzlerce satır Python kodu içinde statik veri.
- 8 haftalık plan, 10 saat/hafta gibi parametreler hardcoded.

**Yeni konum:**
- `GapAnalyzer` sınıfı → `packages/intelligence/gap_analyzer.py`
- `_RESOURCES` → `knowledge/v1/skills/learning_resources.yaml`
- `_VALIDATION_PROJECTS` → `knowledge/v1/skills/validation_projects.yaml`
- `create_roadmap()` → `services/learning-engine/application/roadmap_builder.py`

**Yapılacak:**
1. Sınıfı taşı.
2. İki büyük dict'i YAML'a çıkar.
3. Roadmap parametrelerini config'den oku (hafta sayısı, saat/hafta).

**Öncelik:** Orta.

---

### 1.4 `career_os/data/` — Veri Katmanı

#### `career_os/data/applypilot_loader.py`
**Şu anki görev:** ApplyPilot SQLite'tan iş ilanlarını okur, company/skill extraction yapar, `UserProfile` oluşturur.

**Sorunlar (kritik):**
- Bu dosya hem "plugin" (veri kaynağı adaptörü) hem "domain logic" (company/skill extraction) hem de "config loader" (UserProfile) — üç farklı sorumluluk tek dosyada.
- `_SKILL_PROFILES` dict (68 entry) burada tanımlı — `career_os/models/skill.py`'de veya YAML'da olmalı.
- `_KNOWN_ATS_DOMAINS` ve `_COMPANY_BLOCKLIST` sabitleri buraya hardcoded.

**Yeni konum:** Üç parçaya bölünecek:
- ApplyPilot SQL okuma kısmı → `plugins/job-sources/applypilot/client.py`
- Company/skill extraction logic → `plugins/job-sources/applypilot/adapter.py`
- `create_user_profile_from_config()` → `packages/domain/identity/profile_loader.py`

**Plugin interface:** ARCHITECTURE.md'deki `JobSourcePlugin` ABC'yi implement etmeli:
```python
class ApplyPilotPlugin(JobSourcePlugin):
    def fetch_jobs(self, since: datetime) -> list[JobDiscoveredEvent]: ...
    def get_metadata(self) -> PluginMetadata: ...
```

**Yapılacak:**
1. Dosyayı 3'e böl.
2. `JobSourcePlugin` ABC'yi `packages/plugins/base.py`'de tanımla.
3. `ApplyPilotPlugin`'i ABC'den türet.
4. `_SKILL_PROFILES` → `knowledge/v1/skills/profiles.yaml`
5. `_KNOWN_ATS_DOMAINS`, `_COMPANY_BLOCKLIST` → `knowledge/v1/companies/ats_domains.yaml`

**Öncelik:** Çok yüksek — bu plugin sisteminin temel taşı.

---

### 1.5 `scripts/scan/` — Tarama Betikleri

#### `scripts/scan/run_full_scan.py`
**Şu anki görev:** 6 adımlı pipeline: backup → discover → score → filter → Excel → summary. `applypilot.exe` process'ini çağırır, `logs/run_history.json` yazar.

**Sorunlar:**
- Subprocess çağrıları hardcoded path ile (`applypilot.exe`).
- Pipeline adımları event bus olmadan doğrudan birbirini çağırıyor.
- `run_history.json` yaklaşımı → `scan_history` DB tablosuyla değiştirilmeli (DATABASE_AUDIT.md'de önerildi).

**Yeni konum:** `workers/job-scanner/main.py`

**Yapılacak:**
1. Dosyayı `workers/job-scanner/`'a taşı.
2. Her pipeline adımının tamamlanmasında bir Event yayınla (`JobDiscovered`, `JobScored`, vb.).
3. `run_history.json` yazımını kaldır → `scan_history` DB tablosuna insert at.
4. ApplyPilot path'ini config'den oku.

**Öncelik:** Orta — mevcut haliyle çalışıyor, event-driven geçiş Phase 2 işi.

---

#### `scripts/scan/filter_jobs.py`
**Şu anki görev:** 8 SQL UPDATE filtresi — Senior, Frontend, Contract, Intern, JS-only, Analytics, Paris, 4+ yıl ilanlarının `fit_score`'unu düşürür.

**Sorunlar:**
- Filtreler hardcoded SQL — yeni filtre eklemek için kodu değiştirmek gerekiyor.
- Filtre mantığı "iş zekası" domain'ine ait — script olarak değil servis metodu olarak bulunmalı.

**Yeni konum:** `services/job-intelligence/application/filter_service.py`

**Yapılacak:**
1. Her filtre kural olarak YAML'a çıkarılabilir (`knowledge/v1/filters/score_rules.yaml`).
2. `FilterService` sınıfı YAML'dan kuralları okur, SQL UPDATE'leri uygular.
3. Filtre uygulandığında `JobFiltered` event'i yayınla.

**Öncelik:** Düşük — mevcut haliyle çalışıyor, YAML refactor iyileştirme.

---

#### `scripts/scan/export_to_excel_advanced.py`
**Şu anki görev:** 6 sayfalı Excel üretir. `YOUR_SKILLS` dict hardcoded.

**Sorunlar:**
- `YOUR_SKILLS` dict dosya başında hardcoded — `config.yaml`'dan veya `knowledge/v1/skills/`'den okunmalı.
- Excel, birincil çıktı formatı olmamalı — DB birincil, Excel isteğe bağlı export.
- Bu dosya ARCHITECTURE.md'de "optional plugin" olarak konumlandırılmış.

**Yeni konum:** `plugins/notifications/excel_exporter.py` (opsiyonel plugin)

**Yapılacak:**
1. `YOUR_SKILLS` hardcode'unu kaldır → `knowledge/v1/skills/` veya config'den oku.
2. Veri kaynağını Excel'den değiştir → `career_os.db` (DATABASE_AUDIT.md'deki `career_scores` tablosu).
3. Plugin olarak wrap et, opsiyonel bırak.

**Öncelik:** Düşük — Phase 2 sonrasında.

---

#### `scripts/scan/schedule_info.py`
**Şu anki görev:** `logs/run_history.json`'dan son tarama zamanını okur, "ne zaman tara?" önerir.

**Sorunlar:**
- `run_history.json`'a bağımlı — bu dosya kaldırılınca işlevsiz kalır.
- İşlevselliği `career-os status` CLI komutuyla karşılanabilir.

**Yeni konum:** `apps/cli/commands/status.py` içinde birleştir (ayrı dosya yok).

**Yapılacak:** DB'deki `scan_history` tablosunu sorgulayan bir CLI subcommand yaz, bu dosyayı sil.

**Öncelik:** Düşük.

---

### 1.6 `scripts/strategy/` — Strateji Betikleri

#### `scripts/strategy/apply_strategy.py`
**Şu anki görev:** Tam Career OS pipeline'ını çalıştırır, 5 `.txt` dosyası yazar.

**Sorunlar:**
- Çıktı `.txt` dosyaları — DB'ye yazılmalı.
- Tüm pipeline mantığı tek dosyada — CLI katmanı ile iş mantığı karışmış.

**Yeni konum:**
- CLI entry point → `apps/cli/commands/analyze.py`
- Pipeline mantığı → `services/job-intelligence/application/pipeline.py`

**Yapılacak:**
1. İş mantığını CLI entry point'ten ayır.
2. `.txt` dosyaları yazmaya devam edebilir (backward compat), **ama aynı zamanda** `career_scores` tablosuna da yaz.
3. Her pipeline adımı event yayınlasın.

**Öncelik:** Yüksek — DB geçişi için kilit dosya.

---

#### `scripts/strategy/cold_email_generator.py`
**Şu anki görev:** Excel'den iş okur, 5 farklı email template'i ile cold email + follow-up üretir, `.txt` yazar.

**Sorunlar (kritik):**
- `YOUR_INFO` dict hardcoded — adres, LinkedIn, GitHub, telefon kodu içinde.
- `ACHIEVEMENTS` dict hardcoded STAR formatında 3 başarı — Evidence Graph'e ait veri kod içinde.
- Veri kaynağı Excel — DB olmalı.
- Email'lerin gönderilip gönderilmediği takip edilmiyor.

**Yeni konum:**
- Email generation mantığı → `services/application-engine/application/email_generator.py`
- Template'ler → `templates/email/value_first.j2`, `templates/email/sponsorship_upfront.j2`, vb. (Jinja2)
- `YOUR_INFO` → `packages/domain/resume/` (Evidence Graph'in parçası)
- `ACHIEVEMENTS` → `packages/domain/resume/evidence.py` veya `knowledge/v1/resume/achievements.yaml`

**Yapılacak:**
1. 5 email template'ini Jinja2 dosyasına çıkar.
2. `YOUR_INFO` ve `ACHIEVEMENTS` → config/Evidence Graph.
3. Veri kaynağını Excel → `emails` DB tablosuna değiştir.
4. Üretilen email'leri `emails` tablosuna yaz (`sent_at = NULL` olarak).

**Öncelik:** Orta.

---

#### `scripts/strategy/skills_gap_analyzer.py`
**Şu anki görev:** Excel'deki "Missing Skills" sütunundan frequency analizi, 8 haftalık öğrenme planı üretir.

**Sorunlar:**
- `YOUR_SKILLS` dict hardcoded (aynı liste `export_to_excel_advanced.py`'de de var — duplikasyon).
- `LEARNING_RESOURCES` dict hardcoded — `gap_analyzer.py`'deki benzer dict ile çakışıyor (iki ayrı kaynak).
- Veri kaynağı Excel — DB olmalı.
- `gap_analyzer.py` ile işlev örtüşüyor.

**Yeni konum:** `apps/cli/commands/gaps.py` — ince bir CLI wrapper, asıl mantık `packages/intelligence/gap_analyzer.py`'de.

**Yapılacak:**
1. `LEARNING_RESOURCES` → `knowledge/v1/skills/learning_resources.yaml` (gap_analyzer.py ile birleştir, duplikasyonu kaldır).
2. `YOUR_SKILLS` → tek bir kaynak: `config.yaml` veya `knowledge/v1/skills/`.
3. Veri kaynağını Excel → `career_scores` tablosuna geçir.
4. Bu dosyayı `gap_analyzer.py` üzerinde ince bir CLI wrapper'a indirge.

**Öncelik:** Orta — önce duplikasyonu kaldır.

---

#### `scripts/strategy/extract_requirements.py`
**Şu anki görev:** ApplyPilot DB'sinden `full_description` okur, regex ile requirements section çıkarır, skill frequency analizi yapar, `.json` + `.txt` yazar.

**Sorunlar:**
- `apply_status` ve `applied_at` sütunlarını sorguluyor — bu sütunlar ApplyPilot'un DB şemasında var mı kontrol edilmeli (yoksa hata).
- `job_requirements_analysis/` klasörüne çıktı yazar — bu klasör tanımlı dizin yapısında yok.
- `semantic_matcher.py`'deki extraction ile örtüşüyor.

**Yeni konum:** `services/job-intelligence/application/requirement_extractor.py`

**Yapılacak:**
1. `job_requirements_analysis/` → `data/exports/` veya tamamen DB'ye yaz.
2. `apply_status` sütunu olmayan DB'lerde crash'i önle (nullable check ekle).
3. `semantic_matcher.py`'deki skill keyword listesiyle birleştir, duplikasyonu kaldır.

**Öncelik:** Düşük.

---

### 1.7 `scripts/tracking/` — Takip Betikleri

#### `scripts/tracking/track_applications.py`
**Şu anki görev:** Excel "Notes" sütununu parse eder, `docs/tracking/JOB_APPLICATIONS.md` günceller.

**Sorunlar (kritik):**
- Notes sütununu parse etmek → veri kaynağı olarak Excel kullanmak kırılgan.
- Çıktı Markdown dosyası → sorgulanamaz.
- DATABASE_AUDIT.md'de tam olarak bu senaryo için `applications` tablosu önerildi.

**Yeni konum:** `services/application-engine/application/tracker.py`

**Yapılacak:**
1. Excel okumayı kaldır.
2. `applications` tablosuna doğrudan yaz/oku.
3. Markdown dosyası yerine `career-os track` CLI komutu DB'yi sorgulasın.
4. Mevcut Excel'deki Notes verilerini tek seferlik migration script'i ile DB'ye aktar.

**Öncelik:** Çok yüksek — veri kaybı riski en yüksek olan bileşen bu.

---

#### `scripts/tracking/sync_to_github.py`
**Şu anki görev:** Excel'den GitHub Issues oluşturur.

**Sorunlar:**
- `REPO_NAME = "YOUR_USERNAME/applypilot-jobs"` — placeholder bırakılmış, çalışmaz.
- Excel bağımlılığı.
- Bu işlevsellik "zorunlu" değil, "opsiyonel entegrasyon."

**Yeni konum:** `plugins/notifications/github_issues.py` (opsiyonel plugin)

**Yapılacak:**
1. Veri kaynağını Excel → `applications` DB tablosuna geçir.
2. `REPO_NAME` → config.yaml'dan oku.
3. Plugin interface'i implement et.

**Öncelik:** Düşük — opsiyonel özellik.

---

### 1.8 `scripts/packaging/setup_package.py`
**Şu anki görev:** Proje dosyalarını zip'ler, başkasına kurulum paketi oluşturur.

**Sorunlar:**
- Bu dosyanın amacı yok artık — proje pip install edilebilir bir paket olacak.
- `pyproject.toml` + `pip install career-os` bu ihtiyacı karşılar.

**Yeni konum:** **Silinecek.**

**Yapılacak:** `pyproject.toml` yaz, bu dosyayı sil.

**Öncelik:** Düşük — kolayca silinebilir.

---

### 1.9 Konfigürasyon ve Destek Dosyaları

#### `config.yaml`
**Sorunlar (kritik):**
- Plaintext API anahtarı: `sk-or-v1-4d7abdbc97...` — bu repo'da yaşamamalı.
- Kullanıcı profili burada tanımlı ama `applypilot_loader.py` onu okuyor → kırılgan bağımlılık.

**Yeni konum:** `~/.career-os/config.yaml` (kullanıcının home dizini, repo dışı)

**Yapılacak:**
1. API anahtarını `~/.career-os/.env`'e veya OS keychain'e taşı.
2. `config.yaml`'ı home dizinine taşı.
3. `.gitignore`'a `config.yaml` ve `.env` ekle (şu an yoksa).
4. Repo'da sadece `config.yaml.example` bırak (gerçek değerler olmadan).

**Öncelik:** Çok yüksek — güvenlik riski.

#### `requirements.txt`
**Yeni konum:** `pyproject.toml` → `[project.dependencies]`

**Yapılacak:** `pyproject.toml` oluştur, `requirements.txt`'i koru (eski kullanıcılar için).

#### `run_scan.bat`
**Yeni konum:** `career-os scan` CLI komutu veya `Makefile`.

**Yapılacak:** Sil, CLI komutuna yönlendir.

---

## 2. Gereksiz / Kaldırılacak Dosya ve Klasörler

| Dosya / Klasör | Neden Kaldırılıyor | Yerine Ne Geçiyor |
|---|---|---|
| `scripts/packaging/setup_package.py` | Artık pip paketi olacak | `pyproject.toml` |
| `run_scan.bat` | CLI komutu ile değişiyor | `career-os scan` |
| `career_os_output/*.txt` | DB'ye taşınıyor | `career_scores` tablosu |
| `reports/` (birincil çıktı olarak) | DB birincil, Excel opsiyonel | `career_os.db` + isteğe bağlı export |
| `logs/run_history.json` | DB'de `scan_history` tablosu var | `scan_history` tablosu |
| `backups/db_*.sqlite` | Gerçek DB backup stratejisi gerekiyor | pgdump / otomatik backup |
| `learning_plan/` klasörü | `skills_gap_analyzer.py` çıktısı, DB'ye taşınıyor | `career_scores.skill_gaps` kolonu |
| `job_requirements_analysis/` klasörü | `extract_requirements.py` çıktısı | `services/job-intelligence` DB'ye yazar |

---

## 3. Sıfırdan Yazılacaklar (v0'da Hiç Yok)

Bunlar ARCHITECTURE.md'de tanımlı ama mevcut kodda hiçbir karşılığı olmayan bileşenler:

### Phase 1 (Öncelikli — Temeller)
| Bileşen | Konum | Açıklama |
|---|---|---|
| Event Bus | `events/bus.py` | In-memory başlar, Phase 2'de Redis Streams |
| Event tipleri | `events/types.py` | `JobDiscovered`, `JobScored`, `ApplicationSubmitted`, vb. |
| PostgreSQL migrations | `database/migrations/` | `timeline_snapshots`, `timeline_changes` tabloları |
| `career_os.db` SQLite | `packages/db/local.py` | DATABASE_AUDIT.md'deki 4 tablo |
| `JobSourcePlugin` ABC | `packages/plugins/base.py` | Plugin interface tanımı |
| Feature registry | `features/registry.py` + `feature.yaml` | Feature flag sistemi |
| `pyproject.toml` | proje kökü | Paket tanımı, bağımlılıklar |

### Phase 2 (Servisler)
| Bileşen | Konum | Açıklama |
|---|---|---|
| AI Memory Layer | `packages/memory/` | `candidate_memory`, `company_memory`, `market_memory` |
| LanceDB vektör DB | `packages/vector/` | Semantic search için |
| FastAPI gateway | `apps/api/main.py` | REST API |
| Typer CLI | `apps/cli/main.py` | `career-os scan`, `career-os status`, vb. |
| Knowledge loader | `packages/knowledge/loader.py` | YAML dosyalarını yükler |

### Phase 3 (İleri)
| Bileşen | Konum | Açıklama |
|---|---|---|
| Timeline engine | `packages/timeline/` | Durum geçişlerini takip eder |
| KuzuDB graph | `packages/graph/kuzu_adapter.py` | NetworkX → KuzuDB geçişi |
| Evidence Graph | `packages/domain/resume/evidence_graph.py` | GitHub commit → confidence score |
| Target-Aware Resume | `services/resume-engine/` | Pozisyona özel CV üretimi |

### Phase 4 (UI)
| Bileşen | Konum | Açıklama |
|---|---|---|
| Next.js dashboard | `apps/web/` | Visual career OS |
| Evaluation suite | `evaluation/` | AI benchmark metrikleri |

---

## 4. YAML'a Çıkarılacak Hardcoded Veriler

Bunlar şu an Python kodu içinde statik veri olarak duruyor. Önce YAML'a çıkarmak en hızlı kazanım.

| Veri | Şu an nerede | Yeni yer |
|---|---|---|
| `_SKILL_PROFILES` (68 skill) | `applypilot_loader.py` | `knowledge/v1/skills/profiles.yaml` |
| `SKILL_CATEGORIES` dict | `career_os/models/skill.py` | `knowledge/v1/skills/categories.yaml` |
| `_build_taxonomy()` edges (74 edge) | `career_os/core/skill_graph.py` | `knowledge/v1/skills/skill_graph.yaml` |
| `_COMPANY_TIERS` dict | `opportunity_scorer.py` | `knowledge/v1/companies/tiers.yaml` |
| `_SKILL_DEMAND` dict | `opportunity_scorer.py` | `knowledge/v1/skills/market_demand.yaml` |
| `_RESOURCES` + `_VALIDATION_PROJECTS` | `gap_analyzer.py` | `knowledge/v1/skills/learning_resources.yaml` |
| `LEARNING_RESOURCES` (duplikat) | `skills_gap_analyzer.py` | Aynı YAML — duplikat kaldır |
| `YOUR_SKILLS` (3 ayrı dosyada!) | `export_to_excel_advanced.py`, `skills_gap_analyzer.py`, `cold_email_generator.py` | Tek kaynak: `config.yaml` veya `knowledge/v1/` |
| `YOUR_INFO` (kişisel bilgi) | `cold_email_generator.py` | `packages/domain/resume/` |
| `ACHIEVEMENTS` (STAR format) | `cold_email_generator.py` | `knowledge/v1/resume/achievements.yaml` |
| `_KNOWN_ATS_DOMAINS` | `applypilot_loader.py` | `knowledge/v1/companies/ats_domains.yaml` |
| `_COMPANY_BLOCKLIST` | `applypilot_loader.py` | Aynı YAML |
| Acceptance katsayıları | `opportunity_scorer.py` | `knowledge/v1/scoring/acceptance_config.yaml` |
| Filter SQL kuralları | `filter_jobs.py` | `knowledge/v1/filters/score_rules.yaml` |

---

## 5. Göç Öncelik Sırası

### Acil (güvenlik + veri kaybı riski)
1. **API anahtarını kaldır** — `config.yaml`'daki `sk-or-v1-...` anahtarını environment variable'a taşı. Git geçmişini temizle (`git filter-branch` veya BFG).
2. **`applications` DB tablosu** — `track_applications.py`'nin Excel Notes yaklaşımını değiştir. Her yeni scan mevcut başvuru notlarını eziyor.
3. **`career_scores` DB tablosu** — `apply_strategy.py`'nin `.txt` çıktılarını DB'ye de yaz.

### Yüksek (mimarinin çalışması için)
4. **`JobSourcePlugin` ABC** + `applypilot_loader.py`'yi plugin'e dönüştür.
5. **YAML extraction** — en az skill_graph, company_tiers, skill_demand.
6. **Domain model split** — `profile.py` ve `skill.py`'yi böl.

### Orta (temizlik + sürdürülebilirlik)
7. Tüm `career_os/intelligence/` modüllerini `packages/intelligence/`'a taşı.
8. `YOUR_SKILLS` duplikasyonunu tek kaynağa indir.
9. Email template'lerini Jinja2'ye çıkar.
10. Event Bus'ı in-memory olarak implement et.

### Düşük (opsiyonel iyileştirmeler)
11. Excel'i opsiyonel plugin'e dönüştür.
12. `sync_to_github.py`'yi plugin'e dönüştür.
13. `schedule_info.py` → CLI `status` komutuyla birleştir.
14. `setup_package.py`'yi sil, `pyproject.toml` yaz.
15. `run_scan.bat` → `Makefile` veya CLI.

---

## 6. Özet: Dosya Sayımı

| Kategori | Dosya Sayısı |
|---|---|
| Taşınacak (küçük değişiklikle) | 6 |
| Bölünecek (sorumluluk ayrımı) | 4 |
| Büyük refactor gerektirenler | 5 |
| Silinecekler | 4 |
| Sıfırdan yazılacaklar (Phase 1-2) | ~15 |
| YAML'a çıkarılacak veri setleri | 14 |

Mevcut kod toplamda **~3.500 satır** iş mantığı içeriyor. Bunların büyük çoğunluğu korunacak — yeri ve formu değişecek. Sıfırdan yazılacak bileşenler ağırlıklı olarak altyapı katmanı (Event Bus, DB migrations, plugin registry, CLI).
