from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_AUTH_SECRET_KEY = 'change-this-auth-secret'
DEFAULT_ADMIN_LOGIN_PASSWORD = 'admin123'
DEFAULT_HR_LOGIN_PASSWORD = 'hr123'
UNSAFE_AUTH_SECRET_KEYS = frozenset(
    {
        '',
        DEFAULT_AUTH_SECRET_KEY,
        'change-me',
        'change-this-secret',
        'changeme',
        'default-secret',
        'development-secret',
        'replace-me',
        'replace-this-secret',
        'secret',
        'test-secret',
    }
)
UNSAFE_AUTH_SECRET_KEYS_NORMALIZED = frozenset(value.lower() for value in UNSAFE_AUTH_SECRET_KEYS)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / '.env'),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    app_name: str = '社保表格聚合工具'
    app_version: str = '0.1.0'
    api_v1_prefix: str = '/api/v1'
    backend_cors_origins: list[str] = Field(default_factory=lambda: ['http://localhost:5173', 'http://127.0.0.1:5173'])

    database_url: str = 'sqlite:///./data/app.db'
    database_pool_size: int = 10
    database_max_overflow: int = 20

    upload_dir: str = './data/uploads'
    samples_dir: str = './data/samples'
    templates_dir: str = './data/templates'
    outputs_dir: str = './data/outputs'
    salary_template_path: Optional[str] = None
    final_tool_template_path: Optional[str] = None
    max_upload_size_mb: int = 25

    deepseek_api_key: str = ''
    deepseek_api_base_url: str = 'https://api.deepseek.com/v1'
    deepseek_model: str = 'deepseek-chat'
    enable_llm_fallback: bool = True

    runtime_environment: str = 'local'
    auth_enabled: bool = True
    auth_secret_key: str = DEFAULT_AUTH_SECRET_KEY
    auth_token_expire_minutes: int = 480
    admin_login_username: str = 'admin'
    admin_login_password: str = DEFAULT_ADMIN_LOGIN_PASSWORD
    hr_login_username: str = 'hr'
    hr_login_password: str = DEFAULT_HR_LOGIN_PASSWORD

    log_level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'
    log_format: Literal['plain', 'json'] = 'json'

    @computed_field
    @property
    def root_dir(self) -> Path:
        return ROOT_DIR

    @computed_field
    @property
    def upload_path(self) -> Path:
        return self._resolve_dir(self.upload_dir)

    @computed_field
    @property
    def samples_path(self) -> Path:
        return self._resolve_dir(self.samples_dir)

    @computed_field
    @property
    def templates_path(self) -> Path:
        return self._resolve_dir(self.templates_dir)

    @computed_field
    @property
    def outputs_path(self) -> Path:
        return self._resolve_dir(self.outputs_dir)

    @computed_field
    @property
    def salary_template_file(self) -> Optional[Path]:
        return self._resolve_optional_file(self.salary_template_path)

    @computed_field
    @property
    def final_tool_template_file(self) -> Optional[Path]:
        return self._resolve_optional_file(self.final_tool_template_path)

    @computed_field
    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def normalized_runtime_environment(self) -> str:
        return self.runtime_environment.strip().lower() or 'local'

    @property
    def is_local_runtime(self) -> bool:
        return self.normalized_runtime_environment == 'local'

    @property
    def uses_default_admin_password(self) -> bool:
        return self.admin_login_password == DEFAULT_ADMIN_LOGIN_PASSWORD

    @property
    def uses_default_hr_password(self) -> bool:
        return self.hr_login_password == DEFAULT_HR_LOGIN_PASSWORD

    @property
    def uses_unsafe_auth_secret_key(self) -> bool:
        return self.auth_secret_key.strip().lower() in UNSAFE_AUTH_SECRET_KEYS_NORMALIZED

    def _resolve_dir(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (self.root_dir / path).resolve()

    def _resolve_optional_file(self, value: Optional[str]) -> Optional[Path]:
        if not value:
            return None
        path = Path(value)
        if path.is_absolute():
            return path
        return (self.root_dir / path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()