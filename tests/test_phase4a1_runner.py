import copy,unittest
import numpy as np
from qiskit_machine_learning.algorithms import QSVC
from qiskit_machine_learning.kernels import FidelityStatevectorKernel
from experiments.phase4a1.kernel import circuit
from experiments.phase4a1.runner import config,models,stage,compare
from tests.fixtures.phase4a1.helpers import fresh,budget
class RunnerTests(unittest.TestCase):
    def test_fixed_models_support_all_required_params(self):
        r,q=models()
        for m in (r,q):
            p=m.get_params(deep=False);self.assertEqual(p["C"],100);self.assertEqual(p["class_weight"],"balanced");self.assertFalse(p["probability"])
        self.assertEqual(r.gamma,.01);self.assertEqual(q.quantum_kernel,"precomputed")
    def test_precomputed_matches_direct_artificial_qsvc(self):
        rng=np.random.default_rng(42);x=rng.uniform(.1,3,(6,4));v=rng.uniform(.1,3,(3,4));y=np.repeat([0,1,2],2);f,_=circuit()
        k=FidelityStatevectorKernel(feature_map=f,enforce_psd=False,shots=None)
        pre=models()[1];direct=QSVC(quantum_kernel=k,C=100.,class_weight="balanced",probability=False,random_state=42)
        pre.fit(k.evaluate(x),y);a=pre.predict(k.evaluate(v,x));direct.fit(x,y);np.testing.assert_array_equal(a,direct.predict(v))
    def test_smoke_no_effectiveness_metrics(self):
        r,m=budget();s,_=stage(r,m,"smoke",fresh()/"smoke")
        self.assertIsNone(s["models"]["qsvc"]["metrics"]);self.assertIsNone(s["models"]["rbf"]["metrics"])
    def test_prototype_repeat_and_difference_guards(self):
        r,m=budget();a,aa=stage(r,m,"prototype",fresh()/"first");b,bb=stage(r,m,"prototype",fresh()/"repeat")
        self.assertEqual(compare(a,aa,b,bb)["status"],"PASS")
        changed=copy.deepcopy(b);changed["models"]["qsvc"]["predictions"][0]=(changed["models"]["qsvc"]["predictions"][0]+1)%3
        self.assertEqual(compare(a,aa,changed,bb)["status"],"FAIL")
        bad={**bb,"train_kernel":bb["train_kernel"]+.001};self.assertEqual(compare(a,aa,b,bad)["status"],"FAIL")
    def test_kernel_float_tolerance(self):
        r,m=budget();a,aa=stage(r,m,"prototype",fresh()/"first");b=copy.deepcopy(a);bb={k:v+1e-12 for k,v in aa.items()}
        self.assertEqual(compare(a,aa,b,bb)["status"],"PASS")
    def test_no_test_no_parameter_search(self):
        c=config();self.assertFalse(c["test_allowed"]);self.assertFalse(c["holdout_allowed"]);self.assertFalse(c["retuning_or_resampling"]);self.assertFalse(c["enforce_psd"])
