"""
UTC Datetime Utilities

Centralized utilities for consistent UTC datetime handling across the application.

Core Principles:
1. Store ALL datetimes in UTC
2. Convert at API boundaries
3. Log warnings for naive datetimes
4. Fail fast on timezone issues
"""

from datetime import datetime, timezone
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is UTC-aware.
    
    - If already UTC-aware → return as-is
    - If aware but not UTC → convert to UTC
    - If naive → assume UTC and make aware (with warning)
    
    Args:
        dt: Datetime to convert
    
    Returns:
        UTC-aware datetime
    
    Examples:
        >>> naive = datetime(2025, 10, 26, 12, 0, 0)
        >>> ensure_utc(naive)  # → 2025-10-26 12:00:00+00:00
        
        >>> from pytz import timezone as pytz_tz
        >>> est = pytz_tz('America/New_York')
        >>> est_dt = est.localize(datetime(2025, 10, 26, 12, 0, 0))
        >>> ensure_utc(est_dt)  # → 2025-10-26 17:00:00+00:00 (converted)
    """
    if dt.tzinfo is None:
        logger.warning(
            f"Naive datetime encountered, assuming UTC: {dt}. "
            f"Consider providing timezone-aware datetimes."
        )
        return dt.replace(tzinfo=timezone.utc)
    
    if dt.tzinfo != timezone.utc:
        logger.debug(f"Converting {dt.tzinfo} to UTC: {dt}")
        return dt.astimezone(timezone.utc)
    
    return dt


def ensure_utc_naive(dt: datetime) -> datetime:
    """
    Convert datetime to naive UTC (for PostgreSQL TIMESTAMP storage).
    
    PostgreSQL TIMESTAMP columns don't store timezone info, so we store
    naive UTC datetimes and enforce UTC at the application layer.
    
    Args:
        dt: Datetime to convert
    
    Returns:
        Naive datetime in UTC
    
    Examples:
        >>> from datetime import timezone
        >>> aware = datetime(2025, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
        >>> ensure_utc_naive(aware)  # → 2025-10-26 12:00:00 (naive)
    """
    utc_dt = ensure_utc(dt)
    return utc_dt.replace(tzinfo=None)


def datetime_to_utc_timestamp(dt: datetime) -> float:
    """
    Convert datetime to Unix timestamp (UTC).
    
    Unix timestamps are always relative to UTC (1970-01-01 00:00:00 UTC),
    so this ensures consistent timestamp generation regardless of input timezone.
    
    Args:
        dt: Datetime to convert
    
    Returns:
        Unix timestamp (seconds since 1970-01-01 00:00:00 UTC)
    
    Examples:
        >>> dt = datetime(2025, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
        >>> timestamp = datetime_to_utc_timestamp(dt)
        >>> timestamp  # → 1761494400.0
    """
    utc_dt = ensure_utc(dt)
    return utc_dt.timestamp()


def timestamp_to_utc_datetime(ts: float) -> datetime:
    """
    Convert Unix timestamp to UTC-aware datetime.
    
    Args:
        ts: Unix timestamp (seconds since 1970-01-01 00:00:00 UTC)
    
    Returns:
        UTC-aware datetime
    
    Examples:
        >>> ts = 1761494400.0
        >>> dt = timestamp_to_utc_datetime(ts)
        >>> dt  # → 2025-10-26 12:00:00+00:00
    """
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def now_utc() -> datetime:
    """
    Get current time as UTC-aware datetime.
    
    Returns:
        Current UTC time (aware)
    
    Examples:
        >>> now = now_utc()
        >>> now.tzinfo == timezone.utc  # → True
    """
    return datetime.now(timezone.utc)


def now_utc_naive() -> datetime:
    """
    Get current time as naive UTC datetime (for PostgreSQL TIMESTAMP).
    
    Returns:
        Current UTC time (naive)
    
    Examples:
        >>> now = now_utc_naive()
        >>> now.tzinfo is None  # → True
    """
    return datetime.utcnow()


def safe_datetime_comparison(dt1: datetime, dt2: datetime, operation: str = "<") -> bool:
    """
    Safely compare two datetimes, ensuring both are UTC-aware.
    
    Prevents the common error: "can't compare offset-naive and offset-aware datetimes"
    
    Args:
        dt1: First datetime
        dt2: Second datetime
        operation: Comparison operation ("<", "<=", ">", ">=", "==", "!=")
    
    Returns:
        Result of comparison
    
    Raises:
        ValueError: If operation is invalid
    
    Examples:
        >>> dt1 = datetime(2025, 10, 26, 12, 0, 0)  # naive
        >>> dt2 = datetime(2025, 10, 27, 12, 0, 0, tzinfo=timezone.utc)  # aware
        >>> safe_datetime_comparison(dt1, dt2, "<")  # → True (no error!)
    """
    # Ensure both are UTC-aware
    dt1_utc = ensure_utc(dt1)
    dt2_utc = ensure_utc(dt2)
    
    # Perform comparison
    if operation == "<":
        return dt1_utc < dt2_utc
    elif operation == "<=":
        return dt1_utc <= dt2_utc
    elif operation == ">":
        return dt1_utc > dt2_utc
    elif operation == ">=":
        return dt1_utc >= dt2_utc
    elif operation == "==":
        return dt1_utc == dt2_utc
    elif operation == "!=":
        return dt1_utc != dt2_utc
    else:
        raise ValueError(f"Invalid operation: {operation}")


def validate_datetime_range(
    start: datetime,
    end: datetime,
    field_name: str = "date_range"
) -> tuple[datetime, datetime]:
    """
    Validate datetime range and ensure both are UTC-aware.
    
    Args:
        start: Start datetime
        end: End datetime
        field_name: Field name for error messages
    
    Returns:
        Tuple of (start_utc, end_utc)
    
    Raises:
        ValueError: If start >= end
    
    Examples:
        >>> start = datetime(2025, 10, 26)
        >>> end = datetime(2025, 10, 27)
        >>> start_utc, end_utc = validate_datetime_range(start, end)
        >>> start_utc.tzinfo == timezone.utc  # → True
    """
    start_utc = ensure_utc(start)
    end_utc = ensure_utc(end)
    
    if start_utc >= end_utc:
        raise ValueError(
            f"{field_name}: start date ({start_utc}) must be before end date ({end_utc})"
        )
    
    return start_utc, end_utc


def parse_datetime_flexible(dt_input: str | datetime) -> datetime:
    """
    Parse datetime from various formats, ensuring UTC result.
    
    Handles:
    - ISO 8601 strings (with or without 'Z')
    - datetime objects (naive or aware)
    - Common date formats
    
    Args:
        dt_input: String or datetime to parse
    
    Returns:
        UTC-aware datetime
    
    Examples:
        >>> parse_datetime_flexible("2025-10-26T12:00:00Z")  # ISO with Z
        >>> parse_datetime_flexible("2025-10-26T12:00:00")   # ISO without Z
        >>> parse_datetime_flexible(datetime(2025, 10, 26))  # naive datetime
    """
    if isinstance(dt_input, str):
        # Handle 'Z' suffix (Zulu time = UTC)
        dt_str = dt_input.replace('Z', '+00:00')
        
        try:
            # Try ISO format first
            dt = datetime.fromisoformat(dt_str)
        except ValueError:
            # Fallback to other formats
            try:
                dt = datetime.strptime(dt_input, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    dt = datetime.strptime(dt_input, "%Y-%m-%d")
                except ValueError:
                    raise ValueError(f"Unable to parse datetime: {dt_input}")
    else:
        dt = dt_input
    
    return ensure_utc(dt)


# Convenience type alias for documentation
# UTCDatetime = datetime  # Datetime that is guaranteed to be UTC-aware

