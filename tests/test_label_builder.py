import unittest
from decimal import Decimal
from data_pipeline.labels.builder import _label,event_interval_profile,distribution
from tests.fixtures.phase2d.helpers import rows

def label(data,horizon=100,index=0,end=None,rollback=frozenset()):
    if end is None: end=len(data)
    return _label(data,[r.event_time_ms for r in data],index,horizon,end,False,rollback)

class LabelBuilderTests(unittest.TestCase):
    def test_positive_return(self):
        got=label(rows((0,100),("100","101")))
        self.assertEqual(got["future_return_bps"],Decimal("100"))
    def test_negative_return(self):
        got=label(rows((0,100),("100","99")))
        self.assertEqual(got["future_return_bps"],Decimal("-100"))
    def test_zero_return_retained(self):
        got=label(rows((0,100),("100","100")))
        self.assertTrue(got["valid_label"])
        self.assertEqual(got["future_return_bps"],0)
    def test_actual_horizon_and_match_error(self):
        got=label(rows((0,101)))
        self.assertEqual((got["actual_horizon_ms"],got["match_error_ms"]),(101,1))
    def test_current_zero_invalid(self):
        got=label(rows((0,100),("0","101")))
        self.assertEqual(got["invalid_reason"],"INVALID_CURRENT_PRICE")
        self.assertIsNone(got["future_return_bps"])
    def test_future_zero_invalid(self):
        got=label(rows((0,100),("100","0")))
        self.assertEqual(got["invalid_reason"],"INVALID_FUTURE_PRICE")
    def test_invalid_feature_current(self):
        got=label(rows((0,100),valid=(False,True)))
        self.assertEqual(got["invalid_reason"],"INVALID_CURRENT_FEATURE_ROW")
    def test_invalid_feature_future(self):
        got=label(rows((0,100),valid=(True,False)))
        self.assertEqual(got["invalid_reason"],"INVALID_FUTURE_FEATURE_ROW")
    def test_tail(self):
        got=label(rows((0,99)))
        self.assertEqual(got["invalid_reason"],"SESSION_TAIL_INSUFFICIENT")
        self.assertIsNone(got["target_event_time_ms"])
    def test_cross_view_same_event(self):
        a=rows((0,100),("100","101"),view="aggregate_core_v1")
        b=rows((0,100),("100","101"),view="depth_top5_v1")
        x,y=label(a),label(b)
        for key in ("target_event_time_ms","actual_horizon_ms","match_error_ms",
                    "future_mid_price","future_return_bps"):
            self.assertEqual(x[key],y[key])
    def test_backward_event_invalid(self):
        data=rows((100,50,150))
        got=label(data,index=1,rollback={1})
        self.assertEqual(got["invalid_reason"],"EVENT_TIME_BACKWARDS")
    def test_event_interval_profile(self):
        got=event_interval_profile(rows((0,0,101,202)))
        session=got["artificial_session"]
        self.assertEqual(session["zero"],1)
        self.assertEqual(session["greater_than_100ms"],2)
        self.assertIsNone(session["gap_threshold_ms"])
    def test_distribution_includes_zero(self):
        got=distribution((Decimal("-1"),Decimal("0"),Decimal("1")),(1,5,25,50,75,95,99))
        self.assertEqual((got["count"],got["median"]),(3,"0"))
