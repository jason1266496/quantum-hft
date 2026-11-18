import unittest
from tests.fixtures.phase2e.helpers import pipeline
class WalkForwardTests(unittest.TestCase):
    def test_aggregate_windows(self):self.assertEqual(len(pipeline("aggregate_core_v1")[-1]),2)
    def test_depth_windows(self):self.assertEqual(len(pipeline()[-1]),2)
    def test_time_order(self):
        for w in pipeline()[-1]:self.assertLess(w["train"]["event_time_end"],w["validation"]["event_time_start"])
    def test_no_holdout(self):
        data,plan,p,m,scaler,windows=pipeline()
        for w in windows:
            self.assertFalse(w["holdout_used"]);self.assertLess(w["validation"]["event_time_end"],plan["boundaries"][2])
    def test_fold_policy_train_only(self):
        for w in pipeline()[-1]:
            for x in w["match_error_policy"]["selection_data_scope"]["per_horizon"].values():
                self.assertLess(x["target_end"],w["validation"]["event_time_start"])
    def test_horizon_specific_purge(self):
        w=pipeline()[-1][0]
        self.assertEqual([w["train"]["counts"][str(h)]["purged_rows"] for h in (100,200,500,1000)],[1,2,5,10])
