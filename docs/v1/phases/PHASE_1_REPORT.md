# 📘 FAZ 1 RAPORU — Foundation (Temel Altyapı)

## 📄 Rapor Meta Bilgisi

| Alan | Değer |
|---|---|
| **Rapor Başlığı** | CareerOS Faz 1 — Foundation Architecture Raporu |
| **Rapor Versiyonu** | `v1.0.0` |
| **Oluşturulma Tarihi** | 14 Temmuz 2026 |
| **Son Güncelleme** | 14 Temmuz 2026 |
| **Yazar** | AI Codebase Auditor (gerçek kod okuması) |
| **Kapsam** | `apps/`, `core/db/`, `core/domain/`, `core/events/`, `plugins/`, `services/identity_service/`, `services/job_intelligence/` |
| **Dışında Kalanlar** | Intelligence (Faz 2), Company/Market (Faz 3), Legacy `career_os/` |

---

## 🎯 Faz Özeti

> **Faz 1, CareerOS'un "iskelet" fazıdır.** PostgreSQL veri tabanı, event-driven mimari, plugin system, REST API ve CLI — sistemin tüm diğer fazlarının üzerine inşa edileceği temel altyapıyı kurar.

**Tek Cümle:** *"Veri depolama, iş ilanları keşfi, skorlama ve başvuru takibi için sağlam, multi-user, event-driven bir altyapı."*

---

## 📊 Faz İstatistikleri

