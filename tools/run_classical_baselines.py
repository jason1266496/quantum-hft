"""Phase 3A only: four classical baselines, two horizons, and a sealed Test gate."""
import argparse,json,os,platform,re,subprocess,sys,time,traceback
from datetime import datetime,timezone
from pathlib import Path
for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[name]="1"
os.environ["PYTHONDONTWRITEBYTECODE"]="1"
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from experiments.classical.runner import (dependencies,protected_preflight,scoped_validate,
   experiment,DATASET,DATASET_ID,OLD_FAIL_ID,PYTHON,HORIZONS,Tee,utc)
from models.classical import feature_policy,label_policy
from models.classical.registry import write_json,safe_output,sha
from data_pipeline.datasets.checksums import fingerprint,verify_checksums
TESTS=("tests.test_classification_policy","tests.test_classical_feature_policy","tests.test_train_only_scaler",
       "tests.test_obi_rule","tests.test_logistic_pipeline","tests.test_linear_svm_pipeline",
       "tests.test_rbf_svm_pipeline","tests.test_classical_metrics","tests.test_model_selection",
       "tests.test_kernel_subset","tests.test_test_seal","tests.test_run_classical_baselines")

def tests(run):
    command=[sys.executable,"-B","-m","unittest",*TESTS];start=time.perf_counter()
    value=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,check=False)
    for name,text in (("tests.stdout.txt",value.stdout),("tests.stderr.txt",value.stderr)):
        with (run/"logs"/name).open("x",encoding="utf-8") as f:f.write(text)
    def count(pattern):
        match=re.search(pattern,value.stderr);return int(match[1]) if match else 0
    total=count(r"Ran ([0-9]+) tests?");failed=count(r"failures=([0-9]+)");errors=count(r"errors=([0-9]+)");skips=count(r"skipped=([0-9]+)")
    return {"command":command,"tests":total,"pass":total-failed-errors-skips,"fail":failed,"error":errors,
            "skipped":skips,"exit_code":value.returncode,"duration_seconds":time.perf_counter()-start,
            "stdout_path":"logs/tests.stdout.txt","stderr_path":"logs/tests.stderr.txt"}

