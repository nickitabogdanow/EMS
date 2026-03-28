from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
GZIP_MINIMUM_SIZE = 800


def _parse_int_env(name: str, default: int, *, strict: bool) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw.strip())
    except ValueError as exc:
        if strict:
            raise ValueError(f"{name} must be an integer.") from exc
        return default


def _bounded_int_env(
    name: str,
    default: int,
    *,
    minimum: int,
    maximum: int,
    allow_zero: bool = False,
    strict: bool = False,
) -> int:
    value = _parse_int_env(name, default, strict=strict)
    if allow_zero and value == 0:
        return 0
    if strict and not (minimum <= value <= maximum):
        zero_note = " or 0" if allow_zero else ""
        raise ValueError(f"{name} must be between {minimum} and {maximum}{zero_note}.")
    if allow_zero and value < 0:
        return 0
    return max(minimum, min(value, maximum))


def max_plot_points(*, strict: bool = False) -> int:
    return _bounded_int_env(
        "EMS_MAX_PLOT_POINTS",
        14_000,
        minimum=2_000,
        maximum=500_000,
        allow_zero=True,
        strict=strict,
    )


def max_full_plot_points(*, strict: bool = False) -> int:
    return _bounded_int_env(
        "EMS_MAX_FULL_PLOT_POINTS",
        500_000,
        minimum=2_000,
        maximum=500_000,
        strict=strict,
    )


def max_highlight_shapes(*, strict: bool = False) -> int:
    return _bounded_int_env(
        "EMS_MAX_HIGHLIGHT_SHAPES",
        700,
        minimum=50,
        maximum=5_000,
        strict=strict,
    )


def result_ttl_seconds(*, strict: bool = False) -> int:
    return _bounded_int_env(
        "EMS_RESULT_TTL_SECONDS",
        3_600,
        minimum=60,
        maximum=86_400,
        strict=strict,
    )


def max_csv_rows(*, strict: bool = False) -> int:
    return _bounded_int_env(
        "EMS_MAX_CSV_ROWS",
        400_000,
        minimum=1,
        maximum=2_000_000,
        strict=strict,
    )


def max_upload_bytes(*, strict: bool = False) -> int:
    return _bounded_int_env(
        "EMS_MAX_UPLOAD_BYTES",
        20 * 1024 * 1024,
        minimum=1,
        maximum=512 * 1024 * 1024,
        strict=strict,
    )


def max_request_body_bytes(*, strict: bool = False) -> int:
    return _bounded_int_env(
        "EMS_MAX_REQUEST_BODY_BYTES",
        45 * 1024 * 1024,
        minimum=1,
        maximum=1024 * 1024 * 1024,
        strict=strict,
    )


def max_result_points(*, strict: bool = False) -> int:
    return _bounded_int_env(
        "EMS_MAX_RESULT_POINTS",
        500_000,
        minimum=1,
        maximum=5_000_000,
        strict=strict,
    )


def max_stored_results(*, strict: bool = False) -> int:
    return _bounded_int_env(
        "EMS_MAX_STORED_RESULTS",
        32,
        minimum=1,
        maximum=1_000,
        strict=strict,
    )


def max_stored_points_total(*, strict: bool = False) -> int:
    return _bounded_int_env(
        "EMS_MAX_STORED_POINTS_TOTAL",
        2_000_000,
        minimum=1,
        maximum=20_000_000,
        strict=strict,
    )


def log_level(*, strict: bool = False) -> str:
    raw = os.environ.get("EMS_LOG_LEVEL", "INFO").strip().upper()
    allowed = {"DEBUG", "INFO", "WARNING", "ERROR"}
    if raw in allowed:
        return raw
    if strict:
        raise ValueError("EMS_LOG_LEVEL must be one of DEBUG, INFO, WARNING, ERROR.")
    return "INFO"


def trusted_hosts() -> list[str]:
    raw = os.environ.get("EMS_TRUSTED_HOSTS", "").strip()
    if not raw:
        return []
    return [host.strip() for host in raw.split(",") if host.strip()]


def validate_runtime_config() -> None:
    max_plot_points(strict=True)
    max_full_plot_points(strict=True)
    max_highlight_shapes(strict=True)
    result_ttl_seconds(strict=True)
    max_csv_rows(strict=True)
    max_upload_bytes(strict=True)
    max_request_body_bytes(strict=True)
    max_result_points(strict=True)
    max_stored_results(strict=True)
    max_stored_points_total(strict=True)
    log_level(strict=True)
