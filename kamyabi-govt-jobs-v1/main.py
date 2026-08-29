import json, logging
from pathlib import Path
from datetime import datetime
import requests

from pipeline.store import load_json, write_json, merge_jobs
from scrapers import upsc, ssc, ibps, sbi, indiapost, employment_news

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"; LOGS=ROOT/"logs"

SCRAPERS={
    "upsc":upsc.scrape,
    "ssc":ssc.scrape,
    "ibps":ibps.scrape,
    "sbi":sbi.scrape,
    "indiapost":indiapost.scrape,
    "employment_news":employment_news.scrape
}

def setup_logging():
    LOGS.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(LOGS/"scraper.log",encoding="utf-8"),logging.StreamHandler()])

def run():
    setup_logging()
    now=datetime.now().astimezone().isoformat(timespec="seconds")
    session=requests.Session()
    session.headers.update({"User-Agent":"KamyabiGovtJobsBot/1.4 (+https://kamyabi.in)"})
    cfg=load_json(ROOT/"config/sources.json",{"sources":[]})
    enabled=[x["id"] for x in cfg["sources"] if x.get("enabled")]
    existing=load_json(DATA/"current/jobs.json",[])
    scraped=[]; stats=[]

    for sid in enabled:
        fn=SCRAPERS.get(sid)
        if not fn: continue
        try:
            jobs=fn(session)
            scraped.extend(jobs)
            if jobs:
                status="ok"
            else:
                status="no_data"
            stats.append({"source":sid,"status":status,"jobs":len(jobs),"rejected":0})
            logging.info("%s: %s (%d)",sid,status,len(jobs))
        except Exception as e:
            stats.append({"source":sid,"status":"error","jobs":0,"error":str(e)})
            logging.exception("%s failed",sid)

    merged,changes,review,published=merge_jobs(existing,scraped,now)

    merged.sort(key=lambda x:(x.get("status")!="open",x.get("application_end") or "9999-12-31",x.get("organization") or "",x.get("title") or ""))

    write_json(DATA/"current/jobs.json",merged)
    write_json(DATA/"history"/f"{now[:10]}.json",merged)
    write_json(DATA/"review"/f"{now[:10]}.json",review)
    write_json(DATA/"last_run.json",{
        "run_at":now,
        "total_jobs_scraped":len(scraped),
        "total_jobs_published_this_run":len(published),
        "total_jobs_current":len(merged),
        "review_records":len(review),
        "changes":changes,
        "sources":stats,
        "website_integration":False,
        "data_policy":"Only validated vacancy/recruitment records with a direct notification URL are published; uncertain records go to review; missing fields remain null."
    })
    print(json.dumps({"run_at":now,"scraped":len(scraped),"published":len(published),"current":len(merged),"review":len(review),"sources":stats},indent=2))

if __name__=="__main__":
    run()
