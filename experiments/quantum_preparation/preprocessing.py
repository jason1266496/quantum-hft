"""Read the Frozen Train-only standardization; fit budget-Train-only angle bounds."""
import hashlib,math
import numpy as np
from .io import FEATURES
from models.classical.feature_policy import matrix
class SharedAngleInput:
    def __init__(self,base_scaler,profile):
        self.base=base_scaler;self.profile=profile;self.fitted=False
        if base_scaler["feature_order"]!=list(FEATURES) or base_scaler["fit_split"]!="Train" or base_scaler["fit_scope"]!="kernel_comparison_subset_v2":
            raise ValueError("INVALID_FROZEN_TRAIN_SCALER")
        if base_scaler["n_samples_seen"]!=3000 or base_scaler["horizon_ms"]!=1000:raise ValueError("WRONG_FROZEN_SCALER_UNIVERSE")
        if any(base_scaler[k] for k in ("validation_fit","test_fit","holdout_transformed")):raise ValueError("LEAKED_BASE_SCALER")
        self.mean=np.asarray(base_scaler["mean"],dtype=float);self.scale=np.asarray(base_scaler["scale"],dtype=float)
        if self.mean.shape!=(4,) or self.scale.shape!=(4,) or not np.isfinite(self.mean).all() or not np.isfinite(self.scale).all() or np.any(self.scale<=0):
            raise ValueError("INVALID_BASE_PARAMETERS")
    def standardize(self,rows):return (matrix(rows)-self.mean)/self.scale
    def fit(self,rows,*,split="Train"):
        if split!="Train" or self.fitted:raise ValueError("ANGLE_FIT_TRAIN_ONCE_ONLY")
        z=self.standardize(rows)
        if not len(z):raise ValueError("EMPTY_TRAIN")
        self.low=z.min(axis=0);self.high=z.max(axis=0);self.constant=self.high==self.low
        self.ids_hash=hashlib.sha256(("\n".join(r["sample_id"] for r in rows)+"\n").encode()).hexdigest()
        self.n=len(rows);self.fitted=True;return self
    def transform(self,rows,*,split):
        if split not in ("Train","Validation") or not self.fitted:raise ValueError("ANGLE_TRANSFORM_TEST_HOLDOUT_PROHIBITED")
        z=self.standardize(rows);angles=np.full(z.shape,math.pi/2,dtype=float);varies=~self.constant
        angles[:,varies]=math.pi*np.clip((z[:,varies]-self.low[varies])/(self.high[varies]-self.low[varies]),0.,1.)
        info={"split":split,"rows":len(rows),"below_train_range_counts":np.sum(z<self.low,axis=0).tolist(),
              "above_train_range_counts":np.sum(z>self.high,axis=0).tolist(),"range_policy":"clip to [0,pi]; Train-constant feature always pi/2",
              "fit_performed":False}
        return angles,info
    def artifact(self):
        if not self.fitted:raise ValueError("ANGLE_NOT_FITTED")
        return {"representation_id":"shared_budget_angles_v1","profile":self.profile,"feature_order":list(FEATURES),
            "base_standardization":{"source":"Phase3B Frozen 1000ms scaler; no refit","parameters":self.base,"fit_scope":"subset v2 Train 3000"},
            "angle_fit_split":"Train","angle_fit_scope":"this budget Train only","angle_fit_rows":self.n,"angle_fit_sample_ids_sha256":self.ids_hash,
            "z_train_min":self.low.tolist(),"z_train_max":self.high.tolist(),"constant_features":self.constant.tolist(),
            "angle_range_radians":[0.,math.pi],"out_of_range":"clip","constant_feature_angle":math.pi/2,
            "validation_fit":False,"test_read_or_transform":False,"holdout_read_or_transform":False,
            "effective_nonconstant_map":"pi * clip((raw_feature - budget_Train_min)/(budget_Train_max-budget_Train_min),0,1)",
            "note":"Positive Frozen standardization cancels algebraically in min-max angles. New effective ranges use only this budget Train; old Frozen scaler parameters remain unchanged.",
            "RBF_QSVC_shared_input":True}
def kernel_budget(n,validation):
    return {"train_shape":[n,n],"train_elements":n*n,"train_float64_bytes":n*n*8,
        "validation_vs_train_shape":[validation,n],"validation_elements":validation*n,"validation_float64_bytes":validation*n*8,
        "combined_float64_bytes":(n*n+validation*n)*8,"combined_KiB":(n*n+validation*n)*8/1024,
        "qubits":4,"statevector_dimension":16,"statevector_complex128_bytes_per_state":256,
        "scope":"theoretical dense arrays only; excludes simulator/SVC/cache overhead","actual_quantum_runtime":"NOT_EXECUTED_NOT_ESTIMATED"}
def fair_policy():
    return {"version":"fair_budget_comparison_v1","horizon_ms":1000,"feature_order":list(FEATURES),
        "feature_view":"aggregate_core_v1","label_policy":"direction_3class_exact_v1",
        "budget_membership":"both RBF and QSVC must use identical raw CSV, labels, IDs, ordering and shared input CSV per profile",
        "C":100.0,"RBF":{"kernel":"rbf","gamma":0.01,"class_weight":"balanced","probability":False,
                       "gamma_source":"fixed previously Validation-selected Phase3B 1000ms gamma; not retuned"},
        "QSVC":{"kernel":"FidelityStatevectorKernel","class_weight":"balanced","C":100.0},
        "preprocessing":"Frozen v2 Train-only StandardScaler parameters retained; angle bounds fit this budget Train only; same angles for RBF/QSVC",
        "reference_standardized_representation":"recorded z differs from bounded [0,pi] angles; old 3000-row model scores are not a same-budget comparator",
        "RBF_refit_required_in_phase4a1":True,"old_fitted_RBF_reuse_allowed":False,"random_state_if_supported":42,
        "hyperparameter_or_feature_map_search":False,"Test_allowed":False,"Final_Holdout_allowed":False,
        "new_model_fits_in_phase4a0":0,"formal_kernel_evaluations_in_phase4a0":0,
        "phase3b_baseline_instability_preserved":True,"quantum_advantage_assumed":False}
