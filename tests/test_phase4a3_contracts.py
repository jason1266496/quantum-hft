"""Artificial metadata/numerical fixtures; no market data or model training."""
import copy,unittest,io,csv
from pathlib import Path
import numpy as np
from experiments.phase4a3 import sampling as s,contracts as c
from experiments.phase4a3.runner import determinism,model
from experiments.phase4a1.preprocessing import transform
from experiments.phase4a1.metrics import score
from experiments.phase4a2.analysis import spectrum,class_similarity
from tests.fixtures.phase4a3.helpers import rows,PoisonLabels
from tests.fixtures.phase4a2.helpers import params as shortparams
class SamplingTests(unittest.TestCase):
    def meta(self,n):return [s.project_metadata(r,i) for i,r in enumerate(rows(n))]
    def test_positions_count(self):self.assertEqual(len(s.positions(150912)),96)
    def test_positions_endpoints(self):self.assertEqual((s.positions(150912)[0],s.positions(150912)[-1]),(0,150911))
    def test_positions_exact_floor(self):self.assertEqual(s.positions(10,4),[0,3,6,9])
    def test_positions_unique(self):self.assertEqual(len(set(s.positions(97))),96)
    def test_positions_insufficient(self):
        with self.assertRaises(ValueError):s.positions(95)
    def test_positions_invalid_budget(self):
        with self.assertRaises(ValueError):s.positions(100,1)
    def test_all_rows_if_exact(self):self.assertEqual(s.positions(96),list(range(96)))
    def test_poison_label_and_feature(self):
        m=[s.project_metadata(PoisonLabels(r),i) for i,r in enumerate(rows(100))]
        self.assertEqual(len(s.select(m)[0]),96)
    def test_metadata_fields_only(self):self.assertEqual(set(self.meta(1)[0]),set(s.META)|{"file_row_index"})
    def test_changing_labels_not_selection(self):
        a=rows(110);b=copy.deepcopy(a)
        for i,r in enumerate(b):r["future_return_bps"]=str(i*1000);r["obi_5"]="999"
        self.assertEqual(s.select([s.project_metadata(r,i) for i,r in enumerate(a)])[0],s.select([s.project_metadata(r,i) for i,r in enumerate(b)])[0])
    def test_reversed_input_order_metadata_selection(self):
        a=self.meta(110);chosen,_=s.select(a);chosen2,_=s.select(list(reversed(a)))
        self.assertEqual(chosen,chosen2)
    def test_duplicate_universe_rejected(self):
        a=self.meta(100);a[1]["sample_id"]=a[0]["sample_id"]
        with self.assertRaises(ValueError):s.select(a)
    def test_tie_break(self):
        a=self.meta(4)
        for r in a:r["event_time_ms"]=100
        chosen,order=s.select(list(reversed(a)),4);self.assertEqual([r["record_index"] for r in order],[1,2,3,4])
    def test_numeric_time_sort(self):
        a=self.meta(2);a[0]["event_time_ms"]=100;a[1]["event_time_ms"]=20
        self.assertEqual(s.select(a,2)[0][0]["event_time_ms"],20)
    def test_missing_class_preserved(self):
        r=[{"future_return_bps":"0"}]*96;self.assertEqual(s.class_counts(r),{"DOWN":0,"FLAT":96,"UP":0})
    def test_exact_sign_policy(self):self.assertEqual(s.class_counts([{"future_return_bps":"-0"},{"future_return_bps":"1e-100"},{"future_return_bps":"-1e-100"}]),{"DOWN":1,"FLAT":1,"UP":1})
    def test_invalid_selected_no_silent_filter(self):
        with self.assertRaises(ValueError):s.valid_selected({"feature_view":"aggregate_core_v1","requested_horizon_ms":"1000","valid_feature_row":"false","valid_label":"true"})
class ContractTests(unittest.TestCase):
    def test_no_test_source(self):
        with self.assertRaises(ValueError):list(c.read_rows(c.DATASET/"1000ms/test.csv",c.runpath("20261030T000000Z")))
    def test_no_holdout_source(self):
        with self.assertRaises(ValueError):list(c.read_rows(c.DATASET/"1000ms/final_holdout.csv",c.runpath("20261030T000000Z")))
    def test_output_hft_prohibited(self):
        with self.assertRaises(ValueError):c.safe(Path("/home/jason/hft-realtime/x.json"))
    def test_old_result_output_prohibited(self):
        with self.assertRaises(ValueError):c.safe(c.P1/"x.json")
    def test_wrong_run_id(self):
        with self.assertRaises(ValueError):c.runpath("../old")
    def test_protocol_fixed(self):
        p=c.protocol();self.assertEqual(p["Train_size"],96);self.assertEqual(p["RBF"]["gamma"],.01);self.assertEqual(p["repeat_count"],1)
    def test_protocol_no_label_eligibility(self):self.assertFalse(c.protocol()["selection"]["labels_used"])
    def test_model_fixed_parameters(self):
        for kind in ("RBF","QSVC"):
            m=model(kind);self.assertEqual(m.C,100.);self.assertEqual(m.class_weight,"balanced");self.assertEqual(m.random_state,42)
    def test_unknown_model(self):
        with self.assertRaises(ValueError):model("OTHER")
    def test_rare_support_metrics(self):
        m=score(np.array([0]+[1]*94+[2]),np.ones(96,dtype=int));self.assertEqual(m["prediction_class_count"],1);self.assertIn("CLASS_COVERAGE_WARNING",m["warnings"]);self.assertEqual(m["per_class"]["UP"]["recall"],0)
    def test_finite_rank(self):self.assertAlmostEqual(spectrum(np.eye(4))["entropy_effective_rank"],4)
    def test_rare_class_no_within_pair(self):
        d=class_similarity(np.eye(4),np.array([0,1,1,2]));self.assertEqual(d["class_pairs"]["UP/UP"],{"count":0})
    def test_serialized_angles_roundtrip(self):
        x=np.array([[0,np.pi,.1,.2]]);z=np.array([[float(format(v,".17g")) for v in r] for r in x]);np.testing.assert_array_equal(x,z)
    def test_effective_balanced_weights_change(self):
        counts=[2,92,2];weights=[96/(3*n) for n in counts];self.assertEqual(weights[0],16);self.assertLess(weights[1],1)
    def test_determinism_reject_changed_prediction(self):
        metric=score(np.array([0,1,2]),np.array([0,1,2]));m={"predictions":[0,1,2],"metrics":metric,"effective_class_weight":{"DOWN":1}}
        first={"inputs":{},"frozen_subset_sha256":"a","models":{"rbf":copy.deepcopy(m),"qsvc":copy.deepcopy(m)}};repeat=copy.deepcopy(first);repeat["models"]["qsvc"]["predictions"][0]=1
        d=determinism(first,{"x":np.eye(2)},repeat,{"x":np.eye(2)});self.assertEqual(d["status"],"FAIL")
if __name__=="__main__":unittest.main()
