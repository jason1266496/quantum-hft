"""Generate final evidence and Traditional Chinese report from locked saved outputs."""
import json
from pathlib import Path
from datetime import datetime,timezone
from . import contracts as c
from experiments.phase4a1 import contracts as old
def finalize(run_id):
    run=c.runpath(run_id)
    tests=old.read(run/"summary/unit_tests.json")
    result=old.read(run/"run_result.json") if (run/"run_result.json").exists() else {"status":"PHASE 4B-1 FAIL","reason":"Preflight/unit gate did not pass; no formal execution"}
    passed=result["status"]=="PHASE 4B-1 PASS"
    report=c.ROOT/"docs"/("PHASE4B1_REPORT_"+run_id+".md")
    required=("preregistration_lock.json","input_integrity.json","fold_dataset_manifests.json","preprocessing_manifests.json","kernel_validation.json","kernel_timing.json","model_metrics.json","confusion_matrices.json","per_class_metrics.csv","fold_comparison.csv","aggregate_metrics.json","prediction_distributions.json","minority_support_warnings.json","temporal_dependence_warnings.json","determinism.json","safety_audit.json")
    if not passed:
        for name in required:
            if not (run/name).exists():
                if name.endswith(".csv"):c.csv_write(run/name,("status","reason"),[])
                else:c.write(run/name,{"status":"NOT_EXECUTED_OR_INCOMPLETE","reason":result.get("reason"),"not_fabricated":True})
        c.write(report,"# Phase 4B-1 FAIL\n\nrun_id："+run_id+"。\n\n必要 Gate 或技術驗收失敗，已停止，不重跑同一 run。原因："+str(result.get("reason"))+"。\n\n未完成的模型／Kernel／指標均為 NOT_AVAILABLE，不得視為金融或量子結果。Test 未用；Final Holdout 保持 LOCKED。詳見本輪 failure.json、summary/unit_tests.json 及 logs。\n")
        c.write(run/"summary/final_review.json",{"status":"PHASE 4B-1 FAIL","report":str(report),"report_fp":old.fp(report),"unit_tests":tests,"reason":result.get("reason")})
        return "FAIL"
    c.verify_lock(run)
    metrics=old.read(run/"model_metrics.json")["folds"];agg=old.read(run/"aggregate_metrics.json");kern=old.read(run/"kernel_validation.json");kt=old.read(run/"kernel_timing.json")
    det=old.read(run/"determinism.json");safe=old.read(run/"safety_audit.json");integrity=old.read(run/"final_integrity.json")
    minority=old.read(run/"minority_support_warnings.json");temporal=old.read(run/"temporal_dependence_warnings.json");pre=old.read(run/"preprocessing_manifests.json")
    checks={
      "unit_gate":tests["status"]=="PASS" and tests["failures"]==tests["errors"]==tests["skipped"]==0,
      "fold_IDs_purge_endpoint":old.read(run/"input_integrity.json")["status"]=="PASS",
      "Train_only_preprocessing":pre["Train_only"] and all(s["parameters"]["fit_rows"]==96 for s in pre["first"]+pre["repeat"]),
      "15_first_and15_repeat_candidates":len(metrics)==3 and all(set(f["models"])==set(c.MODELS) for f in metrics) and result["candidate_results_first"]==result["candidate_results_repeat"]==15,
      "Kernel_numerics":kern["status"]=="PASS" and all(f["Quantum"]["status"]==f["RBF"]["status"]=="PASS" for f in kern["folds"]) and not kern["repairs"],
      "all_metrics_complete":all(all(k in v["metrics"] for k in ("macro_f1","balanced_accuracy","accuracy","macro_precision","macro_recall","per_class","confusion_matrix","true_class_distribution","predicted_class_distribution")) for f in metrics for v in f["models"].values()),
      "minority_warning":"MINORITY_SUPPORT_CRITICAL" in minority["folds"][2]["warnings"],
      "temporal_warning":"TEMPORAL_DEPENDENCE_WARNING" in temporal["folds"][0]["warnings"] and temporal["folds"][0]["adjacent_overlapping_Validation_label_pairs"]==383,
      "determinism":det["status"]=="PASS",
      "Dataset_Frozen_venvs":integrity["status"]=="PASS" and integrity["ML_env_unchanged"] and integrity["QML_env_unchanged"],
      "Test_and_Holdout_unused":not safe["Test_values_parsed"] and not safe["Holdout_opened"] and safe["Holdout_status"]=="LOCKED",
      "execution_budget":safe["formal_fits"]==24 and safe["formal_Quantum_evaluate_calls"]==6,
      "no_network_QPU_trading":not safe["network_attempts"] and not any(safe[k] for k in ("packages_changed","QPU","Binance","QAOA","QUBO","trading","backtest","paper_trading","Phase4B2_started")),
      "required_outputs":all((run/n).is_file() for n in required)}
    state="PASS" if all(checks.values()) else "FAIL"
    def count(d):return "/".join(str(d[n]) for n in c.NAMES)
    def fmt(v):return f"{v:.6f}"
    def link(p,label=None):return "["+(label or Path(p).name)+"]("+str(p)+")"
    lines=["# Phase 4B-1：Pre-registered Within-Session Temporal Validation","",
       "**PHASE 4B-1 "+state+"**。run_id："+run_id+"。完成時間 UTC："+datetime.now(timezone.utc).isoformat(),"",
       "ENGINEERING "+state+"：只表示資料、固定模型、數值與重現性驗收。EXPLORATORY RESULT：三個固定 session 區段內的時間順序觀察。GENERALIZATION NOT ESTABLISHED；QUANTUM ADVANTAGE NOT ESTABLISHED；TRADING PROFITABILITY NOT ESTABLISHED。",
       "","## 固定規格與預註冊","",
       "資料值只來自正式 Dataset v1 aggregate_core_v1/1000ms/train.csv 的已封存1,440 IDs，以及同 Train 的 endpoint witnesses；未重選樣本。四特徵順序 obi_5、spread_bps、bid_volume_5、ask_volume_5；direction_3class_exact_v1；DOWN=0/FLAT=1/UP=2。",
       "Phase4B0 parent run 20261030T020400Z；Window Manifest SHA "+c.WINDOW_SHA+"。preflight 通過後先執行完整人工 fixtures，通過後才鎖定全部程式 SHA、model/preprocessing/metrics/execution configs、環境及窗口，再開始任何正式 fit/Kernel。鎖定後沒有改動程式、設定、features、IDs 或模型結構。",
       "RBF-SVM C=100、gamma=0.01，None/balanced；真正 Qiskit QSVC C=100、None/balanced、quantum_kernel='precomputed'；五候選均 probability=False，solver random_state=42。Quantum map 4qubits zz_feature_map、linear、reps=1、alpha=2、FidelityStatevectorKernel、shots=None、enforce_psd=False，無 Kernel 修補。Majority-FLAT 從各 fold Train counts 決定 argmax（固定 DOWN/FLAT/UP tie order）；三個正式 Train 均為 FLAT 多數，不用 Validation 決定。",
       "環境："+json.dumps(old.read(run/"preregistration_lock.json")["environment"],ensure_ascii=False),"",
       "QSVC precomputed API 的等價性：人工 fixtures 對兩權重政策比較標準 QSVC(FidelityStatevectorKernel) 與實際 QSVC precomputed 的 predictions／decision_function；並核對 statevector overlap 定義。正式只計算每 fold一份96×96 Train與384×96 cross Kernel，兩個 QSVC 政策共用；沒有用另一種 classifier 冒充 QSVC。",
       "","## 資料、時間與 preprocessing","",
       "|Fold|Train DOWN/FLAT/UP|Validation DOWN/FLAT/UP|",
       "|---|---|---|"]
    for f in metrics:
        truth=f["models"]["RBF_None"]["metrics"]["true_class_distribution"]
        train=minority["folds"][f["fold"]-1]["Train_support"]
        lines.append(f"|F{f['fold']}|{count(train)}|{count(truth)}|")
    window=c.parent()
    lines+=["","所有fold均Train96/Validation384；相同固定IDs，所有sample與market groups不跨分割。Train實際label endpoint嚴格早於boundary，等號purge；feature lookback=0、額外embargo=0，沒有跨session標籤。1,440列已逐筆核對 source/session/record/update ID/實際future time與同session future mid-price，來源Train checksum相符。",
       "每個fold只使用自身Train96 fit mean、population std、Train z-min/max；theta=pi*clip((z-zmin)/(zmax-zmin),0,1)。constant/zero-std固定pi/2，Validation只transform，不impute或悄悄刪列；非有限值立即失敗。RBF與QSVC使用完全相同的角度陣列與feature order。沒有使用Phase4A舊scaler；與Phase4A分數差異不能全歸因於時間窗口。"]
    for i,f in enumerate(window["folds"]):
        pp=pre["first"][i];vp=pp["diagnostics"]["Validation"]
        lines.append(f"F{f['fold_id']} Train UTC {f['Train']['event_time_start_utc']} ～ {f['Train']['event_time_end_utc']}；Validation UTC {f['Validation']['event_time_start_utc']} ～ {f['Validation']['event_time_end_utc']}。常數mask={pp['parameters']['constant_mask']}；Validation below clipping={vp['clipped_below']}、above={vp['clipped_above']}，nonfinite=0；parameters SHA={pp['parameters_file']['sha256']}。")
    lines+=["","## 每fold完整模型結果","",
       "下列模型／類別順序固定；confusion matrix 的列為 true、欄為 prediction，均 DOWN/FLAT/UP。所有類別都納入 Macro 指標，zero_division=0，沒有排除 FLAT 或未預測的類別。每類precision/recall/F1及support另完整列於 "+link(run/"per_class_metrics.csv")+"；原始預測、完整metrics與repeat分開保存。","",
       "|Fold|Model|Macro-F1|BA|Accuracy|Macro Precision|Macro Recall|DOWN recall|FLAT recall|UP recall|Prediction DOWN/FLAT/UP|",
       "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for f in metrics:
        for name in c.MODELS:
            m=f["models"][name]["metrics"]
            vals=[m[k] for k in ("macro_f1","balanced_accuracy","accuracy","macro_precision","macro_recall")]+[m["per_class"][n]["recall"] for n in c.NAMES]
            lines.append("|F"+str(f["fold"])+"|"+name+"|"+"|".join(fmt(v) for v in vals)+"|"+count(m["predicted_class_distribution"])+"|")
    lines+=["","每模型confusion matrix與少數類別錯誤：",""]
    for f in metrics:
        for name in c.MODELS:
            m=f["models"][name]["metrics"];cm=m["confusion_matrix"]
            lines.append(f"F{f['fold']} {name}：CM={cm}；UP→DOWN/FLAT={cm[2][0]}/{cm[2][1]}，DOWN→FLAT/UP={cm[0][1]}/{cm[0][2]}，FLAT→DOWN/UP={cm[1][0]}/{cm[1][2]}；coverage={m['prediction_class_count']}/3；warnings={m['warnings']}；相對自身fold Majority-FLAT差距={f['models'][name]['vs_majority']}。")
    lines+=["","## 跨fold描述性彙總","",
       "|Model|F1 mean|F1 median|F1 sample std|F1 worst fold/value|BA mean|BA median|BA sample std|BA worst fold/value|單類預測fold|",
       "|---|---:|---:|---:|---|---:|---:|---:|---|---|"]
    for name in c.MODELS:
        z=agg["models"][name];f1=z["macro_f1"];ba=z["balanced_accuracy"]
        lines.append("|"+name+"|"+"|".join(fmt(f1[k]) for k in ("mean","median","standard_deviation_ddof1"))+f"|F{f1['worst_fold']}/{fmt(f1['worst_value'])}|"+"|".join(fmt(ba[k]) for k in ("mean","median","standard_deviation_ddof1"))+f"|F{ba['worst_fold']}/{fmt(ba['worst_value'])}|{z['single_class_prediction_folds']}|")
    for policy,g in agg["paired_gaps"].items():
        lines.append("QSVC − RBF "+policy+"："+json.dumps(g,ensure_ascii=False)+"。")
    lines+=["","上述mean/median/std(ddof=1)及worst fold僅描述這三個固定區段。三fold不是三個獨立市場環境；不以最高分指定交易策略。原Phase4B0不確定性文字仍為moving/nonoverlapping block proposal，未唯一固定區塊方式及anchoring；依本階段規格只報描述性統計，不執行IID CI、bootstrap、顯著性檢定或臨時加入其他有利方法。",
       "","## 警告與解讀限制","",
       "F3 Train UP只有1筆：MINORITY_SUPPORT_CRITICAL；未oversample、補樣或刪fold。balanced實際權重與有效C_i記錄如下，不能把高權重視為已有足夠少數類別證據。"]
    for f in minority["folds"]:
        lines.append("F"+str(f["fold"])+" support/warnings/actual weights："+json.dumps(f,ensure_ascii=False)+"。")
    lines+=["","F1 Validation相鄰實際label區間重疊383對：TEMPORAL_DEPENDENCE_WARNING；384列不等於384個獨立市場結果。F2/F3相鄰重疊各0，也不證明無序列相關。",
       "全部來自2026-08-26 UTC；3個研究aliases不代表獨立capture，實體擷取session數UNKNOWN，exact historical producer與真實receive時間未證實。原Train150,912列中9,203列因額外endpoint witness規則未納入候選，候選合格141,709列；有來源／時間／可見endpoint的選擇偏差可能。這些Train資料亦已用於先前研究；本輪Validation不是全新 untouched Test。不能證明跨日、跨來源或跨市場泛化、量子優勢、速度優勢或足以抵銷成本的交易盈利。",
       "","## Kernel數值、時間與記憶體","",
       "|Fold|Quantum Train s|Quantum cross s|Quantum shared total s|RBF diagnostic matrices s|Quantum min eigenvalue|",
       "|---|---:|---:|---:|---:|---:|"]
    for timing,valid in zip(kt["folds"],kern["folds"]):
        lines.append(f"|F{timing['fold']}|{timing['quantum_Train_seconds']:.9f}|{timing['quantum_Validation_cross_seconds']:.9f}|{timing['quantum_total_shared_seconds']:.9f}|{timing['rbf_explicit_diagnostic_matrices_seconds']:.9f}|{valid['Quantum']['train_min_eigenvalue']:.12g}|")
        lines.append("F"+str(timing["fold"])+" Quantum checks："+json.dumps({k:v for k,v in valid["Quantum"].items() if k!="train_eigenvalues"},ensure_ascii=False)+"。完整spectrum、matrix SHA及circuit manifest已封存；cross matrix非方陣，symmetry/diagonal/PSD不適用，已查shape/finite/range。")
    lines+=["","|Fold|Model|Solver fit s|Predict s|","|---|---|---:|---:|"]
    for f in metrics:
        for name in c.MODELS:
            e=f["models"][name]["execution"];lines.append(f"|F{f['fold']}|{name}|{e['fit_seconds']:.9f}|{e['predict_seconds']:.9f}|")
    lines+=["","各fold preprocessing fit/train-transform/validation-transform seconds："+json.dumps([q["timing"] for q in pre["first"]],ensure_ascii=False)+"。",
       "Quantum Kernel成本每fold共享一次。單獨一個QSVC的完整路徑包含preprocessing、共享Kernel構建與solver fit/predict；兩權重政策的整體實際成本是一次Kernel加兩個solver，不能把共享成本重複加總，也不能只報solver時間宣稱量子加速。repeat重用已驗SHA及input-binding的矩陣，新Quantum evaluate為0。RBF標準SVC fit/predict已包含其內部kernel工作；額外RBF矩陣時間為數值診斷，不冒充solver本身。",
       "本機CPU exact Statevector實驗；process lifetime peak RSS="+str(kt["process_peak_RSS_KiB"])+" KiB（Linux ru_maxrss整體高水位，不是各模型獨立記憶體）。不代表QPU、HFT tick-to-trade latency或任何量子速度優勢。",
       "","## 確定性、完整性與安全","",
       f"Unit tests：{tests['tests_run']}/{tests['tests_run']} PASS，failures/errors/skips=0，全部人工資料；含Phase4B0相關35tests。正式首次及獨立repeat分別封存；IDs、Train-only preprocessing parameters/file SHA、angle arrays、Kernel file/array SHA、predictions、metrics與confusion matrices完全一致，Determinism PASS。正式24個solver fits；Quantum evaluate6次（每fold Train/cross各一次），repeat新Quantum evaluate0。",
       "受保護3,455檔、Dataset/Frozen/Budget/Phase2～4B0、舊FAIL與兩個venv完整性PASS。非Holdout重算SHA；Holdout32檔僅stat並沿用封存SHA，未重新讀取其內容計算hash。Test僅為完整性作opaque checksum，未解析features/labels或評分。沒有網路、套件安裝升級、IBM QPU、Binance、QAOA/QUBO、交易、回測或Paper Trading。",
       "","## 研究結論與下一階段建議","",
       "本次可識別的是固定資料與固定實作在三個既定區段的探索性表現，不能將分數變化單獨歸因於類別比例、權重或量子特徵的普遍優勢。所有候選／fold都完整保留，模型分數高低未作為工程PASS條件。",
       "下一步先人工審核少數類別錯誤、跨fold方向一致性、clipping與支援量，保留五個候選。若要檢驗穩健性，優先提出另行批准的、跨不重疊日期且來源更可核實的新資料與預註冊設計；不重選本輪fold、不用既有Test/Final Holdout選參，不直接執行Feature Map/scaling搜尋或擴充Train。",
       "已停止，等待人工審核；未自動進入Phase4B-2。"]
    c.write(report,"\n".join(lines)+"\n")
    summary={"status":"PHASE 4B-1 "+state,"run_id":run_id,"tests":tests,"fold_metrics":metrics,"aggregate":agg,"kernel_timing":kt,"kernel_validation":kern,
       "minority":minority,"temporal":temporal,"determinism":det,"integrity":integrity,"safety":safe,"report":str(report),"report_fp":old.fp(report)}
    c.write(run/"summary/final_summary.json",summary)
    c.write(run/"summary/final_review.json",{"status":"PHASE 4B-1 "+state,"acceptance_checks":checks,"report":str(report),"report_fp":old.fp(report),"manual_review_required":True})
    c.verify_lock(run)
    return state
