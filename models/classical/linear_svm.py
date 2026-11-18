"""Approved primal LinearSVC grid, suitable for full low-dimensional Train."""
from sklearn.svm import LinearSVC
CANDIDATES=({"C":.1},{"C":1.0},{"C":10.0})
def make(config):
    if config not in CANDIDATES:raise ValueError("UNAPPROVED_LINEAR_CONFIG")
    return LinearSVC(C=config["C"],class_weight="balanced",random_state=42,
                     dual=False,tol=1e-4,max_iter=20000)
