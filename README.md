# ApplyPilot Job Search System

Automated job discovery and application tracking for ML/AI positions.

## Quick Start

```bash
# Run job scan
run_scan.bat

# Generate cold emails
python scripts/cold_email_generator.py

# Analyze skills gap
python scripts/skills_gap_analyzer.py
```

## Features

- **Automated Discovery**: Searches LinkedIn, Indeed, Glassdoor
- **AI Scoring**: GPT-4o-mini rates jobs 1-10
- **Smart Filtering**: Removes senior, freelance, mismatched positions
- **Excel Reports**: 6 sheets with 18 columns per job
- **Cold Email Generator**: Creates personalized outreach emails
- **Skills Analysis**: Identifies missing skills and learning priorities

## System Overview

```
Discover → Score → Filter → Excel → Track → Apply
```

**Input**: 27 search queries × 3 job boards  
**Output**: ~180 quality jobs, scored and filtered  
**Time**: 25 minutes per scan  
**Cost**: ~$0.75 per scan  

## Directory Structure

```
applypilot-jobs/
├── scripts/               # Automation scripts
├── reports/               # Scan results by date
├── docs/                  # Documentation
├── logs/                  # Run history
├── backups/               # Database backups
├── run_scan.bat           # Main entry point
├── README.md              # This file
├── JOB_APPLICATIONS.md    # Application tracker
└── CHANGELOG.md           # Scan history
```

## Workflow

### Every 3 Days

1. Run scan: `run_scan.bat`
2. Review Excel in `reports/latest/`
3. Apply to jobs via Apply Link column
4. Update Notes column with application status

### Application Strategy

**Standard approach** (2-5% response rate):
- Apply via job board
- Wait for response

**Enhanced approach** (15-25% response rate):
- Apply via job board
- Send cold email to hiring manager
- Connect on LinkedIn
- Follow up after 7, 14, 21 days

## Scripts

| Script | Purpose |
|--------|---------|
| `run_full_scan.py` | Main scanner (discover→score→filter→export) |
| `cold_email_generator.py` | Generate personalized outreach emails |
| `skills_gap_analyzer.py` | Analyze missing skills, create learning plan |
| `filter_jobs.py` | Apply 8 automatic filters |
| `export_to_excel_advanced.py` | Create detailed Excel reports |
| `track_applications.py` | Update application tracker |

## Configuration

Main config files (in `~/.applypilot/`):
- `searches.yaml` - Search queries and filters
- `config.yaml` - Your profile and preferences
- `.env` - API keys (OpenRouter/OpenAI)

## Documentation

- [Quick Start](docs/QUICK_START.md) - Get started in 5 minutes
- [Application Tracker](docs/APPLICATION_TRACKER.md) - Track your applications
- [2-Month Action Plan](docs/guides/2_MONTH_ACTION_PLAN.md) - Detailed strategy
- [GitHub Integration](docs/guides/GITHUB_GUIDE.md) - Push code, track with Issues
- [Windows Scheduler](docs/guides/WINDOWS_SCHEDULER_GUIDE.md) - Automated scans
- [System Summary](docs/SYSTEM_SUMMARY.md) - Complete overview

## Results

**First scan (2026-06-22)**:
- 562 jobs discovered
- 181 quality matches after filtering
- 30 perfect matches (score 8+)
- 151 good matches (score 7)

**Filters applied**:
- Senior/Lead/Principal positions
- Standalone Frontend roles
- Freelance/Contract work
- 4+ years experience requirements
- Positions requiring security clearance

## Requirements

- Python 3.8+
- ApplyPilot CLI
- OpenRouter API key (or OpenAI)
- openpyxl library

## Support

- Issues: https://github.com/TriTetra/Job-Status/issues
- Email: abdullahabdulkadir0@gmail.com

## License

Private use only.
