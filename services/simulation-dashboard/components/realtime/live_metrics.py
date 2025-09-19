"""Live Metrics Component.

This module provides real-time monitoring and display of system metrics,
with automatic updates and alerting capabilities.
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import asyncio
import threading
from queue import Queue
import json


def render_live_metrics(
    metrics_data: List[Dict[str, Any]],
    title: str = "📊 Live Metrics Dashboard",
    update_interval: int = 5,
    enable_alerts: bool = True,
    alert_thresholds: Optional[Dict[str, float]] = None,
    on_metric_update: Optional[Callable] = None,
    max_history_points: int = 50
) -> Dict[str, Any]:
    """Render a live metrics dashboard with real-time updates.

    Args:
        metrics_data: Initial metrics data
        title: Dashboard title
        update_interval: Update interval in seconds
        enable_alerts: Whether to enable alerting
        alert_thresholds: Custom alert thresholds
        on_metric_update: Callback for metric updates
        max_history_points: Maximum history points to keep

    Returns:
        Dictionary with current metrics and alert status
    """
    st.markdown(f"### {title}")

    # Initialize session state for live metrics
    if 'live_metrics_data' not in st.session_state:
        st.session_state.live_metrics_data = metrics_data.copy() if metrics_data else []
    if 'metrics_history' not in st.session_state:
        st.session_state.metrics_history = {}
    if 'alerts_queue' not in st.session_state:
        st.session_state.alerts_queue = []
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now()

    # Auto-refresh mechanism
    if st.button("🔄 Refresh Now", key="refresh_live_metrics"):
        update_live_metrics()
        st.rerun()

    # Update interval control
    col_interval, col_status, col_alerts = st.columns([1, 2, 1])

    with col_interval:
        auto_update = st.checkbox("Auto Update", value=True, key="auto_update_metrics")
        current_interval = st.slider(
            "Update Interval (sec)",
            min_value=1,
            max_value=30,
            value=update_interval,
            key="update_interval",
            disabled=not auto_update
        )

    with col_status:
        last_update = st.session_state.get('last_update', datetime.now())
        time_since_update = (datetime.now() - last_update).seconds

        if time_since_update < 10:
            st.success(f"✅ Updated {time_since_update}s ago")
        elif time_since_update < 30:
            st.warning(f"⚠️ Updated {time_since_update}s ago")
        else:
            st.error(f"❌ Last update {time_since_update}s ago")

    with col_alerts:
        alerts_count = len(st.session_state.get('alerts_queue', []))
        if alerts_count > 0:
            st.error(f"🚨 {alerts_count} alerts")
        else:
            st.success("✅ All good")

    # Auto-update mechanism
    if auto_update:
        # Use Streamlit's session state to track time
        current_time = datetime.now()

        if 'last_auto_update' not in st.session_state:
            st.session_state.last_auto_update = current_time

        time_diff = (current_time - st.session_state.last_auto_update).seconds

        if time_diff >= current_interval:
            update_live_metrics()
            st.session_state.last_auto_update = current_time

            # Force refresh every update interval
            if time_diff >= current_interval:
                time.sleep(0.1)  # Small delay to prevent rapid updates
                st.rerun()

    # Display metrics in organized layout
    display_live_metrics_dashboard()

    # Handle alerts
    if enable_alerts:
        display_alerts_section(alert_thresholds)

    # Performance summary
    display_metrics_summary()

    return {
        'current_metrics': st.session_state.get('live_metrics_data', []),
        'alerts': st.session_state.get('alerts_queue', []),
        'last_update': st.session_state.get('last_update', datetime.now()),
        'history': st.session_state.get('metrics_history', {})
    }


def display_live_metrics_dashboard():
    """Display the main live metrics dashboard."""
    metrics_data = st.session_state.get('live_metrics_data', [])

    if not metrics_data:
        st.info("No metrics data available. Waiting for data stream...")
        return

    # Group metrics by category
    metric_categories = {}
    for metric in metrics_data:
        category = metric.get('category', 'General')
        if category not in metric_categories:
            metric_categories[category] = []
        metric_categories[category].append(metric)

    # Display metrics by category
    for category, category_metrics in metric_categories.items():
        with st.expander(f"📈 {category} Metrics ({len(category_metrics)})", expanded=True):
            display_category_metrics(category_metrics)


def display_category_metrics(metrics: List[Dict[str, Any]]):
    """Display metrics for a specific category."""
    # Create metric cards
    cols = st.columns(min(3, len(metrics)))

    for i, metric in enumerate(metrics):
        col_idx = i % 3
        if col_idx == 0 and i > 0:
            cols = st.columns(min(3, len(metrics) - i))

        with cols[col_idx]:
            display_metric_card(metric)


def display_metric_card(metric: Dict[str, Any]):
    """Display a single metric card."""
    name = metric.get('name', 'Unknown')
    value = metric.get('value', 0)
    unit = metric.get('unit', '')
    status = metric.get('status', 'normal')
    threshold = metric.get('threshold')

    # Status-based styling
    if status == 'critical':
        color = '🔴'
        bg_color = '#ffcccc'
    elif status == 'warning':
        color = '🟡'
        bg_color = '#fff3cd'
    else:
        color = '🟢'
        bg_color = '#d4edda'

    # Create metric display
    st.markdown(f"""
    <div style="border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 5px 0; background-color: {bg_color};">
        <h4 style="margin: 0; color: #333;">{color} {name}</h4>
        <h2 style="margin: 5px 0; color: #0066cc;">{value:.2f} {unit}</h2>
    """, unsafe_allow_html=True)

    # Show threshold information
    if threshold is not None:
        threshold_status = "Above" if value > threshold else "Below"
        st.caption(f"Threshold: {threshold:.2f} {unit} ({threshold_status})")

    # Trend indicator
    history = st.session_state.get('metrics_history', {}).get(name, [])
    if len(history) > 1:
        prev_value = history[-2]['value'] if len(history) > 1 else value
        trend = ((value - prev_value) / prev_value) * 100 if prev_value != 0 else 0

        if trend > 5:
            trend_icon = "📈"
            trend_color = "green"
        elif trend < -5:
            trend_icon = "📉"
            trend_color = "red"
        else:
            trend_icon = "➡️"
            trend_color = "gray"

        st.markdown(f"<span style='color: {trend_color};'>{trend_icon} {trend:+.1f}%</span>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Mini chart for recent history
    metric_history = st.session_state.get('metrics_history', {}).get(name, [])
    if len(metric_history) > 5:
        recent_values = [h['value'] for h in metric_history[-10:]]
        st.line_chart(recent_values, height=100)


def display_alerts_section(thresholds: Optional[Dict[str, float]]):
    """Display the alerts section."""
    alerts = st.session_state.get('alerts_queue', [])

    if not alerts:
        st.success("✅ No active alerts")
        return

    st.markdown("#### 🚨 Active Alerts")

    # Display alerts in reverse chronological order (newest first)
    for alert in reversed(alerts[-10:]):  # Show last 10 alerts
        severity = alert.get('severity', 'info')
        timestamp = alert.get('timestamp', datetime.now())

        if severity == 'critical':
            st.error(f"🚨 {alert['message']} ({timestamp.strftime('%H:%M:%S')})")
        elif severity == 'warning':
            st.warning(f"⚠️ {alert['message']} ({timestamp.strftime('%H:%M:%S')})")
        else:
            st.info(f"ℹ️ {alert['message']} ({timestamp.strftime('%H:%M:%S')})")

    # Alert controls
    col_clear, col_export = st.columns(2)

    with col_clear:
        if st.button("🗑️ Clear All Alerts", key="clear_alerts"):
            st.session_state.alerts_queue = []
            st.success("✅ Alerts cleared")

    with col_export:
        if st.button("📥 Export Alerts", key="export_alerts"):
            alerts_df = pd.DataFrame(alerts)
            csv_data = alerts_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="alerts.csv",
                mime='text/csv',
                key="download_alerts_csv"
            )


def display_metrics_summary():
    """Display a summary of all metrics."""
    metrics_data = st.session_state.get('live_metrics_data', [])

    if not metrics_data:
        return

    st.markdown("#### 📊 Metrics Summary")

    # Calculate summary statistics
    df = pd.DataFrame(metrics_data)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_metrics = len(df)
        st.metric("Total Metrics", total_metrics)

    with col2:
        healthy_count = len(df[df['status'] == 'normal'])
        st.metric("Healthy", healthy_count)

    with col3:
        warning_count = len(df[df['status'] == 'warning'])
        st.metric("Warning", warning_count)

    with col4:
        critical_count = len(df[df['status'] == 'critical'])
        st.metric("Critical", critical_count)

    # Health score
    if total_metrics > 0:
        health_score = ((healthy_count * 1.0 + warning_count * 0.5) / total_metrics) * 100

        if health_score >= 90:
            st.success(f"🎉 System Health: {health_score:.1f}%")
        elif health_score >= 75:
            st.warning(f"⚠️ System Health: {health_score:.1f}%")
        else:
            st.error(f"🚨 System Health: {health_score:.1f}%")


def update_live_metrics():
    """Update live metrics with new data."""
    # This would typically fetch data from the simulation service
    # For now, we'll simulate updates

    current_metrics = st.session_state.get('live_metrics_data', [])

    if not current_metrics:
        # Initialize with sample data if empty
        current_metrics = generate_sample_live_metrics()

    # Update existing metrics with slight variations
    for metric in current_metrics:
        name = metric['name']

        # Store history
        if name not in st.session_state.metrics_history:
            st.session_state.metrics_history[name] = []

        # Add current value to history
        history_entry = {
            'timestamp': datetime.now(),
            'value': metric['value']
        }
        st.session_state.metrics_history[name].append(history_entry)

        # Keep only recent history
        max_history = 50
        if len(st.session_state.metrics_history[name]) > max_history:
            st.session_state.metrics_history[name] = st.session_state.metrics_history[name][-max_history:]

        # Simulate value changes
        if 'CPU' in name:
            metric['value'] = max(0, min(100, metric['value'] + np.random.normal(0, 2)))
        elif 'Memory' in name:
            metric['value'] = max(0, min(100, metric['value'] + np.random.normal(0, 1)))
        elif 'Response' in name:
            metric['value'] = max(10, min(2000, metric['value'] + np.random.normal(0, 20)))
        elif 'Error' in name:
            metric['value'] = max(0, min(10, metric['value'] + np.random.normal(0, 0.1)))
        elif 'Throughput' in name:
            metric['value'] = max(50, min(2000, metric['value'] + np.random.normal(0, 10)))

        # Update status based on value and threshold
        threshold = metric.get('threshold')
        if threshold is not None:
            if metric['value'] > threshold * 1.5:
                metric['status'] = 'critical'
            elif metric['value'] > threshold:
                metric['status'] = 'warning'
            else:
                metric['status'] = 'normal'

        # Check for alerts
        check_metric_alerts(metric)

    st.session_state.live_metrics_data = current_metrics
    st.session_state.last_update = datetime.now()


def check_metric_alerts(metric: Dict[str, Any]):
    """Check for metric alerts and add to queue."""
    name = metric['name']
    value = metric['value']
    threshold = metric.get('threshold')
    status = metric['status']

    alerts_queue = st.session_state.get('alerts_queue', [])

    # Critical alerts
    if status == 'critical':
        alert = {
            'severity': 'critical',
            'message': f"{name} is critically high: {value:.2f}",
            'timestamp': datetime.now(),
            'metric': name,
            'value': value
        }
        alerts_queue.append(alert)

    # Warning alerts
    elif status == 'warning':
        alert = {
            'severity': 'warning',
            'message': f"{name} exceeds threshold: {value:.2f}",
            'timestamp': datetime.now(),
            'metric': name,
            'value': value
        }
        alerts_queue.append(alert)

    # Keep only recent alerts (last 50)
    if len(alerts_queue) > 50:
        alerts_queue = alerts_queue[-50:]

    st.session_state.alerts_queue = alerts_queue


def generate_sample_live_metrics() -> List[Dict[str, Any]]:
    """Generate sample live metrics for demonstration."""
    return [
        {
            'name': 'CPU Utilization',
            'value': 65.5,
            'unit': '%',
            'category': 'System',
            'status': 'normal',
            'threshold': 80
        },
        {
            'name': 'Memory Usage',
            'value': 72.3,
            'unit': '%',
            'category': 'System',
            'status': 'warning',
            'threshold': 70
        },
        {
            'name': 'Response Time',
            'value': 245.8,
            'unit': 'ms',
            'category': 'Performance',
            'status': 'normal',
            'threshold': 500
        },
        {
            'name': 'Error Rate',
            'value': 0.05,
            'unit': '%',
            'category': 'Performance',
            'status': 'normal',
            'threshold': 0.1
        },
        {
            'name': 'Throughput',
            'value': 1250.0,
            'unit': 'req/s',
            'category': 'Performance',
            'status': 'normal',
            'threshold': 1000
        },
        {
            'name': 'Active Users',
            'value': 1250.0,
            'unit': 'users',
            'category': 'Business',
            'status': 'normal',
            'threshold': 2000
        }
    ]


# WebSocket simulation for real-time updates
class MetricsWebSocketSimulator:
    """Simulate WebSocket connections for real-time metrics updates."""

    def __init__(self):
        self.connected = False
        self.update_queue = Queue()

    def connect(self):
        """Simulate WebSocket connection."""
        self.connected = True
        # Start background update thread
        update_thread = threading.Thread(target=self._background_updates)
        update_thread.daemon = True
        update_thread.start()

    def disconnect(self):
        """Disconnect WebSocket."""
        self.connected = False

    def _background_updates(self):
        """Background thread for simulating real-time updates."""
        while self.connected:
            try:
                # Simulate receiving updates
                update_data = self._generate_update()
                self.update_queue.put(update_data)
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                print(f"WebSocket simulation error: {e}")
                break

    def _generate_update(self) -> Dict[str, Any]:
        """Generate a simulated metric update."""
        metrics = ['CPU Utilization', 'Memory Usage', 'Response Time', 'Error Rate', 'Throughput']
        metric_name = np.random.choice(metrics)

        if 'CPU' in metric_name or 'Memory' in metric_name:
            value = np.random.uniform(40, 90)
        elif 'Response' in metric_name:
            value = np.random.uniform(100, 800)
        elif 'Error' in metric_name:
            value = np.random.uniform(0, 0.2)
        else:  # Throughput
            value = np.random.uniform(800, 1500)

        return {
            'metric': metric_name,
            'value': round(value, 2),
            'timestamp': datetime.now(),
            'source': 'websocket'
        }

    def get_updates(self) -> List[Dict[str, Any]]:
        """Get pending updates."""
        updates = []
        while not self.update_queue.empty():
            updates.append(self.update_queue.get())
        return updates


# Global WebSocket simulator instance
metrics_websocket = MetricsWebSocketSimulator()
