"""
Service Manager Widget for Streamlit Dashboard.

Provides UI controls to start/restart Docker services automatically.
"""

import streamlit as st
import os
from pathlib import Path
from typing import Optional
from .docker_manager import get_docker_manager, DockerService


class ServiceManagerWidget:
    """Widget to manage Docker services from the dashboard."""
    
    def __init__(self, compose_file: Optional[str] = None):
        """
        Initialize service manager widget.
        
        Args:
            compose_file: Path to docker-compose file (defaults to project root)
        """
        self.docker_manager = get_docker_manager()
        
        # Default to docker-compose.dev.yml in project root
        if compose_file is None:
            # Assuming dashboard is in services/ecosystem-mcp-dashboard/
            project_root = Path(__file__).parent.parent.parent.parent
            compose_file = project_root / "docker-compose.dev.yml"
        
        self.compose_file = str(compose_file) if Path(compose_file).exists() else None
    
    def show_service_status(self, service_name: str, show_controls: bool = True):
        """
        Display service status with optional controls.
        
        Args:
            service_name: Name of the Docker service
            show_controls: Whether to show start/restart controls
        """
        status = self.docker_manager.get_service_status(service_name)
        
        # Status display
        if status.status == "running":
            st.success(f"✅ {service_name} is running")
            if show_controls:
                if st.button(f"🔄 Restart {service_name}", key=f"restart_{service_name}"):
                    self._restart_service(service_name)
        
        elif status.status == "stopped":
            st.warning(f"⏸️ {service_name} is stopped")
            if show_controls:
                if st.button(f"▶️ Start {service_name}", key=f"start_{service_name}"):
                    self._start_service(service_name)
        
        elif status.status == "not_found":
            st.error(f"❌ {service_name} not found")
            if show_controls and self.compose_file:
                if st.button(f"🚀 Deploy {service_name}", key=f"deploy_{service_name}"):
                    self._deploy_service(service_name)
        
        elif status.status == "docker_unavailable":
            st.error("❌ Docker daemon is not running")
            st.info("Please start Docker Desktop to manage services")
            self._show_docker_start_instructions()
        
        else:
            st.error(f"❌ Unknown status for {service_name}: {status.status}")
    
    def auto_start_if_needed(self, service_name: str, api_url: str) -> bool:
        """
        Automatically attempt to start service if API is unreachable.
        
        Args:
            service_name: Name of the Docker service
            api_url: API URL to check
            
        Returns:
            True if service was started or is already running
        """
        import httpx
        
        # First check if API is reachable
        try:
            response = httpx.get(f"{api_url}/health", timeout=2.0)
            if response.status_code == 200:
                return True  # Service is already accessible
        except:
            pass  # API not reachable, continue to start service
        
        # Check Docker service status
        status = self.docker_manager.get_service_status(service_name, force_refresh=True)
        
        if status.status == "running":
            # Service is running but API not responding - may need time to start
            st.info(f"⏳ {service_name} is starting up, please wait...")
            return False
        
        if status.status in ["stopped", "not_found"]:
            # Attempt to start
            with st.spinner(f"Starting {service_name}..."):
                if self.compose_file:
                    success, message = self.docker_manager.auto_start_service(
                        service_name,
                        self.compose_file
                    )
                else:
                    success, message = self.docker_manager.start_service(service_name)
                
                if success:
                    st.success(message)
                    st.info("⏳ Service is starting, please wait 10-30 seconds for it to be ready...")
                    return False  # Not ready yet
                else:
                    st.error(message)
                    return False
        
        return False
    
    def show_ecosystem_services(self):
        """Display status of all ecosystem services."""
        st.subheader("🐳 Ecosystem Services")
        
        # Check Docker status first
        if not self.docker_manager.is_docker_running(force_check=True):
            st.error("❌ Docker daemon is not running")
            self._show_docker_start_instructions()
            return
        
        # Get all ecosystem services
        services = self.docker_manager.get_all_services(filter_prefix="ecosystem-")
        
        if not services:
            st.warning("No ecosystem services found")
            if self.compose_file:
                st.info("You can deploy services using the docker-compose file")
                
                if st.button("🚀 Deploy All Services"):
                    self._deploy_all_services()
            return
        
        # Display services in expandable cards
        for service in services:
            with st.expander(f"{self._get_status_icon(service.status)} {service.name}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Status:** {service.status}")
                    st.markdown(f"**Image:** {service.image}")
                    if service.ports:
                        ports_str = ", ".join([f"{k}→{v}" for k, v in service.ports.items()])
                        st.markdown(f"**Ports:** {ports_str}")
                
                with col2:
                    if service.status == "running":
                        if st.button("🔄 Restart", key=f"restart_{service.name}_exp"):
                            self._restart_service(service.name)
                    elif service.status == "stopped":
                        if st.button("▶️ Start", key=f"start_{service.name}_exp"):
                            self._start_service(service.name)
    
    def show_quick_fix_panel(self, service_name: str):
        """
        Display a quick fix panel for unreachable services.
        
        Args:
            service_name: Name of the service that's unreachable
        """
        st.error(f"🔌 Cannot connect to {service_name}")
        
        with st.expander("🔧 Quick Fix Options", expanded=True):
            status = self.docker_manager.get_service_status(service_name)
            
            st.markdown("### Service Status")
            st.info(f"Current status: **{status.status}**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Refresh Status", key=f"refresh_{service_name}"):
                    st.rerun()
            
            with col2:
                if status.status in ["stopped", "not_found"]:
                    if st.button("▶️ Start Service", key=f"quickstart_{service_name}"):
                        self._start_service(service_name, auto_rerun=True)
                elif status.status == "running":
                    if st.button("🔄 Restart Service", key=f"quickrestart_{service_name}"):
                        self._restart_service(service_name, auto_rerun=True)
            
            with col3:
                if self.compose_file and status.status == "not_found":
                    if st.button("🚀 Deploy Service", key=f"quickdeploy_{service_name}"):
                        self._deploy_service(service_name, auto_rerun=True)
            
            # Show instructions
            st.markdown("---")
            st.markdown("### Manual Steps")
            
            if status.status == "docker_unavailable":
                self._show_docker_start_instructions()
            else:
                st.code(f"""
# Start service manually:
cd {Path(self.compose_file).parent if self.compose_file else '.'}
docker-compose -f docker-compose.dev.yml up -d {service_name}

# Check status:
docker ps | grep {service_name}

# View logs:
docker logs {service_name}
                """, language="bash")
    
    def _start_service(self, service_name: str, auto_rerun: bool = False):
        """Start a service with user feedback."""
        with st.spinner(f"Starting {service_name}..."):
            if self.compose_file:
                success, message = self.docker_manager.start_service(
                    service_name,
                    self.compose_file
                )
            else:
                success, message = self.docker_manager.start_service(service_name)
            
            if success:
                st.success(message)
                st.info("⏳ Waiting for service to be ready (10-30 seconds)...")
                if auto_rerun:
                    import time
                    time.sleep(3)
                    st.rerun()
            else:
                st.error(message)
    
    def _restart_service(self, service_name: str, auto_rerun: bool = False):
        """Restart a service with user feedback."""
        with st.spinner(f"Restarting {service_name}..."):
            success, message = self.docker_manager.restart_service(service_name)
            
            if success:
                st.success(message)
                if auto_rerun:
                    import time
                    time.sleep(3)
                    st.rerun()
            else:
                st.error(message)
    
    def _deploy_service(self, service_name: str, auto_rerun: bool = False):
        """Deploy a service using docker-compose."""
        if not self.compose_file:
            st.error("No docker-compose file configured")
            return
        
        with st.spinner(f"Deploying {service_name}..."):
            success, message = self.docker_manager.start_service(
                service_name,
                self.compose_file
            )
            
            if success:
                st.success(message)
                st.info("⏳ Service is deploying, please wait...")
                if auto_rerun:
                    import time
                    time.sleep(5)
                    st.rerun()
            else:
                st.error(message)
    
    def _deploy_all_services(self):
        """Deploy all services from docker-compose."""
        if not self.compose_file:
            st.error("No docker-compose file configured")
            return
        
        services = self.docker_manager.get_compose_services(self.compose_file)
        
        if not services:
            st.error("No services found in docker-compose file")
            return
        
        with st.spinner(f"Deploying {len(services)} services..."):
            import subprocess
            try:
                result = subprocess.run(
                    ["docker-compose", "-f", self.compose_file, "up", "-d"],
                    capture_output=True,
                    timeout=300,
                    text=True
                )
                
                if result.returncode == 0:
                    st.success(f"✅ Deployed {len(services)} services successfully")
                    st.info("⏳ Services are starting, please wait...")
                    import time
                    time.sleep(5)
                    st.rerun()
                else:
                    st.error(f"Failed to deploy services: {result.stderr}")
            
            except Exception as e:
                st.error(f"Error deploying services: {str(e)}")
    
    def _show_docker_start_instructions(self):
        """Show instructions for starting Docker."""
        st.markdown("""
        ### 🐳 Start Docker Desktop
        
        **macOS:**
        1. Open Spotlight (Cmd + Space)
        2. Type "Docker" and press Enter
        3. Wait for Docker icon in menu bar to be solid
        
        **Or from Terminal:**
        ```bash
        open -a Docker
        ```
        
        **Windows:**
        1. Open Start Menu
        2. Search for "Docker Desktop"
        3. Click to start
        
        **Linux:**
        ```bash
        sudo systemctl start docker
        ```
        
        After Docker starts, refresh this page.
        """)
    
    def _get_status_icon(self, status: str) -> str:
        """Get emoji icon for service status."""
        icons = {
            "running": "🟢",
            "stopped": "🟡",
            "not_found": "🔴",
            "docker_unavailable": "❌",
            "error": "⚠️"
        }
        return icons.get(status, "⚪")


# Convenience function for quick use
def show_service_manager(service_name: str = "ecosystem-mcp", compose_file: Optional[str] = None):
    """
    Show service manager widget for a specific service.
    
    Args:
        service_name: Name of the Docker service
        compose_file: Optional path to docker-compose file
    """
    manager = ServiceManagerWidget(compose_file)
    manager.show_quick_fix_panel(service_name)

