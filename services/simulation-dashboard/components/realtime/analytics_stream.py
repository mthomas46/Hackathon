"""Real-Time Analytics Stream Component.

This module provides real-time analytics streaming capabilities that connect
to multiple ecosystem services to provide live data analytics and insights.
"""

import streamlit as st
import asyncio
import httpx
import json
import time
import pandas as pd
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from datetime import datetime, timedelta
import threading
import queue
from dataclasses import dataclass
import logging

from infrastructure.logging.logger import get_dashboard_logger


logger = get_dashboard_logger("analytics_stream")


@dataclass
class AnalyticsDataPoint:
    """Data point for real-time analytics."""
    timestamp: datetime
    service: str
    metric: str
    value: Any
    metadata: Dict[str, Any] = None


@dataclass
class AnalyticsStream:
    """Real-time analytics stream configuration."""
    name: str
    services: List[str]
    metrics: List[str]
    update_interval: float = 5.0
    max_points: int = 1000


class RealTimeAnalyticsStream:
    """Real-time analytics streaming component."""

    def __init__(self):
        """Initialize the analytics stream."""
        self.streams: Dict[str, AnalyticsStream] = {}
        self.data_queues: Dict[str, queue.Queue] = {}
        self.running_streams: Dict[str, bool] = {}
        self.stream_threads: Dict[str, threading.Thread] = {}

        # Initialize default streams
        self._initialize_default_streams()

    def _initialize_default_streams(self):
        """Initialize default analytics streams."""
        self.streams = {
            "health_monitoring": AnalyticsStream(
                name="Health Monitoring",
                services=["project-simulation", "analysis-service", "llm-gateway", "doc-store"],
                metrics=["response_time", "status", "uptime", "error_rate"],
                update_interval=10.0
            ),
            "performance_metrics": AnalyticsStream(
                name="Performance Metrics",
                services=["project-simulation", "analysis-service"],
                metrics=["cpu_usage", "memory_usage", "throughput", "latency"],
                update_interval=5.0
            ),
            "simulation_tracking": AnalyticsStream(
                name="Simulation Tracking",
                services=["project-simulation"],
                metrics=["active_simulations", "completion_rate", "success_rate", "queue_length"],
                update_interval=2.0
            ),
            "llm_usage": AnalyticsStream(
                name="LLM Usage Analytics",
                services=["llm-gateway"],
                metrics=["queries_per_minute", "tokens_used", "model_usage", "response_time"],
                update_interval=15.0
            )
        }

        # Initialize data queues for each stream
        for stream_name in self.streams.keys():
            self.data_queues[stream_name] = queue.Queue(maxsize=1000)

    async def start_stream(self, stream_name: str) -> bool:
        """Start a real-time analytics stream."""
        if stream_name not in self.streams:
            logger.error(f"Unknown stream: {stream_name}")
            return False

        if stream_name in self.running_streams and self.running_streams[stream_name]:
            logger.warning(f"Stream {stream_name} is already running")
            return True

        self.running_streams[stream_name] = True

        # Start the stream in a separate thread
        thread = threading.Thread(
            target=self._run_stream_async,
            args=(stream_name,),
            daemon=True
        )
        self.stream_threads[stream_name] = thread
        thread.start()

        logger.info(f"Started analytics stream: {stream_name}")
        return True

    def stop_stream(self, stream_name: str) -> bool:
        """Stop a real-time analytics stream."""
        if stream_name not in self.running_streams:
            return False

        self.running_streams[stream_name] = False

        if stream_name in self.stream_threads:
            self.stream_threads[stream_name].join(timeout=5.0)

        logger.info(f"Stopped analytics stream: {stream_name}")
        return True

    def _run_stream_async(self, stream_name: str):
        """Run a stream in an event loop."""
        try:
            asyncio.run(self._run_stream(stream_name))
        except Exception as e:
            logger.error(f"Error running stream {stream_name}: {e}")

    async def _run_stream(self, stream_name: str):
        """Run the analytics stream."""
        stream_config = self.streams[stream_name]
        data_queue = self.data_queues[stream_name]

        logger.info(f"Starting analytics stream {stream_name} with interval {stream_config.update_interval}s")

        while self.running_streams.get(stream_name, False):
            try:
                # Collect data from all services in the stream
                for service in stream_config.services:
                    service_data = await self._collect_service_data(service, stream_config.metrics)

                    # Create data points for each metric
                    for metric, value in service_data.items():
                        if metric in stream_config.metrics:
                            data_point = AnalyticsDataPoint(
                                timestamp=datetime.now(),
                                service=service,
                                metric=metric,
                                value=value,
                                metadata={"stream": stream_name}
                            )

                            # Add to queue (non-blocking)
                            try:
                                data_queue.put_nowait(data_point)
                            except queue.Full:
                                # Remove oldest item if queue is full
                                try:
                                    data_queue.get_nowait()
                                    data_queue.put_nowait(data_point)
                                except queue.Empty:
                                    pass

                # Wait for next update
                await asyncio.sleep(stream_config.update_interval)

            except Exception as e:
                logger.error(f"Error in stream {stream_name}: {e}")
                await asyncio.sleep(5.0)  # Wait before retry

    async def _collect_service_data(self, service_name: str, metrics: List[str]) -> Dict[str, Any]:
        """Collect data from a specific service."""
        service_urls = {
            "project-simulation": "http://localhost:5075/health",
            "analysis-service": "http://localhost:5080/health",
            "llm-gateway": "http://localhost:5055/health",
            "doc-store": "http://localhost:5087/health",
            "orchestrator": "http://localhost:5099/health",
            "interpreter": "http://localhost:5120/health",
            "summarizer-hub": "http://localhost:5160/health"
        }

        if service_name not in service_urls:
            return {}

        url = service_urls[service_name]

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()
                    response_time = response.elapsed.total_seconds()

                    # Extract relevant metrics based on service
                    service_data = {
                        "response_time": response_time,
                        "status": data.get("status", "unknown"),
                        "uptime": data.get("uptime_seconds", 0),
                        "timestamp": time.time()
                    }

                    # Add service-specific metrics
                    if service_name == "project-simulation":
                        # Try to get simulation-specific metrics
                        service_data.update(await self._get_simulation_metrics())
                    elif service_name == "llm-gateway":
                        service_data.update(await self._get_llm_metrics())

                    return service_data
                else:
                    return {
                        "response_time": response.elapsed.total_seconds(),
                        "status": "error",
                        "error": f"HTTP {response.status_code}"
                    }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time": 0
            }

    async def _get_simulation_metrics(self) -> Dict[str, Any]:
        """Get simulation-specific metrics."""
        try:
            # This would ideally call simulation service APIs for real metrics
            return {
                "active_simulations": 3,
                "completion_rate": 87.5,
                "success_rate": 92.3,
                "queue_length": 2
            }
        except:
            return {}

    async def _get_llm_metrics(self) -> Dict[str, Any]:
        """Get LLM-specific metrics."""
        try:
            # This would ideally call LLM gateway APIs for real metrics
            return {
                "queries_per_minute": 12.5,
                "tokens_used": 15420,
                "model_usage": {"llama2": 85, "codellama": 15},
                "avg_response_time": 2.3
            }
        except:
            return {}

    def get_stream_data(self, stream_name: str, max_points: int = 100) -> List[AnalyticsDataPoint]:
        """Get recent data points from a stream."""
        if stream_name not in self.data_queues:
            return []

        data_queue = self.data_queues[stream_name]
        data_points = []

        # Get all available data points
        while not data_queue.empty() and len(data_points) < max_points:
            try:
                data_points.append(data_queue.get_nowait())
            except queue.Empty:
                break

        return data_points[-max_points:]  # Return most recent points

    def get_stream_dataframe(self, stream_name: str, max_points: int = 100) -> pd.DataFrame:
        """Get stream data as a pandas DataFrame."""
        data_points = self.get_stream_data(stream_name, max_points)

        if not data_points:
            return pd.DataFrame()

        # Convert to DataFrame
        data = []
        for point in data_points:
            data.append({
                'timestamp': point.timestamp,
                'service': point.service,
                'metric': point.metric,
                'value': point.value,
                **(point.metadata or {})
            })

        return pd.DataFrame(data)

    def get_active_streams(self) -> List[str]:
        """Get list of currently active streams."""
        return [name for name, running in self.running_streams.items() if running]

    def stop_all_streams(self):
        """Stop all running streams."""
        for stream_name in list(self.running_streams.keys()):
            self.stop_stream(stream_name)


