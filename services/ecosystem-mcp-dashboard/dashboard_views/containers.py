"""Container management page with Docker CLI integration."""

import streamlit as st
import httpx
import time
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import Docker manager
try:
    from utils.docker_manager import get_docker_manager
    from utils.service_manager_widget import ServiceManagerWidget
    DOCKER_MANAGER_AVAILABLE = True
except ImportError:
    DOCKER_MANAGER_AVAILABLE = False

def show(api_base_url: str):
    """Show container management page with enhanced Docker integration."""
    st.title("🐳 Container Management")
    
    st.markdown("""
    Manage Docker containers in the Ecosystem MCP stack. View status, start/stop/restart containers,
    view logs, and monitor resource usage with integrated Docker CLI support.
    """)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Via API", "🐳 Direct Docker Access", "🚀 Service Manager"])
    
    with tab1:
        show_via_api(api_base_url)
    
    with tab2:
        if DOCKER_MANAGER_AVAILABLE:
            show_direct_docker()
        else:
            st.error("Docker manager not available")
    
    with tab3:
        if DOCKER_MANAGER_AVAILABLE:
            show_service_manager()
        else:
            st.error("Service manager not available")


def show_via_api(api_base_url: str):
    """Show containers via API (original implementation)."""
    st.subheader("📊 Containers via API")
    st.caption("Fetching container information through the ecosystem-mcp API")
    
    # Refresh controls
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        if st.button("🔄 Refresh", use_container_width=True, key="api_refresh"):
            st.rerun()
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh", key="api_auto_refresh")
    
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
        st.warning("The ecosystem-mcp service may not be running.")
        
        if DOCKER_MANAGER_AVAILABLE:
            st.info("💡 **Tip:** Try the **🐳 Direct Docker Access** or **🚀 Service Manager** tabs to manage containers directly!")
        else:
            st.info("Make sure Docker is running and the ecosystem-mcp service is started.")
    
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


def show_direct_docker():
    """Show containers using direct Docker CLI access."""
    st.subheader("🐳 Direct Docker Access")
    st.caption("Manage containers directly via Docker CLI with caching")
    
    docker_manager = get_docker_manager()
    
    # Check Docker status
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if not docker_manager.is_docker_running(force_check=True):
            st.error("❌ Docker daemon is not running")
            _show_docker_start_instructions()
            return
        else:
            st.success("✅ Docker daemon is running")
    
    with col2:
        if st.button("🔄 Refresh", key="docker_refresh", use_container_width=True):
            # Clear cache
            docker_manager.service_cache.clear()
            st.rerun()
    
    # Get all services
    st.markdown("---")
    services = docker_manager.get_all_services()
    
    if not services:
        st.warning("No Docker containers found")
        st.info("Containers may not be running or Docker may be starting up")
        return
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        filter_prefix = st.text_input(
            "Filter by name prefix",
            value="ecosystem-",
            key="docker_filter",
            help="Leave empty to show all containers"
        )
    
    with col2:
        status_filter = st.multiselect(
            "Filter by status",
            options=["running", "stopped"],
            default=["running", "stopped"],
            key="docker_status_filter"
        )
    
    # Apply filters
    filtered_services = [
        s for s in services
        if (not filter_prefix or s.name.startswith(filter_prefix))
        and s.status in status_filter
    ]
    
    # Summary
    st.markdown(f"**Found {len(filtered_services)} containers** (of {len(services)} total)")
    
    # Display services
    for service in filtered_services:
        status_icon = "🟢" if service.status == "running" else "🟡" if service.status == "stopped" else "🔴"
        
        with st.expander(f"{status_icon} {service.name} ({service.status})"):
            col_info, col_actions = st.columns([2, 1])
            
            with col_info:
                st.markdown(f"**Status:** {service.status}")
                st.markdown(f"**Image:** {service.image}")
                st.markdown(f"**ID:** `{service.container_id[:12] if service.container_id else 'N/A'}`")
                
                if service.ports:
                    ports_str = ", ".join([f"{k}→{v}" for k, v in service.ports.items()])
                    st.markdown(f"**Ports:** {ports_str}")
                
                st.caption(f"Last checked: {service.last_checked.strftime('%H:%M:%S')}")
            
            with col_actions:
                st.markdown("**Actions**")
                
                if service.status == "running":
                    if st.button("🔄 Restart", key=f"docker_restart_{service.name}", use_container_width=True):
                        success, message = docker_manager.restart_service(service.name)
                        if success:
                            st.success(message)
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(message)
                
                elif service.status == "stopped":
                    if st.button("▶️ Start", key=f"docker_start_{service.name}", use_container_width=True):
                        success, message = docker_manager.start_service(service.name)
                        if success:
                            st.success(message)
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(message)


