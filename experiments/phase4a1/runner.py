"""Fixed Smoke -> Prototype -> mandatory repeat, with no Test path or retuning."""
import contextlib,importlib.metadata as md,json,os,platform,random,re,resource,subprocess,sys,time,traceback,warnings
from pathlib import Path
import numpy as np
from sklearn.svm import SVC
from sklearn.exceptions import ConvergenceWarning
from qiskit_machine_learning.algorithms import QSVC
from .contracts import ROOT,BUDGET,PYTHON,FEATURES,NAMES,fp,read,write,write_csv,save_array,safe,sha,array_sha,load_profile,verify_budget,integrity
from .preprocessing import verify_profile,FORMULA_ATOL,FORMULA_RTOL
from .kernel import compute,validate,NUMERICAL_ATOL,DETERMINISM_ATOL,DETERMINISM_RTOL
from .metrics import score,distribution,close_tree
TESTS=("tests.test_phase4a1_contracts","tests.test_phase4a1_preprocessing","tests.test_phase4a1_kernel","tests.test_phase4a1_metrics","tests.test_phase4a1_runner")
def config():
    return {"phase":"4A-1","horizon_ms":1000,"feature_view":"aggregate_core_v1","feature_order":list(FEATURES),
        "label_policy":"direction_3class_exact_v1","seed":42,"budgets":{"smoke":{"Train":24,"Validation":24},"prototype":{"Train":96,"Validation":96}},
        "RBF":{"kernel":"rbf","C":100.0,"gamma":.01,"class_weight":"balanced","probability":False,"random_state":42},
        "QSVC":{"C":100.0,"class_weight":"balanced","probability":False,"random_state":42,
                "quantum_kernel":"precomputed","matrix_generator":"FidelityStatevectorKernel"},
        "circuit":{"feature_dimension":4,"qubits":4,"reps":1,"entanglement":"linear","alpha":2.,"shots":None},
        "enforce_psd":False,"kernel_repair":False,"new_preprocessing_fit":False,
        "preprocessing":"exact Frozen shared angles; verify fixed Train-only formula, clipping and constant pi/2; never refit",
        "numerical_atol":NUMERICAL_ATOL,"formula_atol":FORMULA_ATOL,"formula_rtol":FORMULA_RTOL,
        "determinism_matrix_atol":DETERMINISM_ATOL,"determinism_matrix_rtol":DETERMINISM_RTOL,
        "determinism_metric_atol":1e-12,"determinism_metric_rtol":1e-12,
        "smoke_metrics":"NOT_COMPUTED_FUNCTIONAL_ONLY_DOWN_ABSENT","prototype_repeat_count":1,
        "test_allowed":False,"holdout_allowed":False,"retuning_or_resampling":False,"package_changes_allowed":False,
        "network":False,"QPU":False,"trading":False,"backtest":False,"paper_trading":False}
def models():
    rbf=SVC(**config()["RBF"])
    qsvc=QSVC(quantum_kernel="precomputed",C=100.,class_weight="balanced",probability=False,random_state=42)
    for model in (rbf,qsvc):
        p=model.get_params(deep=False)
        if p["C"]!=100. or p["class_weight"]!="balanced" or p["probability"] is not False or p["random_state"]!=42:raise ValueError("REQUIRED_API_PARAMETER_UNSUPPORTED")
    if rbf.kernel!="rbf" or rbf.gamma!=.01 or qsvc.quantum_kernel!="precomputed":raise ValueError("KERNEL_COMPARISON_CONTRACT_CHANGED")
    return rbf,qsvc
def fitted(model,x,y):
    t=time.perf_counter()
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always");model.fit(x,y)
    records=[{"category":w.category.__name__,"message":str(w.message)} for w in captured]
    if any(issubclass(w.category,ConvergenceWarning) for w in captured):raise ValueError("MODEL_CONVERGENCE_FAILURE")
    return {"wall_seconds":time.perf_counter()-t,"warnings":records}
def predict(model,x):
    t=time.perf_counter();p=np.asarray(model.predict(x),dtype=np.int64);elapsed=time.perf_counter()-t
    if p.shape!=(len(x),) or not set(p.tolist())<={0,1,2}:raise ValueError("INVALID_MODEL_PREDICTIONS")
    return p,elapsed
