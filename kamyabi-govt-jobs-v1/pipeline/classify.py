import re
BAD = (
    "result", "selected", "selection list", "shortlist", "interview schedule",
    "admit card", "answer key", "score card", "provisional allotment",
    "joining", "wait list", "cut off", "cut-off", "marks", "call letter"
)
GOOD = (
    "recruitment", "advertisement", "vacancy", "vacancies", "engagement",
    "online application", "apply online", "common recruitment process",
    "notification for", "invited applications", "posts"
)

def is_recruitment(title, body=""):
    text=(title+" "+body).lower()
    if any(x in text for x in BAD):
        return False
    return any(x in text for x in GOOD)
