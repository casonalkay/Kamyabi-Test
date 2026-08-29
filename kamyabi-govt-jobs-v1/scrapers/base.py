from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, date
from typing import Optional
import hashlib
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

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
    source_page_url: Optional[str] = None
    application_url: Optional[str] = None
    source: Optional[str] = None
    source_advertisement_no: Optional[str] = None
    record_type: str = "vacancy"
    status: str = "unknown"
    data_quality_score: int = 0
    missing_fields: Optional[list] = None
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

def get(url, session=None, timeout=40, verify=True, extra_headers=None):
    s = session or requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126 Safari/537.36",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    if extra_headers:
        headers.update(extra_headers)
    r = s.get(url, timeout=timeout, headers=headers, verify=verify)
    r.raise_for_status()
    return r

def soup(url, session=None, verify=True):
    r = get(url, session, verify=verify)
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
    return ".pdf" in url.lower().split("?")[0] or "/pdf" in url.lower()

def sha256_text(*parts):
    payload = "\n".join(clean_text(str(p)) for p in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def infer_status(end_date):
    if not end_date:
        return "unknown"
    try:
        d = date.fromisoformat(end_date)
        return "open" if d >= date.today() else "closed"
    except Exception:
        return "unknown"

def make_job_id(source, title, advertisement=None):
    base = "|".join([source.lower(), clean_text(advertisement or ""), clean_text(title).lower()])
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:20]

NON_VACANCY_TERMS = (
    "result", "selection list", "provisionally selected", "interview schedule",
    "admit card", "call letter", "answer key", "marks secured", "shortlisted",
    "wait list", "waitlist", "final result", "written result", "skill test",
    "joining", "document verification", "dv schedule", "exam schedule"
)
VACANCY_TERMS = ("recruitment", "engagement", "vacancy", "vacancies", "apply online", "advertisement")

def classify_record(title, context=""):
    text = clean_text(f"{title} {context}").lower()
    if any(term in text for term in NON_VACANCY_TERMS):
        # A recruitment advertisement can contain later-result language, but if the
        # actual record title is explicitly a result/selection/interview item, reject it.
        t = clean_text(title).lower()
        if not any(term in t for term in VACANCY_TERMS):
            return "other"
    if any(term in text for term in VACANCY_TERMS):
        return "recruitment"
    return "other"

def extract_date_range(text):
    # Supports common Indian government formats: dd.mm.yyyy, dd-mm-yyyy, dd/mm/yyyy
    pat = r"\b(\d{1,2}[./-]\d{1,2}[./-]\d{4})\b"
    vals = re.findall(pat, text or "")
    out = []
    for v in vals:
        for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                out.append(datetime.strptime(v, fmt).date().isoformat())
                break
            except ValueError:
                pass
    return out

def extract_vacancies(text):
    if not text:
        return None
    patterns = [
        r"(?:total\s+)?(?:number\s+of\s+)?vacancies?\s*[:\-]?\s*(\d[\d,]*)",
        r"(?:no\.?\s+of\s+)?posts?\s*[:\-]?\s*(\d[\d,]*)",
        r"(?:number\s+of\s+posts?)\s*[:\-]?\s*(\d[\d,]*)",
        r"(?:total\s+posts?)\s*[:\-]?\s*(\d[\d,]*)",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                pass
    return None

def extract_qualification(text):
    if not text:
        return None
    m = re.search(r"(?:educational qualification|essential qualification|qualification)\s*[:\-]?\s*(.{20,500})", text, re.I)
    return clean_text(m.group(1))[:500] if m else None

def extract_age(text):
    if not text:
        return None
    m = re.search(r"(?:age limit|upper age limit|age as on)\s*[:\-]?\s*(.{5,200})", text, re.I)
    return clean_text(m.group(1))[:200] if m else None

def extract_salary(text):
    if not text:
        return None
    m = re.search(r"(?:pay scale|pay level|salary|remuneration|emoluments?)\s*[:\-]?\s*(.{5,250})", text, re.I)
    return clean_text(m.group(1))[:250] if m else None


GENERIC_TITLES = {
    "recruitment exams", "recruitment", "vacancies", "current openings",
    "government jobs", "jobs", "latest jobs"
}

def is_publishable(job):
    """Hard safety gate before a record can enter current jobs."""
    title = clean_text(job.get("title") or "")
    notification = clean_text(job.get("notification_url") or "")
    official = clean_text(job.get("official_url") or "")
    record_type = job.get("record_type")
    if record_type not in ("vacancy", "recruitment"):
        return False, "invalid_record_type"
    if not title or title.lower() in GENERIC_TITLES:
        return False, "generic_title"
    if not notification or notification == official:
        return False, "missing_direct_notification"
    if not (job.get("application_start") or job.get("application_end")):
        return False, "missing_application_dates"
    if job.get("status") == "unknown":
        return False, "unknown_status"
    return True, None

def quality_score(job):
    required = [
        "title", "organization", "official_url", "notification_url",
        "application_end", "record_type"
    ]
    useful = ["vacancies", "qualification", "age_limit", "salary", "application_start", "published_date"]
    missing = [k for k in required + useful if not job.get(k)]
    score = 100
    score -= 10 * sum(1 for k in required if not job.get(k))
    score -= 5 * sum(1 for k in useful if not job.get(k))
    return max(0, score), missing
