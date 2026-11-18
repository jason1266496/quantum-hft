"""Metadata-only deterministic sampling, with labels loaded after commitment."""
import csv,hashlib,json,time
from collections import Counter
import numpy as np
from data_pipeline.datasets.schema import sample_id
from experiments.phase4a1 import contracts as old
from experiments.phase4a1.preprocessing import transform,verify_profile
from . import contracts as c
META=("sample_id","source_id","session_id","record_index","event_time_ms")
def project_metadata(row,ordinal):
    return {"sample_id":row["sample_id"],"source_id":row["source_id"],"session_id":row["session_id"],
            "record_index":int(row["record_index"]),"event_time_ms":int(row["event_time_ms"]),"file_row_index":ordinal}
def key(row):return (int(row["event_time_ms"]),row["source_id"],row["session_id"],int(row["record_index"]),row["sample_id"])
def positions(n,k=96):
    if k<2 or n<k:raise ValueError("INSUFFICIENT_UNIVERSE_OR_INVALID_BUDGET")
    out=[i*(n-1)//(k-1) for i in range(k)]
    if len(set(out))!=k:raise ValueError("DUPLICATE_POSITIONS")
    return out
def select(metadata,k=96):
    if len({r["sample_id"] for r in metadata})!=len(metadata):raise ValueError("DUPLICATE_UNIVERSE_ID")
    ordered=sorted(metadata,key=key)
    return [ordered[i] for i in positions(len(ordered),k)],ordered
def class_counts(rows):
    return {n:sum(old.class_of(r["future_return_bps"])==i for r in rows) for i,n in enumerate(c.NAMES)}
def valid_selected(row):
    if row["feature_view"]!="aggregate_core_v1" or int(row["requested_horizon_ms"])!=1000 or row["valid_feature_row"]!="true" or row["valid_label"]!="true":raise ValueError("INVALID_SELECTED_ROW_NO_RESELECTION")
    if row["sample_id"]!=sample_id(row):raise ValueError("SELECTED_SAMPLE_ID_MISMATCH")
    if int(row["current_event_time_ms"])!=int(row["event_time_ms"]):raise ValueError("SELECTED_CURRENT_TIME_MISMATCH")
    if not np.isfinite([float(row[f]) for f in c.FEATURES]).all():raise ValueError("NONFINITE_SELECTED_FEATURES")
    old.class_of(row["future_return_bps"])
def build(run):
    expected=c.check_train_checksum();start=time.perf_counter();metadata=[]
    schema=old.read(c.DATASET/"dataset_schema.json")["field_order"]
    with c.TRAIN.open(newline="",encoding="utf-8") as f:
        if next(csv.reader(f))!=schema:raise ValueError("DATASET_SCHEMA_CHANGED")
    for i,row in c.read_rows(c.TRAIN,run):
        if row["feature_view"]!="aggregate_core_v1" or row["requested_horizon_ms"]!="1000":raise ValueError("WRONG_OFFICIAL_TRAIN_ROW")
        metadata.append(project_metadata(row,i))
        if (i+1)%25000==0 or i+1==expected["rows"]:
            elapsed=time.perf_counter()-start
            print(json.dumps({"stage":"TRAIN_METADATA_SCAN","processed":i+1,"total":expected["rows"],"percent":100*(i+1)/expected["rows"],"elapsed_seconds":elapsed,"eta_seconds":elapsed/(i+1)*(expected["rows"]-i-1)}),flush=True)
    if len(metadata)!=expected["rows"]:raise ValueError("TRAIN_COUNT_CHANGED")
    selected,ordered=select(metadata);digest=hashlib.sha256()
    for r in ordered:digest.update((json.dumps(r,sort_keys=True,separators=(",",":"))+"\n").encode())
    commitment={"status":"SELECTED_BEFORE_CLASS_COUNTS","rows":96,"universe_rows":len(ordered),"universe_train_sha256":expected["sha256"],
       "metadata_only_selection":True,"label_values_consulted_for_selection":False,"labels_distribution_computed":False,
       "rank_positions":positions(len(ordered)),"selected_metadata":selected,"ordered_metadata_sha256":digest.hexdigest(),
       "protocol_sha256":old.sha(run/"protocol.json"),"sampling_rule":c.protocol()["selection"]}
    c.write(run/"subset/selection_commitment.json",commitment)
    chosen={r["sample_id"]:r for r in selected};actual={}
    for i,row in c.read_rows(c.TRAIN,run):
        if row["sample_id"] in chosen:
            if project_metadata(row,i)!=chosen[row["sample_id"]]:raise ValueError("SECOND_SCAN_METADATA_CHANGED")
            valid_selected(row);actual[row["sample_id"]]=row
    if len(actual)!=96:raise ValueError("SELECTED_ROWS_MISSING")
    if c.check_train_checksum()!=expected:raise ValueError("DATASET_CHANGED_DURING_SCAN")
    rows=[actual[r["sample_id"]] for r in selected];counts=class_counts(rows)
    projected=[{f:(old.class_of(row["future_return_bps"]) if f=="class_label" else row[f]) for f in old.FIELDS} for row in rows]
    c.write_csv(run/"subset/natural_train.csv",old.FIELDS,projected)
    manifest=old.verify_budget();a=old.load_profile(old.BUDGET,"prototype",manifest)
    original_pre=verify_profile(a);params=a["params"]
    if set(chosen)&set(a["Validation"]["ids"]):raise ValueError("TRAIN_VALIDATION_OVERLAP")
    angles,clip=transform(projected,params,split="Train")
    c.write_csv(run/"subset/natural_train_angles.csv",("sample_id",*c.FEATURES),
       [{"sample_id":row["sample_id"],**{f:format(float(angles[i,j]),".17g") for j,f in enumerate(c.FEATURES)}} for i,row in enumerate(projected)])
    # Verify selected labels finish before the first shared Validation feature in the same source/session.
    vstart={}
    for row in a["Validation"]["raw"]:
        k=(row["source_id"],row["session_id"]);vstart[k]=min(vstart.get(k,10**30),int(row["event_time_ms"]))
    endpoints=[]
    for row in rows:
        k=(row["source_id"],row["session_id"]);end=int(row["event_time_ms"])+int(row["actual_horizon_ms"])
        if k in vstart and end>=vstart[k]:raise ValueError("LABEL_ENDPOINT_CROSSES_VALIDATION")
        endpoints.append({"sample_id":row["sample_id"],"actual_label_end_ms":end,"same_session_Validation_start_ms":vstart.get(k),"match_error_ms":int(row["match_error_ms"])})
    y=np.array([row["class_label"] for row in projected],dtype=np.int64)
    vi=c.input_identity(a["Validation"]["ids"],a["Validation"]["x"],a["Validation"]["y"])
    a_stage=old.read(c.P1/"prototype/first/stage_results.json")
    from experiments.phase4a2.analysis import verify_identity
    verify_identity(a_stage["input_identity"]["Validation"],{**vi,"file_sha256":a["Validation"]["file_sha256"]})
    fixed={"status":"PASS","interface_gap":False,"new_preprocessing_fits":0,"frozen_parameter_source":str(old.BUDGET/"prototype/input_preprocessing.json"),
       "frozen_parameter_sha256":old.sha(old.BUDGET/"prototype/input_preprocessing.json"),"parameters":params,
       "original_A_formula_validation":original_pre,"Natural_Train_clip":clip,"Validation_identity":vi,"shared_Validation_file_sha256":a["Validation"]["file_sha256"],
       "limitation":"Mapping remains learned from original balanced Train budget; Natural Train clipping/compression may differ. No new Train bounds fit."}
    c.write(run/"fixed_preprocessing_validation.json",fixed)
    integrity={"status":"PASS","unique_Train_ids":True,"all_selected_in_formal_Train":True,"Train_Validation_ID_overlap":0,"train_dataset_sha256":expected["sha256"],
       "Train_source_path":str(c.TRAIN),"universe_rows":len(ordered),"selected_rows":96,"label_count_after_commitment":True,
       "selected_source_counts":dict(Counter(row["source_id"] for row in projected)),"selected_label_endpoints":endpoints,
       "no_invalid_row_dropped":True,"no_label_eligibility_filter":True,"Test_parsed":False,"Holdout_content_opened":False}
    c.write(run/"subset_integrity.json",integrity)
    manifest={"status":"FROZEN","run_id":run.name,"Train_class_counts":counts,"training_applicable":all(counts.values()),
        "source_dataset_id":c.DATASET.name,"source_train_sha256":expected["sha256"],"feature_order":list(c.FEATURES),
        "classification_policy":"direction_3class_exact_v1","horizon_ms":1000,"rows":96,"selection_commitment_sha256":old.sha(run/"subset/selection_commitment.json"),
        "Train_identity":c.input_identity([r["sample_id"] for r in projected],angles,y),"Validation_identity":vi,
        "frozen_preprocessing_sha256":fixed["frozen_parameter_sha256"],
        "frozen_files":{n:old.fp(run/n) for n in ("subset/natural_train.csv","subset/natural_train_angles.csv","subset/selection_commitment.json","fixed_preprocessing_validation.json","subset_integrity.json")},
        "source_session_rule":"No label or feature is recomputed across sessions; existing formal Dataset rows retained."}
    c.write(run/"natural_train_subset_manifest.json",manifest)
    names=[*manifest["frozen_files"],"natural_train_subset_manifest.json"]
    c.write(run/"subset/FROZEN.sha256","\n".join(old.sha(run/n)+"  "+n for n in names)+"\n")
    c.verify_freeze(run)
    print(json.dumps({"stage":"NATURAL_BUDGET_FROZEN","class_counts":counts,"training_applicable":all(counts.values())}),flush=True)
    if not all(counts.values()):raise ValueError("NATURAL_TRAIN_MISSING_CLASS_STOP_NO_RESELECTION")
    return manifest

def load(run):
    c.verify_freeze(run);m=old.read(run/"natural_train_subset_manifest.json")
    if not m["training_applicable"]:raise ValueError("MISSING_CLASS")
    rr=[r for _,r in c.read_rows(run/"subset/natural_train.csv",run)]
    aa=[r for _,r in c.read_rows(run/"subset/natural_train_angles.csv",run)]
    ids=[r["sample_id"] for r in rr];x=np.array([[float(r[f]) for f in c.FEATURES] for r in aa]);y=np.array([int(r["class_label"]) for r in rr],dtype=np.int64)
    if len(ids)!=96 or ids!=[r["sample_id"] for r in aa] or c.input_identity(ids,x,y)!=m["Train_identity"]:raise ValueError("FROZEN_TRAIN_IDENTITY_CHANGED")
    a=old.load_profile(old.BUDGET,"prototype",old.verify_budget());verify_profile(a)
    vx=a["Validation"]["x"];vy=a["Validation"]["y"];vid=a["Validation"]["ids"]
    if c.input_identity(vid,vx,vy)!=m["Validation_identity"]:raise ValueError("VALIDATION_CHANGED")
    expected,clip=transform(rr,a["params"],split="Train")
    if not np.allclose(expected,x,atol=1e-12,rtol=1e-11):raise ValueError("INTERFACE_GAP_NATURAL_TRANSFORM")
    if any(old.class_of(r["future_return_bps"])!=int(r["class_label"]) for r in rr):raise ValueError("FROZEN_LABEL_CHANGED")
    return {"Train":{"x":x,"y":y,"ids":ids},"Validation":{"x":vx,"y":vy,"ids":vid},"clip":clip}
