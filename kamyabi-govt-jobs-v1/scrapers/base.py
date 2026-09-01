from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib, re, requests
from urllib.parse import urljoin

@dataclass
class Job:
    job_id: str
    organization: str
    title: str
    department: str | None = None
    job_type: str | None = None
    location: str | None = None
    vacancies: int | None = None
    qualification: str | None = None
    age_limit: str | None = None
    salary: str | None = None
    application_start: str | None = None
    application_end: str | None = None
    exam_date: str | None = None
    published_date: str | None = None
    official_url: str | None = None
    notification_url: str | None = None
    application_url: str | None = None
    source: str | None = None
    source_advertisement_no: str | None = None
    record_type: str = "recruitment"
    status: str = "unknown"
    first_seen: str | None = None
    last_seen: str | None = None
    last_updated: str | None = None
    scrape_date: str | None = None
    content_hash: str | None = None
    data_quality_score: int = 0
    missing_fields: list[str] | None = None

    def to_dict(self):
        return asdict(self)

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def clean_text(s):
    return re.sub(r"\s+", " ", (s or "")).strip()

def absolute(base, href):
    return urljoin(base, href)

def make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": "KamyabiGovtJobsBot/1.4 (+https://kamyabi.in)",
        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
    })
    return s

def get(url, session=None, timeout=30):
    s = session or make_session()
    r = s.get(url, timeout=timeout)
    r.raise_for_status()
    return r

def soup(url, session=None, timeout=30):
    from bs4 import BeautifulSoup
    r = get(url, session, timeout)
    return BeautifulSoup(r.content, "lxml"), r

def is_pdf(url):
    return ".pdf" in url.lower().split("?")[0]

def sha256_text(*parts):
    payload = "\n".join(clean_text(str(p)) for p in parts)
    return hashlib.sha256(payload.encode()).hexdigest()

def make_job_id(source, title, advertisement=None):
    raw = "|".join([source.lower(), clean_text(advertisement or "").lower(), clean_text(title).lower()])
    return hashlib.sha1(raw.encode()).hexdigest()[:20]

def infer_status(end_date):
    from datetime import date
    if not end_date: return "unknown"
    try:
        return "open" if date.fromisoformat(end_date) >= date.today() else "closed"
    except Exception:
        return "unknown"

def is_publishable(job):
    title = clean_text(job.get("title") or "").lower()
    record_type = (job.get("record_type") or "").lower()
    notification_url = (job.get("notification_url") or "").strip()
    official_url = (job.get("official_url") or "").strip()
    generic_titles = {
        "recruitment exams",
        "recruitment exam",
        "recruitment",
        "vacancies",
        "vacancy",
    }
    if record_type not in {"vacancy", "recruitment"}:
        return False, "record_type"
    if title in generic_titles:
        return False, "generic_title"
    if not notification_url:
        return False, "missing_notification"
    if official_url and notification_url.rstrip("/") == official_url.rstrip("/"):
        return False, "missing_direct_notification"
    return True, "ok"
