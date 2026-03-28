from __future__ import annotations

import asyncio
import logging
import time
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api_errors import (
    ApiError,
    api_error_response,
    handle_api_error,
    handle_http_exception,
    handle_unexpected_error,
    handle_validation_error,
)
from app.config import (
    GZIP_MINIMUM_SIZE,
    STATIC_DIR,
    max_csv_rows,
    max_full_plot_points,
    max_request_body_bytes,
    max_plot_points,
    max_upload_bytes,
    trusted_hosts,
    validate_runtime_config,
)
from app.csv_utils import CsvRowsLimitExceeded, parse_csv_upload
from app.logging_utils import configure_logging
from app.services.analysis import build_merge_response_from_maps, build_subtract_response_from_maps
from app.services.result_store import ResultExpired, ResultNotFound, ResultTooLarge, result_store

LOGGER = logging.getLogger("ems.api")


class RequestBodyLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    size = int(content_length)
                except ValueError:
                    size = None
                if size is not None and size > max_request_body_bytes():
                    return api_error_response(
                        request,
                        413,
                        "payload_too_large",
                        (
                            f"Размер запроса превышает лимит {max_request_body_bytes()} байт. "
                            "Уменьшите CSV или увеличьте лимит в настройках."
                        ),
                    )
        return await call_next(request)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        LOGGER.info(
            "request.complete",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else None,
            },
        )
        return response


def _form_bool(v: str | bool) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    return s in ("1", "true", "yes", "on")


def _parse_highlight_threshold(raw: str | float) -> float:
    if isinstance(raw, (int, float)):
        value = float(raw)
    else:
        s = str(raw).strip().replace(",", ".")
        if not s:
            raise ApiError(400, "invalid_parameter", "Порог подсветки должен быть числом 0 или больше.")
        try:
            value = float(s)
        except ValueError as exc:
            raise ApiError(
                400,
                "invalid_parameter",
                "Порог подсветки должен быть числом 0 или больше.",
            ) from exc
    if value < 0:
        raise ApiError(400, "invalid_parameter", "Порог подсветки должен быть числом 0 или больше.")
    return value


def _uploaded_size(upload: UploadFile) -> int | None:
    current = upload.file.tell()
    try:
        upload.file.seek(0, 2)
        size = upload.file.tell()
    except (AttributeError, OSError):
        return None
    finally:
        upload.file.seek(current)
    return size


def _parse_uploaded_csv(file: UploadFile) -> dict[float, float]:
    file_size = _uploaded_size(file)
    if file_size is not None and file_size > max_upload_bytes():
        raise ApiError(
            413,
            "payload_too_large",
            f"Файл {file.filename or 'upload.csv'} превышает лимит {max_upload_bytes()} байт.",
        )
    try:
        return parse_csv_upload(file.file, max_rows=max_csv_rows())
    except UnicodeDecodeError as exc:
        raise ApiError(400, "invalid_utf8", "Файлы должны быть в UTF-8") from exc
    except CsvRowsLimitExceeded as exc:
        raise ApiError(413, "csv_too_large", str(exc)) from exc
    except ValueError as exc:
        raise ApiError(400, "invalid_csv", str(exc)) from exc


def _build_subtract_payload(
    *,
    file_a: UploadFile,
    file_b: UploadFile,
    operation: str,
    show_a: bool,
    show_b: bool,
    show_result: bool,
    highlight_threshold: float,
    full_plot: bool,
) -> dict:
    map_a = _parse_uploaded_csv(file_a)
    map_b = _parse_uploaded_csv(file_b)
    try:
        return build_subtract_response_from_maps(
            map_a,
            map_b,
            operation=operation,
            show_a=show_a,
            show_b=show_b,
            show_result=show_result,
            highlight_threshold=highlight_threshold,
            max_plot_points=0 if full_plot else max_plot_points(),
            max_full_plot_points=max_full_plot_points(),
            full_resolution_plot=full_plot,
        )
    except ResultTooLarge as exc:
        raise ApiError(413, "result_too_large", str(exc)) from exc
    except ValueError as exc:
        raise ApiError(400, "invalid_request", str(exc)) from exc


