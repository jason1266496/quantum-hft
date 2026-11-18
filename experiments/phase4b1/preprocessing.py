"""Frozen fold Train-only population scaling and angle mapping."""
import time
import numpy as np
from . import contracts as c
def matrix(x):
    a=np.asarray(x,dtype=np.float64)
    if a.ndim!=2 or a.shape[1]!=4 or len(a)<1 or not np.isfinite(a).all():raise ValueError("INVALID_FEATURE_MATRIX")
    return a
def fit(x):
    a=matrix(x)
    with np.errstate(over="raise",invalid="raise",divide="raise"):
        mean=a.mean(axis=0);std=a.std(axis=0,ddof=0);constant=(np.ptp(a,axis=0)==0)|(std==0)
        z=(a-mean)/np.where(constant,1.,std);lo=z.min(axis=0);hi=z.max(axis=0)
    if not all(np.isfinite(v).all() for v in (mean,std,lo,hi)):raise ValueError("NONFINITE_PREPROCESSING")
    return {"feature_order":list(c.FEATURES),"fit_rows":len(a),"mean":mean.tolist(),"population_std":std.tolist(),"z_Train_min":lo.tolist(),"z_Train_max":hi.tolist(),
      "constant_mask":constant.tolist(),"ddof":0,"constant_angle":float(np.pi/2),"formula":"z=(x-Train_mean)/Train_population_std; theta=pi*clip((z-z_Train_min)/(z_Train_max-z_Train_min),0,1)","fit_scope":"own selected Train only"}
def transform(x,p):
    a=matrix(x)
    for k in ("mean","population_std","z_Train_min","z_Train_max","constant_mask"):
        if k not in p or len(p[k])!=4:raise ValueError("MISSING_OR_INVALID_PREPROCESSING_"+k)
    mean=np.asarray(p["mean"]);std=np.asarray(p["population_std"]);lo=np.asarray(p["z_Train_min"]);hi=np.asarray(p["z_Train_max"]);const=np.asarray(p["constant_mask"],dtype=bool)
    z=(a-mean)/np.where(const,1.,std);u=(z-lo)/np.where(const,1.,hi-lo)
    low=(u<0)&~const;high=(u>1)&~const
    theta=np.pi*np.clip(u,0,1);theta[:,const]=np.pi/2
    if not np.isfinite(theta).all():raise ValueError("NONFINITE_ANGLES")
    return np.ascontiguousarray(theta,dtype=np.float64),{"clipped_below":low.sum(axis=0).tolist(),"clipped_above":high.sum(axis=0).tolist(),
      "constant_feature_Validation_deviations":((a!=mean)&const).sum(axis=0).tolist(),"nonfinite_values":0,"rows":len(a),"feature_order":list(c.FEATURES)}
def apply(train,val):
    start=time.perf_counter();p=fit(train);fit_s=time.perf_counter()-start
    start=time.perf_counter();tr,tmeta=transform(train,p);tr_s=time.perf_counter()-start
    start=time.perf_counter();va,vmeta=transform(val,p);va_s=time.perf_counter()-start
    return p,tr,va,{"Train":tmeta,"Validation":vmeta},{"fit_seconds":fit_s,"Train_transform_seconds":tr_s,"Validation_transform_seconds":va_s}
