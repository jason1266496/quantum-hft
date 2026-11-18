"""Scoped integrity and metadata checks; Holdout values are never parsed."""
import csv
from pathlib import Path
from data_pipeline.datasets.checksums import fingerprint,verify_checksums
from experiments.classical.runner import dependencies,scoped_validate
from models.classical.feature_policy import matrix
from models.classical.label_policy import classify
from .freeze import DATASET,FEATURES,FIELDS,HORIZONS,ROOT,read,utc
from .sampler import project
def verify_inputs(run):
    expected=read(run/"summary/input_integrity_before.json")
    for name,saved in expected.items():
        if fingerprint(name)!=saved:raise ValueError("PROTECTED_INPUT_CHANGED: "+name)
    return {"status":"PASS","file_count":len(expected),"hft_source_files":sum(Path(p).is_relative_to(Path("/home/jason/hft-realtime-codex")) for p in expected)}
def preflight(run):
    if Path.cwd()!=ROOT or ROOT.resolve()!=ROOT:raise ValueError("WRONG_WORKING_DIRECTORY")
    integrity=verify_inputs(run);deps=dependencies()
    scoped=scoped_validate()
    datasets={p.name:verify_checksums(p) for p in sorted((ROOT/"artifacts/datasets").iterdir()) if p.is_dir()}
    if scoped["holdout_values_parsed"]:raise ValueError("HOLDOUT_PROHIBITED")
    return {"status":"PASS","dependencies":deps,"datasets":datasets,"scoped_dataset_validation":scoped,"integrity":integrity}
def read_split(dataset,horizon,split,*,gate=None,journal=None,positions=None):
    if split not in ("Train","Validation","Test") or horizon not in HORIZONS:raise ValueError("HOLDOUT_OR_SCOPE_PROHIBITED")
    if split=="Test":
        if gate is None:raise ValueError("TEST_BEFORE_SEAL")
        gate.authorize_read(horizon)
    if positions is not None and (len(set(positions))!=len(positions) or any(i<0 for i in positions)):raise ValueError("INVALID_POSITIONS")
    wanted=None if positions is None else set(positions)
    selected=[];seen=set();last=-1;started=utc();count=0
    schema=read(dataset/"dataset_schema.json")["field_order"]
    with (dataset/(str(horizon)+"ms")/(split.lower()+".csv")).open(newline="",encoding="utf-8") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=schema:raise ValueError("DATASET_SCHEMA_CHANGED")
        for index,raw in enumerate(reader):
            count+=1
            if raw["feature_view"]!="aggregate_core_v1" or int(raw["requested_horizon_ms"])!=horizon:raise ValueError("WRONG_FORMAL_SCOPE")
            if raw["valid_feature_row"]!="true" or raw["valid_label"]!="true":raise ValueError("INVALID_FORMAL_ROW")
            event=int(raw["event_time_ms"])
            if event<last or raw["sample_id"] in seen:raise ValueError("UNSORTED_OR_DUPLICATE_INPUT")
            seen.add(raw["sample_id"]);last=event
            if wanted is None or index in wanted:selected.append(project(raw))
    if wanted is not None and len(selected)!=len(wanted):raise ValueError("POSITION_OUT_OF_RANGE")
    if journal is not None:journal.append({"scope":"DATASET_V1_FOR_SUBSET_V2","horizon_ms":horizon,"split":split,
        "started_at_utc":started,"finished_at_utc":utc(),"source_rows":count,"retained_rows":len(selected),
        "all_selections_sealed":bool(gate and gate.sealed),"values_parsed":True})
    return selected,count
def validate_rows(rows,horizon,split):
    if split not in ("Train","Validation","Test") or horizon not in HORIZONS:raise ValueError("SCOPE_PROHIBITED")
    if not rows:raise ValueError("EMPTY_SUBSET")
    if any(set(r)!=set(FIELDS) for r in rows):raise ValueError("SUBSET_SCHEMA")
    if len({r["sample_id"] for r in rows})!=len(rows):raise ValueError("DUPLICATE_SAMPLE_ID")
    times=[int(r["event_time_ms"]) for r in rows]
    if times!=sorted(times):raise ValueError("SUBSET_NOT_SORTED")
    for r in rows:
        if int(r["requested_horizon_ms"])!=horizon or int(r["class_label"])!=classify(r["future_return_bps"]):raise ValueError("LABEL_OR_HORIZON_CHANGED")
    matrix(rows)
    if split=="Train":
        counts=[sum(int(r["class_label"])==c for r in rows) for c in (0,1,2)]
        if not all(counts) or max(counts)>1000 or len(rows)>3000:raise ValueError("INVALID_TRAIN_CLASS_COVERAGE")
        if horizon==100 and len(set(counts))!=1:raise ValueError("SECONDARY_NOT_BALANCED")
    elif len(rows)>1000:raise ValueError("TEMPORAL_SUBSET_TOO_LARGE")
    return {"status":"PASS","rows":len(rows),"unique_ids":len(rows)}
def validate_membership(batches,horizon):
    seen=set();checks={}
    for split,rows in batches.items():
        checks[split]=validate_rows(rows,horizon,split)
        ids={r["sample_id"] for r in rows}
        if ids&seen:raise ValueError("SPLIT_OVERLAP")
        seen|=ids
    return {"status":"PASS","split_checks":checks,"split_overlap":0}
def assert_exact_subset(selected,source,indices):
    if selected!=[project(source[i]) for i in indices]:raise ValueError("SUBSET_ROW_CHANGED")
    return True
def ensure_new_files_allowed(run):
    before=read(run/"summary/input_integrity_before.json")
    new=[]
    for p in ROOT.rglob("*"):
        if not p.is_file() or ".git" in p.parts or "__pycache__" in p.parts or str(p) in before:continue
        allowed=(p.is_relative_to(run) or p.is_relative_to(ROOT/"experiments/kernel_comparison") or
          p.is_relative_to(ROOT/"tests/fixtures/phase3b") or p in
          [ROOT/"tools/build_kernel_comparison_subset.py",ROOT/"tools/run_rbf_kernel_baseline.py",
           ROOT/"docs"/("PHASE3B_REPORT_"+run.name+".md"),
           *(ROOT/"tests"/("test_"+n+".py") for n in ("kernel_class_diagnostics","kernel_sampler","kernel_subset_validator","rbf_kernel_baseline","kernel_subset_freeze","phase3b_test_seal"))])
        if not allowed:raise ValueError("UNAUTHORIZED_NEW_FILE: "+str(p))
        if p.is_symlink():raise ValueError("SYMLINK_PROHIBITED")
        new.append(str(p.relative_to(ROOT)))
    return new
