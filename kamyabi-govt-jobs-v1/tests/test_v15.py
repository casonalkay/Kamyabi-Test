from pipeline.extract import application_window, vacancies, title_from_pdf
from pipeline.classify import is_language_only, is_recruitment

def test_sbi_window():
    assert application_window("Apply Online from 29.08.2026 TO 19.09.2026")==("2026-08-29","2026-09-19")

def test_language_title_rejected():
    assert is_language_only("Hindi")
    assert not is_recruitment("Hindi")

def test_vacancy_count():
    assert vacancies("Total Vacancies: 6,589") == 6589

def test_title_from_pdf():
    assert title_from_pdf("STATE BANK OF INDIA\nJunior Associate (Customer Support & Sales)\nDetailed Advertisement") == "Junior Associate (Customer Support & Sales)"
