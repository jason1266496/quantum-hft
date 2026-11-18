"""Small, deterministic algebraic diagnostics. No estimators, circuits, or sampling."""
import numpy as np
NAMES=("DOWN","FLAT","UP")
FEATURES=("obi_5","spread_bps","bid_volume_5","ask_volume_5")
TOL=1e-10

def bounded(x,columns=None):
    a=np.asarray(x,dtype=float)
    if a.ndim!=2 or not 1<=len(a)<=96 or (columns is not None and a.shape[1]!=columns) or not np.isfinite(a).all():
        raise ValueError("INVALID_OR_LARGE_ARRAY")
    return a

def stats(v):
    v=np.asarray(v,dtype=float).ravel()
    if not len(v):return {"count":0}
    if not np.isfinite(v).all():raise ValueError("NONFINITE")
    q=np.quantile(v,[0,.05,.25,.5,.75,.95,1])
    return dict(count=len(v),min=float(q[0]),q05=float(q[1]),q25=float(q[2]),median=float(q[3]),q75=float(q[4]),q95=float(q[5]),max=float(q[6]),mean=float(v.mean()),std_population=float(v.std()),iqr=float(q[4]-q[2]),unique_values=int(len(np.unique(v))))

def distribution(y):
    y=np.asarray(y)
    if y.ndim!=1 or not len(y) or not np.isin(y,[0,1,2]).all():raise ValueError("INVALID_LABEL")
    return {n:{"count":int(np.sum(y==i)),"proportion":float(np.mean(y==i))} for i,n in enumerate(NAMES)}

def imbalance(train,validation):
    a=distribution(train);b=distribution(validation)
    p=np.array([a[n]["proportion"] for n in NAMES]);q=np.array([b[n]["proportion"] for n in NAMES]);m=(p+q)/2
    kl=lambda x:float(np.sum(x[x>0]*np.log2(x[x>0]/m[x>0])))
    return {"Train":a,"Validation":b,"total_variation_distance":float(abs(p-q).sum()/2),"jensen_shannon_divergence_bits":(kl(p)+kl(q))/2,
            "balanced_class_weights_on_actual_Train":{n:float(len(train)/(3*a[n]["count"])) if a[n]["count"] else "NOT_DEFINED" for n in NAMES},
            "causal_note":"CONFIRMED prior distribution difference; not a uniquely proven causal explanation.",
            "one_rare_Validation_error_recall_change":{n:1/b[n]["count"] if b[n]["count"] else None for n in NAMES},
            "inference_limit":"Only 5 observations per rare Validation class; temporally dependent pairs/overlapping labels are not independent replicates. No resampling or IID confidence intervals."}

def confusion(y,p):
    y=np.asarray(y);p=np.asarray(p)
    distribution(y);distribution(p)
    if y.shape!=p.shape:raise ValueError("LABEL_SHAPE")
    cm=np.zeros((3,3),dtype=int)
    np.add.at(cm,(y.astype(int),p.astype(int)),1)
    per={}
    for i,n in enumerate(NAMES):
        tp=int(cm[i,i]);support=int(cm[i].sum());pred=int(cm[:,i].sum())
        precision=tp/pred if pred else 0.;recall=tp/support if support else 0.
        per[n]={"support":support,"predicted":pred,"precision":precision,"recall":recall,"f1":2*precision*recall/(precision+recall) if precision+recall else 0.}
    return {"class_order":list(NAMES),"matrix_orientation":"row=true, column=predicted","confusion_matrix":cm.tolist(),"per_class":per,
            "true_distribution":distribution(y),"predicted_distribution":distribution(p),"macro_f1":float(np.mean([v["f1"] for v in per.values()])),
            "balanced_accuracy":float(np.mean([v["recall"] for v in per.values()])),"accuracy":float(np.trace(cm)/len(y))}

def rbf(x,y,gamma=.01):
    x=bounded(x,4);y=bounded(y,4)
    if gamma!=.01:raise ValueError("FIXED_GAMMA_REQUIRED")
    return np.exp(-gamma*np.sum((x[:,None,:]-y[None,:,:])**2,axis=2))

def centered(k):
    return k-k.mean(axis=0,keepdims=True)-k.mean(axis=1,keepdims=True)+k.mean()

def alignment(a,b):
    a=centered(np.asarray(a));b=centered(np.asarray(b))
    den=float(np.linalg.norm(a)*np.linalg.norm(b))
    return float(np.sum(a*b)/den) if den>1e-20 else None

