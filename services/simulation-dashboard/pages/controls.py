"""Advanced Simulation Controls Page.

This module provides comprehensive simulation control interfaces,
enabling users to manage simulation lifecycles, implement bulk operations,
and monitor control status in real-time.
"""

import streamlit as st
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json

from services.clients.simulation_client import SimulationClient
from infrastructure.config.config import get_config


def render_controls_page():
    """Render the advanced simulation controls page."""
    st.markdown("## 🎮 Advanced Simulation Controls")
    st.markdown("Comprehensive simulation lifecycle management with real-time control and monitoring.")

    # Initialize session state
    initialize_controls_state()

    # Create tabs for different control aspects
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎛️ Control Panel",
        "📊 Bulk Operations",
        "📈 Status Monitor",
        "⚙️ Queue Management"
    ])

    with tab1:
        render_control_panel()

    with tab2:
        render_bulk_operations()

    with tab3:
        render_status_monitor()

    with tab4:
        render_queue_management()


def initialize_controls_state():
    """Initialize session state for controls page."""
    if 'selected_simulations' not in st.session_state:
        st.session_state.selected_simulations = []

    if 'control_operations' not in st.session_state:
        st.session_state.control_operations = []

    if 'bulk_operation_status' not in st.session_state:
        st.session_state.bulk_operation_status = {}

    if 'control_status_updates' not in st.session_state:
        st.session_state.control_status_updates = []


def render_control_panel():
    """Render the main simulation control panel."""
    st.markdown("### 🎛️ Simulation Control Panel")

    # Simulation selection
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("#### Select Simulation")
        simulations = get_available_simulations()

        if simulations:
            simulation_options = ["Select a simulation..."] + [
                f"{sim.get('id', 'Unknown')} - {sim.get('name', 'Unnamed')} ({sim.get('status', 'Unknown')})"
                for sim in simulations
            ]

            selected_sim_option = st.selectbox(
                "Target Simulation",
                options=simulation_options,
                key="control_simulation_selector"
            )

            if selected_sim_option and selected_sim_option != "Select a simulation...":
                sim_id = selected_sim_option.split(" - ")[0]
                st.session_state.selected_control_simulation = sim_id
            else:
                st.session_state.selected_control_simulation = None
        else:
            st.warning("No simulations available for control.")
            return

    with col2:
        if st.button("🔄 Refresh", key="refresh_simulations"):
            # Force refresh of simulation list
            st.rerun()

    # Control interface
    if st.session_state.selected_control_simulation:
        render_simulation_controls(st.session_state.selected_control_simulation)


