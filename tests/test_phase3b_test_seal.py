import unittest
from experiments.kernel_comparison.rbf_runner import TestGate,choose
from experiments.kernel_comparison.freeze import write
from tests.fixtures.phase3b.helpers import run_tree,fake_selections,candidate
class SealTests(unittest.TestCase):
    def gate(self):
        r=run_tree();return TestGate(fake_selections(r),r/"selection_barrier.json")
    def test_before_seal_denied(self):
        with self.assertRaises(ValueError):self.gate().authorize_read(1000)
    def test_both_manifests_required(self):
        g=self.gate();g.paths.pop(100)
        with self.assertRaises(ValueError):g.seal()
    def test_seal_then_read(self):
        g=self.gate();g.seal();g.authorize_read(1000);self.assertIn(1000,g.reads)
    def test_read_once(self):
        g=self.gate();g.seal();g.authorize_read(1000)
        with self.assertRaises(ValueError):g.authorize_read(1000)
    def test_claim_requires_read(self):
        g=self.gate();g.seal()
        with self.assertRaises(ValueError):g.claim(1000)
    def test_metrics_only_once(self):
        g=self.gate();g.seal();g.authorize_read(1000);g.claim(1000)
        with self.assertRaises(ValueError):g.claim(1000)
    def test_no_retune(self):
        g=self.gate();g.seal()
        with self.assertRaisesRegex(ValueError,"NO_RETUNING"):g.assert_open()
    def test_seal_immutable_detected(self):
        g=self.gate();g.seal()
        with g.paths[1000].open("a") as f:f.write(" ")
        with self.assertRaisesRegex(ValueError,"CHANGED"):g.authorize_read(1000)
    def test_test_cannot_select(self):
        with self.assertRaises(ValueError):choose([candidate()],split="Test")
    def test_holdout_cannot_select(self):
        with self.assertRaises(ValueError):choose([candidate()],split="Final Holdout")
