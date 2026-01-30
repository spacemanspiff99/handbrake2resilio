#!/usr/bin/env python3
"""
Simple test to verify configuration system works
"""

import os
import tempfile
import unittest
from unittest.mock import patch

# Test that we can import our modules
try:
    from config import Config

    print("✅ Config module imported successfully")
except ImportError as e:
    print(f"❌ Config module import failed: {e}")

try:
    from auth import AuthService

    print("✅ Auth module imported successfully")
except ImportError as e:
    print(f"❌ Auth module import failed: {e}")

try:
    from job_queue import JobQueue, ResourceMonitor, ConversionJob, JobStatus

    print("✅ Job queue module imported successfully")
except ImportError as e:
    print(f"❌ Job queue module import failed: {e}")


class TestSimpleConfig(unittest.TestCase):
    """Simple configuration test"""

    def setUp(self):
        """Set up test environment"""
        # Clear environment variables that might interfere
        self.env_vars = {}
        for key in ["JWT_SECRET_KEY", "CPU_LIMIT", "MEMORY_LIMIT"]:
            if key in os.environ:
                self.env_vars[key] = os.environ[key]
                del os.environ[key]

    def tearDown(self):
        """Clean up test environment"""
        # Restore environment variables
        for key, value in self.env_vars.items():
            os.environ[key] = value

    @patch("config.secrets.token_urlsafe")
    def test_config_creation(self, mock_token):
        """Test that configuration can be created"""
        mock_token.return_value = "test-secret-key"

        try:
            config = Config()
            self.assertIsNotNone(config)
            self.assertEqual(config.security.jwt_secret_key, "test-secret-key")
            self.assertEqual(config.resources.cpu_limit_percent, 80)
            self.assertEqual(config.resources.memory_limit_percent, 80)
            print("✅ Configuration created successfully")
        except Exception as e:
            self.fail(f"Configuration creation failed: {e}")

    def test_config_environment_variables(self):
        """Test configuration with environment variables"""
        os.environ["CPU_LIMIT"] = "75"
        os.environ["MEMORY_LIMIT"] = "70"
        os.environ["JWT_SECRET_KEY"] = "env-test-secret"

        try:
            config = Config()
            self.assertEqual(config.resources.cpu_limit_percent, 75)
            self.assertEqual(config.resources.memory_limit_percent, 70)
            self.assertEqual(config.security.jwt_secret_key, "env-test-secret")
            print("✅ Environment variable configuration works")
        except Exception as e:
            self.fail(f"Environment variable configuration failed: {e}")


class TestSimpleAuth(unittest.TestCase):
    """Simple authentication test"""

    def setUp(self):
        """Set up test environment"""
        import tempfile

        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_auth.db")

        # Create mock config
        from unittest.mock import MagicMock

        self.config = MagicMock()
        self.config.storage.database_path = self.db_path
        self.config.security.jwt_secret_key = "test-secret-key"
        self.config.security.jwt_algorithm = "HS256"
        self.config.security.jwt_expiration_hours = 24
        self.config.security.bcrypt_rounds = 12

    def tearDown(self):
        """Clean up test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_auth_service_creation(self):
        """Test that auth service can be created"""
        try:
            auth_service = AuthService(self.config)
            self.assertIsNotNone(auth_service)
            print("✅ Auth service created successfully")
        except Exception as e:
            self.fail(f"Auth service creation failed: {e}")

    def test_user_registration(self):
        """Test user registration"""
        try:
            auth_service = AuthService(self.config)
            success = auth_service.register_user("testuser", "testpass123")
            self.assertTrue(success)
            print("✅ User registration works")
        except Exception as e:
            self.fail(f"User registration failed: {e}")


class TestSimpleJobQueue(unittest.TestCase):
    """Simple job queue test"""

    def setUp(self):
        """Set up test environment"""
        import tempfile

        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_jobs.db")

        # Create mock config
        from unittest.mock import MagicMock

        self.config = MagicMock()
        self.config.storage.database_path = self.db_path
        self.config.resources.cpu_limit_percent = 80
        self.config.resources.memory_limit_percent = 80
        self.config.resources.max_concurrent_jobs = 2

    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self, "job_queue"):
            self.job_queue.shutdown()
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_job_queue_creation(self):
        """Test that job queue can be created"""
        try:
            self.job_queue = JobQueue(self.config, self.db_path)
            self.assertIsNotNone(self.job_queue)
            print("✅ Job queue created successfully")
        except Exception as e:
            self.fail(f"Job queue creation failed: {e}")

    def test_job_creation(self):
        """Test job creation"""
        try:
            job = ConversionJob(
                id="test-job-1",
                input_path="/test/input.mkv",
                output_path="/test/output.mp4",
            )
            self.assertEqual(job.id, "test-job-1")
            self.assertEqual(job.status, JobStatus.PENDING)
            print("✅ Job creation works")
        except Exception as e:
            self.fail(f"Job creation failed: {e}")


if __name__ == "__main__":
    print("🧪 Running simple tests...")
    unittest.main(verbosity=2)
