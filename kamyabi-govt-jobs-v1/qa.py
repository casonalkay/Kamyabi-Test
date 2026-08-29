import json
from pathlib import Path

p = Path("data/current/jobs.json")
jobs = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []

sources = {}
for j in jobs:
    sources.setdefault(j.get("source") or "UNKNOWN", []).append(j)

print("KAMYABI SCRAPER QA")
print("=" * 40)
print(f"Total current records: {len(jobs)}")
print()

for source, rows in sorted(sources.items()):
    missing_url = sum(not r.get("notification_url") for r in rows)
    missing_title = sum(not r.get("title") for r in rows)
    print(f"{source}: {len(rows)} records | missing title={missing_title} | missing notification URL={missing_url}")

print()
print("No website integration is performed by this repository.")
