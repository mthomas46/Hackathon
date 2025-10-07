"""MCP Dashboard - Home Page with System Overview."""

import sys
from pathlib import Path
import asyncio

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd

from integrations.training_client import TrainingClient
from integrations.provisioner_client import ProvisionerClient
from integrations.interpreter_client import InterpreterClient
from integrations.retrieval_client import RetrievalClient

# Page config
st.set_page_config(
    page_title="MCP Dashboard - Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize clients
@st.cache_resource
def get_clients():
    """Initialize service clients (cached)."""
    return {
        "training": TrainingClient(),
        "provisioner": ProvisionerClient(),
        "interpreter": InterpreterClient(),
        "retrieval": RetrievalClient()
    }

clients = get_clients()

# Header
st.title("🏠 MCP Ecosystem Dashboard")
st.markdown("**Unified Control Plane for Model Context Protocol Services**")

# Real-time refresh
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.markdown(f"*Last updated: {st.session_state.last_refresh.strftime('%H:%M:%S')}*")
with col_header2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.session_state.last_refresh = datetime.now()
        st.rerun()

st.divider()

# System Health Overview
st.header("📊 System Health Overview")

# Create 4 columns for key metrics
col1, col2, col3, col4 = st.columns(4)

# Fetch system data (simulated - would call real APIs)
with col1:
    st.metric(
        label="🎯 Active MCPs",
        value="23",
        delta="2 today",
        help="Total number of active MCP instances"
    )

with col2:
    st.metric(
        label="🎓 Training Jobs",
        value="5",
        delta="-1",
        delta_color="inverse",
        help="Currently executing training jobs"
    )

with col3:
    st.metric(
        label="🔍 Queries Today",
        value="1,247",
        delta="+184",
        help="Total queries executed today"
    )

with col4:
    st.metric(
        label="✅ Service Health",
        value="100%",
        delta="All systems operational",
        help="Percentage of healthy services"
    )

st.divider()

# Two-column layout
col_left, col_right = st.columns([2, 1])

with col_left:
    # Training Jobs Status
    st.subheader("🎓 Training Jobs Status")
    
    # Simulated job data (would call training_client.list_jobs())
    jobs_data = [
        {"Job ID": "JOB-001", "MCP": "acme-corp-dev", "Status": "EXECUTING", "Progress": 65, "Priority": "HIGH"},
        {"Job ID": "JOB-002", "MCP": "customer-support", "Status": "EXTRACTING", "Progress": 30, "Priority": "MEDIUM"},
        {"Job ID": "JOB-003", "MCP": "eng-docs", "Status": "EMBEDDING", "Progress": 70, "Priority": "HIGH"},
        {"Job ID": "JOB-004", "MCP": "sales-kb", "Status": "STORING", "Progress": 85, "Priority": "MEDIUM"},
        {"Job ID": "JOB-005", "MCP": "hr-policies", "Status": "VALIDATING", "Progress": 15, "Priority": "LOW"},
    ]
    
    df_jobs = pd.DataFrame(jobs_data)
    
    # Display with progress bars
    for _, job in df_jobs.iterrows():
        with st.container():
            col_job1, col_job2, col_job3, col_job4 = st.columns([2, 2, 1, 1])
            
            with col_job1:
                st.text(f"**{job['Job ID']}**")
                st.caption(job['MCP'])
            
            with col_job2:
                st.progress(job['Progress'] / 100)
                st.caption(f"{job['Progress']}% - {job['Status']}")
            
            with col_job3:
                priority_colors = {
                    "HIGH": "🔴",
                    "MEDIUM": "🟡",
                    "LOW": "🟢"
                }
                st.text(f"{priority_colors.get(job['Priority'], '⚪')} {job['Priority']}")
            
            with col_job4:
                st.button("📊", key=f"view_{job['Job ID']}", help="View details")
    
    st.divider()
    
    # Query Activity Chart
    st.subheader("🔍 Query Activity (Last 24h)")
    
    # Generate sample data
    hours = [(datetime.now() - timedelta(hours=23-i)).strftime('%H:00') for i in range(24)]
    query_counts = [45, 52, 38, 41, 67, 89, 102, 134, 156, 178, 165, 142, 
                   138, 152, 167, 189, 201, 187, 165, 143, 128, 98, 76, 54]
    
    fig_queries = go.Figure()
    fig_queries.add_trace(go.Scatter(
        x=hours,
        y=query_counts,
        mode='lines+markers',
        name='Queries',
        fill='tozeroy',
        line=dict(color='#1f77b4', width=2),
        marker=dict(size=6)
    ))
    
    fig_queries.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis_title="Hour",
        yaxis_title="Query Count",
        showlegend=False,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_queries, use_container_width=True)

