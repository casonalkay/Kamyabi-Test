from pipeline.extract import application_window, vacancies, advertisement_no, clean_title
from pipeline.classify import is_language_only, is_recruitment
from pipeline.dedupe import merge_duplicates

def test_sbi_dates():
    assert application_window("Apply Online from 29.08.2026 TO 19.09.2026")==("2026-08-29","2026-09-19")

def test_language_and_title():
    assert is_language_only("Hindi")
    assert not is_recruitment("Hindi")
    assert clean_title("RECRUITMENT OF TEST (Apply Online from 01.08.2026 to 10.08.2026) DOWNLOAD ADVERTISEMENT APPLY ONLINE")=="RECRUITMENT OF TEST"

def test_vacancy_and_ad():
    assert vacancies("Total Vacancies: 6,589")==6589
    assert advertisement_no("ADVERTISEMENT NO: CRPD/CR/2026-27/17")=="CRPD/CR/2026-27/17"

def test_dedupe_by_advertisement():
    a={"job_id":"1","source":"SBI","source_advertisement_no":"CRPD/X/2026-27/1","title":"English","application_end":"2026-09-19","notification_url":"x"}
    b={"job_id":"2","source":"SBI","source_advertisement_no":"CRPD/X/2026-27/1","title":"Hindi","application_end":"2026-09-19","notification_url":"x","vacancies":100}
    out=merge_duplicates([a,b])
    assert len(out)==1 and out[0]["vacancies"]==100
