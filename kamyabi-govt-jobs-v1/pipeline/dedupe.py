import re, hashlib

def norm_title(s):
    s=re.sub(r"\b(hindi|english)\b","",s or "",flags=re.I)
    s=re.sub(r"\s+"," ",s).strip().lower()
    return s

def identity(job):
    adv=(job.get("source_advertisement_no") or "").strip().lower()
    if adv:
        return f'{job.get("source","")}|adv|{adv}'
    title=norm_title(job.get("title"))
    end=job.get("application_end") or ""
    return f'{job.get("source","")}|title|{title}|end|{end}'

def merge_duplicates(jobs):
    groups={}
    for j in jobs:
        groups.setdefault(identity(j),[]).append(j)
    result=[]
    for key,items in groups.items():
        # Merge non-null fields, prefer longest/richest values.
        best=max(items,key=lambda x:sum(bool(v) for v in x.values()))
        merged=dict(best)
        for item in items:
            for k,v in item.items():
                if v and not merged.get(k): merged[k]=v
        result.append(merged)
    return result