with col_right:
    # Service Status Grid
    st.subheader("🔧 Service Status")
    
    services = [
        {"name": "Gateway", "port": 8001, "status": "✅"},
        {"name": "Interpreter", "port": 8002, "status": "✅"},
        {"name": "Provisioner", "port": 8003, "status": "✅"},
        {"name": "Orchestrator", "port": 8004, "status": "✅"},
        {"name": "Composer", "port": 8005, "status": "✅"},
        {"name": "Registry", "port": 8006, "status": "✅"},
        {"name": "Infrastructure", "port": 8007, "status": "✅"},
        {"name": "Store", "port": 8008, "status": "✅"},
        {"name": "Performance", "port": 8009, "status": "✅"},
        {"name": "Logging", "port": 8010, "status": "✅"},
        {"name": "Logs MCP", "port": 8011, "status": "✅"},
        {"name": "Package Mgr", "port": 8012, "status": "✅"},
        {"name": "Tier Manager", "port": 8013, "status": "✅"},
        {"name": "Retrieval", "port": 8014, "status": "✅"},
        {"name": "Dashboard", "port": 8015, "status": "✅"},
        {"name": "Training Coord", "port": 5600, "status": "✅"},
    ]
    
    df_services = pd.DataFrame(services)
    
    for _, service in df_services.iterrows():
        col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
        with col_s1:
            st.text(f"{service['status']} {service['name']}")
        with col_s2:
            st.caption(f":{service['port']}")
        with col_s3:
            st.caption("< 50ms")
    
    st.divider()
    
    # Recent Queries
    st.subheader("💬 Recent Queries")
    
    recent_queries = [
        {"query": "API best practices?", "time": "2m ago", "mcp": "eng-docs"},
        {"query": "How to deploy?", "time": "5m ago", "mcp": "ops-kb"},
        {"query": "Customer pricing", "time": "8m ago", "mcp": "sales-kb"},
        {"query": "Leave policy", "time": "12m ago", "mcp": "hr-policies"},
        {"query": "Database setup", "time": "15m ago", "mcp": "eng-docs"},
    ]
    
    for q in recent_queries:
        with st.container():
            st.caption(f"🔍 {q['query']}")
            st.text(f"   {q['mcp']} • {q['time']}")
            st.divider()

# Bottom section
st.header("🎯 Quick Actions")

col_action1, col_action2, col_action3, col_action4 = st.columns(4)

with col_action1:
    if st.button("📦 Create New MCP", use_container_width=True, type="primary"):
        st.switch_page("pages/1_📦_MCP_Management.py")

with col_action2:
    if st.button("🎓 Start Training Job", use_container_width=True):
        st.switch_page("pages/2_🎓_Training.py")

with col_action3:
    if st.button("🔍 Execute Query", use_container_width=True):
        st.switch_page("pages/3_🔍_Query.py")

with col_action4:
    if st.button("📊 View Analytics", use_container_width=True):
        st.switch_page("pages/7_📊_Analytics.py")

# System Information Footer
st.divider()
col_footer1, col_footer2, col_footer3 = st.columns(3)

with col_footer1:
    st.caption("🚀 **MCP Ecosystem v1.0.0**")
    st.caption("83% Complete (8.3/10 phases)")

with col_footer2:
    st.caption("📊 **Total Services:** 17")
    st.caption("💾 **Total Storage:** 2.3 TB")

with col_footer3:
    st.caption("👥 **Active Users:** 47")
    st.caption("📈 **Uptime:** 99.97%")

# Auto-refresh every 30 seconds
import time
time.sleep(30)
st.rerun()

