from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.extract import application_window, vacancies, labeled, quality
from pipeline.classify import is_recruitment, is_current

URL="https://ssc.gov.in/"
BAD=("result","answer key","admit card","allocation","marks","score","final result","option-cum-response")

def scrape(session=None):
    s,_=soup(URL,session)
    jobs=[]
    for a in s.find_all("a",href=True):
        title=clean_text(a.get_text(" ",strip=True))
        href=absolute(URL,a["href"])
        low=title.lower()
        if not title or not is_pdf(href): continue
        if any(x in low for x in BAD): continue
        if not is_recruitment(title): continue
        pdf=""
        try: pdf=pdf_text(href,session)
        except Exception: pass
        if pdf and any(x in pdf.lower()[:12000] for x in BAD): continue
        start,end=application_window(pdf+" "+title)
        if not (end and is_current(end)): continue
        d=Job(
            job_id=make_job_id("ssc",title,href),
            organization="Staff Selection Commission",
            title=title[:300],
            job_type="Central Government",
            vacancies=vacancies(pdf),
            qualification=labeled(pdf,["essential qualification","educational qualification","educational qualifications"]),
            age_limit=labeled(pdf,["age limit","age as on"]),
            salary=labeled(pdf,["pay level","salary","pay scale"]),
            application_start=start,
            application_end=end,
            official_url=URL,
            notification_url=href,
            source="SSC",
            record_type="recruitment",
            status=infer_status(end),
            content_hash=sha256_text(title,pdf[:180000],href)
        ).to_dict()
        q,missing=quality(d); d["data_quality_score"]=q; d["missing_fields"]=missing
        jobs.append(d)
    return list({j["job_id"]:j for j in jobs}.values())
