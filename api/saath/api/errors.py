"""RFC 7807 Problem Details error handler."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class ProblemDetailException(Exception):
    def __init__(
        self,
        status_code: int,
        title: str,
        detail: str,
        type_uri: str = "about:blank",
        invalid_params: list[dict[str, Any]] | None = None,
    ) -> None:
        self.status_code = status_code
        self.title = title
        self.detail = detail
        self.type_uri = type_uri
        self.invalid_params = invalid_params or []
        super().__init__(detail)


async def problem_exception_handler(request: Request, exc: ProblemDetailException) -> JSONResponse:
    content: dict[str, Any] = {
        "type": exc.type_uri,
        "title": exc.title,
        "status": exc.status_code,
        "detail": exc.detail,
        "instance": str(request.url),
    }
    if exc.invalid_params:
        content["invalid_params"] = exc.invalid_params
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        media_type="application/problem+json",
    )
