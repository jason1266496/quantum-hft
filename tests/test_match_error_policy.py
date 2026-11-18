import unittest
from data_pipeline.splits.matcher_policy import choose_policy,STATIC_THRESHOLDS,accepted
from data_pipeline.splits.splitter import training_candidates
from tests.fixtures.phase2e.helpers import candidates,pipeline
class MatchPolicyTests(unittest.TestCase):
    def test_minimum_not_maximum_retention(self):
        p=choose_policy(candidates(),"aggregate_core_v1")
        self.assertEqual(set(p["chosen_threshold_by_horizon"].values()),{"1"})
    def test_all_candidates_present(self):
        p=choose_policy(candidates(),"aggregate_core_v1")
        self.assertEqual(p["threshold_candidates"],[*STATIC_THRESHOLDS,"TRAIN_P95","TRAIN_P99"])
    def test_training_quantiles(self):
        p=choose_policy(candidates(),"aggregate_core_v1")
        self.assertEqual(p["retention_by_candidate"]["100"]["statistics"]["count"],20)
        self.assertFalse(p["phase2d_all_data_quantiles_used"])
    def test_test_forbidden(self):
        c=candidates();c[100][0]["split"]="Test"
        with self.assertRaises(ValueError):choose_policy(c,"aggregate_core_v1")
    def test_holdout_forbidden(self):
        c=candidates();c[100][0]["is_holdout"]=True
        with self.assertRaises(ValueError):choose_policy(c,"aggregate_core_v1")
    def test_target_outside_train_forbidden(self):
        c=candidates();c[100][0]["training_end_exclusive"]=c[100][0]["target_event_time_ms"]
        with self.assertRaises(ValueError):choose_policy(c,"aggregate_core_v1")
    def test_insufficient_evidence_no_forced_policy(self):
        p=choose_policy(candidates((99,)*20),"aggregate_core_v1")
        self.assertEqual(p["status"],"NEED_POLICY_REVIEW")
    def test_training_candidates_prevent_cross_boundary(self):
        data,plan,p,*_=pipeline()
        c=training_candidates(data,plan)
        self.assertTrue(all(x["target_event_time_ms"]<plan["boundaries"][0] for h in c for x in c[h]))
    def test_frozen_acceptance(self):
        p=choose_policy(candidates(),"aggregate_core_v1")
        self.assertTrue(accepted(1,100,p));self.assertFalse(accepted(2,100,p))
