import json
import logging
from pathlib import Path
from datetime import datetime
import requests

from pipeline.store import load_json, write_json, merge_jobs
from pipeline.change_detector import content_hash
from scrapers import upsc, ssc, ibps, sbi, indiapost, employment_news
from scrapers.base import is_publishable

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
        handlers=[logging.FileHandler(LOGS / "scraper.log", encoding="utf-8"), logging.StreamHandler()],
    )


def run():
    setup_logging()
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    session = requests.Session()
    config = load_json(ROOT / "config/sources.json", {"sources": []})
    enabled = [x["id"] for x in config["sources"] if x.get("enabled")]
    current_path = DATA / "current/jobs.json"
    existing = load_json(current_path, [])
    all_scraped = []
    review = []
    source_stats = []

    for source_id in enabled:
        fn = SCRAPERS.get(source_id)
        if not fn:
            continue
        try:
            jobs = fn(session)
            valid = []
            rejected = 0
            for j in jobs:
                if j.get("record_type") not in ("vacancy", "recruitment"):
                    rejected += 1
                    review.append({"source": source_id, "job": j, "reason": "invalid_record_type"})
                    continue
                ok, reason = is_publishable(j)
                if not ok:
                    rejected += 1
                    review.append({"source": source_id, "job": j, "reason": reason})
                    continue
                j["content_hash"] = content_hash(j)
                valid.append(j)
            all_scraped.extend(valid)
            source_stats.append({"source": source_id, "status": "ok", "jobs": len(valid), "rejected": rejected})
            logging.info("%s: %d valid jobs (%d rejected)", source_id, len(valid), rejected)
        except Exception as e:
            logging.exception("%s failed", source_id)
            source_stats.append({"source": source_id, "status": "error", "jobs": 0, "error": str(e)})

    merged, changes, review = merge_jobs(existing, all_scraped, now)
    merged.sort(key=lambda x: (
        x.get("status") != "open",
        x.get("application_end") or "9999-12-31",
        x.get("organization") or "",
        x.get("title") or ""
    ))

    write_json(current_path, merged)
    write_json(DATA / "history" / f"{now[:10]}.json", merged)
    write_json(DATA / "review" / f"{now[:10]}.json", review)
    write_json(DATA / "review" / f"{now[:10]}.json", review)
    write_json(DATA / "last_run.json", {
        "run_at": now,
        "total_jobs_scraped": len(all_scraped),
        "total_jobs_current": len(merged),
        "review_records": len(review),
        "changes": changes,
        "sources": source_stats,
        "review_records": len(review),
        "website_integration": False,
        "data_policy": "Only vacancy/recruitment records are stored; missing fields remain null."
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
