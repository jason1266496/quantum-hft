"""RBF SVC is restricted to the fixed kernel comparison subset."""
from sklearn.svm import SVC
CANDIDATES=({"C":1.0,"gamma":"scale"},{"C":1.0,"gamma":.1},
            {"C":10.0,"gamma":"scale"},{"C":10.0,"gamma":.1})
def make(config,*,scope,train_rows):
    if scope!="kernel_comparison_subset_v1" or train_rows>1000:raise ValueError("RBF_FULL_TRAIN_PROHIBITED")
    if config not in CANDIDATES:raise ValueError("UNAPPROVED_RBF_CONFIG")
    return SVC(C=config["C"],gamma=config["gamma"],kernel="rbf",class_weight="balanced",
               probability=False,random_state=42,cache_size=200)
