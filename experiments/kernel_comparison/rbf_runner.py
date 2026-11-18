"""Phase 3B build/fit/selection/Test workflow. v1 diagnostics never drive v2 policies."""
import contextlib,csv,json,math,os,pickle,platform,random,subprocess,sys,time,traceback
from pathlib import Path
import numpy as np
from sklearn.svm import SVC
from data_pipeline.datasets.checksums import fingerprint,sha_file
from models.classical import feature_policy,label_policy
from models.classical.scaler import TrainOnlyScaler
from models.classical.timing import fit_model,predict_batch
from .freeze import ROOT,OLD,DATASET,FEATURES,FIELDS,HORIZONS,NAMES,read,write,csv_write,safe,utc,protocol,freeze,verify_freeze
from .sampler import temporal_positions,sample_train,sample_temporal,subset,project
from .validator import preflight,verify_inputs,read_split,validate_membership,validate_rows,assert_exact_subset,ensure_new_files_allowed
from .diagnostics import original_diagnostics
from .metrics import score,distribution,shift,matrix_size,prediction_distribution
TESTS=("tests.test_kernel_class_diagnostics","tests.test_kernel_sampler","tests.test_kernel_subset_validator",
       "tests.test_rbf_kernel_baseline","tests.test_kernel_subset_freeze","tests.test_phase3b_test_seal")
def grid():return [{"C":c,"gamma":g} for c in (.1,1.,10.,100.) for g in ("scale","auto",.01,.1,1.)]
def make_model(config):
    if config not in grid():raise ValueError("OUTSIDE_FIXED_GRID")
    return SVC(kernel="rbf",C=config["C"],gamma=config["gamma"],class_weight="balanced",probability=False,random_state=42)
def choose(candidates,*,split="Validation"):
    if split!="Validation" or not candidates:raise ValueError("VALIDATION_SELECTION_ONLY")
    gammas=("scale","auto",.01,.1,1.)
    def rank(v):
        m=v["validation_metrics"];c=v["config"]
        if not math.isfinite(m["macro_f1"]) or not math.isfinite(m["balanced_accuracy"]):raise ValueError("NONFINITE_METRIC")
        return (-m["macro_f1"],-m["balanced_accuracy"],c["C"],gammas.index(c["gamma"]))
    return min(candidates,key=rank)
def all_single(candidates):return all(v["validation_metrics"]["prediction_class_count"]==1 for v in candidates)
class TestGate:
    def __init__(self,paths,barrier):
        self.paths=paths;self.barrier=barrier;self.sealed=False;self.hashes={};self.reads=set();self.evaluated=set()
    def assert_open(self):
        if self.sealed or self.barrier.exists():raise ValueError("NO_RETUNING_AFTER_SEAL")
    def seal(self):
        self.assert_open()
        if set(self.paths)!={1000,100}:raise ValueError("BOTH_HORIZONS_MUST_BE_SEALED")
        for h,p in self.paths.items():
            v=read(p)
            if v["test_evaluated"] or v["test_used_for_selection"] or v["selection_split"]!="Validation":raise ValueError("INVALID_SELECTION_SEAL")
            self.hashes[str(h)]=sha_file(p)
        write(self.barrier,{"status":"ALL_SELECTIONS_SEALED_BEFORE_V2_TEST_ACCESS","sealed_at_utc":utc(),
              "selection_sha256":self.hashes,"test_evaluated":False,"test_retuning_allowed":False})
        self.sealed=True
    def verify(self):
        if not self.sealed:raise ValueError("TEST_BEFORE_SEAL")
        for h,p in self.paths.items():
            if sha_file(p)!=self.hashes[str(h)]:raise ValueError("SELECTION_CHANGED")
    def authorize_read(self,h):
        self.verify()
        if h not in self.paths or h in self.reads:raise ValueError("TEST_READ_ALREADY_USED_OR_UNKNOWN")
        self.reads.add(h)
    def claim(self,h):
        self.verify()
        if h not in self.reads or h in self.evaluated:raise ValueError("TEST_EVALUATION_ALREADY_USED_OR_UNAUTHORIZED")
        self.evaluated.add(h)
def load_csv(p):
    with p.open(newline="",encoding="utf-8") as f:return list(csv.DictReader(f))
