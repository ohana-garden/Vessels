"""
Health Check System

Provides liveness and readiness probes for Kubernetes/production deployment.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    timestamp: datetime
    duration_ms: float
    metadata: Dict = None

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'duration_ms': self.duration_ms,
            'metadata': self.metadata or {}
        }


class HealthChecker:
    """
    Health check system for Kubernetes liveness/readiness probes.

    Usage:
        health = HealthChecker()

        @health.register('database')
        def check_database():
            try:
                # Test database connection
                return True, "Database connected"
            except Exception as e:
                return False, f"Database error: {e}"

        # In Flask app:
        @app.route('/health')
        def health_check():
            return jsonify(health.check_all())
    """

    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        logger.info("HealthChecker initialized")

    def register(self, name: str):
        """
        Register health check function (decorator).

        Args:
            name: Name of the health check

        Returns:
            Decorator function
        """
        def decorator(func: Callable):
            self.checks[name] = func
            logger.info(f"Registered health check: {name}")
            return func

        return decorator

    def check_all(self) -> Dict:
        """
        Run all health checks.

        Returns:
            Dictionary with overall status and individual check results
        """
        results = []
        start_time = datetime.utcnow()

        for name, check_func in self.checks.items():
            result = self._run_check(name, check_func)
            results.append(result)

        # Determine overall status
        statuses = [r.status for r in results]

        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            'status': overall_status.value,
            'timestamp': datetime.utcnow().isoformat(),
            'duration_ms': duration,
            'checks': [r.to_dict() for r in results]
        }

    def check_single(self, name: str) -> Optional[Dict]:
        """
        Run single health check.

        Args:
            name: Name of check to run

        Returns:
            Check result dict or None if not found
        """
        if name not in self.checks:
            return None

        result = self._run_check(name, self.checks[name])
        return result.to_dict()

    def _run_check(self, name: str, check_func: Callable) -> HealthCheckResult:
        """Execute health check function"""
        start_time = datetime.utcnow()

        try:
            is_healthy, message, *metadata = check_func()

            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY
            meta = metadata[0] if metadata else {}

        except Exception as e:
            logger.error(f"Health check '{name}' failed: {e}")
            status = HealthStatus.UNHEALTHY
            message = f"Check failed: {str(e)}"
            meta = {}

        duration = (datetime.utcnow() - start_time).total_seconds() * 1000

        return HealthCheckResult(
            name=name,
            status=status,
            message=message,
            timestamp=datetime.utcnow(),
            duration_ms=duration,
            metadata=meta
        )

    def get_check_names(self) -> List[str]:
        """Get names of all registered checks"""
        return list(self.checks.keys())


# Global health checker
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get global health checker"""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker


def register_health_check(name: str):
    """
    Decorator to register health check.

    Usage:
        @register_health_check('redis')
        def check_redis():
            try:
                redis_client.ping()
                return True, "Redis OK"
            except Exception as e:
                return False, f"Redis error: {e}"
    """
    checker = get_health_checker()
    return checker.register(name)
