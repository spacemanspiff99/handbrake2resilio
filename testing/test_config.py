#!/usr/bin/env python3
"""
Unit tests for configuration management
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path

from config import (
    Config,
    SecurityConfig,
    ResourceConfig,
    StorageConfig,
    NetworkConfig,
    VideoConfig,
)


class TestConfig(unittest.TestCase):
    """Test configuration management"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")

        # Set test environment variables
        os.environ["DATABASE_PATH"] = self.db_path
        os.environ["LOGS_DIRECTORY"] = os.path.join(self.temp_dir, "logs")
        os.environ["TEMP_DIRECTORY"] = os.path.join(self.temp_dir, "temp")
        os.environ["UPLOAD_DIRECTORY"] = os.path.join(self.temp_dir, "uploads")
        os.environ["BACKUP_DIRECTORY"] = os.path.join(self.temp_dir, "backups")

        # Clear environment variables
        self.env_vars = {}
        for key in [
            "JWT_SECRET_KEY",
            "CPU_LIMIT",
            "MEMORY_LIMIT",
            "TV_SOURCE",
            "MOVIES_SOURCE",
            "ARCHIVE_DESTINATION",
            "HOST",
            "PORT",
        ]:
            if key in os.environ:
                self.env_vars[key] = os.environ[key]
                del os.environ[key]

    def tearDown(self):
        """Clean up test environment"""
        # Restore environment variables
        for key, value in self.env_vars.items():
            os.environ[key] = value

        # Clean up test environment variables
        for key in ["DATABASE_PATH", "LOGS_DIRECTORY", "TEMP_DIRECTORY",
                    "UPLOAD_DIRECTORY", "BACKUP_DIRECTORY"]:
            if key in os.environ:
                del os.environ[key]

        # Clean up temp directory
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("config.secrets.token_urlsafe")
    def test_jwt_secret_generation(self, mock_token):
        """Test JWT secret generation when not provided"""
        mock_token.return_value = "test-secret-key"

        config = Config()

        self.assertEqual(config.security.jwt_secret_key, "test-secret-key")
        mock_token.assert_called_once_with(32)

    def test_jwt_secret_from_env(self):
        """Test JWT secret from environment variable"""
        os.environ["JWT_SECRET_KEY"] = "env-secret-key"

        config = Config()

        self.assertEqual(config.security.jwt_secret_key, "env-secret-key")

    def test_resource_limits_validation(self):
        """Test resource limits validation"""
        os.environ["CPU_LIMIT"] = "95"
        os.environ["MEMORY_LIMIT"] = "90"

        with patch("config.logger") as mock_logger:
            config = Config()

            # Should log warnings for high limits
            mock_logger.warning.assert_called()

    def test_storage_paths(self):
        """Test storage path configuration"""
        os.environ["TV_SOURCE"] = "/test/tv"
        os.environ["MOVIES_SOURCE"] = "/test/movies"
        os.environ["ARCHIVE_DESTINATION"] = "/test/archive"

        config = Config()

        self.assertEqual(config.storage.tv_source, "/test/tv")
        self.assertEqual(config.storage.movies_source, "/test/movies")
        self.assertEqual(config.storage.archive_destination, "/test/archive")

    def test_network_config(self):
        """Test network configuration"""
        os.environ["HOST"] = "127.0.0.1"
        os.environ["PORT"] = "9000"
        os.environ["CORS_ORIGINS"] = "http://test.com,http://test2.com"

        config = Config()

        self.assertEqual(config.network.host, "127.0.0.1")
        self.assertEqual(config.network.port, 9000)
        self.assertEqual(
            config.network.cors_origins, ["http://test.com", "http://test2.com"]
        )

    def test_video_config(self):
        """Test video processing configuration"""
        os.environ["DEFAULT_QUALITY"] = "20"
        os.environ["DEFAULT_RESOLUTION"] = "1080x720"
        os.environ["DEFAULT_VIDEO_BITRATE"] = "2000"

        config = Config()

        self.assertEqual(config.video.default_quality, 20)
        self.assertEqual(config.video.default_resolution, "1080x720")
        self.assertEqual(config.video.default_video_bitrate, 2000)

    def test_to_dict_method(self):
        """Test configuration serialization"""
        config = Config()
        config_dict = config.to_dict()

        # Check that secrets are not included
        self.assertNotIn("jwt_secret_key", config_dict["security"])

        # Check that other config is included
        self.assertIn("jwt_algorithm", config_dict["security"])
        self.assertIn("cpu_limit_percent", config_dict["resources"])
        self.assertIn("tv_source", config_dict["storage"])

    def test_directory_creation(self):
        """Test automatic directory creation"""
        test_path = os.path.join(self.temp_dir, "test_dir")
        os.environ["TV_SOURCE"] = test_path

        config = Config()

        # Directory should be created
        self.assertTrue(os.path.exists(test_path))

    def test_default_values(self):
        """Test default configuration values"""
        config = Config()

        # Check default values
        self.assertEqual(config.resources.cpu_limit_percent, 80)
        self.assertEqual(config.resources.memory_limit_percent, 80)
        self.assertEqual(config.resources.max_concurrent_jobs, 8)
        self.assertEqual(config.security.jwt_algorithm, "HS256")
        self.assertEqual(config.security.bcrypt_rounds, 12)


if __name__ == "__main__":
    unittest.main()
