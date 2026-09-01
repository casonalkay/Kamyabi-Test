from pipeline.change_detector import diff, content_hash
from pipeline.store import merge_jobs


def test_diff_detects_deadline_change():
    old = {"title": "Test", "application_end": "2026-09-01"}
    new = {"title": "Test", "application_end": "2026-09-05"}
    changes = diff(old, new)
    assert any(x["field"] == "application_end" for x in changes)


def test_hash_changes_when_content_changes():
    a = {"title": "A", "application_end": "2026-09-01"}
    b = {"title": "A", "application_end": "2026-09-02"}
    assert content_hash(a) != content_hash(b)


def test_legacy_non_vacancy_records_are_removed():
    existing = [
        {"job_id": "old", "title": "LIST OF CANDIDATES PROVISIONALLY SELECTED", "record_type": "other"},
        {"job_id": "good", "title": "Recruitment", "record_type": "recruitment"},
    ]
    merged = merge_jobs(existing, [], "2026-08-29T00:00:00+00:00")[0]
    assert [x["job_id"] for x in merged] == ["good"]


def test_publishability_rejects_generic_ibps_homepage_record():
    from scrapers.base import is_publishable
    job = {
        "title": "RECRUITMENT EXAMS",
        "record_type": "recruitment",
        "official_url": "https://www.ibps.in/",
        "notification_url": "https://www.ibps.in/",
        "application_end": None,
        "status": "unknown",
    }
    ok, reason = is_publishable(job)
    assert not ok
    assert reason in ("generic_title", "missing_direct_notification")

def test_publishability_requires_direct_notification():
    from scrapers.base import is_publishable
    job = {
        "title": "Test Recruitment",
        "record_type": "recruitment",
        "official_url": "https://example.gov.in",
        "notification_url": "https://example.gov.in",
        "application_end": "2026-09-01",
        "status": "open",
    }
    ok, reason = is_publishable(job)
    assert not ok
    assert reason == "missing_direct_notification"
