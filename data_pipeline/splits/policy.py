"""Boundary rules fixed from source chronology and feature timestamp metadata."""
from bisect import bisect_left
from .schema import SPLITS,SMOKE_SOURCE

def time_boundaries(times,percentages=(60,80,90)):
    if not times or any(times[i]<times[i-1] for i in range(1,len(times))):
        raise ValueError("UNSORTED_EVENT_TIME")
    start,end=times[0],times[-1]
    requested=[start+(end-start)*p//100 for p in percentages]
    chosen=[]
    for value in requested:
        index=bisect_left(times,value)
        if index==0 or index==len(times):
            raise ValueError("EMPTY_TIME_SPLIT")
        chosen.append(times[index])
    if len(set(chosen))!=len(chosen):
        raise ValueError("EMPTY_TIME_SPLIT")
    return requested,chosen

def whole_session_plan(sources):
    ordered=sorted((s for s in sources if s.source_id!=SMOKE_SOURCE),
                   key=lambda s:(s.rows[0].event_time_ms,s.source_id))
    if len(ordered)<4:
        raise ValueError("INSUFFICIENT_INDEPENDENT_SESSIONS")
    for left,right in zip(ordered,ordered[1:]):
        if left.rows[-1].event_time_ms>=right.rows[0].event_time_ms:
            raise ValueError("OVERLAPPING_SOURCE_INTERVAL")
    groups={SPLITS[0]:ordered[:-3],SPLITS[1]:ordered[-3:-2],
            SPLITS[2]:ordered[-2:-1],SPLITS[3]:ordered[-1:]}
    assignments={}
    for split,items in groups.items():
        assignments[split]=[{"source_id":s.source_id,"session_id":s.session_id,
                             "start":s.rows[0].event_time_ms,"end_exclusive":s.rows[-1].event_time_ms+1}
                            for s in items]
    boundaries=[assignments[x][0]["start"] for x in SPLITS[1:]]
    counts={k:sum(len(s.rows) for s in v) for k,v in groups.items()}
    candidate_a={SPLITS[0]:sum(len(s.rows) for s in ordered[:-4]),
                 SPLITS[1]:len(ordered[-4].rows),
                 SPLITS[2]:sum(len(s.rows) for s in ordered[-3:-1]),
                 SPLITS[3]:len(ordered[-1].rows)} if len(ordered)>=5 else counts
    return {"feature_view":"aggregate_core_v1","chosen":"B_COMPLETE_SESSION_EARLY_EXPANDING_TRAIN",
            "assignments":assignments,"boundaries":boundaries,
            "candidate_A_raw_counts":candidate_a,"candidate_B_raw_counts":counts,
            "rationale":"B preserves entire sessions, uses all earliest sessions for Train, leaves separate later sessions for Validation and Test, and locks the latest independent compatible source. Candidate A has smaller Train than both Validation/Test; no outcome or retention was used to pick boundaries.",
            "smoke_only_sources":[SMOKE_SOURCE],"time_field":"event_time_ms",
            "session_continuation_assumed":False,"holdout_outcomes_used":False}

def depth_plan(source):
    times=[r.event_time_ms for r in source.rows]
    requested,chosen=time_boundaries(times)
    alt_requested,alt=time_boundaries(times,(70,85,95))
    edges=[times[0],*chosen,times[-1]+1]
    assignments={split:[{"source_id":source.source_id,"session_id":source.session_id,
                         "start":edges[i],"end_exclusive":edges[i+1]}]
                 for i,split in enumerate(SPLITS)}
    counts={split:sum(edges[i]<=t<edges[i+1] for t in times) for i,split in enumerate(SPLITS)}
    return {"feature_view":"depth_top5_v1","chosen":"TIME_60_20_10_10",
            "candidate_boundaries":{"60_20_10_10":{"requested":requested,"chosen":chosen},
                                     "70_15_10_5":{"requested":alt_requested,"chosen":alt}},
            "chosen_boundaries":chosen,"boundaries":chosen,"assignments":assignments,
            "sample_counts_before_purge":counts,"time_field":"event_time_ms",
            "rationale":"Only one large Replay session is available. Use the requested initial 60/20/10/10 fractions of elapsed event time, snap forward to an observed timestamp, and place all equal timestamps on one side. No label outcome or holdout retention selected these boundaries.",
            "smoke_only_sources":[SMOKE_SOURCE],"holdout_outcomes_used":False}

def locate(row,plan):
    found=[]
    for split,ranges in plan["assignments"].items():
        for region in ranges:
            if (row.source_id==region["source_id"] and row.session_id==region["session_id"]
                    and region["start"]<=row.event_time_ms<region["end_exclusive"]):
                found.append(split)
    if len(found)!=1:
        raise ValueError("ROW_MUST_HAVE_EXACTLY_ONE_SPLIT")
    return found[0]

def scaler_policy():
    return {"fit_split":"Train","transform_only_splits":["Validation","Test","Final Holdout"],
            "independent_per_feature_view":True,"fit_per_split":False,
            "all_data_statistics_forbidden":True,"parameters_must_be_versioned":True,
            "excluded_columns":["event_time_ms","record_index","source_id","session_id","event_identity"],
            "fit_executed":False,"implementation_phase":"Phase 3"}

def embargo_policy():
    return {"embargo_ms":0,"status":"NO_ADDITIONAL_EMBARGO_BEYOND_PURGING",
            "rationale":"Phase 2C features use only the current book (no rolling feature lookback); actual label-end purging removes split boundary overlap. Within-split overlapping targets remain dependent and must be considered in later evaluation.",
            "test_or_holdout_performance_used":False}
