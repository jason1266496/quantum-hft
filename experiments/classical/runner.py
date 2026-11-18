"""Phase 3A data access, subset construction and two-phase selection/Test experiment."""
import contextlib,csv,hashlib,importlib,json,os,platform,random,sys,time
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from models.classical import feature_policy,label_policy,obi_rule,logistic,linear_svm,rbf_svm
from models.classical.scaler import TrainOnlyScaler
from models.classical.metrics import evaluate
from models.classical.timing import fit_model,predict_batch
from models.classical.selection import choose,seal,TestGate
from models.classical.registry import write_json,write_csv,save_model,sha
from data_pipeline.datasets.checksums import fingerprint,verify_checksums

ROOT=Path("/home/jason/quantum-hft")
DATASET_ID="btcusdt_aggregate_v1_20261026T202040Z"
DATASET=ROOT/"artifacts/datasets"/DATASET_ID
OLD_FAIL_ID="20261026T205307Z"
PYTHON="/home/jason/.venvs/quantum-hft-ml/bin/python"
MODELS=("obi_rule","logistic","linear_svm","rbf_svm")
HORIZONS=(100,1000)
SCOPE="kernel_comparison_subset_v1"
def utc():return datetime.now(timezone.utc).isoformat()
def read_json(path):return json.loads(Path(path).read_text())

def dependencies():
    value={"python":sys.version,"executable":sys.executable,"prefix":sys.prefix,"modules":{},"imports":{}}
    for name in ("numpy","scipy","sklearn"):
        module=importlib.import_module(name)
        value["modules"][name]={"version":module.__version__,"file":module.__file__}
    for module,name in (("sklearn.preprocessing","StandardScaler"),("sklearn.linear_model","LogisticRegression"),
                        ("sklearn.svm","LinearSVC"),("sklearn.svm","SVC"),("sklearn.metrics","f1_score"),
                        ("sklearn.metrics","balanced_accuracy_score"),("sklearn.metrics","confusion_matrix")):
        value["imports"][name]=getattr(importlib.import_module(module),name).__module__
    if sys.executable!=PYTHON:raise ValueError("WRONG_PYTHON_INTERPRETER")
    value["status"]="PASS"
    return value

def protected_preflight():
    if Path.cwd()!=ROOT or ROOT.resolve()!=ROOT:raise ValueError("WRONG_WORKING_DIRECTORY")
    f=ROOT/"artifacts/phase2f/20261026T202040Z"
    previous=read_json(f/"summary/completion_manifest.json")
    if previous["status"]!="PHASE 2F PASS":raise ValueError("PHASE2F_NOT_PASS")
    expected=read_json(f/"summary/input_integrity_before.json")
    expected.update({str(f/name):v for name,v in previous["artifact_files_excluding_this_manifest"].items()})
    expected.update({str(ROOT/name):v for name,v in previous["new_program_files"].items()})
    expected[previous["report"]["path"]]={k:previous["report"][k] for k in ("sha256","size_bytes")}
    for saved in previous["datasets"].values():
        expected.update({str(Path(saved["path"])/name):v for name,v in saved["files"].items()})
    old=ROOT/"artifacts/phase3a"/OLD_FAIL_ID;failure=read_json(old/"summary/completion_manifest.json")
    if failure["status"]!="PHASE 3A FAIL" or failure["reason"]!="DEPENDENCY_MISSING":raise ValueError("OLD_FAIL_STATUS_CHANGED")
    expected.update({str(old/name):v for name,v in failure["new_artifact_files_excluding_this_manifest"].items()})
    expected[failure["report"]["path"]]={k:failure["report"][k] for k in ("sha256","size_bytes")}
    actual={}
    for name,saved in expected.items():
        actual[name]=fingerprint(name)
        if actual[name]!=saved:raise ValueError("PROTECTED_INPUT_CHANGED: "+name)
    for path in (f/"summary/completion_manifest.json",old/"summary/completion_manifest.json",ROOT/"models/classical/README.md"):
        actual[str(path)]=fingerprint(path)
    return actual

