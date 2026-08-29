from .base import *
from pipeline.pdf_extract import pdf_text

URLS = [
    ("https://www.upsc.gov.in/recruitment/recruitment-advertisement", "advertisement"),
    ("https://www.upsc.gov.in/hi/recruitment/recruitment-advertisement", "advertisement"),
    ("https://www.upsc.gov.in/vacancy-circulars", "vacancy"),
]


def scrape(session=None):
    last=None
    s=None; used=None
    for url, page_kind in URLS:
        try:
            s,_=soup(url,session); used=url; break
        except Exception as e:
            last=e
    if s is None:
        raise last
    jobs=[]; seen=set()
    for a in s.find_all("a",href=True):
        title=clean_text(a.get_text(" ",strip=True))
        href=absolute(used,a["href"])
        if not title or not is_pdf(href) or href in seen:
            continue
        if page_kind == "advertisement":
            if "advertisement" not in title.lower() and "advt" not in title.lower() and "recruit" not in title.lower():
                continue
        else:
            if not any(k in title.lower() for k in ("post", "vacancy", "filling up", "engagement")):
                continue
        seen.add(href)
        pdf=""
        try: pdf=pdf_text(href,session)
        except Exception: pass
        if classify_record(title,pdf[:4000]) != "recruitment":
            continue
        dates=extract_date_range(pdf[:60000])
        adv=title
        j=Job(
            job_id=make_job_id("upsc",title,adv),
            organization="Union Public Service Commission",
            title=title[:300],
            job_type="Central Government",
            vacancies=extract_vacancies(pdf),
            qualification=extract_qualification(pdf),
            age_limit=extract_age(pdf),
            salary=extract_salary(pdf),
            application_start=dates[0] if len(dates)>=1 else None,
            application_end=dates[1] if len(dates)>=2 else None,
            official_url=used,
            notification_url=href,
            source="UPSC",
            source_advertisement_no=adv[:200],
            record_type="recruitment",
            status=infer_status(dates[1] if len(dates)>=2 else None),
            content_hash=sha256_text(title,pdf[:100000],href)
        )
        d=j.to_dict(); j.data_quality_score,j.missing_fields=quality_score(d)
        jobs.append(j.to_dict())
    return jobs
