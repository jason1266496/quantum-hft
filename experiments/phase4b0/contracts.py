"""Exclusive Phase4B0 outputs and fixed preregistration."""
import json,re,csv,hashlib,sys,importlib.metadata as md
from pathlib import Path
from datetime import datetime,timezone,timedelta
from experiments.phase4a1 import contracts as old
ROOT=old.ROOT
DATA=ROOT/"artifacts/datasets/btcusdt_aggregate_v1_20261026T202040Z"
TRAIN=DATA/"1000ms/train.csv"
REGISTRY=ROOT/"artifacts/phase2b/20261018T225515Z/registry_snapshot.json"
FEATURES=("obi_5","spread_bps","bid_volume_5","ask_volume_5")
NAMES=("DOWN","FLAT","UP")
def runpath(run_id):
    if not re.fullmatch(r"\d{8}T\d{6}Z",run_id):raise ValueError("INVALID_RUN_ID")
    return ROOT/"artifacts/phase4b0"/run_id
def safe(p):
    p=Path(p)
    if not p.is_absolute():p=ROOT/p
    if ".." in p.parts or any(q.is_symlink() for q in (p,*p.parents)):raise ValueError("UNSAFE_PATH")
    if not (p.is_relative_to(ROOT/"artifacts/phase4b0") or (p.parent==ROOT/"docs" and re.fullmatch(r"PHASE4B0_REPORT_\d{8}T\d{6}Z.md",p.name))):raise ValueError("OUTPUT_SCOPE")
    return p
def write(p,v):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8") as f:
        if isinstance(v,str):f.write(v)
        else:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")
def utc(ms):
    sec,rem=divmod(ms,1000);return (datetime.fromtimestamp(sec,timezone.utc)+timedelta(milliseconds=rem)).isoformat(timespec="milliseconds")
def canonical_sha(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def verify_references(expected,actual):
    if set(expected)!=set(actual) or any(expected[k]!=actual[k] for k in expected):raise ValueError("MANIFEST_REFERENCE_CHANGED")
def environment():
    if Path.cwd()!=ROOT or Path.cwd().resolve()!=ROOT or sys.executable!=old.PYTHON:raise ValueError("WORKDIR_PYTHON")
    versions={p:md.version(p) for p in ("qiskit","qiskit-machine-learning","numpy","scipy","scikit-learn")}
    if versions!={"qiskit":"2.6.1","qiskit-machine-learning":"0.9.1","numpy":"2.5.4","scipy":"1.18.1","scikit-learn":"1.9.1"}:raise ValueError("ENVIRONMENT_DRIFT")
    return {"python_executable":sys.executable,"python":sys.version,"versions":versions,"seed":42,"git_commit":"NOT_AVAILABLE; source SHA sealed","packages_changed":False}
def split_protocol():
    return {"phase":"4B-0","data_path":str(TRAIN),"Dataset_Train_rows_expected":150912,"Dataset_Train_sha256":"8628e45fe52bc1f0ef3cda20a9c31f9c72d8e4f01d1cd4f80103d624a455fd1d",
      "horizon_ms":1000,"feature_view":"aggregate_core_v1","feature_order":list(FEATURES),"label_policy":"direction_3class_exact_v1",
      "method":"SESSION_BOUNDED_ROLLING_MIDPOINT","fold_count":3,"Train_size":96,"Validation_size":384,
      "session_order":"frozen Train region start, end_exclusive, source_id, session_id; exactly3 observed research sessions required",
      "bounds_source":"Dataset frozen_split_policy.assignments.Train (complete source/session metadata), verified against registry",
      "boundary":"floor((source_start + source_end_exclusive)/2) milliseconds; half-open Train[start,b), Validation[b,end)",
      "quality":"retain Phase2E valid feature/label and1000ms match_error<=1; additionally require same-source/session endpoint witness with matching future_mid_price in permitted Train only",
      "witness_limit":"Missing witnesses are not declared invalid labels. Excluded from this conservative candidate pool; no re-matching, filling or edits.",
      "duplicate_policy":"global provided update_id and (event_time,current-state fingerprint) union groups across source aliases; same group never crosses Train/Validation. Conflicting identity or overlapping source intervals BLOCK this fixed design.",
      "sampling":"deterministic rank positions floor(i*(N-1)/(k-1)), inclusive endpoints; metadata sort(event_time_ms,source_id,session_id,record_index,sample_id), no shuffle/label consultation",
      "embargo_ms":0,"feature_lookback_ms":0,"purge":"group maximum actual label endpoint + embargo < Validation boundary; equality purged. Use actual target, never nominal1000 alone.",
      "Val_end":"group maximum actual endpoint < source end_exclusive; no cross-source/session matching",
      "timing_gate":"backwards/duplicate ambiguous clock/update contradictions or observed filtered-Train gap>1001ms ->BLOCKED pending policy review; not a new raw-market gap invalidation threshold",
      "legacy_gap_threshold_ms":None,"class_diagnosis":"only after six fold ID manifests plus top candidate manifest and SHA freeze",
      "missing_Train_class":"preserve IDs, mark3-class SVMs inapplicable and phase BLOCKED; never resample",
      "missing_Validation_class":"preserve IDs, warning and explicit undefined-class metric policy; no resampling",
      "infeasible":"BLOCKED with alternative suggestions only; never change3fold/96/384 or sample rule automatically",
      "historical_provenance":"research aliases are not independent capture IDs; offline recorded-data guarantees only, no latency/authenticity claims",
      "formal_fit":False,"formal_predict":False,"formal_Quantum_kernel":False,"formal_preprocessing_fit":False,"Test_values_used":False,"Holdout_content_opened":False}