# Global instance
analytics_stream = RealTimeAnalyticsStream()


def render_realtime_analytics_dashboard():
    """Render the real-time analytics dashboard."""
    st.markdown("### 📊 Real-Time Analytics Stream")
    st.markdown("Live data streaming from ecosystem services with real-time visualization.")

    # Stream controls
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown("#### 🎮 Stream Controls")

        available_streams = list(analytics_stream.streams.keys())
        selected_streams = st.multiselect(
            "Select Analytics Streams",
            available_streams,
            default=["health_monitoring", "performance_metrics"],
            key="selected_streams"
        )

    with col2:
        st.markdown("#### 📈 Active Streams")
        active_streams = analytics_stream.get_active_streams()

        for stream in selected_streams:
            if stream in active_streams:
                st.success(f"🟢 {stream.replace('_', ' ').title()}")
            else:
                st.info(f"⚪ {stream.replace('_', ' ').title()}")

    with col3:
        if st.button("▶️ Start Selected Streams", key="start_streams"):
            for stream in selected_streams:
                asyncio.run(analytics_stream.start_stream(stream))
            st.rerun()

        if st.button("⏹️ Stop All Streams", key="stop_streams"):
            analytics_stream.stop_all_streams()
            st.rerun()

    # Live data visualization
    if selected_streams:
        st.markdown("---")
        render_stream_visualizations(selected_streams)


