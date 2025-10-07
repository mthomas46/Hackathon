"""
MCP Ecosystem Dashboard

A comprehensive dashboard for managing and monitoring the MCP ecosystem.
"""

import streamlit as st
from streamlit_option_menu import option_menu
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="MCP Ecosystem Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
    }
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    h1 {
        color: #1e3a8a;
    }
    h2 {
        color: #2563eb;
    }
    .status-healthy {
        color: #10b981;
        font-weight: bold;
    }
    .status-unhealthy {
        color: #ef4444;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Import pages
from pages import (
    home,
    mcp_management,
    performance_monitor,
    marketplace,
    registry,
    query_playground,
    training_dashboard,
    system_health
)

def main():
    """Main application entry point."""
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://via.placeholder.com/150x50/2563eb/ffffff?text=MCP", use_column_width=True)
        st.title("🧠 MCP Ecosystem")
        
        selected = option_menu(
            menu_title=None,
            options=[
                "Home",
                "MCP Management",
                "Performance Monitor",
                "Marketplace",
                "Registry",
                "Query Playground",
                "Training Dashboard",
                "System Health"
            ],
            icons=[
                "house",
                "gear",
                "speedometer",
                "shop",
                "book",
                "search",
                "graph-up",
                "heart-pulse"
            ],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"color": "#2563eb", "font-size": "1.2rem"},
                "nav-link": {
                    "font-size": "1rem",
                    "text-align": "left",
                    "margin": "0.2rem",
                    "--hover-color": "#e0e7ff"
                },
                "nav-link-selected": {"background-color": "#2563eb"},
            }
        )
        
        # Service status indicators in sidebar
        st.markdown("---")
        st.subheader("📡 Services")
        
        # Placeholder for service status
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Online", "7", delta="✓")
        with col2:
            st.metric("Offline", "2", delta="⚠")
    
    # Route to selected page
    if selected == "Home":
        home.render()
    elif selected == "MCP Management":
        mcp_management.render()
    elif selected == "Performance Monitor":
        performance_monitor.render()
    elif selected == "Marketplace":
        marketplace.render()
    elif selected == "Registry":
        registry.render()
    elif selected == "Query Playground":
        query_playground.render()
    elif selected == "Training Dashboard":
        training_dashboard.render()
    elif selected == "System Health":
        system_health.render()

if __name__ == "__main__":
    main()
