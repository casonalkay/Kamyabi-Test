from pipeline.extract import application_window, parse_one_date, vacancies, quality
from pipeline.classify import is_current

def test_sbi_date_range():
    text="Apply Online from 29.08.2026 TO 19.09.2026 ADVERTISEMENT NO: CRPD/SCO/2026-27/15"
    assert application_window(text)==("2026-08-29","2026-09-19")

def test_date_label():
    assert parse_one_date("19-09-2026")=="2026-09-19"

def test_vacancy():
    assert vacancies("Total Vacancies: 250") == 250

def test_quality_helper_and_is_current_alias():
    score,missing=quality({"title":"X","record_type":"recruitment","notification_url":"https://example.com/n.pdf"})
    assert score>=0 and isinstance(missing,list)
    assert is_current("2999-01-01")
