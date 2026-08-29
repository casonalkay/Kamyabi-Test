import json,logging
from pathlib import Path
from datetime import datetime
import requests
from pipeline.store import load_json,write_json,merge_jobs
from scrapers import upsc,ssc,ibps,sbi,indiapost,employment_news

ROOT=Path(__file__).resolve().parent; DATA=ROOT/"data"; LOGS=ROOT/"logs"
SCRAPERS={"upsc":upsc.scrape,"ssc":ssc.scrape,"ibps":ibps.scrape,"sbi":sbi.scrape,"indiapost":indiapost.scrape,"employment_news":employment_news.scrape}

def run():
    LOGS.mkdir(exist_ok=True)
    logging.basicConfig(level=logging.INFO,format="%(asctime)s %(levelname)s %(message)s",
                        handlers=[logging.FileHandler(LOGS/"scraper.log",encoding="utf-8"),logging.StreamHandler()])
    now=datetime.now().astimezone().isoformat(timespec="seconds")
    cfg=load_json(ROOT/"config/sources.json",{"sources":[]})
    enabled=[x["id"] for x in cfg["sources"] if x.get("enabled")]
    session=requests.Session()
    session.headers.update({"User-Agent":"KamyabiGovtJobsBot/1.5 (+https://kamyabi.in)"})
    existing=load_json(DATA/"current/jobs.json",[])
    scraped=[];stats=[]
    for sid in enabled:
        try:
            jobs=SCRAPERS[sid](session)
            scraped.extend(jobs)
            status="ok" if jobs else "no_data"
            stats.append({"source":sid,"status":status,"candidates":len(jobs)})
            logging.info("%s: %s (%d candidates)",sid,status,len(jobs))
        except Exception as e:
            stats.append({"source":sid,"status":"error","candidates":0,"error":str(e)})
            logging.exception("%s failed",sid)
    current,changes,review,published=merge_jobs(existing,scraped,now)
    write_json(DATA/"current/jobs.json",current)
    write_json(DATA/"history"/f"{now[:10]}.json",current)
    write_json(DATA/"review"/f"{now[:10]}.json",review)
    write_json(DATA/"last_run.json",{
        "run_at":now,
        "total_candidates":len(scraped),
        "total_jobs_published_this_run":len(published),
        "total_jobs_current":len(current),
        "review_records":len(review),
        "changes":changes,
        "sources":stats,
        "website_integration":False,
        "publish_policy":"OPEN only; direct notification URL; title must be a real recruitment title; quality >= 75; expired jobs removed from current."
    })
    print(json.dumps({"candidates":len(scraped),"published":len(published),"current":len(current),"review":len(review),"sources":stats},indent=2))

if __name__=="__main__": run()
