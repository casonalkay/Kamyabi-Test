from .base import *
from pipeline.pdf_extract import pdf_text
from pipeline.extract import application_window,vacancies,labeled,quality,advertisement_no,title_from_pdf
from pipeline.classify import is_recruitment,is_language_only,is_current
from collections import OrderedDict
import re

URL="https://sbi.bank.in/web/careers/current-openings"

def scrape(session=None):
    s,_=soup(URL,session,timeout=45)
    candidates=[]
    for row in s.find_all(["tr","li","div"]):
        text=clean_text(row.get_text(" ",strip=True))
        links=row.find_all("a",href=True)
        if not links or len(text)<20: continue

        pdfs=[(clean_text(a.get_text(" ",strip=True)),absolute(URL,a["href"]))
              for a in links if is_pdf(absolute(URL,a["href"]))]
        if not pdfs: continue

        # Keep only rows that look like current recruitment cards.
        if not is_recruitment(text): continue

        row_start,row_end=application_window(text)
        app_url=None
        for a in links:
            tt=clean_text(a.get_text(" ",strip=True)).lower()
            if "apply online" in tt or tt=="apply" or "registration" in tt:
                app_url=absolute(URL,a["href"]); break

        for link_title,pdf_url in pdfs:
            # Ignore obvious language-only labels as titles, but still inspect the PDF.
            pdf=""
            try: pdf=pdf_text(pdf_url,session)
            except Exception: continue
            if not pdf or not is_recruitment(text,pdf): continue

            title=title_from_pdf(pdf, text[:300])
            if is_language_only(title): continue

            start,end=application_window(text+"\n"+pdf)
            start=start or row_start; end=end or row_end
            # Closed recruitment is not a current job.
            if not is_current(end): continue

            adv=advertisement_no(pdf) or advertisement_no(text)
            # Dedup English/Hindi/duplicate URLs by advertisement number or normalized core title.
            core=re.sub(r"\b(hindi|english)\b","",title,flags=re.I)
            jid=make_job_id("sbi",core,adv or pdf_url.split("/")[-1].split("?")[0])

            d=Job(
                job_id=jid, organization="State Bank of India", title=core[:300],
                job_type="Public Sector Banking", vacancies=vacancies(pdf),
                qualification=labeled(pdf,["educational qualification","essential qualification","qualification"]),
                age_limit=labeled(pdf,["age limit","age as on"]),
                salary=labeled(pdf,["salary","emoluments","pay scale","remuneration"]),
                application_start=start,application_end=end,
                official_url=URL,notification_url=pdf_url,application_url=app_url,
                source="SBI",source_advertisement_no=adv,record_type="recruitment",
                status="open",content_hash=sha256_text(core,pdf[:200000],adv or pdf_url)
            ).to_dict()
            q,missing=quality(d); d["data_quality_score"]=q; d["missing_fields"]=missing
            candidates.append(d)

    # Deduplicate by job id, preferring the richest record.
    best={}
    for d in candidates:
        old=best.get(d["job_id"])
        if not old or len([x for x in d.values() if x])>len([x for x in old.values() if x]):
            best[d["job_id"]]=d
    return list(best.values())
