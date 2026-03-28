from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_analyze_happy_path(self) -> None:
        response = self.client.post(
            "/api/analyze",
            data={
                "operation": "a_minus_b",
                "show_a": "true",
                "show_b": "false",
                "show_result": "true",
                "highlight_threshold": "5",
            },
            files={
                "file_a": ("a.csv", b"freq,ampl\n10,5\n20,8\n", "text/csv"),
                "file_b": ("b.csv", b"freq,ampl\n20,3\n30,7\n", "text/csv"),
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mode"], "subtract")
        self.assertEqual(payload["matched"], 1)
        self.assertEqual(payload["only_in_a"], 1)
        self.assertEqual(payload["only_in_b"], 1)
        self.assertEqual(payload["result_csv"], "freq,ampl\n20.0,5.0")
        self.assertIn("figure", payload)

    def test_merge_happy_path(self) -> None:
        response = self.client.post(
            "/api/merge",
            data={
                "duplicate_policy": "average",
                "show_a": "false",
                "show_b": "false",
                "show_result": "true",
            },
            files={
                "file_a": ("a.csv", b"freq,ampl\n10,5\n20,8\n", "text/csv"),
                "file_b": ("b.csv", b"freq,ampl\n20,4\n30,6\n", "text/csv"),
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["mode"], "merge")
        self.assertEqual(payload["duplicate_policy"], "average")
        self.assertEqual(payload["merged_points"], 3)
        self.assertEqual(payload["duplicate_freqs"], 1)
        self.assertEqual(payload["result_csv"], "freq,ampl\n10.0,5.0\n20.0,6.0\n30.0,6.0")
        self.assertIn("figure", payload)


if __name__ == "__main__":
    unittest.main()
