from __future__ import annotations

import unittest

from app.csv_utils import merge_series, parse_csv, subtract


class ParseCsvTests(unittest.TestCase):
    def test_rejects_empty_file(self) -> None:
        with self.assertRaisesRegex(ValueError, "Пустой файл"):
            parse_csv("")

    def test_rejects_missing_columns(self) -> None:
        with self.assertRaisesRegex(ValueError, "freq и ampl"):
            parse_csv("x,y\n1,2\n")

    def test_supports_comma_and_semicolon_delimiters(self) -> None:
        parsed_comma = parse_csv("freq,ampl\n10,1\n20,2\n")
        parsed_semicolon = parse_csv("freq;ampl\n10;1\n20;2\n")

        self.assertEqual(parsed_comma, {10.0: 1.0, 20.0: 2.0})
        self.assertEqual(parsed_semicolon, {10.0: 1.0, 20.0: 2.0})

    def test_skips_invalid_rows(self) -> None:
        parsed = parse_csv("freq,ampl\n10,1\nbroken,row\n20,2\n")
        self.assertEqual(parsed, {10.0: 1.0, 20.0: 2.0})


class SpectrumMathTests(unittest.TestCase):
    def test_subtract_counts_and_values(self) -> None:
        result = subtract({10.0: 5.0, 20.0: 7.0}, {20.0: 3.0, 30.0: 9.0}, a_minus_b=True)

        self.assertEqual(result.freqs, [20.0])
        self.assertEqual(result.ampl, [4.0])
        self.assertEqual(result.matched, 1)
        self.assertEqual(result.only_in_a, 1)
        self.assertEqual(result.only_in_b, 1)

    def test_merge_duplicate_policy_average(self) -> None:
        result = merge_series({10.0: 2.0, 20.0: 8.0}, {20.0: 4.0, 30.0: 6.0}, on_duplicate="average")

        self.assertEqual(result.freqs, [10.0, 20.0, 30.0])
        self.assertEqual(result.ampl, [2.0, 6.0, 6.0])
        self.assertEqual(result.duplicate_freqs, 1)
        self.assertEqual(result.only_in_a, 1)
        self.assertEqual(result.only_in_b, 1)

    def test_merge_duplicate_policy_a(self) -> None:
        result = merge_series({10.0: 2.0}, {10.0: 4.0}, on_duplicate="a")
        self.assertEqual(result.ampl, [2.0])

    def test_merge_duplicate_policy_b(self) -> None:
        result = merge_series({10.0: 2.0}, {10.0: 4.0}, on_duplicate="b")
        self.assertEqual(result.ampl, [4.0])


if __name__ == "__main__":
    unittest.main()