def stage(source,manifest,profile,folder):
    t=time.perf_counter();b=load_profile(source,profile,manifest);loaded=time.perf_counter()-t
    pre=verify_profile(b);pre["load_and_verify_seconds"]=loaded+pre["wall_seconds"]
    write(folder/"preprocessing_manifest.json",pre)
    tr,va=b["Train"],b["Validation"]
    before_ids={split:{"ids":b[split]["ids"],"file_sha256":b[split]["file_sha256"],"array_sha256":array_sha(b[split]["x"]),
                      "labels_sha256":__import__("hashlib").sha256(b[split]["y"].tobytes()).hexdigest()} for split in ("Train","Validation")}
    tt,vt,circuit,kt=compute(tr["x"],va["x"])
    save_array(folder/"train_kernel.npy",tt);save_array(folder/"validation_kernel.npy",vt)
    checked=validate(tt,vt,len(tr["ids"]),len(va["ids"]))
    write(folder/"kernel_validation.json",checked);write(folder/"circuit_manifest.json",circuit)
    rbf,qsvc=models();rfit=fitted(rbf,tr["x"],tr["y"]);rpred,rseconds=predict(rbf,va["x"])
    qfit=fitted(qsvc,tt.copy(),tr["y"]);qpred,qseconds=predict(qsvc,vt.copy())
    for split in ("Train","Validation"):
        if array_sha(b[split]["x"])!=before_ids[split]["array_sha256"]:raise ValueError("MODEL_MUTATED_SHARED_INPUT")
    result_models={}
    for name,model,pred,fit,pseconds in (("rbf",rbf,rpred,rfit,rseconds),("qsvc",qsvc,qpred,qfit,qseconds)):
        params=model.get_params(deep=False)
        write(folder/(name+"_config.json"),params)
        write_csv(folder/(name+"_predictions.csv"),("sample_id","true_class","predicted_class"),
            [{"sample_id":sid,"true_class":int(va["y"][i]),"predicted_class":int(pred[i])} for i,sid in enumerate(va["ids"])])
        metric=score(va["y"],pred) if profile=="prototype" else None
        if metric is not None:write(folder/(name+"_metrics.json"),metric)
        result_models[name]={"params":params,"predictions":pred.tolist(),"predicted_class_distribution":distribution(pred),
            "metrics":metric,"metrics_scope":"Prototype Validation all three classes" if metric else "NOT_COMPUTED_SMOKE_FUNCTIONAL_ONLY",
            "fit":fit,"predict_seconds":pseconds}
    timing={"preprocessing_seconds":pre["load_and_verify_seconds"],**kt,
        "qsvc_fit_seconds":qfit["wall_seconds"],"qsvc_predict_seconds":qseconds,
        "rbf_fit_seconds":rfit["wall_seconds"],"rbf_predict_seconds":rseconds,
        "qsvc_matrix_plus_fit_predict_seconds":kt["quantum_kernel_train_matrix_seconds"]+kt["quantum_kernel_validation_matrix_seconds"]+qfit["wall_seconds"]+qseconds,
        "rbf_fit_predict_seconds":rfit["wall_seconds"]+rseconds,
        "qsvc_timing_scope":"precomputed QSVC solver only; separate Kernel construction must be included for total cost",
        "rbf_timing_scope":"native RBF SVC includes its internal classical kernel operations",
        "timing_label":"LOCAL_PYTHON_CPU_STATEVECTOR_SIMULATOR_ONLY","QPU_latency_claim":False,"HFT_latency_claim":False,"quantum_speedup_claim":False}
    write(folder/"timing.json",timing)
    summary={"status":"PASS","profile":profile,"rows":{"Train":len(tr["ids"]),"Validation":len(va["ids"])},
        "class_distributions":{"Train":distribution(tr["y"]),"Validation":distribution(va["y"])},
        "input_identity":before_ids,"preprocessing":pre,"kernel_validation":checked,"circuit":circuit,"models":result_models,"timing":timing,
        "no_reused_phase3b_model":True,"sampling_performed":False,"preprocessing_refit":False,"Test_used":False,"Holdout_used":False}
    write(folder/"stage_results.json",summary)
    return summary,{"train_kernel":tt,"validation_kernel":vt}
