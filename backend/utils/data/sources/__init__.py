"""
Data Sources Module

Alternative data source implementations:
- Fallback: Alternative data source orchestrator
- Yahoo Finance: Primary data adapter (future)
- Demo Data: Testing data generator (future)
"""

from .fallback import fetch_with_fallback

__all__ = [
    'fetch_with_fallback',
]
