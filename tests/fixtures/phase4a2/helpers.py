"""Artificial data only; no market-data reads."""
import numpy as np
def params():
    return {"base_standardization":{"parameters":{"mean":[0]*4,"scale":[1]*4}},
            "z_train_min":[0]*4,"z_train_max":[1]*4,"constant_features":[False]*4,"constant_feature_angle":np.pi/2}
def tri_labels():return np.array([0,0,1,1,2,2])
