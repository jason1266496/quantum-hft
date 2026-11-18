"""Artificial exact-decimal canonical state tests; no market inputs."""

from decimal import Decimal, localcontext
import hashlib
import json
import unittest

from data_pipeline.orderbook.canonical import (
    canonical_bytes, canonical_decimal, canonical_state, canonical_state_hash,
)


D = Decimal


class CanonicalTests(unittest.TestCase):
    def state(self):
        return {"local_update_id": 10, "bids": {D("2"): D("3"), D("1"): D("4")},
                "asks": {D("4"): D("5"), D("3"): D("6")}}

    def test_decimal_fractional_trailing_zeros(self):
        self.assertEqual(canonical_decimal(D("123.45000")), "123.45")

    def test_decimal_integer_trailing_zeros_are_significant(self):
        self.assertEqual(canonical_decimal(D("1200.00")), "1200")

    def test_decimal_positive_exponent_fixed(self):
        self.assertEqual(canonical_decimal(D("1.20E+5")), "120000")

    def test_decimal_negative_exponent_fixed(self):
        self.assertEqual(canonical_decimal(D("1.20E-8")), "0.000000012")

    def test_decimal_signed_zero_canonical(self):
        for number in ("0", "-0", "0E+10", "-0.000"):
            self.assertEqual(canonical_decimal(D(number)), "0")

    def test_decimal_low_context_does_not_round(self):
        text = "123456789012345678901234567890.123456789012345678900"
        with localcontext() as context:
            context.prec = 2
            self.assertEqual(canonical_decimal(D(text)), text.rstrip("0"))

    def test_decimal_nonfinite_rejected(self):
        for value in ("NaN", "sNaN", "Infinity", "-Infinity"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                canonical_decimal(D(value))

    def test_decimal_float_and_integer_rejected(self):
        for value in (1, 1.5, True, "1.5", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                canonical_decimal(value)

    def test_state_bid_desc_ask_asc(self):
        result = canonical_state(self.state())
        self.assertEqual(result["bids"], [["2", "3"], ["1", "4"]])
        self.assertEqual(result["asks"], [["3", "6"], ["4", "5"]])

    def test_state_counts_best_and_update_id(self):
        result = canonical_state(self.state())
        self.assertEqual((result["local_update_id"], result["bid_level_count"],
                          result["ask_level_count"], result["best_bid"], result["best_ask"]),
                         (10, 2, 2, "2", "3"))

    def test_empty_state_supported(self):
        result = canonical_state({"local_update_id": 0, "bids": {}, "asks": {}})
        self.assertEqual(result["bids"], [])
        self.assertEqual(result["asks"], [])
        self.assertIsNone(result["best_bid"])
        self.assertIsNone(result["best_ask"])

    def test_hash_ignores_insertion_order(self):
        a, b = self.state(), self.state()
        b["bids"] = dict(reversed(list(b["bids"].items())))
        b["asks"] = dict(reversed(list(b["asks"].items())))
        self.assertEqual(canonical_state_hash(a), canonical_state_hash(b))

    def test_hash_ignores_numeric_spelling(self):
        a = {"local_update_id": 3, "bids": {D("2.000"): D("3E+0")}, "asks": {D("4.0"): D("5.00")}}
        b = {"local_update_id": 3, "bids": {D("2E+0"): D("3")}, "asks": {D("4"): D("5")}}
        self.assertEqual(canonical_state_hash(a), canonical_state_hash(b))

    def test_hash_low_decimal_context_is_stable(self):
        state = {"local_update_id": 3, "bids": {D("1234567890.123456789"): D("12345678901234567890.123456789")}, "asks": {D("1234567891.123456789"): D("1")}}
        expected = canonical_state_hash(state)
        with localcontext() as context:
            context.prec = 1
            self.assertEqual(canonical_state_hash(state), expected)

    def test_hash_changes_for_quantity_price_or_update_id(self):
        original = self.state()
        expected = canonical_state_hash(original)
        for field in ("quantity", "price", "update_id"):
            state = self.state()
            if field == "quantity":
                state["bids"][D("2")] = D("9")
            elif field == "price":
                state["bids"][D("1.5")] = state["bids"].pop(D("1"))
            else:
                state["local_update_id"] += 1
            self.assertNotEqual(canonical_state_hash(state), expected)

    def test_hash_excludes_incidental_metadata(self):
        state = self.state()
        expected = canonical_state_hash(state)
        state.update(elapsed_seconds=9, local_timestamp_us=17, object_address="irrelevant")
        self.assertEqual(canonical_state_hash(state), expected)

    def test_bytes_are_stable_json_and_sha256(self):
        payload = canonical_bytes(self.state())
        self.assertEqual(json.loads(payload), canonical_state(self.state()))
        self.assertEqual(hashlib.sha256(payload).hexdigest(), canonical_state_hash(self.state()))

    def test_state_canonicalization_does_not_mutate_input(self):
        state = self.state()
        before = {key: dict(value) if isinstance(value, dict) else value for key, value in state.items()}
        canonical_state_hash(state)
        self.assertEqual(state, before)

    def test_state_invalid_update_id_rejected(self):
        for value in (-1, True, D("1"), "1"):
            state = self.state()
            state["local_update_id"] = value
            with self.assertRaises(ValueError):
                canonical_state(state)

    def test_state_nonpositive_prices_rejected(self):
        for value in (D("0"), D("-1"), D("NaN"), 1.5):
            state = self.state()
            state["bids"] = {value: D("1")}
            with self.assertRaises(ValueError):
                canonical_state(state)

    def test_state_nonpositive_or_float_stored_quantity_rejected(self):
        for value in (D("0"), D("-1"), D("Infinity"), 1.5):
            state = self.state()
            state["bids"][D("2")] = value
            with self.assertRaises(ValueError):
                canonical_state(state)


if __name__ == "__main__":
    unittest.main()
