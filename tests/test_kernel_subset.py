import unittest
from experiments.classical.runner import temporal_indices,read_split
from tests.fixtures.phase3a.helpers import artificial_rows
from pathlib import Path
class KernelSubsetTests(unittest.TestCase):
    def test_caps_and_endpoints(self):
        for n,limit in ((150000,1000),(55000,500),(49000,500)):
            x=temporal_indices(range(n),limit)
            self.assertEqual(len(x),limit);self.assertEqual((x[0],x[-1]),(0,n-1))
    def test_all_when_small(self):self.assertEqual(temporal_indices(range(10),1000),list(range(10)))
    def test_deterministic(self):
        self.assertEqual(temporal_indices(range(1500),1000),temporal_indices(range(1500),1000))
    def test_time_sort_stable(self):self.assertEqual(temporal_indices([300,100,100,200],10),[1,2,3,0])
    def test_labels_not_sampling_input(self):
        rows=artificial_rows();a=temporal_indices([r["event_time_ms"] for r in rows],20)
        for r in rows:r["future_return_bps"]="999999"
        self.assertEqual(a,temporal_indices([r["event_time_ms"] for r in rows],20))
    def test_no_holdout(self):
        with self.assertRaisesRegex(ValueError,"HOLDOUT"):read_split(Path("not_opened"),100,"Final Holdout")