def render_stream_visualizations(selected_streams: List[str]):
    """Render real-time visualizations for selected streams."""
    # Create tabs for different streams
    if len(selected_streams) == 1:
        render_single_stream_visualization(selected_streams[0])
    else:
        tabs = st.tabs([s.replace('_', ' ').title() for s in selected_streams])
        for i, (tab, stream_name) in enumerate(zip(tabs, selected_streams)):
            with tab:
                render_single_stream_visualization(stream_name)


def render_single_stream_visualization(stream_name: str):
    """Render visualization for a single stream."""
    st.markdown(f"#### 📈 {stream_name.replace('_', ' ').title()} Stream")

    # Get stream data
    df = analytics_stream.get_stream_dataframe(stream_name, max_points=200)

    if df.empty:
        st.info(f"No data available for {stream_name}. Start the stream to begin collecting data.")
        return

    # Create real-time charts based on stream type
    if stream_name == "health_monitoring":
        render_health_monitoring_charts(df)
    elif stream_name == "performance_metrics":
        render_performance_charts(df)
    elif stream_name == "simulation_tracking":
        render_simulation_tracking_charts(df)
    elif stream_name == "llm_usage":
        render_llm_usage_charts(df)
    else:
        render_generic_charts(df, stream_name)


def render_health_monitoring_charts(df: pd.DataFrame):
    """Render health monitoring specific charts."""
    # Response time trends
    response_time_data = df[df['metric'] == 'response_time'].copy()
    if not response_time_data.empty:
        fig = px.line(response_time_data, x='timestamp', y='value', color='service',
                     title='Service Response Times (seconds)',
                     labels={'value': 'Response Time (s)', 'timestamp': 'Time'})
        st.plotly_chart(fig, use_container_width=True)

    # Service status overview
    status_data = df[df['metric'] == 'status'].copy()
    if not status_data.empty:
        # Convert status to numeric for charting
        status_mapping = {'healthy': 1, 'unhealthy': 0, 'unknown': 0.5}
        status_data['status_numeric'] = status_data['value'].map(status_mapping)

        fig = px.scatter(status_data, x='timestamp', y='status_numeric', color='service',
                        title='Service Health Status Over Time',
                        labels={'status_numeric': 'Status (1=Healthy, 0=Unhealthy)'})
        st.plotly_chart(fig, use_container_width=True)


