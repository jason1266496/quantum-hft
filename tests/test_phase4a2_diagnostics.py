"""Synthetic, deterministic fixtures only. Never train a model."""
import copy,unittest
from pathlib import Path
import numpy as np
from experiments.phase4a2 import analysis as a,io
from experiments.phase4a2.runner import protocol,static_audit,proposals
from tests.fixtures.phase4a2.helpers import params,tri_labels

class SpectrumTests(unittest.TestCase):
    def test_identity_rank(self):
        r=a.spectrum(np.eye(6));self.assertAlmostEqual(r["entropy_effective_rank"],6);self.assertAlmostEqual(r["participation_ratio"],6)
    def test_ones_rank(self):
        r=a.spectrum(np.ones((6,6)));self.assertAlmostEqual(r["entropy_effective_rank"],1);self.assertEqual(r["numerical_rank"],1)
    def test_condition_tolerance(self):
        self.assertEqual(a.spectrum(np.ones((4,4)))["condition_number_at_declared_rank_tolerance"],"INFINITE_AT_DECLARED_RANK_TOLERANCE")
    def test_negative_rejected(self):
        with self.assertRaises(ValueError):a.spectrum(np.array([[1,2],[2,1.]]))
    def test_asymmetric_rejected(self):
        with self.assertRaises(ValueError):a.spectrum(np.array([[1,.2],[.1,1]]))
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):a.spectrum(np.array([[float("nan")]]))
    def test_size_guard(self):
        with self.assertRaises(ValueError):a.bounded(np.ones((97,4)),4)
    def test_no_mutation(self):
        k=np.eye(4);old=k.copy();a.spectrum(k);np.testing.assert_array_equal(k,old)
    def test_within_no_diagonal(self):
        y=tri_labels();r=a.class_similarity(np.eye(6),y)
        self.assertEqual(r["within_class"]["count"],3);self.assertEqual(r["between_class"]["count"],12);self.assertEqual(r["within_class"]["mean"],0)
    def test_centered_alignment(self):self.assertAlmostEqual(a.alignment(np.eye(4),np.eye(4)),1)
    def test_rbf_formula(self):
        x=np.array([[0,0,0,0],[1,0,0,0]])
        self.assertAlmostEqual(a.rbf(x,x)[0,1],np.exp(-.01))
    def test_fixed_gamma(self):
        with self.assertRaises(ValueError):a.rbf(np.zeros((1,4)),np.zeros((1,4)),.02)
    def test_cross_shape(self):
        with self.assertRaises(ValueError):a.cross_similarity(np.ones((2,2)),[0],[0,1])
    def test_concentration_cases(self):
        y=tri_labels();r=a.kernel_diagnostics(np.ones((6,6)),np.ones((6,6)),y,y);self.assertTrue(r["concentration_empirical_flag"])
        r=a.kernel_diagnostics(np.eye(6),np.eye(6),y,y);self.assertFalse(r["concentration_empirical_flag"])

class ClassTests(unittest.TestCase):
    def test_perfect_metrics(self):
        y=tri_labels();self.assertEqual(a.confusion(y,y)["macro_f1"],1)
    def test_up_error_exact(self):
        y=np.array([0]*5+[1]*86+[2]*5);p=np.array([0]*4+[1]+[0]*58+[1]*14+[2]*14+[0]*3+[1]*2)
        m=a.confusion(y,p);self.assertEqual(m["confusion_matrix"],[[4,1,0],[58,14,14],[3,2,0]]);self.assertEqual(m["per_class"]["UP"]["recall"],0);self.assertEqual(m["per_class"]["UP"]["predicted"],14)
    def test_missing_prediction_zero_division(self):
        r=a.confusion(tri_labels(),np.zeros(6,dtype=int));self.assertEqual(r["per_class"]["UP"]["precision"],0)
    def test_invalid_labels(self):
        with self.assertRaises(ValueError):a.confusion([3],[3])
    def test_prior_shift(self):
        m=a.imbalance(np.repeat([0,1,2],32),np.repeat([0,1,2],[5,86,5]))
        self.assertAlmostEqual(m["total_variation_distance"],.5625);self.assertEqual(m["balanced_class_weights_on_actual_Train"],{"DOWN":1.,"FLAT":1.,"UP":1.})

