"""Monitor Page.

This module provides the real-time monitoring page with live progress tracking
and simulation event visualization using WebSocket integration.
"""

import streamlit as st
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

from services.clients.websocket_client import get_websocket_manager
from services.clients.simulation_client import SimulationClient
from infrastructure.config.config import get_config


def render_monitor_page():
    """Render the real-time monitoring page."""
    st.markdown("## 📊 Real-Time Monitoring")
    st.markdown("Monitor active simulations with live progress updates and event streams.")

    # Initialize WebSocket connection for real-time updates
    initialize_realtime_monitoring()

    # Create main layout with tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Live Progress",
        "🎯 Active Simulations",
        "📋 Event Stream",
        "📊 Performance Metrics"
    ])

    with tab1:
        render_live_progress()

    with tab2:
        render_active_simulations_monitor()

    with tab3:
        render_event_stream()

    with tab4:
        render_performance_metrics()

    # WebSocket connection status
    render_connection_status()


def initialize_realtime_monitoring():
    """Initialize WebSocket connections for real-time monitoring."""
    if 'websocket_manager' not in st.session_state:
        st.session_state.websocket_manager = get_websocket_manager()

    if 'realtime_events' not in st.session_state:
        st.session_state.realtime_events = []

    if 'simulation_progress' not in st.session_state:
        st.session_state.simulation_progress = {}

    # Initialize connection status
    if 'websocket_connected' not in st.session_state:
        st.session_state.websocket_connected = False

    if 'service_healthy' not in st.session_state:
        st.session_state.service_healthy = True

    # Start real-time updates if not already started
    if not getattr(st.session_state, 'realtime_started', False):
        try:
            # Start real-time updates asynchronously
            asyncio.run(start_realtime_updates_async())
            st.session_state.realtime_started = True
        except Exception as e:
            st.error(f"Failed to start real-time updates: {str(e)}")

    # Auto-refresh every 2 seconds for real-time updates
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()

    # Refresh data if it's been more than 2 seconds
    if time.time() - st.session_state.last_refresh > 2:
        refresh_realtime_data()
        st.session_state.last_refresh = time.time()


async def start_realtime_updates_async():
    """Start real-time updates asynchronously."""
    websocket_manager = st.session_state.websocket_manager
    success = await websocket_manager.start_realtime_updates()

    if success:
        st.session_state.websocket_connected = True
    else:
        st.session_state.websocket_connected = False


def refresh_realtime_data():
    """Refresh real-time data from simulation service."""
    try:
        # Get simulation client
        if 'simulation_client' in st.session_state:
            client = st.session_state.simulation_client

            # Get active simulations
            active_sims = asyncio.run(get_active_simulations_data(client))
            st.session_state.active_simulations = active_sims

            # Get recent events
            recent_events = asyncio.run(get_recent_events_data(client))
            st.session_state.realtime_events = recent_events[:20]  # Keep last 20 events

    except Exception as e:
        st.error(f"Failed to refresh real-time data: {str(e)}")


async def get_active_simulations_data(client: SimulationClient) -> List[Dict[str, Any]]:
    """Get active simulations data."""
    try:
        result = await client.list_simulations(status="running")
        if result.get("success", False):
            return result.get("simulations", [])
        return []
    except Exception as e:
        st.error(f"Failed to get active simulations: {str(e)}")
        return []


async def get_recent_events_data(client: SimulationClient) -> List[Dict[str, Any]]:
    """Get recent simulation events."""
    try:
        result = await client.get_simulation_events(limit=50)
        if result.get("success", False):
            return result.get("events", [])
        return []
    except Exception as e:
        st.error(f"Failed to get recent events: {str(e)}")
        return []


def render_live_progress():
    """Render live progress monitoring section."""
    st.markdown("### Live Simulation Progress")

    # Get active simulations
    active_sims = getattr(st.session_state, 'active_simulations', [])

    if not active_sims:
        st.info("No active simulations to monitor.")
        return

    # Display each active simulation with live progress
    for sim in active_sims:
        with st.container():
            render_simulation_progress_card(sim)
            st.markdown("---")


