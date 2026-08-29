from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.normalize import first_date, extract_int, clean_field

URL = "https://www.upsc.gov.in/recruitment/recruitment-advertisement"

def scrape(session=None):
    s, _ = soup(URL, session)
    jobs = []
    for a in s.find_all("a", href=True):
        title = clean_text(a.get_text(" ", strip=True))
        href = absolute(URL, a["href"])
        if not title or not is_pdf(href):
            continue
        if "advertisement" not in title.lower() and "advt" not in title.lower() and "special" not in title.lower():
            continue
        text = ""
        try:
            text = pdf_text(href, session)
        except Exception:
            pass
        end = None
        for key in ["LAST DATE", "last date", "Closing Date", "closure"]:
            idx = text.lower().find(key.lower())
            if idx >= 0:
                end = first_date(text[idx:idx+250])
                if end: break
        adv = title
        job_title = title.replace("UNION PUBLIC SERVICE COMMISSION", "").strip()
        job = Job(
            job_id=make_job_id("upsc", job_title, adv),
            organization="Union Public Service Commission",
            title=job_title[:300],
            job_type="Central Government",
            application_end=end,
            official_url=URL,
            notification_url=href,
            source="UPSC",
            source_advertisement_no=adv[:200],
            status=infer_status(end),
            content_hash=sha256_text(job_title, text[:100000], href)
        )
        jobs.append(job.to_dict())
    return jobs
