import json
from pathlib import Path

p = Path("data/current/jobs.json")
jobs = json.loads(p.read_text(encoding="utf-8")) if p.exists() else []

print("KAMYABI SCRAPER QA — V1.1")
print("=" * 45)
print(f"Total current records: {len(jobs)}")

bad_types = [j for j in jobs if j.get("record_type") not in ("vacancy", "recruitment")]
print(f"Invalid record types: {len(bad_types)}")

sources = {}
for j in jobs:
    sources.setdefault(j.get("source") or "UNKNOWN", []).append(j)

for source, rows in sorted(sources.items()):
    missing_title = sum(not r.get("title") for r in rows)
    missing_notification = sum(not r.get("notification_url") for r in rows)
    open_count = sum(r.get("status") == "open" for r in rows)
    print(f"{source}: {len(rows)} records | open={open_count} | missing title={missing_title} | missing notification URL={missing_notification}")

print("\nNo website integration is performed by this repository.")
