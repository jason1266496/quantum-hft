"""Phase 2E: chronological index manifests, frozen training-only policies and leakage checks."""
import argparse,bisect,csv,gc,json,os,re,subprocess,sys,time,traceback
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data_pipeline.splits.schema import (HORIZONS,SPLITS,PHASE2C_RUN,PHASE2D_RUN,SMOKE_SOURCE,
    FeatureIndex,LabelIndex,SourceData,INDEX_FIELDS,RAW_FIELDS,EXCLUDED_FIELDS,schema_document)
from data_pipeline.splits.policy import whole_session_plan,depth_plan,scaler_policy,embargo_policy
from data_pipeline.splits.matcher_policy import choose_policy
from data_pipeline.splits.splitter import training_candidates,build_membership
from data_pipeline.splits.walk_forward import build_windows
from data_pipeline.splits.validator import validate
from data_pipeline.splits.writer import sha_file,write_csv,write_json,safe_output

C=ROOT/"artifacts/phase2c"/PHASE2C_RUN
D=ROOT/"artifacts/phase2d"/PHASE2D_RUN
TESTS=("tests.test_split_schema","tests.test_match_error_policy","tests.test_time_splitter",
       "tests.test_purge","tests.test_walk_forward","tests.test_split_validator",
       "tests.test_split_writer","tests.test_build_splits_tool")
SLUG={"Train":"train","Validation":"validation","Test":"test","Final Holdout":"final_holdout"}

def utc():return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def fingerprint(path):
    p=Path(path)
    if not p.is_file() or any(x.is_symlink() for x in (p,*p.parents)):
        raise ValueError("MISSING_OR_SYMLINK_INPUT: "+str(p))
    return {"sha256":sha_file(p),"size_bytes":p.stat().st_size}

def preflight():
    """No Phase 2E run is created until every formal fingerprint agrees."""
    if Path.cwd()!=ROOT or ROOT!=Path("/home/jason/quantum-hft") or ROOT.resolve()!=ROOT:
        raise ValueError("WRONG_WORKING_DIRECTORY")
    saved=json.loads((D/"summary/run_summary.json").read_text())
    if saved["status"]!="PHASE 2D PASS":raise ValueError("PHASE2D_NOT_PASS")
    known={}
    def check(path,expected=None):
        actual=fingerprint(path);known[str(path)]=actual
        if expected is not None and actual!=expected:
            raise ValueError("INPUT_HASH_MISMATCH: "+str(path))
    for s in sorted((D/"sources").iterdir()):
        for v in sorted(s.iterdir()):
            q=json.loads((v/"label_quality.json").read_text())
            manifest=json.loads((C/"sources"/s.name/"feature_manifest.json").read_text())
            if manifest["status"]!="PASS" or q["status"]!="PASS":
                raise ValueError("PRIOR_OUTPUT_NOT_PASS")
            view=manifest["attempts"][0]["views"][v.name]
            check(C/"sources"/s.name/(v.name+".csv"),
                  {"sha256":view["sha256"],"size_bytes":view["size_bytes"]})
            for key,info in q["output_files"].items():
                name="invalid_labels.csv" if key=="invalid_labels" else f"labels_{key}ms.csv"
                check(v/name,{"sha256":info["sha256"],"size_bytes":info["size_bytes"]})
            check(v/"label_quality.json")
            check(v/"match_error_statistics.json")
    config=json.loads((ROOT/"configs/data_sources.json").read_text())
    if len(config["sources"])!=9:raise ValueError("NINE_HFT_SOURCES_REQUIRED")
    for source in config["sources"]:
        path=Path(source["absolute_path"])
        if path.parent!=Path("/home/jason/hft-realtime-codex/results"):
            raise ValueError("UNAPPROVED_HFT_INPUT")
        check(path,{"sha256":source["sha256"],"size_bytes":source["size_bytes"]})
    for path,expected in json.loads((D/"summary/code_manifest.json").read_text()).items():
        check(Path(path),expected)
    old2c=json.loads((ROOT/"artifacts/phase2c_cleanup/20261019T000857Z/completion_manifest.json").read_text())
    if old2c["phase_status"]!="PHASE 2C PASS":raise ValueError("PHASE2C_NOT_PASS")
    recorded={row["path"]:row for row in old2c["new_files_and_directories"] if row["kind"]=="file"}
    for view in ("aggregate_core_v1","depth_top5_v1"):
        path=C/"schemas"/(view+".schema.json");record=recorded[str(path.relative_to(ROOT))]
        check(path,{"sha256":record["sha256"],"size_bytes":record["size"]})
    check(D/"schemas/label.schema.json")
    schema=json.loads((D/"schemas/label.schema.json").read_text())
    if schema["horizons_ms"]!=list(HORIZONS) or schema["local_timestamp_us_in_output"]:
        raise ValueError("INTERFACE_GAP_LABEL_SCHEMA")
    for path in (ROOT/"configs/data_sources.json",ROOT/"configs/timestamp_policy.json",
                 ROOT/"AGENTS.md",ROOT/"README.md",ROOT/"data_contract/HFT_INPUT_DATA_CONTRACT.md",
                 ROOT/"docs"/f"PHASE2C_REPORT_{PHASE2C_RUN}.md",
                 ROOT/"docs"/f"PHASE2D_REPORT_{PHASE2D_RUN}.md"):
        check(path)
    protected={}
    for group in ("data_pipeline","tools","tests"):
        for path in (ROOT/group).rglob("*.py"):
            rel=str(path.relative_to(ROOT))
            if "/splits/" in rel or "phase2e" in rel or path.name in ("build_splits.py",) or path.name in [x.split(".")[-1]+".py" for x in TESTS]:
                continue
            protected[str(path)]=fingerprint(path)
    known.update(protected)
    return known

