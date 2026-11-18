"""Diagnostics only: replay sealed numbers; never fit/predict/evaluate a model."""
import ast,json,sys,time,platform
from pathlib import Path
import numpy as np
from . import analysis as a
from . import io
from experiments.phase4a1 import contracts as old

def protocol():
    return {"phase":"4A-2","source_run":"20261029T232311Z","purpose":"Read-only diagnostics, not optimization",
        "max_train_rows":96,"max_validation_rows":96,"new_model_fits":0,"new_quantum_kernel_evaluations":0,
        "RBF_only_derived_kernel":"exp(-0.01*||theta_i-theta_j||^2), same saved shared angles, two <=96x96 matrices",
        "PSD_tolerance":a.TOL,"rank_threshold":"max(1e-10,1e-12*lambda_max)","concentration_empirical_rule":"off-diagonal std<=0.05 AND CV<=0.10; descriptive heuristic only",
        "periodicity_rule":"Train angle distance >=Train pair q90 and saved quantum fidelity>=0.9; descriptive only",
        "class_similarity_policy":"upper-triangle off-diagonal pairs only; diagonal excluded; no IID pair inference",
        "parameters_changed":False,"resampling":False,"Test_parsed":False,"Final_Holdout_opened":False,
        "new_preprocessing_fits":0,"network":False,"package_install":False,"QPU_jobs":0,"QAOA":False,"QUBO":False,"trading":False,"backtest":False,
        "hypothesis_statuses":["CONFIRMED","SUPPORTED_BUT_NOT_CAUSALLY_PROVEN","INSUFFICIENT_EVIDENCE","RULED_OUT"],
        "scope_limit":"Train/Validation values only from sealed Phase4A-1 referenced Phase4A-0 prototype; no original full Dataset feature analysis"}

def fairness(d):
    stage=d["stage"];params=d["params"];r=d["rbf"]["config"];q=d["qsvc"]["config"]
    flags={"Train_input_identity":True,"Validation_input_identity":True,"same_labels":True,
           "same_feature_order":params["feature_order"]==list(a.FEATURES),"same_C":r["C"]==q["C"]==100.,
           "same_class_weight":r["class_weight"]==q["class_weight"]=="balanced",
           "same_seed":r["random_state"]==q["random_state"]==42,
           "same_classification_policy":old.read(io.PARENT/"policy/fair_comparison_policy.json")["label_policy"]=="direction_3class_exact_v1",
           "frozen_RBF_gamma":r["gamma"]==.01,"QSVC_precomputed":q["quantum_kernel"]=="precomputed",
           "same_shared_angles":params["RBF_QSVC_shared_input"] is True,
           "Train_only_base_scaler":params["base_standardization"]["parameters"]["fit_split"]=="Train" and not params["base_standardization"]["parameters"]["validation_fit"] and not params["base_standardization"]["parameters"]["test_fit"] and not params["base_standardization"]["parameters"]["holdout_transformed"],
           "Train_only_angle_bounds":params["angle_fit_split"]=="Train" and params["angle_fit_rows"]==96 and not params["validation_fit"],
           "no_Test_no_Holdout":not stage["Test_used"] and not stage["Holdout_used"] and not params["test_read_or_transform"] and not params["holdout_read_or_transform"]}
    for split in ("Train","Validation"):
        flags[split+"_input_identity"]=a.verify_identity(stage["input_identity"][split],d[split]["identity"])
        saved=stage["preprocessing"]["splits"][split]
        flags[split+"_shared_array_sha"]=saved["array_sha256"]==d[split]["identity"]["array_sha256"]
    if not all(flags.values()):raise ValueError("FAIRNESS_FAILED")
    return {"status":"PASS","checks":flags,"input_identity":{s:d[s]["identity"] for s in ("Train","Validation")},"feature_order":list(a.FEATURES),
        "models":{"RBF":r,"QSVC":q},"classification_policy":"direction_3class_exact_v1: Decimal sign, negative DOWN / exact zero FLAT / positive UP",
        "evidence":["Phase4A-1 prototype/first/stage_results.json#/input_identity","Phase4A-1 prototype/first/preprocessing_manifest.json","experiments/phase4a1/runner.py::stage (saved source hash verified), common Train/Validation arrays supplied to both models"],
        "gamma_note":"QSVC gamma=scale is an inherited SVC attribute, ignored for precomputed kernels. Only RBF gamma=0.01 is operative.",
        "regularization_limit":"Same C does not imply identical effective regularization in different RKHS/kernel spectra. This is a preregistered fixed-setting controlled comparison, NOT fully optimized best-model comparison.",
        "selection_limit":"RBF gamma originated from prior Phase3B Validation selection; feature map was fixed. No equal tuning-budget or quantum-advantage claim.",
        "identity_limit":"Verified sealed common input manifests plus preserved source route; no refit or instrumentation of historical model execution."}

