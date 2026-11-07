import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import AppError

logger = logging.getLogger("taskhub")


def request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "not-assigned")


def error_body(request: Request, code: str, message: str, details=None) -> dict:
    return {
        "code": code,
        "message": message,
        "error": {"details": details or {}},
        "request_id": request_id(request),
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(request, exc.code, exc.message, exc.details),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_body(
                request, "VALIDATION_ERROR", "Request validation failed", jsonable_encoder(exc.errors())
            ),
        )

    @app.exception_handler(HTTPException)
    async def handle_http_error(request: Request, exc: HTTPException):
        message = exc.detail if isinstance(exc.detail, str) else "HTTP request failed"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                request, f"HTTP_{exc.status_code}", message, exc.detail if not isinstance(exc.detail, str) else {}
            ),
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def handle_unknown_error(request: Request, exc: Exception):
        logger.exception("Unhandled error request_id=%s", request_id(request))
        return JSONResponse(
            status_code=500,
            content=error_body(request, "INTERNAL_ERROR", "Internal server error"),
        )
