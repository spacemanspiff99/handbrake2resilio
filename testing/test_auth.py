"""Unit tests for api-gateway/auth.py — authentication and authorization."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api-gateway"))


def _make_config(db_path: str):
    """Build a minimal Config object pointing at *db_path*."""
    from shared.config import (
        Config,
        MonitoringConfig,
        NetworkConfig,
        ResourceConfig,
        SecurityConfig,
        StorageConfig,
        VideoConfig,
    )

    return Config(
        security=SecurityConfig(
            jwt_secret_key="test-secret-key-32chars-minimum!!",
            bcrypt_rounds=10,
        ),
        resources=ResourceConfig(),
        storage=StorageConfig(
            database_path=db_path,
            logs_directory="/tmp/test_logs",
            temp_directory="/tmp/test_temp",
            upload_directory="/tmp/test_uploads",
            backup_directory="/tmp/test_backups",
        ),
        network=NetworkConfig(),
        video=VideoConfig(),
        monitoring=MonitoringConfig(),
        environment="development",
    )


@pytest.fixture
def auth_service(tmp_path):
    """AuthService instance backed by a fresh temp database."""
    from auth import AuthService  # type: ignore[import]

    db_path = str(tmp_path / "auth_test.db")
    cfg = _make_config(db_path)
    return AuthService(cfg)


class TestAuthDatabase:
    """Tests for database initialization via AuthService.__init__."""

    def test_db_init_creates_tables(self, tmp_path) -> None:
        """Initializing AuthService creates users, sessions, and tabs tables."""
        import sqlite3
        from auth import AuthService  # type: ignore[import]

        db_path = str(tmp_path / "init_test.db")
        cfg = _make_config(db_path)
        AuthService(cfg)

        conn = sqlite3.connect(db_path)
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        conn.close()
        assert "users" in tables
        assert "sessions" in tables
        assert "tabs" in tables

    def test_default_admin_created(self, auth_service) -> None:
        """Default admin user is created on first init."""
        user = auth_service.authenticate_user("admin", "admin123")
        assert user is not None
        assert user["username"] == "admin"
        assert user["role"] == "admin"


class TestUserRegistration:
    """Tests for user registration."""

    def test_register_new_user(self, auth_service) -> None:
        """Registering a new user returns True."""
        result = auth_service.register_user("newuser", "password123")
        assert result is True

    def test_register_duplicate_returns_false(self, auth_service) -> None:
        """Registering a duplicate username returns False."""
        auth_service.register_user("dupuser", "password123")
        result = auth_service.register_user("dupuser", "otherpass")
        assert result is False

    def test_register_short_username_returns_false(self, auth_service) -> None:
        """Username shorter than 3 chars returns False."""
        result = auth_service.register_user("ab", "password123")
        assert result is False

    def test_register_short_password_returns_false(self, auth_service) -> None:
        """Password shorter than 6 chars returns False."""
        result = auth_service.register_user("validuser", "abc")
        assert result is False

    def test_registered_user_can_authenticate(self, auth_service) -> None:
        """A newly registered user can authenticate immediately."""
        auth_service.register_user("testlogin", "mypassword")
        user = auth_service.authenticate_user("testlogin", "mypassword")
        assert user is not None
        assert user["username"] == "testlogin"


class TestAuthentication:
    """Tests for user authentication."""

    def test_authenticate_valid_credentials(self, auth_service) -> None:
        """Valid credentials return a user info dict."""
        user = auth_service.authenticate_user("admin", "admin123")
        assert user is not None
        assert "id" in user
        assert "username" in user
        assert "role" in user

    def test_authenticate_invalid_password(self, auth_service) -> None:
        """Wrong password returns None."""
        user = auth_service.authenticate_user("admin", "wrongpassword")
        assert user is None

    def test_authenticate_nonexistent_user(self, auth_service) -> None:
        """Non-existent username returns None."""
        user = auth_service.authenticate_user("nobody", "password")
        assert user is None

    def test_authenticate_inactive_user(self, auth_service, tmp_path) -> None:
        """Inactive user cannot authenticate."""
        import sqlite3

        auth_service.register_user("inactiveuser", "password123")
        # Deactivate the user directly in the DB
        conn = sqlite3.connect(auth_service.db_path)
        conn.execute(
            "UPDATE users SET is_active = 0 WHERE username = ?", ("inactiveuser",)
        )
        conn.commit()
        conn.close()

        user = auth_service.authenticate_user("inactiveuser", "password123")
        assert user is None


class TestTokens:
    """Tests for JWT token creation and verification."""

    def test_create_token_returns_string(self, auth_service) -> None:
        """create_token() returns a non-empty string."""
        user_info = auth_service.authenticate_user("admin", "admin123")
        token = auth_service.create_token(user_info)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_returns_user_info(self, auth_service) -> None:
        """verify_token() with a valid token returns user info dict."""
        user_info = auth_service.authenticate_user("admin", "admin123")
        token = auth_service.create_token(user_info)
        verified = auth_service.verify_token(token)
        assert verified is not None
        assert verified["username"] == "admin"

    def test_verify_invalid_token_returns_none(self, auth_service) -> None:
        """verify_token() with a garbage token returns None."""
        result = auth_service.verify_token("not.a.valid.token")
        assert result is None

    def test_verify_tampered_token_returns_none(self, auth_service) -> None:
        """verify_token() with a tampered token returns None."""
        user_info = auth_service.authenticate_user("admin", "admin123")
        token = auth_service.create_token(user_info)
        # Flip the last character to corrupt the signature
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        result = auth_service.verify_token(tampered)
        assert result is None


class TestTabCrud:
    """Tests for tab CRUD operations on AuthService."""

    def test_create_tab(self, auth_service) -> None:
        """create_tab() returns a non-None tab ID."""
        tab_id = auth_service.create_tab(
            name="My Tab",
            source_path="/in",
            destination_path="/out",
            source_type="tv",
            profile="standard",
            user_id=None,
        )
        assert tab_id is not None

    def test_get_tabs_returns_list(self, auth_service) -> None:
        """get_tabs() returns a list."""
        tabs = auth_service.get_tabs()
        assert isinstance(tabs, list)

    def test_created_tab_appears_in_get_tabs(self, auth_service) -> None:
        """A tab created via create_tab() appears in get_tabs()."""
        auth_service.create_tab(
            name="Visible Tab",
            source_path="/src",
            destination_path="/dst",
            source_type="movie",
            profile="high",
            user_id=None,
        )
        tabs = auth_service.get_tabs()
        names = [t["name"] for t in tabs]
        assert "Visible Tab" in names

    def test_update_tab(self, auth_service) -> None:
        """update_tab() returns True and persists the change."""
        tab_id = auth_service.create_tab(
            name="Original",
            source_path="/src",
            destination_path="/dst",
            source_type="tv",
            profile="standard",
            user_id=None,
        )
        result = auth_service.update_tab(tab_id, {"name": "Updated"})
        assert result is True

        tabs = auth_service.get_tabs()
        updated = next((t for t in tabs if t["id"] == tab_id), None)
        assert updated is not None
        assert updated["name"] == "Updated"

    def test_delete_tab(self, auth_service) -> None:
        """delete_tab() returns True and removes the tab."""
        tab_id = auth_service.create_tab(
            name="ToDelete",
            source_path="/src",
            destination_path="/dst",
            source_type="tv",
            profile="standard",
            user_id=None,
        )
        result = auth_service.delete_tab(tab_id)
        assert result is True

        tabs = auth_service.get_tabs()
        ids = [t["id"] for t in tabs]
        assert tab_id not in ids
