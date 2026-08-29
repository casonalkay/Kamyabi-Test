from .base import *
from pipeline.extract import application_window, quality, first_date_in

URL="https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All"

def scrape(session=None):
    s,_=soup(URL,session)
    jobs=[]
    for row in s.select("tr"):
        cells=[clean_text(x.get_text(" ",strip=True)) for x in row.find_all(["td","th"])]
        links=row.find_all("a",href=True)
        if len(cells)<4 or not links: continue
        title=cells[2]
        if not title or title.lower() in ("post","title"): continue
        hrefs=[absolute(URL,a["href"]) for a in links]
        direct=next((h for h in hrefs if h!=URL and "alljobs.aspx?k=all" not in h.lower()),None)
        if not direct: continue
        # Employment News is a discovery layer; notification target must be direct.
        d=Job(
            job_id=make_job_id("employment_news",title,direct),
            organization=cells[1][:200],
            title=title[:300],
            job_type="Government / PSU",
            application_end=first_date_in(cells[-1]),
            published_date=None,
            official_url=URL,
            notification_url=direct,
            source="Employment News",
            record_type="recruitment",
            status="unknown",
            content_hash=sha256_text(title,cells,direct)
        ).to_dict()
        q,missing=quality(d); d["data_quality_score"]=q; d["missing_fields"]=missing
        # Do not publish unless there is at least a direct notification and an identifiable closing date.
        if d["notification_url"]:
            jobs.append(d)
    return jobs