def render_simulation_controls(simulation_id: str):
    """Render detailed controls for a specific simulation."""
    st.markdown("---")

    # Get simulation details
    simulation_details = get_simulation_details(simulation_id)

    if not simulation_details:
        st.error(f"Could not retrieve details for simulation {simulation_id}")
        return

    # Status overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        status = simulation_details.get('status', 'Unknown')
        status_color = get_status_color(status)
        st.metric("Status", status)

    with col2:
        progress = simulation_details.get('progress', 0)
        st.metric("Progress", ".1f")

    with col3:
        elapsed = simulation_details.get('elapsed_time', 'Unknown')
        st.metric("Elapsed Time", elapsed)

    with col4:
        remaining = simulation_details.get('estimated_time_remaining', 'Unknown')
        st.metric("Time Remaining", remaining)

    # Control buttons
    st.markdown("#### 🎮 Control Actions")

    # Primary controls row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if st.button("▶️ Start", key=f"start_{simulation_id}", type="primary",
                    disabled=status in ['running', 'completed', 'failed']):
            execute_control_action(simulation_id, "start")

    with col2:
        if st.button("⏸️ Pause", key=f"pause_{simulation_id}",
                    disabled=status not in ['running']):
            execute_control_action(simulation_id, "pause")

    with col3:
        if st.button("▶️ Resume", key=f"resume_{simulation_id}",
                    disabled=status not in ['paused']):
            execute_control_action(simulation_id, "resume")

    with col4:
        if st.button("⏹️ Stop", key=f"stop_{simulation_id}",
                    disabled=status not in ['running', 'paused']):
            execute_control_action(simulation_id, "stop")

    with col5:
        if st.button("❌ Cancel", key=f"cancel_{simulation_id}",
                    disabled=status in ['completed', 'cancelled', 'failed']):
            execute_control_action(simulation_id, "cancel")

    # Advanced controls
    st.markdown("#### ⚙️ Advanced Controls")

    with st.expander("Advanced Options", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Priority Management**")
            priority = st.selectbox(
                "Set Priority",
                options=["Low", "Normal", "High", "Critical"],
                index=1,
                key=f"priority_{simulation_id}"
            )

            if st.button("Update Priority", key=f"update_priority_{simulation_id}"):
                update_simulation_priority(simulation_id, priority)

        with col2:
            st.markdown("**Resource Allocation**")
            cpu_limit = st.slider(
                "CPU Limit (%)",
                min_value=10,
                max_value=100,
                value=50,
                key=f"cpu_limit_{simulation_id}"
            )

            memory_limit = st.slider(
                "Memory Limit (MB)",
                min_value=128,
                max_value=2048,
                value=512,
                key=f"memory_limit_{simulation_id}"
            )

            if st.button("Update Resources", key=f"update_resources_{simulation_id}"):
                update_simulation_resources(simulation_id, cpu_limit, memory_limit)

    # Control history
    st.markdown("#### 📋 Control History")
    render_control_history(simulation_id)


def render_bulk_operations():
    """Render bulk operations interface."""
    st.markdown("### 📊 Bulk Operations")
    st.markdown("Execute operations across multiple simulations simultaneously.")

    # Simulation selection for bulk operations
    st.markdown("#### Select Simulations")

    simulations = get_available_simulations()
    if not simulations:
        st.warning("No simulations available for bulk operations.")
        return

    simulation_options = [
        f"{sim.get('id', 'Unknown')} - {sim.get('name', 'Unnamed')}"
        for sim in simulations
    ]

    selected_simulations = st.multiselect(
        "Select simulations for bulk operation",
        options=simulation_options,
        key="bulk_simulation_selector"
    )

    if not selected_simulations:
        st.info("Select one or more simulations to enable bulk operations.")
        return

    # Extract simulation IDs
    selected_ids = [sim.split(" - ")[0] for sim in selected_simulations]

    # Bulk operation controls
    st.markdown("#### Bulk Control Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("▶️ Bulk Start", key="bulk_start", type="primary"):
            execute_bulk_operation(selected_ids, "start")

    with col2:
        if st.button("⏸️ Bulk Pause", key="bulk_pause"):
            execute_bulk_operation(selected_ids, "pause")

    with col3:
        if st.button("⏹️ Bulk Stop", key="bulk_stop"):
            execute_bulk_operation(selected_ids, "stop")

    with col4:
        if st.button("❌ Bulk Cancel", key="bulk_cancel"):
            execute_bulk_operation(selected_ids, "cancel")

    # Bulk status monitoring
    if st.session_state.bulk_operation_status:
        st.markdown("#### 📈 Bulk Operation Status")
        render_bulk_status(selected_ids)


def render_status_monitor():
    """Render comprehensive status monitoring interface."""
    st.markdown("### 📈 Real-Time Status Monitor")
    st.markdown("Monitor simulation execution status and control operations in real-time.")

    # Auto-refresh toggle
    col1, col2 = st.columns([1, 3])

    with col1:
        auto_refresh = st.checkbox("Auto-refresh", value=True, key="status_auto_refresh")

    with col2:
        if auto_refresh:
            refresh_interval = st.slider(
                "Refresh interval (seconds)",
                min_value=5,
                max_value=60,
                value=10,
                key="status_refresh_interval"
            )

    # Status overview
    st.markdown("#### 📊 Status Overview")

    simulations = get_available_simulations()
    if simulations:
        render_simulation_status_grid(simulations)
    else:
        st.info("No simulations available for monitoring.")

    # Control operation timeline
    st.markdown("#### ⏰ Control Operations Timeline")
    render_control_timeline()

    # System resource status
    st.markdown("#### 💻 System Resources")
    render_system_resources_status()

    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()


def render_queue_management():
    """Render simulation queue management interface."""
    st.markdown("### ⚙️ Queue Management")
    st.markdown("Manage simulation execution queues and scheduling priorities.")

    # Queue overview
    st.markdown("#### 📋 Queue Overview")

    queue_status = get_queue_status()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Queued", queue_status.get('queued', 0))

    with col2:
        st.metric("Running", queue_status.get('running', 0))

    with col3:
        st.metric("Completed", queue_status.get('completed', 0))

    with col4:
        st.metric("Failed", queue_status.get('failed', 0))

    # Queue controls
    st.markdown("#### 🎛️ Queue Controls")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("▶️ Start Queue Processing", key="start_queue"):
            control_queue_processing("start")

    with col2:
        if st.button("⏸️ Pause Queue Processing", key="pause_queue"):
            control_queue_processing("pause")

    with col3:
        if st.button("🧹 Clear Failed Simulations", key="clear_failed"):
            clear_failed_simulations()

    # Queue configuration
    st.markdown("#### ⚙️ Queue Configuration")

    with st.expander("Queue Settings", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            max_concurrent = st.slider(
                "Max Concurrent Simulations",
                min_value=1,
                max_value=20,
                value=5,
                key="max_concurrent"
            )

            priority_weight = st.slider(
                "Priority Weight",
                min_value=1,
                max_value=10,
                value=3,
                key="priority_weight"
            )

        with col2:
            timeout_minutes = st.slider(
                "Default Timeout (minutes)",
                min_value=5,
                max_value=480,
                value=60,
                key="timeout_minutes"
            )

            retry_attempts = st.slider(
                "Max Retry Attempts",
                min_value=0,
                max_value=5,
                value=2,
                key="retry_attempts"
            )

        if st.button("💾 Save Queue Configuration", key="save_queue_config"):
            save_queue_configuration({
                'max_concurrent': max_concurrent,
                'priority_weight': priority_weight,
                'timeout_minutes': timeout_minutes,
                'retry_attempts': retry_attempts
            })

    # Queue visualization
    st.markdown("#### 📊 Queue Visualization")
    render_queue_visualization()


# Helper functions

def get_available_simulations() -> List[Dict[str, Any]]:
    """Get list of available simulations for control."""
    try:
        config = get_config()
        client = SimulationClient(config.simulation_service)

        # In a real implementation, this would call the API
        # For now, return mock data
        return [
            {
                'id': 'sim_001',
                'name': 'E-commerce Platform Development',
                'status': 'running',
                'progress': 65.5,
                'created_at': '2024-01-15T10:00:00Z'
            },
            {
                'id': 'sim_002',
                'name': 'Mobile App Development',
                'status': 'paused',
                'progress': 30.2,
                'created_at': '2024-01-16T08:30:00Z'
            },
            {
                'id': 'sim_003',
                'name': 'API Service Implementation',
                'status': 'completed',
                'progress': 100.0,
                'created_at': '2024-01-14T15:45:00Z'
            }
        ]

    except Exception as e:
        st.error(f"Failed to get simulations: {str(e)}")
        return []


def get_simulation_details(simulation_id: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific simulation."""
    # Mock implementation - in real system, this would call the API
    simulation_data = {
        'sim_001': {
            'id': 'sim_001',
            'name': 'E-commerce Platform Development',
            'status': 'running',
            'progress': 65.5,
            'elapsed_time': '2h 15m',
            'estimated_time_remaining': '45m',
            'current_phase': 'Implementation',
            'cpu_usage': 45.2,
            'memory_usage': 512.8,
            'documents_generated': 12,
            'workflows_executed': 8
        },
        'sim_002': {
            'id': 'sim_002',
            'name': 'Mobile App Development',
            'status': 'paused',
            'progress': 30.2,
            'elapsed_time': '1h 30m',
            'estimated_time_remaining': '2h 15m',
            'current_phase': 'Design',
            'cpu_usage': 0.0,
            'memory_usage': 128.4,
            'documents_generated': 5,
            'workflows_executed': 3
        },
        'sim_003': {
            'id': 'sim_003',
            'name': 'API Service Implementation',
            'status': 'completed',
            'progress': 100.0,
            'elapsed_time': '3h 45m',
            'estimated_time_remaining': '0m',
            'current_phase': 'Completed',
            'cpu_usage': 0.0,
            'memory_usage': 256.1,
            'documents_generated': 18,
            'workflows_executed': 12
        }
    }

    return simulation_data.get(simulation_id)


def execute_control_action(simulation_id: str, action: str):
    """Execute a control action on a simulation."""
    try:
        # Mock implementation - in real system, this would call the API
        operation = {
            'simulation_id': simulation_id,
            'action': action,
            'timestamp': datetime.now().isoformat(),
            'status': 'executing'
        }

        # Add to control operations history
        if 'control_operations' not in st.session_state:
            st.session_state.control_operations = []

        st.session_state.control_operations.append(operation)

        # Show success message
        action_display = action.title()
        st.success(f"✅ {action_display} command sent to simulation {simulation_id}")

        # Log the operation
        st.info(f"📝 Operation logged: {action_display} simulation {simulation_id}")

    except Exception as e:
        st.error(f"❌ Failed to execute {action} on simulation {simulation_id}: {str(e)}")


def update_simulation_priority(simulation_id: str, priority: str):
    """Update simulation priority."""
    try:
        # Mock implementation
        st.success(f"✅ Priority updated to {priority} for simulation {simulation_id}")
    except Exception as e:
        st.error(f"❌ Failed to update priority: {str(e)}")


def update_simulation_resources(simulation_id: str, cpu_limit: int, memory_limit: int):
    """Update simulation resource allocation."""
    try:
        # Mock implementation
        st.success(f"✅ Resources updated - CPU: {cpu_limit}%, Memory: {memory_limit}MB for simulation {simulation_id}")
    except Exception as e:
        st.error(f"❌ Failed to update resources: {str(e)}")


def render_control_history(simulation_id: str):
    """Render control operation history for a simulation."""
    operations = st.session_state.get('control_operations', [])
    sim_operations = [op for op in operations if op['simulation_id'] == simulation_id]

    if not sim_operations:
        st.info("No control operations recorded for this simulation.")
        return

    # Display recent operations
    for op in sim_operations[-5:]:  # Show last 5 operations
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.write(f"**{op['action'].title()}**")

        with col2:
            timestamp = op['timestamp']
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    st.write(dt.strftime("%H:%M:%S"))
                except:
                    st.write(timestamp[:19])

        with col3:
            status = op.get('status', 'completed')
            if status == 'executing':
                st.info("🔄")
            elif status == 'completed':
                st.success("✅")
            else:
                st.error("❌")

        st.markdown("---")


def execute_bulk_operation(simulation_ids: List[str], action: str):
    """Execute a bulk operation across multiple simulations."""
    try:
        # Mock implementation
        bulk_id = f"bulk_{datetime.now().timestamp()}"

        operation = {
            'bulk_id': bulk_id,
            'action': action,
            'simulation_ids': simulation_ids,
            'timestamp': datetime.now().isoformat(),
            'status': 'executing',
            'completed': 0,
            'total': len(simulation_ids)
        }

        st.session_state.bulk_operation_status = operation

        st.success(f"✅ Bulk {action} initiated for {len(simulation_ids)} simulations")

        # Simulate progress updates
        for i, sim_id in enumerate(simulation_ids):
            # In real implementation, this would be async
            time.sleep(0.5)
            operation['completed'] = i + 1
            st.rerun()

        operation['status'] = 'completed'
        st.success(f"✅ Bulk {action} completed successfully!")

    except Exception as e:
        st.error(f"❌ Bulk operation failed: {str(e)}")


def render_bulk_status(simulation_ids: List[str]):
    """Render bulk operation status."""
    status = st.session_state.get('bulk_operation_status', {})

    if not status:
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total", status.get('total', 0))

    with col2:
        st.metric("Completed", status.get('completed', 0))

    with col3:
        st.metric("Remaining", status.get('total', 0) - status.get('completed', 0))

    with col4:
        progress = (status.get('completed', 0) / max(status.get('total', 1), 1)) * 100
        st.metric("Progress", ".1f")


def get_status_color(status: str) -> str:
    """Get color for status display."""
    colors = {
        'running': '🟢',
        'paused': '🟡',
        'completed': '✅',
        'failed': '❌',
        'cancelled': '🚫',
        'created': '🔵'
    }
    return colors.get(status.lower(), '⚪')


def render_simulation_status_grid(simulations: List[Dict[str, Any]]):
    """Render simulation status in a grid layout."""
    cols = st.columns(min(len(simulations), 3))

    for i, sim in enumerate(simulations):
        col_idx = i % len(cols)
        with cols[col_idx]:
            with st.container():
                status_icon = get_status_color(sim.get('status', 'unknown'))

                st.markdown(f"""
                **{status_icon} {sim.get('name', 'Unknown')}**

                ID: `{sim.get('id', 'Unknown')}`
                Status: **{sim.get('status', 'Unknown').title()}**
                Progress: **{sim.get('progress', 0):.1f}%**

                ---
                """)


def render_control_timeline():
    """Render timeline of control operations."""
    operations = st.session_state.get('control_operations', [])

    if not operations:
        st.info("No control operations to display.")
        return

    # Group operations by time
    timeline_data = {}
    for op in operations[-20:]:  # Show last 20 operations
        timestamp = op.get('timestamp', '')
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_key = dt.strftime("%H:%M")
                if time_key not in timeline_data:
                    timeline_data[time_key] = []
                timeline_data[time_key].append(op)
            except:
                continue

    # Display timeline
    for time_key in sorted(timeline_data.keys(), reverse=True):
        operations_at_time = timeline_data[time_key]

        with st.container():
            col1, col2 = st.columns([1, 4])

            with col1:
                st.write(f"**{time_key}**")

            with col2:
                for op in operations_at_time:
                    action = op.get('action', 'unknown').title()
                    sim_id = op.get('simulation_id', 'unknown')
                    st.write(f"• {action} simulation {sim_id}")

            st.markdown("---")


def render_system_resources_status():
    """Render system resource status."""
    # Mock system resource data
    resources = {
        'cpu_usage': 45.2,
        'memory_usage': 68.7,
        'disk_usage': 32.1,
        'network_io': 12.5
    }

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("CPU Usage", ".1f")

    with col2:
        st.metric("Memory Usage", ".1f")

    with col3:
        st.metric("Disk Usage", ".1f")

    with col4:
        st.metric("Network I/O", ".1f")


def get_queue_status() -> Dict[str, Any]:
    """Get simulation queue status."""
    # Mock queue status
    return {
        'queued': 3,
        'running': 2,
        'completed': 15,
        'failed': 1
    }


def control_queue_processing(action: str):
    """Control queue processing."""
    try:
        # Mock implementation
        st.success(f"✅ Queue processing {action}d successfully")
    except Exception as e:
        st.error(f"❌ Failed to {action} queue processing: {str(e)}")


def clear_failed_simulations():
    """Clear failed simulations from queue."""
    try:
        # Mock implementation
        st.success("✅ Failed simulations cleared from queue")
    except Exception as e:
        st.error(f"❌ Failed to clear failed simulations: {str(e)}")


def save_queue_configuration(config: Dict[str, Any]):
    """Save queue configuration."""
    try:
        # Mock implementation
        st.success("✅ Queue configuration saved successfully")
    except Exception as e:
        st.error(f"❌ Failed to save queue configuration: {str(e)}")


def render_queue_visualization():
    """Render queue visualization."""
    queue_status = get_queue_status()

    # Create a simple bar chart
    import plotly.express as px

    statuses = list(queue_status.keys())
    counts = list(queue_status.values())

    fig = px.bar(
        x=statuses,
        y=counts,
        title="Simulation Queue Status",
        labels={'x': 'Status', 'y': 'Count'}
    )

    st.plotly_chart(fig, use_container_width=True)
