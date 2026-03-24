"""
Centralized exception handlers.

Registered on the FastAPI app in main.py via register_exception_handlers(app).

Covers three cases:
  1. HTTPException      — expected errors raised by route handlers (401, 403, 404, etc.)
  2. RequestValidationError — Pydantic/FastAPI input validation failures (422)
  3. Exception          — any unhandled exception becomes a clean 500 JSON response
                          instead of leaking a Python traceback to the client.

All responses use the same envelope:
  { "success": false, "error": { "code": <int>, "message": <str>, "detail": <any> } }
"""

import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def _error_body(code: int, message: str, detail=None) -> dict:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "detail": detail,
        },
    }


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the app instance."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(
                code=exc.status_code,
                message=exc.detail,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # Flatten Pydantic v2 error list into a readable structure.
        errors = [
            {
                "field": " → ".join(str(loc) for loc in err["loc"]),
                "message": err["msg"],
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body(
                code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="Validation error",
                detail=errors,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="An unexpected error occurred. Please try again later.",
            ),
        )
