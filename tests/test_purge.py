import unittest
from data_pipeline.splits.purge import crosses_boundary,purge_reason
from tests.fixtures.phase2e.helpers import pipeline
class PurgeTests(unittest.TestCase):
    def test_100(self):self.assertTrue(crosses_boundary(0,100,100))
    def test_200(self):self.assertTrue(crosses_boundary(0,200,200))
    def test_500(self):self.assertTrue(crosses_boundary(0,500,500))
    def test_1000(self):self.assertTrue(crosses_boundary(0,1000,1000))
    def test_exact_equality(self):self.assertEqual(purge_reason(99,100,100),"PURGED_LABEL_WINDOW_CROSSES_SPLIT")
    def test_actual_target_not_nominal(self):self.assertTrue(crosses_boundary(0,301,300))
    def test_tail_not_fabricated(self):self.assertFalse(crosses_boundary(0,None,100))
    def test_purge_counts(self):
        data,plan,p,m,*_=pipeline()
        for split in ("Train","Validation","Test"):
            self.assertEqual([m["purge_report"][split][str(h)]["purged_count"] for h in (100,200,500,1000)],[1,2,5,10])
    def test_count_conservation(self):
        data,plan,p,m,*_=pipeline()
        for entries in m["entries"].values():
            for entry in entries:
                for c in entry["per_horizon"].values():
                    self.assertEqual(entry["raw_rows"],c["invalid_label_rows"]+c["purged_rows"]+c["match_error_filtered_rows"]+c["final_rows"])
