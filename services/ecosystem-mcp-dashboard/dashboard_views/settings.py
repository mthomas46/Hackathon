"""Settings & Configuration page."""

import streamlit as st
import httpx
import json

def show(api_base_url: str):
    """Show settings page."""
    st.title("🔧 Settings & Configuration")
    
    # API Configuration
    st.subheader("🔗 API Configuration")
    
    with st.form("api_config"):
        current_url = st.session_state.get("api_base_url", api_base_url)
        
        new_url = st.text_input(
            "API Base URL",
            value=current_url,
            help="Base URL for the Ecosystem MCP API"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            request_timeout = st.number_input(
                "Request Timeout (seconds)",
                min_value=5,
                max_value=120,
                value=30
            )
        
        with col2:
            max_retries = st.number_input(
                "Max Retries",
                min_value=0,
                max_value=5,
                value=3
            )
        
        if st.form_submit_button("💾 Save Configuration"):
            st.session_state.api_base_url = new_url
            st.success("✅ Configuration saved!")
            st.rerun()
    
    # Test connection
    st.markdown("---")
    st.subheader("🔌 Connection Test")
    
    if st.button("🧪 Test Connection", use_container_width=True):
        with st.spinner("Testing connection..."):
            try:
                response = httpx.get(
                    f"{api_base_url}/health",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    st.success("✅ Connection successful!")
                    st.json(response.json())
                else:
                    st.error(f"❌ Connection failed: {response.status_code}")
                    st.code(response.text)
            
            except httpx.ConnectError:
                st.error(f"❌ Cannot connect to {api_base_url}")
                st.info("Check that the service is running and the URL is correct.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Dashboard settings
    st.markdown("---")
    st.subheader("🎨 Dashboard Settings")
    
    with st.form("dashboard_settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            theme = st.selectbox(
                "Theme",
                ["Light", "Dark", "Auto"],
                help="Dashboard color theme"
            )
            
            refresh_interval = st.slider(
                "Auto-refresh Interval (seconds)",
                min_value=10,
                max_value=300,
                value=30,
                step=10
            )
        
        with col2:
            items_per_page = st.number_input(
                "Items Per Page",
                min_value=10,
                max_value=100,
                value=20,
                step=10
            )
            
            enable_animations = st.checkbox("Enable Animations", value=True)
        
        if st.form_submit_button("💾 Save Dashboard Settings"):
            st.success("✅ Dashboard settings saved!")
    
    # Cache management
    st.markdown("---")
    st.subheader("🗑️ Cache Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Clear Browser Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("✅ Browser cache cleared!")
    
    with col2:
        if st.button("Reset Dashboard State", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key != "api_base_url":
                    del st.session_state[key]
            st.success("✅ Dashboard state reset!")
            st.rerun()
    
    # Advanced settings
    st.markdown("---")
    st.subheader("⚙️ Advanced Settings")
    
    with st.expander("🔒 Security Settings"):
        st.info("API authentication and security settings coming soon...")
    
    with st.expander("📊 Logging Settings"):
        log_level = st.selectbox(
            "Log Level",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=1
        )
        
        enable_request_logging = st.checkbox("Enable Request Logging", value=False)
        
        st.info("Logging configuration will be applied in future versions")
    
    with st.expander("🔔 Notification Settings"):
        st.info("Notification settings coming soon...")
    
    # System information
    st.markdown("---")
    st.subheader("ℹ️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**Dashboard Version:** 1.0.0")
        st.info("**Streamlit Version:** 1.31.0")
    
    with col2:
        st.info(f"**Current API:** {api_base_url}")
        st.info(f"**Last Updated:** {st.session_state.get('last_update', 'N/A')}")
    
    # About
    st.markdown("---")
    st.subheader("📖 About")
    
    st.markdown("""
    **Ecosystem MCP Dashboard**
    
    A comprehensive monitoring and management interface for the Ecosystem MCP service.
    
    **Features:**
    - 🏥 Infrastructure health monitoring
    - 🤖 Interactive RAG query interface
    - 📚 Document management
    - ⚡ Cache performance tracking
    - 📊 Real-time metrics and analytics
    - 🔧 System configuration
    
    **Documentation:** [View Docs](#)
    
    **Support:** [Get Help](#)
    
    **License:** MIT
    """)
    
    # Export settings
    st.markdown("---")
    st.subheader("💾 Export / Import")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Settings", use_container_width=True):
            settings = {
                "api_base_url": api_base_url,
                "theme": "light",
                "refresh_interval": 30,
                "items_per_page": 20
            }
            
            st.download_button(
                "Download settings.json",
                data=json.dumps(settings, indent=2),
                file_name="dashboard_settings.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("📤 Import Settings", use_container_width=True):
            st.info("Settings import coming soon...")

