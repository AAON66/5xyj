from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from backend.app.models import Base


EXPECTED_TABLES = {
    "employee_master",
    "export_artifacts",
    "export_jobs",
    "header_mappings",
    "import_batches",
    "match_results",
    "normalized_records",
    "source_files",
    "validation_issues",
}


def test_metadata_registers_expected_tables() -> None:
    assert EXPECTED_TABLES.issubset(Base.metadata.tables.keys())


def test_alembic_upgrade_creates_expected_schema(monkeypatch) -> None:
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    artifacts_dir = Path.cwd() / ".test_artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    database_path = artifacts_dir / "schema_test.db"

    if database_path.exists():
        database_path.unlink()

    database_url = f"sqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)

    assert EXPECTED_TABLES.issubset(set(inspector.get_table_names()))
    assert "alembic_version" in inspector.get_table_names()

    normalized_columns = {column["name"] for column in inspector.get_columns("normalized_records")}
    assert {"person_name", "billing_period", "total_amount", "raw_payload", "source_row_number"}.issubset(
        normalized_columns
    )

    export_artifact_uniques = inspector.get_unique_constraints("export_artifacts")
    assert any(
        set(constraint["column_names"]) == {"export_job_id", "template_type"}
        for constraint in export_artifact_uniques
    )

    engine.dispose()
    if database_path.exists():
        database_path.unlink()