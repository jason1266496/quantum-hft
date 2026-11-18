"""Exclusive Phase 4A-0 outputs and read-only integrity checks."""
import csv,json,re,time
from datetime import datetime
from pathlib import Path
from data_pipeline.datasets.checksums import fingerprint,sha_file,verify_checksums
from experiments.kernel_comparison.freeze import verify_freeze
ROOT=Path("/home/jason/quantum-hft")
PARENT=ROOT/"artifacts/phase3b/20261029T220053Z"
SOURCE=PARENT/"1000ms/subset"
FEATURES=("obi_5","spread_bps","bid_volume_5","ask_volume_5")
FIELDS=("sample_id","source_id","session_id","record_index","event_time_ms","requested_horizon_ms",*FEATURES,"future_return_bps","class_label")
NAMES=("DOWN","FLAT","UP")
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def safe(p):
    p=Path(p)
    if not p.is_absolute():p=ROOT/p
    if ".." in p.parts or any(q.is_symlink() for q in (p,*p.parents)):raise ValueError("UNSAFE_OUTPUT")
    if not (p.is_relative_to(ROOT/"artifacts/phase4a0") or p.is_relative_to(ROOT/"tests/fixtures/phase4a0") or
       (p.parent==ROOT/"docs" and (p.name=="PHASE4A0_EXPERIMENT_PROTOCOL.md" or re.fullmatch(r"PHASE4A0_REPORT_[0-9]{8}T[0-9]{6}Z.md",p.name)))):
        raise ValueError("OUTPUT_OUTSIDE_PHASE4A0")
    return p
def write(p,value):
    with safe(p).open("x",encoding="utf-8") as f:json.dump(value,f,sort_keys=True,ensure_ascii=False,indent=2,allow_nan=False);f.write("\n")
    return sha_file(p)
def write_csv(p,fields,rows):
    with safe(p).open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
    return sha_file(p)
def run_path(run_id):
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z",run_id):raise ValueError("INVALID_RUN_ID")
    datetime.strptime(run_id,"%Y%m%dT%H%M%SZ")
    return safe(ROOT/"artifacts/phase4a0"/run_id)
def verify_inputs(run,*,progress=False):
    baseline=read(run/"summary/input_integrity_before.json");start=time.perf_counter()
    for i,(name,v) in enumerate(baseline.items(),1):
        if fingerprint(name)!=v:raise ValueError("PROTECTED_INPUT_CHANGED: "+name)
        if progress and (i%500==0 or i==len(baseline)):
            elapsed=time.perf_counter()-start
            print(json.dumps({"stage":"INTEGRITY","processed":i,"total":len(baseline),"percent":100*i/len(baseline),
                  "elapsed_seconds":elapsed,"eta_seconds":elapsed/i*(len(baseline)-i)}),flush=True)
    frozen=verify_freeze(PARENT)
    if frozen["manifest_sha256"]!="a630a88a5942dadd77200ad7bf57b230410209957d2f9d00920bc168f9aa7865":raise ValueError("PARENT_FROZEN_CHANGED")
    datasets={}
    for p in sorted((ROOT/"artifacts/datasets").iterdir()):
        if p.is_dir():
            datasets[p.name]=verify_checksums(p)
            if read(p/"final_holdout_manifest.json")["holdout_status"]!="LOCKED":raise ValueError("HOLDOUT_UNLOCKED")
    return {"status":"PASS","protected_files":len(baseline),"hft_files":sum(p.startswith("/home/jason/hft-realtime-codex/") for p in baseline),
            "parent_frozen":frozen,"datasets":datasets,"test_holdout_value_access":False}
def load_source(source,split,expected_sha,*,journal=None):
    if split not in ("Train","Validation"):raise ValueError("TEST_HOLDOUT_VALUE_ACCESS_PROHIBITED")
    source=Path(source)
    if source!=SOURCE and not source.is_relative_to(ROOT/"tests/fixtures/phase4a0"):raise ValueError("SOURCE_OUTSIDE_FROZEN_OR_FIXTURE")
    p=source/(split.lower()+".csv")
    if sha_file(p)!=expected_sha:raise ValueError("FROZEN_SOURCE_HASH_MISMATCH")
    with p.open(newline="",encoding="utf-8") as f:
        r=csv.DictReader(f)
        if r.fieldnames!=list(FIELDS):raise ValueError("SOURCE_SCHEMA_CHANGED")
        rows=list(r)
    from .sampler import validate_rows
    validate_rows(rows)
    if journal is not None:journal.append({"source":str(p),"split":split,"rows":len(rows),"sha256":expected_sha,"purpose":"budget sampling and Train-only preparation"})
    return rows
def verify_budget_freeze(run):
    lines=(run/"FROZEN.sha256").read_text().splitlines();seen=set()
    for line in lines:
        digest,name=line.split("  ",1);p=Path(name)
        if p.is_absolute() or ".." in p.parts or name in seen:raise ValueError("INVALID_BUDGET_FREEZE_PATH")
        seen.add(name)
        if sha_file(run/name)!=digest:raise ValueError("BUDGET_FROZEN_FILE_CHANGED")
    if read(run/"quantum_budget_subset_v1_manifest.json")["status"]!="FROZEN":raise ValueError("BUDGET_NOT_FROZEN")
    return {"status":"PASS","files":len(lines),"manifest_sha256":sha_file(run/"quantum_budget_subset_v1_manifest.json")}
