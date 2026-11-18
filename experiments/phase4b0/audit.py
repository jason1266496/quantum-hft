"""Train-only metadata, current-state formulas and actual endpoint witnesses."""
import csv,time,bisect,json
from collections import defaultdict,Counter
from decimal import Decimal
from data_pipeline.features.formulas import aggregate
from data_pipeline.datasets.schema import sample_id,decimal_text
from . import contracts as c,temporal as t
from experiments.phase4a1 import contracts as old
CURRENT=("best_bid","best_ask","bid_volume_5","ask_volume_5")
REQUIRED=("sample_id","feature_view","source_id","session_id","record_index","event_time_ms","local_update_id","target_event_time_ms","actual_horizon_ms","requested_horizon_ms","match_error_ms","current_event_time_ms","mid_price","current_mid_price","future_mid_price","spread","spread_bps","obi_5","bid_volume_5","ask_volume_5","best_bid","best_ask","valid_feature_row","valid_label","first_update_id","final_update_id")
def require(row,k,empty=False):
    if k not in row or row[k] is None or (not empty and row[k]==""):raise ValueError("MISSING_"+k.upper())
    return row[k]
def current_formula_errors(row):
    values=aggregate(*(Decimal(require(row,k)) for k in CURRENT))
    return [k for k in (*c.FEATURES,"mid_price","spread") if values[k] is None or values[k]!=Decimal(require(row,k))]
def project(row,index):
    for k in REQUIRED:require(row,k,empty=k in ("first_update_id","final_update_id"))
    if row["feature_view"]!="aggregate_core_v1" or int(row["requested_horizon_ms"])!=1000:raise ValueError("WRONG_VIEW_HORIZON")
    if sample_id(row)!=row["sample_id"]:raise ValueError("CANONICAL_SAMPLE_ID_MISMATCH")
    end=t.actual_endpoint(row);now=int(row["event_time_ms"]);record=int(row["record_index"]);update=int(row["local_update_id"])
    if record<1 or update<0 or int(row["current_event_time_ms"])!=now:raise ValueError("INVALID_EVENT_METADATA")
    return {"id":row["sample_id"],"source":row["source_id"],"session":row["session_id"],"record":record,"t":now,"end":end,"update":update,
      "state":c.canonical_sha({k:decimal_text(Decimal(row[k])) for k in CURRENT}),
      "actual_horizon":int(row["actual_horizon_ms"]),"match_error":int(row["match_error_ms"]),"row_index":index,
      "_mid":decimal_text(Decimal(row["mid_price"])),"_future_mid":decimal_text(Decimal(row["future_mid_price"])),
      "legacy_eligible":row["valid_feature_row"]=="true" and row["valid_label"]=="true" and 0<=int(row["match_error_ms"])<=1 and Decimal(row["current_mid_price"])==Decimal(row["mid_price"]),
      "eligible":False,"target_group":None}
def witnesses(rows,mapping):
    by=defaultdict(list)
    for r in rows:by[(r["source"],r["session"],r["t"])].append(r)
    counts=Counter();bad=[]
    for r in rows:
        target=by.get((r["source"],r["session"],r["end"]),[])
        if not r["legacy_eligible"]:counts["legacy_quality_ineligible"]+=1;continue
        if not target:counts["endpoint_not_observable_in_filtered_Train"]+=1;continue
        matches=[a for a in target if a["_mid"]==r["_future_mid"]]
        if not matches:bad.append(r["id"]);counts["endpoint_price_mismatch"]+=1;continue
        groups={mapping[a["id"]] for a in matches}
        if len(groups)!=1:counts["ambiguous_endpoint_identity"]+=1;continue
        r["eligible"]=True;r["target_group"]=next(iter(groups));counts["witness_verified"]+=1
    return dict(counts),bad
def catalogue():
    plan=old.read(c.DATA/"frozen_split_policy.json")["assignments"]["Train"]
    registry={s["source_id"]:s for s in old.read(c.REGISTRY)["sources"]}
    out=[]
    for p in plan:
        s=registry[p["source_id"]]
        if s["session_id"]!=p["session_id"] or s["event_time_start"]!=p["start"] or s["event_time_end"]+1!=p["end_exclusive"]:raise ValueError("SOURCE_PROVENANCE_RANGE_MISMATCH")
        out.append({**p,"registry":s})
    return sorted(out,key=lambda r:(r["start"],r["end_exclusive"],r["source_id"],r["session_id"]))