def show_service_manager():
    """Show service manager with auto-start capabilities."""
    st.subheader("🚀 Service Manager & Auto-Start")
    st.caption("Manage ecosystem services with auto-start/restart capabilities")
    
    # Find docker-compose file
    dashboard_dir = Path(__file__).parent.parent
    project_root = dashboard_dir.parent.parent
    compose_file = project_root / "docker-compose.dev.yml"
    
    if not compose_file.exists():
        st.error(f"Docker-compose file not found at: {compose_file}")
        st.info("Please specify the correct path to docker-compose.dev.yml")
        return
    
    st.success(f"✅ Using compose file: `{compose_file.name}`")
    
    # Initialize service manager
    service_manager = ServiceManagerWidget(str(compose_file))
    docker_manager = get_docker_manager()
    
    # Check Docker status
    if not docker_manager.is_docker_running(force_check=True):
        st.error("❌ Docker daemon is not running")
        _show_docker_start_instructions()
        return
    
    st.markdown("---")
    
    # Key services
    st.subheader("🎯 Key Services")
    
    key_services = [
        "ecosystem-mcp-service",      # Main API service
        "ecosystem-mcp-postgres",     # Database
        "ecosystem-mcp-redis",        # Cache
        "ecosystem-mcp-ollama",       # LLM service
    ]
    
    for service_name in key_services:
        with st.expander(f"⚙️ {service_name}", expanded=(service_name == "ecosystem-mcp-service")):
            status = docker_manager.get_service_status(service_name, force_refresh=True)
            
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                if status.status == "running":
                    st.success(f"✅ Running")
                elif status.status == "stopped":
                    st.warning(f"⏸️ Stopped")
                elif status.status == "not_found":
                    st.error(f"❌ Not Found")
                else:
                    st.info(f"Status: {status.status}")
                
                if status.image:
                    st.caption(f"Image: {status.image}")
                if status.ports:
                    ports_str = ", ".join([f"{k}→{v}" for k, v in status.ports.items()])
                    st.caption(f"Ports: {ports_str}")
            
            with col2:
                if status.status == "running":
                    if st.button("🔄 Restart", key=f"mgr_restart_{service_name}", use_container_width=True):
                        with st.spinner(f"Restarting {service_name}..."):
                            success, message = docker_manager.restart_service(service_name)
                            if success:
                                st.success(message)
                                time.sleep(3)
                                st.rerun()
                            else:
                                st.error(message)
                
                elif status.status in ["stopped", "not_found"]:
                    if st.button("▶️ Start", key=f"mgr_start_{service_name}", use_container_width=True):
                        with st.spinner(f"Starting {service_name}..."):
                            success, message = docker_manager.auto_start_service(
                                service_name,
                                str(compose_file)
                            )
                            if success:
                                st.success(message)
                                time.sleep(3)
                                st.rerun()
                            else:
                                st.error(message)
            
            with col3:
                if st.button("🔍 Logs", key=f"mgr_logs_{service_name}", use_container_width=True):
                    st.session_state[f"show_logs_{service_name}"] = True
            
            # Show logs if requested
            if st.session_state.get(f"show_logs_{service_name}", False):
                st.markdown("**Recent Logs:**")
                try:
                    import subprocess
                    result = subprocess.run(
                        ["docker", "logs", "--tail", "50", service_name],
                        capture_output=True,
                        timeout=5,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        logs = result.stdout + result.stderr
                        st.code(logs, language="log")
                    else:
                        st.error("Failed to fetch logs")
                    
                    if st.button("Close Logs", key=f"close_logs_{service_name}"):
                        st.session_state[f"show_logs_{service_name}"] = False
                        st.rerun()
                
                except Exception as e:
                    st.error(f"Error fetching logs: {str(e)}")
    
    # Bulk actions
    st.markdown("---")
    st.subheader("🎛️ Bulk Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Start All Services", use_container_width=True, type="primary"):
            with st.spinner("Starting all services..."):
                import subprocess
                try:
                    result = subprocess.run(
                        ["docker-compose", "-f", str(compose_file), "up", "-d"],
                        capture_output=True,
                        timeout=300,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        st.success("✅ All services started")
                        time.sleep(5)
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.stderr}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("🔄 Restart All Services", use_container_width=True):
            with st.spinner("Restarting all services..."):
                import subprocess
                try:
                    result = subprocess.run(
                        ["docker-compose", "-f", str(compose_file), "restart"],
                        capture_output=True,
                        timeout=300,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        st.success("✅ All services restarted")
                        time.sleep(5)
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.stderr}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with col3:
        if st.button("⏹️ Stop All Services", use_container_width=True):
            with st.spinner("Stopping all services..."):
                import subprocess
                try:
                    result = subprocess.run(
                        ["docker-compose", "-f", str(compose_file), "stop"],
                        capture_output=True,
                        timeout=120,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        st.success("✅ All services stopped")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(f"Failed: {result.stderr}")
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")


def _show_docker_start_instructions():
    """Show instructions for starting Docker."""
    with st.expander("🐳 How to Start Docker", expanded=True):
        st.markdown("""
        ### Start Docker Desktop
        
        **macOS:**
        ```bash
        open -a Docker
        ```
        Or open Spotlight (Cmd + Space) and type "Docker"
        
        **Windows:**
        - Open Start Menu
        - Search for "Docker Desktop"
        - Click to start
        
        **Linux:**
        ```bash
        sudo systemctl start docker
        ```
        
        **Wait for Docker to be ready:**
        - macOS/Windows: Check menu bar/system tray for solid Docker icon
        - Linux: Run `docker ps` to verify
        
        After Docker starts, click **🔄 Refresh** above.
        """)

