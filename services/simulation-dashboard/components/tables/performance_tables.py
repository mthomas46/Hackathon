"""Performance Table Components.

This module provides table components for displaying performance metrics,
benchmarking results, and system monitoring data.
"""

import streamlit as st
from typing import Dict, Any, Optional, List, Callable
import pandas as pd
from datetime import datetime, timedelta
import numpy as np


def render_performance_table(
    performance_data: List[Dict[str, Any]],
    title: str = "📊 Performance Metrics",
    enable_benchmarking: bool = True,
    enable_trending: bool = True,
    on_threshold_set: Optional[Callable] = None,
    on_alert_config: Optional[Callable] = None
) -> Dict[str, Any]:
    """Render a comprehensive performance metrics table.

    Args:
        performance_data: List of performance metric dictionaries
        title: Table title
        enable_benchmarking: Whether to enable benchmarking features
        enable_trending: Whether to enable trend analysis
        on_threshold_set: Callback for setting thresholds
        on_alert_config: Callback for alert configuration

    Returns:
        Dictionary with performance metrics and analysis
    """
    st.markdown(f"### {title}")

    if not performance_data:
        st.info("No performance data available. Metrics will appear here as the system runs.")
        return {'performance_metrics': {}, 'alerts': []}

    # Convert to DataFrame
    df = pd.DataFrame(performance_data)

    # Ensure required columns exist
    required_columns = ['metric_name', 'value', 'unit', 'timestamp', 'threshold', 'status']
    for col in required_columns:
        if col not in df.columns:
            df[col] = 'N/A' if col in ['metric_name', 'unit'] else 0 if col in ['value', 'threshold'] else 'normal' if col == 'status' else datetime.now()

    # Add derived columns
    df['timestamp_display'] = pd.to_datetime(df['timestamp']).dt.strftime('%H:%M:%S')
    df['status_icon'] = df['status'].apply(get_performance_status_icon)
    df['value_display'] = df.apply(lambda row: f"{row['value']:.2f} {row['unit']}", axis=1)
    df['threshold_display'] = df.apply(lambda row: f"{row['threshold']:.2f} {row['unit']}" if pd.notna(row['threshold']) else 'N/A', axis=1)

    # Performance overview
    st.markdown("#### 📊 Performance Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_metrics = len(df['metric_name'].unique())
        st.metric("Active Metrics", total_metrics)

    with col2:
        healthy_count = len(df[df['status'] == 'normal'])
        st.metric("Normal", healthy_count)

    with col3:
        warning_count = len(df[df['status'] == 'warning'])
        st.metric("Warnings", warning_count)

    with col4:
        critical_count = len(df[df['status'] == 'critical'])
        st.metric("Critical", critical_count)

    # Performance status indicators
    if critical_count > 0 or warning_count > 0:
        st.markdown("#### 🚨 Performance Alerts")

        # Show critical alerts first
        critical_metrics = df[df['status'] == 'critical']
        if len(critical_metrics) > 0:
            st.error(f"🚨 {len(critical_metrics)} critical performance issues detected!")

        # Show warnings
        warning_metrics = df[df['status'] == 'warning']
        if len(warning_metrics) > 0:
            st.warning(f"⚠️ {len(warning_metrics)} performance warnings detected!")

    # Metric type filter
    metric_types = df['metric_name'].unique().tolist()
    selected_metrics = st.multiselect(
        "Filter Metrics",
        options=metric_types,
        default=metric_types[:5],  # Show first 5 by default
        key="performance_metric_filter"
    )

    filtered_df = df[df['metric_name'].isin(selected_metrics)] if selected_metrics else df

    # Main performance table
    st.markdown("#### 📋 Performance Metrics")

    # Group by metric name for better organization
    grouped_metrics = filtered_df.groupby('metric_name')

    for metric_name, metric_data in grouped_metrics:
        with st.expander(f"📊 {metric_name}", expanded=False):
            # Display metric details
            latest_data = metric_data.iloc[-1]  # Most recent data point

            col_info1, col_info2, col_info3 = st.columns(3)

            with col_info1:
                st.metric(
                    "Current Value",
                    latest_data['value_display'],
                    delta=get_performance_delta(metric_data)
                )

            with col_info2:
                if pd.notna(latest_data['threshold']):
                    threshold_status = "Above" if latest_data['value'] > latest_data['threshold'] else "Below"
                    st.metric("Threshold", latest_data['threshold_display'], threshold_status)
                else:
                    st.metric("Threshold", "Not Set")

            with col_info3:
                st.metric("Status", f"{latest_data['status_icon']} {latest_data['status'].title()}")

            # Metric trend chart
            if enable_trending and len(metric_data) > 1:
                st.markdown("**Trend (Last 10 data points):**")

                # Get last 10 data points
                recent_data = metric_data.tail(10).copy()
                recent_data['timestamp'] = pd.to_datetime(recent_data['timestamp'])

                try:
                    import plotly.graph_objects as go

                    fig = go.Figure()

                    # Add main metric line
                    fig.add_trace(go.Scatter(
                        x=recent_data['timestamp'],
                        y=recent_data['value'],
                        mode='lines+markers',
                        name='Value',
                        line=dict(color='blue')
                    ))

                    # Add threshold line if available
                    if pd.notna(recent_data['threshold'].iloc[0]):
                        threshold_val = recent_data['threshold'].iloc[0]
                        fig.add_trace(go.Scatter(
                            x=recent_data['timestamp'],
                            y=[threshold_val] * len(recent_data),
                            mode='lines',
                            name='Threshold',
                            line=dict(color='red', dash='dash')
                        ))

                    fig.update_layout(
                        title=f"{metric_name} Trend",
                        xaxis_title="Time",
                        yaxis_title=latest_data['unit'],
                        height=300
                    )

                    st.plotly_chart(fig, use_container_width=True)

                except ImportError:
                    # Fallback to Streamlit chart
                    st.line_chart(recent_data.set_index('timestamp')['value'])

            # Metric actions
            render_performance_metric_actions(
                metric_name, metric_data, on_threshold_set, on_alert_config
            )

    # Performance benchmarking
    if enable_benchmarking:
        st.markdown("#### 🏆 Performance Benchmarking")

        benchmark_results = calculate_performance_benchmarks(df)

        if benchmark_results:
            col_bench1, col_bench2, col_bench3 = st.columns(3)

            with col_bench1:
                st.metric("Avg Response Time", ".2f", benchmark_results.get('avg_response_time', 0))

            with col_bench2:
                st.metric("Throughput", ".2f", benchmark_results.get('throughput', 0))

            with col_bench3:
                st.metric("Error Rate", ".2f", benchmark_results.get('error_rate', 0))

            # Benchmark comparison
            st.markdown("**Benchmark Status:**")
            for metric, status in benchmark_results.get('benchmark_status', {}).items():
                if status == 'good':
                    st.success(f"✅ {metric}: Within acceptable range")
                elif status == 'warning':
                    st.warning(f"⚠️ {metric}: Approaching limits")
                else:
                    st.error(f"❌ {metric}: Performance degraded")

    # Performance recommendations
    st.markdown("#### 💡 Performance Recommendations")

    recommendations = generate_performance_recommendations(df)

    for rec in recommendations:
        if rec['priority'] == 'high':
            st.error(f"🔴 {rec['message']}")
        elif rec['priority'] == 'medium':
            st.warning(f"🟡 {rec['message']}")
        else:
            st.info(f"💡 {rec['message']}")

    return {
        'performance_metrics': {
            'total_metrics': total_metrics,
            'healthy_count': healthy_count,
            'warning_count': warning_count,
            'critical_count': critical_count
        },
        'alerts': generate_performance_alerts(df),
        'benchmarks': benchmark_results or {},
        'recommendations': recommendations
    }


def render_performance_metric_actions(
    metric_name: str,
    metric_data: pd.DataFrame,
    on_threshold_set: Optional[Callable],
    on_alert_config: Optional[Callable]
):
    """Render action buttons for a performance metric."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if on_threshold_set:
            if st.button("🎯 Set Threshold", key=f"threshold_{metric_name}"):
                st.session_state[f"setting_threshold_{metric_name}"] = True

            if st.session_state.get(f"setting_threshold_{metric_name}", False):
                latest_value = metric_data['value'].iloc[-1]
                suggested_threshold = latest_value * 1.2  # 20% above current value

                new_threshold = st.number_input(
                    f"Threshold for {metric_name}",
                    min_value=0.0,
                    value=float(suggested_threshold),
                    step=0.1,
                    key=f"new_threshold_{metric_name}"
                )

                if st.button("✅ Save", key=f"save_threshold_{metric_name}"):
                    on_threshold_set(metric_name, new_threshold)
                    st.session_state[f"setting_threshold_{metric_name}"] = False
                    st.success(f"✅ Threshold set for {metric_name}")
                    st.rerun()

    with col2:
        if on_alert_config:
            if st.button("🚨 Configure Alerts", key=f"alerts_{metric_name}"):
                on_alert_config(metric_name)

    with col3:
        if st.button("📊 Export Data", key=f"export_{metric_name}"):
            csv_data = metric_data.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"{metric_name}_metrics.csv",
                mime='text/csv',
                key=f"download_{metric_name}"
            )

    with col4:
        # Quick stats
        if len(metric_data) > 1:
            trend = get_performance_delta(metric_data)
            if trend:
                if trend > 0:
                    st.metric("Trend", ".2f", trend, "📈")
                else:
                    st.metric("Trend", ".2f", trend, "📉")


def get_performance_status_icon(status: str) -> str:
    """Get status icon for performance display."""
    icons = {
        'normal': '✅',
        'warning': '⚠️',
        'critical': '🚨',
        'unknown': '❓'
    }
    return icons.get(status, '❓')


def get_performance_delta(metric_data: pd.DataFrame) -> Optional[float]:
    """Calculate performance delta from recent data points."""
    if len(metric_data) < 2:
        return None

    # Compare latest value with previous value
    latest = metric_data['value'].iloc[-1]
    previous = metric_data['value'].iloc[-2]

    if previous == 0:
        return None

    return ((latest - previous) / previous) * 100


def calculate_performance_benchmarks(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate performance benchmarks from metrics data."""
    benchmarks = {}

    # Response time metrics
    response_metrics = df[df['metric_name'].str.contains('response|latency', case=False)]
    if len(response_metrics) > 0:
        avg_response = response_metrics['value'].mean()
        benchmarks['avg_response_time'] = avg_response

        # Benchmark against industry standards (example)
        if avg_response < 100:  # ms
            benchmarks['response_status'] = 'good'
        elif avg_response < 500:
            benchmarks['response_status'] = 'warning'
        else:
            benchmarks['response_status'] = 'poor'

    # Throughput metrics
    throughput_metrics = df[df['metric_name'].str.contains('throughput|requests', case=False)]
    if len(throughput_metrics) > 0:
        avg_throughput = throughput_metrics['value'].mean()
        benchmarks['throughput'] = avg_throughput

    # Error rate metrics
    error_metrics = df[df['metric_name'].str.contains('error|failure', case=False)]
    if len(error_metrics) > 0:
        avg_error_rate = error_metrics['value'].mean()
        benchmarks['error_rate'] = avg_error_rate

        if avg_error_rate < 0.01:  # 1%
            benchmarks['error_status'] = 'good'
        elif avg_error_rate < 0.05:  # 5%
            benchmarks['error_status'] = 'warning'
        else:
            benchmarks['error_status'] = 'poor'

    # Overall benchmark status
    benchmarks['benchmark_status'] = {}
    for key, status_key in [('response_status', 'Response Time'), ('error_status', 'Error Rate')]:
        if key in benchmarks:
            benchmarks['benchmark_status'][status_key] = benchmarks[key]

    return benchmarks


def generate_performance_alerts(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Generate performance alerts based on current metrics."""
    alerts = []

    # Check for critical performance issues
    critical_metrics = df[df['status'] == 'critical']
    for _, row in critical_metrics.iterrows():
        alerts.append({
            'level': 'critical',
            'message': f"Critical: {row['metric_name']} is at {row['value']:.2f} {row['unit']}",
            'timestamp': row['timestamp']
        })

    # Check for warning performance issues
    warning_metrics = df[df['status'] == 'warning']
    for _, row in warning_metrics.iterrows():
        alerts.append({
            'level': 'warning',
            'message': f"Warning: {row['metric_name']} is at {row['value']:.2f} {row['unit']}",
            'timestamp': row['timestamp']
        })

    # Check for metrics exceeding thresholds
    threshold_exceeded = df[
        (df['value'] > df['threshold']) &
        pd.notna(df['threshold'])
    ]
    for _, row in threshold_exceeded.iterrows():
        if row['status'] != 'critical':  # Avoid duplicate alerts
            alerts.append({
                'level': 'warning',
                'message': f"Threshold exceeded: {row['metric_name']} ({row['value']:.2f} > {row['threshold']:.2f} {row['unit']})",
                'timestamp': row['timestamp']
            })

    return alerts


def generate_performance_recommendations(df: pd.DataFrame) -> List[Dict[str, str]]:
    """Generate performance optimization recommendations."""
    recommendations = []

    # Check for consistently high utilization
    high_utilization = df[
        (df['metric_name'].str.contains('cpu|memory|utilization', case=False)) &
        (df['value'] > 80)
    ]
    if len(high_utilization) > 0:
        recommendations.append({
            'message': f"High resource utilization detected in {len(high_utilization.unique())} metrics. Consider scaling resources.",
            'priority': 'high'
        })

    # Check for increasing error rates
    error_trends = df[df['metric_name'].str.contains('error', case=False)]
    if len(error_trends) > 5:  # Need some history
        recent_errors = error_trends['value'].tail(5).mean()
        older_errors = error_trends['value'].head(5).mean()

        if recent_errors > older_errors * 1.5:
            recommendations.append({
                'message': "Error rates are increasing. Investigate recent changes or system issues.",
                'priority': 'high'
            })

    # Check for slow response times
    slow_responses = df[
        (df['metric_name'].str.contains('response|latency', case=False)) &
        (df['value'] > 1000)  # Over 1 second
    ]
    if len(slow_responses) > 0:
        recommendations.append({
            'message': f"Slow response times detected in {len(slow_responses)} operations. Optimize performance.",
            'priority': 'medium'
        })

    # Check for missing thresholds
    missing_thresholds = df[pd.isna(df['threshold'])]
    if len(missing_thresholds) > 0:
        recommendations.append({
            'message': f"Performance thresholds not set for {len(missing_thresholds.unique())} metrics. Configure monitoring thresholds.",
            'priority': 'low'
        })

    return recommendations


# Sample data generator for testing
def generate_sample_performance_data(count: int = 20) -> List[Dict[str, Any]]:
    """Generate sample performance data for testing."""
    metric_names = [
        'CPU Utilization', 'Memory Usage', 'Response Time', 'Error Rate',
        'Throughput', 'Database Connections', 'Network Latency', 'Disk I/O'
    ]
    units = ['%', 'MB', 'ms', '%', 'req/s', 'count', 'ms', 'MB/s']

    performance_metrics = []
    base_time = datetime.now() - timedelta(hours=1)

    for i in range(count):
        metric_name = np.random.choice(metric_names)
        unit = units[metric_names.index(metric_name)]

        # Generate realistic values based on metric type
        if 'CPU' in metric_name or 'Memory' in metric_name:
            value = np.random.uniform(10, 95)
            threshold = 80
        elif 'Response' in metric_name or 'Latency' in metric_name:
            value = np.random.uniform(50, 2000)
            threshold = 500
        elif 'Error' in metric_name:
            value = np.random.uniform(0, 0.1)
            threshold = 0.05
        elif 'Throughput' in metric_name:
            value = np.random.uniform(100, 1000)
            threshold = 200
        else:
            value = np.random.uniform(0, 100)
            threshold = 75

        # Determine status
        if value > threshold * 1.5:
            status = 'critical'
        elif value > threshold:
            status = 'warning'
        else:
            status = 'normal'

        timestamp = base_time + timedelta(minutes=i*3)

        metric = {
            'metric_name': metric_name,
            'value': round(value, 2),
            'unit': unit,
            'timestamp': timestamp,
            'threshold': threshold,
            'status': status
        }
        performance_metrics.append(metric)

    return performance_metrics
