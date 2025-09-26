"""Real-Time Analytics Pipeline Module.

This module provides real-time data processing, pipeline management,
and streaming analytics capabilities.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import streamlit as st


def render_realtime_pipeline():
    """Render the real-time analytics pipeline interface."""
    st.markdown("### ⚡ Real-Time Analytics Pipeline")
    st.markdown("Monitor and control real-time data processing pipelines.")

    # Pipeline status overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        status = st.session_state.analytics_config.get("realtime_enabled", False)
        status_icon = "🟢" if status else "🔴"
        st.metric("Pipeline Status", "Active" if status else "Inactive")
        st.write(f"{status_icon} {'Running' if status else 'Stopped'}")
    
    with col2:
        throughput = st.session_state.analytics_data.get("current_throughput", 0)
        st.metric("Throughput", f"{throughput}/sec")
    
    with col3:
        latency = st.session_state.analytics_data.get("avg_latency", 0)
        st.metric("Avg Latency", f"{latency:.2f}ms")
    
    with col4:
        error_rate = st.session_state.analytics_data.get("error_rate", 0)
        st.metric("Error Rate", f"{error_rate:.2f}%")

    # Pipeline controls
    st.markdown("#### Pipeline Controls")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start Pipeline", key="start_pipeline", 
                    disabled=st.session_state.analytics_config.get("realtime_enabled", False)):
            control_pipeline("start")
            st.rerun()
    
    with col2:
        if st.button("⏹️ Stop Pipeline", key="stop_pipeline",
                    disabled=not st.session_state.analytics_config.get("realtime_enabled", False)):
            control_pipeline("stop")
            st.rerun()
    
    with col3:
        if st.button("🔄 Restart Pipeline", key="restart_pipeline"):
            control_pipeline("restart")
            st.rerun()

    # Pipeline configuration
    with st.expander("⚙️ Pipeline Configuration", expanded=False):
        render_pipeline_configuration()

    # Real-time metrics visualization
    st.markdown("#### 📊 Real-Time Metrics")
    render_realtime_metrics()

    # Data processing queue
    st.markdown("#### 📋 Processing Queue")
    render_processing_queue()


def render_pipeline_configuration():
    """Render pipeline configuration interface."""
    st.markdown("##### Data Sources")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.checkbox("Simulation Metrics", 
                   value=st.session_state.analytics_config.get("data_sources", {}).get("simulation", True),
                   key="pipeline_sim_data")
        st.checkbox("Performance Logs",
                   value=st.session_state.analytics_config.get("data_sources", {}).get("logs", True),
                   key="pipeline_log_data")
    
    with col2:
        st.checkbox("External APIs",
                   value=st.session_state.analytics_config.get("data_sources", {}).get("apis", False),
                   key="pipeline_api_data")
        st.checkbox("Custom Streams",
                   value=st.session_state.analytics_config.get("data_sources", {}).get("custom", False),
                   key="pipeline_custom_data")

    st.markdown("##### Processing Options")
    
    batch_size = st.slider("Batch Size", 10, 1000, 
                          st.session_state.analytics_config.get("batch_size", 100),
                          key="pipeline_batch_size")
    
    processing_interval = st.slider("Processing Interval (seconds)", 1, 60,
                                   st.session_state.analytics_config.get("interval", 5),
                                   key="pipeline_interval")
    
    if st.button("💾 Apply Configuration", key="apply_pipeline_config"):
        config = {
            "data_sources": {
                "simulation": st.session_state.pipeline_sim_data,
                "logs": st.session_state.pipeline_log_data,
                "apis": st.session_state.pipeline_api_data,
                "custom": st.session_state.pipeline_custom_data,
            },
            "batch_size": batch_size,
            "interval": processing_interval,
        }
        apply_pipeline_configuration(config)
        st.success("✅ Pipeline configuration applied!")


def render_realtime_metrics():
    """Render real-time metrics visualization."""
    metrics_data = st.session_state.analytics_data.get("realtime_metrics", [])
    
    if not metrics_data:
        st.info("No real-time metrics available. Start the pipeline to begin collecting data.")
        return
    
    # Convert to DataFrame for display
    df = pd.DataFrame(metrics_data[-50:])  # Show last 50 data points
    
    if not df.empty:
        # Create metrics columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if 'cpu_usage' in df.columns:
                current_cpu = df['cpu_usage'].iloc[-1] if len(df) > 0 else 0
                st.metric("Current CPU", f"{current_cpu:.1f}%")
        
        with col2:
            if 'memory_usage' in df.columns:
                current_mem = df['memory_usage'].iloc[-1] if len(df) > 0 else 0
                st.metric("Current Memory", f"{current_mem:.1f}%")
        
        with col3:
            if 'response_time' in df.columns:
                current_resp = df['response_time'].iloc[-1] if len(df) > 0 else 0
                st.metric("Response Time", f"{current_resp:.1f}ms")
        
        with col4:
            if 'throughput' in df.columns:
                current_tp = df['throughput'].iloc[-1] if len(df) > 0 else 0
                st.metric("Throughput", f"{current_tp}/sec")
        
        # Simple line chart for recent trends
        if len(df) > 5:
            st.markdown("##### Recent Trends")
            # Show CPU and Memory trends
            trend_df = df[['timestamp', 'cpu_usage', 'memory_usage']].tail(20)
            if 'timestamp' in trend_df.columns:
                trend_df['timestamp'] = pd.to_datetime(trend_df['timestamp'])
                st.line_chart(trend_df.set_index('timestamp')[['cpu_usage', 'memory_usage']])


def render_processing_queue():
    """Render the processing queue status."""
    queue_data = st.session_state.analytics_data.get("processing_queue", [])
    
    if not queue_data:
        st.info("Processing queue is empty.")
        return
    
    st.markdown(f"**Queue Size:** {len(queue_data)} items")
    
    # Show recent queue items
    for i, item in enumerate(queue_data[-5:]):  # Show last 5
        status_icon = {"pending": "⏳", "processing": "⚙️", "completed": "✅", "failed": "❌"}.get(item.get("status", "pending"), "❓")
        
        with st.expander(f"{status_icon} {item.get('type', 'Unknown')} - {item.get('timestamp', 'Unknown')}", expanded=False):
            st.write(f"**Status:** {item.get('status', 'Unknown').title()}")
            st.write(f"**Priority:** {item.get('priority', 'Normal')}")
            if 'data' in item:
                st.write(f"**Data Points:** {len(item['data'])}")
            if 'processing_time' in item:
                st.write(f"**Processing Time:** {item['processing_time']:.2f}s")


def control_pipeline(action: str):
    """Control the real-time pipeline (start/stop/restart)."""
    current_status = st.session_state.analytics_config.get("realtime_enabled", False)
    
    if action == "start" and not current_status:
        st.session_state.analytics_config["realtime_enabled"] = True
        # Initialize pipeline data
        if "realtime_metrics" not in st.session_state.analytics_data:
            st.session_state.analytics_data["realtime_metrics"] = []
        if "processing_queue" not in st.session_state.analytics_data:
            st.session_state.analytics_data["processing_queue"] = []
        st.success("▶️ Pipeline started successfully!")
        
    elif action == "stop" and current_status:
        st.session_state.analytics_config["realtime_enabled"] = False
        st.success("⏹️ Pipeline stopped successfully!")
        
    elif action == "restart":
        st.session_state.analytics_config["realtime_enabled"] = False
        time.sleep(0.5)  # Brief pause
        st.session_state.analytics_config["realtime_enabled"] = True
        st.success("🔄 Pipeline restarted successfully!")


def apply_pipeline_configuration(config: Dict[str, Any]):
    """Apply pipeline configuration changes."""
    st.session_state.analytics_config["pipeline_config"] = config
    st.session_state.analytics_config["data_sources"] = config["data_sources"]
    st.session_state.analytics_config["batch_size"] = config["batch_size"]
    st.session_state.analytics_config["interval"] = config["interval"]
