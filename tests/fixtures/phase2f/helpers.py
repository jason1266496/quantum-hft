"""Entirely synthetic C/D/E files; tests never open production or HFT inputs."""
import contextlib,csv,json,tempfile
from pathlib import Path
from data_pipeline.datasets.schema import HORIZONS,SPLITS,SLUG
from data_pipeline.datasets.checksums import fingerprint
FIXTURES=Path(__file__).parent
RUN="20990101T000000Z"
FEATURE_FIELDS=("schema_version","feature_view","source_id","session_id","record_index",
 "event_time_ms","local_update_id","first_update_id","final_update_id","mid_price","valid_feature_row","invalid_reason")
LABEL_FIELDS=("source_id","session_id","record_index","feature_view","requested_horizon_ms",
 "current_event_time_ms","target_event_time_ms","actual_horizon_ms","match_error_ms",
 "current_mid_price","future_mid_price","future_return_bps","valid_label","invalid_reason")
INDEX_FIELDS=("feature_view","source_id","session_id","record_index","event_time_ms",
 "event_identity","requested_horizon_ms","target_event_time_ms","split")

def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:json.dump(value,f,sort_keys=True,indent=2);f.write("\n")

def write_csv(path,fields,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");writer.writeheader();writer.writerows(rows)

def make_fixture(base):
    c,d,e=base/"C",base/"D",base/"E"
    config=base/"configs/data_sources.json"
    hft=[]
    for i in range(9):
        path=base/"artificial_hft"/f"fixture_source_{i}.csv"
        path.parent.mkdir(parents=True,exist_ok=True);path.write_text("synthetic,not_market\n")
        hft.append({"absolute_path":str(path),**fingerprint(path),"session_id":f"fake_session_{i}",
                    "event_time_start":0,"event_time_end":7900,"audit_status":"PASS"})
    write_json(config,{"sources":hft})
    contract=base/"contract.md";contract.write_text("# Artificial fixture contract\n")
    timestamp=base/"timestamp.json";write_json(timestamp,{"horizons_ms":list(HORIZONS),"max_match_error_ms":None})
    write_json(d/"schemas/label.schema.json",{"schema_version":"1.0","field_order":list(LABEL_FIELDS)})
    policies={};held={}
    for line,view in (("aggregate","aggregate_core_v1"),("depth","depth_top5_v1")):
        sid="artificial_"+line;session="session_"+sid
        schema={"schema_version":"1.0","feature_view":view,"field_order":list(FEATURE_FIELDS),
                "fields":[{"name":x,"data_type":"canonical_decimal_string" if x=="mid_price" else "string","nullable":x in ("first_update_id","final_update_id")} for x in FEATURE_FIELDS]}
        write_json(c/"schemas"/(view+".schema.json"),schema)
        features=[]
        for i in range(80):
            features.append({"schema_version":"1.0","feature_view":view,"source_id":sid,"session_id":session,
                             "record_index":str(i+1),"event_time_ms":str(i*100),"local_update_id":str(i+1),
                             "first_update_id":"","final_update_id":"","mid_price":"100",
                             "valid_feature_row":"true","invalid_reason":""})
        write_csv(c/"sources"/sid/(view+".csv"),FEATURE_FIELDS,features)
        assignments={role:[{"source_id":sid,"session_id":session,"start":start,"end_exclusive":end}]
                     for role,start,end in (("Train",0,3200),("Validation",3200,4800),("Test",4800,6400),("Final Holdout",6400,7901))}
        splits={role:{"raw_rows":32 if role=="Train" else 16,
                       "source_entries":[{"source_id":sid,"session_id":session,
                         "event_time_start":assignments[role][0]["start"],"event_time_end":assignments[role][0]["end_exclusive"]-1}],
                       "per_horizon":{}} for role in SPLITS}
        indices={role:[] for role in SPLITS};purges={role:{} for role in SPLITS}
        for h in HORIZONS:
            labels=[]
            counts={role:{"valid_label_rows":0,"invalid_label_rows":0,"match_error_filtered_rows":0,"purged_rows":0,"final_rows":0} for role in SPLITS}
            for i,feature in enumerate(features):
                t=i*100;j=i+h//100;target=j*100 if j<80 else None
                role=next(role for role,regions in assignments.items() if regions[0]["start"]<=t<regions[0]["end_exclusive"])
                label={"source_id":sid,"session_id":session,"record_index":str(i+1),"feature_view":view,
                       "requested_horizon_ms":str(h),"current_event_time_ms":str(t),
                       "target_event_time_ms":"" if target is None else str(target),
                       "actual_horizon_ms":"" if target is None else str(h),"match_error_ms":"" if target is None else "0",
                       "current_mid_price":"100","future_mid_price":"" if target is None else "100",
                       "future_return_bps":"" if target is None else "0","valid_label":"false" if target is None else "true",
                       "invalid_reason":"SESSION_TAIL_INSUFFICIENT" if target is None else ""}
                labels.append(label)
                boundary=assignments[role][0]["end_exclusive"] if role!="Final Holdout" else None
                if target is None:counts[role]["invalid_label_rows"]+=1
                else:
                    counts[role]["valid_label_rows"]+=1
                    if boundary is not None and target>=boundary:counts[role]["purged_rows"]+=1
                    else:
                        counts[role]["final_rows"]+=1
                        indices[role].append({"feature_view":view,"source_id":sid,"session_id":session,
                            "record_index":str(i+1),"event_time_ms":str(t),"event_identity":str(t)+":"+str(i+1),
                            "requested_horizon_ms":str(h),"target_event_time_ms":str(target),"split":role})
            write_csv(d/"sources"/sid/view/f"labels_{h}ms.csv",LABEL_FIELDS,labels)
            for role in SPLITS:
                splits[role]["per_horizon"][str(h)]=counts[role]
                purges[role][str(h)]={"purged_count":counts[role]["purged_rows"]}
        for role in SPLITS:
            indices[role].sort(key=lambda x:(int(x["event_time_ms"]),int(x["requested_horizon_ms"])))
            write_csv(e/line/(SLUG[role]+"_indices.csv"),INDEX_FIELDS,indices[role])
        write_json(e/line/"split_manifest.json",{"feature_view":view,"splits":splits})
        write_json(e/line/"purge_report.json",purges)
        write_json(e/line/"walk_forward_windows.json",{"window_count":0,"windows":[],"models_trained":False})
        write_json(e/line/("aggregate_split_policy.json" if line=="aggregate" else "depth_split_policy.json"),
                   {"feature_view":view,"assignments":assignments,"boundaries":[3200,4800,6400],"time_field":"event_time_ms"})
        policies[line]={"feature_view":view,"chosen_threshold_by_horizon":{str(h):"1" if line=="aggregate" else "0" for h in HORIZONS},
                         "test_data_used_for_selection":False,"final_holdout_used_for_selection":False}
        held[line]={"feature_view":view,"holdout_status":"LOCKED","sources":[{"source_id":sid,"session_id":session,
                      "event_time_start":6400,"event_time_end":7900}],"prohibited_uses":["threshold selection","scaler fitting"]}
    write_json(e/"match_error/match_error_policy.json",policies)
    write_json(e/"policies/scaler_policy.json",{"fit_split":"Train","fit_executed":False})
    write_json(e/"policies/embargo_policy.json",{"embargo_ms":0})
    write_json(e/"policies/final_holdout_manifest.json",held)
    return {"feature_root":c,"label_root":d,"split_root":e,"source_config":config,"contract":contract,"timestamp_policy":timestamp}

@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory(dir=FIXTURES) as temp:
        base=Path(temp);yield base,make_fixture(base)
