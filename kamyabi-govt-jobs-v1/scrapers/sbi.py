from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.extract import *
from pipeline.classify import is_recruitment,current_open
from pipeline.dedupe import merge_duplicates
import re

URL="https://sbi.bank.in/web/careers/current-openings"

def scrape(session=None):
    s,_=soup(URL,session,timeout=45)
    candidates=[]
    for row in s.find_all(["tr","li","div"]):
        text=clean_text(row.get_text(" ",strip=True))
        links=row.find_all("a",href=True)
        if len(text)<25 or not links: continue
        pdfs=[(clean_text(a.get_text(" ",strip=True)),absolute(URL,a["href"])) for a in links if is_pdf(absolute(URL,a["href"]))]
        if not pdfs or not is_recruitment(text): continue

        row_start,row_end=application_window(text)
        app_url=None
        for a in links:
            tt=clean_text(a.get_text(" ",strip=True)).lower()
            if "apply online" in tt or tt=="apply" or "apply now" in tt or "registration" in tt:
                app_url=absolute(URL,a["href"]); break

        for _,pdf_url in pdfs:
            try: pdf=pdf_text(pdf_url,session)
            except Exception: pdf=""
            if pdf and not is_recruitment(text,pdf): continue

            title=title_from_pdf(pdf,text)
            if not title or is_language_only(title): continue
            start,end=application_window(text+"\n"+pdf)
            start=start or row_start; end=end or row_end
            adv=advertisement_no(pdf) or advertisement_no(text)

            d=Job(
                job_id=make_job_id("sbi",title,adv or pdf_url),
                organization="State Bank of India",title=title,
                job_type="Public Sector Banking",vacancies=vacancies(pdf),
                qualification=labeled(pdf,["educational qualification","essential qualification","qualification"]),
                age_limit=labeled(pdf,["age limit","age as on"]),
                salary=labeled(pdf,["salary","emoluments","pay scale","remuneration"]),
                application_start=start,application_end=end,
                official_url=URL,notification_url=pdf_url,application_url=app_url,
                source="SBI",source_advertisement_no=adv,record_type="recruitment",
                status="open" if current_open(end) else "closed",
                content_hash=sha256_text(title,pdf[:200000],adv or pdf_url)
            ).to_dict()
            d["discovery_score"]=discovery_score(d)
            d["publication_score"]=publication_score(d)
            d["missing_fields"]=missing_fields(d)
            candidates.append(d)
    return merge_duplicates(candidates)
