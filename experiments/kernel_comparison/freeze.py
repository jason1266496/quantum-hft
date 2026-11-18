"""Exclusive Phase 3B outputs and an immutable membership/scaler freeze."""
import csv,hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
from data_pipeline.datasets.checksums import fingerprint,sha_file
ROOT=Path("/home/jason/quantum-hft")
OLD=ROOT/"artifacts/phase3a/20261026T212918Z"
DATASET=ROOT/"artifacts/datasets/btcusdt_aggregate_v1_20261026T202040Z"
FEATURES=("obi_5","spread_bps","bid_volume_5","ask_volume_5")
NAMES=("DOWN","FLAT","UP")
HORIZONS=(1000,100)
FIELDS=("sample_id","source_id","session_id","record_index","event_time_ms","requested_horizon_ms",*FEATURES,"future_return_bps","class_label")
def utc():return datetime.now(timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def safe(p):
    p=Path(p)
    if not p.is_absolute():p=ROOT/p
    if ".." in p.parts or any(q.is_symlink() for q in (p,*p.parents)):raise ValueError("UNSAFE_OUTPUT")
    if not (p.is_relative_to(ROOT/"artifacts/phase3b") or p.is_relative_to(ROOT/"tests/fixtures/phase3b") or
            (p.parent==ROOT/"docs" and re.fullmatch(r"PHASE3B_REPORT_[0-9]{8}T[0-9]{6}Z.md",p.name))):
        raise ValueError("OUTPUT_OUTSIDE_PHASE3B")
    return p
def write(p,value):
    p=safe(p)
    with p.open("x",encoding="utf-8") as f:json.dump(value,f,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False);f.write("\n")
    return sha_file(p)
def csv_write(p,fields,rows):
    p=safe(p)
    with p.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
    return sha_file(p)
def run_path(run_id):
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z",run_id):raise ValueError("INVALID_RUN_ID")
    datetime.strptime(run_id,"%Y%m%dT%H%M%SZ")
    return safe(ROOT/"artifacts/phase3b"/run_id)
def protocol():
    return {"version":"kernel_comparison_subset_v2","horizons":{"1000":"PRIMARY","100":"SECONDARY_DIAGNOSTIC"},
        "feature_view":"aggregate_core_v1","feature_policy":"aggregate_compact_v1","feature_order":list(FEATURES),
        "label_policy":"direction_3class_exact_v1","train_class_cap":1000,"validation_cap":1000,"test_cap":1000,
        "primary_train":"min(1000, available class rows) independently for each class; no replacement",
        "secondary_train":"equal per class min(available DOWN,FLAT,UP,1000)",
        "small_minority_warning":"100ms per-class selected count <1000; cap shortfall warning, no synthetic rows",
        "temporal_method":"stable event_time sort; floor(i*(N-1)/(k-1)) rank positions, endpoints included",
        "temporal_interpretation":"uniform chronological ranks preserve observed density approximately; not uniform wall-clock resampling or exact class proportions",
        "validation_test_label_used_for_sampling":False,"test_used_for_policy":False,"holdout_used":False,
        "C_grid":[0.1,1.0,10.0,100.0],"gamma_grid":["scale","auto",0.01,0.1,1.0],
        "selection":"Validation macro_f1 desc, balanced_accuracy desc, C asc, gamma=scale first; remaining gamma ties fixed grid order",
        "class_weight":"balanced","probability":False,"random_state":42,"scaler_fit":"subset v2 Train only per horizon",
        "selected_single_class":"warn; no Test model evaluation if selected Validation predicts fewer than two classes",
        "primary_all_candidates_single_class":"FAIL","secondary_failure_does_not_veto_primary":True,
        "phase4_recommendation":"primary Validation predicts 3 classes, each recall >0, balanced accuracy >1/3; integrity, freeze, seal PASS; Test instability disclosed, never used to retune",
        "phase4_recommendation_is_not_extra_phase3b_pass_threshold":True,"no_minimum_test_performance_threshold":True,
        "quantum_budget_subset_created":False,"timing_scope":"PYTHON_BATCH_INFERENCE_ONLY"}
def freeze(run,manifests):
    out=run/"freeze/kernel_comparison_subset_v2_manifest.json"
    files={}
    for h in HORIZONS:
        base=run/(str(h)+"ms")
        for p in sorted((base/"subset").glob("*")):
            if p.is_file():files[str(p.relative_to(run))]=fingerprint(p)
        for p in (base/"scaler/scaler.json",base/"selection/selection_manifest.json"):
            files[str(p.relative_to(run))]=fingerprint(p)
    for name in ("policy/research_protocol.json","policy/feature_policy.json","policy/classification_policy.json",
                 "selection_barrier.json"):
        p=run/name;files[name]=fingerprint(p)
    document={"status":"FROZEN","version":"kernel_comparison_subset_v2","frozen_at_utc":utc(),
        "source_dataset_id":DATASET.name,"feature_view":"aggregate_core_v1","feature_order":list(FEATURES),
        "feature_policy":"aggregate_compact_v1","classification_policy":"direction_3class_exact_v1",
        "scaler_policy":"each horizon subset v2 Train-only; future Quantum comparison must use identical scaler parameters",
        "horizons":manifests,"files":files,"phase4_membership_change_allowed":False,
        "quantum_budget_subset":"NOT_CREATED; separately approved Phase 4 task only","final_holdout":"FINAL_HOLDOUT_NOT_EVALUATED"}
    write(out,document)
    targets={**{name:v["sha256"] for name,v in files.items()},str(out.relative_to(run)):sha_file(out)}
    with safe(run/"freeze/FROZEN.sha256").open("x",encoding="utf-8") as f:
        f.writelines(v+"  "+k+"\n" for k,v in sorted(targets.items()))
    verify_freeze(run)
    return document
def verify_freeze(run):
    lines=(run/"freeze/FROZEN.sha256").read_text().splitlines();seen=set()
    for line in lines:
        digest,name=line.split("  ",1);p=Path(name)
        if p.is_absolute() or ".." in p.parts or name in seen:raise ValueError("INVALID_FREEZE_PATH")
        seen.add(name)
        if sha_file(run/name)!=digest:raise ValueError("FROZEN_INPUT_CHANGED")
    m=read(run/"freeze/kernel_comparison_subset_v2_manifest.json")
    if m["status"]!="FROZEN" or m["phase4_membership_change_allowed"]:raise ValueError("NOT_FROZEN")
    return {"status":"PASS","files":len(lines),"manifest_sha256":sha_file(run/"freeze/kernel_comparison_subset_v2_manifest.json")}
