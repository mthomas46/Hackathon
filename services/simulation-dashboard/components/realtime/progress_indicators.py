"""Progress Indicators Component.

This module provides real-time progress indicators and status tracking
for simulations and long-running operations.
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
from datetime import datetime, timedelta
import time
import numpy as np


def render_progress_indicator(
    progress_data: Dict[str, Any],
    title: str = "📊 Progress Indicator",
    show_eta: bool = True,
    show_details: bool = True,
    enable_notifications: bool = True,
    on_complete: Optional[Callable] = None,
    on_error: Optional[Callable] = None
) -> Dict[str, Any]:
    """Render a comprehensive progress indicator for operations.

    Args:
        progress_data: Progress data dictionary
        title: Indicator title
        show_eta: Whether to show estimated time
        show_details: Whether to show detailed progress
        enable_notifications: Whether to enable completion notifications
        on_complete: Callback for completion
        on_error: Callback for errors

    Returns:
        Dictionary with current progress status
    """
    st.markdown(f"### {title}")

    # Initialize progress data if not provided
    if not progress_data:
        progress_data = get_default_progress_data()

    # Extract progress information
    operation_id = progress_data.get('operation_id', 'unknown')
    operation_name = progress_data.get('operation_name', 'Unknown Operation')
    progress_percent = progress_data.get('progress', 0)
    status = progress_data.get('status', 'pending')
    start_time = progress_data.get('start_time')
    estimated_duration = progress_data.get('estimated_duration', 0)
    current_stage = progress_data.get('current_stage', 'Initializing')
    total_stages = progress_data.get('total_stages', 1)
    current_stage_progress = progress_data.get('current_stage_progress', 0)

    # Status-based styling
    status_icon, status_color = get_status_display(status)

    # Main progress display
    st.markdown(f"## {status_icon} {operation_name}")
    st.markdown(f"**Operation ID:** {operation_id}")
    st.markdown(f"**Status:** {status.title()}")

    # Overall progress bar
    if progress_percent >= 0:
        st.progress(progress_percent / 100, text=".1f")

    # Stage progress
    if total_stages > 1:
        st.markdown(f"**Current Stage:** {current_stage} ({progress_data.get('current_stage_num', 1)}/{total_stages})")

        if current_stage_progress >= 0:
            stage_progress = min(current_stage_progress / 100, 1.0)
            st.progress(stage_progress, text=".1f")

    # Time information
    display_time_information(start_time, estimated_duration, progress_percent, show_eta)

    # Detailed progress information
    if show_details:
        display_detailed_progress(progress_data)

    # Control buttons
    display_progress_controls(progress_data, on_complete, on_error)

    # Real-time updates simulation
    if status in ['running', 'processing']:
        simulate_progress_updates(progress_data)

    return {
        'current_progress': progress_percent,
        'status': status,
        'estimated_completion': calculate_eta(start_time, estimated_duration, progress_percent),
        'stage_info': {
            'current': current_stage,
            'progress': current_stage_progress,
            'total_stages': total_stages
        }
    }


def display_time_information(start_time: Optional[datetime], estimated_duration: float, progress: float, show_eta: bool):
    """Display time-related information."""
    if not start_time:
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        elapsed = (datetime.now() - start_time).total_seconds()
        st.metric("Elapsed Time", format_duration(elapsed))

    with col2:
        if estimated_duration > 0 and progress > 0:
            eta = calculate_eta(start_time, estimated_duration, progress)
            if eta:
                st.metric("ETA", eta.strftime("%H:%M:%S"))
        else:
            st.metric("ETA", "Calculating...")

    with col3:
        if estimated_duration > 0:
            remaining = max(0, estimated_duration - elapsed)
            st.metric("Time Remaining", format_duration(remaining))


def display_detailed_progress(progress_data: Dict[str, Any]):
    """Display detailed progress information."""
    with st.expander("📋 Progress Details", expanded=False):
        # Current metrics
        metrics = progress_data.get('metrics', {})

        if metrics:
            st.markdown("**Current Metrics:**")
            cols = st.columns(min(3, len(metrics)))

            for i, (metric_name, metric_value) in enumerate(metrics.items()):
                col_idx = i % 3
                if col_idx == 0 and i > 0:
                    cols = st.columns(min(3, len(metrics) - i))

                with cols[col_idx]:
                    if isinstance(metric_value, (int, float)):
                        st.metric(metric_name.replace('_', ' ').title(), ".2f")
                    else:
                        st.metric(metric_name.replace('_', ' ').title(), str(metric_value))

        # Recent activities
        activities = progress_data.get('recent_activities', [])
        if activities:
            st.markdown("**Recent Activities:**")
            for activity in activities[-5:]:  # Show last 5 activities
                timestamp = activity.get('timestamp', datetime.now())
                message = activity.get('message', 'Unknown activity')

                time_str = timestamp.strftime("%H:%M:%S") if isinstance(timestamp, datetime) else str(timestamp)
                st.write(f"• {time_str}: {message}")

        # Performance information
        performance = progress_data.get('performance', {})
        if performance:
            st.markdown("**Performance Metrics:**")

            perf_cols = st.columns(2)
            with perf_cols[0]:
                if 'cpu_usage' in performance:
                    st.metric("CPU Usage", ".1f")
                if 'memory_usage' in performance:
                    st.metric("Memory Usage", ".1f")

            with perf_cols[1]:
                if 'throughput' in performance:
                    st.metric("Throughput", ".1f")
                if 'error_rate' in performance:
                    st.metric("Error Rate", ".1f")


def display_progress_controls(progress_data: Dict[str, Any], on_complete: Callable, on_error: Callable):
    """Display progress control buttons."""
    status = progress_data.get('status', 'pending')
    operation_id = progress_data.get('operation_id', 'unknown')

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if status in ['running', 'processing']:
            if st.button("⏸️ Pause", key=f"pause_{operation_id}"):
                progress_data['status'] = 'paused'
                st.success("⏸️ Operation paused")

    with col2:
        if status == 'paused':
            if st.button("▶️ Resume", key=f"resume_{operation_id}"):
                progress_data['status'] = 'running'
                st.success("▶️ Operation resumed")

    with col3:
        if status in ['running', 'paused', 'processing']:
            if st.button("⏹️ Stop", key=f"stop_{operation_id}", type="secondary"):
                if st.checkbox("Confirm stop operation", key=f"confirm_stop_{operation_id}"):
                    progress_data['status'] = 'stopped'
                    st.warning("⏹️ Operation stopped")
                    if on_error:
                        on_error(operation_id, "Operation stopped by user")

    with col4:
        # Show logs button
        if st.button("📋 View Logs", key=f"logs_{operation_id}"):
            display_operation_logs(progress_data)


def display_operation_logs(progress_data: Dict[str, Any]):
    """Display operation logs."""
    logs = progress_data.get('logs', [])

    if not logs:
        st.info("No logs available for this operation.")
        return

    st.markdown("#### 📋 Operation Logs")

    # Create logs dataframe
    logs_df = pd.DataFrame(logs)

    if not logs_df.empty:
        # Display logs in a table
        st.dataframe(
            logs_df,
            use_container_width=True,
            hide_index=True
        )

        # Export logs
        if st.button("📥 Export Logs", key="export_logs"):
            csv_data = logs_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="operation_logs.csv",
                mime='text/csv',
                key="download_logs_csv"
            )


def simulate_progress_updates(progress_data: Dict[str, Any]):
    """Simulate real-time progress updates."""
    # This would typically connect to a WebSocket or polling endpoint
    # For demonstration, we'll simulate progress updates

    status = progress_data.get('status')

    if status in ['running', 'processing']:
        # Simulate progress increase
        current_progress = progress_data.get('progress', 0)

        # Random progress increase (0-2%)
        progress_increase = np.random.uniform(0, 2)
        new_progress = min(100, current_progress + progress_increase)

        progress_data['progress'] = new_progress

        # Update stage progress
        current_stage_progress = progress_data.get('current_stage_progress', 0)
        stage_increase = np.random.uniform(0, 3)
        new_stage_progress = min(100, current_stage_progress + stage_increase)
        progress_data['current_stage_progress'] = new_stage_progress

        # Simulate stage completion
        if new_stage_progress >= 100:
            current_stage_num = progress_data.get('current_stage_num', 1)
            total_stages = progress_data.get('total_stages', 1)

            if current_stage_num < total_stages:
                progress_data['current_stage_num'] = current_stage_num + 1
                progress_data['current_stage_progress'] = 0

                # Update stage name
                stages = progress_data.get('stages', [])
                if current_stage_num < len(stages):
                    progress_data['current_stage'] = stages[current_stage_num]

        # Check for completion
        if new_progress >= 100:
            progress_data['status'] = 'completed'
            progress_data['end_time'] = datetime.now()

            # Calculate actual duration
            start_time = progress_data.get('start_time')
            if start_time:
                actual_duration = (datetime.now() - start_time).total_seconds()
                progress_data['actual_duration'] = actual_duration

            st.success("🎉 Operation completed successfully!")

        # Add to activity log
        activities = progress_data.get('recent_activities', [])
        activities.append({
            'timestamp': datetime.now(),
            'message': f"Progress updated to {new_progress:.1f}%"
        })

        # Keep only recent activities
        if len(activities) > 20:
            activities = activities[-20:]

        progress_data['recent_activities'] = activities


def calculate_eta(start_time: datetime, estimated_duration: float, progress: float) -> Optional[datetime]:
    """Calculate estimated time of arrival."""
    if not start_time or progress <= 0 or progress >= 100:
        return None

    elapsed = (datetime.now() - start_time).total_seconds()
    total_estimated = estimated_duration

    if elapsed > 0 and total_estimated > elapsed:
        remaining = total_estimated - elapsed
        return datetime.now() + timedelta(seconds=remaining)

    return None


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format."""
    if seconds < 60:
        return ".1f"
    elif seconds < 3600:
        return ".1f"
    elif seconds < 86400:
        return ".1f"
    else:
        return ".1f"


