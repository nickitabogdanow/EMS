from __future__ import annotations

import json
from pathlib import Path

import plotly.graph_objects as go
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.csv_utils import merge_series, parse_csv, result_to_csv, sorted_series, subtract

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="CSV freq/ampl")

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index() -> FileResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="static/index.html not found")
    return FileResponse(index_path)


def _sign_tri(x: float) -> int:
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def diff_highlight_shapes(
    freqs: list[float],
    ampls: list[float],
    threshold: float,
) -> tuple[list[dict], int, int]:
    """Полосы, где |разность| >= threshold: зелёный — >0, красный — <0 (по знаку результата)."""
    if threshold <= 0 or not freqs or len(freqs) != len(ampls):
        return [], 0, 0

    pos_fill = "rgba(52, 211, 153, 0.26)"
    neg_fill = "rgba(248, 113, 113, 0.26)"

    n = len(freqs)
    shapes: list[dict] = []
    pos_bands = 0
    neg_bands = 0
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
        i = j + 1
    return shapes, pos_bands, neg_bands


def build_figure(
    freqs_a: list[float],
    ampl_a: list[float],
    freqs_b: list[float],
    ampl_b: list[float],
    freqs_r: list[float],
    ampl_r: list[float],
    operation_label: str,
    *,
    show_a: bool,
    show_b: bool,
    show_result: bool,
    highlight_shapes: list[dict] | None = None,
) -> dict:
    fig = go.Figure()
    trace_count = 0
    if show_a:
        fig.add_trace(
            go.Scatter(
                x=freqs_a,
                y=ampl_a,
                name="A",
                mode="lines",
                line=dict(color="#3d8bfd", width=1.2),
            )
        )
        trace_count += 1
    if show_b:
        fig.add_trace(
            go.Scatter(
                x=freqs_b,
                y=ampl_b,
                name="B",
                mode="lines",
                line=dict(color="#c792ea", width=1.2),
            )
        )
        trace_count += 1
    if show_result and freqs_r:
        fig.add_trace(
            go.Scatter(
                x=freqs_r,
                y=ampl_r,
                name=f"Результат ({operation_label})",
                mode="lines",
                line=dict(color="#c3e88d", width=1.5),
            )
        )
        trace_count += 1

    layout_kw: dict = dict(
        template="plotly_dark",
        paper_bgcolor="#0f1419",
        plot_bgcolor="#1a2332",
        font=dict(color="#e7ecf3", family="system-ui, sans-serif"),
        margin=dict(l=56, r=24, t=48, b=48),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        showlegend=trace_count > 1,
        hovermode="x unified" if trace_count > 1 else "closest",
        xaxis=dict(title="freq", gridcolor="#2d3a4d", zeroline=False),
        yaxis=dict(title="ampl", gridcolor="#2d3a4d", zeroline=False),
        height=480,
    )
    if highlight_shapes:
        layout_kw["shapes"] = highlight_shapes
    fig.update_layout(**layout_kw)
    return json.loads(fig.to_json())


def _form_bool(v: str | bool) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "on")


def _parse_highlight_threshold(raw: str | float) -> float:
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip().replace(",", ".")
    if not s:
        return 5.0
    try:
        return float(s)
    except ValueError:
        return 5.0


