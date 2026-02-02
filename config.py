#!/usr/bin/env python3
"""
Configuration management for HandBrake2Resilio
Enhanced with production-ready features and validation
"""

import os
import secrets
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Security configuration with enhanced validation"""

    jwt_secret_key: str
    jwt_expiration_hours: int = 24
    bcrypt_rounds: int = 12
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    jwt_algorithm: str = "HS256"
    session_timeout_minutes: int = 60

    def __post_init__(self):
        """Validate security configuration"""
        if self.bcrypt_rounds < 10 or self.bcrypt_rounds > 16:
            raise ValueError("BCRYPT_ROUNDS must be between 10 and 16")
        if self.jwt_expiration_hours < 1 or self.jwt_expiration_hours > 168:
            raise ValueError("JWT_EXPIRATION_HOURS must be between 1 and 168")
        if self.max_login_attempts < 1 or self.max_login_attempts > 10:
            raise ValueError("MAX_LOGIN_ATTEMPTS must be between 1 and 10")


@dataclass
class ResourceConfig:
    """Resource management configuration with enhanced limits"""

    max_concurrent_jobs: int = 2
    cpu_limit_percent: float = 80.0
    memory_limit_percent: float = 80.0
    disk_limit_percent: float = 90.0
    job_timeout_seconds: int = 3600
    retry_attempts: int = 3
    min_memory_gb: float = 2.0
    min_disk_gb: float = 5.0
    max_file_size_gb: float = 10.0

    def __post_init__(self):
        """Validate resource configuration"""
        if self.cpu_limit_percent < 1 or self.cpu_limit_percent > 100:
            raise ValueError("CPU_LIMIT_PERCENT must be between 1 and 100")
        if self.memory_limit_percent < 1 or self.memory_limit_percent > 100:
            raise ValueError("MEMORY_LIMIT_PERCENT must be between 1 and 100")
        if self.disk_limit_percent < 1 or self.disk_limit_percent > 100:
            raise ValueError("DISK_LIMIT_PERCENT must be between 1 and 100")
        if self.max_concurrent_jobs < 1 or self.max_concurrent_jobs > 20:
            raise ValueError("MAX_CONCURRENT_JOBS must be between 1 and 20")


@dataclass
class StorageConfig:
    """Storage configuration with path validation"""

    database_path: str = "/app/data/handbrake2resilio.db"
    logs_directory: str = "/app/logs"
    temp_directory: str = "/app/temp"
    upload_directory: str = "/app/uploads"
    backup_directory: str = "/app/backups"
    max_log_size_mb: int = 100
    max_log_files: int = 10

    def __post_init__(self):
        """Validate storage paths"""
        for path_name, path_value in [
            ("database_path", self.database_path),
            ("logs_directory", self.logs_directory),
            ("temp_directory", self.temp_directory),
            ("upload_directory", self.upload_directory),
            ("backup_directory", self.backup_directory),
        ]:
            if not path_value:
                raise ValueError(f"{path_name} cannot be empty")


@dataclass
class NetworkConfig:
    """Network configuration with enhanced CORS support"""

    host: str = "0.0.0.0"
    port: int = 8080
    cors_origins: List[str] = field(default_factory=list)
    max_content_length: int = 16 * 1024 * 1024  # 16MB
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour
    websocket_ping_interval: int = 25
    websocket_ping_timeout: int = 10

    def __post_init__(self):
        """Validate network configuration"""
        if self.port < 1024 or self.port > 65535:
            raise ValueError("PORT must be between 1024 and 65535")
        if self.max_content_length < 1024 * 1024:  # 1MB minimum
            raise ValueError("MAX_CONTENT_LENGTH must be at least 1MB")


@dataclass
class VideoConfig:
    """Video processing configuration with quality presets"""

    default_quality: int = 23
    default_resolution: str = "720x480"
    default_video_bitrate: int = 1000
    default_audio_bitrate: int = 96
    supported_formats: List[str] = field(default_factory=list)
    quality_presets: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    max_duration_hours: int = 24

    def __post_init__(self):
        """Validate video configuration"""
        if self.default_quality < 0 or self.default_quality > 51:
            raise ValueError("DEFAULT_QUALITY must be between 0 and 51")
        if self.default_video_bitrate < 100 or self.default_video_bitrate > 10000:
            raise ValueError("DEFAULT_VIDEO_BITRATE must be between 100 and 10000")
        if self.default_audio_bitrate < 32 or self.default_audio_bitrate > 320:
            raise ValueError("DEFAULT_AUDIO_BITRATE must be between 32 and 320")
        if self.max_duration_hours < 1 or self.max_duration_hours > 168:
            raise ValueError("MAX_DURATION_HOURS must be between 1 and 168 (1 week)")

        # Validate resolution format (WxH)
        if not self.default_resolution or "x" not in self.default_resolution:
            raise ValueError(
                "DEFAULT_RESOLUTION must be in format WIDTHxHEIGHT (e.g., 1920x1080)"
            )

        try:
            width, height = map(int, self.default_resolution.split("x"))
            if width < 320 or width > 7680 or height < 240 or height > 4320:
                raise ValueError(
                    "Resolution dimensions out of valid range " "(320-7680 x 240-4320)"
                )
        except ValueError:
            raise ValueError(
                "DEFAULT_RESOLUTION must be in format WIDTHxHEIGHT "
                "with valid integers"
            )


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration"""

    enable_metrics: bool = True
    metrics_port: int = 9090
    log_level: str = "INFO"
    enable_health_checks: bool = True
    health_check_interval: int = 30
    enable_structured_logging: bool = True
    log_format: str = "json"  # json or text
    enable_request_logging: bool = True
    enable_performance_monitoring: bool = True

    def __post_init__(self):
        """Validate monitoring configuration"""
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_log_levels}")
        if self.metrics_port < 1024 or self.metrics_port > 65535:
            raise ValueError("METRICS_PORT must be between 1024 and 65535")


