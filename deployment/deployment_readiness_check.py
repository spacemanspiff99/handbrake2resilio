#!/usr/bin/env python3
"""
Deployment Readiness Check for HandBrake2Resilio
Validates all components before production deployment
"""

import os
import sys
import subprocess
import tempfile

# Set up test environment
temp_dir = tempfile.mkdtemp()
os.environ["DATABASE_PATH"] = os.path.join(temp_dir, "test.db")
os.environ["LOGS_DIRECTORY"] = os.path.join(temp_dir, "logs")
os.environ["TEMP_DIRECTORY"] = os.path.join(temp_dir, "temp")
os.environ["UPLOAD_DIRECTORY"] = os.path.join(temp_dir, "uploads")
os.environ["BACKUP_DIRECTORY"] = os.path.join(temp_dir, "backups")
os.environ["MIN_DISK_GB"] = "0.1"
os.environ["MIN_MEMORY_GB"] = "0.1"


def print_status(message, status="INFO"):
    """Print status message with color coding"""
    colors = {
        "INFO": "\033[94m",  # Blue
        "SUCCESS": "\033[92m",  # Green
        "WARNING": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
    }
    reset = "\033[0m"
    color = colors.get(status, colors["INFO"])
    print(f"{color}[{status}]{reset} {message}")


def check_file_exists(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        print_status(f"✅ {description}: {filepath}", "SUCCESS")
        return True
    else:
        print_status(f"❌ {description}: {filepath} - NOT FOUND", "ERROR")
        return False


def check_python_import(module_name, description):
    """Check if a Python module can be imported"""
    try:
        __import__(module_name)
        print_status(f"✅ {description}: {module_name}", "SUCCESS")
        return True
    except ImportError as e:
        print_status(f"❌ {description}: {module_name} - {e}", "ERROR")
        return False


def check_configuration():
    """Check configuration system"""
    print_status("🔧 Checking Configuration System...", "INFO")

    try:
        from config import load_config

        config = load_config()
        print_status("✅ Configuration loaded successfully", "SUCCESS")
        print_status(f"   Environment: {config.environment}", "INFO")
        print_status(f"   Database: {config.storage.database_path}", "INFO")
        print_status(f"   Max Jobs: {config.resources.max_concurrent_jobs}", "INFO")
        return True
    except Exception as e:
        print_status(f"❌ Configuration failed: {e}", "ERROR")
        return False


def check_job_queue():
    """Check job queue system"""
    print_status("📋 Checking Job Queue System...", "INFO")

    try:
        from job_queue import init_job_queue
        from config import load_config

        config = load_config()
        job_queue = init_job_queue(config)
        print_status("✅ Job queue initialized successfully", "SUCCESS")
        return True
    except Exception as e:
        print_status(f"❌ Job queue failed: {e}", "ERROR")
        return False


def check_authentication():
    """Check authentication system"""
    print_status("🔐 Checking Authentication System...", "INFO")

    try:
        from auth import init_auth_service
        from config import load_config

        config = load_config()
        auth_service = init_auth_service(config)
        print_status("✅ Authentication service initialized successfully", "SUCCESS")
        return True
    except Exception as e:
        print_status(f"❌ Authentication failed: {e}", "ERROR")
        return False


def check_docker_files():
    """Check Docker deployment files"""
    print_status("🐳 Checking Docker Files...", "INFO")

    files_to_check = [
        ("Dockerfile.production", "Production Dockerfile"),
        ("docker-compose.production.yml", "Production Docker Compose"),
        ("deploy_production.sh", "Deployment Script"),
        ("requirements.production.txt", "Production Requirements"),
    ]

    all_good = True
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_good = False

    return all_good


def check_dependencies():
    """Check required dependencies"""
    print_status("📦 Checking Dependencies...", "INFO")

    dependencies = [
        ("flask", "Flask Web Framework"),
        ("flask_cors", "Flask CORS"),
        ("flask_socketio", "Flask SocketIO"),
        ("jwt", "PyJWT"),
        ("bcrypt", "bcrypt"),
        ("structlog", "Structured Logging"),
        ("psutil", "System Monitoring"),
    ]

    all_good = True
    for module, description in dependencies:
        if not check_python_import(module, description):
            all_good = False

    return all_good


def run_tests():
    """Run test suites"""
    print_status("🧪 Running Test Suites...", "INFO")

    test_files = [
        ("test_config_simple.py", "Configuration Tests"),
        ("test_job_queue.py", "Job Queue Tests"),
        ("test_auth.py", "Authentication Tests"),
    ]

    all_good = True
    for test_file, description in test_files:
        if os.path.exists(test_file):
            print_status(f"Running {description}...", "INFO")
            try:
                result = subprocess.run(
                    ["python", test_file], capture_output=True, text=True, timeout=60
                )
                if result.returncode == 0:
                    print_status(f"✅ {description} passed", "SUCCESS")
                else:
                    print_status(f"❌ {description} failed", "ERROR")
                    print_status(f"   Output: {result.stdout[:200]}...", "WARNING")
                    all_good = False
            except subprocess.TimeoutExpired:
                print_status(f"❌ {description} timed out", "ERROR")
                all_good = False
        else:
            print_status(f"⚠️ {description} file not found", "WARNING")

    return all_good


def main():
    """Main deployment readiness check"""
    print_status("🚀 HandBrake2Resilio Deployment Readiness Check", "INFO")
    print_status("=" * 60, "INFO")

    checks = [
        ("Configuration System", check_configuration),
        ("Job Queue System", check_job_queue),
        ("Authentication System", check_authentication),
        ("Docker Files", check_docker_files),
        ("Dependencies", check_dependencies),
        ("Test Suites", run_tests),
    ]

    results = []
    for name, check_func in checks:
        print_status(f"\n📋 {name}", "INFO")
        result = check_func()
        results.append((name, result))

    # Summary
    print_status("\n" + "=" * 60, "INFO")
    print_status("📊 DEPLOYMENT READINESS SUMMARY", "INFO")
    print_status("=" * 60, "INFO")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print_status(f"{status} {name}")

    print_status(f"\nOverall: {passed}/{total} checks passed", "INFO")

    if passed == total:
        print_status("🎉 DEPLOYMENT READY!", "SUCCESS")
        print_status("All systems are ready for production deployment.", "SUCCESS")
        return 0
    else:
        print_status("⚠️ DEPLOYMENT NOT READY", "WARNING")
        print_status("Please fix the failed checks before deploying.", "WARNING")
        return 1


if __name__ == "__main__":
    sys.exit(main())
