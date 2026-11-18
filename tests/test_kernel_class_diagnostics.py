import pickle,unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from data_pipeline.datasets.checksums import fingerprint
from experiments.kernel_comparison.diagnostics import temporal_profile,load_trusted_object
from experiments.kernel_comparison.metrics import feature_profile,distribution,numeric_stats,shift,prediction_distribution,score,matrix_size
from experiments.kernel_comparison.metrics import prediction_distribution_from_confusion
from tests.fixtures.phase3b.helpers import rows,fresh
class DiagnosticsTests(unittest.TestCase):
    def test_class_counts(self):self.assertEqual(distribution(rows((1,2,3)))["counts"],{"DOWN":1,"FLAT":2,"UP":3})
    def test_percentages(self):self.assertAlmostEqual(sum(distribution(rows())["percentages"].values()),100)
    def test_temporal_range(self):
        d=temporal_profile(rows())["global"];self.assertEqual(d["first_event_time_ms"],0);self.assertEqual(d["maximum_temporal_gap_ms"],100)
    def test_session_groups(self):
        r=rows();r[-1]["session_id"]="other";self.assertEqual(len(temporal_profile(r)["per_source_session"]),2)
    def test_feature_profile_all_four(self):self.assertEqual(len(feature_profile(rows())),4)
    def test_per_class_iqr(self):self.assertIn("iqr",feature_profile(rows())["obi_5"]["per_class"]["DOWN"])
    def test_median_iqr(self):
        d=numeric_stats([0,1,2,3]);self.assertEqual(d["median"],1.5);self.assertEqual(d["iqr"],1.5)
    def test_empty_stats_not_available(self):self.assertEqual(numeric_stats([])["status"],"NOT_AVAILABLE")
    def test_shift_descriptive(self):
        d=shift({"Train":rows(),"Test":rows(split="Test")});self.assertFalse(d["test_used_for_policy"]);self.assertIn("median",d["splits"]["Test"]["features"]["obi_5"]["all"])
    def test_single_class_warning(self):self.assertEqual(prediction_distribution([1,1])["warnings"],["SINGLE_CLASS_PREDICTION_WARNING"])
    def test_three_class_metrics_flat_kept(self):
        m=score([0,1,2],[0,1,2]);self.assertEqual(m["macro_f1"],1);self.assertFalse(m["flat_excluded"]);self.assertEqual(len(m["confusion_matrix"]),3)
    def test_zero_support_still_three_classes(self):self.assertEqual(len(score([1,1],[1,1])["per_class"]),3)
    def test_kernel_estimate_not_runtime(self):
        d=matrix_size(3000,1000,1000);self.assertEqual(d["train_kernel_elements"],9000000);self.assertEqual(d["quantum_runtime"],"NOT_ESTIMATED")
    def test_trusted_pickle_hash_first(self):
        p=fresh()/"bad.pkl"
        with p.open("xb") as f:pickle.dump({},f)
        with self.assertRaisesRegex(ValueError,"HASH_MISMATCH"):load_trusted_object(p,{"sha256":"0"*64,"size_bytes":0})
    def test_own_origin_pickle_supported(self):
        p=fresh()/"own.pkl";x=np.array([[-1],[0],[1]]);y=np.array([0,1,2]);s=StandardScaler().fit(x);m=SVC().fit(s.transform(x),y)
        with p.open("xb") as f:pickle.dump({"model":m,"scaler":s},f)
        self.assertIsInstance(load_trusted_object(p,fingerprint(p))["model"],SVC)

    def test_sealed_confusion_prediction_totals(self):
        d=prediction_distribution_from_confusion([[0,2,0],[0,3,0],[0,1,0]])
        self.assertEqual(d["counts"],{"DOWN":0,"FLAT":6,"UP":0});self.assertEqual(d["prediction_class_count"],1)
