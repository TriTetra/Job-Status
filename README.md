# ApplyPilot + Career OS

A job search workflow built from two layers: ApplyPilot, an external job-discovery
CLI, and Career OS, a strategic scoring engine built on top of it in this repository.

## How the two systems relate

**ApplyPilot** (`pip install applypilot`, v0.3.0) is a third-party tool, not source
code in this repo. It is installed into `venv/` and does the actual work of finding
and scoring jobs:

- Scrapes LinkedIn, Indeed, and Glassdoor for postings matching the queries in
  `~/.applypilot/searches.yaml` (created by `applypilot init`, not tracked in
  this repo)
- Scores each posting 1-10 with an LLM (GPT-4o-mini by default, configurable in
  `~/.applypilot/.env`)
- Stores everything in a local SQLite database at `~/.applypilot/applypilot.db`

**Career OS** (`career_os/`) is the code that lives in this repository. It reads
ApplyPilot's database and re-ranks the results against a personal skill profile,
estimates the probability of getting hired, and produces a prioritized list of
which jobs to apply to and which skills to learn next.

**Everything in `scripts/`** is glue code connecting the two: filtering ApplyPilot's
raw output, exporting it to Excel, generating cold emails, and so on.

## Quick start

### Run a scan

```bash
run_scan.bat
# or, equivalently:
python scripts/scan/run_full_scan.py
```

This calls the ApplyPilot CLI to discover and score jobs, applies the filters in
`scripts/scan/filter_jobs.py`, and writes an Excel report to `reports/<date>/`.

### Generate an application strategy

```bash
python scripts/strategy/apply_strategy.py
```

This loads ApplyPilot's results into Career OS, scores them against the profile
defined in `career_os/data/applypilot_loader.py`, and writes five files to
`career_os_output/`:

| File | Contents |
|---|---|
| `apply_today_*.txt` | Top 10 jobs by career score |
| `apply_this_week_*.txt` | Top 20 jobs by career score |
| `prioritized_applications_*.txt` | Top 15, diversified across company size |
| `learning_plan_*.txt` | An 8-week skill roadmap, ordered by ROI |
| `summary_*.txt` | Aggregate statistics for the run |

Full walkthrough: [docs/usage/APPLY_NOW.md](docs/usage/APPLY_NOW.md).

### Or skip the analysis layer

Open the Excel report directly, go to the "Perfect Match (8+)" sheet, and apply
from there. Career OS adds a second opinion on top of ApplyPilot's scores; it is
not required to use the system.

## What each layer actually does

For the operational detail behind this section - exact filter rules, Excel
column layout, customization steps - see [docs/SYSTEM_SUMMARY.md](docs/SYSTEM_SUMMARY.md).

### ApplyPilot

- Searches across the queries defined in `~/.applypilot/searches.yaml`
  (created and edited via `applypilot init`; covers ML/AI, backend, and
  full-stack categories across three priority tiers, in English and Turkish)
- Scores postings 1-10 against the profile and resume in `~/.applypilot/`
- `scripts/scan/filter_jobs.py` removes postings that don't fit the target profile
  using 8 rules: seniority (Senior/Lead/Principal/Staff/Director), standalone
  frontend roles, freelance/contract, internships, standalone JavaScript roles,
  Analytics Engineer roles, onsite-only postings, and roles requiring 4+ years
- `scripts/scan/export_to_excel_advanced.py` writes a 6-sheet, 18-column workbook
  (executive summary, perfect matches, good matches, skills analysis, by-company,
  full database)

### Career OS

Implemented in `career_os/`, this layer adds a second scoring pass that ApplyPilot
itself doesn't do:

- **Skill model** (`career_os/models/skill.py`): six proficiency levels (L0
  Unknown through L5 Expert), each adjusted by an "AI multiplier" representing how
  much of that skill's output depends on AI assistance versus independent work