class PreprocessingTests(unittest.TestCase):
    def test_fixed_transform(self):
        x=np.array([[0,.25,.5,1]]);r,_=a.transform(x,params());np.testing.assert_allclose(r,x*np.pi)
    def test_clipping(self):
        _,c=a.transform(np.array([[-1,2,.5,.5]]),params());self.assertEqual(c["below_train_range_counts"],[1,0,0,0]);self.assertEqual(c["above_train_range_counts"],[0,1,0,0])
    def test_constant_angle(self):
        p=params();p["constant_features"][0]=True;p["z_train_max"][0]=0
        r,_=a.transform(np.array([[0,.2,.3,.4]]),p);self.assertAlmostEqual(r[0,0],np.pi/2)
    def test_bad_scale(self):
        p=params();p["base_standardization"]["parameters"]["scale"][0]=0
        with self.assertRaises(ValueError):a.transform(np.zeros((1,4)),p)
    def test_positive_affine_cancel(self):
        x=np.array([[.1,.2,.3,.4]]);p=params()
        p["base_standardization"]["parameters"]={"mean":[2]*4,"scale":[3]*4};p["z_train_min"]=[-2/3]*4;p["z_train_max"]=[-1/3]*4
        np.testing.assert_allclose(a.transform(x,p)[0],a.transform(x,params())[0])
    def test_pi_shift_not_full_period(self):
        x=np.array([[.1,.2,.3,.4],[.1+np.pi,.2,.3,.4]]);delta=np.diff(a.phase_coefficients(x),axis=0)[0]
        self.assertAlmostEqual(np.sin(delta[0]),0);self.assertGreater(abs(np.sin(delta[4])),.1)
    def test_feature_constant_report(self):
        r=a.feature_distributions(np.zeros((3,4)),np.zeros((3,4)));self.assertTrue(r["obi_5"]["raw_constant"])

class SafetyTests(unittest.TestCase):
    def test_id_mismatch(self):
        d={"ids":["a"],"file_sha256":"a","array_sha256":"b","labels_sha256":"c"};e=copy.deepcopy(d);e["ids"]=["z"]
        with self.assertRaises(ValueError):a.verify_identity(d,e)
    def test_label_hash_mismatch(self):
        d={"ids":["a"],"file_sha256":"a","array_sha256":"b","labels_sha256":"c"};e={**d,"labels_sha256":"z"}
        with self.assertRaises(ValueError):a.verify_identity(d,e)
    def test_test_csv_prohibited(self):
        with self.assertRaises(ValueError):io.rows(Path("/not/allowed/test.csv"))
    def test_holdout_csv_prohibited(self):
        with self.assertRaises(ValueError):io.rows(Path("/not/allowed/final_holdout.csv"))
    def test_public_npy_header_roundtrip(self):
        f=__import__("io").BytesIO();np.save(f,np.eye(96),allow_pickle=False);f.seek(0)
        self.assertEqual(io.read_npy_header(f)[0],(96,96))
    def test_public_npy_header_large_rejected(self):
        f=__import__("io").BytesIO();np.lib.format.write_array_header_1_0(f,{"descr":"<f8","fortran_order":False,"shape":(97000,97000)});f.seek(0)
        with self.assertRaises(ValueError):io.read_npy_header(f)
    def test_public_npy_header_dtype_rejected(self):
        f=__import__("io").BytesIO();np.save(f,np.ones((96,96),dtype=np.int64),allow_pickle=False);f.seek(0)
        with self.assertRaises(ValueError):io.read_npy_header(f)
    def test_quantum_other_matrix_prohibited(self):
        with self.assertRaises(ValueError):io.matrix(Path("/not/allowed/new_kernel.npy"))
    def test_output_scope(self):
        with self.assertRaises(ValueError):io.write(Path("/home/jason/hft-realtime/result.json"),{})
    def test_no_training_protocol(self):
        self.assertEqual(protocol()["new_model_fits"],0);self.assertEqual(protocol()["new_quantum_kernel_evaluations"],0)
    def test_proposals_only(self):
        self.assertEqual(proposals()["status"],"PROPOSALS_ONLY_NOT_EXECUTED");self.assertEqual(len(proposals()["experiments"]),7)
    def test_static_guard(self):
        root=Path(__file__).resolve().parents[1]
        self.assertEqual(static_audit(sorted((root/"experiments/phase4a2").glob("*.py"))+[root/"tools/diagnose_quantum_kernel.py"])["status"],"PASS")
if __name__=="__main__":unittest.main()
