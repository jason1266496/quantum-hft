"""Synthetic fixture predictor; no market data, labels or trained model."""
def synthetic_prediction():
    return {'prediction_class':'UP','horizon_ms':1000,'provenance':'SYNTHETIC_ONLY'}
