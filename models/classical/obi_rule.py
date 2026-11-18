"""Fixed, inclusive OBI +/-0.6 heuristic; no scaler or tuning."""
from decimal import Decimal
import numpy as np
CONFIG={"threshold":"0.6","fixed":True,"scaler":False,"policy_id":"fixed_obi_pm06_v1"}
def predict(values):
    out=[]
    for value in values:
        x=Decimal(value)
        if not x.is_finite():raise ValueError("NONFINITE_OBI")
        out.append(2 if x>=Decimal(".6") else (0 if x<=Decimal("-.6") else 1))
    return np.asarray(out,dtype=np.int64)
