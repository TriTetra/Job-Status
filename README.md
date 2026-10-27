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

One Python package, **one folder per feature**. Each feature owns its models,
repositories and services; `apps/` only translates HTTP / CLI into calls to it.

```
 apps/api (FastAPI, HTTP only)        apps/cli (Typer: career-os)         apps/web (Next.js)
          │                                   │
          └─────────────────┬─────────────────┘
                            ▼
 careeros/
   identity · onboarding · evidence · jobs · applications · companies · market · resume · knowledge
                            │
                            ▼
   shared (config, LLM, logging, background jobs, crypto)        db (Base, connection, migrations)
```

Rules enforced by `tests/smoke/test_architecture.py`: config only via `careeros.shared.config`,
LLM only via `careeros.shared.llm`, routers never query the DB, domain modules never import the
DB layer, `careeros` never imports `apps`, library code logs instead of printing.

---

## Quickstart

**Prerequisites:** Python 3.11+, Docker, an OpenRouter API key, a GitHub token (`public_repo` scope).

```bash
# 1. Start PostgreSQL
docker compose -f infra/docker/docker-compose.yml up -d

# 2. Install dependencies + the project itself (editable), apply migrations
pip install -r requirements-dev.txt
pip install -e .            # makes careeros + apps importable everywhere
alembic -c careeros/db/alembic.ini upgrade head

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

All proof lives in one table, `evidence_items`, written by three sources in `careeros/evidence/`:
your GitHub repos (OAuth — languages, stars, topics, `has_tests` / `has_docs` / `has_releases`),
your uploaded CV (PDF → LLM extraction of skills, experience, projects, achievements) and your
portfolio site. `aggregation.py` weighs sources (GitHub > portfolio > CV) into one confidence per skill.

```python
# aggregated skill confidence
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
| GitHub evidence | GitHub REST API (user's OAuth token) |
| Market signals | Algolia HN API + feedparser |
| CV parsing | PyMuPDF → LLM structured extraction |

---

## Project Layout

```
applypilot-jobs/
├── apps/
│   ├── api/              FastAPI — routers (HTTP only), schemas, auth dependency
│   ├── cli/              Typer app (`career-os`)
│   └── web/              Next.js 16 dashboard
├── careeros/
│   ├── shared/           config (.env → Settings), LLM client, logging, background jobs, token crypto
│   ├── db/               Base, connection, model registry, Alembic migrations, legacy tables
│   ├── identity/         users, roles, preferences, GitHub account linking
│   ├── onboarding/       sign-up wizard → Career Graph
│   ├── evidence/         evidence_items from GitHub, CV (PDF+LLM), portfolio; aggregation
│   ├── jobs/             sources (ApplyPilot), scoring, decisions, scan, opportunities
│   ├── applications/     application pipeline (+ CLI)
│   ├── companies/        company profiles, interview memory (+ CLI)
│   ├── market/           HN + TechCrunch signals, refresh job (+ CLI)
│   ├── resume/           target-aware resume generation, prompts, templates (+ CLI)
│   └── knowledge/        countries, visas, salaries, skill graph loader
├── infra/                docker-compose, plugin config, YAML seeds
├── scripts/              seed / backfill / sync operations
├── tests/                unit/ · smoke/ (offline) · integration/ (live) · manual/
└── config.yaml.example   candidate profile template
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
