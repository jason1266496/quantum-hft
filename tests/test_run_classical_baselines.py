import contextlib,json,unittest
from io import StringIO
from unittest.mock import patch
from tools.run_classical_baselines import execute
from experiments.classical.runner import experiment
from models.classical.registry import safe_output,write_json
from models.classical.timing import predict_batch
from tests.fixtures.phase3a.helpers import fixture,make_dataset,xy
class RunClassicalTests(unittest.TestCase):
    def test_scope_approval_required(self):
        with self.assertRaises(ValueError):execute("20990101T000000Z",False)
    def test_old_fail_run_id_forbidden(self):
        with self.assertRaises(ValueError):execute("20261026T205307Z",True)
    def test_dependency_failure_before_run(self):
        with patch("tools.run_classical_baselines.dependencies",side_effect=ModuleNotFoundError("sklearn")),patch("pathlib.Path.mkdir") as mkdir:
            with self.assertRaises(ModuleNotFoundError):execute("20990101T000000Z",True)
            mkdir.assert_not_called()
    def test_hft_and_old_fail_write_forbidden(self):
        for p in ("/home/jason/hft-realtime/out","/home/jason/hft-realtime-codex/results/out",
                  "/home/jason/quantum-hft/artifacts/phase3a/20261026T205307Z/new.json"):
            with self.assertRaises(ValueError):safe_output(p)
    def test_output_existing_refused(self):
        with fixture() as base:
            p=base/"out.json";write_json(p,{})
            with self.assertRaises(FileExistsError):write_json(p,{"x":1})
    def test_batch_timing_not_hft_latency(self):
        import numpy as np
        pred,timing=predict_batch(lambda x:np.zeros(len(x),dtype=int),[1,2,3],repeats=3)
        self.assertEqual(timing["timing_scope"],"PYTHON_BATCH_INFERENCE_ONLY")
        self.assertEqual((timing["warmup_calls"],timing["timed_calls"]),(1,3))
    def test_full_synthetic_workflow(self):
        with fixture() as base:
            dataset=make_dataset(base/"dataset");run=base/"run";run.mkdir()
            for name in ("policy","comparison","timing","logs"):(run/name).mkdir()
            original={p:p.read_bytes() for p in dataset.rglob("*") if p.is_file()}
            with contextlib.redirect_stdout(StringIO()),contextlib.redirect_stderr(StringIO()):
                result=experiment(run,dataset)
            self.assertEqual(result["test_gate"]["test_evaluations"],8)
            self.assertEqual(result["test_gate"]["sealed_selections"],8)
            self.assertFalse(result["holdout_values_read"])
            self.assertEqual(set(result["class_distributions"]),{"100","1000"})
            self.assertTrue(all(v["test_evaluation"]["metric_evaluation_count"]==1 for v in result["models"].values()))
            self.assertTrue(all(v["timing"]["test_predict"]["timed_calls"]==3 for v in result["models"].values()))
            self.assertEqual(original,{p:p.read_bytes() for p in dataset.rglob("*") if p.is_file()})
            self.assertFalse((run/"200ms").exists());self.assertFalse((run/"500ms").exists())
            self.assertFalse(any("quantum" in p.name.lower() for p in run.rglob("*")))
