"""Exactly one fixed evaluation plus one independent deterministic repeat."""
import json,time,random,warnings
import numpy as np
from sklearn.svm import SVC
from sklearn.exceptions import ConvergenceWarning
from qiskit_machine_learning.algorithms import QSVC
from experiments.phase4a1.kernel import compute,validate
from experiments.phase4a1.metrics import score,distribution,close_tree
from experiments.phase4a2.analysis import rbf as algebra_rbf,kernel_diagnostics
from . import contracts as c,sampling
from experiments.phase4a1 import contracts as old

def model(kind):
    if kind not in ("RBF","QSVC"):raise ValueError("UNKNOWN_MODEL")
    policy=c.protocol()[kind]
    out=SVC(**policy) if kind=="RBF" else QSVC(**policy) if kind=="QSVC" else None
    if out is None:raise ValueError("UNKNOWN_MODEL")
    params=out.get_params(deep=False)
    if any(params[k]!=v for k,v in policy.items()):raise ValueError("MODEL_PARAMETER_MISMATCH")
    return out
def fitted(m,x,y):
    start=time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always");m.fit(x,y)
    if any(issubclass(w.category,ConvergenceWarning) for w in caught):raise ValueError("MODEL_NOT_CONVERGED")
    return {"seconds":time.perf_counter()-start,"warnings":[{"category":w.category.__name__,"message":str(w.message)} for w in caught]}
def prediction(m,x):
    start=time.perf_counter();pred=np.asarray(m.predict(x),dtype=np.int64)
    if pred.shape!=(96,) or not set(pred)<={0,1,2}:raise ValueError("PREDICTION_INVALID")
    return pred,time.perf_counter()-start
def stage(run,name):
    if name not in ("first","repeat"):raise ValueError("ONLY_FIRST_AND_ONE_REPEAT")
    folder=run/name;folder.mkdir(exist_ok=False)
    b=sampling.load(run);tr=b["Train"];va=b["Validation"];np.random.seed(42);random.seed(42)
    before={s:c.input_identity(b[s]["ids"],b[s]["x"],b[s]["y"]) for s in ("Train","Validation")}
    result={"stage":name,"inputs":before,"new_preprocessing_fit":False,"models":{}}
    def emit(label,processed):
        print(json.dumps({"stage":name+":"+label,"processed":processed,"total":4,"percent":25*processed,"elapsed_seconds":time.perf_counter()-start,
          "eta_seconds":(time.perf_counter()-start)/processed*(4-processed) if processed else "NOT_AVAILABLE"}),flush=True)
    def archive(kind,m,pred,fit,predict_seconds):
        lower=kind.lower();metric=score(va["y"],pred)
        c.write(folder/(lower+"_metrics.json"),metric);c.write(folder/(lower+"_config.json"),m.get_params(deep=False))
        c.write_csv(folder/(lower+"_predictions.csv"),("sample_id","true_class","predicted_class"),
            [{"sample_id":sid,"true_class":int(va["y"][i]),"predicted_class":int(pred[i])} for i,sid in enumerate(va["ids"])])
        result["models"][lower]={"metrics":metric,"predictions":pred.tolist(),"fit":fit,"predict_seconds":predict_seconds,
             "effective_class_weight":{c.NAMES[int(cls)]:float(weight) for cls,weight in zip(m.classes_,m.class_weight_)},
             "support_count_by_class":{c.NAMES[int(cls)]:int(n) for cls,n in zip(m.classes_,m.n_support_)}}
    start=time.perf_counter();emit("RBF_BEGIN",0)
    r=model("RBF");rf=fitted(r,tr["x"],tr["y"]);rp,rt=prediction(r,va["x"]);archive("RBF",r,rp,rf,rt);emit("RBF_COMPLETE",1)
    tt,vt,circuit,kt=compute(tr["x"],va["x"]);checked=validate(tt,vt,96,96)
    if circuit!=old.read(c.P1/"prototype/first/circuit_manifest.json"):raise ValueError("FEATURE_MAP_CHANGED")
    c.save(folder/"train_kernel.npy",tt);c.save(folder/"validation_kernel.npy",vt)
    c.write(folder/"kernel_validation.json",checked);c.write(folder/"circuit_manifest.json",circuit);emit("QUANTUM_MATRIX_COMPLETE",2)
    q=model("QSVC");qf=fitted(q,tt.copy(),tr["y"]);qp,qt=prediction(q,vt.copy());archive("QSVC",q,qp,qf,qt);emit("QSVC_COMPLETE",3)
    for s in ("Train","Validation"):
        if c.input_identity(b[s]["ids"],b[s]["x"],b[s]["y"])!=before[s]:raise ValueError("MODEL_MUTATED_INPUT")
    rk=algebra_rbf(tr["x"],tr["x"]);rv=algebra_rbf(va["x"],tr["x"])
    c.save(folder/"rbf_train_kernel.npy",rk);c.save(folder/"rbf_validation_kernel.npy",rv)
    qd=kernel_diagnostics(tt,vt,tr["y"],va["y"]);rd=kernel_diagnostics(rk,rv,tr["y"],va["y"])
    c.write(folder/"quantum_kernel_diagnostics.json",qd);c.write(folder/"rbf_kernel_diagnostics.json",rd)
    result.update({"status":"PASS","kernel_validation":checked,"circuit":circuit,"quantum_timing":kt,"input_hashes_unchanged":True,
          "frozen_subset_sha256":old.sha(run/"natural_train_subset_manifest.json"),"preprocessing_clip":b["clip"],"wall_seconds":time.perf_counter()-start})
    c.write(folder/"stage_results.json",result);emit("DIAGNOSTICS_COMPLETE",4)
    return result,{"quantum_train":tt,"quantum_validation":vt,"rbf_train":rk,"rbf_validation":rv}
