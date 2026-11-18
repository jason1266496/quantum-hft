import unittest
from models.classical.label_policy import classify,policy
class ClassificationPolicyTests(unittest.TestCase):
    def test_up(self):self.assertEqual(classify("0.1"),2)
    def test_down(self):self.assertEqual(classify("-0.1"),0)
    def test_flat(self):self.assertEqual(classify("0"),1)
    def test_decimal_exact_zero(self):
        for x in ("-0.000","0E-1000","+0"):self.assertEqual(classify(x),1)
    def test_no_epsilon(self):
        self.assertEqual(classify("1e-1000"),2);self.assertEqual(classify("-1e-1000"),0)
    def test_float_rejected(self):
        with self.assertRaises(ValueError):classify(0.0)
    def test_fixed_primary_policy(self):
        p=policy();self.assertEqual(p["policy_id"],"direction_3class_exact_v1")
        self.assertFalse(any(p[k] for k in ("train_selected","validation_selected","test_selected","holdout_selected","transaction_cost_aware")))
