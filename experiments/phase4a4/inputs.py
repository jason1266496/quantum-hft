"""Read only previously frozen96/96 and reuse sealed kernel matrices."""
import numpy as np
from . import contracts as c
from .analysis import kernel_check
from experiments.phase4a1 import contracts as old
from experiments.phase4a1.preprocessing import transform
from experiments.phase4a2.analysis import rbf
from experiments.phase4a3.contracts import verify_freeze
MATRICES=("train_kernel.npy","validation_kernel.npy","rbf_train_kernel.npy","rbf_validation_kernel.npy")
def header(f):
    version=np.lib.format.read_magic(f)
    if version==(1,0):shape,fortran,dtype=np.lib.format.read_array_header_1_0(f)
    elif version==(2,0):shape,fortran,dtype=np.lib.format.read_array_header_2_0(f)
    else:raise ValueError("NPY_VERSION")
    if shape!=(96,96) or dtype!=np.dtype("float64"):raise ValueError("NPY_BUDGET_OR_DTYPE")
    return shape
def matrix(p):
    p=__import__("pathlib").Path(p)
    if p not in {c.P3/group/name for group in ("first","repeat") for name in MATRICES}:raise ValueError("MATRIX_SOURCE_PROHIBITED")
    c.VALUE_READS.append(str(p))
    expected=old.read(c.P3/"summary/completion_manifest.json")["artifact_files_excluding_this_manifest"][str(p.relative_to(c.P3))]
    if old.fp(p)!=expected:raise ValueError("SEALED_KERNEL_CHANGED")
    with p.open("rb") as f:header(f)
    return np.load(p,allow_pickle=False)
def load():
    mpath=c.P3/"natural_train_subset_manifest.json"
    if old.sha(mpath)!=c.protocol()["Natural_manifest_sha256"]:raise ValueError("NATURAL_MANIFEST_CHANGED")
    verify_freeze(c.P3);m=old.read(mpath)
    if m["horizon_ms"]!=1000 or m["classification_policy"]!="direction_3class_exact_v1" or m["feature_order"]!=list(c.FEATURES):raise ValueError("FROZEN_CONTRACT_CHANGED")
    pp=old.BUDGET/"prototype/input_preprocessing.json";params=old.read(pp);parent=old.read(c.P3/"fixed_preprocessing_validation.json")
    if old.sha(pp)!=m["frozen_preprocessing_sha256"] or params!=parent["parameters"]:raise ValueError("PREPROCESSING_CHANGED")
    out={"preprocessing_sha256":old.sha(pp),"params":params,"inputs":{},"clipping":{},"raw":{}}
    for split,rawpath,ap in (("Train",c.P3/"subset/natural_train.csv",c.P3/"subset/natural_train_angles.csv"),
       ("Validation",old.BUDGET/"prototype/validation.csv",old.BUDGET/"prototype/validation_shared_angles.csv")):
        fields,raw=c.rows(rawpath);af,angles=c.rows(ap)
        if fields!=list(old.FIELDS) or af!=["sample_id",*c.FEATURES]:raise ValueError("FEATURE_ORDER")
        ids=[r["sample_id"] for r in raw]
        if ids!=[r["sample_id"] for r in angles] or len(set(ids))!=96:raise ValueError("INPUT_ID_ORDER")
        y=np.array([int(r["class_label"]) for r in raw],dtype=np.int64)
        if any(old.class_of(r["future_return_bps"])!=int(r["class_label"]) or int(r["requested_horizon_ms"])!=1000 for r in raw):raise ValueError("LABEL_HORIZON_CHANGED")
        x=np.array([[float(r[f]) for f in c.FEATURES] for r in angles],dtype=np.float64)
        ident=c.identity(ids,x,y)
        if ident!=m[split+"_identity"]:raise ValueError("INPUT_SHA_OR_ID_CHANGED")
        theta,clip=transform(raw,params,split=split)
        if not np.allclose(theta,x,atol=1e-12,rtol=1e-11) or not np.isfinite(x).all():raise ValueError("FROZEN_ANGLE_INTERFACE_GAP")
        expectedclip=parent["Natural_Train_clip"] if split=="Train" else parent["original_A_formula_validation"]["splits"]["Validation"]["clip"]
        if clip!=expectedclip:raise ValueError("CLIPPING_CHANGED")
        out[split]={"x":x,"y":y,"ids":ids};out["inputs"][split]=ident;out["clipping"][split]=clip;out["raw"][split]=raw
    if set(out["Train"]["ids"])&set(out["Validation"]["ids"]):raise ValueError("TRAIN_VALIDATION_OVERLAP")
    if [int(np.sum(out["Train"]["y"]==i)) for i in (0,1,2)]!=[6,80,10] or [int(np.sum(out["Validation"]["y"]==i)) for i in (0,1,2)]!=[5,86,5]:raise ValueError("CLASS_COUNTS_CHANGED")
    arrays={name:matrix(c.P3/"first"/name) for name in MATRICES};evidence={}
    for name,a in arrays.items():
        rep=matrix(c.P3/"repeat"/name)
        if not np.allclose(a,rep,atol=1e-10,rtol=1e-9):raise ValueError("PARENT_KERNEL_REPEAT_MISMATCH")
        evidence[name]={"source":str(c.P3/"first"/name),"file":old.fp(c.P3/"first"/name),"array_sha256":old.array_sha(a),
          "parent_repeat_max_abs_diff":float(abs(a-rep).max()),"shape":list(a.shape)}
    rtrain=rbf(out["Train"]["x"],out["Train"]["x"]);rcross=rbf(out["Validation"]["x"],out["Train"]["x"])
    diffs={}
    for name,expected in (("rbf_train_kernel.npy",rtrain),("rbf_validation_kernel.npy",rcross)):
        if not np.allclose(arrays[name],expected,atol=1e-12,rtol=1e-12):raise ValueError("RBF_FORMULA_MISMATCH")
        diffs[name]=float(abs(arrays[name]-expected).max())
    out["kernel_checks"]={"quantum":kernel_check(arrays["train_kernel.npy"],arrays["validation_kernel.npy"]),
                         "rbf":kernel_check(arrays["rbf_train_kernel.npy"],arrays["rbf_validation_kernel.npy"])}
    out["kernels"]=evidence;out["arrays"]=arrays;out["RBF_formula_differences"]=diffs
    if old.read(c.P3/"first/circuit_manifest.json")!=old.read(c.P1/"prototype/first/circuit_manifest.json"):raise ValueError("CIRCUIT_DRIFT")
    out["balanced"]={}
    for name in ("rbf","qsvc"):
        fields,pred=c.rows(c.P3/"first"/(name+"_predictions.csv"))
        if fields!=["sample_id","true_class","predicted_class"] or [r["sample_id"] for r in pred]!=out["Validation"]["ids"] or [int(r["true_class"]) for r in pred]!=out["Validation"]["y"].tolist():raise ValueError("REFERENCE_PREDICTIONS_CHANGED")
        out["balanced"][name]={"predictions":np.array([int(r["predicted_class"]) for r in pred]),"metrics":old.read(c.P3/(name+"_metrics.json")),
                              "config":old.read(c.P3/"first"/(name+"_config.json"))}
    return out
