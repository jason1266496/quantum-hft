import unittest
from data_pipeline.splits.schema import schema_document,INDEX_FIELDS,HORIZONS,SPLITS
class SplitSchemaTests(unittest.TestCase):
    def test_horizons(self):self.assertEqual(HORIZONS,(100,200,500,1000))
    def test_four_splits(self):self.assertEqual(SPLITS,("Train","Validation","Test","Final Holdout"))
    def test_no_local_timestamp(self):self.assertNotIn("local_timestamp_us",INDEX_FIELDS)
    def test_metadata_only(self):
        self.assertNotIn("future_return_bps",INDEX_FIELDS)
        self.assertNotIn("mid_price",INDEX_FIELDS)
    def test_no_class_or_model(self):
        self.assertFalse(schema_document()["class_labels"]);self.assertFalse(schema_document()["models"])
    def test_no_shuffle(self):self.assertFalse(schema_document()["shuffle"])
