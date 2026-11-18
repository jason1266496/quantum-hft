import unittest
import numpy as np
from models.classical.scaler import TrainOnlyScaler
from tests.fixtures.phase3a.helpers import xy
class TrainOnlyScalerTests(unittest.TestCase):
    def test_train_fit(self):
        x,y=xy();s=TrainOnlyScaler(100,"full").fit(x,split="Train",sample_ids=list(map(str,range(len(x)))))
        self.assertEqual(s.artifact()["n_samples_seen"],len(x))
    def test_validation_fit_forbidden(self):
        with self.assertRaises(ValueError):TrainOnlyScaler(100,"full").fit(np.zeros((3,4)),split="Validation",sample_ids=["a","b","c"])
    def test_test_fit_forbidden(self):
        with self.assertRaises(ValueError):TrainOnlyScaler(100,"full").fit(np.zeros((3,4)),split="Test",sample_ids=["a","b","c"])
    def test_holdout_fit_forbidden(self):
        with self.assertRaises(ValueError):TrainOnlyScaler(100,"full").fit(np.zeros((3,4)),split="Final Holdout",sample_ids=["a","b","c"])
    def test_transform_does_not_fit(self):
        x,y=xy();s=TrainOnlyScaler(100,"full").fit(x,split="Train",sample_ids=list(map(str,range(len(x)))))
        before=s.artifact();s.transform(x*10,split="Validation");s.transform(x*100,split="Test")
        self.assertEqual(before,s.artifact())
    def test_holdout_transform_forbidden(self):
        x,y=xy();s=TrainOnlyScaler(100,"full").fit(x,split="Train",sample_ids=list(map(str,range(len(x)))))
        with self.assertRaises(ValueError):s.transform(x,split="Final Holdout")
    def test_fit_once(self):
        x,y=xy();s=TrainOnlyScaler(100,"full").fit(x,split="Train",sample_ids=list(map(str,range(len(x)))))
        with self.assertRaises(ValueError):s.fit(x,split="Train",sample_ids=list(map(str,range(len(x)))))
    def test_horizon_universes_separate(self):
        x,y=xy();a=TrainOnlyScaler(100,"full").fit(x,split="Train",sample_ids=list(map(str,range(len(x)))))
        b=TrainOnlyScaler(1000,"full").fit(x[:60],split="Train",sample_ids=list(map(str,range(60))))
        self.assertNotEqual(a.artifact()["n_samples_seen"],b.artifact()["n_samples_seen"])