def compare(first,fa,repeat,ra):
    checks={"input_identity_exact":first["input_identity"]==repeat["input_identity"],
       "train_kernel_allclose":bool(np.allclose(fa["train_kernel"],ra["train_kernel"],atol=DETERMINISM_ATOL,rtol=DETERMINISM_RTOL)),
       "validation_kernel_allclose":bool(np.allclose(fa["validation_kernel"],ra["validation_kernel"],atol=DETERMINISM_ATOL,rtol=DETERMINISM_RTOL))}
    for name in ("rbf","qsvc"):
        a,b=first["models"][name],repeat["models"][name]
        checks[name+"_predictions_exact"]=a["predictions"]==b["predictions"]
        checks[name+"_metrics_allclose"]=close_tree(a["metrics"],b["metrics"])
        checks[name+"_confusion_exact"]=a["metrics"]["confusion_matrix"]==b["metrics"]["confusion_matrix"]
    return {"status":"PASS" if all(checks.values()) else "FAIL","checks":checks,"matrix_atol":DETERMINISM_ATOL,"matrix_rtol":DETERMINISM_RTOL,
        "metric_atol":1e-12,"metric_rtol":1e-12,"train_kernel_max_abs_diff":float(np.max(np.abs(fa["train_kernel"]-ra["train_kernel"]))),
        "validation_kernel_max_abs_diff":float(np.max(np.abs(fa["validation_kernel"]-ra["validation_kernel"]))),
        "input_SHA_exact":checks["input_identity_exact"],"predictions_and_integer_counts_exact_required":True,"matrix_bitwise_identity_required_across_environments":False,
        "timing_identity_required":False,"result_selection_from_repeat":False}
def tests(run):
    code="import sys,unittest;sys.path.insert(0,'/home/jason/quantum-hft');unittest.main(module=None,argv=['unittest',"+",".join(repr(n) for n in TESTS)+"])"
    argv=[sys.executable,"-I","-B","-c",code];t=time.perf_counter();p=subprocess.run(argv,cwd=ROOT,capture_output=True,text=True)
    for name,value in (("tests.stdout.txt",p.stdout),("tests.stderr.txt",p.stderr)):
        with safe(run/"logs"/name).open("x",encoding="utf-8") as f:f.write(value)
    match=re.search(r"Ran (\d+) tests?",p.stderr)
    value={"status":"PASS" if p.returncode==0 and match else "FAIL","tests":int(match[1]) if match else 0,
       "exit_code":p.returncode,"command":argv,"wall_seconds":time.perf_counter()-t,"fixtures_only":True}
    write(run/"summary/unit_tests.json",value)
    if value["status"]!="PASS":raise ValueError("UNIT_TESTS_FAILED")
    return value
