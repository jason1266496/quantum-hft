"""Exact CPU fidelity kernels and actual QSVC precomputed solvers."""
import time,warnings
import numpy as np
from sklearn.svm import SVC
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.utils.class_weight import compute_class_weight
from qiskit_machine_learning.algorithms import QSVC
from qiskit_machine_learning.kernels import FidelityStatevectorKernel
from experiments.phase4a1.kernel import circuit,validate
from . import contracts as c
FITS=[];QUANTUM_CALLS=[]
def fidelity():
    fmap,manifest=circuit()
    manifest["instructions"]=[{"name":item.operation.name,"qubits":[fmap.find_bit(q).index for q in item.qubits],"parameters":[str(v) for v in item.operation.params]} for item in fmap.data]
    return FidelityStatevectorKernel(feature_map=fmap,shots=None,enforce_psd=False,auto_clear_cache=True),manifest
def quantum(kernel,x,y=None,*,formal=False,tag=""):
    if formal:
        if x.shape not in ((96,4),(384,4)) or (y is not None and y.shape!=(96,4)):raise ValueError("FORMAL_QUANTUM_BUDGET")
        QUANTUM_CALLS.append({"tag":tag,"x_shape":list(x.shape),"y_shape":None if y is None else list(y.shape)})
    start=time.perf_counter();a=np.asarray(kernel.evaluate(x_vec=x,y_vec=y))
    return a,time.perf_counter()-start
def rbf_matrices(train,val):
    start=time.perf_counter();tt=rbf_kernel(train,train,gamma=.01);vt=rbf_kernel(val,train,gamma=.01)
    return tt,vt,time.perf_counter()-start
def model(name):
    if name not in c.MODELS[:4]:raise ValueError("UNKNOWN_MODEL")
    p={"C":100.,"class_weight":"balanced" if name.endswith("Balanced") else None,"probability":False,"random_state":42}
    out=SVC(kernel="rbf",gamma=.01,**p) if name.startswith("RBF") else QSVC(quantum_kernel="precomputed",**p)
    if isinstance(out,QSVC) and (out.kernel!="precomputed" or out.quantum_kernel!="precomputed"):raise ValueError("QSVC_PRECOMPUTED_NOT_AVAILABLE")
    return out
def learn(name,x,y,val,*,formal=False,tag=""):
    m=model(name);start=time.perf_counter()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always");m.fit(x.copy(),y.copy())
    fit_s=time.perf_counter()-start
    if formal:FITS.append({"model":name,"tag":tag,"rows":len(y),"Train_array_sha256":old_array(x),"labels_sha256":c.labels_sha(y)})
    if any(issubclass(w.category,ConvergenceWarning) for w in caught) or m.fit_status_!=0:raise ValueError("SOLVER_CONVERGENCE_FAILURE")
    start=time.perf_counter();pred=np.asarray(m.predict(val.copy()),dtype=np.int64);pred_s=time.perf_counter()-start
    if pred.shape!=(len(val),) or not np.isin(pred,[0,1,2]).all():raise ValueError("INVALID_PREDICTIONS")
    expected=np.ones(len(m.classes_)) if m.class_weight is None else compute_class_weight("balanced",classes=m.classes_,y=y)
    if not np.allclose(expected,m.class_weight_,atol=1e-12,rtol=1e-12):raise ValueError("ACTUAL_CLASS_WEIGHT_MISMATCH")
    weights={c.NAMES[int(k)]:float(w) for k,w in zip(m.classes_,m.class_weight_)}
    return pred,{"fit_seconds":fit_s,"predict_seconds":pred_s,"actual_class_weights":weights,"effective_C_i":{k:100*v for k,v in weights.items()},
       "estimator_class":type(m).__module__+"."+type(m).__name__,"configuration":m.get_params(deep=False),"solver_fit_status":int(m.fit_status_),
       "warnings":[{"category":w.category.__name__,"message":str(w.message)} for w in caught]}
def old_array(x):return c.old.array_sha(x)
def majority(y,n):
    y=np.asarray(y)
    if y.ndim!=1 or not len(y) or y.dtype.kind not in "iu" or not np.isin(y,[0,1,2]).all():raise ValueError("INVALID_TRAIN_LABELS")
    cls=int(np.argmax(np.bincount(y,minlength=3)))
    return np.full(n,cls,dtype=np.int64),{"class":cls,"derived_only_from":"own fold Train labels","Train_distribution":np.bincount(y,minlength=3).tolist(),"tie_break":"DOWN/FLAT/UP order"}
