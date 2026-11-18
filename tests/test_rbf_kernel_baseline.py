import unittest
from unittest.mock import patch
import numpy as np
from models.classical.scaler import TrainOnlyScaler
from models.classical.feature_policy import matrix
from experiments.kernel_comparison.rbf_runner import (grid,make_model,choose,all_single,train_select,TestGate,save_subset,test_once,eligible_primary)
from experiments.kernel_comparison.freeze import write,protocol,FEATURES
from experiments.kernel_comparison.metrics import score
from experiments.kernel_comparison.validator import read_split
from tests.fixtures.phase3b.helpers import rows,candidate,run_tree,dataset
class BaselineTests(unittest.TestCase):
    def test_twenty_configs(self):self.assertEqual(len(grid()),20)
    def test_model_parameters(self):
        m=make_model(grid()[0]);self.assertEqual(m.class_weight,"balanced");self.assertFalse(m.probability);self.assertEqual(m.random_state,42)
    def test_c_grid(self):self.assertEqual(sorted({x["C"] for x in grid()}),[.1,1.,10.,100.])
    def test_gamma_grid(self):self.assertEqual([x["gamma"] for x in grid()[:5]],["scale","auto",.01,.1,1.])
    def test_macro_f1_primary(self):self.assertEqual(choose([candidate(c=.1,f1=.4),candidate(c=10.,f1=.5)])["config"]["C"],10.)
    def test_balanced_accuracy_tie(self):self.assertEqual(choose([candidate(c=.1,ba=.4),candidate(c=10.,ba=.5)])["config"]["C"],10.)
    def test_smaller_c_before_gamma_scale(self):
        a=candidate(c=.1,g="auto");b=candidate(c=1.,g="scale");self.assertEqual(choose([b,a]),a)
    def test_gamma_scale_tie(self):
        a=candidate(g="scale");b=candidate(g="auto");self.assertEqual(choose([b,a]),a)
    def test_remaining_tie_deterministic(self):self.assertEqual(choose([candidate(g=.1),candidate(g="auto")])["config"]["gamma"],"auto")
    def test_all_single_detected(self):self.assertTrue(all_single([candidate(pred=1),candidate(pred=1)]));self.assertFalse(all_single([candidate(pred=1),candidate(pred=2)]))
    def test_train_only_scaler(self):
        x=matrix(rows());s=TrainOnlyScaler(1000,"kernel_comparison_subset_v2").fit(x,split="Train",sample_ids=[r["sample_id"] for r in rows()])
        for split in ("Validation","Test"):
            self.assertEqual(s.transform(x,split=split).shape,x.shape)
            with self.assertRaises(ValueError):s.fit(x,split=split,sample_ids=[])
        self.assertEqual(s.artifact()["fit_scope"],"kernel_comparison_subset_v2")
    def test_holdout_no_transform(self):
        x=matrix(rows());s=TrainOnlyScaler(1000,"v2").fit(x,split="Train",sample_ids=[r["sample_id"] for r in rows()])
        with self.assertRaises(ValueError):s.transform(x,split="Final Holdout")
    def test_horizon_scalers_differ(self):
        x=matrix(rows());ids=[r["sample_id"] for r in rows()]
        a=TrainOnlyScaler(100,"v2").fit(x,split="Train",sample_ids=ids)
        b=TrainOnlyScaler(1000,"v2").fit(x+10,split="Train",sample_ids=ids)
        self.assertNotEqual(a.artifact()["mean"],b.artifact()["mean"])
    def test_primary_all_single_fails_before_test(self):
        root=run_tree();write(root/"policy/research_protocol.json",protocol())
        for split in ("Train","Validation"):save_subset(root,1000,split,rows(split=split),27,list(range(27)))
        gate=TestGate({h:root/(str(h)+"ms")/"selection/selection_manifest.json" for h in (1000,100)},root/"selection_barrier.json")
        class Dummy:
            n_support_=np.array([1,1,1])
            def predict(self,x):return np.ones(len(x),dtype=int)
        with patch("experiments.kernel_comparison.rbf_runner.make_model",return_value=Dummy()),patch("experiments.kernel_comparison.rbf_runner.fit_model",return_value={"fit_wall_seconds":0,"warnings":[]}):
            with self.assertRaisesRegex(ValueError,"PRIMARY_ALL_CANDIDATES_SINGLE_CLASS"):train_select(root,1000,gate,lambda *x:None)
        self.assertFalse(gate.sealed);self.assertFalse(gate.reads)
    def test_full_two_horizon_fixture_pipeline(self):
        root=run_tree();ds=dataset();write(root/"policy/research_protocol.json",protocol())
        write(root/"environment/preflight_verified.json",{"datasets":{ds.name:{"dataset_tree_hash":"fixture-only"}}})
        for h in (1000,100):
            metadata={}
            for split in ("Train","Validation"):
                rr,n=read_split(ds,h,split);metadata[split]=save_subset(root,h,split,rr,n,list(range(n)))
            write(root/(str(h)+"ms")/"subset/selection_plan.json",{"Train":metadata["Train"],"Validation":metadata["Validation"],
               "train_sampling":{"labels_used":True},"test_plan":{"source_rows":18,"positions":list(range(18))},"construction_wall_seconds":0})
        gate=TestGate({h:root/(str(h)+"ms")/"selection/selection_manifest.json" for h in (1000,100)},root/"selection_barrier.json")
        states={h:train_select(root,h,gate,lambda *x:None) for h in (1000,100)}
        self.assertFalse(gate.reads);gate.seal();journal=[]
        with patch("experiments.kernel_comparison.rbf_runner.DATASET",ds):
            for h in (1000,100):
                m,r=test_once(root,h,states[h],gate,journal)
                self.assertEqual(r["test_evaluation"]["metric_evaluation_count"],1);self.assertFalse(r["test_evaluation"]["test_retuning_performed"])
                self.assertEqual(r["timing"]["selected_test_predict"]["timed_calls"],3)
                self.assertFalse(r["timing"]["hft_latency_claim"])
        self.assertEqual(gate.evaluated,{1000,100});self.assertTrue(all(v["all_selections_sealed"] for v in journal))
