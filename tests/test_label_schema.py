import unittest
from decimal import Decimal
from data_pipeline.labels.schema import (HORIZONS_MS,LABEL_FIELDS,decimal_text,
                                          return_bps,schema_document)

class LabelSchemaTests(unittest.TestCase):
    def test_exact_horizons(self):
        self.assertEqual(HORIZONS_MS,(100,200,500,1000))
        self.assertNotIn(250,HORIZONS_MS)
    def test_fixed_fields(self):
        self.assertEqual(len(LABEL_FIELDS),14)
        self.assertIn("future_return_bps",LABEL_FIELDS)
        self.assertNotIn("local_timestamp_us",LABEL_FIELDS)
    def test_no_class_target(self):
        text=" ".join(LABEL_FIELDS).lower()
        for value in ("up","down","flat","target_class","binary_direction"):
            self.assertNotIn(value,text)
        self.assertFalse(schema_document()["class_labels"])
    def test_decimal_precision_and_zero(self):
        self.assertEqual(decimal_text(Decimal("-0.000")),"0")
        self.assertEqual(decimal_text(Decimal("1.23000")),"1.23")
        self.assertEqual(return_bps(Decimal("100"),Decimal("100.01")),Decimal("1.0000"))
    def test_no_float_source(self):
        with self.assertRaises(ValueError):
            return_bps(100.0,Decimal("101"))
        self.assertFalse(schema_document()["decimal_policy"]["float_used"])
