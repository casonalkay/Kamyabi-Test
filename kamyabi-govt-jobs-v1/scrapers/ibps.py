from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.extract import application_window, vacancies, labeled, quality
from pipeline.classify import is_recruitment, is_current

BASE="https://www.ibps.in"
PAGES=[
    f"{BASE}/index.php/clerical-cadre-xvi/",
    f"{BASE}/index.php/crp-po-mt-xvi/",
    f"{BASE}/index.php/specialist-officer-xvi/",
    f"{BASE}/index.php/rrb-xv/"
]

def scrape(session=None):
    jobs=[]
    seen=set()
    for page in PAGES:
        try: s,_=soup(page,session,timeout=30)
        except Exception: continue
        for a in s.find_all("a",href=True):
            title=clean_text(a.get_text(" ",strip=True))
            href=absolute(page,a["href"])
            if not title or not is_pdf(href): continue
            if not is_recruitment(title): continue

            pdf=""
            try: pdf=pdf_text(href,session)
            except Exception: pass
            if pdf and not is_recruitment(title,pdf): continue

            start,end=application_window(pdf+" "+title)
            v=vacancies(pdf)
            d=Job(
                job_id=make_job_id("ibps",title,href),
                organization="Institute of Banking Personnel Selection",
                title=title[:300],
                job_type="Public Sector Banking",
                vacancies=v,
                qualification=labeled(pdf,["educational qualification","eligibility criteria","educational qualifications"]),
                age_limit=labeled(pdf,["age limit","age as on"]),
                salary=labeled(pdf,["pay scale","salary","emoluments"]),
                application_start=start,
                application_end=end,
                official_url=page,
                notification_url=href,
                source="IBPS",
                record_type="recruitment",
                status=infer_status(end),
                content_hash=sha256_text(title,pdf[:180000],href)
            ).to_dict()
            q,missing=quality(d); d["data_quality_score"]=q; d["missing_fields"]=missing
            if d["job_id"] not in seen:
                jobs.append(d); seen.add(d["job_id"])
    return jobs
