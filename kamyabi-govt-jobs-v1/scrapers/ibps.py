from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.fields import find_vacancies, infer_application_window, find_labeled, infer_quality

BASE = "https://www.ibps.in"
PAGES = [
    f"{BASE}/index.php/clerical-cadre-xvi/",
    f"{BASE}/index.php/crp-po-mt-xvi/",
    f"{BASE}/index.php/specialist-officer-xvi/",
    f"{BASE}/index.php/rrb-xv/",
]

BAD = ("result", "select list", "interview", "admit card", "answer key", "score card", "provisional allotment")

def parse_page(page_url, session):
    s, _ = soup(page_url, session)
    jobs = []
    for a in s.find_all("a", href=True):
        title = clean_text(a.get_text(" ", strip=True))
        href = absolute(page_url, a["href"])
        low = title.lower()
        if not title or any(x in low for x in BAD):
            continue
        if not (is_pdf(href) or "registration" in low or "apply" in low or "notification" in low):
            continue
        # Candidate needs recruitment wording.
        if not any(k in low for k in ("notification", "common recruitment", "crp", "recruitment process")):
            continue

        pdf = ""
        if is_pdf(href):
            try: pdf = pdf_text(href, session)
            except Exception: pass

        start, end = infer_application_window(pdf or title)
        vacancies = find_vacancies(pdf)
        application_url = None
        # Find nearby registration/apply links on page.
        parent = a.parent
        for aa in (parent.find_all("a", href=True) if parent else []):
            tt = clean_text(aa.get_text(" ", strip=True)).lower()
            if "apply" in tt or "registration" in tt:
                application_url = absolute(page_url, aa["href"])
                break

        if not end and not vacancies and not pdf:
            continue

        job = Job(
            job_id=make_job_id("ibps", title, href),
            organization="Institute of Banking Personnel Selection",
            title=title[:300],
            job_type="Public Sector Banking",
            vacancies=vacancies,
            qualification=find_labeled(pdf, ["educational qualification", "eligibility criteria", "educational qualifications"]),
            age_limit=find_labeled(pdf, ["age limit", "age as on"]),
            salary=find_labeled(pdf, ["pay scale", "salary", "emoluments"]),
            application_start=start,
            application_end=end,
            official_url=page_url,
            notification_url=href if is_pdf(href) else None,
            application_url=application_url,
            source="IBPS",
            record_type="recruitment",
            status=infer_status(end),
            content_hash=sha256_text(title, pdf[:150000], href)
        )
        q, missing = infer_quality(job.to_dict())
        job.data_quality_score = q if hasattr(job, "data_quality_score") else None
        d = job.to_dict()
        d["data_quality_score"], d["missing_fields"] = q, missing
        jobs.append(d)
    return jobs

def scrape(session=None):
    all_jobs = []
    seen = set()
    for page in PAGES:
        try:
            for j in parse_page(page, session):
                if j["job_id"] not in seen:
                    seen.add(j["job_id"]); all_jobs.append(j)
        except Exception:
            continue
    return all_jobs
