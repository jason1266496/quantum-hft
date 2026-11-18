"""Artificial update-ID cases only; no files, clocks, or market inputs."""

import unittest

from data_pipeline.orderbook.continuity import classify_update
from data_pipeline.orderbook.types import BookError


class ContinuityTests(unittest.TestCase):
    def test_before_snapshot_is_stale(self):
        self.assertEqual(classify_update(100, 100, 0, 90, 99), ("STALE_BEFORE_SNAPSHOT", "SKIP"))

    def test_snapshot_boundary_is_stale(self):
        self.assertEqual(classify_update(100, 100, 0, 90, 100), ("STALE_BEFORE_SNAPSHOT", "SKIP"))

    def test_first_exact_bridge(self):
        self.assertEqual(classify_update(100, 100, 0, 101, 105), ("CONTIGUOUS", "APPLY"))

    def test_first_overlapping_bridge(self):
        self.assertEqual(classify_update(100, 100, 0, 99, 105), ("OVERLAPPING_CONTIGUOUS", "APPLY"))

    def test_first_bridge_missing(self):
        self.assertEqual(classify_update(100, 100, 0, 102, 105), ("FIRST_EVENT_BRIDGE_FAILURE", "STOP"))

    def test_next_contiguous(self):
        self.assertEqual(classify_update(100, 105, 1, 106, 109), ("CONTIGUOUS", "APPLY"))

    def test_next_overlapping(self):
        self.assertEqual(classify_update(100, 105, 1, 104, 109), ("OVERLAPPING_CONTIGUOUS", "APPLY"))

    def test_duplicate(self):
        self.assertEqual(classify_update(100, 105, 1, 101, 105), ("STALE_OR_DUPLICATE", "SKIP"))

    def test_later_stale(self):
        self.assertEqual(classify_update(100, 105, 1, 100, 102), ("STALE_OR_DUPLICATE", "SKIP"))

    def test_gap(self):
        self.assertEqual(classify_update(100, 105, 1, 107, 109), ("UPDATE_ID_GAP", "STOP"))

    def test_zero_snapshot(self):
        self.assertEqual(classify_update(0, 0, 0, 0, 1), ("OVERLAPPING_CONTIGUOUS", "APPLY"))

    def test_large_ids_are_exact(self):
        large = 10 ** 80
        self.assertEqual(classify_update(large, large, 0, large + 1, large + 2), ("CONTIGUOUS", "APPLY"))

    def test_invalid_integer_types(self):
        for index in range(5):
            for invalid in (True, 1.0, "1", None):
                with self.subTest(index=index, invalid=invalid):
                    values = [100, 100, 0, 101, 102]
                    values[index] = invalid
                    with self.assertRaises(BookError) as caught:
                        classify_update(*values)
                    self.assertEqual(caught.exception.code, "INVALID_UPDATE_ID")

    def test_negative_values(self):
        for index in range(5):
            values = [100, 100, 0, 101, 102]
            values[index] = -1
            with self.subTest(index=index), self.assertRaises(BookError):
                classify_update(*values)

    def test_reversed_ids(self):
        with self.assertRaises(BookError):
            classify_update(100, 100, 0, 103, 102)

    def test_local_id_before_snapshot(self):
        with self.assertRaises(BookError) as caught:
            classify_update(100, 99, 1, 100, 101)
        self.assertEqual(caught.exception.code, "INVALID_CONTINUITY_STATE")

    def test_no_apply_cannot_advance_local(self):
        with self.assertRaises(BookError):
            classify_update(100, 101, 0, 102, 102)


if __name__ == "__main__":
    unittest.main()
