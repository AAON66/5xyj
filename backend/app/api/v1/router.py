from fastapi import APIRouter

from backend.app.api.v1.imports import router as imports_router
from backend.app.api.v1.system import router as system_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(imports_router)