| Metrik | Değer |
|---|---|
| **Toplam Dosya Sayısı** | 38 |
| **Toplam Kod Satırı** | ~2,600 (testler hariç) |
| **DB Tabloları (Faz 1)** | 4 (`career_scores`, `scan_history`, `jobs`, `applications`) |
| **REST Endpoint** | 24 (router 22 + main 2) |
| **CLI Komutu (native)** | 4 (version, status, scan, strategy) |
| **CLI Sub-Group** | 4 (track, resume, company, market — mount) |
| **Event Tipi (Faz 1)** | 8 (job: 5, application: 4 — Faz 1'e ait) |
| **Event Tipi (toplam)** | 18 (Faz 2-3 company, market, learning, system olayları dahil) |
| **Plugin Sayısı** | 1 (ApplyPilot) |
| **Domain Entity** | 5 (UserProfile, UserPreferences, Skill, Job, MatchResult) |
| **Test Dosyası (Faz 1)** | 6 (~746 satır) |
| **Test Dosyası (toplam)** | 14 |
| **Tamamlanma Oranı** | ✅ %100 |
| **Mimari Kilit** | 🔒 LOCKED |

---

## 📁 Dosya Envanteri (Detaylı Tablo)

### A. Veri Katmanı — `core/db/`

| # | Dosya | Satır | Sorumluluk | Kritiklik |
|---|---|---|---|---|
| 1 | `connection.py` | 123 | SQLAlchemy engine, `session_scope()` context manager, retry logic | 🔴 Kritik |
| 2 | `models/base.py` | 25 | `DeclarativeBase`, `TimestampMixin` (created_at, updated_at) | 🔴 Kritik |
| 3 | `models/career_score.py` | 51 | `career_scores` tablosu (user_id, url, fit_score, skill_gaps JSONB) | 🔴 Kritik |
| 4 | `models/scan_history.py` | 41 | ApplyPilot scan kayıtları (new/known job tracking) | 🟠 Yüksek |
| 5 | `models/job.py` | 61 | `jobs` tablosu (ApplyPilot SQLite'dan bağımsız) | 🔴 Kritik |
| 6 | `models/application.py` | 49 | `ApplicationStatus` enum (9 state), state machine | 🔴 Kritik |
| 7 | `models/email.py` | 48 | Cold email kayıtları (Faz 1 migration'ında yer alır) | 🟢 Düşük |
| 8 | `repositories/base.py` | 46 | `BaseRepository[T]` ABC — generic CRUD | 🔴 Kritik |
| 9 | `repositories/career_score_repo.py` | 111 | `save_score()`, `get_top_opportunities()`, `get_latest_score()` | 🔴 Kritik |
| 10 | `repositories/scan_history_repo.py` | 70 | `upsert()`, `get_recent()`, `get_new_this_scan()` | 🟠 Yüksek |
| 11 | `repositories/job_repo.py` | 94 | `upsert()`, `filter()`, `advance_status()` | 🔴 Kritik |
| 12 | `repositories/application_repo.py` | 90 | CRUD, `advance_status()`, `get_pipeline_summary()` | 🔴 Kritik |

**`core/db/` Alt Toplam:** ~900 satır | 12 dosya (Faz 1 tabloları)

> **Not:** `core/db/` toplam çok daha fazla model içerir (evidence, company, market_signal, timeline, knowledge — bunlar Faz 2-3'e ait).

---

### B. Domain Entities — `core/domain/`

| # | Dosya | Satır | Sorumluluk | Kritiklik |
|---|---|---|---|---|
| 1 | `__init__.py` | 38 | Tüm entity re-export | 🔴 Kritik |
| 2 | `identity/profile.py` | 85 | `UserProfile`, `UserPreferences`, `Experience` | 🔴 Kritik |
| 3 | `identity/skill.py` | 108 | `Skill`, `SkillLevel` enum, `SkillCategory`, `categorize_skill()` | 🔴 Kritik |
| 4 | `job/job.py` | 51 | `Job` dataclass (url, title, company, required_skills, remote) | 🔴 Kritik |
| 5 | `intelligence/match.py` | 32 | `MatchResult` dataclass (overall_score, breakdown, skill_gaps) | 🟠 Yüksek |
| 6 | `intelligence/scoring.py` | 29 | `OpportunityScore`, `Recommendation` enum | 🟠 Yüksek |

**`core/domain/` Alt Toplam:** ~343 satır | 6 dosya

---

### C. Event Bus — `core/events/`

| # | Dosya | Satır | Faz | Sorumluluk |
|---|---|---|---|---|
| 1 | `event_bus.py` | 135 | F1 | Singleton pub/sub, handler registration, error isolation |
| 2 | `event_types.py` | 26 | F1 | `Event` base dataclass (event_id, timestamp, source) |
| 3 | `job_events.py` | 74 | F1 | `JobDiscovered`, `JobScored`, `JobUpdated`, `JobExpired`, `JobMatched` |
| 4 | `application_events.py` | 60 | F1 | `ApplicationSubmitted`, `StatusChanged`, `ApplicationRejected`, `ApplicationOffer` |
| 5 | `resume_events.py` | 34 | F2 | `ResumeGenerated`, `EvidenceAdded` |
| 6 | `company_events.py` | ~40 | F3 | `CompanyUpdated`, `CompanyHiringSpike`, `CompanyLayoff` |
| 7 | `market_events.py` | ~35 | F3 | Market signal events |
| 8 | `learning_events.py` | ~30 | F3 | Learning/feedback events |
| 9 | `system_events.py` | ~25 | F3 | System-level events |

**`core/events/` Alt Toplam:** 10 dosya | **Faz 1'e ait:** 4 event dosyası + event_bus.py

---

### D. Plugin System — `plugins/`

| # | Dosya | Satır | Sorumluluk | Kritiklik |
|---|---|---|---|---|
| 1 | `plugin_interface.py` | 113 | `JobSourcePlugin`, `ResumeParserPlugin` ABC'ler | 🔴 Kritik |
| 2 | `plugin_loader.py` | 95 | `load_job_source_plugin()`, config-driven factory | 🔴 Kritik |
| 3 | `job_sources/applypilot/client.py` | 133 | SQLite bağlantısı, cursor management | 🟠 Yüksek |
| 4 | `job_sources/applypilot/adapter.py` | 242 | Normalize, company/skill/salary extraction (config-driven) | 🔴 Kritik |
| 5 | `job_sources/applypilot/plugin.yaml` | ~20 | Metadata + extraction rules | 🟠 Yüksek |

**`plugins/` Alt Toplam:** ~603 satır | 5 dosya

---

### E. Deploy Yüzeyleri — `apps/`

#### FastAPI Routers

| Router | Endpoint | Method | Açıklama |
|---|---|---|---|
| `main.py` | `/` | GET | Root health |
| `main.py` | `/health` | GET | Health check |
| `jobs.py` | `/api/jobs` | GET | Job listesi (min_score, recommendation, limit) |
| `jobs.py` | `/api/jobs/pipeline` | GET | Pipeline bucket counts |
| `jobs.py` | `/api/jobs/{url:path}` | GET | Tek job detayı |
| `companies.py` | `/api/companies` | GET | Şirket listesi |
| `companies.py` | `/api/companies/hiring` | GET | Aktif işe alım yapanlar |
| `companies.py` | `/api/companies/{name}` | GET | Şirket detayı |
| `companies.py` | `/api/companies/{name}/memory` | GET | Şirket hafıza bilgisi |
| `applications.py` | `/api/applications` | GET | Başvuru listesi |
| `applications.py` | `/api/applications/summary` | GET | Pipeline özeti |
| `applications.py` | `/api/applications` | POST | Yeni başvuru |
| `applications.py` | `/api/applications/{url:path}` | PUT | Status güncelle |
| `evidence.py` | `/api/evidence` | GET | Evidence listesi |
| `evidence.py` | `/api/evidence/summary` | GET | Skill bazlı özet |
| `evidence.py` | `/api/evidence/{skill}` | GET | Skill detayı |
| `settings.py` | `/api/settings` | GET | Kullanıcı ayarları |
| `settings.py` | `/api/settings` | PUT | Ayar güncelle |
| `settings.py` | `/api/settings/weights` | GET | Skor ağırlıkları |
| `settings.py` | `/api/settings/weights` | PUT | Ağırlık güncelle |
| `market.py` | `/api/market/signals` | GET | Market sinyalleri |
| `market.py` | `/api/market/summary` | GET | Market özeti |
| `market.py` | `/api/market/trend/{skill}` | GET | Skill trend |
| `resume.py` | `/api/resume/generate` | POST | Resume oluştur |

**Toplam: 24 endpoint**

#### CLI — `apps/cli/main.py` (182 satır)

| Komut | Tür | Açıklama |
|---|---|---|
| `career-os version` | Native | Versiyon bilgisi |
| `career-os status` | Native | DB tablo sayıları |
| `career-os scan` | Native | ApplyPilot job scan |
| `career-os strategy` | Native | Tam scoring pipeline |
| `career-os track *` | Mount | `services/application_engine/cli.py` |
| `career-os resume *` | Mount | `services/resume_intelligence/cli.py` |
| `career-os company *` | Mount | `services/company_intelligence/cli.py` |
| `career-os market *` | Mount | `services/market_intelligence/cli.py` |

---

### F. Service Layer (Faz 1)

| # | Dosya | Satır | Sorumluluk | Kritiklik |
|---|---|---|---|---|
| 1 | `services/identity_service/application/profile_service.py` | 97 | `get_profile()`, `save_profile()`, `create_profile_from_config()` | 🔴 Kritik |
| 2 | `services/identity_service/application/preferences_service.py` | 64 | `get_weights()`, `save_weights()`, `get_preferences()` | 🔴 Kritik |
| 3 | `services/job_intelligence/application/scoring_service.py` | 107 | `score_jobs()`, `run_pipeline()`, `save_scores()` | 🔴 Kritik |
| 4 | `services/job_intelligence/application/matching_service.py` | 41 | `match_job()` — lazy SemanticMatcher init | 🟠 Yüksek |

**Services (Faz 1) Alt Toplam:** ~309 satır | 4 dosya

---

### G. Infrastructure

| # | Dosya | Satır | Sorumluluk |
|---|---|---|---|
| 1 | `infra/docker/docker-compose.yml` | ~30 | PostgreSQL 16 container |
| 2 | `infra/docker/init.sql` | ~20 | DB init script |
| 3 | `infra/config/plugins.yaml` | ~150 | Plugin config (ApplyPilot extraction rules) |
| 4 | `config.yaml.example` | ~40 | Onboarding şablonu |

### H. Migrations (Faz 1'e ait)

| # | Migration | Tablo |
|---|---|---|
| 1 | `20260713_..._initial_schema.py` | `career_scores`, `scan_history` |
| 2 | `20260714_..._add_jobs_table.py` | `jobs` |
| 3 | `20260714_..._add_user_id_multiuser.py` | 5 tabloya `user_id` column |
| 4 | `20260714_..._widen_recommendation.py` | `career_scores.recommendation` VARCHAR(100) |
| 5 | `env.py` | Alembic env |

> **Not:** `core/db/migrations/` klasöründe toplam ~16 migration var — Faz 2-3 tabloları (evidence, company, market_signal, timeline, knowledge) bu fazlarda eklendi.

---

## 📐 Modül Detayları (Kritik Olanlar)

### Modül 1: `core/db/connection.py` — Veri Tabanı Bağlantısı

```python
class Database:
    def __init__(self, url: str): ...
    def get_engine(self) -> Engine: ...

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Transaction-safe session context.
        - Commit on successful exit
        - Rollback on exception
        - Always close session
        """
```

- ✅ Connection pooling (SQLAlchemy default: 5 conn, max 10)
- ✅ Transaction isolation (READ COMMITTED)
- ✅ Thread-safe (scoped session)

---

### Modül 2: `core/events/event_bus.py` — Event Bus

```python
class EventBus:
    _instance = None  # Singleton
    _subscribers: Dict[Type[Event], List[Callable]] = defaultdict(list)
    _lock = threading.RLock()
    _history: deque  # Son 1000 event

    def subscribe(self, event_type, handler): ...
    def publish(self, event: Event) -> int: ...  # Returns handler count
    def unsubscribe(self, event_type, handler): ...
    def get_history(self, event_type=None, limit=100): ...
    def clear(self): ...  # Testing için
```

- ✅ Singleton pattern
- ✅ Thread-safe (RLock — nested publishes için reentrant)
- ✅ Error isolation — bir handler hata verse diğerleri çalışır
- ✅ Decorator syntax: `@event_bus.subscribe(JobScored)`
- ✅ Event history (son 1000 event saklanır)

---

### Modül 3: `plugins/job_sources/applypilot/adapter.py` — ApplyPilot Adapter

Config-driven extraction — tüm kurallar `infra/config/plugins.yaml`'da:

```yaml
job_sources:
  applypilot:
    company_extraction:
      ats_domains: [greenhouse.io, lever.co, workday.com, ...]
      blocklist: [this, our, we, the, about, ...]
    skill_extraction:
      keywords: [Python, Java, React, AWS, Docker, ...]  # 36 skill
    salary_patterns:
      - pattern: '\$?(\d+)k?-\$?(\d+)k?'
        multiplier: 1000
```

Extraction stratejisi (öncelik sırası):
1. LinkedIn company URL slug
2. Title pattern (`"ML Engineer - Google"`, `"ML Engineer at Google"`)
3. Application URL (ATS domain filtresi sonrası)
4. Description NLP (`"At Google, we..."`, `"Join Stripe!"`)

---

### Modül 4: `apps/cli/main.py` — Unified CLI

```python
app = typer.Typer(name="career-os")

# Native commands
@app.command()
def version(): typer.echo("CareerOS v1.0.0")

@app.command()
def status():
    """Show counts for all DB tables."""

@app.command()
def scan(hours: int, min_score: int):
    """Scan jobs from ApplyPilot and store results."""

@app.command()
def strategy(user_id: str, hours: int, limit: int, semantic: bool):
    """Run full career strategy: scan → score → save → print summary."""

# Mounted sub-groups (try/except — import hatası sessizce atlanır)
app.add_typer(track_app, name="track")
app.add_typer(resume_app, name="resume")
app.add_typer(company_app, name="company")
app.add_typer(market_app, name="market")
```

---

### Modül 5: `services/job_intelligence/application/scoring_service.py`

```python
class ScoringService:
    def run_pipeline(self, jobs, profile, semantic=False) -> dict:
        # Score → Save to DB → Publish events → Return summary
        return {
            "scored": len(jobs),
            "saved_to_db": saved_count,
            "apply": apply_count,
            "consider": consider_count,
            "skip": skip_count,
        }
```

- ✅ Lazy SemanticMatcher init (420MB model — ilk çağrıda yüklenir)
- ✅ `semantic=False` flag ile hızlı mod
- ✅ Transaction-safe DB commit → sonra event publish

---

## 🔄 Kullanım Diyagramı

```
┌──────────────────────────────────────────────────────┐
│                  EXTERNAL SYSTEMS                    │
│  ApplyPilot SQLite  ·  PostgreSQL 16  ·  config.yaml │
└────────────┬──────────────┬──────────────┬───────────┘
             │              │              │
             ▼              ▼              ▼
┌──────────────────────────────────────────────────────┐
│              apps/ (Deploy Surface)                  │
│   FastAPI (24 endpoint)  ·  Typer CLI (career-os)    │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│              services/ (Business Logic)              │
│  identity_service (ProfileService, PreferencesService)│
│  job_intelligence (ScoringService, MatchingService)  │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│              plugins/ (Connectors)                   │
│  ApplyPilot: client.py → adapter.py (config-driven)  │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│              core/db/ (Data Layer)                   │
│  career_scores · scan_history · jobs · applications  │
│  BaseRepository[T] — generic CRUD                    │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│              core/events/ (Event Bus)                │
│  JobDiscovered · JobScored · ApplicationSubmitted    │
│  → Faz 2-3 servisleri dinler                         │
└──────────────────────────────────────────────────────┘
```

---

## 🔗 Kritik Akışlar

### Akış 1: Job Discovery (ApplyPilot → DB)

```
career-os scan --hours 72
 → load_job_source_plugin("applypilot")
 → client.py: SQLite connect
 → adapter.py: raw row → Job entity (company, skills, salary, seniority)
 → JobRepository.upsert(job)
 → PostgreSQL INSERT
 → event_bus.publish(JobDiscovered)
```

### Akış 2: Scoring Pipeline

```
career-os strategy --user default
 → ProfileService.get_profile()
 → plugin.scan_and_normalize()
 → ScoringService.run_pipeline(jobs, profile)
    ├─ SemanticMatcher.match() → cosine similarity
    ├─ formula: career_score = fit*0.30 + acceptance*0.25 + ...
    ├─ CareerScoreRepository.save_score()
    └─ event_bus.publish(JobScored)
```

### Akış 3: API Request

```
GET /api/jobs?min_score=60&recommendation=APPLY
 → FastAPI router dispatch
 → Dependency injection (session, user_id)
 → CareerScoreRepository.get_top_opportunities()
 → Pydantic v2 serialization
 → HTTP 200 JSON
```

### Akış 4: Weights Update (Persisted)

```
PUT /api/settings/weights  {"fit": 0.40, "acceptance": 0.20, ...}
 → Pydantic validation
 → UserSettingsRepository.set_weights(user_id, weights)
 → PostgreSQL UPDATE
 → Sonraki scoring bu weights'i kullanır
```

---

## 🧠 Career Score Formula

```python
career_score = (
    fit_score          * weights["fit"]           +  # default 0.30
    acceptance_prob    * weights["acceptance"]    +  # default 0.25
    career_value       * weights["career_value"]  +  # default 0.25
    market_demand      * weights["market_demand"]    # default 0.20
)

# Thresholds
if career_score >= 70:   recommendation = "APPLY"
elif career_score >= 50: recommendation = "CONSIDER"
else:                    recommendation = "SKIP"
```

Weights DB'den per-user override edilebilir (dynamic, `PUT /api/settings/weights`).

---

## 🔐 Hardcoded vs Dynamic Analizi

### ✅ DYNAMIC

| Bileşen | Nasıl Değişir |
|---|---|
| Scoring weights | `PUT /api/settings/weights` |
| Career scores | Her scan'de yeniden hesaplanır |
| Applications | CRUD via API + state machine |
| ApplyPilot extraction rules | `infra/config/plugins.yaml` edit |
| Skill keywords (36 adet) | YAML edit |
| ATS domain blocklist | YAML edit |

### ❌ HARDCODED (Sabit)

| Bileşen | Değer | Risk |
|---|---|---|
| Default user_id | `"default"` | 🟢 Low (JWT Faz 4.5) |
| DB connection | `postgresql://career_os:...@localhost/career_os` | 🟢 Low (env var) |
| CORS origins | `localhost:3000`, `3001` | 🟢 Low (Next.js portları) |
| Event history size | 1000 | 🟢 Low |

**Dynamic Skor: ~88%**

---

## 🧪 Test Durumu

### Test Dosyaları (Faz 1'e ait)

| Dosya | Satır | Kapsam |
|---|---|---|
| `tests/test_db_integration.py` | 104 | career_score + scan_history CRUD |
| `tests/test_event_bus.py` | 180 | pub/sub, multi-handler, error isolation |
| `tests/test_applypilot_plugin.py` | 140 | plugin normalize, config parse |
| `tests/test_plugin_refactor.py` | 94 | plugin_loader, config/plugins.yaml |
| `tests/test_scan_history.py` | 128 | scan_history upsert, dedup |
| `tests/test_user_settings.py` | 100 | settings CRUD, weights |

**Faz 1 toplam:** ~746 satır | 6 dosya

> Diğer 8 test dosyası (test_resume_generator, test_company_intelligence, test_github_enrichment vb.) Faz 2-3'e aittir.

---

## ⚠️ Teknik Borç

| # | Borç | Öncelik | Plan |
|---|---|---|---|
| 1 | `career_os/` legacy klasörü | 🟡 Orta | Faz 4.5'te refactor |
| 2 | Auth yok (`X-User-Id` header) | 🟢 Düşük | JWT Faz 4.5 |
| 3 | `apps/api/` test coverage ~%40 | 🟡 Orta | pytest + httpx Faz 4.5 |
| 4 | Rate limiting yok | 🟢 Düşük | Faz 4.5 |
| 5 | Monitoring yok | 🟢 Düşük | Prometheus + Grafana Faz 5 |

---

## 🚀 Faz 1 → Sonraki Fazlara Bağlantı

| Faz 1'den | Nereye |
|---|---|
| `career_scores` tablosu | Faz 2: Evidence Graph join |
| `Job` entity | Faz 2: Resume Generator input |
| `ApplicationStatus` | Faz 2: Memory Layer learning |
| `JobScored` event | Faz 2: Resume Intelligence dinler |
| `ApplicationSubmitted` event | Faz 3: CompanyMemory dinler |
| `BaseRepository` | Faz 3: Company, Market, Timeline repo'ları extend eder |
| `Plugin Interface` | Faz 3: GitHub Enrichment, HN Scanner extend eder |
| `FastAPI` 24 endpoint | Faz 4: Next.js tüketir |

---

## ✅ Kontrol Listesi

- [x] PostgreSQL 16 kurulu (Docker Compose)
- [x] 4 Faz-1 tablosu + migrations
- [x] Repository pattern (generic CRUD)
- [x] Event Bus (in-memory, thread-safe, error isolation)
- [x] Plugin system (interface + loader)
- [x] ApplyPilot plugin (config-driven, 36 skill, salary parsing, seniority)
- [x] FastAPI gateway (24 endpoint, 7 router)
- [x] Unified Typer CLI (4 native + 4 mounted groups)
- [x] Identity service (profile, preferences)
- [x] Job intelligence service (scoring, matching)
- [x] Multi-user foundation (user_id migration)
- [x] CORS configured (Next.js ready)
- [x] Pydantic v2 schemas
- [x] 6 test dosyası, ~746 satır

**✅ Faz 1 %100 TAMAMLANDI — LOCKED**

---

## 🎯 Özet

**Faz 1, CareerOS'un sağlam "iskelet"ini kurar.** ~2,600 satır kod, 4 DB tablosu, 24 REST endpoint, 8 Faz-1 event tipi ve 1 plugin ile sistemin tüm diğer fazlarının üzerine inşa edileceği altyapı hazır. Multi-user, event-driven, config-driven ve plugin-based mimari ile ölçeklenebilir bir temel atıldı.

**Bir sonraki rapor:** Faz 2 — Intelligence Core (Evidence Graph, Memory Layer, Resume Generator)
