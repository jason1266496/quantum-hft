"""Expanding-window specifications; each fold selects policy from its own Train."""
from .schema import HORIZONS
from .policy import time_boundaries
from .splitter import training_candidates
from .matcher_policy import choose_policy,accepted
from .purge import crosses_boundary

def _count(sources,regions,policy):
    counts={str(h):{"raw_rows":0,"valid_labels":0,"purged_rows":0,
                     "match_error_filtered_rows":0,"final_rows":0} for h in HORIZONS}
    times=[]
    for source in sources:
        for i,row in enumerate(source.rows):
            found=[r for r in regions if r["source_id"]==row.source_id and r["session_id"]==row.session_id
                   and r["start"]<=row.event_time_ms<r["end_exclusive"]]
            if not found:continue
            if len(found)!=1:raise ValueError("WALK_FORWARD_REGION_OVERLAP")
            times.append(row.event_time_ms);end=found[0]["end_exclusive"]
            for h in HORIZONS:
                c=counts[str(h)];c["raw_rows"]+=1
                label=source.labels[h][i]
                if not label.valid_label:continue
                c["valid_labels"]+=1
                if crosses_boundary(row.event_time_ms,label.target_event_time_ms,end):c["purged_rows"]+=1
                elif not accepted(label.match_error_ms,h,policy):c["match_error_filtered_rows"]+=1
                else:c["final_rows"]+=1
    return {"event_time_start":min(times),"event_time_end":max(times),"counts":counts}

def build_windows(sources,plan):
    view=plan["feature_view"];specs=[]
    if view=="aggregate_core_v1":
        regions=plan["assignments"]["Train"]+plan["assignments"]["Validation"]
        for n in range(2,len(regions)):
            specs.append((regions[:n],regions[n:n+1]))
    else:
        source=next(s for s in sources if s.source_id=="replay_events_50000")
        times=[r.event_time_ms for r in source.rows]
        _,cuts=time_boundaries(times,(40,60,80))
        for start_val,end_val in ((cuts[0],cuts[1]),(cuts[1],cuts[2])):
            specs.append(([{"source_id":source.source_id,"session_id":source.session_id,
                            "start":times[0],"end_exclusive":start_val}],
                          [{"source_id":source.source_id,"session_id":source.session_id,
                            "start":start_val,"end_exclusive":end_val}]))
    windows=[]
    for number,(train,val) in enumerate(specs,1):
        folded={"assignments":{"Train":train,"Validation":val}}
        policy=choose_policy(training_candidates(sources,folded),view)
        if policy["status"]!="PASS":raise ValueError("WALK_FORWARD_NEED_POLICY_REVIEW")
        windows.append({"window_id":number,"feature_view":view,"train_regions":train,
                        "validation_regions":val,"train":_count(sources,train,policy),
                        "validation":_count(sources,val,policy),
                        "match_error_policy":policy,"holdout_used":False,"test_used":False,
                        "models_trained":False,"purge_uses_actual_target_event_time":True})
    return windows
