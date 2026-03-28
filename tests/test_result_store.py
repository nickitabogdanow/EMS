from __future__ import annotations

import os
import unittest

from app.services.result_store import ResultExpired, ResultTooLarge, result_store


class ResultStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        result_store._items.clear()
        result_store._expired_ids.clear()
        result_store._total_points = 0

    def _set_env(self, key: str, value: str) -> None:
        old_value = os.environ.get(key)
        os.environ[key] = value

        def restore() -> None:
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value

        self.addCleanup(restore)

    def test_evicts_oldest_results_when_store_hits_point_cap(self) -> None:
        self._set_env("EMS_MAX_STORED_RESULTS", "5")
        self._set_env("EMS_MAX_STORED_POINTS_TOTAL", "5")

        oldest_id = result_store.save([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], filename="old.csv")
        newest_id = result_store.save([10.0, 11.0], [5.0, 6.0], filename="new.csv")
        kept_id = result_store.save([20.0], [7.0], filename="keep.csv")

        with self.assertRaises(ResultExpired):
            result_store.get_csv(oldest_id)

        filename, csv_text = result_store.get_csv(newest_id)
        self.assertEqual(filename, "new.csv")
        self.assertIn("10.0,5.0", csv_text)
        self.assertTrue(result_store.get_csv(kept_id)[1].endswith("20.0,7.0"))

    def test_rejects_single_result_over_point_cap(self) -> None:
        self._set_env("EMS_MAX_RESULT_POINTS", "2")

        with self.assertRaises(ResultTooLarge):
            result_store.save([1.0, 2.0, 3.0], [1.0, 2.0, 3.0], filename="too-big.csv")


if __name__ == "__main__":
    unittest.main()
