"""
Data Services Dashboard - Streamlit UI

Hybrid Architecture:
- This file: Streamlit Web UI (port 8501) - For human operators
- api_app.py: FastAPI REST API (port 8080) - For ecosystem integration

Run Streamlit: streamlit run app.py --server.port 8501
Run FastAPI: uvicorn api_app:app --host 0.0.0.0 --port 8080

In Docker: Both are started by start.sh script
"""

import streamlit as st
from streamlit_autorefresh import st_autorefresh
from typing import Optional

# Configure page FIRST (must be first Streamlit command)
st.set_page_config(
    page_title="Datastore Operations Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import modules
from config import config, get_limit_from_time_range
from data import fetch_logs, parse_logs
from visualization import (
    render_overview_tab,
    render_performance_tab,
    render_operations_tab,
    render_workflows_tab,
    render_errors_tab
)
from utils.logging_client import dashboard_logger
from utils.formatting import format_uptime


# ============================================================================
# STREAMLIT UI
# ============================================================================

def render_sidebar() -> dict:
    """
    Render sidebar with filters and controls.
    
    Returns:
        Dictionary with filter values
    """
    st.sidebar.markdown("# 🎛️ Dashboard Controls")
    
    # Service filter
    st.sidebar.markdown("## 🔍 Filters")
    service = st.sidebar.selectbox(
        "Service",
        options=config.default_services,
        help="Filter by service name"
    )
    
    # Time range
    time_range = st.sidebar.selectbox(
        "Time Range",
        options=config.time_ranges,
        help="Select number of operations to display"
    )
    
    # Auto-refresh
    st.sidebar.markdown("## 🔄 Auto-Refresh")
    refresh_interval = st.sidebar.select_slider(
        "Interval (seconds)",
        options=[0, 5, 10, 30, 60],
        value=10,
        help="0 = disabled"
    )
    
    # Trigger auto-refresh
    if refresh_interval > 0:
        st_autorefresh(interval=refresh_interval * 1000, key="datarefresh")
    
    # Status indicators
    st.sidebar.markdown("## 📡 Status")
    
    # Log collector status
    from data.fetcher import check_log_collector_health
    log_collector_status = check_log_collector_health()
    
    if log_collector_status:
        st.sidebar.success("✅ Log Collector: Connected")
    else:
        st.sidebar.error("❌ Log Collector: Disconnected")
    
    # Dashboard info
    st.sidebar.markdown("## ℹ️ Dashboard Info")
    st.sidebar.markdown(f"**Version**: {config.service_version}")
    st.sidebar.markdown(f"**Environment**: {config.environment}")
    st.sidebar.markdown(f"**UI Port**: {config.ui_port}")
    st.sidebar.markdown(f"**API Port**: {config.api_port}")
    
    # API documentation link
    st.sidebar.markdown("## 📖 API")
    st.sidebar.markdown(f"[📚 API Docs](http://localhost:{config.api_port}/docs)")
    st.sidebar.markdown(f"[🔍 ReDoc](http://localhost:{config.api_port}/redoc)")
    
    return {
        "service": service,
        "time_range": time_range,
        "refresh_interval": refresh_interval
    }


def main():
    """
    Main dashboard application.
    
    Renders the header, sidebar, and tabs.
    """
    # Log dashboard startup
    dashboard_logger.dashboard_started(config.service_version, config.ui_port)
    
    # Render header
    st.title("📊 Datastore Operations Dashboard")
    st.markdown("""
    Real-time monitoring of datastore operations across the ecosystem.
    Track performance, errors, and workflows with interactive visualizations.
    """)
    
    # Render sidebar and get filters
    filters = render_sidebar()
    
    # Log filter application
    dashboard_logger.filter_applied(
        filters["service"] if filters["service"] != "All" else None,
        filters["time_range"]
    )
    
    # Fetch logs
    service_filter = filters["service"] if filters["service"] != "All" else None
    limit = get_limit_from_time_range(filters["time_range"])
    
    with st.spinner("🔄 Fetching logs..."):
        raw_logs = fetch_logs(service=service_filter, limit=limit)
    
    # Parse logs
    logs = parse_logs(raw_logs)
    
    # Display log count
    st.markdown(f"**Displaying {len(logs)} operations** (filtered: {service_filter or 'All'})")
    
    st.markdown("---")
    
    # Render tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "⏱️ Performance",
        "🔍 Operations",
        "🌊 Workflows",
        "❌ Errors"
    ])
    
    with tab1:
        dashboard_logger.tab_changed("overview")
        render_overview_tab(logs)
    
    with tab2:
        dashboard_logger.tab_changed("performance")
        render_performance_tab(logs)
    
    with tab3:
        dashboard_logger.tab_changed("operations")
        render_operations_tab(logs)
    
    with tab4:
        dashboard_logger.tab_changed("workflows")
        render_workflows_tab(logs)
    
    with tab5:
        dashboard_logger.tab_changed("errors")
        render_errors_tab(logs)
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🚀 Hybrid Architecture**")
        st.markdown(f"- Streamlit UI: `:{config.ui_port}`")
        st.markdown(f"- REST API: `:{config.api_port}`")
    
    with col2:
        st.markdown("**📈 Monitoring**")
        st.markdown(f"- Services: {len(config.default_services) - 1}")
        st.markdown(f"- Cache TTL: {config.cache_ttl}s")
    
    with col3:
        st.markdown("**🔗 Links**")
        st.markdown(f"[API Health](http://localhost:{config.api_port}/health)")
        st.markdown(f"[API Docs](http://localhost:{config.api_port}/docs)")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        dashboard_logger.dashboard_stopped()
        st.info("👋 Dashboard stopped")
    except Exception as e:
        dashboard_logger.unexpected_error(str(e))
        st.error(f"💥 Unexpected error: {e}")
        raise
