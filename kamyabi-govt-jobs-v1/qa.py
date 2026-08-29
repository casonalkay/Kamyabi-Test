import json
from pathlib import Path
jobs=json.loads(Path("data/current/jobs.json").read_text(encoding="utf-8")) if Path("data/current/jobs.json").exists() else []
print("KAMYABI V1.4 QA")
print("="*50)
print("Current publishable records:",len(jobs))
by={}
for j in jobs: by.setdefault(j.get("source","UNKNOWN"),[]).append(j)
for src,rows in sorted(by.items()):
    avg=sum(r.get("data_quality_score",0) for r in rows)/len(rows)
    print(f"{src}: {len(rows)} records | avg quality {avg:.1f}")
print("Website integration: FALSE")
