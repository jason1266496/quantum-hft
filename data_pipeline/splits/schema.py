"""Fixed metadata-only split schema; no market features or returns copied."""
from dataclasses import dataclass
from decimal import Decimal, Context, ROUND_HALF_EVEN

HORIZONS=(100,200,500,1000)
SPLITS=("Train","Validation","Test","Final Holdout")
VIEWS=("aggregate_core_v1","depth_top5_v1")
PHASE2C_RUN="20261019T001249Z"
PHASE2D_RUN="20261026T193335Z"
SMOKE_SOURCE="replay_events_1000"
INDEX_FIELDS=("feature_view","source_id","session_id","record_index","event_time_ms",
              "event_identity","requested_horizon_ms","target_event_time_ms","split")
RAW_FIELDS=("feature_view","source_id","session_id","record_index","event_time_ms",
            "event_identity","split")
EXCLUDED_FIELDS=INDEX_FIELDS+("reason",)
CONTEXT=Context(prec=50,rounding=ROUND_HALF_EVEN)

@dataclass(frozen=True,slots=True)
class FeatureIndex:
    source_id:str
    session_id:str
    feature_view:str
    record_index:int
    event_time_ms:int
    event_identity:str
    @property
    def key(self):
        return self.source_id,self.session_id,self.record_index

@dataclass(frozen=True,slots=True)
class LabelIndex:
    target_event_time_ms:int|None
    match_error_ms:int|None
    valid_label:bool
    invalid_reason:str

@dataclass(slots=True)
class SourceData:
    source_id:str
    session_id:str
    feature_view:str
    rows:list
    labels:dict
    feature_sha256:str
    label_sha256:dict

def decimal_text(value):
    text=format(Decimal(value),"f")
    return (text.rstrip("0").rstrip(".") if "." in text else text) or "0"

def schema_document():
    return {"schema_version":"1.0","horizons_ms":list(HORIZONS),"splits":list(SPLITS),
            "index_fields":list(INDEX_FIELDS),"raw_assignment_fields":list(RAW_FIELDS),
            "excluded_fields":list(EXCLUDED_FIELDS),"ordering_field":"event_time_ms",
            "local_timestamp_used":False,"class_labels":False,"models":False,
            "view_pools_separate":True,"shuffle":False}
