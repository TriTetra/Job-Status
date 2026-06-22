# Career OS

AI-powered career intelligence platform with semantic job matching and skill gap analysis.

## Architecture

```
career_os/
├── models/              # Data models
│   ├── skill.py         # AI-adjusted skill proficiency
│   └── profile.py       # User profiles, jobs, match results
├── core/                # Core algorithms
│   └── skill_graph.py   # Transfer learning graph
└── intelligence/        # Intelligence modules
    ├── semantic_matcher.py   # Multi-aspect job matching
    └── gap_analyzer.py       # ROI-optimized gap analysis
```

## Features

### 1. AI-Adjusted Skill Levels

Traditional systems treat all skills as binary (have/don't have).

Career OS uses 6 proficiency levels with AI usage awareness:

- **L0 UNKNOWN**: No experience
- **L1 AI_ASSISTED**: Can use with AI help (Cursor, Claude, GPT)
- **L2 WORKING**: Small-medium tasks independently
- **L3 INDEPENDENT**: Self-sufficient with documentation
- **L4 ADVANCED**: Architecture, optimization
- **L5 EXPERT**: Teaching level

Each skill has an `ai_multiplier` (0-1) representing AI dependency.

**Effective level** = `proficiency × ai_multiplier`

Example:
```python
Skill("Python", L3, ai_multiplier=0.8)
# Effective: 2.4/5.0
```

### 2. Transfer Learning

Skill graph models relationships between 200+ skills.

Transfer coefficients (0-1):
- 0.9: React → Next.js (almost identical)
- 0.8: Python → FastAPI (strong transfer)
- 0.4: Python → Go (moderate transfer)
- 0.0: Python → Photoshop (no transfer)

**Learning cost discount**:
- Knowing Python L3 → FastAPI costs 36% less (14h vs 40h)
- Knowing Docker L2 → Kubernetes costs 28% less

### 3. Semantic Job Matching

Multi-aspect matching beyond keyword search:

**Components** (weighted):
1. **Technical Skills** (40%): Level-aware + transfer learning
2. **Domain Experience** (25%): Semantic similarity via embeddings
3. **Seniority Level** (20%): Years + responsibilities
4. **Work Mode** (10%): Remote/hybrid/onsite preferences
5. **AI Capability** (5%): Bonus for AI-native roles

**Output**:
- Overall score (0-100)
- Component breakdown
- Skill gaps identified
- Confidence level
- Human-readable explanation

### 4. ROI-Optimized Gap Analysis

Not just "what skills are missing" but "what should I learn first".

For each gap:
- **Learning cost**: Hours needed (with transfer discount)
- **Impact score**: Career value (jobs unlocked, salary, demand)
- **ROI**: Impact per hour

**Example**:
```
AWS:  ROI 2.5 = 50 impact / 20 hours
Rust: ROI 0.4 = 20 impact / 50 hours
→ Learn AWS first
```

### 5. Learning Roadmaps

Automated 8-week plans with:
- Topological ordering (prerequisites first)
- Resource recommendations
- Validation projects
- Expected fit improvement

## Usage

### Semantic Matching

```python
from career_os.models import UserProfile, Job, Skill, SkillLevel
from career_os.intelligence import SemanticMatcher

# Create profile
profile = UserProfile(
    name="User",
    years_experience=2.0,
    ai_proficiency=0.8,
    skills=[
        Skill("Python", SkillLevel.INDEPENDENT, ai_multiplier=0.8),
        Skill("PyTorch", SkillLevel.WORKING, ai_multiplier=0.7),
    ]
)

# Match job
matcher = SemanticMatcher()
result = matcher.match(profile, job)

print(f"Score: {result.overall_score:.1f}/100")
print(f"Missing: {result.skill_gaps}")
```

### Gap Analysis

```python
from career_os.intelligence import GapAnalyzer

analyzer = GapAnalyzer()

# Analyze gaps
gaps = analyzer.analyze(profile, target_jobs)

for gap in gaps[:5]:  # Top 5 by ROI
    print(f"{gap.skill}: {gap.roi:.2f} ROI, {gap.learning_cost_hours}h")

# Generate roadmap
roadmap = analyzer.create_roadmap(gaps, hours_per_week=10, max_weeks=8)
print(roadmap.summary())
```

## Tests

```bash
# Core foundation
python test_career_os.py

# Day 2: Semantic matching + gap analysis
python test_day2.py
```

## Requirements

```
sentence-transformers
scikit-learn
networkx
numpy
```

## Performance

- Semantic matching: ~100ms per job
- Gap analysis: ~50ms for 50 skills
- Model size: 80MB (MiniLM) or 420MB (mpnet)

## Roadmap

**Day 1**: ✓ Core foundation
**Day 2**: ✓ Semantic matcher + gap analyzer
**Day 3**: Opportunity scorer + market intelligence
**Day 4**: Integration + real data

## Why This Matters

Traditional job search tools:
- Keyword matching (miss semantic relevance)
- Binary skills (have/don't have)
- No learning guidance
- No ROI optimization

Career OS:
- Semantic understanding (context-aware)
- Proficiency levels (nuanced matching)
- Automated learning plans (actionable)
- ROI-driven prioritization (efficient)

**Result**: Higher quality matches, faster skill development, better career decisions.
