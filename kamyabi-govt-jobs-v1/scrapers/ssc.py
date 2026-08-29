from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.normalize import first_date, extract_int

URL = "https://ssc.gov.in/"

def scrape(session=None):
    s, _ = soup(URL, session)
    jobs = []
    seen = set()
    keywords = ("notice", "examination", "recruitment", "chsl", "cgl", "mts", "stenographer", "je", "gd", "selection")
    for a in s.find_all("a", href=True):
        title = clean_text(a.get_text(" ", strip=True))
        href = absolute(URL, a["href"])
        if not title or href in seen or not is_pdf(href):
            continue
        if not any(k in title.lower() for k in keywords):
            continue
        seen.add(href)
        text = ""
        try: text = pdf_text(href, session)
        except Exception: pass
        end = None
        for key in ["Closing Date", "last date", "Last date", "online application"]:
            idx = text.lower().find(key.lower())
            if idx >= 0:
                end = first_date(text[idx:idx+400])
                if end: break
        job = Job(
            job_id=make_job_id("ssc", title, href),
            organization="Staff Selection Commission",
            title=title[:300],
            job_type="Central Government",
            application_end=end,
            official_url=URL,
            notification_url=href,
            source="SSC",
            status=infer_status(end),
            content_hash=sha256_text(title, text[:100000], href)
        )
        jobs.append(job.to_dict())
    return jobs
