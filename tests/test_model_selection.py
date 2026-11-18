import unittest
from models.classical.selection import choose
def candidate(c,f1,ba,gamma=None):
    config={"C":c}
    if gamma is not None:config["gamma"]=gamma
    return {"config":config,"validation_metrics":{"macro_f1":f1,"balanced_accuracy":ba}}
class SelectionTests(unittest.TestCase):
    def test_macro_f1_primary(self):
        a,b=candidate(1,.5,.9),candidate(.1,.6,.7)
        self.assertIs(choose([a,b],"logistic"),b)
    def test_balanced_accuracy_tie(self):
        a,b=candidate(.1,.5,.6),candidate(1,.5,.7)
        self.assertIs(choose([a,b],"linear_svm"),b)
    def test_smaller_c_tie(self):
        a,b=candidate(10,.5,.7),candidate(.1,.5,.7)
        self.assertIs(choose([a,b],"logistic"),b)
    def test_rbf_scale_before_smaller_c(self):
        a,b=candidate(1,.5,.7,.1),candidate(10,.5,.7,"scale")
        self.assertIs(choose([a,b],"rbf_svm"),b)
    def test_rbf_smaller_c_after_gamma(self):
        a,b=candidate(10,.5,.7,"scale"),candidate(1,.5,.7,"scale")
        self.assertIs(choose([a,b],"rbf_svm"),b)
    def test_test_not_selection(self):
        with self.assertRaises(ValueError):choose([candidate(1,.5,.7)],"logistic",split="Test")
