import unittest
from dataclasses import replace
from data_pipeline.splits.validator import validate
from tests.fixtures.phase2e.helpers import pipeline
class SplitValidatorTests(unittest.TestCase):
    def check(self,parts):
        data,plan,policy,membership,scaler,windows=parts
        return validate(data,plan,membership,policy,scaler,windows)
    def test_valid(self):self.assertEqual(self.check(pipeline())["status"],"PASS")
    def flip_order(self,left,right):
        parts=pipeline();raw=parts[3]["raw"]
        latest=max(r[4] for r in raw if r[6]==right)+1
        i=next(i for i,r in enumerate(raw) if r[6]==left)
        row=list(raw[i]);row[4]=latest;raw[i]=tuple(row)
        self.assertEqual(self.check(parts)["status"],"LEAKAGE_DETECTED")
    def test_train_after_validation(self):self.flip_order("Train","Validation")
    def test_validation_after_test(self):self.flip_order("Validation","Test")
    def test_test_after_holdout(self):self.flip_order("Test","Final Holdout")
    def test_row_overlap(self):
        parts=pipeline();parts[3]["raw"].append(parts[3]["raw"][0])
        self.assertIn("SPLIT_ROW_OVERLAP",self.check(parts)["failures"])
    def test_event_overlap(self):
        parts=pipeline();raw=parts[3]["raw"]
        train=next(r for r in raw if r[6]=="Train")
        i=next(i for i,r in enumerate(raw) if r[6]=="Validation")
        row=list(raw[i]);row[5]=train[5];raw[i]=tuple(row)
        self.assertIn("EVENT_IDENTITY_OVERLAP",self.check(parts)["failures"])
    def test_cross_session(self):
        parts=pipeline();source=parts[0][-1]
        source.rows[0]=replace(source.rows[0],session_id="other")
        self.assertIn("CROSS_SOURCE_OR_SESSION",self.check(parts)["failures"])
    def test_cross_source_target(self):
        parts=pipeline();source=parts[0][-1]
        source.labels[100][0]=replace(source.labels[100][0],target_event_time_ms=9999999)
        self.assertIn("CROSS_SESSION_OR_INVALID_TARGET",self.check(parts)["failures"])
    def test_shuffle_flag(self):
        parts=pipeline();parts[1]["shuffle"]=True
        self.assertIn("SHUFFLE_PROHIBITED",self.check(parts)["failures"])
    def test_local_timestamp_prohibited(self):
        parts=pipeline();parts[1]["time_field"]="local_timestamp_us"
        self.assertEqual(self.check(parts)["status"],"LEAKAGE_DETECTED")
    def test_test_policy_forbidden(self):
        parts=pipeline();parts[2]["test_data_used_for_selection"]=True
        self.assertIn("HOLDOUT_OR_TEST_POLICY_SELECTION",self.check(parts)["failures"])
    def test_holdout_policy_forbidden(self):
        parts=pipeline();parts[2]["final_holdout_used_for_selection"]=True
        self.assertEqual(self.check(parts)["status"],"LEAKAGE_DETECTED")
    def test_scaler_holdout_forbidden(self):
        parts=pipeline();parts[4]["fit_split"]="Final Holdout"
        self.assertIn("SCALER_NOT_TRAIN_ONLY",self.check(parts)["failures"])
    def test_walk_forward_holdout_forbidden(self):
        parts=pipeline();parts[5][0]["holdout_used"]=True
        self.assertIn("WALK_FORWARD_HOLDOUT",self.check(parts)["failures"])
    def test_no_target_leakage_after_purge(self):
        parts=pipeline();plan=parts[1]
        for split,records in parts[3]["included"].items():
            if split=="Final Holdout":continue
            end=plan["boundaries"][("Train","Validation","Test").index(split)]
            self.assertTrue(all(r[7]<end for r in records))
