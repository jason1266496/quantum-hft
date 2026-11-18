"""Phase 4A-0 planning/budget lock only; no RBF/QSVC training or kernel evaluation."""
import contextlib,csv,hashlib,json,os,platform,re,subprocess,sys,time,traceback
from pathlib import Path
from data_pipeline.datasets.checksums import fingerprint,sha_file
from .io import ROOT,PARENT,SOURCE,FEATURES,FIELDS,NAMES,read,safe,write,write_csv,verify_inputs,load_source,verify_budget_freeze
from .sampler import build_budgets,distribution
from .preprocessing import SharedAngleInput,kernel_budget,fair_policy
from .environment import inspect_dependencies,circuit_design
TESTS=("tests.test_quantum_budget_sampling","tests.test_quantum_input_preparation","tests.test_quantum_preparation_safety","tests.test_quantum_preparation_tool")
def research_policy():
    return {"phase":"4A-0","horizon_ms":1000,"feature_view":"aggregate_core_v1","feature_order":list(FEATURES),
        "classification_policy":"direction_3class_exact_v1","seed":42,"shuffle":False,
        "prototype":{"Train":96,"Validation":96,"Train_per_class":32},
        "smoke":{"Train":24,"Validation":24,"Train_per_class":8},
        "algorithm":"Prototype: per-class Train stable event_time sort and floor(i*(N-1)/(k-1)); Validation same chronological-rank sampling without labels. Smoke: apply same methods inside Prototype with k=8/class or 24 Validation.",
        "nesting":"Smoke is intentionally a subset of Prototype. No duplicates within a profile/split; Train and Validation disjoint across both profiles. Cross-profile reuse is intentional, not oversampling.",
        "validation_labels_used_for_sampling":False,"test_holdout_used":False,
        "insufficient_rows":"STOP; never change requested sizes","input_representation":"shared_budget_angles_v1",
        "model_fitting_allowed":False,"formal_kernel_computation_allowed":False,"QPU_allowed":False,"Phase4A1_started":False}
def unit_tests(run):
    command=[sys.executable,"-B","-m","unittest",*TESTS];start=time.perf_counter()
    p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    for name,value in (("tests.stdout.txt",p.stdout),("tests.stderr.txt",p.stderr)):
        with safe(run/"logs"/name).open("x",encoding="utf-8") as f:f.write(value)
    match=re.search(r"Ran (\d+) tests?",p.stderr)
    result={"status":"PASS" if p.returncode==0 and match else "FAIL","tests":int(match[1]) if match else 0,
            "command":command,"exit_code":p.returncode,"wall_seconds":time.perf_counter()-start,"fixture_only":True}
    write(run/"summary/unit_tests.json",result)
    if result["status"]!="PASS":raise ValueError("UNIT_TESTS_FAILED")
    return result
