"""Python batch timing; never an HFT inference latency claim."""
import hashlib,time,warnings
from statistics import median
import numpy as np
from sklearn.exceptions import ConvergenceWarning
def fit_model(model,x,y):
    start=time.perf_counter()
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always");model.fit(x,y)
    elapsed=time.perf_counter()-start
    records=[{"category":w.category.__name__,"message":str(w.message)} for w in captured]
    if any(issubclass(w.category,ConvergenceWarning) for w in captured):raise ValueError("MODEL_DID_NOT_CONVERGE")
    return {"fit_wall_seconds":elapsed,"warnings":records}
def predict_batch(predict,data,*,repeats=1):
    if repeats<1:raise ValueError("INVALID_TIMING_REPEATS")
    warm=predict(data);durations=[];hashes=[]
    for _ in range(repeats):
        start=time.perf_counter();result=np.asarray(predict(data),dtype=np.int64)
        durations.append(time.perf_counter()-start)
        if not np.array_equal(warm,result):raise ValueError("NONDETERMINISTIC_PREDICTION")
        hashes.append(hashlib.sha256(result.tobytes()).hexdigest())
    wall=median(durations)
    return result,{"prediction_rows":len(result),"warmup_calls":1,"timed_calls":repeats,
                   "wall_seconds":durations,"median_wall_seconds":wall,
                   "rows_per_second":len(result)/wall if wall else None,
                   "prediction_sha256":hashes,"timing_scope":"PYTHON_BATCH_INFERENCE_ONLY"}
