from pathlib import Path
import json
from datetime import date

def load_json(path,default):
    p=Path(path)
    if not p.exists(): return default
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return default

def write_json(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

def merge_jobs(existing,scraped,now,min_quality=75):
    by_id={j["job_id"]:j for j in existing}
    changes=[];review=[];published=[]
    for job in scraped:
        end=job.get("application_end")
        eligible=(
            job.get("notification_url") and
            job.get("title") and
            job.get("record_type") in ("vacancy","recruitment") and
            job.get("status")=="open" and
            end and job.get("data_quality_score",0)>=min_quality
        )
        if not eligible:
            review.append(job);continue
        old=by_id.get(job["job_id"])
        if old: job["first_seen"]=old.get("first_seen") or now
        else:
            job["first_seen"]=now
            changes.append({"job_id":job["job_id"],"title":job.get("title"),"type":"new","changes":[]})
        job["last_seen"]=now;job["last_updated"]=now;job["scrape_date"]=now
        by_id[job["job_id"]]=job;published.append(job)
    # Remove expired jobs from current dataset; retain them in history.
    current=[]
    for j in by_id.values():
        if j.get("application_end"):
            try:
                if date.fromisoformat(j["application_end"]) < date.today(): continue
            except: pass
        current.append(j)
    current.sort(key=lambda x:(x.get("application_end") or "9999-12-31",x.get("organization") or "",x.get("title") or ""))
    return current,changes,review,published
