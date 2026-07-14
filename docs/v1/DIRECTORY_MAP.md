# CareerOS — Güncel Dizin Haritası

> Oluşturulma: 2026-07-14  
> Mimari: `core/` + `apps/` + `services/` + `plugins/` + `infra/`  
> Toplam aktif Python: ~7,800 satır (hiring-agent dahil ~12,100)

---

## ROOT YAPISI

```
applypilot-jobs/
├── apps/                   ← Deploy yüzeyleri (API + CLI)
├── core/                   ← Paylaşımlı kütüphane (eski: packages/ + events/ + prompts/)
├── services/               ← İş mantığı servisleri
├── plugins/                ← Extensibility / entegrasyonlar
├── infra/                  ← Altyapı (eski: infrastructure/ + config/ + knowledge/)
├── tests/                  ← Test suite
├── scripts/                ← Operasyonel utility scriptler
├── docs/                   ← Dökümantasyon
├── career_os/              ← Legacy (core/ ve data/ — refactor bekliyor)
├── _archive/               ← Arşivlenen eski kod
├── career-os               ← CLI launcher script
├── config.yaml             ← Kullanıcı profil config (gitignored)
├── config.yaml.example     ← Onboarding şablonu
├── requirements.txt        ← Python bağımlılıkları
└── .gitignore
```

---

## FAZ RENKLERİ

| Sembol | Faz |
|--------|-----|
| `[F1]` | Phase 1 — Foundation (DB, API, CLI, Events) |
| `[F2]` | Phase 2 — Intelligence Core (AI, Memory, Resume) |
| `[F3]` | Phase 3 — Company & Market Intelligence |
| `[EX]` | Faz Dışı Extra (Multi-user, Hallucination Fix, vb.) |
| `[CF]` | Config / Altyapı |

---

## apps/ — Deploy Yüzeyleri (Phase 1)

```
apps/                                              [F1]
├── api/
│   └── app/
│       ├── main.py                    44 satır   [F1]  FastAPI app, CORS, router mount
│       ├── dependencies.py            16 satır   [F1]  get_db_session(), get_user_id()
│       ├── routers/
│       │   ├── jobs.py                84 satır   [F1]  GET/POST /api/jobs
│       │   ├── companies.py           58 satır   [F1]  GET /api/companies
│       │   ├── applications.py        75 satır   [F1]  CRUD /api/applications
│       │   ├── evidence.py            76 satır   [F1]  GET /api/evidence
│       │   ├── resume.py              36 satır   [F1]  POST /api/resume/generate
│       │   ├── market.py              45 satır   [F1]  GET /api/market/signals
│       │   └── settings.py           107 satır   [F1]  GET/PUT /api/settings/weights
│       └── schemas/
│           ├── job.py                 27 satır   [F1]  JobResponse, JobWithScore
│           ├── company.py             29 satır   [F1]  CompanyResponse
│           ├── application.py         34 satır   [F1]  ApplicationCreate, ApplicationResponse
│           ├── market.py              36 satır   [F1]  MarketSignalResponse
│           └── resume.py              20 satır   [F1]  ResumeGenerateRequest
└── cli/
    └── main.py                       182 satır   [F1]  Unified Typer CLI (scan, strategy, status)
```

**apps/ toplam:** ~869 satır | 21 REST endpoint | 4 CLI komutu

---

## core/ — Paylaşımlı Kütüphane

### core/db/ — PostgreSQL Katmanı (Phase 1 + Extra)

