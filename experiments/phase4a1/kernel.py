"""Raw exact-statevector matrices with predeclared validation tolerances."""
import time
import numpy as np
from qiskit.circuit.library import zz_feature_map
from qiskit_machine_learning.kernels import FidelityStatevectorKernel
NUMERICAL_ATOL=1e-10
DETERMINISM_ATOL=1e-10
DETERMINISM_RTOL=1e-9
def circuit():
    fmap=zz_feature_map(feature_dimension=4,reps=1,entanglement="linear",alpha=2.,parameter_prefix="x")
    if fmap.num_qubits!=4 or fmap.num_parameters!=4:raise ValueError("CIRCUIT_CONTRACT_CHANGED")
    return fmap,{"feature_map":"zz_feature_map","qubits":int(fmap.num_qubits),"parameters":int(fmap.num_parameters),
      "parameter_order":[str(p) for p in fmap.parameters],"depth":int(fmap.depth()),"gate_counts":{str(k):int(v) for k,v in fmap.count_ops().items()},
      "gate_count_total":int(sum(fmap.count_ops().values())),"entanglement":"linear","reps":1,"alpha":2.,"shots":None,
      "seed":42,"backend":"local exact Statevector on classical CPU","enforce_psd":False,"kernel_repair_performed":False}
def compute(train,val):
    if train.ndim!=2 or val.ndim!=2 or train.shape[1]!=4 or val.shape[1]!=4 or not 1<=len(train)<=96 or not 1<=len(val)<=96:raise ValueError("KERNEL_BUDGET_OR_DIMENSION_PROHIBITED")
    if not np.isfinite(train).all() or not np.isfinite(val).all() or min(train.min(),val.min())<0 or max(train.max(),val.max())>np.pi:raise ValueError("INVALID_FROZEN_ANGLE_INPUT")
    fmap,manifest=circuit()
    kernel=FidelityStatevectorKernel(feature_map=fmap,shots=None,enforce_psd=False,auto_clear_cache=True)
    t=time.perf_counter();tt=np.asarray(kernel.evaluate(x_vec=train));train_time=time.perf_counter()-t
    t=time.perf_counter();vt=np.asarray(kernel.evaluate(x_vec=val,y_vec=train));val_time=time.perf_counter()-t
    return tt,vt,manifest,{"quantum_kernel_train_matrix_seconds":train_time,"quantum_kernel_validation_matrix_seconds":val_time,
        "scope":"Python CPU exact-statevector; matrices computed once per pass; no QPU/HFT latency or speedup claim"}
def validate(tt,vt,ntrain,nval,*,tol=NUMERICAL_ATOL):
    if tt.shape!=(ntrain,ntrain) or vt.shape!=(nval,ntrain):raise ValueError("KERNEL_SHAPE")
    for matrix in (tt,vt):
        if not np.isrealobj(matrix) or not np.isfinite(matrix).all():raise ValueError("KERNEL_NONFINITE_OR_COMPLEX")
        if matrix.min()<-tol or matrix.max()>1+tol:raise ValueError("KERNEL_VALUE_OUT_OF_RANGE")
    sym=float(np.max(np.abs(tt-tt.T)));diag=float(np.max(np.abs(np.diag(tt)-1)))
    if sym>tol or diag>tol:raise ValueError("KERNEL_SYMMETRY_OR_DIAGONAL")
    eigen=np.linalg.eigvalsh(tt)
    if float(eigen.min())<-tol:raise ValueError("KERNEL_NOT_PSD")
    return {"status":"PASS","train_shape":list(tt.shape),"validation_vs_train_shape":list(vt.shape),"train_symmetry_error":sym,
         "train_diagonal_one_error":diag,"train_min_eigenvalue":float(eigen.min()),"train_eigenvalues":eigen.tolist(),
         "train_value_min":float(tt.min()),"train_value_max":float(tt.max()),"validation_value_min":float(vt.min()),"validation_value_max":float(vt.max()),
         "finite_real":True,"PSD_tolerance":tol,"kernel_repair_performed":False,"enforce_psd":False,
         "validation_diagonal_symmetry_PSD":"NOT_APPLICABLE_CROSS_KERNEL","eigenvalue_method":"eigvalsh on raw Train Gram after symmetry check"}
