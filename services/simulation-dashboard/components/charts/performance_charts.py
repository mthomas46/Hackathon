"""Performance Charts Components.

This module provides chart components for displaying performance metrics,
monitoring data, and system analytics visualizations.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("⚠️ Plotly not available. Performance chart components will be limited.")


def render_performance_chart(
    metrics_data: Dict[str, Any],
    chart_type: str = "line",
    title: str = "Performance Metrics",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render performance metrics chart.

    Args:
        metrics_data: Performance metrics data
        chart_type: Type of chart ('line', 'bar', 'area')
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for performance chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not metrics_data or 'data' not in metrics_data:
            st.info("No performance data available")
            return

        data = metrics_data['data']

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)

            # Ensure we have timestamp and value columns
            if 'timestamp' not in df.columns:
                st.error("❌ Performance data missing timestamp column")
                return

            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Get numeric columns for metrics
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            numeric_cols = [col for col in numeric_cols if col != 'timestamp']

            if not numeric_cols:
                st.info("No numeric performance metrics found")
                return

            # Create the chart
            if chart_type == "line":
                fig = px.line(
                    df,
                    x='timestamp',
                    y=numeric_cols,
                    title=title
                )
            elif chart_type == "bar":
                # For bar chart, aggregate by time period
                df_agg = df.set_index('timestamp').resample('1H').mean().reset_index()
                fig = px.bar(
                    df_agg,
                    x='timestamp',
                    y=numeric_cols,
                    title=title
                )
            elif chart_type == "area":
                fig = px.area(
                    df,
                    x='timestamp',
                    y=numeric_cols,
                    title=title
                )
            else:
                # Default to line chart
                fig = px.line(
                    df,
                    x='timestamp',
                    y=numeric_cols,
                    title=title
                )

            fig.update_layout(
                width=width,
                height=height,
                xaxis_title="Time",
                yaxis_title="Metric Value"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display metrics summary
            render_metrics_summary(df, numeric_cols)

        else:
            st.info("No performance data to display")

    except Exception as e:
        st.error(f"❌ Error rendering performance chart: {str(e)}")


def render_metrics_summary(df: pd.DataFrame, metric_columns: List[str]) -> None:
    """Render summary statistics for performance metrics."""
    try:
        if df.empty or not metric_columns:
            return

        st.markdown("#### 📊 Metrics Summary")

        # Calculate summary statistics
        summary_data = []

        for col in metric_columns:
            if col in df.columns:
                values = df[col].dropna()
                if not values.empty:
                    summary_data.append({
                        'Metric': col.replace('_', ' ').title(),
                        'Current': ".2f",
                        'Average': ".2f",
                        'Min': ".2f",
                        'Max': ".2f",
                        'Std Dev': ".2f"
                    })

        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error rendering metrics summary: {str(e)}")


def render_system_health_chart(
    health_data: Dict[str, Any],
    title: str = "System Health Overview",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render system health monitoring chart.

    Args:
        health_data: System health metrics
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not health_data:
            st.info("No health data available")
            return

        # Extract health metrics
        timestamps = []
        cpu_usage = []
        memory_usage = []
        disk_usage = []
        network_io = []

        if 'metrics' in health_data:
            for metric in health_data['metrics']:
                timestamps.append(pd.to_datetime(metric.get('timestamp', datetime.now())))
                cpu_usage.append(metric.get('cpu_percent', 0))
                memory_usage.append(metric.get('memory_percent', 0))
                disk_usage.append(metric.get('disk_percent', 0))
                network_io.append(metric.get('network_io', 0))

        if not timestamps:
            st.info("No health metrics to display")
            return

        # Create subplots for multiple metrics
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('CPU Usage', 'Memory Usage', 'Disk Usage', 'Network I/O'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )

        # Add CPU usage
        fig.add_trace(
            go.Scatter(x=timestamps, y=cpu_usage, name='CPU %', line=dict(color='red')),
            row=1, col=1
        )

        # Add Memory usage
        fig.add_trace(
            go.Scatter(x=timestamps, y=memory_usage, name='Memory %', line=dict(color='blue')),
            row=1, col=2
        )

        # Add Disk usage
        fig.add_trace(
            go.Scatter(x=timestamps, y=disk_usage, name='Disk %', line=dict(color='green')),
            row=2, col=1
        )

        # Add Network I/O
        fig.add_trace(
            go.Scatter(x=timestamps, y=network_io, name='Network I/O', line=dict(color='orange')),
            row=2, col=2
        )

        fig.update_layout(
            title=title,
            width=width,
            height=height,
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        # Display current health status
        render_health_status_summary(health_data)

    except Exception as e:
        st.error(f"❌ Error rendering system health chart: {str(e)}")


def render_health_status_summary(health_data: Dict[str, Any]) -> None:
    """Render health status summary."""
    try:
        if not health_data or 'current' not in health_data:
            return

        current = health_data['current']

        st.markdown("#### 🏥 Current Health Status")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            cpu = current.get('cpu_percent', 0)
            cpu_color = "🟢" if cpu < 70 else "🟡" if cpu < 90 else "🔴"
            st.metric("CPU Usage", ".1f", cpu_color)

        with col2:
            memory = current.get('memory_percent', 0)
            memory_color = "🟢" if memory < 70 else "🟡" if memory < 90 else "🔴"
            st.metric("Memory Usage", ".1f", memory_color)

        with col3:
            disk = current.get('disk_percent', 0)
            disk_color = "🟢" if disk < 80 else "🟡" if disk < 95 else "🔴"
            st.metric("Disk Usage", ".1f", disk_color)

        with col4:
            status = current.get('overall_status', 'unknown')
            status_color = "🟢" if status == 'healthy' else "🟡" if status == 'warning' else "🔴"
            st.metric("Overall Status", status, status_color)

    except Exception as e:
        st.error(f"❌ Error rendering health status summary: {str(e)}")


def render_response_time_chart(
    response_data: Dict[str, Any],
    title: str = "Response Time Analysis",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render response time analysis chart.

    Args:
        response_data: Response time metrics
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not response_data or 'responses' not in response_data:
            st.info("No response time data available")
            return

        responses = response_data['responses']

        if isinstance(responses, list) and len(responses) > 0:
            df = pd.DataFrame(responses)

            if 'timestamp' not in df.columns or 'response_time' not in df.columns:
                st.error("❌ Response data missing required columns (timestamp, response_time)")
                return

            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Create response time chart
            fig = px.line(
                df,
                x='timestamp',
                y='response_time',
                title=title,
                labels={'response_time': 'Response Time (ms)', 'timestamp': 'Time'}
            )

            # Add rolling average
            df['rolling_avg'] = df['response_time'].rolling(window=10).mean()
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['rolling_avg'],
                    name='Rolling Average',
                    line=dict(color='red', width=2)
                )
            )

            fig.update_layout(
                width=width,
                height=height,
                xaxis_title="Time",
                yaxis_title="Response Time (ms)"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display response time statistics
            render_response_time_stats(df)

        else:
            st.info("No response time data to display")

    except Exception as e:
        st.error(f"❌ Error rendering response time chart: {str(e)}")


def render_response_time_stats(df: pd.DataFrame) -> None:
    """Render response time statistics."""
    try:
        if df.empty or 'response_time' not in df.columns:
            return

        response_times = df['response_time'].dropna()

        if response_times.empty:
            return

        st.markdown("#### 📊 Response Time Statistics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            avg_time = response_times.mean()
            st.metric("Average", ".2f", avg_time)

        with col2:
            median_time = response_times.median()
            st.metric("Median", ".2f", median_time)

        with col3:
            p95_time = response_times.quantile(0.95)
            st.metric("95th Percentile", ".2f", p95_time)

        with col4:
            max_time = response_times.max()
            st.metric("Maximum", ".2f", max_time)

        # Response time distribution
        st.markdown("#### 📈 Response Time Distribution")

        fig = px.histogram(
            response_times,
            title="Response Time Distribution",
            labels={'value': 'Response Time (ms)', 'count': 'Frequency'},
            nbins=30
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error rendering response time statistics: {str(e)}")


def render_throughput_chart(
    throughput_data: Dict[str, Any],
    title: str = "System Throughput",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render system throughput chart.

    Args:
        throughput_data: Throughput metrics
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not throughput_data or 'data' not in throughput_data:
            st.info("No throughput data available")
            return

        data = throughput_data['data']

        if isinstance(data, list) and len(data) > 0:
            df = pd.DataFrame(data)

            if 'timestamp' not in df.columns:
                st.error("❌ Throughput data missing timestamp column")
                return

            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Get throughput metrics
            throughput_cols = [col for col in df.columns if 'throughput' in col.lower() or 'requests' in col.lower() or 'transactions' in col.lower()]

            if not throughput_cols:
                # Try to find any numeric columns
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                throughput_cols = [col for col in numeric_cols if col != 'timestamp']

            if not throughput_cols:
                st.info("No throughput metrics found")
                return

            # Create throughput chart
            fig = px.line(
                df,
                x='timestamp',
                y=throughput_cols,
                title=title,
                labels={'value': 'Throughput', 'timestamp': 'Time'}
            )

            fig.update_layout(
                width=width,
                height=height,
                xaxis_title="Time",
                yaxis_title="Throughput (req/sec)"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display throughput summary
            render_throughput_summary(df, throughput_cols)

        else:
            st.info("No throughput data to display")

    except Exception as e:
        st.error(f"❌ Error rendering throughput chart: {str(e)}")


def render_throughput_summary(df: pd.DataFrame, throughput_cols: List[str]) -> None:
    """Render throughput summary statistics."""
    try:
        if df.empty or not throughput_cols:
            return

        st.markdown("#### 📊 Throughput Summary")

        # Calculate summary for each throughput metric
        summary_data = []

        for col in throughput_cols:
            if col in df.columns:
                values = df[col].dropna()
                if not values.empty:
                    summary_data.append({
                        'Metric': col.replace('_', ' ').title(),
                        'Average': ".2f",
                        'Peak': ".2f",
                        'Min': ".2f",
                        'Total': ".0f"
                    })

        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error rendering throughput summary: {str(e)}")


def render_error_rate_chart(
    error_data: Dict[str, Any],
    title: str = "Error Rate Analysis",
    width: Optional[int] = None,
    height: Optional[int] = 400
) -> None:
    """Render error rate analysis chart.

    Args:
        error_data: Error rate metrics
        title: Chart title
        width: Chart width
        height: Chart height
    """
    if not PLOTLY_AVAILABLE:
        st.error("❌ Plotly is required for chart components")
        return

    try:
        st.markdown(f"### {title}")

        if not error_data or 'errors' not in error_data:
            st.info("No error data available")
            return

        errors = error_data['errors']

        if isinstance(errors, list) and len(errors) > 0:
            df = pd.DataFrame(errors)

            if 'timestamp' not in df.columns:
                st.error("❌ Error data missing timestamp column")
                return

            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Calculate error rate if not provided
            if 'error_rate' not in df.columns:
                total_requests = df.get('total_requests', df.get('requests', [1] * len(df)))
                error_count = df.get('error_count', df.get('errors', [0] * len(df)))
                df['error_rate'] = np.array(error_count) / np.array(total_requests) * 100

            # Create error rate chart
            fig = px.line(
                df,
                x='timestamp',
                y='error_rate',
                title=title,
                labels={'error_rate': 'Error Rate (%)', 'timestamp': 'Time'}
            )

            # Add error threshold line
            fig.add_hline(
                y=5,
                line_dash="dash",
                line_color="red",
                annotation_text="Error Threshold (5%)"
            )

            fig.update_layout(
                width=width,
                height=height,
                xaxis_title="Time",
                yaxis_title="Error Rate (%)"
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display error statistics
            render_error_summary(df)

        else:
            st.info("No error data to display")

    except Exception as e:
        st.error(f"❌ Error rendering error rate chart: {str(e)}")


def render_error_summary(df: pd.DataFrame) -> None:
    """Render error summary statistics."""
    try:
        if df.empty:
            return

        st.markdown("#### 📊 Error Analysis")

        col1, col2, col3, col4 = st.columns(4)

        # Calculate error metrics
        if 'error_rate' in df.columns:
            avg_error_rate = df['error_rate'].mean()
            max_error_rate = df['error_rate'].max()
            error_incidents = (df['error_rate'] > 5).sum()  # Above 5% threshold
            total_periods = len(df)

            with col1:
                st.metric("Average Error Rate", ".2f", avg_error_rate)

            with col2:
                st.metric("Peak Error Rate", ".2f", max_error_rate)

            with col3:
                st.metric("Error Incidents", error_incidents)

            with col4:
                reliability = ((total_periods - error_incidents) / total_periods) * 100
                st.metric("Uptime Reliability", ".1f", reliability)

    except Exception as e:
        st.error(f"❌ Error rendering error summary: {str(e)}")
