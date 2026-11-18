"""Phase 2D only: build continuous raw-matched labels from approved Phase 2C views."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from data_pipeline.labels.builder import build_view
from data_pipeline.labels.schema import HORIZONS_MS, LABEL_FIELDS, schema_document
from data_pipeline.labels.validator import (PHASE2C_RUN, CSV_SOURCES, REPLAY_SOURCES,
                                            feature_path)
from data_pipeline.labels.writer import sha256_file, write_json

VIEWS = {**{s:("aggregate_core_v1",) for s in CSV_SOURCES},
         **{s:("aggregate_core_v1","depth_top5_v1") for s in REPLAY_SOURCES}}
REPEAT_SOURCES = ("obi_market_data_20260827_session1","replay_events_1000","replay_events_50000")
TEST_MODULES = ("tests.test_label_schema","tests.test_horizon_matcher",
                "tests.test_label_builder","tests.test_label_reference",
                "tests.test_label_validator","tests.test_label_writer",
                "tests.test_build_labels_tool")
HFT_ALLOWED = (Path("/home/jason/hft-realtime-codex/results"),)

def utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def regular_file(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError("INPUT_NOT_REGULAR: "+str(path))
    return path

def fingerprints(paths):
    return {str(p):{"sha256":sha256_file(regular_file(p)),"size_bytes":p.stat().st_size}
            for p in paths}

def approved_inputs():
    complete=json.loads(regular_file(ROOT/"artifacts/phase2c_cleanup/20261019T000857Z/completion_manifest.json").read_text())
    if complete.get("status")!="PASS" or complete.get("phase_status")!="PHASE 2C PASS":
        raise ValueError("PHASE2C_NOT_PASS")
    policy=json.loads(regular_file(ROOT/"configs/timestamp_policy.json").read_text())
    if tuple(policy["horizons_ms"])!=HORIZONS_MS or policy["max_match_error_ms"] is not None:
        raise ValueError("TIMESTAMP_POLICY_MISMATCH")
    config=json.loads(regular_file(ROOT/"configs/data_sources.json").read_text())
    sources=config["sources"]
    if len(sources)!=9:
        raise ValueError("NINE_SOURCE_CONTRACT_REQUIRED")
    hft_paths=[]
    for item in sources:
        path=Path(item["absolute_path"])
        if path.parent not in HFT_ALLOWED:
            raise ValueError("HFT_PATH_OUTSIDE_APPROVED_RESULTS")
        regular_file(path)
        hft_paths.append(path)
    feature_paths=[]
    for sid,views in VIEWS.items():
        manifest_path=ROOT/"artifacts/phase2c"/PHASE2C_RUN/"sources"/sid/"feature_manifest.json"
        manifest=json.loads(regular_file(manifest_path).read_text())
        if manifest.get("status")!="PASS":
            raise ValueError("FEATURE_MANIFEST_NOT_PASS: "+sid)
        for view in views:
            path=feature_path(ROOT,sid,view)
            expected=manifest["attempts"][0]["views"][view]
            if sha256_file(path)!=expected["sha256"] or path.stat().st_size!=expected["size_bytes"]:
                raise ValueError("PHASE2C_FEATURE_HASH_MISMATCH: "+str(path))
            feature_paths.append(path)
    actual_hft=fingerprints(hft_paths)
    for item in sources:
        actual=actual_hft[item["absolute_path"]]
        if actual["sha256"]!=item["sha256"] or actual["size_bytes"]!=item["size_bytes"]:
            raise ValueError("HFT_SOURCE_HASH_MISMATCH: "+item["relative_path"])
    return hft_paths,feature_paths

def compare_cross_view(left_dir,right_dir,source_id):
    from itertools import zip_longest
    samples=[]
    mismatch_count=0
    compared=0
    keys=("source_id","session_id","record_index","current_event_time_ms",
          "target_event_time_ms","actual_horizon_ms","match_error_ms",
          "future_mid_price","future_return_bps","valid_label","invalid_reason")
    for h in HORIZONS_MS:
        with (left_dir/f"labels_{h}ms.csv").open(newline="",encoding="utf-8") as a, \
             (right_dir/f"labels_{h}ms.csv").open(newline="",encoding="utf-8") as b:
            for x,y in zip_longest(csv.DictReader(a),csv.DictReader(b)):
                compared+=1
                if x is None or y is None:
                    mismatch_count+=1
                    if len(samples)<20:
                        samples.append({"horizon":h,"row":compared,"reason":"ROW_COUNT_MISMATCH"})
                    continue
                differences=[k for k in keys if x[k]!=y[k]]
                if differences:
                    mismatch_count+=1
                    if len(samples)<20:
                        samples.append({"horizon":h,"record_index":x["record_index"],"fields":differences})
    return {"source_id":source_id,"compared_label_pairs":compared,
            "mismatch_count":mismatch_count,"mismatches":samples,
            "status":"PASS" if not mismatch_count else "CROSS_VIEW_LABEL_MISMATCH"}

def compare_repeat(primary,repeat):
    from itertools import zip_longest
    checks={}
    for h in HORIZONS_MS:
        name=f"labels_{h}ms.csv"
        a,b=primary/name,repeat/name
        ah,bh=sha256_file(a),sha256_file(b)
        left_count=right_count=0
        targets_equal=True
        with a.open(newline="",encoding="utf-8") as left, \
             b.open(newline="",encoding="utf-8") as right:
            for x,y in zip_longest(csv.DictReader(left),csv.DictReader(right)):
                if x is not None: left_count+=1
                if y is not None: right_count+=1
                if x is None or y is None or x["target_event_time_ms"]!=y["target_event_time_ms"]:
                    targets_equal=False
        checks[name]={"primary_sha256":ah,"repeat_sha256":bh,
                      "primary_rows":left_count,"repeat_rows":right_count,
                      "target_event_time_equal":targets_equal,
                      "pass":ah==bh and targets_equal and left_count==right_count}
    qa=json.loads((primary/"label_quality.json").read_text())
    qb=json.loads((repeat/"label_quality.json").read_text())
    quality_equal=qa==qb
    return {"status":"PASS" if all(x["pass"] for x in checks.values()) and quality_equal
            else "NON_DETERMINISTIC_LABELS",
            "quality_summary_equal":quality_equal,"per_horizon":checks}

class _Tee:
    def __init__(self,terminal,file):
        self.terminal=terminal
        self.file=file
    def write(self,value):
        self.terminal.write(value)
        self.file.write(value)
        self.file.flush()
    def flush(self):
        self.terminal.flush()
        self.file.flush()

def _report(run_id,results,cross,determinism,integrity,tests,commands,status):
    lines=[
        "# Phase 2D：連續 Future Return Label 與 Horizon Match 品質",
        "",
        f"**{status}**。run_id：`{run_id}`。本報告只記錄本輪實際執行結果。",
        "",
        "## 1. Phase 2C 輸入與安全邊界",
        "",
        f"Phase 2C PASS 來源：`artifacts/phase2c/{PHASE2C_RUN}` 與 cleanup completion manifest。"
        "正式標籤只讀取該 run 的九個 Feature CSV；不重新讀 HFT 產生 Features。",
        "HFT 九來源與九個 Feature 檔案開始及完成 SHA-256/大小一致：" + str(integrity["status"]=="PASS") + "。",
        "未使用 local_timestamp_us；未建立 UP/DOWN/FLAT、binary class、Train/Validation/Test split、模型、回測或 Paper Trading。",
        "執行命令未連網、未交易、未使用 API key；這是本任務命令範圍記錄，並非全機流量量測。",
        "",
        "## 2. Schema、時間與算式",
        "",
        "四個 horizon：100、200、500、1000ms；每個 horizon 各有獨立 CSV。"
        "唯一排序/配對時間為 event_time_ms；每個 source_id/session_id/view 獨立處理。",
        "target = 同 Session 第一筆 event_time_ms >= current_event_time_ms + H；"
        "actual_horizon_ms = target_time - current_time；match_error_ms = actual - H。",
        "future_return_bps = (future_mid_price / current_mid_price - 1) * 10000；"
        "僅使用 Decimal，precision 50、ROUND_HALF_EVEN。"
        "找不到 target 時 invalid_reason=SESSION_TAIL_INSUFFICIENT，無效價格或 feature 另列原因。",
        "match error 大小不會在本階段刪除 RAW_MATCHED；max_match_error_ms 與 gap_threshold_ms 仍為 null。",
        "相同 timestamp 保留原記錄順序；event time 倒退將單調區段切開，禁止跨區段配對並標為無效。",
        "",
        "## 3. 單元測試",
        "",
        f"新測試命令 exit code={tests['exit_code']}；"
        f"stdout/stderr 保存在 `artifacts/phase2d/{run_id}/logs/`。",
        "",
        "## 4. 各來源與 View 的品質",
        "",
        "| source | view | input rows | 100ms valid/invalid | 200ms | 500ms | 1000ms | Reference mismatch |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key,data in results.items():
        q=data["quality"]
        pairs=[f"{q['horizons'][str(h)]['valid_labels']}/{q['horizons'][str(h)]['invalid_labels']}" for h in HORIZONS_MS]
        lines.append("| "+key.replace("/"," | ")+" | "+str(q["input_rows"])+" | "+" | ".join(pairs)+" | "+str(data["reference"]["mismatch_count"])+" |")
    lines+=["","五個 CSV 皆為 aggregate_core_v1；Replay 1000/50000 同時包含 aggregate_core_v1 與 depth_top5_v1。"
             "兩個 View 的同事件列不是獨立市場樣本。","",
             "## 5. Match error、Actual horizon、Gap 與零報酬","",
             "| source/view | H | match p50/p95/p99 (ms) | max actual (ms) | tail | zero return / valid |",
             "| --- | ---: | --- | ---: | ---: | ---: |"]
    for key,data in results.items():
        q=data["quality"]
        for h in HORIZONS_MS:
            z=q["horizons"][str(h)]
            me=z["match_error_distribution_ms"];ah=z["actual_horizon_distribution_ms"]
            lines.append(f"| {key} | {h} | {me['p50']}/{me['p95']}/{me['p99']} | {ah['max']} | {z['session_tail_count']} | {z['zero_return_count']}/{z['valid_labels']} |")
    lines+=["","各 source/session 的 event interval negative、zero、>100/200/500/1000ms、max、p50/p95/p99"
             "及 >100ms 區段完整保存在各 view 的 label_quality.json。"
             "檔案間時間差沒有用於 gap 統計。"
             "0-return 保留於有效樣本與 return 分布；無效標籤保留在 invalid_labels.csv。",
             "",
             "## 6. Reference、跨 View 與確定性","",
             "Reference 使用獨立線性 forward search，主要 matcher 使用 bisect。"
             "Replay1000 全筆四 horizon；Replay50000 前1000、每1000 checkpoint、末1000；"
             "CSV 各檔頭/中/尾各最多500筆。",
             f"Reference mismatch 總數：{sum(d['reference']['mismatch_count'] for d in results.values())}。",
             f"Aggregate/Depth mismatch 總數：{sum(x['mismatch_count'] for x in cross.values())}。",
             "Replay1000、Replay50000 與 CSV Session1 第二輪完整執行；"
             "每 horizon 比較 row count、target_event_time、輸出 SHA，並比對完整 quality JSON。",
             "確定性狀態：" + ("PASS" if all(x["status"]=="PASS" for x in determinism.values()) else "NON_DETERMINISTIC_LABELS") + "。",
             "",
             "## 7. Invalid 原因與候選閾值","",
             "SESSION_TAIL_INSUFFICIENT、INVALID_CURRENT_PRICE、INVALID_FUTURE_PRICE、"
             "INVALID_CURRENT_FEATURE_ROW、INVALID_FUTURE_FEATURE_ROW、EVENT_TIME_BACKWARDS"
             "逐 horizon 計數；各 label_quality.json 另存 return p1/p5/p25/p50/p75/p95/p99。",
             "本階段只輸出原始分布，不從全資料決定最終 match-error 或 gap 閾值。"
             "Phase 2E 可在 Training-side profile 上比較 p95/p99 等候選，人工審核後凍結；"
             "Final Holdout 不得參與選值。",
             "",
             "## 8. 命令、完整性及下一階段","",
             "實際正式命令與子測試命令、exit code、stdout/stderr 路徑保存在 logs/execution.json。"
             "前置 workdir 驗證命令為 pwd、realpath .、findmnt -T .；"
             "正式處理只讀 Phase 2C Feature 與 HFT 雜湊。",
             "九個 HFT source 與九個 Feature input 的前後 SHA/size 比對見 summary/input_integrity_before.json"
             "及 summary/input_integrity_after.json。"
             "沒有虛構任何測試、標籤、模型、網路或交易結果。",
             "Phase 2E 僅建議在人工審核本報告並明確批准後開始；本次不切 split、不訓練。",
             ""]
    return "\n".join(lines)

def execute(run_id):
    if Path.cwd()!=ROOT or ROOT.resolve()!=Path("/home/jason/quantum-hft"):
        raise ValueError("WRONG_WORKING_DIRECTORY")
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z",run_id):
        raise ValueError("INVALID_RUN_ID")
    datetime.strptime(run_id,"%Y%m%dT%H%M%SZ")
    run_parent=ROOT/"artifacts/phase2d"
    if run_parent.is_symlink():
        raise ValueError("SYMLINK_OUTPUT_PARENT")
    run_parent.mkdir(exist_ok=True)
    run=run_parent/run_id
    run.mkdir(exist_ok=False)
    for name in ("schemas","sources","quality","match_error","reference","determinism","logs","summary"):
        (run/name).mkdir(exist_ok=False)
    begun=utc()
    command=[sys.executable,"-B",str(Path(__file__).relative_to(ROOT)),"--run-id",run_id]
    commands=[{"command":command,"cwd":str(ROOT),"started_at_utc":begun,
               "stdout_path":"logs/stdout.txt","stderr_path":"logs/stderr.txt"}]
    original_stdout,original_stderr=sys.stdout,sys.stderr
    stdout_log=(run/"logs/stdout.txt").open("x",encoding="utf-8")
    stderr_log=(run/"logs/stderr.txt").open("x",encoding="utf-8")
    sys.stdout,sys.stderr=_Tee(original_stdout,stdout_log),_Tee(original_stderr,stderr_log)
    try:
        hft_paths,feature_paths=approved_inputs()
        before={"hft":fingerprints(hft_paths),"phase2c_features":fingerprints(feature_paths)}
        write_json(run/"summary/input_integrity_before.json",before)
        write_json(run/"schemas/label.schema.json",schema_document())
        test_command=[sys.executable,"-B","-m","unittest",*TEST_MODULES]
        test_start=utc()
        check=subprocess.run(test_command,cwd=ROOT,encoding="utf-8",capture_output=True,check=False)
        (run/"logs/tests.stdout.txt").open("x",encoding="utf-8").write(check.stdout)
        (run/"logs/tests.stderr.txt").open("x",encoding="utf-8").write(check.stderr)
        tests={"command":test_command,"started_at_utc":test_start,
               "finished_at_utc":utc(),"exit_code":check.returncode,
               "stdout_path":"logs/tests.stdout.txt","stderr_path":"logs/tests.stderr.txt"}
        commands.append(tests)
        write_json(run/"summary/test_results.json",tests)
        if check.returncode:
            raise ValueError("PHASE2D_UNIT_TESTS_FAILED")
        results={}
        cross={}
        for sid,views in VIEWS.items():
            (run/"sources"/sid).mkdir(exist_ok=False)
            for view in views:
                folder=run/"sources"/sid/view
                quality,reference=build_view(ROOT,sid,view,folder)
                results[sid+"/"+view]={"quality":quality,"reference":reference}
                if reference["status"]!="PASS" or quality["status"]!="PASS":
                    raise ValueError("LABEL_REFERENCE_MISMATCH: "+sid+"/"+view)
            if len(views)==2:
                comparison=compare_cross_view(run/"sources"/sid/views[0],
                                              run/"sources"/sid/views[1],sid)
                cross[sid]=comparison
                write_json(run/"quality"/(sid+"_cross_view.json"),comparison)
                if comparison["status"]!="PASS":
                    raise ValueError("CROSS_VIEW_LABEL_MISMATCH")
        determinism={}
        (run/"determinism/repeat").mkdir(exist_ok=False)
        for sid in REPEAT_SOURCES:
            (run/"determinism/repeat"/sid).mkdir(exist_ok=False)
            for view in VIEWS[sid]:
                original=run/"sources"/sid/view
                replica=run/"determinism/repeat"/sid/view
                build_view(ROOT,sid,view,replica,compare_reference=False)
                comparison=compare_repeat(original,replica)
                key=sid+"/"+view
                determinism[key]=comparison
                write_json(original/"determinism.json",comparison)
                if comparison["status"]!="PASS":
                    raise ValueError("NON_DETERMINISTIC_LABELS: "+key)
        for sid,views in VIEWS.items():
            for view in views:
                if sid not in REPEAT_SOURCES:
                    write_json(run/"sources"/sid/view/"determinism.json",
                               {"status":"NOT_AVAILABLE","reason":"SINGLE_EXECUTION_ONLY"})
        write_json(run/"quality/cross_view_summary.json",cross)
        write_json(run/"determinism/summary.json",determinism)
        after={"hft":fingerprints(hft_paths),"phase2c_features":fingerprints(feature_paths)}
        write_json(run/"summary/input_integrity_after.json",after)
        integrity={"status":"PASS" if before==after else "FAIL",
                   "hft_source_count":len(hft_paths),"feature_input_count":len(feature_paths),
                   "hft_equal":before["hft"]==after["hft"],
                   "feature_equal":before["phase2c_features"]==after["phase2c_features"]}
        write_json(run/"summary/input_integrity_comparison.json",integrity)
        if integrity["status"]!="PASS":
            raise ValueError("SOURCE_INTEGRITY_CHANGED")
        aggregate={}
        for h in HORIZONS_MS:
            keys=("input_rows","matched_rows","unmatched_rows","valid_labels",
                  "invalid_labels","session_tail_count","zero_return_count")
            aggregate[str(h)]={k:sum(x["quality"]["horizons"][str(h)][k] for x in results.values())
                               for k in keys}
        summary={"status":"PHASE 2D PASS","run_id":run_id,"phase2c_run_id":PHASE2C_RUN,
                 "views":len(results),"primary_horizon_totals":aggregate,
                 "reference_mismatch_count":sum(v["reference"]["mismatch_count"] for v in results.values()),
                 "cross_view_mismatch_count":sum(v["mismatch_count"] for v in cross.values()),
                 "determinism_status":"PASS","hft_integrity":"PASS","feature_integrity":"PASS",
                 "local_timestamp_used":False,"class_labels_created":False,
                 "split_created":False,"model_created":False,"backtest_created":False,
                 "paper_trading_created":False,"network_used":False,"trade_executed":False}
        write_json(run/"summary/run_summary.json",summary)
        write_json(run/"quality/combined_label_quality.json",
                   {key:value["quality"] for key,value in results.items()})
        write_json(run/"reference/combined_comparison.json",
                   {key:value["reference"] for key,value in results.items()})
        write_json(run/"match_error/combined_statistics.json",
                   {key:{h:value["quality"]["horizons"][h]["match_error_distribution_ms"]
                         for h in map(str,HORIZONS_MS)}
                    for key,value in results.items()})
        code_paths=[ROOT/"data_pipeline/labels"/name for name in
                    ("__init__.py","schema.py","matcher.py","builder.py","reference.py","validator.py","writer.py")]
        code_paths.append(Path(__file__))
        write_json(run/"summary/code_manifest.json",fingerprints(code_paths))
        report=ROOT/"docs"/f"PHASE2D_REPORT_{run_id}.md"
        with report.open("x",encoding="utf-8",newline="\n") as handle:
            handle.write(_report(run_id,results,cross,determinism,integrity,tests,commands,"PHASE 2D PASS"))
        print(json.dumps({"status":"PHASE 2D PASS","run_id":run_id,
                          "summary":str(run/"summary/run_summary.json"),
                          "report":str(report)},sort_keys=True),flush=True)
        commands[0]["finished_at_utc"]=utc()
        commands[0]["exit_code"]=0
        write_json(run/"logs/execution.json",commands)
        return 0
    except Exception as exc:
        commands[0]["finished_at_utc"]=utc()
        commands[0]["exit_code"]=1
        failure={"status":"PHASE 2D FAIL","run_id":run_id,"error":repr(exc),
                 "finished_at_utc":utc(),"commands":commands}
        write_json(run/"summary/failure.json",failure)
        write_json(run/"logs/execution.json",commands)
        report=ROOT/"docs"/f"PHASE2D_REPORT_{run_id}.md"
        with report.open("x",encoding="utf-8",newline="\n") as handle:
            handle.write("# Phase 2D：FAIL\n\n"+json.dumps(failure,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
        print(json.dumps(failure,ensure_ascii=False,sort_keys=True),file=sys.stderr,flush=True)
        return 1
    finally:
        sys.stdout,sys.stderr=original_stdout,original_stderr
        stdout_log.close()
        stderr_log.close()

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id",required=True,help="new UTC ID YYYYMMDDTHHMMSSZ; existing run rejected")
    args=parser.parse_args(argv)
    return execute(args.run_id)

if __name__=="__main__":
    raise SystemExit(main())
