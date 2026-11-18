"""Artificial ML fixtures only; no production Dataset or Holdout values."""
import contextlib,csv,hashlib,json,tempfile
from pathlib import Path
import numpy as np
FIXTURES=Path(__file__).parent
FEATURES=("obi_5","spread_bps","bid_volume_5","ask_volume_5")
FIELDS=("sample_id","feature_view","source_id","session_id","record_index","event_time_ms",
        "requested_horizon_ms",*FEATURES,"future_return_bps","valid_feature_row","valid_label")
def artificial_rows(n=120,h=100,split="Train"):
    offsets={"Train":0,"Validation":100000,"Test":200000}
    rows=[]
    for i in range(n):
        cls=i%3;ret=("-0.01","0","0.01")[cls]
        identity={"feature_view":"aggregate_core_v1","source_id":"artificial_"+split.lower(),
                  "session_id":"synthetic_"+split.lower(),"record_index":i+1,"event_time_ms":offsets[split]+i*100}
        sid=hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(",",":")).encode()).hexdigest()
        rows.append({"sample_id":sid,**{k:str(v) for k,v in identity.items()},
                     "requested_horizon_ms":str(h),"obi_5":("-0.9","0","0.9")[cls],
                     "spread_bps":"0.1","bid_volume_5":str(cls+1),"ask_volume_5":str(3-cls),
                     "future_return_bps":ret,"valid_feature_row":"true","valid_label":"true"})
    return rows
def xy(n=120):
    rows=artificial_rows(n)
    x=np.asarray([[float(r[k]) for k in FEATURES] for r in rows])
    y=np.asarray([i%3 for i in range(n)])
    return x,y
def make_dataset(root):
    root.mkdir()
    (root/"dataset_schema.json").write_text(json.dumps({"field_order":list(FIELDS)}))
    (root/"dataset_manifest.json").write_text(json.dumps({"feature_view":"aggregate_core_v1"}))
    (root/"test").mkdir()
    (root/"test/manifest.json").write_text(json.dumps({"horizons":{str(h):{"rows":60} for h in (100,1000)}}))
    for h in (100,1000):
        folder=root/f"{h}ms";folder.mkdir()
        for split,n in (("Train",120),("Validation",60),("Test",60)):
            with (folder/(split.lower()+".csv")).open("x",newline="",encoding="utf-8") as f:
                w=csv.DictWriter(f,FIELDS,lineterminator="\n");w.writeheader();w.writerows(artificial_rows(n,h,split))
        (folder/"final_holdout.csv").write_text("FORBIDDEN_SENTINEL_NO_VALUES_MAY_BE_READ")
    return root
@contextlib.contextmanager
def fixture():
    with tempfile.TemporaryDirectory(dir=FIXTURES) as path:
        base=Path(path);yield base
def fake_selection(path):
    path.write_text(json.dumps({"test_evaluated":False,"test_used_for_selection":False,"selection_split":"Validation"}))
    return path