def render_simulation_progress_card(simulation: Dict[str, Any]):
    """Render a simulation progress card."""
    sim_id = simulation.get('id', 'unknown')
    sim_name = simulation.get('name', 'Unnamed Simulation')

    col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

    with col1:
        st.markdown(f"**{sim_name}**")
        st.caption(f"ID: {sim_id}")

        # Progress bar
        progress = simulation.get('progress', 0.0)
        st.progress(progress, text=".1%")

    with col2:
        # Status and phase
        status = simulation.get('status', 'unknown')
        phase = simulation.get('current_phase', 'Unknown')

        if status == 'running':
            st.success(f"🟢 {status.title()}")
        elif status == 'paused':
            st.warning(f"🟡 {status.title()}")
        elif status == 'completed':
            st.success(f"✅ {status.title()}")
        else:
            st.info(f"🔵 {status.title()}")

        st.caption(f"Phase: {phase}")

    with col3:
        # Time information
        start_time = simulation.get('start_time')
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                elapsed = datetime.now() - start_dt
                st.metric("Elapsed Time", f"{elapsed.seconds // 3600}h {(elapsed.seconds % 3600) // 60}m")
            except:
                st.caption("Time: Unknown")

        # Estimated completion
        estimated = simulation.get('estimated_completion')
        if estimated:
            st.caption(f"Est. completion: {estimated}")

    with col4:
        # Quick actions
        if st.button("👁️ View Details", key=f"view_{sim_id}", help=f"View detailed progress for {sim_id}"):
            st.session_state.selected_simulation = sim_id
            st.rerun()

        if st.button("⏹️ Stop", key=f"stop_{sim_id}", help=f"Stop simulation {sim_id}"):
            st.warning(f"Stop functionality for {sim_id} would be implemented here")


def render_active_simulations_monitor():
    """Render detailed active simulations monitoring."""
    st.markdown("### Active Simulations Monitor")

    active_sims = getattr(st.session_state, 'active_simulations', [])

    if not active_sims:
        st.info("No active simulations at the moment.")
        st.markdown("**💡 Tip:** Start a simulation from the Create page to see live monitoring in action!")
        return

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Simulations", len(active_sims))

    with col2:
        running_count = sum(1 for sim in active_sims if sim.get('status') == 'running')
        st.metric("Running", running_count)

    with col3:
        avg_progress = sum(sim.get('progress', 0) for sim in active_sims) / len(active_sims) if active_sims else 0
        st.metric("Avg Progress", ".1%")

    with col4:
        total_docs = sum(sim.get('documents_generated', 0) for sim in active_sims)
        st.metric("Documents Generated", total_docs)

    # Detailed simulation cards
    for sim in active_sims:
        with st.expander(f"📊 {sim.get('name', 'Unnamed')} - {sim.get('progress', 0):.1%}", expanded=False):
            render_detailed_simulation_monitor(sim)


def render_detailed_simulation_monitor(simulation: Dict[str, Any]):
    """Render detailed monitoring for a single simulation."""
    sim_id = simulation.get('id')

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Simulation Details**")
        st.write(f"**ID:** {sim_id}")
        st.write(f"**Type:** {simulation.get('type', 'Unknown')}")
        st.write(f"**Status:** {simulation.get('status', 'Unknown')}")
        st.write(f"**Current Phase:** {simulation.get('current_phase', 'Unknown')}")

        # Team information
        team_size = simulation.get('team_size', 0)
        if team_size > 0:
            st.write(f"**Team Size:** {team_size}")

    with col2:
        st.markdown("**Progress Metrics**")
        progress = simulation.get('progress', 0)

        # Progress visualization
        st.progress(progress, text=".1%")

        # Detailed metrics
        docs_generated = simulation.get('documents_generated', 0)
        workflows_executed = simulation.get('workflows_executed', 0)
        quality_score = simulation.get('quality_score', 0)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Documents", docs_generated)
        with col_b:
            st.metric("Workflows", workflows_executed)
        with col_c:
            st.metric("Quality", ".2f")

    # Timeline visualization (placeholder for now)
    st.markdown("**Timeline**")
    st.info("Interactive timeline visualization would be implemented here with phase progression and milestones.")


def render_event_stream():
    """Render real-time event stream."""
    st.markdown("### Real-Time Event Stream")

    # Event filter controls
    col1, col2, col3 = st.columns(3)

    with col1:
        event_types = st.multiselect(
            "Event Types",
            ["SimulationStarted", "SimulationCompleted", "DocumentGenerated", "WorkflowExecuted", "PhaseStarted", "MilestoneAchieved"],
            default=["SimulationStarted", "SimulationCompleted", "DocumentGenerated"],
            key="event_filter_types"
        )

    with col2:
        max_events = st.slider("Max Events", 10, 100, 20, key="max_events_display")

    with col3:
        if st.button("🔄 Refresh Events", key="refresh_events"):
            refresh_realtime_data()

    # Display events
    events = getattr(st.session_state, 'realtime_events', [])

    if not events:
        st.info("No events to display. Events will appear here as simulations run.")
        return

    # Filter events
    filtered_events = events
    if event_types:
        filtered_events = [e for e in events if e.get('event_type') in event_types]

    # Display recent events
    st.markdown(f"**Showing {min(len(filtered_events), max_events)} most recent events**")

    for event in filtered_events[:max_events]:
        render_event_item(event)


