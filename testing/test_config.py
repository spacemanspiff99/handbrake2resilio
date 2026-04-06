"""Unit tests for shared/config.py — configuration loading and validation."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _build_config(db_path: str, **overrides):
    """Build a Config object with sensible test defaults."""
    from shared.config import (
        Config,
        MonitoringConfig,
        NetworkConfig,
        ResourceConfig,
        SecurityConfig,
        StorageConfig,
        VideoConfig,
    )

    security = SecurityConfig(
        jwt_secret_key=overrides.get(
            "jwt_secret_key", "test-secret-key-32chars-minimum!!"
        ),
        bcrypt_rounds=overrides.get("bcrypt_rounds", 10),
    )
    resources = ResourceConfig(
        max_concurrent_jobs=overrides.get("max_concurrent_jobs", 2)
    )
    storage = StorageConfig(
        database_path=db_path,
        logs_directory="/tmp/test_logs",
        temp_directory="/tmp/test_temp",
        upload_directory="/tmp/test_uploads",
        backup_directory="/tmp/test_backups",
    )
    network = NetworkConfig()
    video = VideoConfig()
    monitoring = MonitoringConfig()
    return Config(
        security=security,
        resources=resources,
        storage=storage,
        network=network,
        video=video,
        monitoring=monitoring,
        environment="development",
    )


class TestConfigLoading:
    """Tests for configuration loading and defaults."""

    def test_default_loading(self, tmp_path) -> None:
        """Config can be constructed with sensible defaults."""
        cfg = _build_config(str(tmp_path / "test.db"))
        assert cfg is not None
        assert cfg.environment == "development"

    def test_max_concurrent_jobs_override(self, tmp_path) -> None:
        """max_concurrent_jobs can be overridden."""
        cfg = _build_config(str(tmp_path / "test.db"), max_concurrent_jobs=4)
        assert cfg.resources.max_concurrent_jobs == 4

    def test_to_dict_excludes_jwt_secret(self, tmp_path) -> None:
        """to_dict() does not expose jwt_secret_key."""
        cfg = _build_config(str(tmp_path / "test.db"))
        d = cfg.to_dict()
        security_dict = d.get("security", {})
        assert "jwt_secret_key" not in security_dict

    def test_to_dict_returns_dict(self, tmp_path) -> None:
        """to_dict() returns a plain dict."""
        cfg = _build_config(str(tmp_path / "test.db"))
        d = cfg.to_dict()
        assert isinstance(d, dict)

    def test_security_config_bcrypt_rounds_bounds(self, tmp_path) -> None:
        """bcrypt_rounds outside [10, 16] raises ValueError."""
        from shared.config import SecurityConfig

        with pytest.raises(ValueError):
            SecurityConfig(
                jwt_secret_key="test-secret-key-32chars-minimum!!",
                bcrypt_rounds=9,
            )

    def test_security_config_jwt_expiration_bounds(self, tmp_path) -> None:
        """jwt_expiration_hours outside [1, 168] raises ValueError."""
        from shared.config import SecurityConfig

        with pytest.raises(ValueError):
            SecurityConfig(
                jwt_secret_key="test-secret-key-32chars-minimum!!",
                bcrypt_rounds=10,
                jwt_expiration_hours=0,
            )

    def test_resource_config_max_concurrent_jobs_bounds(self) -> None:
        """max_concurrent_jobs outside [1, 20] raises ValueError."""
        from shared.config import ResourceConfig

        with pytest.raises(ValueError):
            ResourceConfig(max_concurrent_jobs=0)

    def test_storage_config_empty_path_raises(self) -> None:
        """Empty database_path raises ValueError."""
        from shared.config import StorageConfig

        with pytest.raises(ValueError):
            StorageConfig(
                database_path="",
                logs_directory="/tmp",
                temp_directory="/tmp",
                upload_directory="/tmp",
                backup_directory="/tmp",
            )

    def test_video_config_invalid_resolution_raises(self) -> None:
        """Resolution without 'x' raises ValueError."""
        from shared.config import VideoConfig

        with pytest.raises(ValueError):
            VideoConfig(default_resolution="1920-1080")

    def test_config_default_cors_origins_populated(self, tmp_path) -> None:
        """Config populates default CORS origins when none are provided."""
        cfg = _build_config(str(tmp_path / "test.db"))
        assert len(cfg.network.cors_origins) > 0

    def test_config_default_quality_presets_populated(self, tmp_path) -> None:
        """Config populates default quality presets."""
        cfg = _build_config(str(tmp_path / "test.db"))
        assert "standard" in cfg.video.quality_presets
        assert "high" in cfg.video.quality_presets

    def test_bcrypt_rounds_50_raises_value_error(self) -> None:
        """BCRYPT_ROUNDS above 16 fails SecurityConfig validation (e.g. 50)."""
        from shared.config import SecurityConfig

        with pytest.raises(ValueError, match="BCRYPT_ROUNDS"):
            SecurityConfig(
                jwt_secret_key="test-secret-key-32chars-minimum!!",
                bcrypt_rounds=50,
            )

    def test_validate_system_requirements_true_on_test_machine(
        self, tmp_path
    ) -> None:
        """validate_system_requirements() succeeds with relaxed minimums."""
        cfg = _build_config(str(tmp_path / "test.db"))
        cfg.resources.min_memory_gb = 0.01
        cfg.resources.min_disk_gb = 0.01
        assert cfg.validate_system_requirements() is True


class TestLoadConfigFromEnvironment:
    """Fresh-process checks for env-driven load_config (avoids cached module)."""

    def test_max_concurrent_jobs_env_var(self, tmp_path) -> None:
        """MAX_CONCURRENT_JOBS=10 is reflected after load_config in a subprocess."""
        import subprocess

        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db = tmp_path / "subcfg.db"
        logs = tmp_path / "logs"
        temp = tmp_path / "temp"
        up = tmp_path / "up"
        bk = tmp_path / "bk"
        for p in (logs, temp, up, bk):
            p.mkdir(parents=True, exist_ok=True)

        code = f"""
import os, sys
sys.path.insert(0, {root!r})
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32chars-minimum!!"
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_PATH"] = {str(db)!r}
os.environ["LOGS_DIRECTORY"] = {str(logs)!r}
os.environ["TEMP_DIRECTORY"] = {str(temp)!r}
os.environ["UPLOAD_DIRECTORY"] = {str(up)!r}
os.environ["BACKUP_DIRECTORY"] = {str(bk)!r}
os.environ["MIN_MEMORY_GB"] = "0.01"
os.environ["MIN_DISK_GB"] = "0.01"
os.environ["MAX_CONCURRENT_JOBS"] = "10"
import importlib
import shared.config as sc
importlib.reload(sc)
print(sc.config.resources.max_concurrent_jobs)
"""
        out = subprocess.check_output(
            [sys.executable, "-c", code],
            text=True,
            cwd=root,
            timeout=60,
        )
        assert out.strip() == "10"
