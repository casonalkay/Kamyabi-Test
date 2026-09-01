from pipeline.extract import application_window, parse_one_date, quality, vacancies

def test_sbi_date_range():
    text="Apply Online from 29.08.2026 TO 19.09.2026 ADVERTISEMENT NO: CRPD/SCO/2026-27/15"
    assert application_window(text)==("2026-08-29","2026-09-19")

def test_date_label():
    assert parse_one_date("19-09-2026")=="2026-09-19"

def test_vacancy():
    assert vacancies("Total Vacancies: 250") == 250

def test_quality_compatibility():
    score, missing = quality({"title":"Test","organization":"Org","notification_url":"https://example.com/a.pdf","application_end":"2999-12-31","record_type":"recruitment"})
    assert score >= 80
    assert "vacancies" in missing
