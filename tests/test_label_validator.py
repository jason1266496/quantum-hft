import unittest
from decimal import Decimal
from data_pipeline.labels.validator import validate_label,feature_path
from data_pipeline.labels.builder import _label
from data_pipeline.labels.schema import LABEL_FIELDS
from tests.fixtures.phase2d.helpers import rows

class LabelValidatorTests(unittest.TestCase):
    def good(self):
        data=rows((0,100),("100","101"))
        return _label(data,[0,100],0,100,2,False,set())
    def test_valid_label(self):
        self.assertTrue(validate_label(self.good()))
    def test_target_formula(self):
        got=self.good();got["actual_horizon_ms"]=99
        with self.assertRaises(ValueError):validate_label(got)
    def test_match_error_formula(self):
        got=self.good();got["match_error_ms"]=1
        with self.assertRaises(ValueError):validate_label(got)
    def test_invalid_return_empty(self):
        got=self.good();got["valid_label"]=False;got["invalid_reason"]="INVALID_CURRENT_PRICE"
        with self.assertRaises(ValueError):validate_label(got)
    def test_class_field_rejected(self):
        got=self.good();got["UP"]=1
        with self.assertRaises(ValueError):validate_label(got)
    def test_local_timestamp_field_rejected(self):
        got=self.good();got["local_timestamp_us"]=1234
        with self.assertRaises(ValueError):validate_label(got)
    def test_non_decimal_return_rejected(self):
        got=self.good();got["future_return_bps"]=100.0
        with self.assertRaises(ValueError):validate_label(got)
    def test_hft_path_not_accepted_as_feature_source(self):
        with self.assertRaises(ValueError):
            feature_path("/home/jason/quantum-hft","../../hft-realtime","aggregate_core_v1")
