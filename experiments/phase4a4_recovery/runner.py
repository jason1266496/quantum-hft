"""Only None-policy fits; balanced predictions and four kernels are sealed references."""
import sys,os,json,time,random,warnings
from pathlib import Path
import numpy as np
from sklearn.svm import SVC
from sklearn.exceptions import ConvergenceWarning
from qiskit_machine_learning.algorithms import QSVC
from qiskit_machine_learning.kernels import FidelityStatevectorKernel
from experiments.phase4a1 import contracts as old
from experiments.phase4a1.metrics import score,close_tree,distribution
from experiments.phase4a4 import contracts as c,inputs
from . import analysis as a
FITS=[];AUDIT_VALUES=[];OPAQUE_OPENS=0;NETWORK_ATTEMPTS=[]
def forbidden_quantum(*args,**kwargs):raise RuntimeError("QUANTUM_RECOMPUTATION_PROHIBITED_REUSE_ONLY")
def runtime_guard(run):
    FidelityStatevectorKernel.evaluate=forbidden_quantum
    def hook(event,args):
        global OPAQUE_OPENS
        if event in ("socket.connect","socket.getaddrinfo","subprocess.Popen"):
            NETWORK_ATTEMPTS.append(event);raise RuntimeError("NETWORK_SUBPROCESS_PROHIBITED")
        if event!="open" or not isinstance(args[0],(str,bytes,os.PathLike)):return
        p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
        mode=str(args[1] or "");flags=int(args[2] or 0)
        writing=any(k in mode for k in ("w","a","x","+")) or bool(flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC))
        if writing:
            if not p.is_relative_to(run):raise RuntimeError("WRITE_OUTSIDE_NEW_RUN")
            return
        if p.suffix==".csv" and any("holdout" in k.lower() for k in p.parts):raise RuntimeError("HOLDOUT_OPEN_PROHIBITED")
        frame=sys._getframe(1)
        while frame:
            if frame.f_code.co_name=="sha" and frame.f_code.co_filename==str(c.ROOT/"experiments/phase4a1/contracts.py"):OPAQUE_OPENS+=1;return
            frame=frame.f_back
        if p.is_relative_to(c.ROOT/"artifacts"):
            allowed=(p.is_relative_to(run) or p.is_relative_to(c.P3) or p.is_relative_to(old.BUDGET/"prototype") or
                p in (old.BUDGET/"quantum_budget_subset_v1_manifest.json",old.BUDGET/"FROZEN.sha256",c.P1/"prototype/first/circuit_manifest.json") or
                (p.parent.parent==c.ROOT/"artifacts/datasets" and p.name in ("checksums.sha256","dataset_manifest.json","final_holdout_manifest.json")))
            if not allowed:raise RuntimeError("ARTIFACT_VALUE_SOURCE_PROHIBITED "+str(p))
            AUDIT_VALUES.append(str(p))
    sys.addaudithook(hook)
def model(kind,parent):
    if kind not in ("rbf","qsvc"):raise ValueError("UNKNOWN_MODEL")
    params=a.none_config(parent)
    out=SVC(**params) if kind=="rbf" else QSVC(**params)
    if not a.only_weight_changed(parent,out.get_params(deep=False)):raise ValueError("MORE_THAN_CLASS_WEIGHT_CHANGED")
    if out.C!=100. or out.probability is not False or out.random_state!=42:raise ValueError("FIXED_SOLVER_CHANGED")
    if (kind=="rbf" and (out.kernel!="rbf" or out.gamma!=.01)) or (kind=="qsvc" and out.quantum_kernel!="precomputed"):raise ValueError("KERNEL_CONFIG_CHANGED")
    return out
def fit(kind,m,x,y):
    if kind not in ("rbf","qsvc") or m.class_weight is not None or x.shape!=((96,4) if kind=="rbf" else (96,96)):raise ValueError("ONLY_NONE_FIXED_BUDGET")
    start=time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always");m.fit(x,y)
    FITS.append({"model":kind,"class_weight":None,"rows":96})
    if any(issubclass(w.category,ConvergenceWarning) for w in caught):raise ValueError("CONVERGENCE_FAILURE")
    return {"seconds":time.perf_counter()-start,"warnings":[{"category":w.category.__name__,"message":str(w.message)} for w in caught]}
