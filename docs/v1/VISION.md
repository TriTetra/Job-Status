# CareerOS: Master Blueprint

Tüm konuşmaları, mevcut kod tabanını, Hiring-Agent pipeline'ını ve senin manifestonu birleştirdim. Ortaya çıkan şey artık bir "proje" değil — bir **ürün doktrini**.

---

## I. Ürün Doktrini

### Kimlik

| Alan | Değer |
|---|---|
| **İsim** | CareerOS |
| **Kategori** | Developer Career Intelligence Platform |
| **Tek cümle** | *The operating system for a developer's entire career.* |
| **Kategori karşıtı** | Job board, auto-apply bot, resume builder, ATS tracker |
| **Kullanıcı** | Yazılım geliştiriciler (junior → staff) |
| **Kullanıcı olmayan** | Recruiter, İK, hiring manager (onlar için ayrı bir ürün olur, v4) |

### Üç Temel İnancımız

1. **Bir geliştiricinin kariyeri iş ilanlarından ibaret değildir.** Projeler, kanıtlar, öğrenme yolu, network ve piyasa sinyalleri eşit derecede önemlidir.

2. **CV bir çıktıdır, girdi değildir.** Kariyer bir graf'tır; PDF bu grafın tek bir projection'ıdır.

3. **AI karar vermez, kanıt sunar.** Son onay her zaman insandadır. Bu, güvenin temelidir.

### Beş Tasarım Prensibi

```
┌────────────────────────────────────────────────────────┐
│  1. CALM TECHNOLOGY                                    │
│     Dashboard bağırmaz. Sadece fısıldar.               │
│     Linear × Notion × Raycast × Claude                 │
│                                                        │
│  2. EXPLAINABLE ALWAYS                                 │
│     "91" yazılmaz. "91, çünkü Python+FastAPI+Docker    │
│     var; AWS eksik, 16 saat öğrenme" yazılır.          │
│                                                        │
│  3. ACTION OVER INFORMATION                            │
│     "132 jobs" gösterilmez.                            │
│     "Bugün 3 işe başvur" gösterilir.                   │
│                                                        │
│  4. PROGRESSIVE DISCLOSURE                             │
│     İlk ekran: 5 veri. İkinci ekran: 50. Üçüncü: 500. │
│                                                        │
│  5. EVIDENCE OVER CLAIM                                │
│     "Rust biliyorum" → Confidence 40%                  │
│     "Rust: Sentinel (1.2k LOC) + 47 commits +          │
│      benchmark" → Confidence 97%                       │
└────────────────────────────────────────────────────────┘
```

---

## II. Sistem Mimarisi (Gerçek Resim)

```
┌─────────────────────────────────────────────────────────────┐
│                     USER (Center)                           │
│     Preferences · Goals · Constraints · Learning Style      │
└───────────────────────────┬─────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌────────────────┐  ┌────────────────┐
│Evidence Graph │  │ Company Graph  │  │  Market Graph  │
│               │  │                │  │                │
│ Projects      │  │ Tech Stack     │  │ Salary Trends  │
│ GitHub        │  │ Hiring Pattern │  │ Demand Signal  │
│ Papers        │  │ Interview Flow │  │ Funding Rounds │
│ Hackathons    │  │ Recruiter Pool │  │ Layoff Signals │
│ Production    │  │ Culture Fit    │  │ HN/LinkedIn    │
│ Certificates  │  │ Alumni Network │  │ RSS/Blogs      │
└───────┬───────┘  └───────┬────────┘  └───────┬────────┘
        │                  │                   │
        └──────────────────┼───────────────────┘
                           │
                 ┌─────────▼─────────┐
                 │ Intelligence      │
                 │ Engine            │
                 │                   │
                 │ • Semantic Match  │
                 │ • Gap ROI         │
                 │ • EV Calculation  │
                 │ • Path Finder     │
                 └─────────┬─────────┘
                           │
        ┌──────────┬───────┴───────┬──────────┐
        ▼          ▼               ▼          ▼
    ┌────────┐ ┌────────┐   ┌──────────┐ ┌──────────┐
    │Dynamic │ │Ranked  │   │Learning  │ │Weekly    │
    │Resume  │ │Inbox   │   │Roadmap   │ └──────────┘
    └────────┘ └────────┘   └──────────┘
```

