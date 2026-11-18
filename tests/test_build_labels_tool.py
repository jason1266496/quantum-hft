import contextlib
import csv
from io import StringIO
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from data_pipeline.labels.builder import build_view
from data_pipeline.labels.writer import LabelWriter,sha256_file,write_json
from data_pipeline.labels.schema import HORIZONS_MS
from tests.fixtures.phase2d.helpers import rows,FIXTURE_DIR
from tools.build_labels import compare_cross_view,compare_repeat,VIEWS

class BuildLabelsToolTests(unittest.TestCase):
    def test_source_view_contract(self):
        self.assertEqual(len(VIEWS),7)
        self.assertEqual(sum(len(x) for x in VIEWS.values()),9)
        self.assertTrue(all(len(VIEWS[s])==1 for s in tuple(VIEWS)[:5]))
    def test_progress_frequency_does_not_change_output(self):
        synthetic=rows((0,100,200,500,1000),("100","101","101","99","100"))
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as temp:
            base=Path(temp)
            with patch("data_pipeline.labels.builder.read_feature_rows",return_value=synthetic):
                with contextlib.redirect_stdout(StringIO()):
                    build_view(base,"synthetic","aggregate_core_v1",base/"first",progress_every=1)
                    build_view(base,"synthetic","aggregate_core_v1",base/"second",progress_every=1000)
            for h in HORIZONS_MS:
                self.assertEqual(sha256_file(base/"first"/f"labels_{h}ms.csv"),
                                 sha256_file(base/"second"/f"labels_{h}ms.csv"))
            self.assertEqual(compare_repeat(base/"first",base/"second")["status"],"PASS")
    def test_cross_view_mismatch_detected(self):
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as temp:
            left,right=Path(temp)/"left",Path(temp)/"right"
            left.mkdir();right.mkdir()
            for h in HORIZONS_MS:
                a=rows((0,h),("100","101"),view="aggregate_core_v1")
                b=rows((0,h),("100","102"),view="depth_top5_v1")
                with LabelWriter(left/f"labels_{h}ms.csv") as writer:
                    writer.write(__import__("data_pipeline.labels.builder",fromlist=["_label"])._label(a,[0,h],0,h,2,False,set()))
                with LabelWriter(right/f"labels_{h}ms.csv") as writer:
                    writer.write(__import__("data_pipeline.labels.builder",fromlist=["_label"])._label(b,[0,h],0,h,2,False,set()))
            self.assertEqual(compare_cross_view(left,right,"synthetic")["status"],"CROSS_VIEW_LABEL_MISMATCH")
    def test_no_existing_json_overwrite(self):
        with tempfile.TemporaryDirectory(dir=FIXTURE_DIR) as temp:
            p=Path(temp)/"out.json"
            write_json(p,{"a":1})
            with self.assertRaises(FileExistsError):write_json(p,{"a":2})
