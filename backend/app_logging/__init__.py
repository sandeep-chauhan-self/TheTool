"""
Logging Package

Part 4: Architecture Blueprint
CROSS_CUTTING_001: Structured Logging with Correlation IDs

JSON-formatted logs with request correlation for distributed tracing.
"""

from .structured_logging import (
    CorrelationFilter,
    JSONFormatter,
    setup_logging,
    set_correlation_id,
    get_correlation_id,
    correlation_id
)
__all__ = [
    'CorrelationFilter',
    'JSONFormatter',
    'setup_logging',
    'set_correlation_id',
    'get_correlation_id',
    'correlation_id'
]
