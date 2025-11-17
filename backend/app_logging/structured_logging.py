"""
Structured Logging with Correlation IDs

Part 4: Architecture Blueprint
CROSS_CUTTING_001: Logging Architecture

Features:
- JSON-formatted logs for machine parsing
- Correlation IDs for request tracking across services
- Context variables for thread-safe correlation
- Structured metadata (timestamp, level, logger, module, function, line)
- Exception formatting

Usage:
    # Setup logging (once at application start)
    setup_logging(log_level="INFO")
    
    # In request handler
    correlation_id = set_correlation_id(request.headers.get('X-Request-ID'))
    
    # All logs within this context will include correlation_id
    logger.info("Processing request")  # {"correlation_id": "abc-123", ...}
    
    # Nested function calls inherit correlation_id automatically
    process_data()  # Logs also have correlation_id
"""

import logging
import json
import uuid
from typing import Optional, Dict, Any
from contextvars import ContextVar
from datetime import datetime

# Context variable for correlation ID (thread-safe)
correlation_id: ContextVar[str] = ContextVar('correlation_id', default=None)


class CorrelationFilter(logging.Filter):
    """
    Logging filter that adds correlation ID to log records
    
    Retrieves correlation ID from context variable and adds it to
    each log record for inclusion in formatted output.
    """
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation_id attribute to log record"""
        record.correlation_id = correlation_id.get() or "none"
        return True


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    
    Formats log records as JSON with structured fields:
    - timestamp: ISO 8601 timestamp
    - level: Log level (INFO, ERROR, etc.)
    - logger: Logger name
    - correlation_id: Request correlation ID
    - message: Log message
    - module: Python module name
    - function: Function name
    - line: Line number
    - exception: Exception traceback (if present)
    - extra: Additional fields from extra dict
    """
    
    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        include_extra: bool = True
    ):
        super().__init__(fmt, datefmt)
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Base log data
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "correlation_id": getattr(record, 'correlation_id', 'none'),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add stack trace if present
        if record.stack_info:
            log_data["stack_info"] = self.formatStack(record.stack_info)
        
        # Add extra fields
        if self.include_extra:
            # Get all custom attributes added via extra={}
            reserved_attrs = {
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs',
                'message', 'pathname', 'process', 'processName',
                'relativeCreated', 'thread', 'threadName', 'exc_info',
                'exc_text', 'stack_info', 'correlation_id'
            }
            
            for key, value in record.__dict__.items():
                if key not in reserved_attrs and not key.startswith('_'):
                    log_data[key] = value
        
        return json.dumps(log_data, default=str)
    
    def formatTime(self, record: logging.LogRecord, datefmt: Optional[str] = None) -> str:
        """Format timestamp as ISO 8601"""
        if datefmt:
            return super().formatTime(record, datefmt)
        # ISO 8601 format
        dt = datetime.fromtimestamp(record.created)
        return dt.isoformat()


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    handler: Optional[logging.Handler] = None
) -> logging.Logger:
    """
    Setup structured logging with correlation IDs
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ("json" or "text")
        handler: Optional custom handler (uses StreamHandler if None)
    
    Returns:
        Configured root logger
    
    Example:
        # JSON logging to console
        setup_logging(log_level="INFO", log_format="json")
        
        # Text logging to file
        file_handler = logging.FileHandler('app.log')
        setup_logging(log_level="DEBUG", log_format="text", handler=file_handler)
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Remove existing handlers
    for existing_handler in logger.handlers[:]:
        logger.removeHandler(existing_handler)
    
    # Create handler
    if handler is None:
        handler = logging.StreamHandler()
    
    # Set formatter
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        # Text format with correlation ID
        formatter = logging.Formatter(
            '%(asctime)s - %(correlation_id)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationFilter())
    
    # Add handler to logger
    logger.addHandler(handler)
    
    logger.info(f"Logging configured: level={log_level}, format={log_format}")
    
    return logger


def set_correlation_id(request_id: Optional[str] = None) -> str:
    """
    Set correlation ID for current context
    
    Args:
        request_id: Optional request ID (generates UUID if None)
    
    Returns:
        The correlation ID that was set
    
    Example:
        # Generate new ID
        correlation_id = set_correlation_id()
        
        # Use existing ID from request header
        correlation_id = set_correlation_id(request.headers.get('X-Request-ID'))
    """
    if request_id is None:
        request_id = str(uuid.uuid4())
    
    correlation_id.set(request_id)
    return request_id


def get_correlation_id() -> Optional[str]:
    """
    Get current correlation ID
    
    Returns:
        Current correlation ID or None
    """
    return correlation_id.get()


def clear_correlation_id() -> None:
    """Clear correlation ID from context"""
    correlation_id.set(None)


class CorrelationContext:
    """
    Context manager for correlation ID
    
    Automatically sets and clears correlation ID.
    
    Usage:
        with CorrelationContext() as corr_id:
            logger.info("Processing")  # Has correlation_id
            process_request()
        # correlation_id cleared after context
    """
    
    def __init__(self, request_id: Optional[str] = None):
        self.request_id = request_id
        self.previous_id = None
    
    def __enter__(self) -> str:
        """Set correlation ID"""
        self.previous_id = get_correlation_id()
        return set_correlation_id(self.request_id)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore previous correlation ID"""
        if self.previous_id:
            correlation_id.set(self.previous_id)
        else:
            clear_correlation_id()


# Convenience function for structured logging
def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **extra
) -> None:
    """
    Log message with additional structured context
    
    Args:
        logger: Logger instance
        level: Log level (info, warning, error, etc.)
        message: Log message
        **extra: Additional fields to include in JSON
    
    Example:
        log_with_context(
            logger,
            'info',
            'User logged in',
            user_id=123,
            ip_address='192.168.1.1'
        )
        
        # JSON output:
        {
            "timestamp": "2025-11-16T10:30:00",
            "level": "INFO",
            "correlation_id": "abc-123",
            "message": "User logged in",
            "user_id": 123,
            "ip_address": "192.168.1.1",
            ...
        }
    """
    log_method = getattr(logger, level.lower())
    log_method(message, extra=extra)
