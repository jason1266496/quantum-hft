"""Fixed all-class metrics and descriptive comparisons; no selection."""
import numpy as np
from experiments.phase4a1.metrics import score,close_tree
from experiments.phase4a4_recovery.schema import validate_metrics,need
from . import contracts as c
def labels(y):
    a=np.asarray(y)
    if a.ndim!=1 or len(a)<1 or a.dtype.kind not in "iu" or not np.isin(a,[0,1,2]).all():raise ValueError("INVALID_LABEL_VECTOR")
    return a.astype(np.int64)
def metric(y,pred):
    y=labels(y);p=labels(pred)
    if len(y)!=len(p):raise ValueError("PREDICTION_LENGTH")
    m=score(y,p);validate_metrics(m,y,p,"Phase4B1")
    for n in c.NAMES:
        if any(not np.isfinite(m["per_class"][n][k]) or not 0<=m["per_class"][n][k]<=1 for k in ("precision","recall","f1")):raise ValueError("INVALID_PER_CLASS_METRIC")
    return m
def summary(values):
    a=np.asarray(values,dtype=np.float64)
    if a.shape!=(3,) or not np.isfinite(a).all():raise ValueError("REQUIRES_THREE_FOLD_VALUES")
    return {"fold_values":a.tolist(),"mean":float(a.mean()),"median":float(np.median(a)),"standard_deviation_ddof1":float(a.std(ddof=1)),
       "worst_value":float(a.min()),"worst_fold":int(np.argmin(a))+1,"applicable_folds":3,"descriptive_only":True}
def aggregate(stages):
    out={}
    for name in c.MODELS:
        metrics=[s["models"][name]["metrics"] for s in stages]
        out[name]={k:summary([m[k] for m in metrics]) for k in ("macro_f1","balanced_accuracy","accuracy")}
        out[name]["single_class_prediction_folds"]=[i+1 for i,m in enumerate(metrics) if m["prediction_class_count"]==1]
        out[name]["Train_support"]=[s["Train_distribution"] for s in stages]
        out[name]["Validation_support"]=[s["Validation_distribution"] for s in stages]
    gaps={}
    for policy in ("None","Balanced"):
        rows=[]
        for s in stages:
            q=s["models"]["QSVC_"+policy]["metrics"];r=s["models"]["RBF_"+policy]["metrics"]
            rows.append({"fold":s["fold_id"],**{k:q[k]-r[k] for k in ("macro_f1","balanced_accuracy","accuracy")}})
        signs=np.sign([r["macro_f1"] for r in rows]).tolist()
        gaps[policy]={"QSVC_minus_RBF":rows,"MacroF1_gap_signs":signs,"strict_direction_consistent":all(s>0 for s in signs) or all(s<0 for s in signs),"all_ties":all(s==0 for s in signs)}
    return {"models":out,"paired_gaps":gaps,"inference":"DESCRIPTIVE_ONLY","IID_CI_computed":False,"statistical_significance_computed":False,
      "generalization":"NOT_ESTABLISHED","quantum_advantage":"NOT_ESTABLISHED","trading_profitability":"NOT_ESTABLISHED"}
def repeat_check(first,repeat):
    for stage in (first,repeat):
        for key in ("inputs","preprocessing_parameters","preprocessing_sha256","angle_array_shas","kernels","models"):need(stage,key,"repeat stage")
        for name in c.MODELS:
            record=need(stage["models"],name,"repeat models")
            for key in ("predictions","prediction_sha256","metrics","execution"):need(record,key,name)
            need(record["metrics"],"confusion_matrix",name)
    checks={"inputs":first["inputs"]==repeat["inputs"],"preprocessing_parameters":first["preprocessing_parameters"]==repeat["preprocessing_parameters"],
      "preprocessing_sha":first["preprocessing_sha256"]==repeat["preprocessing_sha256"],"angle_array_shas":first["angle_array_shas"]==repeat["angle_array_shas"],"kernels":first["kernels"]==repeat["kernels"]}
    per={}
    for name in c.MODELS:
        a=first["models"][name];b=repeat["models"][name]
        per[name]={"predictions":a["predictions"]==b["predictions"],"prediction_file_sha":a["prediction_sha256"]==b["prediction_sha256"],
          "metrics":a["metrics"]==b["metrics"],"confusion_matrix":a["metrics"]["confusion_matrix"]==b["metrics"]["confusion_matrix"],
          "actual_weights":a["execution"].get("actual_class_weights")==b["execution"].get("actual_class_weights")}
    ok=all(checks.values()) and all(all(v.values()) for v in per.values())
    return {"fold":first["fold_id"],"status":"PASS" if ok else "DETERMINISM_FAIL","checks":checks,"models":per,"repeat_kernel_reused":True}
