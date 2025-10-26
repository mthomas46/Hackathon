"""
Retry Queue Dashboard

Real-time monitoring and management of the retry queue.

Features:
- Live queue statistics
- Circuit breaker status
- Recent retry items
- Success rate charts
- Manual reprocess controls

Created: 2025-10-26
Phase: 3.2 (Retry Infrastructure Monitoring)
"""

import streamlit as st
import requests
from datetime import datetime
import time
import pandas as pd
from typing import Dict, Any, List, Optional

# Configure API endpoint
API_BASE = "http://ecosystem-mcp:8000/api/v1"


def fetch_retry_stats() -> Optional[Dict[str, Any]]:
    """
    Fetch retry queue statistics from API.
    
    Returns:
        Statistics dict or None if error
    """
    try:
        response = requests.get(f"{API_BASE}/admin/retry-queue/stats", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch retry stats: {e}")
        return None


def fetch_retry_items(limit: int = 50, offset: int = 0) -> Optional[Dict[str, Any]]:
    """
    Fetch retry queue items.
    
    Args:
        limit: Maximum number of items
        offset: Number of items to skip
    
    Returns:
        Items response or None if error
    """
    try:
        response = requests.get(
            f"{API_BASE}/admin/retry-queue/items",
            params={"limit": limit, "offset": offset},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch retry items: {e}")
        return None


def fetch_worker_status() -> Optional[Dict[str, Any]]:
    """
    Fetch retry worker status.
    
    Returns:
        Worker status or None if error
    """
    try:
        response = requests.get(f"{API_BASE}/admin/retry-worker/status", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch worker status: {e}")
        return None


def reprocess_all() -> bool:
    """
    Trigger reprocess of all DLQ items.
    
    Returns:
        True if successful
    """
    try:
        response = requests.post(
            f"{API_BASE}/admin/retry-queue/reprocess",
            json={"all": True},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        st.success(f"✅ {result['message']}")
        return True
    except Exception as e:
        st.error(f"Failed to reprocess: {e}")
        return False


def reprocess_job(job_id: str) -> bool:
    """
    Reprocess all failures for a specific job.
    
    Args:
        job_id: Job ID to reprocess
    
    Returns:
        True if successful
    """
    try:
        response = requests.post(
            f"{API_BASE}/admin/retry-queue/reprocess",
            json={"job_id": job_id},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        st.success(f"✅ {result['message']}")
        return True
    except Exception as e:
        st.error(f"Failed to reprocess job: {e}")
        return False


def get_circuit_breaker_color(state: str) -> str:
    """Get color for circuit breaker state."""
    colors = {
        "closed": "🟢",
        "open": "🔴",
        "half_open": "🟡"
    }
    return colors.get(state.lower(), "⚪")


def show():
    """Main function to display retry queue dashboard."""
    
    st.title("🔄 Retry Queue Dashboard")
    st.markdown("Real-time monitoring and management of document retry processing")
    
    # Auto-refresh control
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=True, key="retry_auto_refresh")
    with col2:
        if st.button("🔄 Refresh Now", key="retry_refresh_now"):
            st.rerun()
    with col3:
        refresh_interval = st.number_input(
            "Interval (s)",
            min_value=10,
            max_value=300,
            value=30,
            step=10,
            key="retry_refresh_interval"
        )
    
    st.markdown("---")
    
    # Fetch data
    stats = fetch_retry_stats()
    worker_status = fetch_worker_status()
    items_response = fetch_retry_items(limit=50)
    
    if not stats or not worker_status:
        st.error("Failed to load retry queue data. Please check API connectivity.")
        return
    
    # ========================================================================
    # SECTION 1: Key Metrics
    # ========================================================================
    
    st.subheader("📊 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Items in Queue",
            value=stats.get("total_items", 0),
            delta=None,
            help="Total number of documents in retry queue"
        )
    
    with col2:
        st.metric(
            label="Ready to Retry",
            value=stats.get("ready_to_retry", 0),
            delta=None,
            help="Documents ready for immediate retry"
        )
    
    with col3:
        st.metric(
            label="Pending",
            value=stats.get("pending", 0),
            delta=None,
            help="Documents waiting for next retry time"
        )
    
    with col4:
        success_rate = worker_status.get("statistics", {}).get("success_rate_percent", 0)
        st.metric(
            label="Success Rate",
            value=f"{success_rate}%",
            delta=None,
            help="Percentage of retries that succeeded"
        )
    
    st.markdown("---")
    
    # ========================================================================
    # SECTION 2: Worker Status & Circuit Breaker
    # ========================================================================
    
    st.subheader("🔧 Worker Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Worker Status
        worker_running = worker_status.get("running", False)
        worker_indicator = "🟢 Running" if worker_running else "🔴 Stopped"
        st.markdown(f"**Worker:** {worker_indicator}")
        st.markdown(f"**Worker ID:** `{worker_status.get('worker_id', 'unknown')}`")
        
        started_at = worker_status.get("started_at")
        if started_at:
            st.markdown(f"**Started:** {started_at}")
        
        last_poll = worker_status.get("last_poll_at")
        if last_poll:
            st.markdown(f"**Last Poll:** {last_poll}")
    
    with col2:
        # Circuit Breaker Status
        cb_state = stats.get("circuit_breaker_state", "unknown")
        cb_color = get_circuit_breaker_color(cb_state)
        
        st.markdown(f"**Circuit Breaker:** {cb_color} {cb_state.upper()}")
        
        cb_info = worker_status.get("circuit_breaker", {})
        st.markdown(f"**Failure Count:** {cb_info.get('failure_count', 0)}")
        st.markdown(f"**Success Count:** {cb_info.get('success_count', 0)}")
        st.markdown(f"**Total Trips:** {worker_status.get('circuit_breaker_trips', 0)}")
        
        recovery_time = cb_info.get("time_until_recovery_seconds")
        if recovery_time and recovery_time > 0:
            st.warning(f"⏱️ Recovery in {recovery_time}s")
    
    st.markdown("---")
    
    # ========================================================================
    # SECTION 3: Statistics
    # ========================================================================
    
    st.subheader("📈 Lifetime Statistics")
    
    statistics = worker_status.get("statistics", {})
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Total Retried",
            value=statistics.get("total_retried", 0),
            help="Total documents retried"
        )
    
    with col2:
        st.metric(
            label="Recovered",
            value=statistics.get("total_recovered", 0),
            delta=None,
            help="Successfully recovered documents"
        )
    
    with col3:
        st.metric(
            label="Failed",
            value=statistics.get("total_failed", 0),
            delta=None,
            help="Documents that failed retry"
        )
    
    with col4:
        st.metric(
            label="Moved to DLQ",
            value=statistics.get("total_moved_to_dlq", 0),
            delta=None,
            help="Documents moved to dead letter queue"
        )
    
    with col5:
        st.metric(
            label="Batches Processed",
            value=statistics.get("batches_processed", 0),
            delta=None,
            help="Total batches processed"
        )
    
    # Success rate bar chart
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        total_retried = statistics.get("total_retried", 0)
        total_recovered = statistics.get("total_recovered", 0)
        total_failed = statistics.get("total_failed", 0)
        
        if total_retried > 0:
            chart_data = pd.DataFrame({
                "Status": ["Recovered", "Failed"],
                "Count": [total_recovered, total_failed]
            })
            st.bar_chart(chart_data.set_index("Status"))
        else:
            st.info("No retry attempts yet")
    
    st.markdown("---")
    
    # ========================================================================
    # SECTION 4: Recent Retry Items
    # ========================================================================
    
    st.subheader("📋 Recent Retry Items")
    
    if items_response and items_response.get("items"):
        items = items_response["items"]
        total = items_response.get("total", 0)
        
        st.markdown(f"**Showing {len(items)} of {total} items**")
        
        # Convert to DataFrame
        df_items = []
        for item in items:
            df_items.append({
                "File Path": item.get("file_path", "unknown")[:50] + "...",
                "Error Type": item.get("error_type", "unknown"),
                "Retry Count": item.get("retry_count", 0),
                "Next Retry": item.get("next_retry_at", "unknown")[:19],
                "Job ID": item.get("job_id", "unknown")[:8]
            })
        
        df = pd.DataFrame(df_items)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Reprocess controls
        st.markdown("### 🔄 Manual Reprocess Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            job_id_input = st.text_input(
                "Job ID to reprocess",
                placeholder="Enter job ID",
                key="retry_job_id_input"
            )
            if st.button("Reprocess Job", key="retry_reprocess_job_btn"):
                if job_id_input:
                    reprocess_job(job_id_input)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.warning("Please enter a job ID")
        
        with col2:
            st.markdown("")  # Spacer
            st.markdown("")
            if st.button("⚠️ Reprocess All DLQ Items", key="retry_reprocess_all_btn", type="primary"):
                with st.spinner("Reprocessing all items..."):
                    if reprocess_all():
                        time.sleep(1)
                        st.rerun()
    
    else:
        st.info("✅ Retry queue is empty - all documents processed successfully!")
    
    st.markdown("---")
    
    # ========================================================================
    # SECTION 5: Auto-refresh
    # ========================================================================
    
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


if __name__ == "__main__":
    show()

