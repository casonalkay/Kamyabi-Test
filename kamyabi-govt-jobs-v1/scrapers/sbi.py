from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.extract import application_window, vacancies, labeled, quality
from pipeline.classify import is_recruitment

URL="https://sbi.bank.in/web/careers/current-openings"

def scrape(session=None):
    s,_=soup(URL,session)
    jobs=[]
    for row in s.find_all(["tr","li","div"]):
        text=clean_text(row.get_text(" ",strip=True))
        links=row.find_all("a",href=True)
        if not links or not text: continue
        if not is_recruitment(text): continue

        pdfs=[(clean_text(a.get_text(" ",strip=True)),absolute(URL,a["href"]))
              for a in links if is_pdf(absolute(URL,a["href"]))]
        if not pdfs: continue

        # Use the row heading/first substantial text as title.
        title=clean_text(links[0].get_text(" ",strip=True)) or text[:300]
        if len(title)<5: title=text[:300]

        # Parse the page text first — SBI exposes the application window in HTML.
        start,end=application_window(text)
        app_url=None
        for a in links:
            tt=clean_text(a.get_text(" ",strip=True)).lower()
            if "apply online" in tt or tt=="apply" or "registration" in tt:
                app_url=absolute(URL,a["href"]); break

        for _,pdf_url in pdfs[:2]:
            pdf=""
            try: pdf=pdf_text(pdf_url,session)
            except Exception: pass
            if not is_recruitment(title,pdf): continue

            ps,pe=application_window(pdf)
            start=start or ps
            end=end or pe
            v=vacancies(pdf)
            d=Job(
                job_id=make_job_id("sbi",title,pdf_url),
                organization="State Bank of India",
                title=title[:300],
                job_type="Public Sector Banking",
                vacancies=v,
                qualification=labeled(pdf,["educational qualification","essential qualification","qualification"]),
                age_limit=labeled(pdf,["age limit","age as on"]),
                salary=labeled(pdf,["salary","emoluments","pay scale","remuneration"]),
                application_start=start,
                application_end=end,
                official_url=URL,
                notification_url=pdf_url,
                application_url=app_url,
                source="SBI",
                record_type="recruitment",
                status=infer_status(end),
                content_hash=sha256_text(title,pdf[:180000],text)
            ).to_dict()
            q,missing=quality(d); d["data_quality_score"]=q; d["missing_fields"]=missing
            jobs.append(d)
    return list({j["job_id"]:j for j in jobs}.values())
