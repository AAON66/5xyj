from __future__ import annotations

from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(data: Any, message: str = "ok", status_code: int = 200) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": jsonable_encoder(data),
        },
    )


def error_response(code: str, message: str, status_code: int, details: Any = None) -> JSONResponse:
    payload: dict[str, Any] = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
        },
    }
    if details is not None:
        payload["error"]["details"] = jsonable_encoder(details)
    return JSONResponse(status_code=status_code, content=payload)