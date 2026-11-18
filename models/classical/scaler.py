"""One Train fit per explicit universe; no Holdout access or transform."""
import hashlib
import numpy as np
import sklearn
from sklearn.preprocessing import StandardScaler
from .feature_policy import FEATURES
class TrainOnlyScaler:
    def __init__(self,horizon,scope):
        self.horizon=horizon;self.scope=scope;self.scaler=StandardScaler();self.fitted=False
    def fit(self,x,*,split,sample_ids):
        if split!="Train" or self.fitted:raise ValueError("SCALER_FIT_MUST_BE_TRAIN_ONCE")
        if len(x)!=len(sample_ids):raise ValueError("SCALER_UNIVERSE_MISMATCH")
        self.scaler.fit(x);self.fitted=True
        self.ids_hash=hashlib.sha256(("\n".join(sample_ids)+"\n").encode()).hexdigest()
        return self
    def transform(self,x,*,split):
        if split not in ("Train","Validation","Test") or not self.fitted:raise ValueError("SCALER_TRANSFORM_SCOPE_PROHIBITED")
        return self.scaler.transform(x)
    def artifact(self):
        if not self.fitted:raise ValueError("SCALER_NOT_FITTED")
        return {"feature_order":list(FEATURES),"horizon_ms":self.horizon,"fit_split":"Train",
                "fit_scope":self.scope,"fit_sample_ids_sha256":self.ids_hash,
                "mean":self.scaler.mean_.tolist(),"scale":self.scaler.scale_.tolist(),"var":self.scaler.var_.tolist(),
                "n_samples_seen":int(self.scaler.n_samples_seen_),"sklearn_version":sklearn.__version__,
                "holdout_transformed":False,"validation_fit":False,"test_fit":False}
