"""Sidebar Navigation Component.

This module provides the sidebar navigation component for the dashboard,
including page selection, theme switching, and quick actions.
"""

import streamlit as st
from typing import Dict, Any, Optional

from infrastructure.config.config import get_config


def render_sidebar(pages: Dict[str, Dict[str, Any]]) -> str:
    """Render the sidebar navigation component."""
    config = get_config()

    # Sidebar header
    st.sidebar.title("🎯 Simulation Dashboard")
    st.sidebar.markdown(f"**v{config.service_version}**")
    st.sidebar.markdown("---")

    # Environment indicator
    if config.environment != "production":
        env_color = {
            "development": "🟢",
            "staging": "🟡",
            "testing": "🔵"
        }.get(config.environment, "⚪")

        st.sidebar.markdown(f"{env_color} **{config.environment.title()}**")

    # Quick status
    render_quick_status()

    st.sidebar.markdown("---")

    # Page navigation
    selected_page = render_page_navigation(pages)

    st.sidebar.markdown("---")

    # Quick actions
    render_quick_actions()

    st.sidebar.markdown("---")

    # Theme selector
    render_theme_selector()

    # Footer
    render_sidebar_footer()

    return selected_page


def render_quick_status():
    """Render quick status indicators."""
    col1, col2 = st.sidebar.columns(2)

    with col1:
        # Simulation service status
        if 'simulation_client' in st.session_state:
            try:
                # This would be a quick health check
                st.sidebar.metric("Service", "✅ Connected")
            except Exception:
                st.sidebar.metric("Service", "❌ Disconnected")

    with col2:
        # Active simulations count
        active_count = getattr(st.session_state, 'active_simulations_count', 0)
        st.sidebar.metric("Active", active_count)


def render_page_navigation(pages: Dict[str, Dict[str, Any]]) -> str:
    """Render page navigation menu."""
    st.sidebar.subheader("📋 Navigation")

    # Get current page from session state
    current_page = getattr(st.session_state, 'current_page', 'overview')

    # Create radio button navigation
    page_options = []
    page_labels = []

    for page_key, page_info in pages.items():
        page_options.append(page_key)
        page_labels.append(page_info["name"])

    # Find current index
    try:
        current_index = page_options.index(current_page)
    except ValueError:
        current_index = 0

    # Render navigation
    selected_page = st.sidebar.radio(
        "Select Page:",
        options=page_options,
        format_func=lambda x: pages[x]["name"],
        index=current_index,
        key="page_navigation",
        label_visibility="collapsed"
    )

    # Update session state
    st.session_state.current_page = selected_page

    return selected_page


def render_quick_actions():
    """Render quick action buttons."""
    st.sidebar.subheader("⚡ Quick Actions")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.sidebar.button("➕ New Simulation", key="quick_new_sim", use_container_width=True):
            st.session_state.current_page = "create"
            st.rerun()

    with col2:
        if st.sidebar.button("📊 Monitor", key="quick_monitor", use_container_width=True):
            st.session_state.current_page = "monitor"
            st.rerun()

    # Recent simulations dropdown
    if 'simulations_cache' in st.session_state and st.session_state.simulations_cache:
        st.sidebar.subheader("🕒 Recent Simulations")

        # Get recent simulations (last 5)
        simulations_data = st.session_state.simulations_cache
        if 'simulations' in simulations_data:
            recent_sims = simulations_data['simulations'][:5]

            sim_options = ["Select simulation..."]
            sim_options.extend([f"{sim.get('id', 'Unknown')} - {sim.get('name', 'Unnamed')}" for sim in recent_sims])

            selected_sim = st.sidebar.selectbox(
                "Quick Access:",
                options=sim_options,
                key="quick_sim_select",
                label_visibility="collapsed"
            )

            if selected_sim and selected_sim != "Select simulation...":
                # Extract simulation ID
                sim_id = selected_sim.split(" - ")[0]
                st.session_state.selected_simulation = sim_id
                st.session_state.current_page = "monitor"
                st.rerun()


def render_theme_selector():
    """Render theme selector."""
    st.sidebar.subheader("🎨 Theme")

    theme_options = {
        "light": "☀️ Light",
        "dark": "🌙 Dark",
        "auto": "🔄 Auto"
    }

    current_theme = getattr(st.session_state, 'theme', 'light')

    selected_theme = st.sidebar.selectbox(
        "Choose Theme:",
        options=list(theme_options.keys()),
        format_func=lambda x: theme_options[x],
        index=list(theme_options.keys()).index(current_theme),
        key="theme_selector",
        label_visibility="collapsed"
    )

    # Update theme in session state
    st.session_state.theme = selected_theme

    # Apply theme (this would require custom CSS in a full implementation)
    if selected_theme != current_theme:
        st.rerun()


def render_sidebar_footer():
    """Render sidebar footer with useful links."""
    st.sidebar.markdown("---")

    with st.sidebar.expander("ℹ️ Info & Links"):
        st.markdown("""
        **Project Simulation Dashboard**

        A comprehensive interface for managing and monitoring
        software development project simulations.

        **Links:**
        - 📚 [Documentation](https://github.com/your-org/simulation-dashboard)
        - 🐛 [Report Issue](https://github.com/your-org/simulation-dashboard/issues)
        - 💬 [Support](https://github.com/your-org/simulation-dashboard/discussions)

        **Connected to:**
        - Simulation Service: `http://localhost:5075`
        - Environment: Development
        """)

    # Version info
    config = get_config()
    st.sidebar.caption(f"v{config.service_version} - {config.environment}")
