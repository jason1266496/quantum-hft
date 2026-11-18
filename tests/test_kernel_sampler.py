import copy,unittest
from experiments.kernel_comparison.sampler import sample_train,sample_temporal,temporal_positions,subset
from experiments.kernel_comparison.freeze import protocol
from tests.fixtures.phase3b.helpers import rows
class SamplerTests(unittest.TestCase):
    def test_primary_1000_per_class(self):
        r=rows((1002,1003,1004));i,d=sample_train(r,1000)
        self.assertEqual([sum(r[j]["class_label"]==c for j in i) for c in (0,1,2)],[1000]*3)
    def test_primary_short_class_not_topped_up(self):
        r=rows((4,1003,7));i,d=sample_train(r,1000);self.assertEqual(len(i),1011)
    def test_secondary_balanced_min(self):
        r=rows((4,8,6),h=100);i,d=sample_train(r,100);self.assertEqual(len(i),12);self.assertEqual(d["per_class_cap"],4)
    def test_small_minority_warning(self):self.assertIn("SMALL_MINORITY_CLASS_WARNING",sample_train(rows((2,3,4)),100)[1]["warnings"])
    def test_missing_class_rejected(self):
        with self.assertRaisesRegex(ValueError,"CLASS_MISSING"):sample_train(rows((0,4,4)),1000)
    def test_no_duplicate_or_synthetic(self):
        r=rows();i,d=sample_train(r,1000);self.assertEqual(len(i),len(set(i)));self.assertEqual(subset(r,i),r);self.assertFalse(d["synthetic_rows"])
    def test_train_only(self):
        for split in ("Validation","Test","Final Holdout"):
            with self.assertRaises(ValueError):sample_train(rows(),1000,split=split)
    def test_train_deterministic(self):self.assertEqual(sample_train(rows(),1000),sample_train(rows(),1000))
    def test_class_endpoints_preserved(self):
        r=rows((1005,1005,1005));i,_=sample_train(r,1000)
        for c in (0,1,2):
            group=[j for j,v in enumerate(r) if v["class_label"]==c];self.assertIn(group[0],i);self.assertIn(group[-1],i)
    def test_val_not_balanced(self):
        r=rows((1,20,1),split="Validation");i=sample_temporal(r,split="Validation");self.assertEqual(subset(r,i),r)
    def test_test_not_balanced(self):
        r=rows((1,20,1),split="Test");i=sample_temporal(r,split="Test");self.assertEqual(subset(r,i),r)
    def test_val_labels_ignored(self):
        r=rows((10,30,20));a=sample_temporal(r,split="Validation",cap=10)
        for v in r:v["future_return_bps"]="DO_NOT_READ_LABEL";v["class_label"]="POISON"
        self.assertEqual(a,sample_temporal(r,split="Validation",cap=10))
    def test_test_labels_ignored(self):
        r=rows();a=sample_temporal(r,split="Test",cap=10)
        for v in r:v["future_return_bps"]=None
        self.assertEqual(a,sample_temporal(r,split="Test",cap=10))
    def test_holdout_sampling_rejected(self):
        with self.assertRaises(ValueError):sample_temporal(rows(),split="Final Holdout")
    def test_limits_and_endpoints(self):
        p=temporal_positions(49116,1000);self.assertEqual((len(p),p[0],p[-1]),(1000,0,49115));self.assertEqual(len(set(p)),1000)
    def test_tiny_temporal_all(self):self.assertEqual(temporal_positions(3,1000),[0,1,2])
    def test_time_sort_no_shuffle(self):
        r=rows()[::-1];p=sample_temporal(r,split="Validation",cap=5)
        self.assertEqual([int(r[i]["event_time_ms"]) for i in p],sorted(int(r[i]["event_time_ms"]) for i in p))
    def test_test_does_not_affect_train_sampling(self):
        train=rows();a=sample_train(train,1000);test=rows((1,99,1),split="Test");test.clear();self.assertEqual(a,sample_train(train,1000))
    def test_protocol_exact_features_and_labels(self):
        p=protocol();self.assertEqual(len(p["feature_order"]),4);self.assertEqual(p["label_policy"],"direction_3class_exact_v1")
    def test_invalid_horizon(self):
        for h in (200,500):
            with self.assertRaises(ValueError):sample_train(rows(),h)
