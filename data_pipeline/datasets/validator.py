"""Validate frozen archives, exact source joins and horizon-specific Phase 2E membership."""
import bisect,csv,json,re,time
from itertools import zip_longest
from decimal import Decimal
from pathlib import Path
from .schema import HORIZONS,SPLITS,SLUG,FORBIDDEN_COLUMNS,columns,identity_bytes,sample_id,HOLDOUT_STATS_STATUS,decimal_text
from .checksums import fingerprint,verify_checksums
from .manifest import holdout_contract

ROOT_FILES={"feature_schema.json","label_schema.json","split_manifest.json","match_error_policy.json",
 "purge_report.json","scaler_policy.json","embargo_policy.json","walk_forward_windows.json",
 "frozen_split_policy.json","HFT_INPUT_DATA_CONTRACT.md","timestamp_policy.json","dataset_schema.json",
 "final_holdout_manifest.json","purge_policy.json","source_files.json","quality_report.json",
 "README.md","dataset_manifest.json","checksums.sha256"}
CREDENTIAL=re.compile(rb"""(?i)(?:api[_ -]?key|secret[_ -]?key)\s*[:=]\s*["']?[A-Za-z0-9_/-]{16,}""")

def read(path):return json.loads(Path(path).read_text())

def scan_files(root):
    allowed=set(ROOT_FILES)
    allowed.update(f"{h}ms/{SLUG[s]}.csv" for h in HORIZONS for s in SPLITS)
    allowed.update(SLUG[s]+"/manifest.json" for s in SPLITS)
    actual=set()
    for path in Path(root).rglob("*"):
        if path.is_symlink():raise ValueError("SYMLINK_IN_DATASET")
        if not path.is_file():continue
        name=path.relative_to(root).as_posix();actual.add(name)
        if name not in allowed:raise ValueError("UNAPPROVED_OR_RAW_FILE: "+name)
        with path.open("rb") as f:
            first=f.read(4)
            if first==b"\x7fELF":raise ValueError("ELF_PROHIBITED")
            carry=first
            for block in iter(lambda:f.read(1024*1024),b""):
                value=carry+block
                if CREDENTIAL.search(value):raise ValueError("CREDENTIAL_PATTERN_PROHIBITED: "+name)
                if name.endswith(".csv") and b"\r" in value:raise ValueError("CSV_MUST_USE_LF")
                carry=value[-1024:]
            if CREDENTIAL.search(carry):raise ValueError("CREDENTIAL_PATTERN_PROHIBITED: "+name)
        if path.suffix==".json":read(path)
    if actual!=allowed:raise ValueError("REQUIRED_DATASET_FILE_MISSING")
    return len(actual)

def source_pair(context,sid,view,h):
    feature=context["feature_root"]/"sources"/sid/(view+".csv")
    label=context["label_root"]/"sources"/sid/view/f"labels_{h}ms.csv"
    with feature.open(newline="",encoding="utf-8") as f:features={int(x["record_index"]):x for x in csv.DictReader(f)}
    with label.open(newline="",encoding="utf-8") as f:labels={int(x["record_index"]):x for x in csv.DictReader(f)}
    ordered=list(features.values())
    times=[int(x["event_time_ms"]) for x in ordered]
    return features,labels,times,ordered