@dataclass
class Config:
    """Main configuration class with enhanced validation"""

    security: SecurityConfig
    resources: ResourceConfig
    storage: StorageConfig
    network: NetworkConfig
    video: VideoConfig
    monitoring: MonitoringConfig
    environment: str = "production"

    def __post_init__(self):
        """Initialize default values and validate configuration"""
        # Set default CORS origins if not provided
        if not self.network.cors_origins:
            self.network.cors_origins = [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:3002",
                "http://192.168.10.18:3000",
                "http://192.168.10.18:3001",
                "http://192.168.10.18:3002",
            ]

        # Set default supported formats if not provided
        if not self.video.supported_formats:
            self.video.supported_formats = [
                ".mp4",
                ".mkv",
                ".avi",
                ".mov",
                ".wmv",
                ".flv",
                ".webm",
            ]

        # Set default quality presets
        if not self.video.quality_presets:
            self.video.quality_presets = {
                "fast": {"quality": 28, "resolution": "720x480", "video_bitrate": 800},
                "standard": {
                    "quality": 23,
                    "resolution": "1280x720",
                    "video_bitrate": 1500,
                },
                "high": {
                    "quality": 20,
                    "resolution": "1920x1080",
                    "video_bitrate": 2500,
                },
                "ultra": {
                    "quality": 18,
                    "resolution": "1920x1080",
                    "video_bitrate": 4000,
                },
            }

        # Validate environment
        valid_environments = ["development", "staging", "production"]
        if self.environment not in valid_environments:
            raise ValueError(f"ENVIRONMENT must be one of {valid_environments}")

    def to_dict(self) -> dict:
        """Convert config to dictionary for logging (excluding sensitive data)"""
        return {
            "environment": self.environment,
            "security": {
                "jwt_expiration_hours": self.security.jwt_expiration_hours,
                "bcrypt_rounds": self.security.bcrypt_rounds,
                "max_login_attempts": self.security.max_login_attempts,
                "lockout_duration_minutes": self.security.lockout_duration_minutes,
                "jwt_algorithm": self.security.jwt_algorithm,
                "session_timeout_minutes": self.security.session_timeout_minutes,
            },
            "resources": {
                "max_concurrent_jobs": self.resources.max_concurrent_jobs,
                "cpu_limit_percent": self.resources.cpu_limit_percent,
                "memory_limit_percent": self.resources.memory_limit_percent,
                "disk_limit_percent": self.resources.disk_limit_percent,
                "job_timeout_seconds": self.resources.job_timeout_seconds,
                "retry_attempts": self.resources.retry_attempts,
                "min_memory_gb": self.resources.min_memory_gb,
                "min_disk_gb": self.resources.min_disk_gb,
                "max_file_size_gb": self.resources.max_file_size_gb,
            },
            "storage": {
                "database_path": self.storage.database_path,
                "logs_directory": self.storage.logs_directory,
                "temp_directory": self.storage.temp_directory,
                "upload_directory": self.storage.upload_directory,
                "backup_directory": self.storage.backup_directory,
                "max_log_size_mb": self.storage.max_log_size_mb,
                "max_log_files": self.storage.max_log_files,
            },
            "network": {
                "host": self.network.host,
                "port": self.network.port,
                "cors_origins": self.network.cors_origins,
                "max_content_length": self.network.max_content_length,
                "rate_limit_requests": self.network.rate_limit_requests,
                "rate_limit_window": self.network.rate_limit_window,
            },
            "video": {
                "default_quality": self.video.default_quality,
                "default_resolution": self.video.default_resolution,
                "default_video_bitrate": self.video.default_video_bitrate,
                "default_audio_bitrate": self.video.default_audio_bitrate,
                "supported_formats": self.video.supported_formats,
                "max_duration_hours": self.video.max_duration_hours,
            },
            "monitoring": {
                "enable_metrics": self.monitoring.enable_metrics,
                "metrics_port": self.monitoring.metrics_port,
                "log_level": self.monitoring.log_level,
                "enable_health_checks": self.monitoring.enable_health_checks,
                "health_check_interval": self.monitoring.health_check_interval,
                "enable_structured_logging": self.monitoring.enable_structured_logging,
                "log_format": self.monitoring.log_format,
                "enable_request_logging": self.monitoring.enable_request_logging,
                "enable_performance_monitoring": self.monitoring.enable_performance_monitoring,
            },
        }

    def validate_system_requirements(self) -> bool:
        """Validate that the system meets minimum requirements"""
        try:
            import psutil

            # Check available memory
            memory = psutil.virtual_memory()
            available_memory_gb = memory.available / (1024**3)
            if available_memory_gb < self.resources.min_memory_gb:
                logger.error(
                    f"Insufficient memory: {available_memory_gb:.1f}GB available, {self.resources.min_memory_gb}GB required"
                )
                return False

            # Check available disk space
            disk = psutil.disk_usage("/")
            available_disk_gb = disk.free / (1024**3)
            if available_disk_gb < self.resources.min_disk_gb:
                logger.error(
                    f"Insufficient disk space: {available_disk_gb:.1f}GB available, {self.resources.min_disk_gb}GB required"
                )
                return False

            logger.info(
                f"System requirements validated: {available_memory_gb:.1f}GB memory, {available_disk_gb:.1f}GB disk space"
            )
            return True

        except ImportError:
            logger.warning(
                "psutil not available, skipping system requirements validation"
            )
            return True


