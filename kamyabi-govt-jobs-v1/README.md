# Kamyabi Government Jobs Scraper — V1.1 TEST ONLY

This repository is a **test-only** data collector for Kamyabi. It does **not** connect to, modify, deploy to, or call `kamyabi.in`.

## What changed in V1.1

- Added `record_type` validation so results, selection lists, interview schedules, admit cards and similar notices are not treated as vacancies.
- SBI scraper now starts from actual **DOWNLOAD ADVERTISEMENT** records and requires recruitment/apply context instead of scraping every PDF on the page.
- Added application-date extraction from SBI's recruitment block and notification PDF.
- Added vacancy/qualification/age/salary extraction where the PDF text supports it.
- SSC, India Post, IBPS and Employment News parsers were tightened around recruitment records.
- IBPS has a narrowly scoped certificate-chain fallback; it does not disable TLS globally.
- UPSC has an alternate official vacancy-circular endpoint if the recruitment-advertisement page blocks the runner.
- Legacy V1 records without a valid `record_type` are removed from the current dataset on the next run.
- Added QA and tests to the GitHub Action before scraping.

## Current sources

- UPSC
- SSC
- IBPS
- SBI Careers
- India Post
- Employment News

## Data policy

Only `vacancy` and `recruitment` records enter `data/current/jobs.json`.
Missing values are kept as `null`; the scraper does not invent vacancy counts, qualifications, dates or salary information.
The official government notification remains the source of truth.

## Output

- `data/current/jobs.json` — current normalized vacancy dataset
- `data/history/YYYY-MM-DD.json` — daily snapshot
- `data/last_run.json` — source health, counts and detected changes
- `logs/scraper.log` — execution log

## GitHub Actions

The workflow runs daily at 05:30 IST and can be manually triggered from Actions. Because the repository is currently nested under `kamyabi-govt-jobs-v1/`, the workflow explicitly runs Python from that directory.

Before any future website integration, inspect the actual records and source-level QA results for several runs.


## V1.2 data-safety gates

A scraped item is not allowed into `data/current/jobs.json` unless it has:
- a specific non-generic title,
- a direct notification target different from the source landing page,
- at least one application date,
- a known open/closed status,
- a `vacancy` or `recruitment` record type.

Rejected items are written to `data/review/YYYY-MM-DD.json` for inspection rather than being published.
