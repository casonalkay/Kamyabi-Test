from .base import *
from pipeline.normalize import parse_date

URL = "https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All"

def _direct_link(row, base):
    for a in row.find_all("a", href=True):
        href = absolute(base, a["href"])
        label = clean_text(a.get_text(" ", strip=True)).lower()
        if is_pdf(href) or ".pdf" in href.lower() or "download" in label or "view" in label:
            if href != base and "alljobs.aspx" not in href.lower():
                return href
    return None

def scrape(session=None):
    s,_=soup(URL,session)
    jobs=[]
    for row in s.select("tr"):
        cells=[clean_text(x.get_text(" ",strip=True)) for x in row.find_all(["td","th"])]
        if len(cells)<5:
            continue
        title=cells[2]
        org=cells[1]
        method=cells[3]
        if not title or title.lower() in ("post","title"):
            continue
        low = f"{title} {method}".lower()
        if any(x in low for x in ("result", "merit list", "selection list", "corrigendum", "answer key")):
            continue
        if "recruit" not in low and "deputation" not in low and "engagement" not in low:
            continue

        href=_direct_link(row, URL)
        # Employment News is an aggregator. Do not publish a record when the
        # row does not expose a direct notification/application target.
        if not href:
            continue

        pub=parse_date(cells[0])
        end=parse_date(cells[4])
        if not end:
            continue

        j=Job(
            job_id=make_job_id("employment_news",title,org),
            organization=org[:250],
            title=title[:300],
            job_type="Government / PSU",
            application_end=end,
            published_date=pub,
            official_url=URL,
            source_page_url=URL,
            notification_url=href,
            source="Employment News",
            record_type="recruitment",
            status=infer_status(end),
            content_hash=sha256_text(title,org,method,pub,end,href)
        )
        d=j.to_dict(); j.data_quality_score,j.missing_fields=quality_score(d)
        jobs.append(j.to_dict())
    return jobs
