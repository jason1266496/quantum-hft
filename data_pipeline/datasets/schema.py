"""Stable sample identity and a documented projection of approved source schemas."""
from datetime import datetime,timezone
from decimal import Decimal,Context,ROUND_HALF_EVEN
import hashlib,json,re
HORIZONS=(100,200,500,1000)
SPLITS=("Train","Validation","Test","Final Holdout")
SLUG={"Train":"train","Validation":"validation","Test":"test","Final Holdout":"final_holdout"}
VIEWS={"aggregate_core_v1":"btcusdt_aggregate_v1","depth_top5_v1":"btcusdt_depth_top5_v1"}
IDENTITY_FIELDS=("feature_view","source_id","session_id","record_index","event_time_ms")
SHARED_LABEL_FIELDS=frozenset(("feature_view","source_id","session_id","record_index"))
FORBIDDEN_COLUMNS=frozenset(("local_timestamp_us","UP","DOWN","FLAT","binary_target",
 "target_class","class_label","model_score","prediction","scaler_mean","scaler_std"))
CONTEXT=Context(prec=50,rounding=ROUND_HALF_EVEN)
HOLDOUT_STATS_STATUS="NOT_COMPUTED_HOLDOUT_LOCKED"

def validate_run_id(value):
    if not re.fullmatch(r"[0-9]{8}T[0-9]{6}Z",value):raise ValueError("INVALID_DATASET_RUN_ID")
    return datetime.strptime(value,"%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)

def dataset_id(view,run_id):
    validate_run_id(run_id)
    if view not in VIEWS:raise ValueError("UNKNOWN_FEATURE_VIEW")
    return VIEWS[view]+"_"+run_id

def identity_document(row):
    value={name:row[name] for name in IDENTITY_FIELDS}
    if value["feature_view"] not in VIEWS:raise ValueError("INVALID_FEATURE_VIEW")
    for name in ("source_id","session_id"):
        if type(value[name]) is not str or not value[name]:raise ValueError("INVALID_IDENTITY")
    for name in ("record_index","event_time_ms"):
        raw=value[name]
        if type(raw) not in (int,str) or not re.fullmatch(r"[0-9]+",str(raw)):
            raise ValueError("INVALID_IDENTITY_INTEGER")
        value[name]=int(raw)
    if value["record_index"]<1:raise ValueError("INVALID_RECORD_INDEX")
    return value

def identity_bytes(row):
    return json.dumps(identity_document(row),sort_keys=True,ensure_ascii=False,separators=(",",":")).encode("utf-8")

def sample_id(row):return hashlib.sha256(identity_bytes(row)).hexdigest()

def decimal_text(value):
    if type(value) is not Decimal or not value.is_finite():raise ValueError("FINITE_DECIMAL_REQUIRED")
    if value==0:return "0"
    text=format(value,"f")
    return text.rstrip("0").rstrip(".") if "." in text else text

def columns(feature_schema,label_schema):
    features=feature_schema["field_order"];labels=label_schema["field_order"]
    if len(set(features))!=len(features) or len(set(labels))!=len(labels):raise ValueError("DUPLICATE_SOURCE_COLUMN")
    if set(features)&FORBIDDEN_COLUMNS or set(labels)&FORBIDDEN_COLUMNS:raise ValueError("FORBIDDEN_COLUMN")
    result=["sample_id",*features];mapping={}
    for name in labels:
        if name in SHARED_LABEL_FIELDS:continue
        output="label_invalid_reason" if name=="invalid_reason" else name
        if output in result:raise ValueError("UNDOCUMENTED_JOIN_COLLISION")
        result.append(output);mapping[name]=output
    required={"future_return_bps","future_mid_price","requested_horizon_ms","actual_horizon_ms","match_error_ms","valid_label"}
    if not required<=set(result):raise ValueError("LABEL_INTERFACE_GAP")
    return result,mapping

def dataset_schema(feature_schema,label_schema):
    fields,mapping=columns(feature_schema,label_schema)
    return {"schema_version":"1.0","field_order":fields,"feature_columns":feature_schema["field_order"],
            "label_column_mapping":mapping,"encoding":"UTF-8","newline":"LF",
            "numeric_policy":"copy approved canonical decimal strings; no feature/return recomputation",
            "sample_id":{"algorithm":"SHA-256","identity_fields":list(IDENTITY_FIELDS),
                         "canonical":"UTF-8 JSON, sorted keys, compact separators, integer metadata typed as int",
                         "excludes":["future_return","target_event_time","split","horizon","execution_time"],
                         "uniqueness_scope":"one horizon across all splits; same event intentionally reuses ID across horizons"},
            "local_timestamp_used":False,"class_labels":False,"holdout_return_statistics":HOLDOUT_STATS_STATUS}
