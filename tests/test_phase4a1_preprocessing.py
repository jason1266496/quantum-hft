import copy,math,unittest
import numpy as np
from experiments.phase4a1.contracts import load_profile,FEATURES
from experiments.phase4a1.preprocessing import transform,verify_profile
from tests.fixtures.phase4a1.helpers import budget
class PreprocessingTests(unittest.TestCase):
    def fixture(self):
        r,m=budget();return load_profile(r,"prototype",m)
    def test_frozen_formula_and_zero_refits(self):
        b=self.fixture();v=verify_profile(b);self.assertEqual(v["new_preprocessing_fits"],0);self.assertEqual(v["status"],"PASS")
    def test_test_and_holdout_transform_rejected(self):
        b=self.fixture()
        for split in ("Test","Final Holdout"):
            with self.assertRaises(ValueError):transform(b["Train"]["raw"],b["params"],split=split)
    def test_undefined_clipping_stops(self):
        b=self.fixture();del b["params"]["out_of_range"]
        with self.assertRaisesRegex(ValueError,"UNDEFINED"):transform(b["Train"]["raw"],b["params"],split="Train")
    def test_undefined_constant_policy_stops(self):
        b=self.fixture();del b["params"]["constant_feature_angle"]
        with self.assertRaisesRegex(ValueError,"UNDEFINED"):transform(b["Train"]["raw"],b["params"],split="Train")
    def test_feature_order_cannot_change(self):
        b=self.fixture();b["params"]["feature_order"].reverse()
        with self.assertRaises(ValueError):transform(b["Train"]["raw"],b["params"],split="Train")
    def test_metadata_and_labels_excluded(self):
        b=self.fixture();a,_=transform(b["Train"]["raw"],b["params"],split="Train")
        for r in b["Train"]["raw"]:r["future_return_bps"]="POISON";r["source_id"]="POISON"
        c,_=transform(b["Train"]["raw"],b["params"],split="Train");np.testing.assert_array_equal(a,c)
    def test_validation_does_not_modify_ranges(self):
        b=self.fixture();before=copy.deepcopy(b["params"]);transform(b["Validation"]["raw"],b["params"],split="Validation");self.assertEqual(before,b["params"])
    def test_fixed_clipping(self):
        b=self.fixture()
        for r in b["Validation"]["raw"]:r["obi_5"]="999"
        x,c=transform(b["Validation"]["raw"],b["params"],split="Validation")
        np.testing.assert_allclose(x[:,0],math.pi);self.assertEqual(c["above_train_range_counts"][0],96)
    def test_constant_feature_pi_over_two(self):
        b=self.fixture();p=b["params"];p["z_train_max"][0]=p["z_train_min"][0];p["constant_features"][0]=True
        x,_=transform(b["Train"]["raw"],p,split="Train");np.testing.assert_allclose(x[:,0],math.pi/2)
    def test_nonfinite_rejected(self):
        b=self.fixture();b["Train"]["raw"][0]["obi_5"]="nan"
        with self.assertRaisesRegex(ValueError,"NONFINITE"):transform(b["Train"]["raw"],b["params"],split="Train")