```
core/db/
├── connection.py                     123 satır   [F1]  SQLAlchemy engine, session_scope()
├── models/
│   ├── base.py                        25 satır   [F1]  DeclarativeBase
│   ├── career_score.py                51 satır   [F1]  fit_score, skill_gaps JSONB
│   ├── scan_history.py                41 satır   [F1]  ApplyPilot scan kayıtları
│   ├── job.py                         61 satır   [F1]  jobs tablosu (Phase 1 ek)
│   ├── application.py                 49 satır   [F1]  ApplicationStatus enum, pipeline
│   ├── user_settings.py               64 satır   [EX] scoring weights, profile JSONB
│   ├── user_custom_skills.py          24 satır   [EX] per-user skill ekleme
│   ├── evidence.py                    71 satır   [F2]  skill confidence + 9 GitHub metric col
│   ├── company.py                     45 satır   [F3]  tech_stack, hiring_signal JSONB
│   ├── company_memory.py              36 satır   [F3]  interview facts per company
│   ├── market_signal.py               49 satır   [F3]  signal_type, skills_affected, magnitude
│   ├── timeline.py                    53 satır   [F3]  snapshots + field-level diffs
│   ├── country.py                     44 satır   [F3]  visa_details, tech_hubs JSONB
│   ├── visa.py                        42 satır   [F3]  eligibility, application JSONB
│   ├── salary_range.py                45 satır   [F3]  role_family, level, currency
│   └── email.py                       48 satır   [EX] cold email kayıtları
├── repositories/
│   ├── base.py                        46 satır   [F1]  BaseRepository ABC
│   ├── career_score_repo.py          111 satır   [F1]  save(), get_top_opportunities()
│   ├── scan_history_repo.py           70 satır   [F1]  upsert(), get_recent()
│   ├── job_repo.py                    94 satır   [F1]  upsert(), filter, advance_status()
│   ├── application_repo.py            90 satır   [F1]  CRUD, advance_status()
│   ├── user_settings_repo.py         143 satır   [EX] get_settings(), upsert(), skill_summary()
│   ├── evidence_repo.py               87 satır   [F2]  add(), get_all_for_user(), update_metrics()
│   ├── company_repo.py               135 satır   [F3]  get(), upsert(), update_tech_stack()
│   ├── market_signal_repo.py         182 satır   [F3]  save(), get_skill_trend(), get_summary()
│   ├── country_repo.py                58 satır   [F3]  get_by_iso(), list_all()
│   ├── visa_repo.py                   37 satır   [F3]  get_by_type(), list_for_country()
│   └── salary_repo.py                 73 satır   [F3]  get_salary(), upsert_from_yaml()
└── migrations/versions/
    ├── 20260713_..._initial_schema.py        101 satır  [F1]  career_scores, scan_history
    ├── 20260714_..._add_jobs_table.py         57 satır  [F1]  jobs tablosu
    ├── 20260714_..._add_evidence_table.py     45 satır  [F2]  evidence (5 col)
    ├── 20260714_..._add_companies_*.py       106 satır  [F3]  companies + company_memory
    ├── 20260714_..._add_market_signals.py     58 satır  [F3]  market_signals
    ├── 20260714_..._add_timeline_tables.py    57 satır  [F3]  timeline_snapshots + changes
    ├── 20260714_..._add_knowledge_tables.py  111 satır  [F3]  countries, visas, salary_ranges
    ├── 20260714_..._add_user_settings.py      76 satır  [EX] user_settings tablosu
    ├── 20260714_..._add_user_id_multiuser.py  58 satır  [EX] user_id col (5 tabloya)
    ├── 20260714_..._add_github_metrics_*.py   40 satır  [EX] 9 col evidence'a (hallucination fix)
    ├── 20260714_..._widen_recommendation.py   32 satır  [EX] VARCHAR(100) fix
    ├── 20260714_..._drop_visa_country_fk.py   26 satır  [EX] FK düzeltme
    ├── 20260714_..._widen_visa_duration.py    40 satır  [EX] TEXT fix
    └── env.py                                 56 satır  [CF] Alembic env
```

**core/db/ toplam:** ~2,335 satır | 16 model | 12 repository | 14 migration

---

### core/domain/ — Pure Python Domain Entities

```
core/domain/
├── __init__.py                        38 satır   [F1]  tüm entity re-export
├── identity/
│   ├── profile.py                     85 satır   [F1]  UserProfile, UserPreferences, Experience
│   └── skill.py                      108 satır   [F1]  Skill, SkillLevel enum, SkillCategory
├── job/
│   └── job.py                         51 satır   [F1]  Job dataclass (required_skills, remote)
├── intelligence/
│   ├── match.py                       32 satır   [F1]  MatchResult dataclass
│   └── scoring.py                     29 satır   [F1]  OpportunityScore, Recommendation enum
├── application/
│   └── application.py                 50 satır   [EX] Application, ApplicationStatus enum
├── company/
│   └── company.py                     44 satır   [EX] Company, TechHub dataclass
├── resume/
│   ├── resume.py                      36 satır   [EX] Resume, ResumeSection
│   └── evidence.py                    30 satır   [EX] Evidence dataclass
├── market/
│   └── market_signal.py               28 satır   [EX] MarketSignal dataclass
├── learning/
│   ├── skill_gap.py                   62 satır   [EX] SkillGap, LearningTask, LearningRoadmap
│   └── roi.py                         32 satır   [EX] SkillROI dataclass
└── analytics/
    ├── funnel.py                      36 satır   [EX] ApplicationFunnel, FunnelStage
    └── metrics.py                     37 satır   [EX] AnalyticsMetrics
```