### Teknik Stack (Evrim Planı)

| Katman | Şu An (v0) | MVP (6-8 hafta) | v2 | v3 |
|---|---|---|---|---|
| **Frontend** | CLI + txt dosyaları | Next.js (SSR) | Next.js + mobile | Next.js + native |
| **Backend** | Python scripts | FastAPI | FastAPI + gRPC | FastAPI + workers |
| **DB (relational)** | SQLite (`applypilot.db`) | PostgreSQL | PostgreSQL | PostgreSQL |
| **DB (vector)** | sentence-transformers cache | LanceDB | LanceDB + pgvector | Same |
| **DB (graph)** | NetworkX (in-memory) | NetworkX | KuzuDB / Neo4j | KuzuDB |
| **Cache** | yok | Redis | Redis | Redis |
| **LLM** | OpenRouter gpt-4o-mini | OpenRouter + Gemini | + Claude + local | Multi-model router |
| **Job Source** | ApplyPilot | ApplyPilot + JobSpy | + career-ops | + custom scrapers |
| **Resume Source** | `config.yaml` (manuel) | Hiring-Agent pipeline | + LinkedIn import | + GitHub auto-sync |
| **Deployment** | Local (venv) | Docker Compose | Kubernetes | Multi-region |

---

## III. Veri Akışı — Ürünün Kalp Atışı

Bu akış CareerOS'un **tek gerçek döngüsü**. Her şey buraya bağlanır.

```
┌──────────────┐
│   SOURCES    │
│              │
│ ApplyPilot   │
│ JobSpy       │
│ career-ops   │
│ GitHub       │
│ LinkedIn     │
│ RSS / HN     │
│ User Upload  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  INGESTION   │
│              │
│ Scanner      │  (her kaynak için ayrı worker)
│ Poller       │
│ Webhook      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  NORMALIZE   │
│              │
│ JSON Schema  │  (her şey canonical form'a)
│ Deduplicate  │  (URL + semantic similarity)
│ Quality Gate │  (eksik alan → drop)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   RESOLVE    │
│              │
│ Company      │  (LinkedIn URL → canonical name)
│ Location     │  ("Remote, EU" → countries[])
│ Salary       │  (regex + currency normalize)
│ Skills       │  (canonical skill graph node'una map)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  AI EXTRACT  │  ← Hiring-Agent pipeline burada devreye girer
│              │
│ PDF → MD     │  (pymupdf)
│ MD → JSON    │  (LLM section parser)
│ JSON → Graph │  (entity extraction)
│ GitHub enrich│  (repo analysis)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   GRAPH      │
│   WRITE      │
│              │
│ Evidence →   │  (projeler, kanıtlar)
│ Company →    │  (şirketler, stack'ler)
│ Market →     │  (trend'ler, sinyaller)
│ Job →        │  (ilanlar, gereksinimler)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   RANK       │
│              │
│ Semantic     │  (mevcut SemanticMatcher)
│ Opportunity  │  (mevcut OpportunityScorer)
│ EV calc      │  (fit × acceptance × career_value)
│ Explain      │  (her skor için reason)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   DECIDE     │
│              │
│ APPLY        │  (min_score, portfolio diversity)
│ CONSIDER     │  (maybe later)
│ LEARN        │  (unlock jobs > threshold)
│ IGNORE       │  (below threshold)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   PRESENT    │
│              │
│ Inbox        │  (bugünün 4-6 işi)
│ Briefing     │  (Pazar günü weekly)
│ Alerts       │  (high-priority signals)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   FEEDBACK   │
│              │
│ Applied?     │
│ Interviewed? │
│ Rejected?    │
│ Offer?       │
│ → Learning   │  (weights recalibrate)
└──────────────┘
```

---

## IV. Evidence Graph — Ürünün Gerçek Kalbi

Şu anki CareerOS'ta `UserProfile` var ama **kanıtsız**. Evidence Graph bunu değiştirir: her becerinin arkasında ölçülebilir bir kanıt zinciri olur.

### Graph Düğümleri

