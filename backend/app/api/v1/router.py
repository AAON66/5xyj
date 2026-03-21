from fastapi import APIRouter

from backend.app.api.v1.dashboard import router as dashboard_router
from backend.app.api.v1.employees import router as employees_router
from backend.app.api.v1.imports import router as imports_router
from backend.app.api.v1.mappings import router as mappings_router
from backend.app.api.v1.system import router as system_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(dashboard_router)
api_router.include_router(imports_router)
api_router.include_router(mappings_router)
api_router.include_router(employees_router)
