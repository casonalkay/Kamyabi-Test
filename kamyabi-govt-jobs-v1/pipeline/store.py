from pathlib import Path
import json

def load_json(path, default):
    p=Path(path)
    if not p.exists(): return default
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return default

def write_json(path,data):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

def merge_jobs(existing,scraped,now,min_quality=62):
    by_id={j["job_id"]:j for j in existing}
    changes=[]; review=[]; published=[]

    for job in scraped:
        score=job.get("data_quality_score",0)
        eligible=(
            job.get("notification_url") and
            job.get("record_type") in ("vacancy","recruitment") and
            job.get("title") and
            score>=min_quality
        )
        if not eligible:
            review.append(job); continue

        old=by_id.get(job["job_id"])
        if old:
            job["first_seen"]=old.get("first_seen") or now
            if old.get("content_hash")!=job.get("content_hash"):
                changes.append({
                    "job_id":job["job_id"],"title":job.get("title"),"type":"updated",
                    "changes":[
                        {"field":k,"old":old.get(k),"new":job.get(k)}
                        for k in job if old.get(k)!=job.get(k)
                        and k not in ("first_seen","last_seen","last_updated","scrape_date","content_hash")
                    ]
                })
        else:
            job["first_seen"]=now
            changes.append({"job_id":job["job_id"],"title":job.get("title"),"type":"new","changes":[]})
        job["last_seen"]=now
        job["last_updated"]=now
        job["scrape_date"]=now
        by_id[job["job_id"]]=job
        published.append(job)

    return list(by_id.values()),changes,review,published
