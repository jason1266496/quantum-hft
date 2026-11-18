"""No official data reads: artificial fixtures are the mandatory execution gate."""
import unittest,copy,csv,io
import numpy as np
from qiskit.quantum_info import Statevector
from qiskit_machine_learning.algorithms import QSVC
from experiments.phase4b1 import contracts as c,inputs,preprocessing as p,numerics as n,analysis as a
from experiments.phase4a4_recovery.schema import validate_metrics
from tests.fixtures.phase4b1.helpers import data,member,kernel_data,stage,raw
from data_pipeline.datasets.schema import sample_id
class InputTests(unittest.TestCase):
    def setUp(self):self.f,self.rows=data()
    def test_complete_artificial_loader(self):
        f=inputs.assemble(self.f,self.rows)
        self.assertEqual(f["Train"]["x"].shape,(96,4));self.assertEqual(f["Validation"]["x"].shape,(384,4))
        self.assertEqual(np.bincount(f["Train"]["y"],minlength=3).tolist(),[16,76,4])
    def test_csv_decode_and_order(self):
        out=io.StringIO();w=csv.DictWriter(out,fieldnames=list(next(iter(self.rows.values()))));w.writeheader();w.writerows(self.rows.values())
        decoded={r["sample_id"]:r for r in csv.DictReader(io.StringIO(out.getvalue()))}
        self.assertEqual(inputs.assemble(self.f,decoded)["Train"]["ids"],self.f["Train"]["sample_ids"])
    def test_frozen_ID_order_mismatch(self):
        self.f["Train"]["sample_ids"].reverse()
        with self.assertRaisesRegex(ValueError,"MANIFEST_ID_ORDER"):inputs.assemble(self.f,self.rows)
    def test_missing_required_field_safe(self):
        sid=self.f["Train"]["sample_ids"][0];del self.rows[sid]["future_return_bps"]
        with self.assertRaisesRegex(ValueError,"MISSING_FUTURE_RETURN_BPS"):inputs.assemble(self.f,self.rows)
    def test_unknown_ID_stops(self):
        del self.rows[self.f["Train"]["sample_ids"][0]]
        with self.assertRaisesRegex(ValueError,"MISSING_FROZEN_ROW"):inputs.assemble(self.f,self.rows)
    def test_duplicate_ID_rejected(self):
        self.f["Train"]["sample_ids"][1]=self.f["Train"]["sample_ids"][0]
        with self.assertRaisesRegex(ValueError,"ID_COUNT"):inputs.assemble(self.f,self.rows)
    def test_source_metadata_changed(self):
        self.f["Train"]["members"][0]["source_id"]="different"
        with self.assertRaises(ValueError):inputs.assemble(self.f,self.rows)
    def test_label_sign_mapping_exact(self):
        self.assertEqual([c.old.class_of(x) for x in ("-0.00000000000000000001","-0","0","0.00000000000000000001")],[0,1,1,2])
    def test_nonfinite_label_safe(self):
        for v in ("NaN","Infinity"):
            with self.assertRaises(ValueError):c.old.class_of(v)
    def endpoint(self,actual):
        old=self.f["Train"]["sample_ids"][-1];row=raw(140)
        row.update(event_time_ms=str(15000-actual),current_event_time_ms=str(15000-actual),target_event_time_ms="15000",
          actual_horizon_ms=str(actual),match_error_ms=str(actual-1000),future_return_bps="100",future_mid_price="101")
        row["sample_id"]=sample_id(row);rec=member(row,95)
        self.f["Train"]["sample_ids"][-1]=row["sample_id"];self.f["Train"]["members"][-1]=rec;self.rows[row["sample_id"]]=row
    def test_actual_endpoint_equal_boundary_purged(self):
        self.endpoint(1000)
        with self.assertRaisesRegex(ValueError,"ACTUAL_ENDPOINT_LEAKAGE"):inputs.assemble(self.f,self.rows)
    def test_1001_endpoint_not_nominal(self):
        self.endpoint(1001)
        with self.assertRaisesRegex(ValueError,"ACTUAL_ENDPOINT_LEAKAGE"):inputs.assemble(self.f,self.rows)
    def test_market_group_overlap_rejected(self):
        self.f["Validation"]["members"][0]["leakage_group"]=self.f["Train"]["members"][0]["leakage_group"]
        with self.assertRaisesRegex(ValueError,"MARKET_GROUP_OVERLAP"):inputs.assemble(self.f,self.rows)
    def test_class_support_change_rejected(self):
        self.rows[self.f["Train"]["sample_ids"][0]]["future_return_bps"]="0"
        with self.assertRaisesRegex(ValueError,"FROZEN_CLASS_SUPPORT"):inputs.assemble(self.f,self.rows)