def load_sources():
    sources=[]
    start=time.monotonic()
    for folder in sorted((D/"sources").iterdir()):
        for view in sorted(folder.iterdir()):
            feature=C/"sources"/folder.name/(view.name+".csv")
            rows=[];identity=None;last_time=-1;last_index=0
            schema=json.loads((C/"schemas"/(view.name+".schema.json")).read_text())
            with feature.open(newline="",encoding="utf-8") as f:
                reader=csv.DictReader(f)
                if reader.fieldnames!=schema["field_order"]:raise ValueError("INTERFACE_GAP_FEATURE_SCHEMA")
                for raw in reader:
                    pair=(raw["source_id"],raw["session_id"])
                    if identity is None:identity=pair
                    if pair!=identity or pair[0]!=folder.name or raw["feature_view"]!=view.name:
                        raise ValueError("CROSS_SOURCE_SESSION_OR_VIEW")
                    t=int(raw["event_time_ms"]);index=int(raw["record_index"])
                    if t<last_time or index<=last_index:raise ValueError("UNSORTED_INPUT")
                    last_time,last_index=t,index
                    event_id=raw["local_update_id"] or "record:"+str(index)
                    rows.append(FeatureIndex(pair[0],pair[1],view.name,index,t,str(t)+":"+event_id))
            if not rows:raise ValueError("EMPTY_FEATURE_INPUT")
            times=[r.event_time_ms for r in rows];labels={};label_hashes={}
            for h in HORIZONS:
                path=view/f"labels_{h}ms.csv";items=[]
                with path.open(newline="",encoding="utf-8") as f:
                    reader=csv.DictReader(f)
                    if "local_timestamp_us" in reader.fieldnames:raise ValueError("LOCAL_TIMESTAMP_PROHIBITED")
                    for row,raw in zip(rows,reader,strict=True):
                        if (raw["source_id"],raw["session_id"],raw["feature_view"])!=(row.source_id,row.session_id,row.feature_view):
                            raise ValueError("LABEL_SOURCE_SESSION_MISMATCH")
                        if int(raw["record_index"])!=row.record_index or int(raw["current_event_time_ms"])!=row.event_time_ms or int(raw["requested_horizon_ms"])!=h:
                            raise ValueError("FEATURE_LABEL_ALIGNMENT_MISMATCH")
                        target=None if raw["target_event_time_ms"]=="" else int(raw["target_event_time_ms"])
                        error=None if raw["match_error_ms"]=="" else int(raw["match_error_ms"])
                        j=bisect.bisect_left(times,row.event_time_ms+h)
                        expected=times[j] if j<len(times) else None
                        if target!=expected:raise ValueError("CROSS_SESSION_OR_CHANGED_TARGET")
                        if target is not None and (error!=target-row.event_time_ms-h or
                            int(raw["actual_horizon_ms"])!=target-row.event_time_ms):
                            raise ValueError("LABEL_ENDPOINT_MISMATCH")
                        valid=raw["valid_label"]=="true"
                        if valid and (target is None or error is None or error<0):raise ValueError("INVALID_VALID_LABEL")
                        items.append(LabelIndex(target,error,valid,raw["invalid_reason"]))
                labels[h]=items;label_hashes[str(h)]=sha_file(path)
            sources.append(SourceData(identity[0],identity[1],view.name,rows,labels,sha_file(feature),label_hashes))
            print(json.dumps({"stage":"LOAD_INPUT_METADATA","sources_loaded":len(sources),"total_sources":9,
                              "percent":round(len(sources)*100/9,2),"elapsed_seconds":round(time.monotonic()-start,3),
                              "eta_seconds":round((9-len(sources))*(time.monotonic()-start)/len(sources),3),
                              "source_id":identity[0],"feature_view":view.name}),flush=True)
    return sources