def render_performance_charts(df: pd.DataFrame):
    """Render performance metrics charts."""
    # CPU/Memory usage if available
    if 'cpu_usage' in df['metric'].values:
        cpu_data = df[df['metric'] == 'cpu_usage'].copy()
        if not cpu_data.empty:
            fig = px.area(cpu_data, x='timestamp', y='value', color='service',
                         title='CPU Usage Over Time (%)')
            st.plotly_chart(fig, use_container_width=True)

    # Throughput metrics
    if 'throughput' in df['metric'].values:
        throughput_data = df[df['metric'] == 'throughput'].copy()
        if not throughput_data.empty:
            fig = px.bar(throughput_data, x='timestamp', y='value', color='service',
                        title='Service Throughput')
            st.plotly_chart(fig, use_container_width=True)


def render_simulation_tracking_charts(df: pd.DataFrame):
    """Render simulation tracking charts."""
    # Active simulations
    if 'active_simulations' in df['metric'].values:
        sim_data = df[df['metric'] == 'active_simulations'].copy()
        if not sim_data.empty:
            fig = px.line(sim_data, x='timestamp', y='value',
                         title='Active Simulations Over Time',
                         labels={'value': 'Active Simulations'})
            st.plotly_chart(fig, use_container_width=True)

    # Success rate trends
    if 'success_rate' in df['metric'].values:
        success_data = df[df['metric'] == 'success_rate'].copy()
        if not success_data.empty:
            fig = px.line(success_data, x='timestamp', y='value',
                         title='Simulation Success Rate (%)',
                         labels={'value': 'Success Rate (%)'})
            fig.add_hline(y=90, line_dash="dot", line_color="red",
                         annotation_text="Target: 90%")
            st.plotly_chart(fig, use_container_width=True)


def render_llm_usage_charts(df: pd.DataFrame):
    """Render LLM usage analytics charts."""
    # Queries per minute
    if 'queries_per_minute' in df['metric'].values:
        query_data = df[df['metric'] == 'queries_per_minute'].copy()
        if not query_data.empty:
            fig = px.line(query_data, x='timestamp', y='value',
                         title='LLM Queries per Minute',
                         labels={'value': 'Queries/min'})
            st.plotly_chart(fig, use_container_width=True)

    # Token usage
    if 'tokens_used' in df['metric'].values:
        token_data = df[df['metric'] == 'tokens_used'].copy()
        if not token_data.empty:
            fig = px.area(token_data, x='timestamp', y='value',
                         title='Token Usage Over Time',
                         labels={'value': 'Tokens Used'})
            st.plotly_chart(fig, use_container_width=True)


def render_generic_charts(df: pd.DataFrame, stream_name: str):
    """Render generic charts for unknown stream types."""
    # Group by metric and create subplots
    metrics = df['metric'].unique()

    if len(metrics) <= 4:  # Create subplots for up to 4 metrics
        cols = st.columns(len(metrics))
        for i, metric in enumerate(metrics):
            with cols[i]:
                metric_data = df[df['metric'] == metric].copy()
                if not metric_data.empty:
                    fig = px.line(metric_data, x='timestamp', y='value', color='service',
                                 title=f'{metric.replace("_", " ").title()}')
                    st.plotly_chart(fig, use_container_width=True)
    else:
        # Single combined chart
        fig = px.line(df, x='timestamp', y='value', color='metric',
                     title=f'{stream_name.replace("_", " ").title()} - All Metrics')
        st.plotly_chart(fig, use_container_width=True)
