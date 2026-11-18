import copy,math,unittest
import numpy as np
from models.classical.feature_policy import matrix
from experiments.quantum_preparation.preprocessing import SharedAngleInput,kernel_budget,fair_policy
from experiments.quantum_preparation.io import FEATURES
from tests.fixtures.phase4a0.helpers import rows,base_scaler
class InputTests(unittest.TestCase):
    def test_train_only_fit(self):
        s=SharedAngleInput(base_scaler(),"smoke")
        for split in ("Validation","Test","Final Holdout"):
            with self.assertRaises(ValueError):s.fit(rows(),split=split)
    def test_fit_once(self):
        s=SharedAngleInput(base_scaler(),"smoke").fit(rows())
        with self.assertRaises(ValueError):s.fit(rows())
    def test_test_holdout_no_transform(self):
        s=SharedAngleInput(base_scaler(),"smoke").fit(rows())
        for split in ("Test","Final Holdout"):
            with self.assertRaises(ValueError):s.transform(rows(),split=split)
    def test_validation_transform_does_not_fit(self):
        s=SharedAngleInput(base_scaler(),"smoke").fit(rows());before=copy.deepcopy(s.artifact())
        s.transform(rows(split="Validation"),split="Validation");self.assertEqual(before,s.artifact())
    def test_feature_order_fixed(self):self.assertEqual(fair_policy()["feature_order"],list(FEATURES))
    def test_bad_feature_order_rejected(self):
        b=base_scaler();b["feature_order"].reverse()
        with self.assertRaises(ValueError):SharedAngleInput(b,"smoke")
    def test_metadata_labels_not_features(self):
        r=rows();s=SharedAngleInput(base_scaler(),"smoke").fit(r);a,_=s.transform(r,split="Train")
        for v in r:v["future_return_bps"]="POISON";v["source_id"]="POISON"
        b,_=s.transform(r,split="Validation");np.testing.assert_array_equal(a,b);self.assertEqual(a.shape[1],4)
    def test_angles_bounded(self):
        s=SharedAngleInput(base_scaler(),"smoke").fit(rows());x,_=s.transform(rows(),split="Train")
        self.assertTrue(np.all(x>=0));self.assertTrue(np.all(x<=math.pi))
    def test_validation_outside_range_clips(self):
        s=SharedAngleInput(base_scaler(),"smoke").fit(rows());v=rows(split="Validation")
        for r in v:r["obi_5"]="1e6"
        a,c=s.transform(v,split="Validation");np.testing.assert_allclose(a[:,0],math.pi);self.assertEqual(c["above_train_range_counts"][0],len(v))
    def test_constant_feature_midpoint(self):
        r=rows()
        for v in r:v["obi_5"]="0"
        s=SharedAngleInput(base_scaler(),"smoke").fit(r);a,_=s.transform(r,split="Train");np.testing.assert_allclose(a[:,0],math.pi/2)
    def test_equivalent_raw_train_minmax(self):
        t=rows();b=base_scaler();b["mean"]=[3,4,5,6];b["scale"]=[2,3,4,5]
        s=SharedAngleInput(b,"smoke").fit(t);a,_=s.transform(t,split="Train")
        x=matrix(t);expected=math.pi*(x-x.min(axis=0))/(x.max(axis=0)-x.min(axis=0))
        np.testing.assert_allclose(a,expected,rtol=1e-12,atol=1e-12)
    def test_frozen_base_parameters_unchanged(self):
        b=base_scaler();before=copy.deepcopy(b);SharedAngleInput(b,"smoke").fit(rows());self.assertEqual(b,before)
    def test_c_fixed_and_no_old_model_reuse(self):
        p=fair_policy();self.assertEqual(p["C"],100);self.assertEqual(p["QSVC"]["C"],100);self.assertEqual(p["RBF"]["gamma"],.01);self.assertFalse(p["old_fitted_RBF_reuse_allowed"])
    def test_kernel_budget_smoke(self):
        b=kernel_budget(24,24);self.assertEqual(b["train_shape"],[24,24]);self.assertEqual(b["train_elements"],576);self.assertEqual(b["combined_float64_bytes"],9216)
    def test_kernel_budget_prototype(self):
        b=kernel_budget(96,96);self.assertEqual(b["train_elements"],9216);self.assertEqual(b["combined_float64_bytes"],147456);self.assertEqual(b["statevector_dimension"],16)
