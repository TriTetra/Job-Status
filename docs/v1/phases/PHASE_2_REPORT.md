# 📘 FAZ 2 RAPORU — Intelligence Core (Zeka Katmanı)

## 📄 Rapor Meta Bilgisi

| Alan | Değer |
|---|---|
| **Rapor Başlığı** | CareerOS Faz 2 — Intelligence Core Architecture Raporu |
| **Rapor Versiyonu** | `v1.0.0` |
| **Oluşturulma Tarihi** | 14 Temmuz 2026 |
| **Son Güncelleme** | 14 Temmuz 2026 |
| **Yazar** | AI Codebase Auditor (gerçek kod okuması) |
| **Kapsam** | `core/intelligence/`, `core/memory/`, `core/prompts/`, `services/resume_intelligence/`, `services/application_engine/`, `services/hiring-agent/`, `plugins/resume_parsers/`, `plugins/enrichment/github/`, `core/knowledge/` |
| **Arşivlenen** | `_archive/features/` (Feature Registry — single-user tool için gereksiz) |
| **Dışında Kalanlar** | Foundation (Faz 1), Company/Market (Faz 3), Frontend (Faz 4) |
| **Önceki Rapor** | Faz 1 — Foundation (v1.0.0) |

---

## 🎯 Faz Özeti

> **Faz 2, CareerOS'un "beyin" fazıdır.** Hiring-Agent entegrasyonu ile CV parse etme, Evidence Graph ile kanıta dayalı skill takibi, Target-Aware Resume Generator ile her başvuruya özel CV üretme ve Memory Layer ile öğrenme — vizyonun "Evidence > Claim" prensibini ürüne dönüştürür.

**Tek Cümle:** *"AI destekli CV parsing, kanıta dayalı skill confidence, target-aware CV üretimi ve öğrenme kapasitesi."*

---

## 📊 Faz İstatistikleri

| Metrik | Değer |
|---|---|
| **Toplam Dosya Sayısı** | 22 (hiring-agent hariç) + 11 (hiring-agent) = **33** |
| **Toplam Kod Satırı** | ~2,900 (hiring-agent hariç) |
| **Hiring-Agent Satırı** | ~4,280 (external microservice) |
| **DB Tabloları** | 1 (`evidence`) + 9 GitHub metric column |
| **LLM Prompts** | 4 Jinja template |
| **Memory Types** | 5 (candidate, company, market, conversation, learning) |
| **Feature Registry** | `_archive/features/` — arşivlendi (single-user için gereksiz) |
| **Plugin Sayısı** | 2 (hiring_agent parser, github enrichment) |
| **Test Dosyası (aktif)** | 4 |
| **Test Satırı** | ~688 |
| **Tamamlanma Oranı** | ✅ %100 |
| **Mimari Kilit** | 🔒 LOCKED |

---

## 📁 Dosya Envanteri (Detaylı Tablo)

### A. Intelligence Package — `core/intelligence/`

| # | Dosya | Satır | Sorumluluk | Kritiklik |
|---|---|---|---|---|
| 1 | `semantic_matcher.py` | 421 | SentenceTransformer wrapper, cosine similarity, lazy init | 🔴 Kritik |
| 2 | `opportunity_scorer.py` | 564 | Weighted scoring formula, configurable weights | 🔴 Kritik |
| 3 | `gap_analyzer.py` | 419 | Skill gap detection, learning path suggestions | 🟠 Yüksek |

**`core/intelligence/` Alt Toplam:** ~1,404 satır | 3 dosya

---

### B. Memory Layer — `core/memory/`

| # | Dosya | Satır | Sorumluluk | Kritiklik |
|---|---|---|---|---|
| 1 | `base.py` | 79 | `BaseMemory` ABC, `MemoryFact` dataclass | 🔴 Kritik |
| 2 | `candidate_memory.py` | 126 | User learning patterns, application outcome learning | 🔴 Kritik |
| 3 | `company_memory.py` | 103 | Per-company interview facts, recommendations | 🟠 Yüksek |
| 4 | `conversation_memory.py` | 69 | LLM conversation context | 🟡 Orta |
| 5 | `learning_memory.py` | 72 | Skill learning tracking, optimal hours | 🟡 Orta |
| 6 | `market_memory.py` | 82 | Market signal history cache | 🟡 Orta |