def save_profile(run,name,budget,base):
    folder=run/name;mapping=SharedAngleInput(base,name).fit(budget["Train"],split="Train")
    param_sha=write(folder/"input_preprocessing.json",mapping.artifact());splits={}
    for split in ("Train","Validation"):
        rows=budget[split];slug=split.lower()
        raw=folder/(slug+".csv");raw_sha=write_csv(raw,FIELDS,rows)
        index_sha=write_csv(folder/(slug+"_indices.csv"),("frozen_v2_row_index","sample_id","event_time_ms"),
          [{"frozen_v2_row_index":i,"sample_id":r["sample_id"],"event_time_ms":r["event_time_ms"]} for i,r in zip(budget["parent_positions"][split],rows)])
        z=mapping.standardize(rows);angles,clip=mapping.transform(rows,split=split)
        def input_rows(values):
            return [{"sample_id":r["sample_id"],**{feature:format(float(values[i,j]),".17g") for j,feature in enumerate(FEATURES)}} for i,r in enumerate(rows)]
        standard_path=folder/(slug+"_standardized_reference.csv")
        standard_sha=write_csv(standard_path,("sample_id",*FEATURES),input_rows(z))
        angles_path=folder/(slug+"_shared_angles.csv");angles_sha=write_csv(angles_path,("sample_id",*FEATURES),input_rows(angles))
        times=[int(r["event_time_ms"]) for r in rows]
        splits[split]={"rows":len(rows),"sample_ids":[r["sample_id"] for r in rows],"class_distribution":distribution(rows),
            "event_time_start":min(times),"event_time_end":max(times),"source_ids":sorted({r["source_id"] for r in rows}),
            "session_ids":sorted({r["session_id"] for r in rows}),"raw_path":str(raw.relative_to(run)),"raw_sha256":raw_sha,
            "indices_sha256":index_sha,"shared_input_path":str(angles_path.relative_to(run)),"shared_input_sha256":angles_sha,
            "reference_standardized_path":str(standard_path.relative_to(run)),"reference_standardized_sha256":standard_sha,
            "feature_order":list(FEATURES),"input_units":"radians","clip_counts_descriptive_only":clip}
    shared={split:{k:v[k] for k in ("sample_ids","raw_path","raw_sha256","shared_input_path","shared_input_sha256")} for split,v in splits.items()}
    matching={"RBF":shared,"QSVC":shared}
    write(folder/"fair_comparison_membership.json",matching)
    return {"profile":name,"splits":splits,"sampling_parent":budget["sampling_parent"],
            "prototype_positions":budget.get("prototype_positions"),"preprocessing_path":name+"/input_preprocessing.json",
            "preprocessing_sha256":param_sha,"same_input_for_RBF_QSVC":matching,"Test_included":False,"Holdout_included":False}
def lock_budget(run,profiles,parent_manifest_sha):
    inputs={}
    for name in ("smoke","prototype"):
        for p in sorted((run/name).glob("*")):
            if p.is_file():inputs[str(p.relative_to(run))]=fingerprint(p)
    for name in ("fair_comparison_policy.json","policy/research_policy.json","policy/classification_policy.json","policy/feature_policy.json"):
        inputs[name]=fingerprint(run/name)
    content="".join(v["sha256"]+"  "+name+"\n" for name,v in sorted(inputs.items()))
    manifest={"version":"quantum_budget_subset_v1","status":"FROZEN","horizon_ms":1000,"source":"Phase3B Frozen Subset v2",
        "parent_manifest_path":str(PARENT/"freeze/kernel_comparison_subset_v2_manifest.json"),"parent_manifest_sha256":parent_manifest_sha,
        "source_dataset_id":"btcusdt_aggregate_v1_20261026T202040Z","feature_view":"aggregate_core_v1","feature_order":list(FEATURES),
        "classification_policy":"direction_3class_exact_v1","seed":42,"profiles":profiles,"policy":research_policy(),"files":inputs,
        "content_tree_sha256":hashlib.sha256(content.encode()).hexdigest(),
        "content_tree_definition":"SHA256 of sorted '<file SHA>  <run-relative file path> LF'; only listed data/input/policy files; manifest and FROZEN.sha256 excluded to avoid self reference",
        "model_training_performed":False,"kernel_computation_performed":False,"Test_used":False,"Final_Holdout_used":False}
    manifest_sha=write(run/"quantum_budget_subset_v1_manifest.json",manifest)
    records={**{name:v["sha256"] for name,v in inputs.items()},"quantum_budget_subset_v1_manifest.json":manifest_sha}
    with safe(run/"FROZEN.sha256").open("x",encoding="utf-8") as f:f.writelines(digest+"  "+name+"\n" for name,digest in sorted(records.items()))
    verify_budget_freeze(run)
    return manifest,manifest_sha
