from pipeline.store import merge_jobs

def test_weak_record_goes_to_review():
    existing = []
    job = {
        "job_id":"x","title":"Test","organization":"Org",
        "record_type":"recruitment","notification_url":None,
        "data_quality_score":40
    }
    current, changes, review = merge_jobs(existing,[job],"2026-08-29T00:00:00+00:00")
    assert current == []
    assert len(review) == 1

def test_good_record_is_published():
    job = {
        "job_id":"x","title":"Test","organization":"Org",
        "record_type":"recruitment","notification_url":"https://example.com/a.pdf",
        "data_quality_score":80
    }
    current, changes, review = merge_jobs([], [job], "2026-08-29T00:00:00+00:00")
    assert len(current) == 1
    assert review == []
