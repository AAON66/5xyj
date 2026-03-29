from fastapi import APIRouter, Depends

from backend.app.api.v1.aggregate import router as aggregate_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.compare import router as compare_router
from backend.app.api.v1.dashboard import router as dashboard_router
from backend.app.api.v1.employee_portal import router as employee_portal_router
from backend.app.api.v1.employees import router as employees_router
from backend.app.api.v1.imports import router as imports_router
from backend.app.api.v1.mappings import router as mappings_router
from backend.app.api.v1.system import router as system_router
from backend.app.api.v1.users import router as users_router
from backend.app.dependencies import require_role

api_router = APIRouter()

# Public -- no auth required
api_router.include_router(auth_router)
api_router.include_router(system_router)

# Admin only (D-08: admin manages user accounts)
api_router.include_router(users_router, dependencies=[Depends(require_role("admin"))])

# Admin only (D-06: only admin can view audit logs)
api_router.include_router(audit_router, dependencies=[Depends(require_role("admin"))])

# Admin + HR (D-14: HR has all business functions)
api_router.include_router(aggregate_router, dependencies=[Depends(require_role("admin", "hr"))])
api_router.include_router(compare_router, dependencies=[Depends(require_role("admin", "hr"))])
api_router.include_router(dashboard_router, dependencies=[Depends(require_role("admin", "hr"))])
api_router.include_router(imports_router, dependencies=[Depends(require_role("admin", "hr"))])
api_router.include_router(mappings_router, dependencies=[Depends(require_role("admin", "hr"))])
api_router.include_router(employees_router, dependencies=[Depends(require_role("admin", "hr"))])

# Employee portal -- endpoint-level auth (employee role token required)
api_router.include_router(employee_portal_router)
