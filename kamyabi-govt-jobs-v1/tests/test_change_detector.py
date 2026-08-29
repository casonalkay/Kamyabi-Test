from pipeline.change_detector import diff, content_hash

def test_diff_detects_deadline_change():
    old = {"title":"Test","application_end":"2026-09-01"}
    new = {"title":"Test","application_end":"2026-09-05"}
    changes = diff(old, new)
    assert any(x["field"] == "application_end" for x in changes)

def test_hash_changes_when_content_changes():
    a = {"title":"A","application_end":"2026-09-01"}
    b = {"title":"A","application_end":"2026-09-02"}
    assert content_hash(a) != content_hash(b)
