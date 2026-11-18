import unittest
import numpy as np
from models.classical.logistic import CANDIDATES,make
from tests.fixtures.phase3a.helpers import xy
class LogisticTests(unittest.TestCase):
    def test_grid(self):self.assertEqual([x["C"] for x in CANDIDATES],[.1,1,10])
    def test_fixed_parameters(self):
        p=make({"C":1.0}).get_params();self.assertEqual((p["class_weight"],p["random_state"],p["max_iter"]),("balanced",42,5000))
    def test_fit_and_prediction_deterministic(self):
        x,y=xy();m=make({"C":1.0}).fit(x,y)
        np.testing.assert_array_equal(m.predict(x),m.predict(x))
    def test_unapproved_config(self):
        with self.assertRaises(ValueError):make({"C":100.0})
