import re
BAD=(
    "result","selected","selection list","shortlist","interview schedule","interview call",
    "admit card","answer key","score card","provisional allotment","joining","wait list",
    "cut off","cut-off","marks","call letter","corrigendum","cancellation","withdrawal",
    "response sheet","document verification"
)
LANG_ONLY=re.compile(r"^(hindi|english|हिंदी|अंग्रेज़ी)(?:\s*/.*)?$",re.I)
GOOD=("recruitment","advertisement","vacancy","vacancies","engagement","online application",
      "apply online","common recruitment process","notification for","invited applications",
      "posts","cadre officer","junior associate","probationary officer")

def is_language_only(title): return bool(LANG_ONLY.match((title or "").strip()))

def is_recruitment(title,body=""):
    text=(title+" "+body).lower()
    if is_language_only(title): return False
    if any(x in text for x in BAD): return False
    return any(x in text for x in GOOD)

def current_open(end_date):
    from datetime import date
    if not end_date:return False
    try:return date.fromisoformat(end_date)>=date.today()
    except:return False
