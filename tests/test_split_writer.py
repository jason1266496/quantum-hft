import tempfile,unittest
from pathlib import Path
from data_pipeline.splits.writer import write_csv,write_json,sha_file,safe_output
from data_pipeline.splits.schema import RAW_FIELDS
from tests.fixtures.phase2e.helpers import FIXTURES
class SplitWriterTests(unittest.TestCase):
    def test_existing_output_rejected(self):
        with tempfile.TemporaryDirectory(dir=FIXTURES) as temp:
            p=Path(temp)/"out.json";write_json(p,{"a":1})
            with self.assertRaises(FileExistsError):write_json(p,{"a":2})
    def test_deterministic_hash(self):
        with tempfile.TemporaryDirectory(dir=FIXTURES) as temp:
            a,b=Path(temp)/"a.csv",Path(temp)/"b.csv"
            record=("view","source","session",1,100,"event","Train")
            write_csv(a,RAW_FIELDS,[record]);write_csv(b,RAW_FIELDS,[record])
            self.assertEqual(sha_file(a),sha_file(b))
    def test_hft_write_forbidden(self):
        for path in ("/home/jason/hft-realtime/out.csv","/home/jason/hft-realtime-codex/results/out.csv"):
            with self.assertRaises(ValueError):safe_output(path)
    def test_float_metadata_forbidden(self):
        with tempfile.TemporaryDirectory(dir=FIXTURES) as temp:
            with self.assertRaises(ValueError):
                write_csv(Path(temp)/"bad.csv",("a",),[(1.5,)])
    def test_embargo_zero_allowed(self):
        from data_pipeline.splits.policy import embargo_policy
        self.assertEqual(embargo_policy()["embargo_ms"],0)
        self.assertEqual(embargo_policy()["status"],"NO_ADDITIONAL_EMBARGO_BEYOND_PURGING")
