from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "社保表格聚合工具"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])

    database_url: str = "sqlite:///./data/app.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    upload_dir: str = "./data/uploads"
    samples_dir: str = "./data/samples"
    templates_dir: str = "./data/templates"
    outputs_dir: str = "./data/outputs"
    max_upload_size_mb: int = 25

    deepseek_api_key: str = ""
    deepseek_api_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    enable_llm_fallback: bool = True

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["plain", "json"] = "json"

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
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def _resolve_dir(self, value: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return (self.root_dir / path).resolve()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()