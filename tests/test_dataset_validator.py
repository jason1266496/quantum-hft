import contextlib,json,tempfile,unittest
from io import StringIO
from pathlib import Path
from data_pipeline.datasets.packager import package_family
from data_pipeline.datasets.validator import validate_dataset,scan_files
from data_pipeline.datasets.schema import columns
from tests.fixtures.phase2f.helpers import fixture,RUN,FIXTURES,FEATURE_FIELDS,LABEL_FIELDS
class DatasetValidatorTests(unittest.TestCase):
    def setUp(self):
        cm=fixture();self.base,self.ctx=cm.__enter__();self.addCleanup(cm.__exit__,None,None,None)
        self.root=self.base/"dataset"
        with contextlib.redirect_stdout(StringIO()):package_family(self.ctx,"aggregate",RUN,self.root,"fixture")
    def validate(self):
        with contextlib.redirect_stdout(StringIO()):return validate_dataset(self.root,self.ctx,"aggregate")
    def test_valid(self):self.assertEqual(self.validate()["status"],"PASS")
    def test_feature_source_change_detected(self):
        p=self.ctx["feature_root"]/"sources/artificial_aggregate/aggregate_core_v1.csv"
        with p.open("a") as f:f.write("tamper\n")
        self.assertEqual(self.validate()["status"],"DATASET_VALIDATION_FAIL")
    def test_label_source_change_detected(self):
        p=self.ctx["label_root"]/"sources/artificial_aggregate/aggregate_core_v1/labels_100ms.csv"
        with p.open("a") as f:f.write("tamper\n")
        self.assertEqual(self.validate()["status"],"DATASET_VALIDATION_FAIL")
    def test_split_membership_change_detected(self):
        p=self.ctx["split_root"]/"aggregate/train_indices.csv"
        with p.open("a") as f:f.write("tamper\n")
        self.assertEqual(self.validate()["status"],"DATASET_VALIDATION_FAIL")
    def test_packaged_file_tamper(self):
        with (self.root/"100ms/train.csv").open("a") as f:f.write("tamper\n")
        self.assertEqual(self.validate()["status"],"DATASET_VALIDATION_FAIL")
    def test_raw_hft_csv_forbidden(self):
        (self.root/"obi_market_data.csv").write_text("raw")
        self.assertEqual(self.validate()["status"],"DATASET_VALIDATION_FAIL")
    def test_replay_jsonl_forbidden(self):
        (self.root/"replay.jsonl").write_text("{}")
        self.assertEqual(self.validate()["status"],"DATASET_VALIDATION_FAIL")
    def test_env_forbidden(self):
        (self.root/".env").write_text("fixture")
        self.assertEqual(self.validate()["status"],"DATASET_VALIDATION_FAIL")
    def test_elf_forbidden(self):
        (self.root/"README.md").write_bytes(b"\x7fELFfake")
        self.assertEqual(self.validate()["status"],"DATASET_VALIDATION_FAIL")
    def test_api_key_pattern_forbidden(self):
        (self.root/"README.md").write_text("API_KEY=FAKE_SYNTHETIC_0123456789")
        self.assertEqual(self.validate()["status"],"DATASET_VALIDATION_FAIL")
    def test_class_label_column_forbidden(self):
        for name in ("UP","DOWN","FLAT","class_label","binary_target"):
            with self.subTest(name=name),self.assertRaises(ValueError):
                columns({"field_order":[*FEATURE_FIELDS,name]},{"field_order":list(LABEL_FIELDS)})
    def test_model_score_column_forbidden(self):
        with self.assertRaises(ValueError):columns({"field_order":[*FEATURE_FIELDS,"model_score"]},{"field_order":list(LABEL_FIELDS)})
    def test_scaler_parameters_file_forbidden(self):
        (self.root/"scaler_parameters.json").write_text("{}")
        self.assertEqual(self.validate()["status"],"DATASET_VALIDATION_FAIL")
    def test_no_duplicate_ids_or_overlap(self):
        v=self.validate();self.assertEqual((v["duplicate_sample_ids"],v["sample_id_collision_count"],v["split_overlap"]),(0,0,0))
