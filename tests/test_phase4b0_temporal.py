"""Synthetic timing/leakage fixtures only, no estimators or official input reads."""
import unittest,copy
from pathlib import Path
from experiments.phase4b0 import contracts as c,temporal as t,audit,runner
from tests.fixtures.phase4b0.helpers import raw,source,prepared,PoisonLabels
class OrderingTests(unittest.TestCase):
    def test_positions(self):self.assertEqual(t.positions(10,4),[0,3,6,9])
    def test_insufficient_budget_stops(self):
        with self.assertRaises(ValueError):t.positions(95,96)
    def test_time_order(self):
        a,_=source(10);self.assertEqual([r["t"] for r in t.sample(list(reversed(a)),4)],[0,300,600,900])
    def test_metadata_tie_break_numeric(self):
        a,_=source(2);a[0]["t"]=a[1]["t"]=0;a[0]["record"]=10;a[1]["record"]=2
        self.assertEqual([r["record"] for r in t.sample(a,2)],[2,10])
    def test_sampling_deterministic(self):
        a,_=source(100);self.assertEqual(t.sample(a,20),t.sample(list(reversed(a)),20))
    def test_duplicate_sample_ID_rejected(self):
        a,_=source(3);a[1]["id"]=a[0]["id"]
        with self.assertRaises(ValueError):t.sample(a,2)
    def test_labels_never_projected(self):
        a=audit.project(PoisonLabels(raw()),0);self.assertNotIn("future_return_bps",a)
class IdentityTests(unittest.TestCase):
    def test_same_market_event_across_source_aliases_grouped(self):
        a=audit.project(raw(source="a",session="a"),0);b=audit.project(raw(source="b",session="b"),0)
        m,_,d=t.leakage_groups([a,b]);self.assertEqual(m[a["id"]],m[b["id"]]);self.assertEqual(d["exact_duplicate_observations"],1)
    def test_conflicting_update_identity_flagged(self):
        a=audit.project(raw(i=0),0);b=audit.project(raw(i=1,update_base=999),1)
        _,_,d=t.leakage_groups([a,b]);self.assertEqual(d["conflicting_update_identity_count"],1)
    def test_equal_state_at_different_time_is_not_duplicate(self):
        a,_=source(2);m,_,d=t.leakage_groups(a);self.assertEqual(len(set(m.values())),2);self.assertEqual(d["exact_duplicate_observations"],0)
    def test_update_ids_global_not_source_scoped(self):
        a=audit.project(raw(source="a"),0);b=audit.project(raw(source="b"),0)
        m,_,_=t.leakage_groups([a,b]);self.assertEqual(m[a["id"]],m[b["id"]])
    def test_cross_session_endpoint_witness_forbidden(self):
        a=audit.project(raw(i=0,source="a",session="a"),0);b=audit.project(raw(i=10,source="b",session="b"),1)
        m,_,_=t.leakage_groups([a,b]);counts,_=audit.witnesses([a,b],m);self.assertFalse(a["eligible"]);self.assertEqual(counts["endpoint_not_observable_in_filtered_Train"],2)
    def test_same_session_endpoint_witness(self):
        a=audit.project(raw(i=0),0);b=audit.project(raw(i=10),1)
        m,_,_=t.leakage_groups([a,b]);audit.witnesses([a,b],m);self.assertTrue(a["eligible"]);self.assertEqual(a["target_group"],m[b["id"]])
    def test_future_price_contradiction(self):
        a=audit.project(raw(i=0),0);b=audit.project(raw(i=10),1);b["_mid"]="101"
        m,_,_=t.leakage_groups([a,b]);_,bad=audit.witnesses([a,b],m);self.assertEqual(bad,[a["id"]])
