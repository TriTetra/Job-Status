# CareerOS — Product Architecture Document v1.0

**Versiyon:** 1.0.0-final (Architecture Lock)  
**Tarih:** 14 Temmuz 2026  
**Durum:** KILITLENDI — Bu doküman nihai referanstır. Yeni domain/servis/klasör eklenmez.

---

## I. Ürün Tanımı

> **CareerOS is an AI-native career operating system that continuously discovers opportunities, builds evidence of your expertise, monitors the global software engineering market, and helps you make better career decisions throughout your professional journey.**

Bu tanım artık "job tracker" değil, **kariyer işletim sistemi** olarak konumlanır.

---

## II. Temel Prensipler (Değişmez)

1. **Center = Developer** — iş ilanı değil, kullanıcı merkezde
2. **Evidence > Claim** — kanıtsız skill, skill değildir
3. **AI Suggests, Human Decides** — otomatik başvuru yok
4. **Explainable Always** — skor açıklaması zorunlu
5. **Local-First** — kullanıcı verisi kendi makinesinde

---

## III. 8 Ana Domain (Değişmez)

```
┌─────────────────────────────────────────────────────────┐
│                    CareerOS Platform                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   1. Identity              Kullanıcının kendisi         │
│   2. Job Intelligence      İş ilanları evreni           │
│   3. Company Intelligence  Şirket hafızası              │
│   4. Resume Intelligence   Kanıt tabanlı CV motoru      │
│   5. Market Intelligence   Piyasa nabzı                 │
│   6. Application Engine    Başvuru yaşam döngüsü        │
│   7. Learning Engine       Skill ROI motoru             │
│   8. Analytics             Geri bildirim & içgörü       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## IV. Event-Driven Architecture

Domain'ler birbirine doğrudan bağlı değil. **Event Bus** üzerinden haberleşir.

### Event Tipleri

```
events/
├── event_bus.py            # Pub/Sub (Redis Streams veya in-memory)
├── event_types.py          # Tüm event tanımları
│
├── job_events.py
│   ├── JobDiscovered(job_id, source, discovered_at)
│   ├── JobScored(job_id, score, explanation)
│   ├── JobExpired(job_id)
│   └── JobMatched(job_id, user_id, match_score)
│
├── company_events.py
│   ├── CompanyUpdated(company_id, changes)
│   ├── CompanyHiringSpike(company_id, job_count)
│   └── CompanyLayoff(company_id, news_url)
│
├── resume_events.py
│   ├── ResumeGenerated(user_id, version, target_job)
│   ├── EvidenceAdded(user_id, skill, project, confidence)
│   └── ResumeABTestCompleted(version_a, version_b, winner)
│
├── application_events.py
│   ├── ApplicationSubmitted(job_id, user_id, resume_version)
│   ├── ApplicationRejected(job_id, user_id, reason)
│   ├── ApplicationInterview(job_id, user_id, round)
│   └── ApplicationOffer(job_id, user_id, salary)
│
├── market_events.py
│   ├── SkillTrendDetected(skill, direction, magnitude)
│   ├── MarketSignalDetected(signal_type, source, impact)
│   └── SalaryTrendUpdated(country, role, change)
│
├── learning_events.py
│   ├── SkillLearned(user_id, skill, hours_spent)
│   ├── RoadmapGenerated(user_id, skills, timeline)
│   └── ROICalculated(skill, unlocked_jobs, hours)
│
└── system_events.py
    ├── WeeklyReportGenerated(user_id, insights)
    ├── ModelCalibrated(model_name, new_weights)
    └── FeatureToggled(feature_name, enabled)
```

### Event Flow

```
1. [Worker] job-scanner
   → ApplyPilot'dan 45 yeni iş buldu
   → Event Bus: JobDiscovered(job_id=123, source="applypilot")

2. [Service] job-intelligence
   → JobDiscovered dinledi
   → Normalize, deduplicate, skill extraction, embedding
   → Timeline snapshot yaz
   → Event Bus: JobScored(job_id=123, score=87, explanation="...")

