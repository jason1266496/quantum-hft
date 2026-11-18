"""Verify the Frozen Train-only transform; never refit or choose new bounds."""
import hashlib,math,time
import numpy as np
from .contracts import FEATURES,array_sha
FORMULA_ATOL=1e-12
FORMULA_RTOL=1e-11
def transform(raw,params,*,split):
    if split not in ("Train","Validation"):raise ValueError("TEST_HOLDOUT_TRANSFORM_PROHIBITED")
    required=("out_of_range","constant_feature_angle","constant_features","z_train_min","z_train_max","angle_range_radians")
    if any(k not in params for k in required):raise ValueError("CLIPPING_OR_CONSTANT_POLICY_UNDEFINED")
    if params["feature_order"]!=list(FEATURES) or params["out_of_range"]!="clip":raise ValueError("FEATURE_OR_CLIP_POLICY_CHANGED")
    if params["angle_range_radians"]!=[0.,math.pi] or params["constant_feature_angle"]!=math.pi/2:raise ValueError("ANGLE_POLICY_CHANGED")
    if params["angle_fit_split"]!="Train" or params["validation_fit"] or params["test_read_or_transform"] or params["holdout_read_or_transform"]:raise ValueError("PREPROCESSING_LEAKAGE")
    b=params["base_standardization"]["parameters"]
    if b["fit_split"]!="Train" or b["fit_scope"]!="kernel_comparison_subset_v2" or b["n_samples_seen"]!=3000 or b["horizon_ms"]!=1000:raise ValueError("BASE_SCALER_UNIVERSE_CHANGED")
    if b["feature_order"]!=list(FEATURES) or any(b[k] for k in ("validation_fit","test_fit","holdout_transformed")):raise ValueError("BASE_SCALER_LEAKAGE_OR_ORDER_CHANGED")
    mean=np.asarray(b["mean"]);scale=np.asarray(b["scale"]);low=np.asarray(params["z_train_min"]);high=np.asarray(params["z_train_max"])
    const=np.asarray(params["constant_features"],dtype=bool)
    if any(v.shape!=(4,) for v in (mean,scale,low,high,const)) or not np.isfinite(np.r_[mean,scale,low,high]).all() or np.any(scale<=0) or np.any(high<low) or not np.array_equal(const,high==low):raise ValueError("INVALID_PARAMETERS")
    x=np.asarray([[float(r[f]) for f in FEATURES] for r in raw],dtype=np.float64)
    if not np.isfinite(x).all():raise ValueError("NONFINITE_RAW_FEATURE")
    z=(x-mean)/scale;theta=np.full(x.shape,math.pi/2,dtype=np.float64);varies=~const
    theta[:,varies]=math.pi*np.clip((z[:,varies]-low[varies])/(high[varies]-low[varies]),0,1)
    return theta,{"below_train_range_counts":np.sum(z<low,axis=0).tolist(),"above_train_range_counts":np.sum(z>high,axis=0).tolist(),
                  "raw_nonfinite_count":0,"angle_nonfinite_count":int(np.sum(~np.isfinite(theta))),"fit_performed":False}
def verify_profile(batch):
    start=time.perf_counter();p=batch["params"];train=batch["Train"]
    ids_hash=hashlib.sha256(("\n".join(train["ids"])+"\n").encode()).hexdigest()
    if ids_hash!=p["angle_fit_sample_ids_sha256"] or p["angle_fit_rows"]!=len(train["ids"]):raise ValueError("ANGLE_FIT_MEMBERSHIP_CHANGED")
    results={}
    for split in ("Train","Validation"):
        b=batch[split];theta,clip=transform(b["raw"],p,split=split)
        if not np.allclose(theta,b["x"],atol=FORMULA_ATOL,rtol=FORMULA_RTOL):raise ValueError("FROZEN_ANGLES_DO_NOT_MATCH_FORMULA")
        original=b["source"]["clip_counts_descriptive_only"]
        if any(clip[k]!=original[k] for k in ("above_train_range_counts","below_train_range_counts")):raise ValueError("CLIPPING_COUNTS_CHANGED")
        if b["x"].min()<0 or b["x"].max()>math.pi:raise ValueError("ANGLE_OUT_OF_RANGE")
        results[split]={"file_sha256":b["file_sha256"],"array_sha256":array_sha(b["x"]),"rows":len(b["ids"]),"feature_order":list(FEATURES),
                       "clip":clip,"nonfinite_input_count":int(np.sum(~np.isfinite(b["x"]))),"model_input":"exact Frozen shared-angle CSV values, not newly fitted values"}
    return {"status":"PASS","profile":batch["profile"],"parameters":p,"splits":results,"wall_seconds":time.perf_counter()-start,
         "new_preprocessing_fits":0,"formula_atol":FORMULA_ATOL,"formula_rtol":FORMULA_RTOL}