def timeline(sources):
    ordered=sorted({s.source_id:s for s in sources}.values(),key=lambda s:s.rows[0].event_time_ms)
    ranks={s.source_id:i+1 for i,s in enumerate(ordered)}
    entries=[]
    for s in sorted(sources,key=lambda x:(x.rows[0].event_time_ms,x.feature_view)):
        entries.append({"source_id":s.source_id,"session_id":s.session_id,"feature_view":s.feature_view,
                        "row_count":len(s.rows),"event_time_start":s.rows[0].event_time_ms,
                        "event_time_end":s.rows[-1].event_time_ms,
                        "date_utc":datetime.fromtimestamp(s.rows[0].event_time_ms//1000,timezone.utc).date().isoformat(),
                        "source_family":"replay" if s.source_id.startswith("replay") else "csv",
                        "chronological_rank":ranks[s.source_id],
                        "resource_role":"SMOKE_VALIDATION_ONLY" if s.source_id==SMOKE_SOURCE else "FORMAL_CANDIDATE",
                        "phase2d_valid_labels":{str(h):sum(x.valid_label for x in s.labels[h]) for h in HORIZONS},
                        "phase2d_invalid_labels":{str(h):sum(not x.valid_label for x in s.labels[h]) for h in HORIZONS}})
    overlaps=[]
    for i,a in enumerate(ordered):
        for b in ordered[i+1:]:
            if b.rows[0].event_time_ms<=a.rows[-1].event_time_ms:
                overlaps.append({"code":"OVERLAPPING_SOURCE_INTERVAL","left":a.source_id,"right":b.source_id})
    return {"entries":entries,"overlapping_source_intervals":overlaps,
            "date_basis":"UTC derived from audited event_time_ms; filenames do not order sources"}

def save_view(out,sources,plan,policy,scaler):
    out.mkdir(exist_ok=False)
    membership=build_membership(sources,plan,policy)
    raw_info=write_csv(out/"raw_assignment_indices.csv",RAW_FIELDS,membership["raw"])
    excluded_info=write_csv(out/"excluded_indices.csv",EXCLUDED_FIELDS,membership["excluded"])
    manifests={}
    for split in SPLITS:
        info=write_csv(out/(SLUG[split]+"_indices.csv"),INDEX_FIELDS,membership["included"][split])
        entries=membership["entries"][split]
        counts={str(h):{key:sum(x["per_horizon"][str(h)][key] for x in entries)
                        for key in ("valid_label_rows","invalid_label_rows","match_error_filtered_rows",
                                    "purged_rows","final_rows")} for h in HORIZONS}
        for item in entries:item["split_indices_hash"]=info["sha256"]
        manifests[split]={"feature_view":plan["feature_view"],"raw_rows":sum(x["raw_rows"] for x in entries),
                          "event_time_start":min(x["event_time_start"] for x in entries),
                          "event_time_end":max(x["event_time_end"] for x in entries),
                          "source_entries":entries,"per_horizon":counts,"indices":info}
    windows=build_windows(sources,plan)
    checks=validate(sources,plan,membership,policy,scaler,windows)
    write_json(out/"split_manifest.json",{"feature_view":plan["feature_view"],"splits":manifests,
               "raw_assignment_indices":raw_info,"excluded_indices":excluded_info,
               "shuffle":False,"time_field":"event_time_ms","class_labels":False})
    write_json(out/"purge_report.json",membership["purge_report"])
    write_json(out/"walk_forward_windows.json",{"feature_view":plan["feature_view"],
               "window_count":len(windows),"windows":windows,"models_trained":False})
    write_json(out/("depth_split_policy.json" if plan["feature_view"]=="depth_top5_v1" else "aggregate_split_policy.json"),plan)
    return {"plan":plan,"manifest":manifests,"leakage":checks,"windows":windows,
            "raw_count":len(membership["raw"]),"purge_report":membership["purge_report"]}

def build_once(out):
    sources=load_sources()
    metadata=timeline(sources)
    write_json(out/"source_timeline.json",metadata)
    for name in ("match_error","policies","quality"):(out/name).mkdir(exist_ok=False)
    aggregate=[s for s in sources if s.feature_view=="aggregate_core_v1"]
    depth=[s for s in sources if s.feature_view=="depth_top5_v1"]
    plans={"aggregate":whole_session_plan(aggregate),
           "depth":depth_plan(next(s for s in depth if s.source_id=="replay_events_50000"))}
    groups={"aggregate":aggregate,"depth":depth}
    policies={}
    for name in plans:
        policies[name]=choose_policy(training_candidates(groups[name],plans[name]),plans[name]["feature_view"])
        if policies[name]["status"]!="PASS":
            write_json(out/"match_error"/(name+"_policy_review.json"),policies[name])
            raise ValueError("NEED_POLICY_REVIEW")
    write_json(out/"match_error/candidate_thresholds.json",
               {k:{"threshold_candidates":v["threshold_candidates"],"guardrails":v["guardrails"]} for k,v in policies.items()})
    write_json(out/"match_error/retention_analysis.json",
               {k:v["retention_by_candidate"] for k,v in policies.items()})
    write_json(out/"match_error/match_error_policy.json",policies)
    scaler=scaler_policy();embargo=embargo_policy()
    write_json(out/"policies/scaler_policy.json",scaler)
    write_json(out/"policies/embargo_policy.json",embargo)
    result={}
    for name in plans:
        result[name]=save_view(out/name,groups[name],plans[name],policies[name],scaler)
        if result[name]["leakage"]["status"]!="PASS":
            write_json(out/"quality"/(name+"_leakage_failure.json"),result[name]["leakage"])
            raise ValueError("LEAKAGE_DETECTED")
    prohibited=["feature selection","threshold selection","label threshold selection","scaler fitting",
                "hyperparameter tuning","Quantum Feature Map selection","QAOA penalty selection",
                "model selection","repeated experimentation"]
    holdout={}
    for name,value in result.items():
        held=value["manifest"]["Final Holdout"]
        holdout[name]={"feature_view":value["plan"]["feature_view"],"holdout_status":"LOCKED",
                       "lock_type":"VERSIONED_PROTOCOL_LOCK_NOT_OS_ACCESS_CONTROL",
                       "sources":[{"source_id":x["source_id"],"session_id":x["session_id"],
                                   "event_time_start":x["event_time_start"],"event_time_end":x["event_time_end"],
                                   "row_count":x["raw_rows"],
                                   "valid_label_count_by_horizon":{h:x["per_horizon"][h]["valid_label_rows"] for h in map(str,HORIZONS)},
                                   "feature_sha256":x["source_feature_hash"],"label_sha256":x["source_label_hash"],
                                   "frozen_final_rows_by_horizon":{h:x["per_horizon"][h]["final_rows"] for h in map(str,HORIZONS)}}
                                  for x in held["source_entries"]],
                       "split_indices_sha256":held["indices"]["sha256"],
                       "raw_assignment_sha256":sha_file(out/name/"raw_assignment_indices.csv"),
                       "allowed_uses":["integrity and identity audit",
                                       "single final evaluation after model and research design freeze and explicit approval"],
                       "prohibited_uses":prohibited,
                       "phase3_4_5_require_model_and_protocol_frozen":True}
    write_json(out/"policies/final_holdout_manifest.json",holdout)
    write_json(out/"quality/leakage_validation.json",
               {"status":"PASS","views":{k:v["leakage"] for k,v in result.items()}})
    write_json(out/"quality/overlap_check.json",{"status":"PASS",
               "source_interval_overlaps":metadata["overlapping_source_intervals"],
               "per_view":{k:{"row_overlap":v["leakage"]["row_overlap_count"],
                              "event_overlap":v["leakage"]["event_overlap_count"]} for k,v in result.items()},
               "cross_view_same_events":"INTENTIONAL_SEPARATE_RESEARCH_LINES_NOT_A_MERGED_POOL"})
    write_json(out/"quality/split_quality.json",
               {k:{"raw_rows":v["raw_count"],"splits":v["manifest"]} for k,v in result.items()})
    return {"views":result,"policies":policies,"holdout":holdout,"timeline":metadata}

def deterministic_files(root):
    paths=[root/"source_timeline.json"]
    for group in ("aggregate","depth","match_error","policies","quality"):
        paths.extend(p for p in (root/group).rglob("*") if p.is_file())
    return {str(p.relative_to(root)):fingerprint(p) for p in sorted(paths)}

class Tee:
    def __init__(self,terminal,file):self.terminal,self.file=terminal,file
    def write(self,value):
        self.terminal.write(value);self.file.write(value);self.file.flush()
    def flush(self):self.terminal.flush();self.file.flush()

def report(run_id,result,tests,determinism,integrity,command):
    lines=["# Phase 2E：時間切分、Leakage Protection 與 Final Holdout 鎖定","",
           "**PHASE 2E PASS**；run_id："+run_id,"",
           "Phase 2D 20261026T193335Z 已獲人工審核批准。正式輸入先對既有 manifest/quality SHA 與大小驗證，全部通過後才建立本 run。",
           "程式只使用 Python 標準函式庫。Git commit 為 NOT_AVAILABLE；程式 SHA 保存於 summary/code_manifest.json，無隨機運算。",
           "本報告的 counts 全由本輪新 indices/manifest 計算，沒有虛構結果。","",
           "## 來源時間線與研究線","",
           "| source | view | UTC date | rows | start event ms | end event ms | role |",
           "| --- | --- | --- | ---: | ---: | ---: | --- |"]
    for row in result["timeline"]["entries"]:
        lines.append(f"| {row['source_id']} | {row['feature_view']} | {row['date_utc']} | {row['row_count']} | {row['event_time_start']} | {row['event_time_end']} | {row['resource_role']} |")
    lines+=["","來源重疊區段數："+str(len(result["timeline"]["overlapping_source_intervals"]))+"。"
             "不同月份/Session 各保留原 identity，不視為連續市場。Aggregate 與 Depth 的樣本池完全分開；Replay1000 僅作 smoke/reference/pipeline validation，不入正式 split 或 Holdout。",
             "Aggregate 比較 A/B 完整 Session 配置，選 B：前三個最早 CSV Session 作 Train、Session3 作 Validation、Replay50000 作 Test、最新 obi_market_data 作 Holdout。"
             "候選 A 的 Train 小於 Validation/Test；B 保留所有完整 Session，並保有較大的早期 Train。"
             "來源名稱中的 test 不等於正式 Test；角色以 event-time protocol 決定。",
             "Depth 只用 Replay50000；以 elapsed event time 的60/80/90%作候選切點，向前找第一個已觀察 timestamp，"
             "相同 timestamp 放同一側。也記錄70/85/95%候選，依使用者初始比例選60/20/10/10，沒有用 Holdout outcome 改界線。","",
             "## Training-only Match Error Policy","",
             "選擇準則在正式 Training 分布分析前固定：在 max error / nominal horizon <=5% 的候選中，"
             "選擇達到至少90% Training Candidate 保留率的最小 threshold。這是 timing-distortion/coverage 規格，不是最大化保留數或報酬。"
             "若無候選同時滿足，標記 NEED_POLICY_REVIEW。完整候選0/1/2/5/10/25/50/100ms與 TRAIN_P95/TRAIN_P99均已比較。",
             "Training Candidate 必須 current 位於 Train 且實際 target 在 Train region 結束前；"
             "Test/Final Holdout/Phase2D全資料quantile均未參與 threshold 選擇；未讀取 future_return_bps 作政策選擇。",
             "| line | H | threshold ms | training candidate count | retained fraction | TRAIN p95/p99 |",
             "| --- | ---: | ---: | ---: | --- | --- |"]
    for name,p in result["policies"].items():
        for h in map(str,HORIZONS):
            info=p["retention_by_candidate"][h]
            lines.append(f"| {name} | {h} | {p['chosen_threshold_by_horizon'][h]} | {info['statistics']['count']} | {info['chosen_retention']} | {info['statistics']['p95']}/{info['statistics']['p99']} |")
    lines+=["","每條研究線分別凍結自己的 threshold；共同門檻是否適用與 horizon-specific 比較結果見 match_error/match_error_policy.json。"
             "gap profile 已讀取 Phase2D 記錄；本階段沒有因 later data 的 gap/return 表現增訂資料驅動 gap threshold。","",
             "## 切分、Purge 與結果","",
             "indices 檔每列是一個 source/session/record/horizon 的可用 label index，不複製 Feature 或 continuous return 值。"
             "raw_assignment_indices.csv 每個市場事件一列；excluded_indices.csv 保存 invalid、purged 或 match-error 過濾原因。",
             "先依實際 target_event_time >= 下一 split boundary purge（等於也 purge），再套用已凍結 match-error policy。"
             "無效 Session tail 不補值、不跨來源搜尋。Purge 不是固定刪最後1000ms。",
             "| line | split | raw events | final H100/H200/H500/H1000 | purged H100/H200/H500/H1000 | filtered H100/H200/H500/H1000 |",
             "| --- | --- | ---: | --- | --- | --- |"]
    for name,value in result["views"].items():
        for split,m in value["manifest"].items():
            final="/".join(str(m["per_horizon"][str(h)]["final_rows"]) for h in HORIZONS)
            purged="/".join(str(m["per_horizon"][str(h)]["purged_rows"]) for h in HORIZONS)
            filtered="/".join(str(m["per_horizon"][str(h)]["match_error_filtered_rows"]) for h in HORIZONS)
            lines.append(f"| {name} | {split} | {m['raw_rows']} | {final} | {purged} | {filtered} |")
    lines+=["","Purge report 逐 split/horizon 保存 before/purged/after 與首末被移除 event time。"
             "Aggregate 的完整 Session boundary 沒有跨檔 target；Depth 三個切點用 actual endpoint 驗證。","",
             "## Embargo、Scaler 與 Walk-forward","",
             "embargo_ms=0，NO_ADDITIONAL_EMBARGO_BEYOND_PURGING。現有 Feature 沒有 rolling lookback，"
             "actual-target purge 已處理跨 split 標籤視窗；同 split 內 label 仍高度重疊，後續評估不可假設獨立。",
             "Scaler 尚未 fit；只可 Train fit，Validation/Test/Holdout transform；每個 View 獨立、參數需版本化，"
             "禁止全資料統計、不同 split 各自fit；event time、ID與categorical metadata不得作數值標準化。",
             "Walk-forward 為 expanding-window 規格；Aggregate 用完整早期 Session，Depth 用同 Session 內時間區段。"
             "每個 fold 都從自己的 Train 重新選 match policy並purge train/validation endpoint；沒有使用較晚 formal Train 的政策污染早期 fold。"
             "所有 window 都早於 formal Test 和 Holdout。"]
    for name,value in result["views"].items():
        lines.append(f"- {name}：{len(value['windows'])} 個 window；train/validation時間、counts、每horizon purge及fold policy均存於對應 walk_forward_windows.json。")
    lines+=["","## Final Holdout 鎖定","",
             "LOCKED 是版本化研究規格鎖定，不宣稱 OS 強制禁止讀取。允許 identity/hash audit；"
             "Phase3/4/5 僅可在模型及研究設計固定且人工批准後作一次 final evaluation。",
             "禁止 feature selection、threshold selection、label threshold selection、scaler fitting、hyperparameter tuning、"
             "Quantum Feature Map selection、QAOA penalty selection、model selection、repeated experimentation。"]
    for name,hold in result["holdout"].items():
        for source in hold["sources"]:
            lines.append(f"- {name}：{source['source_id']} / {source['session_id']}，{source['event_time_start']}–{source['event_time_end']}ms，raw rows={source['row_count']}。")
    lines+=["","## 測試、Leakage、Determinism 與完整性","",
             f"Phase2E 單元測試：{tests['test_count']} tests，PASS={tests['pass']}，FAIL={tests['fail']}，ERROR={tests['error']}，skipped={tests['skipped']}，exit={tests['exit_code']}，duration={tests['duration_seconds']}s。"
             "測試只使用人工 fixture，暫存資料只在 tests/fixtures/phase2e/。",
             "Leakage Validator：兩條研究線全部 PASS。檢查時間順序、raw/source/event overlap、actual target boundary、"
             "label source/session、Training-only threshold、Train-only scaler、walk-forward及no-holdout policy。",
             "Overlap check：raw row/event 跨split重疊為0。相同市場事件的Aggregate/Depth是兩個獨立研究線，不合併sample pool。",
             f"完整第二次建立：{determinism['status']}；比較全部 {determinism['compared_file_count']} 個 deterministic檔案，"
             "涵蓋 membership、indices SHA、purge、threshold、walk-forward、Holdout與timeline。",
             f"輸入完整性：{integrity['status']}，前後核對{integrity['file_count']}檔；"
             "含9個 Feature CSV、36個正式 label CSV、9個 invalid label CSV、9個HFT來源、schema與既有程式/政策證據。",
             "沒有 local_timestamp、class label、模型訓練、回測、Paper Trading、Quantum Kernel、QUBO/QAOA、HFT binary、網路或交易。"
             "本次命令範圍沒有網路操作，並非全機封包監測。","",
             "## 實際命令與停止點","",
             "工作目錄前置命令：pwd、realpath .、findmnt -T .。",
             "正式命令：","", "    "+" ".join(command),"",
             "測試命令：","", "    "+ " ".join(tests["command"]),"",
             "完整stdout/stderr/exit code見logs/execution.json及logs下檔案；"
             "開發與唯讀前置命令另見logs/development_commands.json（若由Codex交付時封存）。",
             "PHASE 2E PASS。建議人工審核 policies、資料regime差異與locked holdout後，另行明確批准Phase2F。"
             "本次已停止，沒有進入Phase2F，也沒有虛構模型、量子、回測或交易結果。",""]
    return "\n".join(lines)

def execute(run_id):
    before=preflight()
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z",run_id):raise ValueError("INVALID_RUN_ID")
    datetime.strptime(run_id,"%Y%m%dT%H%M%SZ")
    report_path=safe_output(ROOT/"docs"/f"PHASE2E_REPORT_{run_id}.md")
    run=safe_output(ROOT/"artifacts/phase2e"/run_id)
    if os.path.lexists(run) or os.path.lexists(report_path):raise FileExistsError("RUN_OR_REPORT_EXISTS")
    run.parent.mkdir(exist_ok=True);run.mkdir(exist_ok=False)
    for name in ("logs","summary","determinism"):(run/name).mkdir(exist_ok=False)
    oldout,olderr=sys.stdout,sys.stderr
    out=(run/"logs/stdout.txt").open("x",encoding="utf-8")
    err=(run/"logs/stderr.txt").open("x",encoding="utf-8")
    sys.stdout,sys.stderr=Tee(oldout,out),Tee(olderr,err)
    command=[sys.executable,"-B","tools/build_splits.py","--run-id",run_id]
    started=utc();test_result=None
    try:
        write_json(run/"summary/input_integrity_before.json",before)
        write_json(run/"summary/split_schema.json",schema_document())
        test_command=[sys.executable,"-B","-m","unittest",*TESTS]
        t=time.monotonic()
        check=subprocess.run(test_command,cwd=ROOT,capture_output=True,text=True,check=False)
        for name,value in (("tests.stdout.txt",check.stdout),("tests.stderr.txt",check.stderr)):
            with (run/"logs"/name).open("x",encoding="utf-8") as f:f.write(value)
        match=re.search(r"Ran ([0-9]+) tests?",check.stderr)
        failure=re.search(r"failures=([0-9]+)",check.stderr)
        error=re.search(r"errors=([0-9]+)",check.stderr)
        skipped=re.search(r"skipped=([0-9]+)",check.stderr)
        count=int(match[1]) if match else 0
        fails=int(failure[1]) if failure else 0
        errors=int(error[1]) if error else 0
        skips=int(skipped[1]) if skipped else 0
        test_result={"command":test_command,"test_count":count,"pass":count-fails-errors-skips,
                     "fail":fails,"error":errors,"skipped":skips,
                     "exit_code":check.returncode,"duration_seconds":round(time.monotonic()-t,6),
                     "stdout_path":"logs/tests.stdout.txt","stderr_path":"logs/tests.stderr.txt"}
        write_json(run/"summary/test_results.json",test_result)
        if check.returncode or not count:raise RuntimeError("PHASE2E_TESTS_FAILED")
        result=build_once(run)
        gc.collect()
        replica=run/"determinism/repeat";replica.mkdir(exist_ok=False)
        repeat_result=build_once(replica)
        first,second=deterministic_files(run),deterministic_files(replica)
        differences=[k for k in set(first)|set(second) if first.get(k)!=second.get(k)]
        determinism={"status":"PASS" if not differences else "NON_DETERMINISTIC_SPLIT",
                     "compared_file_count":len(first),"differences":sorted(differences),
                     "first":first,"second":second}
        write_json(run/"determinism/comparison.json",determinism)
        if differences:raise RuntimeError("NON_DETERMINISTIC_SPLIT")
        after={path:fingerprint(path) for path in before}
        write_json(run/"summary/input_integrity_after.json",after)
        integrity={"status":"PASS" if before==after else "FAIL","file_count":len(before),
                   "changed_inputs":[p for p in before if before[p]!=after[p]],
                   "features":9,"labels":36,"invalid_labels":9,"hft_sources":9}
        write_json(run/"summary/input_integrity_comparison.json",integrity)
        if before!=after:raise RuntimeError("INPUT_INTEGRITY_CHANGED")
        code=[*sorted((ROOT/"data_pipeline/splits").glob("*.py")),Path(__file__),
              *(ROOT/(x.replace(".","/")+".py") for x in TESTS),
              *sorted((ROOT/"tests/fixtures/phase2e").glob("*.py"))]
        write_json(run/"summary/code_manifest.json",{str(p.relative_to(ROOT)):fingerprint(p) for p in code})
        with report_path.open("x",encoding="utf-8",newline="\n") as f:
            f.write(report(run_id,result,test_result,determinism,integrity,command))
        summary={"status":"PHASE 2E PASS","run_id":run_id,"report":str(report_path),
                 "tests":test_result,"policies":{k:{"thresholds":v["chosen_threshold_by_horizon"],
                     "training_retention":{h:i["chosen_retention"] for h,i in v["retention_by_candidate"].items()}}
                     for k,v in result["policies"].items()},
                 "split_counts":{k:{s:{"raw_rows":m["raw_rows"],"per_horizon":m["per_horizon"]}
                     for s,m in v["manifest"].items()} for k,v in result["views"].items()},
                 "purge_counts":{k:v["purge_report"] for k,v in result["views"].items()},
                 "walk_forward_windows":{k:len(v["windows"]) for k,v in result["views"].items()},
                 "determinism":"PASS","leakage":"PASS","integrity":integrity,
                 "holdout":result["holdout"],"phase2f_started":False,
                 "local_timestamp_used":False,"class_label_created":False,"model_trained":False,
                 "backtest":False,"network":False,"trading":False}
        write_json(run/"summary/run_summary.json",summary)
        write_json(run/"logs/execution.json",{"command":command,"cwd":str(ROOT),"started_at_utc":started,
                   "finished_at_utc":utc(),"exit_code":0,"stdout_path":"logs/stdout.txt",
                   "stderr_path":"logs/stderr.txt","subcommands":[test_result]})
        print(json.dumps({"status":"PHASE 2E PASS","run_id":run_id,"report":str(report_path)}),flush=True)
        return 0
    except Exception as exc:
        failure={"status":"PHASE 2E FAIL","run_id":run_id,"error":repr(exc),"traceback":traceback.format_exc()}
        write_json(run/"summary/failure.json",failure)
        write_json(run/"logs/execution.json",{"command":command,"cwd":str(ROOT),"started_at_utc":started,
                   "finished_at_utc":utc(),"exit_code":1,"stdout_path":"logs/stdout.txt",
                   "stderr_path":"logs/stderr.txt","subcommands":[test_result] if test_result else []})
        if not report_path.exists():
            with report_path.open("x",encoding="utf-8") as f:f.write("# PHASE 2E FAIL\n\n"+json.dumps(failure,ensure_ascii=False,indent=2)+"\n")
        print(json.dumps(failure),file=sys.stderr,flush=True)
        return 1
    finally:
        sys.stdout,sys.stderr=oldout,olderr;out.close();err.close()

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id",required=True)
    return execute(parser.parse_args(argv).run_id)

if __name__=="__main__":raise SystemExit(main())
