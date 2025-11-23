"""
Metrics Collection

Prometheus-compatible metrics for monitoring.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Dict, Callable, Any
import time
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Base metric class"""
    name: str
    help_text: str
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Counter(Metric):
    """Counter metric (monotonically increasing)"""
    value: float = 0.0

    def inc(self, amount: float = 1.0):
        """Increment counter"""
        self.value += amount


@dataclass
class Gauge(Metric):
    """Gauge metric (can go up or down)"""
    value: float = 0.0

    def set(self, value: float):
        """Set gauge value"""
        self.value = value

    def inc(self, amount: float = 1.0):
        """Increase gauge"""
        self.value += amount

    def dec(self, amount: float = 1.0):
        """Decrease gauge"""
        self.value -= amount


@dataclass
class Histogram(Metric):
    """Histogram metric for tracking distributions"""
    observations: list = field(default_factory=list)
    sum: float = 0.0
    count: int = 0

    def observe(self, value: float):
        """Record observation"""
        self.observations.append(value)
        self.sum += value
        self.count += 1

    def quantile(self, q: float) -> float:
        """Calculate quantile"""
        if not self.observations:
            return 0.0

        sorted_obs = sorted(self.observations)
        idx = int(q * len(sorted_obs))
        return sorted_obs[min(idx, len(sorted_obs) - 1)]


class MetricsCollector:
    """
    Metrics collector for Prometheus export.

    Tracks counters, gauges, and histograms for monitoring.
    """

    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        self.lock = threading.Lock()

        # Register default metrics
        self._register_defaults()

    def _register_defaults(self):
        """Register default application metrics"""
        # Request metrics
        self.counter('requests_total', 'Total HTTP requests')
        self.counter('requests_errors', 'Total HTTP errors')
        self.histogram('request_duration_seconds', 'HTTP request duration')

        # Agent metrics
        self.gauge('agents_active', 'Number of active agents')
        self.counter('agents_created_total', 'Total agents created')
        self.counter('agents_failed_total', 'Total agent failures')

        # Memory metrics
        self.counter('memories_stored_total', 'Total memories stored')
        self.histogram('memory_search_duration_seconds', 'Memory search duration')

        # Constraint metrics
        self.counter('constraint_violations_total', 'Total constraint violations')
        self.counter('actions_gated_total', 'Total actions gated')

        # Database metrics
        self.histogram('db_query_duration_seconds', 'Database query duration')
        self.counter('db_queries_total', 'Total database queries')

    def counter(self, name: str, help_text: str, labels: Dict[str, str] = None) -> Counter:
        """
        Get or create counter metric.

        Args:
            name: Metric name
            help_text: Description
            labels: Optional labels

        Returns:
            Counter instance
        """
        with self.lock:
            key = self._metric_key(name, labels)
            if key not in self.counters:
                self.counters[key] = Counter(name, help_text, labels or {})
            return self.counters[key]

    def gauge(self, name: str, help_text: str, labels: Dict[str, str] = None) -> Gauge:
        """Get or create gauge metric"""
        with self.lock:
            key = self._metric_key(name, labels)
            if key not in self.gauges:
                self.gauges[key] = Gauge(name, help_text, labels or {})
            return self.gauges[key]

    def histogram(self, name: str, help_text: str, labels: Dict[str, str] = None) -> Histogram:
        """Get or create histogram metric"""
        with self.lock:
            key = self._metric_key(name, labels)
            if key not in self.histograms:
                self.histograms[key] = Histogram(name, help_text, labels or {})
            return self.histograms[key]

    def _metric_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Generate unique key for metric"""
        if not labels:
            return name

        label_str = ','.join(f'{k}={v}' for k, v in sorted(labels.items()))
        return f'{name}{{{label_str}}}'

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []

        with self.lock:
            # Export counters
            for counter in self.counters.values():
                lines.append(f'# HELP {counter.name} {counter.help_text}')
                lines.append(f'# TYPE {counter.name} counter')
                label_str = self._format_labels(counter.labels)
                lines.append(f'{counter.name}{label_str} {counter.value}')

            # Export gauges
            for gauge in self.gauges.values():
                lines.append(f'# HELP {gauge.name} {gauge.help_text}')
                lines.append(f'# TYPE {gauge.name} gauge')
                label_str = self._format_labels(gauge.labels)
                lines.append(f'{gauge.name}{label_str} {gauge.value}')

            # Export histograms
            for hist in self.histograms.values():
                lines.append(f'# HELP {hist.name} {hist.help_text}')
                lines.append(f'# TYPE {hist.name} histogram')
                label_str = self._format_labels(hist.labels)

                # Histogram buckets
                lines.append(f'{hist.name}_sum{label_str} {hist.sum}')
                lines.append(f'{hist.name}_count{label_str} {hist.count}')

        return '\n'.join(lines) + '\n'

    def _format_labels(self, labels: Dict[str, str]) -> str:
        """Format labels for Prometheus"""
        if not labels:
            return ''

        label_pairs = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return '{' + ','.join(label_pairs) + '}'

    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics statistics"""
        with self.lock:
            return {
                'counters': len(self.counters),
                'gauges': len(self.gauges),
                'histograms': len(self.histograms),
                'timestamp': datetime.utcnow().isoformat()
            }


# Global metrics collector
_collector: MetricsCollector = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector


def track_time(metric_name: str = 'function_duration_seconds', labels: Dict[str, str] = None):
    """
    Decorator to track function execution time.

    Usage:
        @track_time('memory_search_duration_seconds')
        def search_memories(query):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                collector = get_metrics_collector()
                hist = collector.histogram(metric_name, f'Duration of {func.__name__}', labels)
                hist.observe(duration)

        return wrapper
    return decorator


def track_count(metric_name: str, labels: Dict[str, str] = None):
    """
    Decorator to track function call count.

    Usage:
        @track_count('agents_created_total')
        def create_agent(...):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            collector = get_metrics_collector()
            counter = collector.counter(metric_name, f'Count of {func.__name__}', labels)
            counter.inc()

            return result

        return wrapper
    return decorator
