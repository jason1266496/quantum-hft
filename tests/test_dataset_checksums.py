import json,tempfile,unittest
from pathlib import Path
from data_pipeline.datasets.checksums import write_json,seal_dataset,verify_checksums,tree_hash,safe_output
from tests.fixtures.phase2f.helpers import FIXTURES
class DatasetChecksumTests(unittest.TestCase):
    def setUp(self):
        cm=tempfile.TemporaryDirectory(dir=FIXTURES);self.base=Path(cm.__enter__());self.addCleanup(cm.__exit__,None,None,None)
    def make(self,name):
        root=self.base/name;root.mkdir();(root/"README.md").write_text("synthetic\n")
        write_json(root/"extra.json",{"a":1});seal_dataset(root,{"dataset_id":"fixture","dataset_tree_hash":None})
        return root
    def test_checksum_ok(self):self.assertEqual(verify_checksums(self.make("one"))["status"],"PASS")
    def test_checksum_tamper_fail(self):
        root=self.make("one");(root/"README.md").write_text("changed")
        with self.assertRaises(ValueError):verify_checksums(root)
    def test_missing_file_fail(self):
        root=self.make("one");(root/"extra.json").unlink()
        with self.assertRaises(ValueError):verify_checksums(root)
    def test_unlisted_file_fail(self):
        root=self.make("one");(root/"other.txt").write_text("new")
        with self.assertRaises(ValueError):verify_checksums(root)
    def test_self_excluded(self):
        root=self.make("one")
        self.assertNotIn("  checksums.sha256",(root/"checksums.sha256").read_text())
    def test_paths_sorted(self):
        root=self.make("one");lines=(root/"checksums.sha256").read_text().splitlines()
        self.assertEqual([x.split("  ",1)[1] for x in lines],sorted(x.split("  ",1)[1] for x in lines))
    def test_tree_hash_normalization(self):
        root=self.make("one")
        self.assertEqual(tree_hash(root),json.loads((root/"dataset_manifest.json").read_text())["dataset_tree_hash"])
    def test_deterministic_manifest_and_checksum(self):
        a,b=self.make("one"),self.make("two")
        self.assertEqual((a/"dataset_manifest.json").read_bytes(),(b/"dataset_manifest.json").read_bytes())
        self.assertEqual((a/"checksums.sha256").read_bytes(),(b/"checksums.sha256").read_bytes())
    def test_no_existing_output_overwrite(self):
        p=self.base/"one.json";write_json(p,{})
        with self.assertRaises(FileExistsError):write_json(p,{"change":True})
    def test_hft_write_rejected(self):
        for p in ("/home/jason/hft-realtime/new","/home/jason/hft-realtime-codex/results/new"):
            with self.assertRaises(ValueError):safe_output(p)
