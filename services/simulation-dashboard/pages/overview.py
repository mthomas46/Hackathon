"""Overview Dashboard Page.

This module provides the main overview dashboard page with key metrics,
recent activity, simulation status overview, and quick actions.
"""

import streamlit as st
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import time

from infrastructure.logging.logger import get_dashboard_logger


logger = get_dashboard_logger("overview_page")


def render_overview_page():
    """Render the main overview dashboard page."""
    # Page header
    st.markdown("## 📊 Dashboard Overview")
    st.markdown("Welcome to the Project Simulation Dashboard. Monitor your simulations, view key metrics, and access quick actions.")

    # Create tabs for different overview sections
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Key Metrics", "🎯 Active Simulations", "📋 Recent Activity", "⚡ Quick Actions"])

    with tab1:
        render_key_metrics()

    with tab2:
        render_active_simulations()

    with tab3:
        render_recent_activity()

    with tab4:
        render_quick_actions()

    # System status section
    st.markdown("---")
    render_system_status()


def render_key_metrics():
    """Render key performance metrics."""
    st.markdown("### Key Performance Indicators")

    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)

    # Mock data - in real implementation this would come from the simulation service
    with col1:
        total_simulations = get_total_simulations_count()
        st.metric(
            label="Total Simulations",
            value=total_simulations,
            delta="+2 from yesterday",
            help="Total number of simulations created"
        )

    with col2:
        active_simulations = get_active_simulations_count()
        st.metric(
            label="Active Simulations",
            value=active_simulations,
            delta=f"{active_simulations} running",
            help="Currently running simulations"
        )

    with col3:
        success_rate = get_success_rate()
        st.metric(
            label="Success Rate",
            value=f"{success_rate}%",
            delta="+5% from last week",
            help="Percentage of successful simulations"
        )

    with col4:
        avg_duration = get_average_duration()
        st.metric(
            label="Avg Duration",
            value=f"{avg_duration}min",
            delta="-2min from last week",
            help="Average simulation duration"
        )

    # Additional metrics
    st.markdown("---")
    render_additional_metrics()


def render_additional_metrics():
    """Render additional performance metrics."""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📊 Simulation Types**")
        # Mock data
        simulation_types = {
            "Web Application": 45,
            "Mobile App": 23,
            "API Service": 18,
            "Data Pipeline": 14
        }

        for sim_type, count in simulation_types.items():
            st.progress(count / 100, text=f"{sim_type}: {count}")

    with col2:
        st.markdown("**⏱️ Performance Trends**")
        # Mock performance data
        performance_data = [85, 87, 82, 89, 91, 88, 93]
        for i, value in enumerate(performance_data[-7:]):
            days_ago = 6 - i
            st.progress(value / 100, text=f"{days_ago} days ago: {value}%")

    with col3:
        st.markdown("**🏆 Top Performers**")
        # Mock top performers
        top_performers = [
            ("E-commerce Platform", "98%"),
            ("User Management API", "95%"),
            ("Analytics Dashboard", "93%")
        ]

        for name, score in top_performers:
            st.markdown(f"• **{name}**: {score}")


def render_active_simulations():
    """Render active simulations overview."""
    st.markdown("### Active Simulations")

    # Get active simulations
    active_sims = get_active_simulations()

    if not active_sims:
        st.info("No active simulations at the moment.")
        return

    # Display active simulations
    for sim in active_sims:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])

            with col1:
                st.markdown(f"**{sim['name']}**")
                st.caption(f"ID: {sim['id']}")

            with col2:
                st.markdown(f"**Status:** {sim['status']}")
                if sim['status'] == 'running':
                    st.success("🟢 Running")
                elif sim['status'] == 'paused':
                    st.warning("🟡 Paused")
                else:
                    st.info(f"🔵 {sim['status']}")

            with col3:
                progress = sim.get('progress', 0)
                st.progress(progress / 100, text=f"{progress}% Complete")

            with col4:
                st.markdown(f"**Started:** {sim['start_time']}")
                if 'estimated_completion' in sim:
                    st.caption(f"Est. completion: {sim['estimated_completion']}")

            with col5:
                if st.button("👁️ View", key=f"view_{sim['id']}", help=f"Monitor simulation {sim['id']}"):
                    st.session_state.selected_simulation = sim['id']
                    st.session_state.current_page = "monitor"
                    st.rerun()

            st.markdown("---")


def render_recent_activity():
    """Render recent activity feed."""
    st.markdown("### Recent Activity")

    # Get recent activity
    activities = get_recent_activities()

    if not activities:
        st.info("No recent activity to display.")
        return

    # Display activities
    for activity in activities:
        with st.container():
            col1, col2 = st.columns([1, 4])

            with col1:
                # Activity icon based on type
                icon_map = {
                    "simulation_created": "➕",
                    "simulation_started": "▶️",
                    "simulation_completed": "✅",
                    "simulation_failed": "❌",
                    "report_generated": "📊"
                }
                icon = icon_map.get(activity['type'], "📝")
                st.markdown(f"### {icon}")

            with col2:
                st.markdown(f"**{activity['title']}**")
                st.caption(f"{activity['description']}")
                st.caption(f"{activity['timestamp']} • {activity['user']}")

            st.markdown("---")


