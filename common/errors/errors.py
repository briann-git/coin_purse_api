# common/errors.py
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from schemas.errors import ErrorResponse


def _map_status_to_code(status_code: int) -> str:
    if status_code == 404:
        return "not_found"
    if status_code == 401:
        return "unauthorized"
    if status_code == 403:
        return "forbidden"
    if status_code == 409:
        return "conflict"
    if status_code == 422:
        return "validation_error"
    if 400 <= status_code < 500:
        return "bad_request"
    return "server_error"


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_request: Request, exc: StarletteHTTPException):
        code = getattr(exc, "detail_code", None) or _map_status_to_code(exc.status_code)
        payload = ErrorResponse(
            error=code,
            message=str(exc.detail) if exc.detail else "Request failed",
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=payload.model_dump(mode="json"),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_request: Request, exc: RequestValidationError):
        payload = ErrorResponse(
            error="validation_error",
            message="Request validation failed",
            details=exc.errors(),
        )
        return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_request: Request, _exc: Exception):
        payload = ErrorResponse(
            error="server_error",
            message="An unexpected error occurred",
        )
        return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))
