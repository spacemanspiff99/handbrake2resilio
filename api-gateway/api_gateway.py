#!/usr/bin/env python3
"""
API Gateway for HandBrake2Resilio
Main entry point that orchestrates communication between services
"""

import os
import logging
import threading
import time
import redis
import requests
from datetime import datetime
from flask import Flask, jsonify, request, current_app
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import structlog

# Import our modules
from config import config
from auth import init_auth_service, require_auth, require_role

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize Redis connection
redis_client = redis.Redis.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True
)

# HandBrake service URL
HANDBRAKE_SERVICE_URL = os.getenv(
    "HANDBRAKE_SERVICE_URL", "http://handbrake-service:8081"
)

app = Flask(__name__)
CORS(app, origins=config.network.cors_origins)

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins=config.network.cors_origins)

# Initialize services
auth_service = init_auth_service(config)
app.auth_service = auth_service

# Global socketio instance
socketio.init_app(app, async_mode="threading")


def get_handbrake_service_status():
    """Check HandBrake service status"""
    try:
        response = requests.get(f"{HANDBRAKE_SERVICE_URL}/health", timeout=5)
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        logger.error(f"Error checking HandBrake service: {e}")
        return None


def forward_to_handbrake_service(endpoint, method="GET", data=None):
    """Forward request to HandBrake service"""
    try:
        url = f"{HANDBRAKE_SERVICE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            return None, "Unsupported method"

        return response.json(), response.status_code
    except Exception as e:
        logger.error(f"Error forwarding to HandBrake service: {e}")
        return None, 500


@app.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Check Redis
        redis_status = redis_client.ping()

        # Check HandBrake service
        handbrake_status = get_handbrake_service_status()

        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "api-gateway",
                "version": "2.0.0",
                "redis_connected": redis_status,
                "handbrake_service": handbrake_status is not None,
                "handbrake_status": handbrake_status,
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/api/auth/login", methods=["POST"])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return (
                jsonify(
                    {
                        "error": "Missing credentials",
                        "message": "Username and password are required",
                    }
                ),
                400,
            )

        # Authenticate user
        user_info = auth_service.authenticate_user(username, password)

        if user_info:
            # Create JWT token
            token = auth_service.create_token(user_info)

            logger.info(f"User {username} logged in successfully")

            return jsonify(
                {
                    "message": "Login successful",
                    "token": token,
                    "user": {
                        "id": user_info["id"],
                        "username": user_info["username"],
                        "role": user_info["role"],
                    },
                }
            )
        else:
            logger.warning(f"Failed login attempt for user {username}")
            return (
                jsonify(
                    {
                        "error": "Invalid credentials",
                        "message": "Username or password is incorrect",
                    }
                ),
                401,
            )

    except Exception as e:
        logger.error(f"Login error: {e}")
        return (
            jsonify(
                {"error": "Login failed", "message": "An error occurred during login"}
            ),
            500,
        )


@app.route("/api/auth/register", methods=["POST"])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")
        email = data.get("email")

        if not username or not password:
            return (
                jsonify(
                    {
                        "error": "Missing required fields",
                        "message": "Username and password are required",
                    }
                ),
                400,
            )

        # Register user
        success = auth_service.register_user(username, password, email)

        if success:
            logger.info(f"User {username} registered successfully")
            return jsonify({"message": "Registration successful", "username": username})
        else:
            return (
                jsonify(
                    {
                        "error": "Registration failed",
                        "message": "Username may already exist",
                    }
                ),
                400,
            )

    except Exception as e:
        logger.error(f"Registration error: {e}")
        return (
            jsonify(
                {
                    "error": "Registration failed",
                    "message": "An error occurred during registration",
                }
            ),
            500,
        )


@app.route("/api/auth/verify", methods=["GET"])
@require_auth
def verify_token():
    """Verify JWT token validity"""
    # If we reached here, the @require_auth decorator has already verified the token
    # and populated request.user
    return jsonify(
        {
            "valid": True,
            "user": request.user
        }
    )


@app.route("/api/tabs", methods=["GET"])
@require_auth
def get_tabs():
    """Get all tabs"""
    # Optionally filter by user if not admin? For now, list all or user's own.
    # Let's just list all for simplicity or user's own.
    # request.user is available.
    tabs = auth_service.get_tabs(request.user['id'])
    return jsonify({"data": tabs})


