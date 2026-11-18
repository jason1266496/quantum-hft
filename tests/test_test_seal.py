import json,unittest
from unittest.mock import patch
from pathlib import Path
from models.classical.selection import TestGate
from experiments.classical.runner import read_split
from tests.fixtures.phase3a.helpers import fixture,fake_selection
class TestSealTests(unittest.TestCase):
    def gate(self,base):
        path=fake_selection(base/"selection.json")
        return TestGate({"100/model":path},base/"barrier.json")
    def test_read_before_seal_forbidden(self):
        with fixture() as base:
            gate=self.gate(base)
            with self.assertRaises(ValueError):gate.authorize_test_read(100)
    def test_dataset_test_guard_before_open(self):
        with patch("pathlib.Path.open") as opening:
            with self.assertRaises(ValueError):read_split(Path("not_opened"),100,"Test")
            opening.assert_not_called()
    def test_freeze_then_read(self):
        with fixture() as base:
            gate=self.gate(base);gate.freeze();gate.authorize_test_read(100)
            self.assertTrue(gate.sealed)
    def test_no_second_label_read(self):
        with fixture() as base:
            gate=self.gate(base);gate.freeze();gate.authorize_test_read(100)
            with self.assertRaises(ValueError):gate.authorize_test_read(100)
    def test_test_evaluated_once(self):
        with fixture() as base:
            gate=self.gate(base);gate.freeze();gate.authorize_test_read(100)
            gate.claim_evaluation("100/model",100)
            with self.assertRaises(ValueError):gate.claim_evaluation("100/model",100)
    def test_no_retune_after_freeze(self):
        with fixture() as base:
            gate=self.gate(base);gate.freeze()
            with self.assertRaises(ValueError):gate.assert_selection_open()
    def test_selection_immutable(self):
        with fixture() as base:
            gate=self.gate(base);gate.freeze()
            path=base/"selection.json";value=json.loads(path.read_text());value["test_evaluated"]=True;path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):gate.authorize_test_read(100)
    def test_holdout_not_read(self):
        with patch("pathlib.Path.open") as opening:
            with self.assertRaises(ValueError):read_split(Path("not_opened"),100,"Final Holdout")
            opening.assert_not_called()
