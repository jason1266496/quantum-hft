import json,unittest
from pathlib import Path
from unittest.mock import patch
from experiments.phase4a1.contracts import (verify_budget,load_profile,source_file,write,save_array,safe,ROOT,class_of,FEATURES,sha)
from tests.fixtures.phase4a1.helpers import budget,fresh
class ContractTests(unittest.TestCase):
    def test_frozen_fixture_valid(self):
        r,m=budget();self.assertEqual(verify_budget(r),m)
    def test_profile_sizes_and_same_ids(self):
        r,m=budget()
        for p,n in (("smoke",24),("prototype",96)):
            b=load_profile(r,p,m);self.assertEqual(b["Train"]["x"].shape,(n,4));self.assertFalse(set(b["Train"]["ids"])&set(b["Validation"]["ids"]))
    def test_test_and_holdout_guard_before_open(self):
        with patch.object(Path,"open",side_effect=AssertionError("opened")):
            for s in ("Test","Final Holdout"):
                with self.assertRaises(ValueError):source_file(Path("/unused"),"prototype",s,"angles")
    def test_no_unknown_budget_or_resampling_profile(self):
        with self.assertRaises(ValueError):source_file(Path("/unused"),"full","Train","raw")
    def test_future_label_exact(self):
        self.assertEqual([class_of("-1e-100"),class_of("0.0000"),class_of("1e-100")],[0,1,2])
    def test_changed_file_rejected(self):
        r,m=budget()
        with (r/"prototype/train_shared_angles.csv").open("a") as f:f.write("\n")
        with self.assertRaisesRegex(ValueError,"CHANGED"):verify_budget(r)
    def test_wrong_feature_order_contract(self):
        r,m=budget();m["feature_order"].reverse()
        with (r/"quantum_budget_subset_v1_manifest.json").open("w") as f:json.dump(m,f)
        with self.assertRaisesRegex(ValueError,"CONTRACT_CHANGED"):verify_budget(r)
    def test_output_no_overwrite(self):
        p=fresh()/"x.json";write(p,{})
        with self.assertRaises(FileExistsError):write(p,{})
    def test_old_phase_and_hft_write_prohibited(self):
        for p in (ROOT/"artifacts/phase4a0/x.json",ROOT/"artifacts/datasets/x.csv","/home/jason/hft-realtime/src/x.cpp"):
            with self.assertRaises(ValueError):safe(p)
    def test_frozen_source_unchanged_by_loading(self):
        r,m=budget();before=sha(r/"prototype/train.csv");load_profile(r,"prototype",m);self.assertEqual(before,sha(r/"prototype/train.csv"))
