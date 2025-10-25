"""
Ecosystem MCP Dashboard

A comprehensive Streamlit dashboard for monitoring and managing the Ecosystem MCP service.
Provides real-time insights into infrastructure health, document ingestion, RAG queries,
cache performance, and system metrics.
"""

import sys
import os

# Ensure /app is in the Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime
from pathlib import Path

# Add pages directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import health checker
from utils.health_check import HealthChecker

# Import state management
from utils.state_manager import StateManager
from utils.active_process_widget import (
    show_active_processes,
    show_generated_content_manager,
    show_state_persistence_indicator
)

# Initialize state manager
StateManager.initialize()

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

# Organized navigation with categories
st.sidebar.markdown("### 📊 OVERVIEW")
overview_pages = ["🏠 Home", "🏥 Health & Infrastructure", "🔬 Diagnostics"]

st.sidebar.markdown("### 🔍 QUERY & SEARCH")
query_pages = ["🤖 RAG Query", "🎯 Enhanced Query", "🔬 Multi-Pass RAG Query", "⏰ Temporal RAG", "🧠 Context-Aware RAG", "📚 Document Search"]

st.sidebar.markdown("### 📥 DATA MANAGEMENT")
data_pages = ["📚 Documents", "📥 Ingestion Manager", "⚡ Mode Comparison", "🔄 Job Recovery", "⚙️ Worker Monitor"]

st.sidebar.markdown("### 📖 DOCUMENTATION")
doc_pages = ["📖 Documentation Generator", "📚 Documentation Browser", "🔧 Doc Maintenance"]

st.sidebar.markdown("### 📊 ANALYSIS & REPORTS")
analysis_pages = ["📈 Timeline Analysis", "📈 Timeline Viewer", "📑 Report Generation"]

st.sidebar.markdown("### 🎯 DISCOVERY & ORCHESTRATION")
discovery_pages = ["🎯 Discovery & Orchestration"]

st.sidebar.markdown("### 🏗️ INFRASTRUCTURE")
infra_pages = ["🐳 Container Management", "🔍 Redis Explorer", "🗄️ PostgreSQL Explorer", "🔮 ChromaDB Explorer", "🎯 Embeddings Manager"]

st.sidebar.markdown("### 📈 MONITORING")
monitoring_pages = ["⚡ Cache Performance", "📊 Metrics & Analytics", "🎯 Quality Dashboard", "📋 Logs Viewer", "🔍 Performance Monitor", "📦 Repository Contexts"]

st.sidebar.markdown("### 🔧 CONFIGURATION")
config_pages = ["🔌 API Explorer", "⚙️ Configuration", "⚙️ RAG Config Manager", "🔌 LLM Tier Management", "🔧 Settings"]

# Combine all pages for radio selection
all_pages = overview_pages + query_pages + data_pages + doc_pages + analysis_pages + discovery_pages + infra_pages + monitoring_pages + config_pages

