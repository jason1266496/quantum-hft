import unittest
from experiments.kernel_comparison.freeze import write,freeze,verify_freeze,protocol,FEATURES
from experiments.kernel_comparison.validator import validate_membership
from experiments.kernel_comparison.metrics import matrix_size
from tests.fixtures.phase3b.helpers import run_tree,rows
class FreezeTests(unittest.TestCase):
    def make_frozen(self):
        r=run_tree()
        for h in (1000,100):
            write(r/(str(h)+"ms")/"subset/kernel_comparison_subset_v2_manifest.json",{"status":"FROZEN","sample_ids":["fixture"]})
            write(r/(str(h)+"ms")/"scaler/scaler.json",{"fit_split":"Train","feature_order":list(FEATURES)})
            write(r/(str(h)+"ms")/"selection/selection_manifest.json",{"test_evaluated":False})
        for name in ("research_protocol","feature_policy","classification_policy"):write(r/"policy"/(name+".json"),{"fixture":True})
        write(r/"selection_barrier.json",{"fixture":True})
        freeze(r,{"1000":{"Train":["fixture-a"]},"100":{"Train":["fixture-b"]}})
        return r
    def test_frozen_manifest_and_sha(self):
        r=self.make_frozen();self.assertEqual(verify_freeze(r)["status"],"PASS");self.assertTrue((r/"freeze/FROZEN.sha256").exists())
    def test_freeze_detects_change(self):
        r=self.make_frozen()
        with (r/"1000ms/scaler/scaler.json").open("a") as f:f.write(" ")
        with self.assertRaisesRegex(ValueError,"FROZEN_INPUT_CHANGED"):verify_freeze(r)
    def test_no_overwrite(self):
        r=run_tree();p=r/"summary/x.json";write(p,{"x":1})
        with self.assertRaises(FileExistsError):write(p,{"x":2})
    def test_deterministic_manifest_serialization(self):
        r=run_tree();a=write(r/"summary/a.json",protocol());b=write(r/"summary/b.json",protocol());self.assertEqual(a,b)
    def test_no_quantum_or_backtest_protocol(self):
        p=protocol();self.assertFalse(p["quantum_budget_subset_created"]);self.assertEqual(p["timing_scope"],"PYTHON_BATCH_INFERENCE_ONLY")
    def test_sizes_not_quantum_runtime(self):self.assertEqual(matrix_size(30,10,10)["quantum_runtime"],"NOT_ESTIMATED")
