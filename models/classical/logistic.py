"""Approved sklearn Logistic Regression grid."""
from sklearn.linear_model import LogisticRegression
CANDIDATES=({"C":.1},{"C":1.0},{"C":10.0})
def make(config):
    if config not in CANDIDATES:raise ValueError("UNAPPROVED_LOGISTIC_CONFIG")
    return LogisticRegression(C=config["C"],class_weight="balanced",random_state=42,
                              solver="lbfgs",tol=1e-4,max_iter=5000)
