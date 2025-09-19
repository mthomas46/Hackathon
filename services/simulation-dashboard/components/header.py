"""Header Component.

This module provides the header component for the dashboard,
including title, status indicators, and global actions.
"""

import streamlit as st
from typing import Optional
from datetime import datetime

from infrastructure.config.config import get_config


def render_header():
    """Render the main header component."""
    config = get_config()

    # Create header container
    header_container = st.container()

    with header_container:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            # Main title
            st.title("🚀 Project Simulation Dashboard")
            st.caption(f"Interactive platform for managing project simulations • v{config.service_version}")

        with col2:
            # Service status
            render_service_status()

        with col3:
            # System time
            render_system_time()

        with col4:
            # Quick actions
            render_header_actions()

    # Separator
    st.markdown("---")


def render_service_status():
    """Render service connection status."""
    if 'simulation_client' in st.session_state:
        try:
            # This would be a real health check in production
            status = "🟢 Connected"
            st.metric("Simulation Service", status)
        except Exception:
            status = "🔴 Disconnected"
            st.metric("Simulation Service", status)
    else:
        st.metric("Simulation Service", "⚪ Initializing")


def render_system_time():
    """Render current system time."""
    current_time = datetime.now().strftime("%H:%M:%S")
    st.metric("System Time", current_time)


def render_header_actions():
    """Render header action buttons."""
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Refresh", key="header_refresh", use_container_width=True):
            # Clear caches and refresh data
            if 'simulation_client' in st.session_state:
                st.session_state.simulation_client.clear_cache()

            if 'simulations_cache' in st.session_state:
                st.session_state.simulations_cache = {}

            if 'health_cache' in st.session_state:
                st.session_state.health_cache = {}

            st.rerun()

    with col2:
        if st.button("🏥 Health", key="header_health", use_container_width=True):
            st.session_state.current_page = "config"
            st.rerun()


def render_breadcrumb(current_page: str, pages: dict):
    """Render breadcrumb navigation."""
    if current_page in pages:
        page_info = pages[current_page]
        st.markdown(f"**Navigation:** Home › {page_info['name'].replace('🏠 ', '').replace('➕ ', '').replace('📊 ', '').replace('📋 ', '').replace('⚙️ ', '')}")


def render_environment_banner():
    """Render environment banner for non-production environments."""
    config = get_config()

    if config.environment != "production":
        env_colors = {
            "development": "#28a745",  # Green
            "staging": "#ffc107",     # Yellow
            "testing": "#007bff",     # Blue
        }

        env_color = env_colors.get(config.environment, "#6c757d")

        st.markdown(
            f"""
            <div style="
                background-color: {env_color};
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
                margin-bottom: 16px;
            ">
                🔧 {config.environment.upper()} ENVIRONMENT - For testing and development only
            </div>
            """,
            unsafe_allow_html=True
        )
