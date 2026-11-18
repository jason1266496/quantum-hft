"""Diagnose hash-verified, own-origin v1 objects; no refit or new Test scoring."""
import csv,pickle
import numpy as np
from sklearn.svm import SVC
from models.classical.feature_policy import matrix
from models.classical.label_policy import labels
from data_pipeline.datasets.checksums import fingerprint,sha_file
from .freeze import OLD,FEATURES,NAMES,read,utc
from .metrics import distribution,feature_profile,numeric_stats,prediction_distribution,prediction_distribution_from_confusion
def temporal_profile(rows):
    groups={}
    for row in rows:groups.setdefault((row["source_id"],row["session_id"]),[]).append(int(row["event_time_ms"]))
    def describe(times):
        a=sorted(times);span=a[-1]-a[0]
        return {"rows":len(a),"first_event_time_ms":a[0],"last_event_time_ms":a[-1],"event_time_span_ms":span,
                "rows_per_second_over_span":len(a)*1000/span if span else None,
                "maximum_temporal_gap_ms":max((b-a for a,b in zip(a,a[1:])),default=0),
                "median_temporal_gap_ms":float(np.median(np.diff(a))) if len(a)>1 else 0}
    return {"global":describe([int(r["event_time_ms"]) for r in rows]),
            "per_source_session":[{"source_id":s,"session_id":q,**describe(t)} for (s,q),t in sorted(groups.items())],
            "gap_semantics":"global may span sessions; per_source_session gaps are reported separately"}
def load_trusted_object(path,expected):
    if fingerprint(path)!=expected:raise ValueError("OLD_MODEL_HASH_MISMATCH")
    if not PathAllowed(path):raise ValueError("UNTRUSTED_MODEL_ORIGIN")
    with path.open("rb") as f:obj=pickle.load(f)
    if not isinstance(obj,dict) or not isinstance(obj.get("model"),SVC):raise ValueError("UNEXPECTED_OWN_MODEL_TYPE")
    return obj
def PathAllowed(p):
    from pathlib import Path
    from .freeze import ROOT
    return p.is_relative_to(OLD) or p.is_relative_to(ROOT/"tests/fixtures/phase3b")
def original_diagnostics(protected):
    results={}
    for h in (1000,100):
        folder=OLD/(str(h)+"ms");rbf=folder/"rbf_svm"
        expected=protected[str(rbf/"model.pkl")]
        obj=load_trusted_object(rbf/"model.pkl",expected)
        model,scaler=obj["model"],obj["scaler"]
        batches={}
        for split in ("Train","Validation","Test"):
            with (folder/"kernel_subset"/(split.lower()+".csv")).open(newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
            x=matrix(rows);y=labels(rows);z=scaler.transform(x)
            decisions=np.asarray(model.decision_function(z))
            predfile=rbf/(split.lower()+"_predictions.csv")
            if predfile.exists():
                with predfile.open(newline="",encoding="utf-8") as f:pred_rows=list(csv.DictReader(f))
                assert [r["sample_id"] for r in pred_rows]==[r["sample_id"] for r in rows]
                predictions=prediction_distribution([int(r["predicted_class"]) for r in pred_rows])
            else:
                saved_metric=rbf/(split.lower()+"_metrics.json")
                if saved_metric.exists():
                    predictions=prediction_distribution_from_confusion(read(saved_metric)["confusion_matrix"])
                    predictions["source"]="sealed confusion-matrix column totals; no new predict call"
                else:predictions={"status":"NOT_AVAILABLE","reason":"No saved predictions or confusion matrix; no new predict call"}
            batches[split]={"rows":len(rows),"class_distribution":distribution(rows),
                "temporal":temporal_profile(rows),"features":feature_profile(rows),
                "scaled_features":{name:numeric_stats(z[:,i]) for i,name in enumerate(FEATURES)},
                "prediction_distribution":predictions,"decision_function_by_class":{name:numeric_stats(decisions[:,i]) for i,name in enumerate(NAMES)},
                "decision_argmax_distribution":prediction_distribution(np.argmax(decisions,axis=1)),
                "sample_ids_unique":len({r["sample_id"] for r in rows})==len(rows),
                "labels_match_saved":all(int(r["class_label"])==int(y[i]) for i,r in enumerate(rows))}
            if split=="Train":
                mean=x.mean(axis=0);var=x.var(axis=0)
                scaler_ok=bool(np.allclose(mean,scaler.mean_,rtol=1e-12,atol=1e-12) and np.allclose(var,scaler.var_,rtol=1e-12,atol=1e-12))
                train_ranges=(x.min(axis=0),x.max(axis=0));train_counts=distribution(rows)["counts"]
            else:
                batches[split]["outside_train_feature_minmax_counts"]={name:int(np.sum((x[:,i]<train_ranges[0][i])|(x[:,i]>train_ranges[1][i]))) for i,name in enumerate(FEATURES)}
        observed="FLAT" if h==100 else "UP"
        reasons={
          "single_class_prediction":{"status":"OBSERVED","description":f"封存 Test predictions 全為 {observed}；固定模型下的 decision function 分布另存，沒有重新評分。單一因果歸因 INSUFFICIENT_EVIDENCE。"},
          "missing_minority_train_classes":{"status":"REJECTED_BY_COUNTS","counts":train_counts,"missing":any(v==0 for v in train_counts.values())},
          "temporal_sampling_class_coverage":{"status":"OBSERVED_IMBALANCE_NOT_MISSING","description":"v1 非 class-aware；全部類別有樣本，但支持數不均。無對照干預，是否為充分成因 INSUFFICIENT_EVIDENCE。"},
          "scaler_fault":{"status":"NO_FAULT_DETECTED" if scaler_ok else "SCALER_MISMATCH","train_population_mean_var_match":scaler_ok},
          "hyperparameter_cause":{"status":"INSUFFICIENT_EVIDENCE","description":"只知封存 Validation 選 C=10 gamma=0.1；沒有 Test 上的替代參數實驗，不歸因單一超參數。"},
          "distribution_shift":{"status":"DESCRIPTIVE_DIFFERENCES_RECORDED","description":"class proportions、source/session、feature median/IQR 與 range 越界另存；不是因果證明。"},
          "data_error":{"status":"NO_ERROR_DETECTED_WITHIN_CHECKED_SCOPE","description":"v1 artifacts/checksums 已驗證，IDs、exact labels、有限 features、Train-only scaler 通過；未獨立重建 HFT 原始資料。"},
          "root_cause_certainty":"INSUFFICIENT_EVIDENCE"}
        if not scaler_ok or not all(v["sample_ids_unique"] and v["labels_match_saved"] for v in batches.values()):raise ValueError("OLD_SUBSET_DATA_ERROR")
        results[str(h)]={"scope":"APPROVED_V1_DIAGNOSTIC_ONLY_NOT_V2_SELECTION","started_at_utc":utc(),"splits":batches,
            "scaler_parameters":read(rbf/"scaler.json"),"scaler_checked_against_subset_train":scaler_ok,
            "selected_config":read(rbf/"config.json")["selected_config"],
            "support_vectors_per_class":{name:int(model.n_support_[i]) for i,name in enumerate(NAMES)},
            "effective_gamma":float(model._gamma),"confusion_matrix":read(rbf/"test_metrics.json")["confusion_matrix"],
            "per_class_metrics":read(rbf/"test_metrics.json")["per_class"],"answers":reasons,
            "model_sha256":sha_file(rbf/"model.pkl"),"model_refit":False,"new_predict_calls":0,
            "decision_function_calls":3,"new_test_metric_evaluations":0}
    return results
