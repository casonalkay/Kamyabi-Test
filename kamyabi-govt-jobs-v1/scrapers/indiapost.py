from .base import *
from pipeline.pdf_extract import pdf_text

URL = "https://www.indiapost.gov.in/vacancies"
GDS = "https://www.indiapost.gov.in/gdsonlineengagement"


def scrape(session=None):
    jobs=[]; seen=set()
    for page_url in (URL, GDS):
        try:
            s,_=soup(page_url, session)
        except Exception:
            continue
        for a in s.find_all("a", href=True):
            title=clean_text(a.get_text(" ", strip=True))
            href=absolute(page_url,a["href"])
            if not title or href in seen or not is_pdf(href):
                continue
            ctx=clean_text(a.parent.get_text(" ", strip=True) if a.parent else title)
            if not any(k in (title+" "+ctx).lower() for k in ("vacan", "notification", "recruit", "engagement", "gds", "artisan", "driver")):
                continue
            if any(k in (title+" "+ctx).lower() for k in ("corrigendum", "result", "selection list", "admit card")):
                continue
            seen.add(href)
            pdf=""
            try: pdf=pdf_text(href,session)
            except Exception: pass
            record_type=classify_record(title,pdf[:4000])
            if record_type not in ("recruitment",):
                continue
            dates=extract_date_range(pdf[:60000])
            pub=None
            m=re.search(r"(?:published|date|dated)\s*[:\-]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})",ctx,re.I)
            if m:
                vals=extract_date_range(m.group(1)); pub=vals[0] if vals else None
            j=Job(
                job_id=make_job_id("indiapost",title,href),
                organization="India Post",
                title=title[:300],
                job_type="Central Government",
                vacancies=extract_vacancies(pdf),
                qualification=extract_qualification(pdf),
                age_limit=extract_age(pdf),
                salary=extract_salary(pdf),
                application_start=dates[0] if len(dates)>=1 else None,
                application_end=dates[1] if len(dates)>=2 else None,
                published_date=pub,
                official_url=page_url,
                notification_url=href,
                source="India Post",
                record_type="recruitment",
                status=infer_status(dates[1] if len(dates)>=2 else None),
                content_hash=sha256_text(title,pdf[:100000],href)
            )
            d=j.to_dict(); j.data_quality_score,j.missing_fields=quality_score(d)
            jobs.append(j.to_dict())
    return jobs
