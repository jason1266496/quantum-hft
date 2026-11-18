"""Decode only frozen selected IDs and their same-session endpoint witnesses."""
import csv
from decimal import Decimal
import numpy as np
from data_pipeline.datasets.schema import sample_id
from experiments.phase4b0.audit import project,current_formula_errors
from . import contracts as c
from experiments.phase4a1 import contracts as old
def required(row,key):
    if key not in row or row[key] is None or row[key]=="":raise ValueError("MISSING_"+key.upper())
    return row[key]
def parse_selected(row,member):
    keys=("sample_id","source_id","session_id","record_index","event_time_ms","local_update_id","target_event_time_ms","requested_horizon_ms","actual_horizon_ms","match_error_ms","future_return_bps",*c.FEATURES)
    for k in keys:required(row,k)
    meta=project(row,member["source_Train_file_row_index"])
    if not meta["legacy_eligible"] or current_formula_errors(row):raise ValueError("INPUT_QUALITY_OR_CURRENT_FEATURE_FORMULA")
    expected={"sample_id":meta["id"],"source_id":meta["source"],"session_id":meta["session"],"record_index":meta["record"],"event_time_ms":meta["t"],
        "provided_update_id":meta["update"],"actual_target_event_time_ms":meta["end"]}
    if any(member.get(k)!=v for k,v in expected.items()):raise ValueError("FROZEN_MEMBER_METADATA_CHANGED")
    if sample_id(row)!=member["sample_id"]:raise ValueError("CANONICAL_ID_MISMATCH")
    x=np.asarray([float(row[k]) for k in c.FEATURES],dtype=np.float64)
    if not np.isfinite(x).all():raise ValueError("NONFINITE_FEATURE")
    return {"x":x,"y":old.class_of(row["future_return_bps"]),"meta":meta,"member":member}
def assemble(fold,selected):
    out={"fold_id":fold["fold_id"],"region":fold["region"],"boundary":fold["boundary"]}
    seen=set();groups=set()
    for split,n in (("Train",96),("Validation",384)):
        fm=fold[split];ids=fm["sample_ids"]
        if len(ids)!=n or len(set(ids))!=n or seen&set(ids):raise ValueError("ID_COUNT_DUPLICATE_OR_OVERLAP")
        seen.update(ids)
        if ids!=[r["sample_id"] for r in fm["members"]]:raise ValueError("MANIFEST_ID_ORDER")
        items=[]
        for member in fm["members"]:
            if member["sample_id"] not in selected:raise ValueError("MISSING_FROZEN_ROW")
            item=parse_selected(selected[member["sample_id"]],member);meta=item["meta"]
            if member["leakage_group"] in groups:raise ValueError("MARKET_GROUP_OVERLAP")
            groups.add(member["leakage_group"])
            if (meta["source"],meta["session"])!=(fold["region"]["source_id"],fold["region"]["session_id"]):raise ValueError("SOURCE_SESSION_MISMATCH")
            if split=="Train" and not meta["end"]<fold["boundary"]:raise ValueError("ACTUAL_ENDPOINT_LEAKAGE")
            if split=="Validation" and not (meta["t"]>=fold["boundary"] and meta["end"]<fold["region"]["end_exclusive"]):raise ValueError("VALIDATION_ENDPOINT_OR_TIME")
            items.append(item)
        order=[(q["meta"]["t"],q["meta"]["source"],q["meta"]["session"],q["meta"]["record"],q["meta"]["id"]) for q in items]
        if order!=sorted(order):raise ValueError("NON_TEMPORAL_INPUT_ORDER")
        x=np.asarray([q["x"] for q in items],dtype=np.float64);y=np.asarray([q["y"] for q in items],dtype=np.int64)
        if list(np.bincount(y,minlength=3))!=list(c.COUNTS[fold["fold_id"]-1][0 if split=="Train" else 1]):raise ValueError("FROZEN_CLASS_SUPPORT_CHANGED")
        out[split]={"x":x,"y":y,"ids":ids,"identity":c.identity(ids,x,y),"members":fm["members"]}
    if max(q["event_time_ms"] for q in out["Train"]["members"])>=min(q["event_time_ms"] for q in out["Validation"]["members"]):raise ValueError("TRAIN_NOT_EARLIER")
    return out
def load():
    manifest=c.parent();selected_members={};target_times=set()
    for fold in manifest["folds"]:
        for split in ("Train","Validation"):
            for member in fold[split]["members"]:
                sid=member["sample_id"]
                if sid in selected_members:raise ValueError("GLOBAL_ID_OVERLAP")
                selected_members[sid]=member
                target_times.add((member["source_id"],member["session_id"],member["actual_target_event_time_ms"]))
    assert len(selected_members)==1440
    schema=old.read(c.TRAIN.parent.parent/"dataset_schema.json")["field_order"]
    selected={};witnesses={}
    with c.TRAIN.open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=schema:raise ValueError("FEATURE_LABEL_SCHEMA_CHANGED")
        rows=0
        for index,row in enumerate(reader):
            rows+=1;sid=row["sample_id"]
            if sid in selected_members:
                if sid in selected:raise ValueError("DUPLICATE_SOURCE_ROW")
                if index!=selected_members[sid]["source_Train_file_row_index"]:raise ValueError("SOURCE_ROW_ORDINAL_CHANGED")
                selected[sid]=row
            key=(row["source_id"],row["session_id"],int(row["event_time_ms"]))
            if key in target_times:
                if key in witnesses:raise ValueError("AMBIGUOUS_TARGET_ROW")
                witnesses[key]=row
    if rows!=150912 or set(selected)!=set(selected_members):raise ValueError("TRAIN_COUNT_OR_SELECTED_IDS_CHANGED")
    if old.sha(c.TRAIN)!=old.read(c.PARENT/"split_protocol.json")["Dataset_Train_sha256"]:raise ValueError("TRAIN_SHA_CHANGED")
    for sid,row in selected.items():
        member=selected_members[sid];key=(row["source_id"],row["session_id"],int(row["target_event_time_ms"]))
        if key not in witnesses:raise ValueError("MISSING_SAME_SESSION_ENDPOINT")
        target=witnesses[key]
        if Decimal(target["mid_price"])!=Decimal(row["future_mid_price"]):raise ValueError("FUTURE_PRICE_WITNESS_MISMATCH")
        if c.digest([sample_id(target)])!=member["actual_target_group"] or c.digest([sid])!=member["leakage_group"]:raise ValueError("ENDPOINT_MARKET_GROUP_CHANGED")
    folds=[assemble(f,selected) for f in manifest["folds"]]
    return folds,{"status":"PASS","selected_rows":1440,"Train_rows_streamed":rows,"parsed_value_path":str(c.TRAIN),"source_Train_sha256":old.sha(c.TRAIN),
      "window_manifest_sha256":c.WINDOW_SHA,"selected_IDs_unchanged":True,"purge_embargo_endpoint":"PASS","same_session_endpoint_witnesses":1440,
      "class_policy":"direction_3class_exact_v1","feature_order":list(c.FEATURES),"horizon_ms":1000,"Test_values_parsed":False,"Holdout_opened":False}
