"""
API Request/Response Tracker

Utility for tracking, logging, and debugging API calls in the dashboard.
Provides detailed request/response information for troubleshooting.
"""

import streamlit as st
import httpx
import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import contextmanager


class APITracker:
    """Track API requests and responses for debugging."""
    
    def __init__(self):
        """Initialize API tracker."""
        if 'api_calls' not in st.session_state:
            st.session_state.api_calls = []
        if 'api_errors' not in st.session_state:
            st.session_state.api_errors = []
    
    def log_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        body: Optional[Any] = None
    ) -> Dict:
        """Log an API request."""
        request_log = {
            'timestamp': datetime.now().isoformat(),
            'method': method.upper(),
            'url': url,
            'headers': headers or {},
            'params': params or {},
            'body': body,
            'request_id': f"req_{int(time.time() * 1000)}"
        }
        
        st.session_state.api_calls.append(request_log)
        return request_log
    
    def log_response(
        self,
        request_log: Dict,
        status_code: int,
        response_data: Optional[Any] = None,
        error: Optional[str] = None,
        duration_ms: Optional[float] = None
    ):
        """Log an API response."""
        request_log['response'] = {
            'status_code': status_code,
            'data': response_data,
            'error': error,
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log errors separately
        if error or status_code >= 400:
            error_log = {
                'timestamp': datetime.now().isoformat(),
                'method': request_log['method'],
                'url': request_log['url'],
                'status_code': status_code,
                'error': error,
                'request_id': request_log['request_id']
            }
            st.session_state.api_errors.append(error_log)
    
    @contextmanager
    def track_request(self, method: str, url: str, **kwargs):
        """Context manager for tracking API requests."""
        request_log = self.log_request(method, url, **kwargs)
        start_time = time.time()
        
        try:
            yield request_log
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.log_response(
                request_log,
                status_code=0,
                error=str(e),
                duration_ms=duration_ms
            )
            raise
        finally:
            # Response logging happens in the actual request method
            pass
    
    def get_recent_calls(self, limit: int = 10) -> List[Dict]:
        """Get recent API calls."""
        return st.session_state.api_calls[-limit:]
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """Get recent API errors."""
        return st.session_state.api_errors[-limit:]
    
    def clear_history(self):
        """Clear API call history."""
        st.session_state.api_calls = []
        st.session_state.api_errors = []
    
    def get_stats(self) -> Dict:
        """Get API call statistics."""
        total_calls = len(st.session_state.api_calls)
        errors = len(st.session_state.api_errors)
        
        success_rate = 0
        if total_calls > 0:
            success_rate = ((total_calls - errors) / total_calls) * 100
        
        # Calculate average response time
        durations = []
        for call in st.session_state.api_calls:
            if 'response' in call and call['response'].get('duration_ms'):
                durations.append(call['response']['duration_ms'])
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        return {
            'total_calls': total_calls,
            'total_errors': errors,
            'success_rate': success_rate,
            'avg_response_time_ms': avg_duration
        }


def make_api_request(
    api_base_url: str,
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict] = None,
    json_data: Optional[Dict] = None,
    timeout: float = 10.0,
    show_error: bool = True
) -> Optional[Dict]:
    """
    Make an API request with comprehensive tracking and error handling.
    
    Args:
        api_base_url: Base URL for API
        endpoint: API endpoint path
        method: HTTP method
        params: Query parameters
        json_data: JSON body data
        timeout: Request timeout
        show_error: Whether to display errors in UI
    
    Returns:
        Response data or None on error
    """
    tracker = APITracker()
    url = f"{api_base_url}{endpoint}"
    
    with tracker.track_request(method, url, params=params, body=json_data):
        start_time = time.time()
        
        try:
            # Make the request
            if method.upper() == "GET":
                response = httpx.get(url, params=params, timeout=timeout)
            elif method.upper() == "POST":
                response = httpx.post(url, params=params, json=json_data, timeout=timeout)
            elif method.upper() == "PUT":
                response = httpx.put(url, params=params, json=json_data, timeout=timeout)
            elif method.upper() == "DELETE":
                response = httpx.delete(url, params=params, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            # Log response
            request_log = tracker.get_recent_calls(1)[0]
            tracker.log_response(
                request_log,
                status_code=response.status_code,
                response_data=response_data,
                duration_ms=duration_ms
            )
            
            # Handle errors
            if response.status_code >= 400:
                # 🔧 FIX #1: Handle rate limiting (HTTP 429)
                if response.status_code == 429:
                    # Extract rate limit headers
                    limit = response.headers.get('X-RateLimit-Limit', 'unknown')
                    remaining = response.headers.get('X-RateLimit-Remaining', '0')
                    reset = response.headers.get('X-RateLimit-Reset', 'unknown')
                    window = response.headers.get('X-RateLimit-Window', 'unknown')
                    
                    # Calculate time until reset
                    try:
                        reset_timestamp = int(reset)
                        current_time = int(time.time())
                        seconds_until_reset = max(0, reset_timestamp - current_time)
                        minutes_until_reset = seconds_until_reset // 60
                        
                        if minutes_until_reset > 0:
                            retry_msg = f"Try again in {minutes_until_reset} minute(s)"
                        else:
                            retry_msg = f"Try again in {seconds_until_reset} second(s)"
                    except:
                        retry_msg = "Try again shortly"
                    
                    if show_error:
                        st.warning(f"⚠️ **Rate Limit Exceeded**")
                        st.info(
                            f"📊 **Rate Limit Status:**\n\n"
                            f"- Limit: {limit} requests per {window} seconds\n"
                            f"- Remaining: {remaining} requests\n"
                            f"- {retry_msg}"
                        )
                        
                        with st.expander("💡 Rate Limit Tips"):
                            st.markdown("""
                            **What can you do?**
                            - Wait a moment before trying again
                            - Reduce the frequency of requests
                            - Use fewer API calls by leveraging caching
                            - Check the rate limit status in the header
                            """)
                    
                    return None
                
                # Handle other errors
                error_msg = f"API Error {response.status_code}"
                if isinstance(response_data, dict):
                    error_msg = response_data.get('detail', error_msg)
                    error_msg = response_data.get('message', error_msg)
                
                if show_error:
                    st.error(f"❌ {error_msg}")
                    
                    with st.expander("🔍 Request Details"):
                        st.code(f"Method: {method}\nURL: {url}\nStatus: {response.status_code}")
                        if json_data:
                            st.json(json_data)
                
                return None
            
            return response_data
        
        except httpx.ConnectError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Connection failed: {str(e)}"
            
            request_log = tracker.get_recent_calls(1)[0]
            tracker.log_response(
                request_log,
                status_code=0,
                error=error_msg,
                duration_ms=duration_ms
            )
            
            if show_error:
                st.error(f"❌ Cannot connect to API at {api_base_url}")
                st.info("🔧 Make sure the service is running")
            
            return None
        
        except httpx.TimeoutException as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Request timeout: {str(e)}"
            
            request_log = tracker.get_recent_calls(1)[0]
            tracker.log_response(
                request_log,
                status_code=0,
                error=error_msg,
                duration_ms=duration_ms
            )
            
            if show_error:
                st.error(f"❌ Request timeout after {timeout}s")
                st.info("⚡ Try increasing the timeout or check API performance")
            
            return None
        
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            
            request_log = tracker.get_recent_calls(1)[0]
            tracker.log_response(
                request_log,
                status_code=0,
                error=error_msg,
                duration_ms=duration_ms
            )
            
            if show_error:
                st.error(f"❌ Unexpected error: {error_msg}")
                
                with st.expander("🔍 Error Details"):
                    st.code(f"Method: {method}\nURL: {url}\nError: {error_msg}")
            
            return None


def show_api_tracker_widget():
    """Display API tracker widget in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 API Tracker")
    
    tracker = APITracker()
    stats = tracker.get_stats()
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("Calls", stats['total_calls'])
    with col2:
        st.metric("Errors", stats['total_errors'])
    
    if stats['total_calls'] > 0:
        st.sidebar.metric(
            "Success Rate",
            f"{stats['success_rate']:.1f}%"
        )
        st.sidebar.metric(
            "Avg Response",
            f"{stats['avg_response_time_ms']:.0f}ms"
        )
    
    with st.sidebar.expander("🔍 Recent Calls", expanded=False):
        recent = tracker.get_recent_calls(5)
        for call in reversed(recent):
            status = "✅" if 'response' in call and call['response']['status_code'] < 400 else "❌"
            duration = ""
            if 'response' in call and call['response'].get('duration_ms'):
                duration = f" ({call['response']['duration_ms']:.0f}ms)"
            
            st.caption(f"{status} {call['method']} {call['url'].split('/')[-1]}{duration}")
    
    if stats['total_errors'] > 0:
        with st.sidebar.expander("⚠️ Recent Errors", expanded=False):
            errors = tracker.get_recent_errors(3)
            for error in reversed(errors):
                st.error(f"{error['method']} {error['url']}")
                st.caption(error.get('error', 'Unknown error'))
    
    if st.sidebar.button("🔄 Clear Tracker", use_container_width=True):
        tracker.clear_history()
        st.rerun()

