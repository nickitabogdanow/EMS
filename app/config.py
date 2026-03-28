from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
GZIP_MINIMUM_SIZE = 800


def max_plot_points() -> int:
    raw = os.environ.get("EMS_MAX_PLOT_POINTS", "14000").strip()
    try:
        n = int(raw)
    except ValueError:
        return 14000
    if n <= 0:
        return 0
    return max(2000, min(n, 500_000))


def max_highlight_shapes() -> int:
    try:
        n = int(os.environ.get("EMS_MAX_HIGHLIGHT_SHAPES", "700").strip())
    except ValueError:
        n = 700
    return max(50, min(n, 5000))


def result_ttl_seconds() -> int:
    try:
        n = int(os.environ.get("EMS_RESULT_TTL_SECONDS", "3600").strip())
    except ValueError:
        n = 3600
    return max(60, min(n, 86_400))
