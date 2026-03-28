from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

LOGGER = logging.getLogger("ems.api")


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        details: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers or {}


def request_id_from_request(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def build_error_payload(
    request: Request,
    code: str,
    message: str,
    *,
    details: Any | None = None,
) -> dict[str, Any]:
    request_id = request_id_from_request(request)
    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if request_id:
        error["request_id"] = request_id
    if details is not None:
        error["details"] = details

    payload: dict[str, Any] = {
        "detail": message,
        "error": error,
    }
    if request_id:
        payload["request_id"] = request_id
    return payload


def api_error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    *,
    details: Any | None = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=build_error_payload(request, code, message, details=details),
        headers=headers,
    )


async def handle_api_error(request: Request, exc: ApiError) -> JSONResponse:
    return api_error_response(
        request,
        exc.status_code,
        exc.code,
        exc.message,
        details=exc.details,
        headers=exc.headers,
    )


async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    code_map = {
        400: "bad_request",
        404: "not_found",
        410: "gone",
        413: "payload_too_large",
    }
    message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    details = None if isinstance(exc.detail, str) else exc.detail
    return api_error_response(
        request,
        exc.status_code,
        code_map.get(exc.status_code, "http_error"),
        message,
        details=details,
        headers=exc.headers,
    )


async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    return api_error_response(
        request,
        422,
        "validation_error",
        "Некорректный запрос.",
        details=exc.errors(),
    )


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    LOGGER.exception(
        "Unhandled application error",
        extra={"request_id": request_id_from_request(request), "path": request.url.path},
    )
    return api_error_response(
        request,
        500,
        "internal_error",
        "Внутренняя ошибка сервера.",
    )
