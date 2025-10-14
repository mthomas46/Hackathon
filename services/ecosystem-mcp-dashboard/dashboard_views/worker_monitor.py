"""
Worker Monitor Page

Displays background worker status and provides controls for restarting workers.
"""

import streamlit as st
import httpx
from datetime import datetime


def show(api_base_url: str):
    """Display worker monitor page."""
    
    st.title("⚙️ Worker Monitor")
    st.markdown("Monitor and manage background workers")
    
    # Create tabs
    tab1, tab2 = st.tabs(["📊 Worker Status", "🔧 Management"])
    
    # ============================================================================
    # Tab 1: Worker Status
    # ============================================================================
    with tab1:
        st.header("📊 Worker Status")
        
        # Auto-refresh controls
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        with col2:
            auto_refresh = st.checkbox("Auto-refresh", value=False, key="worker_auto_refresh")
        
        with col3:
            if auto_refresh:
                refresh_interval = st.selectbox(
                    "Interval",
                    options=[5, 10, 15, 30],
                    index=1,
                    key="worker_refresh_interval"
                )
        
        # Auto-refresh logic
        if auto_refresh:
            import time
            if 'worker_last_refresh_time' not in st.session_state:
                st.session_state.worker_last_refresh_time = time.time()
            
            current_time = time.time()
            time_since_last_refresh = current_time - st.session_state.worker_last_refresh_time
            
            if time_since_last_refresh >= refresh_interval:
                st.session_state.worker_last_refresh_time = current_time
                st.rerun()
            else:
                time.sleep(0.5)
                st.rerun()
        
        st.markdown("---")
        
        # Fetch comprehensive health
        try:
            response = httpx.get(
                f"{api_base_url}/api/v1/admin/workers/health",
                timeout=10.0
            )
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Overall status
                overall_healthy = health_data.get("overall_healthy", False)
                timestamp = health_data.get("timestamp", "Unknown")
                
                if overall_healthy:
                    st.success(f"✅ All systems healthy (checked at {timestamp})")
                else:
                    st.error(f"⚠️ System health issues detected (checked at {timestamp})")
                
                st.markdown("---")
                
                # Container status
                st.subheader("🐳 Container Status")
                container = health_data.get("container", {})
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    container_healthy = container.get("healthy", False)
                    st.metric(
                        "Health",
                        "✅ Healthy" if container_healthy else "❌ Unhealthy",
                        help="Overall container health"
                    )
                
                with col2:
                    running = container.get("running", False)
                    st.metric(
                        "Status",
                        "🟢 Running" if running else "🔴 Stopped",
                        help="Container running state"
                    )
                
                with col3:
                    health_status = container.get("health_status", "none")
                    emoji = {"healthy": "✅", "unhealthy": "❌", "starting": "⏳", "none": "⚪"}.get(health_status, "❓")
                    st.metric(
                        "Health Check",
                        f"{emoji} {health_status.capitalize()}",
                        help="Docker health check status"
                    )
                
                with col4:
                    pid = container.get("pid", 0)
                    st.metric(
                        "Process ID",
                        str(pid) if pid > 0 else "N/A",
                        help="Container process ID"
                    )
                
                # Container details
                with st.expander("🔍 Container Details"):
                    st.json(container)
                
                st.markdown("---")
                
                # Worker status
                st.subheader("⚙️ Worker Status")
                workers = health_data.get("workers", {})
                
                # Ingestion worker
                ingestion = workers.get("ingestion", {})
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    worker_healthy = ingestion.get("healthy", False)
                    st.metric(
                        "Ingestion Worker",
                        "✅ Healthy" if worker_healthy else "❌ Unhealthy",
                        help="Overall worker health"
                    )
                
                with col2:
                    running = ingestion.get("running", False)
                    st.metric(
                        "Running",
                        "🟢 Yes" if running else "🔴 No",
                        help="Worker is running"
                    )
                
                with col3:
                    processing = ingestion.get("processing", False)
                    st.metric(
                        "Processing",
                        "🔄 Active" if processing else "⏸️ Idle",
                        help="Worker is actively processing jobs"
                    )
                
                with col4:
                    restart_attempts = ingestion.get("restart_attempts", 0)
                    st.metric(
                        "Restart Attempts",
                        str(restart_attempts),
                        help="Number of recent restart attempts"
                    )
                
                # Worker details
                with st.expander("🔍 Worker Details"):
                    st.json(ingestion)
                
                st.markdown("---")
                
                # Recommendations
                recommendations = health_data.get("recommendations", [])
                if recommendations:
                    st.subheader("💡 Recommendations")
                    for rec in recommendations:
                        if "✅" in rec:
                            st.success(rec)
                        elif "⚠️" in rec or "error" in rec.lower() or "unhealthy" in rec.lower():
                            st.warning(rec)
                        else:
                            st.info(rec)
                
            else:
                st.error(f"❌ Failed to get worker health (HTTP {response.status_code})")
                st.json(response.json())
                
        except httpx.RequestError as e:
            st.error(f"❌ Connection error: {e}")
            st.info("💡 Make sure the ecosystem-mcp service is running")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
    
    # ============================================================================
    # Tab 2: Management
    # ============================================================================
    with tab2:
        st.header("🔧 Worker Management")
        
        st.markdown("""
        ### Ingestion Worker Controls
        
        The ingestion worker processes document ingestion jobs from the queue.
        If the worker stops or gets stuck, you can restart it here.
        """)
        
        # Manual restart section
        st.subheader("🔄 Manual Restart")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            **When to use:**
            - Worker shows as unhealthy
            - Jobs are stuck in "queued" status
            - Worker is not processing jobs
            
            **What it does:**
            1. Stops the current worker instance
            2. Starts a new worker instance
            3. Verifies the new worker is healthy
            """)
        
        with col2:
            if st.button("🔄 Restart Worker", type="primary", use_container_width=True, key="manual_restart"):
                st.session_state['confirm_restart'] = True
        
        # Confirmation dialog
        if st.session_state.get('confirm_restart', False):
            st.warning("⚠️ This will restart the ingestion worker. Current processing jobs may be interrupted.")
            conf_col1, conf_col2 = st.columns(2)
            with conf_col1:
                if st.button("✅ Yes, Restart", type="primary", key="confirm_restart_yes"):
                    with st.spinner("Restarting worker..."):
                        try:
                            response = httpx.post(
                                f"{api_base_url}/api/v1/admin/workers/ingestion/restart",
                                timeout=30.0
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                if result.get("success"):
                                    st.success("✅ Worker restarted successfully!")
                                    st.json(result)
                                else:
                                    st.error(f"❌ Restart failed: {result.get('message', 'Unknown error')}")
                                    st.json(result)
                            else:
                                st.error(f"❌ HTTP {response.status_code}: {response.text}")
                            
                            st.session_state['confirm_restart'] = False
                            
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            st.session_state['confirm_restart'] = False
            
            with conf_col2:
                if st.button("❌ Cancel", key="confirm_restart_no"):
                    st.session_state['confirm_restart'] = False
                    st.rerun()
        
        st.markdown("---")
        
        # Auto-recovery section
        st.subheader("🔧 Auto-Recovery")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("""
            **Smart recovery:**
            - Checks if worker is healthy
            - Only restarts if unhealthy
            - Safer than manual restart
            
            **Use this when:**
            - You want automatic diagnostics
            - You're not sure if restart is needed
            - You want to be cautious
            """)
        
        with col2:
            if st.button("🔧 Auto-Recover", use_container_width=True, key="auto_recover"):
                with st.spinner("Checking worker health and recovering if needed..."):
                    try:
                        response = httpx.post(
                            f"{api_base_url}/api/v1/admin/workers/ingestion/auto-recover",
                            timeout=30.0
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            recovered = result.get("recovered", False)
                            message = result.get("message", "Unknown")
                            
                            if recovered:
                                st.success(f"✅ {message}")
                            else:
                                st.info(f"ℹ️ {message}")
                            
                            st.json(result)
                        else:
                            st.error(f"❌ HTTP {response.status_code}: {response.text}")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
        
        st.markdown("---")
        
        # Advanced section
        with st.expander("🔍 Advanced Diagnostics"):
            st.markdown("### Container Health Check")
            if st.button("Check Container", key="check_container"):
                try:
                    response = httpx.get(
                        f"{api_base_url}/api/v1/admin/workers/container/health",
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        st.json(response.json())
                    else:
                        st.error(f"HTTP {response.status_code}: {response.text}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            
            st.markdown("---")
            
            st.markdown("### Ingestion Worker Status")
            if st.button("Check Ingestion Worker", key="check_ingestion"):
                try:
                    response = httpx.get(
                        f"{api_base_url}/api/v1/admin/workers/ingestion/status",
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        st.json(response.json())
                    else:
                        st.error(f"HTTP {response.status_code}: {response.text}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        # Tips section
        st.markdown("---")
        st.markdown("### 💡 Tips")
        st.markdown("""
        - **Auto-refresh** the Worker Status tab to monitor in real-time
        - **Auto-Recover** is safer than manual restart
        - Check **logs** if restart doesn't fix the issue: `docker logs ecosystem-mcp-service`
        - If problems persist, try restarting the container: `docker restart ecosystem-mcp-service`
        """)

