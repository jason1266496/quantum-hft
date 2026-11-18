import unittest
from models.classical.metrics import evaluate
from models.classical.label_policy import distribution
class ClassicalMetricTests(unittest.TestCase):
    def test_flat_included_accuracy(self):
        m=evaluate([0,1,1,2],[0,0,1,2]);self.assertEqual(m["accuracy"],.75);self.assertFalse(m["flat_excluded"])
    def test_three_class_confusion(self):
        m=evaluate([1,1],[1,1]);self.assertEqual(len(m["confusion_matrix"]),3);self.assertEqual(m["per_class"]["FLAT"]["support"],2)
    def test_macro_f1_includes_zero_support(self):self.assertAlmostEqual(evaluate([1,1],[1,1])["macro_f1"],1/3)
    def test_distribution(self):
        d=distribution([0,1,1,2]);self.assertEqual(d["counts"],{"DOWN":1,"FLAT":2,"UP":1})
    def test_missing_train_class_fail(self):
        with self.assertRaises(ValueError):distribution([1,1],require_all=True)
    def test_extreme_warning_not_deletion(self):
        d=distribution([0]+[1]*200+[2],require_all=True)
        self.assertIn("EXTREME_CLASS_IMBALANCE_WARNING",d["warnings"]);self.assertEqual(d["total"],202)
