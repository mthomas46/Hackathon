"""Container management page."""

import streamlit as st
import httpx
import time
from datetime import datetime

def show(api_base_url: str):
    """Show container management page."""
    st.title("🐳 Container Management")
    
    st.markdown("""
    Manage Docker containers in the Ecosystem MCP stack. You can view status,
    restart containers, view logs, and monitor resource usage.
    """)
    
    # Refresh controls
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh")
    
    if auto_refresh:
        time.sleep(5)
        st.rerun()
    
    # Fetch containers
    try:
        response = httpx.get(
            f"{api_base_url}/api/v1/containers",
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            containers = data.get("containers", [])
            
            if not containers:
                st.info("No containers found. Make sure Docker is running.")
                return
            
            # Summary metrics
            st.subheader("📊 Container Summary")
            
            col1, col2, col3, col4 = st.columns(4)
            
            running = sum(1 for c in containers if c.get("status") == "running")
            stopped = sum(1 for c in containers if c.get("status") in ["exited", "stopped"])
            paused = sum(1 for c in containers if c.get("status") == "paused")
            
            with col1:
                st.metric("Total Containers", len(containers))
            
            with col2:
                st.metric("Running", running, delta=None)
            
            with col3:
                st.metric("Stopped", stopped, delta=None)
            
            with col4:
                st.metric("Paused", paused, delta=None)
            
            # Container list
            st.markdown("---")
            st.subheader("📦 Containers")
            
            for container in containers:
                name = container.get("name", "Unknown")
                container_id = container.get("id", "N/A")
                status = container.get("status", "unknown")
                image = container.get("image", "N/A")
                
                # Status icon
                if status == "running":
                    status_icon = "🟢"
                    status_color = "normal"
                elif status in ["exited", "stopped"]:
                    status_icon = "🔴"
                    status_color = "error"
                elif status == "paused":
                    status_icon = "🟡"
                    status_color = "warning"
                else:
                    status_icon = "⚪"
                    status_color = "info"
                
                with st.expander(f"{status_icon} **{name}** ({status})"):
                    # Container info
                    col_info, col_actions = st.columns([2, 1])
                    
                    with col_info:
                        st.markdown(f"**ID:** `{container_id}`")
                        st.markdown(f"**Image:** {image}")
                        st.markdown(f"**Status:** {status}")
                        
                        if status == "running":
                            # Show resource usage
                            memory_usage = container.get("memory_usage_mb")
                            memory_limit = container.get("memory_limit_mb")
                            memory_percent = container.get("memory_percent")
                            
                            if memory_usage:
                                st.markdown(f"**Memory:** {memory_usage:.1f} MB / {memory_limit:.1f} MB ({memory_percent:.1f}%)")
                        
                        # Ports
                        ports = container.get("ports", {})
                        if ports:
                            port_list = []
                            for internal, external_list in ports.items():
                                if external_list:
                                    for ext in external_list:
                                        host_port = ext.get("HostPort")
                                        if host_port:
                                            port_list.append(f"{host_port}->{internal}")
                            
                            if port_list:
                                st.markdown(f"**Ports:** {', '.join(port_list)}")
                    
                    with col_actions:
                        st.markdown("**Actions**")
                        
                        # Action buttons based on status
                        if status == "running":
                            if st.button("🔄 Restart", key=f"restart_{name}", use_container_width=True):
                                with st.spinner(f"Restarting {name}..."):
                                    try:
                                        action_response = httpx.post(
                                            f"{api_base_url}/api/v1/containers/action",
                                            json={
                                                "action": "restart",
                                                "container_name": name
                                            },
                                            timeout=30.0
                                        )
                                        
                                        if action_response.status_code == 200:
                                            result = action_response.json()
                                            st.success(result.get("message", "Restarted successfully"))
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error(f"Failed: {action_response.status_code}")
                                    
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            
                            if st.button("⏸️ Pause", key=f"pause_{name}", use_container_width=True):
                                with st.spinner(f"Pausing {name}..."):
                                    try:
                                        action_response = httpx.post(
                                            f"{api_base_url}/api/v1/containers/action",
                                            json={
                                                "action": "pause",
                                                "container_name": name
                                            },
                                            timeout=30.0
                                        )
                                        
                                        if action_response.status_code == 200:
                                            st.success("Paused successfully")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(f"Failed: {action_response.status_code}")
                                    
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                            
                            if st.button("⏹️ Stop", key=f"stop_{name}", use_container_width=True):
                                with st.spinner(f"Stopping {name}..."):
                                    try:
                                        action_response = httpx.post(
                                            f"{api_base_url}/api/v1/containers/action",
                                            json={
                                                "action": "stop",
                                                "container_name": name
                                            },
                                            timeout=30.0
                                        )
                                        
                                        if action_response.status_code == 200:
                                            st.success("Stopped successfully")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(f"Failed: {action_response.status_code}")
                                    
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                        
                        elif status == "paused":
                            if st.button("▶️ Unpause", key=f"unpause_{name}", use_container_width=True):
                                with st.spinner(f"Unpausing {name}..."):
                                    try:
                                        action_response = httpx.post(
                                            f"{api_base_url}/api/v1/containers/action",
                                            json={
                                                "action": "unpause",
                                                "container_name": name
                                            },
                                            timeout=30.0
                                        )
                                        
                                        if action_response.status_code == 200:
                                            st.success("Unpaused successfully")
                                            time.sleep(1)
                                            st.rerun()
                                        else:
                                            st.error(f"Failed: {action_response.status_code}")
                                    
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                        
                        elif status in ["exited", "stopped"]:
                            if st.button("▶️ Start", key=f"start_{name}", use_container_width=True):
                                with st.spinner(f"Starting {name}..."):
                                    try:
                                        action_response = httpx.post(
                                            f"{api_base_url}/api/v1/containers/action",
                                            json={
                                                "action": "start",
                                                "container_name": name
                                            },
                                            timeout=30.0
                                        )
                                        
                                        if action_response.status_code == 200:
                                            st.success("Started successfully")
                                            time.sleep(2)
                                            st.rerun()
                                        else:
                                            st.error(f"Failed: {action_response.status_code}")
                                    
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                    
                    # Tabs for details
                    tab1, tab2, tab3 = st.tabs(["📊 Stats", "📜 Logs", "ℹ️ Details"])
                    
                    with tab1:
                        if status == "running":
                            if st.button("Load Stats", key=f"stats_{name}"):
                                try:
                                    stats_response = httpx.get(
                                        f"{api_base_url}/api/v1/containers/{name}/stats",
                                        timeout=10.0
                                    )
                                    
                                    if stats_response.status_code == 200:
                                        stats = stats_response.json()
                                        
                                        # Memory stats
                                        memory = stats.get("memory", {})
                                        st.metric("Memory Usage", f"{memory.get('usage_mb', 0):.1f} MB")
                                        st.metric("Memory Limit", f"{memory.get('limit_mb', 0):.1f} MB")
                                        st.metric("Memory %", f"{memory.get('percent', 0):.1f}%")
                                        
                                        # CPU stats
                                        cpu = stats.get("cpu", {})
                                        st.metric("Online CPUs", cpu.get("online_cpus", 0))
                                    
                                    else:
                                        st.error("Failed to load stats")
                                
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                        else:
                            st.info("Container must be running to view stats")
                    
                    with tab2:
                        if st.button("Load Logs", key=f"logs_{name}"):
                            try:
                                logs_response = httpx.get(
                                    f"{api_base_url}/api/v1/containers/{name}/logs?tail=50",
                                    timeout=10.0
                                )
                                
                                if logs_response.status_code == 200:
                                    logs_data = logs_response.json()
                                    log_lines = logs_data.get("logs", [])
                                    
                                    # Convert list to string (API returns logs as a list of lines)
                                    if log_lines:
                                        if isinstance(log_lines, list):
                                            logs_text = "\n".join(str(line) for line in log_lines[-50:])
                                        else:
                                            logs_text = str(log_lines)
                                        
                                        st.text_area(
                                            "Container Logs",
                                            value=logs_text,
                                            height=400,
                                            disabled=True,
                                            key=f"container_logs_{name}"
                                        )
                                    else:
                                        st.info("No logs available")
                                else:
                                    st.error("Failed to load logs")
                            
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with tab3:
                        if st.button("Load Details", key=f"details_{name}"):
                            try:
                                details_response = httpx.get(
                                    f"{api_base_url}/api/v1/containers/{name}",
                                    timeout=10.0
                                )
                                
                                if details_response.status_code == 200:
                                    details = details_response.json()
                                    
                                    # Show key details
                                    st.markdown(f"**Full ID:** `{details.get('id', 'N/A')}`")
                                    st.markdown(f"**Created:** {details.get('created', 'N/A')}")
                                    if details.get('started'):
                                        st.markdown(f"**Started:** {details.get('started')}")
                                    
                                    # Full JSON
                                    with st.expander("Full Container Details (JSON)"):
                                        st.json(details)
                                else:
                                    st.error("Failed to load details")
                            
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
        
        elif response.status_code == 503:
            st.error("❌ Docker is not available")
            st.info("Make sure Docker is running and the ecosystem-mcp service has access to Docker.")
            st.markdown("""
            **Troubleshooting:**
            - Check if Docker daemon is running: `docker ps`
            - Verify Docker socket is mounted: `/var/run/docker.sock`
            - Ensure container has permissions to access Docker
            """)
        
        else:
            st.error(f"Failed to fetch containers: {response.status_code}")
            st.code(response.text)
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
        st.info("Make sure the ecosystem-mcp service is running.")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    # Help section
    st.markdown("---")
    st.subheader("💡 Container Management Help")
    
    with st.expander("ℹ️ About Container Actions"):
        st.markdown("""
        **Available Actions:**
        
        - **🔄 Restart**: Stops and starts a container
        - **▶️ Start**: Starts a stopped container
        - **⏹️ Stop**: Stops a running container
        - **⏸️ Pause**: Pauses a running container (freezes state)
        - **▶️ Unpause**: Resumes a paused container
        
        **Safety Notes:**
        - Restarting a container will interrupt active connections
        - Allow 10-30 seconds for actions to complete
        - Check logs if a container fails to start
        - Some containers have health checks that may restart them automatically
        """)
    
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        **Common Issues:**
        
        1. **"Container not found"**
           - Container may have been removed
           - Refresh the list
        
        2. **"Docker not available"**
           - Ensure Docker daemon is running
           - Check Docker socket mount in docker-compose.yml
        
        3. **"Permission denied"**
           - Container needs access to Docker socket
           - Add to docker-compose: `volumes: - /var/run/docker.sock:/var/run/docker.sock`
        
        4. **Container won't start**
           - Check logs for errors
           - Verify port conflicts
           - Check resource limits
        """)

