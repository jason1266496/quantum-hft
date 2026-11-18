import unittest
import numpy as np
from models.classical.feature_policy import FEATURES,matrix,validate_scope
from tests.fixtures.phase3a.helpers import artificial_rows
class ClassicalFeatureTests(unittest.TestCase):
    def test_fixed_order(self):self.assertEqual(FEATURES,("obi_5","spread_bps","bid_volume_5","ask_volume_5"))
    def test_metadata_excluded(self):
        r=artificial_rows(3);a=matrix(r)
        for x in r:x.update({"source_id":"changed","sample_id":"changed","event_time_ms":"99999"})
        np.testing.assert_array_equal(a,matrix(r))
    def test_labels_excluded(self):
        r=artificial_rows(3);a=matrix(r)
        for x in r:x.update({"future_return_bps":"99999","actual_horizon_ms":"99999","match_error_ms":"99999"})
        np.testing.assert_array_equal(a,matrix(r))
    def test_nonfinite_feature(self):
        r=artificial_rows(3);r[0]["obi_5"]="NaN"
        with self.assertRaises(ValueError):matrix(r)
    def test_200_500_depth_prohibited(self):
        for view,h in (("aggregate_core_v1",200),("aggregate_core_v1",500),("depth_top5_v1",100)):
            with self.assertRaises(ValueError):validate_scope(view,h)
    def test_two_horizons_allowed(self):
        validate_scope("aggregate_core_v1",100);validate_scope("aggregate_core_v1",1000)
