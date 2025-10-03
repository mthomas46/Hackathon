#!/usr/bin/env python3
"""
Datastore Operations Dashboard

A comprehensive Streamlit dashboard for monitoring and visualizing datastore operations
across the entire ecosystem. Integrates with log-collector to display real-time metrics,
performance trends, and operational insights.

Usage:
    streamlit run services/data-services-dashboard/app.py
    
Features:
    - Real-time operation monitoring
    - Performance metrics and trends
    - Service health overview
    - Workflow tracking and tracing
    - Error analysis and alerting
    - Interactive filtering and drill-down
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import time
from collections import defaultdict

# Page configuration
st.set_page_config(
    page_title="Datastore Operations Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-healthy {
        color: #28a745;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
LOG_COLLECTOR_URL = "http://localhost:8104"
DEFAULT_SERVICES = [
    "doc_store",
    "prompt_store",
    "external-service-store",
    "memory-agent"
]

# Helper functions
@st.cache_data(ttl=5)
def fetch_logs(service: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch logs from log-collector with caching."""
    try:
        params = {"limit": limit}
        if service:
            params["service"] = service
            
        response = httpx.get(f"{LOG_COLLECTOR_URL}/logs", params=params, timeout=5.0)
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])
    except Exception as e:
        st.error(f"Failed to fetch logs: {e}")
        return []

def parse_log_entry(log: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a log entry into structured data."""
    context = log.get("context", {})
    return {
        "timestamp": datetime.fromisoformat(log.get("timestamp", datetime.now().isoformat())),
        "service": log.get("service", "unknown"),
        "level": log.get("level", "INFO"),
        "message": log.get("message", ""),
        "operation_type": context.get("operation_type", "unknown"),
        "method": context.get("method", ""),
        "path": context.get("path", ""),
        "status_code": context.get("status_code"),
        "duration_ms": context.get("duration_ms"),
        "success": context.get("success"),
        "phase": context.get("phase", ""),
        "workflow_id": context.get("workflow_id", "")
    }

def calculate_metrics(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregate metrics from logs."""
    if not logs:
        return {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "avg_duration_ms": 0,
            "operations_per_service": {},
            "error_rate": 0
        }
    
    completed_logs = [l for l in logs if l.get("phase") == "complete"]
    
    successful = [l for l in completed_logs if l.get("success") is True]
    failed = [l for l in completed_logs if l.get("success") is False]
    
    durations = [l["duration_ms"] for l in completed_logs if l.get("duration_ms") is not None]
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    operations_by_service = defaultdict(int)
    for log in completed_logs:
        operations_by_service[log["service"]] += 1
    
    error_rate = (len(failed) / len(completed_logs) * 100) if completed_logs else 0
    
    return {
        "total_operations": len(completed_logs),
        "successful_operations": len(successful),
        "failed_operations": len(failed),
        "avg_duration_ms": avg_duration,
        "operations_per_service": dict(operations_by_service),
        "error_rate": error_rate
    }

# Main dashboard
def main():
    """Main dashboard application."""
    
    # Header
    st.markdown('<div class="main-header">📊 Datastore Operations Dashboard</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Auto-refresh
    refresh_interval = st.sidebar.select_slider(
        "Auto-refresh interval (seconds)",
        options=[0, 5, 10, 30, 60],
        value=10
    )
    
    if refresh_interval > 0:
        count = st_autorefresh(interval=refresh_interval * 1000, key="datarefresh")
    
    # Sidebar filters
    st.sidebar.markdown("## 🔍 Filters")
    
    selected_service = st.sidebar.selectbox(
        "Service",
        ["All"] + DEFAULT_SERVICES
    )
    
    time_range = st.sidebar.selectbox(
        "Time Range",
        ["Last 100 operations", "Last 500 operations", "Last 1000 operations"],
        index=0
    )
    
    limit_map = {
        "Last 100 operations": 100,
        "Last 500 operations": 500,
        "Last 1000 operations": 1000
    }
    limit = limit_map[time_range]
    
    # Fetch data
    with st.spinner("Fetching logs..."):
        service_filter = None if selected_service == "All" else selected_service
        raw_logs = fetch_logs(service=service_filter, limit=limit)
        logs = [parse_log_entry(log) for log in raw_logs]
    
    # Calculate metrics
    metrics = calculate_metrics(logs)
    
    # Display metrics
    st.markdown("### 📈 Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Operations",
            metrics["total_operations"],
            help="Total completed operations"
        )
    
    with col2:
        st.metric(
            "Successful",
            metrics["successful_operations"],
            help="Operations completed successfully"
        )
    
    with col3:
        st.metric(
            "Failed",
            metrics["failed_operations"],
            delta=f"-{metrics['error_rate']:.1f}%" if metrics['error_rate'] > 0 else "0%",
            delta_color="inverse",
            help="Failed operations"
        )
    
    with col4:
        st.metric(
            "Avg Duration",
            f"{metrics['avg_duration_ms']:.2f}ms",
            help="Average operation duration"
        )
    
    with col5:
        error_color = "normal" if metrics['error_rate'] < 5 else "inverse"
        st.metric(
            "Error Rate",
            f"{metrics['error_rate']:.1f}%",
            delta_color=error_color,
            help="Percentage of failed operations"
        )
    
    st.markdown("---")
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "⏱️ Performance",
        "🔍 Operations",
        "🌊 Workflows",
        "⚠️ Errors"
    ])
    
    with tab1:
        render_overview_tab(logs, metrics)
    
    with tab2:
        render_performance_tab(logs)
    
    with tab3:
        render_operations_tab(logs)
    
    with tab4:
        render_workflows_tab(logs)
    
    with tab5:
        render_errors_tab(logs)

