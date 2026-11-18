"""Synthetic Frozen-like budgets only; fresh fixture outputs retained."""
import hashlib,math,tempfile
from pathlib import Path
import numpy as np
from experiments.phase4a1.contracts import ROOT,FIELDS,FEATURES,NAMES,write,write_csv,sha
from experiments.phase4a1.preprocessing import transform
def fresh():
    p=ROOT/"tests/fixtures/phase4a1";p.mkdir(parents=True,exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="case_",dir=p))
def raw(counts,split):
    out=[];offset=0 if split=="Train" else 100000
    for c,n in enumerate(counts):
        for i in range(n):
            j=len(out)
            out.append(dict(zip(FIELDS,(split+"-"+str(j),"synthetic","synthetic-"+split,str(j),str(offset+j*100),"1000",
              str(.2+c*.6+i*.001),str(.1+c*.02+i*.0001),str(1+c+i*.01),str(4-c+i*.02),("-1e-30","0","1e-30")[c],c))))
    return out
def params(train,profile):
    x=np.array([[float(r[f]) for f in FEATURES] for r in train])
    low=x.min(axis=0);high=x.max(axis=0)
    return {"profile":profile,"feature_order":list(FEATURES),"angle_fit_split":"Train","angle_fit_rows":len(train),
       "angle_fit_sample_ids_sha256":hashlib.sha256(("\n".join(r["sample_id"] for r in train)+"\n").encode()).hexdigest(),
       "z_train_min":low.tolist(),"z_train_max":high.tolist(),"constant_features":(low==high).tolist(),
       "angle_range_radians":[0.,math.pi],"out_of_range":"clip","constant_feature_angle":math.pi/2,
       "validation_fit":False,"test_read_or_transform":False,"holdout_read_or_transform":False,
       "base_standardization":{"parameters":{"feature_order":list(FEATURES),"fit_split":"Train","fit_scope":"kernel_comparison_subset_v2",
          "n_samples_seen":3000,"horizon_ms":1000,"mean":[0.,0.,0.,0.],"scale":[1.,1.,1.,1.],"var":[1.,1.,1.,1.],
          "test_fit":False,"validation_fit":False,"holdout_transformed":False}}}
def budget():
    root=fresh();pt=raw((32,32,32),"Train");pv=raw((16,64,16),"Validation")
    ti=[c*32+i*31//7 for c in range(3) for i in range(8)];vi=[i*95//23 for i in range(24)]
    data={"prototype":{"Train":pt,"Validation":pv},"smoke":{"Train":[pt[i] for i in ti],"Validation":[pv[i] for i in vi]}}
    profiles={}
    for profile,b in data.items():
        folder=root/profile;folder.mkdir();p=params(b["Train"],profile);ph=write(folder/"input_preprocessing.json",p);splits={}
        for split,r in b.items():
            slug=split.lower();rh=write_csv(folder/(slug+".csv"),FIELDS,r);angles,clip=transform(r,p,split=split)
            ah=write_csv(folder/(slug+"_shared_angles.csv"),("sample_id",*FEATURES),
              [{"sample_id":v["sample_id"],**{f:format(float(angles[i,j]),".17g") for j,f in enumerate(FEATURES)}} for i,v in enumerate(r)])
            splits[split]={"raw_path":profile+"/"+slug+".csv","raw_sha256":rh,"shared_input_path":profile+"/"+slug+"_shared_angles.csv","shared_input_sha256":ah,
              "sample_ids":[v["sample_id"] for v in r],"class_distribution":{"counts":{name:sum(int(v["class_label"])==c for v in r) for c,name in enumerate(NAMES)}},
              "clip_counts_descriptive_only":clip}
        profiles[profile]={"splits":splits,"preprocessing_path":profile+"/input_preprocessing.json","preprocessing_sha256":ph,
            "same_input_for_RBF_QSVC":{"RBF":splits,"QSVC":splits},"Test_included":False,"Holdout_included":False}
    manifest={"status":"FROZEN","horizon_ms":1000,"feature_view":"aggregate_core_v1","feature_order":list(FEATURES),
              "classification_policy":"direction_3class_exact_v1","profiles":profiles}
    write(root/"quantum_budget_subset_v1_manifest.json",manifest)
    records={str(p.relative_to(root)):sha(p) for p in root.rglob("*") if p.is_file()}
    with (root/"FROZEN.sha256").open("x") as f:f.writelines(v+"  "+n+"\n" for n,v in sorted(records.items()))
    return root,manifest