**core/domain/ toplam:** ~758 satır | 9 subdomain | 15 dataclass

---

### core/events/ — Event Bus (Phase 1)

```
core/events/
├── event_bus.py                      135 satır   [F1]  EventBus singleton, pub/sub
├── event_types.py                     26 satır   [F1]  Event base dataclass
├── job_events.py                      74 satır   [F1]  JobDiscovered, JobScored, JobUpdated
├── application_events.py              60 satır   [F1]  ApplicationSubmitted, StatusChanged
├── resume_events.py                   34 satır   [F1]  ResumeGenerated
├── company_events.py                  37 satır   [F3]  CompanyEnriched, MemoryRecorded
├── market_events.py                   43 satır   [F3]  SignalDetected, TrendUpdated
├── learning_events.py                 39 satır   [EX] SkillGapIdentified, RoadmapCreated
└── system_events.py                   40 satır   [EX] SystemHealthCheck, ErrorOccurred
```

**core/events/ toplam:** ~488 satır | 26 event tipi

---

### core/intelligence/ — Zeka Algoritmaları (Phase 2)

```
core/intelligence/
├── semantic_matcher.py               421 satır   [F2]  SentenceTransformer, cosine similarity
├── opportunity_scorer.py             564 satır   [F2]  OpportunityScorer, ağırlıklı puanlama
└── gap_analyzer.py                   419 satır   [F2]  GapAnalyzer, skill eksik analizi
```

**core/intelligence/ toplam:** ~1,404 satır | 3 algoritma sınıfı

---

### core/memory/ — Memory Layer (Phase 2)

```
core/memory/
├── base.py                            79 satır   [F2]  BaseMemory ABC
├── candidate_memory.py               126 satır   [F2]  başvuru sonucu öğrenme
├── company_memory.py                 103 satır   [F2]  şirket interview faktları
├── conversation_memory.py             69 satır   [F2]  konuşma geçmişi
├── learning_memory.py                 72 satır   [F2]  skill öğrenme takibi
└── market_memory.py                   82 satır   [F2]  market sinyal geçmişi
```

**core/memory/ toplam:** ~531 satır | 5 memory tipi

---

### core/prompts/ — LLM Jinja2 Şablonları (Phase 2)

```
core/prompts/
├── template_loader.py                 72 satır   [F2]  Jinja2 singleton, render(), list()
├── job/
│   └── extract_priorities.jinja      ~40 satır   [F2]  iş ilanından öncelik çıkarma
└── resume/
    ├── tailor_for_target.jinja       ~60 satır   [F2]  hedef şirkete CV özelleştirme
    ├── select_projects.jinja         ~35 satır   [F2]  en iyi 4 projeyi seçme
    └── generate_summary.jinja        ~30 satır   [F2]  2 satır özet üretme
```

**core/prompts/ toplam:** ~237 satır | 4 LLM prompt şablonu

---

### core/knowledge/ — YAML Loaderlar (Phase 1 + Phase 3)

```
core/knowledge/
├── skill_loader.py                   100 satır   [F2]  SkillLoader singleton, alias/topic map
└── company_loader.py                  45 satır   [F3]  CompanyLoader, YAML → dict
```

### core/timeline/ — Timeline Katmanı (Phase 3)

```
core/timeline/
└── timeline.py                       295 satır   [F3]  track_snapshot(), get_history(), auto-diff
```

### core/config.py — Plugin Config Loader (Config)

```
core/config.py                         19 satır   [CF]  load_plugin_config(), lru_cache
```

---

## services/ — İş Mantığı Servisleri

