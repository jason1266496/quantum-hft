"""One locked first pass and one saved-kernel determinism repeat."""
import sys,os,time,random,json,traceback,resource
from pathlib import Path
import numpy as np
from qiskit_machine_learning.utils import algorithm_globals
from experiments.phase4a1 import contracts as old
from . import contracts as c,inputs,preprocessing as pre,numerics as num,analysis as a
READS=[];NETWORK=[];DONE=0;START=None
def guard(run):
    report=c.ROOT/"docs"/("PHASE4B1_REPORT_"+run.name+".md")
    def hook(event,args):
        if event in ("socket.connect","socket.getaddrinfo","subprocess.Popen"):NETWORK.append(event);raise RuntimeError("NETWORK_SUBPROCESS_PROHIBITED")
        if event!="open" or not isinstance(args[0],(str,bytes,os.PathLike)):return
        p=Path(os.fsdecode(args[0]));p=p if p.is_absolute() else Path.cwd()/p
        mode=str(args[1] or "");flags=int(args[2] or 0)
        if any(k in mode for k in ("w","a","x","+")) or flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC):
            if not (p.is_relative_to(run) or p==report):raise RuntimeError("WRITE_OUTSIDE_CURRENT_PHASE_RUN")
            return
        if p.suffix==".csv" and any("holdout" in k.lower() for k in p.parts):raise RuntimeError("HOLDOUT_CONTENT_PROHIBITED")
        frame=sys._getframe(1)
        while frame:
            if frame.f_code.co_name=="sha" and frame.f_code.co_filename==str(c.ROOT/"experiments/phase4a1/contracts.py"):return
            frame=frame.f_back
        if p.suffix in (".csv",".npy"):
            if not (p==c.TRAIN or p.is_relative_to(run)):raise RuntimeError("OLD_OR_FORBIDDEN_VALUES_PROHIBITED "+str(p))
            READS.append(str(p))
    sys.addaudithook(hook)
def progress(stage,fold,model="",advance=False):
    global DONE
    if advance:DONE+=1
    print(json.dumps({"stage":"FORMAL_EXECUTION","pass":stage,"fold":fold,"model":model,"processed":DONE,"total":48,"percent":100*DONE/48,"elapsed_seconds":time.perf_counter()-START,"eta_seconds":"NOT_AVAILABLE"}),flush=True)
def prep_stage(run,label,fold):
    folder=run/label/("fold_"+str(fold["fold_id"]))
    p,tr,va,diag,timing=pre.apply(fold["Train"]["x"],fold["Validation"]["x"])
    if p["fit_rows"]!=96:raise ValueError("PREPROCESSING_FIT_NOT_SELECTED_TRAIN")
    c.write(folder/"preprocessing_parameters.json",p)
    c.save(folder/"Train_angles.npy",tr);c.save(folder/"Validation_angles.npy",va)
    ids={s:fold[s]["identity"] for s in ("Train","Validation")}
    metadata={"inputs":ids,"parameters":p,"parameters_file":old.fp(folder/"preprocessing_parameters.json"),
        "angle_array_shas":{"Train":old.array_sha(tr),"Validation":old.array_sha(va)},"diagnostics":diag,"timing":timing,
        "fit_only_Train":True,"source_protocol":old.fp(c.PARENT/"preprocessing_protocol.json")}
    c.write(folder/"preprocessing_manifest.json",metadata)
    progress(label,fold["fold_id"],"preprocessing",True)
    return folder,p,tr,va,metadata
