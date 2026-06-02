# Contributing

## Before You Start

```powershell
git pull origin main
```

## What Belongs In Git

Commit:

- crawler improvements
- new portal handlers in `crawlers/`
- shared helper code in `utils/`
- updates to `data/JobDataBank.ods`
- keyword/location preference changes you both want shared

Do not commit:

- generated files in `users/*/outputs/`
- personal `seen_jobs.json` files
- virtual environments
- Python cache files

## Suggested Branches

Use small feature branches for larger changes:

```powershell
git checkout -b codex/workday-handler
git push -u origin codex/workday-handler
```

Then open a pull request on GitHub and merge into `main`.
