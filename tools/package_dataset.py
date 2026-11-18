"""Phase 2F only: package and lock two dataset families from approved C/D/E outputs."""
import argparse,hashlib,json,os,re,subprocess,sys,time,traceback
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data_pipeline.datasets.schema import dataset_id,validate_run_id,HORIZONS,HOLDOUT_STATS_STATUS
from data_pipeline.datasets.manifest import C_RUN,D_RUN,E_RUN
from data_pipeline.datasets.checksums import fingerprint,sha_file,write_json,safe_output
from data_pipeline.datasets.packager import package_family
from data_pipeline.datasets.validator import validate_dataset
E=ROOT/"artifacts/phase2e"/E_RUN
TESTS=("tests.test_dataset_schema","tests.test_dataset_manifest","tests.test_dataset_packager",
       "tests.test_dataset_validator","tests.test_dataset_checksums","tests.test_package_dataset_tool")

def utc():return datetime.now(timezone.utc).isoformat()

def context():
    return {"feature_root":ROOT/"artifacts/phase2c"/C_RUN,
            "label_root":ROOT/"artifacts/phase2d"/D_RUN,"split_root":E,
            "source_config":ROOT/"configs/data_sources.json",
            "timestamp_policy":ROOT/"configs/timestamp_policy.json",
            "contract":ROOT/"data_contract/HFT_INPUT_DATA_CONTRACT.md"}

def preflight():
    if Path.cwd()!=ROOT or ROOT!=Path("/home/jason/quantum-hft") or ROOT.resolve()!=ROOT:
        raise ValueError("WRONG_WORKING_DIRECTORY")
    seal=json.loads((E/"summary/completion_manifest.json").read_text())
    if seal["status"]!="PHASE 2E PASS":raise ValueError("PHASE2E_NOT_PASS")
    expected=json.loads((E/"summary/input_integrity_before.json").read_text())
    expected.update({str(E/name):saved for name,saved in seal["artifact_files_excluding_this_manifest"].items()})
    expected.update({str(ROOT/name):saved for name,saved in json.loads((E/"summary/code_manifest.json").read_text()).items()})
    expected[seal["report"]["path"]]={k:seal["report"][k] for k in ("sha256","size_bytes")}
    actual={}
    for name,saved in expected.items():
        actual[name]=fingerprint(name)
        if actual[name]!=saved:raise ValueError("INPUT_HASH_MISMATCH: "+name)
    actual[str(E/"summary/completion_manifest.json")]=fingerprint(E/"summary/completion_manifest.json")
    return actual

