"""Preregister, audit, freeze IDs, then count selected labels. No models."""
import os,sys,json,csv,time,ast
from pathlib import Path
from collections import Counter
from . import contracts as c,temporal as t,audit
from experiments.phase4a1 import contracts as old
READS=[];NETWORK=[]
def guard(run):
    def hook(event,args):
        if event in ("socket.connect","socket.getaddrinfo","subprocess.Popen"):NETWORK.append(event);raise RuntimeError("NETWORK_SUBPROCESS_PROHIBITED")
        if event!="open" or not isinstance(args[0],(str,bytes,os.PathLike)):return
        p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
        mode=str(args[1] or "");flags=int(args[2] or 0)
        if any(k in mode for k in ("w","a","x","+")) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):
            if not p.is_relative_to(run):raise RuntimeError("WRITE_OUTSIDE_NEW_RUN")
            return
        if p.suffix==".csv" and any("holdout" in k.lower() for k in p.parts):raise RuntimeError("HOLDOUT_OPEN_PROHIBITED")
        frame=sys._getframe(1)
        while frame:
            if frame.f_code.co_name=="sha" and frame.f_code.co_filename==str(c.ROOT/"experiments/phase4a1/contracts.py"):return
            frame=frame.f_back
        if p.suffix==".csv":
            if p!=c.TRAIN:raise RuntimeError("NON_TRAIN_CSV_VALUES_PROHIBITED")
            READS.append(str(p))
    sys.addaudithook(hook)
def register(run):
    c.write(run/"split_protocol.json",c.split_protocol())
    c.write(run/"purge_embargo_protocol.json",{"actual_field":"target_event_time_ms (matched event timestamp, NOT nominal target)",
      "consistency":"target == event_time + actual_horizon; match_error==actual_horizon-1000; original Phase2E match error<=1ms",
      "Train_condition":"group.max_actual_label_end + embargo_ms < Validation_start; equality purged",
      "Validation_condition":"group.max_actual_label_end < same registered source/session end_exclusive",
      "feature_lookback_ms":0,"embargo_ms":0,"inherited_embargo_source":str(c.DATA/"embargo_policy.json"),"inherited_embargo_sha256":old.sha(c.DATA/"embargo_policy.json"),
      "rationale":"Current-row features have zero rolling lookback; retain Phase2E no-extra-embargo and actual endpoint purge. Serial dependence remains.",
      "duplicate_market_groups":"never split group across Train/Validation; cannot treat different source aliases as independent",
      "candidate_witness":"same-source/session endpoint row must be visible in official filtered Train and match future_mid_price",
      "unsafe_source_or_infeasible_budget":"BLOCKED; no automatic alternative or row-count changes"})
    c.write(run/"model_protocol.json",{"candidates":[{"model":"RBF-SVM","class_weight":w,"C":100.,"gamma":.01,"probability":False,"random_state":42} for w in (None,"balanced")]+
      [{"model":"QSVC","class_weight":w,"C":100.,"probability":False,"random_state":42,"map":"zz_feature_map","qubits":4,"reps":1,"entanglement":"linear","alpha":2.,"kernel":"FidelityStatevectorKernel","shots":None,"enforce_psd":False} for w in (None,"balanced")]+[{"model":"Majority-FLAT","policy":"always class1","training":False}],
      "versions":c.environment()["versions"],"horizon_ms":1000,"feature_order":list(c.FEATURES),"label_policy":"direction_3class_exact_v1",
      "missing_Train_class":"3class SVM evaluation inapplicable; preserve fold, do not resample","winner_selection":"not based on previous4A or this repeated exploratory evaluation",
      "execution_this_phase":False})
    c.write(run/"preprocessing_protocol.json",{"future_fit_rows":"each fold selected Train96 only, never all candidate rows/Validation/other folds",
      "feature_order":list(c.FEATURES),"numeric":"float64, finite only; any nonfinite invalidates fold, no imputation or silent row dropping",
      "future_formula":"z=(x-Train_mean)/Train_population_std; theta=pi*clip((z-z_Train_min)/(z_Train_max-z_Train_min),0,1)",
      "zero_std_or_constant":"constant feature angle pi/2; record mask and zero variance, no division by zero",
      "Validation":"transform only with own fold frozen parameters; record below/above clipping and nonfinite counts",
      "same_fold_shared_inputs":"RBF and QSVC receive same angles, IDs, y and feature ordering",
      "cache":"new fold-specific Kernel/input/scaler hashes; reuse within fold weight policies only, never assume previous4A kernels reusable",
      "difference_from_Phase4A":"4A fixed parameters from historical balanced Train; new fold-specific fit changes representation too. Score differences across phases cannot be attributed only to time windows.",
      "official_preprocessing_fit_performed":False})
    c.write(run/"evaluation_protocol.json",{"execution_this_phase":False,"per_fold":["macro_f1","balanced_accuracy","accuracy","per_class_precision_recall_f1","confusion_matrix","true_predicted_distributions","class_coverage","majority_FLAT","Kernel_compute_costs","event_time_span","class_support"],
      "classes":list(c.NAMES),"macro_f1":"fixed labels0/1/2, zero_division0","balanced_accuracy":"sklearn present-true-class average; missing Validation class warning; also report fixed3class macro recall/support",
      "cross_fold":["all fold values including NA reasons","mean","median","sample std ddof1 if>=2 applicable folds","worst fold","missing-class warnings","applicable fold count"],
      "uncertainty_proposal":{"method":"paired moving/nonoverlapping time-block bootstrap of saved predictions, separated by source/session and duplicate leakage groups",
         "block_rule":"future preregistered duration 5*max actual label horizon in that fold Train + feature lookback; sensitivity at10x and20x, all reported without cherry-picking",
         "minimum_blocks":20,"insufficient":"NOT_AVAILABLE if fewer20 valid blocks or missing class support; no IID event-level CI",
         "replicates":2000,"seed":42,"performed_now":False,"warning":"3 folds from one historical date are not independent market-day replicates; block length does not prove independence"},
      "cost_scope":"local CPU Kernel construction vs solver fit/predict separately; no quantum speedup, QPU or HFT latency/profit claims",
      "selection":"no model/hyperparameter selection from Test/Holdout or repeated current Validation"})
    c.write(run/"SPLIT_PROTOCOL.sha256",old.sha(run/"split_protocol.json")+"  split_protocol.json\n")
