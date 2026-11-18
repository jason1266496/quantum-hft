"""Exclusive outputs, frozen-budget contracts and immutable input/environment checks."""
import csv,hashlib,json,os,re,stat,time
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import numpy as np
ROOT=Path("/home/jason/quantum-hft")
BUDGET=ROOT/"artifacts/phase4a0/20261029T222609Z"
ENV=ROOT/"artifacts/phase4a_env/20261029T225013Z"
PYTHON="/home/jason/.venvs/quantum-hft-qml/bin/python"
FEATURES=("obi_5","spread_bps","bid_volume_5","ask_volume_5")
FIELDS=("sample_id","source_id","session_id","record_index","event_time_ms","requested_horizon_ms",*FEATURES,"future_return_bps","class_label")
NAMES=("DOWN","FLAT","UP")
BUDGET_SHA="dc58043453c7a0ada067ddd189e27570b7039b47a54e32c897b5c841b7e975bc"
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def sha(p):
    p=Path(p)
    if p.suffix==".csv" and ("holdout" in p.name.lower() or any("holdout" in k.lower() for k in p.parts)):raise ValueError("HOLDOUT_CONTENT_PROHIBITED")
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()
def fp(p):return {"sha256":sha(p),"size_bytes":Path(p).stat().st_size}
def safe(p):
    p=Path(p)
    if not p.is_absolute():p=ROOT/p
    if ".." in p.parts or any(q.is_symlink() for q in (p,*p.parents)):raise ValueError("UNSAFE_OUTPUT")
    if not (p.is_relative_to(ROOT/"artifacts/phase4a1") or p.is_relative_to(ROOT/"tests/fixtures/phase4a1") or
        (p.parent==ROOT/"docs" and re.fullmatch(r"PHASE4A1_REPORT_[0-9]{8}T[0-9]{6}Z.md",p.name))):raise ValueError("OUTPUT_OUTSIDE_PHASE4A1")
    return p
def write(p,v):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8") as f:json.dump(v,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")
    return sha(p)
def write_csv(p,fields,rows):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
    return sha(p)
