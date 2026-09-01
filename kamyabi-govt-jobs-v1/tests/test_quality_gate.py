from pipeline.store import merge_jobs

def test_weak_record_is_review():
    j={"job_id":"x","title":"Test","organization":"Org","record_type":"recruitment","notification_url":None,"data_quality_score":40}
    current,changes,review,pub=merge_jobs([], [j], "2026-08-29T00:00:00+00:00")
    assert not current and len(review)==1

def test_good_record_publishes():
    j={"job_id":"x","title":"Recruitment of Test","organization":"Org","record_type":"recruitment","official_url":"https://example.com","notification_url":"https://example.com/a.pdf","application_end":"2999-12-31"}
    current,changes,review,pub=merge_jobs([], [j], "2026-08-29T00:00:00+00:00")
    assert len(current)==1 and not review