def support_policy(folds):
    missing=[{"fold":f["fold_id"],"classes":[n for n in c.NAMES if f["Train"][n]==0]} for f in folds if any(f["Train"][n]==0 for n in c.NAMES)]
    return {"status":"BLOCKED" if missing else "PASS","missing_Train_classes":missing,
      "missing_Validation_classes":[{"fold":f["fold_id"],"classes":[n for n in c.NAMES if f["Validation"][n]==0]} for f in folds if any(f["Validation"][n]==0 for n in c.NAMES)],
      "no_resampling":True,"all_selected_IDs_preserved":True}
def candidates(data,train_n=96,val_n=384):
    regions=data["catalog"];issues=list(data["fatal_reasons"])
    if len(regions)!=3:issues.append("REQUIRES_EXACTLY3_RESEARCH_SESSIONS")
    plans=[]
    for i,region in enumerate(regions,1):
        rows=[r for r in data["rows"] if (r["source"],r["session"])==(region["source_id"],region["session_id"])]
        tr,va,b,counts=t.split_candidates(rows,region,data["mapping"],data["group_bounds"],0)
        entry={"fold_id":i,"region":{k:region[k] for k in ("source_id","session_id","start","end_exclusive")},"boundary":b,
           "Train_candidates":len(tr),"Validation_candidates":len(va),"excluded":counts}
        if len(tr)<train_n or len(va)<val_n:issues.append("FOLD_"+str(i)+"_INSUFFICIENT96_384")
        plans.append((entry,tr,va))
    if issues:return {"status":"BLOCKED","reasons":sorted(set(issues)),"folds":[p[0] for p in plans]},[]
    folded=[]
    for entry,tr,va in plans:
        a=t.sample(tr,train_n);b=t.sample(va,val_n)
        check=t.check_split(a,b,data["mapping"],entry["boundary"],entry["region"]["end_exclusive"],0)
        folded.append((entry,a,b,check))
    for i,(entry,tr,va,check) in enumerate(folded):
        for other,_,v2,_ in folded[i+1:]:
            if entry["boundary"]<other["region"]["end_exclusive"] and other["boundary"]<entry["region"]["end_exclusive"]:raise ValueError("VALIDATION_WINDOWS_OVERLAP")
            if {data["mapping"][r["id"]] for r in va}&{data["mapping"][r["id"]] for r in v2}:raise ValueError("CROSS_FOLD_VALIDATION_EVENT_GROUP_OVERLAP")
    return {"status":"FEASIBLE","folds":[v[0] for v in folded]},folded