def environment():
    if str(Path.cwd())!=str(ROOT) or str(ROOT.resolve())!=str(ROOT) or sys.executable!=PYTHON:raise ValueError("WRONG_WORKDIR_OR_PYTHON")
    versions={p:md.version(p) for p in ("qiskit","qiskit-machine-learning","numpy","scipy","scikit-learn")}
    if versions!={"qiskit":"2.6.1","qiskit-machine-learning":"0.9.1","numpy":"2.5.4","scipy":"1.18.1","scikit-learn":"1.9.1"}:raise ValueError("ENVIRONMENT_VERSION_CHANGED")
    return {"python_executable":sys.executable,"python":sys.version,"versions":versions,"platform":platform.platform(),"kernel":platform.release(),
        "logical_cores":os.cpu_count(),"thread_environment":{k:os.environ.get(k) for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS")},
        "CPU":next((v.split(":",1)[1].strip() for v in Path("/proc/cpuinfo").read_text().splitlines() if v.startswith("model name")),"NOT_AVAILABLE"),
        "RAM_MemTotal":next((v.split(":",1)[1].strip() for v in Path("/proc/meminfo").read_text().splitlines() if v.startswith("MemTotal:")),"NOT_AVAILABLE"),
        "seed":42,"git_commit":"NOT_AVAILABLE; source SHA-256 sealed","packages_changed":False,"network":False}
def report(run,env,smoke,proto,det,timing,integ,unit):
    lines=["# Phase 4A-1：Quantum Kernel + QSVC vs RBF 公平比較原型","",
      "**PHASE 4A-1 PASS**；run_id："+run.name,"",
      "1000ms／aggregate_core_v1，固定四特徵："+", ".join(FEATURES)+"。direction_3class_exact_v1：DOWN0、FLAT1、UP2；Decimal exact zero，FLAT未排除。",
      "只使用Phase4A-0 Frozen Smoke24/24及Prototype96/96，沒有重新抽樣、擴大樣本、搜尋參數、變更Feature Map或角度範圍。","",
      "## 環境與固定模型","",
      json.dumps(env,ensure_ascii=False,indent=2),
      "RBF：C100、gamma0.01、balanced、probability=False、seed42。QSVC：C100、balanced、probability=False、seed42。",
      "量子矩陣由FidelityStatevectorKernel、4-qubit zz_feature_map、linear、reps1、alpha2、shots=None生成，enforce_psd=False；不修補Kernel。QSVC使用官方支援的precomputed模式，模型端輸入矩陣來自同一Frozen四維角度，便於分開計時；未換成其他分類器。",
      "## Frozen前處理與Smoke","",
      "保留原Frozen Train-only StandardScaler與Budget Train角度參數；本輪無fit前處理。固定clip至[0,pi]，常數feature=pi/2。公式驗證後實際模型都讀相同shared-angle CSV，raw/array/labels/IDs SHA封存。",
      "Smoke Train/Val="+str(smoke["rows"])+"；真實分布="+json.dumps(smoke["class_distributions"],ensure_ascii=False)+"。Smoke Validation缺DOWN，只記錄功能與prediction distribution，沒有計算用來宣稱效果的三分類分數。",
      "Smoke clipping："+json.dumps({k:v["clip"] for k,v in smoke["preprocessing"]["splits"].items()},ensure_ascii=False),
      "Smoke所有Kernel數值檢查、RBF與QSVC fit/predict成功後，才開始Prototype。","",
      "## Prototype Validation","",
      "Train96、Validation96；分布："+json.dumps(proto["class_distributions"],ensure_ascii=False),
      "|model|Macro-F1|Balanced Accuracy|Accuracy|Macro Precision|Macro Recall|prediction DOWN/FLAT/UP|","|---|---:|---:|---:|---:|---:|---|"]
    for name,m in proto["models"].items():
        v=m["metrics"];p=v["predicted_class_distribution"]
        lines.append(f'|{name}|{v["macro_f1"]:.9f}|{v["balanced_accuracy"]:.9f}|{v["accuracy"]:.9f}|{v["macro_precision"]:.9f}|{v["macro_recall"]:.9f}|'+"/".join(str(p[n]) for n in NAMES)+"|")
        lines+=["",name+" 完整metrics："+json.dumps(v,ensure_ascii=False),""] 
    lines+=["三類confusion matrix與per-class precision/recall/F1/support見confusion_matrices.csv與class_metrics.csv；任何缺少預測類別標CLASS_COVERAGE_WARNING，未排除FLAT。","",
      "## Circuit與Kernel數值品質","",json.dumps(proto["circuit"],ensure_ascii=False),
      "Train Gram檢查shape、finite-real、range、symmetry、diagonal及raw eigvalsh最小eigenvalue；Val-vs-Train是cross kernel，只檢查shape/finite/range，不對其錯套unit diagonal或PSD。",
      json.dumps({name:{"train_shape":r["kernel_validation"]["train_shape"],"validation_shape":r["kernel_validation"]["validation_vs_train_shape"],
        "min_eigenvalue":r["kernel_validation"]["train_min_eigenvalue"],"symmetry_error":r["kernel_validation"]["train_symmetry_error"],
        "diagonal_error":r["kernel_validation"]["train_diagonal_one_error"],"tolerance":NUMERICAL_ATOL} for name,r in (("smoke",smoke),("prototype",proto))},ensure_ascii=False,indent=2),
      "所有原始.npy矩陣保存；不裁切、平移、投影或以PSD修補掩蓋數值問題。","",
      "## 時間與記憶體","",
      json.dumps(timing,ensure_ascii=False,indent=2),
      "所有time.perf_counter數值僅為本機Python／CPU Statevector Simulator。QSVC fit/predict為precomputed solver時間，不能忽略另列Train/Val Kernel成本。RBF時間含內部native RBF計算；兩者不據此宣稱Quantum speedup、QPU latency、Tick-to-Trade或HFT execution latency。",
      "Peak RSS為Linux runner process high-water，包含imports，非單模型獨占記憶體；不包含unit-test子程序。","",
      "## 確定性、完整性與安全","",
      json.dumps(det,ensure_ascii=False,indent=2),
      "Prototype以相同Frozen inputs/config重新執行一次；input SHA、predictions、confusion integers要求一致，Kernel與metric用預先固定容許誤差比較，timing不要求相同。主結果取第一次，不選較好repeat。",
      "單元測試："+json.dumps(unit,ensure_ascii=False),
      "完整性："+json.dumps(integ,ensure_ascii=False),
      "Test features/labels未解析或用於模型；只允許opaque SHA完整性檢查。Holdout CSV不開啟，沿用既有SHA與stat metadata，LOCKED／FINAL_HOLDOUT_NOT_EVALUATED；不宣稱fresh重讀Holdout hash。",
      "無套件安裝/升級/移除、網路、IBM QPU、Binance、API Key、Testnet、真實交易、QUBO/QAOA、回測或Paper Trading。此網路聲明限本輪命令，非全機封包監測。","",
      "## 研究限制與下一階段","",
      "保留Phase3B 1000ms RBF baseline instability：歷史Test prediction為102／0／898、FLAT recall0。這是已知舊結果，本輪未重新使用Test，也未據此調參。",
      "Prototype Validation僅96筆且少數類別各5筆；Train32/32/32的class-aware比例不是真實市場比例。Statevector是經典電腦模擬量子電路；單次Validation比較不代表泛化優勢、量子優勢或交易獲利。",
      "本階段沒有Test或Final Holdout驗證。若人工審核後進Phase4A-2，應另行預先指定研究問題與固定比較規格；本次不擴樣、不改參、不執行Test、不自動進入下一階段。",
      "所有結果來自實際執行，未虛構結果；已停止等待人工審核。","",
      "## 命令與證據","",
      PYTHON+" -I -B tools/run_quantum_kernel_experiment.py --run-id "+run.name,
      "完整命令/stdout/stderr/exit見command_history.txt與logs；code SHA見summary/code_manifest.json，最終封存見summary/completion_manifest.json。",""]
    return "\n".join(lines)
def experiment(run):
    if (run/"experiment_config.json").exists() or (ROOT/"docs"/("PHASE4A1_REPORT_"+run.name+".md")).exists():raise FileExistsError("RUN_ALREADY_STARTED")
    env=environment();before=integrity(run);manifest=verify_budget()
    write(run/"experiment_config.json",config());write(run/"environment.json",env)
    write(run/"policy/classification_policy.json",read(BUDGET/"policy/classification_policy.json"))
    write(run/"policy/feature_policy.json",read(BUDGET/"policy/feature_policy.json"))
    write(run/"policy/fair_comparison_policy.json",read(BUDGET/"fair_comparison_policy.json"))
    unit=tests(run);print("Phase4A-1 synthetic unit tests PASS",unit["tests"],flush=True)
    random.seed(42);np.random.seed(42);start=time.perf_counter()
    def progress(done,label):
        t=time.perf_counter()-start
        print(json.dumps({"stage":label,"processed":done,"total":3,"percent":100*done/3,"elapsed_seconds":t,
              "eta_seconds":t/done*(3-done) if done else "NOT_AVAILABLE"}),flush=True)
    smoke,_=stage(BUDGET,manifest,"smoke",run/"smoke");write(run/"smoke_results.json",smoke);progress(1,"SMOKE_PASS")
    proto,pa=stage(BUDGET,manifest,"prototype",run/"prototype/first");progress(2,"PROTOTYPE_FIRST_PASS")
    repeat,ra=stage(BUDGET,manifest,"prototype",run/"determinism/repeat")
    det=compare(proto,pa,repeat,ra);write(run/"determinism.json",det)
    if det["status"]!="PASS":raise ValueError("PROTOTYPE_DETERMINISM_FAILED")
    progress(3,"PROTOTYPE_REPEAT_PASS")
    write(run/"budget_subset_validation.json",{"status":"PASS","budget_manifest_sha256":sha(BUDGET/"quantum_budget_subset_v1_manifest.json"),
        "profiles":{name:{"rows":v["rows"],"class_distributions":v["class_distributions"],"input_identity":v["input_identity"]} for name,v in (("smoke",smoke),("prototype",proto))},
        "same_model_inputs":True,"resampling":False,"Test_used":False,"Holdout_used":False})
    write(run/"preprocessing_manifest.json",{name:r["preprocessing"] for name,r in (("smoke",smoke),("prototype",proto))})
    write(run/"circuit_manifest.json",proto["circuit"])
    write(run/"kernel_validation.json",{"smoke":smoke["kernel_validation"],"prototype":proto["kernel_validation"],"repeat":repeat["kernel_validation"]})
    for name,m in proto["models"].items():write(run/("prototype_"+name+"_metrics.json"),m["metrics"])
    write_csv(run/"confusion_matrices.csv",("model","true_class","pred_DOWN","pred_FLAT","pred_UP"),
        [dict(zip(("model","true_class","pred_DOWN","pred_FLAT","pred_UP"),(name,c,*m["metrics"]["confusion_matrix"][i]))) for name,m in proto["models"].items() for i,c in enumerate(NAMES)])
    write_csv(run/"class_metrics.csv",("model","class","precision","recall","f1","support"),
        [{"model":name,"class":c,**m["metrics"]["per_class"][c]} for name,m in proto["models"].items() for c in NAMES])
    after=integrity(run);write(run/"input_integrity.json",{"status":"PASS","before":before,"after":after})
    for name,v in read(run/"summary/code_manifest.json").items():
        if fp(ROOT/name)!=v:raise ValueError("SOURCE_CHANGED_DURING_EXPERIMENT")
    timing={"smoke":smoke["timing"],"prototype_first":proto["timing"],"prototype_repeat":repeat["timing"],
            "process_peak_rss_bytes":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)*1024 if sys.platform.startswith("linux") else "NOT_AVAILABLE",
            "memory_scope":"Linux runner process high water incl imports; not per-model and excludes unit-test child"}
    write(run/"timing.json",timing)
    output=ROOT/"docs"/("PHASE4A1_REPORT_"+run.name+".md")
    with safe(output).open("x",encoding="utf-8") as f:f.write(report(run,env,smoke,proto,det,timing,after,unit))
    summary={"status":"PHASE 4A-1 PASS","run_id":run.name,"unit_tests":unit,"prototype_metrics":{n:m["metrics"] for n,m in proto["models"].items()},
         "determinism":det,"input_integrity":after,"timing":timing,"network":False,"package_changes":False,"Test_used":False,
         "Final_Holdout_used":False,"QPU":False,"trading":False,"backtest":False,"phase4a2_started":False,"report":str(output)}
    write(run/"summary/run_summary.json",summary)
    print(json.dumps({"status":summary["status"],"run_id":run.name,"report":str(output),"determinism":det["status"]}),flush=True)
    return summary