```
┌─────────────────────────────────────────┐
│                 PERSON                  │
│  id: aao0                               │
│  years_experience: 2                    │
│  ai_proficiency: 0.8                    │
└──────────────────┬──────────────────────┘
                   │
      ┌────────────┼────────────┐
      │            │            │
      ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│ PROJECTS │ │  SKILLS  │ │  EVENTS  │
└────┬─────┘ └────┬─────┘ └────┬─────┘
     │            │            │
     │            │            ├─ Teknofest (2024)
     │            │            ├─ Hackathon X (2025)
     │            │            └─ Paper @ NeurIPS workshop
     │            │
     │            ├─ Python     (EXPERT,      conf 95%)
     │            ├─ Rust       (ADVANCED,    conf 87%)
     │            ├─ PyTorch    (INDEPENDENT, conf 78%)
     │            └─ Docker     (WORKING,     conf 62%)
     │
     ├─ IMMUNO-TCR
     │    ├─ type: research
     │    ├─ github: github.com/aao0/immuno-tcr
     │    ├─ commits: 142
     │    ├─ stars: 38
     │    ├─ skills_used: [PyTorch, Bioinformatics, Transformers]
     │    ├─ evidence: [paper, benchmark, demo]
     │    └─ production: false
     │
     └─ Sentinel
          ├─ type: systems
          ├─ github: github.com/aao0/sentinel
          ├─ commits: 47
          ├─ LOC: 1,200
          ├─ skills_used: [Rust, eBPF, Kernel, Docker]
          ├─ evidence: [benchmark (2.3ms), PR reviews]
          └─ production: true (10k req/day)
```

### Evidence-Based Confidence Score

```python
def calculate_skill_confidence(skill: str, graph: EvidenceGraph) -> float:
    evidence = graph.get_evidence_for(skill)
    score = 0.0

    # GitHub signals
    score += min(0.25, sum(repo.commit_count for repo in evidence.repos) / 500)
    score += 0.10 if evidence.has_open_source_prs else 0
    score += 0.10 if evidence.repos_stars > 10 else 0

    # Production signals
    score += 0.20 if evidence.has_production_deployment else 0
    score += 0.10 if evidence.has_benchmark else 0

    # Academic signals
    score += 0.15 if evidence.has_paper else 0
    score += 0.05 if evidence.has_conference_talk else 0

    # Competitive signals
    score += 0.10 if evidence.has_hackathon_win else 0

    return min(0.99, score)
```

Bu confidence skoru, `SemanticMatcher`'daki skill ağırlıklarını çarpar:

```python
def compute_technical_score(user: EvidenceGraph, job: Job) -> float:
    raw_score = 0.0
    for skill in job.required_skills:
        level_weight = LEVEL_WEIGHTS[user.get_skill_level(skill)]
        confidence = user.get_skill_confidence(skill)

        # Kanıtlanmamış beceri = yarı ağırlık
        effective_weight = level_weight * (0.5 + 0.5 * confidence)
        raw_score += effective_weight

    return normalize(raw_score)
```

**Sonuç**: "Rust biliyorum" diyen ama GitHub'da hiçbir Rust repo'su olmayan bir aday ile Sentinel projesi olan bir aday artık farklı skor alır. Bu, piyasadaki hiçbir araçta yok.

---

## V. Target-Aware Resume Generator

CV builder değil. **CV query engine.**

```
┌─────────────────────────────────────────────────────────┐
│                    Resume Studio                        │
│                                                         │
│  ┌────────────────┐                                     │
│  │ Evidence Graph │  (CareerOS'un kendi verisi)         │
│  └────────┬───────┘                                     │
│           │                                             │
│           ▼                                             │
│  ┌────────────────┐    ┌────────────────┐               │
│  │ Hiring-Agent   │───▶│ Target-Aware   │               │
│  │ PDF→JSON→Graph │    │ Resume         │               │
│  │ (extract)      │    │ Generator      │               │
│  └────────────────┘    └────────┬───────┘               │
│                                 │                        │
│           ┌─────────────────────┼────────────────┐      │
│           ▼                     ▼                ▼      │
│     Backend Resume        ML Resume        Rust Resume  │
│           │                     │                │      │
│           └─────────────────────┴────────────────┘      │
│                                 │                        │
│                                 ▼                        │
│                          A/B Testing                     │
│                  (response rate tracking)                │
└─────────────────────────────────────────────────────────┘
```