def describe(rows,mapping):
    return {"rows":len(rows),"sample_ids":[r["id"] for r in rows],"event_time_start":min(r["t"] for r in rows),"event_time_end":max(r["t"] for r in rows),
      "event_time_start_utc":c.utc(min(r["t"] for r in rows)),"event_time_end_utc":c.utc(max(r["t"] for r in rows)),
      "max_actual_label_endpoint":max(r["end"] for r in rows),"min_actual_label_endpoint":min(r["end"] for r in rows),
      "members":[{"sample_id":r["id"],"source_id":r["source"],"session_id":r["session"],"record_index":r["record"],"event_time_ms":r["t"],"provided_update_id":r["update"],
        "actual_target_event_time_ms":r["end"],"leakage_group":mapping[r["id"]],"actual_target_group":r["target_group"],"source_Train_file_row_index":r["row_index"]} for r in rows]}
def freeze(run,data,plan,folded):
    records=[];paths=[]
    for entry,tr,va,check in folded:
        row={**entry,"purge_embargo_check":check,"Train":describe(tr,data["mapping"]),"Validation":describe(va,data["mapping"])}
        for split in ("Train","Validation"):
            name="folds/fold_"+str(entry["fold_id"])+"/"+split.lower()+"_manifest.json"
            c.write(run/name,{"status":"FROZEN_BEFORE_CLASS_COUNTS","fold":entry["fold_id"],"split":split,"members":row[split],
                 "source_Train_sha256":c.split_protocol()["Dataset_Train_sha256"],"split_protocol_sha256":old.sha(run/"split_protocol.json")})
            paths.append(name)
        records.append(row)
    manifest={"status":"FROZEN","method":c.split_protocol()["method"],"class_counts_computed":False,"split_protocol_sha256":old.sha(run/"split_protocol.json"),
      "source_Train_sha256":c.split_protocol()["Dataset_Train_sha256"],"folds":records,"member_manifests":{n:old.fp(run/n) for n in paths},
      "no_labels_for_selection":True,"no_reselection_after_support_diagnosis":True}
    c.write(run/"candidate_window_manifest.json",manifest)
    names=["split_protocol.json","purge_embargo_protocol.json","model_protocol.json","preprocessing_protocol.json","evaluation_protocol.json",
        "temporal_source_audit.json","session_inventory.json","duplicate_event_audit.json",*paths,"candidate_window_manifest.json"]
    c.write(run/"FROZEN_WINDOWS.sha256","\n".join(old.sha(run/n)+"  "+n for n in names)+"\n")
    return manifest
def verify_frozen(run):
    for line in (run/"FROZEN_WINDOWS.sha256").read_text().splitlines():
        sha,name=line.split("  ",1)
        if Path(name).is_absolute() or ".." in Path(name).parts or old.sha(run/name)!=sha:raise ValueError("WINDOW_MANIFEST_CHANGED")
