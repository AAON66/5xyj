from fastapi import APIRouter, Depends

from backend.app.api.v1.aggregate import router as aggregate_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.compare import router as compare_router
from backend.app.api.v1.dashboard import router as dashboard_router
from backend.app.api.v1.employees import router as employees_router
from backend.app.api.v1.imports import router as imports_router
from backend.app.api.v1.mappings import router as mappings_router
from backend.app.api.v1.system import router as system_router
from backend.app.dependencies import require_authenticated_user

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(system_router)
api_router.include_router(aggregate_router, dependencies=[Depends(require_authenticated_user)])
api_router.include_router(compare_router, dependencies=[Depends(require_authenticated_user)])
api_router.include_router(dashboard_router, dependencies=[Depends(require_authenticated_user)])
api_router.include_router(imports_router, dependencies=[Depends(require_authenticated_user)])
api_router.include_router(mappings_router, dependencies=[Depends(require_authenticated_user)])
api_router.include_router(employees_router)