def assessment(q,r,pre):
    def e(id,status,finding,evidence,limit,kind="CAUSAL_HYPOTHESIS"):
        return {"id":id,"classification":status,"finding_type":kind,"finding":finding,"evidence":evidence,"causal_limit":limit}
    items=[
      e("prior_shift","CONFIRMED","Train32/32/32; Validation5/86/5; balanced weights on this Train all equal1.","class_imbalance_report.json#/balanced_class_weights_on_actual_Train","Descriptive fact; does not identify a sole cause.","DESCRIPTIVE_FACT"),
      e("imbalance_contribution","SUPPORTED_BUT_NOT_CAUSALLY_PROVEN","Prior mismatch may contribute to excessive directional predictions and poor FLAT recall.","confusion_analysis.json#/models","No natural-prior controlled retraining permitted; feature/time/decision-boundary effects confounded."),
      e("qsvc_up_errors","CONFIRMED","All5 trueUP missed:3DOWN,2FLAT. All14 predictedUP are trueFLAT.","confusion_analysis.json#/true_UP_cases","Exact errors, not a mechanism.","DESCRIPTIVE_FACT"),
      e("quantum_numerical_failure","RULED_OUT","Saved prototype Gram matrix finite, symmetric, unit diagonal and PSD at1e-10 tolerance.","quantum_kernel_diagnostics.json","Scope: saved matrix numerical validity only; not predictive utility."),
      e("prototype_clipping","RULED_OUT","Both prototype splits have zero out-of-range clipping counts.","preprocessing_analysis.json#/splits","Smoke clipping is a different24-row functional check; cannot explain prototype predictions."),
      e("constant_features","RULED_OUT","Four prototype raw/angle features are nonconstant; all values finite.","preprocessing_analysis.json#/splits","Nonconstant does not prove informative labels."),
      e("unfair_membership_or_transform","RULED_OUT","IDs, labels, feature order, fixed settings, Train-only preprocessing verified.","fairness_review.json#/checks","Scope: preserved protocol/artifacts/source evidence; not independent recollection of all past execution."),
      e("limited_label_separation","SUPPORTED_BUT_NOT_CAUSALLY_PROVEN","Current quantum feature representation may lack robust out-of-time class separation.","quantum_kernel_diagnostics.json#/class_similarity and #/centered_label_kernel_alignment; confusion_analysis.json","Full Train rank does not imply generalization; aggregate similarities are not SVM margins. No feature-map counterfactual."),
      e("quantum_empirical_near_constant","SUPPORTED_BUT_NOT_CAUSALLY_PROVEN" if q["concentration_empirical_flag"] else "RULED_OUT","Empirical near-constant flag="+str(q["concentration_empirical_flag"]),"quantum_kernel_diagnostics.json#/off_diagonal","Only the declared std/CV heuristic on this fixed matrix. Does not test asymptotic concentration."),
      e("asymptotic_quantum_concentration","INSUFFICIENT_EVIDENCE","One fixed4-qubit experiment cannot demonstrate dimension-dependent kernel concentration.","quantum_kernel_diagnostics.json#/asymptotic_kernel_concentration","Requires separately approved protocol."),
      e("periodic_folding","SUPPORTED_BUT_NOT_CAUSALLY_PROVEN" if pre["periodicity"]["far_high_similarity_pair_count"] else "INSUFFICIENT_EVIDENCE","Far/high-fidelity Train pairs="+str(pre["periodicity"]["far_high_similarity_pair_count"]),"preprocessing_analysis.json#/periodicity","Even such pairs do not prove phase folding caused classification failures; no causal intervention."),
      e("independent_mod_pi_equivalence","RULED_OUT","Single P gate periodicity does not make full ZZ map independently pi-periodic.","preprocessing_analysis.json#/periodicity","ZZ cross terms change under a single-coordinate pi shift; no altered mapping executed."),
      e("svm_margin_or_support_vectors","INSUFFICIENT_EVIDENCE","Historical support vectors, dual coefficients and decision scores unavailable.","confusion_analysis.json#/decision_function_or_dual_coefficients","No serialized fitted models; prohibited refit not performed."),
      e("rbf_near_constant_structure","CONFIRMED","RBF empirical near-constant flag="+str(r["concentration_empirical_flag"])+", effective rank="+str(r["entropy_effective_rank"]),"rbf_kernel_diagnostics.json","Descriptive geometry; good/bad regularization and performance cannot be inferred from rank alone.","DESCRIPTIVE_FACT"),
      e("optimal_regularization","INSUFFICIENT_EVIDENCE","Equal C does not equate effective regularization or establish optimality.","fairness_review.json#/regularization_limit","No C/gamma/reps/feature-map selection in this phase."),
      e("sampling_uncertainty_and_time_shift","SUPPORTED_BUT_NOT_CAUSALLY_PROVEN","Only5 Validation observations per rare class; one error changes recall by0.2.","class_imbalance_report.json; preprocessing_analysis.json","Small sample and temporal dependence limit generalization; no resampling performed."),
      e("upstream_market_label_quality","INSUFFICIENT_EVIDENCE","Sealed labels/sign policy consistent; upstream market reconstruction not independently re-audited here.","integrity_report.json; fairness_review.json","Dataset integrity is byte preservation, not proof that every market label is economically informative.")
    ]
    return {"unique_causal_root_confirmed":False,"assessment":items,"conclusion":"No uniquely established causal root. Preserve exact failures; imbalance, representation and small/time-dependent sample risks remain hypotheses. No tuning performed."}

