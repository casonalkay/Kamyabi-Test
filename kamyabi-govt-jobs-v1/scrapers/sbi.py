from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.normalize import first_date

URL = "https://sbi.bank.in/web/careers/Current-openings"

def scrape(session=None):
    s, _ = soup(URL, session)
    jobs = []
    for a in s.find_all("a", href=True):
        title = clean_text(a.get_text(" ", strip=True))
        href = absolute(URL, a["href"])
        if not title or not is_pdf(href):
            continue
        if not any(k in title.lower() for k in ("advert", "recruit", "officer", "associate", "probation", "specialist")):
            continue
        pdf = ""
        try: pdf = pdf_text(href, session)
        except Exception: pass
        end = None
        for key in ["ONLINE REGISTRATION", "last date", "closure of registration", "TO"]:
            idx = pdf.lower().find(key.lower())
            if idx >= 0:
                end = first_date(pdf[idx:idx+500])
                if end: break
        job = Job(
            job_id=make_job_id("sbi", title, href),
            organization="State Bank of India",
            title=title[:300],
            job_type="Public Sector Banking",
            application_end=end,
            official_url=URL,
            notification_url=href,
            source="SBI",
            status=infer_status(end),
            content_hash=sha256_text(title, pdf[:100000], href)
        )
        jobs.append(job.to_dict())
    return jobs
