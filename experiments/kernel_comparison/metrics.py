"""All three classes, prediction distributions and descriptive feature shifts."""
import numpy as np
from models.classical.metrics import evaluate
from models.classical.label_policy import labels
from .freeze import FEATURES,NAMES
def prediction_distribution(pred):
    v=np.asarray(pred,dtype=int)
    if not len(v) or not set(v)<={0,1,2}:raise ValueError("INVALID_PREDICTIONS")
    counts={name:int(np.sum(v==i)) for i,name in enumerate(NAMES)}
    number=sum(c>0 for c in counts.values())
    return {"counts":counts,"percentages":{k:n*100/len(v) for k,n in counts.items()},
            "prediction_class_count":number,"warnings":["SINGLE_CLASS_PREDICTION_WARNING"] if number==1 else []}
def score(y,pred):
    m=evaluate(y,pred);m.update(prediction_distribution(pred))
    return m
def distribution(rows):
    y=labels(rows);counts={name:int(np.sum(y==i)) for i,name in enumerate(NAMES)}
    return {"total":len(y),"counts":counts,"percentages":{k:v*100/len(y) for k,v in counts.items()},
            "warnings":["EXTREME_CLASS_IMBALANCE_WARNING"] if any(v/len(y)<.01 for v in counts.values()) else []}
def numeric_stats(values):
    a=np.asarray(values,dtype=float)
    if not len(a):return {"status":"NOT_AVAILABLE","count":0}
    q=np.quantile(a,[.25,.5,.75])
    return {"count":len(a),"min":float(a.min()),"max":float(a.max()),"median":float(q[1]),
            "q25":float(q[0]),"q75":float(q[2]),"iqr":float(q[2]-q[0]),"finite":bool(np.isfinite(a).all())}
def feature_profile(rows):
    y=labels(rows)
    return {name:{"all":numeric_stats([r[name] for r in rows]),
         "per_class":{c:numeric_stats([r[name] for i,r in enumerate(rows) if y[i]==j]) for j,c in enumerate(NAMES)}} for name in FEATURES}
def shift(batches):
    return {"scope":"descriptive only; no sampling or parameter changes based on Test",
            "splits":{split:{"class_distribution":distribution(rows),"features":feature_profile(rows)} for split,rows in batches.items()},
            "test_used_for_policy":False,"holdout_used":False}
def matrix_size(n,validation,test):
    return {"train_N":n,"validation_N":validation,"test_N":test,"train_kernel_elements":n*n,
            "validation_vs_train_elements":validation*n,"test_vs_train_elements":test*n,
            "quantum_runtime":"NOT_ESTIMATED","quantum_budget_subset_created":False}

def prediction_distribution_from_confusion(cm):
    a=np.asarray(cm,dtype=int)
    if a.shape!=(3,3) or np.any(a<0) or a.sum()==0:raise ValueError("INVALID_SEALED_CONFUSION")
    return prediction_distribution(np.repeat(np.arange(3),a.sum(axis=0)))