page = st.sidebar.radio(
    "Select Page",
    all_pages,
    label_visibility="collapsed"
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

# ============================================================================
# Active Process Management Widgets
# ============================================================================

# Show active processes widget
show_active_processes()

# Show generated content manager
show_generated_content_manager()

# Show state persistence indicator
show_state_persistence_indicator()

# Page routing
if page == "🏠 Home":
    from dashboard_views import home
    home.show(api_base_url)
elif page == "🏥 Health & Infrastructure":
    from dashboard_views import health
    health.show(api_base_url)
elif page == "🔬 Diagnostics":
    from dashboard_views import diagnostics
    diagnostics.show(api_base_url)
elif page == "⚙️ Configuration":
    from dashboard_views import config_viewer
    config_viewer.show(api_base_url)
elif page == "⚙️ RAG Config Manager":
    from dashboard_views import rag_config_manager
    rag_config_manager.show(api_base_url)
elif page == "📋 Logs Viewer":
    from dashboard_views import logs_viewer
    logs_viewer.show(api_base_url)
elif page == "🔌 API Explorer":
    from dashboard_views import api_explorer
    api_explorer.show(api_base_url)
elif page == "🐳 Container Management":
    from dashboard_views import containers
    containers.show(api_base_url)
elif page == "🔍 Redis Explorer":
    from dashboard_views import redis_explorer
    redis_explorer.show(api_base_url)
elif page == "🗄️ PostgreSQL Explorer":
    from dashboard_views import postgres_explorer
    postgres_explorer.show(api_base_url)
elif page == "🔮 ChromaDB Explorer":
    from dashboard_views import chromadb_explorer
    chromadb_explorer.show(api_base_url)
elif page == "🤖 RAG Query":
    from dashboard_views import rag
    rag.show(api_base_url)
elif page == "🎯 Enhanced Query":
    from dashboard_views import query_enhanced
    query_enhanced.show(api_base_url)
elif page == "🔬 Multi-Pass RAG Query":
    from dashboard_views import rag_multi_pass
    rag_multi_pass.show(api_base_url)
elif page == "⏰ Temporal RAG":
    from dashboard_views import temporal_rag_query
    temporal_rag_query.show(api_base_url)
elif page == "🧠 Context-Aware RAG":
    from pages import context_aware_rag
    context_aware_rag.show(api_base_url)
elif page == "📚 Document Search":
    from dashboard_views import documents
    documents.show(api_base_url)
elif page == "📚 Documents":
    from dashboard_views import documents
    documents.show(api_base_url)
elif page == "📥 Ingestion Manager":
    from dashboard_views import ingestion_manager
    ingestion_manager.show(api_base_url)
elif page == "⚡ Mode Comparison":
    from dashboard_views import mode_comparison
    mode_comparison.show(api_base_url)
elif page == "📖 Documentation Generator":
    from dashboard_views import doc_generator
    doc_generator.show(api_base_url)
elif page == "📚 Documentation Browser":
    from dashboard_views import documentation_browser
    documentation_browser.show()
elif page == "🔧 Doc Maintenance":
    from dashboard_views import doc_maintenance
    doc_maintenance.show(api_base_url)
elif page == "🎯 Embeddings Manager":
    from dashboard_views import embeddings_manager
    embeddings_manager.show(api_base_url)
elif page == "🔄 Job Recovery":
    from dashboard_views import job_recovery_manager
    job_recovery_manager.show()
elif page == "📈 Timeline Viewer":
    from dashboard_views import timeline_viewer
    timeline_viewer.show()
elif page == "⚙️ Worker Monitor":
    from dashboard_views import worker_monitor
    worker_monitor.show(api_base_url)
elif page == "⚡ Cache Performance":
    from dashboard_views import cache
    cache.show(api_base_url)
elif page == "📊 Metrics & Analytics":
    from dashboard_views import metrics
    metrics.show(api_base_url)
elif page == "🔌 LLM Tier Management":
    from dashboard_views import tier_management
    tier_management.show(api_base_url)
elif page == "🔧 Settings":
    from dashboard_views import settings
    settings.show(api_base_url)
elif page == "🎯 Quality Dashboard":
    from dashboard_views import quality_dashboard
    quality_dashboard.show(api_base_url)
elif page == "📊 Timeline Analysis":
    from dashboard_views import timeline_analysis
    timeline_analysis.show(api_base_url)
elif page == "🔍 Performance Monitor":
    from pages import performance_monitor
    performance_monitor.show(api_base_url)
elif page == "📦 Repository Contexts":
    from pages import repository_contexts
    repository_contexts.show(api_base_url)
elif page == "🎯 Discovery & Orchestration":
    from dashboard_views import discovery_orchestration
    discovery_orchestration.show(api_base_url)
elif page == "📑 Report Generation":
    from dashboard_views import reports_generator
    reports_generator.show(api_base_url)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.sidebar.caption("Ecosystem MCP Dashboard v1.0.0")

