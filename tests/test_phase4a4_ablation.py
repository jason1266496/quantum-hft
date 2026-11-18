"""Artificial fixtures only. No fit/predict or quantum evaluate calls."""
import unittest,copy,io
from pathlib import Path
import numpy as np
from experiments.phase4a4 import analysis as a,contracts as c,inputs
from experiments.phase4a4.runner import model,forbidden_quantum,fit
from tests.fixtures.phase4a4.helpers import reference,validation_labels
class ConfigTests(unittest.TestCase):
    def test_none_changes_only_weight(self):
        p=reference("rbf");n=a.none_config(p);self.assertTrue(a.only_weight_changed(p,n));self.assertEqual(p["class_weight"],"balanced")
    def test_extra_gamma_change_rejected(self):
        p=reference("rbf");n=a.none_config(p);n["gamma"]=.02;self.assertFalse(a.only_weight_changed(p,n))
    def test_missing_parameter_rejected(self):
        p=reference("rbf");n=a.none_config(p);del n["C"];self.assertFalse(a.only_weight_changed(p,n))
    def test_nonbalanced_reference_rejected(self):
        with self.assertRaises(ValueError):a.none_config({"class_weight":None})
    def test_rbf_constructor_no_fit(self):
        m=model("rbf",reference("rbf"));self.assertIsNone(m.class_weight);self.assertEqual(m.C,100);self.assertEqual(m.gamma,.01)
    def test_qsvc_constructor_precomputed_no_fit(self):
        m=model("qsvc",reference("qsvc"));self.assertIsNone(m.class_weight);self.assertEqual(m.quantum_kernel,"precomputed")
    def test_unknown_model_guard(self):
        with self.assertRaises(ValueError):model("other",{})
    def test_balanced_fit_not_exposed(self):
        self.assertTrue(c.protocol()["balanced_policy"].startswith("sealed references"))
    def test_quantum_guard(self):
        with self.assertRaises(RuntimeError):forbidden_quantum()
class MatrixTests(unittest.TestCase):
    def test_identity_matrix_valid(self):self.assertEqual(a.kernel_check(np.eye(96),np.zeros((96,96)))["status"],"PASS")
    def test_wrong_shape(self):
        with self.assertRaises(ValueError):a.kernel_check(np.eye(97),np.zeros((96,97)))
    def test_nonfinite(self):
        k=np.eye(96);k[0,0]=np.nan
        with self.assertRaises(ValueError):a.kernel_check(k,np.eye(96))
    def test_asymmetry(self):
        k=np.eye(96);k[0,1]=.1
        with self.assertRaises(ValueError):a.kernel_check(k,np.eye(96))
    def test_diagonal_changed(self):
        k=np.eye(96);k[0,0]=.5
        with self.assertRaises(ValueError):a.kernel_check(k,np.eye(96))
    def test_PSD_failure_with_valid_range(self):
        k=np.eye(96);k[:3,:3]=[[1,.9,.9],[.9,1,0],[.9,0,1]]
        with self.assertRaises(ValueError):a.kernel_check(k,np.eye(96))
    def test_cross_not_required_PSD(self):
        k=np.triu(np.ones((96,96)));self.assertEqual(a.kernel_check(np.eye(96),k)["status"],"PASS")
    def test_matrix_not_mutated(self):
        k=np.eye(96);saved=k.copy();a.kernel_check(k,k);np.testing.assert_array_equal(k,saved)
    def test_public_header(self):
        f=io.BytesIO();np.save(f,np.eye(96),allow_pickle=False);f.seek(0);self.assertEqual(inputs.header(f),(96,96))
    def test_large_header_rejected(self):
        f=io.BytesIO();np.lib.format.write_array_header_1_0(f,{"descr":"<f8","fortran_order":False,"shape":(1000000,1000000)});f.seek(0)
        with self.assertRaises(ValueError):inputs.header(f)
    def test_wrong_header_dtype(self):
        f=io.BytesIO();np.save(f,np.eye(96,dtype=np.int64),allow_pickle=False);f.seek(0)
        with self.assertRaises(ValueError):inputs.header(f)
