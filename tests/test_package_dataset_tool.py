import contextlib,tempfile,unittest
from io import StringIO
from unittest.mock import patch
from tools.package_dataset import execute,fileset,main
from data_pipeline.datasets.packager import package_family
from data_pipeline.datasets.validator import validate_dataset
from tests.fixtures.phase2f.helpers import fixture,RUN
class PackageDatasetToolTests(unittest.TestCase):
    def test_preflight_failure_creates_nothing(self):
        with patch("tools.package_dataset.preflight",side_effect=ValueError("INPUT_HASH_MISMATCH")):
            with patch("pathlib.Path.mkdir") as mkdir:
                with self.assertRaises(ValueError):execute(RUN)
                mkdir.assert_not_called()
    def test_existing_output_stops(self):
        with fixture() as (base,ctx):
            target=base/"artifacts/datasets"/("btcusdt_aggregate_v1_"+RUN);target.mkdir(parents=True)
            with patch("tools.package_dataset.ROOT",base),patch("tools.package_dataset.preflight",return_value={}):
                with self.assertRaises(FileExistsError):execute(RUN)
    def test_full_repeat_both_families(self):
        with fixture() as (base,ctx):
            for line in ("aggregate","depth"):
                a,b=base/(line+"_first"),base/(line+"_second")
                with contextlib.redirect_stdout(StringIO()):
                    x=package_family(ctx,line,RUN,a,"fixture");y=package_family(ctx,line,RUN,b,"fixture")
                    va=validate_dataset(a,ctx,line);vb=validate_dataset(b,ctx,line)
                self.assertEqual(va["status"],"PASS");self.assertEqual(vb["status"],"PASS")
                self.assertEqual(x["row_counts"],y["row_counts"]);self.assertEqual(fileset(a),fileset(b))
                self.assertEqual(x["dataset_tree_hash"],y["dataset_tree_hash"])
    def test_help_does_not_package(self):
        with contextlib.redirect_stdout(StringIO()),self.assertRaises(SystemExit) as result:main(["--help"])
        self.assertEqual(result.exception.code,0)
