"""Synthetic only; fresh retained fixture directories under this phase."""
import tempfile
from pathlib import Path
from experiments.quantum_preparation.io import ROOT,FIELDS,FEATURES,write,write_csv
def fresh():
    base=ROOT/"tests/fixtures/phase4a0";base.mkdir(parents=True,exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="case_",dir=base))
def rows(counts=(100,100,100),split="Train"):
    out=[];offset=0 if split=="Train" else 1000000
    for c,count in enumerate(counts):
        for i in range(count):
            n=len(out)
            out.append(dict(zip(FIELDS,(split+"-"+str(n),"fixture-source","fixture-"+split,str(n),str(offset+n*100),"1000",
                str(-.8+c*.8+i*.0001),str(.1+c*.02+i*.00001),str(1+c+i*.01),str(5-c+i*.02),
                ("-0.0000000001","0","0.0000000001")[c],c))))
    return out
def base_scaler():
    return {"feature_order":list(FEATURES),"fit_split":"Train","fit_scope":"kernel_comparison_subset_v2",
       "horizon_ms":1000,"n_samples_seen":3000,"mean":[0.,0.,0.,0.],"scale":[1.,1.,1.,1.],"var":[1.,1.,1.,1.],
       "validation_fit":False,"test_fit":False,"holdout_transformed":False,"sklearn_version":"fixture",
       "fit_sample_ids_sha256":"synthetic-only"}
def run_tree():
    r=fresh()
    for name in ("smoke","prototype","policy","logs","summary"):(r/name).mkdir()
    return r