def class_similarity(k,y):
    k=bounded(k);y=np.asarray(y)
    if k.shape!=(len(y),len(y)):raise ValueError("KERNEL_LABEL_SHAPE")
    ii,jj=np.triu_indices(len(y),1);same=y[ii]==y[jj];v=k[ii,jj]
    within=stats(v[same]);between=stats(v[~same]);blocks={}
    for a in range(3):
        for b in range(a,3):
            take=((y[ii]==a)&(y[jj]==b))|((y[ii]==b)&(y[jj]==a))
            blocks[NAMES[a]+"/"+NAMES[b]]=stats(v[take])
    return {"pair_policy":"unique upper-triangle pairs, diagonal excluded; no significance claim from dependent pairs",
            "within_class":within,"between_class":between,"within_minus_between_mean":float(within["mean"]-between["mean"]) if same.any() and (~same).any() else None,
            "class_pairs":blocks}

def cross_similarity(k,yval,ytrain):
    k=bounded(k)
    if k.shape!=(len(yval),len(ytrain)):raise ValueError("CROSS_SHAPE")
    return {NAMES[a]+"/"+NAMES[b]:stats(k[np.ix_(np.asarray(yval)==a,np.asarray(ytrain)==b)]) for a in range(3) for b in range(3)}

def spectrum(k):
    k=bounded(k)
    if k.shape[0]!=k.shape[1]:raise ValueError("SQUARE_REQUIRED")
    sym=float(abs(k-k.T).max())
    if sym>TOL:raise ValueError("ASYMMETRIC")
    eig=np.linalg.eigvalsh(k);sv=np.linalg.svd(k,compute_uv=False)
    if eig[0]<-TOL:raise ValueError("NOT_PSD_WITHIN_TOLERANCE")
    positive=eig[eig>0];p=positive/positive.sum()
    threshold=max(TOL,1e-12*float(eig[-1]));rank=int(np.sum(eig>threshold))
    return {"shape":list(k.shape),"symmetry_max_error":sym,"diagonal":stats(np.diag(k)),"diagonal_one_max_error":float(abs(np.diag(k)-1).max()),
            "finite_real":True,"eigenvalues_ascending":eig.tolist(),"minimum_eigenvalue":float(eig[0]),"maximum_eigenvalue":float(eig[-1]),
            "PSD_tolerance":TOL,"negative_eigenvalue_count":int(np.sum(eig<0)),"numerical_rank":rank,"rank_threshold":threshold,
            "entropy_effective_rank":float(np.exp(-np.sum(p*np.log(p)))),"participation_ratio":float(eig.sum()**2/np.sum(eig**2)),
            "leading_eigenvalue_trace_fraction":float(eig[-1]/eig.sum()),
            "condition_number_at_declared_rank_tolerance":float(sv[0]/sv[-1]) if rank==len(k) else "INFINITE_AT_DECLARED_RANK_TOLERANCE",
            "raw_svd_condition_estimate":float(sv[0]/sv[-1]) if sv[-1]>0 else "INFINITE",
            "effective_rank_definition":"exp(-sum(p log p)), p=positive eigenvalues / sum(positive eigenvalues); participation ratio=(sum lambda)^2/sum(lambda^2). Tiny negative roundoff excluded only from entropy; stored matrix NEVER repaired.",
            "matrix_modified":False}

def kernel_diagnostics(k,cross,y,yv):
    out=spectrum(k);off=k[np.triu_indices(len(k),1)];s=stats(off);cv=float(off.std()/abs(off.mean())) if off.mean()!=0 else None
    out.update({"off_diagonal":s,"off_diagonal_cv":cv,"concentration_empirical_flag":bool(s["std_population"]<=.05 and cv is not None and cv<=.1),
        "concentration_rule":"Diagnostic-only near-constant flag: off-diagonal population std <=0.05 AND CV<=0.10, declared before formal analysis. Not a universal quantum concentration theorem.",
        "asymptotic_kernel_concentration":"INSUFFICIENT_EVIDENCE: one fixed 4-qubit matrix cannot establish scaling with dimension",
        "class_similarity":class_similarity(k,y),"validation_by_true_class_train_similarity":cross_similarity(cross,yv,y),
        "centered_label_kernel_alignment":alignment(k,np.equal.outer(y,y).astype(float)),
        "validation_kernel_shape":list(cross.shape),"validation_values":stats(cross),
        "validation_self_kernel":"NOT_AVAILABLE: saved matrix is Validation x Train, not Validation x Validation. No new quantum evaluations.",
        "interpretation_limit":"Class mean/max similarities are descriptive, not the trained SVM decision function or causal proof."})
    return out

def verify_identity(expected,actual):
    for k in ("ids","file_sha256","array_sha256","labels_sha256"):
        if expected[k]!=actual[k]:raise ValueError("INPUT_IDENTITY_MISMATCH_"+k)
    return True