def scoped_validate(dataset=DATASET):
    checksum=verify_checksums(dataset)
    source=ROOT/"artifacts/phase2f/20261026T202040Z/validation/aggregate.json"
    prior=read_json(source)
    if prior["status"]!="PASS" or prior["checksums"]["dataset_tree_hash"]!=checksum["dataset_tree_hash"]:
        raise ValueError("FORMAL_VALIDATOR_EVIDENCE_MISMATCH")
    manifest=read_json(dataset/"dataset_manifest.json")
    if manifest["feature_view"]!="aggregate_core_v1":raise ValueError("DEPTH_MODEL_DATA_PROHIBITED")
    held=read_json(dataset/"final_holdout_manifest.json")
    if held["holdout_status"]!="LOCKED" or held["model_access_policy"]!="PROHIBITED_UNTIL_FINAL_EVALUATION":
        raise ValueError("HOLDOUT_NOT_LOCKED")
    fields=read_json(dataset/"dataset_schema.json")["field_order"];counts={}
    for h in HORIZONS:
        for split in ("train","validation","test","final_holdout"):
            path=dataset/f"{h}ms"/(split+".csv")
            with path.open("rb") as f:
                header=next(csv.reader([f.readline().decode("utf-8").rstrip("\n")]))
                count=sum(block.count(b"\n") for block in iter(lambda:f.read(1024*1024),b""))
            expected=read_json(dataset/split/"manifest.json")["horizons"][str(h)]["rows"]
            if header!=fields or count!=expected:raise ValueError("SCHEMA_OR_ROW_COUNT_MISMATCH")
            counts[f"{h}/{split}"]={"rows":count,"header_valid":True,"values_parsed":False}
    return {"status":"PASS","mode":"USER_APPROVED_SCOPED_VALIDATION",
            "prior_formal_validator_evidence":{"path":str(source),"status":"PASS","data_bytes_unchanged":True},
            "checksums":checksum,"schema_row_count_checks":counts,"holdout_values_parsed":False,
            "scope_note":"old full validator not rerun; hash-preserved formal PASS plus scoped current checks",
            "approval_request_id":"call_5662f59e3e9e42068f14dbbad403a516"}

def read_split(dataset,horizon,split,*,gate=None,journal=None):
    feature_policy.validate_scope("aggregate_core_v1",horizon)
    if split not in ("Train","Validation","Test"):raise ValueError("HOLDOUT_VALUES_ACCESS_PROHIBITED")
    if split=="Test":
        if gate is None:raise ValueError("TEST_LABEL_ACCESS_BEFORE_SEAL")
        gate.authorize_test_read(horizon)
    path=dataset/f"{horizon}ms"/({"Train":"train","Validation":"validation","Test":"test"}[split]+".csv")
    fields=read_json(dataset/"dataset_schema.json")["field_order"]
    rows=[];seen=set();last=-1;started=utc()
    with path.open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=fields:raise ValueError("DATASET_SCHEMA_CHANGED")
        for raw in reader:
            if raw["feature_view"]!="aggregate_core_v1" or int(raw["requested_horizon_ms"])!=horizon:
                raise ValueError("WRONG_VIEW_OR_HORIZON")
            if raw["valid_feature_row"]!="true" or raw["valid_label"]!="true":raise ValueError("INVALID_FORMAL_ROW")
            t=int(raw["event_time_ms"])
            if t<last or raw["sample_id"] in seen:raise ValueError("UNSORTED_OR_DUPLICATE_INPUT")
            last=t;seen.add(raw["sample_id"])
            row={name:raw[name] for name in ("sample_id","source_id","session_id","record_index","event_time_ms",
                  "requested_horizon_ms",*feature_policy.FEATURES,"future_return_bps")}
            rows.append(row)
    if journal is not None:journal.append({"event":"DATASET_VALUES_READ","split":split,"horizon_ms":horizon,
                    "started_at_utc":started,"finished_at_utc":utc(),"rows":len(rows),
                    "all_selections_sealed":bool(gate and gate.sealed)})
    return batch(rows,split)

def batch(rows,split):
    return {"rows":rows,"x":feature_policy.matrix(rows),"y":label_policy.labels(rows),
            "ids":[r["sample_id"] for r in rows],"split":split}