### Identity Service (Phase 1)

```
services/identity_service/
└── application/
    ├── profile_service.py             97 satır   [F1]  get_profile(), save_profile()
    └── preferences_service.py         64 satır   [F1]  get_weights(), save_weights()
```

### Job Intelligence Service (Phase 1)

```
services/job_intelligence/
└── application/
    ├── scoring_service.py            107 satır   [F1]  score_jobs(), run_pipeline(), save_scores()
    └── matching_service.py            41 satır   [F1]  match_job() → lazy SemanticMatcher
```

### Application Engine (Phase 2)

```
services/application_engine/
└── cli.py                            336 satır   [F2]  track add/list/status, apply, stats
```

### Resume Intelligence (Phase 2)

```
services/resume_intelligence/
├── hiring_agent_adapter.py            99 satır   [F2]  PDF → HiringAgent → CSV bridge
├── cli.py                             60 satır   [F2]  resume generate, evidence show
└── application/
    ├── evidence_builder.py           165 satır   [F2]  CSV → Evidence, confidence scoring
    ├── llm_client.py                 110 satır   [F2]  OpenRouter HTTP client
    └── resume_generator.py           357 satır   [F2]  5-step LLM pipeline → Markdown
```

### Company Intelligence (Phase 3)

```
services/company_intelligence/
├── cli.py                             97 satır   [F3]  company show, enrich, memory
└── application/
    ├── company_enricher.py            75 satır   [F3]  job postinglerden tech stack zenginleştirme
    └── company_memory.py              96 satır   [F3]  interview fact kaydetme, tavsiye üretme
```

### Market Intelligence (Phase 3)

```
services/market_intelligence/
└── cli.py                             97 satır   [F3]  signals scan, trend show, summary
```

### Hiring-Agent (Phase 2 — Dış Servis)

```
services/hiring-agent/                             [F2]  Harici CV değerlendirme ajanı
├── score.py                          377 satır         ana değerlendirme motoru
├── transform.py                      938 satır         CV → structured data dönüşümü
├── models.py                         434 satır         Pydantic modeller
├── pdf.py                            323 satır         PyMuPDF ile PDF okuma
├── evaluator.py                       91 satır         LLM değerlendirici
├── github.py                         495 satır         GitHub profil çekme
├── pymupdf_rag.py                   1377 satır         RAG pipeline
├── llm_utils.py                       66 satır         LLM yardımcıları
├── prompt.py                          83 satır         prompt builder
├── config.py                           6 satır         env config
└── prompts/
    └── template_manager.py            90 satır         şablon yönetimi
```

**services/ toplam:** ~5,285 satır (hiring-agent dahil) | 7 servis

---

## plugins/ — Extensibility Katmanı

### Job Sources (Phase 1)

```
plugins/job_sources/applypilot/
├── client.py                         133 satır   [F1]  ApplyPilot SQLite bağlantısı
├── adapter.py                        242 satır   [F1]  normalize(), config-driven extraction
└── plugin.yaml                        ~20 satır  [CF]  skill keywords, salary patterns
```

### Resume Parsers (Phase 2)

```
plugins/resume_parsers/hiring_agent/
└── client.py                         156 satır   [F2]  ResumeParserPlugin impl, CSV bridge
```

### GitHub Enrichment (Phase 3 + Extra)

```
plugins/enrichment/github/
├── client.py                          35 satır   [F3]  PyGithub wrapper
├── repo_analyzer.py                   88 satır   [F3]  LOC, has_tests, has_docs analizi
└── evidence_enricher.py              117 satır   [EX] evidence → GitHub → DB güncelleme
```

### Market Signals (Phase 3)

```
plugins/market_signals/hackernews/
├── client.py                          67 satır   [F3]  HN API client
├── who_is_hiring_parser.py            72 satır   [F3]  "Who is Hiring?" thread parser
└── signal_extractor.py               122 satır   [F3]  272 posting → market signal çıkarma

plugins/market_signals/techcrunch/
├── rss_client.py                      40 satır   [F3]  feedparser RSS okuyucu
└── signal_extractor.py               105 satır   [F3]  funding/layoff tespiti
```

### Plugin Infrastructure (Phase 1)

