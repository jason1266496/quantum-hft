"""Class-aware Train only; label-blind chronological rank sampling elsewhere."""
from models.classical.label_policy import classify
from .freeze import FIELDS,HORIZONS
META=("sample_id","source_id","session_id","record_index","event_time_ms")
def temporal_positions(n,cap):
    if cap<1 or n<0:raise ValueError("INVALID_SIZE")
    k=min(n,cap)
    return list(range(n)) if n<=cap else ([0] if k==1 else [i*(n-1)//(k-1) for i in range(k)])
def temporal_indices(metadata,cap):
    order=sorted(range(len(metadata)),key=lambda i:int(metadata[i]["event_time_ms"]))
    return [order[i] for i in temporal_positions(len(order),cap)]
def sample_train(rows,horizon,*,split="Train"):
    if split!="Train" or horizon not in HORIZONS:raise ValueError("TRAIN_SAMPLING_SCOPE")
    classes={c:[] for c in (0,1,2)}
    for i,row in enumerate(rows):classes[classify(row["future_return_bps"])].append(i)
    if not all(classes.values()):raise ValueError("TRAIN_CLASS_MISSING")
    cap=1000 if horizon==1000 else min(1000,*(len(x) for x in classes.values()))
    chosen=[]
    for group in classes.values():
        positions=temporal_indices([rows[i] for i in group],cap)
        chosen.extend(group[i] for i in positions)
    chosen.sort(key=lambda i:(int(rows[i]["event_time_ms"]),i))
    return chosen,{"available_counts":{str(c):len(v) for c,v in classes.items()},
        "per_class_cap":cap,"labels_used":True,"label_source_split":"Train","duplicates_generated":False,
        "synthetic_rows":False,"warnings":["SMALL_MINORITY_CLASS_WARNING"] if horizon==100 and cap<1000 else []}
def sample_temporal(rows,*,split,cap=1000):
    if split not in ("Validation","Test"):raise ValueError("TEMPORAL_SAMPLING_SCOPE")
    metadata=[{k:row[k] for k in META} for row in rows]
    return temporal_indices(metadata,cap)
def project(row):
    return {k:(classify(row["future_return_bps"]) if k=="class_label" else row[k]) for k in FIELDS}
def subset(rows,indices):return [project(rows[i]) for i in indices]
