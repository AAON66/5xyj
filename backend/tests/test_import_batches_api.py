from __future__ import annotations

import shutil
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import ROOT_DIR, Settings
from backend.app.core.database import create_database_engine, create_session_factory
from backend.app.dependencies import get_db
from backend.app.main import create_app
from backend.app.models import Base


ARTIFACTS_ROOT = ROOT_DIR / ".test_artifacts" / "import_batches_api"


def build_test_client(test_name: str) -> tuple[TestClient, Settings]:
    artifacts_dir = ARTIFACTS_ROOT / test_name
    if artifacts_dir.exists():
        shutil.rmtree(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    database_path = artifacts_dir / "imports.db"
    settings = Settings(
        app_name="导入测试",
        app_version="0.2.0",
        database_url=f"sqlite:///{database_path.as_posix()}",
        upload_dir=str(artifacts_dir / "uploads"),
        samples_dir=str(artifacts_dir / "samples"),
        templates_dir=str(artifacts_dir / "templates"),
        outputs_dir=str(artifacts_dir / "outputs"),
        log_format="plain",
    )

    engine = create_database_engine(settings)
    session_factory = create_session_factory(settings)
    Base.metadata.create_all(engine)

    app = create_app(settings)

    def override_get_db():
        db: Session = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    return client, settings


def test_create_import_batch_persists_files_and_metadata() -> None:
    client, settings = build_test_client("create_batch")

    with client:
        response = client.post(
            "/api/v1/imports",
            data={
                "batch_name": "2026-02 社保批次",
                "regions": '["guangzhou", "hangzhou"]',
                "company_names": '["广分", "杭州聚变"]',
            },
            files=[
                ("files", ("guangzhou.xlsx", b"sheet-a", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
                ("files", ("hangzhou.xls", b"sheet-bb", "application/vnd.ms-excel")),
            ],
        )

    assert response.status_code == 201
    payload = response.json()
    assert payload["success"] is True
    assert payload["message"] == "Import batch created."
    assert payload["data"]["batch_name"] == "2026-02 社保批次"
    assert payload["data"]["status"] == "uploaded"
    assert payload["data"]["file_count"] == 2

    source_files = payload["data"]["source_files"]
    assert [item["region"] for item in source_files] == ["guangzhou", "hangzhou"]
    assert [item["company_name"] for item in source_files] == ["广分", "杭州聚变"]
    assert [item["file_size"] for item in source_files] == [7, 8]

    batch_dir = settings.upload_path / payload["data"]["id"]
    assert batch_dir.exists()
    assert len(list(batch_dir.iterdir())) == 2
    assert all(Path(item["file_path"]).exists() for item in source_files)


def test_list_and_detail_import_batches_return_saved_batch() -> None:
    client, _ = build_test_client("list_detail")

    with client:
        created = client.post(
            "/api/v1/imports",
            files=[("files", ("wuhan.xlsx", b"row-data", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))],
            data={"regions": "wuhan", "company_names": "武汉公司"},
        )
        batch_id = created.json()["data"]["id"]

        list_response = client.get("/api/v1/imports")
        detail_response = client.get(f"/api/v1/imports/{batch_id}")

    assert list_response.status_code == 200
    assert list_response.json()["success"] is True
    assert list_response.json()["data"][0]["id"] == batch_id
    assert list_response.json()["data"][0]["file_count"] == 1

    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["id"] == batch_id
    assert detail_response.json()["data"]["source_files"][0]["region"] == "wuhan"
    assert detail_response.json()["data"]["source_files"][0]["company_name"] == "武汉公司"


def test_create_import_batch_rejects_invalid_extension() -> None:
    client, settings = build_test_client("invalid_extension")

    with client:
        response = client.post(
            "/api/v1/imports",
            files=[("files", ("notes.txt", b"bad", "text/plain"))],
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "http_error"
    assert ".txt" in response.json()["error"]["message"]
    assert not any(settings.upload_path.iterdir())


def test_create_import_batch_rejects_metadata_length_mismatch() -> None:
    client, _ = build_test_client("metadata_mismatch")

    with client:
        response = client.post(
            "/api/v1/imports",
            data={
                "regions": '["guangzhou", "hangzhou"]',
                "company_names": '["only-one", "two", "three"]',
            },
            files=[
                ("files", ("g1.xlsx", b"one", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
                ("files", ("g2.xlsx", b"two", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")),
            ],
        )

    assert response.status_code == 400
    assert "company_names" in response.json()["error"]["message"]