def determinism(first,fa,repeat,ra):
    checks={"input_hashes_and_ids":first["inputs"]==repeat["inputs"],"subset_manifest_sha":first["frozen_subset_sha256"]==repeat["frozen_subset_sha256"]}
    diffs={}
    for name in fa:
        checks[name+"_allclose"]=bool(np.allclose(fa[name],ra[name],atol=1e-10,rtol=1e-9))
        diffs[name]=float(abs(fa[name]-ra[name]).max())
    for name in ("rbf","qsvc"):
        x=first["models"][name];y=repeat["models"][name]
        checks[name+"_predictions"]=x["predictions"]==y["predictions"]
        checks[name+"_metrics"]=close_tree(x["metrics"],y["metrics"],atol=1e-12,rtol=1e-12)
        checks[name+"_confusion"]=x["metrics"]["confusion_matrix"]==y["metrics"]["confusion_matrix"]
        checks[name+"_effective_weights"]=x["effective_class_weight"]==y["effective_class_weight"]
    return {"status":"PASS" if all(checks.values()) else "FAIL","checks":checks,"kernel_max_abs_differences":diffs,"matrix_atol":1e-10,"matrix_rtol":1e-9,"metric_atol":1e-12,"metric_rtol":1e-12,
         "versions_fixed":c.environment(),"same_frozen_sample_IDs":True,"new_preprocessing_fit":False,"result_selection_from_repeat":False,"timings_compared":False}
def root_assessment(oldmetrics,newmetrics):
    return {"unique_causal_root_proven":False,"Validation_status":"Repeated exploratory Validation; not a new independent out-of-sample test",
      "assessments":[
        {"factor":"label_blind_selection","classification":"CONFIRMED","evidence":"subset/selection_commitment.json and synthetic poison-label fixture","limit":"Deterministic finite temporal budget is not guaranteed to match full-market priors exactly."},
        {"factor":"mapping_unchanged","classification":"CONFIRMED","evidence":"fixed_preprocessing_validation.json, first/repeat input hashes","limit":"Balanced-budget mapping may clip or compress Natural Train; no map refit allowed."},
        {"factor":"class_prior_effect","classification":"SUPPORTED_BUT_NOT_CAUSALLY_PROVEN","evidence":"class_distribution_comparison.json; original_vs_natural_metrics.json","limit":"Training IDs, feature/time distribution and effective balanced weights changed together; cannot isolate priors alone."},
        {"factor":"single_root_or_generalization","classification":"INSUFFICIENT_EVIDENCE","evidence":"only one96-row Natural Train and reused96-row Validation","limit":"No fresh Test/Holdout; no uniquely established causal root or independent financial generalization."},
        {"factor":"retuning_or_Validation_sampling","classification":"RULED_OUT","evidence":"protocol.json, selection commitment before class counts, frozen subset checks","limit":"Limited to this executed protocol."},
        {"factor":"quantum_advantage","classification":"INSUFFICIENT_EVIDENCE","evidence":"fixed small CPU statevector controlled comparison","limit":"Score changes alone cannot establish quantum advantage, optimal hyperparameters or trading utility."}],
      "scores":{"A":oldmetrics,"B":newmetrics}}
