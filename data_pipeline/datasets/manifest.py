"""Dataset v1 identity, frozen provenance, and holdout access contract."""
import copy,sys
from .schema import dataset_id,validate_run_id,HORIZONS,HOLDOUT_STATS_STATUS

C_RUN="20261019T001249Z"
D_RUN="20261026T193335Z"
E_RUN="20261026T195329Z"

def holdout_contract(upstream):
    value=copy.deepcopy(upstream)
    if value.get("holdout_status")!="LOCKED":raise ValueError("HOLDOUT_NOT_LOCKED")
    value.update({"model_access_policy":"PROHIBITED_UNTIL_FINAL_EVALUATION",
                  "hyperparameter_tuning":False,"feature_selection":False,"threshold_selection":False,
                  "scaler_fit":False,"quantum_feature_map_selection":False,"qaoa_parameter_selection":False,
                  "return_statistics":HOLDOUT_STATS_STATUS})
    return value

def make_manifest(view,run_id,policy,embargo,generator_version):
    created=validate_run_id(run_id).isoformat().replace("+00:00","Z")
    return {"dataset_id":dataset_id(view,run_id),"dataset_run_id":run_id,
            "project":"quantum-hft","market":"BTCUSDT","feature_view":view,
            "feature_version":view,"label_version":"1.0",
            "horizons_ms":list(HORIZONS),"ordering_field":"event_time_ms",
            "local_timestamp_used":False,"cross_session_labels":False,"shuffled":False,
            "match_error_policy":copy.deepcopy(policy),"purge_enabled":True,
            "embargo_ms":embargo["embargo_ms"],"final_holdout_locked":True,
            "scaler_fitted":False,"class_labels_present":False,"model_training_performed":False,
            "source_phase2c_run_id":C_RUN,"source_phase2d_run_id":D_RUN,"source_phase2e_run_id":E_RUN,
            "created_at_utc":created,"creation_time_basis":"UTC DATASET_RUN_ID, fixed for both packaging executions",
            "generator_version":generator_version,"python_version":sys.version,
            "holdout_return_statistics":HOLDOUT_STATS_STATUS,
            "smoke_reference_only_source":"replay_events_1000",
            "dataset_status":"LOCKED_DATASET_V1",
            "validation_evidence":"external artifacts/phase2f/"+run_id,
            "sample_id_reused_across_horizons":True}
