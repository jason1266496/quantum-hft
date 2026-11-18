"""Fixed protocol, exclusive outputs and verified environment."""
import csv,json,re,hashlib,sys,importlib.metadata as md
from pathlib import Path
import numpy as np
from experiments.phase4a1 import contracts as old
ROOT=old.ROOT
P3=ROOT/"artifacts/phase4a3/20261030T002304Z"
P1=ROOT/"artifacts/phase4a1/20261029T232311Z"
FEATURES=old.FEATURES
NAMES=old.NAMES
VALUE_READS=[]
def runpath(run_id):
    if not re.fullmatch(r"\d{8}T\d{6}Z",run_id):raise ValueError("BAD_RUN_ID")
    return ROOT/"artifacts/phase4a4"/run_id
def safe(p):
    p=Path(p)
    if not p.is_absolute():p=ROOT/p
    if ".." in p.parts or any(v.is_symlink() for v in (p,*p.parents)):raise ValueError("UNSAFE_OUTPUT")
    if not (p.is_relative_to(ROOT/"artifacts/phase4a4") or (p.parent==ROOT/"docs" and re.fullmatch(r"PHASE4A4_REPORT_\d{8}T\d{6}Z.md",p.name))):raise ValueError("OUTPUT_SCOPE")
    return p
def write(p,value):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8") as f:
        if isinstance(value,str):f.write(value)
        else:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")
def csv_write(p,fields,rows):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
CSV_ALLOWED={P3/"subset/natural_train.csv",P3/"subset/natural_train_angles.csv",
 old.BUDGET/"prototype/validation.csv",old.BUDGET/"prototype/validation_shared_angles.csv",
 P3/"first/rbf_predictions.csv",P3/"first/qsvc_predictions.csv"}
def rows(p):
    p=Path(p)
    if p not in CSV_ALLOWED:raise ValueError("CSV_VALUE_ACCESS_PROHIBITED")
    VALUE_READS.append(str(p))
    with p.open(newline="",encoding="utf-8") as f:
        r=csv.DictReader(f);names=r.fieldnames;data=list(r)
    if len(data)!=96:raise ValueError("EXACT96_REQUIRED")
    return names,data
def identity(ids,x,y):
    return {"ids":ids,"array_sha256":old.array_sha(x),"labels_sha256":hashlib.sha256(np.ascontiguousarray(y,dtype=np.int64).tobytes()).hexdigest()}
def environment():
    if Path.cwd()!=ROOT or Path.cwd().resolve()!=ROOT or sys.executable!=old.PYTHON:raise ValueError("WORKDIR_EXECUTABLE")
    versions={p:md.version(p) for p in ("qiskit","qiskit-machine-learning","numpy","scipy","scikit-learn")}
    if versions!={"qiskit":"2.6.1","qiskit-machine-learning":"0.9.1","numpy":"2.5.4","scipy":"1.18.1","scikit-learn":"1.9.1"}:raise ValueError("VERSION_DRIFT")
    return {"python_executable":sys.executable,"python":sys.version,"versions":versions,"seed":42,"git_commit":"NOT_AVAILABLE; source SHA sealed","packages_changed":False}
def protocol():
    return {"phase":"4A-4","purpose":"Fixed-data class-weight controlled exploratory ablation","horizon_ms":1000,"feature_view":"aggregate_core_v1","feature_order":list(FEATURES),
      "classification_policy":"direction_3class_exact_v1","class_order":list(NAMES),"Train_counts":[6,80,10],"Validation_counts":[5,86,5],
      "parent_run":"20261030T002304Z","Natural_manifest_sha256":"9f8796f9305d1923ee83e9fe46b8beb695bdd21e2356787b6a9c09237aeb45c9",
      "policies":{"A":None,"B":"balanced"},"new_policy":"A only","balanced_policy":"sealed references only, never refit",
      "RBF":{"kernel":"rbf","C":100.,"gamma":.01,"class_weight":None,"probability":False},
      "QSVC":{"quantum_kernel":"precomputed","C":100.,"class_weight":None,"probability":False},
      "remaining_solver_parameters":"exact parent first configs, only class_weight key changes",
      "quantum":{"qubits":4,"feature_map":"zz_feature_map","entanglement":"linear","reps":1,"alpha":2.,"shots":None,"enforce_psd":False},
      "preprocessing":"exact existing balanced-budget angle parameters and already Frozen shared angles; transform verification only",
      "kernels":"reuse parent first Quantum Train and Validation-cross; validate four saved Quantum/RBF matrices against parent repeat and inputs",
      "new_quantum_evaluations":0,"new_model_fits":4,"execution_order":["first:RBF None","first:QSVC None","repeat:RBF None","repeat:QSVC None"],"repeat_count":1,
      "seed":42,"matrix_atol":1e-10,"matrix_rtol":1e-9,"metric_atol":1e-12,"metric_rtol":1e-12,"formula_atol":1e-12,"formula_rtol":1e-11,
      "majority_baseline":"Always FLAT on the same96, no fit or use for model selection",
      "resampling":False,"retuning":False,"new_preprocessing_fit":False,"Test_used":False,"Holdout_content_opened":False,
      "network":False,"packages_changed":False,"QPU":False,"QAOA":False,"QUBO":False,"trading":False,"backtest":False,"paper_trading":False,
      "failure_rule":"Stop and preserve evidence for any necessary acceptance failure; class coverage loss is warning, not engineering failure"}
