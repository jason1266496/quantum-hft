import csv
import tempfile
import unittest
from pathlib import Path
from data_pipeline.labels.writer import LabelWriter,sha256_file
from data_pipeline.labels.builder import _label
from tests.fixtures.phase2d.helpers import rows,FIXTURE_DIR

class LabelWriterTests(unittest.TestCase):
    def fixture_label(self):
        data=rows((0,100),("100","101"))
        return _label(data,[0,100],0,100,2,False,set())
    def test_exclusive_output(self):
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as temp:
            path=Path(temp)/"labels.csv"
            with LabelWriter(path) as writer:writer.write(self.fixture_label())
            with self.assertRaises(FileExistsError):LabelWriter(path)
    def test_canonical_sha_stable(self):
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as temp:
            a,b=Path(temp)/"a.csv",Path(temp)/"b.csv"
            for path in (a,b):
                with LabelWriter(path) as writer:writer.write(self.fixture_label())
            self.assertEqual(sha256_file(a),sha256_file(b))
    def test_row_order_and_no_extra_columns(self):
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as temp:
            path=Path(temp)/"labels.csv"
            data=rows((0,100,200),("100","101","102"))
            with LabelWriter(path) as writer:
                for i in (0,1):
                    writer.write(_label(data,[0,100,200],i,100,3,False,set()))
            with path.open(newline="",encoding="utf-8") as f:
                reader=csv.DictReader(f);items=list(reader)
                self.assertEqual([r["record_index"] for r in items],["1","2"])
                self.assertNotIn("local_timestamp_us",reader.fieldnames)
                self.assertNotIn("UP",reader.fieldnames)
