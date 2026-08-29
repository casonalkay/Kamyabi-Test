import hashlib
from datetime import datetime

TRACKED = [
    "title", "vacancies", "qualification", "age_limit", "salary",
    "application_start", "application_end", "exam_date",
    "official_url", "notification_url", "source_advertisement_no"
]

def content_hash(job):
    payload = "|".join(str(job.get(k) or "") for k in TRACKED)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def diff(old, new):
    changes = []
    for k in TRACKED:
        if (old.get(k) or "") != (new.get(k) or ""):
            changes.append({"field": k, "old": old.get(k), "new": new.get(k)})
    return changes
