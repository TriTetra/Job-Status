# Career OS

A strategic scoring layer for job search, built on top of ApplyPilot's job
discovery data.

## What it does

ApplyPilot finds and scores jobs; Career OS takes those results and adds a
second pass of analysis: which jobs are realistically worth applying to, and
which skills are worth learning first. Concretely:

1. **Semantic job matching** — scores a job against a profile across five
   weighted dimensions, not just keyword overlap
2. **Acceptance probability** — a heuristic estimate of how likely an
   application is to succeed, based on company tier, experience gap, and
   competition
3. **ROI-ranked learning plan** — orders missing skills by career impact per
   hour of study, accounting for transfer learning from skills already known
4. **Application prioritization** — picks a diversified shortlist instead of
   ranking by raw fit score alone

## Architecture

```
career_os/
├── models/
│   ├── skill.py          Skill, SkillLevel (six proficiency tiers, AI multiplier)
│   └── profile.py        UserProfile, Job, Experience, UserPreferences
├── core/
│   └── skill_graph.py    Transfer-learning graph (68 skills, 74 weighted edges)
├── intelligence/
│   ├── semantic_matcher.py    Multi-aspect job matching (sentence-transformers)
│   ├── gap_analyzer.py        ROI-ranked skill gaps and learning roadmap
│   └── opportunity_scorer.py  Acceptance probability, career value, CareerDecisionEngine
└── data/
    └── applypilot_loader.py  Reads jobs out of ApplyPilot's SQLite database
```

`CareerDecisionEngine` — the orchestrator referenced throughout this document
and in `scripts/strategy/apply_strategy.py` — is defined inside `opportunity_scorer.py`
and re-exported through `intelligence/__init__.py`.

## Skill levels and the AI multiplier

Most skill self-assessments are binary: you know a tool, or you don't. Career
OS instead tracks two numbers per skill (`models/skill.py`):

**Six proficiency tiers** (`SkillLevel`, L0-L5): Unknown, AI-Assisted (can
produce output with Cursor/Claude/GPT but needs guidance), Working (handles
small-to-medium tasks independently), Independent (self-sufficient with
documentation), Advanced (architecture/optimization), Expert (teaching level).

**AI multiplier (0.0-1.0):** how much of that proficiency depends on AI
assistance versus independent capability. `effective_level()` returns
`level * ai_multiplier` — e.g. `Skill("Python", INDEPENDENT, ai_multiplier=0.8)`
has an effective level of 2.4/5.0, not 3.0.

The rationale: a hiring manager evaluating AI-era candidates cares about the
gap between "can produce this with tools" and "understands it independently."
This multiplier is self-reported, not measured — it is a structured way to be
honest about that gap, not a verified metric.

## Transfer learning graph

`core/skill_graph.py` is a directed graph (built with `networkx`) connecting
related skills with a transfer-learning weight: knowing Python at a given
level discounts the cost of learning FastAPI, because the underlying ability
transfers. As built today, the graph has **68 skill nodes and 74 weighted
edges** — for example Python to FastAPI at 0.8, Java to Spring Boot at 0.9,
Docker to Kubernetes at 0.7.

`SkillGraph.calculate_learning_discount()` multiplies these weights (scaled by
current proficiency in the known skill) into a discount factor capped at 0.3,
meaning a maximum 70% reduction in estimated learning hours. `GapAnalyzer`
uses this discount when estimating how long a new skill will actually take
given what's already known.

## Semantic matching

`intelligence/semantic_matcher.py` scores a job against a profile across five
fixed weights (`SemanticMatcher.match`):

| Component | Weight | Method |
|---|---|---|
| Technical skills | 40% | Level-aware exact match + transfer-learning partial credit |
| Domain experience | 25% | Cosine similarity between resume/experience text and job description embeddings |
| Seniority | 20% | Years of experience vs. required years, with decay for under-qualification |
| Work mode | 10% | Remote/hybrid/onsite preference match |
| AI capability | 5% | Bonus when the job description mentions AI tools and the candidate's AI proficiency is high |

These weights are fixed constants chosen by hand; they are not fit to any
labeled dataset of outcomes.

## Opportunity scoring

`intelligence/opportunity_scorer.py` answers "should I apply?" rather than
just "do I match?" `OpportunityScorer._estimate_acceptance()` starts from a
0.5 baseline and multiplies in:

- **Company tier:** big tech 0.25x, large 0.45x, midsize 0.7x, startup 1.2x,
  unknown 0.6x (`_build_company_tiers` recognizes Google, Meta, Amazon,
  Apple, Microsoft, Netflix, OpenAI, and Anthropic as big tech by name match)