def environment(run_id,deps,validation):
    cpu="NOT_AVAILABLE"
    for line in Path("/proc/cpuinfo").read_text().splitlines():
        if line.startswith("model name"):cpu=line.split(":",1)[1].strip();break
    memory={line.split(":",1)[0]:line.split(":",1)[1].strip() for line in Path("/proc/meminfo").read_text().splitlines()}
    return {"run_id":run_id,"python":sys.version,"python_executable":sys.executable,
            "dependencies":deps["modules"],"verified_imports":deps["imports"],
            "os":platform.platform(),"kernel":platform.release(),"cpu":cpu,"logical_cores":os.cpu_count(),
            "ram_MemTotal":memory.get("MemTotal","NOT_AVAILABLE"),"working_directory":str(ROOT),
            "dataset_ids":[DATASET_ID],"dataset_tree_hashes":{"aggregate":validation["checksums"]["dataset_tree_hash"]},
            "thread_environment":{name:os.environ.get(name) for name in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS")},
            "packages_installed":False,"model_inference_timing":"Python batch; no HFT latency claim"}

def make_report(run_id,result,test,env,validation,integrity,command):
    lines=["# Phase 3A：Classical Baseline、固定分類與 Kernel Comparison Subset","",
       "**PHASE 3A PASS**。run_id："+run_id,"",
       "本次為全新執行，沒有沿用舊 FAIL 的未完成結果。舊run 20261026T205307Z永久保留PHASE3A FAIL／DEPENDENCY_MISSING，舊run與報告SHA均保持。",
       "依使用者Dependency Recheck的條件式授權，指定venv全部imports通過後重啟完整Phase3A。"
       "另獲明確批准採受限Dataset驗證：封存Phase2F正式Validator PASS＋重驗全部SHA/tree＋本輪允許資料檢查；"
       "既有全量Validator未重跑，以避免解析Holdout值。","",
       "## Dataset、Environment 與固定政策","",
       "Dataset："+DATASET_ID+"；tree hash："+validation["checksums"]["dataset_tree_hash"]+"。",
       "Python executable："+env["python_executable"]+"；"+env["python"],
       "套件版本："+json.dumps({k:v["version"] for k,v in env["dependencies"].items()},sort_keys=True)+"。",
       "OS："+env["os"]+"；CPU："+env["cpu"]+"；logical cores："+str(env["logical_cores"])+"；RAM MemTotal："+env["ram_MemTotal"]+"。",
       "BLAS/OpenMP相關threads固定1；Python random、NumPy、支援API的random_state均42。"
       "LBFGS／primal LinearSVC／無probability的SVC在本pipeline為deterministic設定；時間測量本身不要求逐次相同。",
       "Classification：direction_3class_exact_v1；Decimal原始return <0→DOWN=0、==0→FLAT=1、>0→UP=2，沒有epsilon、buffer或cost threshold。"
       "這是分類研究baseline，不是最終交易entry threshold；成本感知規則留待另行研究。",
       "Feature policy：aggregate_compact_v1，固定順序obi_5、spread_bps、bid_volume_5、ask_volume_5。"
       "模型輸入僅這4欄的float64；metadata、ID、event time、future label與match error沒有作特徵，沒有Feature Selection。",
       "只跑Aggregate 100ms/1000ms；沒有200ms、500ms、Depth模型、Quantum Kernel/QSVC/QUBO/QAOA。",
       "OBI規則：原始Decimal obi>=+0.6→UP、<=-0.6→DOWN，其餘FLAT；固定且不使用scaler。",
       "Logistic：balanced，C=[0.1,1,10]，LBFGS max_iter=5000；LinearSVC：balanced，C=[0.1,1,10]，primal dual=False、max_iter=20000。"
       "RBF：只用kernel_comparison_subset_v1，C=[1,10]×gamma=[scale,0.1]，balanced、probability=False。",
       "每horizon獨立fit Full Train scaler供Logistic/Linear使用；RBF另只fit該horizon Subset Train scaler。"
       "Validation/Test僅transform，Holdout完全不transform。各model/scaler.json保存mean/scale/var/n_samples_seen、fit sample-ID SHA及feature order，config保存artifact SHA。","",
       "## Class distribution：DOWN／FLAT／UP","",
       "| H | split | DOWN | FLAT | UP | percentages DOWN/FLAT/UP |",
       "| --- | --- | ---: | ---: | ---: | --- |"]
    warnings=[]
    for h,data in result["class_distributions"].items():
        for split,d in data.items():
            c=d["counts"];p=d["percentages"]
            lines.append(f"| {h} | {split} | {c['DOWN']} | {c['FLAT']} | {c['UP']} | {p['DOWN']:.6f}/{p['FLAT']:.6f}/{p['UP']:.6f} |")
            if d["warnings"]:warnings.append({"horizon":h,"scope":"full","split":split,"warnings":d["warnings"]})
    lines+=["","所有FLAT與零return樣本都保留；Train若任何class為0立即FAIL，<1%只標warning，不刪類別。"
             "Test class distribution在全部8個selection manifest封存後才計算，沒有用於選政策。","",
             "## Validation selection 與正式 Test 結果","",
             "Primary為Validation Macro-F1；tie-break Balanced Accuracy，其後較小C；RBF同分先gamma=scale再較小C。"
             "以下Test分數只屬各模型自己的dataset scope，Full與Kernel Subset不能宣稱完全公平的頭對頭比較。",
             "| H | model | scope | selected config | Val Macro-F1 | Val BA | Test Macro-F1 | Test BA | Test Accuracy |",
             "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |"]
    for key,m in result["models"].items():
        v,t=m["validation_metrics"],m["test_metrics"]
        lines.append(f"| {m['horizon_ms']} | {m['model']} | {m['dataset_scope']} | {json.dumps(m['selected_config'],sort_keys=True)} | {v['macro_f1']:.9f} | {v['balanced_accuracy']:.9f} | {t['macro_f1']:.9f} | {t['balanced_accuracy']:.9f} | {t['accuracy']:.9f} |")
    lines+=["","每個model有Validation/Test metrics、三類confusion_matrix.csv、per_class_metrics.csv、support與prediction CSV。"
             "Accuracy為全樣本，沒有用conditional direction accuracy取代。",
             "",
             "## Kernel Subset 與 Test Seal","",
             "Train最多1000、Validation/Test最多500；按event time穩定排序，用floor(i*(N-1)/(k-1)) evenly-spaced positions，包含頭尾，不shuffle或看class選樣。"
             "Train/Validation subset先固定；Test positions只由已封存row count固定，直到全部selection seals完成後才讀Test資料並保存IDs／class distribution。"
             "每split保留selected sample_ids、event range、indices SHA與subset SHA。"
             "Phase4 Quantum Kernel/QSVC應沿用同membership及Train scaler universe，才能與RBF公平比較。"]
    for h,sub in result["kernel_subsets"].items():
        sizes={k:v["selected_rows"] for k,v in sub.items()}
        lines.append("- "+h+"ms subset："+json.dumps(sizes,sort_keys=True)+"。")
        if sub["Train"]["class_distribution_after_selection"]["warnings"]:
            warnings.append({"horizon":h,"scope":"kernel_comparison_subset_v1","split":"Train",
                             "warnings":sub["Train"]["class_distribution_after_selection"]["warnings"]})
    lines+=["","Test seal：全部8份selection_manifest.json在任何Test label read前封存並計算SHA；各檔test_evaluated=false的選擇時狀態保留不改。"
             "Global barrier SHA連結selection seals；Test結果另存test_evaluation_manifest.json，每model metric_evaluation_count=1。"
             "Test prediction warm-up 1次＋正式3次只作timing，三次prediction相同；metrics僅計算一次，沒有Test retuning。"
             "Dataset access log記錄兩個horizon Test labels讀取皆在barrier之後。",
             "Final Holdout：LOCKED，FINAL_HOLDOUT_NOT_EVALUATED。僅存在、header/schema、row count、checksum檢查；沒有Holdout feature/label值解析、transform、class distribution、score或diagnostics。","",
             "## Timing 與 Class Imbalance","",
             "| H | model | fit wall s | Test prediction rows | Test predict median s | rows/sec |",
             "| --- | --- | ---: | ---: | ---: | ---: |"]
    for m in result["models"].values():
        t=m["timing"];p=t["test_predict"]
        lines.append(f"| {m['horizon_ms']} | {m['model']} | {t['fit_wall_seconds']:.9f} | {p['prediction_rows']} | {p['median_wall_seconds']:.9f} | {p['rows_per_second']:.3f} |")
    lines+=["","這是time.perf_counter量測的Python batch inference wall time，包含各次predict呼叫；不是microsecond HFT latency，也不是deployment latency。"
             "資料轉換／scaler與模型fit universe記錄獨立；timing.json另存Validation prediction、候選fit總耗時及Test三次測量。",
             "Class imbalance warnings："+json.dumps(warnings,ensure_ascii=False,sort_keys=True)+"。","",
             "## 測試、Integrity 與限制","",
             f"人工fixture unit tests：{test['tests']}，PASS={test['pass']}，FAIL={test['fail']}，ERROR={test['error']}，skipped={test['skipped']}，exit={test['exit_code']}，wall={test['duration_seconds']:.6f}s。",
             f"開始/完成{integrity['file_count']}個受保護檔案SHA/size一致；包括Dataset v1、HFT九來源、舊Phase及舊FAIL證據。"
             "Dataset tree hash與Phase2F checksums一致，沒有重新切split、改match threshold/purge/continuous labels或解鎖Holdout。",
             "沒有安裝/移除/升級套件、網路／Binance/Testnet、真實交易、HFT binary、回測、Paper Trading或Quantum模型。"
             "本次網路聲明限執行命令，非全機封包量測。",
             "限制：類別失衡、重疊label依賴與跨月份regime差異仍存在；單次Test只作凍結規格檢查，不證明獲利。"
             "Full模型與RBF subset score只按scope分列；沒有因此修改候選、政策或membership。",
             "模型pickle只保存本run自己建立的物件與SHA，沒有載入外部pickle，也未批准部署。",
             "Phase3B可在人工審核後另行規劃穩健性/研究規格；Phase4原型應優先用本次同kernel subset，"
             "都需要下一次明確批准。本次未進入Phase3B/4，也沒有虛構任何結果。","",
             "## 命令與證據","",
             "正式命令：","", "    "+" ".join(command),"",
             "測試命令：","", "    "+" ".join(test["command"]),"",
             "Environment、policies、selection/Test seals、class distributions、comparison、timing、完整stdout/stderr/exit在本run封存。"
             "程式/測試SHA見summary/code_manifest.json；開發與dependency recheck命令見logs/development_commands.json；"
             "完整新增檔案及最後完整性見summary/completion_manifest.json。",""]
    return "\n".join(lines)

def execute(run_id,scoped_approved=False):
    if not scoped_approved:raise ValueError("SCOPED_VALIDATION_REQUIRES_EXPLICIT_USER_APPROVAL")
    if run_id==OLD_FAIL_ID or not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z",run_id):raise ValueError("INVALID_OR_RESERVED_RUN_ID")
    datetime.strptime(run_id,"%Y%m%dT%H%M%SZ")
    deps=dependencies();before=protected_preflight();validation=scoped_validate()
    run=safe_output(ROOT/"artifacts/phase3a"/run_id)
    report=safe_output(ROOT/"docs"/f"PHASE3A_REPORT_{run_id}.md")
    if os.path.lexists(run) or os.path.lexists(report):raise FileExistsError("RUN_OR_REPORT_EXISTS")
    run.mkdir(exist_ok=False)
    for name in ("policy","environment","comparison","timing","logs","summary"):(run/name).mkdir(exist_ok=False)
    stdout,stderr=sys.stdout,sys.stderr
    out=(run/"logs/stdout.txt").open("x",encoding="utf-8");err=(run/"logs/stderr.txt").open("x",encoding="utf-8")
    sys.stdout,sys.stderr=Tee(stdout,out),Tee(stderr,err)
    command=[sys.executable,"-B","tools/run_classical_baselines.py","--run-id",run_id,"--scoped-validation-approved"]
    started=utc();test=None
    try:
        write_json(run/"environment/dependency_recheck.json",deps)
        write_json(run/"environment/dataset_validation.json",validation)
        write_json(run/"policy/scoped_validation_approval.json",{"approved":True,"source":"direct human reply in this conversation",
          "request_id":"call_5662f59e3e9e42068f14dbbad403a516","answer":"採用受限驗證並繼續（建議）"})
        write_json(run/"summary/input_integrity_before.json",before)
        env=environment(run_id,deps,validation);write_json(run/"environment/environment.json",env)
        test=tests(run);write_json(run/"summary/test_results.json",test)
        if test["exit_code"] or not test["tests"]:raise ValueError("PHASE3A_TESTS_FAILED")
        write_json(run/"policy/classification_policy.json",label_policy.policy())
        write_json(run/"policy/feature_policy.json",feature_policy.policy())
        write_json(run/"policy/random_seed_policy.json",{"python_random":42,"numpy_seed":42,"api_random_state":42,
                   "thread_count":1,"no_random_subset_sampling":True})
        write_json(run/"policy/scaler_policy.json",{"fit_split":"Train","separate_horizon_scalers":True,
                   "full_scaler_shared_by":["logistic","linear_svm"],"rbf_scaler_fit_universe":"kernel subset Train only",
                   "obi_scaler":False,"validation_test":"transform only","holdout":"no access or transform"})
        result=experiment(run)
        after={p:fingerprint(p) for p in before}
        write_json(run/"summary/input_integrity_after.json",after)
        integrity={"status":"PASS" if before==after else "FAIL","file_count":len(before),
                   "changed_files":[p for p in before if before[p]!=after[p]],
                   "old_fail_run_id":OLD_FAIL_ID,"old_fail_remains":"PHASE 3A FAIL",
                   "dataset_tree_after":verify_checksums(DATASET)["dataset_tree_hash"],"hft_sources":9}
        write_json(run/"summary/input_integrity_comparison.json",integrity)
        if before!=after:raise ValueError("PROTECTED_INPUT_CHANGED")
        code=[*sorted((ROOT/"models/classical").glob("*.py")),*sorted((ROOT/"experiments/classical").glob("*.py")),Path(__file__),
              *(ROOT/(name.replace(".","/")+".py") for name in TESTS),
              *sorted((ROOT/"tests/fixtures/phase3a").glob("*.py"))]
        write_json(run/"summary/code_manifest.json",{str(p.relative_to(ROOT)):fingerprint(p) for p in code})
        write_json(run/"summary/model_registry.json",{key:{"config":value["config"],"selection_sha256":value["selection_sha256"],
                   "deployment_status":"NOT_APPROVED_FOR_DEPLOYMENT"} for key,value in result["models"].items()})
        with report.open("x",encoding="utf-8") as f:f.write(make_report(run_id,result,test,env,validation,integrity,command))
        summary={"status":"PHASE 3A PASS","run_id":run_id,"dataset_id":DATASET_ID,
                 "dataset_tree_hash":validation["checksums"]["dataset_tree_hash"],"dependency_recheck":"PASS",
                 "python_executable":sys.executable,"sklearn_version":deps["modules"]["sklearn"]["version"],
                 "tests":test,"results":result,"integrity":integrity,"old_fail_preserved":True,
                 "final_holdout":"FINAL_HOLDOUT_NOT_EVALUATED","holdout_values_parsed":False,
                 "network":False,"trading":False,"backtest":False,"quantum_models":False,
                 "phase3b_started":False,"phase4_started":False,"report":str(report)}
        write_json(run/"summary/run_summary.json",summary)
        write_json(run/"logs/execution.json",{"command":command,"cwd":str(ROOT),"started_at_utc":started,
                   "finished_at_utc":utc(),"exit_code":0,"stdout_path":"logs/stdout.txt","stderr_path":"logs/stderr.txt",
                   "subcommands":[test]})
        print(json.dumps({"status":"PHASE 3A PASS","run_id":run_id,"report":str(report),
                          "test_evaluations":result["test_gate"]["test_evaluations"]}),flush=True)
        return 0
    except Exception as exc:
        failure={"status":"PHASE 3A FAIL","run_id":run_id,"error":repr(exc),"traceback":traceback.format_exc()}
        write_json(run/"summary/failure.json",failure)
        write_json(run/"logs/execution.json",{"command":command,"cwd":str(ROOT),"started_at_utc":started,
                   "finished_at_utc":utc(),"exit_code":1,"stdout_path":"logs/stdout.txt","stderr_path":"logs/stderr.txt",
                   "subcommands":[test] if test else []})
        if not report.exists():
            with report.open("x",encoding="utf-8") as f:f.write("# PHASE 3A FAIL\n\n"+json.dumps(failure,ensure_ascii=False,indent=2)+"\n")
        print(json.dumps(failure),file=sys.stderr,flush=True)
        return 1
    finally:
        sys.stdout,sys.stderr=stdout,stderr;out.close();err.close()

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-id",required=True);p.add_argument("--scoped-validation-approved",action="store_true")
    a=p.parse_args(argv);return execute(a.run_id,a.scoped_validation_approved)
if __name__=="__main__":raise SystemExit(main())