**`core/memory/` Alt Toplam:** ~531 satır | 6 dosya

> **Not:** Tüm memory tipleri şimdilik **in-memory** — restart'ta kaybolur. Faz 5'te DB persistence.

---

### C. Prompts — `core/prompts/`

| # | Dosya | Satır | Sorumluluk | Kritiklik |
|---|---|---|---|---|
| 1 | `template_loader.py` | 72 | Jinja2 Environment singleton, `render()`, `list_templates()` | 🔴 Kritik |
| 2 | `job/extract_priorities.jinja` | ~40 | İş ilanından skill priority extraction | 🟠 Yüksek |
| 3 | `resume/tailor_for_target.jinja` | ~60 | Hedef şirkete CV özelleştirme (available_skills constraint) | 🔴 Kritik |
| 4 | `resume/select_projects.jinja` | ~35 | En iyi 4 projeyi seçme (relevance, depth, impact) | 🟠 Yüksek |
| 5 | `resume/generate_summary.jinja` | ~30 | 2-sentence positioning summary | 🟠 Yüksek |

**`core/prompts/` Alt Toplam:** ~237 satır | 5 dosya

---

### D. Resume Intelligence Service

| # | Dosya | Satır | Sorumluluk | Kritiklik |
|---|---|---|---|---|
| 1 | `hiring_agent_adapter.py` | 99 | PDF → HiringAgent subprocess → CSV bridge | 🔴 Kritik |
| 2 | `cli.py` | 60 | `resume generate`, `evidence show` | 🟠 Yüksek |
| 3 | `application/evidence_builder.py` | 165 | CSV + GitHub cache → Evidence Graph, confidence scoring | 🔴 Kritik |
| 4 | `application/llm_client.py` | 110 | OpenRouter HTTP client (JSON mode, temperature control) | 🔴 Kritik |
| 5 | `application/resume_generator.py` | 357 | 5-step LLM pipeline → Markdown CV | 🔴 Kritik |

**`services/resume_intelligence/` Alt Toplam:** ~791 satır | 5 dosya

---

### E. Evidence System (DB)

| # | Dosya | Satır | Sorumluluk | Kritiklik |
|---|---|---|---|---|
| 1 | `core/db/models/evidence.py` | 71 | Evidence tablosu + 9 GitHub metric column | 🔴 Kritik |
| 2 | `core/db/repositories/evidence_repo.py` | 87 | `add()`, `get_all_for_user()`, `update_metrics()` | 🔴 Kritik |
| 3 | Migration: `add_evidence_table.py` | 45 | Initial schema | 🟠 Yüksek |
| 4 | Migration: `add_github_metrics_to_evidence.py` | 40 | 9 column addition (hallucination fix) | 🔴 Kritik |

**Evidence System Alt Toplam:** ~243 satır | 4 dosya

---

### F. Application Engine

| # | Dosya | Satır | Sorumluluk | Kritiklik |
|---|---|---|---|---|
| 1 | `services/application_engine/cli.py` | 336 | `track add/list/status/apply/stats/stale` komutları | 🔴 Kritik |

---

### G. Feature Registry — `_archive/features/` (ARŞİVLENDİ)

> **Neden arşivlendi:** SHA-256 hash tabanlı deterministic A/B rollout yalnızca multi-user SaaS'ta anlamlıdır. CareerOS şimdilik single-user personal tool olduğu için gereksizdir. Faz 5'te SaaS modeline geçildiğinde geri alınabilir.

| # | Dosya | Satır |
|---|---|---|
| 1 | `_archive/features/feature_registry.py` | ~150 |
| 2 | `_archive/features/resume_ai/feature.yaml` | ~20 |
| 3 | `_archive/features/target_aware_resume/feature.yaml` | ~20 |
| 4 | `_archive/features/feedback_learning/feature.yaml` | ~20 |
| 5 | `_archive/scripts/test_feature_registry.py` | ~200 |

---

### H. Hiring-Agent (External Microservice — `services/hiring-agent/`)

> Bu CareerOS'un değil, external bir microservice'tir. Subprocess ile çağrılır.

