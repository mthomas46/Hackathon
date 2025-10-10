"""
Errors tab rendering.

Displays error analysis by service and status code.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict
import pandas as pd

from data.models import LogEntry
from metrics.calculator import calculate_status_code_distribution
from utils.formatting import format_timestamp, format_duration, format_percentage


def render_errors_tab(logs: List[LogEntry]):
    """
    Render errors tab with error analysis and diagnostics.
    
    Args:
        logs: List of parsed log entries
    """
    if not logs:
        st.info("📭 No operations to display. Waiting for data...")
        return
    
    # Filter failed operations
    failed_logs = [log for log in logs if log.success is False]
    
    if not failed_logs:
        st.success("🎉 No errors detected! All operations successful.")
        st.balloons()
        return
    
    # Error summary
    _render_error_summary(logs, failed_logs)
    
    st.markdown("---")
    
    # Error distribution charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ❌ Errors by Service")
        _render_errors_by_service(failed_logs)
    
    with col2:
        st.markdown("### 🔢 Status Code Distribution")
        _render_status_code_distribution(failed_logs)
    
    st.markdown("---")
    
    # Error timeline
    st.markdown("### 📈 Error Timeline")
    _render_error_timeline(failed_logs)
    
    st.markdown("---")
    
    # Failed operations table
    st.markdown("### 📋 Failed Operations")
    _render_failed_operations_table(failed_logs)


def _render_error_summary(all_logs: List[LogEntry], failed_logs: List[LogEntry]):
    """
    Render error summary metrics row.
    
    Args:
        all_logs: All log entries
        failed_logs: Failed log entries
    """
    total = len(all_logs)
    failed = len(failed_logs)
    error_rate = (failed / total * 100) if total > 0 else 0.0
    
    # Count unique services with errors
    services_with_errors = len(set(log.service for log in failed_logs))
    
    # Most common error status
    status_codes = [log.status_code for log in failed_logs if log.status_code is not None]
    most_common_status = max(set(status_codes), key=status_codes.count) if status_codes else None
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Errors",
            failed,
            delta=f"-{error_rate:.1f}% error rate",
            delta_color="inverse",
            help="Total number of failed operations"
        )
    
    with col2:
        st.metric(
            "Services Affected",
            services_with_errors,
            help="Number of services with errors"
        )
    
    with col3:
        st.metric(
            "Error Rate",
            format_percentage(error_rate),
            help="Percentage of operations that failed"
        )
    
    with col4:
        st.metric(
            "Most Common Status",
            most_common_status or "N/A",
            help="Most frequent HTTP status code in errors"
        )
    
    with col5:
        # Success rate (inverse of error rate)
        success_rate = 100 - error_rate
        st.metric(
            "Success Rate",
            format_percentage(success_rate),
            delta=f"✅ {len(all_logs) - failed} succeeded",
            delta_color="normal",
            help="Percentage of successful operations"
        )


def _render_errors_by_service(failed_logs: List[LogEntry]):
    """
    Render bar chart of errors by service.
    
    Args:
        failed_logs: Failed log entries
    """
    # Count errors per service
    errors_per_service = {}
    for log in failed_logs:
        service = log.service
        errors_per_service[service] = errors_per_service.get(service, 0) + 1
    
    # Create DataFrame
    df = pd.DataFrame([
        {"Service": service, "Errors": count}
        for service, count in sorted(errors_per_service.items(), key=lambda x: -x[1])
    ])
    
    # Create bar chart
    fig = px.bar(
        df,
        x="Service",
        y="Errors",
        color="Errors",
        color_continuous_scale="Reds"
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Service",
        yaxis_title="Error Count",
        margin=dict(t=20, b=40, l=40, r=20),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_status_code_distribution(failed_logs: List[LogEntry]):
    """
    Render pie chart of HTTP status codes.
    
    Args:
        failed_logs: Failed log entries
    """
    status_distribution = calculate_status_code_distribution(failed_logs)
    
    if not status_distribution:
        st.info("No status code data available")
        return
    
    # Create DataFrame
    df = pd.DataFrame([
        {"Status Code": f"{code} ({_get_status_name(code)})", "Count": count}
        for code, count in status_distribution.items()
    ])
    
    # Create pie chart
    fig = px.pie(
        df,
        values="Count",
        names="Status Code",
        hole=0.3,
        color_discrete_sequence=px.colors.sequential.Reds
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label'
    )
    
    fig.update_layout(
        height=400,
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_error_timeline(failed_logs: List[LogEntry]):
    """
    Render timeline of errors.
    
    Args:
        failed_logs: Failed log entries
    """
    # Limit to last 100 for performance
    recent_errors = failed_logs[:100]
    
    # Create DataFrame
    df = pd.DataFrame([
        {
            "Timestamp": log.timestamp,
            "Service": log.service,
            "Status": log.status_code or "Unknown",
            "Operation": log.operation_type
        }
        for log in recent_errors
    ])
    
    # Create scatter plot
    fig = px.scatter(
        df,
        x="Timestamp",
        y="Service",
        color="Status",
        symbol="Operation",
        hover_data=["Operation"],
        color_continuous_scale="Reds"
    )
    
    fig.update_layout(
        height=300,
        xaxis_title="Time",
        yaxis_title="Service",
        margin=dict(t=20, b=40, l=100, r=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_failed_operations_table(failed_logs: List[LogEntry]):
    """
    Render table of failed operations.
    
    Args:
        failed_logs: Failed log entries
    """
    # Create table data
    table_data = []
    for log in failed_logs[:50]:  # Limit to 50 for performance
        table_data.append({
            "Time": format_timestamp(log.timestamp),
            "Service": log.service,
            "Operation": log.operation_type,
            "Method": log.method or "—",
            "Path": log.path or "—",
            "Status": log.status_code or "N/A",
            "Duration": format_duration(log.duration_ms),
            "Error Message": log.message[:60] + "..." if len(log.message) > 60 else log.message
        })
    
    df = pd.DataFrame(table_data)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Time": st.column_config.TextColumn("Time", width="medium"),
            "Service": st.column_config.TextColumn("Service", width="medium"),
            "Operation": st.column_config.TextColumn("Operation", width="small"),
            "Method": st.column_config.TextColumn("Method", width="small"),
            "Path": st.column_config.TextColumn("Path", width="large"),
            "Status": st.column_config.NumberColumn("Status", width="small"),
            "Duration": st.column_config.TextColumn("Duration", width="small"),
            "Error Message": st.column_config.TextColumn("Error Message", width="large")
        }
    )
    
    # Show more details
    with st.expander("🔍 Error Details by Service"):
        # Group errors by service
        services = set(log.service for log in failed_logs)
        
        for service in sorted(services):
            service_errors = [log for log in failed_logs if log.service == service]
            
            st.markdown(f"**{service}** ({len(service_errors)} errors)")
            
            # Most common error messages
            messages = [log.message for log in service_errors if log.message]
            if messages:
                from collections import Counter
                common_messages = Counter(messages).most_common(3)
                
                for msg, count in common_messages:
                    st.markdown(f"- `{msg[:80]}` ({count}x)")
            
            st.markdown("")


def _get_status_name(status_code: int) -> str:
    """
    Get human-readable name for HTTP status code.
    
    Args:
        status_code: HTTP status code
        
    Returns:
        Status code name
    """
    status_names = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        408: "Timeout",
        409: "Conflict",
        422: "Validation Error",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout"
    }
    
    return status_names.get(status_code, "Error")