3. [Service] company-intelligence
   → JobScored dinledi
   → Şirket bilgisini zenginleştir
   → Event Bus: CompanyUpdated(company_id="google")

4. [Service] resume-intelligence
   → JobScored dinledi
   → Memory'den context al, Evidence Graph'tan projects seç
   → Target-aware resume üret
   → Event Bus: ResumeGenerated(user_id="aao0", version="google_ml_v3")

5. [Service] application-engine
   → Kullanıcı "Apply" butonuna bastı
   → Timeline'a application event yaz
   → Event Bus: ApplicationSubmitted(job_id=123)

6. [Worker] feedback-learner
   → ApplicationRejected dinledi
   → company_memory ve candidate_memory güncelle
   → Event Bus: ModelCalibrated(model="acceptance_probability")

7. [Service] analytics-engine
   → Tüm event'leri dinle
   → Timeline queries, trend analizi
   → Event Bus: WeeklyReportGenerated(insights=[...])

8. [Frontend] apps/web → Briefing göster
```

---

## V. Plugin System

Her connector bağımsız paket. Core değişmeden yeni kaynak eklenir.

```
plugins/
├── plugin_manager.py
├── plugin_interface.py
│
├── job-sources/
│   ├── applypilot/          # plugin.yaml + client.py + adapter.py
│   ├── jobspy/
│   ├── greenhouse/
│   ├── lever/
│   ├── ashby/
│   ├── workday/
│   ├── linkedin-jobs/
│   ├── indeed/
│   ├── glassdoor/
│   └── google-jobs/
│
├── enrichment/
│   ├── github/              # PyGithub wrapper + repo analysis
│   ├── linkedin-profile/
│   ├── stackoverflow/
│   └── stackshare/
│
├── market-signals/
│   ├── hackernews/          # "Who is hiring?" parser
│   ├── techcrunch/
│   ├── rss-feeds/
│   └── reddit/
│
└── notifications/
    ├── email/
    ├── discord/
    ├── telegram/
    ├── slack/
    └── push/
```

### Plugin Interface

```python
class JobSourcePlugin(ABC):
    @abstractmethod
    def scan(self, hours_old: int = 72) -> List[Job]:
        pass

    @abstractmethod
    def get_metadata(self) -> dict:
        pass

class EnrichmentPlugin(ABC):
    @abstractmethod
    def enrich(self, entity: Any) -> Any:
        pass
```

### Plugin Discovery

```python
class PluginManager:
    def discover_plugins(self):
        for plugin_dir in Path('plugins').glob('*/'):
            plugin_yaml = plugin_dir / 'plugin.yaml'
            if plugin_yaml.exists():
                metadata = yaml.safe_load(plugin_yaml.read_text())
                self.plugins[metadata['name']] = {
                    'path': plugin_dir,
                    'metadata': metadata,
                    'enabled': metadata.get('enabled', True)
                }

    def get_job_sources(self) -> List[JobSourcePlugin]:
        return [
            self.load_plugin(name)
            for name, plugin in self.plugins.items()
            if plugin['metadata']['type'] == 'job-source'
            and plugin['enabled']
        ]
```

---

## VI. Feature Registry

Her feature kendi metadata dosyasına sahip. Gradual rollout, A/B test, dependency yönetimi.

```
features/
├── feature_registry.py
├── resume_ai/
│   ├── feature.yaml
│   ├── implementation.py
│   └── tests/
├── market_ai/
├── company_ai/
├── weekly_planner/
├── linkedin_scanner/
├── feedback_learning/
└── timeline_view/
```

### Feature Metadata

```yaml
# features/resume_ai/feature.yaml
name: resume_ai
description: "AI-powered resume generation and optimization"
version: 1.0.0
enabled: true
rollout_percentage: 100
dependencies: []
requires:
  - github_token
metrics:
  - resumes_generated
  - ats_score_improvement
