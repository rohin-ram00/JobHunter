# JobHunter

Shared job crawler for Rohin and Bhakti.

The repository keeps the crawler code and shared company database in one place, while each person keeps their own keywords, locations, seen jobs, and output files under `users/`.

## Repository Layout

```text
JobHunter/
├── data/
│   └── JobDataBank.ods          # shared company database
├── crawlers/                    # portal-specific handlers
├── utils/                       # shared scoring, filtering, storage helpers
├── users/
│   ├── Rohin/
│   │   ├── keywords.txt         # Rohin keyword weights
│   │   ├── locations.txt        # Rohin location preferences
│   │   ├── seen_jobs.json       # Rohin local run history
│   │   └── outputs/             # Rohin generated results
│   └── Bhakti/
│       ├── keywords.txt
│       ├── locations.txt
│       ├── seen_jobs.json
│       └── outputs/
├── ParallelCrawler.py           # recommended crawler entry point
├── Crawler.py                   # older crawler entry point
└── requirements.txt
```

## First-Time Setup

Install Python 3.12 or newer, then run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m playwright install chromium
```

## Daily Workflow

Pull the newest crawler code and shared company database:

```powershell
git pull origin main
```

Run for Rohin:

```powershell
.\scripts\run_user.ps1 -User Rohin
```

Run for Bhakti:

```powershell
.\scripts\run_user.ps1 -User Bhakti
```

You can also run directly:

```powershell
python .\ParallelCrawler.py --user Rohin --concurrency 5 --min-score 45
python .\ParallelCrawler.py --user Bhakti --concurrency 5 --min-score 45
```

Results are written to:

```text
users/<User>/outputs/JobMatches.xlsx
users/<User>/outputs/matches.txt
users/<User>/outputs/PotentialJobs.xlsx
users/<User>/outputs/potential_jobs.txt
```

## Editing Preferences

Add keywords as weighted lines:

```text
CFD|30
Simulation|25
OpenFOAM|20
```

Add locations one per line:

```text
Germany
Netherlands
Austria
```

Higher keyword weights increase a job's score. The crawler saves matches when the score is at least `--min-score`.

## Sharing Rules

Commit and push shared changes:

```powershell
git add data crawlers utils ParallelCrawler.py README.md requirements.txt
git commit -m "Update crawler and company database"
git push origin main
```

Generated outputs and `seen_jobs.json` are ignored by Git by default, so each person can run the crawler without overwriting the other's local history. If you intentionally want to share result files, remove the matching ignore rule from `.gitignore`.

## GitHub Remote

Recommended repository name:

```text
JobHunter
```

Recommended remote:

```text
https://github.com/rohin-ram00/JobHunter.git
```
