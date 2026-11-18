"""Analytic synthetic books, invalid inputs, and context independence."""

from decimal import Decimal as D, Inexact, ROUND_DOWN, localcontext
import unittest
from data_pipeline.features.formulas import aggregate, depth


def levels():
    return (tuple((D(99-i), D(i+1)) for i in range(5)),
            tuple((D(101+i), D(2*(i+1))) for i in range(5)))


class FeatureFormulaTests(unittest.TestCase):
    def test_mid_price(self):
        self.assertEqual(aggregate(D(99), D(101), D(15), D(30))["mid_price"], D(100))

    def test_spread(self):
        self.assertEqual(aggregate(D(99), D(101), D(15), D(30))["spread"], D(2))

    def test_spread_bps(self):
        self.assertEqual(aggregate(D(99), D(101), D(15), D(30))["spread_bps"], D(200))

    def test_obi_1(self):
        self.assertEqual(depth(*levels())["obi_1"], D("-0." + "3"*50))

    def test_obi_3(self):
        self.assertEqual(depth(*levels())["obi_3"], D("-0." + "3"*50))

    def test_obi_5(self):
        self.assertEqual(depth(*levels())["obi_5"], D("-0." + "3"*50))

    def test_level_imbalance(self):
        row = depth(*levels())
        for i in range(1, 6):
            self.assertEqual(row[f"level_imbalance_{i}"], D("-0." + "3"*50))

    def test_microprice(self):
        self.assertEqual(depth(*levels())["microprice"], D("99." + "6"*47 + "7"))

    def test_microprice_deviation(self):
        bids, asks = levels()
        bids = ((D(99), D(3)),) + bids[1:]
        asks = ((D(101), D(1)),) + asks[1:]
        self.assertEqual(depth(bids, asks)["microprice_deviation_bps"], D(50))

    def test_bid_distance(self):
        row = depth(*levels())
        for i in range(1, 6):
            self.assertEqual(row[f"bid_distance_bps_{i}"], D(i * 100))

    def test_ask_distance(self):
        row = depth(*levels())
        for i in range(1, 6):
            self.assertEqual(row[f"ask_distance_bps_{i}"], D(i * 100))

    def test_cumulative_quantities(self):
        row = depth(*levels())
        self.assertEqual([row[f"cumulative_bid_quantity_{i}"] for i in range(1, 6)], list(map(D, (1, 3, 6, 10, 15))))
        self.assertEqual([row[f"cumulative_ask_quantity_{i}"] for i in range(1, 6)], list(map(D, (2, 6, 12, 20, 30))))

    def test_exact_decimal_input(self):
        row = aggregate(D("0.1"), D("0.3"), D("0.1"), D("0.2"))
        self.assertEqual(row["mid_price"], D("0.2"))
        self.assertEqual(row["spread"], D("0.2"))
        self.assertEqual(row["obi_5"], D("-0." + "3"*50))

    def test_caller_context_and_traps_cannot_change_output(self):
        expected = depth(*levels())
        with localcontext() as ctx:
            ctx.prec = 3
            ctx.rounding = ROUND_DOWN
            ctx.traps[Inexact] = True
            self.assertEqual(depth(*levels()), expected)
            self.assertEqual(aggregate(D(99), D(101), D(15), D(30))["obi_5"], expected["obi_5"])

    def test_float_rejected_without_conversion(self):
        row = aggregate(99.0, D(101), D(1), D(1))
        self.assertFalse(row["valid_feature_row"])
        self.assertIsNone(row["best_bid"])
        self.assertIn("INVALID_NUMERIC_TYPE", row["invalid_reason"])

    def test_numeric_string_rejected(self):
        self.assertIsNone(aggregate("99", D(101), D(1), D(1))["best_bid"])

    def test_nonfinite_values_null_and_invalid(self):
        for value in (D("NaN"), D("sNaN"), D("Infinity"), D("-Infinity")):
            row = aggregate(value, D(101), D(1), D(1))
            self.assertFalse(row["valid_feature_row"])
            self.assertIsNone(row["best_bid"])
            self.assertIn("NON_FINITE_VALUE", row["invalid_reason"])

    def test_negative_price_invalid(self):
        row = aggregate(D(-1), D(101), D(1), D(1))
        self.assertIsNone(row["best_bid"])
        self.assertIn("INVALID_PRICE", row["invalid_reason"])

    def test_zero_price_invalid(self):
        self.assertFalse(aggregate(D(0), D(101), D(1), D(1))["valid_feature_row"])

    def test_negative_quantity_invalid(self):
        row = aggregate(D(99), D(101), D(-1), D(1))
        self.assertIsNone(row["bid_volume_5"])
        self.assertIn("INVALID_QUANTITY", row["invalid_reason"])

    def test_crossed_invalid(self):
        row = aggregate(D(102), D(101), D(1), D(1))
        self.assertFalse(row["valid_feature_row"])
        self.assertIn("CROSSED_BOOK", row["invalid_reason"])
        self.assertEqual(row["spread"], D(-1))

    def test_locked_invalid(self):
        row = aggregate(D(100), D(100), D(1), D(1))
        self.assertFalse(row["valid_feature_row"])
        self.assertEqual(row["spread"], D(0))

    def test_empty_side_invalid(self):
        row = depth((), levels()[1])
        self.assertFalse(row["valid_feature_row"])
        self.assertIn("EMPTY_SIDE", row["invalid_reason"])
        self.assertIsNone(row["mid_price"])

    def test_insufficient_depth_not_filled(self):
        bids, asks = levels()
        row = depth(bids[:3], asks)
        self.assertFalse(row["valid_feature_row"])
        self.assertIn("INSUFFICIENT_TOP5_DEPTH", row["invalid_reason"])
        self.assertIsNone(row["bid_price_4"])
        self.assertIsNone(row["cumulative_bid_quantity_5"])
        self.assertIsNone(row["obi_5"])
        self.assertIsNotNone(row["obi_3"])

    def test_zero_depth_denominator_invalid(self):
        row = aggregate(D(99), D(101), D(0), D(0))
        self.assertFalse(row["valid_feature_row"])
        self.assertIsNone(row["obi_5"])
        self.assertEqual(row["invalid_reason"], "ZERO_DEPTH_DENOMINATOR")

    def test_zero_level_denominator_warning_only(self):
        bids, asks = levels()
        bids = bids[:1] + ((D(98), D(0)),) + bids[2:]
        asks = asks[:1] + ((D(102), D(0)),) + asks[2:]
        row = depth(bids, asks)
        self.assertTrue(row["valid_feature_row"])
        self.assertIsNone(row["level_imbalance_2"])
        self.assertEqual(row["invalid_reason"], "ZERO_LEVEL_DENOMINATOR")

    def test_zero_best_quantities_also_invalidate_microprice(self):
        bids, asks = levels()
        row = depth(((D(99), D(0)),) + bids[1:], ((D(101), D(0)),) + asks[1:])
        self.assertFalse(row["valid_feature_row"])
        self.assertIsNone(row["microprice"])
        self.assertIn("ZERO_DEPTH_DENOMINATOR", row["invalid_reason"])
        self.assertIn("ZERO_MICROPRICE_DENOMINATOR", row["invalid_reason"])

    def test_obi_range_and_endpoints(self):
        for bq, aq, expected in ((1, 0, 1), (0, 1, -1), (1, 1, 0)):
            row = aggregate(D(99), D(101), D(bq), D(aq))
            self.assertTrue(row["valid_feature_row"])
            self.assertEqual(row["obi_5"], D(expected))

    def test_microprice_within_spread(self):
        bids, asks = levels()
        for bq, aq in ((0, 1), (1, 0), (1, 2), (100, 1)):
            row = depth(((D(99), D(bq)),) + bids[1:], ((D(101), D(aq)),) + asks[1:])
            self.assertLessEqual(D(99), row["microprice"])
            self.assertLessEqual(row["microprice"], D(101))

    def test_unsorted_depth_invalid_not_sorted_silently(self):
        bids, asks = levels()
        row = depth(tuple(reversed(bids)), asks)
        self.assertIn("UNSORTED_DEPTH", row["invalid_reason"])
        self.assertEqual(row["bid_price_1"], D(95))

    def test_malformed_level_invalid(self):
        row = depth(((D(99),),), levels()[1])
        self.assertFalse(row["valid_feature_row"])
        self.assertIn("INVALID_LEVEL_STRUCTURE", row["invalid_reason"])

    def test_reason_codes_sorted_unique(self):
        row = aggregate(D("NaN"), D("NaN"), D(-1), D(-2))
        self.assertEqual(row["invalid_reason"], "INVALID_QUANTITY;NON_FINITE_VALUE")

    def test_inputs_unchanged(self):
        bids, asks = levels()
        expected = (bids, asks)
        depth(bids, asks)
        self.assertEqual((bids, asks), expected)


if __name__ == "__main__":
    unittest.main()
