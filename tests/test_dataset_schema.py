import unittest
from data_pipeline.datasets.schema import dataset_id,sample_id,identity_bytes,columns,FORBIDDEN_COLUMNS
class DatasetSchemaTests(unittest.TestCase):
    def row(self):
        return {"feature_view":"aggregate_core_v1","source_id":"fake","session_id":"a","record_index":"1","event_time_ms":"100"}
    def test_dataset_id(self):self.assertEqual(dataset_id("aggregate_core_v1","20990101T000000Z"),"btcusdt_aggregate_v1_20990101T000000Z")
    def test_bad_dataset_id(self):
        with self.assertRaises(ValueError):dataset_id("aggregate_core_v1","bad")
    def test_sample_id_determinism(self):self.assertEqual(sample_id(self.row()),sample_id(dict(reversed(list(self.row().items())))))
    def test_sample_id_excludes_future(self):
        a=self.row();b={**a,"future_return_bps":"999","target_event_time_ms":"9999","split":"Holdout","requested_horizon_ms":1000}
        self.assertEqual(sample_id(a),sample_id(b))
    def test_cross_view_id_differs(self):
        a=self.row();b={**a,"feature_view":"depth_top5_v1"};self.assertNotEqual(sample_id(a),sample_id(b))
    def test_integer_metadata_canonical(self):
        a=self.row();b={**a,"record_index":1,"event_time_ms":100};self.assertEqual(sample_id(a),sample_id(b))
    def test_no_float_identity(self):
        row=self.row();row["event_time_ms"]=100.0
        with self.assertRaises(ValueError):sample_id(row)
    def test_local_timestamp_forbidden(self):
        from tests.fixtures.phase2f.helpers import FEATURE_FIELDS,LABEL_FIELDS
        fs={"field_order":[*FEATURE_FIELDS,"local_timestamp_us"]};ls={"field_order":list(LABEL_FIELDS)}
        with self.assertRaises(ValueError):columns(fs,ls)
    def test_label_reason_alias(self):
        from tests.fixtures.phase2f.helpers import FEATURE_FIELDS,LABEL_FIELDS
        order,mapping=columns({"field_order":list(FEATURE_FIELDS)},{"field_order":list(LABEL_FIELDS)})
        self.assertIn("invalid_reason",order);self.assertEqual(mapping["invalid_reason"],"label_invalid_reason")
