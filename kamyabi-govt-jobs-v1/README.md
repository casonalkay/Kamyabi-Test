# Kamyabi Government Jobs Scraper — V1.5 TEST

This is a test-only scraper. `website_integration` remains false. Nothing deploys to or modifies Kamyabi.in.

## V1.5 quality-first rules

1. Discover candidate recruitment notices.
2. Reject result/selection/interview/admit-card/corrigendum documents.
3. Reject language-only titles such as Hindi/English.
4. Parse the actual job title from the notification PDF when possible.
5. Deduplicate English/Hindi versions using advertisement number / normalized identity.
6. Require a direct notification URL.
7. Require a valid application end date and `status=open` for publication.
8. Require quality score >= 75.
9. Expired jobs are removed from `data/current/jobs.json` but remain in dated history.
10. Uncertain candidates go to `data/review/YYYY-MM-DD.json`.
11. Missing fields are never guessed.

## Run
```bash
pip install -r requirements.txt
pytest -q
python main.py
python qa.py
```
