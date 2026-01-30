#!/usr/bin/env python3
"""
Configuration management for HandBrake2Resilio
"""

import os
import secrets
from dataclasses import dataclass
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class SecurityConfig:
    """Security configuration"""
    jwt_secret: str
    jwt_expiration_hours: int = 24
    bcrypt_rounds: int = 12
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15

@dataclass
class ResourceConfig:
    """Resource management configuration"""
    max_concurrent_jobs: int = 2
    cpu_limit_percent: float = 80.0
    memory_limit_percent: float = 80.0
    disk_limit_percent: float = 90.0
    job_timeout_seconds: int = 3600
    retry_attempts: int = 3

@dataclass
class StorageConfig:
    """Storage configuration"""
    database_path: str = "/app/data/handbrake2resilio.db"
    logs_directory: str = "/app/logs"
    temp_directory: str = "/app/temp"
    upload_directory: str = "/app/uploads"

@dataclass
class NetworkConfig:
    """Network configuration"""
    host: str = "0.0.0.0"
    port: int = 8080
    cors_origins: List[str] = None
    max_content_length: int = 16 * 1024 * 1024  # 16MB

@dataclass
class VideoConfig:
    """Video processing configuration"""
    default_quality: int = 23
    default_resolution: str = "720x480"
    default_video_bitrate: int = 1000
    default_audio_bitrate: int = 96
    supported_formats: List[str] = None

@dataclass
class Config:
    """Main configuration class"""
    security: SecurityConfig
    resources: ResourceConfig
    storage: StorageConfig
    network: NetworkConfig
    video: VideoConfig

    def __post_init__(self):
        """Initialize default values after dataclass creation"""
        if self.network.cors_origins is None:
            self.network.cors_origins = ["http://localhost:3000", "http://localhost:3001"]
        
        if self.video.supported_formats is None:
            self.video.supported_formats = [".mp4", ".mkv", ".avi", ".mov", ".wmv"]

    def to_dict(self) -> dict:
        """Convert config to dictionary for logging (excluding sensitive data)"""
        return {
            "security": {
                "jwt_expiration_hours": self.security.jwt_expiration_hours,
                "bcrypt_rounds": self.security.bcrypt_rounds,
                "max_login_attempts": self.security.max_login_attempts,
                "lockout_duration_minutes": self.security.lockout_duration_minutes
            },
            "resources": {
                "max_concurrent_jobs": self.resources.max_concurrent_jobs,
                "cpu_limit_percent": self.resources.cpu_limit_percent,
                "memory_limit_percent": self.resources.memory_limit_percent,
                "disk_limit_percent": self.resources.disk_limit_percent,
                "job_timeout_seconds": self.resources.job_timeout_seconds,
                "retry_attempts": self.resources.retry_attempts
            },
            "storage": {
                "database_path": self.storage.database_path,
                "logs_directory": self.storage.logs_directory,
                "temp_directory": self.storage.temp_directory,
                "upload_directory": self.storage.upload_directory
            },
            "network": {
                "host": self.network.host,
                "port": self.network.port,
                "cors_origins": self.network.cors_origins,
                "max_content_length": self.network.max_content_length
            },
            "video": {
                "default_quality": self.video.default_quality,
                "default_resolution": self.video.default_resolution,
                "default_video_bitrate": self.video.default_video_bitrate,
                "default_audio_bitrate": self.video.default_audio_bitrate,
                "supported_formats": self.video.supported_formats
            }
        }

def load_config() -> Config:
    """Load configuration from environment variables"""
    
    # Generate JWT secret if not provided
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        jwt_secret = secrets.token_urlsafe(32)
        logger.warning("JWT_SECRET not provided, generated new secret")
    
    # Security config
    security = SecurityConfig(
        jwt_secret=jwt_secret,
        jwt_expiration_hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")),
        bcrypt_rounds=int(os.getenv("BCRYPT_ROUNDS", "12")),
        max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
        lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
    )
    
    # Resource config
    resources = ResourceConfig(
        max_concurrent_jobs=int(os.getenv("MAX_CONCURRENT_JOBS", "2")),
        cpu_limit_percent=float(os.getenv("CPU_LIMIT_PERCENT", "80.0")),
        memory_limit_percent=float(os.getenv("MEMORY_LIMIT_PERCENT", "80.0")),
        disk_limit_percent=float(os.getenv("DISK_LIMIT_PERCENT", "90.0")),
        job_timeout_seconds=int(os.getenv("JOB_TIMEOUT_SECONDS", "3600")),
        retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3"))
    )
    
    # Storage config
    storage = StorageConfig(
        database_path=os.getenv("DATABASE_PATH", "/app/data/handbrake2resilio.db"),
        logs_directory=os.getenv("LOGS_DIRECTORY", "/app/logs"),
        temp_directory=os.getenv("TEMP_DIRECTORY", "/app/temp"),
        upload_directory=os.getenv("UPLOAD_DIRECTORY", "/app/uploads")
    )
    
    # Network config
    network = NetworkConfig(
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        max_content_length=int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024))
    )
    
    # Video config
    video = VideoConfig(
        default_quality=int(os.getenv("DEFAULT_QUALITY", "23")),
        default_resolution=os.getenv("DEFAULT_RESOLUTION", "720x480"),
        default_video_bitrate=int(os.getenv("DEFAULT_VIDEO_BITRATE", "1000")),
        default_audio_bitrate=int(os.getenv("DEFAULT_AUDIO_BITRATE", "96"))
    )
    
    config = Config(
        security=security,
        resources=resources,
        storage=storage,
        network=network,
        video=video
    )
    
    # Create necessary directories
    os.makedirs(storage.logs_directory, exist_ok=True)
    os.makedirs(storage.temp_directory, exist_ok=True)
    os.makedirs(storage.upload_directory, exist_ok=True)
    os.makedirs(os.path.dirname(storage.database_path), exist_ok=True)
    
    # Validate resource limits
    if resources.cpu_limit_percent > 100 or resources.cpu_limit_percent < 1:
        raise ValueError("CPU_LIMIT_PERCENT must be between 1 and 100")
    
    if resources.memory_limit_percent > 100 or resources.memory_limit_percent < 1:
        raise ValueError("MEMORY_LIMIT_PERCENT must be between 1 and 100")
    
    if resources.disk_limit_percent > 100 or resources.disk_limit_percent < 1:
        raise ValueError("DISK_LIMIT_PERCENT must be between 1 and 100")
    
    logger.info("Configuration loaded successfully")
    return config

# Global config instance
config = load_config() 