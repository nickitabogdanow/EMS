from __future__ import annotations

from app.csv_utils import merge_series, parse_csv, sorted_series, subtract
from app.highlight import diff_highlight_shapes
from app.plot_decimate import for_plot
from app.plot_figure import build_figure
from app.services.result_store import result_store


def build_subtract_response(
    raw_a: str,
    raw_b: str,
    *,
    operation: str,
    show_a: bool,
    show_b: bool,
    show_result: bool,
    highlight_threshold: float,
    max_plot_points: int,
    max_full_plot_points: int,
    full_resolution_plot: bool = False,
) -> dict:
    map_a = parse_csv(raw_a)
    map_b = parse_csv(raw_b)
    return build_subtract_response_from_maps(
        map_a,
        map_b,
        operation=operation,
        show_a=show_a,
        show_b=show_b,
        show_result=show_result,
        highlight_threshold=highlight_threshold,
        max_plot_points=max_plot_points,
        max_full_plot_points=max_full_plot_points,
        full_resolution_plot=full_resolution_plot,
    )


def build_subtract_response_from_maps(
    map_a: dict[float, float],
    map_b: dict[float, float],
    *,
    operation: str,
    show_a: bool,
    show_b: bool,
    show_result: bool,
    highlight_threshold: float,
    max_plot_points: int,
    max_full_plot_points: int,
    full_resolution_plot: bool = False,
) -> dict:
    if full_resolution_plot and max(len(map_a), len(map_b)) > max_full_plot_points:
        raise ValueError(
            f"Полный график разрешён только до {max_full_plot_points} точек на ряд. "
            "Отключите режим без прореживания или уменьшите CSV."
        )
    a_minus_b = operation == "a_minus_b"
    sub = subtract(map_a, map_b, a_minus_b=a_minus_b)
    op_label = "A − B" if a_minus_b else "B − A"

    fa, aa = sorted_series(map_a)
    fb, ab = sorted_series(map_b)

    fa_p, aa_p, d_a = for_plot(fa, aa, max_plot_points)
    fb_p, ab_p, d_b = for_plot(fb, ab, max_plot_points)
    fr_p, ar_p, d_r = for_plot(sub.freqs, sub.ampl, max_plot_points)
    plot_decimated = d_a or d_b or d_r

    # Подсветка строится по прореженному ряду, который реально уходит в Plotly.
    if sub.matched > 0 and highlight_threshold > 0 and fr_p:
        h_shapes, h_pos, h_neg = diff_highlight_shapes(fr_p, ar_p, highlight_threshold)
    else:
        h_shapes, h_pos, h_neg = [], 0, 0
    plot_pts = max(len(fa_p), len(fb_p), len(fr_p))

    figure = build_figure(
        fa_p,
        aa_p,
        fb_p,
        ab_p,
        fr_p,
        ar_p,
        op_label,
        show_a=show_a,
        show_b=show_b,
        show_result=show_result,
        highlight_shapes=h_shapes or None,
    )

    result_id = None
    result_filename = "result.csv"
    result_download_url = None
    if sub.matched > 0:
        result_id = result_store.save(sub.freqs, sub.ampl, filename=result_filename)
        result_download_url = f"/api/download/{result_id}"

    return {
        "mode": "subtract",
        "matched": sub.matched,
        "only_in_a": sub.only_in_a,
        "only_in_b": sub.only_in_b,
        "operation": operation,
        "operation_label": op_label,
        "figure": figure,
        "result_id": result_id,
        "result_filename": result_filename,
        "result_download_url": result_download_url,
        "points_a": len(map_a),
        "points_b": len(map_b),
        "highlight_threshold": highlight_threshold,
        "highlight_bands": h_pos + h_neg,
        "highlight_bands_positive": h_pos,
        "highlight_bands_negative": h_neg,
        "plot_decimated": plot_decimated,
        "plot_max_points": max_plot_points,
        "plot_trace_points": plot_pts,
        "plot_full_resolution": full_resolution_plot,
    }


def build_merge_response(
    raw_a: str,
    raw_b: str,
    *,
    duplicate_policy: str,
    show_a: bool,
    show_b: bool,
    show_result: bool,
    max_plot_points: int,
    max_full_plot_points: int,
    full_resolution_plot: bool = False,
) -> dict:
    map_a = parse_csv(raw_a)
    map_b = parse_csv(raw_b)
    return build_merge_response_from_maps(
        map_a,
        map_b,
        duplicate_policy=duplicate_policy,
        show_a=show_a,
        show_b=show_b,
        show_result=show_result,
        max_plot_points=max_plot_points,
        max_full_plot_points=max_full_plot_points,
        full_resolution_plot=full_resolution_plot,
    )


def build_merge_response_from_maps(
    map_a: dict[float, float],
    map_b: dict[float, float],
    *,
    duplicate_policy: str,
    show_a: bool,
    show_b: bool,
    show_result: bool,
    max_plot_points: int,
    max_full_plot_points: int,
    full_resolution_plot: bool = False,
) -> dict:
    if full_resolution_plot and max(len(map_a), len(map_b)) > max_full_plot_points:
        raise ValueError(
            f"Полный график разрешён только до {max_full_plot_points} точек на ряд. "
            "Отключите режим без прореживания или уменьшите CSV."
        )
    merged = merge_series(map_a, map_b, on_duplicate=duplicate_policy)

    policy_label = {"average": "среднее A и B", "a": "значение из A", "b": "значение из B"}[
        duplicate_policy
    ]
    op_label = f"объединение ({policy_label})"

    fa, aa = sorted_series(map_a)
    fb, ab = sorted_series(map_b)

    fa_p, aa_p, d_a = for_plot(fa, aa, max_plot_points)
    fb_p, ab_p, d_b = for_plot(fb, ab, max_plot_points)
    fm_p, am_p, d_m = for_plot(merged.freqs, merged.ampl, max_plot_points)
    plot_decimated = d_a or d_b or d_m
    plot_pts = max(len(fa_p), len(fb_p), len(fm_p))

    figure = build_figure(
        fa_p,
        aa_p,
        fb_p,
        ab_p,
        fm_p,
        am_p,
        op_label,
        show_a=show_a,
        show_b=show_b,
        show_result=show_result,
    )

    result_id = None
    result_filename = "merged.csv"
    result_download_url = None
    if merged.freqs:
        result_id = result_store.save(merged.freqs, merged.ampl, filename=result_filename)
        result_download_url = f"/api/download/{result_id}"

    return {
        "mode": "merge",
        "duplicate_policy": duplicate_policy,
        "operation_label": op_label,
        "merged_points": len(merged.freqs),
        "duplicate_freqs": merged.duplicate_freqs,
        "only_in_a": merged.only_in_a,
        "only_in_b": merged.only_in_b,
        "figure": figure,
        "result_id": result_id,
        "result_filename": result_filename,
        "result_download_url": result_download_url,
        "points_a": len(map_a),
        "points_b": len(map_b),
        "plot_decimated": plot_decimated,
        "plot_max_points": max_plot_points,
        "plot_trace_points": plot_pts,
        "plot_full_resolution": full_resolution_plot,
    }
