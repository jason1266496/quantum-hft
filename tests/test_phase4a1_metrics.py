import unittest
from experiments.phase4a1.metrics import score,close_tree
class MetricTests(unittest.TestCase):
    def test_all_three_classes(self):
        m=score([0,1,2],[0,1,2]);self.assertEqual(m["macro_f1"],1.);self.assertEqual(len(m["confusion_matrix"]),3)
    def test_flat_not_excluded(self):
        m=score([0,1,1,2],[0,0,0,2]);self.assertFalse(m["flat_excluded"]);self.assertEqual(m["row_count"],4);self.assertEqual(m["accuracy"],.5)
    def test_missing_prediction_class_warning(self):
        m=score([0,1,2],[1,1,1]);self.assertIn("CLASS_COVERAGE_WARNING",m["warnings"]);self.assertEqual(m["predicted_class_distribution"],{"DOWN":0,"FLAT":3,"UP":0})
    def test_missing_true_class_still_three_metric_rows(self):self.assertEqual(len(score([1,1,2],[1,1,2])["per_class"]),3)
    def test_metric_tolerance(self):self.assertTrue(close_tree({"f":.5},{"f":.5+1e-13}));self.assertFalse(close_tree({"f":.5},{"f":.51}))
    def test_integer_confusion_exact(self):self.assertFalse(close_tree([[1,2,3]],[[1,2,4]]))
