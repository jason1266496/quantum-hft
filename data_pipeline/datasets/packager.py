"""Join approved feature/label strings using frozen Phase 2E membership only."""
import csv,json,time
from collections import defaultdict
from contextlib import ExitStack
from decimal import Decimal,localcontext
from pathlib import Path
from .schema import (HORIZONS,SPLITS,SLUG,CONTEXT,HOLDOUT_STATS_STATUS,columns,dataset_schema,
                     identity_bytes,sample_id,decimal_text,dataset_id)
from .checksums import archive,fingerprint,write_json,safe_output,seal_dataset
from .manifest import make_manifest,holdout_contract

class SampleRegistry:
    def __init__(self):
        self.identities={};self.horizons={h:set() for h in HORIZONS}
    def observe(self,value,identity,split,horizon):
        old=self.identities.get(value)
        if old is not None:
            if old[0]!=identity:raise ValueError("SAMPLE_ID_COLLISION")
            if old[1]!=split:raise ValueError("SPLIT_SAMPLE_OVERLAP")
        if value in self.horizons[horizon]:raise ValueError("DUPLICATE_SAMPLE_ID")
        self.identities[value]=(identity,split);self.horizons[horizon].add(value)

def read_json(path):return json.loads(Path(path).read_text())

def return_statistics(values):
    if not values:
        return {"count":0,**{k:None for k in ("min","max","mean","median","p1","p5","p25","p50","p75","p95","p99")}}
    values=sorted(values)
    with localcontext(CONTEXT):
        def percentile(p):
            position=Decimal(len(values)-1)*Decimal(p)/100
            i=int(position);j=min(i+1,len(values)-1);fraction=position-i
            return values[i]*(1-fraction)+values[j]*fraction
        return {"count":len(values),"min":decimal_text(values[0]),"max":decimal_text(values[-1]),
                "mean":decimal_text(sum(values,Decimal(0))/Decimal(len(values))),
                "median":decimal_text(percentile(50)),
                **{f"p{p}":decimal_text(percentile(p)) for p in (1,5,25,50,75,95,99)}}

def joined_row(feature,label,feature_schema,label_schema):
    order,mapping=columns(feature_schema,label_schema)
    if feature["valid_feature_row"]!="true" or label["valid_label"]!="true":
        raise ValueError("INVALID_ROW_IN_FORMAL_MEMBERSHIP")
    for name in ("feature_view","source_id","session_id","record_index"):
        if feature[name]!=label[name]:raise ValueError("FEATURE_LABEL_IDENTITY_MISMATCH")
    if feature["event_time_ms"]!=label["current_event_time_ms"]:raise ValueError("EVENT_TIME_JOIN_MISMATCH")
    if feature["mid_price"]!=label["current_mid_price"]:raise ValueError("CURRENT_MID_JOIN_MISMATCH")
    if set(feature)!=set(feature_schema["field_order"]) or set(label)!=set(label_schema["field_order"]):
        raise ValueError("SOURCE_SCHEMA_MISMATCH")
    value={"sample_id":sample_id(feature),**feature}
    for source,output in mapping.items():value[output]=label[source]
    if list(value)!=order:raise ValueError("DATASET_COLUMN_ORDER_MISMATCH")
    return value

