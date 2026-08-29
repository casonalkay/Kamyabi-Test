from .base import *
from pipeline.pdf_extract import pdf_text
import urllib3

HOME = "https://www.ibps.in/"
CATEGORY_URLS = [
    "https://www.ibps.in/index.php/management-trainees-xvi/",
    "https://www.ibps.in/index.php/specialist-officers-xvi/",
    "https://www.ibps.in/index.php/clerical-cadre-xvi/",
]
BAD_WORDS = ("result", "score", "interview", "call letter", "shortlisted",
             "provisionally allotted", "cut-off", "corrigendum", "application reprint",
             "updated vacancies")


def _get(url, session=None):
    try:
        return soup(url, session)
    except requests.exceptions.SSLError:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return soup(url, session, verify=False)


def _registration_dates(url, session):
    if not url:
        return None, None
    try:
        s, _ = _get(url, session)
        text = clean_text(s.get_text(" ", strip=True))
        m = re.search(r"Commencement of online registration.*?(\d{1,2}/\d{1,2}/\d{4}).*?"
                      r"Closure of registration.*?(\d{1,2}/\d{1,2}/\d{4})", text, re.I)
        if m:
            vals = extract_date_range(m.group(1) + " " + m.group(2))
            return (vals[0], vals[1]) if len(vals) >= 2 else (None, None)
    except Exception:
        pass
    return None, None


def scrape(session=None):
    jobs = []
    seen = set()

    for category_url in CATEGORY_URLS:
        try:
            s, _ = _get(category_url, session)
        except Exception:
            continue

        page_title = clean_text(s.title.get_text(" ", strip=True) if s.title else "")
        # Find the actual notification and application links, not the homepage's
        # generic "RECRUITMENT EXAMS" link.
        notification = None
        apply_url = None
        notification_title = None

        for a in s.find_all("a", href=True):
            label = clean_text(a.get_text(" ", strip=True))
            href = absolute(category_url, a["href"])
            low = label.lower()
            if any(x in low for x in BAD_WORDS):
                continue
            if "notification for common recruitment process" in low:
                notification = href
                notification_title = label
            elif "apply online" in low and apply_url is None:
                apply_url = href

        if not notification:
            # Some category pages expose the notification only as a PDF link.
            for a in s.find_all("a", href=True):
                label = clean_text(a.get_text(" ", strip=True))
                href = absolute(category_url, a["href"])
                low = label.lower()
                if "notification" in low and "common recruitment process" in low and "corrigendum" not in low:
                    notification = href
                    notification_title = label
                    break

        if not notification:
            continue

        key = notification
        if key in seen:
            continue
        seen.add(key)

        pdf = ""
        try:
            if is_pdf(notification):
                pdf = pdf_text(notification, session)
        except Exception:
            pass

        start, end = _registration_dates(apply_url, session)
        if not start and not end:
            dates = extract_date_range(pdf[:80000])
            if len(dates) >= 2:
                start, end = dates[0], dates[1]

        # Use the category page's canonical recruitment name rather than the
        # generic homepage title.
        title = notification_title or page_title
        title = re.sub(r"\s+", " ", title).strip()
        if "crp" not in title.lower():
            title = page_title or title

        if not (start or end):
            continue

        j = Job(
            job_id=make_job_id("ibps", title, notification),
            organization="Institute of Banking Personnel Selection",
            title=title[:300],
            job_type="Public Sector Banking",
            vacancies=extract_vacancies(pdf),
            qualification=extract_qualification(pdf),
            age_limit=extract_age(pdf),
            salary=extract_salary(pdf),
            application_start=start,
            application_end=end,
            official_url=category_url,
            source_page_url=category_url,
            notification_url=notification,
            application_url=apply_url,
            source="IBPS",
            record_type="recruitment",
            status=infer_status(end),
            content_hash=sha256_text(title, pdf[:100000], notification, apply_url, start, end),
        )
        d = j.to_dict()
        j.data_quality_score, j.missing_fields = quality_score(d)
        jobs.append(j.to_dict())

    return jobs
