# Kamyabi Government Jobs Scraper — V1.6 TEST

**Test only.** No deployment, API push, database write, or website integration with Kamyabi.in.

## V1.6 architecture

**Discover broadly -> Extract deeply -> Deduplicate -> Validate -> Publish**

### Data layers

- `data/discovered/YYYY-MM-DD.json` — every usable candidate discovered by source adapters.
- `data/review/YYYY-MM-DD.json` — candidates that fail publication validation.
- `data/current/jobs.json` — only current/open, validated records.
- `data/history/YYYY-MM-DD.json` — daily current snapshot.
- `data/last_run.json` — source health and run statistics.

### Publication policy

A job must:
- be a genuine recruitment/vacancy record;
- have a direct notification URL;
- have a real job title;
- have a valid current application end date;
- pass discovery and publication score thresholds;
- not be a result/selection/interview/admit-card/corrigendum notice.

Missing fields are never fabricated.

### GitHub

The workflow runs unit tests before the scraper, then QA, then commits only test-repository data.