def unit_tests(run):
    command=[sys.executable,"-B","-m","unittest",*TESTS];start=time.perf_counter()
    r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    for name,value in (("tests.stdout.txt",r.stdout),("tests.stderr.txt",r.stderr)):
        with safe(run/"logs"/name).open("x",encoding="utf-8") as f:f.write(value)
    import re
    match=re.search(r"Ran (\d+) tests?",r.stderr)
    result={"command":command,"exit_code":r.returncode,"tests":int(match[1]) if match else 0,
            "wall_seconds":time.perf_counter()-start,"stdout":"logs/tests.stdout.txt","stderr":"logs/tests.stderr.txt"}
    result["status"]="PASS" if r.returncode==0 and result["tests"] else "FAIL"
    write(run/"summary/unit_tests.json",result)
    if result["status"]!="PASS":raise ValueError("UNIT_TESTS_FAILED")
    return result
def subset_meta(rows,source_count,indices_sha,csv_sha):
    times=[int(r["event_time_ms"]) for r in rows]
    return {"source_row_count":source_count,"selected_row_count":len(rows),"selected_sample_ids":[r["sample_id"] for r in rows],
            "event_time_start":min(times),"event_time_end":max(times),"source_ids":sorted({r["source_id"] for r in rows}),
            "session_ids":sorted({r["session_id"] for r in rows}),"class_distribution":distribution(rows),
            "indices_sha256":indices_sha,"subset_sha256":csv_sha}
def save_subset(run,h,split,rows,source_count,indices):
    folder=run/(str(h)+"ms")/"subset";slug=split.lower()
    for_check=validate_rows(rows,h,split)
    ih=csv_write(folder/(slug+"_indices.csv"),("original_row_index","sample_id","event_time_ms"),
        [{"original_row_index":i,"sample_id":r["sample_id"],"event_time_ms":r["event_time_ms"]} for i,r in zip(indices,rows)])
    ch=csv_write(folder/(slug+".csv"),FIELDS,rows)
    return {**subset_meta(rows,source_count,ih,ch),"validation":for_check}