class PreprocessingTests(unittest.TestCase):
    def setUp(self):self.x=np.asarray([[0.,10.,5.,2.],[2.,20.,5.,6.]])
    def test_population_mean_std(self):
        q=p.fit(self.x);self.assertEqual(q["mean"],[1.,15.,5.,4.]);self.assertEqual(q["population_std"],[1.,5.,0.,2.])
    def test_Train_extrema_map_to_endpoints(self):
        q=p.fit(self.x);theta,_=p.transform(self.x,q)
        np.testing.assert_allclose(theta,[[0,0,np.pi/2,0],[np.pi,np.pi,np.pi/2,np.pi]],rtol=0,atol=1e-14)
    def test_Validation_only_transform_and_clipping(self):
        q=p.fit(self.x);theta,d=p.transform([[4.,15.,999.,0.]],q)
        np.testing.assert_allclose(theta,[[np.pi,np.pi/2,np.pi/2,0]],atol=1e-14)
        self.assertEqual(d["clipped_above"],[1,0,0,0]);self.assertEqual(d["clipped_below"],[0,0,0,1])
        self.assertEqual(d["constant_feature_Validation_deviations"],[0,0,1,0])
    def test_Validation_cannot_change_Train_statistics(self):
        q,tr,_,_,_=p.apply(self.x,np.ones((3,4)));q2,tr2,_,_,_=p.apply(self.x,np.full((8,4),1e9))
        self.assertEqual(q,q2);np.testing.assert_array_equal(tr,tr2)
    def test_constant_all_features(self):
        theta,_=p.transform(np.zeros((3,4)),p.fit(np.zeros((2,4))))
        np.testing.assert_array_equal(theta,np.full((3,4),np.pi/2))
    def test_nonfinite_features_rejected(self):
        for val in (np.nan,np.inf,-np.inf):
            q=self.x.copy();q[0,0]=val
            with self.assertRaises(ValueError):p.fit(q)
    def test_nonfinite_Validation_rejected(self):
        q=p.fit(self.x)
        with self.assertRaises(ValueError):p.transform([[np.nan,0,0,0]],q)
    def test_wrong_feature_dimension(self):
        with self.assertRaises(ValueError):p.fit(np.ones((2,3)))
    def test_missing_parameters_safe(self):
        q=p.fit(self.x);del q["mean"]
        with self.assertRaises(ValueError):p.transform(self.x,q)
class KernelSolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.x,cls.y,cls.v=kernel_data();cls.kernel,cls.circuit=n.fidelity()
        cls.tt,_=n.quantum(cls.kernel,cls.x);cls.vt,_=n.quantum(cls.kernel,cls.v,cls.x)
    def test_exact_quantum_matrices(self):self.assertEqual(n.validate(self.tt,self.vt,9,6)["status"],"PASS")
    def test_circuit_manifest(self):
        self.assertEqual((self.circuit["qubits"],self.circuit["parameters"],self.circuit["reps"],self.circuit["entanglement"]),(4,4,1,"linear"))
        self.assertTrue(self.circuit["instructions"])
    def test_statevector_overlap_definition(self):
        fmap=self.kernel.feature_map
        a0=Statevector.from_instruction(fmap.assign_parameters(self.x[0]));a1=Statevector.from_instruction(fmap.assign_parameters(self.x[1]))
        self.assertAlmostEqual(self.tt[0,1],float(abs(np.vdot(a0.data,a1.data))**2),places=12)
    def test_standard_QSVC_precomputed_equivalence_both_policies(self):
        for policy in (None,"balanced"):
            direct_kernel,_=n.fidelity()
            direct=QSVC(quantum_kernel=direct_kernel,C=100.,class_weight=policy,probability=False,random_state=42).fit(self.x,self.y)
            name="QSVC_None" if policy is None else "QSVC_Balanced"
            pred,_=n.learn(name,self.tt,self.y,self.vt)
            np.testing.assert_array_equal(pred,direct.predict(self.v))
            pre=n.model(name).fit(self.tt,self.y)
            np.testing.assert_allclose(pre.decision_function(self.vt),direct.decision_function(self.v),atol=1e-10,rtol=1e-10)
    def test_RBF_fit_predict(self):
        pred,meta=n.learn("RBF_None",self.x,self.y,self.v)
        self.assertEqual(pred.shape,(6,));self.assertTrue(set(pred)<={0,1,2});self.assertEqual(meta["configuration"]["gamma"],.01)
    def test_RBF_definition(self):
        tt,vt,_=n.rbf_matrices(self.x,self.v)
        self.assertAlmostEqual(vt[2,3],float(np.exp(-.01*np.sum((self.v[2]-self.x[3])**2))),places=14)
        self.assertEqual(n.validate(tt,vt,9,6)["status"],"PASS")
    def test_class_weights_None(self):
        _,m=n.learn("QSVC_None",self.tt,self.y,self.vt)
        self.assertEqual(m["actual_class_weights"],dict.fromkeys(c.NAMES,1.))
    def test_critical_class_weights_and_effective_C(self):
        y=np.asarray([0]*13+[1]*82+[2])
        _,m=n.learn("QSVC_Balanced",np.eye(96),y,np.eye(96)[:6])
        expected=[96/(3*13),96/(3*82),32.]
        np.testing.assert_allclose([m["actual_class_weights"][k] for k in c.NAMES],expected)
        self.assertEqual(m["effective_C_i"]["UP"],3200.)
    def test_majority_uses_Train_not_constant_FLAT(self):
        p,m=n.majority(np.asarray([2,1,2]),6)
        np.testing.assert_array_equal(p,np.full(6,2));self.assertEqual(m["class"],2)
    def test_shape_failure(self):
        with self.assertRaisesRegex(ValueError,"KERNEL_SHAPE"):n.validate(self.tt,self.vt[:,:8],9,6)
    def test_nonfinite_kernel_failure(self):
        q=self.tt.copy();q[0,0]=np.nan
        with self.assertRaisesRegex(ValueError,"KERNEL_NONFINITE"):n.validate(q,self.vt,9,6)
    def test_asymmetric_kernel_failure(self):
        with self.assertRaisesRegex(ValueError,"KERNEL_SYMMETRY"):n.validate(np.asarray([[1.,.2],[.3,1.]]),np.zeros((2,2)),2,2)
    def test_bad_diagonal_failure(self):
        with self.assertRaisesRegex(ValueError,"KERNEL_SYMMETRY_OR_DIAGONAL"):n.validate(np.eye(2)*.9,np.zeros((2,2)),2,2)
    def test_nonPSD_kernel_failure(self):
        q=np.asarray([[1.,1.,1.],[1.,1.,0.],[1.,0.,1.]])
        with self.assertRaisesRegex(ValueError,"KERNEL_NOT_PSD"):n.validate(q,np.zeros((2,3)),3,2)
    def test_solver_determinism(self):
        first,_=n.learn("QSVC_Balanced",self.tt,self.y,self.vt);repeat,_=n.learn("QSVC_Balanced",self.tt,self.y,self.vt)
        np.testing.assert_array_equal(first,repeat)
    def test_unknown_candidate_fails(self):
        with self.assertRaises(ValueError):n.model("other")
