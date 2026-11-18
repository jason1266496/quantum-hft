"""Exact Decimal sign classes, without epsilon, cost or fitted thresholds."""
from decimal import Decimal
import numpy as np
CLASS_NAMES=("DOWN","FLAT","UP")
def classify(value):
    if type(value) is float:raise ValueError("FLOAT_LABEL_SOURCE_PROHIBITED")
    number=Decimal(value)
    if not number.is_finite():raise ValueError("NONFINITE_CONTINUOUS_LABEL")
    return 2 if number>0 else (0 if number<0 else 1)
def labels(rows):return np.asarray([classify(row["future_return_bps"]) for row in rows],dtype=np.int64)
def policy():
    return {"policy_id":"direction_3class_exact_v1","source_label":"future_return_bps",
            "down_condition":"return < 0","flat_condition":"return == 0","up_condition":"return > 0",
            "mapping":{"DOWN":0,"FLAT":1,"UP":2},"decimal_exact_zero":True,
            "train_selected":False,"validation_selected":False,"test_selected":False,"holdout_selected":False,
            "transaction_cost_aware":False,
            "purpose":"classification research baseline, not a final trading entry threshold"}
def distribution(values,*,require_all=False):
    y=np.asarray(values,dtype=np.int64)
    if not len(y) or not set(np.unique(y))<={0,1,2}:raise ValueError("INVALID_CLASSES")
    counts=np.bincount(y,minlength=3)
    if require_all and np.any(counts==0):raise ValueError("TRAIN_CLASS_MISSING")
    return {"total":len(y),"counts":{name:int(counts[i]) for i,name in enumerate(CLASS_NAMES)},
            "percentages":{name:float(counts[i]*100/len(y)) for i,name in enumerate(CLASS_NAMES)},
            "warnings":["EXTREME_CLASS_IMBALANCE_WARNING"] if require_all and np.any(counts/len(y)<.01) else []}
