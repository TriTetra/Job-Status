# Changelog

Her commit, her mimari karar, her belge değişikliği burada kayıt altında.  
Sıralama: en yeniden en eskiye.

---

## Phase Tamamlanma Tablosu

| Phase | İçerik | Durum | Tarih |
|-------|---------|-------|-------|
| Phase 0 | Hazırlık: git tag, backup, API key rotation, architecture planning | ✅ Tamam | 2026-07-13 |
| Phase 1A | PostgreSQL DB layer: 4 tablo, Alembic migrations, repositories | ✅ Tamam | 2026-07-13 |
| Phase 1B | Career Scores → PostgreSQL; skill extraction fix; threshold fix | ✅ Tamam | 2026-07-14 |
| Phase 1C | Scan history tracking: `scan_history` tablosu, bulk diff | ✅ Tamam | 2026-07-14 |
| Phase 2A | `packages/intelligence/` migration; backward-compat shim | ✅ Tamam | 2026-07-14 |
| Phase 2B | `services/hiring-agent/` CV scoring; OpenRouter; GitHub token fix | ✅ Tamam | 2026-07-14 |
| Phase 2G | Evidence Graph → DB: `evidence` tablosu, `EvidenceRepository`, `EvidenceBuilder` | ✅ Tamam | 2026-07-14 |
| Phase 2I | Skill Graph YAML: 68 skill, 229 topic, `SkillLoader`, hardcode sıfır | ✅ Tamam | 2026-07-14 |
| Phase 2J | Application Engine: `services/application_engine/cli.py`, 6 komut, state machine | ✅ Tamam | 2026-07-14 |
| Refactor | Plugin + Config-Driven Architecture: `config/plugins.yaml`, `ResumeParserPlugin` ABC | ✅ Tamam | 2026-07-14 |
| Event Bus | Thread-safe pub/sub: `events/`, 18 domain event tipi | ✅ Tamam | 2026-07-14 |
| ApplyPilot Plugin | `JobSourcePlugin` ABC, SQLite client/adapter, config-driven | ✅ Tamam | 2026-07-14 |
| Single DB | PostgreSQL `jobs` tablosu, `JobRepository`, 562 job sync | ✅ Tamam | 2026-07-14 |
| Multi-User | `user_id` 5 tabloya eklendi, repo/caller güncellemesi | ✅ Tamam | 2026-07-14 |
| Week 3 Domain | `packages/domain/` — identity/job/intelligence; 7/7 test | ✅ Tamam | 2026-07-14 |
| Phase 2C | Target-aware resume generator: 4 LLM call, `available_skills` constraint | ✅ Tamam | 2026-07-14 |
| Phase 3 (CI) | Company Intelligence: enricher, memory service, per-company advice | ✅ Tamam | 2026-07-14 |
| Phase 3 (MI) | Market Intelligence: HN "Who is Hiring?" scanner, TechCrunch RSS | ✅ Tamam | 2026-07-14 |
| Phase 3 (GH) | GitHub Enrichment: 9 real metrics, hallucination fix, `loc_count` | ✅ Tamam | 2026-07-14 |
| Phase 3 (TL) | Timeline Layer: `track_snapshot()`, auto-diff, `detect_changes()` | ✅ Tamam | 2026-07-14 |
| Phase 3 (KB) | Knowledge DB: 14 YAML → 5 country + 3 visa + 50+ salary rows | ✅ Tamam | 2026-07-14 |
| Phase 4A | FastAPI Gateway: 24 endpoint, CORS, Pydantic v2, live-tested | ✅ Tamam | 2026-07-14 |
| Phase 4B | Domain Migration: 15 entity → 6 subdomain (`core/domain/`) | ✅ Tamam | 2026-07-14 |
| Phase 4C | Service Extraction: `identity_service`, `job_intelligence` | ✅ Tamam | 2026-07-14 |
| Phase 4D | Unified CLI: `career-os` launcher, 4 native + 4 sub-groups (Typer) | ✅ Tamam | 2026-07-14 |
| Docs v1 | `docs/v1/` versioned layout; Phase 1/2/3 Architecture Reports | ✅ Tamam | 2026-07-14 |

---

## [Docs v1] — 2026-07-14 — Versioned Architecture Reports ✅

### Yapılan
`docs/` dizini versioned `docs/v1/` layoutuna taşındı. Her fazın tam teknik raporu yazıldı ve codebase'e karşı doğrulandı.

