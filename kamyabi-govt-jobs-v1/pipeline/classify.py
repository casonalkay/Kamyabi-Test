import re

BAD=(
    "result","selected","selection list","shortlist","interview schedule",
    "admit card","answer key","score card","provisional allotment",
    "joining","wait list","cut off","cut-off","marks","call letter",
    "corrigendum","cancellation","withdrawal","response sheet"
)
LANG_ONLY=re.compile(r"^(hindi|english|हिंदी|अंग्रेज़ी)(?:\s*/.*)?$",re.I)
GOOD=(
    "recruitment","advertisement","vacancy","vacancies","engagement",
    "online application","apply online","common recruitment process",
    "notification for","invited applications","posts"
)

def is_language_only(title):
    return bool(LANG_ONLY.match((title or "").strip()))

def is_recruitment(title,body=""):
    text=(title+" "+body).lower()
    if is_language_only(title): return False
    if any(x in text for x in BAD): return False
    return any(x in text for x in GOOD)

def is_current(end_date, today=None):
    from datetime import date
    if not end_date: return False
    try:
        return date.fromisoformat(end_date) >= (today or date.today())
    except: return False
