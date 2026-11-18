"""Source/session aware raw assignments and horizon-specific eligible indices."""
from collections import Counter
from .schema import HORIZONS,SPLITS,SMOKE_SOURCE
from .policy import locate
from .matcher_policy import accepted
from .purge import crosses_boundary

def _region(row,plan,split):
    regions=[x for x in plan["assignments"][split]
             if x["source_id"]==row.source_id and x["session_id"]==row.session_id
             and x["start"]<=row.event_time_ms<x["end_exclusive"]]
    if len(regions)!=1:raise ValueError("CROSS_SOURCE_OR_SESSION_REGION")
    return regions[0]

def training_candidates(sources,plan):
    candidates={h:[] for h in HORIZONS}
    for source in sorted(sources,key=lambda s:(s.rows[0].event_time_ms,s.source_id)):
        if source.source_id==SMOKE_SOURCE:continue
        for i,row in enumerate(source.rows):
            regions=[r for r in plan["assignments"]["Train"]
                     if r["source_id"]==row.source_id and r["session_id"]==row.session_id
                     and r["start"]<=row.event_time_ms<r["end_exclusive"]]
            if not regions:continue
            if len(regions)!=1:raise ValueError("OVERLAPPING_TRAINING_REGIONS")
            end=regions[0]["end_exclusive"]
            for h in HORIZONS:
                label=source.labels[h][i]
                if label.valid_label and label.target_event_time_ms is not None and label.target_event_time_ms<end:
                    candidates[h].append({"source_id":row.source_id,"session_id":row.session_id,
                                          "record_index":row.record_index,"current_event_time_ms":row.event_time_ms,
                                          "target_event_time_ms":label.target_event_time_ms,
                                          "match_error_ms":label.match_error_ms,
                                          "training_end_exclusive":end,"split":"Train","is_holdout":False})
    return candidates

def build_membership(sources,plan,policy):
    raw=[];included={s:[] for s in SPLITS};excluded=[]
    entries={s:{} for s in SPLITS}
    purge={s:{str(h):{"split":s,"horizon":h,"before_count":0,"purged_count":0,
                           "after_count":0,"first_purged_event_time":None,
                           "last_purged_event_time":None,
                           "reason":"PURGED_LABEL_WINDOW_CROSSES_SPLIT"} for h in HORIZONS}
           for s in SPLITS}
    for source in sorted(sources,key=lambda s:(s.rows[0].event_time_ms,s.source_id)):
        if source.source_id==SMOKE_SOURCE:continue
        for i,row in enumerate(source.rows):
            split=locate(row,plan)
            region=_region(row,plan,split)
            boundary=plan["boundaries"][SPLITS.index(split)] if split!="Final Holdout" else None
            raw.append((row.feature_view,row.source_id,row.session_id,row.record_index,
                        row.event_time_ms,row.event_identity,split))
            entry=entries[split].setdefault(source.source_id,{
                "feature_view":row.feature_view,"source_id":row.source_id,"session_id":row.session_id,
                "event_time_start":row.event_time_ms,"event_time_end":row.event_time_ms,
                "raw_rows":0,"source_feature_hash":source.feature_sha256,
                "source_label_hash":source.label_sha256,
                "per_horizon":{str(h):{"valid_label_rows":0,"invalid_label_rows":0,
                                      "match_error_filtered_rows":0,"purged_rows":0,"final_rows":0}
                               for h in HORIZONS}})
            entry["raw_rows"]+=1;entry["event_time_end"]=row.event_time_ms
            for h in HORIZONS:
                label=source.labels[h][i]
                rec=(row.feature_view,row.source_id,row.session_id,row.record_index,
                     row.event_time_ms,row.event_identity,h,label.target_event_time_ms,split)
                count=entry["per_horizon"][str(h)]
                pr=purge[split][str(h)]
                reason=""
                if not label.valid_label:
                    count["invalid_label_rows"]+=1
                    reason=label.invalid_reason or "INVALID_LABEL"
                else:
                    count["valid_label_rows"]+=1
                    pr["before_count"]+=1
                    if crosses_boundary(row.event_time_ms,label.target_event_time_ms,boundary):
                        count["purged_rows"]+=1;pr["purged_count"]+=1
                        if pr["first_purged_event_time"] is None:pr["first_purged_event_time"]=row.event_time_ms
                        pr["last_purged_event_time"]=row.event_time_ms
                        reason="PURGED_LABEL_WINDOW_CROSSES_SPLIT"
                    elif not accepted(label.match_error_ms,h,policy):
                        count["match_error_filtered_rows"]+=1
                        reason="MATCH_ERROR_EXCEEDS_FROZEN_POLICY"
                    else:
                        included[split].append(rec);count["final_rows"]+=1
                if reason:excluded.append((*rec,reason))
    for s in SPLITS:
        for h in HORIZONS:
            p=purge[s][str(h)];p["after_count"]=p["before_count"]-p["purged_count"]
    return {"raw":raw,"included":included,"excluded":excluded,
            "entries":{s:list(entries[s].values()) for s in SPLITS},
            "purge_report":purge}
