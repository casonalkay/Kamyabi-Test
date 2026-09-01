import re
from dateutil import parser as dtparser

MONTHS = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_TOKEN = re.compile(rf"\b(?:\d{{1,2}}[./-]\d{{1,2}}[./-]\d{{2,4}}|\d{{1,2}}\s+{MONTHS}\s*,?\s*\d{{4}})\b", re.I)

def norm(s): return re.sub(r"\s+", " ", s or "").strip()

def parse_one_date(s):
    if not s: return None
    try: return dtparser.parse(norm(s)[:80], dayfirst=True, fuzzy=False).date().isoformat()
    except Exception: return None

def all_dates(text):
    out=[]
    for m in DATE_TOKEN.finditer(text or ""):
        d=parse_one_date(m.group(0))
        if d and d not in out: out.append(d)
    return out

def first_date_in(text):
    ds=all_dates(text)
    return ds[0] if ds else None

def date_after_label(text, labels, window=240):
    low=(text or "").lower()
    for label in labels:
        pos=0
        while True:
            i=low.find(label.lower(),pos)
            if i<0: break
            for m in DATE_TOKEN.finditer(text[i:i+window]):
                d=parse_one_date(m.group(0))
                if d: return d
            pos=i+len(label)
    return None

def application_window(text):
    text=text or ""
    start=date_after_label(text,[
        "opening date","start date","commencement of online application",
        "online application starts","registration starts","registration begins",
        "apply online from","application start"
    ])
    end=date_after_label(text,[
        "closing date","last date to apply","last date","end date",
        "application ends","registration ends","registration closes",
        "apply online till","application end"
    ])
    # Explicit range: from DATE to DATE / DATE to DATE.
    ranges=re.finditer(rf"(?:from\s+)?({DATE_TOKEN.pattern})\s+(?:to|till|through|-|–)\s+({DATE_TOKEN.pattern})", text, re.I)
    for m in ranges:
        a,b=parse_one_date(m.group(1)),parse_one_date(m.group(2))
        if a and b:
            start=start or a; end=end or b; break
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
        if m: return int(m.group(1).replace(",",""))
    return None

def labeled(text, labels, window=600):
    low=(text or "").lower()
    for label in labels:
        i=low.find(label.lower())
        if i>=0:
            chunk=norm(text[i:i+window])
            chunk=re.sub(r"^.*?[:\-]\s*","",chunk,count=1)
            return chunk[:1500] or None
    return None

def advertisement_no(text):
    patterns=[
        r"(?:advertisement|advt\.?|notification)\s*(?:no\.?|number)?\s*[:\-]\s*([A-Z0-9][A-Z0-9./_-]{3,})",
        r"\b([A-Z]{2,10}/[A-Z0-9._-]{2,}/\d{4}(?:-\d{2})?/\d+)\b",
    ]
    for p in patterns:
        m=re.search(p,text or "",re.I)
        if m: return m.group(1).strip(" .;,")
    return None

def clean_title(s):
    s=norm(s)
    # Remove UI noise after recruitment title.
    s=re.sub(r"\s*\((?:apply online|last date to apply).*?\)", "", s, flags=re.I)
    s=re.split(r"\b(?:download advertisement|apply online|apply now|biodata|undertaking format)\b", s, flags=re.I)[0]
    s=re.sub(r"\s*(?:new)\s*$","",s,flags=re.I)
    return s.strip(" -:|")

def title_from_pdf(text, fallback=None):
    if not text: return clean_title(fallback)
    lines=[norm(x) for x in text.splitlines() if norm(x)]
    bad=re.compile(r"^(hindi|english|click here|download|advertisement|notification|page\s+\d+)$",re.I)
    good=re.compile(r"(recruitment|recruit|vacancy|vacancies|probationary officer|junior associate|officer|manager|assistant|engineer|scientist|clerk|constable|teacher|apprentice|specialist|group\s+[abc]|cadre)",re.I)
    for line in lines[:180]:
        if 8 <= len(line) <= 220 and not bad.match(line) and good.search(line):
            return clean_title(line)
    return clean_title(fallback)

def discovery_score(job):
    score=0
    for k,w in [("organization",20),("title",25),("notification_url",25),("record_type",10),
                ("application_start",5),("application_end",10),("advertisement_no",5)]:
        key="source_advertisement_no" if k=="advertisement_no" else k
        if job.get(key): score+=w
    return min(score,100)

def publication_score(job):
    score=discovery_score(job)
    for k,w in [("vacancies",8),("qualification",7),("age_limit",5),("salary",4),
                ("application_url",6),("location",3),("published_date",2)]:
        if job.get(k): score+=w
    return min(score,100)

def missing_fields(job):
    return [k for k in ["vacancies","qualification","age_limit","salary","application_start",
                        "application_end","application_url","published_date","location"]
            if not job.get(k)]

def quality(job):
    return publication_score(job), missing_fields(job)
