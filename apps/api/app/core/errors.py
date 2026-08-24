from collections.abc import Mapping
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException


class DomainError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        *,
        fields: Mapping[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.fields = dict(fields) if fields is not None else None
        super().__init__(message)


def _is_v2(request: Request) -> bool:
    return request.url.path == "/api/v2" or request.url.path.startswith("/api/v2/")


def _correlation_id(request: Request) -> str:
    return getattr(
        request.state,
        "correlation_id",
        getattr(request.state, "request_id", "unavailable"),
    )


def _v2_error(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    fields: Mapping[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "correlation_id": _correlation_id(request),
            "fields": dict(fields) if fields is not None else None,
        },
    )


def _http_code(status_code: int) -> str:
    try:
        return HTTPStatus(status_code).name
    except ValueError:
        return "HTTP_ERROR"


def _http_message(exc: StarletteHTTPException) -> str:
    if isinstance(exc.detail, str):
        return exc.detail
    try:
        return HTTPStatus(exc.status_code).phrase
    except ValueError:
        return "HTTP request failed"


def _validation_fields(exc: RequestValidationError) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", ())) or "request"
        fields.setdefault(location, []).append(str(error.get("msg", "Invalid value")))
    return fields


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        if _is_v2(request):
            return _v2_error(
                request,
                status_code=exc.status_code,
                code=exc.code,
                message=exc.message,
                fields=exc.fields,
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> Response:
        if not _is_v2(request):
            return await http_exception_handler(request, exc)
        return _v2_error(
            request,
            status_code=exc.status_code,
            code=_http_code(exc.status_code),
            message=_http_message(exc),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> Response:
        if not _is_v2(request):
            return await request_validation_exception_handler(request, exc)
        return _v2_error(
            request,
            status_code=422,
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            fields=_validation_fields(exc),
        )