def load_memberships(e_root,line,view):
    memberships=defaultdict(lambda:{h:{} for h in HORIZONS})
    for split in SPLITS:
        with (e_root/line/(SLUG[split]+"_indices.csv")).open(newline="",encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["feature_view"]!=view or row["split"]!=split or row["source_id"]=="replay_events_1000":
                    raise ValueError("WRONG_VIEW_SPLIT_OR_SMOKE_MEMBERSHIP")
                h=int(row["requested_horizon_ms"]);index=int(row["record_index"])
                if h not in HORIZONS:raise ValueError("UNAPPROVED_HORIZON")
                bucket=memberships[row["source_id"]][h]
                if index in bucket:raise ValueError("DUPLICATE_PHASE2E_MEMBERSHIP")
                bucket[index]=(split,int(row["event_time_ms"]),int(row["target_event_time_ms"]),
                               row["session_id"],row["event_identity"])
    return memberships

def source_manifest(context,line,sources):
    config=read_json(context["source_config"])
    hft=[]
    for x in config["sources"]:
        path=Path(x["absolute_path"])
        hft.append({"source_id":path.stem,"original_path":str(path),"sha256":x["sha256"],
                    "size_bytes":x["size_bytes"],"session_id":x["session_id"],
                    "event_time_start":x["event_time_start"],"event_time_end":x["event_time_end"],
                    "audit_status":x["audit_status"],"role":"READ_ONLY_PROVENANCE_NOT_COPIED"})
    inputs=[]
    for sid in sources:
        feature=context["feature_root"]/"sources"/sid/(context["view"]+".csv")
        inputs.append({"path":str(feature),**fingerprint(feature),"role":"PHASE2C_FEATURE_INPUT"})
        for h in HORIZONS:
            label=context["label_root"]/"sources"/sid/context["view"]/f"labels_{h}ms.csv"
            inputs.append({"path":str(label),**fingerprint(label),"role":"PHASE2D_LABEL_INPUT"})
    for p in sorted((context["split_root"]/line).iterdir()):
        if p.is_file():inputs.append({"path":str(p),**fingerprint(p),"role":"PHASE2E_SPLIT_INPUT"})
    for p in sorted((context["split_root"]/"policies").iterdir()):
        if p.is_file():inputs.append({"path":str(p),**fingerprint(p),"role":"PHASE2E_FROZEN_POLICY"})
    p=context["split_root"]/"match_error/match_error_policy.json"
    inputs.append({"path":str(p),**fingerprint(p),"role":"PHASE2E_MATCH_ERROR_POLICY"})
    return {"hft_sources":hft,"derived_inputs":inputs,"raw_market_data_copied":False,
            "replay1000_role":"SMOKE_REFERENCE_ONLY_NOT_PACKAGED"}

def package_family(context,line,run_id,output,generator_version):
    view="aggregate_core_v1" if line=="aggregate" else "depth_top5_v1"
    context={**context,"view":view}
    output=safe_output(output)
    if output.exists():raise FileExistsError("DATASET_OUTPUT_EXISTS")
    feature_schema_path=context["feature_root"]/"schemas"/(view+".schema.json")
    label_schema_path=context["label_root"]/"schemas/label.schema.json"
    fs,ls=read_json(feature_schema_path),read_json(label_schema_path)
    order,_=columns(fs,ls)
    e=context["split_root"]
    frozen=read_json(e/line/"split_manifest.json")
    split_plan=read_json(e/line/("aggregate_split_policy.json" if line=="aggregate" else "depth_split_policy.json"))
    next_role={"Train":"Validation","Validation":"Test","Test":"Final Holdout"}
    next_boundaries={split:min((r["start"] for r in split_plan["assignments"].get(next_role.get(split,""),[])),default=None)
                     for split in SPLITS}
    policy=read_json(e/"match_error/match_error_policy.json")[line]
    embargo=read_json(e/"policies/embargo_policy.json")
    if any(policy["chosen_threshold_by_horizon"][str(h)]!=("1" if line=="aggregate" else "0") for h in HORIZONS):
        raise ValueError("APPROVED_MATCH_POLICY_CHANGED")
    memberships=load_memberships(e,line,view)
    source_order=sorted(memberships,key=lambda sid:min(entry["event_time_start"]
                   for s in frozen["splits"].values() for entry in s["source_entries"] if entry["source_id"]==sid))
    output.mkdir(exist_ok=False)
    for h in HORIZONS:(output/f"{h}ms").mkdir(exist_ok=False)
    for split in SPLITS:(output/SLUG[split]).mkdir(exist_ok=False)
    archive(feature_schema_path,output/"feature_schema.json")
    archive(label_schema_path,output/"label_schema.json")
    archive(e/line/"split_manifest.json",output/"split_manifest.json")
    archive(e/"match_error/match_error_policy.json",output/"match_error_policy.json")
    archive(e/line/"purge_report.json",output/"purge_report.json")
    archive(e/"policies/scaler_policy.json",output/"scaler_policy.json")
    archive(e/"policies/embargo_policy.json",output/"embargo_policy.json")
    archive(e/line/"walk_forward_windows.json",output/"walk_forward_windows.json")
    archive(e/line/("aggregate_split_policy.json" if line=="aggregate" else "depth_split_policy.json"),output/"frozen_split_policy.json")
    archive(context["contract"],output/"HFT_INPUT_DATA_CONTRACT.md")
    archive(context["timestamp_policy"],output/"timestamp_policy.json")
    write_json(output/"dataset_schema.json",dataset_schema(fs,ls))
    upstream_holdout=read_json(e/"policies/final_holdout_manifest.json")[line]
    write_json(output/"final_holdout_manifest.json",holdout_contract(upstream_holdout))
    write_json(output/"purge_policy.json",{
        "enabled":True,"rule":"current_event_time_ms < next_split_boundary <= actual target_event_time_ms",
        "thresholds_reselected":False,"actual_label_endpoint_required":True,
        "source_phase2e_run_id":"20261026T195329Z","report":read_json(e/line/"purge_report.json"),
        "embargo_ms":embargo["embargo_ms"]})
    write_json(output/"source_files.json",source_manifest(context,line,source_order))
    registry=SampleRegistry()
    stats={h:{s:{"packaged_rows":0,"missing_feature_values":0,"missing_by_feature":{},
                "invalid_feature_rows":0,"duplicate_event_time_count":0,"returns":[] if s!="Final Holdout" else None,
                "last_event":None} for s in SPLITS} for h in HORIZONS}
    expected_total=sum(len(records) for source in memberships.values() for records in source.values())
    processed=0;start=time.monotonic()
    with ExitStack() as stack:
        writers={}
        for h in HORIZONS:
            for split in SPLITS:
                f=stack.enter_context((output/f"{h}ms"/(SLUG[split]+".csv")).open("x",encoding="utf-8",newline=""))
                writer=csv.writer(f,lineterminator="\n");writer.writerow(order);writers[h,split]=writer
        for sid in source_order:
            feature_path=context["feature_root"]/"sources"/sid/(view+".csv")
            with feature_path.open(newline="",encoding="utf-8") as f:
                reader=csv.DictReader(f)
                if reader.fieldnames!=fs["field_order"]:raise ValueError("FEATURE_SCHEMA_CHANGED")
                features={int(x["record_index"]):x for x in reader}
            for h in HORIZONS:
                label_path=context["label_root"]/"sources"/sid/view/f"labels_{h}ms.csv"
                matched=set()
                with label_path.open(newline="",encoding="utf-8") as f:
                    reader=csv.DictReader(f)
                    if reader.fieldnames!=ls["field_order"]:raise ValueError("LABEL_SCHEMA_CHANGED")
                    for label in reader:
                        index=int(label["record_index"])
                        if index not in memberships[sid][h]:continue
                        split,current,target,session,event=memberships[sid][h][index]
                        if (int(label["current_event_time_ms"])!=current or int(label["target_event_time_ms"])!=target
                                or label["session_id"]!=session or label["valid_label"]!="true"):
                            raise ValueError("PHASE2E_LABEL_MEMBERSHIP_MISMATCH")
                        if Decimal(label["match_error_ms"])>Decimal(policy["chosen_threshold_by_horizon"][str(h)]):
                            raise ValueError("MATCH_ERROR_REJECTED_IN_MEMBERSHIP")
                        boundary=next_boundaries[split]
                        if boundary is not None and target>=boundary:raise ValueError("PURGED_ROW_IN_MEMBERSHIP")
                        row=joined_row(features[index],label,fs,ls)
                        identity=identity_bytes(row)
                        registry.observe(row["sample_id"],identity,split,h)
                        writers[h,split].writerow([row[name] for name in order])
                        q=stats[h][split];q["packaged_rows"]+=1
                        for field in fs["field_order"]:
                            if row[field]=="" and field!="invalid_reason":
                                q["missing_feature_values"]+=1
                                q["missing_by_feature"][field]=q["missing_by_feature"].get(field,0)+1
                        event_key=(sid,session,current)
                        if q["last_event"]==event_key:q["duplicate_event_time_count"]+=1
                        q["last_event"]=event_key
                        if split!="Final Holdout":q["returns"].append(Decimal(row["future_return_bps"]))
                        matched.add(index);processed+=1
                        if processed%25000==0:
                            elapsed=time.monotonic()-start
                            print(json.dumps({"family":line,"processed":processed,"total":expected_total,
                                "percent":round(processed*100/expected_total,2),"elapsed_seconds":round(elapsed,3),
                                "eta_seconds":round((expected_total-processed)*elapsed/processed,3)}),flush=True)
                if matched!=set(memberships[sid][h]):raise ValueError("MISSING_LABEL_JOIN")
    quality={"feature_view":view,"status":"PACKAGING_QUALITY_PASS","per_horizon":{},
             "sample_id_uniqueness_scope":"one horizon across all splits; reused IDs across horizons represent the same event",
             "sample_id_collision_count":0,"unique_event_sample_ids":len(registry.identities),
             "holdout_return_statistics":HOLDOUT_STATS_STATUS,
             "return_statistics_used_to_change_policy":False}
    for h in HORIZONS:
        quality["per_horizon"][str(h)]={}
        for split in SPLITS:
            q=stats[h][split];upstream=frozen["splits"][split]
            source=upstream["per_horizon"][str(h)]
            if q["packaged_rows"]!=source["final_rows"]:raise ValueError("ROW_COUNT_DOES_NOT_MATCH_PHASE2E")
            quality["per_horizon"][str(h)][split]={
                "raw_candidate_rows":upstream["raw_rows"],"valid_label_rows":source["valid_label_rows"],
                "match_error_rejected":source["match_error_filtered_rows"],"purged_rows":source["purged_rows"],
                "packaged_rows":q["packaged_rows"],"duplicate_sample_ids":0,"sample_id_collision_count":0,
                "missing_feature_values":q["missing_feature_values"],"missing_by_feature":q["missing_by_feature"],
                "missing_value_semantics":"empty invalid_reason excluded; documented unavailable nullable source fields counted",
                "invalid_feature_rows":q["invalid_feature_rows"],"duplicate_event_time_count":q["duplicate_event_time_count"],
                "continuous_return_bps":({"status":HOLDOUT_STATS_STATUS,"count":q["packaged_rows"]} if split=="Final Holdout"
                                           else {"status":"DESCRIPTIVE_ONLY_NO_POLICY_SELECTION",**return_statistics(q["returns"])})}
    write_json(output/"quality_report.json",quality)
    for split in SPLITS:
        write_json(output/SLUG[split]/"manifest.json",{
            "split":split,"holdout_status":"LOCKED" if split=="Final Holdout" else "NOT_APPLICABLE",
            "horizons":{str(h):{"path":f"{h}ms/{SLUG[split]}.csv","rows":stats[h][split]["packaged_rows"],
                                **fingerprint(output/f"{h}ms"/(SLUG[split]+".csv"))} for h in HORIZONS}})
    text=(
        "# "+dataset_id(view,run_id)+"\n\n"
        "BTCUSDT 連續 future-return 研究資料集；feature_view="+view+"。Horizon 為100/200/500/1000ms，各自保留 Phase2E membership。\n\n"
        "來源：Phase2C 20261019T001249Z Features、Phase2D 20261026T193335Z Labels、Phase2E 20261026T195329Z Split。"
        "Feature/Label schema 與原始字串值照存；label invalid_reason 在 joined row 別名為 label_invalid_reason，來源 schema 不變。\n\n"
        "match error 門檻："+("Aggregate 1ms" if line=="aggregate" else "Depth 0ms")+"；purge 使用實際 target endpoint；embargo=0。"
        "Replay1000 僅為 SMOKE/REFERENCE，未入正式資料。\n\n"
        "sample_id=SHA256(canonical metadata JSON)，只含 feature_view/source_id/session_id/record_index/event_time_ms。"
        "同事件跨 horizon 共用 sample_id；每個 horizon 內唯一，跨 split 不重疊。不同 View 的 ID 不同。\n\n"
        "Final Holdout 維持 LOCKED，model_access_policy=PROHIBITED_UNTIL_FINAL_EVALUATION。"
        "禁止利用 Holdout 作 feature/threshold/label threshold/scaler/hyperparameter/quantum map/QAOA/model selection。"
        "本階段僅封存 Holdout 原值與筆數，return 分布為 NOT_COMPUTED_HOLDOUT_LOCKED。\n\n"
        "local_timestamp_us 未使用；尚無 class label、scaler 或模型。Phase3 必須另獲批准：scaler.fit(Train)，"
        "Validation/Test/Final Holdout transform only；不同 View 使用不同 scaler。"
        "不同 horizon 只有在明確規範 Train Feature scaler fit universe 後才可共用；禁止用 Holdout 計算任何統計參數。\n\n"
        "train/validation/test/final_holdout 目錄僅保存指向 horizon CSV 的 manifest；正式 CSV 位於100ms/200ms/500ms/1000ms。"
        "checksums.sha256 覆蓋全部正式檔案且排除自身；dataset_tree_hash 的 normalized-manifest 自參照規則見 dataset_manifest.json。\n\n"
        "HFT_INPUT_DATA_CONTRACT.md 與 timestamp_policy.json 為原始契約證據逐位元封存，"
        "其中早期 SPECIFICATION_ONLY/null 描述保留歷史原樣；本 Dataset 以封存的已批准 Phase2E policy 決定 membership，不修改舊契約。\n"
    )
    with safe_output(output/"README.md").open("x",encoding="utf-8",newline="") as f:f.write(text)
    manifest=make_manifest(view,run_id,policy,embargo,generator_version)
    digest=seal_dataset(output,manifest)
    print(json.dumps({"family":line,"processed":processed,"total":expected_total,"percent":100,
                     "elapsed_seconds":round(time.monotonic()-start,3),"eta_seconds":0,
                     "dataset_tree_hash":digest}),flush=True)
    return {"dataset_id":dataset_id(view,run_id),"feature_view":view,"dataset_tree_hash":digest,
            "row_counts":{str(h):{SLUG[s]:stats[h][s]["packaged_rows"] for s in SPLITS} for h in HORIZONS},
            "quality_report":quality}
