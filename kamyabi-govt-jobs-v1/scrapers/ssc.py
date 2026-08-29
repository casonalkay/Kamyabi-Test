from .base import *
from pipeline.pdf_extract import pdf_text

URL = "https://ssc.gov.in/"

RECRUITMENT_HINTS = ("notice of", "examination", "recruitment", "combined", "junior engineer", "constable", "stenographer", "mts", "cgl", "chsl", "selection post")
BAD_HINTS = ("result", "answer key", "admit card", "allocation", "shortlisted", "marks", "call letter", "skill test")


def scrape(session=None):
    s, _ = soup(URL, session)
    jobs = []
    seen = set()
    for a in s.find_all("a", href=True):
        title = clean_text(a.get_text(" ", strip=True))
        href = absolute(URL, a["href"])
        if not title or not is_pdf(href) or href in seen:
            continue
        low = title.lower()
        if any(x in low for x in BAD_HINTS):
            continue
        if not any(x in low for x in RECRUITMENT_HINTS):
            continue
        seen.add(href)
        pdf = ""
        try:
            pdf = pdf_text(href, session)
        except Exception:
            pass
        combined = f"{title} {pdf[:5000]}"
        if any(x in combined.lower() for x in BAD_HINTS) and not any(x in title.lower() for x in ("notice of", "recruitment")):
            continue
        record_type = classify_record(title, pdf[:3000])
        if record_type != "recruitment":
            continue
        dates = extract_date_range(pdf[:60000])
        app_start = dates[0] if len(dates) >= 1 else None
        app_end = dates[1] if len(dates) >= 2 else None
        adv = None
        m = re.search(r"(?:F\.\s*No\.?|Notice\s*(?:No\.?|Number)?|No\.\s*HQ[-\w/]*)\s*[:.]?\s*([A-Z0-9\-/]+)", pdf[:5000], re.I)
        if m:
            adv = m.group(1)
        j = Job(
            job_id=make_job_id("ssc", title, adv or href),
            organization="Staff Selection Commission",
            title=title[:300],
            job_type="Central Government",
            vacancies=extract_vacancies(pdf),
            qualification=extract_qualification(pdf),
            age_limit=extract_age(pdf),
            salary=extract_salary(pdf),
            application_start=app_start,
            application_end=app_end,
            official_url=URL,
            notification_url=href,
            source="SSC",
            source_advertisement_no=adv,
            record_type="recruitment",
            status=infer_status(app_end),
            content_hash=sha256_text(title, pdf[:100000], href)
        )
        d=j.to_dict(); j.data_quality_score, j.missing_fields=quality_score(d)
        jobs.append(j.to_dict())
    return jobs
