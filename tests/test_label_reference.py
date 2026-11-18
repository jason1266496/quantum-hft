import unittest
from unittest.mock import patch
from data_pipeline.labels.reference import reference_label
from data_pipeline.labels.builder import _label
from tests.fixtures.phase2d.helpers import rows

class LabelReferenceTests(unittest.TestCase):
    def test_independent_forward_matcher(self):
        data=rows((0,101),("100","101"))
        with patch("data_pipeline.labels.matcher.first_target",side_effect=AssertionError("called")):
            got=reference_label(data,0,100,len(data))
        self.assertEqual((got["actual_horizon_ms"],got["match_error_ms"]),(101,1))
    def test_builder_reference_agree_all_horizons(self):
        data=rows((0,101,201,501,1001),("100","101","99","100","100"))
        times=[r.event_time_ms for r in data]
        for h in (100,200,500,1000):
            for i in range(len(data)):
                with self.subTest(h=h,i=i):
                    main=_label(data,times,i,h,len(data),False,set())
                    ref=reference_label(data,i,h,len(data))
                    for key in ("target_event_time_ms","actual_horizon_ms","match_error_ms",
                                "future_mid_price","future_return_bps","valid_label","invalid_reason"):
                        self.assertEqual(main[key],ref[key])
    def test_reference_stops_at_session_boundary(self):
        data=rows((0,50),session="a")+rows((100,),session="b")
        got=reference_label(data,0,100,2)
        self.assertEqual(got["invalid_reason"],"SESSION_TAIL_INSUFFICIENT")
