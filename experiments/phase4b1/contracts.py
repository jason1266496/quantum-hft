"""Exclusive Phase4B1 outputs and immutable pre-registration."""
import json,csv,re,sys,os
from pathlib import Path
import numpy as np
from experiments.phase4a1 import contracts as old
from experiments.phase4b0 import contracts as c0,runner as r0
ROOT=old.ROOT
PARENT=ROOT/"artifacts/phase4b0/20261030T020400Z"
TRAIN=c0.TRAIN
NAMES=old.NAMES
FEATURES=old.FEATURES
WINDOW_SHA="18e28f5c6eea162dc8d13e951969785254e3044214d56328546b5d52dcd2b396"
PARENT_SHA="2027110ee45eb0732bcffcbb482a3b3b7566cc3d4d9d5c2899eeacb9a6ab82b7"
MODELS=("RBF_None","RBF_Balanced","QSVC_None","QSVC_Balanced","Majority_FLAT")
COUNTS=(((16,76,4),(32,253,99)),((12,77,7),(28,327,29)),((13,82,1),(39,299,46)))
def runpath(run_id):
    if not re.fullmatch(r"\d{8}T\d{6}Z",run_id):raise ValueError("INVALID_RUN_ID")
    return ROOT/"artifacts/phase4b1"/run_id
def safe(p):
    p=Path(p)
    if not p.is_absolute():p=ROOT/p
    if ".." in p.parts or any(q.is_symlink() for q in (p,*p.parents)):raise ValueError("UNSAFE_PATH")
    if not (p.is_relative_to(ROOT/"artifacts/phase4b1") or (p.parent==ROOT/"docs" and re.fullmatch(r"PHASE4B1_REPORT_\d{8}T\d{6}Z.md",p.name))):raise ValueError("OUTPUT_SCOPE")
    return p
def write(p,value):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8") as f:
        if isinstance(value,str):f.write(value)
        else:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")
def csv_write(p,fields,rows):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
def save(p,array):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("xb") as f:np.save(f,array,allow_pickle=False)
    return old.fp(p)
def digest(v):return c0.canonical_sha(v)
def labels_sha(y):
    import hashlib
    return hashlib.sha256(np.ascontiguousarray(y,dtype=np.int64).tobytes()).hexdigest()
def identity(ids,x,y):
    return {"ids":ids,"IDs_sha256":digest(ids),"features_sha256":old.array_sha(x),"labels_sha256":labels_sha(y),"rows":len(ids),"feature_order":list(FEATURES)}
def parent():
    if old.sha(PARENT/"completion_manifest.json")!=PARENT_SHA or old.sha(PARENT/"candidate_window_manifest.json")!=WINDOW_SHA:raise ValueError("PARENT_WINDOW_HASH_CHANGED")
    r0.verify_frozen(PARENT)
    return old.read(PARENT/"candidate_window_manifest.json")
def code_paths():
    return sorted((ROOT/"experiments/phase4b1").glob("*.py"))+[ROOT/"tools/run_temporal_quantum_validation.py",ROOT/"tests/fixtures/phase4b1/helpers.py",ROOT/"tests/test_phase4b1.py"]
def lock(run):
    if old.read(run/"summary/unit_tests.json")["status"]!="PASS" or old.read(run/"summary/preflight.json")["status"]!="PASS":raise ValueError("GATE_NOT_PASSED")
    parent();c0.environment()
    model=old.read(PARENT/"model_protocol.json")
    model={"parent_protocol":model,"execution_candidates":list(MODELS),"baseline":"derive np.argmax Train class counts in DOWN/FLAT/UP tie order; all frozen folds are FLAT","solver_mode":{"RBF":"standard SVC rbf","QSVC":"actual Qiskit QSVC quantum_kernel='precomputed' verified against standard FidelityStatevectorKernel QSVC with artificial data"}}
    write(run/"configs/model_config.json",model)
    write(run/"configs/preprocessing_config.json",{"parent_protocol":old.read(PARENT/"preprocessing_protocol.json"),"context":"Apply the unchanged parent formula in Phase4B1; parent performed flags describe Phase4B0 only"})
    write(run/"configs/metrics_config.json",{"labels":[0,1,2],"names":list(NAMES),"zero_division":0,"averages":["macro_f1","balanced_accuracy","accuracy","macro_precision","macro_recall"],"cross_fold_std_ddof":1,
      "uncertainty":"DESCRIPTIVE_ONLY; parent text is a proposal and does not uniquely fix moving vs nonoverlapping blocks/anchors; no CI or significance calculation","all_classes_included":True})
    write(run/"configs/execution_config.json",{"first_order":"fold1/2/3, each RBF_None/RBF_Balanced/QSVC_None/QSVC_Balanced/Majority_FLAT","repeat_order":"same; one repeat; fresh Train-only preprocessing and solver fits, verified saved matrices reused",
       "seed":42,"formal_solver_fits":24,"formal_quantum_evaluate_calls":6,"train_shape":[96,96],"cross_shape":[384,96],"kernel_atol":1e-10,
       "determinism":"exact IDs/params/array hashes/predictions/metrics/CM; no tolerance applied to prediction equality",
       "thread_policy":"OMP/OPENBLAS/MKL/NUMEXPR=1","network":False,"no_parameter_search":True})
    paths=code_paths()
    refs={str(p):old.fp(p) for p in paths}
    for name in ("model_config.json","preprocessing_config.json","metrics_config.json","execution_config.json"):refs[str(run/"configs"/name)]=old.fp(run/"configs"/name)
    for name in ("split_protocol.json","preprocessing_protocol.json","model_protocol.json","evaluation_protocol.json","candidate_window_manifest.json","FROZEN_WINDOWS.sha256"):refs[str(PARENT/name)]=old.fp(PARENT/name)
    # Pin implementation dependencies and installed QSVC/SVC API source as well.
    for name in ("experiments/phase4a1/contracts.py","experiments/phase4a1/kernel.py","experiments/phase4a1/metrics.py","experiments/phase4a4_recovery/schema.py","models/classical/metrics.py","experiments/phase4b0/audit.py","data_pipeline/datasets/schema.py","data_pipeline/features/formulas.py"):
        refs[str(ROOT/name)]=old.fp(ROOT/name)
    import inspect
    from qiskit_machine_learning.algorithms import QSVC
    from sklearn.svm import SVC
    for cls in (QSVC,SVC):refs[inspect.getfile(cls)]=old.fp(inspect.getfile(cls))
    write(run/"preregistration_lock.json",{"status":"LOCKED_BEFORE_FORMAL_EXECUTION","references":refs,"window_manifest_sha256":WINDOW_SHA,
       "unit_test_evidence":old.fp(run/"summary/unit_tests.json"),"environment":c0.environment(),"scores_seen_before_lock":False,"research_scope":"Pre-registered Within-Session Temporal Validation"})
    verify_lock(run)
def verify_lock(run):
    m=old.read(run/"preregistration_lock.json")
    for name,fp in m["references"].items():
        if old.fp(name)!=fp:raise ValueError("PREREGISTRATION_CHANGED "+name)
    parent()
    return m
