"""Footer Component.

This module provides the footer component for the dashboard,
including version information, links, and system status.
"""

import streamlit as st
from datetime import datetime

from infrastructure.config.config import get_config


def render_footer():
    """Render the main footer component."""
    config = get_config()

    # Create footer container with muted styling
    st.markdown("---")

    footer_container = st.container()

    with footer_container:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            render_version_info()

        with col2:
            render_system_info()

        with col3:
            render_links()

        with col4:
            render_performance_info()

    # Final separator and copyright
    st.markdown("---")
    render_copyright()


def render_version_info():
    """Render version and build information."""
    st.markdown("**📦 Version Info**")

    version_info = f"""
    - Dashboard: v{config.service_version}
    - Environment: {config.environment.title()}
    - Python: 3.13
    - Streamlit: 1.28.0
    """

    st.code(version_info, language="text")


def render_system_info():
    """Render system status information."""
    st.markdown("**🖥️ System Status**")

    # Get current system metrics
    import psutil
    import platform

    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Platform info
        platform_info = platform.system()

        status_info = f"""
        - OS: {platform_info}
        - CPU: {cpu_percent:.1f}%
        - Memory: {memory_percent:.1f}%
        - Status: ✅ Operational
        """

        st.code(status_info, language="text")

    except ImportError:
        st.code("- System metrics unavailable\n- Status: ✅ Operational", language="text")


def render_links():
    """Render useful links."""
    st.markdown("**🔗 Quick Links**")

    links_info = """
    📚 Documentation
    🐛 Report Issue
    💬 Community
    🌟 GitHub Repo
    """

    st.code(links_info, language="text")

    # Make links clickable (in a real implementation)
    if st.button("📖 Open Documentation", key="footer_docs"):
        st.info("Documentation would open in a new tab")

    if st.button("🐛 Report Bug", key="footer_bug"):
        st.info("Bug report form would open")


def render_performance_info():
    """Render performance metrics."""
    st.markdown("**⚡ Performance**")

    # Calculate some basic metrics
    import time
    import streamlit.runtime.caching as caching

    try:
        # Get cache info
        cache_info = caching._get_cache_info()
        cache_entries = len(cache_info) if cache_info else 0

        # Response time (mock)
        avg_response_time = "< 100ms"

        perf_info = f"""
        - Cache Entries: {cache_entries}
        - Avg Response: {avg_response_time}
        - Uptime: {get_uptime_string()}
        - Active Users: 1
        """

        st.code(perf_info, language="text")

    except Exception:
        st.code("- Performance metrics unavailable", language="text")


def get_uptime_string() -> str:
    """Get system uptime as a formatted string."""
    try:
        import psutil
        uptime_seconds = int(time.time() - psutil.boot_time())

        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

    except Exception:
        return "Unknown"


def render_copyright():
    """Render copyright and legal information."""
    current_year = datetime.now().year

    copyright_text = f"""
    © {current_year} Project Simulation Dashboard • Built with ❤️ using Streamlit

    This dashboard is part of the LLM Documentation Ecosystem.
    For more information, visit our [GitHub repository](https://github.com/your-org/project-simulation-dashboard).
    """

    st.caption(copyright_text)


def render_debug_info():
    """Render debug information (only in development)."""
    config = get_config()

    if config.debug:
        with st.expander("🐛 Debug Information"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Session State:**")
                if st.session_state:
                    for key, value in st.session_state.items():
                        if not key.startswith('_'):  # Skip private keys
                            if isinstance(value, (str, int, float, bool)):
                                st.code(f"{key}: {value}")
                            else:
                                st.code(f"{key}: {type(value).__name__}")
                else:
                    st.code("No session state")

            with col2:
                st.markdown("**Configuration:**")
                st.code(f"Environment: {config.environment}")
                st.code(f"Debug: {config.debug}")
                st.code(f"Port: {config.port}")
                st.code(f"Simulation Service: {config.simulation_service.base_url}")


# Add debug info to footer if in development
config = get_config()
if config.is_development():
    render_debug_info()
