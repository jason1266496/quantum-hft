import unittest
from models.classical.rbf_svm import CANDIDATES,make
from tests.fixtures.phase3a.helpers import xy
class RbfSvmTests(unittest.TestCase):
    def test_grid(self):self.assertEqual(len(CANDIDATES),4)
    def test_full_data_prohibited(self):
        with self.assertRaises(ValueError):make({"C":1.0,"gamma":"scale"},scope="full",train_rows=150000)
    def test_large_subset_prohibited(self):
        with self.assertRaises(ValueError):make({"C":1.0,"gamma":"scale"},scope="kernel_comparison_subset_v1",train_rows=1001)
    def test_fixed_parameters_and_fit(self):
        x,y=xy();m=make({"C":1.0,"gamma":"scale"},scope="kernel_comparison_subset_v1",train_rows=len(x))
        self.assertFalse(m.probability);self.assertEqual(m.class_weight,"balanced");m.fit(x,y)
        self.assertEqual(set(m.predict(x)),{0,1,2})
