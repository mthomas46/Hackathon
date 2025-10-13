"""Health & Infrastructure monitoring page."""

import streamlit as st
import httpx
import json
from datetime import datetime

def show(api_base_url: str):
    """Show health & infrastructure page."""
    st.title("🏥 Health & Infrastructure")
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (30s)")
    
    if auto_refresh:
        st.info("Auto-refreshing every 30 seconds...")
        # Note: Streamlit will handle this with st.experimental_rerun
    
    try:
        # Fetch infrastructure health
        response = httpx.get(f"{api_base_url}/api/v1/infrastructure/health", timeout=10.0)
        
        if response.status_code == 200:
            health_data = response.json()
            
            # Overall status
            status = health_data.get("status", "unknown")
            if status == "healthy":
                st.success(f"✅ System Status: **{status.upper()}**")
            elif status == "degraded":
                st.warning(f"⚠️ System Status: **{status.upper()}**")
            else:
                st.error(f"❌ System Status: **{status.upper()}**")
            
            st.caption(f"Last checked: {health_data.get('timestamp', 'N/A')}")
            
            # Component health
            st.markdown("---")
            st.subheader("🔧 Component Health")
            
            components = health_data.get("components", {})
            
            # Create columns for components
            cols = st.columns(min(len(components), 3))
            for idx, (component, details) in enumerate(components.items()):
                with cols[idx % 3]:
                    comp_status = details.get("status", "unknown")
                    
                    if comp_status == "healthy":
                        status_icon = "🟢"
                        status_color = "normal"
                    elif comp_status == "degraded":
                        status_icon = "🟡"
                        status_color = "warning"
                    else:
                        status_icon = "🔴"
                        status_color = "error"
                    
                    st.metric(
                        label=f"{status_icon} {component.title()}",
                        value=comp_status.upper()
                    )
                    
                    # Show details
                    if isinstance(details, dict):
                        with st.expander(f"Details"):
                            st.json(details)
            
            # Circuit breakers
            st.markdown("---")
            st.subheader("⚡ Circuit Breakers")
            
            breakers = health_data.get("components", {}).get("circuit_breakers", {})
            
            if breakers:
                for breaker_name, breaker_data in breakers.items():
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                    
                    state = breaker_data.get("state", "UNKNOWN")
                    
                    with col1:
                        if state == "CLOSED":
                            st.success(f"✅ {breaker_name}")
                        elif state == "HALF_OPEN":
                            st.warning(f"⚠️ {breaker_name}")
                        else:
                            st.error(f"❌ {breaker_name}")
                    
                    with col2:
                        st.write(f"State: **{state}**")
                    
                    with col3:
                        st.write(f"Failures: {breaker_data.get('failures', 0)}")
                    
                    with col4:
                        if state == "OPEN":
                            retry_time = breaker_data.get('time_until_retry_seconds', 0)
                            st.write(f"Retry in: {retry_time:.1f}s")
                        else:
                            st.write("—")
                    
                    # Show details in expander
                    with st.expander(f"🔍 {breaker_name} Details"):
                        st.json(breaker_data)
            else:
                st.info("No circuit breakers found or all are closed")
            
            # Diagnostics
            st.markdown("---")
            st.subheader("🔬 Diagnostics")
            
            if st.button("🔍 Run Full Diagnostics", use_container_width=True):
                with st.spinner("Running diagnostics..."):
                    try:
                        diag_response = httpx.get(
                            f"{api_base_url}/api/v1/infrastructure/diagnostics",
                            timeout=15.0
                        )
                        if diag_response.status_code == 200:
                            diag_data = diag_response.json()
                            
                            # Show recommendations
                            recommendations = diag_data.get("recommendations", [])
                            if recommendations:
                                st.warning("**Recommendations:**")
                                for rec in recommendations:
                                    st.markdown(f"- {rec}")
                            else:
                                st.success("✅ No issues found!")
                            
                            # Show full diagnostic data
                            with st.expander("Full Diagnostic Report"):
                                st.json(diag_data)
                        else:
                            st.error(f"Diagnostics failed: {diag_response.status_code}")
                    except Exception as e:
                        st.error(f"Error running diagnostics: {str(e)}")
        
        else:
            st.error(f"Failed to fetch health data: {response.status_code}")
            st.code(response.text)
    
    except httpx.TimeoutException:
        st.error("⏱️ Request timed out. The service may be unresponsive.")
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to service at {api_base_url}")
        st.info("Make sure the ecosystem-mcp service is running and accessible.")
    except Exception as e:
        st.error(f"Error: {str(e)}")