def render_overview_tab(logs: List[Dict[str, Any]], metrics: Dict[str, Any]):
    """Render the overview tab with service health and operation distribution."""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏢 Operations by Service")
        if metrics["operations_per_service"]:
            df_services = pd.DataFrame([
                {"Service": service, "Operations": count}
                for service, count in metrics["operations_per_service"].items()
            ])
            
            fig = px.pie(
                df_services,
                values="Operations",
                names="Service",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No operation data available")
    
    with col2:
        st.markdown("#### 📈 Operation Types")
        operation_types = defaultdict(int)
        for log in logs:
            if log.get("phase") == "complete":
                operation_types[log.get("operation_type", "unknown")] += 1
        
        if operation_types:
            df_types = pd.DataFrame([
                {"Type": op_type, "Count": count}
                for op_type, count in operation_types.items()
            ])
            
            fig = px.bar(
                df_types,
                x="Type",
                y="Count",
                color="Count",
                color_continuous_scale="Blues"
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No operation type data available")
    
    # Recent activity timeline
    st.markdown("#### ⏰ Recent Activity Timeline")
    
    completed_logs = [l for l in logs if l.get("phase") == "complete"][:50]
    
    if completed_logs:
        df_timeline = pd.DataFrame([
            {
                "timestamp": log["timestamp"],
                "service": log["service"],
                "operation": f"{log['method']} {log['path']}",
                "duration_ms": log.get("duration_ms", 0),
                "status": "✅ Success" if log.get("success") else "❌ Failed"
            }
            for log in sorted(completed_logs, key=lambda x: x["timestamp"], reverse=True)
        ])
        
        fig = px.scatter(
            df_timeline,
            x="timestamp",
            y="duration_ms",
            color="service",
            symbol="status",
            hover_data=["operation"],
            title="Operation Timeline (Last 50)"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline data available")

def render_performance_tab(logs: List[Dict[str, Any]]):
    """Render the performance analysis tab."""
    
    st.markdown("### ⏱️ Performance Analysis")
    
    completed_logs = [l for l in logs if l.get("phase") == "complete" and l.get("duration_ms") is not None]
    
    if not completed_logs:
        st.warning("No performance data available")
        return
    
    # Performance over time
    st.markdown("#### 📈 Response Time Trend")
    
    df_perf = pd.DataFrame([
        {
            "timestamp": log["timestamp"],
            "duration_ms": log["duration_ms"],
            "service": log["service"],
            "operation": log.get("operation_type", "unknown")
        }
        for log in sorted(completed_logs, key=lambda x: x["timestamp"])
    ])
    
    fig = px.line(
        df_perf,
        x="timestamp",
        y="duration_ms",
        color="service",
        title="Response Time Trend by Service"
    )
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Duration Distribution")
        fig = px.histogram(
            df_perf,
            x="duration_ms",
            nbins=30,
            title="Response Time Distribution"
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📦 Duration by Operation")
        fig = px.box(
            df_perf,
            x="operation",
            y="duration_ms",
            color="operation",
            title="Duration by Operation Type"
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance stats table
    st.markdown("#### 📋 Performance Statistics by Service")
    
    perf_stats = df_perf.groupby("service")["duration_ms"].agg([
        ("Count", "count"),
        ("Min (ms)", "min"),
        ("Max (ms)", "max"),
        ("Mean (ms)", "mean"),
        ("Median (ms)", "median"),
        ("Std Dev (ms)", "std")
    ]).round(2)
    
    st.dataframe(perf_stats, use_container_width=True)

def render_operations_tab(logs: List[Dict[str, Any]]):
    """Render the detailed operations log tab."""
    
    st.markdown("### 🔍 Operation Details")
    
    completed_logs = [l for l in logs if l.get("phase") == "complete"]
    
    if not completed_logs:
        st.warning("No operations data available")
        return
    
    # Filter controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        operation_filter = st.selectbox(
            "Operation Type",
            ["All"] + sorted(set(l.get("operation_type", "unknown") for l in completed_logs))
        )
    
    with col2:
        status_filter = st.selectbox(
            "Status",
            ["All", "Success", "Failed"]
        )
    
    with col3:
        show_count = st.number_input(
            "Show entries",
            min_value=10,
            max_value=500,
            value=50,
            step=10
        )
    
    # Apply filters
    filtered_logs = completed_logs
    
    if operation_filter != "All":
        filtered_logs = [l for l in filtered_logs if l.get("operation_type") == operation_filter]
    
    if status_filter == "Success":
        filtered_logs = [l for l in filtered_logs if l.get("success") is True]
    elif status_filter == "Failed":
        filtered_logs = [l for l in filtered_logs if l.get("success") is False]
    
    # Display as table
    if filtered_logs:
        df_ops = pd.DataFrame([
            {
                "Timestamp": log["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "Service": log["service"],
                "Operation": log.get("operation_type", ""),
                "Method": log.get("method", ""),
                "Path": log.get("path", ""),
                "Duration (ms)": f"{log.get('duration_ms', 0):.2f}",
                "Status": log.get("status_code", ""),
                "Success": "✅" if log.get("success") else "❌",
                "Workflow ID": log.get("workflow_id", "")[:12]
            }
            for log in sorted(filtered_logs, key=lambda x: x["timestamp"], reverse=True)[:show_count]
        ])
        
        st.dataframe(df_ops, use_container_width=True, height=600)
        
        # Export option
        csv = df_ops.to_csv(index=False)
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"operations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No operations match the current filters")

def render_workflows_tab(logs: List[Dict[str, Any]]):
    """Render the workflow tracking tab."""
    
    st.markdown("### 🌊 Workflow Tracking")
    
    # Group by workflow ID
    workflows = defaultdict(list)
    for log in logs:
        workflow_id = log.get("workflow_id")
        if workflow_id and workflow_id != "unknown":
            workflows[workflow_id].append(log)
    
    if not workflows:
        st.warning("No workflow data available")
        return
    
    st.markdown(f"**Found {len(workflows)} unique workflows**")
    
    # Workflow selection
    workflow_ids = sorted(workflows.keys(), key=lambda x: max(l["timestamp"] for l in workflows[x]), reverse=True)
    
    selected_workflow = st.selectbox(
        "Select Workflow",
        workflow_ids,
        format_func=lambda x: f"{x} ({len(workflows[x])} operations)"
    )
    
    if selected_workflow:
        workflow_logs = sorted(workflows[selected_workflow], key=lambda x: x["timestamp"])
        
        # Workflow summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Operations", len(workflow_logs))
        
        with col2:
            services_used = set(l["service"] for l in workflow_logs)
            st.metric("Services Touched", len(services_used))
        
        with col3:
            successful = sum(1 for l in workflow_logs if l.get("success") is True)
            st.metric("Successful", successful)
        
        with col4:
            completed = [l for l in workflow_logs if l.get("phase") == "complete" and l.get("duration_ms")]
            total_duration = sum(l["duration_ms"] for l in completed)
            st.metric("Total Duration", f"{total_duration:.2f}ms")
        
        # Workflow timeline
        st.markdown("#### 📅 Workflow Timeline")
        
        df_workflow = pd.DataFrame([
            {
                "Timestamp": log["timestamp"].strftime("%H:%M:%S.%f")[:-3],
                "Service": log["service"],
                "Operation": f"{log.get('method', '')} {log.get('path', '')}",
                "Phase": log.get("phase", ""),
                "Duration (ms)": f"{log.get('duration_ms', 0):.2f}" if log.get("duration_ms") else "N/A",
                "Status": "✅" if log.get("success") else "❌" if log.get("success") is False else "⏳"
            }
            for log in workflow_logs
        ])
        
        st.dataframe(df_workflow, use_container_width=True)
        
        # Workflow visualization
        st.markdown("#### 🗺️ Service Call Flow")
        
        completed_workflow = [l for l in workflow_logs if l.get("phase") == "complete"]
        if completed_workflow:
            fig = px.timeline(
                pd.DataFrame([
                    {
                        "Service": log["service"],
                        "Start": log["timestamp"],
                        "Finish": log["timestamp"] + timedelta(milliseconds=log.get("duration_ms", 0)),
                        "Operation": log.get("operation_type", "")
                    }
                    for log in completed_workflow
                ]),
                x_start="Start",
                x_end="Finish",
                y="Service",
                color="Operation",
                title="Service Call Timeline"
            )
            st.plotly_chart(fig, use_container_width=True)

def render_errors_tab(logs: List[Dict[str, Any]]):
    """Render the error analysis tab."""
    
    st.markdown("### ⚠️ Error Analysis")
    
    failed_logs = [l for l in logs if l.get("success") is False and l.get("phase") == "complete"]
    
    if not failed_logs:
        st.success("✅ No errors detected in the current time range!")
        return
    
    st.warning(f"**{len(failed_logs)} failed operations detected**")
    
    # Error distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏢 Errors by Service")
        errors_by_service = defaultdict(int)
        for log in failed_logs:
            errors_by_service[log["service"]] += 1
        
        df_errors = pd.DataFrame([
            {"Service": service, "Errors": count}
            for service, count in errors_by_service.items()
        ])
        
        fig = px.bar(
            df_errors,
            x="Service",
            y="Errors",
            color="Errors",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 Errors by Status Code")
        errors_by_status = defaultdict(int)
        for log in failed_logs:
            status_code = log.get("status_code", "Unknown")
            errors_by_status[str(status_code)] += 1
        
        df_status = pd.DataFrame([
            {"Status Code": status, "Count": count}
            for status, count in errors_by_status.items()
        ])
        
        fig = px.pie(
            df_status,
            values="Count",
            names="Status Code",
            title="Error Distribution by Status Code"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Error details table
    st.markdown("#### 📋 Error Details")
    
    df_error_details = pd.DataFrame([
        {
            "Timestamp": log["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "Service": log["service"],
            "Operation": log.get("operation_type", ""),
            "Method": log.get("method", ""),
            "Path": log.get("path", ""),
            "Status Code": log.get("status_code", ""),
            "Duration (ms)": f"{log.get('duration_ms', 0):.2f}",
            "Message": log.get("message", "")[:100]
        }
        for log in sorted(failed_logs, key=lambda x: x["timestamp"], reverse=True)
    ])
    
    st.dataframe(df_error_details, use_container_width=True, height=400)

if __name__ == "__main__":
    main()

