import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tools.build_splits import build_once,deterministic_files,execute,fingerprint
from tests.fixtures.phase2e.helpers import FIXTURES,sources

class BuildSplitsToolTests(unittest.TestCase):
    def test_hash_mismatch_stops_before_run(self):
        with patch("tools.build_splits.preflight",side_effect=ValueError("INPUT_HASH_MISMATCH")):
            with patch("pathlib.Path.mkdir") as mkdir:
                with self.assertRaises(ValueError):execute("20990101T000000Z")
                mkdir.assert_not_called()
    def test_existing_run_rejected(self):
        with tempfile.TemporaryDirectory(dir=FIXTURES) as temp:
            base=Path(temp);run=base/"artifacts/phase2e/20990101T000000Z"
            run.mkdir(parents=True)
            with patch("tools.build_splits.ROOT",base),patch("tools.build_splits.preflight",return_value={}),patch("tools.build_splits.safe_output",side_effect=lambda p:p):
                with self.assertRaises(FileExistsError):execute("20990101T000000Z")
    def test_full_determinism_and_holdout_lock(self):
        data=sources()+sources("depth_top5_v1")
        with tempfile.TemporaryDirectory(dir=FIXTURES) as temp:
            a,b=Path(temp)/"first",Path(temp)/"second";a.mkdir();b.mkdir()
            with patch("tools.build_splits.load_sources",return_value=data):
                first=build_once(a);second=build_once(b)
            self.assertEqual(deterministic_files(a),deterministic_files(b))
            for value in first["holdout"].values():
                self.assertEqual(value["holdout_status"],"LOCKED")
                self.assertIn("scaler fitting",value["prohibited_uses"])
                self.assertFalse(any(s["source_id"]=="replay_events_1000" for s in value["sources"]))
    def test_input_fingerprint_is_read_only(self):
        with tempfile.TemporaryDirectory(dir=FIXTURES) as temp:
            p=Path(temp)/"artificial_input.txt";p.write_text("fixture")
            before=(p.read_bytes(),p.stat().st_mtime_ns)
            a=fingerprint(p);b=fingerprint(p)
            self.assertEqual(a,b)
            self.assertEqual(before,(p.read_bytes(),p.stat().st_mtime_ns))