def scan():
    expected=old.read(c.DATA/"train/manifest.json")["horizons"]["1000"]
    if expected["rows"]!=150912 or old.sha(c.TRAIN)!=c.split_protocol()["Dataset_Train_sha256"]:raise ValueError("TRAIN_CHECKSUM_COUNT_CHANGED")
    catalog=catalogue();regions={(r["source_id"],r["session_id"]):r for r in catalog}
    schema=old.read(c.DATA/"dataset_schema.json")["field_order"]
    rows=[];stats={};fatal=[];formbad=Counter();start=time.perf_counter()
    with c.TRAIN.open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=schema:raise ValueError("DATASET_HEADER_CHANGED")
        for i,row in enumerate(reader):
            r=project(row,i);k=(r["source"],r["session"])
            if k not in regions:raise ValueError("UNREGISTERED_TRAIN_SESSION")
            region=regions[k]
            if not region["start"]<=r["t"]<r["end"]<region["end_exclusive"]:fatal.append("EVENT_OR_LABEL_OUTSIDE_REGISTERED_SESSION")
            formbad.update(current_formula_errors(row))
            v=stats.setdefault(k,{"rows":0,"min_time":r["t"],"max_time":r["t"],"min_update":r["update"],"max_update":r["update"],
                "backwards":0,"same_time":0,"update_backwards":0,"update_repeated":0,"record_nonincrease":0,"max_observed_gap_ms":0,
                "max_actual_horizon_ms":0,"match_error_counts":Counter(),"first_update_present":0,"final_update_present":0,"last":None})
            v["rows"]+=1;v["min_time"]=min(v["min_time"],r["t"]);v["max_time"]=max(v["max_time"],r["t"])
            v["min_update"]=min(v["min_update"],r["update"]);v["max_update"]=max(v["max_update"],r["update"])
            if v["last"] is not None:
                prev=v["last"];delta=r["t"]-prev["t"];v["backwards"]+=int(delta<0);v["same_time"]+=int(delta==0)
                v["update_backwards"]+=int(r["update"]<prev["update"]);v["update_repeated"]+=int(r["update"]==prev["update"])
                v["record_nonincrease"]+=int(r["record"]<=prev["record"]);v["max_observed_gap_ms"]=max(v["max_observed_gap_ms"],delta)
            v["last"]=r;v["max_actual_horizon_ms"]=max(v["max_actual_horizon_ms"],r["actual_horizon"]);v["match_error_counts"][str(r["match_error"])]+=1
            v["first_update_present"]+=int(bool(row["first_update_id"]));v["final_update_present"]+=int(bool(row["final_update_id"]))
            rows.append(r)
            if (i+1)%25000==0 or i+1==150912:
                elapsed=time.perf_counter()-start;print(json.dumps({"stage":"TRAIN_SOURCE_TIME_AUDIT","processed":i+1,"total":150912,"percent":100*(i+1)/150912,"elapsed_seconds":elapsed,"eta_seconds":elapsed/(i+1)*(150912-i-1)}),flush=True)
    if len(rows)!=150912:raise ValueError("TRAIN_ROW_COUNT_CHANGED")
    mapping,bounds,duplicates=t.leakage_groups(rows);witness,pricebad=witnesses(rows,mapping)
    if pricebad:fatal.append("OBSERVED_ENDPOINT_PRICE_CONTRADICTION")
    if formbad:fatal.append("CURRENT_FEATURE_FORMULA_MISMATCH")
    if duplicates["conflicting_update_identity_count"] or duplicates["ambiguous_time_state_collisions"]:fatal.append("UNRELIABLE_EVENT_IDENTITY")
    overlaps=[]
    for i,a in enumerate(catalog):
        for b in catalog[i+1:]:
            if max(a["start"],b["start"])<min(a["end_exclusive"],b["end_exclusive"]):overlaps.append([a["source_id"],b["source_id"]])
    if overlaps:fatal.append("OVERLAPPING_SOURCE_INTERVALS_FOR_FIXED_ROLLING_DESIGN")
    inventory=[];earlier=0
    for k,v in stats.items():
        items=[r for r in rows if (r["source"],r["session"])==k];times=sorted({r["t"] for r in items})
        for r in items:
            j=bisect.bisect_left(times,r["t"]+1000)
            if j<len(times) and times[j]<r["end"]:earlier+=1
        if v["backwards"] or v["update_backwards"] or v["record_nonincrease"] or v["max_observed_gap_ms"]>1001:fatal.append("UNRELIABLE_TIME_CONTINUITY")
        reg=regions[k];public={name:value for name,value in v.items() if name!="last"}
        public.update({"source_id":k[0],"session_id":k[1],"event_time_start_utc":c.utc(v["min_time"]),"event_time_end_utc":c.utc(v["max_time"]),"span_ms":v["max_time"]-v["min_time"],
            "registered_source_start":reg["start"],"registered_source_end_exclusive":reg["end_exclusive"],
            "provided_update_id_semantics":"CSV alias, not independently verified Binance U/u ranges","capture_identity_status":"UNKNOWN; registry alias only",
            "witness_eligible_rows":sum(r["eligible"] for r in items),"registry_provenance":reg["registry"],"historical_exact_CSV_writer":"UNKNOWN"})
        inventory.append(public)
    if earlier:fatal.append("OBSERVED_EARLIER_MATCH_CONTRADICTION")
    if old.sha(c.TRAIN)!=expected["sha256"]:raise ValueError("TRAIN_CHANGED_DURING_AUDIT")
    return {"rows":rows,"mapping":mapping,"group_bounds":bounds,"catalog":catalog,"inventory":inventory,"fatal_reasons":sorted(set(fatal)),
      "duplicates":{**duplicates,"source_interval_overlaps":overlaps,"unique_sample_IDs":len(mapping),"independent_capture_identity":"NOT_PROVEN"},
      "audit":{"Train_rows":len(rows),"legacy_quality_pass_rows":sum(r["legacy_eligible"] for r in rows),"witness_eligible_rows":sum(r["eligible"] for r in rows),
        "endpoint_witness":witness,"observed_endpoint_price_mismatch":len(pricebad),"observed_earlier_match_contradiction":earlier,
        "current_feature_formula_mismatches":dict(formbad),"actual_endpoint_consistency":"target_event_time_ms == event_time_ms + actual_horizon_ms; checked every row",
        "cross_session_label_evidence":"All endpoints inside matching registered source/session bounds; selected candidates require same-source/session endpoint witness",
        "unobserved_endpoints":"Not declared invalid; filtered current rows/session tails can remove witnesses. No re-matching, filling or data expansion.",
        "future_feature_scope":"Current-row arithmetic verified; exact upstream CSV writer/capture authenticity UNKNOWN",
        "time_source":"Provided historical event_time_ms; exact original producer/clock implementation UNKNOWN, no receive-time or latency inference",
        "class_labels_consulted":False,"model_or_Kernel_operations":0}}
