"""Header Component - Dashboard header for the Data Services Dashboard.

This module provides the header component with branding and global controls.
"""

import streamlit as st
from datetime import datetime


def render_header():
    """Render the dashboard header."""
    # Create header with columns
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("# 📊 Data Services Dashboard")
        st.markdown("*Unified Interface for Memory Agent, Prompt Store & Document Store*")

    with col2:
        # Current time
        current_time = datetime.now().strftime("%H:%M:%S")
        st.metric("Current Time", current_time)

    with col3:
        # Global status
        st.metric("Services Online", "3/3", help="All data services are operational")

        # Theme selector
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark"],
            index=0,
            key="global_theme"
        )

    # Global search bar
    st.markdown("---")
    render_global_search()


def render_global_search():
    """Render the global search bar."""
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        search_query = st.text_input(
            "🔍 Global Search",
            placeholder="Search across all services...",
            key="global_search",
            help="Search for content across memory items, prompts, and documents"
        )

    with col2:
        search_scope = st.selectbox(
            "Search In",
            ["All Services", "Memory Only", "Prompts Only", "Documents Only"],
            key="search_scope"
        )

    with col3:
        if st.button("🔍 Search", key="execute_global_search"):
            if search_query.strip():
                # Store search parameters and navigate to search page
                st.session_state.global_search_query = search_query
                st.session_state.global_search_scope = search_scope
                st.session_state.current_page = "search"
                st.rerun()
            else:
                st.warning("Please enter a search query")