def compare_outputs(run,manifest,first,repeat,det):
    a=old.read(c.P1/"prototype/first/stage_results.json");b=first["models"]
    if first["inputs"]["Validation"]!={k:a["input_identity"]["Validation"][k] for k in ("ids","array_sha256","labels_sha256")}:raise ValueError("A_B_VALIDATION_NOT_IDENTICAL")
    originals={m:a["models"][m]["metrics"] for m in ("rbf","qsvc")};new={m:b[m]["metrics"] for m in ("rbf","qsvc")}
    refs={}
    paths=[c.P1/"prototype/first"/name for name in ("stage_results.json","preprocessing_manifest.json","rbf_predictions.csv","qsvc_predictions.csv","rbf_metrics.json","qsvc_metrics.json","train_kernel.npy","validation_kernel.npy","rbf_config.json","qsvc_config.json")]
    paths +=[c.P2/name for name in ("quantum_kernel_diagnostics.json","rbf_kernel_diagnostics.json","class_imbalance_report.json","confusion_analysis.json")]
    for path in paths:refs[str(path)]=old.fp(path)
    c.write(run/"experiment_A_reference.json",{"source_run":"20261029T232311Z","diagnostic_run":"20261030T000951Z","files":refs,"A_retrained":False})
    for m in ("rbf","qsvc"):c.write(run/(m+"_metrics.json"),new[m])
    c.write(run/"original_vs_natural_metrics.json",{"A":originals,"B":new,"primary_B_result":"first; repeat only for determinism","Validation_reused_exploratory":True})
    c.write(run/"class_distribution_comparison.json",{"class_order":list(c.NAMES),"A_Train":a["class_distributions"]["Train"],"B_Train":manifest["Train_class_counts"],
       "Validation":a["class_distributions"]["Validation"],"A_predictions":{m:originals[m]["predicted_class_distribution"] for m in originals},
       "B_predictions":{m:new[m]["predicted_class_distribution"] for m in new},
       "A_balanced_effective_weights":{n:1. for n in c.NAMES},"B_effective_weights":{m:b[m]["effective_class_weight"] for m in b},
       "Train_ID_overlap_A_B":len(set(a["input_identity"]["Train"]["ids"])&set(manifest["Train_identity"]["ids"])),
       "note":"Fixed balanced policy has different effective weights when class counts change; membership and covariates also change."})
    rows=[]
    for experiment,metrics in (("A",originals),("B",new)):
        for m,values in metrics.items():
            for i,truth in enumerate(c.NAMES):
                for j,pred in enumerate(c.NAMES):rows.append({"experiment":experiment,"model":m,"true_class":truth,"predicted_class":pred,"count":values["confusion_matrix"][i][j]})
    c.write_csv(run/"confusion_comparison.csv",("experiment","model","true_class","predicted_class","count"),rows)
    for name in ("quantum","rbf"):
        qa=old.read(c.P2/(name+"_kernel_diagnostics.json"));qb=old.read(run/"first"/(name+"_kernel_diagnostics.json"))
        c.write(run/(name+"_kernel_diagnostics.json"),{"A":qa,"B":qb,"entropy_effective_rank_delta_B_minus_A":qb["entropy_effective_rank"]-qa["entropy_effective_rank"],
            "interpretation":"Larger effective rank does not necessarily imply better prediction; priors and class-pair mixture differ. Within/between diagonal excluded."})
    c.write(run/"root_cause_assessment.json",root_assessment(originals,new))
    c.write(run/"proposed_next_experiment.json",{"status":"PROPOSAL_ONLY_NOT_EXECUTED","design":"On exactly the SAME newly frozen Natural Train96 and same angle mapping/Validation IDs, compare predefined class_weight=None vs balanced.",
       "reason":"Isolates the effective-weight treatment while keeping membership fixed; no new sampling, map or C/gamma changes in that future protocol.",
       "requires":"Separate protocol, new run_id, manual approval; repeated Validation remains exploratory; no Test/Holdout selection."})
def run(run_id):
    run=c.runpath(run_id)
    if not (run/"summary/preflight.json").exists() or old.read(run/"protocol.json")!=c.protocol():raise ValueError("PREFLIGHT_OR_PROTOCOL_MISSING")
    if old.read(run/"summary/accepted_unit_tests.json")["status"]!="PASS":raise ValueError("TESTS_REQUIRED")
    for name,v in old.read(run/"summary/accepted_code_manifest.json").items():
        if old.fp(c.ROOT/name)!=v:raise ValueError("SOURCE_CHANGED")
    c.write(run/"environment.json",c.environment());c.write(run/"summary/integrity_before.json",old.integrity(run))
    manifest=sampling.build(run)
    first,fa=stage(run,"first");repeat,ra=stage(run,"repeat");det=determinism(first,fa,repeat,ra);c.write(run/"determinism.json",det)
    if det["status"]!="PASS":raise ValueError("DETERMINISM_FAILURE")
    compare_outputs(run,manifest,first,repeat,det)
    c.verify_freeze(run);integ=old.integrity(run)
    integ.update({"Natural_budget_FROZEN_unchanged":True,"all_old_A_results_unchanged":True,"formal_model_fits":4,"formal_Quantum_kernel_matrices":4,
       "Test_results_parsed":False,"Test_features_labels_parsed":False,"Final_Holdout_LOCKED":True})
    c.write(run/"integrity_report.json",integ)
    c.write(run/"analysis_input_access.json",{"CSV_streams":c.CSV_ACCESS,"other_value_access":"A saved Train/Validation inputs/metrics/diagnostics; Train-only manifest and dataset schemas",
       "integrity_scope":"Other protected non-Holdout files opaque SHA only; Holdout stat and prior sealed SHA, no content read","Test_or_Holdout_features_labels_results_used":False})
    return {"status":"EXPERIMENT_COMPLETE_PENDING_REPORT_AND_AUDIT","run_id":run_id,"Train_class_counts":manifest["Train_class_counts"]}