def first_kernel(run,fold,tr,va,prep):
    i=fold["fold_id"];folder=run/"kernels"/("fold_"+str(i));kernel,circuit=num.fidelity()
    c.write(folder/"circuit_manifest.json",circuit)
    progress("first",i,"Quantum Train Kernel BEGIN")
    tt,ttrain=num.quantum(kernel,tr,formal=True,tag="fold"+str(i)+"/Train")
    c.save(folder/"quantum_train.npy",tt);progress("first",i,"Quantum Train Kernel",True)
    vt,tval=num.quantum(kernel,va,tr,formal=True,tag="fold"+str(i)+"/Validation")
    c.save(folder/"quantum_validation_cross.npy",vt);progress("first",i,"Quantum Validation Kernel",True)
    qvalid=num.validate(tt,vt,96,384)
    rtt,rvt,rbftime=num.rbf_matrices(tr,va)
    c.save(folder/"rbf_train.npy",rtt);c.save(folder/"rbf_validation_cross.npy",rvt)
    rvalid=num.validate(rtt,rvt,96,384)
    progress("first",i,"RBF Kernel diagnostics",True)
    binding={"inputs":prep["inputs"],"preprocessing_sha256":prep["parameters_file"]["sha256"],"angle_array_shas":prep["angle_array_shas"]}
    c.write(folder/"input_reference.json",binding)
    matrices={}
    for name,mat in (("quantum_train.npy",tt),("quantum_validation_cross.npy",vt),("rbf_train.npy",rtt),("rbf_validation_cross.npy",rvt)):
        matrices[name]={"path":str(folder/name),"file":old.fp(folder/name),"array_sha256":old.array_sha(mat)}
    manifest={"status":"PASS","matrices":matrices,"binding":binding,"input_reference":old.fp(folder/"input_reference.json"),
        "circuit_manifest":old.fp(folder/"circuit_manifest.json"),"quantum_validation":qvalid,"rbf_validation":rvalid,
        "timing":{"quantum_Train_seconds":ttrain,"quantum_Validation_cross_seconds":tval,"quantum_total_shared_seconds":ttrain+tval,"rbf_explicit_diagnostic_matrices_seconds":rbftime},
        "QSVC_definition":"Qiskit FidelityStatevectorKernel.evaluate with frozen4qubit ZZ map; actual QSVC precomputed mode tested against standard mode on artificial inputs","kernel_repairs":False}
    c.write(folder/"kernel_manifest.json",manifest)
    return tt,vt,manifest
def reuse_kernel(run,fold,tr,va,prep,first):
    folder=run/"kernels"/("fold_"+str(fold["fold_id"]));saved=old.read(folder/"kernel_manifest.json")
    if saved!=first["kernel_manifest"]:raise ValueError("SAVED_KERNEL_MANIFEST_CHANGED")
    binding={"inputs":prep["inputs"],"preprocessing_sha256":prep["parameters_file"]["sha256"],"angle_array_shas":prep["angle_array_shas"]}
    if binding!=saved["binding"] or old.fp(folder/"input_reference.json")!=saved["input_reference"]:raise ValueError("KERNEL_INPUT_BINDING_MISMATCH")
    if old.fp(folder/"circuit_manifest.json")!=saved["circuit_manifest"]:raise ValueError("CIRCUIT_MANIFEST_CHANGED")
    arrays={}
    for name,ref in saved["matrices"].items():
        if old.fp(ref["path"])!=ref["file"]:raise ValueError("KERNEL_FILE_CHANGED")
        arr=np.load(ref["path"],allow_pickle=False)
        if old.array_sha(arr)!=ref["array_sha256"]:raise ValueError("KERNEL_ARRAY_CHANGED")
        arrays[name]=arr
    num.validate(arrays["quantum_train.npy"],arrays["quantum_validation_cross.npy"],96,384)
    num.validate(arrays["rbf_train.npy"],arrays["rbf_validation_cross.npy"],96,384)
    progress("repeat",fold["fold_id"],"verified saved Kernel reuse",True)
    return arrays["quantum_train.npy"],arrays["quantum_validation_cross.npy"],saved
