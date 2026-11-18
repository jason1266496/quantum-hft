"""Phase-local exclusive outputs, sealed input paths and fixed protocol."""
import csv,json,re,hashlib,sys,importlib.metadata as md
from pathlib import Path
import numpy as np
from experiments.phase4a1 import contracts as old
ROOT=old.ROOT
P1=ROOT/"artifacts/phase4a1/20261029T232311Z"
P2=ROOT/"artifacts/phase4a2/20261030T000951Z"
DATASET=ROOT/"artifacts/datasets/btcusdt_aggregate_v1_20261026T202040Z"
TRAIN=DATASET/"1000ms/train.csv"
FEATURES=old.FEATURES
NAMES=old.NAMES
CSV_ACCESS=[]
def runpath(run_id):
    if not re.fullmatch(r"\d{8}T\d{6}Z",run_id):raise ValueError("INVALID_RUN_ID")
    return ROOT/"artifacts/phase4a3"/run_id
def safe(p):
    p=Path(p)
    if not p.is_absolute():p=ROOT/p
    if ".." in p.parts or any(v.is_symlink() for v in (p,*p.parents)):raise ValueError("UNSAFE_OUTPUT")
    if not (p.is_relative_to(ROOT/"artifacts/phase4a3") or p.is_relative_to(ROOT/"tests/fixtures/phase4a3") or
       (p.parent==ROOT/"docs" and re.fullmatch(r"PHASE4A3_REPORT_\d{8}T\d{6}Z.md",p.name))):raise ValueError("OUTPUT_SCOPE")
    return p
def write(p,v):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8") as f:
        if isinstance(v,str):f.write(v)
        else:json.dump(v,f,sort_keys=True,indent=2,ensure_ascii=False,allow_nan=False);f.write("\n")
def write_csv(p,fields,rows):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
def save(p,a):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("xb") as f:np.save(f,a,allow_pickle=False)
def read_rows(p,run):
    p=Path(p)
    allowed={TRAIN,old.BUDGET/"prototype/train.csv",old.BUDGET/"prototype/validation.csv",
       old.BUDGET/"prototype/train_shared_angles.csv",old.BUDGET/"prototype/validation_shared_angles.csv",
       Path(run)/"subset/natural_train.csv",Path(run)/"subset/natural_train_angles.csv"}
    if p not in allowed:raise ValueError("CSV_SOURCE_PROHIBITED")
    CSV_ACCESS.append({"path":str(p),"mode":"value_stream","purpose":"Train universe metadata / selected rows, or fixed A/B budget"})
    with p.open(newline="",encoding="utf-8") as f:
        r=csv.DictReader(f)
        for i,row in enumerate(r):yield i,row
def check_train_checksum():
    expected=old.read(DATASET/"train/manifest.json")["horizons"]["1000"]
    if expected!={"path":"1000ms/train.csv","rows":150912,"sha256":"8628e45fe52bc1f0ef3cda20a9c31f9c72d8e4f01d1cd4f80103d624a455fd1d","size_bytes":65902450}:raise ValueError("OFFICIAL_TRAIN_MANIFEST_CHANGED")
    if old.fp(TRAIN)!={k:expected[k] for k in ("sha256","size_bytes")}:raise ValueError("OFFICIAL_TRAIN_CHECKSUM_CHANGED")
    return expected
def input_identity(ids,x,y):
    return {"ids":ids,"array_sha256":old.array_sha(x),"labels_sha256":hashlib.sha256(np.ascontiguousarray(y,dtype=np.int64).tobytes()).hexdigest()}
def protocol():
    return {"phase":"4A-3","horizon_ms":1000,"feature_view":"aggregate_core_v1","feature_order":list(FEATURES),"classification_policy":"direction_3class_exact_v1",
      "Train_size":96,"Validation_size":96,"Train_source":str(TRAIN),"Validation_reference_run":"20261029T232311Z",
      "selection":{"eligible_universe":"ALL formal 1000ms Train rows, no label/feature/result eligibility filtering",
        "sort_key":["event_time_ms:int","source_id:str","session_id:str","record_index:int","sample_id:str"],
        "rank_positions":"floor(i*(N-1)/95), i=0..95 inclusive endpoints",
        "ties":"fixed metadata lexicographic tie break; file row index records provenance only",
        "uniformity":"evenly spaced ranks AFTER event-time sort; not equal elapsed milliseconds",
        "labels_used":False,"class_counts_computed":"only AFTER selection commitment is sealed",
        "invalid_selected_row_policy":"STOP, never drop/reselect","missing_class_policy":"preserve selection/distribution, stop inapplicable 3class training"},
      "RBF":{"C":100.,"gamma":.01,"class_weight":"balanced","kernel":"rbf","probability":False,"random_state":42},
      "QSVC":{"C":100.,"class_weight":"balanced","quantum_kernel":"precomputed","probability":False,"random_state":42},
      "quantum":{"feature_map":"zz_feature_map","qubits":4,"reps":1,"entanglement":"linear","alpha":2.,"shots":None,"enforce_psd":False},
      "preprocessing":"exact Phase4A-1 Frozen Train-only scaler and balanced-budget angle bounds; transform only, no refit",
      "execution_order":["first:RBF","first:QSVC","repeat:RBF","repeat:QSVC"],"repeat_count":1,"formal_model_fits":4,"formal_quantum_kernel_matrices":4,
      "seed":42,"PSD_tolerance":1e-10,"matrix_determinism_atol":1e-10,"matrix_determinism_rtol":1e-9,"metric_atol":1e-12,"metric_rtol":1e-12,
      "interpretation":"Training membership, feature/time distribution and balanced effective weights change together; not a pure causal intervention on priors. Reused Validation is exploratory, not a new independent out-of-sample test.",
      "Test_used":False,"Final_Holdout_used":False,"retuning":False,"new_mapping_fit":False,"resampling_after_selection":False,"network":False,"package_changes":False,"QPU":False,"QAOA":False,"QUBO":False,"trading":False,"backtest":False,"paper_trading":False}
def environment():
    if Path.cwd()!=ROOT or Path.cwd().resolve()!=ROOT or sys.executable!=old.PYTHON:raise ValueError("WORKDIR_OR_EXECUTABLE")
    versions={p:md.version(p) for p in ("qiskit","qiskit-machine-learning","numpy","scipy","scikit-learn")}
    if versions!={"qiskit":"2.6.1","qiskit-machine-learning":"0.9.1","numpy":"2.5.4","scipy":"1.18.1","scikit-learn":"1.9.1"}:raise ValueError("VERSION_MISMATCH")
    return {"python_executable":sys.executable,"python":sys.version,"versions":versions,"seed":42,"new_packages":False,"git_commit":"NOT_AVAILABLE; source SHA-256 sealed"}
def verify_freeze(run):
    run=Path(run)
    for line in (run/"subset/FROZEN.sha256").read_text().splitlines():
        digest,name=line.split("  ",1);p=Path(name)
        if p.is_absolute() or ".." in p.parts or old.sha(run/p)!=digest:raise ValueError("NATURAL_BUDGET_CHANGED")