def protocol_text(run):
    return "\n".join(["# Phase 4A-0 固定實驗規格","",
      "本規格只完成實驗準備與小樣本鎖定；Phase4A-1必須另獲人工批准。規格在讀取預算子集合的Validation分布前固定，沒有依Test改設定。",
      "Primary=1000ms、aggregate_core_v1；Feature order："+", ".join(FEATURES)+"；分類沿用direction_3class_exact_v1，Decimal return負／零／正=DOWN／FLAT／UP。",
      "父資料唯一為Phase3B 20261029T220053Z Frozen Subset v2。不得重切原Dataset split，不得改Frozen membership或讀Test／Holdout值。","",
      "## 固定抽樣",
      "Prototype Train每類32共96；Validation96。Train只在各Train class內穩定依event_time排序，取floor(i*(N-1)/(k-1))，含頭尾。Validation只按event_time排序取相同rank公式，不讀label決定indices。",
      "Smoke嵌套於Prototype：Train每類8共24，Validation24，沿用相同規則。Smoke與Prototype跨規模重用IDs是刻意嵌套；每個profile/split內無duplicate，Train與Validation在所有profile間完全不重疊。",
      "不足指定樣本即停止，不自動降規、不重複／合成／shuffle；seed42，但抽樣本身無randomness。","",
      "## 共同輸入與公平比較",
      "保留父Frozen 1000ms Train3000的StandardScaler參數與SHA，不refit、不更動父manifest。各Budget的角度範圍另只fit該Budget Train；Validation transform only。",
      "z=(x-FrozenMean)/FrozenScale；非constant欄theta=pi*clip((z-zTrainMin)/(zTrainMax-zTrainMin),0,1)。常數欄theta=pi/2。Validation超界只按預定規則clip，記錄次數，不用來改範圍。",
      "Frozen正scale在min-max式中代數抵消，所以有效角度範圍只依該Budget Train的raw extrema。保存base參數、Budget Train IDs SHA、z extrema、constant mask、raw CSV、standardized reference CSV及shared angles CSV。",
      "StandardScaler的z為零中心尺度表示，角度表示為有界[0,pi]且可能clip，兩者幾何不同。未來RBF／QSVC都以相同shared angles檔、相同labels/IDs/order/split比較；不能把舊3000-row RBF score當成same-budget基準。",
      "兩模型C固定100、class_weight=balanced；RBF gamma固定0.01，來源是既有Phase3B的Validation選擇，本輪不重調；QSVC目標FidelityStatevectorKernel。RBF必須在相同Budget Train重新fit，但本階段不執行任何model fit。","",
      "## 預定電路",
      "4 features／4 qubits，zz_feature_map，linear [(0,1),(1,2),(2,3)]，reps1、alpha2、parameter prefix x、4個輸入參數；不搜尋電路架構。",
      "本機exact statevector，seed42，不使用QPU。參考未transpile H/P/CX分解為H4、P7、CX6，共17 gates、depth11；這是明列的設計排程推導，不是SDK或硬體實測。若Qiskit缺失，SDK count/depth/parameter count標NOT_AVAILABLE。",
      "實際API與相容性只以本輪metadata/import與允許的circuit construction確認；不以Python版本要求推論完整Kernel／QSVC runtime可用。","",
      "## 預算與環境",
      "Smoke 24x24 Train及24x24 Validation-vs-Train各576元素、各4608 bytes，合計9216 bytes；Prototype 96x96各9216元素、各73728 bytes，合計147456 bytes。都是float64 dense理論量，不含cache/model overhead。",
      "4-qubit statevector維度16，單一complex128 vector理論256 bytes；沒有估計或執行quantum runtime，禁止3000-row Quantum Kernel。",
      "缺Qiskit仍完成規劃與非Qiskit測試，runtime標DEPENDENCY_BLOCKED，不安裝套件或建立venv。候選獨立venv /home/jason/.venvs/quantum-hft-qml僅建議；相容pin尚未離線驗證，須另案批准及驗證。",
      "保留Phase3B baseline instability：1000ms Test預測102／0／898、FLAT recall0；本輪不重新評估Test，不假設量子改善。","",
      "## 停止條件",
      "輸入hash、Frozen、LOCKED或抽樣規則不符立即FAIL並停止。完成本輪後等待人工審核；無Quantum/RBF訓練、正式Kernel、Test評估、QPU、QUBO/QAOA、網路、交易、回測或Paper Trading。","",
      "首個準備run："+run.name+"；實際檔案與SHA見該run manifest與FROZEN.sha256。",""])
