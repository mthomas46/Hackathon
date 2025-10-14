"""Home dashboard page."""

import streamlit as st
import httpx
from datetime import datetime
import plotly.graph_objects as go

def show(api_base_url: str):
    """Show home dashboard."""
    st.title("🏠 Dashboard Overview")
    
    # Quick stats row
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Fetch service info
        response = httpx.get(f"{api_base_url}/about-me", timeout=5.0)
        if response.status_code == 200:
            service_info = response.json()
            
            with col1:
                st.metric("Service", "Ecosystem MCP", delta="v0.1.0")
            
            with col2:
                st.metric("Status", "🟢 Healthy", delta=None)
            
            with col3:
                st.metric("Uptime", "Running", delta=None)
            
            with col4:
                st.metric("API Version", "v1", delta=None)
            
            # Service description
            st.markdown("---")
            st.subheader("📋 About Ecosystem MCP")
            st.info(service_info.get("description", "N/A"))
            
            # Capabilities
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("✨ Key Capabilities")
                for cap in service_info.get("capabilities", []):
                    st.markdown(f"✅ {cap}")
            
            with col_right:
                st.subheader("🎯 Key Features")
                for feature in service_info.get("key_features", []):
                    st.markdown(f"🔹 {feature}")
            
            # Ecosystem role
            st.markdown("---")
            st.subheader("🌐 Ecosystem Role")
            st.success(service_info.get("ecosystem_role", "N/A"))
            
        else:
            st.error(f"Failed to fetch service info: {response.status_code}")
    
    except Exception as e:
        st.error(f"Error connecting to API: {str(e)}")
        st.info(f"Make sure the service is running at {api_base_url}")
    
    # Recent activity (placeholder)
    st.markdown("---")
    st.subheader("📌 Recent Activity")
    st.info("Activity tracking coming soon...")

