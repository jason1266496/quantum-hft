import copy,unittest
from experiments.quantum_preparation.sampler import build_budgets,positions,train_indices,validation_indices,distribution,validate_rows
from tests.fixtures.phase4a0.helpers import rows
class SamplingTests(unittest.TestCase):
    def budgets(self):return build_budgets(rows(),rows((10,270,20),"Validation"))
    def test_prototype_train_32_each(self):self.assertEqual(self.budgets()["prototype"]["Train"].__len__(),96);self.assertEqual(set(distribution(self.budgets()["prototype"]["Train"])["counts"].values()),{32})
    def test_smoke_train_8_each(self):self.assertEqual(set(distribution(self.budgets()["smoke"]["Train"])["counts"].values()),{8})
    def test_validation_exact_sizes(self):
        b=self.budgets();self.assertEqual(len(b["prototype"]["Validation"]),96);self.assertEqual(len(b["smoke"]["Validation"]),24)
    def test_train_sampling_scope(self):
        for split in ("Test","Validation","Final Holdout"):
            with self.assertRaises(ValueError):train_indices(rows(),32,split=split)
    def test_validation_sampling_scope(self):
        for split in ("Test","Train","Final Holdout"):
            with self.assertRaises(ValueError):validation_indices(rows(),96,split=split)
    def test_validation_no_label_use(self):
        r=rows();before=validation_indices(r,96)
        for v in r:v["future_return_bps"]="POISON";v["class_label"]="POISON"
        self.assertEqual(before,validation_indices(r,96))
    def test_build_validation_membership_independent_of_labels(self):
        t=rows();v=rows(split="Validation");a=build_budgets(t,v)
        for r in v:
            c=(int(r["class_label"])+1)%3;r["class_label"]=c;r["future_return_bps"]=("-1","0","1")[c]
        b=build_budgets(t,v)
        self.assertEqual([r["sample_id"] for r in a["prototype"]["Validation"]],[r["sample_id"] for r in b["prototype"]["Validation"]])
    def test_deterministic(self):self.assertEqual(self.budgets(),self.budgets())
    def test_no_duplicate(self):
        for b in self.budgets().values():
            for split in ("Train","Validation"):
                ids=[r["sample_id"] for r in b[split]];self.assertEqual(len(ids),len(set(ids)))
    def test_train_validation_disjoint(self):
        b=self.budgets();train={r["sample_id"] for x in b.values() for r in x["Train"]};val={r["sample_id"] for x in b.values() for r in x["Validation"]};self.assertFalse(train&val)
    def test_smoke_nested(self):
        b=self.budgets()
        for split in ("Train","Validation"):self.assertTrue({r["sample_id"] for r in b["smoke"][split]}<={r["sample_id"] for r in b["prototype"][split]})
    def test_no_synthetic_or_changed_values(self):
        t=rows();v=rows(split="Validation");source={r["sample_id"]:r for r in t+v}
        for b in build_budgets(t,v).values():
            for split in ("Train","Validation"):
                for r in b[split]:self.assertEqual(r,source[r["sample_id"]])
    def test_temporal_endpoints(self):
        p=positions(1000,96);self.assertEqual((p[0],p[-1]),(0,999));self.assertEqual(len(set(p)),96)
    def test_insufficient_class_stops(self):
        with self.assertRaisesRegex(ValueError,"UNAVAILABLE"):build_budgets(rows((31,100,100)),rows(split="Validation"))
    def test_insufficient_validation_stops(self):
        with self.assertRaisesRegex(ValueError,"UNAVAILABLE"):build_budgets(rows(),rows((30,30,35),"Validation"))
    def test_source_overlap_rejected(self):
        with self.assertRaisesRegex(ValueError,"OVERLAP"):build_budgets(rows(),rows())
    def test_duplicate_source_rejected(self):
        r=rows();r[-1]["sample_id"]=r[0]["sample_id"]
        with self.assertRaisesRegex(ValueError,"DUPLICATE"):build_budgets(r,rows(split="Validation"))
    def test_exact_zero_policy(self):
        r=rows();r[0]["future_return_bps"]="1e-100";r[0]["class_label"]=2;self.assertTrue(validate_rows(r))
        r[0]["class_label"]=1
        with self.assertRaisesRegex(ValueError,"CLASSIFICATION"):validate_rows(r)