def build(run):
    if (run/"summary/build_summary.json").exists() or (run/"policy/research_protocol.json").exists():raise FileExistsError("BUILD_ALREADY_STARTED")
    checked=preflight(run)
    write(run/"environment/preflight_verified.json",checked)
    env={"python":sys.version,"executable":sys.executable,"dependencies":checked["dependencies"],
         "os":platform.platform(),"kernel":platform.release(),"logical_cores":os.cpu_count(),
         "cpu":next((l.split(":",1)[1].strip() for l in Path("/proc/cpuinfo").read_text().splitlines() if l.startswith("model name")),"NOT_AVAILABLE"),
         "ram_MemTotal":next((l.split(":",1)[1].strip() for l in Path("/proc/meminfo").read_text().splitlines() if l.startswith("MemTotal:")),"NOT_AVAILABLE"),
         "working_directory":str(ROOT),"run_id":run.name,"thread_environment":{k:os.environ.get(k) for k in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS")},
         "dataset_tree_hashes":checked["datasets"],"seed":42,"git_commit":"NOT_AVAILABLE; code SHA-256 recorded"}
    write(run/"environment/environment.json",env)
    write(run/"policy/research_protocol.json",protocol())
    write(run/"policy/feature_policy.json",read(OLD/"policy/feature_policy.json"))
    write(run/"policy/classification_policy.json",read(OLD/"policy/classification_policy.json"))
    write(run/"policy/scaler_policy.json",{"fit":"subset v2 Train only independently per horizon","old_full_scaler_reused":False,
        "validation_test":"transform only","holdout":"no values read or transform"})
    tests=unit_tests(run)
    print("Phase 3B fixture tests PASS:",tests["tests"],flush=True)
    diagnostics=original_diagnostics(read(run/"summary/input_integrity_before.json"))
    write(run/"diagnostics/original_subset_diagnostics.json",{"policy_preregistered_sha256":sha_file(run/"policy/research_protocol.json"),
        "diagnostic_scope":"v1 Test explicitly approved; never used for v2 sampling/grid selection","horizons":diagnostics})
    journal=[];plans={};counts=checked["scoped_dataset_validation"]["schema_row_count_checks"]
    for h in HORIZONS:
        start=time.perf_counter()
        train,n=read_split(DATASET,h,"Train",journal=journal)
        val,nval=read_split(DATASET,h,"Validation",journal=journal)
        ti,sampling=sample_train(train,h);vi=sample_temporal(val,split="Validation")
        a,b=subset(train,ti),subset(val,vi)
        assert_exact_subset(a,train,ti);assert_exact_subset(b,val,vi)
        validate_membership({"Train":a,"Validation":b},h)
        tr=save_subset(run,h,"Train",a,n,ti);va=save_subset(run,h,"Validation",b,nval,vi)
        ntest=counts[str(h)+"/test"]["rows"];test_positions=temporal_positions(ntest,1000)
        plan={"horizon_ms":h,"role":"PRIMARY" if h==1000 else "SECONDARY_DIAGNOSTIC",
              "Train":tr,"Validation":va,"train_sampling":sampling,
              "test_plan":{"source_rows":ntest,"selected_rows":len(test_positions),"positions":test_positions,
                    "labels_used_for_sampling":False,"fixed_before_v2_test_values":True},
              "construction_wall_seconds":time.perf_counter()-start,"protocol_sha256":sha_file(run/"policy/research_protocol.json")}
        write(run/(str(h)+"ms")/"subset/selection_plan.json",plan);plans[str(h)]=plan
        print("Built",h,"Train",len(a),"Validation",len(b),"Test plan",len(test_positions),flush=True)
        del train,val,a,b
    write(run/"logs/build_dataset_access_log.json",journal)
    result={"status":"BUILD PASS","run_id":run.name,"horizons":plans,"tests":tests,"v2_test_values_read":False,
            "holdout_values_read":False,"protocol_sha256":sha_file(run/"policy/research_protocol.json")}
    write(run/"summary/build_summary.json",result)
    verify_inputs(run)
    return result
def train_select(run,h,gate,progress):
    gate.assert_open()
    base=run/(str(h)+"ms");train=load_csv(base/"subset/train.csv");val=load_csv(base/"subset/validation.csv")
    validate_membership({"Train":train,"Validation":val},h)
    x,y=feature_policy.matrix(train),label_policy.labels(train)
    vx,vy=feature_policy.matrix(val),label_policy.labels(val)
    scaler=TrainOnlyScaler(h,"kernel_comparison_subset_v2")
    start=time.perf_counter();scaler.fit(x,split="Train",sample_ids=[r["sample_id"] for r in train]);scale_time=time.perf_counter()-start
    scaler_sha=write(base/"scaler/scaler.json",scaler.artifact())
    z=scaler.transform(x,split="Train");vz=scaler.transform(vx,split="Validation")
    candidates=[];objects=[]
    for config in grid():
        gate.assert_open();model=make_model(config);fit=fit_model(model,z,y)
        pred,timing=predict_batch(model.predict,vz)
        metric=score(vy,pred)
        record={"config":config,"validation_metrics":metric,"fit":fit,"validation_predict_timing":timing,
                "support_vectors_per_class":{name:int(model.n_support_[i]) for i,name in enumerate(NAMES)}}
        candidates.append(record);objects.append(model);progress(h,config)
    chosen=choose(candidates)
    single=all_single(candidates)
    if h==1000 and single:raise ValueError("PRIMARY_ALL_CANDIDATES_SINGLE_CLASS")
    selected_model=objects[candidates.index(chosen)]
    selected_count=chosen["validation_metrics"]["prediction_class_count"]
    if h==1000 and selected_count==1:raise ValueError("PRIMARY_SELECTED_VALIDATION_SINGLE_CLASS_TEST_BLOCKED")
    with safe(base/"rbf/model.pkl").open("xb") as f:pickle.dump({"model":selected_model,"scaler":scaler.scaler},f,protocol=5)
    config={"horizon_ms":h,"selected_config":chosen["config"],"estimator_params":selected_model.get_params(),
            "feature_order":list(FEATURES),"label_policy":"direction_3class_exact_v1","dataset_scope":"kernel_comparison_subset_v2",
            "scaler_sha256":scaler_sha,"model_sha256":sha_file(base/"rbf/model.pkl"),"origin":"created in this Phase 3B run",
            "deployment_status":"NOT_APPROVED_FOR_DEPLOYMENT"}
    write(base/"rbf/config.json",config)
    selection={"horizon_ms":h,"candidate_configs":grid(),"validation_candidates":candidates,
        "selected_config":chosen["config"],"selected_validation_metrics":chosen["validation_metrics"],
        "selection_split":"Validation","selection_metric":"macro_f1","tie_breaks":["balanced_accuracy desc","C asc","gamma=scale first","remaining fixed grid order"],
        "selected_at_utc":utc(),"test_evaluated":False,"test_used_for_selection":False,"holdout_used":False,
        "protocol_sha256":sha_file(run/"policy/research_protocol.json"),"scaler_sha256":scaler_sha,
        "train_subset_sha256":sha_file(base/"subset/train.csv"),"validation_subset_sha256":sha_file(base/"subset/validation.csv"),
        "all_candidates_single_class":single,"selected_validation_prediction_class_count":selected_count,
        "warnings":chosen["validation_metrics"]["warnings"]+(["SECONDARY_ALL_CANDIDATES_SINGLE_CLASS"] if single else [])}
    write(base/"selection/selection_manifest.json",selection)
    write(base/"rbf/validation_metrics.json",chosen["validation_metrics"])
    csv_write(base/"rbf/candidate_results.csv",("C","gamma","macro_f1","balanced_accuracy","prediction_class_count","fit_seconds","validation_predict_median_seconds"),
        [{"C":v["config"]["C"],"gamma":v["config"]["gamma"],"macro_f1":v["validation_metrics"]["macro_f1"],
          "balanced_accuracy":v["validation_metrics"]["balanced_accuracy"],"prediction_class_count":v["validation_metrics"]["prediction_class_count"],
          "fit_seconds":v["fit"]["fit_wall_seconds"],"validation_predict_median_seconds":v["validation_predict_timing"]["median_wall_seconds"]} for v in candidates])
    selected_pred,_=predict_batch(selected_model.predict,vz)
    csv_write(base/"rbf/validation_predictions.csv",("sample_id","true_class","predicted_class"),
        [{"sample_id":r["sample_id"],"true_class":int(vy[i]),"predicted_class":int(selected_pred[i])} for i,r in enumerate(val)])
    return {"model":selected_model,"scaler":scaler,"train":train,"validation":val,"selection":selection,
        "scaler_fit_wall_seconds":scale_time,"chosen":chosen,"scaler_sha256":scaler_sha}
def test_once(run,h,state,gate,journal):
    base=run/(str(h)+"ms");plan=read(base/"subset/selection_plan.json")
    positions=plan["test_plan"]["positions"]
    test,n=read_split(DATASET,h,"Test",gate=gate,journal=journal,positions=positions)
    if n!=plan["test_plan"]["source_rows"]:raise ValueError("TEST_SOURCE_COUNT_CHANGED")
    validate_membership({"Train":state["train"],"Validation":state["validation"],"Test":test},h)
    tm=save_subset(run,h,"Test",test,n,positions)
    selected=state["selection"];manifest={"version":"kernel_comparison_subset_v2","status":"FROZEN","horizon_ms":h,
        "role":"PRIMARY" if h==1000 else "SECONDARY_DIAGNOSTIC","feature_view":"aggregate_core_v1",
        "feature_policy":"aggregate_compact_v1","feature_order":list(FEATURES),"classification_policy":"direction_3class_exact_v1",
        "sampling_method":protocol()["temporal_method"],"Train_sampling":plan["train_sampling"],"seed":42,
        "splits":{"Train":plan["Train"],"Validation":plan["Validation"],"Test":tm},
        "validation_test_class_balanced":False,"test_labels_used_for_sampling":False,"holdout_used":False,
        "scaler_sha256":state["scaler_sha256"],"dataset_tree_hash":read(run/"environment/preflight_verified.json")["datasets"][DATASET.name]["dataset_tree_hash"],
        "test_policy_fixed_before_values":True}
    write(base/"subset/kernel_comparison_subset_v2_manifest.json",manifest)
    if selected["selected_validation_prediction_class_count"]<2:
        evaluation={"status":"NOT_EVALUATED_SELECTED_VALIDATION_SINGLE_CLASS","metric_evaluation_count":0,
                    "test_retuning_performed":False,"selection_sha256":gate.hashes[str(h)],"test_rows":len(test)}
        metric=None;timing=None
    else:
        gate.claim(h)
        write(base/"test/test_evaluation_started.json",{"started_at_utc":utc(),"selection_sha256":gate.hashes[str(h)],"allowed_evaluation_count":1})
        start=time.perf_counter();z=state["scaler"].transform(feature_policy.matrix(test),split="Test")
        transform_seconds=time.perf_counter()-start
        pred,timing=predict_batch(state["model"].predict,z,repeats=3)
        metric=score(label_policy.labels(test),pred)
        write(base/"test/test_metrics.json",metric)
        csv_write(base/"test/test_predictions.csv",("sample_id","true_class","predicted_class"),
            [{"sample_id":r["sample_id"],"true_class":int(r["class_label"]),"predicted_class":int(pred[i])} for i,r in enumerate(test)])
        csv_write(base/"test/confusion_matrix.csv",("true_class","pred_DOWN","pred_FLAT","pred_UP"),
            [dict(zip(("true_class","pred_DOWN","pred_FLAT","pred_UP"),(name,*metric["confusion_matrix"][i]))) for i,name in enumerate(NAMES)])
        csv_write(base/"test/per_class_metrics.csv",("class","precision","recall","f1","support"),
            [{"class":name,**metric["per_class"][name]} for name in NAMES])
        evaluation={"status":"TEST EVALUATED ONCE","metric_evaluation_count":1,"test_rows":len(test),
            "selection_sha256":gate.hashes[str(h)],"barrier_sha256":sha_file(run/"selection_barrier.json"),
            "test_metrics_sha256":sha_file(base/"test/test_metrics.json"),"selected_config":selected["selected_config"],
            "prediction_warmup_calls":1,"prediction_timed_calls":3,"test_retuning_performed":False,
            "final_holdout_used":False,"test_transform_wall_seconds":transform_seconds,"completed_at_utc":utc()}
    write(base/"test/test_evaluation_manifest.json",evaluation)
    write(base/"rbf/timing.json",{"timing_scope":"PYTHON_BATCH_INFERENCE_ONLY","hft_latency_claim":False,
        "subset_construction_wall_seconds":plan["construction_wall_seconds"],"scaler_fit_wall_seconds":state["scaler_fit_wall_seconds"],
        "selected_fit":state["chosen"]["fit"],"selected_validation_predict":state["chosen"]["validation_predict_timing"],"selected_test_predict":timing})
    write(base/"rbf/prediction_distributions.json",{"Validation":prediction_distribution_from_metric(state["chosen"]["validation_metrics"]),
         "Test":prediction_distribution_from_metric(metric) if metric else evaluation})
    gate.verify()
    return manifest,{"horizon_ms":h,"role":manifest["role"],"selected_config":selected["selected_config"],
        "validation_metrics":state["chosen"]["validation_metrics"],"test_metrics":metric,"test_evaluation":evaluation,
        "sizes":{k:v["selected_row_count"] for k,v in manifest["splits"].items()},
        "class_distributions":{k:v["class_distribution"] for k,v in manifest["splits"].items()},
        "timing":read(base/"rbf/timing.json"),"kernel_size_estimate":matrix_size(len(state["train"]),len(state["validation"]),len(test)),
        "distribution_shift":shift({"Train":state["train"],"Validation":state["validation"],"Test":test})}
def prediction_distribution_from_metric(m):
    return {k:m[k] for k in ("counts","percentages","prediction_class_count","warnings")}
def eligible_primary(result):
    m=result["validation_metrics"];t=result["test_metrics"]
    eligible=(m["prediction_class_count"]==3 and all(v["recall"]>0 for v in m["per_class"].values()) and m["balanced_accuracy"]>1/3)
    return {"recommendation":"RECOMMEND_1000MS_PHASE4A_AFTER_HUMAN_APPROVAL" if eligible else "DO_NOT_RECOMMEND_PHASE4A_YET",
        "validation_gate_pass":eligible,"validation_only_gate":True,"test_instability":bool(t and t["prediction_class_count"]==1),
        "test_used_for_retuning":False,"actual_quantum_execution":False,"membership":"FROZEN subset v2; any quantum budget subset requires separate explicit approval"}
def report_text(run,results,integrity,recommendation):
    old=read(run/"diagnostics/original_subset_diagnostics.json")
    lines=["# Phase 3B：Kernel Subset v2、RBF Baseline 與公平比較凍結","",
      "**PHASE 3B PASS**；run_id："+run.name,"",
      "Phase 3A PASS 20261026T212918Z 的完整 inventory、報告與程式 SHA 已驗證且保持不變；舊 FAIL 20261026T205307Z 保留。Dataset v1、Phase2A～2F 與 HFT 全部唯讀。研究政策在 v1 Test 診斷之前封存，v2 Test 在兩 horizon selection seals 後才讀。",
      "Feature view aggregate_core_v1；固定順序："+", ".join(FEATURES)+"。Label 沿用 direction_3class_exact_v1，Decimal exact sign，零為 FLAT，沒有 epsilon、成本門檻或 Feature Selection。","",
      "## 原 subset 診斷"]
    for h in HORIZONS:
        d=old["horizons"][str(h)]
        lines += [f"### {h}ms",json.dumps({k:d[k] for k in ("selected_config","support_vectors_per_class","scaler_checked_against_subset_train","answers")},ensure_ascii=False,indent=2),
                  "Train／Validation／Test 的 class counts、比例、source/session、時間密度、最大 gap、feature min/max/median、per-class median/IQR、decision function 與 scaler 全見 diagnostics/original_subset_diagnostics.json。缺少 minority class 的假設由實際 count 檢查；觀察到分布差異不當成已證實因果。"]
    lines += ["","## Subset v2 與 Scaler",
      "1000ms Primary：Train 每類至多1000，不補樣、不重複。100ms Secondary：每類 min(各類available,1000)，若少於1000/class 標 SMALL_MINORITY_CLASS_WARNING，不能阻擋 Primary。",
      "每類或 split 按 event_time 穩定排序，再取 floor(i*(N-1)/(k-1)) 等距 rank，包含頭尾；不是均勻 wall-clock 重採樣。Validation／Test 各最多1000，不看 label、不 class-balance；保持觀測時間密度的近似抽樣，不能宣稱比例與全量完全相同。",
      "各 horizon 僅以 subset v2 Train fit 新 StandardScaler；Validation/Test transform only；未重用舊 Full scaler。保存 mean/scale/var/n_samples_seen、feature order、version、Train IDs SHA及artifact SHA。",
      "RBF grid：C=[0.1,1,10,100] × gamma=[scale,auto,0.01,0.1,1.0]，balanced、probability=False、random_state=42。只以 Validation Macro-F1、BA、較小C、gamma=scale優先選擇；剩餘精確同分沿固定 grid order。","",
      "## Class distributions、選擇與結果","|h|split|DOWN|FLAT|UP|percent DOWN/FLAT/UP|","|---|---|---:|---:|---:|---|"]
    for h in HORIZONS:
        for split,d in results[str(h)]["class_distributions"].items():
            lines.append(f"|{h}|{split}|"+ "|".join(str(d["counts"][c]) for c in NAMES)+"|"+"/".join(f'{d["percentages"][c]:.6f}' for c in NAMES)+"|")
    lines += ["","|h|selected config|Val Macro-F1|Val BA|Test Macro-F1|Test BA|Val predicted classes|Test predicted classes|",
              "|---|---|---:|---:|---:|---:|---:|---:|"]
    for h in HORIZONS:
        r=results[str(h)];v=r["validation_metrics"];t=r["test_metrics"]
        lines.append(f'|{h}|{json.dumps(r["selected_config"])}|{v["macro_f1"]:.9f}|{v["balanced_accuracy"]:.9f}|'+
                     (f'{t["macro_f1"]:.9f}|{t["balanced_accuracy"]:.9f}|' if t else "NOT_EVALUATED|NOT_EVALUATED|")+
                     f'{v["prediction_class_count"]}|'+str(t["prediction_class_count"] if t else "NOT_EVALUATED")+"|")
        lines += ["",f"{h}ms prediction distributions："+json.dumps({"Validation":prediction_distribution_from_metric(v),"Test":prediction_distribution_from_metric(t) if t else "NOT_EVALUATED"},ensure_ascii=False),
          "三類 confusion matrix、per-class precision/recall/F1/support 與全樣本 accuracy 均保存；FLAT 未排除。subset/CSV、indices、IDs、class counts、source/session/time range 與 SHA 已固定。"]
    lines += ["","## Validation candidate results","|h|C|gamma|Macro-F1|BA|prediction class count|fit s|Val predict s|",
              "|---|---:|---|---:|---:|---:|---:|---:|"]
    for h in HORIZONS:
        for v in read(run/(str(h)+"ms")/"selection/selection_manifest.json")["validation_candidates"]:
            m=v["validation_metrics"];c=v["config"]
            lines.append(f'|{h}|{c["C"]}|{c["gamma"]}|{m["macro_f1"]:.9f}|{m["balanced_accuracy"]:.9f}|{m["prediction_class_count"]}|{v["fit"]["fit_wall_seconds"]:.9f}|{v["validation_predict_timing"]["median_wall_seconds"]:.9f}|')
    lines += ["","## Test seal、Frozen 與 Distribution Shift",
      "全部選擇先封存，selection_manifest.json 保留 test_evaluated=false；SHA 鏈結 selection_barrier.json，Test 結果在獨立 test_evaluation_manifest.json。每個允許評分的 selected model metrics 一次；timing warm-up1＋3次相同prediction。沒有 Test retuning。",
      "freeze/kernel_comparison_subset_v2_manifest.json 與 FROZEN.sha256 固定兩 horizon Train/Validation/Test IDs、Feature/Label policy、Train-only scaler。Phase4 不得改 membership；本輪不建立 quantum_budget_subset。",
      "distribution_shift_report.json 描述四 features Train/Val/Test median/IQR 及每類 support/proportions；含 v1 與 v2 分開 scope，不用 Test 統計改 policy。原 Dataset Test 已在 Phase3A 使用，本輪是已見 Test 的新研究 protocol，不宣稱新的獨立外樣本驗證；Final Holdout 仍未使用。","",
      "## Timing 與 Kernel Matrix 規模","|h|construction s|scaler fit s|selected fit s|Test median s|Test rows|","|---|---:|---:|---:|---:|---:|"]
    for h in HORIZONS:
        r=results[str(h)];t=r["timing"];p=t["selected_test_predict"]
        lines.append(f'|{h}|{t["subset_construction_wall_seconds"]:.9f}|{t["scaler_fit_wall_seconds"]:.9f}|{t["selected_fit"]["fit_wall_seconds"]:.9f}|'+
                     (f'{p["median_wall_seconds"]:.9f}|{p["prediction_rows"]}|' if p else "NOT_EVALUATED|0|"))
        lines.append("Kernel size "+str(h)+"ms："+json.dumps(r["kernel_size_estimate"]))
    lines += ["全部為 time.perf_counter 的 Python batch timing，非 HFT latency；各 candidate fit、Validation inference 與 Test三次計時另存。Kernel 元素數只估規模，沒有估量子 runtime。","",
      "## Integrity、環境與限制",
      "Final Holdout：LOCKED／FINAL_HOLDOUT_NOT_EVALUATED。僅checksum/schema/row count/metadata；未解析 feature/label、計算class distribution、transform、predict或diagnostics。",
      "完整性："+json.dumps(integrity,ensure_ascii=False)+"。Dataset兩 tree hash與Phase2F checksums一致，舊Phase3A包含所有artifact、report與code保持，HFT程式與來源檔保持。",
      "環境與seed見environment/environment.json；不安裝/移除/升級套件，不連網/Binance/Testnet/下單、不回測/Paper Trading、不建立Quantum Kernel/QSVC/QUBO/QAOA。網路聲明限本輪命令，非全機封包稽核。","",
      "## Phase 4A recommendation",json.dumps(recommendation,ensure_ascii=False,indent=2),
      "合理三類區分的保守建議判準在Test前固定：Primary Validation預測三類、各類recall>0、BA>1/3。這只用於建議，並非獲利證明或Quantum優勢證明。Test單類結果只記不調參；100ms Secondary 不否決 Primary。",
      "所有數值來自實際執行，沒有虛構結果；old v1 因果不足明列 INSUFFICIENT_EVIDENCE。本次止於Phase3B，等待人工審核，不自批Phase4A。","",
      "## 命令與證據",
      "正式命令：venv python -B tools/build_kernel_comparison_subset.py --run-id "+run.name+"；接著 venv python -B tools/run_rbf_kernel_baseline.py --run-id "+run.name,
      "完整命令/stdout/stderr/exit見logs；程式SHA見summary/code_manifest.json；完整封存見summary/completion_manifest.json。",""]
    return "\n".join(lines)
def run_baseline(run):
    if not (run/"summary/build_summary.json").exists() or (run/"selection_barrier.json").exists():raise ValueError("BUILD_REQUIRED_OR_RUN_ALREADY_STARTED")
    verify_inputs(run);checked=read(run/"summary/build_summary.json")
    if checked["status"]!="BUILD PASS" or read(run/"policy/research_protocol.json")!=protocol():raise ValueError("PROTOCOL_CHANGED")
    random.seed(42);np.random.seed(42)
    paths={h:run/(str(h)+"ms")/"selection/selection_manifest.json" for h in HORIZONS}
    gate=TestGate(paths,run/"selection_barrier.json")
    start=time.perf_counter();done=0;total=40
    def progress(h,c):
        nonlocal done
        done+=1;elapsed=time.perf_counter()-start
        print(json.dumps({"stage":"RBF_VALIDATION_GRID","horizon_ms":h,"config":c,"processed":done,"total":total,
            "percent":done*100/total,"elapsed_seconds":elapsed,"eta_seconds":elapsed/done*(total-done)}),flush=True)
    states={h:train_select(run,h,gate,progress) for h in HORIZONS}
    gate.seal();results={};manifests={};journal=[]
    for h in HORIZONS:
        manifest,result=test_once(run,h,states[h],gate,journal)
        manifests[str(h)]=manifest;results[str(h)]=result
        print("Test stage",h,result["test_evaluation"]["status"],flush=True)
    if 1000 not in gate.evaluated:raise ValueError("PRIMARY_TEST_INCOMPLETE")
    gate.verify()
    write(run/"logs/test_dataset_access_log.json",journal)
    write(run/"diagnostics/distribution_shift_report.json",{h:r["distribution_shift"] for h,r in results.items()})
    for r in results.values():del r["distribution_shift"]
    write(run/"comparison/rbf_results.json",results)
    write(run/"timing/summary.json",{h:r["timing"] for h,r in results.items()})
    write(run/"comparison/kernel_matrix_estimates.json",{h:r["kernel_size_estimate"] for h,r in results.items()})
    frozen=freeze(run,manifests)
    integrity=verify_inputs(run);ensure_new_files_allowed(run)
    recommendation=eligible_primary(results["1000"])
    summary={"status":"PHASE 3B PASS","run_id":run.name,"phase3a_status":"PHASE 3A PASS",
         "tests":checked["tests"],"results":results,"integrity":integrity,"freeze":verify_freeze(run),
         "phase4a_recommendation":recommendation,"final_holdout":"FINAL_HOLDOUT_NOT_EVALUATED","holdout_status":"LOCKED",
         "holdout_values_read":False,"network":False,"trading":False,"backtest":False,"paper_trading":False,
         "quantum_model":False,"phase4a_started":False,"old_fail_preserved":True}
    report=safe(ROOT/"docs"/("PHASE3B_REPORT_"+run.name+".md"))
    with report.open("x",encoding="utf-8") as f:f.write(report_text(run,results,integrity,recommendation))
    write(run/"summary/run_summary.json",summary)
    print(json.dumps({"status":summary["status"],"run_id":run.name,"report":str(report),"recommendation":recommendation}),flush=True)
    return summary
class Tee:
    def __init__(self,a,b):self.a=a;self.b=b
    def write(self,s):self.a.write(s);self.b.write(s)
    def flush(self):self.a.flush();self.b.flush()
def execute(stage,run):
    if stage not in ("build","baseline"):raise ValueError("INVALID_STAGE")
    log=run/"logs"
    command=[sys.executable,"-B","tools/"+("build_kernel_comparison_subset.py" if stage=="build" else "run_rbf_kernel_baseline.py"),"--run-id",run.name]
    start=utc()
    with safe(log/(stage+".stdout.txt")).open("x",encoding="utf-8") as out,safe(log/(stage+".stderr.txt")).open("x",encoding="utf-8") as err:
        try:
            with contextlib.redirect_stdout(Tee(sys.stdout,out)),contextlib.redirect_stderr(Tee(sys.stderr,err)):
                result=build(run) if stage=="build" else run_baseline(run)
            code=0
        except Exception as exc:
            record={"status":"PHASE 3B FAIL","run_id":run.name,"stage":stage,"error":repr(exc),"traceback":traceback.format_exc(),"final_holdout":"FINAL_HOLDOUT_NOT_EVALUATED"}
            write(run/"summary"/(stage+"_failure.json"),record)
            report=ROOT/"docs"/("PHASE3B_REPORT_"+run.name+".md")
            if not report.exists():
                with safe(report).open("x",encoding="utf-8") as f:f.write("# PHASE 3B FAIL\n\n"+json.dumps(record,ensure_ascii=False,indent=2)+"\n")
            print(json.dumps(record,ensure_ascii=False),file=err,flush=True);print(json.dumps(record,ensure_ascii=False),file=sys.stderr,flush=True)
            code=1
    write(log/(stage+"_execution.json"),{"command":command,"cwd":str(ROOT),"started_at_utc":start,"finished_at_utc":utc(),
         "exit_code":code,"stdout":stage+".stdout.txt","stderr":stage+".stderr.txt"})
    return code