```
plugins/plugin_interface.py           113 satır   [F1]  ABC: JobSourcePlugin, ResumeParserPlugin
plugins/plugin_loader.py               95 satır   [F1]  load_job_source_plugin(), config-driven
```

**plugins/ toplam:** ~1,285 satır | 5 aktif plugin

---

## infra/ — Altyapı

```
infra/
├── docker/
│   ├── docker-compose.yml             [CF]  PostgreSQL 16 container
│   └── init.sql                       [CF]  DB init
├── config/
│   └── plugins.yaml                   [CF]  plugin paths, confidence weights, skill keywords
└── seeds/v1/
    ├── skills/
    │   └── skill_graph.yaml      ~400 satır  [F2]  canonical skills, aliases, topic map, edges
    ├── countries/
    │   ├── canada.yaml                [F3]  tech_hubs, visa, tax, salary_ranges
    │   ├── germany.yaml               [F3]
    │   ├── netherlands.yaml           [F3]
    │   ├── uae.yaml                   [F3]
    │   └── usa.yaml                   [F3]
    ├── visa/
    │   ├── eu_blue_card.yaml          [F3]
    │   ├── uk_skilled_worker.yaml     [F3]
    │   └── us_h1b.yaml               [F3]
    ├── salaries/
    │   ├── backend_eu.yaml            [F3]
    │   ├── frontend_global.yaml       [F3]
    │   └── ml_us.yaml                [F3]
    └── companies/
        ├── big_tech.yaml              [F3]  Google, Meta, Apple, vb.
        ├── unicorns.yaml              [F3]  Stripe, Notion, vb.
        └── company_memory_schema.yaml [F3]  şema dokümantasyonu
```

---

## scripts/ — Operasyonel Araçlar

```
scripts/
├── seed_knowledge_from_yaml.py       213 satır   [F3]  YAML → DB (countries/visa/salary)
├── sync_jobs_from_applypilot.py      112 satır   [EX] ApplyPilot SQLite → PostgreSQL sync
└── enrich_github_evidence.py          69 satır   [EX] evidence kayıtlarını GitHub ile zenginleştir
```

---

## tests/ — Test Suite

```
tests/
├── test_db_integration.py            104 satır   [F1]  career_score + scan_history CRUD
├── test_event_bus.py                 180 satır   [F1]  pub/sub, wildcard, multi-handler
├── test_applypilot_plugin.py         140 satır   [F1]  plugin normalize(), config parse
├── test_plugin_refactor.py            94 satır   [F1]  plugin_loader, config/plugins.yaml
├── test_scan_history.py              128 satır   [F1]  scan_history upsert, dedup
├── test_user_settings.py             208 satır   [EX] settings CRUD, weights, multi-user
├── test_memory_layer.py              185 satır   [F2]  5 memory tipi
├── test_prompts.py                   200 satır   [F2]  template render, 4 şablon
├── test_resume_generator.py          141 satır   [F2]  LLM pipeline mock
├── test_github_enrichment.py         162 satır   [F3]  repo_analyzer, evidence enrichment
├── test_company_intelligence.py      203 satır   [F3]  enricher, company memory
├── test_market_intelligence.py       179 satır   [F3]  HN + TechCrunch signal extraction
├── test_knowledge_db.py              189 satır   [F3]  country/visa/salary CRUD
└── test_timeline_layer.py            176 satır   [F3]  snapshot, diff, history query
```

**tests/ toplam:** ~2,289 satır | 14 test dosyası

---

## career_os/ — Legacy (Geçici)

```
career_os/                             [LEGACY — refactor bekliyor]
├── config_loader.py                   ~60 satır  config.yaml okuyucu
├── core/
│   └── skill_graph.py                ~200 satır  NetworkX SkillGraph (core/intelligence import ediyor)
└── data/
    └── applypilot_loader.py          ~300 satır  config.yaml → UserProfile builder
```

> **Not:** `career_os/core/skill_graph.py` → `core/intelligence/semantic_matcher.py` tarafından import ediliyor.  
> `career_os/data/applypilot_loader.py` → `career_os/config_loader.py` tarafından kullanılıyor.  
> `career_os/` tamamen silinebilmesi için `core/intelligence/` refactor edilmeli.

---

