"""Artificial parameter dictionaries and labels; no formal data or fitting."""
import numpy as np
from sklearn.svm import SVC
from qiskit_machine_learning.algorithms import QSVC
def reference(kind):
    if kind=="rbf":return SVC(C=100.,gamma=.01,class_weight="balanced",probability=False,random_state=42).get_params(deep=False)
    if kind=="qsvc":return QSVC(quantum_kernel="precomputed",C=100.,class_weight="balanced",probability=False,random_state=42).get_params(deep=False)
    raise ValueError("UNKNOWN_FIXTURE_KIND")
def validation_labels():return np.array([0]*5+[1]*86+[2]*5,dtype=np.int64)