class BoundaryTests(unittest.TestCase):
    def test_actual_endpoint_not_nominal(self):
        r=raw();r.update(target_event_time_ms="1001",actual_horizon_ms="1001",match_error_ms="1")
        self.assertEqual(t.actual_endpoint(r),1001)
    def test_inconsistent_endpoint_rejected(self):
        r=raw();r["target_event_time_ms"]="1001"
        with self.assertRaises(ValueError):t.actual_endpoint(r)
    def test_missing_endpoint_field_safe(self):
        r=raw();del r["actual_horizon_ms"]
        with self.assertRaisesRegex(ValueError,"MISSING_ACTUAL_HORIZON_MS"):t.actual_endpoint(r)
    def fixture(self):
        rows,region,m,b=prepared();tr,va,cut,counts=t.split_candidates(rows,region,m,b)
        return t.sample(tr,96),t.sample(va,384),region,m,cut
    def test_real_budget_purge_no_overlap(self):
        tr,va,region,m,b=self.fixture();self.assertEqual(t.check_split(tr,va,m,b,region["end_exclusive"])["status"],"PASS")
    def test_equality_boundary_purged(self):
        rows,region,m,b=prepared(100);region["end_exclusive"]=2000;rows=[r for r in rows if r["t"]<2000]
        tr,_,cut,_=t.split_candidates(rows,region,m,b);self.assertEqual(cut,1000);self.assertFalse(any(r["t"]==0 for r in tr))
    def test_actual_1001_equality_not_allowed(self):
        r=audit.project(raw(),0);r.update(end=1001,eligible=True);m={r["id"]:"g"};b={"g":{"min_t":0,"max_t":0,"max_end":1001}}
        tr,_,_,_=t.split_candidates([r],{"source_id":"fixture","session_id":"s","start":0,"end_exclusive":2002},m,b)
        self.assertEqual(tr,[])
    def test_embargo_positive(self):
        tr,va,region,m,b=self.fixture();new=copy.deepcopy(tr);new[-1]["end"]=b-10
        with self.assertRaisesRegex(ValueError,"ACTUAL_ENDPOINT_OR_EMBARGO"):t.check_split(new,va,m,b,region["end_exclusive"],embargo=10)
    def test_sample_overlap_rejected(self):
        tr,va,region,m,b=self.fixture()
        with self.assertRaisesRegex(ValueError,"SAMPLE_ID_OVERLAP"):t.check_split(tr,va+[tr[0]],m,b,region["end_exclusive"])
    def test_duplicate_event_group_not_split(self):
        tr,va,region,m,b=self.fixture();m=dict(m);m[va[0]["id"]]=m[tr[0]["id"]]
        with self.assertRaisesRegex(ValueError,"DUPLICATE_EVENT_GROUP"):t.check_split(tr,va,m,b,region["end_exclusive"])
    def test_session_boundaries(self):
        rows,region,m,b=prepared();rows[0]["session"]="wrong"
        with self.assertRaisesRegex(ValueError,"SESSION_BOUNDARY"):t.split_candidates(rows,region,m,b)
    def test_Validation_label_end_session_rejected(self):
        tr,va,region,m,b=self.fixture();va[-1]["end"]=region["end_exclusive"]
        with self.assertRaisesRegex(ValueError,"VALIDATION_LABEL_CROSSES_SESSION"):t.check_split(tr,va,m,b,region["end_exclusive"])
class ProtocolTests(unittest.TestCase):
    def test_manifest_integrity(self):
        expected={"a":{"sha256":"abc","size_bytes":1}};c.verify_references(expected,copy.deepcopy(expected))
        with self.assertRaises(ValueError):c.verify_references(expected,{"a":{"sha256":"changed","size_bytes":1}})
    def test_missing_required_field_fails_safely(self):
        r=raw();del r["local_update_id"]
        with self.assertRaisesRegex(ValueError,"MISSING_LOCAL_UPDATE_ID"):audit.project(r,0)
    def test_current_features_ignore_future_fields(self):
        r=PoisonLabels(raw());self.assertEqual(audit.current_formula_errors(r),[])
    def test_fixed_feature_formula_detects_mismatch(self):
        r=raw();r["obi_5"]="0";self.assertIn("obi_5",audit.current_formula_errors(r))
    def test_three_fold_metadata_only_sampling(self):
        rows=[];regions=[]
        for i in range(3):
            rr,reg=source(1000,"src"+str(i),i*1000000,i*1000000+1000);rows+=rr;regions.append(reg)
        m,b,_=t.leakage_groups(rows);audit.witnesses(rows,m)
        plan,folds=runner.candidates({"rows":rows,"catalog":regions,"mapping":m,"group_bounds":b,"fatal_reasons":[]})
        self.assertEqual(plan["status"],"FEASIBLE");self.assertEqual([(len(tr),len(va)) for _,tr,va,_ in folds],[(96,384)]*3)
    def test_missing_class_preserved_and_blocked(self):
        a={"fold_id":1,"Train":{"DOWN":0,"FLAT":96,"UP":0},"Validation":{"DOWN":0,"FLAT":384,"UP":0}}
        b=copy.deepcopy(a);self.assertEqual(runner.support_policy([a])["status"],"BLOCKED");self.assertEqual(a,b)
    def test_unsafe_source_no_alternative_selected(self):
        rr,reg,m,b=prepared()
        plan,folds=runner.candidates({"rows":rr,"catalog":[reg],"mapping":m,"group_bounds":b,"fatal_reasons":["UNRELIABLE_TIME_CONTINUITY"]})
        self.assertEqual(plan["status"],"BLOCKED");self.assertEqual(folds,[])
    def test_static_no_model_APIs(self):
        root=Path(__file__).resolve().parents[1];self.assertEqual(runner.static_safety(sorted((root/"experiments/phase4b0").glob("*.py"))+[root/"tools/prepare_walk_forward_protocol.py"])["status"],"PASS")
    def test_old_output_forbidden(self):
        with self.assertRaises(ValueError):c.safe(c.DATA/"new.json")
    def test_run_id_forbidden(self):
        with self.assertRaises(ValueError):c.runpath("../old")
if __name__=="__main__":unittest.main()
