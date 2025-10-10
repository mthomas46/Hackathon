"""
Workflows tab rendering.

Displays cross-service workflow tracing and timelines.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict
import pandas as pd
from datetime import datetime

from data.models import LogEntry
from data.parser import get_unique_workflows
from utils.formatting import format_duration, format_timestamp, truncate_workflow_id


def render_workflows_tab(logs: List[LogEntry]):
    """
    Render workflows tab with workflow tracing and analysis.
    
    Args:
        logs: List of parsed log entries
    """
    if not logs:
        st.info("📭 No operations to display. Waiting for data...")
        return
    
    # Filter logs with workflow IDs
    workflow_logs = [log for log in logs if log.workflow_id]
    
    if not workflow_logs:
        st.warning("⚠️ No workflow data available in logs")
        st.info("💡 Tip: Workflows are tracked using workflow_id in log context")
        return
    
    # Get unique workflows
    workflows = get_unique_workflows(workflow_logs)
    
    st.markdown(f"### 🌊 Workflows ({len(workflows)} unique workflows)")
    
    # Workflow selector
    selected_workflow = _render_workflow_selector(workflows, workflow_logs)
    
    if selected_workflow:
        st.markdown("---")
        _render_workflow_details(selected_workflow, workflow_logs)
    else:
        st.markdown("---")
        _render_workflow_summary(workflow_logs, workflows)


def _render_workflow_selector(
    workflows: List[str],
    workflow_logs: List[LogEntry]
) -> str:
    """
    Render workflow selector dropdown.
    
    Args:
        workflows: List of unique workflow IDs
        workflow_logs: All logs with workflow IDs
        
    Returns:
        Selected workflow ID or empty string
    """
    # Create workflow options with counts
    workflow_options = ["All Workflows"] + workflows
    
    # Count operations per workflow
    workflow_counts = {}
    for wf_id in workflows:
        count = sum(1 for log in workflow_logs if log.workflow_id == wf_id)
        workflow_counts[wf_id] = count
    
    # Format options
    formatted_options = {
        "All Workflows": "All Workflows"
    }
    for wf_id in workflows:
        formatted_options[wf_id] = f"{truncate_workflow_id(wf_id, 20)} ({workflow_counts[wf_id]} ops)"
    
    # Selector
    selected = st.selectbox(
        "Select Workflow",
        options=workflow_options,
        format_func=lambda x: formatted_options[x],
        help="Select a workflow to view details"
    )
    
    return selected if selected != "All Workflows" else ""


def _render_workflow_summary(workflow_logs: List[LogEntry], workflows: List[str]):
    """
    Render summary of all workflows.
    
    Args:
        workflow_logs: All logs with workflow IDs
        workflows: List of unique workflow IDs
    """
    st.markdown("### 📊 Workflow Summary")
    
    # Create summary data
    summary_data = []
    for wf_id in workflows[:20]:  # Limit to 20 for performance
        wf_logs = [log for log in workflow_logs if log.workflow_id == wf_id]
        
        # Calculate metrics
        total_ops = len(wf_logs)
        services = len(set(log.service for log in wf_logs))
        durations = [log.duration_ms for log in wf_logs if log.duration_ms is not None]
        total_duration = sum(durations) if durations else 0
        failed = sum(1 for log in wf_logs if log.success is False)
        
        summary_data.append({
            "Workflow ID": truncate_workflow_id(wf_id, 20),
            "Operations": total_ops,
            "Services": services,
            "Total Duration": format_duration(total_duration),
            "Status": "✅ Success" if failed == 0 else f"❌ {failed} failed",
            "Start Time": format_timestamp(min(log.timestamp for log in wf_logs))
        })
    
    df = pd.DataFrame(summary_data)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # Workflow distribution chart
    st.markdown("### 📈 Operations per Workflow")
    
    # Count operations per workflow (top 15)
    workflow_counts = {}
    for wf_id in workflows[:15]:
        count = sum(1 for log in workflow_logs if log.workflow_id == wf_id)
        workflow_counts[truncate_workflow_id(wf_id, 15)] = count
    
    df_counts = pd.DataFrame([
        {"Workflow": wf, "Operations": count}
        for wf, count in workflow_counts.items()
    ]).sort_values("Operations", ascending=True)
    
    fig = px.bar(
        df_counts,
        x="Operations",
        y="Workflow",
        orientation="h",
        color="Operations",
        color_continuous_scale="Blues"
    )
    
    fig.update_layout(
        height=400,
        xaxis_title="Number of Operations",
        yaxis_title="Workflow",
        margin=dict(t=20, b=40, l=150, r=20),
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_workflow_details(workflow_id: str, workflow_logs: List[LogEntry]):
    """
    Render detailed view of a single workflow.
    
    Args:
        workflow_id: Selected workflow ID
        workflow_logs: All logs with workflow IDs
    """
    # Filter logs for this workflow
    wf_logs = [log for log in workflow_logs if log.workflow_id == workflow_id]
    wf_logs = sorted(wf_logs, key=lambda x: x.timestamp)
    
    st.markdown(f"### 🔍 Workflow: `{workflow_id}`")
    
    # Workflow metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Operations", len(wf_logs))
    
    with col2:
        services = len(set(log.service for log in wf_logs))
        st.metric("Services", services)
    
    with col3:
        durations = [log.duration_ms for log in wf_logs if log.duration_ms is not None]
        total_duration = sum(durations) if durations else 0
        st.metric("Total Duration", format_duration(total_duration))
    
    with col4:
        failed = sum(1 for log in wf_logs if log.success is False)
        status = "✅ Success" if failed == 0 else f"❌ {failed} failed"
        st.metric("Status", status)
    
    st.markdown("---")
    
    # Workflow timeline
    st.markdown("### ⏱️ Workflow Timeline")
    _render_workflow_timeline(wf_logs)
    
    st.markdown("---")
    
    # Operation details table
    st.markdown("### 📋 Operation Details")
    _render_workflow_operations_table(wf_logs)


def _render_workflow_timeline(wf_logs: List[LogEntry]):
    """
    Render Gantt chart timeline of workflow operations.
    
    Args:
        wf_logs: Logs for a single workflow
    """
    # Create timeline data
    timeline_data = []
    for i, log in enumerate(wf_logs):
        start_time = log.timestamp
        duration_ms = log.duration_ms or 10  # Default 10ms if no duration
        
        timeline_data.append({
            "Task": f"{log.service} - {log.operation_type}",
            "Start": start_time,
            "Finish": start_time.timestamp() + (duration_ms / 1000),
            "Service": log.service,
            "Duration": format_duration(log.duration_ms),
            "Status": "✅" if log.success else "❌"
        })
    
    df = pd.DataFrame(timeline_data)
    
    # Convert timestamps for Gantt chart
    df["Start_str"] = df["Start"].dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    df["Finish_dt"] = pd.to_datetime(df["Finish"], unit='s')
    df["Finish_str"] = df["Finish_dt"].dt.strftime("%Y-%m-%d %H:%M:%S.%f")
    
    # Create Gantt chart
    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish_dt",
        y="Task",
        color="Service",
        hover_data=["Duration", "Status"]
    )
    
    fig.update_yaxes(autorange="reversed")
    
    fig.update_layout(
        height=max(300, len(wf_logs) * 40),
        xaxis_title="Time",
        yaxis_title="Operation",
        margin=dict(t=20, b=40, l=200, r=20),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def _render_workflow_operations_table(wf_logs: List[LogEntry]):
    """
    Render table of operations in workflow.
    
    Args:
        wf_logs: Logs for a single workflow
    """
    table_data = []
    for i, log in enumerate(wf_logs, 1):
        table_data.append({
            "#": i,
            "Time": format_timestamp(log.timestamp),
            "Service": log.service,
            "Operation": log.operation_type,
            "Method": log.method or "—",
            "Path": log.path or "—",
            "Duration": format_duration(log.duration_ms),
            "Status": "✅" if log.success else "❌",
            "Message": log.message[:40] + "..." if len(log.message) > 40 else log.message
        })
    
    df = pd.DataFrame(table_data)
    
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