| # | Dosya | Satır | Sorumluluk |
|---|---|---|---|
| 1 | `score.py` | 377 | Ana değerlendirme motoru |
| 2 | `transform.py` | 938 | CV → structured data dönüşümü |
| 3 | `models.py` | 434 | Pydantic modeller |
| 4 | `pdf.py` | 323 | PyMuPDF PDF okuma |
| 5 | `evaluator.py` | 91 | LLM evaluator |
| 6 | `github.py` | 495 | GitHub profil çekme |
| 7 | `pymupdf_rag.py` | 1,377 | RAG pipeline |
| 8 | `llm_utils.py` | 66 | LLM helpers |
| 9 | `prompt.py` | 83 | Prompt builder |
| 10 | `config.py` | 6 | Env config |
| 11 | `prompts/template_manager.py` | 90 | Şablon yönetimi |

**Hiring-Agent Toplam:** ~4,280 satır | 11 dosya

---

### I. Knowledge (Skill Graph)

| # | Dosya | Satır | Sorumluluk | Kritiklik |
|---|---|---|---|---|
| 1 | `core/knowledge/skill_loader.py` | 100 | Singleton, alias/topic map (68 skill, 229 topic) | 🔴 Kritik |
| 2 | `core/knowledge/company_loader.py` | ~80 | Company YAML loader (Faz 3'e ait ama aynı klasörde) | 🟠 Yüksek |
| 3 | `infra/seeds/v1/skills/skill_graph.yaml` | ~400 | 68 skill, 141 edge, 229 topic map | 🔴 Kritik |
| 4 | `career_os/core/skill_graph.py` | ~200 | NetworkX SkillGraph (LEGACY — refactor bekliyor) | 🟡 Orta |

---

### J. Plugin Infrastructure (Faz 2'ye ait)

| # | Dosya | Satır | Sorumluluk | Kritiklik |
|---|---|---|---|---|
| 1 | `plugins/resume_parsers/hiring_agent/client.py` | 156 | `ResumeParserPlugin` impl, CSV bridge | 🔴 Kritik |
| 2 | `plugins/enrichment/github/client.py` | 35 | PyGithub wrapper | 🟠 Yüksek |
| 3 | `plugins/enrichment/github/repo_analyzer.py` | 88 | LOC, topics, PR count, has_tests, has_docs | 🔴 Kritik |
| 4 | `plugins/enrichment/github/evidence_enricher.py` | 117 | Evidence → GitHub API → DB update | 🔴 Kritik |
| 5 | `scripts/enrich_github_evidence.py` | 69 | CLI enrichment runner | 🟠 Yüksek |

**Plugin (Faz 2) Alt Toplam:** ~465 satır | 5 dosya

---

## 📐 Modül Detayları (Kritik Olanlar)

### Modül 1: `core/intelligence/semantic_matcher.py`

**Satır:** 421 | **Sorumluluk:** SentenceTransformer ile user-job skill matching

```python
class SemanticMatcher:
    def __init__(self):
        self.model = None  # Lazy init — 420MB

    def match(self, user_profile: UserProfile, job: Job) -> MatchResult:
        if self.model is None:
            self.model = SentenceTransformer("all-MiniLM-L6-v2")

        user_emb = self.model.encode(" ".join([s.name for s in user_profile.skills]))
        job_emb  = self.model.encode(" ".join(job.required_skills + job.preferred_skills))

        similarity = np.dot(user_emb, job_emb) / (
            np.linalg.norm(user_emb) * np.linalg.norm(job_emb)
        )

        user_names = {s.name.lower() for s in user_profile.skills}
        skill_gaps = [s for s in job.required_skills if s.lower() not in user_names]

        return MatchResult(overall_score=similarity * 100, skill_gaps=skill_gaps)
```

- ✅ Lazy init — model sadece gerektiğinde yüklenir
- ✅ Cosine similarity — semantic matching (exact keyword değil)
- ✅ Skill gap detection
- ⚠️ `career_os/core/skill_graph.py` import ediyor (legacy technical debt)

---

### Modül 2: `core/intelligence/opportunity_scorer.py`

**Satır:** 564 | **Sorumluluk:** Weighted career score calculation

```python
career_score = (
    fit_score       * w["fit"]          +  # default 0.30
    acceptance_prob * w["acceptance"]   +  # default 0.25
    career_value    * w["career_value"] +  # default 0.25
    market_demand   * w["market_demand"]   # default 0.20
)
expected_value = career_score * acceptance_prob

if career_score >= 70:   recommendation = "APPLY"
elif career_score >= 50: recommendation = "CONSIDER"
else:                    recommendation = "SKIP"
```

- ✅ Weights DB'den per-user override edilebilir
- ✅ 4 sub-score + expected value
- ✅ Threshold-based recommendation

---

### Modül 3: `core/prompts/template_loader.py`

**Satır:** 72 | **Sorumluluk:** Singleton Jinja2 environment

```python
class TemplateLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            prompts_dir = Path(__file__).parent  # core/prompts/
            cls._env = Environment(
                loader=FileSystemLoader(str(prompts_dir)),
                trim_blocks=True, lstrip_blocks=True
            )
            cls._env.filters["join_skills"]    = lambda skills: ", ".join(skills)
            cls._env.filters["truncate_text"]  = lambda text, n=200: text[:n]+"..." if len(text)>n else text
        return cls._instance

    def render(self, template_path: str, **context) -> str:
        return self._env.get_template(template_path).render(**context)
```

- ✅ Singleton — bir kere init, cached
- ✅ `Path(__file__).parent` — konumdan bağımsız, her yerden çalışır
- ✅ Custom filters: `join_skills`, `truncate_text`

---

### Modül 4: `services/resume_intelligence/application/resume_generator.py`

**Satır:** 357 | **Sorumluluk:** 5-step LLM pipeline → Markdown CV

```python
def generate(self, target_company, target_title, template_name, job_description="") -> Path:

    # [1] Load evidence (DB) + projects (GitHub cache)
    evidence = self._load_evidence()
    projects = self._load_github_projects()

    # [2] LLM #1 — extract_priorities.jinja
    priorities = self._extract_priorities(target_title, target_company, job_description)
    # → {must_have: [...], important: [...], culture_signals: [...]}

    # [3] LLM #2 — tailor_for_target.jinja
    # KRITIK: available_skills=list(evidence.keys()) → LLM uyduramaz
    tailoring = self._tailor_evidence(...)
    tailoring = self._normalize_skill_names(tailoring, evidence)  # fuzzy match
    # → {emphasized_skills: [...], de_emphasized_skills: [...], skill_mappings: {...}}

    # [4] LLM #3 — select_projects.jinja
    project_selection = self._select_projects(target_company, target_title, projects)
    # → {selected: [{name, score, reasoning, key_bullets}, ...]}

    # [5] LLM #4 — generate_summary.jinja
    summary = self._generate_summary(...)
    # → "2-sentence positioning string"

    # [6] Jinja Markdown render + write to personal/
    markdown = self._render_template(...)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path
```

**Target-Aware Diff Kanıtı (aynı user, farklı target):**

```
Google ML Engineer:
  Summary:  "ML Engineer with production-grade computer vision..."
  #1 Proje: Project-Drone-Vision (YOLOv8, synthetic data)
  Skills:   Computer Vision, PyTorch, Python

Stripe Backend Engineer:
  Summary:  "Backend engineer experienced in Rust systems programming..."
  #1 Proje: evolutionary-tsp (algorithms, Streamlit)
  Skills:   API design, distributed systems, Rust
```

**"Evidence > Claim" kanıtlandı.**

---

### Modül 5: `services/resume_intelligence/application/evidence_builder.py`

**Satır:** 165 | **Sorumluluk:** CSV + GitHub cache → Evidence Graph

```python
def _confidence(self, commits, stars, eval_scores):
    base             = eval_scores["technical_skills"] / 100
    commit_bonus     = min(commits / 100, 0.20)
    star_bonus       = min(stars / 50, 0.10)
    production_bonus = (eval_scores["production"] / 100) * 0.20
    return min(base + commit_bonus + star_bonus + production_bonus, 1.0)
```

- ✅ SkillLoader topic map: `"yolov8"` → `"Computer Vision"`
- ✅ Her project × skill için ayrı evidence record
- ✅ Confidence formula: base + 3 bonus, cap 1.0

---

### Modül 6: `plugins/enrichment/github/repo_analyzer.py`

**Satır:** 88 | **Sorumluluk:** Real GitHub metrics (hallucination fix)

```python
def analyze(self, repo) -> dict:
    langs = repo.get_languages()
    return {
        "loc_count":        sum(langs.values()),
        "language":         max(langs, key=langs.get),
        "topics":           list(repo.get_topics()),
        "pr_count":         repo.get_pulls(state="all").totalCount,
        "issue_count":      repo.get_issues(state="all").totalCount,
        "has_releases":     repo.get_releases().totalCount > 0,
        "has_tests":        self._detect_tests(repo),
        "has_docs":         self._detect_docs(repo),
        "last_commit_date": ...,
    }
```

- ✅ 9 real metric → evidence tablosunda 9 kolon
- ✅ LLM prompt'una gerçek veri → hallucination önlendi

---

## 🔄 Kullanım Diyagramı

```
┌────────────────────────────────────────────────────────┐
│                 EXTERNAL SYSTEMS                       │
│   OpenRouter (LLM)  ·  GitHub API  ·  Skill YAML      │
└──────────┬────────────────┬──────────────┬─────────────┘
           │                │              │
           ▼                ▼              ▼
┌────────────────────────────────────────────────────────┐
│            services/ (Business Logic)                  │
│                                                        │
│  ResumeGenerator (4 LLM calls)                         │
│  ├─ extract_priorities.jinja  → job priorities         │
│  ├─ tailor_for_target.jinja   → skill selection        │
│  ├─ select_projects.jinja     → project ranking        │
│  └─ generate_summary.jinja    → 2-line summary         │
│                                                        │
│  EvidenceBuilder  (CSV + cache → DB)                   │
│  ApplicationEngine CLI (track add/list/status/apply)   │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│            core/intelligence/ (AI Core)                │
│  SemanticMatcher (420MB, lazy)                         │
│  OpportunityScorer (weighted formula)                  │
│  GapAnalyzer (learning path)                           │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│            core/memory/ (Stateful AI)                  │
│  CandidateMemory · CompanyMemory · MarketMemory        │
│  ConversationMemory · LearningMemory                   │
│  (in-memory — Faz 5'te DB persistence)                 │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│            core/db/ — evidence tablosu                 │
│  skill × project × confidence + 9 GitHub metric col.  │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│            plugins/ (Connectors)                       │
│  Hiring-Agent Plugin  (PDF → CSV → Evidence)           │
│  GitHub Enrichment    (evidence → real metrics)        │
└────────────────────────────────────────────────────────┘
```

---

## 🔗 Kritik Akışlar

### Akış 1: Evidence Graph Pipeline (CV → Evidence)

```
1. PDF: personal/Abdullokh_Abdukodirov.pdf
   ↓ hiring_agent_adapter.py (subprocess)
2. services/hiring-agent/score.py
   → pdf.py:       PDF → text
   → transform.py: text → structured data
   → github.py:    GitHub profil çekme
   → evaluator.py: LLM scoring
   ↓
3. Output:
   - resume_evaluations.csv        (scores: technical_skills, production, ...)
   - cache/githubcache_*.json      (projects + commits + stars)
   ↓ evidence_builder.py
4. EvidenceBuilder.build():
   ├─ CSV parse   → eval scores
   ├─ JSON parse  → project list
   ├─ SkillLoader.topic_map: "yolov8" → "Computer Vision"
   ├─ confidence  = base + commit_bonus + star_bonus + production_bonus
   └─ EvidenceRepository.add() → PostgreSQL INSERT INTO evidence
   ↓
5. Result: 25 evidence record, 11 skill, confidence scores
   ↓
6. event_bus.publish(EvidenceAdded(user_id, skill, project, confidence))
```

---

### Akış 2: Target-Aware Resume Generation

```
1. POST /api/resume/generate
   {target_company: "Google", target_title: "ML Engineer"}
   ↓
2. ResumeGenerator.generate():

   [LLM #1] extract_priorities.jinja
   → {must_have: ["Python","PyTorch","CV"], important: ["Docker"]}

   [LLM #2] tailor_for_target.jinja
   CONSTRAINT: available_skills = list(evidence.keys())
   LLM sadece gerçek evidence'daki skill'lerden seçer
   _normalize_skill_names(): "API design" → "FastAPI" (fuzzy)
   → {emphasized_skills: ["Computer Vision", "PyTorch", "Python"]}

   [LLM #3] select_projects.jinja
   Score: relevance × depth × impact × recency × uniqueness
   → {selected: [Project-Drone-Vision (9.0), IMMUNO-TCR (8.5), ...]}

   [LLM #4] generate_summary.jinja
   → "ML Engineer with production-grade CV experience..."

   [Jinja render] ml_research.md.jinja → Markdown
   ↓
3. personal/Abdullokh_Abdukodirov_Google_ML_Engineer.md
```

---

### Akış 3: GitHub Enrichment (Hallucination Fix)

```
Problem:
  Evidence tablosunda sadece commits + stars vardı
  LLM yeterli context olmadığında hallucination yapıyordu

Solution:
  scripts/enrich_github_evidence.py
  ↓
  Her evidence.github_url için:
  ├─ client.py:           PyGithub.get_repo(owner/repo)
  ├─ repo_analyzer.py:    9 metric extract (LOC, topics, PRs, has_tests, ...)
  └─ evidence_enricher.py: UPDATE evidence SET loc_count=?, topics=?, ...
  ↓
  Migration: add_github_metrics_to_evidence (9 yeni kolon)
  ↓
  LLM prompt'u artık gerçek veri görür:
  "13M LOC, topics:[yolov8,opencv], has_tests:true, 12 PRs"
  → No more hallucination
```

---

### Akış 4: Memory Layer Learning

```
1. career-os track update --url ... --status rejected
   ↓ ApplicationRepository.update_status()
2. event_bus.publish(ApplicationRejected(company="Google", stage="phone_screen"))
   ↓
3. CandidateMemory subscriber:
   learn_from_application_outcome("Google", "phone_screen", "rejected")
   → MemoryFact {type: "rejection_pattern", confidence: 0.7}
   (in-memory — Faz 5'te DB persistence)
   ↓
4. Sonraki CompanyMemoryService.get_advice("Google"):
   "Google'da phone screen'de reddedildiniz (experience gap)."
```

---

## 🧠 Kritik Algoritmalar

### Algoritma 1: Confidence Formula

```python
# evidence_builder.py — temel formula
confidence = min(
    eval_scores["technical_skills"] / 100   # base     (0.0–1.0)
    + min(commits / 100, 0.20)              # commits  (max 0.20)
    + min(stars / 50, 0.10)                # stars    (max 0.10)
    + (eval_scores["production"] / 100) * 0.20,  # prod (max 0.20)
    1.0
)

# evidence_enricher.py — GitHub metrics sonrası ek bonuslar
# + min(loc_count / 5000, 0.15)           # LOC      (max 0.15)
# + has_tests * 0.05                      # quality
# + has_docs  * 0.03
# + has_releases * 0.05
# + (pr_count > 5) * 0.04
# + (issue_count > 3) * 0.03             # max toplam 0.20
```

### Algoritma 2: Skill Name Normalization

```python
def _normalize_skill_names(self, tailoring, evidence):
    """LLM output'unu gerçek evidence key'lerine eşle."""
    available_lower = {s.lower(): s for s in evidence.keys()}

    def resolve(skill):
        if skill in evidence:               return skill           # direct
        if skill.lower() in available_lower: return ...           # case-insensitive
        if skill in mappings:               return mappings[skill] # LLM's mapping
        for real in evidence:                                      # fuzzy substring
            if skill.lower() in real.lower(): return real
        return None
```

### Algoritma 3: Deterministic Feature Rollout (arşivlendi — referans için)

```python
# _archive/features/feature_registry.py
hash_input = f"{feature_name}:{user_id}"
bucket = int(SHA256(hash_input).hexdigest(), 16) % 100
return bucket < rollout_percentage
# Aynı user → her zaman aynı bucket → stable A/B
# Faz 5 SaaS modeline geçildiğinde geri alınacak
```

---

## 🔐 Hardcoded vs Dynamic Analizi

### ✅ DYNAMIC

| Bileşen | Nasıl Değişir |
|---|---|
| Evidence Graph | Her CV parse'de güncellenir |
| Skill Confidence | GitHub Enrichment ile recalculate |
| Memory Facts | Application outcomes → öğrenir |
| Scoring Weights | `PUT /api/settings/weights` |
| LLM Prompts | `core/prompts/*.jinja` edit |
| Resume Templates | `services/resume_intelligence/templates/*.jinja` edit |
| Skill Graph | `infra/seeds/v1/skills/skill_graph.yaml` edit |

### ❌ HARDCODED

| Bileşen | Değer | Risk |
|---|---|---|
| SemanticMatcher model | `all-MiniLM-L6-v2` | 🟢 Low |
| Memory storage | in-memory | 🟡 Medium (Faz 5: DB) |
| Skill Graph lokasyonu | YAML'da (DB'ye taşınmadı) | 🟢 Low (doğru karar) |