def _build_merge_payload(
    *,
    file_a: UploadFile,
    file_b: UploadFile,
    duplicate_policy: str,
    show_a: bool,
    show_b: bool,
    show_result: bool,
    full_plot: bool,
) -> dict:
    map_a = _parse_uploaded_csv(file_a)
    map_b = _parse_uploaded_csv(file_b)
    try:
        return build_merge_response_from_maps(
            map_a,
            map_b,
            duplicate_policy=duplicate_policy,
            show_a=show_a,
            show_b=show_b,
            show_result=show_result,
            max_plot_points=0 if full_plot else max_plot_points(),
            max_full_plot_points=max_full_plot_points(),
            full_resolution_plot=full_plot,
        )
    except ResultTooLarge as exc:
        raise ApiError(413, "result_too_large", str(exc)) from exc
    except ValueError as exc:
        raise ApiError(400, "invalid_request", str(exc)) from exc


def create_app() -> FastAPI:
    validate_runtime_config()
    configure_logging()

    app = FastAPI(title="CSV freq/ampl")
    app.add_exception_handler(ApiError, handle_api_error)
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)

    app.add_middleware(GZipMiddleware, minimum_size=GZIP_MINIMUM_SIZE)
    allowed_hosts = trusted_hosts()
    if allowed_hosts:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
    app.add_middleware(RequestBodyLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def index() -> FileResponse:
        index_path = STATIC_DIR / "index.html"
        if not index_path.is_file():
            raise HTTPException(status_code=404, detail="static/index.html not found")
        return FileResponse(index_path)

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        return JSONResponse({"status": "ok"})

    @app.get("/ready")
    async def ready() -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "static_dir_present": STATIC_DIR.is_dir(),
                "result_store": result_store.stats(),
            }
        )

    @app.post("/api/analyze")
    async def analyze(
        file_a: UploadFile = File(...),
        file_b: UploadFile = File(...),
        operation: str = Form("a_minus_b"),
        show_a: str | bool = Form("false"),
        show_b: str | bool = Form("false"),
        show_result: str | bool = Form("true"),
        highlight_threshold: str | float = Form("5"),
        full_resolution_plot: str | bool = Form("false"),
    ) -> JSONResponse:
        if operation not in ("a_minus_b", "b_minus_a"):
            raise ApiError(400, "invalid_parameter", "operation must be a_minus_b or b_minus_a")

        sa, sb, sr = _form_bool(show_a), _form_bool(show_b), _form_bool(show_result)
        if not (sa or sb or sr):
            raise ApiError(
                400,
                "invalid_parameter",
                "Выберите хотя бы один вариант отображения: A, B или результат.",
            )

        payload = await asyncio.to_thread(
            _build_subtract_payload,
            file_a=file_a,
            file_b=file_b,
            operation=operation,
            show_a=sa,
            show_b=sb,
            show_result=sr,
            highlight_threshold=_parse_highlight_threshold(highlight_threshold),
            full_plot=_form_bool(full_resolution_plot),
        )
        return JSONResponse(payload)

    @app.post("/api/merge")
    async def merge(
        file_a: UploadFile = File(...),
        file_b: UploadFile = File(...),
        duplicate_policy: str = Form("average"),
        show_a: str | bool = Form("false"),
        show_b: str | bool = Form("false"),
        show_result: str | bool = Form("true"),
        full_resolution_plot: str | bool = Form("false"),
    ) -> JSONResponse:
        if duplicate_policy not in ("average", "a", "b"):
            raise ApiError(
                400,
                "invalid_parameter",
                "duplicate_policy: average (среднее), a (из A), b (из B)",
            )

        sa, sb, sr = _form_bool(show_a), _form_bool(show_b), _form_bool(show_result)
        if not (sa or sb or sr):
            raise ApiError(
                400,
                "invalid_parameter",
                "Выберите хотя бы один вариант отображения: A, B или объединённый ряд.",
            )

        payload = await asyncio.to_thread(
            _build_merge_payload,
            file_a=file_a,
            file_b=file_b,
            duplicate_policy=duplicate_policy,
            show_a=sa,
            show_b=sb,
            show_result=sr,
            full_plot=_form_bool(full_resolution_plot),
        )
        return JSONResponse(payload)

    @app.get("/api/download/{result_id}")
    async def download_result(result_id: str) -> Response:
        try:
            filename, csv_text = result_store.get_csv(result_id)
        except ResultExpired as exc:
            raise ApiError(410, "result_expired", str(exc)) from exc
        except ResultNotFound as exc:
            raise ApiError(404, "result_not_found", str(exc)) from exc

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        }
        return Response(content=csv_text, media_type="text/csv; charset=utf-8", headers=headers)

    return app


app = create_app()
