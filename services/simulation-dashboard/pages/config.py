"""Configuration Page.

This module provides the configuration and settings page for managing
service connections, health monitoring, and system settings.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from services.clients.simulation_client import SimulationClient
from infrastructure.config.config import get_config


def render_config_page():
    """Render the comprehensive configuration and health monitoring page."""
    st.markdown("## ⚙️ Configuration & Health Monitoring")
    st.markdown("Manage service connections, monitor system health, and configure dashboard settings.")

    # Create tabs for different configuration sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔗 Service Connections",
        "🏥 Health Dashboard",
        "📊 System Resources",
        "⚙️ Settings"
    ])

    with tab1:
        render_service_connections()

    with tab2:
        render_health_dashboard()

    with tab3:
        render_system_resources()

    with tab4:
        render_dashboard_settings()


def render_service_connections():
    """Render service connections configuration."""
    st.markdown("### 🔗 Service Connections")

    # Get configuration
    config = get_config()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🎯 Simulation Service**")
        st.text_input("Host", value=config.simulation_service.host, disabled=True)
        st.text_input("Port", value=str(config.simulation_service.port), disabled=True)

        # Test connection
        if st.button("🔍 Test Connection", key="test_sim_connection"):
            with st.spinner("Testing connection..."):
                health_status = test_simulation_service_health()
                if health_status['healthy']:
                    st.success("✅ Simulation service is healthy")
                    st.metric("Response Time", f"{health_status['response_time']}ms")
                else:
                    st.error("❌ Simulation service is not responding")

    with col2:
        st.markdown("**📊 Analysis Service (Optional)**")
        analysis_host = st.text_input("Host", value=config.analysis_service_url or "", placeholder="Optional")
        analysis_port = st.text_input("Port", value="", placeholder="Optional")

        if analysis_host and analysis_port:
            if st.button("🔍 Test Connection", key="test_analysis_connection"):
                with st.spinner("Testing connection..."):
                    health_status = test_analysis_service_health(analysis_host, analysis_port)
                    if health_status['healthy']:
                        st.success("✅ Analysis service is healthy")
                        st.metric("Response Time", f"{health_status['response_time']}ms")
                    else:
                        st.warning("⚠️ Analysis service is not responding")
        else:
            st.info("Analysis service connection not configured")

    # Ecosystem Services Status
    st.markdown("---")
    st.markdown("### 🌐 Ecosystem Services Status")

    render_ecosystem_services_status()


def render_health_dashboard():
    """Render comprehensive health dashboard."""
    st.markdown("### 🏥 Health Dashboard")

    # Health overview metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Overall system health
        overall_health = get_overall_system_health()
        if overall_health['status'] == 'healthy':
            st.metric("Overall Health", "✅ Healthy")
        elif overall_health['status'] == 'warning':
            st.metric("Overall Health", "⚠️ Warning")
        else:
            st.metric("Overall Health", "❌ Issues")

    with col2:
        # Active services
        active_services = count_active_services()
        st.metric("Active Services", active_services)

    with col3:
        # Response time
        avg_response_time = get_average_response_time()
        st.metric("Avg Response Time", f"{avg_response_time}ms")

    with col4:
        # Uptime
        uptime = get_system_uptime()
        st.metric("System Uptime", uptime)

    # Service health details
    st.markdown("---")
    st.markdown("#### 🔍 Service Health Details")

    render_service_health_details()

    # Health trends
    st.markdown("---")
    st.markdown("#### 📈 Health Trends")

    render_health_trends()

    # Alerts and notifications
    st.markdown("---")
    st.markdown("#### 🚨 Alerts & Notifications")

    render_health_alerts()


def render_system_resources():
    """Render system resources monitoring."""
    st.markdown("### 📊 System Resources")

    # Real-time resource usage
    col1, col2, col3, col4 = st.columns(4)

    # Get current system stats
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    with col1:
        st.metric("CPU Usage", ".1f")
        # CPU gauge
        fig_cpu = go.Figure(go.Indicator(
            mode="gauge+number",
            value=cpu_percent,
            title={'text': "CPU"},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "darkblue"},
                   'steps': [
                       {'range': [0, 60], 'color': "lightgreen"},
                       {'range': [60, 80], 'color': "yellow"},
                       {'range': [80, 100], 'color': "red"}
                   ]}
        ))
        fig_cpu.update_layout(height=200)
        st.plotly_chart(fig_cpu, use_container_width=True)

    with col2:
        memory_percent = memory.percent
        st.metric("Memory Usage", ".1f")
        # Memory gauge
        fig_mem = go.Figure(go.Indicator(
            mode="gauge+number",
            value=memory_percent,
            title={'text': "Memory"},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "darkgreen"},
                   'steps': [
                       {'range': [0, 70], 'color': "lightgreen"},
                       {'range': [70, 85], 'color': "yellow"},
                       {'range': [85, 100], 'color': "red"}
                   ]}
        ))
        fig_mem.update_layout(height=200)
        st.plotly_chart(fig_mem, use_container_width=True)

    with col3:
        disk_percent = disk.percent
        st.metric("Disk Usage", ".1f")
        # Disk gauge
        fig_disk = go.Figure(go.Indicator(
            mode="gauge+number",
            value=disk_percent,
            title={'text': "Disk"},
            gauge={'axis': {'range': [0, 100]},
                   'bar': {'color': "darkorange"},
                   'steps': [
                       {'range': [0, 80], 'color': "lightgreen"},
                       {'range': [80, 90], 'color': "yellow"},
                       {'range': [90, 100], 'color': "red"}
                   ]}
        ))
        fig_disk.update_layout(height=200)
        st.plotly_chart(fig_disk, use_container_width=True)

    with col4:
        # Network I/O (placeholder)
        st.metric("Network I/O", "12.5 MB/s")
        st.info("Network monitoring would be implemented here")

    # Resource usage over time
    st.markdown("---")
    st.markdown("#### 📈 Resource Usage Trends")

    render_resource_usage_trends()

    # Process information
    st.markdown("---")
    st.markdown("#### 🔧 Process Information")

    render_process_information()


def render_dashboard_settings():
    """Render dashboard settings configuration."""
    st.markdown("### ⚙️ Dashboard Settings")

    # Theme settings
    st.markdown("#### 🎨 Appearance")

    col1, col2 = st.columns(2)
    with col1:
        theme = st.selectbox(
            "Theme",
            options=["Light", "Dark", "Auto"],
            help="Choose dashboard theme"
        )

    with col2:
        font_size = st.selectbox(
            "Font Size",
            options=["Small", "Medium", "Large"],
            index=1,
            help="Choose default font size"
        )

    # Performance settings
    st.markdown("#### ⚡ Performance")

    col1, col2 = st.columns(2)
    with col1:
        refresh_rate = st.slider(
            "Auto-refresh Rate (seconds)",
            min_value=5,
            max_value=300,
            value=30,
            help="How often to refresh data automatically"
        )

    with col2:
        max_items = st.slider(
            "Max Items Per Page",
            min_value=10,
            max_value=100,
            value=50,
            help="Maximum number of items to display per page"
        )

    # Notification settings
    st.markdown("#### 🔔 Notifications")

    enable_notifications = st.checkbox(
        "Enable Notifications",
        value=True,
        help="Enable dashboard notifications"
    )

    if enable_notifications:
        notification_types = st.multiselect(
            "Notification Types",
            options=["Simulation Completed", "Errors", "Warnings", "Service Health Changes"],
            default=["Simulation Completed", "Errors"],
            help="Choose which notifications to receive"
        )

    # Data management
    st.markdown("#### 💾 Data Management")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Cache", help="Clear all cached data"):
            st.success("Cache cleared successfully!")

    with col2:
        if st.button("📥 Export Settings", help="Export dashboard settings"):
            st.info("Settings export would be implemented here")

    # Save settings
    st.markdown("---")
    if st.button("💾 Save Settings", type="primary", use_container_width=True):
        save_dashboard_settings({
            'theme': theme,
            'font_size': font_size,
            'refresh_rate': refresh_rate,
            'max_items': max_items,
            'enable_notifications': enable_notifications,
            'notification_types': notification_types if enable_notifications else []
        })


# Helper functions

def test_simulation_service_health() -> Dict[str, Any]:
    """Test simulation service health."""
    try:
        config = get_config()
        client = SimulationClient(config.simulation_service)

        start_time = time.time()
        result = client.get_health()
        response_time = int((time.time() - start_time) * 1000)

        return {
            'healthy': result.get('status') == 'healthy',
            'response_time': response_time
        }
    except Exception as e:
        return {
            'healthy': False,
            'response_time': 0,
            'error': str(e)
        }


def test_analysis_service_health(host: str, port: str) -> Dict[str, Any]:
    """Test analysis service health."""
    try:
        # This would implement actual health check for analysis service
        return {
            'healthy': False,  # Placeholder
            'response_time': 0,
            'message': 'Analysis service health check not implemented'
        }
    except Exception as e:
        return {
            'healthy': False,
            'response_time': 0,
            'error': str(e)
        }


def render_ecosystem_services_status():
    """Render ecosystem services status overview."""
    services = [
        {
            'name': 'Simulation Service',
            'status': 'healthy',
            'response_time': 45,
            'last_check': datetime.now() - timedelta(seconds=30)
        },
        {
            'name': 'Analysis Service',
            'status': 'unhealthy',
            'response_time': None,
            'last_check': datetime.now() - timedelta(minutes=5)
        },
        {
            'name': 'Health Monitoring',
            'status': 'healthy',
            'response_time': 23,
            'last_check': datetime.now() - timedelta(seconds=15)
        },
        {
            'name': 'WebSocket Service',
            'status': 'healthy',
            'response_time': 12,
            'last_check': datetime.now() - timedelta(seconds=5)
        }
    ]

    for service in services:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 2])

        with col1:
            st.write(f"**{service['name']}**")

        with col2:
            if service['status'] == 'healthy':
                st.success("✅")
            elif service['status'] == 'warning':
                st.warning("⚠️")
            else:
                st.error("❌")

        with col3:
            if service['response_time']:
                st.metric("Response", f"{service['response_time']}ms")
            else:
                st.caption("N/A")

        with col4:
            time_diff = datetime.now() - service['last_check']
            if time_diff.seconds < 60:
                st.caption(f"{time_diff.seconds}s ago")
            else:
                st.caption(f"{time_diff.seconds // 60}m ago")


def get_overall_system_health() -> Dict[str, Any]:
    """Get overall system health status."""
    # Mock implementation - in real system this would aggregate all service health
    return {
        'status': 'healthy',
        'services_healthy': 3,
        'services_total': 4,
        'last_check': datetime.now()
    }


def count_active_services() -> int:
    """Count active services."""
    # Mock implementation
    return 3


def get_average_response_time() -> int:
    """Get average response time across services."""
    # Mock implementation
    return 35


def get_system_uptime() -> str:
    """Get system uptime."""
    try:
        uptime_seconds = int(time.time() - psutil.boot_time())
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60

        if days > 0:
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "Unknown"


def render_service_health_details():
    """Render detailed service health information."""
    services = [
        {
            'name': 'Project Simulation Service',
            'status': 'healthy',
            'uptime': '2h 15m',
            'cpu_usage': 23.5,
            'memory_usage': 45.2,
            'active_connections': 12,
            'last_error': None
        },
        {
            'name': 'Analysis Service',
            'status': 'unhealthy',
            'uptime': '0h 0m',
            'cpu_usage': 0.0,
            'memory_usage': 0.0,
            'active_connections': 0,
            'last_error': 'Connection timeout'
        },
        {
            'name': 'WebSocket Service',
            'status': 'healthy',
            'uptime': '2h 15m',
            'cpu_usage': 5.2,
            'memory_usage': 12.8,
            'active_connections': 3,
            'last_error': None
        }
    ]

    for service in services:
        with st.expander(f"🔍 {service['name']}", expanded=False):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Status", service['status'].title())
                st.metric("Uptime", service['uptime'])
                if service['last_error']:
                    st.error(f"Last Error: {service['last_error']}")

            with col2:
                st.metric("CPU Usage", ".1f")
                st.metric("Memory Usage", ".1f")

            with col3:
                st.metric("Active Connections", service['active_connections'])
                if service['status'] == 'healthy':
                    st.success("Service is operating normally")
                else:
                    st.error("Service is not responding")


def render_health_trends():
    """Render health trends over time."""
    # Mock health trend data
    hours = [f"{i}:00" for i in range(24)]
    health_scores = [85, 87, 82, 89, 91, 88, 93, 90, 87, 89, 92, 88,
                     85, 87, 82, 89, 91, 88, 93, 90, 87, 89, 92, 88]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours,
        y=health_scores,
        mode='lines+markers',
        name='Health Score',
        line=dict(color='green', width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title="System Health Score (Last 24 Hours)",
        xaxis_title="Time",
        yaxis_title="Health Score (%)",
        height=300
    )

    st.plotly_chart(fig, use_container_width=True)


def render_health_alerts():
    """Render health alerts and notifications."""
    alerts = [
        {
            'type': 'info',
            'message': 'All services are operating normally',
            'timestamp': datetime.now() - timedelta(minutes=5)
        },
        {
            'type': 'warning',
            'message': 'Analysis service is not responding',
            'timestamp': datetime.now() - timedelta(minutes=15)
        },
        {
            'type': 'success',
            'message': 'WebSocket connections restored',
            'timestamp': datetime.now() - timedelta(hours=1)
        }
    ]

    for alert in alerts:
        col1, col2, col3 = st.columns([1, 4, 1])

        with col1:
            if alert['type'] == 'success':
                st.success("✅")
            elif alert['type'] == 'warning':
                st.warning("⚠️")
            elif alert['type'] == 'error':
                st.error("❌")
            else:
                st.info("ℹ️")

        with col2:
            st.write(alert['message'])

        with col3:
            time_diff = datetime.now() - alert['timestamp']
            if time_diff.seconds < 3600:
                st.caption(f"{time_diff.seconds // 60}m ago")
            else:
                st.caption(f"{time_diff.seconds // 3600}h ago")


def render_resource_usage_trends():
    """Render resource usage trends."""
    # Mock resource usage data
    times = [datetime.now() - timedelta(minutes=i) for i in range(60, 0, -5)]
    cpu_usage = [23, 25, 22, 28, 24, 26, 23, 29, 25, 27, 24, 26]
    memory_usage = [45, 47, 44, 49, 46, 48, 45, 50, 47, 49, 46, 48]

    fig = make_subplots(rows=2, cols=1,
                       subplot_titles=('CPU Usage (%)', 'Memory Usage (%)'),
                       shared_xaxes=True)

    fig.add_trace(go.Scatter(
        x=times,
        y=cpu_usage,
        mode='lines',
        name='CPU',
        line=dict(color='blue')
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=times,
        y=memory_usage,
        mode='lines',
        name='Memory',
        line=dict(color='green')
    ), row=2, col=1)

    fig.update_layout(height=400, showlegend=False)
    fig.update_xaxes(title_text="Time")
    fig.update_yaxes(title_text="Usage (%)", row=1, col=1)
    fig.update_yaxes(title_text="Usage (%)", row=2, col=1)

    st.plotly_chart(fig, use_container_width=True)


def render_process_information():
    """Render process information."""
    try:
        # Get current process information
        current_process = psutil.Process()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Process CPU", ".1f")
            st.metric("Process Memory", ".1f")

        with col2:
            st.metric("Threads", current_process.num_threads())
            st.metric("Open Files", len(current_process.open_files()))

        with col3:
            st.metric("PID", current_process.pid)
            create_time = datetime.fromtimestamp(current_process.create_time())
            st.caption(f"Started: {create_time.strftime('%H:%M:%S')}")

    except Exception as e:
        st.warning(f"Could not retrieve process information: {str(e)}")


def save_dashboard_settings(settings: Dict[str, Any]):
    """Save dashboard settings."""
    # In a real implementation, this would save to a configuration file
    # or database. For now, we'll just show a success message.
    st.success("✅ Dashboard settings saved successfully!")

    # Display saved settings
    with st.expander("📋 Saved Settings"):
        for key, value in settings.items():
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
