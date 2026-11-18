"""Pure class-weight controls, prediction changes and kernel checks."""
import numpy as np
from experiments.phase4a1.metrics import score,close_tree
NAMES=("DOWN","FLAT","UP")
def none_config(parent):
    if parent.get("class_weight")!="balanced":raise ValueError("REFERENCE_MUST_BE_BALANCED")
    out=dict(parent);out["class_weight"]=None
    return out
def only_weight_changed(parent,new):
    if set(parent)!=set(new) or parent.get("class_weight")!="balanced" or new.get("class_weight") is not None:return False
    return {k for k in parent if parent[k]!=new[k]}=={"class_weight"}
def kernel_check(train,cross):
    if train.shape!=(96,96) or cross.shape!=(96,96):raise ValueError("KERNEL_SHAPE")
    for k in (train,cross):
        if not np.isrealobj(k) or not np.isfinite(k).all() or k.min()<-1e-10 or k.max()>1+1e-10:raise ValueError("KERNEL_FINITE_OR_RANGE")
    sym=float(abs(train-train.T).max());diag=float(abs(np.diag(train)-1).max())
    if sym>1e-10 or diag>1e-10:raise ValueError("KERNEL_SYMMETRY_DIAGONAL")
    eig=np.linalg.eigvalsh(train)
    if eig.min()<-1e-10:raise ValueError("KERNEL_PSD")
    return {"status":"PASS","train_shape":[96,96],"cross_shape":[96,96],"finite_real":True,"symmetry_error":sym,"diagonal_error":diag,
      "min_eigenvalue":float(eig.min()),"max_eigenvalue":float(eig.max()),"PSD_tolerance":1e-10,"raw_matrix_modified":False,
      "cross_PSD_or_diagonal":"NOT_APPLICABLE"}
def majority(y):
    y=np.asarray(y,dtype=np.int64)
    return score(y,np.ones(len(y),dtype=np.int64))
def changes(ids,y,before,after):
    y=np.asarray(y);before=np.asarray(before);after=np.asarray(after)
    if len(set(ids))!=len(ids) or not (len(ids)==len(y)==len(before)==len(after)):raise ValueError("PREDICTION_ID_LENGTH")
    if not all(np.isin(a,[0,1,2]).all() for a in (y,before,after)):raise ValueError("PREDICTION_CLASS")
    transition=np.zeros((3,3),dtype=int);np.add.at(transition,(before,after),1)
    mask=before!=after
    return {"changed_count":int(mask.sum()),"unchanged_count":int((~mask).sum()),"old_to_new_prediction_matrix":transition.tolist(),
      "transition_orientation":"rows=balanced predictions, cols=None predictions",
      "per_true_class_changed":{n:int(np.sum(mask&(y==i))) for i,n in enumerate(NAMES)},
      "balanced_predicted_FLAT":int(np.sum(before==1)),"None_predicted_FLAT":int(np.sum(after==1)),
      "None_minus_balanced_FLAT_predictions":int(np.sum(after==1)-np.sum(before==1)),
      "changed_samples":[{"sample_id":ids[i],"true_class":NAMES[int(y[i])],"balanced_prediction":NAMES[int(before[i])],"None_prediction":NAMES[int(after[i])]} for i in np.flatnonzero(mask)]}
def compare_repeats(first,repeat):
    checks={"inputs":first["inputs"]==repeat["inputs"],"preprocessing_SHA":first["preprocessing_sha256"]==repeat["preprocessing_sha256"],
            "kernel_fingerprints":first["kernels"]==repeat["kernels"]}
    for n in ("rbf","qsvc"):
        a=first["models"][n];b=repeat["models"][n]
        checks[n+"_prediction_SHA"]=a["prediction_sha256"]==b["prediction_sha256"]
        checks[n+"_predictions"]=a["predictions"]==b["predictions"]
        checks[n+"_metrics"]=close_tree(a["metrics"],b["metrics"],atol=1e-12,rtol=1e-12)
        checks[n+"_confusion"]=a["metrics"]["confusion_matrix"]==b["metrics"]["confusion_matrix"]
        checks[n+"_weights"]=a["effective_class_weight"]==b["effective_class_weight"]
    return {"status":"PASS" if all(checks.values()) else "FAIL","checks":checks,"matrix_atol":1e-10,"matrix_rtol":1e-9,"metric_atol":1e-12,"metric_rtol":1e-12,
      "kernel_policy":"identical sealed files reloaded for both passes; SHA, raw arrays, parent repeat and formula checked","result_selection_from_repeat":False}