**Dizin Yapısı:**
```
docs/v1/
├── ARCHITECTURE.md          — Genel mimari
├── CODEBASE_OVERVIEW.md     — Tam codebase anatomisi
├── SYSTEM_SUMMARY.md        — Executive summary
├── VISION.md                — Ürün doktrini
├── DIRECTORY_MAP.md         — Klasör açıklamaları
├── development/
│   ├── DATABASE_AUDIT.md
│   └── MIGRATION_REPORT.md
└── phases/
    ├── PHASE_1_REPORT.md    — Foundation (DB, Events, CLI, Plugins, 24 endpoint)
    ├── PHASE_2_REPORT.md    — Intelligence Core (Evidence Graph, Resume AI, Hiring-Agent)
    └── PHASE_3_REPORT.md    — Company & Market Intelligence (8 DB tablo, Timeline, Knowledge DB)
```

**Raporlarda Doğrulanan Düzeltmeler:**
- Faz 1: Endpoint sayısı 21→24 (companies 4, settings 4, main +root+health)
- Faz 1: `POST /api/jobs/score` yok → `GET /api/jobs/pipeline`
- Faz 2: Feature Registry `_archive/features/` altında (aktif dizinde değil)
- Faz 2: Test sayısı 5→4 aktif (`test_feature_registry.py` → `_archive/scripts/`)
- Faz 3: `CompanyMemoryRepository` ayrı dosyada değil — `company_repo.py` (L67) içinde

---

## [Phase 4D] — 2026-07-14 — Unified CLI ✅

**Commit:** `654085c`

### Yapılan

**`apps/cli/main.py`** (182 satır) — Typer tabanlı unified CLI
- 4 native komut: `version`, `status`, `scan`, `strategy`
- 4 mounted sub-group: `track`, `resume`, `company`, `market`
- Try/except mounting pattern — import failure silently skip edilir
- `career-os` launcher script: `apps/cli/career_os_launcher.py`

**Sub-group CLI'ları:**
- `track` → `services/application_engine/cli.py`
- `resume` → `services/resume_intelligence/cli.py`
- `company` → `services/company_intelligence/cli.py`
- `market` → `services/market_intelligence/cli.py`

**Kullanım:**
```
career-os version
career-os status
career-os track add --url ... --title ... --company ...
career-os resume generate --company Google --title "ML Engineer"
career-os company show --name Google
career-os market signals --source hackernews
```

---

## [Phase 4C] — 2026-07-14 — Service Extraction ✅

**Commit:** `a613a33`

### Yapılan

`packages/domain/` içinde iki yeni service modülü:

**`core/services/identity_service.py`**
- `IdentityService` — user profile, skill management, evidence CRUD
- `get_user_profile()`, `add_skill()`, `get_evidence_summary()`

**`core/services/job_intelligence.py`**
- `JobIntelligenceService` — job scoring, pipeline filtering, career score queries
- `score_jobs()`, `get_pipeline()`, `get_top_opportunities()`

Her iki servis de `BaseRepository[T]` üzerinden DB'ye erişir; FastAPI router'ları bu servisleri dependency injection ile kullanır.

---

## [Phase 4B] — 2026-07-14 — Domain Migration ✅

**Commit:** `f7c577d`

### Yapılan

15 entity, 6 subdomain'e migrate edildi:

```
core/domain/
├── identity/     user.py, skill.py, profile.py
├── job/          job.py, scan.py
├── evidence/     evidence.py, github_metrics.py
├── application/  application.py, email.py
├── company/      company.py, memory.py
└── market/       signal.py, timeline.py
```

**Backward-compat shim'ler:** `packages/domain/*.py` → `core/domain/*` re-export

---

## [Phase 4A] — 2026-07-14 — FastAPI Gateway ✅

**Commit:** `3dd3fa2`

### Yapılan

**`apps/api/app/main.py`** — FastAPI app
- 7 router mount + root + health = **24 endpoint** (live-tested)
- CORS: `localhost:3000`, `localhost:3001`, `127.0.0.1:3000`

**Router → Endpoint Tablosu:**

| Router | Endpoint'ler | Sayı |
|---|---|---|
| jobs | GET /api/jobs, GET /api/jobs/pipeline, GET /api/jobs/{url} | 3 |
| applications | GET /, GET /summary, POST /, PUT /{url} | 4 |
| evidence | GET /, POST /build, GET /{skill}, DELETE /{id} | 4 |
| companies | GET /, GET /hiring, GET /{name}, GET /{name}/memory | 4 |
| market | GET /signals, GET /summary, GET /trend/{skill} | 3 |
| settings | GET /, PUT /, GET /validate, POST /reload | 4 |
| resume | GET /templates, POST /generate | 2 |
| main | GET /, GET /health | 2 |

**Dependency injection:** `get_db_session()`, `get_user_id()` — tüm router'larda tutarlı
**Schemas:** Pydantic v2, `model_config = ConfigDict(from_attributes=True)`

---

## [Phase 3 — Knowledge DB] — 2026-07-14 ✅

**Commit:** `4afc006` (DB-First Knowledge Layer)

### Yapılan

14 YAML dosyası → PostgreSQL (one-time seed, sonrası DB source of truth)

