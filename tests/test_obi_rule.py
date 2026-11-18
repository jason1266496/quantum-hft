import unittest
from models.classical.obi_rule import predict,CONFIG
class ObiRuleTests(unittest.TestCase):
    def test_plus_boundary(self):self.assertEqual(predict(["0.6"]).tolist(),[2])
    def test_minus_boundary(self):self.assertEqual(predict(["-0.6"]).tolist(),[0])
    def test_plus_059(self):self.assertEqual(predict(["0.59"]).tolist(),[1])
    def test_minus_059(self):self.assertEqual(predict(["-0.59"]).tolist(),[1])
    def test_no_scaler(self):self.assertFalse(CONFIG["scaler"])
