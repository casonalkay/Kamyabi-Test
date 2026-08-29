# Kamyabi Government Jobs Scraper — V1

TEST-ONLY automated collection of government-job vacancy/notification data from official portals. This repository does NOT connect to or modify Kamyabi.in.

## V1 sources

- UPSC
- SSC
- IBPS
- SBI Careers
- India Post
- Employment News

The scraper is intentionally source-adapter based. Each portal has its own scraper under `scrapers/`.

## Data flow

Official portal → scraper → PDF/text extraction → normalization → deduplication/change detection → `data/current/jobs.json` → daily history snapshot → Kamyabi.in

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Output

`data/current/jobs.json` is the primary dataset.

`data/history/YYYY-MM-DD.json` is a daily snapshot.

`data/last_run.json` contains source health and detected changes.

Every job includes:

- `job_id`
- organization
- title
- vacancies
- qualification
- age limit
- salary
- application dates
- official URL
- notification URL
- source
- first seen
- last seen
- last updated
- scrape date
- content hash

## Important V1 limitation

Government portals frequently change HTML, use JavaScript, or publish information only inside PDFs. V1 therefore uses a combination of HTML link discovery and PDF text extraction. Some fields may remain `null` until a source-specific parser is strengthened.

Do not treat a scraped record as authoritative unless the user follows the linked official notification. The official government notification remains the source of truth.

## TEST-ONLY SAFETY

This repository is intentionally isolated from `kamyabi.in`. No website code, API, database, DNS, deployment, or production credentials are used. The workflow only writes data inside this repository.

## GitHub Actions

`.github/workflows/daily_scraper.yml` runs once per day at 05:30 IST and commits changed data back to the repository.

It can also be started manually from the GitHub Actions UI.

## Kamyabi integration

For a first version, Kamyabi can read:

```text
https://raw.githubusercontent.com/<GITHUB_USER>/kamyabi-govt-jobs/main/data/current/jobs.json
```

Later, move the public delivery layer to a database/API if traffic grows.

## Recommended next iterations

1. Add RRB regional portals.
2. Add DRDO.
3. Add state PSCs.
4. Improve PDF field extraction.
5. Add OCR for scanned PDFs.
6. Add source health checks and alerting.
7. Add job-level change history.
8. Add an API/cache layer for Kamyabi.


## Test-first workflow

1. Upload this ZIP into a separate GitHub test repository/folder.
2. Run the workflow manually with `workflow_dispatch`.
3. Inspect `data/current/jobs.json` and `data/last_run.json`.
4. Review source-level errors before using any data on a website.
5. Do not connect this repository to Kamyabi.in until extraction quality is approved.

## Safety rule

The scraper must not fabricate missing values. Unknown fields should remain `null`.
The linked official government notification remains the source of truth.
