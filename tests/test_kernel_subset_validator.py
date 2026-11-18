import copy,unittest
from unittest.mock import patch
from pathlib import Path
from data_pipeline.datasets.checksums import fingerprint
from experiments.kernel_comparison.validator import validate_rows,validate_membership,assert_exact_subset,read_split
from experiments.kernel_comparison.freeze import safe,ROOT
from models.classical.feature_policy import matrix,FEATURES
from tests.fixtures.phase3b.helpers import rows,dataset,fresh
class ValidatorTests(unittest.TestCase):
    def test_valid_train(self):self.assertEqual(validate_rows(rows(),1000,"Train")["status"],"PASS")
    def test_duplicate_ids(self):
        r=rows();r[-1]["sample_id"]=r[0]["sample_id"]
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):validate_rows(r,1000,"Train")
    def test_split_overlap(self):
        r=rows()
        with self.assertRaisesRegex(ValueError,"OVERLAP"):validate_membership({"Train":r,"Validation":r},1000)
    def test_nonoverlap_valid(self):self.assertEqual(validate_membership({"Train":rows(),"Validation":rows(split="Validation")},1000)["split_overlap"],0)
    def test_wrong_label_rejected(self):
        r=rows();r[0]["class_label"]=2
        with self.assertRaises(ValueError):validate_rows(r,1000,"Train")
    def test_feature_order_and_metadata_excluded(self):
        r=rows();r[0]["sample_id"]="POISON";x=matrix(r);self.assertEqual(x.shape[1],4);self.assertEqual(x[0,0],float(r[0]["obi_5"]))
    def test_unsorted_rejected(self):
        with self.assertRaisesRegex(ValueError,"NOT_SORTED"):validate_rows(rows()[::-1],1000,"Train")
    def test_horizon_separate(self):
        with self.assertRaises(ValueError):validate_rows(rows(),100,"Train")
    def test_holdout_guard_before_open(self):
        with patch.object(Path,"open",side_effect=AssertionError("opened")):
            with self.assertRaisesRegex(ValueError,"PROHIBITED"):read_split(Path("/unused"),1000,"Final Holdout")
    def test_test_guard_before_open(self):
        with patch.object(Path,"open",side_effect=AssertionError("opened")):
            with self.assertRaisesRegex(ValueError,"BEFORE_SEAL"):read_split(Path("/unused"),1000,"Test")
    def test_read_fixture_dataset_unchanged(self):
        ds=dataset();p=ds/"1000ms/train.csv";before=fingerprint(p)
        got,n=read_split(ds,1000,"Train");self.assertEqual(len(got),36);self.assertEqual(n,36);self.assertEqual(fingerprint(p),before)
    def test_exact_subset_no_modification(self):
        r=rows();self.assertTrue(assert_exact_subset([r[0],r[3]],r,[0,3]))
        changed=copy.deepcopy(r);changed[0]["obi_5"]="999"
        with self.assertRaises(ValueError):assert_exact_subset([changed[0]],r,[0])
    def test_hft_write_guard(self):
        for path in ("/home/jason/hft-realtime/src/x.cpp","/home/jason/hft-realtime-codex/results/x.csv"):
            with self.assertRaisesRegex(ValueError,"OUTSIDE_PHASE3B"):safe(path)
    def test_old_phase_write_guard(self):
        for path in ("artifacts/phase3a/x.json","artifacts/datasets/x.csv","docs/PHASE3A_REPORT_x.md"):
            with self.assertRaises(ValueError):safe(ROOT/path)
