"""Fixed compact features, with metadata and future labels excluded."""
import numpy as np
FEATURES=("obi_5","spread_bps","bid_volume_5","ask_volume_5")
HORIZONS=(100,1000)
VIEW="aggregate_core_v1"
def policy():
    return {"policy_id":"aggregate_compact_v1","feature_view":VIEW,"feature_order":list(FEATURES),
            "horizons_ms":list(HORIZONS),"feature_selection_performed":False,
            "metadata_or_label_columns_included":False,"model_dtype":"numpy.float64",
            "source_values":"approved canonical decimal strings; float64 conversion only for sklearn input"}
def validate_scope(view,horizon):
    if view!=VIEW or horizon not in HORIZONS:raise ValueError("PHASE3A_SCOPE_PROHIBITED")
def matrix(rows):
    x=np.asarray([[float(row[name]) for name in FEATURES] for row in rows],dtype=np.float64)
    if x.ndim!=2 or x.shape[1]!=4 or not np.isfinite(x).all():raise ValueError("INVALID_FEATURE_MATRIX")
    return x
