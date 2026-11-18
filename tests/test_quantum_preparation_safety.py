import json,unittest
from pathlib import Path
from unittest.mock import patch
from data_pipeline.datasets.checksums import fingerprint,sha_file
from experiments.quantum_preparation.io import ROOT,FIELDS,write,write_csv,load_source,safe,verify_budget_freeze
from experiments.quantum_preparation.runner import save_profile,lock_budget,research_policy
from experiments.quantum_preparation.sampler import build_budgets
from tests.fixtures.phase4a0.helpers import rows,fresh,run_tree,base_scaler
class SafetyTests(unittest.TestCase):
    def test_test_guard_before_open(self):
        with patch.object(Path,"open",side_effect=AssertionError("opened")):
            with self.assertRaisesRegex(ValueError,"PROHIBITED"):load_source(Path("/unused"),"Test","not-used")
    def test_holdout_guard_before_open(self):
        with patch.object(Path,"open",side_effect=AssertionError("opened")):
            with self.assertRaisesRegex(ValueError,"PROHIBITED"):load_source(Path("/unused"),"Final Holdout","not-used")
    def test_source_immutable(self):
        d=fresh();p=d/"train.csv";write_csv(p,FIELDS,rows());before=fingerprint(p)
        self.assertEqual(len(load_source(d,"Train",before["sha256"])),300);self.assertEqual(before,fingerprint(p))
    def test_source_hash_mismatch(self):
        d=fresh();write_csv(d/"train.csv",FIELDS,rows())
        with self.assertRaisesRegex(ValueError,"HASH_MISMATCH"):load_source(d,"Train","0"*64)
    def test_output_no_overwrite(self):
        p=fresh()/"x.json";write(p,{"x":1})
        with self.assertRaises(FileExistsError):write(p,{"x":2})
    def test_old_phases_and_hft_write_denied(self):
        for p in (ROOT/"artifacts/phase3b/x",ROOT/"artifacts/datasets/x","/home/jason/hft-realtime/src/x","/home/jason/hft-realtime-codex/results/x"):
            with self.assertRaises(ValueError):safe(p)
    def test_classification_policy_fixed(self):
        p=research_policy();self.assertEqual(p["classification_policy"],"direction_3class_exact_v1");self.assertFalse(p["test_holdout_used"])
    def test_fair_membership_and_frozen(self):
        r=run_tree();profiles={};b=build_budgets(rows(),rows(split="Validation"))
        for n in ("smoke","prototype"):profiles[n]=save_profile(r,n,b[n],base_scaler())
        for p in ("fair_comparison_policy.json","policy/research_policy.json","policy/classification_policy.json","policy/feature_policy.json"):write(r/p,{"fixture":True})
        m,digest=lock_budget(r,profiles,"fixture-parent-sha")
        self.assertEqual(verify_budget_freeze(r)["manifest_sha256"],digest)
        for n in ("smoke","prototype"):
            refs=m["profiles"][n]["same_input_for_RBF_QSVC"];self.assertEqual(refs["RBF"],refs["QSVC"])
        self.assertFalse(m["Test_used"]);self.assertFalse(m["Final_Holdout_used"])
    def test_budget_freeze_detects_change(self):
        r=run_tree();b=build_budgets(rows(),rows(split="Validation"));ps={n:save_profile(r,n,b[n],base_scaler()) for n in ("smoke","prototype")}
        for p in ("fair_comparison_policy.json","policy/research_policy.json","policy/classification_policy.json","policy/feature_policy.json"):write(r/p,{})
        lock_budget(r,ps,"fixture")
        with (r/"smoke/train.csv").open("a") as f:f.write("\n")
        with self.assertRaisesRegex(ValueError,"CHANGED"):verify_budget_freeze(r)
    def test_budget_manifest_deterministic(self):
        hashes=[]
        for _ in range(2):
            r=run_tree();b=build_budgets(rows(),rows(split="Validation"));ps={n:save_profile(r,n,b[n],base_scaler()) for n in ("smoke","prototype")}
            for p in ("fair_comparison_policy.json","policy/research_policy.json","policy/classification_policy.json","policy/feature_policy.json"):write(r/p,{})
            hashes.append(lock_budget(r,ps,"fixture")[1])
        self.assertEqual(hashes[0],hashes[1])
