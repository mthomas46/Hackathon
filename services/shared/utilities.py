"""Shared utility functions for common operations.

Provides reusable utility functions for string processing, date handling,
validation, and other common operations across all services.
"""

import re
import hashlib
import uuid
import os
import httpx
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path

from .constants_new import Patterns


# ============================================================================
# STRING UTILITIES
# ============================================================================

def clean_string(text: str) -> str:
    """Clean and normalize a string."""
    if not text:
        return ""
    return " ".join(text.split()).strip()


def extract_variables(text: str) -> List[str]:
    """Extract template variables from text (e.g., {variable})."""
    matches = re.findall(Patterns.VARIABLE, text)
    return list(set(matches))  # Remove duplicates


def generate_id(prefix: str = "", length: int = 12) -> str:
    """Generate a unique ID with optional prefix."""
    unique_id = hashlib.md5(f"{datetime.now(timezone.utc).isoformat()}{uuid.uuid4()}".encode()).hexdigest()[:length]
    return f"{prefix}{unique_id}" if prefix else unique_id


def safe_filename(filename: str) -> str:
    """Create a safe filename by removing/replacing unsafe characters."""
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[^\w\.-]', '_', filename)
    return filename


# ============================================================================
# DATE AND TIME UTILITIES
# ============================================================================

def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string."""
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse datetime from string."""
    return datetime.strptime(date_str, format_str)


def iso_datetime(dt: Optional[datetime] = None) -> str:
    """Get ISO format datetime string."""
    if dt is None:
        dt = utc_now()
    return dt.isoformat()


def relative_time(dt: datetime) -> str:
    """Get human-readable relative time (e.g., '2 hours ago')."""
    now = utc_now()
    diff = now - dt

    seconds = int(diff.total_seconds())
    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minutes ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hours ago"
    else:
        days = seconds // 86400
        return f"{days} days ago"


# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

def is_valid_email(email: str) -> bool:
    """Validate email address format."""
    return bool(re.match(Patterns.EMAIL, email))


def is_valid_url(url: str) -> bool:
    """Validate URL format."""
    return bool(re.match(Patterns.URL, url))


def validate_string_length(text: str, min_len: int = 0, max_len: int = 1000) -> bool:
    """Validate string length constraints.

    This is a simplified version for basic validation.
    For detailed error messages, use error_handling.validate_string_length.
    """
    return min_len <= len(text) <= max_len


def validate_numeric_range(value: Union[int, float], min_val: Optional[float] = None,
                          max_val: Optional[float] = None) -> bool:
    """Validate numeric value is within range."""
    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False
    return True


