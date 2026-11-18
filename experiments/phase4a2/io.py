"""Exclusive new outputs and strict saved-data interface."""
import csv,json,hashlib,re
from pathlib import Path
import numpy as np
from experiments.phase4a1 import contracts as old
ROOT=old.ROOT
PARENT=ROOT/"artifacts/phase4a1/20261029T232311Z"
FIRST=PARENT/"prototype/first"
BUDGET=old.BUDGET
ALLOWED_CSV={BUDGET/"prototype"/n for n in ("train.csv","validation.csv","train_shared_angles.csv","validation_shared_angles.csv")}|{FIRST/n for n in ("rbf_predictions.csv","qsvc_predictions.csv")}
VALUE_READS=[]
def write(p,v):
    p=Path(p)
    if not (p.is_relative_to(ROOT/"artifacts/phase4a2") or (p.parent==ROOT/"docs" and re.fullmatch(r"PHASE4A2_DIAGNOSTIC_REPORT_\d{8}T\d{6}Z.md",p.name))):raise ValueError("OUTPUT_SCOPE")
    if any(q.is_symlink() for q in (p,*p.parents)):raise ValueError("OUTPUT_SYMLINK")
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8") as f:
        if isinstance(v,str):f.write(v)
        else:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")
def rows(p):
    p=Path(p)
    if p not in ALLOWED_CSV:raise ValueError("CSV_VALUE_ACCESS_PROHIBITED")
    VALUE_READS.append(str(p))
    with p.open(newline="",encoding="utf-8") as f:
        d=csv.DictReader(f);fields=d.fieldnames;result=list(d)
    if len(result)!=96:raise ValueError("FROZEN_96_ROWS_REQUIRED")
    return fields,result
def read_npy_header(f):
    version=np.lib.format.read_magic(f)
    if version==(1,0):shape,fortran,dtype=np.lib.format.read_array_header_1_0(f)
    elif version==(2,0):shape,fortran,dtype=np.lib.format.read_array_header_2_0(f)
    else:raise ValueError("UNSUPPORTED_NPY_VERSION")
    if shape!=(96,96) or dtype!=np.dtype("float64"):raise ValueError("LARGE_OR_CHANGED_KERNEL_HEADER")
    return shape,fortran,dtype
def matrix(p):
    p=Path(p)
    if p not in (FIRST/"train_kernel.npy",FIRST/"validation_kernel.npy"):raise ValueError("QUANTUM_MATRIX_SOURCE_PROHIBITED")
    VALUE_READS.append(str(p))
    with p.open("rb") as f:
        read_npy_header(f)
    a=np.load(p,allow_pickle=False)
    if not np.isfinite(a).all():raise ValueError("NONFINITE_KERNEL")
    return a
def load():
    from .analysis import FEATURES,verify_identity,transform
    manifest=old.verify_budget();stage=old.read(FIRST/"stage_results.json")
    params=old.read(BUDGET/"prototype/input_preprocessing.json");out={"params":params,"stage":stage}
    if params!=old.read(FIRST/"preprocessing_manifest.json")["parameters"]:raise ValueError("PREPROCESSING_CHANGED")
    for split in ("Train","Validation"):
        info=manifest["profiles"]["prototype"]["splits"][split]
        path=BUDGET/"prototype"/(split.lower()+".csv");ap=BUDGET/"prototype"/(split.lower()+"_shared_angles.csv")
        if old.sha(path)!=info["raw_sha256"] or old.sha(ap)!=info["shared_input_sha256"]:raise ValueError("SOURCE_SHA")
        fields,raw=rows(path);af,angles=rows(ap)
        if fields!=list(old.FIELDS) or af!=["sample_id",*FEATURES]:raise ValueError("FEATURE_ORDER")
        ids=[r["sample_id"] for r in raw]
        if ids!=[r["sample_id"] for r in angles] or ids!=info["sample_ids"] or len(set(ids))!=96:raise ValueError("IDS")
        x=np.array([[float(r[f]) for f in FEATURES] for r in angles]);xr=np.array([[float(r[f]) for f in FEATURES] for r in raw])
        y=np.array([int(r["class_label"]) for r in raw],dtype=np.int64)
        if any(old.class_of(r["future_return_bps"])!=int(r["class_label"]) or int(r["requested_horizon_ms"])!=1000 for r in raw):raise ValueError("LABEL_POLICY")
        identity={"ids":ids,"file_sha256":old.sha(ap),"array_sha256":old.array_sha(x),"labels_sha256":hashlib.sha256(y.tobytes()).hexdigest()}
        verify_identity(stage["input_identity"][split],identity)
        expected,clip=transform(xr,params)
        if not np.allclose(x,expected,atol=1e-12,rtol=1e-11):raise ValueError("FROZEN_TRANSFORM")
        out[split]={"ids":ids,"x":x,"raw":xr,"y":y,"clip":clip,"identity":identity,"transform_max_error":float(abs(x-expected).max())}
    if set(out["Train"]["ids"])&set(out["Validation"]["ids"]):raise ValueError("SPLIT_ID_OVERLAP")
    for model in ("rbf","qsvc"):
        f,r=rows(FIRST/(model+"_predictions.csv"))
        if f!=["sample_id","true_class","predicted_class"] or [s["sample_id"] for s in r]!=out["Validation"]["ids"] or [int(s["true_class"]) for s in r]!=out["Validation"]["y"].tolist():raise ValueError("PREDICTION_ID_OR_LABEL")
        pred=np.array([int(s["predicted_class"]) for s in r],dtype=int)
        if pred.tolist()!=stage["models"][model]["predictions"]:raise ValueError("SEALED_PREDICTIONS_CHANGED")
        out[model]={"p":pred,"config":old.read(FIRST/(model+"_config.json")),"metrics":old.read(FIRST/(model+"_metrics.json"))}
    out["qtrain"]=matrix(FIRST/"train_kernel.npy");out["qcross"]=matrix(FIRST/"validation_kernel.npy")
    return out
