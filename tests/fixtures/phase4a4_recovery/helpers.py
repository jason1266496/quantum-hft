"""Legitimate artificial labels/predictions; metrics computed by official scorer."""
import copy,hashlib,numpy as np
from experiments.phase4a1.metrics import score
from experiments.phase4a4.contracts import identity
TRUE_LABELS=[0,1,2,1]
PREDICTIONS=[0,1,1,1]
def stage_fixture(predictions=None):
    y=np.array(TRUE_LABELS,dtype=np.int64);p=np.array(PREDICTIONS if predictions is None else predictions,dtype=np.int64)
    metric=score(y,p)
    if predictions is None:
        assert metric["confusion_matrix"]==[[1,0,0],[0,2,0],[0,1,0]]
        assert [sum(row) for row in metric["confusion_matrix"]]==[1,2,1]
    x=np.arange(16,dtype=float).reshape(4,4)/16
    model={"prediction_sha256":hashlib.sha256(p.tobytes()).hexdigest(),"predictions":p.tolist(),"metrics":metric,
           "effective_class_weight":{"DOWN":1.,"FLAT":1.,"UP":1.}}
    return {"status":"PASS","inputs":{"Train":identity(["train"+str(i) for i in range(4)],x,y),"Validation":identity(["val"+str(i) for i in range(4)],x,y)},
      "preprocessing_sha256":hashlib.sha256(b"artificial_fixed_preprocessing").hexdigest(),
      "kernels":{"fixture":{"shape":[4,4],"array_sha256":hashlib.sha256(np.eye(4).tobytes()).hexdigest()}},
      "models":{"rbf":copy.deepcopy(model),"qsvc":copy.deepcopy(model)}}
