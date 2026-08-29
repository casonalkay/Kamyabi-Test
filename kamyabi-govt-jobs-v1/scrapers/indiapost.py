from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.normalize import first_date

URL = "https://www.indiapost.gov.in/vacancies"
GDS = "https://www.indiapost.gov.in/gdsonlineengagement"

def scrape(session=None):
    jobs = []
    for page_url in (URL, GDS):
        try:
            s, _ = soup(page_url, session)
        except Exception:
            continue
        for a in s.find_all("a", href=True):
            title = clean_text(a.get_text(" ", strip=True))
            href = absolute(page_url, a["href"])
            if not title or not is_pdf(href):
                continue
            if not any(k in (title + " " + href).lower() for k in ("vacan", "gds", "notification", "engagement", "recruit")):
                continue
            pdf = ""
            try: pdf = pdf_text(href, session)
            except Exception: pass
            end = None
            for key in ["End Date", "End date", "last date", "application submission"]:
                idx = pdf.lower().find(key.lower())
                if idx >= 0:
                    end = first_date(pdf[idx:idx+500])
                    if end: break
            job = Job(
                job_id=make_job_id("indiapost", title, href),
                organization="India Post",
                title=title[:300],
                job_type="Central Government",
                application_end=end,
                official_url=page_url,
                notification_url=href,
                source="India Post",
                status=infer_status(end),
                content_hash=sha256_text(title, pdf[:100000], href)
            )
            jobs.append(job.to_dict())
    return jobs