@app.route("/api/tabs", methods=["POST"])
@require_auth
def create_tab():
    """Create a new tab"""
    data = request.get_json()
    name = data.get("name")
    source_path = data.get("source_path")
    destination_path = data.get("destination_path") # Matches schema but frontend sends 'destination'
    
    # Handle frontend sending 'destination' instead of 'destination_path'
    if not destination_path and "destination" in data:
        destination_path = data["destination"]

    if not name or not source_path or not destination_path:
        return jsonify({"error": "Missing required fields"}), 400

    tab_id = auth_service.create_tab(
        name=name,
        source_path=source_path,
        destination_path=destination_path,
        source_type=data.get("source_type", "tv"),
        profile=data.get("profile", "standard"),
        user_id=request.user['id']
    )

    if tab_id:
        return jsonify({"message": "Tab created", "id": tab_id}), 201
    else:
        return jsonify({"error": "Failed to create tab"}), 500


@app.route("/api/tabs/<int:tab_id>", methods=["PUT"])
@require_auth
def update_tab(tab_id):
    """Update a tab"""
    data = request.get_json()
    
    # Map frontend 'destination' to 'destination_path' if needed
    if "destination" in data:
        data["destination_path"] = data.pop("destination")

    success = auth_service.update_tab(tab_id, data)
    if success:
        return jsonify({"message": "Tab updated"})
    else:
        return jsonify({"error": "Failed to update tab"}), 500


@app.route("/api/tabs/<int:tab_id>", methods=["DELETE"])
@require_auth
def delete_tab(tab_id):
    """Delete a tab"""
    success = auth_service.delete_tab(tab_id)
    if success:
        return jsonify({"message": "Tab deleted"})
    else:
        return jsonify({"error": "Failed to delete tab"}), 500


@app.route("/api/jobs/add", methods=["POST"])
@require_auth
def add_job():
    """Add a new conversion job"""
    try:
        data = request.get_json()

        # Forward to HandBrake service
        response_data, status_code = forward_to_handbrake_service(
            "/convert", method="POST", data=data
        )

        if response_data:
            return jsonify(response_data), status_code
        else:
            return (
                jsonify(
                    {
                        "error": "HandBrake service unavailable",
                        "message": "Video conversion service is not responding",
                    }
                ),
                503,
            )

    except Exception as e:
        logger.error(f"Add job error: {e}")
        return (
            jsonify(
                {
                    "error": "Add job failed",
                    "message": "An error occurred while adding job",
                }
            ),
            500,
        )


@app.route("/api/jobs/status/<job_id>", methods=["GET"])
@require_auth
def get_job_status(job_id):
    """Get status of a specific job"""
    try:
        # Forward to HandBrake service
        response_data, status_code = forward_to_handbrake_service(f"/job/{job_id}")

        if response_data:
            return jsonify(response_data), status_code
        else:
            return (
                jsonify(
                    {
                        "error": "HandBrake service unavailable",
                        "message": "Video conversion service is not responding",
                    }
                ),
                503,
            )

    except Exception as e:
        logger.error(f"Get job status error: {e}")
        return (
            jsonify(
                {
                    "error": "Failed to get job status",
                    "message": "An error occurred while getting job status",
                }
            ),
            500,
        )


@app.route("/api/jobs/list", methods=["GET"])
@require_auth
def list_jobs():
    """List all jobs"""
    try:
        # Forward to HandBrake service
        response_data, status_code = forward_to_handbrake_service("/jobs")

        if response_data:
            return jsonify(response_data), status_code
        else:
            return (
                jsonify(
                    {
                        "error": "HandBrake service unavailable",
                        "message": "Video conversion service is not responding",
                    }
                ),
                503,
            )

    except Exception as e:
        logger.error(f"List jobs error: {e}")
        return (
            jsonify(
                {
                    "error": "Failed to list jobs",
                    "message": "An error occurred while listing jobs",
                }
            ),
            500,
        )


@app.route("/api/jobs/cancel/<job_id>", methods=["POST"])
@require_auth
def cancel_job(job_id):
    """Cancel a running job"""
    try:
        # Forward to HandBrake service
        response_data, status_code = forward_to_handbrake_service(
            f"/cancel/{job_id}", method="POST"
        )

        if response_data:
            return jsonify(response_data), status_code
        else:
            return (
                jsonify(
                    {
                        "error": "HandBrake service unavailable",
                        "message": "Video conversion service is not responding",
                    }
                ),
                503,
            )

    except Exception as e:
        logger.error(f"Cancel job error: {e}")
        return (
            jsonify(
                {
                    "error": "Failed to cancel job",
                    "message": "An error occurred while cancelling job",
                }
            ),
            500,
        )


