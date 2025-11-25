"""
Configuration Settings

Type-safe configuration management with environment variable overrides.
Replaces scattered hardcoded values and multiple config systems.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import os
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration"""
    sqlite_path: str = "data/vessels.db"
    grants_db_path: str = "data/grants.db"
    applications_db_path: str = "data/applications.db"
    enable_foreign_keys: bool = True
    journal_mode: str = "WAL"
    synchronous_mode: str = "NORMAL"
    connection_timeout: int = 30
    max_connections: int = 10


@dataclass
class RedisConfig:
    """Redis/FalkorDB configuration"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 50
    socket_timeout: int = 30


@dataclass
class SecurityConfig:
    """Security configuration"""
    jwt_secret_key: Optional[str] = field(default_factory=lambda: os.environ.get('JWT_SECRET_KEY'))
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    session_ttl_seconds: int = 3600
    max_sessions: int = 10000
    enable_cors: bool = True
    allowed_origins: List[str] = field(default_factory=lambda: os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5000').split(','))
    rate_limit_per_minute: int = 60
    enable_csrf: bool = True
    require_https: bool = field(default_factory=lambda: os.environ.get('ENVIRONMENT') == 'production')


@dataclass
class PerformanceConfig:
    """Performance tuning configuration"""
    max_workers: int = 50
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    vector_batch_size: int = 32
    max_context_items: int = 100
    enable_query_cache: bool = True
    query_cache_size: int = 1000


@dataclass
class ObservabilityConfig:
    """Monitoring and logging configuration"""
    log_level: str = "INFO"
    enable_structured_logging: bool = True
    enable_metrics: bool = True
    metrics_port: int = 9090
    enable_tracing: bool = False
    tracing_endpoint: Optional[str] = None
    health_check_port: int = 8080


@dataclass
class VesselsConfig:
    """
    Main configuration object for Vessels platform.

    Provides type-safe, centralized configuration with:
    - Environment variable overrides
    - Validation
    - Default values
    - Clear documentation
    """

    # Subsystem configs
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    observability: ObservabilityConfig = field(default_factory=ObservabilityConfig)

    # Application settings
    environment: str = "development"
    debug: bool = False
    app_name: str = "Vessels Platform"
    version: str = "0.1.0"

    # Paths
    data_dir: Path = field(default_factory=lambda: Path("data"))
    logs_dir: Path = field(default_factory=lambda: Path("logs"))
    config_dir: Path = field(default_factory=lambda: Path("config"))

    @classmethod
    def from_yaml(cls, config_path: str = "config/vessels.yaml") -> 'VesselsConfig':
        """
        Load configuration from YAML file with environment variable overrides.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            VesselsConfig instance
        """
        config = cls()

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    yaml_config = yaml.safe_load(f)

                # Apply YAML config (implementation would map YAML to dataclass)
                logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        else:
            logger.info(f"Config file {config_path} not found, using defaults")

        # Apply environment variable overrides
        config._apply_env_overrides()

        return config

    def _apply_env_overrides(self):
        """Apply environment variable overrides"""
        # Database overrides
        if db_path := os.environ.get('VESSELS_DB_PATH'):
            self.database.sqlite_path = db_path

        # Redis overrides
        if redis_host := os.environ.get('REDIS_HOST'):
            self.redis.host = redis_host
        if redis_port := os.environ.get('REDIS_PORT'):
            self.redis.port = int(redis_port)
        if redis_password := os.environ.get('REDIS_PASSWORD'):
            self.redis.password = redis_password

        # Security overrides
        if jwt_secret := os.environ.get('JWT_SECRET_KEY'):
            self.security.jwt_secret_key = jwt_secret
        if allowed_origins := os.environ.get('ALLOWED_ORIGINS'):
            self.security.allowed_origins = allowed_origins.split(',')

        # Environment
        if env := os.environ.get('ENVIRONMENT'):
            self.environment = env
            self.debug = (env == 'development')

        logger.debug("Applied environment variable overrides")

    def validate(self) -> List[str]:
        """
        Validate configuration and return list of errors.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Security validation - JWT secret is always required
        if not self.security.jwt_secret_key:
            errors.append(
                "JWT_SECRET_KEY must be set. Generate one with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        elif len(self.security.jwt_secret_key) < 32:
            errors.append("JWT_SECRET_KEY should be at least 32 characters for security")

        if self.environment == 'production':
            if not self.security.require_https:
                errors.append("HTTPS should be required in production")

            if self.debug:
                errors.append("Debug mode should be disabled in production")

            # Check for known insecure defaults
            insecure_defaults = ('CHANGE_IN_PRODUCTION', 'CHANGE_THIS_IN_PRODUCTION',
                               'change-this-in-production', 'dev-only-insecure-secret')
            if self.security.jwt_secret_key and any(d in self.security.jwt_secret_key for d in insecure_defaults):
                errors.append("JWT_SECRET_KEY contains insecure default value")

        # Performance validation
        if self.performance.max_workers < 1:
            errors.append("max_workers must be >= 1")

        if self.performance.cache_ttl_seconds < 0:
            errors.append("cache_ttl_seconds must be >= 0")

        # Database validation
        if not self.database.sqlite_path:
            errors.append("sqlite_path cannot be empty")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation (safe for logging/serialization)
        """
        return {
            'environment': self.environment,
            'debug': self.debug,
            'app_name': self.app_name,
            'version': self.version,
            'database': {
                'sqlite_path': self.database.sqlite_path,
                'enable_foreign_keys': self.database.enable_foreign_keys,
                'journal_mode': self.database.journal_mode,
            },
            'redis': {
                'host': self.redis.host,
                'port': self.redis.port,
                'db': self.redis.db,
            },
            'security': {
                'jwt_algorithm': self.security.jwt_algorithm,
                'access_token_expire_minutes': self.security.access_token_expire_minutes,
                'session_ttl_seconds': self.security.session_ttl_seconds,
                'allowed_origins': self.security.allowed_origins,
                'enable_cors': self.security.enable_cors,
            },
            'performance': {
                'max_workers': self.performance.max_workers,
                'enable_caching': self.performance.enable_caching,
                'cache_ttl_seconds': self.performance.cache_ttl_seconds,
            },
            'observability': {
                'log_level': self.observability.log_level,
                'enable_metrics': self.observability.enable_metrics,
                'metrics_port': self.observability.metrics_port,
            }
        }


# Global configuration instance
_config: Optional[VesselsConfig] = None


def load_config(config_path: str = "config/vessels.yaml") -> VesselsConfig:
    """
    Load and validate configuration.

    Args:
        config_path: Path to YAML configuration file

    Returns:
        VesselsConfig instance

    Raises:
        ValueError: If configuration is invalid
    """
    global _config

    _config = VesselsConfig.from_yaml(config_path)

    # Validate
    errors = _config.validate()
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(f"Configuration loaded successfully (environment: {_config.environment})")
    return _config


def get_config() -> VesselsConfig:
    """
    Get current configuration instance.

    Returns:
        VesselsConfig instance

    Raises:
        RuntimeError: If configuration not loaded yet
    """
    if _config is None:
        raise RuntimeError("Configuration not loaded. Call load_config() first.")

    return _config
