import unittest
from unittest.mock import patch
import numpy as np
from experiments.phase4a1.kernel import circuit,compute,validate
class KernelTests(unittest.TestCase):
    def test_fixed_circuit(self):
        f,m=circuit();self.assertEqual((f.num_qubits,f.num_parameters),(4,4));self.assertEqual(m["depth"],11);self.assertEqual(m["gate_count_total"],17);self.assertIsNone(m["shots"])
    def test_artificial_statevector_matrix(self):
        rng=np.random.default_rng(42);a,b,_,_=compute(rng.uniform(0,3,(6,4)),rng.uniform(0,3,(3,4)))
        self.assertEqual(validate(a,b,6,3)["status"],"PASS")
    def test_train_diagonal_required(self):
        a=np.eye(3);a[0,0]=.5
        with self.assertRaises(ValueError):validate(a,np.zeros((2,3)),3,2)
    def test_asymmetry_rejected(self):
        a=np.eye(3);a[0,1]=.2
        with self.assertRaises(ValueError):validate(a,np.zeros((2,3)),3,2)
    def test_nonfinite_rejected(self):
        a=np.eye(3);a[0,1]=np.nan
        with self.assertRaises(ValueError):validate(a,np.zeros((2,3)),3,2)
    def test_out_of_range_rejected(self):
        a=np.eye(3);a[0,1]=a[1,0]=1.1
        with self.assertRaises(ValueError):validate(a,np.zeros((2,3)),3,2)
    def test_non_psd_never_repaired(self):
        a=np.array([[1.,1.,1.],[1.,1.,0.],[1.,0.,1.]]);before=a.copy()
        with self.assertRaisesRegex(ValueError,"NOT_PSD"):validate(a,np.zeros((2,3)),3,2)
        np.testing.assert_array_equal(a,before)
    def test_cross_kernel_no_diagonal_or_psd_rule(self):
        a=np.eye(3);b=np.array([[.1,.2,.3],[.4,.1,.6],[.9,.4,.1]])
        self.assertEqual(validate(a,b,3,3)["validation_diagonal_symmetry_PSD"],"NOT_APPLICABLE_CROSS_KERNEL")
    def test_complex_rejected(self):
        with self.assertRaises(ValueError):validate(np.eye(3).astype(complex),np.zeros((2,3)),3,2)
    def test_3000_row_kernel_forbidden_before_API(self):
        with patch("experiments.phase4a1.kernel.FidelityStatevectorKernel",side_effect=AssertionError("called")):
            with self.assertRaisesRegex(ValueError,"PROHIBITED"):compute(np.zeros((3000,4)),np.zeros((96,4)))
