"""Three-class, all-sample metrics; no filtering or fitted thresholds."""
import math
import numpy as np
from models.classical.metrics import evaluate
from .contracts import NAMES
def distribution(y):
    y=np.asarray(y,dtype=int)
    if not len(y) or not set(y.tolist())<={0,1,2}:raise ValueError("INVALID_CLASSES")
    return {name:int(np.sum(y==i)) for i,name in enumerate(NAMES)}
def score(y,pred):
    m=evaluate(y,pred);counts=distribution(pred)
    m.update({"true_class_distribution":distribution(y),"predicted_class_distribution":counts,
              "prediction_class_count":sum(v>0 for v in counts.values()),
              "warnings":["CLASS_COVERAGE_WARNING"] if any(v==0 for v in counts.values()) else []})
    return m
def close_tree(a,b,*,atol=1e-12,rtol=1e-12):
    if isinstance(a,dict):return isinstance(b,dict) and set(a)==set(b) and all(close_tree(a[k],b[k],atol=atol,rtol=rtol) for k in a)
    if isinstance(a,(list,tuple)):return isinstance(b,(list,tuple)) and len(a)==len(b) and all(close_tree(x,y,atol=atol,rtol=rtol) for x,y in zip(a,b))
    if isinstance(a,float):return math.isfinite(a) and isinstance(b,(float,int)) and math.isclose(a,b,abs_tol=atol,rel_tol=rtol)
    return a==b
