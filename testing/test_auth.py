#!/usr/bin/env python3
"""
Unit tests for authentication system
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import jwt
import bcrypt

from auth import AuthService, require_auth, require_role


class TestAuthService(unittest.TestCase):
    """Test authentication service"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_auth.db")

        # Create test config
        self.config = MagicMock()
        self.config.storage.database_path = self.db_path
        self.config.security.jwt_secret_key = "test-secret-key"
        self.config.security.jwt_algorithm = "HS256"
        self.config.security.jwt_expiration_hours = 24
        self.config.security.bcrypt_rounds = 12

        # Create auth service
        self.auth_service = AuthService(self.config)

    def tearDown(self):
        """Clean up test environment"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_user_registration(self):
        """Test user registration"""
        success = self.auth_service.register_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            role="user",
        )

        self.assertTrue(success)

    def test_user_registration_duplicate(self):
        """Test duplicate user registration"""
        # Register first user
        self.auth_service.register_user("testuser", "testpass123")

        # Try to register same user again
        success = self.auth_service.register_user("testuser", "testpass123")

        self.assertFalse(success)

    def test_user_registration_validation(self):
        """Test user registration validation"""
        # Test short username
        success = self.auth_service.register_user("ab", "testpass123")
        self.assertFalse(success)

        # Test short password
        success = self.auth_service.register_user("testuser", "123")
        self.assertFalse(success)

    def test_user_authentication(self):
        """Test user authentication"""
        # Register user
        self.auth_service.register_user("testuser", "testpass123")

        # Authenticate with correct credentials
        user_info = self.auth_service.authenticate_user("testuser", "testpass123")

        self.assertIsNotNone(user_info)
        self.assertEqual(user_info["username"], "testuser")
        self.assertEqual(user_info["role"], "user")

    def test_user_authentication_wrong_password(self):
        """Test authentication with wrong password"""
        # Register user
        self.auth_service.register_user("testuser", "testpass123")

        # Authenticate with wrong password
        user_info = self.auth_service.authenticate_user("testuser", "wrongpass")

        self.assertIsNone(user_info)

    def test_user_authentication_nonexistent_user(self):
        """Test authentication with nonexistent user"""
        user_info = self.auth_service.authenticate_user("nonexistent", "testpass123")

        self.assertIsNone(user_info)

    def test_token_creation(self):
        """Test JWT token creation"""
        user_info = {"id": 1, "username": "testuser", "role": "user"}

        token = self.auth_service.create_token(user_info)

        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

    def test_token_verification(self):
        """Test JWT token verification"""
        user_info = {"id": 1, "username": "testuser", "role": "user"}

        # Create token
        token = self.auth_service.create_token(user_info)

        # Verify token
        verified_user = self.auth_service.verify_token(token)

        self.assertIsNotNone(verified_user)
        self.assertEqual(verified_user["username"], "testuser")

    def test_token_verification_invalid(self):
        """Test JWT token verification with invalid token"""
        verified_user = self.auth_service.verify_token("invalid-token")

        self.assertIsNone(verified_user)

    def test_password_change(self):
        """Test password change"""
        # Register user
        self.auth_service.register_user("testuser", "oldpass123")

        # Authenticate to get user ID
        user_info = self.auth_service.authenticate_user("testuser", "oldpass123")

        # Change password
        success = self.auth_service.change_password(
            user_info["id"], "oldpass123", "newpass123"
        )

        self.assertTrue(success)

        # Verify new password works
        new_user_info = self.auth_service.authenticate_user("testuser", "newpass123")
        self.assertIsNotNone(new_user_info)

        # Verify old password doesn't work
        old_user_info = self.auth_service.authenticate_user("testuser", "oldpass123")
        self.assertIsNone(old_user_info)

    def test_password_change_wrong_old_password(self):
        """Test password change with wrong old password"""
        # Register user
        self.auth_service.register_user("testuser", "oldpass123")

        # Authenticate to get user ID
        user_info = self.auth_service.authenticate_user("testuser", "oldpass123")

        # Try to change password with wrong old password
        success = self.auth_service.change_password(
            user_info["id"], "wrongpass", "newpass123"
        )

        self.assertFalse(success)

    def test_default_admin_creation(self):
        """Test default admin user creation"""
        # Create new auth service (should create default admin)
        new_db_path = os.path.join(self.temp_dir, "test_admin.db")
        new_config = MagicMock()
        new_config.storage.database_path = new_db_path
        new_config.security.jwt_secret_key = "test-secret-key"
        new_config.security.jwt_algorithm = "HS256"
        new_config.security.jwt_expiration_hours = 24
        new_config.security.bcrypt_rounds = 12

        auth_service = AuthService(new_config)

        # Try to authenticate with default admin
        user_info = auth_service.authenticate_user("admin", "admin123")

        self.assertIsNotNone(user_info)
        self.assertEqual(user_info["username"], "admin")
        self.assertEqual(user_info["role"], "admin")


class TestAuthDecorators(unittest.TestCase):
    """Test authentication decorators"""

    def setUp(self):
        """Set up test environment"""
        from flask import Flask, request, jsonify

        self.app = Flask(__name__)

        # Mock request
        self.app.test_request_context = self.app.test_request_context

    def test_require_auth_decorator(self):
        """Test require_auth decorator"""

        @require_auth
        def protected_route():
            return {"message": "success"}

        # Test without token
        with self.app.test_request_context():
            response = protected_route()
            self.assertEqual(response[1], 401)  # Unauthorized

        # Test with invalid token
        with self.app.test_request_context():
            request.headers = {"Authorization": "Bearer invalid-token"}
            response = protected_route()
            self.assertEqual(response[1], 401)  # Unauthorized

    def test_require_role_decorator(self):
        """Test require_role decorator"""

        @require_role("admin")
        def admin_route():
            return {"message": "admin-only"}

        # Test without authentication
        with self.app.test_request_context():
            response = admin_route()
            self.assertEqual(response[1], 401)  # Unauthorized


if __name__ == "__main__":
    unittest.main()