def stage(run,label):
    if label not in ("first","repeat"):raise ValueError("ONLY_ONE_MANDATORY_REPEAT")
    folder=run/label;folder.mkdir(exist_ok=False);b=inputs.load();tr=b["Train"];va=b["Validation"];start=time.perf_counter()
    random.seed(42);np.random.seed(42)
    out={"status":"PASS","inputs":b["inputs"],"preprocessing_sha256":b["preprocessing_sha256"],"kernels":b["kernels"],"models":{}}
    for i,kind in enumerate(("rbf","qsvc"),1):
        print(json.dumps({"stage":label+":"+kind+"_None_BEGIN","processed":i-1,"total":2,"percent":50*(i-1),"elapsed_seconds":time.perf_counter()-start,"eta_seconds":"NOT_AVAILABLE"}),flush=True)
        m=model(kind,b["balanced"][kind]["config"])
        x=tr["x"] if kind=="rbf" else b["arrays"]["train_kernel.npy"];v=va["x"] if kind=="rbf" else b["arrays"]["validation_kernel.npy"]
        fitted=fit(kind,m,x.copy(),tr["y"].copy());t=time.perf_counter();p=np.asarray(m.predict(v.copy()),dtype=np.int64);pt=time.perf_counter()-t
        if p.shape!=(96,) or not np.isin(p,[0,1,2]).all():raise ValueError("PREDICTION_INVALID")
        metric=score(va["y"],p);predpath=folder/(kind+"_predictions.csv")
        c.csv_write(predpath,("sample_id","true_class","predicted_class"),[{"sample_id":sid,"true_class":int(va["y"][j]),"predicted_class":int(p[j])} for j,sid in enumerate(va["ids"])])
        c.write(folder/(kind+"_metrics.json"),metric);c.write(folder/(kind+"_config.json"),m.get_params(deep=False))
        weights={c.NAMES[int(k)]:float(w) for k,w in zip(m.classes_,m.class_weight_)}
        if weights!={n:1. for n in c.NAMES}:raise ValueError("NONE_EFFECTIVE_WEIGHTS")
        out["models"][kind]={"predictions":p.tolist(),"prediction_sha256":old.sha(predpath),"metrics":metric,"effective_class_weight":weights,"C_i":{n:100*w for n,w in weights.items()},
          "fit":fitted,"predict_seconds":pt,"balanced_reference_only":True}
        print(json.dumps({"stage":label+":"+kind+"_None_COMPLETE","processed":i,"total":2,"percent":50*i,"elapsed_seconds":time.perf_counter()-start,"eta_seconds":(time.perf_counter()-start)/i*(2-i)}),flush=True)
    for split in ("Train","Validation"):
        z=b[split]
        if c.identity(z["ids"],z["x"],z["y"])!=b["inputs"][split]:raise ValueError("SHARED_INPUT_MUTATED")
    for name,v in b["kernels"].items():
        if old.fp(v["source"])!=v["file"] or old.array_sha(b["arrays"][name])!=v["array_sha256"]:raise ValueError("KERNEL_MUTATED")
    c.write(folder/"stage_results.json",out)
    return out,b