def render_quick_actions():
    """Render quick action buttons."""
    st.markdown("### Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("**🚀 Start New**")
        if st.button("Create Simulation", key="quick_create", use_container_width=True):
            st.session_state.current_page = "create"
            st.rerun()

        if st.button("From Config File", key="quick_config", use_container_width=True):
            st.session_state.current_page = "create"
            st.rerun()

    with col2:
        st.markdown("**📊 Monitor**")
        if st.button("Active Simulations", key="quick_monitor", use_container_width=True):
            st.session_state.current_page = "monitor"
            st.rerun()

        if st.button("System Health", key="quick_health", use_container_width=True):
            st.session_state.current_page = "config"
            st.rerun()

    with col3:
        st.markdown("**📋 Reports**")
        if st.button("Generate Report", key="quick_report", use_container_width=True):
            st.session_state.current_page = "reports"
            st.rerun()

        if st.button("View Analytics", key="quick_analytics", use_container_width=True):
            st.session_state.current_page = "analytics"
            st.rerun()

    with col4:
        st.markdown("**⚙️ Manage**")
        if st.button("Configuration", key="quick_config_manage", use_container_width=True):
            st.session_state.current_page = "config"
            st.rerun()

        if st.button("Settings", key="quick_settings", use_container_width=True):
            st.info("Settings panel would open here")


def render_system_status():
    """Render system status overview."""
    st.markdown("## 🏥 System Status")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Simulation Service Status
        st.markdown("**🎯 Simulation Service**")
        service_status = check_simulation_service_status()
        if service_status['healthy']:
            st.success("✅ Healthy")
        else:
            st.error("❌ Unhealthy")
        st.caption(f"Response: {service_status['response_time']}ms")

    with col2:
        # Database Status
        st.markdown("**🗄️ Database**")
        db_status = check_database_status()
        if db_status['healthy']:
            st.success("✅ Connected")
        else:
            st.error("❌ Disconnected")
        st.caption(f"Connections: {db_status['active_connections']}")

    with col3:
        # WebSocket Status
        st.markdown("**🔄 Real-time Updates**")
        ws_status = check_websocket_status()
        if ws_status['connected']:
            st.success("✅ Connected")
        else:
            st.warning("⚠️ Disconnected")
        st.caption(f"Active: {ws_status['active_connections']}")

    with col4:
        # System Resources
        st.markdown("**💻 System Resources**")
        resources = get_system_resources()
        cpu_usage = resources['cpu_percent']
        memory_usage = resources['memory_percent']

        if cpu_usage < 70 and memory_usage < 80:
            st.success("✅ Normal")
        elif cpu_usage < 90 and memory_usage < 90:
            st.warning("⚠️ High")
        else:
            st.error("❌ Critical")

        st.caption(f"CPU: {cpu_usage}% | RAM: {memory_usage}%")


# Mock data functions - in real implementation these would call the actual services

def get_total_simulations_count() -> int:
    """Get total simulations count."""
    # Mock data
    return 127

def get_active_simulations_count() -> int:
    """Get active simulations count."""
    # Mock data
    return 3

def get_success_rate() -> int:
    """Get success rate percentage."""
    # Mock data
    return 89

def get_average_duration() -> int:
    """Get average duration in minutes."""
    # Mock data
    return 45

def get_active_simulations() -> List[Dict[str, Any]]:
    """Get list of active simulations."""
    # Mock data
    return [
        {
            "id": "sim_001",
            "name": "E-commerce Platform",
            "status": "running",
            "progress": 67,
            "start_time": "2024-01-15 14:30:00",
            "estimated_completion": "2024-01-15 16:15:00"
        },
        {
            "id": "sim_002",
            "name": "User Management API",
            "status": "running",
            "progress": 34,
            "start_time": "2024-01-15 15:45:00",
            "estimated_completion": "2024-01-15 17:30:00"
        },
        {
            "id": "sim_003",
            "name": "Analytics Dashboard",
            "status": "paused",
            "progress": 12,
            "start_time": "2024-01-15 16:00:00"
        }
    ]

def get_recent_activities() -> List[Dict[str, Any]]:
    """Get recent activities."""
    # Mock data
    return [
        {
            "type": "simulation_completed",
            "title": "Simulation Completed",
            "description": "Mobile App Development simulation finished successfully",
            "timestamp": "2024-01-15 14:15:00",
            "user": "System"
        },
        {
            "type": "report_generated",
            "title": "Report Generated",
            "description": "Executive summary report for Project Alpha",
            "timestamp": "2024-01-15 13:45:00",
            "user": "john.doe@example.com"
        },
        {
            "type": "simulation_started",
            "title": "Simulation Started",
            "description": "E-commerce Platform simulation initiated",
            "timestamp": "2024-01-15 13:30:00",
            "user": "jane.smith@example.com"
        },
        {
            "type": "simulation_created",
            "title": "Simulation Created",
            "description": "New simulation: API Service Development",
            "timestamp": "2024-01-15 12:00:00",
            "user": "System"
        }
    ]

def check_simulation_service_status() -> Dict[str, Any]:
    """Check simulation service health."""
    # Mock health check
    return {
        "healthy": True,
        "response_time": 45
    }

def check_database_status() -> Dict[str, Any]:
    """Check database health."""
    # Mock database check
    return {
        "healthy": True,
        "active_connections": 5
    }

def check_websocket_status() -> Dict[str, Any]:
    """Check WebSocket connection status."""
    # Mock WebSocket check
    return {
        "connected": True,
        "active_connections": 2
    }

def get_system_resources() -> Dict[str, Any]:
    """Get system resource usage."""
    # Mock resource data
    return {
        "cpu_percent": 23.5,
        "memory_percent": 45.2
    }
