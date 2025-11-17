"""
Data Sources Module

Alternative data source implementations:
- Fallback: Alternative data source orchestrator
- Yahoo Finance: Primary data adapter (future)
- Demo Data: Testing data generator (future)
"""

from utils.data.sources.fallback import get_fallback_data

__all__ = [
    'get_fallback_data',
]
