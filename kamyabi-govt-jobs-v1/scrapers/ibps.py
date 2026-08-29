from .base import *
from pipeline.pdf_extract import pdf_text
import urllib3

URL = "https://www.ibps.in/"
RECRUITMENT_WORDS = ("recruitment", "crp-", "registration", "notification for", "posts of")
BAD_WORDS = ("result", "score", "interview", "shortlisted", "provisionally allotted", "cut-off")


def _get_soup(session):
    try:
        return soup(URL, session)
    except requests.exceptions.SSLError:
        # IBPS currently presents a certificate-chain problem to some runners.
        # Scope the fallback to this public source only and emit a warning.
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return soup(URL, session, verify=False)


def scrape(session=None):
    s, _ = _get_soup(session)
    jobs=[]; seen=set()
    for a in s.find_all("a", href=True):
        title=clean_text(a.get_text(" ", strip=True))
        href=absolute(URL, a["href"])
        low=title.lower()
        if not title or href in seen:
            continue
        if not any(k in low for k in RECRUITMENT_WORDS):
            continue
        if any(k in low for k in BAD_WORDS):
            continue
        if not (is_pdf(href) or "recruit" in href.lower() or "crp" in href.lower()):
            continue
        seen.add(href)
        pdf=""
        if is_pdf(href):
            try:
                pdf=pdf_text(href, session)
            except Exception:
                pass
        context=clean_text(f"{title} {pdf[:5000]}")
        if classify_record(title, context) != "recruitment":
            continue
        dates=extract_date_range(pdf[:60000])
        j=Job(
            job_id=make_job_id("ibps", title, href),
            organization="Institute of Banking Personnel Selection",
            title=title[:300],
            job_type="Public Sector Banking",
            vacancies=extract_vacancies(pdf),
            qualification=extract_qualification(pdf),
            age_limit=extract_age(pdf),
            salary=extract_salary(pdf),
            application_start=dates[0] if len(dates)>=1 else None,
            application_end=dates[1] if len(dates)>=2 else None,
            official_url=URL,
            notification_url=href if is_pdf(href) else None,
            source="IBPS",
            record_type="recruitment",
            status=infer_status(dates[1] if len(dates)>=2 else None),
            content_hash=sha256_text(title,pdf[:100000],href)
        )
        d=j.to_dict(); j.data_quality_score,j.missing_fields=quality_score(d)
        jobs.append(j.to_dict())
    return jobs
