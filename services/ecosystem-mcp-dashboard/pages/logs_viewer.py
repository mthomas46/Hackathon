"""Logs viewer page."""

import streamlit as st
import httpx
import asyncio
from datetime import datetime

def show(api_base_url: str):
    """Show logs viewer page."""
    st.title("📋 Logs Viewer")
    
    st.markdown("""
    View and monitor logs from all running containers in real-time.
    """)
    
    # Tabs for different log sources
    tab1, tab2, tab3 = st.tabs(["🐳 Container Logs", "🖥️ Dashboard Logs", "🔍 Search Logs"])
    
    with tab1:
        show_container_logs(api_base_url)
    
    with tab2:
        show_dashboard_logs()
    
    with tab3:
        show_log_search(api_base_url)


def show_container_logs(api_base_url: str):
    """Display logs from Docker containers."""
    st.subheader("🐳 Container Logs")
    
    # Fetch list of containers
    try:
        response = httpx.get(f"{api_base_url}/api/v1/containers", timeout=10.0)
        
        if response.status_code == 200:
            containers = response.json()
            
            if not containers:
                st.info("No containers found.")
                return
            
            # Container selection
            container_names = [c['name'] for c in containers]
            selected_container = st.selectbox(
                "Select Container",
                container_names,
                key="container_select"
            )
            
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                tail_lines = st.number_input(
                    "Number of lines",
                    min_value=10,
                    max_value=1000,
                    value=100,
                    step=10
                )
            
            with col2:
                auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)
            
            with col3:
                if st.button("🔄 Refresh", use_container_width=True):
                    st.rerun()
            
            # Auto-refresh logic
            if auto_refresh:
                import time
                time.sleep(5)
                st.rerun()
            
            # Fetch logs for selected container
            if selected_container:
                with st.spinner(f"Fetching logs for {selected_container}..."):
                    try:
                        log_response = httpx.get(
                            f"{api_base_url}/api/v1/containers/{selected_container}/logs",
                            params={"tail": tail_lines},
                            timeout=30.0  # Increased timeout for large log files
                        )
                        
                        if log_response.status_code == 200:
                            log_data = log_response.json()
                            logs = log_data.get("logs", "")
                            
                            st.markdown(f"**Logs from:** `{selected_container}`")
                            st.markdown(f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                            
                            # Display logs in a code block
                            if logs:
                                st.code(logs, language="log")
                                
                                # Download button
                                st.download_button(
                                    label="📥 Download Logs",
                                    data=logs,
                                    file_name=f"{selected_container}_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                                    mime="text/plain"
                                )
                            else:
                                st.info("No logs available for this container.")
                        else:
                            st.error(f"Failed to fetch logs: {log_response.status_code}")
                    
                    except Exception as e:
                        st.error(f"Error fetching logs: {str(e)}")
        
        else:
            st.error(f"Failed to fetch containers: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def show_dashboard_logs():
    """Display logs from the dashboard itself."""
    st.subheader("🖥️ Dashboard Logs")
    
    st.info("This feature displays logs from the Streamlit dashboard container.")
    
    # Try to read logs from common locations
    import subprocess
    import os
    
    try:
        # Try to get logs from Docker
        result = subprocess.run(
            ["docker", "logs", "ecosystem-mcp-dashboard", "--tail", "100"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            logs = result.stdout + result.stderr
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                if st.button("🔄 Refresh", key="refresh_dashboard", use_container_width=True):
                    st.rerun()
            
            if logs:
                st.code(logs, language="log")
                
                # Download button
                st.download_button(
                    label="📥 Download Dashboard Logs",
                    data=logs,
                    file_name=f"dashboard_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
                    mime="text/plain"
                )
            else:
                st.info("No logs available.")
        else:
            st.warning("Could not fetch dashboard logs via Docker command.")
            st.text(f"Error: {result.stderr}")
    
    except subprocess.TimeoutExpired:
        st.error("Timeout while fetching logs.")
    except FileNotFoundError:
        st.error("Docker command not found. Make sure Docker is installed.")
    except Exception as e:
        st.error(f"Error: {str(e)}")


def show_log_search(api_base_url: str):
    """Search and filter logs."""
    st.subheader("🔍 Search Logs")
    
    st.markdown("Search across container logs for specific patterns or keywords.")
    
    # Fetch list of containers
    try:
        response = httpx.get(f"{api_base_url}/api/v1/containers", timeout=10.0)
        
        if response.status_code == 200:
            containers = response.json()
            
            if not containers:
                st.info("No containers found.")
                return
            
            # Search configuration
            col1, col2 = st.columns([3, 1])
            
            with col1:
                search_term = st.text_input(
                    "🔍 Search term",
                    placeholder="Enter text to search for...",
                    key="search_term"
                )
            
            with col2:
                case_sensitive = st.checkbox("Case sensitive", value=False)
            
            # Container selection for search
            container_names = [c['name'] for c in containers]
            selected_containers = st.multiselect(
                "Select containers to search",
                container_names,
                default=container_names[:3] if len(container_names) >= 3 else container_names
            )
            
            if st.button("🔍 Search", type="primary", use_container_width=True):
                if not search_term:
                    st.warning("Please enter a search term.")
                    return
                
                if not selected_containers:
                    st.warning("Please select at least one container.")
                    return
                
                # Search logs
                results = []
                
                for container_name in selected_containers:
                    with st.spinner(f"Searching {container_name}..."):
                        try:
                            log_response = httpx.get(
                                f"{api_base_url}/api/v1/containers/{container_name}/logs",
                                params={"tail": 500},
                                timeout=30.0  # Increased timeout for large log files
                            )
                            
                            if log_response.status_code == 200:
                                log_data = log_response.json()
                                logs = log_data.get("logs", "")
                                
                                # Search in logs
                                if logs:
                                    lines = logs.split('\n')
                                    matching_lines = []
                                    
                                    for i, line in enumerate(lines, 1):
                                        if case_sensitive:
                                            if search_term in line:
                                                matching_lines.append((i, line))
                                        else:
                                            if search_term.lower() in line.lower():
                                                matching_lines.append((i, line))
                                    
                                    if matching_lines:
                                        results.append({
                                            'container': container_name,
                                            'matches': matching_lines
                                        })
                        
                        except Exception as e:
                            st.error(f"Error searching {container_name}: {str(e)}")
                
                # Display results
                if results:
                    st.success(f"Found matches in {len(results)} container(s)")
                    
                    for result in results:
                        with st.expander(f"📦 {result['container']} ({len(result['matches'])} matches)"):
                            st.markdown(f"**Container:** `{result['container']}`")
                            st.markdown(f"**Matches:** {len(result['matches'])}")
                            
                            # Show matches
                            for line_num, line in result['matches'][:50]:  # Limit to 50 matches
                                st.text(f"Line {line_num}: {line}")
                            
                            if len(result['matches']) > 50:
                                st.info(f"Showing first 50 of {len(result['matches'])} matches")
                else:
                    st.info(f"No matches found for '{search_term}' in selected containers.")
        
        else:
            st.error(f"Failed to fetch containers: {response.status_code}")
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to API at {api_base_url}")
    except Exception as e:
        st.error(f"Error: {str(e)}")

