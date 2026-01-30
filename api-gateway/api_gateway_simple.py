#!/usr/bin/env python3
"""
API Gateway for HandBrake2Resilio (Simplified)
Main entry point with SQLite storage instead of Redis
"""

import os
import threading
import time
import sqlite3
import requests
from datetime import datetime
from flask import Flask, jsonify, request, current_app
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import structlog

# Import our modules
from config import config
from auth import init_auth_service, require_auth
from job_queue import ConversionJob, JobStatus

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

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

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "default-secret-key")

# Configure CORS
CORS(app, origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","))

# Initialize SocketIO
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    logger=True,
    engineio_logger=True,
)

# Environment variables
HANDBRAKE_SERVICE_URL = os.getenv("HANDBRAKE_SERVICE_URL", "http://localhost:8081")

# Initialize auth service
auth_service = init_auth_service(config)
app.auth_service = auth_service


# Socket.IO Event Handlers
@socketio.on("connect")
def handle_connect():
    """Handle client WebSocket connection"""
    logger.info(f"Client connected: {request.sid}")
    emit("connected", {"message": "Connected to HandBrake2Resilio API Gateway"})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client WebSocket disconnection"""
    logger.info(f"Client disconnected: {request.sid}")


@socketio.on("request_system_update")
def handle_system_update_request():
    """Handle system update request from client"""
    try:
        handbrake_status = get_handbrake_service_status()
        jobs = get_all_jobs_from_db()

        emit(
            "system_update",
            {
                "timestamp": datetime.utcnow().isoformat(),
                "handbrake_service": handbrake_status,
                "jobs": jobs,
            },
        )
    except Exception as e:
        logger.error(f"Error handling system update request: {e}")
        emit("error", {"message": "Failed to get system update"})


@socketio.on("request_queue_update")
def handle_queue_update_request():
    """Handle queue update request from client"""
    try:
        jobs = get_all_jobs_from_db()
        emit("queue_update", {"jobs": jobs})
    except Exception as e:
        logger.error(f"Error handling queue update request: {e}")
        emit("error", {"message": "Failed to get queue update"})


@socketio.on("join_room")
def handle_join_room(data):
    """Handle room join request"""
    room = data.get("room")
    if room:
        join_room(room)
        emit("joined_room", {"room": room})


@socketio.on("leave_room")
def handle_leave_room(data):
    """Handle room leave request"""
    room = data.get("room")
    if room:
        leave_room(room)
        emit("left_room", {"room": room})


# Initialize SQLite database for job tracking
def init_job_database():
    """Initialize SQLite database for job tracking"""
    db_path = os.getenv("DATABASE_PATH", "/app/data/handbrake2resilio.db")

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                input_path TEXT,
                output_path TEXT,
                quality TEXT,
                resolution TEXT,
                video_bitrate INTEGER,
                audio_bitrate INTEGER,
                status TEXT,
                progress REAL,
                error_message TEXT,
                retry_count INTEGER,
                max_retries INTEGER,
                created_at TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP
            )
            """
        )
        conn.commit()
        logger.info("Job database initialized")


# Initialize database
init_job_database()


def save_job_to_db(job):
    """Save job to SQLite database"""
    db_path = os.getenv("DATABASE_PATH", "/app/data/handbrake2resilio.db")

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO jobs (
                id, input_path, output_path, quality, resolution,
                video_bitrate, audio_bitrate, status, progress,
                error_message, retry_count, max_retries,
                created_at, started_at, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job.id,
                job.input_path,
                job.output_path,
                job.quality,
                job.resolution,
                job.video_bitrate,
                job.audio_bitrate,
                job.status.value,
                job.progress,
                job.error_message,
                job.retry_count,
                job.max_retries,
                job.created_at.isoformat() if job.created_at else None,
                job.started_at.isoformat() if job.started_at else None,
                job.completed_at.isoformat() if job.completed_at else None,
            ),
        )
        conn.commit()


def get_job_from_db(job_id):
    """Get job from SQLite database"""
    db_path = os.getenv("DATABASE_PATH", "/app/data/handbrake2resilio.db")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(
            """
            SELECT * FROM jobs WHERE id = ?
            """,
            (job_id,),
        )
        row = cursor.fetchone()

        if row:
            # Convert row to ConversionJob object
            job = ConversionJob(
                id=row[0],
                input_path=row[1],
                output_path=row[2],
                quality=row[3],
                resolution=row[4],
                video_bitrate=row[5],
                audio_bitrate=row[6],
                status=JobStatus(row[7]),
                progress=row[8],
                error_message=row[9],
                retry_count=row[10],
                max_retries=row[11],
            )
            return job
        return None


