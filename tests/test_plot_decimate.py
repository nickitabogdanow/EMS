from __future__ import annotations

import unittest

from app.plot_decimate import for_plot


class PlotDecimateTests(unittest.TestCase):
    def test_keeps_small_series_untouched(self) -> None:
        freqs = [1.0, 2.0, 3.0]
        ampls = [10.0, 20.0, 30.0]

        out_f, out_a, decimated = for_plot(freqs, ampls, max_points=10)

        self.assertEqual(out_f, freqs)
        self.assertEqual(out_a, ampls)
        self.assertFalse(decimated)

    def test_decimates_large_series(self) -> None:
        freqs = [float(i) for i in range(20)]
        ampls = [float((i % 5) - 2) for i in range(20)]

        out_f, out_a, decimated = for_plot(freqs, ampls, max_points=6)

        self.assertTrue(decimated)
        self.assertLessEqual(len(out_f), 6)
        self.assertEqual(len(out_f), len(out_a))

    def test_zero_cap_disables_decimation(self) -> None:
        freqs = [float(i) for i in range(20)]
        ampls = [float(i) for i in range(20)]

        out_f, out_a, decimated = for_plot(freqs, ampls, max_points=0)

        self.assertEqual(out_f, freqs)
        self.assertEqual(out_a, ampls)
        self.assertFalse(decimated)


if __name__ == "__main__":
    unittest.main()