**`scripts/seed_knowledge_from_yaml.py`** (213 satır)
- `seed_countries()` → 5 kayıt (`germany`, `canada`, `netherlands`, `uae`, `usa`)
- `seed_visas()` → 3 kayıt (EU Blue Card, US H1B, UK Skilled Worker)
- `seed_salaries()` → 50+ kayıt (backend_eu, ml_us, frontend_global)
- `session.merge()` upsert (iso_code / visa_type PK)
- Salary: composite key manual upsert

**DB Modeller:** `countries`, `visas`, `salary_ranges` — JSONB columns for flexible data

**YAML Seed Dosyaları (14 adet, ~2,500 satır):**
```
infra/seeds/v1/countries/  → germany, canada, netherlands, uae, usa
infra/seeds/v1/visa/       → eu_blue_card, us_h1b, uk_skilled_worker
infra/seeds/v1/salaries/   → backend_eu, ml_us, frontend_global
infra/seeds/v1/companies/  → big_tech, unicorns, company_memory_schema
```

**Sonuç:** `Total: 58 records seeded` — DB artık knowledge'ın canonical kaynağı

---

## [Phase 3 — Timeline Layer] — 2026-07-14 ✅

### Yapılan

**`core/timeline/timeline.py`** (295 satır)
- `track_snapshot(entity_type, entity_id, data)` — zaman serisi snapshot
- `_detect_and_record_changes()` — auto-diff: field-by-field önceki snapshot ile karşılaştır
- `get_entity_history(entity_type, entity_id, days)` — temporal query
- `detect_changes(entity_type, entity_id, field, days)` — field-level change query
- `get_trending_entities(entity_type, field, days, limit)` — en çok değişen entity'ler

**`core/db/models/timeline.py`** (53 satır)
- `TimelineSnapshot` — entity state at a point in time (JSONB)
- `TimelineChange` — field-level diff record (`old_value`, `new_value`, `change_type`)

**Migration:** `add_timeline_tables.py` — 2 tablo + indexes

**Kullanım Örneği:**
```python
timeline.track_snapshot("job", job_url, {"career_score": 91, "company": "Google"})
# Otomatik diff → "career_score: 78 → 91 (↑ 16.7%)"
```

---

## [Phase 3 — GitHub Enrichment] — 2026-07-14 ✅

### Yapılan

**Problem:** Evidence confidence'ı heuristik hesaplanıyordu (commit sayısı + star). LLM resume oluştururken GitHub URL yoksa project details hallucinate ediyordu.

**Çözüm:** PyGithub → 9 gerçek metrik → `evidence` tablosuna yazıldı.

**`plugins/enrichment/github/repo_analyzer.py`** (88 satır)
- 9 metrik: `loc_count`, `language`, `topics`, `has_tests`, `has_docs`, `has_releases`, `pr_count`, `issue_count`, `contributor_count`

**`plugins/enrichment/github/evidence_enricher.py`** (117 satır)
- Her `evidence` kaydı için GitHub URL → repo_analyzer → DB UPDATE
- Confidence formula güncellendi: LOC, has_tests, has_docs ağırlık eklenildi

**`scripts/enrich_github_evidence.py`** (69 satır) — CLI runner

**`services/resume_intelligence/application/resume_generator.py`**
- `_load_evidence()` artık `loc_count`, `has_tests`, `pr_count` vs. DB'den okuyor
- `_tailor_evidence()` → `available_skills=list(evidence.keys())` — LLM'e gerçek skill listesi verildi
- `_normalize_skill_names()` — fuzzy match: LLM döndürdüğü skill adları → gerçek evidence key'leri

**Sonuç:** LLM artık gerçek metriklerle çalışıyor, hallucination büyük ölçüde çözüldü.

---

## [Phase 3 — Market Intelligence] — 2026-07-14 ✅

### Yapılan

**HN "Who is Hiring?" Scanner:**
- `plugins/market_signals/hackernews/client.py` (67 satır) — Algolia API
- `plugins/market_signals/hackernews/who_is_hiring_parser.py` (72 satır) — comment → structured job
- `plugins/market_signals/hackernews/signal_extractor.py` (122 satır)
  - 272 job posting → 42 signal (Temmuz 2026)
  - Top 20 skill demand, Top 20 company hiring spikes, remote/visa stats

**TechCrunch Scanner:**
- `plugins/market_signals/techcrunch/rss_client.py` (40 satır) — feedparser
- `plugins/market_signals/techcrunch/signal_extractor.py` (105 satır) — funding/layoff detection

**`core/db/models/market_signal.py`** — `signal_type`, `skills_affected` (JSONB array), `magnitude`
**`core/db/repositories/market_signal_repo.py`** (182 satır)
- `get_skill_trend()` — period-over-period (current window vs previous window)
- `source_id` ile dedup