def report_text(run,summary,dependency,design,parent_distribution):
    manifest=summary["budget_manifest"];profiles=manifest["profiles"]
    lines=["# Phase 4A-0：Quantum Kernel 實驗準備與小樣本鎖定","",
      "**PHASE 4A-0 PASS**；run_id："+run.name,"研究規劃：COMPLETE；執行環境："+dependency["execution_environment_status"]+"；Quantum Runtime Ready=false。","",
      "## 環境與相容性","工作目錄："+str(ROOT)+"；Python："+dependency["python"]+"；executable："+dependency["executable"]]
    lines += ["套件版本："+json.dumps({k:v["version"] for k,v in dependency["packages"].items()},ensure_ascii=False),
      "相依狀態："+dependency["status"]+"；四項指定import逐項結果見dependency_report.json。",
      "Python3.14量子相容性："+dependency["python_3_14_quantum_compatibility"]+"。未安裝套件；缺少實際套件時不能由Requires-Python推定相容或不相容。",
      "經確認的阻礙與處理："+json.dumps(dependency["remediation"],ensure_ascii=False),
      "qiskit-algorithms僅在選定API需要時才必要；qiskit-aer非本statevector路徑必要條件；未安裝根套件時，完整transitive要求尚無本機metadata可查。","",
      "## 固定研究規格與來源",
      "1000ms／aggregate_core_v1；feature order："+", ".join(FEATURES)+"；direction_3class_exact_v1完全保留，不重定義零return。",
      "父Frozen SHA："+summary["source_frozen"]["manifest_sha256"]+"；核對25項Frozen項目、Dataset checksums與Holdout LOCKED。本輪只有Train/Validation CSV值讀取，Test/Holdout僅完整性byte hash及允許metadata。",
      "先固定抽樣、輸入與C/gamma政策再計算小樣本分布；沒有用Test選樣本、角度範圍、模型或電路。","",
      "## Budget Subset v1",
      "Prototype直接由父Train每類抽32、Val按時間取96；Smoke在Prototype內每類抽8、Val取24。固定floor-rank公式與完整IDs/indices/SHA在manifest，無shuffle/duplicate/synthetic，無Train-Val overlap。",
      "父Validation真實類別比例："+json.dumps(parent_distribution,ensure_ascii=False),
      "|profile|split|rows|DOWN|FLAT|UP|percent DOWN/FLAT/UP|","|---|---|---:|---:|---:|---:|---|"]
    for name,p in profiles.items():
        for split,v in p["splits"].items():
            d=v["class_distribution"]
            lines.append("|"+name+"|"+split+"|"+str(v["rows"])+"|"+"|".join(str(d["counts"][c]) for c in NAMES)+"|"+"/".join(f'{d["percentages"][c]:.6f}' for c in NAMES)+"|")
    lines += ["", "Manifest SHA-256："+summary["budget_manifest_sha256"],"Content tree SHA-256："+manifest["content_tree_sha256"],
      "兩種budget內Train/Val不重疊；Smoke故意嵌套Prototype，跨profile的重用不是oversampling。",
      "## 輸入表示與Fair Comparison",
      "保留Frozen Train3000 StandardScaler；角度min/max只fit各Budget Train，Validation transform only。等價raw Train min/max公式、constant pi/2、clip政策與全部參數均保存。未讀Test/Holdout設定範圍。",
      "每個profile的RBF/QSVC指向同一raw CSV、labels、shared angles CSV與SHA。另存原標準化z供比較，不能把z與angles當成相同幾何表示。future RBF必須在同Budget重新fit，C100、gamma0.01固定；QSVC C100，固定同feature map；本輪model fit=0。",
      "## 電路規格",
      json.dumps(design,ensure_ascii=False,indent=2),
      "分析參考gate count/depth與SDK實測欄位明確分開；沒有statevector/Kernel/QSVC執行，沒有虛構實測數值。",
      "## Kernel 成本估算",
      json.dumps(summary["kernel_budget_estimate"],ensure_ascii=False,indent=2),
      "上述只為dense float64矩陣與complex128 statevector理論尺寸，不是runtime／HFT latency或量子優勢。禁止3000筆正式Quantum Kernel。",
      "## 測試、完整性與停止",
      "人工fixture unit tests："+json.dumps(summary["unit_tests"],ensure_ascii=False),
      "完整性："+json.dumps(summary["integrity"],ensure_ascii=False),
      "Quantum budget Frozen："+json.dumps(summary["budget_freeze"],ensure_ascii=False),
      "沒有修改Phase1～3B、Dataset v1、原Frozen或HFT；Final Holdout維持LOCKED／FINAL_HOLDOUT_NOT_EVALUATED。",
      "保留既有1000ms baseline instability：Test預測DOWN102／FLAT0／UP898，FLAT recall0。這是已封存舊結果的註記，本輪沒有再評估Test。",
      "本輪只執行2次Budget Train角度前處理fit，沒有任何模型fit、Kernel evaluate、Quantum訓練、QPU、Test評估、網路、交易、回測、Paper Trading或QUBO/QAOA。",
      "所有結果來自實際輸出與標明的理論推導，沒有虛構量子結果。相依未通過時，不建議開始Phase4A-1實際量子實驗；先另案批准環境準備並實測相容性。","",
      "## 命令與檔案",
      str(sys.executable)+" -B tools/prepare_quantum_experiment.py --run-id "+run.name,
      "完整stdout/stderr/exit見logs；code SHA見summary/code_manifest.json；全部檔案最終清單見summary/completion_manifest.json。",
      "已完成Phase4A-0並停止，等待人工審核；未自動開始Phase4A-1。",""]
    return "\n".join(lines)
