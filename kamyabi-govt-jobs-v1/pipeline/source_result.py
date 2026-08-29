def result(source,candidates,status="ok",error=None):
    return {"source":source,"status":status,"candidates":len(candidates),
            "error":error,"candidate_records":candidates}
