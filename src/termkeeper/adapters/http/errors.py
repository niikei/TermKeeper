"""Stable HTTP error contracts and exception mapping."""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from termkeeper.application import NotFoundError, ValidationError


class ErrorDetail(BaseModel):
    location: tuple[str | int, ...]
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: tuple[ErrorDetail, ...] = ()


def register_error_handlers(app: FastAPI) -> None:
    """Map application and request exceptions to stable HTTP responses."""

    @app.exception_handler(RequestValidationError)
    def request_validation_error(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = tuple(
            ErrorDetail(
                location=tuple(error["loc"]),
                code=error["type"],
                message=error["msg"],
            )
            for error in exc.errors()
        )
        return _response(
            ErrorResponse(
                error=type(exc).__name__,
                message="Request validation failed.",
                details=details,
            ),
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    @app.exception_handler(ValidationError)
    def validation_error(_request: Request, exc: ValidationError) -> JSONResponse:
        return _application_error_response(exc, status.HTTP_422_UNPROCESSABLE_CONTENT)

    @app.exception_handler(NotFoundError)
    def not_found_error(_request: Request, exc: NotFoundError) -> JSONResponse:
        return _application_error_response(exc, status.HTTP_404_NOT_FOUND)


def _application_error_response(exc: Exception, status_code: int) -> JSONResponse:
    return _response(
        ErrorResponse(error=type(exc).__name__, message=str(exc)),
        status_code,
    )


def _response(error: ErrorResponse, status_code: int) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error.model_dump(mode="json", exclude_defaults=True),
    )
