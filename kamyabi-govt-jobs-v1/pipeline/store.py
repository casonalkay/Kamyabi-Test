from pathlib import Path
import json
from datetime import date
from pipeline.extract import discovery_score, publication_score, missing_fields

def load_json(path,default):
    p=Path(path)
    if not p.exists():return default
    try:return json.loads(p.read_text(encoding="utf-8"))
    except:return default

def write_json(path,data):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

def normalize_candidate(job):
    if job.get("discovery_score") is None:
        base_score = job.get("data_quality_score")
        job["discovery_score"] = int(base_score) if base_score is not None else discovery_score(job)
    if job.get("publication_score") is None:
        base_score = job.get("data_quality_score")
        job["publication_score"] = int(base_score) if base_score is not None else publication_score(job)
    if job.get("missing_fields") is None:
        job["missing_fields"] = missing_fields(job)
    return job

def merge_jobs(existing,candidates,now,min_publication_score=78):
    by_id={j["job_id"]:j for j in existing}
    review=[];published=[];changes=[]
    for j in candidates:
        j=normalize_candidate(j)
        end=j.get("application_end")
        open_now=not end
        if end:
            try: open_now=date.fromisoformat(end)>=date.today()
            except: pass
        eligible=(
            j.get("notification_url") and
            j.get("title") and
            j.get("record_type") in ("vacancy","recruitment") and
            j.get("publication_score",0)>=min_publication_score and
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
        if j.get("record_type") not in ("vacancy","recruitment"):
            continue
        end=j.get("application_end")
        if end:
            try:
                if date.fromisoformat(end)<date.today():continue
            except:pass
        current.append(j)
    current.sort(key=lambda x:(x.get("application_end") or "9999-12-31",x.get("organization") or "",x.get("title") or ""))
    return current,changes,review,published