def get_all_jobs_from_db():
    """Get all jobs from SQLite database"""
    db_path = os.getenv("DATABASE_PATH", "/app/data/handbrake2resilio.db")

    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC")
        rows = cursor.fetchall()

        jobs = []
        for row in rows:
            job = ConversionJob(
                id=row[0],
                input_path=row[1],
                output_path=row[2],
                quality=row[3],
                resolution=row[4],
                video_bitrate=row[5],
                audio_bitrate=row[6],
                status=JobStatus(row[7]),
                progress=row[8],
                error_message=row[9],
                retry_count=row[10],
                max_retries=row[11],
            )
            jobs.append(job.to_dict())

        return jobs


def get_handbrake_service_status():
    """Check HandBrake service status"""
    try:
        response = requests.get(f"{HANDBRAKE_SERVICE_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"HandBrake service check failed: {e}")
        return None


def forward_to_handbrake_service(endpoint, data=None, method="GET"):
    """Forward request to HandBrake service"""
    try:
        url = f"{HANDBRAKE_SERVICE_URL}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            return None

        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"HandBrake service request failed: {e}")
        return None


@app.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Check HandBrake service
        handbrake_status = get_handbrake_service_status()

        # Check database
        db_path = os.getenv("DATABASE_PATH", "/app/data/handbrake2resilio.db")
        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"error: {e}"

        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "service": "api-gateway",
                "version": "2.0.0",
                "database": db_status,
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
            # Generate JWT token
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
        success = auth_service.register_user(username, password)
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


@app.route("/api/jobs/add", methods=["POST"])
def add_job():
    """Add a new conversion job"""
    try:
        data = request.get_json()

        # Create job object
        job = ConversionJob(
            input_path=data.get("input_path"),
            output_path=data.get("output_path"),
            quality=data.get("quality", "medium"),
            resolution=data.get("resolution", "720x480"),
            video_bitrate=data.get("video_bitrate", 1000),
            audio_bitrate=data.get("audio_bitrate", 96),
        )

        # Save to database
        save_job_to_db(job)

        # Forward to HandBrake service
        handbrake_response = forward_to_handbrake_service(
            "/convert", job.to_dict(), "POST"
        )

        if handbrake_response:
            logger.info(f"Job {job.id} added successfully")
            return jsonify(
                {
                    "message": "Job added successfully",
                    "job_id": job.id,
                    "status": "queued",
                }
            )
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


@app.route("/api/jobs/status/<job_id>")
def get_job_status(job_id):
    """Get job status"""
    try:
        # Get from database
        job = get_job_from_db(job_id)

        if job:
            return jsonify(job.to_dict())
        else:
            return (
                jsonify(
                    {
                        "error": "Job not found",
                        "message": f"Job {job_id} does not exist",
                    }
                ),
                404,
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


@app.route("/api/jobs/list")
def list_jobs():
    """List all jobs"""
    try:
        jobs = get_all_jobs_from_db()
        return jsonify({"jobs": jobs, "count": len(jobs)})

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
def cancel_job(job_id):
    """Cancel a job"""
    try:
        # Forward to HandBrake service
        handbrake_response = forward_to_handbrake_service(
            f"/cancel/{job_id}", method="POST"
        )

        if handbrake_response:
            # Update job in database
            job = get_job_from_db(job_id)
            if job:
                job.status = JobStatus.CANCELLED
                save_job_to_db(job)

            logger.info(f"Job {job_id} cancelled successfully")
            return jsonify({"message": "Job cancelled successfully"})
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


@app.route("/api/system/status")
def get_system_status():
    """Get comprehensive system status"""
    try:
        # Get HandBrake service status
        handbrake_status = get_handbrake_service_status()

        # Get system resources
        import psutil

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Get job statistics
        jobs = get_all_jobs_from_db()
        active_jobs = len([j for j in jobs if j["status"] in ["running", "pending"]])
        completed_jobs = len([j for j in jobs if j["status"] == "completed"])
        failed_jobs = len([j for j in jobs if j["status"] == "failed"])

        status = {
            "service": "api-gateway",
            "status": "healthy",
            "database": "healthy",
            "handbrake_service": handbrake_status is not None,
            "handbrake_status": handbrake_status,
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
            },
            "jobs": {
                "active": active_jobs,
                "completed": completed_jobs,
                "failed": failed_jobs,
                "total": len(jobs),
            },
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
        }

        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({"error": str(e)}), 500


# Add tabs endpoints for frontend compatibility
@app.route("/api/tabs", methods=["GET"])
def get_tabs():
    """Get all tabs (placeholder for frontend compatibility)"""
    try:
        # For now, return empty tabs list since we don't have tab storage
        # This allows the frontend to load without errors
        return jsonify({"success": True, "data": []})
    except Exception as e:
        logger.error(f"Error getting tabs: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tabs", methods=["POST"])