def comparison(run,first,b):
    groups={}
    for gid,kind,policy in (("A1","rbf","balanced"),("A2","rbf",None),("B1","qsvc","balanced"),("B2","qsvc",None)):
        metric=b["balanced"][kind]["metrics"] if policy else first["models"][kind]["metrics"]
        if policy and not close_tree(score(b["Validation"]["y"],b["balanced"][kind]["predictions"]),metric):raise ValueError("BALANCED_REFERENCE_METRICS_MISMATCH")
        groups[gid]={"model":kind,"class_weight":policy,"metrics":metric,"source":"Phase4A-3 sealed first" if policy else "new first None"}
    c.write(run/"four_group_metrics.json",groups)
    for kind in ("rbf","qsvc"):c.write(run/(kind+"_none_metrics.json"),first["models"][kind]["metrics"])
    c.write(run/"majority_flat_baseline.json",{"policy":"Always FLAT, no training or use for model selection","metrics":a.majority(b["Validation"]["y"]),"training_performed":False})
    matrices={g:v["metrics"]["confusion_matrix"] for g,v in groups.items()}
    matrices["Majority_FLAT"]=a.majority(b["Validation"]["y"])["confusion_matrix"]
    c.write(run/"confusion_matrices.json",{"class_order":list(c.NAMES),"orientation":"row=true / column=predicted","matrices":matrices})
    changes={}
    for kind in ("rbf","qsvc"):changes[kind]=a.changes(b["Validation"]["ids"],b["Validation"]["y"],b["balanced"][kind]["predictions"],first["models"][kind]["predictions"])
    c.write(run/"prediction_changes.json",changes)
    rows=[];fields=["group","model","class_weight","macro_f1","balanced_accuracy","accuracy","macro_precision","macro_recall","DOWN_precision","DOWN_recall","DOWN_f1","FLAT_precision","FLAT_recall","FLAT_f1","UP_precision","UP_recall","UP_f1","predicted_DOWN","predicted_FLAT","predicted_UP","class_coverage","FLAT_to_DOWN","FLAT_to_UP","warnings"]
    for gid,v in groups.items():
        m=v["metrics"];row={"group":gid,"model":v["model"],"class_weight":"None" if v["class_weight"] is None else "balanced",
             **{k:m[k] for k in ("macro_f1","balanced_accuracy","accuracy","macro_precision","macro_recall")},
             "class_coverage":m["prediction_class_count"],"FLAT_to_DOWN":m["confusion_matrix"][1][0],"FLAT_to_UP":m["confusion_matrix"][1][2],"warnings":json.dumps(m["warnings"])}
        for n in c.NAMES:
            row["predicted_"+n]=m["predicted_class_distribution"][n]
            for k in ("precision","recall","f1"):row[n+"_"+k]=m["per_class"][n][k]
        rows.append(row)
    c.csv_write(run/"class_weight_comparison.csv",fields,rows)
    c.write(run/"causal_assessment.json",{"assessments":[
      {"classification":"CONFIRMED","finding":"Fixed-data/kernel/solver class_weight intervention produced these exact observed changes","evidence":"prediction_changes.json","scope":{n:d["changed_count"] for n,d in changes.items()},"limit":"Only this Natural96, mapping, solver and reused Validation96; all other checked settings invariant."},
      {"classification":"SUPPORTED_BUT_NOT_CAUSALLY_PROVEN","finding":"Changes in relative per-class penalties can affect direction/FLAT recognition.","evidence":"class_weight_config.json; four_group_metrics.json","limit":"Not proof of a market-generating mechanism or all historical failure causes."},
      {"classification":"INSUFFICIENT_EVIDENCE","finding":"Other time periods, large samples, independent generalization, quantum advantage and trading value.","evidence":"one fixed96/96 repeated exploratory comparison","limit":"No Test/Holdout, no model selection or trading."},
      {"classification":"RULED_OUT","finding":"Changed membership, preprocessing, kernel or non-weight hyperparameters within this checked comparison.","evidence":"input_integrity.json; kernel_equivalence.json; actual saved configs","limit":"Finite archived computational experiment only."}
    ],"quantum_advantage_proven":False,"all_failure_causes_proven":False,"financial_signal_or_profitability_proven":False})
    c.write(run/"proposed_next_protocol.json",{"status":"RECOMMENDATION_ONLY_NOT_EXECUTED","requires":"New preregistered protocol, new run_id and manual approval",
      "data":"Official Dataset v1 TRAIN only, multiple mutually nonoverlapping time intervals; never Test/Final Holdout for selection.",
      "time_causality":"Earlier Train then later development Validation inside each interval. Purge by actual label endpoint and feature lookback; predeclare embargo. No horizon label may cross boundary. No cross-session merge.",
      "preprocessing":"Fit each interval's scaler and angle bounds only on earlier Train; shared input per model. Do not reuse a global mapping containing internal-Validation information.",
      "fixed_candidates":"Retain both RBF/QSVC and preregistered None/balanced policies, not a unique winner chosen from today's best score; fixed C/gamma/map/reps/seed.",
      "reporting":"Predeclare windows, minimum support/inapplicable-class rules and comparison schedule; report all window per-class supports, PRF/CM and variability, no cherry-picking.",
      "validation_reuse":"Stop repeatedly tuning against current96; new TRAIN-only windows are development robustness evidence, not an independent final Test."})
