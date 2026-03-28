from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from app.config import GZIP_MINIMUM_SIZE, STATIC_DIR, max_plot_points
from app.services.analysis import build_merge_response, build_subtract_response


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


def create_app() -> FastAPI:
    app = FastAPI(title="CSV freq/ampl")
    app.add_middleware(GZipMiddleware, minimum_size=GZIP_MINIMUM_SIZE)

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        index_path = STATIC_DIR / "index.html"
        if not index_path.is_file():
            raise HTTPException(status_code=404, detail="static/index.html not found")
        return FileResponse(index_path)

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
            payload = build_subtract_response(
                raw_a,
                raw_b,
                operation=operation,
                show_a=sa,
                show_b=sb,
                show_result=sr,
                highlight_threshold=_parse_highlight_threshold(highlight_threshold),
                max_plot_points=max_plot_points(),
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        return JSONResponse(payload)

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
            payload = build_merge_response(
                raw_a,
                raw_b,
                duplicate_policy=duplicate_policy,
                show_a=sa,
                show_b=sb,
                show_result=sr,
                max_plot_points=max_plot_points(),
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

        return JSONResponse(payload)

    return app


app = create_app()
