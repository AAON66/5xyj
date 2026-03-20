from __future__ import annotations

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class UploadGuardMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size_bytes: int) -> None:
        super().__init__(app)
        self.max_upload_size_bytes = max_upload_size_bytes

    async def dispatch(self, request: Request, call_next) -> Response:
        content_type = request.headers.get("content-type", "")
        content_length = request.headers.get("content-length")

        if "multipart/form-data" in content_type and content_length:
            try:
                if int(content_length) > self.max_upload_size_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "success": False,
                            "error": {
                                "code": "payload_too_large",
                                "message": f"Upload exceeds the configured {self.max_upload_size_bytes} byte limit.",
                            },
                        },
                    )
            except ValueError:
                pass

        return await call_next(request)