from __future__ import annotations

import json

import plotly.graph_objects as go


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
