"""Home page - Dashboard overview."""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
import pandas as pd


def render():
    """Render the home page."""
    
    st.title("🏠 MCP Ecosystem Dashboard")
    st.markdown("Welcome to the Model Context Protocol management interface")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Active MCPs",
            value="12",
            delta="+2",
            help="Currently running MCP instances"
        )
    
    with col2:
        st.metric(
            label="Total Queries (24h)",
            value="1,847",
            delta="+12%",
            help="Query volume in last 24 hours"
        )
    
    with col3:
        st.metric(
            label="Avg Response Time",
            value="245ms",
            delta="-15ms",
            delta_color="inverse",
            help="Average query response time"
        )
    
    with col4:
        st.metric(
            label="Success Rate",
            value="99.7%",
            delta="+0.2%",
            help="Query success rate"
        )
    
    # Recent Activity
    st.markdown("---")
    st.subheader("📊 System Activity")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Mock data for activity chart
        import numpy as np
        
        hours = list(range(24))
        queries = np.random.randint(50, 150, 24)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=hours,
            y=queries,
            mode='lines+markers',
            name='Queries',
            line=dict(color='#2563eb', width=2),
            fill='tozeroy',
            fillcolor='rgba(37, 99, 235, 0.1)'
        ))
        
        fig.update_layout(
            title="Query Volume (Last 24h)",
            xaxis_title="Hour",
            yaxis_title="Queries",
            height=300,
            margin=dict(l=0, r=0, t=40, b=0),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🔥 Top Patterns")
        
        patterns = {
            "RAG": 342,
            "Chain-of-Thought": 287,
            "ReAct": 198,
            "Tree-of-Thoughts": 156,
            "Self-Reflection": 134
        }
        
        for pattern, count in patterns.items():
            st.markdown(f"**{pattern}**")
            st.progress(count / 400)
            st.caption(f"{count} executions")
            st.markdown("")
    
    # Recent Events
    st.markdown("---")
    st.subheader("📝 Recent Events")
    
    events = [
        {"time": "2 minutes ago", "type": "✅ Success", "message": "MCP 'customer-support' provisioned successfully"},
        {"time": "5 minutes ago", "type": "⚡ Performance", "message": "Response time improved by 15% after optimization"},
        {"time": "12 minutes ago", "type": "🔄 Update", "message": "MCP Store package 'analytics-v2' uploaded"},
        {"time": "18 minutes ago", "type": "⚠️ Warning", "message": "High memory usage detected on training-worker-3"},
        {"time": "25 minutes ago", "type": "✅ Success", "message": "Training job completed for 'product-docs' MCP"},
    ]
    
    for event in events:
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            st.caption(event["time"])
        with col2:
            st.markdown(event["type"])
        with col3:
            st.markdown(event["message"])
    
    # Quick Actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🚀 Provision MCP", use_container_width=True):
            st.info("Navigate to MCP Management to provision a new MCP")
    
    with col2:
        if st.button("🔍 Run Query", use_container_width=True):
            st.info("Navigate to Query Playground to execute queries")
    
    with col3:
        if st.button("📦 Browse Packages", use_container_width=True):
            st.info("Navigate to Marketplace to browse MCP packages")
    
    with col4:
        if st.button("📊 View Metrics", use_container_width=True):
            st.info("Navigate to Performance Monitor for detailed metrics")
