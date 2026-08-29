from .base import *
from pipeline.pdf_extract import pdf_text

URL = "https://sbi.bank.in/en/web/careers/current-openings"


def _context(a):
    node = a
    best = ""
    for _ in range(6):
        node = node.parent
        if not node:
            break
        txt = clean_text(node.get_text(" ", strip=True))
        if 80 <= len(txt) <= 3500:
            best = txt
            if "ADVERTISEMENT NO" in txt.upper() and ("APPLY ONLINE" in txt.upper() or "LAST DATE TO APPLY" in txt.upper()):
                return txt
    return best


def scrape(session=None):
    s, _ = soup(URL, session)
    jobs = []
    seen = set()
    for a in s.find_all("a", href=True):
        link_text = clean_text(a.get_text(" ", strip=True))
        href = absolute(URL, a["href"])
        if "download advertisement" not in link_text.lower() or not is_pdf(href):
            continue
        ctx = _context(a)
        record_type = classify_record(ctx[:500], ctx)
        if record_type != "recruitment":
            continue
        adv = None
        m = re.search(r"ADVERTISEMENT\s*NO\s*[:.]?\s*([A-Z0-9/\-]+)", ctx, re.I)
        if m:
            adv = m.group(1)
        title = ctx.split("ADVERTISEMENT NO", 1)[0].strip(" -:")
        if not title:
            title = link_text
        # Ignore old/secondary documents accidentally nested in a block.
        key = (title.lower(), href)
        if key in seen:
            continue
        seen.add(key)

        dates = extract_date_range(ctx)
        app_start = dates[0] if len(dates) >= 1 else None
        app_end = dates[1] if len(dates) >= 2 else None
        last = re.search(r"LAST DATE TO APPLY\s*[:\-]?\s*(\d{1,2}[-/.]\d{1,2}[-/.]\d{4})", ctx, re.I)
        if last:
            vals = extract_date_range(last.group(1))
            if vals:
                app_end = vals[0]

        pdf = ""
        try:
            pdf = pdf_text(href, session)
        except Exception:
            pass
        if pdf:
            pdf_dates = extract_date_range(pdf[:50000])
            if not app_start and len(pdf_dates) >= 1:
                app_start = pdf_dates[0]
            if not app_end and len(pdf_dates) >= 2:
                app_end = pdf_dates[1]

        # Find the Apply Online URL in the same recruitment block.
        application_url = None
        for sibling_a in a.parent.find_all("a", href=True) if a.parent else []:
            st = clean_text(sibling_a.get_text(" ", strip=True)).lower()
            if "apply online" in st:
                application_url = absolute(URL, sibling_a["href"])
                break

        j = Job(
            job_id=make_job_id("sbi", title, adv),
            organization="State Bank of India",
            title=title[:300],
            job_type="Public Sector Banking",
            vacancies=extract_vacancies(pdf),
            qualification=extract_qualification(pdf),
            age_limit=extract_age(pdf),
            salary=extract_salary(pdf),
            application_start=app_start,
            application_end=app_end,
            official_url=URL,
            notification_url=href,
            application_url=application_url,
            source="SBI",
            source_advertisement_no=adv,
            record_type="recruitment",
            status=infer_status(app_end),
            content_hash=sha256_text(title, adv, ctx, pdf[:100000], href)
        )
        d = j.to_dict()
        j.data_quality_score, j.missing_fields = quality_score(d)
        jobs.append(j.to_dict())
    return jobs
