"""
Performance tab rendering.

Displays response times, duration analysis, and performance statistics.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import List
import pandas as pd

from data.models import LogEntry
from metrics.calculator import (
    calculate_avg_duration,
    calculate_duration_percentiles,
    calculate_min_max_duration,
    aggregate_by_service
)
from utils.formatting import format_duration


def render_performance_tab(logs: List[LogEntry]):
    """
    Render performance tab with duration analysis and charts.
    
    Args:
        logs: List of parsed log entries
    """
    if not logs:
        st.info("📭 No operations to display. Waiting for data...")
        return
    
    # Filter logs with duration data
    logs_with_duration = [log for log in logs if log.duration_ms is not None]
    
    if not logs_with_duration:
        st.warning("⚠️ No duration data available in logs")
        return
    
    # Render performance metrics
    _render_performance_metrics(logs_with_duration)
    
    st.markdown("---")
    
    # Create two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Duration Distribution")
        _render_duration_histogram(logs_with_duration)
    
    with col2:
        st.markdown("### 🎯 Percentiles by Service")
        _render_percentiles_by_service(logs_with_duration)
    
    st.markdown("---")
    
    # Full-width chart
    st.markdown("### 📈 Duration Over Time")
    _render_duration_timeline(logs_with_duration)


def _render_performance_metrics(logs: List[LogEntry]):
    """
    Render performance metrics row.
    
    Args:
        logs: List of log entries with duration data
    """
    # Calculate metrics
    avg_duration = calculate_avg_duration(logs)
    min_max = calculate_min_max_duration(logs)
    percentiles = calculate_duration_percentiles(logs)
    
    # Display in columns
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Average",
            format_duration(avg_duration),
            help="Average operation duration"
        )
    
    with col2:
        st.metric(
            "Median (p50)",
            format_duration(percentiles["p50"]),
            help="50th percentile (median)"
        )
    
    with col3:
        st.metric(
            "p95",
            format_duration(percentiles["p95"]),
            help="95th percentile"
        )
    
    with col4:
        st.metric(
            "p99",
            format_duration(percentiles["p99"]),
            help="99th percentile"
        )
    
    with col5:
        st.metric(
            "Max",
            format_duration(min_max["max"]),
            delta=f"Min: {format_duration(min_max['min'])}",
            delta_color="off",
            help="Maximum duration"
        )


def _render_duration_histogram(logs: List[LogEntry]):
    """
    Render histogram of operation durations.
    
    Args:
        logs: List of log entries with duration data
    """
    # Create DataFrame
    df = pd.DataFrame([
        {"Duration (ms)": log.duration_ms, "Service": log.service}
        for log in logs
    ])
    
    # Create histogram
    fig = px.histogram(
        df,
        x="Duration (ms)",
        color="Service",
        nbins=30,
        barmode="overlay",
        opacity=0.7
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Duration (ms)",
        yaxis_title="Count",
        margin=dict(t=20, b=40, l=40, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_percentiles_by_service(logs: List[LogEntry]):
    """
    Render bar chart of p95 duration by service.
    
    Args:
        logs: List of log entries with duration data
    """
    # Aggregate by service
    metrics_by_service = aggregate_by_service(logs)
    
    # Extract p95 for each service
    data = []
    for service, metrics in metrics_by_service.items():
        # Get service logs
        service_logs = [log for log in logs if log.service == service]
        percentiles = calculate_duration_percentiles(service_logs)
        
        data.append({
            "Service": service,
            "p95 (ms)": percentiles["p95"]
        })
    
    if not data:
        st.info("No data to display")
        return
    
    # Create DataFrame
    df = pd.DataFrame(data).sort_values("p95 (ms)", ascending=False)
    
    # Create bar chart
    fig = px.bar(
        df,
        x="Service",
        y="p95 (ms)",
        color="p95 (ms)",
        color_continuous_scale="Reds"
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Service",
        yaxis_title="p95 Duration (ms)",
        margin=dict(t=20, b=40, l=40, r=20),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_duration_timeline(logs: List[LogEntry]):
    """
    Render scatter plot of duration over time.
    
    Args:
        logs: List of log entries with duration data
    """
    # Limit to last 100 for performance
    recent_logs = logs[:100]
    
    # Create DataFrame
    df = pd.DataFrame([
        {
            "Timestamp": log.timestamp,
            "Duration (ms)": log.duration_ms,
            "Service": log.service,
            "Operation": log.operation_type,
            "Status": "✅" if log.success else "❌"
        }
        for log in recent_logs
    ])
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x="Timestamp",
        y="Duration (ms)",
        color="Service",
        symbol="Status",
        hover_data=["Operation"],
        size_max=10
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Time",
        yaxis_title="Duration (ms)",
        margin=dict(t=20, b=40, l=40, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show stats table
    with st.expander("📊 Duration Statistics by Service"):
        stats_data = []
        for service in df["Service"].unique():
            service_df = df[df["Service"] == service]
            durations = service_df["Duration (ms)"]
            
            stats_data.append({
                "Service": service,
                "Count": len(durations),
                "Min": format_duration(durations.min()),
                "Avg": format_duration(durations.mean()),
                "Max": format_duration(durations.max()),
                "Std Dev": format_duration(durations.std())
            })
        
        stats_df = pd.DataFrame(stats_data)
        st.dataframe(stats_df, use_container_width=True, hide_index=True)