class MetricsTests(unittest.TestCase):
    def test_majority_exact(self):
        m=a.majority(validation_labels());self.assertAlmostEqual(m["accuracy"],86/96);self.assertAlmostEqual(m["balanced_accuracy"],1/3);self.assertAlmostEqual(m["macro_f1"],(172/182)/3)
    def test_majority_confusion(self):self.assertEqual(a.majority(validation_labels())["confusion_matrix"],[[0,5,0],[0,86,0],[0,5,0]])
    def test_majority_warning(self):self.assertIn("CLASS_COVERAGE_WARNING",a.majority(validation_labels())["warnings"])
    def test_prediction_changes(self):
        d=a.changes(["a","b","c"],np.array([0,1,2]),np.array([0,2,1]),np.array([1,1,1]))
        self.assertEqual(d["changed_count"],2);self.assertEqual(d["None_minus_balanced_FLAT_predictions"],2)
    def test_zero_prediction_changes(self):
        d=a.changes(["a"],np.array([1]),np.array([1]),np.array([1]));self.assertEqual(d["changed_count"],0)
    def test_duplicate_change_ids(self):
        with self.assertRaises(ValueError):a.changes(["a","a"],np.array([1,1]),np.array([1,1]),np.array([1,1]))
    def test_invalid_prediction_class(self):
        with self.assertRaises(ValueError):a.changes(["a"],np.array([1]),np.array([3]),np.array([1]))
    def test_determinism_reject_changed_sha(self):
        m={"prediction_sha256":"x","predictions":[1],"metrics":{},"effective_class_weight":{}}
        d={"inputs":{},"preprocessing_sha256":"x","kernels":{},"models":{"rbf":copy.deepcopy(m),"qsvc":copy.deepcopy(m)}}
        e=copy.deepcopy(d);e["models"]["qsvc"]["prediction_sha256"]="y";self.assertEqual(a.compare_repeats(d,e)["status"],"FAIL")
class SafetyTests(unittest.TestCase):
    def test_Test_prohibited(self):
        with self.assertRaises(ValueError):c.rows(Path("/home/jason/quantum-hft/artifacts/datasets/test.csv"))
    def test_Holdout_prohibited(self):
        with self.assertRaises(ValueError):c.rows(Path("/home/jason/quantum-hft/artifacts/datasets/final_holdout.csv"))
    def test_other_matrix_prohibited(self):
        with self.assertRaises(ValueError):inputs.matrix(Path("/tmp/other.npy"))
    def test_old_output_prohibited(self):
        with self.assertRaises(ValueError):c.safe(c.P3/"new.json")
    def test_hft_output_prohibited(self):
        with self.assertRaises(ValueError):c.safe(Path("/home/jason/hft-realtime/result.json"))
    def test_run_id_guard(self):
        with self.assertRaises(ValueError):c.runpath("../old")
    def test_fit_balanced_guard_before_any_training(self):
        from types import SimpleNamespace
        with self.assertRaises(ValueError):fit("rbf",SimpleNamespace(class_weight="balanced"),np.zeros((96,4)),np.ones(96))
    def test_fit_qsvc_shape_guard_before_any_training(self):
        from types import SimpleNamespace
        with self.assertRaises(ValueError):fit("qsvc",SimpleNamespace(class_weight=None),np.zeros((96,4)),np.ones(96))
    def test_fit_unknown_kind_guard(self):
        from types import SimpleNamespace
        with self.assertRaises(ValueError):fit("unknown",SimpleNamespace(class_weight=None),np.zeros((96,4)),np.ones(96))
    def test_protocol_budget(self):self.assertEqual(c.protocol()["new_quantum_evaluations"],0);self.assertEqual(c.protocol()["new_model_fits"],4)
if __name__=="__main__":unittest.main()