def generator_version():
    files=[*sorted((ROOT/"data_pipeline/datasets").glob("*.py")),Path(__file__)]
    evidence={str(p.relative_to(ROOT)):fingerprint(p) for p in files}
    digest=hashlib.sha256(json.dumps(evidence,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return "phase2f-packager-v1/sha256:"+digest,evidence

def fileset(root):
    return {p.relative_to(root).as_posix():fingerprint(p) for p in sorted(Path(root).rglob("*")) if p.is_file()}

class Tee:
    def __init__(self,terminal,file):self.terminal,self.file=terminal,file
    def write(self,text):self.terminal.write(text);self.file.write(text);self.file.flush()
    def flush(self):self.terminal.flush();self.file.flush()

def test_result(run):
    command=[sys.executable,"-B","-m","unittest",*TESTS];start=time.monotonic()
    r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,check=False)
    for name,text in (("tests.stdout.txt",r.stdout),("tests.stderr.txt",r.stderr)):
        with (run/"logs"/name).open("x",encoding="utf-8") as f:f.write(text)
    def number(pattern):
        match=re.search(pattern,r.stderr);return int(match[1]) if match else 0
    count=number(r"Ran ([0-9]+) tests?")
    fails,errors,skipped=(number(pattern) for pattern in (r"failures=([0-9]+)",r"errors=([0-9]+)",r"skipped=([0-9]+)"))
    return {"command":command,"tests":count,"pass":count-fails-errors-skipped,"fail":fails,
            "error":errors,"skipped":skipped,"duration_seconds":round(time.monotonic()-start,6),
            "exit_code":r.returncode,"stdout_path":"logs/tests.stdout.txt","stderr_path":"logs/tests.stderr.txt"}

def make_report(run_id,roots,results,validations,tests,comparison,integrity,command,version):
    lines=["# Phase 2F：Dataset v1 封裝、契約封存與鎖定","",
           "**PHASE 2F PASS**。DATASET_RUN_ID："+run_id,"",
           "Phase2E 20261026T195329Z 已由使用者人工審核批准。前置驗證先比對既有 seal、split/policy SHA、C/D outputs及HFT九來源；通過後才建立本run與Dataset。",
           "本次只用Python標準函式庫。generator_version："+version+"；Git commit=NOT_AVAILABLE，程式/測試SHA另存summary/code_manifest.json。","",
           "## Dataset 與版本","",
           "| family | dataset_id | feature version | label version | dataset tree hash |",
           "| --- | --- | --- | --- | --- |"]
    for line,value in results.items():
        lines.append(f"| {line} | {value['dataset_id']} | {value['feature_view']} | 1.0 | {value['dataset_tree_hash']} |")
    lines+=["","兩條研究線獨立封裝；Replay1000只在來源證據中保留SMOKE/REFERENCE定位，沒有正式membership。",
             "每個family有100/200/500/1000ms各自train/validation/test/final_holdout.csv；"
             "root的train/validation/test/final_holdout目錄只放對應horizon manifest，不重複複製大型資料。",
             "Feature schema、Label schema逐位元封存；沒有重定義公式。"
             "Dataset row固定欄序為sample_id +完整Feature columns+去除重複identity後的Label columns；"
             "Label invalid_reason別名為label_invalid_reason，來源欄位對應存於dataset_schema.json。","",
             "## 凍結政策、Sample ID 與 Holdout","",
             "Aggregate match error沿用各horizon1ms；Depth沿用0ms。"
             "Split、actual-target purge、embargo=0及walk-forward均封存Phase2E結果，沒有重新選threshold或membership。",
             "sample_id為metadata canonical JSON的SHA-256：feature_view/source_id/session_id/record_index/event_time_ms；"
             "整數metadata型別固定，UTF-8、key排序、compact separators。"
             "不含future return、target time、split、horizon或execution time。"
             "同View同事件跨horizon共用ID是預期設計；唯一性按每個horizon跨所有split檢查；不同View的ID不同。",
             "Final Holdout仍為LOCKED，model_access_policy=PROHIBITED_UNTIL_FINAL_EVALUATION；"
             "hyperparameter/feature/threshold/scaler/quantum-map/QAOA選擇旗標均false。"
             "依使用者在本對話的明確答覆，Holdout只封存原值與筆數；return分布標記NOT_COMPUTED_HOLDOUT_LOCKED。"
             "沒有計算Holdout accuracy、F1、return統計或model score。",
             "Scaler policy照存，未fit亦未產生參數。Phase3需另批准：scaler.fit(Train)，Validation/Test/Holdout transform only；"
             "不同View使用不同scaler。不同horizon共用前須明定Train Feature fit universe，禁止用Holdout統計參數。","",
             "## 各 Horizon/Split 封裝列數","",
             "| family | horizon ms | Train | Validation | Test | Final Holdout |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for line,value in results.items():
        for h in map(str,HORIZONS):
            row=value["row_counts"][h]
            lines.append(f"| {line} | {h} | {row['train']} | {row['validation']} | {row['test']} | {row['final_holdout']} |")
    lines+=["","所有count逐一對上Phase2E final_rows。invalid、match-error rejected、purged row不入正式CSV；"
             "quality_report仍保留raw candidate、valid、rejected、purged與packaged counts。",
             "quality_report分View/Horizon/Split記錄duplicate ID、collision、缺失欄、invalid feature與duplicate timestamp。"
             "合法未知CSV first/final update ID空值保留並計數，沒有以NaN掩蓋invalid label。"
             "Train/Validation/Test的continuous return僅作描述性count/min/max/mean/median/quantiles，未改任何policy；Holdout不計算。","",
             "## Validator、單元測試與確定性","",
             f"Unit tests：{tests['tests']}，PASS={tests['pass']}，FAIL={tests['fail']}，ERROR={tests['error']}，skipped={tests['skipped']}，exit={tests['exit_code']}，duration={tests['duration_seconds']}s。人工fixture暫存只在tests/fixtures/phase2f/。",
             "正式及第二次完整封裝均執行Dataset Validator：manifest/schema/source hash、exact Feature/Label字串join、"
             "Phase2E membership、actual target、match error、purge、row counts、sample ID與跨split event皆通過。"
             "並掃描固定檔案清單、raw HFT/JSONL/ELF/.env/credential pattern、local_timestamp/class/model/scaler參數，沒有禁止項目。",
             "每個horizon的duplicate sample IDs=0、sample ID collision=0、split overlap=0；"
             "跨horizon相同ID對應同一metadata，沒有誤算為duplicate。",
             f"確定性：{comparison['status']}。第二次輸出保留在artifacts/phase2f/{run_id}/determinism/repeat/，"
             "沒有覆寫正式Dataset；比較row counts、column order、每split/horizon SHA、所有manifest、quality、README、checksums及tree hash。","",
             "## Checksums、契約及完整性","",
             "checksums.sha256涵蓋root內全部正式檔案，排除自身；relative POSIX paths穩定排序。"
             "dataset_tree_hash是排序後'<file_sha256>  <relative path> LF'的SHA-256；"
             "dataset_manifest.json以dataset_tree_hash=null的canonical JSON計算該項digest，明確解決self-reference；checksums仍涵蓋最終manifest實際bytes。",
             "HFT_INPUT_DATA_CONTRACT.md與timestamp_policy.json逐位元封存歷史規格；其中SPECIFICATION_ONLY/null保留原樣，"
             "正式Dataset以已批准Phase2E政策為準。source_files.json記錄九HFT來源path/SHA/size/session/time/audit_status與C/D/E derived-input角色，沒有複製HFT raw CSV、Snapshot、Replay JSONL或src/results。",
             f"開始/完成完整性：{integrity['status']}，{integrity['file_count']}個受保護檔案SHA/size不變。"
             "涵蓋9個HFT來源、Phase2C Features、Phase2D Labels、Phase2E完整封存及既有程式。","",
             "## 新增檔案、命令與停止點",""]
    for line,path in roots.items():lines.append("- "+line+"："+str(path))
    lines+=["- 本輪code/test版本見summary/code_manifest.json；全部新增檔案清單及SHA於收尾summary/completion_manifest.json封存。",
            "- 各Dataset正式檔案完整清單見checksums.sha256。","",
            "正式命令：","", "    "+" ".join(command),"",
            "單元測試命令：","", "    "+" ".join(tests["command"]),"",
            "完整stdout/stderr/exit code與第二次比較見logs/及determinism/；"
            "開發命令另封存logs/development_commands.json，收尾命令保留於Codex原始工具紀錄。",
            "沒有local_timestamp、class label、scaler fit、模型訓練、hyperparameter search、回測、Paper Trading、Quantum Kernel/QSVC/QUBO/QAOA、HFT binary、網路或交易。"
            "網路聲明限本次執行命令，非全機流量稽核。",
            "本報告所有結果均由本輪實際輸出驗證，沒有虛構。"
            "建議人工審核Dataset契約、各family的regime差異及Holdout限制後另行批准Phase3；本次已停止，未進入Phase3。",""]
    return "\n".join(lines)

def execute(run_id):
    before=preflight()
    validate_run_id(run_id)
    roots={line:safe_output(ROOT/"artifacts/datasets"/dataset_id(view,run_id))
           for line,view in (("aggregate","aggregate_core_v1"),("depth","depth_top5_v1"))}
    run=safe_output(ROOT/"artifacts/phase2f"/run_id)
    report=safe_output(ROOT/"docs"/f"PHASE2F_REPORT_{run_id}.md")
    for path in (*roots.values(),run,report):
        if os.path.lexists(path):raise FileExistsError("PLANNED_OUTPUT_EXISTS: "+str(path))
    for parent in (run.parent,ROOT/"artifacts/datasets"):
        safe_output(parent).mkdir(exist_ok=True)
    run.mkdir(exist_ok=False)
    for name in ("logs","summary","validation","determinism"):(run/name).mkdir(exist_ok=False)
    oldout,olderr=sys.stdout,sys.stderr
    out=(run/"logs/stdout.txt").open("x",encoding="utf-8")
    err=(run/"logs/stderr.txt").open("x",encoding="utf-8")
    sys.stdout,sys.stderr=Tee(oldout,out),Tee(olderr,err)
    command=[sys.executable,"-B","tools/package_dataset.py","--run-id",run_id]
    start=utc();tests=None
    try:
        write_json(run/"summary/input_integrity_before.json",before)
        write_json(run/"summary/user_holdout_statistics_decision.json",{
            "decision":"僅封存 Holdout 原值與筆數，return 分布標記 NOT_COMPUTED_HOLDOUT_LOCKED",
            "source":"direct human reply in this Codex conversation",
            "request_id":"call_23570cf2911d4a32a5ee37e6146e0399"})
        tests=test_result(run);write_json(run/"summary/test_results.json",tests)
        if tests["exit_code"] or not tests["tests"]:raise RuntimeError("PHASE2F_UNIT_TESTS_FAILED")
        version,programs=generator_version()
        ctx=context();results={};validations={}
        for line,path in roots.items():
            results[line]=package_family(ctx,line,run_id,path,version)
            validations[line]=validate_dataset(path,ctx,line)
            write_json(run/"validation"/(line+".json"),validations[line])
            if validations[line]["status"]!="PASS":raise RuntimeError("DATASET_VALIDATION_FAIL: "+line)
        replica=run/"determinism/repeat";replica.mkdir(exist_ok=False)
        comparisons={}
        for line,formal in roots.items():
            duplicate=replica/formal.name
            second=package_family(ctx,line,run_id,duplicate,version)
            check=validate_dataset(duplicate,ctx,line)
            write_json(run/"validation"/(line+"_repeat.json"),check)
            first_files,second_files=fileset(formal),fileset(duplicate)
            changed=[name for name in set(first_files)|set(second_files) if first_files.get(name)!=second_files.get(name)]
            same=(not changed and results[line]["row_counts"]==second["row_counts"]
                  and results[line]["dataset_tree_hash"]==second["dataset_tree_hash"] and check["status"]=="PASS")
            comparisons[line]={"status":"PASS" if same else "NON_DETERMINISTIC_DATASET",
                               "changed_files":sorted(changed),"compared_files":len(first_files),
                               "formal_files":first_files,"repeat_files":second_files,
                               "dataset_tree_hash":second["dataset_tree_hash"],"row_counts_equal":results[line]["row_counts"]==second["row_counts"]}
            if not same:raise RuntimeError("NON_DETERMINISTIC_DATASET")
        comparison={"status":"PASS","families":comparisons}
        write_json(run/"determinism/comparison.json",comparison)
        after={path:fingerprint(path) for path in before}
        write_json(run/"summary/input_integrity_after.json",after)
        integrity={"status":"PASS" if before==after else "FAIL","file_count":len(before),
                   "changed_inputs":[p for p in before if before[p]!=after[p]],"hft_sources":9,
                   "phase2c_features":9,"phase2d_labels":36,"phase2e_artifacts":"ALL_SEALED_FILES"}
        write_json(run/"summary/input_integrity_comparison.json",integrity)
        if before!=after:raise RuntimeError("INPUT_INTEGRITY_CHANGED")
        testfiles=[ROOT/(name.replace(".","/")+".py") for name in TESTS]
        testfiles.extend(sorted((ROOT/"tests/fixtures/phase2f").glob("*.py")))
        allprograms={**programs,**{str(p.relative_to(ROOT)):fingerprint(p) for p in testfiles}}
        write_json(run/"summary/code_manifest.json",allprograms)
        with report.open("x",encoding="utf-8",newline="") as f:
            f.write(make_report(run_id,roots,results,validations,tests,comparison,integrity,command,version))
        summary={"status":"PHASE 2F PASS","dataset_run_id":run_id,"tests":tests,
                 "datasets":{k:{key:v[key] for key in ("dataset_id","feature_view","dataset_tree_hash","row_counts")} for k,v in results.items()},
                 "validation":validations,"determinism":"PASS","integrity":integrity,
                 "holdout_status":"LOCKED","holdout_return_statistics":HOLDOUT_STATS_STATUS,
                 "local_timestamp":False,"class_labels":False,"scaler_fitted":False,
                 "models_trained":False,"network":False,"trading":False,"backtest":False,
                 "phase3_started":False,"report":str(report)}
        write_json(run/"summary/run_summary.json",summary)
        write_json(run/"logs/execution.json",{"command":command,"cwd":str(ROOT),"started_at_utc":start,
                   "finished_at_utc":utc(),"exit_code":0,"stdout_path":"logs/stdout.txt","stderr_path":"logs/stderr.txt",
                   "subcommands":[tests]})
        print(json.dumps({"status":"PHASE 2F PASS","dataset_run_id":run_id,"report":str(report),
                          "tree_hashes":{k:v["dataset_tree_hash"] for k,v in results.items()}}),flush=True)
        return 0
    except Exception as exc:
        failure={"status":"PHASE 2F FAIL","dataset_run_id":run_id,"error":repr(exc),"traceback":traceback.format_exc()}
        write_json(run/"summary/failure.json",failure)
        write_json(run/"logs/execution.json",{"command":command,"cwd":str(ROOT),"started_at_utc":start,
                   "finished_at_utc":utc(),"exit_code":1,"stdout_path":"logs/stdout.txt","stderr_path":"logs/stderr.txt",
                   "subcommands":[tests] if tests else []})
        if not report.exists():
            with report.open("x",encoding="utf-8") as f:f.write("# PHASE 2F FAIL\n\n"+json.dumps(failure,ensure_ascii=False,indent=2)+"\n")
        print(json.dumps(failure),file=sys.stderr,flush=True)
        return 1
    finally:
        sys.stdout,sys.stderr=oldout,olderr;out.close();err.close()

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id",required=True)
    return execute(parser.parse_args(argv).run_id)

if __name__=="__main__":raise SystemExit(main())
