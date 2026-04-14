from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.models.system_setting import SystemSetting


FEISHU_SYNC_ENABLED_KEY = "feishu_sync_enabled"
FEISHU_OAUTH_ENABLED_KEY = "feishu_oauth_enabled"
FEISHU_APP_ID_KEY = "feishu_app_id"
FEISHU_APP_SECRET_KEY = "feishu_app_secret"


@dataclass(frozen=True)
class EffectiveFeishuSettings:
    feishu_sync_enabled: bool
    feishu_oauth_enabled: bool
    feishu_app_id: str
    feishu_app_secret: str
    credentials_configured: bool


def get_setting(db: Session, key: str) -> Optional[str]:
    record = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    return record.value if record is not None else None


def set_setting(db: Session, key: str, value: str | bool | None) -> Optional[SystemSetting]:
    record = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if value is None:
        if record is not None:
            db.delete(record)
        return None

    serialized = _serialize_setting_value(value)
    if record is None:
        record = SystemSetting(key=key, value=serialized)
        db.add(record)
    else:
        record.value = serialized
    return record


def get_effective_feishu_settings(db: Session, env_settings: Settings) -> EffectiveFeishuSettings:
    feishu_sync_enabled = _resolve_bool_setting(
        db,
        FEISHU_SYNC_ENABLED_KEY,
        env_settings.feishu_sync_enabled,
    )
    feishu_oauth_enabled = _resolve_bool_setting(
        db,
        FEISHU_OAUTH_ENABLED_KEY,
        env_settings.feishu_oauth_enabled,
    )
    feishu_app_id = _resolve_text_setting(db, FEISHU_APP_ID_KEY, env_settings.feishu_app_id)
    feishu_app_secret = _resolve_text_setting(db, FEISHU_APP_SECRET_KEY, env_settings.feishu_app_secret)
    return EffectiveFeishuSettings(
        feishu_sync_enabled=feishu_sync_enabled,
        feishu_oauth_enabled=feishu_oauth_enabled,
        feishu_app_id=feishu_app_id,
        feishu_app_secret=feishu_app_secret,
        credentials_configured=bool(feishu_app_id and feishu_app_secret),
    )


def mask_app_id(app_id: str) -> Optional[str]:
    normalized = app_id.strip()
    if not normalized:
        return None
    if len(normalized) <= 6:
        return "*" * len(normalized)
    return f"{normalized[:4]}{'*' * (len(normalized) - 6)}{normalized[-2:]}"


def _resolve_bool_setting(db: Session, key: str, default: bool) -> bool:
    raw_value = get_setting(db, key)
    if raw_value is None:
        return default
    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _resolve_text_setting(db: Session, key: str, default: str) -> str:
    raw_value = get_setting(db, key)
    if raw_value is None:
        return default
    return raw_value.strip()


def _serialize_setting_value(value: str | bool) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()
