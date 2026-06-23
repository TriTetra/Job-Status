# ApplyPilot Changelog

Every scan run and any configuration change is logged here.

## 2026-06-22 - Initial scan

### Summary

- First complete scan after setup
- 562 jobs discovered
- 30 scored 8+ ("perfect match")
- 121 scored 7 ("good match")

### Configuration

- LLM: GPT-4o-mini via OpenRouter
- Search queries: as configured in `searches.yaml` at the time
- Sites: LinkedIn, Indeed, Glassdoor
- Filters: the 8 rules in `scripts/scan/filter_jobs.py`

### Results

- Total LLM cost: ~$0.73
- Duration: ~30 minutes
- Perfect match rate: 5.3% (30/562)
- Combined 7+ match rate: 26.9% (151/562)

### Filters applied

1. Senior/Lead/Principal positions
2. Standalone frontend roles
3. Freelance/contract roles (16 filtered)
4. Internships (2 filtered)
5. Standalone JavaScript Developer roles
6. Analytics Engineer roles
7. Paris onsite roles
8. Roles requiring 4+ years experience (12 filtered)

### Files generated

- `reports/2026-06-22/applypilot_advanced_20260622_203154.xlsx`
- `backups/db_20260622_*.sqlite`
- `logs/2026-06-22.log`

## Template for future entries

```markdown
## YYYY-MM-DD - Scan #X

### Summary
- Jobs discovered:
- Perfect matches (8+):
- Good matches (7):

### Changes
- Config changes:
- New filters:
- Issues fixed:

### Results
- Top companies:
- Top locations:
- Salary range:

### Actions taken
- Applied to: X jobs
- Interviews:
- Offers:
```

Add a new entry at the top of this file after each scan.
