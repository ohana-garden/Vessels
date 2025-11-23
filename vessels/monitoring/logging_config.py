"""
Structured Logging Configuration

Sets up JSON-formatted structured logging for production.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any
import traceback


class StructuredFormatter(logging.Formatter):
    """
    JSON-formatted structured logging.

    Outputs logs in JSON format for easy parsing by log aggregators.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""

        log_data: Dict[str, Any] = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }

        # Add extra fields from record
        if hasattr(record, 'extra'):
            log_data['extra'] = record.extra

        # Add request ID if present (for tracing)
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id

        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """
    Human-readable colored logging for development.
    """

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',   # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for terminal"""
        color = self.COLORS.get(record.levelname, '')
        reset = self.RESET

        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        log_line = (
            f"{color}[{timestamp}] {record.levelname:8s}{reset} "
            f"{record.name}:{record.funcName}:{record.lineno} - "
            f"{record.getMessage()}"
        )

        if record.exc_info:
            log_line += '\n' + ''.join(traceback.format_exception(*record.exc_info))

        return log_line


def setup_logging(
    level: str = "INFO",
    structured: bool = False,
    log_file: str = None
) -> None:
    """
    Configure application logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Use JSON structured logging (for production)
        log_file: Optional file path for log output
    """

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Choose formatter
    if structured:
        formatter = StructuredFormatter()
    else:
        formatter = HumanReadableFormatter()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(StructuredFormatter())  # Always JSON for files
        root_logger.addHandler(file_handler)

    # Set levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    logging.info(
        f"Logging configured: level={level}, structured={structured}, "
        f"file={log_file or 'none'}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger for module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