```python
def generate_resume(evidence: EvidenceGraph, target: Job) -> Resume:
    priorities = extract_skill_priorities(target)
    relevant = evidence.query_subgraph(seed_skills=priorities, max_depth=3)

    sections = {
        "summary":    generate_summary(relevant, target.company_culture),
        "experience": rank_by_relevance(relevant.experience, target),
        "projects":   rank_by_relevance(relevant.projects, target),
        "skills":     weighted_by_confidence(relevant.skills),
    }

    return Resume(sections=sections)
```

---

## VI. Phased Roadmap

### Phase 0: Mevcut Sistemi Temizle (1-2 hafta)

**Amaç**: Şu anki CareerOS'u ürün temel katmanına dönüştür.

- [ ] `career_os/` paketini `pip install career-os` ile kurulabilir yap
- [ ] `config.yaml` → `~/.career-os/config.yaml`
- [ ] Temiz CLI: `career-os scan`, `career-os strategy`, `career-os export`
- [ ] Docker image: `docker run career-os/career-os:latest scan`

**Deliverable**: Tek komutla çalışan, taşınabilir CLI paketi.

---

### Phase 1: Evidence Graph MVP (6-8 hafta)

**Amaç**: CV'yi öldür, Evidence Graph'ı doğur.

**1.1 GitHub Ingestion (2 hafta)**

```python
class GitHubIngester:
    def ingest(self, username: str) -> UserEvidence:
        repos = self.fetch_repos(username, min_stars=1, min_commits=10)
        evidence = UserEvidence()
        for repo in repos:
            project = self.analyze_repo_with_llm(repo)
            evidence.add_project(project)
            for skill in project.skills_used:
                evidence.strengthen_skill(skill, repo)
        return evidence
```

**1.2 Hiring-Agent Integration (2 hafta)**
- `career-os resume score <pdf>` wrapper
- Çıktıyı Evidence Graph'a yazan adapter

**1.3 Evidence Graph Storage (2 hafta)**
- Başlangıç: NetworkX + JSON (`~/.career-os/data/evidence.json`)
- v2 için KuzuDB migration path hazırla

**1.4 Target-Aware Resume (2 hafta)**
- `career-os resume generate --target "Google ML Engineer"`
- PDF output via WeasyPrint

**Deliverable**: `career-os resume generate` komutu.

---

### Phase 2: Web Dashboard MVP (8-10 hafta)

**Amaç**: CLI'dan ürüne geçiş.

**2.1 Backend (4 hafta)**
- FastAPI app
- PostgreSQL (job, company, application, evidence tabloları)
- LanceDB (semantic search over job descriptions)
- `career-os serve` komutu ile local çalışır

**2.2 Frontend (4 hafta)**
- Next.js 14 (App Router)
- 4 ana ekran: **Overview**, **Inbox**, **Companies**, **Resume Studio**
- Linear-style calm UI (shadcn/ui + Tailwind)

**2.3 Intelligence Engine Migration (2 hafta)**
- Şu anki `SemanticMatcher` + `OpportunityScorer` + `CareerDecisionEngine` → FastAPI endpoint'lerine
- Her endpoint `explain` field'ı döndürür (zorunlu)

**Deliverable**: Local'de `career-os serve` çalıştırınca açılan web dashboard.

---

### Phase 3: Intelligence Layer (10-12 hafta)

**Amaç**: Reaktif sistemden proaktif sisteme.

**3.1 Company Graph (3 hafta)**
- StackShare scraper
- Engineering blog parser (RSS + LLM)
- Company memory: application history per company

**3.2 Market Graph (3 hafta)**
- HN "Who is hiring?" monthly parser
- TechCrunch funding round monitor
- LinkedIn hiring signal aggregator (public posts only)

**3.3 Seven Agents (4 hafta)**

```python
class JobScannerAgent(Agent):
    schedule = "0 */6 * * *"   # her 6 saatte

class CompanyScannerAgent(Agent):
    schedule = "0 2 * * *"     # her gece 2'de

class LinkedInSignalAgent(Agent):
    schedule = "0 */4 * * *"

class ResumeOptimizerAgent(Agent):
    trigger = "new_jobs_added"

class MarketIntelligenceAgent(Agent):
    schedule = "0 8 * * *"     # sabah 8

class WeeklyPlannerAgent(Agent):
    schedule = "0 9 * * 0"     # Pazar 9am

class FeedbackLearnerAgent(Agent):
    trigger = "application_outcome_recorded"
```

