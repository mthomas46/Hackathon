"""Project Simulation Dashboard Service - Main Streamlit Application.

This is the main entry point for the Project Simulation Dashboard Service,
providing a comprehensive, interactive frontend for the project-simulation service
with real-time monitoring, analytics, and intuitive management interfaces.

Features:
- Interactive dashboard with real-time updates
- Simulation creation and management
- Live progress monitoring with WebSocket integration
- Comprehensive reporting and analytics
- Health monitoring and ecosystem status
- Multi-deployment support (terminal, Docker, ecosystem)
"""

import streamlit as st
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import logging

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import local modules
from infrastructure.config.config import get_config, DashboardSettings
from infrastructure.logging.logger import setup_logging, get_logger
from services.clients.simulation_client import SimulationClient
from services.clients.websocket_client import WebSocketClient
from components.sidebar import render_sidebar
from components.header import render_header
from components.footer import render_footer
from pages.overview import render_overview_page
from pages.create import render_create_page
from pages.monitor import render_monitor_page
from pages.reports import render_reports_page
from pages.config import render_config_page
from pages.analytics import render_analytics_page
from pages.events import render_events_page
from pages.controls import render_controls_page
from pages.audit import render_audit_page
from pages.ai_insights import render_ai_insights_page
from pages.autonomous import render_autonomous_page
from pages.advanced_analytics import render_advanced_analytics_page

# Configure page
st.set_page_config(
    page_title="Project Simulation Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-org/project-simulation-dashboard',
        'Report a bug': 'https://github.com/your-org/project-simulation-dashboard/issues',
        'About': '''
        ## Project Simulation Dashboard

        A comprehensive dashboard for managing and monitoring
        project simulations in the LLM Documentation Ecosystem.

        **Version:** 1.0.0
        **Environment:** Development
        '''
    }
)

# Load configuration
config: DashboardSettings = get_config()

# Setup logging
setup_logging(config.logging)
logger = get_logger(__name__)

# Initialize service clients
@st.cache_resource
def get_simulation_client() -> SimulationClient:
    """Get cached simulation client instance."""
    return SimulationClient(config.simulation_service)

@st.cache_resource
def get_websocket_client() -> WebSocketClient:
    """Get cached WebSocket client instance."""
    return WebSocketClient(config.websocket)

# Initialize session state
def initialize_session_state():
    """Initialize Streamlit session state."""
    if 'simulation_client' not in st.session_state:
        st.session_state.simulation_client = get_simulation_client()

    if 'websocket_client' not in st.session_state:
        st.session_state.websocket_client = get_websocket_client()

    if 'current_page' not in st.session_state:
        st.session_state.current_page = "overview"

    if 'selected_simulation' not in st.session_state:
        st.session_state.selected_simulation = None

    if 'theme' not in st.session_state:
        st.session_state.theme = config.dashboard.theme

    if 'simulations_cache' not in st.session_state:
        st.session_state.simulations_cache = {}

    if 'health_cache' not in st.session_state:
        st.session_state.health_cache = {}

# Page routing
PAGES = {
    "overview": {
        "name": "🏠 Overview",
        "function": render_overview_page,
        "description": "Main dashboard with simulation status and key metrics"
    },
    "create": {
        "name": "➕ Create",
        "function": render_create_page,
        "description": "Create new project simulations"
    },
    "controls": {
        "name": "🎮 Controls",
        "function": render_controls_page,
        "description": "Advanced simulation lifecycle controls"
    },
    "ai_insights": {
        "name": "🤖 AI Insights",
        "function": render_ai_insights_page,
        "description": "AI-powered pattern recognition and optimization"
    },
    "autonomous": {
        "name": "🚀 Autonomous",
        "function": render_autonomous_page,
        "description": "Self-managing autonomous operation system"
    },
    "advanced_analytics": {
        "name": "📊 Advanced Analytics",
        "function": render_advanced_analytics_page,
        "description": "Real-time analytics pipeline and predictive modeling"
    },
    "audit": {
        "name": "🔍 Audit",
        "function": render_audit_page,
        "description": "Comprehensive audit trail and compliance"
    },
    "monitor": {
        "name": "📊 Monitor",
        "function": render_monitor_page,
        "description": "Real-time monitoring and progress tracking"
    },
    "events": {
        "name": "📅 Events",
        "function": render_events_page,
        "description": "Event timeline and replay visualization"
    },
    "reports": {
        "name": "📋 Reports",
        "function": render_reports_page,
        "description": "Generate and view simulation reports"
    },
    "analytics": {
        "name": "📈 Analytics",
        "function": render_analytics_page,
        "description": "Advanced analytics and insights"
    },
    "config": {
        "name": "⚙️ Configure",
        "function": render_config_page,
        "description": "Configuration and settings"
    }
}

def render_page_content(page_key: str):
    """Render the content for the selected page."""
    try:
        page_info = PAGES.get(page_key)
        if page_info:
            page_info["function"]()
        else:
            st.error(f"Page '{page_key}' not found")
            render_overview_page()
    except Exception as e:
        logger.error(f"Error rendering page {page_key}: {str(e)}")
        st.error(f"Error loading page: {str(e)}")
        with st.expander("Error Details"):
            st.code(str(e))

def main():
    """Main application entry point."""
    try:
        # Initialize session state
        initialize_session_state()

        # Render header
        render_header()

        # Create two-column layout
        col1, col2 = st.columns([1, 4])

        with col1:
            # Render sidebar navigation
            selected_page = render_sidebar(PAGES)

        with col2:
            # Render main content area
            st.markdown("---")

            # Page title and description
            if selected_page in PAGES:
                page_info = PAGES[selected_page]
                st.title(page_info["name"])
                st.markdown(f"*{page_info['description']}*")
                st.markdown("---")

            # Render page content
            render_page_content(selected_page)

        # Render footer
        st.markdown("---")
        render_footer()

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please refresh the page.")
        with st.expander("Error Details"):
            st.code(str(e))

        # Show basic navigation as fallback
        st.sidebar.title("Navigation")
        if st.sidebar.button("🏠 Overview", key="fallback_overview"):
            st.rerun()

if __name__ == "__main__":
    # Log startup
    logger.info(
        "Starting Project Simulation Dashboard Service",
        version=config.service_version,
        environment=config.environment,
        port=config.port
    )

    # Print startup information
    print("🚀 Starting Project Simulation Dashboard Service...")
    print(f"📊 Service: {config.service_name} v{config.service_version}")
    print(f"🌐 Dashboard: http://localhost:{config.port}")
    print(f"🎯 Simulation Service: {config.simulation_service.base_url}")
    print(f"⚙️  Environment: {config.environment}")
    print(f"🔧 Debug Mode: {config.debug}")
    print("\n📋 Available Pages:")
    for key, page in PAGES.items():
        print(f"  • {page['name']}: {page['description']}")
    print("\n✨ Features:")
    print("  🎯 Interactive Dashboard with Real-Time Updates")
    print("  🚀 Simulation Creation and Management")
    print("  📊 Live Progress Monitoring")
    print("  📈 Comprehensive Analytics and Reporting")
    print("  🔧 Configuration Management")
    print("  🌐 Ecosystem Health Monitoring")
    print("\n🎨 Built with:")
    print("  🐍 Python & Streamlit")
    print("  🔄 Real-Time WebSocket Integration")
    print("  📊 Interactive Charts & Visualizations")
    print("  🏗️ Domain-Driven Design Architecture")

    # Run the application
    main()
