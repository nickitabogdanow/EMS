"""Прореживание рядов только для отрисовки Plotly (полные данные — в CSV)."""

from __future__ import annotations

from app.config import max_plot_points as _max_plot_points


def max_plot_points() -> int:
    return _max_plot_points()


def decimate_minmax(
    freqs: list[float],
    ampls: list[float],
    max_points: int,
) -> tuple[list[float], list[float]]:
    """
    Если точек больше max_points — оставляем до max_points точек, сохраняя
    в каждом частотном бакете точки с min и max ampl (огибающая спектра).
    """
    n = len(freqs)
    if n <= max_points or n <= 2:
        return list(freqs), list(ampls)

    n_buckets = max(1, max_points // 2)
    out_f: list[float] = []
    out_a: list[float] = []

    for b in range(n_buckets):
        lo = (b * n) // n_buckets
        hi = ((b + 1) * n) // n_buckets
        if hi <= lo:
            continue
        sub_a = ampls[lo:hi]
        off_min = sub_a.index(min(sub_a))
        off_max = sub_a.index(max(sub_a))
        imin = lo + off_min
        imax = lo + off_max
        for idx in sorted({imin, imax}, key=lambda i: freqs[i]):
            out_f.append(freqs[idx])
            out_a.append(ampls[idx])

    return out_f, out_a


def for_plot(
    freqs: list[float],
    ampls: list[float],
    max_points: int | None = None,
) -> tuple[list[float], list[float], bool]:
    """Возвращает (freqs, ampls, был_ли_прорежен)."""
    cap = max_points if max_points is not None else max_plot_points()
    if cap <= 0:
        return freqs, ampls, False
    if len(freqs) <= cap:
        return freqs, ampls, False
    f, a = decimate_minmax(freqs, ampls, cap)
    return f, a, True
