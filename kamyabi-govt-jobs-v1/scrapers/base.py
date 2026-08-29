from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
import hashlib
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

IST = "Asia/Kolkata"

@dataclass
class Job:
    job_id: str
    organization: str
    title: str
    department: Optional[str] = None
    job_type: Optional[str] = None
    location: Optional[str] = None
    vacancies: Optional[int] = None
    qualification: Optional[str] = None
    age_limit: Optional[str] = None
    salary: Optional[str] = None
    application_start: Optional[str] = None
    application_end: Optional[str] = None
    exam_date: Optional[str] = None
    published_date: Optional[str] = None
    official_url: Optional[str] = None
    notification_url: Optional[str] = None
    source: Optional[str] = None
    source_advertisement_no: Optional[str] = None
    status: str = "unknown"
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    last_updated: Optional[str] = None
    scrape_date: Optional[str] = None
    content_hash: Optional[str] = None

    def to_dict(self):
        return asdict(self)

def now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def clean_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()

def absolute(base, href):
    return urljoin(base, href)

def get(url, session=None, timeout=40):
    s = session or requests.Session()
    r = s.get(url, timeout=timeout, headers={
        "User-Agent": "KamyabiGovtJobsBot/1.0 (+https://kamyabi.in)"
    })
    r.raise_for_status()
    return r

def soup(url, session=None):
    r = get(url, session)
    return BeautifulSoup(r.content, "lxml"), r

def extract_links(soup_obj, base_url):
    out = []
    for a in soup_obj.find_all("a", href=True):
        text = clean_text(a.get_text(" ", strip=True))
        href = absolute(base_url, a["href"])
        if text or href:
            out.append((text, href))
    return out

def is_pdf(url):
    return ".pdf" in url.lower().split("?")[0]

def sha256_text(*parts):
    payload = "\n".join(clean_text(str(p)) for p in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def infer_status(end_date):
    if not end_date:
        return "unknown"
    from datetime import date
    try:
        d = date.fromisoformat(end_date)
        return "open" if d >= date.today() else "closed"
    except Exception:
        return "unknown"

def make_job_id(source, title, advertisement=None):
    base = "|".join([source.lower(), clean_text(advertisement or ""), clean_text(title).lower()])
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:20]