@app.route("/api/filesystem/browse", methods=["GET"])
@require_auth
def browse_filesystem():
    """Browse filesystem on HandBrake service"""
    try:
        path = request.args.get("path")
        query = f"?path={path}" if path else ""
        
        # Forward to HandBrake service
        response_data, status_code = forward_to_handbrake_service(f"/browse{query}")

        if response_data:
            return jsonify(response_data), status_code
        else:
            return (
                jsonify(
                    {
                        "error": "HandBrake service unavailable",
                        "message": "Service is not responding",
                    }
                ),
                503,
            )
    except Exception as e:
        logger.error(f"Browse filesystem error: {e}")
        return jsonify({"error": "Browse failed", "message": str(e)}), 500


@app.route("/api/filesystem/scan", methods=["GET"])
@require_auth
def scan_filesystem():
    """Scan filesystem for media files"""
    try:
        path = request.args.get("path")
        query = f"?path={path}" if path else ""
        
        # Forward to HandBrake service
        response_data, status_code = forward_to_handbrake_service(f"/scan{query}")

        if response_data:
            return jsonify(response_data), status_code
        else:
            return (
                jsonify(
                    {
                        "error": "HandBrake service unavailable",
                        "message": "Service is not responding",
                    }
                ),
                503,
            )
    except Exception as e:
        logger.error(f"Scan filesystem error: {e}")
        return jsonify({"error": "Scan failed", "message": str(e)}), 500


@app.route("/api/system/status", methods=["GET"])
@require_auth
def get_system_status():
    """Get system status"""
    try:
        # Get HandBrake service status
        handbrake_status = get_handbrake_service_status()

        # Get Redis status
        redis_status = redis_client.ping()

        return jsonify(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "handbrake_service": handbrake_status,
                "redis_connected": redis_status,
                "api_gateway": "healthy",
            }
        )

    except Exception as e:
        logger.error(f"System status error: {e}")
        return (
            jsonify(
                {
                    "error": "Failed to get system status",
                    "message": "An error occurred while getting system status",
                }
            ),
            500,
        )


@app.route("/api/config")
@require_auth
def get_config():
    """Get application configuration (without secrets)"""
    return jsonify(config.to_dict())


@app.route("/")
def root():
    """Root endpoint"""
    return jsonify(
        {
            "name": "HandBrake2Resilio API Gateway",
            "version": "2.0.0",
            "status": "running",
            "services": {
                "api_gateway": "running",
                "handbrake_service": get_handbrake_service_status() is not None,
                "redis": redis_client.ping(),
            },
        }
    )


def start_realtime_updates():
    """Start real-time updates via WebSocket"""

    def emit_updates():
        while True:
            try:
                if socketio:
                    # Get system status
                    handbrake_status = get_handbrake_service_status()
                    redis_status = redis_client.ping()

                    # Get jobs from HandBrake service
                    jobs_data, _ = forward_to_handbrake_service("/jobs")

                    socketio.emit(
                        "system_update",
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "handbrake_service": handbrake_status,
                            "redis_connected": redis_status,
                            "jobs": jobs_data.get("jobs", []) if jobs_data else [],
                        },
                    )

                time.sleep(5)  # Update every 5 seconds

            except Exception as e:
                logger.error(f"Error in real-time updates: {e}")
                time.sleep(10)  # Wait longer on error

    update_thread = threading.Thread(target=emit_updates, daemon=True)
    update_thread.start()
    logger.info("Started real-time updates thread")


if __name__ == "__main__":
    # Start background threads
    start_realtime_updates()

    # Log startup information
    logger.info("Starting HandBrake2Resilio API Gateway...")
    logger.info(f"Redis URL: {os.getenv('REDIS_URL', 'redis://localhost:6379')}")
    logger.info(f"HandBrake Service URL: {HANDBRAKE_SERVICE_URL}")

    # Start the server
    socketio.run(
        app,
        host=config.network.host,
        port=config.network.port,
        debug=False,
        use_reloader=False,
    )
