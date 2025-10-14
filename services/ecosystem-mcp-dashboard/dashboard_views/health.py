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
            
            try:
                # Fetch circuit breaker data from admin endpoint
                breaker_response = httpx.get(f"{api_base_url}/api/v1/admin/circuit-breakers", timeout=5.0)
                
                if breaker_response.status_code == 200:
                    breaker_data = breaker_response.json()
                    breakers = breaker_data.get("circuit_breakers", {})
                    
                    if breakers:
                        for breaker_name, breaker_info in breakers.items():
                            state = breaker_info.get("state", "UNKNOWN").upper()
                            
                            # Skip if not configured
                            if state == "NOT_CONFIGURED":
                                continue
                            
                            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                            
                            with col1:
                                if state == "CLOSED":
                                    st.success(f"✅ **{breaker_name.title()}**")
                                elif state == "HALF_OPEN":
                                    st.warning(f"⚠️ **{breaker_name.title()}**")
                                else:
                                    st.error(f"❌ **{breaker_name.title()}**")
                            
                            with col2:
                                st.metric("State", state)
                            
                            with col3:
                                failure_count = breaker_info.get('failure_count', 0)
                                total_calls = breaker_info.get('total_calls', 0)
                                st.metric("Failures", f"{failure_count}/{breaker_info.get('config', {}).get('failure_threshold', 5)}")
                            
                            with col4:
                                if state == "OPEN":
                                    retry_time = breaker_info.get('recovery_time_remaining', 0)
                                    st.metric("Retry In", f"{retry_time:.0f}s")
                                elif state == "CLOSED" and total_calls > 0:
                                    success_rate = (breaker_info.get('total_successes', 0) / total_calls * 100) if total_calls > 0 else 0
                                    st.metric("Success", f"{success_rate:.1f}%")
                                else:
                                    st.metric("Calls", total_calls)
                            
                            # Show details in expander
                            with st.expander(f"🔍 {breaker_name.title()} Details"):
                                detail_col1, detail_col2 = st.columns(2)
                                
                                with detail_col1:
                                    st.markdown("**Statistics:**")
                                    st.write(f"Total Calls: {breaker_info.get('total_calls', 0)}")
                                    st.write(f"Total Successes: {breaker_info.get('total_successes', 0)}")
                                    st.write(f"Total Failures: {breaker_info.get('total_failures', 0)}")
                                    st.write(f"Current Failures: {breaker_info.get('failure_count', 0)}")
                                
                                with detail_col2:
                                    st.markdown("**Configuration:**")
                                    config = breaker_info.get('config', {})
                                    st.write(f"Failure Threshold: {config.get('failure_threshold', 'N/A')}")
                                    st.write(f"Success Threshold: {config.get('success_threshold', 'N/A')}")
                                    st.write(f"Timeout: {config.get('timeout', 'N/A')}s")
                                
                                if "last_failure_time" in breaker_info:
                                    st.markdown("**Timing:**")
                                    st.write(f"Time Since Last Failure: {breaker_info.get('time_since_last_failure', 0):.1f}s")
                                
                                if "time_in_open_state" in breaker_info:
                                    st.write(f"Time in Open State: {breaker_info.get('time_in_open_state', 0):.1f}s")
                                
                                st.markdown("**Raw Data:**")
                                st.json(breaker_info)
                        
                        # Show summary
                        st.info(f"ℹ️ {breaker_data.get('message', 'Circuit breakers active')}")
                    else:
                        st.info("✅ All circuit breakers are healthy (CLOSED state)")
                else:
                    st.warning(f"Could not fetch circuit breaker data: HTTP {breaker_response.status_code}")
            
            except Exception as breaker_error:
                st.error(f"Error fetching circuit breakers: {str(breaker_error)}")
            
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