**`services/market_intelligence/cli.py`** (97 satır) — `signals scan`, `trend show`, `summary`

---

## [Phase 3 — Company Intelligence] — 2026-07-14 ✅

### Yapılan

**`services/company_intelligence/application/company_enricher.py`** (75 satır)
- Job posting → tech stack aggregation
- `CompanyRepository.update_tech_stack()` — JSONB merge, existing skills korunur

**`services/company_intelligence/application/company_memory.py`** (96 satır)
- `record_interview_fact()` — "Google'da Docker ve Redis soruldu"
- `get_advice_for_company()` — rejection pattern detection + advice generation
- 3+ reject → "6 ay bekle", 1 reject → "phone screen'e hazırlan"

**`core/db/repositories/company_repo.py`** (135 satır)
- `CompanyRepository` + `CompanyMemoryRepository` — **aynı dosyada**
- `get_or_create()`, `get_hiring_now()`, `find_by_tech_stack()`, `update_tech_stack()`
- `add_fact()`, `get_facts_for_company()`, `get_company_summary()`

**`services/company_intelligence/cli.py`** (97 satır) — `show`, `enrich`, `memory`

**Migration:** `add_companies_and_memory.py` — `companies` + `company_memory` tabloları

---

## [Phase 2C] — 2026-07-14 — Target-Aware Resume Generator ✅

### Yapılan

**`services/resume_intelligence/application/resume_generator.py`** (357 satır)

5-adımlı pipeline:
1. Evidence DB + GitHub cache yükle
2. `_extract_priorities()` — job title/company → `{must_have, important, culture_signals}`
3. `_tailor_evidence()` — `available_skills` constraint → LLM hallucination önlendi
4. `_select_projects()` — max 4 proje, score-based ranking
5. `_generate_summary()` — 2-satır özet, max 200 token

**`_normalize_skill_names()`** (35 satır)
- LLM çıktısındaki skill adları → gerçek evidence key'leri
- Exact match → lowercase match → skill_mappings dict → partial match → top-confidence fallback

**`_role_hint()`** — JD yoksa role tipine göre domain hint injection (10 role tipi)

**Jinja2 template rendering:** `services/resume_intelligence/templates/resume/`
- `ml_research.md.jinja`, `backend.md.jinja`

**Output:** `personal/{Name}_{Company}_{Role}.md` — Markdown CV

---

## [Week 3 Domain Migration] — 2026-07-14 ✅

### Yapılan
`career_os/models/` → `packages/domain/` migration: entity'ler 3 domain'e dağıtıldı.

**Yeni yapı:**
```
packages/domain/
├── identity/   skill.py, profile.py  (Skill, SkillLevel, UserProfile, Experience, UserPreferences)
├── job/        job.py                (Job)
└── intelligence/ match.py, scoring.py (MatchResult, OpportunityScore)
```

**Güncellemeler:**
- `packages/intelligence/*.py` — `from packages.domain import ...` kullanıyor
- `career_os/data/applypilot_loader.py` — `from packages.domain import ...`
- `career_os/core/skill_graph.py` — `from packages.domain.identity.skill import Skill`
- `career_os/models/` — backward-compat shim (re-export, aynı class instance)

**Sınıf identity korundu:** `career_os.models.Skill is packages.domain.Skill` → True

### Test
```
python scripts/test_domain_migration.py  # 7/7 PASS
```

---

## [Multi-User] — 2026-07-14 — Multi-user foundation ✅

### Ne Yapıldı
- **Alembic migration** `b2c3d4e5f6a7` — `user_id VARCHAR(100) NOT NULL DEFAULT 'default'`
  5 tabloya eklendi: `career_scores`, `applications`, `emails`, `scan_history`, `evidence`
- **Mevcut veriler** otomatik `user_id='default'` olarak backfill edildi (200 score, 562 scan, 25 evidence)
- **Tüm repository metotları** `user_id: str = "default"` parametresi aldı:
  `CareerScoreRepository`, `ApplicationRepository`, `EvidenceRepository`, `ScanHistoryRepository`
- **Caller güncelleme**: `apply_strategy.py`, `run_full_scan.py`, `evidence_builder.py`
  artık `config.yaml → user.id`'den `user_id` alıyor
- **`config.yaml`** `user.id = "abdullokh"` bloğu eklendi
- **`config_loader.py`** `user.id` yoksa otomatik `"default"` fallback

### Test
```
python scripts/test_multiuser_migration.py
# 5/5 PASS
```

### Mimari
- PKs değiştirilmedi (emails FK bozulmaması için)
- `user_id` filtre kolonu + index — tüm sorgular user'a göre izole
- `jobs` tablosu shared (global katalog, user_id yok)
- Phase 3 Auth'ta kolayca JWT/session → user_id mapping yapılabilir

---

## [Single DB] — 2026-07-14 — PostgreSQL tek veritabanı ✅

