"""Normal, missing, malformed contracts; no model training or quantum calls."""
import copy,unittest
from experiments.phase4a4_recovery.schema import validate_stage
from experiments.phase4a4_recovery.analysis import compare_repeats
from tests.fixtures.phase4a4_recovery.helpers import stage_fixture,TRUE_LABELS
class SchemaRegressionTests(unittest.TestCase):
    def bad(self,modify,regex):
        d=stage_fixture();modify(d)
        with self.assertRaisesRegex(ValueError,regex):validate_stage(d,TRUE_LABELS)
    def test_normal_fixture_matrix_ground_truth(self):
        d=stage_fixture();v=validate_stage(d,TRUE_LABELS);self.assertEqual(v["true_support"],[1,2,1]);self.assertEqual(v["class_order"],["DOWN","FLAT","UP"])
    def test_normal_identical_repeat_PASS(self):
        d=stage_fixture();self.assertEqual(compare_repeats(d,copy.deepcopy(d),true_labels=TRUE_LABELS)["status"],"PASS")
    def test_changed_prediction_SHA_returns_FAIL_not_KeyError(self):
        d=stage_fixture();e=copy.deepcopy(d);e["models"]["qsvc"]["prediction_sha256"]="0"*64
        self.assertEqual(compare_repeats(d,e,true_labels=TRUE_LABELS)["status"],"FAIL")
    def test_missing_confusion_matrix(self):self.bad(lambda d:d["models"]["qsvc"]["metrics"].pop("confusion_matrix"),"MISSING_CONFUSION_MATRIX")
    def test_missing_class_order(self):self.bad(lambda d:d["models"]["rbf"]["metrics"].pop("class_order"),"MISSING_CLASS_ORDER")
    def test_invalid_class_order(self):self.bad(lambda d:d["models"]["rbf"]["metrics"].update(class_order=["UP","FLAT","DOWN"]),"INVALID_CLASS_ORDER")
    def test_invalid_shape(self):self.bad(lambda d:d["models"]["rbf"]["metrics"].update(confusion_matrix=[[1,0],[0,1]]),"INVALID_CONFUSION_SHAPE")
    def test_ragged_matrix(self):self.bad(lambda d:d["models"]["rbf"]["metrics"].update(confusion_matrix=[[1,0,0],[0,2],[0,1,0]]),"INVALID_CONFUSION_SHAPE")
    def test_negative_count(self):self.bad(lambda d:d["models"]["rbf"]["metrics"].update(confusion_matrix=[[-1,0,0],[0,2,0],[0,1,0]]),"INVALID_CONFUSION_COUNTS")
    def test_float_count(self):self.bad(lambda d:d["models"]["rbf"]["metrics"].update(confusion_matrix=[[1.0,0,0],[0,2,0],[0,1,0]]),"INVALID_CONFUSION_COUNTS")
    def test_boolean_count(self):self.bad(lambda d:d["models"]["rbf"]["metrics"].update(confusion_matrix=[[True,0,0],[0,2,0],[0,1,0]]),"INVALID_CONFUSION_COUNTS")
    def test_huge_count(self):self.bad(lambda d:d["models"]["rbf"]["metrics"].update(confusion_matrix=[[10**80,0,0],[0,2,0],[0,1,0]]),"INVALID_CONFUSION_COUNTS")
    def test_rows_must_match_true_labels(self):self.bad(lambda d:d["models"]["rbf"]["metrics"].update(confusion_matrix=[[1,0,0],[0,1,0],[0,1,1]]),"CONFUSION_ROW_SUPPORT_MISMATCH")
    def test_columns_must_match_predictions(self):self.bad(lambda d:d["models"]["rbf"]["metrics"].update(confusion_matrix=[[0,1,0],[0,2,0],[0,1,0]]),"CONFUSION_PREDICTION_MISMATCH")
    def test_invalid_row_count(self):self.bad(lambda d:d["models"]["rbf"]["metrics"].update(row_count=3),"INVALID_ROW_COUNT")
    def test_invalid_per_class_support(self):self.bad(lambda d:d["models"]["rbf"]["metrics"]["per_class"]["DOWN"].update(support=2),"PER_CLASS_SUPPORT_MISMATCH")
    def test_missing_model(self):self.bad(lambda d:d["models"].pop("qsvc"),"MISSING_QSVC")
    def test_invalid_prediction_class(self):self.bad(lambda d:d["models"]["rbf"].update(predictions=[0,1,3,1]),"INVALID_STAGE_PREDICTIONS")
    def test_missing_external_true_labels(self):
        with self.assertRaisesRegex(ValueError,"MISSING_TRUE_LABELS"):compare_repeats(stage_fixture(),stage_fixture())
    def test_true_label_SHA_mismatch(self):self.bad(lambda d:d["inputs"]["Validation"].update(labels_sha256="0"*64),"TRUE_LABEL_SHA_MISMATCH")
    def test_valid_other_predictions_gives_comparison_FAIL(self):
        self.assertEqual(compare_repeats(stage_fixture(),stage_fixture([1,1,1,1]),true_labels=TRUE_LABELS)["status"],"FAIL")
    def test_QSVC_is_official_precomputed_class(self):
        from qiskit_machine_learning.algorithms import QSVC
        from experiments.phase4a4_recovery.runner import model
        from tests.fixtures.phase4a4.helpers import reference
        m=model("qsvc",reference("qsvc"));self.assertIs(type(m),QSVC);self.assertEqual(m.kernel,"precomputed");self.assertEqual(m.quantum_kernel,"precomputed")
if __name__=="__main__":unittest.main()
