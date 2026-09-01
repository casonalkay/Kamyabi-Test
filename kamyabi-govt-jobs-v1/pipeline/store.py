from pathlib import Path
import json
from datetime import date

def load_json(path,default):
    p=Path(path)
    if not p.exists():return default
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return default

def write_json(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

def _not_expired(end):
    """Return True if the end date is absent or not yet past."""
    if not end: return True
    try: return date.fromisoformat(end) >= date.today()
    except: return True

def merge_jobs(existing,candidates,now,min_quality_score=78):
    # Filter out legacy non-vacancy records from existing store
    clean_existing = [j for j in existing if j.get("record_type") in ("vacancy", "recruitment")]
    by_id={j["job_id"]:j for j in clean_existing}
    review=[];published=[];changes=[]
    for j in candidates:
        eligible=(
            j.get("notification_url") and
            j.get("title") and
            j.get("record_type") in ("vacancy","recruitment") and
            j.get("data_quality_score",0)>=min_quality_score and
            _not_expired(j.get("application_end"))
        )
        if not eligible:
            review.append(j); continue
        old=by_id.get(j["job_id"])
        if old:
            j["first_seen"]=old.get("first_seen") or now
        else:
            j["first_seen"]=now
            changes.append({"job_id":j["job_id"],"title":j.get("title"),"type":"new","changes":[]})
        j["last_seen"]=now;j["last_updated"]=now;j["scrape_date"]=now
        j["status"]="open"
        by_id[j["job_id"]]=j;published.append(j)

    current=[j for j in by_id.values() if _not_expired(j.get("application_end"))]
    current.sort(key=lambda x:(x.get("application_end") or "9999-12-31",x.get("organization") or "",x.get("title") or ""))
    return current,changes,review,published
