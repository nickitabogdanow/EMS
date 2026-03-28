from __future__ import annotations

from app.config import max_highlight_shapes


def _sign_tri(x: float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def _typical_freq_step(freqs: list[float]) -> float:
    if len(freqs) < 2:
        return 1.0
    return (freqs[-1] - freqs[0]) / (len(freqs) - 1)


def _collect_highlight_segments(
    freqs: list[float],
    ampls: list[float],
    threshold: float,
) -> list[tuple[float, float, int]]:
    """Сегменты (f0, f1, sign), sign ∈ {-1, 1}."""
    n = len(freqs)
    if n != len(ampls) or n == 0 or threshold <= 0:
        return []

    out: list[tuple[float, float, int]] = []
    i = 0
    while i < n:
        if abs(ampls[i]) < threshold:
            i += 1
            continue

        sg = _sign_tri(ampls[i])
        if sg == 0:
            i += 1
            continue

        j = i
        while j + 1 < n:
            if abs(ampls[j + 1]) < threshold:
                break
            if _sign_tri(ampls[j + 1]) != sg:
                break
            j += 1

        x0, x1 = freqs[i], freqs[j]
        if x1 < x0:
            x0, x1 = x1, x0
        out.append((x0, x1, sg))
        i = j + 1

    return out


def _merge_highlight_segments(
    segments: list[tuple[float, float, int]],
    max_gap_hz: float,
) -> list[tuple[float, float, int]]:
    """Слить соседние сегменты одного знака, если разрыв по freq не больше max_gap_hz."""
    if not segments:
        return []

    segs = sorted(segments, key=lambda t: t[0])
    merged: list[tuple[float, float, int]] = []
    c0, c1, sg = segs[0]
    for x0, x1, g in segs[1:]:
        if g == sg and x0 - c1 <= max_gap_hz:
            c1 = max(c1, x1)
        else:
            merged.append((c0, c1, sg))
            c0, c1, sg = x0, x1, g
    merged.append((c0, c1, sg))
    return merged


def diff_highlight_shapes(
    freqs: list[float],
    ampls: list[float],
    threshold: float,
) -> tuple[list[dict], int, int]:
    """
    Полосы подсветки по прореженному ряду (как на графике).
    Близкие сегменты одного знака объединяются, число фигур ограничено — иначе Plotly зависает.
    """
    if threshold <= 0 or not freqs or len(freqs) != len(ampls):
        return [], 0, 0

    pos_fill = "rgba(52, 211, 153, 0.26)"
    neg_fill = "rgba(248, 113, 113, 0.26)"

    segments = _collect_highlight_segments(freqs, ampls, threshold)
    if not segments:
        return [], 0, 0

    step = _typical_freq_step(freqs)
    cap = max_highlight_shapes()
    gap = step * 8.0
    merged = segments
    for _ in range(14):
        merged = _merge_highlight_segments(merged, gap)
        if len(merged) <= cap:
            break
        gap *= 1.45

    if len(merged) > cap:
        merged = merged[:cap]

    shapes: list[dict] = []
    pos_bands = 0
    neg_bands = 0
    for x0, x1, sg in merged:
        shapes.append(
            {
                "type": "rect",
                "xref": "x",
                "yref": "paper",
                "x0": x0,
                "x1": x1,
                "y0": 0,
                "y1": 1,
                "fillcolor": pos_fill if sg > 0 else neg_fill,
                "line": {"width": 0},
                "layer": "below",
            }
        )
        if sg > 0:
            pos_bands += 1
        else:
            neg_bands += 1

    return shapes, pos_bands, neg_bands
