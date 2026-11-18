import unittest
import numpy as np
from models.classical.linear_svm import CANDIDATES,make
from tests.fixtures.phase3a.helpers import xy
class LinearSvmTests(unittest.TestCase):
    def test_grid(self):self.assertEqual([x["C"] for x in CANDIDATES],[.1,1,10])
    def test_fixed_parameters(self):
        p=make({"C":1.0}).get_params();self.assertEqual((p["class_weight"],p["random_state"],p["dual"]),("balanced",42,False))
    def test_fit_and_prediction(self):
        x,y=xy();m=make({"C":1.0}).fit(x,y);np.testing.assert_array_equal(m.predict(x),m.predict(x))
    def test_unapproved_config(self):
        with self.assertRaises(ValueError):make({"C":100.0})
