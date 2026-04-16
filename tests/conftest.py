from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.models.base import Base
from backend.app.models.employee_master import EmployeeMaster
from backend.app.models.user import User
from backend.app.services.user_service import hash_password

TEST_SECRET_KEY = "test-secret-key-for-unit-tests-only"
TEST_DB_URL = "sqlite://"  # in-memory


@pytest.fixture()
def db_engine():
    engine = create_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def test_client(db_session: Session):
    """FastAPI TestClient with auth_enabled=True and test DB session."""
    from backend.app.core.config import Settings
    from backend.app.main import create_app
    from backend.app.dependencies import get_db

    settings = Settings(
        auth_enabled=True,
        auth_secret_key=TEST_SECRET_KEY,
        auth_token_expire_minutes=480,
        employee_token_expire_minutes=30,
        database_url=TEST_DB_URL,
    )

    app = create_app(settings)

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture()
def test_client_auth_disabled(db_session: Session):
    """FastAPI TestClient with auth_enabled=False."""
    from backend.app.core.config import Settings
    from backend.app.main import create_app
    from backend.app.dependencies import get_db

    settings = Settings(
        auth_enabled=False,
        auth_secret_key=TEST_SECRET_KEY,
        database_url=TEST_DB_URL,
    )

    app = create_app(settings)

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture()
def seed_test_admin(db_session: Session) -> User:
    admin = User(
        username="testadmin",
        hashed_password=hash_password("testpass123"),
        role="admin",
        display_name="Test Admin",
        is_active=True,
        must_change_password=False,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture()
def seed_test_hr(db_session: Session) -> User:
    hr = User(
        username="testhr",
        hashed_password=hash_password("hrpass123"),
        role="hr",
        display_name="Test HR",
        is_active=True,
        must_change_password=False,
    )
    db_session.add(hr)
    db_session.commit()
    db_session.refresh(hr)
    return hr


@pytest.fixture()
def seed_disabled_admin(db_session: Session) -> User:
    admin = User(
        username="disabledadmin",
        hashed_password=hash_password("testpass123"),
        role="admin",
        display_name="Disabled Admin",
        is_active=False,
        must_change_password=False,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture()
def test_client_feishu(db_session: Session):
    """FastAPI TestClient with feishu_sync_enabled=True and test DB session."""
    from backend.app.core.config import Settings
    from backend.app.main import create_app
    from backend.app.dependencies import get_db

    settings = Settings(
        auth_enabled=True,
        auth_secret_key=TEST_SECRET_KEY,
        auth_token_expire_minutes=480,
        database_url=TEST_DB_URL,
        feishu_sync_enabled=True,
        feishu_oauth_enabled=True,
        feishu_app_id="test_app_id",
        feishu_app_secret="test_app_secret",
    )
    app = create_app(settings)

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture()
def seed_test_employee(db_session: Session) -> EmployeeMaster:
    emp = EmployeeMaster(
        employee_id="EMP001",
        person_name="Zhang San",
        id_number="110101199001011234",
        company_name="Test Company",
        active=True,
    )
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    return emp


@pytest.fixture()
def seed_employee_master(db_session: Session) -> EmployeeMaster:
    """Seed a single EmployeeMaster for OAuth auto-bind tests."""
    emp = EmployeeMaster(
        employee_id="EMP1001",
        person_name="Test User",
        id_number="110101199001011111",
        company_name="Test Company",
        department="Engineering",
        active=True,
    )
    db_session.add(emp)
    db_session.commit()
    db_session.refresh(emp)
    return emp


@pytest.fixture()
def seed_multiple_employees_same_name(db_session: Session) -> list:
    """Seed two EmployeeMasters with the same name for pending_candidates tests."""
    emp1 = EmployeeMaster(
        employee_id="EMP2001",
        person_name="Duplicate Name",
        id_number="110101199002021111",
        company_name="Company A",
        department="Sales",
        active=True,
    )
    emp2 = EmployeeMaster(
        employee_id="EMP2002",
        person_name="Duplicate Name",
        id_number="110101199003031111",
        company_name="Company B",
        department="Marketing",
        active=True,
    )
    db_session.add_all([emp1, emp2])
    db_session.commit()
    db_session.refresh(emp1)
    db_session.refresh(emp2)
    return [emp1, emp2]
