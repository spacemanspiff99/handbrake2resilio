#!/usr/bin/env python3
"""
Authentication system for HandBrake2Resilio
Handles user authentication, JWT tokens, and password management
"""

import jwt
import bcrypt
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service with JWT and bcrypt"""

    def __init__(self, config):
        self.config = config
        self.db_path = config.storage.database_path
        self._init_database()

    def _init_database(self):
        """Initialize the authentication database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        email TEXT,
                        role TEXT DEFAULT 'user',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        token_hash TEXT NOT NULL,
                        expires_at TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """
                )

                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tabs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        source_path TEXT NOT NULL,
                        destination_path TEXT NOT NULL,
                        source_type TEXT DEFAULT 'tv',
                        profile TEXT DEFAULT 'standard',
                        user_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """
                )

                # Create default admin user if no users exist
                cursor = conn.execute("SELECT COUNT(*) FROM users")
                if cursor.fetchone()[0] == 0:
                    self._create_default_admin(conn)

                conn.commit()
                logger.info("Authentication database initialized")

        except Exception as e:
            logger.error(f"Failed to initialize auth database: {e}")
            raise

    def _create_default_admin(self, conn):
        """Create default admin user"""
        default_password = "admin123"  # Should be changed immediately
        password_hash = bcrypt.hashpw(
            default_password.encode("utf-8"),
            bcrypt.gensalt(self.config.security.bcrypt_rounds),
        ).decode("utf-8")

        conn.execute(
            """
            INSERT INTO users (username, password_hash, email, role)
            VALUES (?, ?, ?, ?)
        """,
            ("admin", password_hash, "admin@localhost", "admin"),
        )

        logger.warning(
            "Default admin user created with password 'admin123'. "
            "Please change this immediately!"
        )

    def register_user(
        self, username: str, password: str, email: str = None, role: str = "user"
    ) -> bool:
        """Register a new user"""
        try:
            # Validate input
            if not username or len(username) < 3:
                raise ValueError("Username must be at least 3 characters")
            if not password or len(password) < 6:
                raise ValueError("Password must be at least 6 characters")

            # Hash password
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt(self.config.security.bcrypt_rounds),
            ).decode("utf-8")

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO users (username, password_hash, email, role)
                    VALUES (?, ?, ?, ?)
                """,
                    (username, password_hash, email, role),
                )
                conn.commit()

            logger.info(f"User registered: {username}")
            return True

        except sqlite3.IntegrityError:
            logger.warning(f"Username already exists: {username}")
            return False
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user info if successful"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, username, password_hash, email, role, is_active
                    FROM users WHERE username = ?
                """,
                    (username,),
                )
                user = cursor.fetchone()

            if not user:
                logger.warning(f"Authentication failed: user not found - {username}")
                return None

            user_id, username, password_hash, email, role, is_active = user

            if not is_active:
                logger.warning(f"Authentication failed: user inactive - {username}")
                return None

            # Verify password
            if not bcrypt.checkpw(
                password.encode("utf-8"), password_hash.encode("utf-8")
            ):
                logger.warning(f"Authentication failed: invalid password - {username}")
                return None

            # Update last login
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE users SET last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                """,
                    (user_id,),
                )
                conn.commit()

            logger.info(f"User authenticated: {username}")
            return {"id": user_id, "username": username, "email": email, "role": role}

        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None

    def create_token(self, user_info: Dict) -> str:
        """Create JWT token for user"""
        payload = {
            "user_id": user_info["id"],
            "username": user_info["username"],
            "role": user_info["role"],
            "exp": datetime.utcnow()
            + timedelta(hours=self.config.security.jwt_expiration_hours),
            "iat": datetime.utcnow(),
        }

        return jwt.encode(
            payload,
            self.config.security.jwt_secret_key,
            algorithm=self.config.security.jwt_algorithm,
        )

    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return user info"""
        try:
            payload = jwt.decode(
                token,
                self.config.security.jwt_secret_key,
                algorithms=[self.config.security.jwt_algorithm],
            )

            # Check if user still exists and is active
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT id, username, email, role, is_active
                    FROM users WHERE id = ? AND is_active = 1
                """,
                    (payload["user_id"],),
                )
                user = cursor.fetchone()

            if not user:
                logger.warning(f"Token verification failed: user not found")
                return None

            return {
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "role": user[3],
            }

        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> bool:
        """Change user password"""
        try:
            # Get current password hash
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT password_hash FROM users WHERE id = ?
                """,
                    (user_id,),
                )
                result = cursor.fetchone()

            if not result:
                return False

            current_hash = result[0]

            # Verify old password
            if not bcrypt.checkpw(
                old_password.encode("utf-8"), current_hash.encode("utf-8")
            ):
                return False

            # Hash new password
            new_hash = bcrypt.hashpw(
                new_password.encode("utf-8"),
                bcrypt.gensalt(self.config.security.bcrypt_rounds),
            ).decode("utf-8")

            # Update password
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE users SET password_hash = ? WHERE id = ?
                """,
                    (new_hash, user_id),
                )
                conn.commit()

            logger.info(f"Password changed for user ID: {user_id}")
            return True

        except Exception as e:
            logger.error(f"Password change failed: {e}")
            return False

    def create_tab(self, name, source_path, destination_path, source_type, profile, user_id):
        """Create a new tab"""
        try:
            logger.info(f"📝 Creating tab '{name}' for user {user_id}")
            logger.info(f"📂 Source: {source_path}, Destination: {destination_path}")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO tabs (name, source_path, destination_path, source_type, profile, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (name, source_path, destination_path, source_type, profile, user_id),
                )
                conn.commit()
                tab_id = cursor.lastrowid
                logger.info(f"✅ Tab created with ID: {tab_id}")
                return tab_id
        except Exception as e:
            logger.error(f"❌ Failed to create tab: {e}")
            return None

    def get_tabs(self, user_id=None):
        """Get all tabs, optionally filtered by user"""
        try:
            logger.info(f"🔍 Getting tabs for user_id: {user_id}")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                if user_id:
                    cursor = conn.execute("SELECT * FROM tabs WHERE user_id = ?", (user_id,))
                else:
                    cursor = conn.execute("SELECT * FROM tabs")
                
                rows = cursor.fetchall()
                tabs = [dict(row) for row in rows]
                logger.info(f"✅ Found {len(tabs)} tabs")
                return tabs
        except Exception as e:
            logger.error(f"❌ Failed to get tabs: {e}")
            return []

    def update_tab(self, tab_id, data):
        """Update a tab"""
        try:
            fields = []
            values = []
            for key, value in data.items():
                if key in ['name', 'source_path', 'destination_path', 'source_type', 'profile']:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                return False
            
            values.append(tab_id)
            query = f"UPDATE tabs SET {', '.join(fields)} WHERE id = ?"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, values)
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update tab: {e}")
            return False

    def delete_tab(self, tab_id):
        """Delete a tab"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM tabs WHERE id = ?", (tab_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to delete tab: {e}")
            return False


def require_auth(f):
    """Decorator to require authentication"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None

        # Get token from header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        # Verify token
        auth_service = current_app.auth_service
        user_info = auth_service.verify_token(token)

        if not user_info:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Add user info to request
        request.user = user_info
        return f(*args, **kwargs)

    return decorated_function


def require_role(role):
    """Decorator to require specific role"""

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, "user"):
                return jsonify({"error": "Authentication required"}), 401

            if request.user["role"] != role and request.user["role"] != "admin":
                return jsonify({"error": "Insufficient permissions"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Global auth service instance
auth_service = None


def init_auth_service(config):
    """Initialize the global auth service"""
    global auth_service
    auth_service = AuthService(config)
    return auth_service