def prepare(run):
    if Path.cwd()!=ROOT or ROOT.resolve()!=ROOT or sys.executable!="/home/jason/.venvs/quantum-hft-ml/bin/python":raise ValueError("WRONG_WORKDIR_OR_INTERPRETER")
    protocol_path=ROOT/"docs/PHASE4A0_EXPERIMENT_PROTOCOL.md";report_path=ROOT/"docs"/("PHASE4A0_REPORT_"+run.name+".md")
    if protocol_path.exists() or report_path.exists() or (run/"quantum_budget_subset_v1_manifest.json").exists():raise FileExistsError("OUTPUT_EXISTS_NO_OVERWRITE")
    integrity=verify_inputs(run,progress=True)
    dependency,loaded=inspect_dependencies();design=circuit_design(dependency,loaded)
    write(run/"dependency_report.json",dependency);write(run/"circuit_design.json",design)
    write(run/"policy/research_policy.json",research_policy())
    write(run/"policy/classification_policy.json",read(PARENT/"policy/classification_policy.json"))
    write(run/"policy/feature_policy.json",read(PARENT/"policy/feature_policy.json"))
    write(run/"fair_comparison_policy.json",fair_policy())
    with safe(protocol_path).open("x",encoding="utf-8") as f:f.write(protocol_text(run))
    tests=unit_tests(run);print("Phase4A-0 fixture tests PASS",tests["tests"],flush=True)
    parent=read(PARENT/"freeze/kernel_comparison_subset_v2_manifest.json")["horizons"]["1000"]
    journal=[];source={}
    for split in ("Train","Validation"):
        source[split]=load_source(SOURCE,split,parent["splits"][split]["subset_sha256"],journal=journal)
        if [r["sample_id"] for r in source[split]]!=parent["splits"][split]["selected_sample_ids"]:raise ValueError("PARENT_MEMBERSHIP_CHANGED")
    budgets=build_budgets(source["Train"],source["Validation"])
    base_path=PARENT/"1000ms/scaler/scaler.json";base=read(base_path)
    if sha_file(base_path)!=parent["scaler_sha256"]:raise ValueError("FROZEN_SCALER_CHANGED")
    profiles={};start=time.perf_counter()
    for i,name in enumerate(("smoke","prototype"),1):
        profiles[name]=save_profile(run,name,budgets[name],base)
        elapsed=time.perf_counter()-start
        print(json.dumps({"stage":"BUDGET_PREPARATION","profile":name,"processed":i,"total":2,"percent":50*i,
              "elapsed_seconds":elapsed,"eta_seconds":elapsed/i*(2-i)}),flush=True)
    manifest,manifest_sha=lock_budget(run,profiles,integrity["parent_frozen"]["manifest_sha256"])
    estimate={name:kernel_budget(n,n) for name,n in (("smoke",24),("prototype",96))}
    write(run/"kernel_budget_estimate.json",estimate)
    write(run/"logs/input_value_access_log.json",journal)
    integrity=verify_inputs(run,progress=True)
    for name,v in read(run/"summary/code_manifest.json").items():
        if fingerprint(ROOT/name)!=v:raise ValueError("PREPARATION_CODE_CHANGED")
    summary={"status":"PHASE 4A-0 PASS","run_id":run.name,"research_planning_status":"COMPLETE",
       "execution_environment_status":dependency["execution_environment_status"],"dependency_status":dependency["status"],
       "quantum_runtime_ready":False,"unit_tests":tests,"source_frozen":integrity["parent_frozen"],
       "budget_manifest_sha256":manifest_sha,"budget_manifest":manifest,"budget_freeze":verify_budget_freeze(run),
       "kernel_budget_estimate":estimate,"parent_validation_class_distribution":distribution(source["Validation"]),
       "integrity":integrity,"preprocessing_fit_calls":2,"model_fit_calls":0,"quantum_kernel_evaluations":0,"test_evaluations":0,
       "QPU_calls":0,"test_value_accessed":False,"holdout_value_accessed":False,"final_holdout":"FINAL_HOLDOUT_NOT_EVALUATED",
       "network":False,"trading":False,"backtest":False,"paper_trading":False,"qaoa":False,"packages_changed":False,"phase4a1_started":False}
    with safe(report_path).open("x",encoding="utf-8") as f:f.write(report_text(run,summary,dependency,design,summary["parent_validation_class_distribution"]))
    write(run/"summary/run_summary.json",summary)
    print(json.dumps({"status":summary["status"],"run_id":run.name,"environment":dependency["execution_environment_status"],
                     "budget_manifest_sha256":manifest_sha,"report":str(report_path),"phase4a1_started":False}),flush=True)
    return summary
