from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.fields import find_vacancies, infer_application_window, find_labeled, infer_quality

URL = "https://sbi.bank.in/web/careers/current-openings"
BAD = ("select list", "selected", "interview", "result", "admit card", "answer key", "score card", "shortlist", "wait list", "joining")

def scrape(session=None):
    s, _ = soup(URL, session)
    jobs = []
    for container in s.find_all(["tr","li","div"]):
        links = container.find_all("a", href=True)
        if not links: continue
        row_text = clean_text(container.get_text(" ", strip=True))
        low = row_text.lower()
        if any(x in low for x in BAD):
            continue
        pdf_links = [(clean_text(a.get_text(" ",strip=True)), absolute(URL,a["href"])) for a in links if is_pdf(absolute(URL,a["href"]))]
        if not pdf_links: continue

        title = clean_text(links[0].get_text(" ", strip=True)) or row_text[:250]
        if not any(k in (title+" "+row_text).lower() for k in ("recruit", "officer", "associate", "probation", "cadre", "apprentice", "manager", "specialist")):
            continue

        for link_title, href in pdf_links[:3]:
            if any(x in (link_title+" "+href).lower() for x in BAD):
                continue
            pdf = ""
            try: pdf = pdf_text(href, session)
            except Exception: pass
            if any(x in pdf.lower() for x in BAD):
                continue
            start, end = infer_application_window(pdf + " " + row_text)
            vacancies = find_vacancies(pdf)
            if not (end or vacancies or start):
                continue

            application_url = None
            for a in links:
                tt = clean_text(a.get_text(" ",strip=True)).lower()
                if "apply" in tt or "registration" in tt:
                    application_url = absolute(URL,a["href"]); break

            d = Job(
                job_id=make_job_id("sbi", title, href),
                organization="State Bank of India",
                title=title[:300],
                job_type="Public Sector Banking",
                vacancies=vacancies,
                qualification=find_labeled(pdf, ["educational qualification", "eligibility", "qualification"]),
                age_limit=find_labeled(pdf, ["age limit", "age as on"]),
                salary=find_labeled(pdf, ["pay scale", "salary", "emoluments", "remuneration"]),
                application_start=start,
                application_end=end,
                official_url=URL,
                notification_url=href,
                application_url=application_url,
                source="SBI",
                record_type="recruitment",
                status=infer_status(end),
                content_hash=sha256_text(title, pdf[:150000], href)
            ).to_dict()
            q, missing = infer_quality(d)
            d["data_quality_score"], d["missing_fields"] = q, missing
            jobs.append(d)
    # Deduplicate
    return list({j["job_id"]: j for j in jobs}.values())