def stage(run,label,fold,first=None):
    c.verify_lock(run);random.seed(42);np.random.seed(42);algorithm_globals.random_seed=42
    i=fold["fold_id"];progress(label,i,"BEGIN")
    folder,p,tr,va,prep=prep_stage(run,label,fold)
    if label=="first":tt,vt,k=first_kernel(run,fold,tr,va,prep)
    elif label=="repeat" and first is not None:tt,vt,k=reuse_kernel(run,fold,tr,va,prep,first)
    else:raise ValueError("UNKNOWN_EXECUTION_PASS")
    out={"fold_id":i,"inputs":prep["inputs"],"preprocessing_parameters":p,"preprocessing_sha256":prep["parameters_file"]["sha256"],
      "angle_array_shas":prep["angle_array_shas"],"kernels":k["matrices"],"kernel_manifest":k,"preprocessing":prep,
      "Train_distribution":{n:int(np.sum(fold["Train"]["y"]==j)) for j,n in enumerate(c.NAMES)},
      "Validation_distribution":{n:int(np.sum(fold["Validation"]["y"]==j)) for j,n in enumerate(c.NAMES)},"models":{}}
    for name in c.MODELS:
        progress(label,i,name+" BEGIN")
        if name=="Majority_FLAT":
            start=time.perf_counter();pred,execution=num.majority(fold["Train"]["y"],384)
            execution.update({"fit_seconds":0.,"predict_seconds":time.perf_counter()-start})
            if execution["class"]!=1:raise ValueError("FROZEN_TRAIN_MAJORITY_NO_LONGER_FLAT")
        else:
            x,v=(tt,vt) if name.startswith("QSVC") else (tr,va)
            pred,execution=num.learn(name,x,fold["Train"]["y"],v,formal=True,tag=label+"/fold"+str(i))
            if old.array_sha(tr)!=prep["angle_array_shas"]["Train"] or old.array_sha(va)!=prep["angle_array_shas"]["Validation"]:raise ValueError("SHARED_INPUT_MUTATED")
            if old.array_sha(tt)!=k["matrices"]["quantum_train.npy"]["array_sha256"] or old.array_sha(vt)!=k["matrices"]["quantum_validation_cross.npy"]["array_sha256"]:raise ValueError("SHARED_KERNEL_MUTATED")
        m=a.metric(fold["Validation"]["y"],pred)
        predpath=folder/(name+"_predictions.csv")
        c.csv_write(predpath,("sample_id","true_class","predicted_class"),[{"sample_id":sid,"true_class":int(y),"predicted_class":int(q)} for sid,y,q in zip(fold["Validation"]["ids"],fold["Validation"]["y"],pred)])
        record={"predictions":pred.tolist(),"prediction_sha256":old.sha(predpath),"metrics":m,"execution":execution,
            "shared_Quantum_kernel_seconds":k["timing"]["quantum_total_shared_seconds"] if name.startswith("QSVC") else 0.,
            "actual_kernel_compute_seconds_this_pass":k["timing"]["quantum_total_shared_seconds"] if name.startswith("QSVC") and label=="first" else 0.,
            "kernel_cost_note":"Shared Quantum cost once per fold, not per policy; repeat reuses it. RBF standard SVC costs include its internal kernel work."}
        c.write(folder/(name+"_result.json"),record);out["models"][name]=record
        progress(label,i,name,True)
    base=out["models"]["Majority_FLAT"]["metrics"]
    for record in out["models"].values():record["vs_majority"]={key:record["metrics"][key]-base[key] for key in ("macro_f1","balanced_accuracy","accuracy")}
    c.write(folder/"stage_results.json",out)
    c.verify_lock(run)
    return out
def safety(status):
    return {"status":status,"formal_fits":len(num.FITS),"formal_fit_records":num.FITS,"formal_Quantum_evaluate_calls":len(num.QUANTUM_CALLS),"Quantum_evaluate_records":num.QUANTUM_CALLS,
      "parsed_value_paths":sorted(set(READS)),"network_attempts":NETWORK,"Test_values_parsed":False,"Holdout_opened":False,"Holdout_status":"LOCKED",
      "resampling":False,"parameter_search":False,"packages_changed":False,"QPU":False,"Binance":False,"QAOA":False,"QUBO":False,"trading":False,"backtest":False,"paper_trading":False,"Phase4B2_started":False}