- **Experience gap:** full credit between 0.8x-1.5x of required years, else
  exponential decay
- **Remote match:** 1.3x boost when both job and preference are remote
- **Visa sponsorship:** 0.4x penalty if sponsorship is required but not offered
- **Estimated competition:** remote, high-salary, and big-tech postings each
  reduce the probability further

`career_score` combines fit (30%), acceptance probability (25%), career value
(25%), and market demand (20%) into a single ranking number. None of this has
been checked against actual interview or offer outcomes — see "What's not
verified" below.

## ROI-optimized learning plan

`intelligence/gap_analyzer.py`'s `GapAnalyzer.analyze()` aggregates required
skills across target jobs, estimates the learning cost for each (base hours
per level, discounted by the transfer graph), scores impact (jobs unlocked,
salary signal, a small hardcoded list of high-demand skills), and ranks gaps
by `roi = impact / cost`. `create_roadmap()` then schedules the highest-ROI
gaps into an 8-week plan at a configurable hours-per-week pace, pulling
resource links and a validation project from small hand-curated dictionaries
inside the same file (currently covering AWS, Kubernetes, Docker, React,
PyTorch, FastAPI).

## Loading real data

`data/applypilot_loader.py` connects directly to ApplyPilot's SQLite database
at `~/.applypilot/applypilot.db` and converts rows into `Job` objects,
extracting skills and required years from the description text with simple
keyword and regex heuristics.

```python
from career_os.data import ApplyPilotLoader, create_user_profile_from_config
from career_os.intelligence import CareerDecisionEngine, SemanticMatcher, GapAnalyzer, OpportunityScorer

loader = ApplyPilotLoader()
jobs = loader.load_jobs(min_score=7, limit=50)
profile = create_user_profile_from_config()

matcher = SemanticMatcher(model_name='all-MiniLM-L6-v2')
analyzer = GapAnalyzer()
scorer = OpportunityScorer(matcher=matcher)
engine = CareerDecisionEngine(matcher, analyzer, scorer)

result = engine.analyze_opportunities(jobs, profile)
print(f"Apply now: {len(result['apply_now'])} jobs")
print(f"Top gap: {result['top_gaps'][0].skill} (ROI {result['top_gaps'][0].roi:.2f})")
```

`create_user_profile_from_config()` reads contact info, years of experience,
target roles, salary range, and remote/sponsorship preferences from the
project's `config.yaml` (copy `config.yaml.example` at the repo root to get
started - this file is unrelated to `applypilot init`'s own `~/.applypilot/`
files), and resume text from `personal/<Name>.txt` if it exists. Skill proficiency levels and AI multipliers aren't part of
`config.yaml`'s schema (it only stores skill names), so those still come from
a hand-assessed `_SKILL_PROFILES` dict in the same file; any skill listed in
`config.yaml` that isn't in that dict falls back to a conservative default
(`WORKING`, `ai_multiplier=0.6`).

## Usage

```bash
python tests/test_career_os.py      # core models
python tests/test_day2.py           # semantic matcher + gap analyzer
python tests/test_day3.py           # opportunity scorer + decision engine
python tests/test_production.py     # integration against the real ApplyPilot database
```

These are manual verification scripts run from the shell, not an automated
test suite (no pytest, no CI).

## Requirements

```
sentence-transformers   semantic embeddings (model: all-MiniLM-L6-v2 or all-mpnet-base-v2)
scikit-learn            cosine similarity
networkx                skill graph
numpy                   aggregate statistics
```

## What's not verified

The numbers in this document that describe **code behavior** — skill counts,
edge counts, component weights, multipliers, filter counts — are read directly
from the modules above and are accurate as of this writing.

The numbers that would describe **real-world results** — acceptance
probability matching actual outcomes, response-rate improvement over a
baseline, "accuracy" against ground truth — do not exist yet. No applications
had been logged in `docs/tracking/JOB_APPLICATIONS.md` at the time this was written, so
there is no outcome data to validate any of the scoring formulas against. Any
statement along those lines should be treated as the system's design intent,
not a measured result, until there's a track record to check it against.

## Development timeline

Built incrementally over four days, visible in the commit history: core
models and the skill graph (day 1), semantic matcher and gap analyzer
(day 2), opportunity scorer and decision engine (day 3), production
integration with real ApplyPilot data (day 4).

## License

Private use only.
