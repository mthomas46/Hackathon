"""Performance Monitor page - View MCP and pattern performance metrics."""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np


def render():
    """Render the performance monitor page."""
    
    st.title("📈 Performance Monitor")
    st.markdown("Real-time performance metrics and analytics")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Overview", "📊 Pattern Performance", "⚠️ Anomalies"])
    
    with tab1:
        render_overview()
    
    with tab2:
        render_pattern_performance()
    
    with tab3:
        render_anomalies()


def render_overview():
    """Render performance overview."""
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Response Time", "245ms", delta="-15ms")
    
    with col2:
        st.metric("P95 Latency", "892ms", delta="-42ms")
    
    with col3:
        st.metric("Success Rate", "99.7%", delta="+0.2%")
    
    with col4:
        st.metric("Throughput", "47 req/s", delta="+5")
    
    # Response time trend
    st.markdown("---")
    st.subheader("Response Time Trend (24h)")
    
    # Mock data
    hours = list(range(24))
    response_times = [200 + np.random.randint(-50, 50) + (i % 6) * 10 for i in hours]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hours,
        y=response_times,
        mode='lines+markers',
        name='Response Time',
        line=dict(color='#2563eb', width=2)
    ))
    
    fig.update_layout(
        xaxis_title="Hour",
        yaxis_title="Response Time (ms)",
        height=350,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Execution distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Executions by Status")
        status_data = pd.DataFrame({
            "Status": ["Success", "Failed", "Timeout"],
            "Count": [1843, 5, 2]
        })
        fig = px.pie(status_data, values="Count", names="Status",
                     color_discrete_sequence=["#10b981", "#ef4444", "#f59e0b"])
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Top MCPs by Volume")
        mcp_data = pd.DataFrame({
            "MCP": ["customer-support", "product-docs", "code-analysis", "sales-insights"],
            "Queries": [12500, 8200, 3100, 1800]
        })
        fig = px.bar(mcp_data, x="MCP", y="Queries", color="Queries",
                     color_continuous_scale="Blues")
        st.plotly_chart(fig, use_container_width=True)


def render_pattern_performance():
    """Render pattern-specific performance."""
    
    st.subheader("Pattern Performance")
    
    # Pattern selector
    pattern = st.selectbox("Select Pattern", [
        "RAG",
        "Chain-of-Thought",
        "ReAct",
        "Tree-of-Thoughts",
        "Self-Reflection",
        "Multi-Agent"
    ])
    
    # Pattern metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Executions", "342", delta="+12%")
    
    with col2:
        st.metric("Avg Duration", "1.2s", delta="-0.1s")
    
    with col3:
        st.metric("Success Rate", "99.1%", delta="+0.3%")
    
    with col4:
        st.metric("Avg Tokens", "1,247", delta="+52")
    
    # Performance trend
    st.markdown("---")
    st.subheader(f"{pattern} Performance Trend")
    
    days = list(range(7))
    durations = [1.0 + np.random.random() * 0.5 for _ in days]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=days,
        y=durations,
        mode='lines+markers',
        name='Duration',
        line=dict(color='#8b5cf6', width=2)
    ))
    
    fig.update_layout(
        xaxis_title="Days Ago",
        yaxis_title="Duration (seconds)",
        height=300
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent executions
    st.markdown("---")
    st.subheader("Recent Executions")
    
    executions = pd.DataFrame({
        "Time": ["2 min ago", "5 min ago", "8 min ago", "12 min ago", "15 min ago"],
        "MCP": ["customer-support", "product-docs", "code-analysis", "customer-support", "sales-insights"],
        "Duration (ms)": [1234, 987, 1456, 1123, 1089],
        "Tokens": [1205, 985, 1432, 1156, 1001],
        "Status": ["✅ Success", "✅ Success", "✅ Success", "✅ Success", "✅ Success"]
    })
    
    st.dataframe(executions, use_container_width=True, hide_index=True)


def render_anomalies():
    """Render anomaly detection results."""
    
    st.subheader("⚠️ Detected Anomalies")
    
    # Time range selector
    time_range = st.selectbox("Time Range", ["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"])
    
    # Anomaly stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Anomalies", "3", delta="-2")
    
    with col2:
        st.metric("High Severity", "0", delta="0")
    
    with col3:
        st.metric("Medium Severity", "2", delta="+1")
    
    with col4:
        st.metric("Low Severity", "1", delta="-3")
    
    # Anomaly list
    st.markdown("---")
    st.subheader("Anomaly Details")
    
    anomalies = [
        {
            "time": "18 minutes ago",
            "type": "Response Time Spike",
            "severity": "Medium",
            "details": "Response time increased to 2.3s (3.2σ above mean)",
            "mcp": "customer-support",
            "pattern": "RAG"
        },
        {
            "time": "42 minutes ago",
            "type": "High Memory Usage",
            "severity": "Medium",
            "details": "Memory usage reached 3.8 GB (2.1σ above mean)",
            "mcp": "code-analysis",
            "pattern": "Tree-of-Thoughts"
        },
        {
            "time": "1 hour ago",
            "type": "Low Success Rate",
            "severity": "Low",
            "details": "Success rate dropped to 96.5% for 10 minutes",
            "mcp": "product-docs",
            "pattern": "Chain-of-Thought"
        }
    ]
    
    for anomaly in anomalies:
        severity_color = {
            "High": "🔴",
            "Medium": "🟡",
            "Low": "🟢"
        }[anomaly["severity"]]
        
        with st.expander(f"{severity_color} **{anomaly['type']}** - {anomaly['time']}", expanded=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Details:** {anomaly['details']}")
                st.markdown(f"**MCP:** {anomaly['mcp']} | **Pattern:** {anomaly['pattern']}")
            
            with col2:
                if st.button("Investigate", key=f"inv_{anomaly['time']}"):
                    st.info("Opening detailed investigation view...")
                if st.button("Dismiss", key=f"dismiss_{anomaly['time']}"):
                    st.success("Anomaly dismissed")
