"""
Ecosystem MCP Dashboard

A comprehensive Streamlit dashboard for monitoring and managing the Ecosystem MCP service.
Provides real-time insights into infrastructure health, document ingestion, RAG queries,
cache performance, and system metrics.
"""

import streamlit as st
from datetime import datetime
import sys
import os
from pathlib import Path

# Add pages directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import health checker
from utils.health_check import HealthChecker

# Page configuration
st.set_page_config(
    page_title="Ecosystem MCP Dashboard",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .status-healthy {
        color: #00c851;
        font-weight: bold;
    }
    .status-unhealthy {
        color: #ff4444;
        font-weight: bold;
    }
    .status-degraded {
        color: #ffbb33;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown('<div class="main-header">🧠 Ecosystem MCP Dashboard</div>', unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    [
        # Overview & Status
        "🏠 Home",
        "🏥 Health & Infrastructure",
        "🔬 Diagnostics",
        
        # Query Interfaces
        "🤖 RAG Query",
        "🎯 Enhanced Query",
        "🔬 Multi-Pass RAG Query",
        
        # Data Management
        "📚 Documents",
        
        # Infrastructure
        "🐳 Container Management",
        "🔍 Redis Explorer",
        "🗄️ PostgreSQL Explorer",
        
        # Monitoring & Analytics
        "⚡ Cache Performance",
        "📊 Metrics & Analytics",
        "📋 Logs Viewer",
        
        # Tools & Configuration
        "🔌 API Explorer",
        "⚙️ Configuration",
        "🔧 Settings"
    ]
)

# API Base URL configuration
st.sidebar.markdown("---")
st.sidebar.subheader("🔗 Configuration")
api_base_url = st.sidebar.text_input(
    "Ecosystem MCP API Base URL",
    value=os.getenv("API_BASE_URL", "http://localhost:8000"),
    help="Base URL for the Ecosystem MCP API"
)

# Health monitoring widget (with error handling)
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Connection Status")

try:
    # Import health monitor
    from utils.health_monitor import HealthMonitor
    
    # Create health monitor
    health_monitor = HealthMonitor(api_base_url, timeout=3.0)
    
    # Check all datasources
    health_results = health_monitor.check_all_datasources()
    overall_status = health_monitor.get_overall_status(health_results)
    
    # Display overall status
    status_colors = {
        "healthy": "🟢",
        "degraded": "🟡",
        "unhealthy": "🔴"
    }
    st.sidebar.markdown(f"**Overall:** {status_colors.get(overall_status, '⚪')} {overall_status.capitalize()}")
    
    # Display individual datasources (compact view)
    with st.sidebar.expander("📋 View Details", expanded=False):
        for name, status in health_results.items():
            color = health_monitor.get_status_color(status.status)
            latency_str = f"{status.latency_ms:.0f}ms" if status.latency_ms < 1000 else f"{status.latency_ms/1000:.1f}s"
            st.markdown(f"{color} **{name}** ({latency_str})")
            if status.error_message:
                st.caption(f"⚠️ {status.error_message}")
        
        # Refresh button
        if st.button("🔄 Refresh Status", use_container_width=True, key="refresh_health"):
            st.rerun()

except Exception as e:
    # If health monitoring fails, show a simple error message
    st.sidebar.error(f"⚠️ Health monitoring unavailable")
    if st.sidebar.checkbox("Show error details", key="show_health_error"):
        st.sidebar.code(str(e))

# Store in session state
if 'api_base_url' not in st.session_state:
    st.session_state.api_base_url = api_base_url
else:
    st.session_state.api_base_url = api_base_url

# Page routing
if page == "🏠 Home":
    from pages import home
    home.show(api_base_url)
elif page == "🏥 Health & Infrastructure":
    from pages import health
    health.show(api_base_url)
elif page == "🔬 Diagnostics":
    from pages import diagnostics
    diagnostics.show(api_base_url)
elif page == "⚙️ Configuration":
    from pages import config_viewer
    config_viewer.show(api_base_url)
elif page == "📋 Logs Viewer":
    from pages import logs_viewer
    logs_viewer.show(api_base_url)
elif page == "🔌 API Explorer":
    from pages import api_explorer
    api_explorer.show(api_base_url)
elif page == "🐳 Container Management":
    from pages import containers
    containers.show(api_base_url)
elif page == "🔍 Redis Explorer":
    from pages import redis_explorer
    redis_explorer.show(api_base_url)
elif page == "🗄️ PostgreSQL Explorer":
    from pages import postgres_explorer
    postgres_explorer.show(api_base_url)
elif page == "🤖 RAG Query":
    from pages import rag
    rag.show(api_base_url)
elif page == "🎯 Enhanced Query":
    from pages import query_enhanced
    query_enhanced.show(api_base_url)
elif page == "🔬 Multi-Pass RAG Query":
    from pages import rag_multi_pass
    rag_multi_pass.show(api_base_url)
elif page == "📚 Documents":
    from pages import documents
    documents.show(api_base_url)
elif page == "⚡ Cache Performance":
    from pages import cache
    cache.show(api_base_url)
elif page == "📊 Metrics & Analytics":
    from pages import metrics
    metrics.show(api_base_url)
elif page == "🔧 Settings":
    from pages import settings
    settings.show(api_base_url)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.sidebar.caption("Ecosystem MCP Dashboard v1.0.0")