def temporal_indices(times,limit):
    if limit<1:raise ValueError("INVALID_SUBSET_LIMIT")
    order=sorted(range(len(times)),key=lambda i:int(times[i]))
    n=len(order)
    if not n:return []
    count=min(n,limit)
    positions=list(range(n)) if count==n else ([0] if count==1 else [i*(n-1)//(count-1) for i in range(count)])
    return [order[i] for i in positions]

def subset_batch(full,indices):
    return batch([full["rows"][i] for i in indices],full["split"])

def save_subset(folder,full,indices):
    split=full["split"];slug=split.lower()
    rows=[full["rows"][i] for i in indices]
    indices_hash=write_csv(folder/(slug+"_indices.csv"),("original_row_index","sample_id","event_time_ms"),
                          [(i,full["rows"][i]["sample_id"],full["rows"][i]["event_time_ms"]) for i in indices])
    fields=("sample_id","source_id","session_id","record_index","event_time_ms","requested_horizon_ms",
            *feature_policy.FEATURES,"future_return_bps","class_label")
    content=[tuple(row[name] for name in fields[:-1])+(label_policy.classify(row["future_return_bps"]),) for row in rows]
    subset_hash=write_csv(folder/(slug+".csv"),fields,content)
    y=label_policy.labels(rows)
    return {"original_split_rows":len(full["rows"]),"selected_rows":len(rows),"selected_sample_ids":[r["sample_id"] for r in rows],
            "event_time_start":int(rows[0]["event_time_ms"]),"event_time_end":int(rows[-1]["event_time_ms"]),
            "class_distribution_after_selection":label_policy.distribution(y,require_all=split=="Train"),
            "indices_sha256":indices_hash,"subset_sha256":subset_hash,
            "selection_used_class_labels":False,"selection_used_holdout":False}

class Tee:
    def __init__(self,terminal,file):self.terminal,self.file=terminal,file
    def write(self,value):self.terminal.write(value);self.file.write(value);self.file.flush()
    def flush(self):self.terminal.flush();self.file.flush()

@contextlib.contextmanager
def model_logs(state):
    stdout,stderr=sys.stdout,sys.stderr
    sys.stdout,sys.stderr=Tee(stdout,state["stdout"]),Tee(stderr,state["stderr"])
    try:yield
    finally:sys.stdout,sys.stderr=stdout,stderr

def _predict_fn(name,model):
    return (lambda rows:obi_rule.predict([r["obi_5"] for r in rows])) if name=="obi_rule" else model.predict

def _save_predictions(path,batch_value,pred):
    write_csv(path,("sample_id","true_class","predicted_class"),
              [(sample,int(y),int(p)) for sample,y,p in zip(batch_value["ids"],batch_value["y"],pred,strict=True)])

def train_select(name,horizon,train,validation,scaler,folder,gate,streams,progress):
    gate.assert_selection_open()
    scope=SCOPE if name=="rbf_svm" else "full"
    if name=="obi_rule":
        configs=[dict(obi_rule.CONFIG)];xtrain=train["rows"];xval=validation["rows"]
    else:
        configs=[dict(x) for x in {"logistic":logistic,"linear_svm":linear_svm,"rbf_svm":rbf_svm}[name].CANDIDATES]
        xtrain=scaler.transform(train["x"],split="Train")
        xval=scaler.transform(validation["x"],split="Validation")
        scaler_sha=write_json(folder/"scaler.json",scaler.artifact())
    candidates=[];fitted=[]
    state={"model_name":name,"horizon_ms":horizon,"scope":scope,"folder":folder,
           "train":train,"validation":validation,"scaler":scaler,**streams}
    with model_logs(state):
        for config in configs:
            gate.assert_selection_open()
            if name=="obi_rule":model=None;fit={"fit_wall_seconds":0.0,"fit_performed":False,"warnings":[]}
            else:
                factory={"logistic":logistic,"linear_svm":linear_svm,"rbf_svm":rbf_svm}[name]
                model=factory.make(config,scope=scope,train_rows=len(train["rows"])) if name=="rbf_svm" else factory.make(config)
                fit=fit_model(model,xtrain,train["y"])
            predict=_predict_fn(name,model)
            pred,timing=predict_batch(predict,xval,repeats=1)
            metrics=evaluate(validation["y"],pred)
            candidates.append({"config":config,"validation_metrics":metrics,"fit":fit,"validation_timing":timing})
            fitted.append((model,pred));progress["done"]+=1
            elapsed=time.perf_counter()-progress["started"]
            print(json.dumps({"stage":"VALIDATION_SELECTION","horizon":horizon,"model":name,"config":config,
                "processed":progress["done"],"total":22,"percent":round(progress["done"]*100/22,2),
                "elapsed_seconds":round(elapsed,4),"eta_seconds":round((22-progress["done"])*elapsed/progress["done"],4)}),flush=True)
        selected=choose(candidates,name);index=next(i for i,x in enumerate(candidates) if x is selected)
        model,pred=fitted[index]
        selection,digest=seal(folder/"selection_manifest.json",candidates,selected,name,horizon)
        write_json(folder/"validation_metrics.json",selected["validation_metrics"])
        _save_predictions(folder/"validation_predictions.csv",validation,pred)
        train_pred,train_time=predict_batch(_predict_fn(name,model),xtrain,repeats=1)
        write_json(folder/"train_metrics.json",evaluate(train["y"],train_pred))
        if name!="obi_rule":
            object_info=save_model(folder/"model.pkl",{"model":model,"scaler":scaler.scaler,
                "feature_order":feature_policy.FEATURES,"horizon_ms":horizon,
                "label_policy":"direction_3class_exact_v1","scope":scope})
        else:object_info=None
        config={"model":name,"horizon_ms":horizon,"dataset_scope":scope,
                "feature_policy":"aggregate_compact_v1","label_policy":"direction_3class_exact_v1",
                "candidate_grid":configs,"selected_config":selected["config"],
                "estimator_params":model.get_params() if model is not None else dict(obi_rule.CONFIG),
                "random_state":42,"scaler_used":name!="obi_rule","holdout_used":False,
                "scaler_artifact_sha256":scaler_sha if name!="obi_rule" else None,"model_object":object_info}
        write_json(folder/"config.json",config)
    state.update({"estimator":model,"selected":selected,"selection":selection,"selection_sha256":digest,
                  "fit_search_seconds":sum(x["fit"]["fit_wall_seconds"] for x in candidates),
                  "train_timing":train_time,"config":config})
    return state

def evaluate_test(state,test,gate,test_file_sha):
    name=state["model_name"];h=state["horizon_ms"];folder=state["folder"];key=f"{h}/{name}"
    selection_sha=gate.claim_evaluation(key,h)
    write_json(folder/"test_evaluation_started.json",{"selection_manifest_sha256":selection_sha,
               "started_at_utc":utc(),"retuning_allowed":False})
    with model_logs(state):
        x=test["rows"] if name=="obi_rule" else state["scaler"].transform(test["x"],split="Test")
        pred,timing=predict_batch(_predict_fn(name,state["estimator"]),x,repeats=3)
        metrics=evaluate(test["y"],pred)
        write_json(folder/"test_metrics.json",metrics)
        _save_predictions(folder/"test_predictions.csv",test,pred)
        write_csv(folder/"confusion_matrix.csv",("true_class","pred_DOWN","pred_FLAT","pred_UP"),
                  [(label_policy.CLASS_NAMES[i],*row) for i,row in enumerate(metrics["confusion_matrix"])])
        write_csv(folder/"per_class_metrics.csv",("class","precision","recall","f1","support"),
                  [(name,*[values[k] for k in ("precision","recall","f1","support")]) for name,values in metrics["per_class"].items()])
        all_timing={"timing_scope":"PYTHON_BATCH_INFERENCE_ONLY","hft_latency_claim":False,
                    "fit_wall_seconds":state["selected"]["fit"]["fit_wall_seconds"],
                    "fit_search_total_seconds":state["fit_search_seconds"],"train_predict":state["train_timing"],
                    "validation_predict":state["selected"]["validation_timing"],"test_predict":timing}
        write_json(folder/"timing.json",all_timing)
        evaluation={"horizon_ms":h,"model":name,"selected_config":state["selected"]["config"],
                    "selection_manifest_sha256":selection_sha,"test_evaluated":True,
                    "metric_evaluation_count":1,"prediction_warmup_calls":1,"prediction_timed_calls":3,
                    "predictions_identical_across_timing_repeats":len(set(timing["prediction_sha256"]))==1,
                    "test_source_file_sha256":test_file_sha,"dataset_scope":state["scope"],
                    "test_rows":len(test["rows"]),"test_metrics_sha256":sha(folder/"test_metrics.json"),
                    "evaluated_at_utc":utc(),"test_retuning_performed":False,"final_holdout_used":False,
                    "global_selection_barrier_sha256":sha(gate.barrier_path)}
        write_json(folder/"test_evaluation_manifest.json",evaluation)
        if sha(folder/"selection_manifest.json")!=selection_sha:raise ValueError("SELECTION_MANIFEST_CHANGED")
        print(json.dumps({"stage":"TEST_EVALUATED_ONCE","horizon":h,"model":name,"scope":state["scope"],"rows":len(test["rows"])}),flush=True)
    state.update({"test_metrics":metrics,"timing":all_timing,"test_evaluation":evaluation,
                  "test_rows":len(test["rows"])})
    return state

def experiment(run,dataset=DATASET):
    random.seed(42);np.random.seed(42)
    states={};class_distributions={};subsets={};journal=[];streams=[]
    paths={f"{h}/{name}":run/f"{h}ms"/name/"selection_manifest.json" for h in HORIZONS for name in MODELS}
    gate=TestGate(paths,run/"policy/all_model_selection_seal.json")
    progress={"done":0,"started":time.perf_counter()}
    horizon_data={}
    try:
        for h in HORIZONS:
            base=run/f"{h}ms";base.mkdir(exist_ok=False)
            kernel=base/"kernel_subset";kernel.mkdir(exist_ok=False)
            train=read_split(dataset,h,"Train",journal=journal);validation=read_split(dataset,h,"Validation",journal=journal)
            class_distributions[str(h)]={"Train":label_policy.distribution(train["y"],require_all=True),
                                         "Validation":label_policy.distribution(validation["y"])}
            write_json(base/"class_distribution_train_validation.json",class_distributions[str(h)])
            ti=temporal_indices([r["event_time_ms"] for r in train["rows"]],1000)
            vi=temporal_indices([r["event_time_ms"] for r in validation["rows"]],500)
            kt,kv=subset_batch(train,ti),subset_batch(validation,vi)
            subsets[h]={"Train":save_subset(kernel,train,ti),"Validation":save_subset(kernel,validation,vi)}
            label_policy.distribution(kt["y"],require_all=True)
            test_count=read_json(dataset/"test/manifest.json")["horizons"][str(h)]["rows"]
            test_positions=[i*(test_count-1)//499 for i in range(500)] if test_count>500 else list(range(test_count))
            write_json(kernel/"selection_plan.json",{"subset_id":SCOPE,"horizon_ms":h,"maximum_rows":{"Train":1000,"Validation":500,"Test":500},
                "algorithm":"stable event_time order; floor(i*(N-1)/(k-1)); include first and last",
                "test_positions_frozen_before_label_access":test_positions,
                "class_labels_used_for_sampling":False,"holdout_used":False,"source_dataset_id":DATASET_ID})
            full_scaler=TrainOnlyScaler(h,"full").fit(train["x"],split="Train",sample_ids=train["ids"])
            subset_scaler=TrainOnlyScaler(h,SCOPE).fit(kt["x"],split="Train",sample_ids=kt["ids"])
            for name in MODELS:
                folder=base/name;folder.mkdir(exist_ok=False)
                out=(folder/"stdout.txt").open("x",encoding="utf-8");err=(folder/"stderr.txt").open("x",encoding="utf-8")
                streams.extend([out,err])
                tr,val,scaler=(kt,kv,subset_scaler) if name=="rbf_svm" else (train,validation,full_scaler if name!="obi_rule" else None)
                states[h,name]=train_select(name,h,tr,val,scaler,folder,gate,{"stdout":out,"stderr":err},progress)
            horizon_data[h]={"train":train,"validation":validation,"full_scaler":full_scaler,"subset_scaler":subset_scaler,
                             "test_positions":test_positions}
        gate.freeze()
        for h in HORIZONS:
            full_test=read_split(dataset,h,"Test",gate=gate,journal=journal)
            class_distributions[str(h)]["Test"]=label_policy.distribution(full_test["y"])
            write_json(run/f"{h}ms"/"class_distribution_test.json",class_distributions[str(h)]["Test"])
            indices=temporal_indices([r["event_time_ms"] for r in full_test["rows"]],500)
            if indices!=horizon_data[h]["test_positions"]:raise ValueError("TEST_SUBSET_POSITIONS_CHANGED")
            kernel_test=subset_batch(full_test,indices)
            subsets[h]["Test"]=save_subset(run/f"{h}ms"/"kernel_subset",full_test,indices)
            write_json(run/f"{h}ms"/"kernel_subset/kernel_comparison_subset_manifest.json",
                       {"subset_id":SCOPE,"horizon_ms":h,"source_dataset_id":DATASET_ID,
                        "splits":subsets[h],"feature_policy":"aggregate_compact_v1",
                        "label_policy":"direction_3class_exact_v1",
                        "class_labels_used_for_sampling":False,"holdout_used":False,
                        "phase4_comparison_requires_same_membership":True,
                        "global_selection_barrier_sha256":sha(gate.barrier_path)})
            for name in MODELS:
                test=kernel_test if name=="rbf_svm" else full_test
                evaluate_test(states[h,name],test,gate,sha(dataset/f"{h}ms/test.csv"))
        gate.assert_all_evaluated_once()
        write_json(run/"logs/dataset_access_log.json",journal)
        write_json(run/"comparison/class_distributions.json",class_distributions)
        fields=("horizon_ms","model","dataset_scope","feature_policy","label_policy","train_rows","validation_rows","test_rows",
                "Macro-F1","Balanced Accuracy","Accuracy","selected_config","fit_time_seconds","test_predict_median_seconds","rows_per_second")
        records=[]
        for (h,name),state in states.items():
            m=state["test_metrics"];t=state["timing"]
            records.append((h,name,state["scope"],"aggregate_compact_v1","direction_3class_exact_v1",
                len(state["train"]["rows"]),len(state["validation"]["rows"]),state["test_rows"],
                m["macro_f1"],m["balanced_accuracy"],m["accuracy"],json.dumps(state["selected"]["config"],sort_keys=True),
                t["fit_wall_seconds"],t["test_predict"]["median_wall_seconds"],t["test_predict"]["rows_per_second"]))
        write_csv(run/"comparison/classical_results.csv",fields,records)
        compact={f"{h}/{name}":{"horizon_ms":h,"model":name,"dataset_scope":s["scope"],
                "selected_config":s["selected"]["config"],"train_rows":len(s["train"]["rows"]),
                "validation_rows":len(s["validation"]["rows"]),"test_rows":s["test_rows"],
                "validation_metrics":s["selected"]["validation_metrics"],"test_metrics":s["test_metrics"],
                "timing":s["timing"],"selection_sha256":s["selection_sha256"],
                "test_evaluation":s["test_evaluation"],"config":s["config"]} for (h,name),s in states.items()}
        write_json(run/"comparison/results.json",compact)
        write_json(run/"timing/summary.json",{key:value["timing"] for key,value in compact.items()})
        return {"models":compact,"class_distributions":class_distributions,
                "kernel_subsets":{str(h):data for h,data in subsets.items()},
                "test_gate":{"status":"PASS","sealed_selections":len(paths),"test_evaluations":len(gate.evaluated),
                             "selection_sha256":gate.hashes,"all_sealed_before_test_labels":True},
                "final_holdout":"FINAL_HOLDOUT_NOT_EVALUATED","holdout_values_read":False}
    finally:
        for handle in streams:handle.close()
