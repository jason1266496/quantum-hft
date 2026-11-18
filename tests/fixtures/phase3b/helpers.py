"""Synthetic fixtures only. Fresh per-test directories are retained as evidence."""
import json,tempfile
from pathlib import Path
from experiments.kernel_comparison.freeze import ROOT,FIELDS,FEATURES,write,csv_write,protocol,NAMES
def fresh():
    base=ROOT/"tests/fixtures/phase3b";base.mkdir(exist_ok=True,parents=True)
    return Path(tempfile.mkdtemp(prefix="case_",dir=base))
def rows(counts=(9,9,9),split="Train",h=1000):
    result=[];offset={"Train":0,"Validation":100000,"Test":200000}[split]
    for c,count in enumerate(counts):
        for i in range(count):
            index=len(result);obi=(-.8,0.,.8)[c]+i*.0001
            result.append(dict(zip(FIELDS,(f"{h}-{split}-{index}","fixture-source","fixture-"+split,str(index),
             str(offset+index*100),str(h),str(obi),str(1+c*.1),str(10+c*5+i*.01),str(20-c*5+i*.01),
             ("-0.0001","0","0.0001")[c],c))))
    return result
def run_tree(root=None):
    root=fresh() if root is None else root
    for name in ("logs","summary","policy","environment","freeze"):(root/name).mkdir(exist_ok=True)
    for h in (1000,100):
        for name in ("subset","scaler","rbf","selection","test"):(root/(str(h)+"ms")/name).mkdir(parents=True,exist_ok=True)
    return root
def fake_selections(root):
    paths={}
    for h in (1000,100):
        p=root/(str(h)+"ms")/"selection/selection_manifest.json"
        write(p,{"selection_split":"Validation","test_evaluated":False,"test_used_for_selection":False})
        paths[h]=p
    return paths
def dataset(root=None):
    root=fresh() if root is None else root;ds=root/"dataset";ds.mkdir()
    extra=("feature_view","valid_feature_row","valid_label")
    schema=[*FIELDS,*extra]
    write(ds/"dataset_schema.json",{"field_order":schema})
    for h in (1000,100):
        (ds/(str(h)+"ms")).mkdir()
        for split in ("Train","Validation","Test"):
            rr=rows((12,12,12) if split=="Train" else (6,6,6),split,h)
            full=[{**r,"feature_view":"aggregate_core_v1","valid_feature_row":"true","valid_label":"true"} for r in rr]
            csv_write(ds/(str(h)+"ms")/(split.lower()+".csv"),schema,full)
        with (ds/(str(h)+"ms")/"final_holdout.csv").open("x") as f:f.write("NEVER_PARSE_THIS_SENTINEL")
    return ds
def candidate(c=1.,g="scale",f1=.5,ba=.5,pred=3):
    return {"config":{"C":c,"gamma":g},"validation_metrics":{"macro_f1":f1,"balanced_accuracy":ba,"prediction_class_count":pred}}