class Tee:
    def __init__(self,a,b):self.a=a;self.b=b
    def write(self,s):self.a.write(s);self.b.write(s)
    def flush(self):self.a.flush();self.b.flush()
def execute(run):
    command=[sys.executable,"-B","tools/prepare_quantum_experiment.py","--run-id",run.name];start=time.time()
    with safe(run/"logs/stdout.txt").open("x",encoding="utf-8") as out,safe(run/"logs/stderr.txt").open("x",encoding="utf-8") as err:
        try:
            with contextlib.redirect_stdout(Tee(sys.stdout,out)),contextlib.redirect_stderr(Tee(sys.stderr,err)):prepare(run)
            code=0
        except Exception as exc:
            failure={"status":"PHASE 4A-0 FAIL","run_id":run.name,"error":repr(exc),"traceback":traceback.format_exc()}
            write(run/"summary/failure.json",failure)
            report=ROOT/"docs"/("PHASE4A0_REPORT_"+run.name+".md")
            if not report.exists():
                with safe(report).open("x",encoding="utf-8") as f:f.write("# PHASE 4A-0 FAIL\n\n"+json.dumps(failure,ensure_ascii=False,indent=2)+"\n")
            print(json.dumps(failure,ensure_ascii=False),file=err,flush=True);print(json.dumps(failure,ensure_ascii=False),file=sys.stderr,flush=True)
            code=1
    write(run/"logs/execution.json",{"command":command,"cwd":str(ROOT),"exit_code":code,"wall_seconds":time.time()-start,
         "stdout":"logs/stdout.txt","stderr":"logs/stderr.txt"})
    return code