def _validate(root,context,line):
    root=Path(root);file_count=scan_files(root);checksum=verify_checksums(root)
    view="aggregate_core_v1" if line=="aggregate" else "depth_top5_v1"
    e=context["split_root"]
    for original,name in ((context["feature_root"]/"schemas"/(view+".schema.json"),"feature_schema.json"),
                          (context["label_root"]/"schemas/label.schema.json","label_schema.json"),
                          (e/line/"split_manifest.json","split_manifest.json"),
                          (e/"match_error/match_error_policy.json","match_error_policy.json"),
                          (e/line/"purge_report.json","purge_report.json"),
                          (e/"policies/scaler_policy.json","scaler_policy.json"),
                          (e/"policies/embargo_policy.json","embargo_policy.json"),
                          (e/line/"walk_forward_windows.json","walk_forward_windows.json"),
                          (context["contract"],"HFT_INPUT_DATA_CONTRACT.md"),
                          (context["timestamp_policy"],"timestamp_policy.json"),
                          (e/line/("aggregate_split_policy.json" if line=="aggregate" else "depth_split_policy.json"),"frozen_split_policy.json")):
        if fingerprint(original)!=fingerprint(root/name):raise ValueError("FROZEN_SOURCE_CHANGED: "+name)
    provenance=read(root/"source_files.json")
    if len(provenance["hft_sources"])!=9 or provenance["raw_market_data_copied"]:
        raise ValueError("RAW_SOURCE_PROVENANCE_INVALID")
    config=read(context["source_config"])
    expected={Path(x["absolute_path"]).stem:x for x in config["sources"]}
    for item in provenance["hft_sources"]:
        original=expected[item["source_id"]]
        for key,source_key in (("original_path","absolute_path"),("sha256","sha256"),("size_bytes","size_bytes"),
                               ("session_id","session_id"),("event_time_start","event_time_start"),
                               ("event_time_end","event_time_end"),("audit_status","audit_status")):
            if item[key]!=original[source_key]:raise ValueError("HFT_PROVENANCE_CHANGED")
        if fingerprint(item["original_path"])!={k:item[k] for k in ("sha256","size_bytes")}:
            raise ValueError("HFT_SOURCE_HASH_MISMATCH")
    for item in provenance["derived_inputs"]:
        if fingerprint(item["path"])!={k:item[k] for k in ("sha256","size_bytes")}:
            raise ValueError("DERIVED_SOURCE_HASH_MISMATCH")
    manifest=read(root/"dataset_manifest.json")
    if manifest["feature_view"]!=view or manifest["horizons_ms"]!=list(HORIZONS):raise ValueError("DATASET_MANIFEST_MISMATCH")
    for key in ("local_timestamp_used","cross_session_labels","shuffled","scaler_fitted",
                "class_labels_present","model_training_performed"):
        if manifest[key] is not False:raise ValueError("FORBIDDEN_DATASET_MANIFEST_FLAG")
    if not manifest["final_holdout_locked"] or not manifest["purge_enabled"]:
        raise ValueError("HOLDOUT_OR_PURGE_DISABLED")
    fs,ls=read(root/"feature_schema.json"),read(root/"label_schema.json")
    order,mapping=columns(fs,ls)
    if read(root/"dataset_schema.json")["field_order"]!=order or set(order)&FORBIDDEN_COLUMNS:
        raise ValueError("FORBIDDEN_OR_CHANGED_DATASET_SCHEMA")
    if read(root/"final_holdout_manifest.json")!=holdout_contract(read(e/"policies/final_holdout_manifest.json")[line]):
        raise ValueError("HOLDOUT_CONTRACT_CHANGED")
    if read(root/"scaler_policy.json")["fit_executed"]:raise ValueError("SCALER_FIT_PROHIBITED")
    policy=read(root/"match_error_policy.json")[line]
    if manifest["match_error_policy"]!=policy:raise ValueError("MATCH_POLICY_CHANGED")
    frozen=read(root/"split_manifest.json");plan=read(root/"frozen_split_policy.json")
    quality=read(root/"quality_report.json")
    identities={};roles={};event_roles={}
    counts={str(h):{} for h in HORIZONS};checked=0
    total=sum(x["per_horizon"][str(h)]["final_rows"] for x in frozen["splits"].values() for h in HORIZONS)
    start=time.monotonic()
    for h in HORIZONS:
        horizon_ids=set()
        for split in SPLITS:
            path=root/f"{h}ms"/(SLUG[split]+".csv")
            next_role={"Train":"Validation","Validation":"Test","Test":"Final Holdout"}.get(split)
            boundary=min((x["start"] for x in plan["assignments"].get(next_role,[])),default=None)
            active_source=None;last_time=-1;count=0
            with path.open(newline="",encoding="utf-8") as output, \
                 (e/line/(SLUG[split]+"_indices.csv")).open(newline="",encoding="utf-8") as source:
                reader=csv.DictReader(output)
                if reader.fieldnames!=order:raise ValueError("DATASET_COLUMN_ORDER_MISMATCH")
                membership=(x for x in csv.DictReader(source) if int(x["requested_horizon_ms"])==h)
                for row,index in zip_longest(reader,membership):
                    if row is None or index is None:raise ValueError("PHASE2E_MEMBERSHIP_COUNT_MISMATCH")
                    if row["source_id"]=="replay_events_1000":raise ValueError("SMOKE_SOURCE_IN_FORMAL_DATASET")
                    if (row["feature_view"],row["source_id"],row["session_id"],row["record_index"],row["event_time_ms"])!=(
                        view,index["source_id"],index["session_id"],index["record_index"],index["event_time_ms"]):
                        raise ValueError("PHASE2E_MEMBERSHIP_CHANGED")
                    sid=row["source_id"];record=int(row["record_index"]);t=int(row["event_time_ms"])
                    if sid!=active_source:
                        features,labels,times,ordered=source_pair(context,sid,view,h);active_source=sid
                    feature,label=features[record],labels[record]
                    for column in fs["field_order"]:
                        if row[column]!=feature[column]:raise ValueError("FEATURE_VALUE_CHANGED")
                    for original,column in mapping.items():
                        if row[column]!=label[original]:raise ValueError("LABEL_VALUE_CHANGED")
                    for identity in ("source_id","session_id","record_index","feature_view"):
                        if feature[identity]!=label[identity]:raise ValueError("CROSS_SESSION_LABEL")
                    if row["valid_feature_row"]!="true" or row["valid_label"]!="true":
                        raise ValueError("INVALID_ROW_IN_DATASET")
                    if int(row["requested_horizon_ms"])!=h:raise ValueError("HORIZON_MIXED")
                    target=int(row["target_event_time_ms"]);actual=int(row["actual_horizon_ms"]);error=int(row["match_error_ms"])
                    j=bisect.bisect_left(times,t+h)
                    if j>=len(times) or target!=times[j] or row["future_mid_price"]!=ordered[j]["mid_price"]:
                        raise ValueError("CROSS_SOURCE_OR_CHANGED_FUTURE_TARGET")
                    if actual!=target-t or error!=actual-h or error<0:
                        raise ValueError("LABEL_TIMING_CHANGED")
                    if Decimal(error)>Decimal(policy["chosen_threshold_by_horizon"][str(h)]):
                        raise ValueError("MATCH_ERROR_REJECTED_IN_DATASET")
                    if boundary is not None and target>=boundary:raise ValueError("PURGED_ROW_IN_DATASET")
                    for name in ("current_mid_price","future_mid_price","future_return_bps"):
                        value=Decimal(row[name])
                        if not value.is_finite() or decimal_text(value)!=row[name]:raise ValueError("NONCANONICAL_LABEL_DECIMAL")
                    value=row["sample_id"];identity=identity_bytes(row)
                    if value!=sample_id(row):raise ValueError("SAMPLE_ID_MISMATCH")
                    if value in identities and identities[value]!=identity:raise ValueError("SAMPLE_ID_COLLISION")
                    identities[value]=identity
                    if value in horizon_ids:raise ValueError("DUPLICATE_SAMPLE_ID")
                    horizon_ids.add(value)
                    if value in roles and roles[value]!=split:raise ValueError("SPLIT_SAMPLE_OVERLAP")
                    roles[value]=split
                    event=(sid,row["session_id"],row["event_time_ms"],row["local_update_id"])
                    if event in event_roles and event_roles[event]!=split:raise ValueError("SPLIT_EVENT_OVERLAP")
                    event_roles[event]=split
                    if t<last_time:raise ValueError("SHUFFLED_DATASET")
                    last_time=t;count+=1;checked+=1
                    if checked%50000==0:
                        elapsed=time.monotonic()-start
                        print(json.dumps({"stage":"VALIDATE_DATASET","family":line,"checked":checked,"total":total,
                           "percent":round(checked*100/total,2),"elapsed_seconds":round(elapsed,3),
                           "eta_seconds":round((total-checked)*elapsed/checked,3)}),flush=True)
            expected_count=frozen["splits"][split]["per_horizon"][str(h)]["final_rows"]
            q=quality["per_horizon"][str(h)][split]
            if count!=expected_count or q["packaged_rows"]!=count:raise ValueError("ROW_COUNT_MISMATCH")
            if split=="Final Holdout" and q["continuous_return_bps"]!={"status":HOLDOUT_STATS_STATUS,"count":count}:
                raise ValueError("HOLDOUT_RETURN_STATISTICS_PROHIBITED")
            for key in ("duplicate_sample_ids","sample_id_collision_count","invalid_feature_rows"):
                if q[key]!=0:raise ValueError("QUALITY_FAILURE")
            counts[str(h)][SLUG[split]]=count
    if quality["unique_event_sample_ids"]!=len(identities):raise ValueError("UNIQUE_SAMPLE_COUNT_MISMATCH")
    return {"status":"PASS","feature_view":view,"dataset_id":manifest["dataset_id"],
            "checked_rows":checked,"unique_event_sample_ids":len(identities),"row_counts":counts,
            "duplicate_sample_ids":0,"sample_id_collision_count":0,"split_overlap":0,
            "holdout_status":"LOCKED","holdout_return_statistics":HOLDOUT_STATS_STATUS,
            "source_values_exact":True,"checksums":checksum,"formal_file_count":file_count}

def validate_dataset(root,context,line):
    try:return _validate(root,context,line)
    except Exception as exc:
        return {"status":"DATASET_VALIDATION_FAIL","failure":str(exc),"error_type":type(exc).__name__}
