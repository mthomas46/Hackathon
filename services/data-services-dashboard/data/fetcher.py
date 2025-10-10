"""
Log fetching from log-collector service.

Fetches operation logs with retry logic and caching.
"""

import streamlit as st
import httpx
from typing import List, Dict, Any, Optional

from utils.retry import with_retry
from utils.logging_client import dashboard_logger
from config import config


# HTTP client with connection pooling
http_client = httpx.Client(
    limits=httpx.Limits(
        max_connections=10,
        max_keepalive_connections=5
    ),
    timeout=config.http_timeout
)


@st.cache_data(ttl=config.cache_ttl)
def fetch_logs(
    service: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch logs from log-collector with caching and retry logic.
    
    Uses Streamlit's caching mechanism to avoid redundant requests.
    Implements retry logic with exponential backoff.
    
    Args:
        service: Optional service filter (None = all services)
        limit: Maximum number of logs to fetch (default: 100)
        
    Returns:
        List of log entries as dictionaries
        
    Raises:
        httpx.HTTPError: If request fails after all retries
        
    Example:
        logs = fetch_logs(service="doc_store", limit=100)
        for log in logs:
            print(log["timestamp"], log["message"])
    """
    # Log fetching attempt
    dashboard_logger.fetching_logs(service, limit)
    
    try:
        import time
        start_time = time.time()
        
        # Fetch with retry logic
        logs = _fetch_logs_with_retry(service, limit)
        
        # Log success
        elapsed_ms = (time.time() - start_time) * 1000
        dashboard_logger.logs_fetched(service, len(logs), elapsed_ms)
        
        return logs
        
    except httpx.TimeoutException as e:
        dashboard_logger.fetch_timeout(service or "all", config.http_timeout)
        st.error(f"⏱️ Request timeout: Unable to reach log-collector")
        return []
        
    except httpx.HTTPStatusError as e:
        dashboard_logger.fetch_failed(service or "all", f"HTTP {e.response.status_code}")
        st.error(f"⚠️ HTTP Error {e.response.status_code}: {e}")
        return []
        
    except httpx.RequestError as e:
        dashboard_logger.fetch_failed(service or "all", str(e))
        st.error(f"🔌 Connection Error: Unable to reach log-collector. {e}")
        return []
        
    except Exception as e:
        dashboard_logger.unexpected_error(str(e))
        st.error(f"💥 Unexpected Error: {e}")
        return []


@with_retry(
    max_attempts=config.max_retry_attempts,
    delay=config.retry_delay,
    backoff=config.retry_backoff
)
def _fetch_logs_with_retry(
    service: Optional[str],
    limit: int
) -> List[Dict[str, Any]]:
    """
    Internal function to fetch logs with retry decorator.
    
    Args:
        service: Optional service filter
        limit: Maximum number of logs
        
    Returns:
        List of log entries
        
    Raises:
        httpx exceptions if all retries fail
    """
    # Build request parameters
    params = {"limit": limit}
    if service and service != "All":
        params["service"] = service
    
    # Make HTTP request
    response = http_client.get(
        f"{config.log_collector_url}/logs",
        params=params
    )
    
    # Raise for HTTP errors
    response.raise_for_status()
    
    # Parse response
    data = response.json()
    
    # Extract items
    items = data.get("items", [])
    
    if not isinstance(items, list):
        raise ValueError(f"Expected list of logs, got {type(items)}")
    
    return items


def check_log_collector_health() -> bool:
    """
    Check if log-collector service is reachable.
    
    Returns:
        True if reachable, False otherwise
        
    Example:
        if check_log_collector_health():
            print("✅ Log-collector is online")
        else:
            print("❌ Log-collector is offline")
    """
    try:
        response = http_client.get(
            f"{config.log_collector_url}/health",
            timeout=2.0
        )
        return response.status_code == 200
    except Exception:
        return False


def get_available_services() -> List[str]:
    """
    Get list of services that have logged operations.
    
    Fetches a small sample of logs and extracts unique service names.
    
    Returns:
        List of unique service names
        
    Example:
        services = get_available_services()
        # ["doc_store", "prompt_store", "memory-agent"]
    """
    try:
        # Fetch recent logs (small sample)
        logs = fetch_logs(service=None, limit=100)
        
        # Extract unique service names
        services = set()
        for log in logs:
            if "service" in log:
                services.add(log["service"])
        
        # Return sorted list
        return sorted(list(services))
        
    except Exception:
        # Return default services if fetch fails
        return config.default_services[1:]  # Skip "All"

