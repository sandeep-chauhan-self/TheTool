"""
Timezone Utility Module

Provides consistent Indian Standard Time (IST) handling across the application.
All timestamps stored in database should be IST for consistency.

Usage:
    from utils.timezone_util import get_ist_now, get_ist_timestamp
    
    # Get current time in IST
    now = get_ist_now()
    
    # Get ISO format timestamp
    iso_ts = get_ist_timestamp()
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

# Indian Standard Time offset (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_now() -> datetime:
    """
    Get current datetime in Indian Standard Time (IST).
    
    Returns:
        datetime: Current time in IST (timezone-aware)
    """
    return datetime.now(tz=IST)


def get_ist_timestamp() -> str:
    """
    Get current timestamp in ISO format with IST timezone.
    
    Returns:
        str: Current ISO format timestamp in IST (e.g., "2025-11-30T13:29:45.123456+05:30")
    """
    return get_ist_now().isoformat()


def convert_to_ist(dt: datetime) -> datetime:
    """
    Convert any datetime to IST.
    
    Args:
        dt: datetime object (can be naive or timezone-aware)
    
    Returns:
        datetime: Same time converted to IST (timezone-aware)
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.astimezone(IST)


def format_ist_for_display(dt: datetime) -> str:
    """
    Format datetime for display in IST.
    
    Args:
        dt: datetime object
    
    Returns:
        str: Formatted string (e.g., "2025-11-30 13:29:45")
    """
    if dt is None:
        return None
    
    ist_dt = convert_to_ist(dt)
    return ist_dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_ist_timestamp(timestamp_str: str) -> datetime:
    """
    Parse ISO format timestamp and convert to IST if needed.
    
    Args:
        timestamp_str: ISO format timestamp string
    
    Returns:
        datetime: Parsed datetime in IST
    """
    if not timestamp_str:
        return None
    
    try:
        # Parse ISO format
        dt = datetime.fromisoformat(timestamp_str)
        # Convert to IST
        return convert_to_ist(dt)
    except (ValueError, TypeError):
        return None