def get_status_display(status: str) -> tuple[str, str]:
    """Get status icon and color."""
    status_map = {
        'pending': ('⏳', '#6c757d'),
        'running': ('🔄', '#007bff'),
        'processing': ('⚙️', '#28a745'),
        'paused': ('⏸️', '#ffc107'),
        'completed': ('✅', '#28a745'),
        'failed': ('❌', '#dc3545'),
        'stopped': ('⏹️', '#6c757d'),
        'cancelled': ('🚫', '#dc3545')
    }

    return status_map.get(status, ('❓', '#6c757d'))


def get_default_progress_data() -> Dict[str, Any]:
    """Get default progress data for demonstration."""
    return {
        'operation_id': 'op_001',
        'operation_name': 'Sample Simulation',
        'progress': 45.5,
        'status': 'running',
        'start_time': datetime.now() - timedelta(minutes=12),
        'estimated_duration': 1200,  # 20 minutes
        'current_stage': 'Data Processing',
        'current_stage_num': 2,
        'total_stages': 5,
        'current_stage_progress': 78.3,
        'stages': ['Initialization', 'Data Processing', 'Analysis', 'Reporting', 'Cleanup'],
        'metrics': {
            'records_processed': 1250,
            'success_rate': 98.5,
            'average_response_time': 245.8
        },
        'performance': {
            'cpu_usage': 67.3,
            'memory_usage': 72.1,
            'throughput': 1250.0,
            'error_rate': 0.05
        },
        'recent_activities': [
            {'timestamp': datetime.now() - timedelta(minutes=2), 'message': 'Started data processing phase'},
            {'timestamp': datetime.now() - timedelta(minutes=1), 'message': 'Processed 750 records'},
            {'timestamp': datetime.now(), 'message': 'Analysis phase initiated'}
        ],
        'logs': [
            {'timestamp': datetime.now() - timedelta(minutes=15), 'level': 'INFO', 'message': 'Operation started'},
            {'timestamp': datetime.now() - timedelta(minutes=12), 'level': 'INFO', 'message': 'Initialization completed'},
            {'timestamp': datetime.now() - timedelta(minutes=10), 'level': 'INFO', 'message': 'Data loading completed'},
            {'timestamp': datetime.now() - timedelta(minutes=2), 'level': 'INFO', 'message': 'Processing phase started'}
        ]
    }


# Progress tracking manager for multiple operations
class ProgressManager:
    """Manager for tracking multiple progress indicators."""

    def __init__(self):
        self.operations = {}

    def add_operation(self, operation_id: str, progress_data: Dict[str, Any]):
        """Add a new operation to track."""
        self.operations[operation_id] = progress_data

    def update_operation(self, operation_id: str, updates: Dict[str, Any]):
        """Update an operation's progress."""
        if operation_id in self.operations:
            self.operations[operation_id].update(updates)

    def get_operation(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get operation progress data."""
        return self.operations.get(operation_id)

    def remove_operation(self, operation_id: str):
        """Remove an operation from tracking."""
        if operation_id in self.operations:
            del self.operations[operation_id]

    def get_all_operations(self) -> Dict[str, Dict[str, Any]]:
        """Get all operations being tracked."""
        return self.operations.copy()

    def get_operations_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get operations by status."""
        return [op for op in self.operations.values() if op.get('status') == status]


# Global progress manager instance
progress_manager = ProgressManager()