def proposals():
    return {"status":"PROPOSALS_ONLY_NOT_EXECUTED","requires":"Separate approved protocol, new run_id and new frozen budget. No existing Test result for parameter selection; Final Holdout stays LOCKED.",
      "validation_reuse_risk":"Repeatedly inspecting this Validation can overfit research choices; preregister hypotheses and evaluation schedule before next run, with Train-only temporal development splits where feasible.",
      "experiments":[
       {"id":"natural_prior_train","design":"Build a new small Train budget from original Dataset v1 Train preserving its natural market class proportions; same fixed Validation membership and evaluation policy for paired comparison.","caution":"Current3B balanced Train cannot recover natural prior by further label-blind subsampling. No new data accessed now."},
       {"id":"fixed_class_weights","design":"Preregister None vs balanced on a natural-prior Train, or theory-fixed unequal weights; no Validation/Test weight tuning.","caution":"On current32/32/32 Train, None and balanced are exactly equivalent weights1; that comparison alone adds no treatment."},
       {"id":"feature_map","design":"One preregistered alternative such as Z-only vs current ZZ with fixed qubits/reps, same raw IDs and shared input.","caution":"One factor at a time; new protocol and budget; no map construction now."},
       {"id":"input_range","design":"One fixed alternative e.g [0,pi/2] vs [0,pi], or a predeclared smooth bounded Train-only map; RBF/QSVC share each representation.","caution":"Avoid changing both sample membership and scaler fit scope in the same treatment; no Validation-directed scaling."},
       {"id":"sample_size","design":"Subject to a new compute budget, propose96 to192 Train samples with fixed paired Validation; reuse an explicitly frozen Train-only scaling policy to isolate N.","caution":"Theoretical proposal only; no larger matrix or resampling now."},
       {"id":"time_robustness","design":"Preregister multiple contiguous time windows and Train-only purged development splits respecting actual label endpoints/feature lookback.","caution":"No shuffled CV; no IID pair/bootstrap claims; no access to existing Test for selection."},
       {"id":"primary_horizon","design":"Keep1000ms as the primary research horizon in the next protocol; any additional horizon is separately preregistered.","caution":"No horizon selection from Test/Holdout. No trading/PnL claims."}]}