def save_array(p,a):
    p=safe(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("xb") as f:np.save(f,a,allow_pickle=False)
    return sha(p)
def run_path(run_id):
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z",run_id):raise ValueError("INVALID_RUN_ID")
    datetime.strptime(run_id,"%Y%m%dT%H%M%SZ")
    return safe(ROOT/"artifacts/phase4a1"/run_id)
def array_sha(a):return hashlib.sha256(np.ascontiguousarray(a,dtype=np.float64).tobytes()).hexdigest()
def class_of(value):
    d=Decimal(value)
    if not d.is_finite():raise ValueError("NONFINITE_LABEL")
    return 0 if d<0 else (2 if d>0 else 1)
def rows(p):
    with p.open(newline="",encoding="utf-8") as f:
        r=csv.DictReader(f);return r.fieldnames,list(r)
def verify_budget(root=BUDGET):
    root=Path(root)
    if root!=BUDGET and not root.is_relative_to(ROOT/"tests/fixtures/phase4a1"):raise ValueError("SOURCE_OUTSIDE_BUDGET")
    manifest=root/"quantum_budget_subset_v1_manifest.json"
    if root==BUDGET and sha(manifest)!=BUDGET_SHA:raise ValueError("BUDGET_MANIFEST_CHANGED")
    m=read(manifest)
    if m["status"]!="FROZEN" or m["horizon_ms"]!=1000 or m["feature_view"]!="aggregate_core_v1" or m["feature_order"]!=list(FEATURES) or m["classification_policy"]!="direction_3class_exact_v1":
        raise ValueError("BUDGET_CONTRACT_CHANGED")
    for line in (root/"FROZEN.sha256").read_text().splitlines():
        digest,name=line.split("  ",1);p=Path(name)
        if p.is_absolute() or ".." in p.parts:raise ValueError("UNSAFE_FREEZE_PATH")
        if sha(root/name)!=digest:raise ValueError("BUDGET_FROZEN_FILE_CHANGED")
    return m
def source_file(root,profile,split,kind):
    if profile not in ("smoke","prototype") or split not in ("Train","Validation"):raise ValueError("TEST_HOLDOUT_OR_PROFILE_PROHIBITED")
    names={"raw":split.lower()+".csv","angles":split.lower()+"_shared_angles.csv"}
    if kind not in names:raise ValueError("UNKNOWN_SOURCE_KIND")
    return Path(root)/profile/names[kind]
def load_profile(root,profile,m):
    if profile not in ("smoke","prototype"):raise ValueError("UNKNOWN_PROFILE")
    expected=24 if profile=="smoke" else 96;p=m["profiles"][profile]
    if p["Test_included"] or p["Holdout_included"] or p["same_input_for_RBF_QSVC"]["RBF"]!=p["same_input_for_RBF_QSVC"]["QSVC"]:
        raise ValueError("UNFAIR_OR_FORBIDDEN_MEMBERSHIP")
    out={"profile":profile,"source_manifest_sha256":sha(Path(root)/"quantum_budget_subset_v1_manifest.json")}
    seen=set()
    for split in ("Train","Validation"):
        info=p["splits"][split];rawpath=source_file(root,profile,split,"raw");anglepath=source_file(root,profile,split,"angles")
        if info["raw_path"]!=str(rawpath.relative_to(root)) or info["shared_input_path"]!=str(anglepath.relative_to(root)):raise ValueError("SOURCE_PATH_CHANGED")
        if sha(rawpath)!=info["raw_sha256"] or sha(anglepath)!=info["shared_input_sha256"]:raise ValueError("BUDGET_INPUT_CHANGED")
        fields,raw=rows(rawpath);af,angle=rows(anglepath)
        if fields!=list(FIELDS) or af!=["sample_id",*FEATURES] or len(raw)!=expected or len(angle)!=expected:raise ValueError("SHAPE_OR_FEATURE_ORDER_CHANGED")
        ids=[r["sample_id"] for r in raw]
        if len(set(ids))!=expected or ids!=[r["sample_id"] for r in angle] or ids!=info["sample_ids"] or set(ids)&seen:raise ValueError("ID_CHANGED_DUPLICATE_OR_OVERLAP")
        seen.update(ids)
        if any(int(r["requested_horizon_ms"])!=1000 or class_of(r["future_return_bps"])!=int(r["class_label"]) for r in raw):raise ValueError("LABEL_OR_HORIZON_CHANGED")
        ts=[int(r["event_time_ms"]) for r in raw]
        if ts!=sorted(ts):raise ValueError("MEMBERSHIP_NOT_TIME_SORTED")
        x=np.asarray([[float(r[f]) for f in FEATURES] for r in angle],dtype=np.float64)
        y=np.asarray([int(r["class_label"]) for r in raw],dtype=np.int64)
        if not np.isfinite(x).all() or x.shape!=(expected,4):raise ValueError("INVALID_ANGLES")
        count={name:int(np.sum(y==i)) for i,name in enumerate(NAMES)}
        if count!=info["class_distribution"]["counts"]:raise ValueError("CLASS_DISTRIBUTION_CHANGED")
        out[split]={"raw":raw,"x":x,"y":y,"ids":ids,"source":info,"file_sha256":sha(anglepath),"array_sha256":array_sha(x)}
    params_path=Path(root)/p["preprocessing_path"]
    if sha(params_path)!=p["preprocessing_sha256"]:raise ValueError("PREPROCESSING_PARAMS_CHANGED")
    out["params"]=read(params_path);return out
def snapshot(root,label):
    result={};paths=sorted(Path(root).rglob("*"));start=time.perf_counter()
    for i,p in enumerate(paths,1):
        st=p.lstat();v={"mode":stat.S_IMODE(st.st_mode)}
        if p.is_symlink():v.update({"kind":"symlink","target":os.readlink(p)})
        elif p.is_file():v.update({"kind":"file",**fp(p)})
        elif p.is_dir():v.update({"kind":"directory"})
        else:raise ValueError("UNSUPPORTED_ENV_ENTRY")
        result[str(p.relative_to(root))]=v
        if i%3000==0 or i==len(paths):
            t=time.perf_counter()-start
            print(json.dumps({"stage":label,"processed":i,"total":len(paths),"percent":100*i/len(paths),"elapsed_seconds":t,"eta_seconds":t/i*(len(paths)-i)}),flush=True)
    return result
def integrity(run):
    expected=read(run/"summary/protected_input_baseline.json");start=time.perf_counter()
    for i,(name,v) in enumerate(expected.items(),1):
        if fp(name)!=v:raise ValueError("PROTECTED_INPUT_CHANGED "+name)
        if i%500==0 or i==len(expected):
            t=time.perf_counter()-start;print(json.dumps({"stage":"PROTECTED_INTEGRITY","processed":i,"total":len(expected),"percent":100*i/len(expected),"elapsed_seconds":t,"eta_seconds":t/i*(len(expected)-i)}),flush=True)
    held=read(run/"summary/heldout_metadata_baseline.json")
    for name,v in held.items():
        s=Path(name).stat()
        if (s.st_size,s.st_mtime_ns,s.st_ino,s.st_dev)!=(v["size_bytes"],v["mtime_ns"],v["inode"],v["device"]):raise ValueError("HOLDOUT_METADATA_CHANGED")
    for prefix,label in (("quantum-hft-ml","ML"),("quantum-hft-qml","QML")):
        actual=snapshot(Path("/home/jason/.venvs")/prefix,label+"_ENV_INTEGRITY")
        if actual!=read(run/"summary"/(label.lower()+"_venv_baseline.json")):raise ValueError(label+"_ENV_CHANGED")
    manifest=verify_budget()
    datasets={}
    for folder in sorted((ROOT/"artifacts/datasets").iterdir()):
        if not folder.is_dir():continue
        recorded={}
        for line in (folder/"checksums.sha256").read_text().splitlines():
            digest,name=line.split("  ",1);path=str(folder/name)
            assert digest==(held[path]["prior_sealed_sha256"] if path in held else expected[path]["sha256"])
            recorded[name]=digest
        assert set(recorded)=={str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file() and p.name!="checksums.sha256"}
        assert read(folder/"final_holdout_manifest.json")["holdout_status"]=="LOCKED"
        datasets[folder.name]={"status":"PASS_WITH_SEALED_HOLDOUT_HASH_REUSE","tree_hash":read(folder/"dataset_manifest.json")["dataset_tree_hash"],
            "mode":"fresh non-Holdout SHA, prior Holdout SHA plus unchanged stat; no Holdout CSV content read"}
    return {"status":"PASS","protected_sha_files":len(expected),"heldout_metadata_files":len(held),"ML_env_unchanged":True,"QML_env_unchanged":True,
         "budget_manifest_sha256":sha(BUDGET/"quantum_budget_subset_v1_manifest.json"),"datasets":datasets,
         "Test_values_parsed":False,"Holdout_content_opened":False,"packages_changed":False}
