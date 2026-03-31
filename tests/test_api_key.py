"""Tests for API Key model, service, and CRUD endpoints."""
from __future__ import annotations

import hashlib

import pytest
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.services.user_service import hash_password


# ---------------------------------------------------------------------------
# Service-level unit tests (Task 1)
# ---------------------------------------------------------------------------


class TestGenerateApiKey:
    """Test 1: generate_api_key returns (raw_key, key_prefix, key_hash)."""

    def test_returns_tuple_of_three(self):
        from backend.app.services.api_key_service import generate_api_key

        raw_key, key_prefix, key_hash = generate_api_key()
        assert isinstance(raw_key, str)
        assert isinstance(key_prefix, str)
        assert isinstance(key_hash, str)

    def test_prefix_is_first_8_chars(self):
        from backend.app.services.api_key_service import generate_api_key

        raw_key, key_prefix, _ = generate_api_key()
        assert key_prefix == raw_key[:8]

    def test_hash_is_sha256_of_raw_key(self):
        from backend.app.services.api_key_service import generate_api_key

        raw_key, _, key_hash = generate_api_key()
        expected_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        assert key_hash == expected_hash


class TestCreateApiKey:
    """Test 2 & 3: create_api_key succeeds and enforces 5-key limit."""

    def _make_admin(self, db_session: Session) -> User:
        admin = User(
            username="apikeyadmin",
            hashed_password=hash_password("pass"),
            role="admin",
            display_name="Admin",
            is_active=True,
            must_change_password=False,
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        return admin

    def test_create_returns_record_and_raw_key(self, db_session: Session):
        from backend.app.services.api_key_service import create_api_key

        admin = self._make_admin(db_session)
        record, raw_key = create_api_key(
            db_session,
            name="Test Key",
            owner_id=admin.id,
            owner_username=admin.username,
            owner_role=admin.role,
        )
        assert record.name == "Test Key"
        assert record.owner_id == admin.id
        assert record.key_prefix == raw_key[:8]
        assert record.key_hash == hashlib.sha256(raw_key.encode()).hexdigest()
        assert record.is_active is True

    def test_limit_exceeded_error(self, db_session: Session):
        from backend.app.services.api_key_service import (
            ApiKeyLimitExceededError,
            create_api_key,
        )

        admin = self._make_admin(db_session)
        for i in range(5):
            create_api_key(db_session, name=f"Key {i}", owner_id=admin.id,
                           owner_username=admin.username, owner_role=admin.role)

        with pytest.raises(ApiKeyLimitExceededError):
            create_api_key(db_session, name="Key 6", owner_id=admin.id,
                           owner_username=admin.username, owner_role=admin.role)


class TestLookupApiKey:
    """Test 4, 5, 6: lookup_api_key with valid, invalid, and revoked keys."""

    def _setup(self, db_session: Session):
        from backend.app.services.api_key_service import create_api_key

        admin = User(
            username="lookupadmin",
            hashed_password=hash_password("pass"),
            role="admin",
            display_name="Admin",
            is_active=True,
            must_change_password=False,
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
        record, raw_key = create_api_key(
            db_session, name="Lookup Key", owner_id=admin.id,
            owner_username=admin.username, owner_role=admin.role,
        )
        return admin, record, raw_key

    def test_valid_key_returns_record(self, db_session: Session):
        from backend.app.services.api_key_service import lookup_api_key

        _, record, raw_key = self._setup(db_session)
        found = lookup_api_key(db_session, raw_key)
        assert found is not None
        assert found.id == record.id
        assert found.last_used_at is not None

    def test_invalid_key_returns_none(self, db_session: Session):
        from backend.app.services.api_key_service import lookup_api_key

        self._setup(db_session)
        found = lookup_api_key(db_session, "totally-invalid-key")
        assert found is None

    def test_revoked_key_returns_none(self, db_session: Session):
        from backend.app.services.api_key_service import lookup_api_key, revoke_api_key

        _, record, raw_key = self._setup(db_session)
        revoke_api_key(db_session, record.id)
        found = lookup_api_key(db_session, raw_key)
        assert found is None


class TestRevokeApiKey:
    """Test 7: revoke_api_key sets is_active=False."""

    def test_revoke_sets_inactive(self, db_session: Session):
        from backend.app.services.api_key_service import create_api_key, revoke_api_key

        admin = User(
            username="revokeadmin",
            hashed_password=hash_password("pass"),
            role="admin",
            display_name="Admin",
            is_active=True,
            must_change_password=False,
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)

        record, _ = create_api_key(
            db_session, name="Revoke Key", owner_id=admin.id,
            owner_username=admin.username, owner_role=admin.role,
        )
        assert record.is_active is True

        revoked = revoke_api_key(db_session, record.id)
        assert revoked is not None
        assert revoked.is_active is False


class TestListApiKeys:
    """Test 8: list_api_keys returns only keys for specified owner_id."""

    def test_list_filters_by_owner(self, db_session: Session):
        from backend.app.services.api_key_service import create_api_key, list_api_keys

        admin1 = User(
            username="listadmin1", hashed_password=hash_password("p"),
            role="admin", display_name="A1", is_active=True, must_change_password=False,
        )
        admin2 = User(
            username="listadmin2", hashed_password=hash_password("p"),
            role="admin", display_name="A2", is_active=True, must_change_password=False,
        )
        db_session.add_all([admin1, admin2])
        db_session.commit()
        db_session.refresh(admin1)
        db_session.refresh(admin2)

        create_api_key(db_session, name="A1-K1", owner_id=admin1.id,
                       owner_username=admin1.username, owner_role=admin1.role)
        create_api_key(db_session, name="A1-K2", owner_id=admin1.id,
                       owner_username=admin1.username, owner_role=admin1.role)
        create_api_key(db_session, name="A2-K1", owner_id=admin2.id,
                       owner_username=admin2.username, owner_role=admin2.role)

        keys_a1 = list_api_keys(db_session, owner_id=admin1.id)
        assert len(keys_a1) == 2

        keys_a2 = list_api_keys(db_session, owner_id=admin2.id)
        assert len(keys_a2) == 1

        all_keys = list_api_keys(db_session)
        assert len(all_keys) == 3