```

### Feature Registry

```python
class FeatureRegistry:
    def is_enabled(self, feature_name: str, user_id: str = None) -> bool:
        feature = self.features.get(feature_name)
        if not feature or not feature['enabled']:
            return False

        if user_id and feature['rollout_percentage'] < 100:
            hash_value = hash(user_id) % 100
            return hash_value < feature['rollout_percentage']

        return True
```

---

## VII. Versioned Knowledge

Domain knowledge versiyonlanır. Visa sistemi değişirse `v2/` eklenir, `v1/` bozulmaz.

```
knowledge/
├── v1/
│   ├── skills/
│   │   ├── skill_graph.yaml
│   │   ├── categories.yaml
│   │   ├── transfer_weights.yaml
│   │   └── market_demand.yaml
│   ├── countries/
│   │   ├── germany.yaml
│   │   ├── canada.yaml
│   │   ├── netherlands.yaml
│   │   ├── uae.yaml
│   │   └── usa.yaml
│   ├── visa/
│   │   ├── eu_blue_card.yaml
│   │   ├── us_h1b.yaml
│   │   └── uk_skilled_worker.yaml
│   ├── companies/
│   │   ├── big_tech.yaml
│   │   ├── unicorns.yaml
│   │   └── startups.yaml
│   └── salaries/
│       ├── backend_eu.yaml
│       ├── ml_us.yaml
│       └── frontend_global.yaml
└── v2/                         # Gelecek versiyon
    ├── skills/
    └── countries/
```

### Knowledge Loader

```python
class KnowledgeLoader:
    def __init__(self, version: str = 'v1'):
        self.base_path = Path(f'knowledge/{version}')

    def load_skill_graph(self) -> dict:
        return yaml.safe_load(
            (self.base_path / 'skills' / 'skill_graph.yaml').read_text()
        )

    def load_country(self, country: str) -> dict:
        return yaml.safe_load(
            (self.base_path / 'countries' / f'{country}.yaml').read_text()
        )
```

---

## VIII. AI Memory Layer

LLM her seferinde sıfırdan hesaplamaz. Sistem zamanla daha akıllı olur.

```
packages/memory/
├── candidate_memory.py     # "Remote işlerde interview rate 2x"
├── company_memory.py       # "Google'da phone screen'de system design soruluyor"
├── market_memory.py        # "Rust talebi son 6 ayda %40 arttı"
├── conversation_memory.py  # "Kullanıcı Big Tech'ten kaçınmak istiyor"
└── learning_memory.py      # "Haftada 10 saat optimal"
```

### Memory Usage

```python
class FeedbackLearnerUseCase:
    def learn_from_rejection(self, application: Application, feedback: str):
        self.company_memory.add_fact(
            company=application.company,
            fact=f"Rejected at {application.stage}",
            context=feedback
        )
        if "experience" in feedback.lower():
            self.candidate_memory.add_fact(
                fact=f"{application.company} için experience yetersiz",
                confidence=0.7
            )

    def get_personalized_advice(self, job: Job) -> str:
        company_facts = self.company_memory.get_facts(job.company)
        candidate_facts = self.candidate_memory.get_facts()

        prompt = f"""
        Based on the following memory:
        - Company facts: {company_facts}
        - Candidate facts: {candidate_facts}

        What advice would you give for this job application?
        """
        return llm.generate(prompt)
