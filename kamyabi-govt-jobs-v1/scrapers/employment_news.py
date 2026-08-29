from .base import *
from pipeline.extract import first_date_in,quality
from pipeline.classify import is_current

URL="https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All"

def scrape(session=None):
    s,_=soup(URL,session,timeout=30)
    jobs=[]
    for row in s.select("tr"):
        cells=[clean_text(x.get_text(" ",strip=True)) for x in row.find_all(["td","th"])]
        links=row.find_all("a",href=True)
        if len(cells)<4 or not links: continue
        title=cells[2]
        if not title or title.lower() in ("post","title"): continue
        hrefs=[absolute(URL,a["href"]) for a in links]
        direct=next((h for h in hrefs if h!=URL and "alljobs.aspx?k=all" not in h.lower()),None)
        end=first_date_in(cells[-1])
        if not direct or not end or not is_current(end): continue
        d=Job(
            job_id=make_job_id("employment_news",title,direct),
            organization=cells[1][:200],title=title[:300],
            job_type="Government / PSU",application_end=end,
            official_url=URL,notification_url=direct,
            source="Employment News",record_type="recruitment",
            status="open",content_hash=sha256_text(title,cells,direct)
        ).to_dict()
        q,missing=quality(d); d["data_quality_score"]=q; d["missing_fields"]=missing
        jobs.append(d)
    return jobs
