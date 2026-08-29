import json
import logging
from pathlib import Path
from datetime import datetime
import requests

from pipeline.store import load_json, write_json, merge_jobs
from pipeline.change_detector import content_hash
from scrapers import upsc, ssc, ibps, sbi, indiapost, employment_news

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
LOGS = ROOT / "logs"

SCRAPERS = {
    "upsc": upsc.scrape,
    "ssc": ssc.scrape,
    "ibps": ibps.scrape,
    "sbi": sbi.scrape,
    "indiapost": indiapost.scrape,
    "employment_news": employment_news.scrape,
}

def setup_logging():
    LOGS.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(LOGS / "scraper.log", encoding="utf-8"),
            logging.StreamHandler()
        ],
    )

def run():
    setup_logging()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    session = requests.Session()
    config = load_json(ROOT / "config/sources.json", {"sources":[]})
    enabled = [x["id"] for x in config["sources"] if x.get("enabled")]
    current_path = DATA / "current/jobs.json"
    existing = load_json(current_path, [])
    all_scraped = []
    source_stats = []

    for source_id in enabled:
        fn = SCRAPERS.get(source_id)
        if not fn:
            continue
        try:
            jobs = fn(session)
            for j in jobs:
                j["content_hash"] = content_hash(j)
            all_scraped.extend(jobs)
            source_stats.append({"source":source_id, "status":"ok", "jobs":len(jobs)})
            logging.info("%s: %d jobs", source_id, len(jobs))
        except Exception as e:
            logging.exception("%s failed", source_id)
            source_stats.append({"source":source_id, "status":"error", "error":str(e)})

    merged, changes = merge_jobs(existing, all_scraped, now)

    # Keep stable, deterministic ordering.
    merged.sort(key=lambda x: (x.get("status") != "open", x.get("application_end") or "9999-12-31", x.get("organization") or "", x.get("title") or ""))

    write_json(current_path, merged)
    write_json(DATA / "history" / f"{now[:10]}.json", merged)
    write_json(DATA / "last_run.json", {
        "run_at": now,
        "total_jobs_scraped": len(all_scraped),
        "total_jobs_current": len(merged),
        "changes": changes,
        "sources": source_stats
    })

    print(json.dumps({
        "run_at": now,
        "scraped": len(all_scraped),
        "current": len(merged),
        "changes": len(changes),
        "sources": source_stats
    }, indent=2))

if __name__ == "__main__":
    run()