class MetricsTests(unittest.TestCase):
    def setUp(self):self.y=np.asarray([0,0,1,1,2,2]);self.p=np.asarray([0,1,1,1,0,2]);self.m=a.metric(self.y,self.p)
    def test_hand_calculated_confusion_and_accuracy(self):
        self.assertEqual(self.m["confusion_matrix"],[[1,1,0],[0,2,0],[1,0,1]])
        self.assertAlmostEqual(self.m["accuracy"],4/6);self.assertAlmostEqual(self.m["macro_f1"],(.5+.8+2/3)/3)
    def test_hand_calculated_recall(self):
        self.assertAlmostEqual(self.m["balanced_accuracy"],2/3)
        self.assertEqual([self.m["per_class"][k]["recall"] for k in c.NAMES],[.5,1.,.5])
    def test_missing_predictions_keep_all_three_classes(self):
        m=a.metric(np.asarray([0,1,2]),np.asarray([1,1,1]))
        self.assertEqual(m["prediction_class_count"],1);self.assertIn("CLASS_COVERAGE_WARNING",m["warnings"]);self.assertAlmostEqual(m["macro_f1"],1/6)
    def test_missing_true_classes_fixed_macro(self):
        m=a.metric(np.asarray([1,1,1]),np.asarray([1,1,1]))
        self.assertAlmostEqual(m["macro_f1"],1/3);self.assertAlmostEqual(m["balanced_accuracy"],1.)
    def test_missing_confusion_matrix_safe(self):
        q=copy.deepcopy(self.m);del q["confusion_matrix"]
        with self.assertRaisesRegex(ValueError,"MISSING_CONFUSION_MATRIX"):validate_metrics(q,self.y,self.p,"fixture")
    def test_invalid_confusion_shape(self):
        q=copy.deepcopy(self.m);q["confusion_matrix"]=[[1,0],[0,1]]
        with self.assertRaisesRegex(ValueError,"INVALID_CONFUSION_SHAPE"):validate_metrics(q,self.y,self.p,"fixture")
    def test_negative_confusion_counts(self):
        q=copy.deepcopy(self.m);q["confusion_matrix"][0][0]=-1
        with self.assertRaisesRegex(ValueError,"INVALID_CONFUSION_COUNTS"):validate_metrics(q,self.y,self.p,"fixture")
    def test_confusion_support_mismatch(self):
        q=copy.deepcopy(self.m);q["confusion_matrix"][0][0]=0
        with self.assertRaisesRegex(ValueError,"CONFUSION_ROW_SUPPORT"):validate_metrics(q,self.y,self.p,"fixture")
    def test_float_labels_rejected(self):
        with self.assertRaises(ValueError):a.metric([.2,1,2],[1,1,2])
    def test_aggregate_std_ddof1(self):
        q=a.summary([1.,2.,3.]);self.assertEqual(q["mean"],2.);self.assertEqual(q["standard_deviation_ddof1"],1.);self.assertEqual(q["worst_fold"],1)
class DeterminismSafetyTests(unittest.TestCase):
    def test_repeat_complete_schema(self):
        s=stage();self.assertEqual(a.repeat_check(s,copy.deepcopy(s))["status"],"PASS")
    def test_prediction_difference_detected(self):
        s=stage();t=copy.deepcopy(s);t["models"]["QSVC_None"]["predictions"][0]=2
        self.assertEqual(a.repeat_check(s,t)["status"],"DETERMINISM_FAIL")
    def test_preprocessing_difference_detected(self):
        s=stage();t=copy.deepcopy(s);t["preprocessing_parameters"]["mean"][0]=3.
        self.assertEqual(a.repeat_check(s,t)["status"],"DETERMINISM_FAIL")
    def test_missing_repeat_confusion_safe(self):
        s=stage();t=copy.deepcopy(s);del t["models"]["QSVC_None"]["metrics"]["confusion_matrix"]
        with self.assertRaisesRegex(ValueError,"MISSING_CONFUSION_MATRIX"):a.repeat_check(s,t)
    def test_output_scope_protected(self):
        with self.assertRaises(ValueError):c.safe(c.TRAIN.parent/"new.json")
    def test_invalid_run_ID(self):
        with self.assertRaises(ValueError):c.runpath("../old")
if __name__=="__main__":unittest.main()