## ÖZET İSTATİSTİKLER

### Faz Bazında Kod Satırı

| Faz | Dosya Sayısı | Tahmini Satır | Kapsam |
|-----|-------------|---------------|--------|
| **Phase 1** | 38 | ~2,600 | DB, API, CLI, Events, Domain (identity/job), Plugins |
| **Phase 2** | 22 | ~2,900 | Intelligence, Memory, Resume, Evidence, Prompts |
| **Phase 3** | 22 | ~1,900 | Company, Market, Timeline, GitHub, Knowledge |
| **Faz Dışı** | 18 | ~900 | Multi-user, Domain extras, Hallucination fix |
| **Config/Infra** | — | ~700 | YAML seeds, docker, config |
| **Tests** | 14 | ~2,289 | Tüm fazları kapsar |
| **Hiring-Agent** | 11 | ~4,280 | Harici PDF/CV değerlendirme servisi |
| **TOPLAM** | **125+** | **~15,570** | |

### DB Tabloları Faz Bazında

| Faz | Tablolar |
|-----|----------|
| Phase 1 | `career_scores`, `scan_history`, `jobs`, `applications` |
| Phase 2 | `evidence` |
| Phase 3 | `companies`, `company_memory`, `market_signals`, `timeline_snapshots`, `timeline_changes`, `countries`, `visas`, `salary_ranges` |
| Faz Dışı | `user_settings`, `user_custom_skills`, `emails` |

**Toplam: 16 tablo**

### REST Endpoint Dağılımı (21 endpoint)

| Router | Endpoint Sayısı | Faz |
|--------|----------------|-----|
| `jobs.py` | 5 | F1 |
| `companies.py` | 4 | F1 |
| `applications.py` | 4 | F1 |
| `evidence.py` | 3 | F1 |
| `settings.py` | 4 | F1 |
| `resume.py` | 1 | F2 |
| `market.py` | 3 | F3 |

### Event Tipi Dağılımı (26 event)

| Modül | Event Sayısı | Faz |
|-------|-------------|-----|
| `job_events.py` | 8 | F1 |
| `application_events.py` | 6 | F1 |
| `resume_events.py` | 4 | F2 |
| `company_events.py` | 4 | F3 |
| `market_events.py` | 4 | F3 |
| `learning_events.py` | 4 | EX |
| `system_events.py` | 4 | EX |

---

## MİMARİ BAĞIMLILIK HARİTASI

```
apps/api     ──────────────────────────► core/db (repositories)
apps/cli     ──────────────────────────► services/* + core/db + plugins/*
             
services/identity_service     ─────────► core/db/repositories/user_settings_repo
services/job_intelligence     ─────────► core/db + core/intelligence (lazy)
services/resume_intelligence  ─────────► core/db + core/prompts + services/hiring-agent
services/company_intelligence ─────────► core/db + core/memory
services/market_intelligence  ─────────► core/db + plugins/market_signals/*
services/application_engine   ─────────► core/db (direct)
             
plugins/job_sources/applypilot ────────► core/db + infra/config/plugins.yaml
plugins/resume_parsers         ────────► services/hiring-agent (bridge)
plugins/enrichment/github      ────────► core/db/repositories/evidence_repo
plugins/market_signals/*       ────────► (standalone, output → services/market_intelligence)
             
core/intelligence  ────────────────────► career_os/core/skill_graph (LEGACY BAĞIMLILIK)
core/knowledge     ────────────────────► infra/seeds/v1/ (YAML files)
core/config        ────────────────────► infra/config/plugins.yaml
```

---

## SONRAKI ADIMLAR (Teknik Borç)

| # | Konu | Etki | Dosya |
|---|------|------|-------|
| 1 | `career_os/` kaldır | `core/intelligence/semantic_matcher.py` refactor | `career_os/core/skill_graph.py` |
| 2 | Country/Visa/Salary endpoint ekle | UI country karşılaştırma | `apps/api/app/routers/` |
| 3 | Timeline endpoint ekle | UI timeline görünümü | `apps/api/app/routers/` |
| 4 | JWT authentication | `X-User-Id` header yerine | `apps/api/app/dependencies.py` |
| 5 | WebSocket | Real-time scan updates | `apps/api/app/main.py` |
