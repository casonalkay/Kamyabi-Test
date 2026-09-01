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

def merge_jobs(existing,candidates,now,min_publication_score=78):
    by_id={j["job_id"]:j for j in existing if j.get("record_type") in ("vacancy","recruitment")}
    review=[];published=[];changes=[]
    for j in candidates:
        end=j.get("application_end")
        open_now=not end
        if end:
            try: open_now=date.fromisoformat(end)>=date.today()
            except: open_now=False
        score=j.get("publication_score",j.get("data_quality_score",0))
        discovery=j.get("discovery_score",j.get("data_quality_score",0))
        eligible=(
            j.get("notification_url") and
            j.get("title") and
            j.get("record_type") in ("vacancy","recruitment") and
            discovery>=70 and
            score>=min_publication_score and
            open_now
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

    current=[]
    for j in by_id.values():
        end=j.get("application_end")
        if end:
            try:
                if date.fromisoformat(end)<date.today():continue
            except:pass
        current.append(j)
    current.sort(key=lambda x:(x.get("application_end") or "9999-12-31",x.get("organization") or "",x.get("title") or ""))
    return current,changes,review,published