def run(run_id):
    run=c.runpath(run_id);c.environment()
    if old.read(run/"experiment_protocol.json")!=c.protocol() or old.read(run/"summary/unit_tests.json")["status"]!="PASS":raise ValueError("PROTOCOL_TESTS_REQUIRED")
    for name,fp in old.read(run/"summary/code_manifest.json").items():
        if old.fp(c.ROOT/name)!=fp:raise ValueError("SOURCE_CHANGED")
    runtime_guard(run);c.write(run/"environment.json",c.environment())
    b=inputs.load()
    c.write(run/"input_integrity.json",{"status":"PASS","inputs":b["inputs"],"preprocessing_sha256":b["preprocessing_sha256"],"clipping":b["clipping"],"feature_order":list(c.FEATURES),
      "counts":{"Train":distribution(b["Train"]["y"]),"Validation":distribution(b["Validation"]["y"])},"Train_Validation_overlap":0,"new_sampling":False,"new_preprocessing_fit":False,
      "preprocessing_limit":"Mapping comes from original balanced Train, not refit on Natural Train"})
    c.write(run/"kernel_equivalence.json",{"status":"PASS","kernels":b["kernels"],"numeric_checks":b["kernel_checks"],"RBF_formula_max_differences":b["RBF_formula_differences"],
       "new_Quantum_evaluations":0,"reused_without_modification":True,"native_RBF_solver":"kernel=rbf, gamma0.01 on exact saved angle input; diagnostic matrices independently formula-checked"})
    c.write(run/"class_weight_config.json",{"None":{"weights":{n:1. for n in c.NAMES},"C_i":{n:100. for n in c.NAMES}},
      "balanced":{"weights":{"DOWN":96/(3*6),"FLAT":96/(3*80),"UP":96/(3*10)},"C_i":{"DOWN":100*96/(3*6),"FLAT":40.,"UP":320.}},
      "C":100.,"only_intervention":"class_weight None instead of balanced","balanced_fits":0,"reference":"parent recorded estimator class_weight_; no balanced refit"})
    first,b=stage(run,"first");repeat,_=stage(run,"repeat")
    det=a.compare_repeats(first,repeat,true_labels=b["Validation"]["y"]);c.write(run/"determinism.json",det)
    if det["status"]!="PASS":raise ValueError("DETERMINISM_FAIL")
    comparison(run,first,b)
    integ=old.integrity(run);c.write(run/"integrity_report.json",integ)
    c.write(run/"safety_audit.json",{"status":"PASS","model_fits":FITS,"new_model_fit_count":len(FITS),"balanced_model_fit_count":0,"new_Quantum_evaluations":0,"Quantum_evaluate_runtime_prohibited":True,
      "new_sampling":False,"new_preprocessing_fit":False,"retuning":False,"Test_values_parsed":False,"Holdout_CSV_opened":False,"Holdout_status":"LOCKED",
      "value_read_paths":sorted(set(c.VALUE_READS+AUDIT_VALUES)),"opaque_hash_opens":OPAQUE_OPENS,"network_or_subprocess_attempts":NETWORK_ATTEMPTS,
      "packages_changed":False,"QPU":False,"QAOA":False,"QUBO":False,"trading":False,"backtest":False,"paper_trading":False})
    if len(FITS)!=4 or any(v["class_weight"] is not None for v in FITS):raise ValueError("FIT_BUDGET_OR_POLICY")
    return {"status":"EXPERIMENT_COMPLETE_PENDING_REPORT_AND_SEAL","run_id":run_id}