def static_audit(paths):
    forbidden_imports={"qiskit","qiskit_machine_learning","sklearn","subprocess","socket","urllib","requests"}
    forbidden_calls={"fit","predict","evaluate","compute","shuffle","sample","resample"}
    problems=[]
    for path in paths:
        tree=ast.parse(path.read_text())
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):
                for m in n.names:
                    if m.name.split(".")[0] in forbidden_imports:problems.append(str(path)+":import "+m.name)
            if isinstance(n,ast.ImportFrom) and n.module and n.module.split(".")[0] in forbidden_imports:problems.append(str(path)+":from "+n.module)
            if isinstance(n,ast.Call):
                name=n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id if isinstance(n.func,ast.Name) else ""
                if name in forbidden_calls:problems.append(str(path)+":call "+name)
    if problems:raise ValueError(problems)
    return {"status":"PASS","checked_files":[str(p) for p in paths],"forbidden_imports":sorted(forbidden_imports),"forbidden_calls":sorted(forbidden_calls),"limitations":"AST guard plus data whitelist and protected hashes, not a general-purpose proof of absence of all possible effects."}

def run(run_id):
    if not __import__("re").fullmatch(r"\d{8}T\d{6}Z",run_id):raise ValueError("RUN_ID")
    run=io.ROOT/"artifacts/phase4a2"/run_id
    if not (run/"summary/preflight.json").is_file():raise ValueError("PREFLIGHT_REQUIRED")
    if old.read(run/"diagnostic_protocol.json")!=protocol():raise ValueError("PREREGISTERED_PROTOCOL_CHANGED")
    start=time.perf_counter()
    def progress(stage,i,total=5):
        t=time.perf_counter()-start;print(json.dumps({"stage":stage,"processed":i,"total":total,"percent":100*i/total,"elapsed_seconds":t,"eta_seconds":t/i*(total-i) if i else "NOT_AVAILABLE"}),flush=True)
    io.write(run/"summary/integrity_before.json",old.integrity(run));progress("INTEGRITY_AND_LOAD",1)
    d=io.load();tr=d["Train"];va=d["Validation"];y=tr["y"];yv=va["y"]
    im=a.imbalance(y,yv);im["prediction_distributions"]={}
    cm={"models":{}}
    for name in ("rbf","qsvc"):
        m=a.confusion(yv,d[name]["p"]);saved=d[name]["metrics"]
        for k in ("macro_f1","balanced_accuracy","accuracy"):
            if not np.isclose(m[k],saved[k],atol=1e-12,rtol=1e-12):raise ValueError("SAVED_METRIC_CHANGED")
        if m["confusion_matrix"]!=saved["confusion_matrix"]:raise ValueError("SAVED_CM_CHANGED")
        cm["models"][name]=m;im["prediction_distributions"][name]=m["predicted_distribution"]
    cm.update(a.error_cases(va["ids"],yv,d["rbf"]["p"],d["qsvc"]["p"],d["qcross"],y,va["raw"],va["x"]))
    io.write(run/"class_imbalance_report.json",im);io.write(run/"confusion_analysis.json",cm);progress("CLASS_ERRORS",2)
    rt=a.rbf(tr["x"],tr["x"]);rc=a.rbf(va["x"],tr["x"])
    for name,array in (("rbf_train_kernel.npy",rt),("rbf_validation_train_kernel.npy",rc)):
        with (run/name).open("xb") as f:np.save(f,array,allow_pickle=False)
    q=a.kernel_diagnostics(d["qtrain"],d["qcross"],y,yv);r=a.kernel_diagnostics(rt,rc,y,yv)
    for name,obj,kind in (("quantum",q,"Saved exact Statevector Gram, no new quantum calls"),("rbf",r,"Derived algebraically from sealed angles, gamma0.01, no estimator fit")):
        obj["provenance"]=kind
        obj["comparison"]={"centered_Quantum_RBF_alignment":a.alignment(d["qtrain"],rt),
           "off_diagonal_Quantum_RBF_Pearson":float(np.corrcoef(d["qtrain"][np.triu_indices(96,1)],rt[np.triu_indices(96,1)])[0,1])}
        if obj["diagonal_one_max_error"]>1e-10 or obj["off_diagonal"]["min"] < -1e-10 or obj["off_diagonal"]["max"]>1+1e-10:raise ValueError("INVALID_GRAM")
        io.write(run/(name+"_kernel_diagnostics.json"),obj)
    progress("KERNEL_ALGEBRA",3)
    pre={"feature_order":list(a.FEATURES),"frozen_parameters":d["params"],"splits":{},
         "base_scaler_fit_rows":3000,"angle_bounds_fit_rows":96,"new_fits":0,
         "positive_affine_cancellation":"Frozen positive StandardScaler cancels algebraically in subsequent Train min-max; angles effectively depend on the budget Train raw min/max.",
         "periodicity":a.periodicity(tr["x"],d["qtrain"],tr["ids"]),
         "Smoke_context_only":"Parent smoke preprocessing records 7 below-range spread_bps Validation values; Smoke24 is a different functional test, not this prototype score. Prototype96 clipping independently recomputed here.",
         "distribution_limit":"Quantiles/entropy/IQR describe concentration; no validation-driven change or causal threshold selection."}
    for split in ("Train","Validation"):
        s=d[split];pre["splits"][split]={"features":a.feature_distributions(s["raw"],s["x"]),"clip":s["clip"],"max_frozen_transform_error":s["transform_max_error"]}
    io.write(run/"preprocessing_analysis.json",pre)
    io.write(run/"fairness_review.json",fairness(d));io.write(run/"root_cause_assessment.json",assessment(q,r,pre));io.write(run/"proposed_experiments.json",proposals())
    io.write(run/"analysis_input_access.json",{"parsed_CSV_and_NPY_paths":io.VALUE_READS,"allowed_csv_paths":sorted(str(p) for p in io.ALLOWED_CSV),
        "Test_values_parsed":False,"Holdout_content_opened":False,"integrity_reads":"Other protected non-Holdout files SHA-streamed only; Holdout stat + prior sealed SHA, never content opened."})
    sources=sorted((io.ROOT/"experiments/phase4a2").glob("*.py"))+[io.ROOT/"tools/diagnose_quantum_kernel.py"]
    io.write(run/"summary/static_safety_review.json",static_audit(sources))
    io.write(run/"summary/runtime.json",{"python_executable":sys.executable,"python":sys.version,"numpy":np.__version__,"platform":platform.platform(),
        "new_model_fits":0,"new_quantum_kernel_evaluations":0,"new_RBF_algebra_matrices":2,"largest_matrix_shape":[96,96],"network":False,"package_changes":False,
        "randomness":"No RNG, resampling, or stochastic operations used; inherited model seed42 is unchanged."})
    progress("PREPROCESSING_FAIRNESS_HYPOTHESES",4)
    integrity=old.integrity(run);integrity.update({"phase4a1_unchanged":True,"new_model_fits":0,"new_quantum_evaluations":0,"Frozen_Subsets_unchanged":True})
    io.write(run/"integrity_report.json",integrity);progress("COMPLETE_AWAITING_REPORT_AUDIT",5)
    return {"status":"DIAGNOSTICS_COMPLETE_PENDING_REPORT_AUDIT","run_id":run_id}

if __name__=="__main__":print(json.dumps(run(sys.argv[1]),ensure_ascii=False))
