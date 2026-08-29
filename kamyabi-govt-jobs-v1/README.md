# Kamyabi Government Jobs Scraper — V1.4 TEST

TEST-ONLY repository. It does not connect to, modify, deploy to, or send data to Kamyabi.in.

## V1.4 design

Official portal -> source-specific discovery -> PDF/HTML extraction -> validation -> quality gate -> current dataset or review queue.

Publishable data:
- `data/current/jobs.json`

Uncertain records:
- `data/review/YYYY-MM-DD.json`

Daily snapshots:
- `data/history/YYYY-MM-DD.json`

Run locally:
```bash
pip install -r requirements.txt
pytest -q
python main.py
python qa.py
```

GitHub Actions runs tests before scraping and commits only repository data. No production credentials are required.

## V1.4 rules

- Never fabricate missing values.
- Never publish result/selection/interview/admit-card documents as vacancies.
- Require a direct notification URL.
- Use exact date-token extraction instead of fuzzy parsing of entire sentences.
- Distinguish `ok`, `no_data`, and `error` in source health.
- Keep the website integration flag false.