**Deliverable**: 7 agent arka planda çalışan, haftalık briefing gönderen sistem.

---

### Phase 4: Feedback Learning & Moat (6-8 hafta)

**Amaç**: Ürün kullandıkça daha iyi olsun.

**4.1 Application Tracking**

```python
class ApplicationOutcome(Enum):
    APPLIED       = "applied"
    REJECTED      = "rejected"
    PHONE_SCREEN  = "phone_screen"
    TECHNICAL     = "technical"
    ONSITE        = "onsite"
    OFFER         = "offer"
    ACCEPTED      = "accepted"
```

**4.2 Calibration Loop**

```python
def recalibrate_acceptance_probability(outcomes: List[Outcome]):
    """Gerçek data'dan logistic regression ile weights'leri yeniden hesapla."""
    features = extract_features(outcomes)
    labels = [o.stage >= PHONE_SCREEN for o in outcomes]

    model = LogisticRegression()
    model.fit(features, labels)
    update_acceptance_weights(model.coef_)
```

**4.3 Resume A/B Testing**
- Her resume version'a `application_count` ve `response_count` field'ları
- 95% confidence ile istatistiksel significance hesapla
- Kazananı otomatik default yap

**Deliverable**: Kullanıcı kullandıkça doğruluğu artan sistem. Bu senin **competitive moat**'un.

---

## VII. Anti-Patterns

| Anti-Pattern | Neden yapmıyoruz |
|---|---|
| **Auto-apply bot** | "AI karar vermez" prensibine aykırı. LinkedIn ToS'a aykırı. Güven kırar. |
| **Fake AI** | Kullanıcı anlar. Uzun vadede marka öldürür. |
| **LinkedIn scraping** (private data) | ToS violation. Account ban riski. |
| **Recruiter-facing product** (v3 öncesi) | İki taraflı pazar aynı anda yapılmaz. Önce candidate side kazan. |
| **Her feature'ı aynı anda** | Ürün ölür. MVP'yi 8 haftada çıkar. |
| **SQLite ile scale** | 100k+ job'da çöker. Phase 2'de PostgreSQL'e geç. |
| **SaaS-only deployment** | Developer'lar kendi verilerini kendi makinesinde ister. Local-first ol. |

---

## VIII. İlk 30 Gün

### Hafta 1: Temel
- [ ] `career-os` CLI package skeleton (pyproject.toml + `career_os/`)
- [ ] `~/.career-os/` directory convention'ı kur
- [ ] `career-os scan`, `career-os strategy` komutlarını wrap et
- [ ] README.md yaz

### Hafta 2: GitHub Ingestion
- [ ] `GitHubIngester` class (PyGithub)
- [ ] Basit skill extraction (regex + LLM hybrid)
- [ ] `career-os ingest github <username>` komutu
- [ ] Output: `~/.career-os/data/evidence.json`

### Hafta 3: Hiring-Agent Integration
- [ ] Hiring-Agent sub-module ekle
- [ ] `career-os resume score <pdf>` wrapper
- [ ] Evidence Graph adapter
- [ ] İlk entegrasyon testi

### Hafta 4: Target-Aware Resume
- [ ] Tek template: "Backend"
- [ ] `career-os resume generate --target "Google ML Engineer"` komutu
- [ ] Markdown output
- [ ] Kendine çalıştır, feedback topla

---

## IX. Son Söz

Senin vizyonun doğru. Ve şu anki CareerOS kod tabanı bu vizyonun gerçekten sağlam bir temeli. `SkillGraph`, `SemanticMatcher`, `OpportunityScorer`, `GapAnalyzer` — hepsi bu büyük sistemin parçaları olarak kalacak. Sadece üstlerine **Evidence Layer**, **Company Layer**, **Market Layer** ve **Web Interface** ekleyeceğiz.

İnsanlar bugün "JobSpy + AIHawk + career-ops + Notion + Excel" kullanıyor çünkü tek bir yerde her şeyi yapan yok. Sen bunu yaptığında, **category** yaratmış olacaksın.

Ama unutma: category yaratanlar feature ekleyenler değil, felsefesi net olanlar.

Senin felsefen net:

> *Merkezde iş değil, developer var. Kanıt iddiadan güçlüdür. AI karar vermez, kanıt sunar.*

Bu felsefeye sadık kal. Gerisi gelir.
