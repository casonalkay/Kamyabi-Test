import re
from datetime import date
from pipeline.normalize import parse_date, clean_field, extract_int

def find_labeled(text, labels, window=250):
    text = text or ""
    low = text.lower()
    for label in labels:
        idx = low.find(label.lower())
        if idx >= 0:
            chunk = text[idx:idx+window]
            chunk = re.sub(r"^[^:]{0,100}:\s*", "", chunk, count=1)
            return clean_field(chunk)
    return None

def find_date_after(text, labels):
    text = text or ""
    low = text.lower()
    for label in labels:
        start = 0
        while True:
            idx = low.find(label.lower(), start)
            if idx < 0: break
            d = parse_date(text[idx:idx+250])
            if d: return d
            start = idx + len(label)
    return None

def find_all_dates(text):
    dates = []
    for m in re.finditer(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", text or ""):
        d = parse_date(m.group(0))
        if d and d not in dates: dates.append(d)
    return dates

def find_vacancies(text):
    patterns = [
        r"(?:total\s+)?vacancies?\s*[:\-]?\s*(\d[\d,]*)",
        r"(\d[\d,]*)\s+(?:vacancies|posts|post[s]?)\b",
        r"no\.?\s+of\s+(?:vacancies|posts)\s*[:\-]?\s*(\d[\d,]*)",
        r"number\s+of\s+(?:vacancies|posts)\s*[:\-]?\s*(\d[\d,]*)"
    ]
    for p in patterns:
        m = re.search(p, text or "", re.I)
        if m:
            try: return int(m.group(1).replace(",",""))
            except: pass
    return None

def infer_application_window(text):
    start = find_date_after(text, [
        "opening date", "start date", "commencement of online application",
        "online application starts", "application starts", "registration starts",
        "registration begins", "apply online from"
    ])
    end = find_date_after(text, [
        "closing date", "last date", "end date", "application ends",
        "registration ends", "registration closes", "apply online till",
        "online application closes"
    ])
    return start, end

def infer_quality(job):
    required = ["title", "organization", "notification_url", "application_end", "record_type"]
    useful = ["vacancies", "qualification", "age_limit", "salary", "application_start", "location", "published_date", "application_url"]
    score = 40
    for k in required:
        if job.get(k): score += 8
    for k in useful:
        if job.get(k): score += 3
    score = min(score, 100)
    missing = [k for k in useful if not job.get(k)]
    return score, missing
