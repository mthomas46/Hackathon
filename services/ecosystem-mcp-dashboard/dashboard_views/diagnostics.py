"""Diagnostics and connection testing page."""

import streamlit as st
import httpx
import time
from datetime import datetime

def show(api_base_url: str):
    """Show diagnostics page."""
    st.title("🔬 Diagnostics & Connection Testing")
    
    st.markdown("""
    Test connections, monitor service health, and view real-time diagnostics for all services.
    """)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🏥 Health Checks", "🔌 Connection Tests", "📡 Real-Time Monitoring"])
    
    with tab1:
        show_health_checks(api_base_url)
    
    with tab2:
        show_connection_tests(api_base_url)
    
    with tab3:
        show_realtime_monitoring(api_base_url)


def show_health_checks(api_base_url: str):
    """Display comprehensive health checks."""
    st.subheader("🏥 Comprehensive Health Check")
    
    col1, col2 = st.columns([3, 1])
    
    with col2:
        if st.button("🔄 Run Health Check", use_container_width=True, type="primary"):
            st.session_state.run_health_check = True
    
    if st.button("🔄 Check All Services", key="health_check_button") or st.session_state.get("run_health_check"):
        st.session_state.run_health_check = False
        
        with st.spinner("Running health checks..."):
            try:
                response = httpx.get(
                    f"{api_base_url}/api/v1/diagnostics/health",
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Overall status
                    overall_status = data.get("status", "unknown")
                    
                    if overall_status == "healthy":
                        st.success(f"✅ All services are healthy")
                    elif overall_status == "degraded":
                        st.warning(f"⚠️ Some services are degraded")
                    else:
                        st.error(f"❌ System is unhealthy")
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Checks", data.get("total_checks", 0))
                    with col2:
                        st.metric("Healthy", data.get("healthy", 0), delta=None)
                    with col3:
                        st.metric("Degraded", data.get("degraded", 0), delta=None)
                    with col4:
                        st.metric("Unhealthy", data.get("unhealthy", 0), delta=None)
                    
                    # Service details
                    st.markdown("---")
                    st.markdown("### Service Status")
                    
                    services = data.get("services", [])
                    
                    for service in services:
                        name = service.get("name", "Unknown")
                        status = service.get("status", "unknown")
                        latency = service.get("latency_ms", 0)
                        message = service.get("message", "")
                        details = service.get("details", {})
                        
                        # Status icon
                        if status == "healthy":
                            status_icon = "✅"
                            status_color = "normal"
                        elif status == "degraded":
                            status_icon = "⚠️"
                            status_color = "warning"
                        else:
                            status_icon = "❌"
                            status_color = "error"
                        
                        with st.expander(f"{status_icon} {name} ({status.upper()})"):
                            col_info, col_latency = st.columns([2, 1])
                            
                            with col_info:
                                st.markdown(f"**Status:** {status}")
                                st.markdown(f"**Message:** {message}")
                                st.markdown(f"**Timestamp:** {service.get('timestamp', 'unknown')}")
                            
                            with col_latency:
                                st.metric("Latency", f"{latency:.2f}ms")
                            
                            if details:
                                st.markdown("**Details:**")
                                st.json(details)
                
                else:
                    st.error(f"Health check failed: {response.status_code}")
            
            except httpx.ConnectError:
                st.error(f"❌ Cannot connect to API at {api_base_url}")
            except Exception as e:
                st.error(f"Error: {str(e)}")


def show_connection_tests(api_base_url: str):
    """Display individual connection tests."""
    st.subheader("🔌 Connection Tests")
    
    st.markdown("Test individual service connections:")
    
    services = ["postgresql", "redis", "chromadb", "ollama", "filesystem"]
    
    for service_name in services:
        col_name, col_button = st.columns([3, 1])
        
        with col_name:
            st.markdown(f"### {service_name.title()}")
        
        with col_button:
            if st.button(f"🧪 Test", key=f"test_{service_name}", use_container_width=True):
                st.session_state[f"test_result_{service_name}"] = None
                
                with st.spinner(f"Testing {service_name}..."):
                    try:
                        response = httpx.post(
                            f"{api_base_url}/api/v1/diagnostics/test-connection?service={service_name}",
                            timeout=10.0
                        )
                        
                        if response.status_code == 200:
                            st.session_state[f"test_result_{service_name}"] = response.json()
                    
                    except Exception as e:
                        st.session_state[f"test_result_{service_name}"] = {
                            "status": "error",
                            "message": str(e)
                        }
        
        # Display result if available
        result = st.session_state.get(f"test_result_{service_name}")
        if result:
            status = result.get("status", "unknown")
            latency = result.get("latency_ms", 0)
            message = result.get("message", "")
            
            if status == "healthy":
                st.success(f"✅ {message} ({latency:.2f}ms)")
            elif status == "degraded":
                st.warning(f"⚠️ {message} ({latency:.2f}ms)")
            elif status == "error":
                st.error(f"❌ {message}")
            else:
                st.error(f"❌ {message} ({latency:.2f}ms)")
            
            details = result.get("details", {})
            if details:
                with st.expander("Details"):
                    st.json(details)
        
        st.markdown("---")


def show_realtime_monitoring(api_base_url: str):
    """Display real-time monitoring data."""
    st.subheader("📡 Real-Time Monitoring")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        auto_refresh = st.checkbox("Auto-refresh every 5 seconds")
    
    with col2:
        if st.button("🔄 Refresh Now", use_container_width=True):
            st.rerun()
    
    if auto_refresh:
        time.sleep(5)
        st.rerun()
    
    try:
        response = httpx.get(
            f"{api_base_url}/api/v1/diagnostics/monitor",
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            
            st.info(f"**Last Updated:** {data.get('timestamp', 'unknown')}")
            
            # System resources
            system = data.get("system", {})
            if system and "error" not in system:
                st.markdown("### 💻 System Resources")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    cpu = system.get("cpu_percent", 0)
                    st.metric("CPU Usage", f"{cpu:.1f}%")
                
                with col2:
                    memory = system.get("memory_percent", 0)
                    st.metric("Memory Usage", f"{memory:.1f}%")
                
                with col3:
                    disk = system.get("disk_percent", 0)
                    st.metric("Disk Usage", f"{disk:.1f}%")
                
                with col4:
                    processes = system.get("process_count", 0)
                    st.metric("Processes", processes)
            
            # Service monitoring
            st.markdown("---")
            st.markdown("### 🔧 Services")
            
            services = data.get("services", {})
            
            for service_name, service_data in services.items():
                status = service_data.get("status", "unknown")
                
                if status == "healthy":
                    status_icon = "🟢"
                elif status == "degraded":
                    status_icon = "🟡"
                else:
                    status_icon = "🔴"
                
                with st.expander(f"{status_icon} {service_name.title()} ({status})"):
                    if "error" in service_data:
                        st.error(f"Error: {service_data['error']}")
                    else:
                        latency = service_data.get("latency_ms", 0)
                        st.metric("Latency", f"{latency:.2f}ms")
                        
                        # Service-specific metrics
                        if service_name == "postgresql":
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Connections", service_data.get("connections", 0))
                            with col2:
                                cache_hit = service_data.get("cache_hit_ratio", 0)
                                st.metric("Cache Hit Ratio", f"{cache_hit:.2f}%")
                            
                            db_size = service_data.get("database_size_bytes", 0)
                            st.metric("Database Size", f"{db_size / 1024 / 1024:.2f} MB")
                        
                        elif service_name == "redis":
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Clients", service_data.get("connected_clients", 0))
                            with col2:
                                st.metric("Memory", service_data.get("used_memory", "unknown"))
                            with col3:
                                st.metric("Ops/sec", service_data.get("ops_per_sec", 0))
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Hits", service_data.get("keyspace_hits", 0))
                            with col2:
                                st.metric("Misses", service_data.get("keyspace_misses", 0))
                        
                        elif service_name == "chromadb":
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Collections", service_data.get("collections", 0))
                            with col2:
                                st.metric("Total Vectors", service_data.get("total_vectors", 0))
                        
                        elif service_name == "ollama":
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Models", service_data.get("models", 0))
                            with col2:
                                model_names = service_data.get("model_names", [])
                                if model_names:
                                    st.markdown("**Available Models:**")
                                    for model in model_names:
                                        st.text(f"• {model}")
        
        else:
            st.error(f"Failed to fetch monitoring data: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