def transform(raw,params):
    raw=bounded(raw,4);base=params["base_standardization"]["parameters"]
    scale=np.array(base["scale"])
    if np.any(scale<=0):raise ValueError("NONPOSITIVE_SCALE")
    z=(raw-base["mean"])/scale;lo=np.array(params["z_train_min"]);hi=np.array(params["z_train_max"])
    const=np.array(params["constant_features"],dtype=bool)
    if np.any((hi<=lo)&~const):raise ValueError("BAD_BOUNDS")
    unit=(z-lo)/np.where(const,1,hi-lo)
    angle=np.pi*np.clip(unit,0,1);angle[:,const]=params["constant_feature_angle"]
    return angle,{"below_train_range_counts":np.sum(z<lo-1e-12,axis=0).tolist(),"above_train_range_counts":np.sum(z>hi+1e-12,axis=0).tolist(),
                  "constant_features":const.tolist(),"fits_performed":0}

def feature_distributions(raw,angles):
    out={}
    for i,n in enumerate(FEATURES):
        hist=np.histogram(angles[:,i],bins=10,range=(0,np.pi))[0];p=hist[hist>0]/len(angles)
        out[n]={"raw":stats(raw[:,i]),"angles":stats(angles[:,i]),"raw_constant":bool(np.ptp(raw[:,i])==0),
                "angle_constant":bool(np.ptp(angles[:,i])==0),"angle_histogram_10_equal_bins":hist.tolist(),
                "angle_histogram_entropy_bits":float(-np.sum(p*np.log2(p))),"angle_q05_q95_width_over_pi":float(np.diff(np.quantile(angles[:,i],[.05,.95]))[0]/np.pi)}
    return out

def phase_coefficients(x):
    x=bounded(x,4)
    return np.column_stack([2*x,2*(np.pi-x[:,:-1])*(np.pi-x[:,1:])])

def periodicity(x,k,ids):
    x=bounded(x,4);k=bounded(k)
    if k.shape!=(len(x),len(x)) or len(ids)!=len(x):raise ValueError("PERIODICITY_SHAPE")
    ii,jj=np.triu_indices(len(x),1);dist=np.linalg.norm(x[ii]-x[jj],axis=1);cut=float(np.quantile(dist,.9))
    coeff=phase_coefficients(x);delta=coeff[ii]-coeff[jj]
    circular=np.sqrt(np.mean(np.arctan2(np.sin(delta),np.cos(delta))**2,axis=1))
    pick=np.flatnonzero((dist>=cut)&(k[ii,jj]>=.9))
    examples=[{"sample_id_a":ids[int(ii[t])],"sample_id_b":ids[int(jj[t])],"angle_distance":float(dist[t]),"quantum_similarity":float(k[ii[t],jj[t]]),"circular_phase_coefficient_RMS":float(circular[t])} for t in pick[:10]]
    return {"Train_pair_angle_distance":stats(dist),"Train_far_distance_q90":cut,"high_similarity_threshold":.9,
            "far_high_similarity_pair_count":len(pick),"examples":examples,"phase_coefficient_circular_RMS":stats(circular),
            "calculation":"Pure classical 7 phase coefficients [2*x_i, 2*(pi-x_i)*(pi-x_{i+1})]; circular coefficient distance is descriptive only. No circuits, states, or new quantum kernels.",
            "single_phase_period":"P(2*x_i) alone has period pi in x_i",
            "full_ZZ_map_independently_pi_periodic":False,
            "caution":"Changing one input by pi changes ZZ cross coefficients in general. Do not identify modulo-pi inputs as identical full feature maps. Far/high-fidelity examples would support folding but cannot prove it caused classification errors."}

def error_cases(ids,y,pr,pq,cross,ytrain,raw,x):
    result=[]
    for i in range(len(ids)):
        result.append({"sample_id":ids[i],"true_class":NAMES[int(y[i])],"RBF_prediction":NAMES[int(pr[i])],"QSVC_prediction":NAMES[int(pq[i])],
             "raw_features":dict(zip(FEATURES,raw[i].tolist())),"angles":dict(zip(FEATURES,x[i].tolist())),
             "quantum_similarity_to_train_classes":{n:{"mean":float(cross[i,ytrain==j].mean()),"max":float(cross[i,ytrain==j].max())} for j,n in enumerate(NAMES)}})
    return {"true_UP_cases":[r for r in result if r["true_class"]=="UP"],
            "QSVC_predicted_UP_cases":[r for r in result if r["QSVC_prediction"]=="UP"],
            "FLAT_errors":[r for r in result if r["true_class"]=="FLAT" and (r["QSVC_prediction"]!="FLAT" or r["RBF_prediction"]!="FLAT")],
            "paired_prediction_agreement_count":int(np.sum(pr==pq)),
            "decision_function_or_dual_coefficients":"NOT_AVAILABLE: no serialized fitted models/margins in parent artifacts; no refit to recover them",
            "similarity_caution":"Mean/max kernel similarity is not a QSVC decision score; no causal attribution to individual kernel values."}
