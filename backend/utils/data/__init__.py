"""
Data Access Layer Module

Handles all external data operations:
- Fetching: Retrieve market data from sources
- Validation: Ensure data quality
- Fallback: Handle source failures
"""

from utils.data.fetcher import fetch_ticker_data
from utils.data.validator import DataValidator

__all__ = [
    'fetch_ticker_data',
    'DataValidator',
]