def render_event_item(event: Dict[str, Any]):
    """Render a single event item."""
    event_type = event.get('event_type', 'Unknown')
    timestamp = event.get('timestamp', '')

    # Event type icons
    event_icons = {
        "SimulationStarted": "▶️",
        "SimulationCompleted": "✅",
        "SimulationFailed": "❌",
        "DocumentGenerated": "📄",
        "WorkflowExecuted": "⚙️",
        "PhaseStarted": "🚀",
        "PhaseCompleted": "🏁",
        "MilestoneAchieved": "🎯",
        "TeamMemberAdded": "👥",
        "ProjectStatusChanged": "📊"
    }

    icon = event_icons.get(event_type, "📝")

    with st.container():
        col1, col2, col3 = st.columns([1, 4, 2])

        with col1:
            st.markdown(f"### {icon}")

        with col2:
            st.markdown(f"**{event_type}**")

            # Event-specific details
            if event_type == "SimulationStarted":
                st.caption(f"Started simulation: {event.get('simulation_id', 'Unknown')}")
            elif event_type == "DocumentGenerated":
                st.caption(f"Generated: {event.get('title', 'Document')}")
            elif event_type == "WorkflowExecuted":
                execution_time = event.get('execution_time_seconds', 0)
                st.caption(".2f")
            else:
                simulation_id = event.get('simulation_id', event.get('project_id', 'Unknown'))
                st.caption(f"Simulation: {simulation_id}")

        with col3:
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_ago = datetime.now() - dt

                    if time_ago.days > 0:
                        time_str = f"{time_ago.days}d ago"
                    elif time_ago.seconds > 3600:
                        time_str = f"{time_ago.seconds // 3600}h ago"
                    elif time_ago.seconds > 60:
                        time_str = f"{time_ago.seconds // 60}m ago"
                    else:
                        time_str = f"{time_ago.seconds}s ago"

                    st.caption(time_str)
                except:
                    st.caption("Time: Unknown")

        st.markdown("---")


def render_performance_metrics():
    """Render performance metrics section."""
    st.markdown("### Performance Metrics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**System Performance**")

        # Mock performance data - in real implementation this would come from monitoring
        cpu_usage = 45.2
        memory_usage = 67.8
        disk_usage = 23.1

        st.metric("CPU Usage", ".1f")
        st.metric("Memory Usage", ".1f")
        st.metric("Disk Usage", ".1f")

    with col2:
        st.markdown("**Simulation Performance**")

        # Simulation-specific metrics
        avg_execution_time = 2.3  # seconds
        success_rate = 94.5  # percentage
        throughput = 12.8  # documents per minute

        st.metric("Avg Execution Time", ".1f")
        st.metric("Success Rate", ".1f")
        st.metric("Throughput", ".1f")

    # Performance charts (placeholder)
    st.markdown("**Performance Trends**")
    st.info("Interactive performance charts and trend analysis would be implemented here.")

    # Sample chart placeholder
    st.line_chart({
        "CPU Usage": [40, 45, 42, 48, 43, 46, 44, 47, 45, 46],
        "Memory Usage": [60, 65, 63, 67, 64, 66, 65, 68, 66, 67],
        "Response Time": [120, 115, 118, 110, 125, 112, 117, 108, 122, 115]
    })


def render_connection_status():
    """Render WebSocket connection status."""
    st.markdown("---")
    st.markdown("### 🔗 Connection Status")

    col1, col2, col3 = st.columns(3)

    with col1:
        # WebSocket status
        ws_connected = getattr(st.session_state, 'websocket_connected', False)
        if ws_connected:
            st.success("✅ WebSocket Connected")
        else:
            st.error("❌ WebSocket Disconnected")

    with col2:
        # Simulation service status
        service_healthy = getattr(st.session_state, 'service_healthy', True)
        if service_healthy:
            st.success("✅ Simulation Service")
        else:
            st.error("❌ Simulation Service")

    with col3:
        # Last update time
        last_update = getattr(st.session_state, 'last_refresh', time.time())
        time_since = time.time() - last_update
        st.info(".1f")


# WebSocket event handlers
def handle_simulation_progress(event_data: Dict[str, Any]):
    """Handle simulation progress updates."""
    simulation_id = event_data.get('simulation_id')
    if simulation_id:
        st.session_state.simulation_progress[simulation_id] = event_data
        # Trigger Streamlit rerun to update UI
        st.rerun()


def handle_simulation_event(event_data: Dict[str, Any]):
    """Handle simulation domain events."""
    # Add to events list
    events = getattr(st.session_state, 'realtime_events', [])
    events.insert(0, event_data)  # Add to beginning

    # Keep only last 100 events
    st.session_state.realtime_events = events[:100]

    # Trigger UI update
    st.rerun()


def handle_websocket_connected(connected: bool, context: Optional[str] = None):
    """Handle WebSocket connection status changes."""
    st.session_state.websocket_connected = connected
    st.rerun()


def handle_service_health_changed(healthy: bool):
    """Handle simulation service health changes."""
    st.session_state.service_healthy = healthy
    st.rerun()