def deep_merge_dicts(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


# ============================================================================
# FILE AND PATH UTILITIES
# ============================================================================

def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_size_mb(file_path: Union[str, Path]) -> float:
    """Get file size in megabytes."""
    path = Path(file_path)
    return path.stat().st_size / (1024 * 1024)


def read_file_safe(file_path: Union[str, Path], encoding: str = "utf-8") -> Optional[str]:
    """Safely read a file, returning None if it doesn't exist or can't be read."""
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except (FileNotFoundError, IOError, UnicodeDecodeError):
        return None


def write_file_safe(file_path: Union[str, Path], content: str, encoding: str = "utf-8") -> bool:
    """Safely write content to a file."""
    try:
        ensure_directory(Path(file_path).parent)
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except IOError:
        return False


# ============================================================================
# DATA PROCESSING UTILITIES
# ============================================================================

def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size."""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def flatten_list(nested_list: List[List[Any]]) -> List[Any]:
    """Flatten a nested list structure."""
    return [item for sublist in nested_list for item in sublist]


def unique_list(items: List[Any]) -> List[Any]:
    """Remove duplicates from a list while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def group_by(items: List[Dict[str, Any]], key: str) -> Dict[Any, List[Dict[str, Any]]]:
    """Group a list of dictionaries by a key."""
    result = {}
    for item in items:
        group_key = item.get(key)
        if group_key not in result:
            result[group_key] = []
        result[group_key].append(item)
    return result


def sort_by(items: List[Dict[str, Any]], key: str, reverse: bool = False) -> List[Dict[str, Any]]:
    """Sort list of dictionaries by a key."""
    return sorted(items, key=lambda x: x.get(key), reverse=reverse)


def filter_by(items: List[Dict[str, Any]], key: str, value: Any) -> List[Dict[str, Any]]:
    """Filter list of dictionaries by key-value pair."""
    return [item for item in items if item.get(key) == value]


def find_by(items: List[Dict[str, Any]], key: str, value: Any) -> Optional[Dict[str, Any]]:
    """Find first item in list by key-value pair."""
    for item in items:
        if item.get(key) == value:
            return item
    return None


# ============================================================================
# HASHING AND ENCRYPTION UTILITIES
# ============================================================================

def hash_string(text: str, algorithm: str = "sha256") -> str:
    """Generate hash of a string."""
    if algorithm == "md5":
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(text.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(text.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def stable_hash(text: str) -> str:
    """Generate a stable hash for consistent results."""
    return hash_string(text, "sha256")


# ============================================================================
# SERVICE REGISTRATION UTILITIES
# ============================================================================

def attach_self_register(app, service_name: str) -> None:
    """Register service with the orchestrator or discovery mechanism.

    This function sets up the service to be discoverable by other services
    and registers it with any central registry if available.
    """
    # For now, this is a simple stub implementation
    # In a full implementation, this would register with a service discovery system
    # like Consul, etcd, or a custom registry
    try:
        # Import here to avoid circular dependencies
        from services.shared.logging import fire_and_forget

        # Log the service registration
        fire_and_forget(
            "info",
            "service_registration",
            service_name,
            {
                "service_name": service_name,
                "status": "registered",
                "timestamp": utc_now().isoformat()
            }
        )
    except ImportError:
        # Fallback if logging is not available
        pass


def get_service_client(timeout: Optional[int] = None) -> Any:
    """Get a configured ServiceClients instance for making HTTP requests."""
    try:
        from services.shared.clients import ServiceClients
        return ServiceClients(timeout=timeout)
    except ImportError:
        # Fallback if clients module is not available
        class DummyServiceClients:
            def __init__(self, timeout=None):
                self.timeout = timeout or 30
            def get_json(self, *args, **kwargs):
                raise NotImplementedError("ServiceClients not available")
            def post_json(self, *args, **kwargs):
                raise NotImplementedError("ServiceClients not available")
        return DummyServiceClients(timeout=timeout)


def setup_common_middleware(app, service_name: str, enable_rate_limit: bool = False,
                           rate_limits: Optional[Dict[str, tuple[float, int]]] = None) -> None:
    """Setup common middleware for FastAPI services."""
    try:
        from services.shared.middleware import ServiceMiddleware
        middleware = ServiceMiddleware(
            service_name=service_name,
            rate_limits=rate_limits,
            enable_rate_limit=enable_rate_limit
        )

        # Apply middleware to the FastAPI app
        for middleware_factory in middleware.get_middlewares():
            app.add_middleware(middleware_factory)
    except ImportError:
        # Fallback if middleware module is not available
        pass


# ============================================================================
# HTTP UTILITIES
# ============================================================================

async def cached_get(url: str, etag: Optional[str] = None, last_modified: Optional[str] = None, timeout: int = 15) -> Tuple[int, str, Dict[str, str]]:
    """Perform cached HTTP GET request with ETag and Last-Modified support.

    Returns:
        Tuple of (status_code, response_body, response_headers)
    """
    headers = {}
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url, headers=headers)

            # Return status, body, and headers
            return response.status_code, response.text, dict(response.headers)

    except Exception as e:
        # Return error status with empty body and error headers
        return 500, "", {"error": str(e)}


# ============================================================================
# RATE LIMITING UTILITIES
# ============================================================================

class TokenBucket:
    """Token bucket for rate limiting.

    Refills tokens at a constant rate up to a maximum capacity.
    Requests consume one token each.
    """

    def __init__(self, rate_per_sec: float, burst: int):
        """Initialize token bucket.

        Args:
            rate_per_sec: Tokens added per second
            burst: Maximum token capacity
        """
        self.rate = rate_per_sec
        self.capacity = burst
        self.tokens = burst
        self.last = time.monotonic()

    def allow(self) -> bool:
        """Check if request should be allowed and consume a token."""
        now = time.monotonic()
        elapsed = now - self.last
        self.last = now
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


# ============================================================================
# CONFIGURATION UTILITIES
# ============================================================================