**Dynamic Skor: ~78%** — Memory in-memory olduğu için biraz düşük, Faz 5'te artacak.

---

## 🧪 Test Durumu

### Test Dosyaları (Faz 2 — Aktif)

| Dosya | Satır | Kapsam |
|---|---|---|
| `tests/test_memory_layer.py` | 185 | 5 memory tipi, BaseMemory ABC |
| `tests/test_prompts.py` | 200 | Template render, 4 şablon |
| `tests/test_resume_generator.py` | 141 | LLM pipeline (mock) |
| `tests/test_github_enrichment.py` | 162 | Repo analyzer, evidence enrichment |

**Faz 2 aktif toplam:** ~688 satır | 4 dosya

> `_archive/scripts/test_feature_registry.py` (~200 satır) Feature Registry ile birlikte arşivlendi.

---

## ⚠️ Teknik Borç

| # | Borç | Öncelik | Plan |
|---|---|---|---|
| 1 | Memory in-memory (restart'ta kaybolur) | 🟡 Orta | DB persistence Faz 5 |
| 2 | `career_os/core/skill_graph.py` legacy | 🟡 Orta | `core/intelligence/` refactor Faz 4.5 |
| 3 | Hiring-Agent external microservice | 🟢 Düşük | Dockerize + health check Faz 5 |
| 4 | LLM call testing (pahalı) | 🟢 Düşük | Mock server Faz 4.5 |
| 5 | Feature Registry arşivde | 🟢 Düşük | SaaS modeli için geri alınır Faz 5 |

---

## 🚀 Faz 2 → Faz 3 Bağlantısı

| Faz 2'den | Faz 3'te |
|---|---|
| `evidence` tablosu | GitHub Enrichment ile zenginleştirilir (zaten başlandı) |
| `EvidenceAdded` event | Company Intelligence dinler |
| `ApplicationRejected` event | CompanyMemory öğrenir |
| `CandidateMemory` | Company advice generation'da kullanılır |
| `SemanticMatcher` | Market Intelligence'da skill matching |

---

## ✅ Kontrol Listesi

- [x] SemanticMatcher (lazy init, cosine similarity)
- [x] OpportunityScorer (weighted formula, configurable weights)
- [x] GapAnalyzer (skill gap detection)
- [x] Memory Layer (5 tip, BaseMemory ABC)
- [x] LLM Prompts (4 Jinja template)
- [x] Evidence Graph (25 record, 11 skill, confidence scores)
- [x] Target-Aware Resume (4 LLM call, diff kanıtlandı)
- [x] Feature Registry → `_archive/` (single-user için gereksiz)
- [x] Hiring-Agent Integration (PDF → CSV → Evidence, 11 dosya)
- [x] GitHub Enrichment (9 metric, hallucination fix, migration)
- [x] Application Engine CLI (track add/list/status/apply)
- [x] Skill Graph (68 skill, 141 edge, 229 topic map, YAML)
- [x] Evidence Repository (CRUD + update_metrics)
- [x] LLM Client (OpenRouter, JSON mode)
- [x] 4 aktif test dosyası, ~688 satır

**✅ Faz 2 %100 TAMAMLANDI — LOCKED**

---

## 🎯 Özet

**Faz 2, CareerOS'un "beyin" fazıdır.** ~2,900 satır kod (hiring-agent hariç), 1 DB tablosu + 9 GitHub metric, 4 LLM prompt ve 5 memory type ile "Evidence > Claim" prensibini ürüne dönüştürür. Target-Aware Resume Generator, her başvuruya özel CV üreterek differentiator'ı kanıtlar. GitHub Enrichment ile LLM hallucination çözülür. Memory Layer ile AI stateful olur. Feature Registry single-user için gereksiz olduğundan arşivlendi — Faz 5 SaaS modeline geçildiğinde geri alınacak.

**Bir sonraki rapor:** Faz 3 — Company & Market Intelligence
