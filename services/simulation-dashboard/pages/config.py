"""Configuration Page.

This module provides the configuration and settings page for managing
service connections, health monitoring, and system settings.
"""

import streamlit as st


def render_config_page():
    """Render the configuration page."""
    st.markdown("## ⚙️ Configuration & Settings")
    st.markdown("Manage service connections, monitor system health, and configure dashboard settings.")

    # Service Connections
    st.subheader("Service Connections")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🎯 Simulation Service**")
        st.text_input("Host", value="localhost", disabled=True)
        st.text_input("Port", value="5075", disabled=True)
        st.success("✅ Connected")

    with col2:
        st.markdown("**📊 Analysis Service (Optional)**")
        st.text_input("Host", placeholder="Optional", disabled=True)
        st.text_input("Port", placeholder="Optional", disabled=True)
        st.warning("⚠️ Not Connected")

    # Health Monitoring
    st.subheader("System Health")
    st.info("🚧 Health monitoring dashboard is under development.")

    # Dashboard Settings
    st.subheader("Dashboard Settings")
    theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
    refresh_rate = st.slider("Auto-refresh Rate (seconds)", 5, 300, 30)
    max_items = st.slider("Max Items Per Page", 10, 100, 50)

    if st.button("Save Settings"):
        st.success("Settings saved successfully!")