def create_tab():
    """Create a new tab (placeholder for frontend compatibility)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Generate a unique ID for the tab
        import uuid

        tab_id = str(uuid.uuid4())

        # For now, return success with the tab data
        # This allows the frontend to work without errors
        return jsonify(
            {
                "success": True,
                "data": {
                    "id": tab_id,
                    "name": data.get("name", ""),
                    "destination": data.get("destination", ""),
                    "source_type": data.get("source_type", "tv"),
                },
            }
        )
    except Exception as e:
        logger.error(f"Error creating tab: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tabs/<tab_id>", methods=["DELETE"])
def delete_tab(tab_id):
    """Delete a tab (placeholder for frontend compatibility)"""
    try:
        # For now, return success but don't actually delete
        return jsonify({"success": True, "message": "Tab deletion not implemented yet"})
    except Exception as e:
        logger.error(f"Error deleting tab: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tabs/<tab_id>", methods=["PUT"])
def update_tab(tab_id):
    """Update a tab (placeholder for frontend compatibility)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        return jsonify({"success": True, "message": "Tab update not implemented yet"})
    except Exception as e:
        logger.error(f"Error updating tab: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/tabs/<tab_id>/settings", methods=["GET"])
def get_tab_settings(tab_id):
    """Get tab settings"""
    try:
        # Mock settings for testing
        settings = {
            "id": tab_id,
            "auto_convert": True,
            "quality": "high",
            "format": "mp4",
        }
        return jsonify({"success": True, "data": settings})
    except Exception as e:
        logger.error(f"Error getting tab settings: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/log-error", methods=["POST"])
def log_client_error():
    """Log client-side JavaScript errors to server logs"""
    try:
        error_data = request.get_json()
        
        # Extract error information
        error_message = error_data.get('error', 'Unknown error')
        stack_trace = error_data.get('stack', 'No stack trace')
        component_stack = error_data.get('componentStack', 'No component stack')
        timestamp = error_data.get('timestamp', datetime.utcnow().isoformat())
        user_agent = error_data.get('userAgent', 'Unknown')
        url = error_data.get('url', 'Unknown')
        error_type = error_data.get('type', 'javascript_error')
        
        # Log with structured logging
        logger.error(
            "CLIENT-SIDE ERROR",
            error_message=error_message,
            stack_trace=stack_trace,
            component_stack=component_stack,
            timestamp=timestamp,
            user_agent=user_agent,
            url=url,
            error_type=error_type,
            client_ip=request.remote_addr
        )
        
        return jsonify({"status": "logged", "message": "Error logged successfully"}), 200
        
    except Exception as e:
        logger.error("Failed to log client error", error=str(e))
        return jsonify({"status": "error", "message": "Failed to log error"}), 500

@app.route("/api/log-info", methods=["POST"])
def log_client_info():
    """Log client-side info messages to server logs"""
    try:
        info_data = request.get_json()
        
        message = info_data.get('message', 'No message')
        timestamp = info_data.get('timestamp', datetime.utcnow().isoformat())
        user_agent = info_data.get('userAgent', 'Unknown')
        url = info_data.get('url', 'Unknown')
        
        # Log with structured logging
        logger.info(
            "CLIENT-SIDE INFO",
            message=message,
            timestamp=timestamp,
            user_agent=user_agent,
            url=url,
            client_ip=request.remote_addr
        )
        
        return jsonify({"status": "logged", "message": "Info logged successfully"}), 200
        
    except Exception as e:
        logger.error("Failed to log client info", error=str(e))
        return jsonify({"status": "error", "message": "Failed to log info"}), 500

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
                "database": "sqlite",
            },
        }
    )


def start_realtime_updates():
    """Start real-time updates thread"""
    
    def update_loop():
        while True:
            try:
                # Get system status
                system_status = get_system_status()
                
                # Get job queue
                jobs = get_all_jobs_from_db()
                
                # Emit updates to all connected clients
                socketio.emit("system_update", system_status)
                socketio.emit("queue_update", {"jobs": jobs})
                
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                time.sleep(10)  # Wait longer on error
    
    # Start update thread
    update_thread = threading.Thread(target=update_loop, daemon=True)
    update_thread.start()


if __name__ == "__main__":
    # Initialize job database
    init_job_database()
    
    # Start real-time updates
    start_realtime_updates()
    
    # Run the application
    socketio.run(app, host="0.0.0.0", port=8080, debug=False, allow_unsafe_werkzeug=True)
