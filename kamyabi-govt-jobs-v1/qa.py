import json
from pathlib import Path
jobs=json.loads(Path("data/current/jobs.json").read_text(encoding="utf-8")) if Path("data/current/jobs.json").exists() else []
print("KAMYABI V1.6 QA")
print("="*55)
print("Publishable current jobs:",len(jobs))
bad=[]
for j in jobs:
    if j.get("status")!="open" or not j.get("notification_url") or j.get("publication_score",0)<78:
        bad.append(j.get("title"))
print("QA failures:",len(bad))
if bad:
    print("\n".join(map(str,bad)))
print("Website integration: FALSE")