- **Transfer learning graph** (`career_os/core/skill_graph.py`): a graph of 68
  skills connected by 74 weighted relationships (e.g. Python to FastAPI transfers
  at 0.8), used to discount the learning cost of a new skill based on what's
  already known
- **Semantic matcher** (`career_os/intelligence/semantic_matcher.py`): scores a
  job against a profile across five weighted components - technical skills (40%),
  domain experience via sentence-embedding similarity (25%), seniority match
  (20%), work-mode match (10%), and an AI-capability bonus (5%)
- **Opportunity scorer** (`career_os/intelligence/opportunity_scorer.py`):
  estimates acceptance probability from company tier (big tech multiplies the
  baseline by 0.25, startups by 1.2), experience gap, remote/visa fit, and
  estimated competition; combines fit (30%), acceptance (25%), career value
  (25%), and market demand (20%) into a single career score
- **Gap analyzer** (`career_os/intelligence/gap_analyzer.py`): ranks missing
  skills by ROI (career impact per hour of learning, after the transfer-learning
  discount) and assembles them into an 8-week roadmap

These weights and thresholds are heuristics chosen by hand, not learned from data
- there is no feedback loop from real application outcomes yet (see "What's not
verified" below).

## Directory layout

```
applypilot-jobs/
├── scripts/              ApplyPilot orchestration and export tooling
│   ├── scan/               run_full_scan.py, filter_jobs.py, export_to_excel_advanced.py, schedule_info.py
│   ├── strategy/           apply_strategy.py, cold_email_generator.py, skills_gap_analyzer.py, extract_requirements.py
│   ├── tracking/           track_applications.py, sync_to_github.py
│   └── packaging/          setup_package.py
├── career_os/            The local scoring engine (models, core, intelligence, data)
├── tests/                Manual verification scripts for career_os
├── docs/                 All other documentation
│   ├── setup/              Installation and automation guides
│   ├── usage/              Day-to-day usage of apply_strategy.py and the Excel output
│   ├── tracking/           JOB_APPLICATIONS.md and the 8-week tracker (live data)
│   └── strategy/           The job-search plan itself, not tool-related
├── personal/             CV files (gitignored, not tracked)
├── reports/              Dated Excel exports from each scan - the canonical output location
├── logs/, backups/       Scan logs and database backups
├── run_scan.bat          Entry point for a full ApplyPilot scan
├── config.yaml.example   Template for config.yaml (Career OS profile - see docs/setup/QUICK_START.md)
└── config.yaml           Career OS profile, gitignored (copy from config.yaml.example)
```

ApplyPilot's own configuration (`searches.yaml`, `profile.json`, `resume.txt`,
`.env`) lives entirely in `~/.applypilot/`, created by `applypilot init` - none
of it is kept in this repo.
```

## What's not verified

The Career OS scoring weights and acceptance-probability formula are reasoned
heuristics, grounded in the code linked above - they have not been validated
against actual interview or offer outcomes, because no applications had been
sent at the time this was written (`docs/tracking/JOB_APPLICATIONS.md` shows zero). Any
claim about real-world accuracy or response-rate improvement should be treated
as a hypothesis the system is designed to test, not a measured result.

The numbers that *are* measured come from the one scan logged in
[CHANGELOG.md](CHANGELOG.md): 562 jobs discovered, 30 scored 8+, 121 scored 7,
for about $0.73 in LLM cost.

## Documentation

Full index, organized by setup / usage / tracking / strategy: [docs/README.md](docs/README.md).

Most likely starting points:

- [docs/setup/QUICK_START.md](docs/setup/QUICK_START.md) - first-scan setup
- [docs/usage/APPLY_NOW.md](docs/usage/APPLY_NOW.md) - the apply_strategy.py workflow, step by step
- [docs/SYSTEM_SUMMARY.md](docs/SYSTEM_SUMMARY.md) - full ApplyPilot architecture
- [career_os/README.md](career_os/README.md) - Career OS architecture in detail

## License

Private use only.