### Problem
`ApplyPilotPlugin` iş ilanlarını harici bir SQLite dosyasından (`~/.applypilot/applypilot.db`)
okuyordu. Proje kendi veritabanında sadece URL ve skorları tutuyordu; başlık/şirket/açıklama
bilgileri PostgreSQL'de yoktu.

### Çözüm
- **`packages/db/models/job.py`** — yeni `Job` modeli (url PK, title, company, description,
  required_skills JSONB, salary_min/max, remote, vb.)
- **`packages/db/repositories/job_repo.py`** — `JobRepository` (`upsert_many`, `get_unscored`,
  `known_urls`)
- **Alembic migration** `a1b2c3d4e5f6` — `jobs` tablosu + 6 index (GIN dahil)
- **`scripts/sync_jobs_from_applypilot.py`** — SQLite → PostgreSQL tek seferlik/tekrarlı sync
  (`--min-score`, `--hours` flag'leri)

### Sonuç
```
python scripts/sync_jobs_from_applypilot.py
# → 562 job PostgreSQL jobs tablosuna aktarıldı
# → company known: 261/562, remote: 388/562
```

SQLite artık sadece ApplyPilot tarafından yazılan harici bir INPUT kaynağı.
Projenin kendi pipeline'ı tamamen PostgreSQL üzerinde çalışıyor.

---

## [ApplyPilot Plugin] — 2026-07-14 — Job Source Plugin (Week 2) ✅

### Değişiklikler

**`plugins/plugin_interface.py`** — `JobSourcePlugin` ABC eklendi
- `scan(hours_old, min_score)` — raw job listesi
- `normalize(raw_job)` — canonical schema'ya dönüşüm
- `scan_and_normalize()` — convenience, hata izole

**`config/plugins.yaml`** — `job_sources.applypilot` bloğu
- `db_path`, `columns`, `table_name` — kaynak konfigürasyonu
- `company_extraction`: ATS domain listesi (13 alan), blocklist (19 kelime), pattern sırası
- `skill_extraction`: 37 keyword, requirements section scoping, `max_section_chars`
- `salary_patterns`: 3 regex (USD, EUR, bare number) — YAML single-quote regex escaping fix uygulandı
- `company_sizes`: big_tech (9 şirket), large (6 şirket)
- `seniority`: title patterns (senior/junior/lead), description `(\d+)+ years` regex

**`plugins/job_sources/applypilot/client.py`**
- `ApplyPilotClient` — SQLite I/O, `hours_old` filtresi, `count_jobs()`, `get_all_urls()`
- `ApplyPilotPlugin(JobSourcePlugin)` — high-level interface, `adapter` + `client` composition

**`plugins/job_sources/applypilot/adapter.py`**
- Company extraction: LinkedIn slug → title pattern → ATS-filtered app URL → description NLP
- Skill extraction: requirements section öncelikli, word-boundary matching
- Salary: 3 configurable regex pattern
- Seniority: title keyword → description `X years experience`
- Remote: `remote/anywhere/wfh` keyword scan

**`plugins/plugin_loader.py`**
- `load_job_source_plugin(name)` factory
- `list_available_job_sources()` → metadata dict

**`scripts/test_applypilot_plugin.py`** — 6/6 test geçti
- 562 iş DB'de, 151 son 72 saatte, şirket extraction oranı %54

---

## [Event Bus] — 2026-07-14 — Domain Event Pub/Sub Foundation ✅

### Değişiklikler

**`events/event_bus.py`** — Thread-safe singleton
- `subscribe(event_type, handler)` — direct + `@decorator` syntax her ikisi de çalışıyor
- `publish(event)` — handler hataları izole, diğer handler'ları durdurmaz
- `get_history(event_type, limit)` — debug için son N event'i tutar (`deque(maxlen=1000)`)
- `unsubscribe()`, `clear()`, `stats()` — tam kontrol
- `RLock` — nested publish için reentrant lock

**`events/event_types.py`** — `Event` base dataclass (UUID, UTC timestamp, source)

**8 domain event modülü — 18 event tipi:**
- `job_events`: `JobDiscovered`, `JobScored`, `JobExpired`, `JobMatched`
- `application_events`: `ApplicationSubmitted`, `ApplicationRejected`, `ApplicationInterview`, `ApplicationOffer`
- `resume_events`: `ResumeGenerated`, `EvidenceAdded`
- `company_events`: `CompanyUpdated`, `CompanyHiringSpike`, `CompanyLayoff`
- `market_events`: `SkillTrendDetected`, `MarketSignalDetected`, `SalaryTrendUpdated`
- `learning_events`: `SkillLearned`, `RoadmapGenerated`, `ROICalculated`
- `system_events`: `WeeklyReportGenerated`, `ModelCalibrated`, `FeatureToggled`

**`scripts/strategy/apply_strategy.py`** — entegrasyon (backward compat)
- Her `repo.save_score()` sonrası `JobScored` event'i publish ediliyor
- DB transaction'ı dışında — hata event bus'ı etkilemez, bus hatası DB'yi etkilemez

**`scripts/test_event_bus.py`** — 8 test (hepsi geçti)

**Phase 2 yol haritası:**
- Redis Streams'e geçmek = sadece `event_bus.py` içini değiştir, tüm subscriber'lar aynı kalır

---

## [Refactor] — 2026-07-14 — Plugin + Config-Driven Architecture ✅

### Değişiklikler

**Sorun:** `hiring_agent_adapter.py` ve `evidence_builder.py` içinde hardcoded path'ler, CSV column isimleri ve confidence katsayıları vardı.

**`config/plugins.yaml`** (yeni — tek kaynak)
- `install_dir`, `csv_filename`, `cache_dir`, `score_script` — tüm path'ler buradan
- `csv_columns.scores` / `csv_columns.metadata` — CSV schema buradan
- `confidence_formula` — `base_divisor`, `commit_bonus_max`, `star_bonus_max`, `production_weight` buradan
- `enrichment_keys` — hangi alanların `career_scores.explanation`'a yazılacağı buradan

**`plugins/plugin_interface.py`** (yeni)
- `ResumeParserPlugin` ABC — `parse()`, `get_metadata()`, `get_enrichment_payload()`
- `ResumeData` dataclass — parser çıktısı için tip güvenli struct

**`plugins/resume_parsers/hiring_agent/client.py`** (yeni)
- `HiringAgentPlugin(ResumeParserPlugin)` — tüm değerleri `plugins.yaml`'dan okur, sıfır hardcode

**`plugins/plugin_loader.py`** (yeni)
- `load_parser_plugin(name)` — factory pattern; yeni parser eklemek = 1 satır + klasör

**`packages/config.py`** (yeni)
- `load_plugin_config()` — `config/plugins.yaml` için `lru_cache`'li loader

**`services/resume_intelligence/application/evidence_builder.py`** (refactor)
- Artık `ResumeParserPlugin` interface'ini kabul ediyor — hiring-agent'a bağımlı değil
- Confidence katsayıları config'den okunuyor

**`services/resume_intelligence/hiring_agent_adapter.py`** (refactor)
- `HiringAgentPlugin`'i kullanıyor; `_build_enrichment_payload()` hardcoded key listesi kaldırıldı

**`scripts/test_plugin_refactor.py`** (yeni)
- 8 adımlı structural test — config yükleme, plugin instantiation, formula doğrulama

---

## [Phase 2J] — 2026-07-14 — Application Engine CLI ✅

### Değişiklikler

**`services/application_engine/__init__.py`** (yeni)

**`services/application_engine/cli.py`** (yeni — typer tabanlı CLI)
- `add` — URL, title, company, status, notes ile iş ekle (duplicate → warn, skip)
- `update` — status değiştir; `applied` status'a geçince `applied_at` otomatik set edilir; notes append edilir
- `list` — tüm işleri tablo olarak göster; `--status` ile filtrele
- `summary` — pipeline count tablosu (to_apply/applied/phone_screen/...)
- `stale` — N gündür güncellenmemiş aktif başvuruları listele (ghosted tespiti için)
- `migrate-from-markdown` — `docs/tracking/JOB_APPLICATIONS.md`'daki gerçek URL satırlarını DB'ye import et; placeholder `[Apply](link)` satırlarını atlar
- State machine: `to_apply → applied → phone_screen → technical → onsite → offer / rejected / ghosted / withdrawn`
- Windows CP1252 uyumlu çıktı (emoji/unicode yok)

**`packages/db/repositories/application_repo.py`** (güncellendi)
- `get_stale(statuses, before)` eklendi — `stale` komutu için

---

## [Phase 2B] — 2026-07-14 — CV Scoring Servisi ✅

### Değişiklikler

**`services/hiring-agent/`** (yeni, ana repo'ya entegre edildi)
- Ayrı git submodule değil — `.git` kaldırıldı, direkt repo içinde yaşıyor
- PDF → PyMuPDF → JSONResume → GitHub enrichment → LLM evaluation pipeline
- Scoring: Open Source (35) + Self Projects (30) + Production (25) + Technical (10) + bonus/deductions
- OpenRouter desteği: `openai/gpt-4o-mini` default, Ollama yok (VPS'te Ollama kurulu değil)
- **`prompt.py`:** `load_dotenv()` → `load_dotenv(Path(__file__).parent / ".env")` — token artık herhangi bir `cwd`'dan çalışınca doğru yükleniyor
- **`github.py`:** GitHub token zaten set edilmişken "Set GITHUB_TOKEN" tip mesajı gizlendi

**`services/resume-intelligence/hiring_agent_adapter.py`** (yeni)
- `score_resume(pdf_path)` — `score.py`'yi subprocess olarak çalıştırır, `resume_evaluations.csv`'nin son satırını okur, scores dict döner
- `enrich_career_scores(session, scores)` — hiring-agent sonuçlarını `career_scores.explanation` JSONB'ye `"resume_score"` key'i altında yazar; zaten enriched satırları atlar
- `HiringAgentAdapter` class API: `HiringAgentAdapter(pdf_path).run()`

### CV Değerlendirme Sonuçları — Abdullokh Abdukodirov

```
Toplam Puan: 55/100

Open Source:        0/35  (kendi projeler, başkasına katkı yok)
Self Projects:     25/30  (Sentropy Engine, IMMUNO-TCR, YADIGAR — karmaşık, gerçek etki)
Production:        20/25  (Full Stack + Computer Vision rolleri, ölçülebilir başarılar)
Technical Skills:  10/10  (Python, Rust, Go, ML/AI framework'leri)

Bonus: 0   Deduction: 0
```

**Güçlü Yönler:** Production experience, ML/AI breadth, karmaşık self-projects  
**İyileştirme:** Open source katkılar (0/35 en büyük fırsat), portfolio site, collaborative projeler

### GitHub Token Fix
- Önceki durum: `GITHUB_TOKEN` `.env`'de comment'li (`# GITHUB_TOKEN=`) → 60 req/hr (unauthenticated)
- Şimdiki durum: Token set + `load_dotenv()` path fix → **4991/5000 req/hr** ✅
- Token scope: sadece `public_repo` (read-only public repos — yeterli)

---

## [Phase 2A] — 2026-07-14 — Intelligence Paketi Migrasyonu ✅

### Değişiklikler

**`packages/intelligence/`** (yeni)
- `semantic_matcher.py`, `opportunity_scorer.py`, `gap_analyzer.py` — canonical konumları
- `__init__.py` — `SemanticMatcher`, `OpportunityScorer`, `CareerDecisionEngine`, `GapAnalyzer` export'ları

**`career_os/intelligence/__init__.py`** — backward-compat shim'e dönüştürüldü
```python
from packages.intelligence import SemanticMatcher, OpportunityScorer, ...
```

**`scripts/strategy/apply_strategy.py`** — import `career_os.intelligence` → `packages.intelligence`

---

## [Phase 1C] — 2026-07-14 — Scan History Tracking ✅

### Değişiklikler

**`packages/db/repositories/scan_history_repo.py`**
- `get_all_known_urls()` eklendi — tek sorguda tüm bilinen URL'leri set olarak döner (O(1) per-job lookup)

**`scripts/scan/run_full_scan.py`**
- `scan_timestamp = datetime.utcnow()` — tüm scan için tek timestamp
- `load_jobs_from_applypilot()` — ApplyPilot DB'den scored job'ları çeker
- `track_scan_history(jobs, scanned_at)` — bulk set-diff ile new/known ayırt eder, SAVEPOINT per job
- Step 4.5 olarak pipeline'a eklendi; Step 7'de yeni job'lar listelenir

**`scripts/test_scan_history.py`** (yeni) — verification script

---

## [Phase 1B] — 2026-07-14 — Career Scores → PostgreSQL ✅

## [Phase 1B] — 2026-07-14 — Career Scores → PostgreSQL ✅

### Değişiklikler

**`scripts/strategy/apply_strategy.py`**
- `packages.db` import'u eklendi
- Yeni adım `[4.5/5]`: `rank_opportunities()` sonrası tüm job'lar için `career_scores` tablosuna insert
- `session.begin_nested()` (SAVEPOINT) per job — bir hata diğer kayıtları bozmaz
- `float()` cast: `np.float64` → Python float (psycopg type safety)
- `str()[:100]` guard: recommendation overflow'u önler
- `.txt` çıktıları korundu — backward compatible

**`packages/db/connection.py`**
- `_load_dotenv()` eklendi — modül import edildiğinde `.env` otomatik yüklenir, her session'da `$env:DATABASE_URL` set etmeye gerek kalmaz

**`packages/db/models/career_score.py`**
- `recommendation: VARCHAR(20) → VARCHAR(100)`
  `OpportunityScorer` `'CONSIDER - Review details'` (23 karakter) döndürüyor, 20'ye sığmıyordu

**Migration: `bc16185b1de3`** — widen_recommendation_to_varchar100

**`scripts/test_db_integration.py`** (yeni)
- Toplam kayıt, son scan zamanı, recommendation dağılımı
- Top 10 APPLY fırsatı (fallback: en yüksek skorlular)
- JSONB unnest SQL: en sık eksik skill'ler
- Örnek kayıt tam detayı

### Doğrulama Sonuçları (2026-07-13 19:06 UTC)

```
Toplam kayıt:     100 / 100 job  (saved_count=100, failed=0)
Recommendation:   CONSIDER - Review details: 66
                  SKIP - Better opportunities: 20
                  CONSIDER - Build skills first: 14
Avg career score: 53.9/100
Avg acceptance:   21.2%
```

**JSONB aggregation (en sık eksik skill'ler):**
```
ai              88 ilanda eksik   ← "ai" keyword extraction sorunu (bkz. not)
javascript      50 ilanda eksik
c++             47 ilanda eksik
docker          19 ilanda eksik
aws             19 ilanda eksik
kubernetes      15 ilanda eksik
```

**Not:** `ai` 88 ilanda eksik göründü ama kullanıcının `Machine Learning`, `LLM`, `NLP` skill'leri var. "ai" bare keyword olarak match edilmiyor — bu `applypilot_loader.py`'deki skill normalization sorunu, Phase 1B değil. `company = "Unknown"` çoğu iş için aynı sebep — company extraction v0 sorunu.

---

## [Phase 1A] — 2026-07-13 — PostgreSQL Database Layer ✅

### infrastructure/docker/
- `docker-compose.yml` — PostgreSQL 16-alpine + Adminer (port 8080), healthcheck, named volume
- `init.sql` — `uuid-ossp`, `pg_trgm`, `btree_gin` extensions; `vector` Phase 2'ye ertelendi

### packages/db/models/
- `base.py` — `DeclarativeBase` + `TimestampMixin` (created_at / updated_at)
- `career_score.py` — (url, scanned_at) composite PK zaman serisi; JSONB `skill_gaps` + `explanation`; GIN index + 4 btree index
- `application.py` — pipeline state machine (`to_apply → applied → phone_screen → offer / rejected`); JSONB `interview_rounds`
- `email.py` — cold email + follow-up; `sent_at / opened_at / replied_at` tracking; FK→applications CASCADE
- `scan_history.py` — job bazında scan kaydı; `discovered_in_this_scan` flag; 3 index

### packages/db/
- `connection.py` — singleton `QueuePool` (size=10, overflow=20), `session_scope` context manager, `DB_ECHO` toggle
- `repositories/base.py` — `Generic[T]` CRUD: get / get_all / create / update / delete
- `repositories/career_score_repo.py` — `save_score`, `get_latest`, `get_top_opportunities` (window function), `get_trends`
- `repositories/application_repo.py` — `upsert`, `mark_applied`, `advance_status`, `get_pipeline_summary`
- `repositories/scan_history_repo.py` — `record_scan`, `get_first_seen`, `get_new_this_scan`
- `alembic.ini` — `DATABASE_URL` env override; file template with date prefix
- `migrations/env.py` — online + offline migration modes; auto-imports `Base.metadata`

### Migration: `49c3e6a25ee5` — initial_schema
- Alembic autogenerate ile oluşturuldu, canlı PostgreSQL 16'ya uygulandı
- 4 tablo, 8 index, 1 FK oluştu — `alembic upgrade head` clean çalıştı

### Doğrulama
```
docker-compose up -d        → career-os-postgres: Healthy ✅
alembic revision --autogenerate → 4 tablo, 8 index detected ✅
alembic upgrade head        → clean ✅
```

---

## [Phase 0] — 2026-07-13 — Hazırlık Tamamlandı

### 0.1 — Git Tag `v0-final`
- Tüm planning doc'ları commit edildi (CODEBASE_OVERVIEW, DATABASE_AUDIT, VISION, ARCHITECTURE, MIGRATION_REPORT, tam CHANGELOG)
- `git tag v0-final` — v0 kodu donduruldu

### 0.2 — Full Backup (`backups/v0-final/`)
- `~/.applypilot/applypilot.db` → `backups/v0-final/applypilot.db`
- `reports/` → `backups/v0-final/reports/`
- `docs/tracking/JOB_APPLICATIONS.md` → `backups/v0-final/JOB_APPLICATIONS.md`
- `backups/` .gitignore'da — git'e gitmez

### 0.3 — API Key Rotation
- `config.yaml`'daki plaintext API key → `.env` dosyasına taşındı
- `config.yaml` artık `${OPENROUTER_API_KEY}` placeholder kullanıyor
- `.env` .gitignore'da (ve zaten başından beri öyleydi — key hiç git'e girmedi)
- `career_os/config_loader.py` oluşturuldu: `.env` yükler, `${VAR}` substitution yapar, dış bağımlılık yok
- `config.yaml.example` güncellendi
- `.gitignore`'a eklendi: `career_os_output/`, `cold_emails/`, `learning_plan/`, `job_requirements_analysis/`, `.vscode/`, `.idea/`

---

## [Architecture Planning] — 2026-07-13 — Architecture Planning Session

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
