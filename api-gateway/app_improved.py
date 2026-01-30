#!/usr/bin/env python3
"""
Improved HandBrake2Resilio Application
Integrates security, authentication, resource management, and error recovery
"""

import os
import logging
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, request, current_app
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import structlog

# Import our improved modules
from config import config
from auth import init_auth_service, require_auth, require_role
from job_queue import init_job_queue

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

# Global socketio instance
socketio = SocketIO(cors_allowed_origins=config.network.cors_origins)


def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Configure CORS
    CORS(app, origins=config.network.cors_origins)

    # Set maximum content length
    app.config["MAX_CONTENT_LENGTH"] = config.network.max_content_length

    # Initialize services
    logger.info("Initializing HandBrake2Resilio services...")

    # Initialize authentication service
    auth_service = init_auth_service(config)
    app.auth_service = auth_service

    # Initialize job queue
    job_queue = init_job_queue(config)
    app.job_queue = job_queue

    # Initialize SocketIO with the app
    socketio.init_app(app, async_mode="threading")

    # Register blueprints
    from api.auth_routes import auth_bp
    from api.job_routes import job_bp
    from api.system_routes import system_bp
    from api.realtime_routes import realtime_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(job_bp, url_prefix="/api/jobs")
    app.register_blueprint(system_bp, url_prefix="/api/system")
    app.register_blueprint(realtime_bp, url_prefix="/api/realtime")

    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request", "details": str(error)}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": "Forbidden"}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(429)
    def too_many_requests(error):
        return jsonify({"error": "Too many requests"}), 429

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        logger.error(f"Unhandled exception: {error}")
        return jsonify({"error": "Internal server error"}), 500

    # Request logging middleware
    @app.before_request
    def log_request():
        logger.info(
            "Request",
            method=request.method,
            path=request.path,
            remote_addr=request.remote_addr,
            user_agent=request.headers.get("User-Agent", "Unknown"),
        )

    @app.after_request
    def log_response(response):
        logger.info(
            "Response",
            status_code=response.status_code,
            content_length=response.content_length,
        )
        return response

    # Health check endpoint
    @app.route("/health")
    def health_check():
        """Health check endpoint"""
        try:
            # Check system resources
            usage = app.job_queue.resource_monitor.get_system_usage()

            # Check database connectivity
            db_status = "healthy"
            try:
                with app.auth_service.db_path as conn:
                    conn.execute("SELECT 1")
            except Exception as e:
                db_status = f"error: {e}"

            return jsonify(
                {
                    "status": "healthy",
                    "timestamp": datetime.utcnow().isoformat(),
                    "version": "2.0.0",
                    "system": {
                        "cpu_percent": usage["cpu_percent"],
                        "memory_percent": usage["memory_percent"],
                        "disk_free_gb": usage["disk_free_gb"],
                    },
                    "database": db_status,
                    "queue": app.job_queue.get_queue_status(),
                }
            )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({"status": "unhealthy", "error": str(e)}), 500

    # Configuration endpoint
    @app.route("/api/config")
    @require_auth
    def get_config():
        """Get application configuration (without secrets)"""
        return jsonify(config.to_dict())

    # Root endpoint
    @app.route("/")
    def root():
        """Root endpoint with basic info"""
        return jsonify(
            {
                "name": "HandBrake2Resilio",
                "version": "2.0.0",
                "status": "running",
                "docs": "/api/docs",
            }
        )

    logger.info("Application created successfully")
    return app


def start_realtime_updates():
    """Start real-time updates via WebSocket"""

    def emit_updates():
        while True:
            try:
                if socketio:
                    # Emit system status
                    usage = current_app.job_queue.resource_monitor.get_system_usage()
                    queue_status = current_app.job_queue.get_queue_status()

                    socketio.emit(
                        "system_update",
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "usage": usage,
                            "queue": queue_status,
                        },
                    )

                    # Emit job updates
                    running_jobs = list(current_app.job_queue.running_jobs.values())
                    if running_jobs:
                        socketio.emit(
                            "job_updates",
                            {"jobs": [job.to_dict() for job in running_jobs]},
                        )

                time.sleep(5)  # Update every 5 seconds

            except Exception as e:
                logger.error(f"Error in real-time updates: {e}")
                time.sleep(10)  # Wait longer on error

    update_thread = threading.Thread(target=emit_updates, daemon=True)
    update_thread.start()
    logger.info("Started real-time updates thread")


def start_metrics_collection():
    """Start metrics collection for monitoring"""

    def collect_metrics():
        while True:
            try:
                # Collect system metrics
                usage = current_app.job_queue.resource_monitor.get_system_usage()
                queue_status = current_app.job_queue.get_queue_status()

                # Log metrics for monitoring
                logger.info(
                    "System metrics",
                    cpu_percent=usage["cpu_percent"],
                    memory_percent=usage["memory_percent"],
                    queue_size=queue_status["queue_size"],
                    running_jobs=queue_status["running_jobs"],
                )

                time.sleep(60)  # Collect metrics every minute

            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                time.sleep(60)

    metrics_thread = threading.Thread(target=collect_metrics, daemon=True)
    metrics_thread.start()
    logger.info("Started metrics collection thread")


def graceful_shutdown(app):
    """Graceful shutdown handler"""

    def shutdown_handler(signum, frame):
        logger.info("Received shutdown signal, starting graceful shutdown...")

        # Shutdown job queue
        if hasattr(app, "job_queue"):
            app.job_queue.shutdown()

        # Close database connections
        # (SQLite connections are automatically closed)

        logger.info("Graceful shutdown completed")
        os._exit(0)

    return shutdown_handler


if __name__ == "__main__":
    # Create application
    app = create_app()

    # Start background threads
    with app.app_context():
        start_realtime_updates()
        start_metrics_collection()

    # Log startup information
    logger.info("Starting HandBrake2Resilio server...")
    logger.info("Configuration", **config.to_dict())

    # Start the server
    socketio.run(
        app,
        host=config.network.host,
        port=config.network.port,
        debug=False,
        use_reloader=False,
    )
