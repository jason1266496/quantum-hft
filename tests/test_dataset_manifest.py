import unittest
from data_pipeline.datasets.manifest import make_manifest,holdout_contract
class DatasetManifestTests(unittest.TestCase):
    def manifest(self):return make_manifest("aggregate_core_v1","20990101T000000Z",{"chosen":"fixture"},{"embargo_ms":0},"fixture-v1")
    def test_required_manifest(self):
        value=self.manifest();self.assertEqual(value["market"],"BTCUSDT");self.assertTrue(value["final_holdout_locked"])
    def test_deterministic_manifest(self):self.assertEqual(self.manifest(),self.manifest())
    def test_created_time_fixed(self):self.assertEqual(self.manifest()["created_at_utc"],"2099-01-01T00:00:00Z")
    def test_no_models_or_scaler(self):
        v=self.manifest();self.assertFalse(v["model_training_performed"]);self.assertFalse(v["scaler_fitted"])
    def test_holdout_locked(self):
        v=holdout_contract({"holdout_status":"LOCKED"});self.assertEqual(v["model_access_policy"],"PROHIBITED_UNTIL_FINAL_EVALUATION")
    def test_holdout_cannot_tune(self):
        v=holdout_contract({"holdout_status":"LOCKED"})
        for key in ("hyperparameter_tuning","feature_selection","threshold_selection","scaler_fit","quantum_feature_map_selection","qaoa_parameter_selection"):self.assertFalse(v[key])
    def test_unlocked_holdout_rejected(self):
        with self.assertRaises(ValueError):holdout_contract({"holdout_status":"OPEN"})
    def test_no_holdout_statistics(self):
        self.assertEqual(self.manifest()["holdout_return_statistics"],"NOT_COMPUTED_HOLDOUT_LOCKED")