class Tee:
    def __init__(self,a,b):self.a=a;self.b=b
    def write(self,s):self.a.write(s);self.b.write(s)
    def flush(self):self.a.flush();self.b.flush()
def execute(run):
    argv=[sys.executable,"-I","-B","tools/run_quantum_kernel_experiment.py","--run-id",run.name];t=time.perf_counter()
    with safe(run/"logs/stdout.txt").open("x",encoding="utf-8") as out,safe(run/"logs/stderr.txt").open("x",encoding="utf-8") as err:
        try:
            with contextlib.redirect_stdout(Tee(sys.stdout,out)),contextlib.redirect_stderr(Tee(sys.stderr,err)):experiment(run)
            code=0
        except Exception as exc:
            fail={"status":"PHASE 4A-1 FAIL","run_id":run.name,"exception":type(exc).__name__,"message":str(exc),"traceback":traceback.format_exc()}
            write(run/"summary/failure.json",fail)
            output=ROOT/"docs"/("PHASE4A1_REPORT_"+run.name+".md")
            if not output.exists():
                with safe(output).open("x",encoding="utf-8") as f:f.write("# PHASE 4A-1 FAIL\n\n"+json.dumps(fail,ensure_ascii=False,indent=2)+"\n")
            print(json.dumps(fail,ensure_ascii=False),file=err,flush=True);print(json.dumps(fail,ensure_ascii=False),file=sys.stderr,flush=True)
            code=1
    write(run/"logs/execution.json",{"command":argv,"cwd":str(ROOT),"exit_code":code,"wall_seconds":time.perf_counter()-t,"stdout":"logs/stdout.txt","stderr":"logs/stderr.txt"})
    return code
