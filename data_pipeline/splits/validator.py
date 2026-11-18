"""Independent leakage checks over actual assignment and retained label endpoints."""
from .schema import SPLITS,HORIZONS
from .matcher_policy import accepted

def validate(sources,plan,membership,policy,scaler,windows):
    failures=[]
    if plan.get("time_field")!="event_time_ms" or plan.get("local_timestamp_used",False):
        failures.append("LOCAL_TIMESTAMP_OR_WRONG_TIME_FIELD")
    if plan.get("shuffle",False):failures.append("SHUFFLE_PROHIBITED")
    for source in sources:
        target_times={r.event_time_ms for r in source.rows}
        for i,row in enumerate(source.rows):
            if (row.source_id,row.session_id,row.feature_view)!=(source.source_id,source.session_id,source.feature_view):
                failures.append("CROSS_SOURCE_OR_SESSION")
            if i and row.event_time_ms<source.rows[i-1].event_time_ms:
                failures.append("UNSORTED_EVENT_TIME")
            for h in HORIZONS:
                label=source.labels[h][i]
                if label.valid_label and (label.target_event_time_ms not in target_times or
                    label.target_event_time_ms<row.event_time_ms+h or
                    label.match_error_ms!=label.target_event_time_ms-row.event_time_ms-h):
                    failures.append("CROSS_SESSION_OR_INVALID_TARGET")
    raw=membership["raw"];included=membership["included"]
    row_splits={};event_splits={};split_times={s:[] for s in SPLITS}
    for view,source,session,index,t,event,split in raw:
        key=(source,session,index)
        if key in row_splits:failures.append("SPLIT_ROW_OVERLAP")
        row_splits[key]=split
        event_splits.setdefault((source,session,event),set()).add(split)
        split_times[split].append(t)
    if any(len(x)>1 for x in event_splits.values()):failures.append("EVENT_IDENTITY_OVERLAP")
    for a,b in zip(SPLITS,SPLITS[1:]):
        if not split_times[a] or not split_times[b] or max(split_times[a])>=min(split_times[b]):
            failures.append("TIME_ORDER_"+a+"_"+b)
    lookup={(s.source_id,s.session_id,row.record_index):(s,i,row)
            for s in sources for i,row in enumerate(s.rows)}
    retained=set()
    for split,records in included.items():
        boundary=plan["boundaries"][SPLITS.index(split)] if split!="Final Holdout" else None
        for view,sid,session,index,t,event,h,target,claimed in records:
            key=(sid,session,index)
            if claimed!=split or row_splits.get(key)!=split:failures.append("SOURCE_ROW_OVERLAP")
            labelkey=(key,h)
            if labelkey in retained:failures.append("DUPLICATE_LABEL_INDEX")
            retained.add(labelkey)
            if key not in lookup or h not in HORIZONS:
                failures.append("CROSS_SOURCE_OR_SESSION")
                continue
            source,i,row=lookup[key];label=source.labels[h][i]
            if row.event_time_ms!=t or row.feature_view!=view or row.event_identity!=event:
                failures.append("EVENT_IDENTITY_MISMATCH")
            if not label.valid_label or label.target_event_time_ms!=target:
                failures.append("INVALID_OR_CHANGED_LABEL")
            if target is None or (boundary is not None and target>=boundary):
                failures.append("TARGET_WINDOW_LEAKAGE")
            if not accepted(label.match_error_ms,h,policy):failures.append("MATCH_ERROR_POLICY_VIOLATION")
    if policy.get("test_data_used_for_selection") or policy.get("final_holdout_used_for_selection"):
        failures.append("HOLDOUT_OR_TEST_POLICY_SELECTION")
    if policy.get("selection_data_scope",{}).get("name")!="TRAINING_CANDIDATE_REGION":
        failures.append("POLICY_SCOPE_NOT_TRAINING")
    for info in policy.get("selection_data_scope",{}).get("per_horizon",{}).values():
        train_sources={r["source_id"] for r in plan["assignments"]["Train"]}
        if not set(info["source_ids"])<=train_sources:failures.append("POLICY_SOURCE_OUTSIDE_TRAIN")
        if info["target_end"]>=plan["boundaries"][0]:failures.append("POLICY_TARGET_OUTSIDE_TRAIN")
    if scaler["fit_split"]!="Train" or scaler["fit_per_split"] or scaler["fit_executed"]:
        failures.append("SCALER_NOT_TRAIN_ONLY")
    holdout_start=min(split_times["Final Holdout"]) if split_times["Final Holdout"] else 0
    test_start=min(split_times["Test"]) if split_times["Test"] else 0
    for window in windows:
        if window["holdout_used"] or window["validation"]["event_time_end"]>=holdout_start:
            failures.append("WALK_FORWARD_HOLDOUT")
        if window["train"]["event_time_end"]>=window["validation"]["event_time_start"]:
            failures.append("WALK_FORWARD_TIME_ORDER")
        if window["validation"]["event_time_end"]>=test_start:
            failures.append("WALK_FORWARD_FORMAL_TEST")
        for stats in window["match_error_policy"]["selection_data_scope"]["per_horizon"].values():
            if stats["target_end"]>=window["validation"]["event_time_start"]:
                failures.append("WALK_FORWARD_POLICY_LOOKAHEAD")
    counts={s:{str(h):sum(r[6]==h for r in included[s]) for h in HORIZONS} for s in SPLITS}
    return {"status":"PASS" if not failures else "LEAKAGE_DETECTED",
            "failures":sorted(set(failures)),"raw_row_count":len(raw),
            "included_label_count":len(retained),"counts_by_split_horizon":counts,
            "time_ranges":{s:{"start":min(v) if v else None,"end":max(v) if v else None}
                           for s,v in split_times.items()},
            "row_overlap_count":len(raw)-len(row_splits),
            "event_overlap_count":sum(len(x)>1 for x in event_splits.values()),
            "local_timestamp_used":False,"class_labels":False,
            "target_identity_check":"input loader confirms first target inside the same source/session",
            "scaler_fitted":False}