@app.post("/api/analyze")
async def analyze(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
    operation: str = Form("a_minus_b"),
    show_a: str | bool = Form("false"),
    show_b: str | bool = Form("false"),
    show_result: str | bool = Form("true"),
    highlight_threshold: str | float = Form("5"),
):
    if operation not in ("a_minus_b", "b_minus_a"):
        raise HTTPException(status_code=400, detail="operation must be a_minus_b or b_minus_a")

    sa, sb, sr = _form_bool(show_a), _form_bool(show_b), _form_bool(show_result)
    if not (sa or sb or sr):
        raise HTTPException(
            status_code=400,
            detail="Выберите хотя бы один вариант отображения: A, B или результат.",
        )

    try:
        raw_a = (await file_a.read()).decode("utf-8")
        raw_b = (await file_b.read()).decode("utf-8")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail="Файлы должны быть в UTF-8") from e

    try:
        map_a = parse_csv(raw_a)
        map_b = parse_csv(raw_b)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    a_minus_b = operation == "a_minus_b"
    sub = subtract(map_a, map_b, a_minus_b=a_minus_b)
    op_label = "A − B" if a_minus_b else "B − A"

    fa, aa = sorted_series(map_a)
    fb, ab = sorted_series(map_b)

    ht = _parse_highlight_threshold(highlight_threshold)
    if sub.matched > 0 and ht > 0:
        h_shapes, h_pos, h_neg = diff_highlight_shapes(sub.freqs, sub.ampl, ht)
    else:
        h_shapes, h_pos, h_neg = [], 0, 0

    figure = build_figure(
        fa,
        aa,
        fb,
        ab,
        sub.freqs,
        sub.ampl,
        op_label,
        show_a=sa,
        show_b=sb,
        show_result=sr,
        highlight_shapes=h_shapes or None,
    )

    result_csv = ""
    if sub.matched > 0:
        result_csv = result_to_csv(sub.freqs, sub.ampl)

    return JSONResponse(
        {
            "mode": "subtract",
            "matched": sub.matched,
            "only_in_a": sub.only_in_a,
            "only_in_b": sub.only_in_b,
            "operation": operation,
            "operation_label": op_label,
            "figure": figure,
            "result_csv": result_csv,
            "points_a": len(map_a),
            "points_b": len(map_b),
            "highlight_threshold": ht,
            "highlight_bands": h_pos + h_neg,
            "highlight_bands_positive": h_pos,
            "highlight_bands_negative": h_neg,
        }
    )


@app.post("/api/merge")
async def merge(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
    duplicate_policy: str = Form("average"),
    show_a: str | bool = Form("false"),
    show_b: str | bool = Form("false"),
    show_result: str | bool = Form("true"),
):
    if duplicate_policy not in ("average", "a", "b"):
        raise HTTPException(
            status_code=400,
            detail="duplicate_policy: average (среднее), a (из A), b (из B)",
        )

    sa, sb, sr = _form_bool(show_a), _form_bool(show_b), _form_bool(show_result)
    if not (sa or sb or sr):
        raise HTTPException(
            status_code=400,
            detail="Выберите хотя бы один вариант отображения: A, B или объединённый ряд.",
        )

    try:
        raw_a = (await file_a.read()).decode("utf-8")
        raw_b = (await file_b.read()).decode("utf-8")
    except UnicodeDecodeError as e:
        raise HTTPException(status_code=400, detail="Файлы должны быть в UTF-8") from e

    try:
        map_a = parse_csv(raw_a)
        map_b = parse_csv(raw_b)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        merged = merge_series(map_a, map_b, on_duplicate=duplicate_policy)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    policy_label = {"average": "среднее A и B", "a": "значение из A", "b": "значение из B"}[
        duplicate_policy
    ]
    op_label = f"объединение ({policy_label})"

    fa, aa = sorted_series(map_a)
    fb, ab = sorted_series(map_b)

    figure = build_figure(
        fa,
        aa,
        fb,
        ab,
        merged.freqs,
        merged.ampl,
        op_label,
        show_a=sa,
        show_b=sb,
        show_result=sr,
    )

    result_csv = result_to_csv(merged.freqs, merged.ampl) if merged.freqs else ""

    return JSONResponse(
        {
            "mode": "merge",
            "duplicate_policy": duplicate_policy,
            "operation_label": op_label,
            "merged_points": len(merged.freqs),
            "duplicate_freqs": merged.duplicate_freqs,
            "only_in_a": merged.only_in_a,
            "only_in_b": merged.only_in_b,
            "figure": figure,
            "result_csv": result_csv,
            "points_a": len(map_a),
            "points_b": len(map_b),
        }
    )
