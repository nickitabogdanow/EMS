from __future__ import annotations

import os
import unittest

from app.highlight import diff_highlight_shapes


class HighlightTests(unittest.TestCase):
    def test_counts_positive_and_negative_bands(self) -> None:
        freqs = [1.0, 2.0, 3.0, 4.0, 5.0]
        ampls = [0.0, 6.0, 7.0, -8.0, -9.0]

        shapes, pos_bands, neg_bands = diff_highlight_shapes(freqs, ampls, threshold=5.0)

        self.assertEqual(len(shapes), 2)
        self.assertEqual(pos_bands, 1)
        self.assertEqual(neg_bands, 1)
        self.assertEqual(shapes[0]["fillcolor"], "rgba(52, 211, 153, 0.26)")
        self.assertEqual(shapes[1]["fillcolor"], "rgba(248, 113, 113, 0.26)")

    def test_caps_shape_count_from_env(self) -> None:
        old_value = os.environ.get("EMS_MAX_HIGHLIGHT_SHAPES")
        os.environ["EMS_MAX_HIGHLIGHT_SHAPES"] = "50"
        try:
            freqs = [float(i) for i in range(140)]
            pattern = [6.0, 0.0, -6.0, 0.0]
            ampls = [pattern[i % len(pattern)] for i in range(140)]

            shapes, pos_bands, neg_bands = diff_highlight_shapes(freqs, ampls, threshold=5.0)

            self.assertEqual(len(shapes), 50)
            self.assertEqual(pos_bands + neg_bands, 50)
        finally:
            if old_value is None:
                os.environ.pop("EMS_MAX_HIGHLIGHT_SHAPES", None)
            else:
                os.environ["EMS_MAX_HIGHLIGHT_SHAPES"] = old_value


if __name__ == "__main__":
    unittest.main()
