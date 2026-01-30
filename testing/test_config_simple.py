#!/usr/bin/env python3
"""
Simple configuration test without global instantiation
"""

import os
import tempfile
import sys

# Set up test environment
temp_dir = tempfile.mkdtemp()
os.environ["DATABASE_PATH"] = os.path.join(temp_dir, "test.db")
os.environ["LOGS_DIRECTORY"] = os.path.join(temp_dir, "logs")
os.environ["TEMP_DIRECTORY"] = os.path.join(temp_dir, "temp")
os.environ["UPLOAD_DIRECTORY"] = os.path.join(temp_dir, "uploads")
os.environ["BACKUP_DIRECTORY"] = os.path.join(temp_dir, "backups")
os.environ["ENVIRONMENT"] = "development"
os.environ["MIN_DISK_GB"] = "0.1"  # Lower disk requirement for testing
os.environ["MIN_MEMORY_GB"] = "0.1"  # Lower memory requirement for testing

# Import config module without triggering global load
sys.path.insert(0, '.')
from config import load_config


def test_config_loading():
    """Test configuration loading with test environment"""
    try:
        config = load_config()
        print("✅ Configuration loaded successfully!")
        print(f"Environment: {config.environment}")
        print(f"Database path: {config.storage.database_path}")
        print(f"Logs directory: {config.storage.logs_directory}")
        print(f"Default quality: {config.video.default_quality}")
        print(f"Default resolution: {config.video.default_resolution}")
        print(f"Max concurrent jobs: {config.resources.max_concurrent_jobs}")
        return True
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False


if __name__ == "__main__":
    success = test_config_loading()
    if success:
        print("\n🎉 Configuration test passed!")
    else:
        print("\n💥 Configuration test failed!")
        sys.exit(1) 