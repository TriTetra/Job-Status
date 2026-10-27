<div align="center">

```
 ██████╗ █████╗ ██████╗ ███████╗███████╗██████╗      ██████╗ ███████╗
██╔════╝██╔══██╗██╔══██╗██╔════╝██╔════╝██╔══██╗    ██╔═══██╗██╔════╝
██║     ███████║██████╔╝█████╗  █████╗  ██████╔╝    ██║   ██║███████╗
██║     ██╔══██║██╔══██╗██╔══╝  ██╔══╝  ██╔══██╗    ██║   ██║╚════██║
╚██████╗██║  ██║██║  ██║███████╗███████╗██║  ██║    ╚██████╔╝███████║
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝     ╚═════╝ ╚══════╝
```

**Your career as infrastructure.**

[![Python](https://img.shields.io/badge/python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-private-lightgrey?style=flat-square)](./LICENSE)

</div>

---

CareerOS is a self-hosted career intelligence stack. It builds an evidence graph from your GitHub activity, scores job postings against it, generates resumes tailored to a specific company and role, tracks interview outcomes per company, and monitors market signals from Hacker News and TechCrunch — all from a single CLI backed by PostgreSQL.

No SaaS. No subscriptions. Your data stays local.

---

## What it looks like

```
$ career-os status

  Evidence Graph     68 skills · 229 topics · 25 projects
  Career Scores      562 jobs scored · avg 53.9/100
  Applications       4 in pipeline · 1 at phone screen
  Market Signals     42 signals · last scan Jul 2026

$ career-os strategy

  [1]  Anthropic          ML Engineer          91  ██████████  APPLY
  [2]  Cohere             Backend Engineer      87  ████████░░  APPLY
  [3]  Hugging Face       Research Engineer     84  ████████░░  APPLY
  [4]  Modal              Platform Engineer     79  ███████░░░  CONSIDER
  [5]  Mistral AI         AI Engineer           76  ███████░░░  CONSIDER

  Top skill gap:  distributed inference  (ROI: 2.4×, est. 40 hrs)
  Next:           open source commit to vllm or triton

$ career-os resume generate --company Anthropic --title "ML Engineer"

  [1/5]  Loading Evidence Graph + GitHub projects...
         34 skills · 8 projects
  [2/5]  Extracting job priorities (LLM)...
         must_have: [transformers, RLHF, distributed training, Python]
  [3/5]  Tailoring evidence for target (LLM)...
         emphasized: [PyTorch, Python, FastAPI, Rust, distributed-systems]
  [4/5]  Selecting best projects (LLM)...
         - IMMUNO-TCR: 9.2  ✓
         - Sentropy Engine: 8.7  ✓
         - YADIGAR: 8.1  ✓
  [5/5]  Generating 2-line summary (LLM)...

  Resume saved: personal/User_Anthropic_ML_Engineer.md (4,218 chars)
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  SOURCES                                                            │
│  ApplyPilot (job postings)  ·  GitHub API  ·  HN  ·  TechCrunch   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PLUGINS           plugins/                                         │
│  JobSourcePlugin → applypilot/                                      │
│  EnrichmentPlugin → github/ (9 metrics: LOC, PRs, has_tests …)     │
│  MarketPlugin     → hackernews/ · techcrunch/                       │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  SERVICES          services/                                        │
│  resume_intelligence   → Evidence Graph + 4-call LLM pipeline      │
│  company_intelligence  → tech stack enrichment + interview memory   │
│  market_intelligence   → signal extraction + trend queries          │
│  application_engine    → state machine (to_apply → offer/rejected)  │
│  hiring-agent          → PDF → GitHub enrichment → LLM scoring      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  CORE              core/                                            │
│  db/           SQLAlchemy + Alembic · 16 tables · BaseRepository[T] │
│  timeline/     track_snapshot() · auto-diff · detect_changes()      │
│  events/       thread-safe EventBus · 18 domain event types         │
│  prompts/      Jinja2 template loader · custom filters              │
│  knowledge/    Countries · Visas · Salary ranges (DB-backed)        │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
          ┌──────────────┐  ┌──────────────┐
          │  FastAPI     │  │  Typer CLI   │
          │  24 endpoints│  │  career-os   │
          │  apps/api/   │  │  apps/cli/   │
          └──────────────┘  └──────────────┘
```

---

## Quickstart

**Prerequisites:** Python 3.11+, Docker, an OpenRouter API key, a GitHub token (`public_repo` scope).

```bash
# 1. Start PostgreSQL
docker compose -f infra/docker/docker-compose.yml up -d

# 2. Install dependencies + the project itself (editable), apply migrations
pip install -r requirements-dev.txt
pip install -e .            # makes core/services/plugins/apps importable everywhere
alembic -c core/db/alembic.ini upgrade head

# 3. Configure
cp config.yaml.example config.yaml
# fill in: candidate.name, github, skills; set OPENROUTER_API_KEY in .env

# 4. Seed knowledge (countries, visas, salary ranges)
python scripts/seed_knowledge_from_yaml.py

# 5. Run
career-os status                                       # CLI
uvicorn apps.api.app.main:app --reload --port 8000     # API (from any directory)
pytest                                                 # offline tests; -m integration for live ones
```

> Your API key belongs in `.env`, never in `config.yaml`. Both files are gitignored.

---

## Core Concepts

### Evidence Graph

CareerOS builds a skill × project matrix from your GitHub activity. Every project gets 9 real metrics (LOC, PR count, `has_tests`, `has_docs`, language, topics …) pulled via the GitHub API. Confidence scores are computed from commits, stars, and code quality signals — not hallucinated.

```python
# evidence table: skill_name × project × confidence
Python      | Sentropy-Engine  | 0.91
PyTorch     | IMMUNO-TCR       | 0.87
FastAPI     | career-os        | 0.84
Rust        | Sentropy-Engine  | 0.79
```

When the LLM generates a resume section, it only sees skills that exist in this graph (`available_skills` constraint). It cannot invent skills you don't have evidence for.

### Target-Aware Resume

```
job description ──► extract priorities   (LLM call 1)
evidence graph  ──► tailor evidence      (LLM call 2)  ← available_skills constraint
github cache    ──► select projects      (LLM call 3)
candidate info  ──► generate summary     (LLM call 4)
                         │
                         ▼
               Jinja2 Markdown template → .md file
```

`_normalize_skill_names()` maps LLM output back to real evidence keys via exact match → lowercase → partial match → confidence fallback. The resume can't claim skills you don't have.

### Company Intelligence

Every company gets a living profile updated from job postings. Interview outcomes are stored per user — "rejected at phone screen, asked about Docker and Redis" — and queried for pattern-aware advice next time you apply.

```bash
career-os company show --name Google
# → tech stack, open positions, your interview history, recommendation
```

### Market Intelligence

```bash
career-os market signals --source hackernews --year 2026 --month 7
# → 272 postings parsed → 42 signals stored
#   skill_demand: [Python ↑12%, Rust ↑8%, Go ↑5% …]
#   hiring_spike: [Anthropic ×3, Modal ×2 …]
#   remote_pct:   67%
```

Signals are queryable period-over-period:

```bash
career-os market trend --skill rust
# → current: 31 · previous: 19 · change: +63% · direction: up
```

---

## CLI Reference

```
career-os
  version                    Print version
  status                     Evidence, scores, pipeline, market summary
  scan                       Run a full job discovery + scoring pass
  strategy                   Ranked opportunities + top skill gap

  track
    add --url --title --company --status
    update --url --status --notes
    list [--status]
    summary
    stale [--days]

  resume
    generate --company --title [--template] [--jd]
    templates

  company
    show --name
    enrich
    memory --name

  market
    signals --source [hackernews|techcrunch] --year --month
    trend --skill
    summary
```

---

## Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| API | FastAPI 0.115 + Pydantic v2 |
| CLI | Typer |
| Database | PostgreSQL 16 (Docker) |
| ORM / Migrations | SQLAlchemy 2 + Alembic |
| LLM | OpenRouter (`openai/gpt-4o-mini` default) |
| Templates | Jinja2 |
| GitHub enrichment | PyGithub |
| Market signals | Algolia HN API + feedparser |
| PDF scoring | PyMuPDF → hiring-agent pipeline |

---

## Project Layout

```
applypilot-jobs/
├── apps/
│   ├── api/              FastAPI app — 24 endpoints across 7 routers
│   └── cli/              career-os launcher + Typer app
├── services/
│   ├── resume_intelligence/   Evidence Graph → Target-Aware Resume
│   ├── company_intelligence/  Tech stack enrichment + company memory
│   ├── market_intelligence/   HN + TechCrunch signal scanning
│   ├── application_engine/    Application state machine
│   └── hiring-agent/          PDF → LLM scoring pipeline (~4,300 lines)
├── core/
│   ├── db/               Models, repositories, Alembic migrations
│   ├── timeline/         Snapshot tracking + auto-diff
│   ├── events/           Thread-safe EventBus (18 event types)
│   ├── prompts/          Jinja2 template loader
│   └── knowledge/        Country/visa/salary repositories
├── plugins/
│   ├── job_sources/      ApplyPilot SQLite adapter
│   ├── enrichment/       GitHub metrics (9 signals per repo)
│   └── market_signals/   HN + TechCrunch scrapers
├── infra/seeds/v1/       14 YAML files → DB seed (countries, visas, salaries)
├── tests/                14 test files
├── config.yaml.example   Profile template
└── docker-compose.yml    PostgreSQL 16 + Adminer
```

---

## Documentation

Architecture reports for each build phase live in [`docs/v1/phases/`](docs/v1/phases/):

- [Phase 1 — Foundation](docs/v1/phases/PHASE_1_REPORT.md) — DB layer, EventBus, Plugin system, FastAPI gateway
- [Phase 2 — Intelligence Core](docs/v1/phases/PHASE_2_REPORT.md) — Evidence Graph, Resume AI, Hiring-Agent, Skill Graph
- [Phase 3 — Company & Market](docs/v1/phases/PHASE_3_REPORT.md) — Company Intelligence, Market Intelligence, Timeline, Knowledge DB

Full doc index: [`docs/README.md`](docs/README.md)

---

<div align="center">
<sub>Built in phases. Evidence over claim. PostgreSQL over hype.</sub>
</div>
