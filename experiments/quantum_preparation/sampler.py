"""Fixed nested budgets; class-aware Train only and label-blind Validation."""
from models.classical.label_policy import classify
from .io import FIELDS,FEATURES,NAMES
def positions(n,k):
    if k<1 or n<k:raise ValueError("REQUIRED_SIZE_UNAVAILABLE")
    return list(range(n)) if n==k else ([0] if k==1 else [i*(n-1)//(k-1) for i in range(k)])
def validate_rows(rows):
    if not rows:raise ValueError("EMPTY_SOURCE")
    if len({r["sample_id"] for r in rows})!=len(rows):raise ValueError("DUPLICATE_SAMPLE_ID")
    if any(set(r)!=set(FIELDS) or int(r["requested_horizon_ms"])!=1000 for r in rows):raise ValueError("WRONG_SCHEMA_OR_HORIZON")
    if [int(r["event_time_ms"]) for r in rows]!=sorted(int(r["event_time_ms"]) for r in rows):raise ValueError("UNSORTED_SOURCE")
    for r in rows:
        if int(r["class_label"])!=classify(r["future_return_bps"]):raise ValueError("CLASSIFICATION_CHANGED")
        from math import isfinite
        if not all(isfinite(float(r[f])) for f in FEATURES):raise ValueError("NONFINITE_FEATURE")
    return True
def train_indices(rows,per_class,*,split="Train"):
    if split!="Train":raise ValueError("TRAIN_LABEL_SAMPLING_SCOPE")
    groups={c:[] for c in (0,1,2)}
    for i,r in enumerate(rows):groups[classify(r["future_return_bps"])].append(i)
    chosen=[]
    for group in groups.values():
        group=sorted(group,key=lambda i:int(rows[i]["event_time_ms"]))
        chosen.extend(group[i] for i in positions(len(group),per_class))
    return sorted(chosen,key=lambda i:(int(rows[i]["event_time_ms"]),i))
def validation_indices(metadata,count,*,split="Validation"):
    if split!="Validation":raise ValueError("VALIDATION_SAMPLING_SCOPE")
    order=sorted(range(len(metadata)),key=lambda i:int(metadata[i]["event_time_ms"]))
    return [order[i] for i in positions(len(order),count)]
def distribution(rows):
    count={name:sum(classify(r["future_return_bps"])==i for r in rows) for i,name in enumerate(NAMES)}
    return {"count":len(rows),"counts":count,"percentages":{c:n*100/len(rows) for c,n in count.items()}}
def build_budgets(train,validation):
    validate_rows(train);validate_rows(validation)
    if {r["sample_id"] for r in train}&{r["sample_id"] for r in validation}:raise ValueError("TRAIN_VALIDATION_OVERLAP")
    ti=train_indices(train,32);vi=validation_indices(validation,96)
    prototype={"Train":[dict(train[i]) for i in ti],"Validation":[dict(validation[i]) for i in vi],
               "parent_positions":{"Train":ti,"Validation":vi},"sampling_parent":"FROZEN_SUBSET_V2_1000MS"}
    sti=train_indices(prototype["Train"],8);svi=validation_indices(prototype["Validation"],24)
    smoke={"Train":[dict(prototype["Train"][i]) for i in sti],"Validation":[dict(prototype["Validation"][i]) for i in svi],
           "parent_positions":{"Train":[ti[i] for i in sti],"Validation":[vi[i] for i in svi]},
           "prototype_positions":{"Train":sti,"Validation":svi},"sampling_parent":"PROTOTYPE_BUDGET"}
    for label,budget,k in (("prototype",prototype,96),("smoke",smoke,24)):
        for split in ("Train","Validation"):
            rr=budget[split];validate_rows(rr)
            if len(rr)!=k:raise ValueError("BUDGET_SIZE_CHANGED")
        if set(distribution(budget["Train"])["counts"].values())!={k//3}:raise ValueError("BUDGET_TRAIN_NOT_BALANCED")
    return {"smoke":smoke,"prototype":prototype}