def class_diagnosis(run,manifest):
    verify_frozen(run)
    selected={sid:[] for f in manifest["folds"] for split in ("Train","Validation") for sid in f[split]["sample_ids"]}
    counts={f["fold_id"]:{s:{n:0 for n in c.NAMES} for s in ("Train","Validation")} for f in manifest["folds"]}
    for f in manifest["folds"]:
        for split in ("Train","Validation"):
            for sid in f[split]["sample_ids"]:selected[sid].append((f["fold_id"],split))
    seen=set()
    with c.TRAIN.open(newline="",encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sid=row["sample_id"]
            if sid in selected:
                cls=old.class_of(row["future_return_bps"]);seen.add(sid)
                for fold,split in selected[sid]:counts[fold][split][c.NAMES[cls]]+=1
    if seen!=set(selected):raise ValueError("SELECTED_IDS_DISAPPEARED")
    result=[{"fold_id":i,**v} for i,v in sorted(counts.items())]
    policy=support_policy(result)
    c.write(run/"class_support_feasibility.json",{**policy,"folds":result,"computed_only_after_freeze":True,"freeze_index":old.fp(run/"FROZEN_WINDOWS.sha256"),
      "scope":"Only selected Train/Validation IDs; no all-Train return distribution and no model score"})
    verify_frozen(run);return policy
def static_safety(paths):
    bad=[]
    for p in paths:
        for n in ast.walk(ast.parse(p.read_text())):
            if isinstance(n,ast.Import) and any(v.name.split(".")[0] in ("sklearn","qiskit","qiskit_machine_learning","torch","requests") for v in n.names):bad.append(str(p))
            if isinstance(n,ast.ImportFrom) and n.module and n.module.split(".")[0] in ("sklearn","qiskit","qiskit_machine_learning","torch","requests"):bad.append(str(p))
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ("fit","predict","evaluate"):bad.append(str(p))
    if bad:raise ValueError("MODEL_API_PROHIBITED "+str(bad))
    return {"status":"PASS","checked":[str(p) for p in paths],"model_imports_or_calls":0}
def run(run_id):
    run=c.runpath(run_id);c.environment();guard(run)
    if old.read(run/"split_protocol.json")!=c.split_protocol() or old.read(run/"summary/unit_tests.json")["status"]!="PASS":raise ValueError("PROTOCOL_AND_TESTS_REQUIRED")
    for name,v in old.read(run/"summary/code_manifest.json").items():
        if old.fp(c.ROOT/name)!=v:raise ValueError("SOURCE_CHANGED")
    c.write(run/"environment.json",c.environment())
    data=audit.scan()
    c.write(run/"temporal_source_audit.json",{"status":"BLOCKED" if data["fatal_reasons"] else "PASS_WITH_LIMITATIONS",**data["audit"],"blocking_reasons":data["fatal_reasons"],
      "source_code_evidence":{str(c.ROOT/p):old.fp(c.ROOT/p) for p in ("data_pipeline/features/formulas.py","data_pipeline/features/builder.py","data_pipeline/labels/matcher.py","data_pipeline/labels/builder.py","data_pipeline/splits/purge.py")}})
    c.write(run/"session_inventory.json",{"research_session_alias_count":len(data["inventory"]),"independent_capture_session_count":"UNKNOWN","sessions":data["inventory"]})
    c.write(run/"duplicate_event_audit.json",data["duplicates"])
    plan,folded=candidates(data)
    if plan["status"]=="FEASIBLE":
        manifest=freeze(run,data,plan,folded);support=class_diagnosis(run,manifest)
        state="PASS" if support["status"]=="PASS" else "BLOCKED"
        reasons=[] if state=="PASS" else ["MISSING_TRAIN_CLASS_IN_FIXED_FOLD"]
    else:
        c.write(run/"candidate_window_manifest.json",{**plan,"selected_IDs":[],"class_counts_computed":False})
        c.write(run/"class_support_feasibility.json",{"status":"NOT_COMPUTED_NO_FROZEN_WINDOWS","reason":plan["reasons"],"resampling":False})
        state="BLOCKED";reasons=plan["reasons"]
    c.write(run/"feasibility_result.json",{"status":"PHASE 4B-0 "+state,"reasons":reasons,"no_automatic_alternative":True,
      "alternatives_if_BLOCKED":"Only propose a separately approved Train-only expanding/time-grid design or revised budget; do not execute/reselect. Existing manifests remain frozen.",
      "recommend_Phase4B1":state=="PASS"})
    c.write(run/"summary/static_safety.json",static_safety(sorted((c.ROOT/"experiments/phase4b0").glob("*.py"))+[c.ROOT/"tools/prepare_walk_forward_protocol.py"]))
    c.write(run/"integrity_report.json",old.integrity(run))
    c.write(run/"safety_audit.json",{"status":"PASS","formal_model_fits":0,"formal_predictions":0,"formal_Quantum_kernels":0,"formal_preprocessing_fits":0,"formal_scores":0,
      "Train_value_read_paths":sorted(set(READS)),"Test_values_parsed":False,"Holdout_CSV_opened":False,"Holdout_status":"LOCKED","network_attempts":NETWORK,
      "packages_changed":False,"QPU":False,"Binance":False,"QAOA":False,"QUBO":False,"trading":False,"backtest":False,"paper_trading":False,"next_phase_started":False})
    return {"status":"PHASE 4B-0 "+state,"run_id":run_id,"reasons":reasons,"Train_rows":len(data["rows"]),"witness_eligible":data["audit"]["witness_eligible_rows"]}
