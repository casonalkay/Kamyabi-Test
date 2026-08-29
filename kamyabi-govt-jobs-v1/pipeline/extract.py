import re
from dateutil import parser as dtparser

MONTHS = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_TOKEN = re.compile(
    rf"\b(?:\d{{1,2}}[./-]\d{{1,2}}[./-]\d{{2,4}}|\d{{1,2}}\s+{MONTHS}\s*,?\s*\d{{4}})\b",
    re.I,
)

def norm(s): return re.sub(r"\s+", " ", s or "").strip()

def parse_one_date(s):
    if not s: return None
    try:
        return dtparser.parse(norm(s)[:80], dayfirst=True, fuzzy=False).date().isoformat()
    except Exception:
        return None

def first_date_in(text):
    m = DATE_TOKEN.search(text or "")
    return parse_one_date(m.group(0)) if m else None

def all_dates(text):
    out=[]
    for m in DATE_TOKEN.finditer(text or ""):
        d=parse_one_date(m.group(0))
        if d and d not in out: out.append(d)
    return out

def date_after_label(text, labels, window=240):
    low=(text or "").lower()
    for label in labels:
        pos=0
        while True:
            i=low.find(label.lower(),pos)
            if i<0: break
            d=first_date_in(text[i:i+window])
            if d: return d
            pos=i+len(label)
    return None

def application_window(text):
    text=text or ""
    start=date_after_label(text,[
        "opening date","start date","commencement of online application",
        "online application starts","registration starts","registration begins",
        "apply online from","application start","from "
    ])
    end=date_after_label(text,[
        "closing date","last date to apply","last date","end date",
        "application ends","registration ends","registration closes",
        "apply online till","application end","to "
    ])
    ds=all_dates(text)
    # Explicit "from DATE to DATE" or "DATE to DATE".
    if len(ds)>=2:
        m=re.search(r"(?:from\s+)?"+DATE_TOKEN.pattern+r"\s+(?:to|till|through|-|–)\s+"+DATE_TOKEN.pattern,text,re.I)
        if m:
            pair=DATE_TOKEN.findall(m.group(0))
            if len(pair)>=2:
                start=start or parse_one_date(pair[0])
                end=end or parse_one_date(pair[1])
    return start,end

def vacancies(text):
    patterns=[
        r"(?:total\s+)?vacancies?\s*[:\-]?\s*(\d[\d,]*)",
        r"(?:no\.?|number)\s+of\s+(?:vacancies|posts)\s*[:\-]?\s*(\d[\d,]*)",
        r"(\d[\d,]*)\s+(?:vacancies|posts)\b",
        r"total\s+number\s+of\s+posts\s*[:\-]?\s*(\d[\d,]*)",
    ]
    for p in patterns:
        m=re.search(p,text or "",re.I)
        if m:
            return int(m.group(1).replace(",",""))
    return None

def labeled(text, labels, window=500):
    low=(text or "").lower()
    for label in labels:
        i=low.find(label.lower())
        if i>=0:
            chunk=norm(text[i:i+window])
            chunk=re.sub(r"^.*?[:\-]\s*","",chunk,count=1)
            return chunk[:1200] or None
    return None

def advertisement_no(text):
    pats=[
        r"(?:advertisement|advt\.?|notification)\s*(?:no\.?|number)?\s*[:\-]\s*([A-Z0-9][A-Z0-9./_-]{3,})",
        r"\b([A-Z]{2,8}/[A-Z0-9._/-]{3,})\b"
    ]
    for p in pats:
        m=re.search(p,text or "",re.I)
        if m: return m.group(1).strip(" .;,")
    return None

def title_from_pdf(text, fallback=None):
    if not text: return fallback
    lines=[norm(x) for x in text.splitlines() if norm(x)]
    bad=re.compile(r"^(hindi|english|click here|download|advertisement|notification|page \d+)$",re.I)
    good=re.compile(r"(recruitment|recruit|vacancy|vacancies|probationary officer|junior associate|officer|manager|assistant|engineer|scientist|clerk|constable|teacher|apprentice|specialist|group [abc])",re.I)
    for line in lines[:120]:
        if len(line)>8 and len(line)<180 and not bad.match(line) and good.search(line):
            return line
    return fallback

def quality(job):
    # Strict score: identity + current application evidence are mandatory for publishing.
    score=0
    for k,w in [("organization",10),("title",20),("notification_url",20),("record_type",10)]:
        if job.get(k): score+=w
    for k,w in [("application_start",8),("application_end",12),("vacancies",8),
                ("qualification",5),("age_limit",3),("salary",2),("application_url",2)]:
        if job.get(k): score+=w
    missing=[k for k in [
        "vacancies","qualification","age_limit","salary",
        "application_start","application_end","application_url",
        "published_date","location"
    ] if not job.get(k)]
    return min(score,100),missing
