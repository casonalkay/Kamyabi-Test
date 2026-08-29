from .base import *
from pipeline.normalize import parse_date
from pipeline.fields import infer_quality

URL = "https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All"

def scrape(session=None):
    s, _ = soup(URL, session)
    jobs = []
    for row in s.select("tr"):
        cells = [clean_text(x.get_text(" ", strip=True)) for x in row.find_all(["td","th"])]
        links = row.find_all("a", href=True)
        if len(cells) < 4 or not links: continue
        title = cells[2]
        if not title or title.lower() in ("post","title"):
            continue
        # Prefer a direct item/notification link. If the table only points to the listing,
        # don't publish the record.
        hrefs = [absolute(URL,a["href"]) for a in links]
        direct = next((h for h in hrefs if h != URL and not h.lower().endswith("alljobs.aspx?k=all")), None)
        if not direct: continue
        pub = parse_date(cells[0])
        end = parse_date(cells[-1])
        d = Job(
            job_id=make_job_id("employment_news", title, direct),
            organization=cells[1][:200],
            title=title[:300],
            job_type="Government / PSU",
            application_end=end,
            published_date=pub,
            official_url=URL,
            notification_url=direct,
            source="Employment News",
            record_type="recruitment",
            status=infer_status(end),
            content_hash=sha256_text(title, cells, direct)
        ).to_dict()
        q, missing = infer_quality(d)
        d["data_quality_score"], d["missing_fields"] = q, missing
        jobs.append(d)
    return jobs
