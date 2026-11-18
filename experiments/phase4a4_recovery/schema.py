"""Required stage-output contract; no fitting, preprocessing or sampling."""
import re,hashlib
import numpy as np
NAMES=("DOWN","FLAT","UP")
def need(value,key,where):
    if not isinstance(value,dict) or key not in value:raise ValueError("MISSING_"+key.upper()+":"+where)
    return value[key]
def integer(x):return isinstance(x,(int,np.integer)) and not isinstance(x,(bool,np.bool_))
def labels(value):
    a=np.asarray(value)
    if a.ndim!=1 or not 1<=len(a)<=96 or a.dtype.kind not in "iu" or not np.isin(a,[0,1,2]).all():raise ValueError("INVALID_TRUE_LABELS")
    return np.ascontiguousarray(a,dtype=np.int64)
def validate_metrics(metric,y,pred,where):
    cm=need(metric,"confusion_matrix",where)
    if not isinstance(cm,(list,tuple,np.ndarray)) or len(cm)!=3 or any(not isinstance(row,(list,tuple,np.ndarray)) or len(row)!=3 for row in cm):raise ValueError("INVALID_CONFUSION_SHAPE:"+where)
    if any(not integer(v) or v<0 or v>len(y) for row in cm for v in row):raise ValueError("INVALID_CONFUSION_COUNTS:"+where)
    matrix=np.asarray(cm,dtype=np.int64)
    if need(metric,"class_order",where)!=list(NAMES):raise ValueError("INVALID_CLASS_ORDER:"+where)
    n=need(metric,"row_count",where)
    if not integer(n) or n!=len(y):raise ValueError("INVALID_ROW_COUNT:"+where)
    expected_support=np.bincount(y,minlength=3)
    if not np.array_equal(matrix.sum(axis=1),expected_support):raise ValueError("CONFUSION_ROW_SUPPORT_MISMATCH:"+where)
    expected=np.zeros((3,3),dtype=np.int64);np.add.at(expected,(y,pred),1)
    if not np.array_equal(matrix,expected):raise ValueError("CONFUSION_PREDICTION_MISMATCH:"+where)
    per=need(metric,"per_class",where);truth=need(metric,"true_class_distribution",where);predicted=need(metric,"predicted_class_distribution",where)
    for i,name in enumerate(NAMES):
        support=need(need(per,name,where),"support",where)
        if not integer(support) or support!=int(expected_support[i]):raise ValueError("PER_CLASS_SUPPORT_MISMATCH:"+where)
        if need(truth,name,where)!=int(expected_support[i]) or need(predicted,name,where)!=int(np.sum(pred==i)):raise ValueError("CLASS_DISTRIBUTION_MISMATCH:"+where)
    for key in ("macro_f1","balanced_accuracy","accuracy","macro_precision","macro_recall"):
        v=need(metric,key,where)
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not np.isfinite(v) or not 0<=v<=1:raise ValueError("INVALID_METRIC_VALUE:"+where)
    return matrix
def validate_stage(stage,true_labels):
    if true_labels is None:raise ValueError("MISSING_TRUE_LABELS")
    y=labels(true_labels)
    for key in ("inputs","preprocessing_sha256","kernels","models"):need(stage,key,"stage")
    v=need(stage["inputs"],"Validation","inputs")
    ids=need(v,"ids","Validation")
    if not isinstance(ids,list) or len(ids)!=len(y) or len(set(ids))!=len(y):raise ValueError("VALIDATION_ID_COUNT_OR_DUPLICATE")
    if need(v,"labels_sha256","Validation")!=hashlib.sha256(y.tobytes()).hexdigest():raise ValueError("TRUE_LABEL_SHA_MISMATCH")
    for name in ("rbf","qsvc"):
        m=need(stage["models"],name,"models")
        pred=np.asarray(need(m,"predictions",name))
        if pred.ndim!=1 or len(pred)!=len(y) or pred.dtype.kind not in "iu" or not np.isin(pred,[0,1,2]).all():raise ValueError("INVALID_STAGE_PREDICTIONS:"+name)
        digest=need(m,"prediction_sha256",name)
        if not isinstance(digest,str) or not re.fullmatch(r"[0-9a-f]{64}",digest):raise ValueError("INVALID_PREDICTION_SHA:"+name)
        need(m,"effective_class_weight",name)
        validate_metrics(need(m,"metrics",name),y,pred.astype(np.int64),name)
    return {"status":"PASS","rows":len(y),"class_order":list(NAMES),"true_support":np.bincount(y,minlength=3).tolist()}
