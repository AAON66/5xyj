from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.api.v1.responses import error_response, success_response
from backend.app.api.v1.router import api_router
from backend.app.bootstrap import bootstrap_application
from backend.app.core.config import Settings, get_settings
from backend.app.core.upload_guard import UploadGuardMiddleware


def create_lifespan(runtime_settings: Settings):
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        settings = bootstrap_application(runtime_settings)
        app.state.settings = settings
        yield

    return lifespan


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException):
        code = "http_error"
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "not_found"
        elif exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            code = "method_not_allowed"
        return error_response(code, str(exc.detail), exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(request: Request, exc: RequestValidationError):
        return error_response(
            "validation_error",
            "Request validation failed.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=exc.errors(),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception):
        return error_response(
            "internal_server_error",
            "An unexpected server error occurred.",
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        )



def create_app(settings: Optional[Settings] = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    app = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.app_version,
        summary="社保表格聚合工具 API",
        lifespan=create_lifespan(runtime_settings),
    )

    app.state.settings = runtime_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(UploadGuardMiddleware, max_upload_size_bytes=runtime_settings.max_upload_size_bytes)

    register_exception_handlers(app)
    app.include_router(api_router, prefix=runtime_settings.api_v1_prefix)

    @app.get("/health", tags=["system"])
    async def healthcheck(request: Request):
        active_settings: Settings = request.app.state.settings
        return success_response(
            {
                "status": "ok",
                "app_name": active_settings.app_name,
                "version": active_settings.app_version,
            }
        )

    return app


app = create_app()
