from .base import *
from pipeline.normalize import parse_date

URL = "https://employmentnews.gov.in/newemp/AllJobs.aspx?k=All"

def scrape(session=None):
    s, _ = soup(URL, session)
    jobs = []
    for row in s.select("tr"):
        cells = [clean_text(x.get_text(" ", strip=True)) for x in row.find_all(["td","th"])]
        links = row.find_all("a", href=True)
        if len(cells) < 3 or not links:
            continue
        title = cells[2]
        href = absolute(URL, links[-1]["href"])
        pub = parse_date(cells[0])
        end = parse_date(cells[-1]) if len(cells) >= 4 else None
        if not title or title.lower() in ("title", "post"):
            continue
        job = Job(
            job_id=make_job_id("employment_news", title, href),
            organization=cells[1][:200],
            title=title[:300],
            job_type="Government / PSU",
            application_end=end,
            published_date=pub,
            official_url=URL,
            notification_url=href,
            source="Employment News",
            status=infer_status(end),
            content_hash=sha256_text(title, cells, href)
        )
        jobs.append(job.to_dict())
    return jobs