def run(run_id):
    global START
    run=c.runpath(run_id);START=time.perf_counter();c.c0.environment();guard(run)
    try:
        c.verify_lock(run)
        folds,integrity=inputs.load();c.write(run/"input_integrity.json",integrity)
        c.write(run/"fold_dataset_manifests.json",{"status":"PASS","window_manifest_sha256":c.WINDOW_SHA,"folds":[{"fold":f["fold_id"],"inputs":{s:f[s]["identity"] for s in ("Train","Validation")},"source_members":{s:f[s]["members"] for s in ("Train","Validation")},"region":f["region"],"boundary":f["boundary"]} for f in folds]})
        first=[stage(run,"first",f) for f in folds]
        repeatfolds,again=inputs.load()
        if again!=integrity:raise ValueError("REPEAT_INPUT_INTEGRITY_CHANGED")
        repeat=[stage(run,"repeat",f,first[i]) for i,f in enumerate(repeatfolds)]
        det=[a.repeat_check(x,y) for x,y in zip(first,repeat)]
        c.write(run/"determinism.json",{"status":"PASS" if all(v["status"]=="PASS" for v in det) else "DETERMINISM_FAIL","folds":det,"formal_Quantum_recomputations_for_repeat":0,"first_and_repeat_saved_separately":True})
        if any(v["status"]!="PASS" for v in det):raise ValueError("DETERMINISM_FAIL")
        if len(num.FITS)!=24 or len(num.QUANTUM_CALLS)!=6 or DONE!=48:raise ValueError("EXECUTION_BUDGET_MISMATCH")
        c.write(run/"preprocessing_manifests.json",{"status":"PASS","first":[s["preprocessing"] for s in first],"repeat":[s["preprocessing"] for s in repeat],"Train_only":True})
        c.write(run/"kernel_validation.json",{"status":"PASS","folds":[{"fold":s["fold_id"],"Quantum":s["kernel_manifest"]["quantum_validation"],"RBF":s["kernel_manifest"]["rbf_validation"],"matrices":s["kernels"],"circuit_manifest":s["kernel_manifest"]["circuit_manifest"]} for s in first],"repairs":False})
        c.write(run/"kernel_timing.json",{"scope":"local CPU exact Statevector; no QPU or HFT latency","shared_cost_counted_once_per_fold":True,"folds":[{"fold":s["fold_id"],**s["kernel_manifest"]["timing"]} for s in first],"repeat_new_Quantum_kernel_seconds":0.,
            "process_peak_RSS_KiB":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,"peak_memory_scope":"Linux ru_maxrss process lifetime high-water mark, not an isolated model allocation"})
        c.write(run/"model_metrics.json",{"status":"PASS","folds":[{"fold":s["fold_id"],"models":{n:{"metrics":v["metrics"],"vs_majority":v["vs_majority"],"execution":v["execution"]} for n,v in s["models"].items()}} for s in first]})
        c.write(run/"confusion_matrices.json",{"class_order":list(c.NAMES),"folds":[{"fold":s["fold_id"],"models":{n:v["metrics"]["confusion_matrix"] for n,v in s["models"].items()}} for s in first]})
        c.write(run/"prediction_distributions.json",{"class_order":list(c.NAMES),"folds":[{"fold":s["fold_id"],"true_distribution":s["Validation_distribution"],"models":{n:{"predicted":v["metrics"]["predicted_class_distribution"],"coverage":v["metrics"]["prediction_class_count"],"warnings":v["metrics"]["warnings"]} for n,v in s["models"].items()}} for s in first]})
        minority=[];temporal=[]
        parent=c.parent()
        for s,f in zip(first,parent["folds"]):
            critical=any(v<=1 for v in s["Train_distribution"].values())
            minority.append({"fold":s["fold_id"],"Train_support":s["Train_distribution"],"Validation_support":s["Validation_distribution"],"warnings":["MINORITY_SUPPORT_CRITICAL"] if critical else (["MINORITY_SUPPORT_LOW"] if min(s["Train_distribution"].values())<5 else []),
                 "actual_class_weights_and_C_i":{n:{k:v["execution"][k] for k in ("actual_class_weights","effective_C_i")} for n,v in s["models"].items() if n!="Majority_FLAT"},"oversampling":False})
            members=f["Validation"]["members"];overlaps=sum(x["actual_target_event_time_ms"]>=y["event_time_ms"] for x,y in zip(members,members[1:]))
            if overlaps!=f["purge_embargo_check"]["Validation_adjacent_label_overlaps"]:raise ValueError("TEMPORAL_OVERLAP_COUNT_CHANGED")
            temporal.append({"fold":s["fold_id"],"adjacent_overlapping_Validation_label_pairs":overlaps,"warnings":["TEMPORAL_DEPENDENCE_WARNING"] if overlaps else ["SERIAL_DEPENDENCE_NOT_RULED_OUT"],"independent_observations_assumed":False})
        c.write(run/"minority_support_warnings.json",{"folds":minority,"no_resampling":True})
        c.write(run/"temporal_dependence_warnings.json",{"folds":temporal,"UTC_date":"2026-08-26","independent_physical_capture_count":"UNKNOWN","witness_rule_exclusions":9203,"selection_bias_possible":True,"generalization":"NOT_ESTABLISHED"})
        c.write(run/"aggregate_metrics.json",a.aggregate(first))
        per=[];comparison=[]
        for s in first:
            for name in c.MODELS:
                v=s["models"][name];m=v["metrics"]
                for n in c.NAMES:per.append({"fold":s["fold_id"],"model":name,"class":n,**m["per_class"][n]})
                comparison.append({"fold":s["fold_id"],"model":name,**{k:m[k] for k in ("macro_f1","balanced_accuracy","accuracy","macro_precision","macro_recall")},
                    "DOWN_recall":m["per_class"]["DOWN"]["recall"],"FLAT_recall":m["per_class"]["FLAT"]["recall"],"UP_recall":m["per_class"]["UP"]["recall"],
                    "prediction_class_count":m["prediction_class_count"],"fit_seconds":v["execution"]["fit_seconds"],"predict_seconds":v["execution"]["predict_seconds"]})
        c.csv_write(run/"per_class_metrics.csv",("fold","model","class","precision","recall","f1","support"),per)
        c.csv_write(run/"fold_comparison.csv",tuple(comparison[0]),comparison)
        c.verify_lock(run);c.write(run/"final_integrity.json",old.integrity(run))
        c.write(run/"safety_audit.json",safety("PASS"))
        c.write(run/"run_result.json",{"status":"PHASE 4B-1 PASS","run_id":run_id,"formal_solver_fits":24,"formal_Quantum_evaluate_calls":6,"candidate_results_first":15,"candidate_results_repeat":15,"engineering":"PASS","exploratory_only":True,"manual_review_required":True})
        return old.read(run/"run_result.json")
    except BaseException as exc:
        c.write(run/"failure.json",{"status":"PHASE 4B-1 FAIL","type":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc(),"completed_work_units":DONE,"formal_fits":len(num.FITS),"formal_quantum_calls":len(num.QUANTUM_CALLS)})
        c.write(run/"safety_audit.json",safety("FAIL"))
        c.write(run/"run_result.json",{"status":"PHASE 4B-1 FAIL","run_id":run_id,"reason":str(exc),"do_not_retry_this_run":True})
        raise
