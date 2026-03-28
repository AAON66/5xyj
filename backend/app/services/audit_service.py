from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog


def log_audit(
    db: Session,
    action: str,
    actor_username: str,
    actor_role: str,
    ip_address: Optional[str] = None,
    detail: Optional[dict] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    success: bool = True,
) -> None:
    """Write an audit log entry.

    Detail field security constraints:
    - Prohibit writing: password plaintext/hash, JWT tokens, full ID numbers
    - Only record descriptive information (username, filename, record count, etc.)
    Callers are responsible for ensuring detail content does not contain sensitive data.
    """
    entry = AuditLog(
        action=action,
        actor_username=actor_username,
        actor_role=actor_role,
        ip_address=ip_address,
        detail=json.dumps(detail, ensure_ascii=False) if detail else None,
        resource_type=resource_type,
        resource_id=resource_id,
        success=success,
    )
    db.add(entry)
    db.commit()
