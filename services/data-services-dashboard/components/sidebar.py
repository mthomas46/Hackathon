"""Sidebar Component - Navigation sidebar for the Data Services Dashboard.

This module provides the sidebar navigation component following the simulation-dashboard pattern.
"""

import streamlit as st
from typing import Dict, Any


def render_sidebar(pages: Dict[str, Dict[str, Any]]) -> str:
    """Render the sidebar navigation.

    Args:
        pages: Dictionary of available pages

    Returns:
        Selected page key
    """
    st.sidebar.title("📊 Data Services Dashboard")

    # Service Health Status
    st.sidebar.markdown("### 🔧 Service Status")
    render_service_health_status()

    st.sidebar.markdown("---")

    # Navigation
    st.sidebar.markdown("### 🧭 Navigation")

    # Get current page from session state
    current_page = st.session_state.get('current_page', 'overview')

    # Create navigation buttons
    selected_page = current_page

    for page_key, page_info in pages.items():
        if st.sidebar.button(
            page_info["name"],
            key=f"nav_{page_key}",
            help=page_info["description"],
            use_container_width=True
        ):
            selected_page = page_key
            st.session_state.current_page = page_key
            st.rerun()

    st.sidebar.markdown("---")

    # Quick Actions
    st.sidebar.markdown("### ⚡ Quick Actions")
    render_quick_actions()

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("*Data Services Dashboard v1.0*")

    return selected_page


def render_service_health_status():
    """Render service health status indicators."""
    services = {
        "Memory Agent": {"status": "unknown", "url": "http://localhost:5040/health"},
        "Prompt Store": {"status": "unknown", "url": "http://localhost:8080/health"},
        "Document Store": {"status": "unknown", "url": "http://localhost:8081/health"}
    }

    for service_name, service_info in services.items():
        # Simple status indicator (would be replaced with actual health checks)
        status_icon = "⚪"  # Default unknown
        if service_info["status"] == "healthy":
            status_icon = "🟢"
        elif service_info["status"] == "unhealthy":
            status_icon = "🔴"

        st.sidebar.markdown(f"{status_icon} {service_name}")


def render_quick_actions():
    """Render quick action buttons."""
    # Memory Agent Quick Actions
    if st.sidebar.button("🧠 Add Memory", key="quick_add_memory", use_container_width=True):
        st.session_state.current_page = "memory_browser"
        # Would open memory creation dialog
        st.rerun()

    # Prompt Store Quick Actions
    if st.sidebar.button("📝 New Prompt", key="quick_new_prompt", use_container_width=True):
        st.session_state.current_page = "prompt_browser"
        # Would open prompt creation dialog
        st.rerun()

    # Document Store Quick Actions
    if st.sidebar.button("📄 Upload Doc", key="quick_upload_doc", use_container_width=True):
        st.session_state.current_page = "document_browser"
        # Would open document upload dialog
        st.rerun()

    # Cross-Service Actions
    if st.sidebar.button("🔗 Link Items", key="quick_link_items", use_container_width=True):
        st.session_state.current_page = "cross_service"
        # Would open cross-service linking dialog
        st.rerun()
