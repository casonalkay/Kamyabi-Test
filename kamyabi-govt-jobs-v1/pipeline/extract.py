import re
from dateutil import parser as dtparser
from datetime import date

def norm(s):
    return re.sub(r"\s+", " ", s or "").strip()

def parse_one_date(s):
    if not s: return None
    # Only pass a short date-like token to the parser.
    s = norm(s)[:80]
    try:
        return dtparser.parse(s, dayfirst=True, fuzzy=False).date().isoformat()
    except Exception:
        return None

DATE_TOKEN = re.compile(
    r"\b(?:\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|\d{1,2}\s+"
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)\s*,?\s*\d{4})\b", re.I)

def first_date_in(text):
    if not text: return None
    m = DATE_TOKEN.search(text)
    return parse_one_date(m.group(0)) if m else None

def dates_in(text):
    out=[]
    for m in DATE_TOKEN.finditer(text or ""):
        d=parse_one_date(m.group(0))
        if d and d not in out: out.append(d)
    return out

def date_after_label(text, labels, window=220):
    low=(text or "").lower()
    for label in labels:
        start=0
        while True:
            i=low.find(label.lower(), start)
            if i<0: break
            chunk=text[i:i+window]
            # Find the first actual date token, not the whole sentence.
            d=first_date_in(chunk)
            if d: return d
            start=i+len(label)
    return None

def application_window(text):
    start=date_after_label(text, [
        "opening date", "start date", "commencement of online application",
        "online application starts", "registration starts", "registration begins",
        "apply online from", "application start"
    ])
    end=date_after_label(text, [
        "closing date", "last date to apply", "last date", "end date",
        "application ends", "registration ends", "registration closes",
        "apply online till", "application end"
    ])
    # Handle explicit ranges such as "29.08.2026 TO 19.09.2026"
    if not start or not end:
        toks=list(DATE_TOKEN.finditer(text or ""))
        for a,b in zip(toks, toks[1:]):
            between=text[a.end():b.start()]
            if re.search(r"\bto\b|[-–]\s*$|\bthrough\b", between, re.I):
                da=parse_one_date(a.group(0)); db=parse_one_date(b.group(0))
                if da and db:
                    start=start or da
                    end=end or db
                    break
    return start,end

def vacancies(text):
    pats=[
        r"(?:total\s+)?vacancies?\s*[:\-]?\s*(\d[\d,]*)",
        r"(?:no\.?|number)\s+of\s+(?:vacancies|posts)\s*[:\-]?\s*(\d[\d,]*)",
        r"(\d[\d,]*)\s+(?:vacancies|posts)\b"
    ]
    for p in pats:
        m=re.search(p,text or "",re.I)
        if m:
            return int(m.group(1).replace(",",""))
    return None

def labeled(text, labels, window=300):
    low=(text or "").lower()
    for label in labels:
        i=low.find(label.lower())
        if i>=0:
            chunk=norm(text[i:i+window])
            # Strip label itself.
            chunk=re.sub(r"^.*?[:\-]\s*", "", chunk, count=1)
            return chunk[:1000] or None
    return None

def quality(job):
    score=0
    # Hard identity fields.
    for k,w in [("organization",10),("title",15),("notification_url",20),("record_type",10)]:
        if job.get(k): score+=w
    # Important publishing fields.
    for k,w in [("application_end",15),("application_start",5),("vacancies",8),
                ("qualification",5),("age_limit",4),("salary",4),("application_url",4)]:
        if job.get(k): score+=w
    useful=["vacancies","qualification","age_limit","salary","application_start","application_end","application_url","published_date","location"]
    missing=[k for k in useful if not job.get(k)]
    return min(score,100), missing
