"""Status Dashboard Component.

This module provides real-time status monitoring and dashboard display
for system health, service status, and operational metrics.
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


def render_status_dashboard(
    status_data: Dict[str, Any],
    title: str = "🖥️ System Status Dashboard",
    enable_health_checks: bool = True,
    enable_alerts: bool = True,
    refresh_interval: int = 30,
    on_service_action: Optional[Callable] = None
) -> Dict[str, Any]:
    """Render a comprehensive system status dashboard.

    Args:
        status_data: System status data
        title: Dashboard title
        enable_health_checks: Whether to enable health checks
        enable_alerts: Whether to enable alerts
        refresh_interval: Auto-refresh interval in seconds
        on_service_action: Callback for service actions

    Returns:
        Dictionary with current system status
    """
    st.markdown(f"### {title}")

    # Initialize status data if not provided
    if not status_data:
        status_data = get_default_status_data()

    # Overall system health
    display_overall_health(status_data)

    # Service status grid
    display_service_status_grid(status_data, on_service_action)

    # System metrics overview
    display_system_metrics(status_data)

    # Alerts and notifications
    if enable_alerts:
        display_alerts_section(status_data)

    # Performance trends
    display_performance_trends(status_data)

    # System controls
    display_system_controls(status_data, on_service_action)

    # Simulate real-time updates
    simulate_status_updates(status_data)

    return {
        'overall_health': calculate_overall_health(status_data),
        'service_status': status_data.get('services', {}),
        'system_metrics': status_data.get('metrics', {}),
        'active_alerts': status_data.get('alerts', []),
        'last_update': datetime.now()
    }


def display_overall_health(status_data: Dict[str, Any]):
    """Display overall system health status."""
    services = status_data.get('services', {})
    alerts = status_data.get('alerts', [])

    # Calculate health metrics
    total_services = len(services)
    healthy_services = sum(1 for s in services.values() if s.get('status') == 'healthy')
    critical_services = sum(1 for s in services.values() if s.get('status') == 'critical')
    warning_services = sum(1 for s in services.values() if s.get('status') == 'warning')

    # Overall health score
    health_score = calculate_overall_health(status_data)

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        # Health score with color coding
        if health_score >= 90:
            st.metric("System Health", ".1f", delta="Excellent", delta_color="normal")
        elif health_score >= 75:
            st.metric("System Health", ".1f", delta="Good", delta_color="normal")
        elif health_score >= 60:
            st.metric("System Health", ".1f", delta="Fair", delta_color="inverse")
        else:
            st.metric("System Health", ".1f", delta="Poor", delta_color="inverse")

    with col2:
        st.metric("Total Services", total_services)

    with col3:
        st.metric("Healthy", healthy_services)

    with col4:
        st.metric("Warnings", warning_services)

    with col5:
        st.metric("Critical", critical_services)

    # Health status indicator
    if health_score >= 90:
        st.success("✅ System operating normally")
    elif health_score >= 75:
        st.warning("⚠️ System experiencing minor issues")
    elif health_score >= 60:
        st.error("🚨 System requires attention")
    else:
        st.error("🚨 Critical system issues detected")


def display_service_status_grid(status_data: Dict[str, Any], on_service_action: Optional[Callable]):
    """Display service status in a grid layout."""
    services = status_data.get('services', {})

    if not services:
        st.info("No services configured for monitoring.")
        return

    st.markdown("#### 🔧 Service Status")

    # Create service cards
    cols = st.columns(min(3, len(services)))

    for i, (service_name, service_info) in enumerate(services.items()):
        col_idx = i % 3
        if col_idx == 0 and i > 0:
            cols = st.columns(min(3, len(services) - i))

        with cols[col_idx]:
            display_service_card(service_name, service_info, on_service_action)


def display_service_card(service_name: str, service_info: Dict[str, Any], on_service_action: Optional[Callable]):
    """Display a single service status card."""
    status = service_info.get('status', 'unknown')
    uptime = service_info.get('uptime', 0)
    response_time = service_info.get('response_time', 0)
    version = service_info.get('version', 'N/A')

    # Status-based styling
    if status == 'healthy':
        icon = "🟢"
        bg_color = "#d4edda"
        border_color = "#28a745"
    elif status == 'warning':
        icon = "🟡"
        bg_color = "#fff3cd"
        border_color = "#ffc107"
    elif status == 'critical':
        icon = "🔴"
        bg_color = "#f8d7da"
        border_color = "#dc3545"
    else:
        icon = "⚪"
        bg_color = "#e2e3e5"
        border_color = "#6c757d"

    # Service card
    st.markdown(f"""
    <div style="border: 2px solid {border_color}; border-radius: 10px; padding: 15px; margin: 10px 0; background-color: {bg_color};">
        <h4 style="margin: 0; color: #333;">{icon} {service_name}</h4>
        <p style="margin: 5px 0; font-size: 14px;">Status: {status.title()}</p>
        <p style="margin: 5px 0; font-size: 12px;">Uptime: {format_uptime(uptime)}</p>
        <p style="margin: 5px 0; font-size: 12px;">Response: {response_time:.0f}ms</p>
        <p style="margin: 5px 0; font-size: 12px;">Version: {version}</p>
    </div>
    """, unsafe_allow_html=True)

    # Service actions
    if on_service_action:
        action_col1, action_col2 = st.columns(2)

        with action_col1:
            if status == 'critical':
                if st.button("🔄 Restart", key=f"restart_{service_name}"):
                    on_service_action(service_name, 'restart')
                    st.info(f"🔄 Restarting {service_name}...")

        with action_col2:
            if st.button("📊 Details", key=f"details_{service_name}"):
                display_service_details(service_name, service_info)


def display_service_details(service_name: str, service_info: Dict[str, Any]):
    """Display detailed service information."""
    st.markdown(f"#### 🔍 {service_name} Details")

    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Status:** {service_info.get('status', 'unknown').title()}")
        st.write(f"**Version:** {service_info.get('version', 'N/A')}")
        st.write(f"**Uptime:** {format_uptime(service_info.get('uptime', 0))}")
        st.write(f"**Start Time:** {service_info.get('start_time', 'N/A')}")

    with col2:
        st.write(f"**Response Time:** {service_info.get('response_time', 0):.0f}ms")
        st.write(f"**CPU Usage:** {service_info.get('cpu_usage', 0):.1f}%")
        st.write(f"**Memory Usage:** {service_info.get('memory_usage', 0):.1f}%")
        st.write(f"**Active Connections:** {service_info.get('connections', 0)}")

    # Recent logs if available
    logs = service_info.get('recent_logs', [])
    if logs:
        st.markdown("**Recent Logs:**")
        for log in logs[-5:]:  # Show last 5 logs
            log_time = log.get('timestamp', datetime.now())
            log_level = log.get('level', 'INFO')
            log_message = log.get('message', '')

            if log_level == 'ERROR':
                st.error(f"{log_time.strftime('%H:%M:%S')} - {log_message}")
            elif log_level == 'WARNING':
                st.warning(f"{log_time.strftime('%H:%M:%S')} - {log_message}")
            else:
                st.info(f"{log_time.strftime('%H:%M:%S')} - {log_message}")


def display_system_metrics(status_data: Dict[str, Any]):
    """Display system-wide metrics."""
    metrics = status_data.get('metrics', {})

    if not metrics:
        return

    st.markdown("#### 📊 System Metrics")

    # Create metrics dashboard
    metric_cols = st.columns(min(4, len(metrics)))

    for i, (metric_name, metric_value) in enumerate(metrics.items()):
        col_idx = i % 4
        if col_idx == 0 and i > 0:
            metric_cols = st.columns(min(4, len(metrics) - i))

        with metric_cols[col_idx]:
            if isinstance(metric_value, (int, float)):
                # Add trend information if available
                trend = metrics.get(f"{metric_name}_trend")
                if trend:
                    st.metric(
                        metric_name.replace('_', ' ').title(),
                        ".2f",
                        delta=".2f" if isinstance(trend, (int, float)) else str(trend)
                    )
                else:
                    st.metric(metric_name.replace('_', ' ').title(), ".2f")
            else:
                st.metric(metric_name.replace('_', ' ').title(), str(metric_value))


def display_alerts_section(status_data: Dict[str, Any]):
    """Display active alerts and notifications."""
    alerts = status_data.get('alerts', [])

    if not alerts:
        st.success("✅ No active alerts")
        return

    st.markdown("#### 🚨 Active Alerts")

    # Group alerts by severity
    critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
    warning_alerts = [a for a in alerts if a.get('severity') == 'warning']
    info_alerts = [a for a in alerts if a.get('severity') == 'info']

    # Display critical alerts first
    for alert in critical_alerts:
        st.error(f"🚨 {alert.get('message', 'Unknown alert')}")

    for alert in warning_alerts:
        st.warning(f"⚠️ {alert.get('message', 'Unknown alert')}")

    for alert in info_alerts:
        st.info(f"ℹ️ {alert.get('message', 'Unknown alert')}")

    # Alert summary
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Critical", len(critical_alerts))

    with col2:
        st.metric("Warnings", len(warning_alerts))

    with col3:
        st.metric("Info", len(info_alerts))


def display_performance_trends(status_data: Dict[str, Any]):
    """Display performance trends over time."""
    trends = status_data.get('performance_trends', [])

    if not trends:
        return

    st.markdown("#### 📈 Performance Trends")

    # Convert trends to DataFrame for visualization
    trends_df = pd.DataFrame(trends)

    if not trends_df.empty and len(trends_df) > 1:
        # Create trend chart
        try:
            import plotly.graph_objects as go

            fig = go.Figure()

            # Add CPU trend
            if 'cpu_usage' in trends_df.columns:
                fig.add_trace(go.Scatter(
                    x=trends_df['timestamp'],
                    y=trends_df['cpu_usage'],
                    mode='lines',
                    name='CPU Usage (%)',
                    line=dict(color='blue')
                ))

            # Add Memory trend
            if 'memory_usage' in trends_df.columns:
                fig.add_trace(go.Scatter(
                    x=trends_df['timestamp'],
                    y=trends_df['memory_usage'],
                    mode='lines',
                    name='Memory Usage (%)',
                    line=dict(color='green')
                ))

            # Add Response Time trend
            if 'response_time' in trends_df.columns:
                fig.add_trace(go.Scatter(
                    x=trends_df['timestamp'],
                    y=trends_df['response_time'],
                    mode='lines',
                    name='Response Time (ms)',
                    line=dict(color='red'),
                    yaxis='y2'
                ))

            fig.update_layout(
                title="System Performance Trends",
                xaxis_title="Time",
                yaxis_title="Usage (%)",
                yaxis2=dict(
                    title="Response Time (ms)",
                    overlaying="y",
                    side="right"
                ),
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

        except ImportError:
            # Fallback to simple line chart
            if 'cpu_usage' in trends_df.columns:
                st.line_chart(trends_df.set_index('timestamp')['cpu_usage'])
    else:
        st.info("Insufficient trend data for visualization.")


def display_system_controls(status_data: Dict[str, Any], on_service_action: Optional[Callable]):
    """Display system control buttons."""
    st.markdown("#### 🎮 System Controls")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Refresh Status", key="refresh_status"):
            simulate_status_updates(status_data)
            st.success("✅ Status refreshed")
            st.rerun()

    with col2:
        if st.button("🩺 Health Check", key="health_check"):
            run_health_check(status_data)
            st.info("🩺 Health check completed")

    with col3:
        if st.button("📊 Generate Report", key="generate_report"):
            generate_status_report(status_data)
            st.success("📊 Report generated")

    with col4:
        if st.button("⚙️ System Settings", key="system_settings"):
            display_system_settings(status_data)


def simulate_status_updates(status_data: Dict[str, Any]):
    """Simulate real-time status updates."""
    services = status_data.get('services', {})
    metrics = status_data.get('metrics', {})

    # Update service metrics
    for service_name, service_info in services.items():
        # Simulate slight variations in metrics
        if 'response_time' in service_info:
            current_rt = service_info['response_time']
            variation = np.random.normal(0, 10)  # ±10ms variation
            service_info['response_time'] = max(0, current_rt + variation)

        if 'cpu_usage' in service_info:
            current_cpu = service_info['cpu_usage']
            variation = np.random.normal(0, 2)  # ±2% variation
            service_info['cpu_usage'] = max(0, min(100, current_cpu + variation))

        if 'memory_usage' in service_info:
            current_mem = service_info['memory_usage']
            variation = np.random.normal(0, 1)  # ±1% variation
            service_info['memory_usage'] = max(0, min(100, current_mem + variation))

    # Update system metrics
    for metric_name, metric_value in metrics.items():
        if isinstance(metric_value, (int, float)):
            variation = np.random.normal(0, metric_value * 0.05)  # ±5% variation
            metrics[metric_name] = max(0, metric_value + variation)

    # Update performance trends
    trends = status_data.get('performance_trends', [])
    if trends:
        latest_trend = trends[-1].copy()
        latest_trend['timestamp'] = datetime.now()

        # Add some variation to trend data
        for key, value in latest_trend.items():
            if isinstance(value, (int, float)) and key != 'timestamp':
                variation = np.random.normal(0, value * 0.02)  # ±2% variation
                latest_trend[key] = max(0, value + variation)

        trends.append(latest_trend)

        # Keep only recent trends (last 100 points)
        if len(trends) > 100:
            status_data['performance_trends'] = trends[-100:]


def run_health_check(status_data: Dict[str, Any]):
    """Run a health check on all services."""
    services = status_data.get('services', {})

    st.markdown("#### 🩺 Health Check Results")

    health_results = {}

    for service_name, service_info in services.items():
        # Simulate health check
        response_time = service_info.get('response_time', 0)
        cpu_usage = service_info.get('cpu_usage', 0)
        memory_usage = service_info.get('memory_usage', 0)

        # Health criteria
        is_healthy = (
            response_time < 1000 and  # Response time < 1s
            cpu_usage < 90 and        # CPU usage < 90%
            memory_usage < 90         # Memory usage < 90%
        )

        health_results[service_name] = {
            'healthy': is_healthy,
            'response_time': response_time,
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage
        }

    # Display results
    for service_name, result in health_results.items():
        if result['healthy']:
            st.success(f"✅ {service_name}: Healthy")
        else:
            st.error(f"❌ {service_name}: Unhealthy")
            st.write(f"   Response: {result['response_time']:.0f}ms, CPU: {result['cpu_usage']:.1f}%, Memory: {result['memory_usage']:.1f}%")


def generate_status_report(status_data: Dict[str, Any]):
    """Generate a system status report."""
    report_data = {
        'timestamp': datetime.now(),
        'overall_health': calculate_overall_health(status_data),
        'services': status_data.get('services', {}),
        'metrics': status_data.get('metrics', {}),
        'alerts': status_data.get('alerts', [])
    }

    # Convert to JSON for download
    import json
    report_json = json.dumps(report_data, default=str, indent=2)

    st.download_button(
        label="Download Status Report",
        data=report_json,
        file_name=f"system_status_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime='application/json',
        key="download_status_report"
    )


def display_system_settings(status_data: Dict[str, Any]):
    """Display system settings panel."""
    st.markdown("#### ⚙️ System Settings")

    with st.expander("Monitoring Settings", expanded=True):
        st.slider("Health Check Interval", 30, 300, 60, key="health_check_interval")
        st.slider("Alert Threshold", 50, 95, 80, key="alert_threshold")
        st.checkbox("Enable Email Notifications", value=True, key="email_notifications")
        st.checkbox("Enable SMS Alerts", value=False, key="sms_alerts")

    with st.expander("Performance Settings", expanded=False):
        st.slider("CPU Threshold (%)", 50, 95, 80, key="cpu_threshold")
        st.slider("Memory Threshold (%)", 50, 95, 85, key="memory_threshold")
        st.slider("Response Time Threshold (ms)", 500, 5000, 2000, key="response_threshold")


def calculate_overall_health(status_data: Dict[str, Any]) -> float:
    """Calculate overall system health score."""
    services = status_data.get('services', {})

    if not services:
        return 100.0

    total_score = 0
    service_count = len(services)

    for service_info in services.values():
        status = service_info.get('status', 'unknown')

        if status == 'healthy':
            score = 100
        elif status == 'warning':
            score = 75
        elif status == 'critical':
            score = 25
        else:
            score = 50

        total_score += score

    return total_score / service_count if service_count > 0 else 100.0


def format_uptime(seconds: float) -> str:
    """Format uptime in seconds to human-readable format."""
    if seconds < 60:
        return ".1f"
    elif seconds < 3600:
        return ".1f"
    elif seconds < 86400:
        return ".1f"
    else:
        return ".1f"


def get_default_status_data() -> Dict[str, Any]:
    """Get default status data for demonstration."""
    return {
        'services': {
            'simulation-engine': {
                'status': 'healthy',
                'version': '2.1.0',
                'uptime': 345600,  # 4 days
                'response_time': 145.8,
                'cpu_usage': 67.3,
                'memory_usage': 72.1,
                'connections': 25,
                'start_time': (datetime.now() - timedelta(days=4)).strftime('%Y-%m-%d %H:%M:%S')
            },
            'database': {
                'status': 'warning',
                'version': '13.4',
                'uptime': 259200,  # 3 days
                'response_time': 45.2,
                'cpu_usage': 45.8,
                'memory_usage': 78.9,
                'connections': 15,
                'start_time': (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S')
            },
            'api-gateway': {
                'status': 'healthy',
                'version': '1.8.2',
                'uptime': 604800,  # 7 days
                'response_time': 23.4,
                'cpu_usage': 34.2,
                'memory_usage': 56.7,
                'connections': 89,
                'start_time': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
            },
            'monitoring-service': {
                'status': 'critical',
                'version': '3.2.1',
                'uptime': 86400,  # 1 day
                'response_time': 1250.0,
                'cpu_usage': 89.5,
                'memory_usage': 91.2,
                'connections': 5,
                'start_time': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
            }
        },
        'metrics': {
            'total_requests': 15420,
            'active_users': 234,
            'error_rate': 0.05,
            'avg_response_time': 145.8,
            'cpu_usage': 67.3,
            'memory_usage': 72.1,
            'disk_usage': 45.6,
            'network_traffic': 1250.5
        },
        'alerts': [
            {
                'severity': 'critical',
                'message': 'Monitoring service response time exceeds 1000ms',
                'timestamp': datetime.now() - timedelta(minutes=15)
            },
            {
                'severity': 'warning',
                'message': 'Database memory usage above 75%',
                'timestamp': datetime.now() - timedelta(minutes=30)
            }
        ],
        'performance_trends': [
            {
                'timestamp': datetime.now() - timedelta(hours=2),
                'cpu_usage': 65.2,
                'memory_usage': 70.5,
                'response_time': 142.3
            },
            {
                'timestamp': datetime.now() - timedelta(hours=1),
                'cpu_usage': 67.8,
                'memory_usage': 72.1,
                'response_time': 148.7
            },
            {
                'timestamp': datetime.now(),
                'cpu_usage': 67.3,
                'memory_usage': 72.1,
                'response_time': 145.8
            }
        ]
    }