```

---

## IX. Timeline Layer

Her şey zaman ekseninde tutulur. "Geçen hafta ne değişti?" sorusu cevaplanabilir.

### Schema

```sql
CREATE TABLE timeline_snapshots (
    id            SERIAL PRIMARY KEY,
    entity_type   TEXT NOT NULL,   -- 'job', 'company', 'skill', 'salary'
    entity_id     TEXT NOT NULL,
    snapshot_at   TIMESTAMP NOT NULL,
    snapshot_data JSONB NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE timeline_changes (
    id            SERIAL PRIMARY KEY,
    entity_type   TEXT NOT NULL,
    entity_id     TEXT NOT NULL,
    changed_at    TIMESTAMP NOT NULL,
    field_name    TEXT NOT NULL,
    old_value     JSONB,
    new_value     JSONB,
    change_type   TEXT,             -- 'created', 'updated', 'deleted'
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_timeline_entity ON timeline_snapshots(entity_type, entity_id);
CREATE INDEX idx_timeline_time   ON timeline_snapshots(snapshot_at);
CREATE INDEX idx_changes_entity  ON timeline_changes(entity_type, entity_id);
CREATE INDEX idx_changes_time    ON timeline_changes(changed_at);
```

### Timeline Queries

```python
class Timeline:
    def get_entity_history(self, entity_type: str, entity_id: str,
                           days: int = 30) -> List[dict]:
        # Entity'nin son N günlük state geçmişi

    def detect_changes(self, entity_type: str, entity_id: str,
                       field: str) -> List[dict]:
        # Belirli bir alandaki değişimler
```

### Kullanıcı Göreceği Örnek

```
Google ML Engineer
├─ Salary: $85k → $92k     (↑ 8%,  2 weeks ago)
├─ Fit Score: 78 → 91      (↑ 13,  1 week ago)
└─ Competition: Mid → High (↑,     3 days ago)

Rust (Skill)
├─ Job Count: 1,240 → 1,580  (↑ 27%, last month)
├─ Avg Salary: $95k → $102k  (↑ 7%,  last month)
└─ Demand: High → Very High  (↑,     2 weeks ago)
```

---

## X. AI Briefing Dashboard

```
┌─────────────────────────────────────────────────────────┐
│  Good morning, AAO0                                     │
│  Tuesday, July 14, 2026                                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  TODAY'S BRIEF                                          │
│  ├─ 27 new jobs discovered                              │
│  ├─ 5 high-priority matches                             │
│  ├─ 1 deadline approaching (Google ML Engineer)         │
│  └─ 3 companies started hiring this week                │
│                                                         │
│  MARKET SIGNALS                                         │
│  ├─ Rust demand +14% (last 7 days)                      │
│  ├─ Google opened 12 ML positions (Berlin)              │
│  ├─ Docker skills unlock 91 new jobs                    │
│  └─ Remote competition increased 23%                    │
│                                                         │
│  YOUR ACTIONS                                           │
│  ├─ Apply to 4 jobs today                               │
│  ├─ Learn Docker (12h → 91 jobs)                        │
│  ├─ Update resume for Spotify (evidence gap)            │
│  └─ Follow up with Microsoft (7 days since applied)     │
│                                                         │
│  INSIGHTS                                               │
│  ├─ Your Rust projects increase interview rate by 40%   │
│  ├─ Backend resume outperforms ML resume (2:1)          │
│  └─ Germany has highest success rate for your profile   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**9 Dashboard Ekranı:**

| # | Ekran | İçerik |
|---|---|---|
| 1 | **Briefing** | AI-generated daily brief |
| 2 | **Inbox** | Prioritized job matches |
| 3 | **Companies** | Living company profiles |
| 4 | **Resume Studio** | Evidence-based resume generation |
| 5 | **Applications** | Pipeline & timeline |
| 6 | **Market** | Trends & signals |
| 7 | **Learning** | Skill ROI & roadmap |
| 8 | **Analytics** | Funnel & insights |
| 9 | **Settings** | Preferences & config |

---

## XI. Klasör Yapısı (LOCKED v1.0)

```
career-os/
│
├── apps/
│   ├── api/                    # FastAPI Gateway
│   ├── web/                    # Next.js Dashboard
│   └── cli/                    # Typer CLI
│
├── packages/
│   ├── domain/                 # 8 domain entity (saf Python, bağımlılık yok)
│   │   ├── identity/
│   │   ├── job/
│   │   ├── company/
│   │   ├── resume/
│   │   ├── market/
│   │   ├── application/
│   │   ├── learning/
│   │   └── analytics/
│   ├── shared/                 # Types, utils, exceptions
│   ├── db/                     # Postgres + migrations
│   ├── vector/                 # LanceDB embeddings
│   ├── graph/                  # NetworkX → KuzuDB
│   ├── intelligence/           # SemanticMatcher, OpportunityScorer, GapAnalyzer
│   ├── memory/                 # AI Memory Layer
│   ├── timeline/               # Temporal data layer
│   ├── knowledge/              # Versioned knowledge loader
│   └── sdk/                    # Public SDK
│
├── services/                   # 8 domain implementation (Clean Architecture)
│   ├── identity-service/
│   ├── job-intelligence/
│   ├── company-intelligence/
│   ├── resume-intelligence/    # Hiring-Agent entegrasyonu
│   ├── market-intelligence/
│   ├── application-engine/
│   ├── learning-engine/
│   └── analytics-engine/
│
├── workers/                    # 8 background agent (Dramatiq)
│   ├── job-scanner/
│   ├── company-monitor/
│   ├── market-monitor/
│   ├── resume-optimizer/
│   ├── weekly-planner/
│   ├── feedback-learner/
│   ├── reminder-agent/
│   └── notification-worker/
│
├── plugins/                    # Extensible connectors
│   ├── job-sources/
│   ├── enrichment/
│   ├── market-signals/
│   └── notifications/
│
├── events/                     # Event Bus
│   ├── event_bus.py
│   ├── job_events.py
│   ├── company_events.py
│   ├── resume_events.py
│   ├── application_events.py
│   ├── market_events.py
│   ├── learning_events.py
│   └── system_events.py
│
├── features/                   # Feature Registry
│   ├── feature_registry.py
│   └── [feature_name]/feature.yaml + implementation.py
│
├── knowledge/                  # Versioned domain knowledge
│   ├── v1/skills/, countries/, visa/, companies/, salaries/
│   └── v2/                     # Gelecek versiyon
│
├── prompts/                    # Versioned LLM prompts (.jinja)
│   ├── resume/
│   ├── job/
│   ├── company/
│   ├── market/
│   └── weekly/
│
├── templates/                  # Output templates
│   ├── resume/
│   ├── cover-letter/
│   └── email/
│
├── evaluation/                 # AI benchmarks
│   ├── job-matching/
│   ├── resume-quality/
│   └── company-extraction/
│
├── design-system/              # UI tokens & components
├── design/                     # Figma, wireframes
├── assets/
├── config/
├── infrastructure/             # Docker, K8s, Terraform
├── scripts/
├── database/                   # Schema, migrations
├── docs/
└── tests/                      # Unit, integration, E2E
```

---

## XII. Teknoloji Stack (LOCKED v1.0)

| Katman | Teknoloji |
|---|---|
| **Frontend** | Next.js 14 (App Router), Tailwind, shadcn/ui |
| **API Gateway** | FastAPI, Pydantic v2 |
| **Domain Logic** | Python 3.11+, Typer (CLI) |
| **Primary DB** | PostgreSQL 16 (+ Timeline tables) |
| **Vector DB** | LanceDB (local-first) |
| **Graph DB** | NetworkX → KuzuDB (scale) |
| **Event Bus** | Redis Streams (in-memory for local) |
| **Cache** | Redis |
| **Queue** | Dramatiq (workers) |
| **LLM Router** | OpenRouter + Ollama (local) + Gemini |
| **Embeddings** | sentence-transformers (all-MiniLM-L6-v2) |
| **PDF Parsing** | PyMuPDF + Hiring-Agent pipeline |
| **Monorepo** | Turborepo |
| **Deployment** | Docker Compose (local), K8s (production) |

---

## XIII. Phased Roadmap

### Phase 1 — Foundation (Week 1-4)
- `packages/domain` — 8 domain entity
- `packages/db` — PostgreSQL + migrations (timeline tables dahil)
- `events/` — Event Bus implementation
- `services/identity-service` + `services/job-intelligence`
- `plugins/job-sources/applypilot` — ilk plugin
- `apps/api` — FastAPI gateway
- `apps/cli` — `career-os scan`, `career-os strategy`

### Phase 2 — Intelligence Core (Week 5-10)
- `packages/intelligence` — mevcut SemanticMatcher, OpportunityScorer, GapAnalyzer buraya taşınır
- `packages/memory` — Candidate & Company memory
- `services/resume-intelligence` — Hiring-Agent entegrasyonu
- `services/application-engine` — başvuru tracking
- `prompts/job/`, `prompts/resume/`
- `knowledge/v1/skills/` — skill_graph.yaml
- `features/resume_ai` — Feature registry

### Phase 3 — Company & Market (Week 11-16)
- `services/company-intelligence` — living company profiles
- `services/market-intelligence` — news scanner
- `plugins/enrichment/github` — Evidence Graph enrichment
- `plugins/market-signals/hackernews` — HN scanner
- `knowledge/v1/countries/`, `knowledge/v1/companies/`
- `packages/timeline` — Timeline queries

### Phase 4 — Frontend (Week 17-22)
- `apps/web` — Next.js dashboard
- 9 ekran: Briefing, Inbox, Companies, Resume Studio, Applications, Market, Learning, Analytics, Settings
- Timeline view (geçmiş değişiklikler)
- `design-system/` — tokens & components
- Feature flag → frontend render entegrasyonu

### Phase 5 — Learning & Analytics (Week 23-28)
- `services/learning-engine` — ROI-based roadmap
- `services/analytics-engine` — feedback learning
- `packages/memory/learning_memory`
- `evaluation/` — AI benchmarks
- `workers/feedback-learner` — model calibration
- `workers/weekly-planner` — AI briefing generator

### Phase 6 — Scale (Week 29-36)
- Tüm 8 worker aktif
- `plugins/notifications/` — multi-channel
- `graph/` — KuzuDB migration
- `knowledge/v2/`
- Plugin marketplace (community contributions)
- SaaS-ready deployment

---

## XIV. Anti-Patterns (Yasaklar)

| Yapılmaz | Yerine |
|---|---|
| Auto-apply bot | Human-in-the-loop application |
| Hardcoded thresholds | `config/thresholds.yaml` |
| Inline LLM prompts | `prompts/*.jinja` (versioned) |
| Magic numbers | `knowledge/v1/*.yaml` |
| Business logic in routers | `services/*/application/` |
| Direct DB queries in services | `packages/db/repositories/` |
| Cross-domain direct imports | Event Bus üzerinden |
| SQLite in production | PostgreSQL |
| Connector hardcoding | `plugins/` ile extensible |
| Feature flag without metadata | `features/*/feature.yaml` |
| Knowledge without versioning | `knowledge/v1/`, `knowledge/v2/` |
| LLM without memory | `packages/memory/` kullan |
| Data without timeline | `packages/timeline/` kullan |

---

## XV. Başarı Kriteri

Bir yıl sonra, bir kullanıcı CareerOS'u bir arkadaşına şöyle anlatabilmeli:

> *"Kariyerimin tamamını orada yönetiyorum. İlanları buluyor, şirketleri araştırıyor, CV'mi her başvuruya özel üretiyor, hangi skill'i öğrenmem gerektiğini ROI ile söylüyor, başvuru sonrası mülakat hatırlatması yapıyor. En güzeli, her sabah bana 'Bugün ne yapmalısın' diye AI briefing veriyor. Geçen hafta ne değiştiğini timeline'dan görüyorum. Artık Excel, Notion, LinkedIn, JobSpy — hiçbiri yok."*

---

## XVI. Architecture Lock Beyanı

**14 Temmuz 2026** tarihinden itibaren:

- Yeni domain eklenmez (8 domain sabit)
- Yeni servis eklenmez (mevcut domain'lerin içine feature eklenir)
- Yeni üst-düzey klasör eklenmez (mevcut yapıya uymalı)
- Event Bus üzerinden iletişim (direct coupling yasak)
- Plugin system ile genişletme (connector hardcoding yasak)
- Feature registry ile gradual rollout
- Versioned knowledge ile migration
- AI memory ile learning
- Timeline ile temporal queries

**Değişiklik süreci:** Change request → Impact analysis → Migration plan → Approval → Doküman güncellenir (v1.1, v2.0)
