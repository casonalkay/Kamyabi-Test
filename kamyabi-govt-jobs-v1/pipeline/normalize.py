import re
from dateutil.parser import parse as dtparse

DATE_PATTERNS = [
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b\d{1,2}\s+(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s*,?\s*\d{4}\b",
    r"\b(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+\d{1,2},?\s+\d{4}\b"
]

def parse_date(text):
    if not text:
        return None
    dt = dtparse(text, dayfirst=True, fuzzy=True)
    return dt.date().isoformat() if dt else None

def first_date(text):
    if not text:
        return None
    for pat in DATE_PATTERNS:
        m = re.search(pat, text, re.I)
        if m:
            return parse_date(m.group(0))
    return None

def extract_int(text):
    if not text:
        return None
    m = re.search(r"(?<!\d)(\d[\d,]*)(?!\d)", text)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None

def clean_field(text, max_len=1000):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text[:max_len] or None