def load_config() -> Config:
    """Load configuration from environment variables with enhanced error handling"""

    try:
        # Generate JWT secret if not provided
        jwt_secret_key = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret_key:
            jwt_secret_key = secrets.token_urlsafe(32)
            logger.warning("JWT_SECRET_KEY not provided, generated new secret")

        # Security config
        security = SecurityConfig(
            jwt_secret_key=jwt_secret_key,
            jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
            bcrypt_rounds=int(os.getenv("BCRYPT_ROUNDS", "12")),
            max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
            lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", "15")),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            session_timeout_minutes=int(os.getenv("SESSION_TIMEOUT_MINUTES", "60")),
        )

        # Resource config
        resources = ResourceConfig(
            max_concurrent_jobs=int(os.getenv("MAX_CONCURRENT_JOBS", "2")),
            cpu_limit_percent=float(os.getenv("CPU_LIMIT_PERCENT", "80.0")),
            memory_limit_percent=float(os.getenv("MEMORY_LIMIT_PERCENT", "80.0")),
            disk_limit_percent=float(os.getenv("DISK_LIMIT_PERCENT", "90.0")),
            job_timeout_seconds=int(os.getenv("JOB_TIMEOUT_SECONDS", "3600")),
            retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3")),
            min_memory_gb=float(os.getenv("MIN_MEMORY_GB", "2.0")),
            min_disk_gb=float(os.getenv("MIN_DISK_GB", "5.0")),
            max_file_size_gb=float(os.getenv("MAX_FILE_SIZE_GB", "10.0")),
        )

        # Storage config
        storage = StorageConfig(
            database_path=os.getenv("DATABASE_PATH", "/app/data/handbrake2resilio.db"),
            logs_directory=os.getenv("LOGS_DIRECTORY", "/app/logs"),
            temp_directory=os.getenv("TEMP_DIRECTORY", "/app/temp"),
            upload_directory=os.getenv("UPLOAD_DIRECTORY", "/app/uploads"),
            backup_directory=os.getenv("BACKUP_DIRECTORY", "/app/backups"),
            max_log_size_mb=int(os.getenv("MAX_LOG_SIZE_MB", "100")),
            max_log_files=int(os.getenv("MAX_LOG_FILES", "10")),
        )

        # Network config
        network = NetworkConfig(
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8080")),
            max_content_length=int(
                os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024))
            ),
            rate_limit_requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            rate_limit_window=int(os.getenv("RATE_LIMIT_WINDOW", "3600")),
            websocket_ping_interval=int(os.getenv("WEBSOCKET_PING_INTERVAL", "25")),
            websocket_ping_timeout=int(os.getenv("WEBSOCKET_PING_TIMEOUT", "10")),
        )

        # Video config
        video = VideoConfig(
            default_quality=int(os.getenv("DEFAULT_QUALITY", "23")),
            default_resolution=os.getenv("DEFAULT_RESOLUTION", "720x480"),
            default_video_bitrate=int(os.getenv("DEFAULT_VIDEO_BITRATE", "1000")),
            default_audio_bitrate=int(os.getenv("DEFAULT_AUDIO_BITRATE", "96")),
            max_duration_hours=int(os.getenv("MAX_DURATION_HOURS", "24")),
        )

        # Monitoring config
        monitoring = MonitoringConfig(
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            metrics_port=int(os.getenv("METRICS_PORT", "9090")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            enable_health_checks=os.getenv("ENABLE_HEALTH_CHECKS", "true").lower()
            == "true",
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
            enable_structured_logging=os.getenv(
                "ENABLE_STRUCTURED_LOGGING", "true"
            ).lower()
            == "true",
            log_format=os.getenv("LOG_FORMAT", "json"),
            enable_request_logging=os.getenv("ENABLE_REQUEST_LOGGING", "true").lower()
            == "true",
            enable_performance_monitoring=os.getenv(
                "ENABLE_PERFORMANCE_MONITORING", "true"
            ).lower()
            == "true",
        )

        # Environment
        environment = os.getenv("ENVIRONMENT", "production").lower()

        config = Config(
            security=security,
            resources=resources,
            storage=storage,
            network=network,
            video=video,
            monitoring=monitoring,
            environment=environment,
        )

        # Create necessary directories
        for directory in [
            storage.logs_directory,
            storage.temp_directory,
            storage.upload_directory,
            storage.backup_directory,
            os.path.dirname(storage.database_path),
        ]:
            Path(directory).mkdir(parents=True, exist_ok=True)

        # Validate system requirements
        if not config.validate_system_requirements():
            logger.error("System requirements validation failed")
            sys.exit(1)

        logger.info("Configuration loaded successfully", extra=config.to_dict())
        return config

    except ValueError as e:
        logger.error(f"Configuration validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)


# Global config instance
config = load_config()
