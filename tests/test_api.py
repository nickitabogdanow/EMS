from __future__ import annotations

import unittest
from time import time

from fastapi.testclient import TestClient

from app.main import app
from app.services.result_store import result_store


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
        self.assertNotIn("result_csv", payload)
        self.assertEqual(payload["result_filename"], "result.csv")
        self.assertRegex(payload["result_id"], r"^[0-9a-f]{32}$")
        self.assertEqual(payload["result_download_url"], f"/api/download/{payload['result_id']}")
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
        self.assertNotIn("result_csv", payload)
        self.assertEqual(payload["result_filename"], "merged.csv")
        self.assertRegex(payload["result_id"], r"^[0-9a-f]{32}$")
        self.assertEqual(payload["result_download_url"], f"/api/download/{payload['result_id']}")
        self.assertIn("figure", payload)

    def test_download_endpoint_returns_csv(self) -> None:
        response = self.client.post(
            "/api/analyze",
            data={
                "operation": "a_minus_b",
                "show_a": "false",
                "show_b": "false",
                "show_result": "true",
                "highlight_threshold": "0",
            },
            files={
                "file_a": ("a.csv", b"freq,ampl\n10,5\n20,8\n", "text/csv"),
                "file_b": ("b.csv", b"freq,ampl\n20,3\n30,7\n", "text/csv"),
            },
        )

        self.assertEqual(response.status_code, 200)
        result_id = response.json()["result_id"]

        download = self.client.get(f"/api/download/{result_id}")

        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.text, "freq,ampl\n20.0,5.0")
        self.assertIn('attachment; filename="result.csv"', download.headers["content-disposition"])
        self.assertIn("text/csv", download.headers["content-type"])

    def test_download_endpoint_returns_410_for_expired_result(self) -> None:
        result_id = result_store.save([10.0], [5.0], filename="result.csv")
        result_store._items[result_id].created_at = time() - 4000

        response = self.client.get(f"/api/download/{result_id}")

        self.assertEqual(response.status_code, 410)
        self.assertEqual(response.json()["detail"], "Результат устарел. Выполните расчёт заново.")

    def test_analyze_rejects_non_utf8_upload(self) -> None:
        response = self.client.post(
            "/api/analyze",
            data={
                "operation": "a_minus_b",
                "show_a": "false",
                "show_b": "false",
                "show_result": "true",
                "highlight_threshold": "0",
            },
            files={
                "file_a": ("a.csv", b"\xff\xfe\x00", "text/csv"),
                "file_b": ("b.csv", b"freq,ampl\n20,3\n", "text/csv"),
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Файлы должны быть в UTF-8")

    def test_analyze_can_disable_plot_decimation(self) -> None:
        rows_a = "freq,ampl\n" + "\n".join(f"{i},{i}" for i in range(2500)) + "\n"
        rows_b = "freq,ampl\n" + "\n".join(f"{i},{i - 1}" for i in range(2500)) + "\n"

        response = self.client.post(
            "/api/analyze",
            data={
                "operation": "a_minus_b",
                "show_a": "false",
                "show_b": "false",
                "show_result": "true",
                "highlight_threshold": "0",
                "full_resolution_plot": "true",
            },
            files={
                "file_a": ("a.csv", rows_a.encode("utf-8"), "text/csv"),
                "file_b": ("b.csv", rows_b.encode("utf-8"), "text/csv"),
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertFalse(payload["plot_decimated"])
        self.assertTrue(payload["plot_full_resolution"])
        self.assertEqual(payload["plot_trace_points"], 2500)


if __name__ == "__main__":
    unittest.main()
