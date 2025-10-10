"""
Overview tab rendering.

Displays service health, operation distribution, and key metrics.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import List
import pandas as pd

from data.models import LogEntry, MetricsSummary
from metrics.calculator import (
    calculate_metrics,
    calculate_operations_per_service,
    calculate_operations_per_type
)
from utils.formatting import format_percentage


def render_overview_tab(logs: List[LogEntry]):
    """
    Render overview tab with service health and distribution charts.
    
    Args:
        logs: List of parsed log entries
    """
    if not logs:
        st.info("📭 No operations to display. Waiting for data...")
        return
    
    # Calculate metrics
    metrics = calculate_metrics(logs)
    
    # Render metrics row
    _render_metrics_row(metrics)
    
    st.markdown("---")
    
    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Operations by Service")
        _render_operations_by_service_chart(logs)
    
    with col2:
        st.markdown("### 🔄 Operations by Type")
        _render_operations_by_type_chart(logs)
    
    st.markdown("---")
    
    # Full-width charts
    st.markdown("### 📈 Operations Over Time")
    _render_operations_timeline(logs)


def _render_metrics_row(metrics: MetricsSummary):
    """
    Render top metrics row with 5 columns.
    
    Args:
        metrics: Calculated metrics summary
    """
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Operations",
            metrics.total_operations,
            help="Total number of operations"
        )
    
    with col2:
        st.metric(
            "Successful",
            metrics.successful_operations,
            delta=f"{100 - metrics.error_rate:.1f}%",
            delta_color="normal",
            help="Successfully completed operations"
        )
    
    with col3:
        st.metric(
            "Failed",
            metrics.failed_operations,
            delta=f"-{metrics.error_rate:.1f}%",
            delta_color="inverse",
            help="Failed operations"
        )
    
    with col4:
        st.metric(
            "Avg Duration",
            f"{metrics.avg_duration_ms:.2f}ms",
            help="Average operation duration"
        )
    
    with col5:
        st.metric(
            "Error Rate",
            format_percentage(metrics.error_rate),
            delta=f"-{metrics.failed_operations}" if metrics.failed_operations > 0 else "✅ No errors",
            delta_color="inverse" if metrics.failed_operations > 0 else "off",
            help="Percentage of failed operations"
        )


def _render_operations_by_service_chart(logs: List[LogEntry]):
    """
    Render pie chart of operations by service.
    
    Args:
        logs: List of parsed log entries
    """
    ops_per_service = calculate_operations_per_service(logs)
    
    if not ops_per_service:
        st.info("No data to display")
        return
    
    # Create DataFrame
    df = pd.DataFrame([
        {"Service": service, "Operations": count}
        for service, count in ops_per_service.items()
    ])
    
    # Create pie chart
    fig = px.pie(
        df,
        values="Operations",
        names="Service",
        hole=0.3,  # Donut chart
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )
    
    fig.update_layout(
        showlegend=True,
        height=400,
        margin=dict(t=20, b=20, l=20, r=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_operations_by_type_chart(logs: List[LogEntry]):
    """
    Render bar chart of operations by type.
    
    Args:
        logs: List of parsed log entries
    """
    ops_per_type = calculate_operations_per_type(logs)
    
    if not ops_per_type:
        st.info("No data to display")
        return
    
    # Create DataFrame
    df = pd.DataFrame([
        {"Type": op_type, "Count": count}
        for op_type, count in sorted(ops_per_type.items(), key=lambda x: -x[1])
    ])
    
    # Create bar chart
    fig = px.bar(
        df,
        x="Type",
        y="Count",
        color="Type",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_layout(
        showlegend=False,
        height=400,
        xaxis_title="Operation Type",
        yaxis_title="Count",
        margin=dict(t=20, b=20, l=20, r=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_operations_timeline(logs: List[LogEntry]):
    """
    Render timeline of operations (last 100).
    
    Args:
        logs: List of parsed log entries
    """
    if not logs:
        st.info("No data to display")
        return
    
    # Create DataFrame
    df = pd.DataFrame([
        {
            "Timestamp": log.timestamp,
            "Service": log.service,
            "Type": log.operation_type,
            "Success": "✅ Success" if log.success else "❌ Failed"
        }
        for log in logs[:100]  # Limit to last 100 for performance
    ])
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x="Timestamp",
        y="Service",
        color="Success",
        symbol="Type",
        hover_data=["Type"],
        color_discrete_map={
            "✅ Success": "green",
            "❌ Failed": "red"
        }
    )
    
    fig.update_layout(
        height=300,
        xaxis_title="Time",
        yaxis_title="Service",
        margin=dict(t=20, b=40, l=100, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

