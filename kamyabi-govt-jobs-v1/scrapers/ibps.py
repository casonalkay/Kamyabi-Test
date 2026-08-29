from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.normalize import first_date

URL = "https://www.ibps.in/index.php/recruitment/"

def scrape(session=None):
    s, _ = soup(URL, session)
    jobs = []
    for row in s.select("tr"):
        text = clean_text(row.get_text(" ", strip=True))
        links = row.find_all("a", href=True)
        if not text or not links:
            continue
        href = absolute(URL, links[-1]["href"])
        if not is_pdf(href):
            continue
        title = clean_text(links[0].get_text(" ", strip=True)) or text[:250]
        pdf = ""
        try: pdf = pdf_text(href, session)
        except Exception: pass
        end = None
        for key in ["closure of registration", "closing date", "last date", "ends on"]:
            idx = pdf.lower().find(key)
            if idx >= 0:
                end = first_date(pdf[idx:idx+300])
                if end: break
        job = Job(
            job_id=make_job_id("ibps", title, href),
            organization="Institute of Banking Personnel Selection",
            title=title[:300],
            job_type="Public Sector Banking",
            application_end=end,
            official_url=URL,
            notification_url=href,
            source="IBPS",
            status=infer_status(end),
            content_hash=sha256_text(title, pdf[:100000], href)
        )
        jobs.append(job.to_dict())
    return jobs
