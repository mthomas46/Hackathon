"""
Operations tab rendering.

Displays detailed operation log with search and filtering.
"""

import streamlit as st
import pandas as pd
from typing import List

from data.models import LogEntry
from utils.formatting import (
    format_duration,
    format_timestamp,
    format_status_code,
    truncate_workflow_id
)


def render_operations_tab(logs: List[LogEntry]):
    """
    Render operations tab with detailed log table.
    
    Args:
        logs: List of parsed log entries
    """
    if not logs:
        st.info("📭 No operations to display. Waiting for data...")
        return
    
    st.markdown(f"### 📋 Operation Log ({len(logs)} operations)")
    
    # Search and filter controls
    filtered_logs = _render_filter_controls(logs)
    
    st.markdown(f"**Showing {len(filtered_logs)} of {len(logs)} operations**")
    
    # Render operations table
    _render_operations_table(filtered_logs)


def _render_filter_controls(logs: List[LogEntry]) -> List[LogEntry]:
    """
    Render filter controls and return filtered logs.
    
    Args:
        logs: List of log entries
        
    Returns:
        Filtered list of log entries
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Search by message
        search_query = st.text_input(
            "🔍 Search messages",
            placeholder="Type to search...",
            help="Search in log messages"
        )
    
    with col2:
        # Filter by operation type
        operation_types = ["All"] + sorted(list(set(log.operation_type for log in logs)))
        selected_type = st.selectbox(
            "Operation Type",
            options=operation_types,
            help="Filter by operation type"
        )
    
    with col3:
        # Filter by success status
        status_options = ["All", "Success", "Failed"]
        selected_status = st.selectbox(
            "Status",
            options=status_options,
            help="Filter by success status"
        )
    
    # Apply filters
    filtered_logs = logs
    
    # Search filter
    if search_query:
        filtered_logs = [
            log for log in filtered_logs
            if search_query.lower() in log.message.lower()
        ]
    
    # Operation type filter
    if selected_type != "All":
        filtered_logs = [
            log for log in filtered_logs
            if log.operation_type == selected_type
        ]
    
    # Status filter
    if selected_status == "Success":
        filtered_logs = [log for log in filtered_logs if log.success is True]
    elif selected_status == "Failed":
        filtered_logs = [log for log in filtered_logs if log.success is False]
    
    return filtered_logs


def _render_operations_table(logs: List[LogEntry]):
    """
    Render operations table with formatted columns.
    
    Args:
        logs: List of log entries
    """
    if not logs:
        st.info("No operations match the filters")
        return
    
    # Create DataFrame with formatted columns
    table_data = []
    for log in logs:
        table_data.append({
            "Time": format_timestamp(log.timestamp),
            "Service": log.service,
            "Type": log.operation_type,
            "Method": log.method or "—",
            "Path": log.path or "—",
            "Status": format_status_code(log.status_code),
            "Duration": format_duration(log.duration_ms),
            "Message": log.message[:50] + "..." if len(log.message) > 50 else log.message,
            "Workflow": truncate_workflow_id(log.workflow_id, max_length=12)
        })
    
    df = pd.DataFrame(table_data)
    
    # Display table
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Time": st.column_config.TextColumn("Time", width="medium"),
            "Service": st.column_config.TextColumn("Service", width="medium"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "Method": st.column_config.TextColumn("Method", width="small"),
            "Path": st.column_config.TextColumn("Path", width="large"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Duration": st.column_config.TextColumn("Duration", width="small"),
            "Message": st.column_config.TextColumn("Message", width="large"),
            "Workflow": st.column_config.TextColumn("Workflow ID", width="medium")
        }
    )
    
    # Export button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        # Export to CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Export CSV",
            data=csv,
            file_name="operations_export.csv",
            mime="text/csv",
            help="Download filtered operations as CSV"
        )
    
    with col2:
        # Show raw data
        if st.button("🔍 Show Raw Data"):
            st.json([log.model_dump(mode='json') for log in logs[:10]])

