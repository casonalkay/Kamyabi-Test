from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.extract import application_window, vacancies, labeled, quality
from pipeline.classify import is_recruitment

PAGES=[
    "https://www.indiapost.gov.in/vacancies",
    "https://www.indiapost.gov.in/gdsonlineengagement"
]

def scrape(session=None):
    jobs=[]
    seen=set()
    for page in PAGES:
        try: s,_=soup(page,session)
        except Exception: continue
        for a in s.find_all("a",href=True):
            title=clean_text(a.get_text(" ",strip=True))
            href=absolute(page,a["href"])
            if not title or not is_pdf(href): continue
            if not is_recruitment(title): continue
            pdf=""
            try: pdf=pdf_text(href,session)
            except Exception: pass
            start,end=application_window(pdf+" "+title)
            if not (end and is_current(end)): continue
            d=Job(
                job_id=make_job_id("indiapost",title,href),
                organization="India Post",
                title=title[:300],
                job_type="Central Government",
                vacancies=vacancies(pdf),
                qualification=labeled(pdf,["educational qualification","qualification","eligibility"]),
                age_limit=labeled(pdf,["age limit","age as on"]),
                salary=labeled(pdf,["salary","pay","emoluments"]),
                application_start=start,
                application_end=end,
                official_url=page,
                notification_url=href,
                source="India Post",
                record_type="recruitment",
                status=infer_status(end),
                content_hash=sha256_text(title,pdf[:180000],href)
            ).to_dict()
            q,missing=quality(d); d["data_quality_score"]=q; d["missing_fields"]=missing
            if d["job_id"] not in seen:
                jobs.append(d); seen.add(d["job_id"])
    return jobs
