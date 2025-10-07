"""Training Dashboard - Tight Training Coordinator Integration."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd

from integrations.training_client import TrainingClient

# Page config
st.set_page_config(
    page_title="Training Dashboard",
    page_icon="🎓",
    layout="wide"
)

# Initialize client
@st.cache_resource
def get_training_client():
    return TrainingClient()

training_client = get_training_client()

st.title("🎓 Training Dashboard")
st.markdown("Manage training jobs and monitor progress")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Active Jobs",
    "➕ Create Job",
    "👷 Workers",
    "📈 Analytics"
])

# Tab 1: Active Jobs
with tab1:
    st.subheader("Training Jobs")
    
    # Job filters
    col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 1])
    
    with col_filter1:
        status_filter = st.selectbox(
            "Status",
            ["All", "PENDING", "EXECUTING", "COMPLETED", "FAILED"]
        )
    
    with col_filter2:
        priority_filter = st.selectbox(
            "Priority",
            ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW", "DEFERRED"]
        )
    
    with col_filter3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Simulated jobs (would call training_client.list_jobs())
    jobs = [
        {
            "id": "JOB-001",
            "mcp": "acme-corp-dev",
            "status": "EXECUTING",
            "stage": "EMBEDDING",
            "progress": 65,
            "priority": "HIGH",
            "sources": ["GITHUB", "CONFLUENCE"],
            "started": datetime.now() - timedelta(minutes=45),
            "docs_processed": 6500,
            "total_docs": 10000
        },
        {
            "id": "JOB-002",
            "mcp": "customer-support-kb",
            "status": "EXTRACTING",
            "stage": "EXTRACTING",
            "progress": 30,
            "priority": "MEDIUM",
            "sources": ["SLACK", "JIRA"],
            "started": datetime.now() - timedelta(minutes=20),
            "docs_processed": 2400,
            "total_docs": 8000
        },
        {
            "id": "JOB-003",
            "mcp": "eng-docs",
            "status": "STORING",
            "stage": "STORING",
            "progress": 85,
            "priority": "HIGH",
            "sources": ["GITHUB", "NOTION"],
            "started": datetime.now() - timedelta(hours=1),
            "docs_processed": 8500,
            "total_docs": 10000
        },
    ]
    
    # Display jobs
    for job in jobs:
        with st.expander(f"**{job['id']}** - {job['mcp']} ({job['progress']}%)", expanded=True):
            # Progress bar
            st.progress(job['progress'] / 100)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Status", job['status'])
                st.metric("Stage", job['stage'])
            
            with col2:
                st.metric("Priority", job['priority'])
                st.metric("Sources", ", ".join(job['sources']))
            
            with col3:
                duration = (datetime.now() - job['started']).seconds // 60
                st.metric("Duration", f"{duration}m")
                st.metric("Docs Processed", f"{job['docs_processed']:,}")
            
            with col4:
                st.metric("Total Docs", f"{job['total_docs']:,}")
                completion = (job['docs_processed'] / job['total_docs'] * 100)
                st.metric("Completion", f"{completion:.1f}%")
            
            # Action buttons
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
            
            with col_btn1:
                st.button("⏸️ Pause", key=f"pause_{job['id']}")
            
            with col_btn2:
                st.button("❌ Cancel", key=f"cancel_{job['id']}")
            
            with col_btn3:
                st.button("📋 View Logs", key=f"logs_{job['id']}")
    
    if not jobs:
        st.info("No active training jobs. Create a new job to get started!")

# Tab 2: Create Job
with tab2:
    st.subheader("Create Training Job")
    
    with st.form("create_training_job"):
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            mcp_id = st.selectbox(
                "Select MCP *",
                ["acme-corp-dev", "customer-support-kb", "eng-docs", "sales-playbook"],
                help="MCP instance to train"
            )
            
            priority = st.selectbox(
                "Priority",
                ["CRITICAL", "HIGH", "MEDIUM", "LOW", "DEFERRED"],
                index=2
            )
            
            data_sources = st.multiselect(
                "Data Sources *",
                ["GITHUB", "CONFLUENCE", "JIRA", "SLACK", "NOTION", 
                 "GOOGLE_DRIVE", "FULLSTORY", "AIRTABLE"],
                default=["GITHUB", "CONFLUENCE"],
                help="Select one or more data sources"
            )
        
        with col_form2:
            st.markdown("**Resource Limits**")
            
            max_documents = st.number_input(
                "Max Documents",
                min_value=100,
                max_value=100000,
                value=10000,
                step=1000
            )
            
            max_duration = st.number_input(
                "Max Duration (minutes)",
                min_value=10,
                max_value=480,
                value=120,
                step=10
            )
            
            max_cost = st.number_input(
                "Max Cost ($)",
                min_value=1.0,
                max_value=1000.0,
                value=50.0,
                step=5.0
            )
        
        st.divider()
        
        # Data source configuration
        if "GITHUB" in data_sources:
            with st.expander("⚙️ GitHub Configuration"):
                gh_repos = st.text_area(
                    "Repositories (one per line)",
                    placeholder="owner/repo1\nowner/repo2",
                    height=100
                )
                gh_include_issues = st.checkbox("Include Issues", value=True)
                gh_include_prs = st.checkbox("Include Pull Requests", value=True)
        
        if "CONFLUENCE" in data_sources:
            with st.expander("⚙️ Confluence Configuration"):
                cf_spaces = st.text_input(
                    "Spaces (comma-separated)",
                    placeholder="ENG,PROD,DOCS"
                )
                cf_include_attachments = st.checkbox("Include Attachments", value=True)
        
        st.divider()
        
        col_submit1, col_submit2 = st.columns([1, 3])
        
        with col_submit1:
            submitted = st.form_submit_button(
                "🚀 Start Training",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            if not data_sources:
                st.error("Please select at least one data source")
            else:
                with st.spinner("Creating training job..."):
                    # Would call: training_client.create_job(...)
                    job_id = f"JOB-{datetime.now().timestamp():.0f}"
                    st.success(f"✅ Training job created: {job_id}")
                    st.info("Job has been queued and will start shortly")
                    
                    # Would call: training_client.execute_job(job_id)
                    st.balloons()

# Tab 3: Workers
with tab3:
    st.subheader("Worker Status")
    
    # Simulated worker status (would call training_client.get_worker_status())
    workers = [
        {"type": "Extraction", "active": 3, "limit": 10, "utilization": 30},
        {"type": "Normalization", "active": 2, "limit": 8, "utilization": 25},
        {"type": "Embedding", "active": 1, "limit": 5, "utilization": 20},
        {"type": "Storage", "active": 1, "limit": 3, "utilization": 33},
    ]
    
    for worker in workers:
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 2])
        
        with col1:
            st.markdown(f"### {worker['type']} Workers")
        
        with col2:
            st.metric("Active", worker['active'])
        
        with col3:
            st.metric("Limit", worker['limit'])
        
        with col4:
            st.metric("Utilization", f"{worker['utilization']}%")
        
        with col5:
            st.progress(worker['utilization'] / 100)
        
        st.divider()

# Tab 4: Analytics
with tab4:
    st.subheader("Training Analytics")
    
    col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
    
    with col_metric1:
        st.metric("Total Jobs (30d)", "47", delta="5")
    
    with col_metric2:
        st.metric("Success Rate", "94.7%", delta="2.3%")
    
    with col_metric3:
        st.metric("Avg Duration", "42m", delta="-8m", delta_color="inverse")
    
    with col_metric4:
        st.metric("Total Docs", "487K", delta="52K")
    
    st.divider()
    
    # Training jobs over time
    st.subheader("📈 Training Jobs (Last 30 Days)")
    
    dates = [(datetime.now() - timedelta(days=29-i)).strftime('%m/%d') for i in range(30)]
    job_counts = [1, 2, 1, 3, 2, 1, 2, 3, 2, 1, 2, 3, 4, 2, 1, 
                  2, 3, 2, 4, 3, 2, 1, 2, 3, 2, 1, 3, 2, 1, 2]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dates, y=job_counts, name="Jobs"))
    fig.update_layout(
        height=300,
        xaxis_title="Date",
        yaxis_title="Job Count",
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Success vs Failed
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("✅ Job Status Distribution")
        
        fig_status = go.Figure(data=[go.Pie(
            labels=["Completed", "Failed", "Cancelled"],
            values=[45, 2, 1],
            hole=.3
        )])
        fig_status.update_layout(height=300)
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col_chart2:
        st.subheader("📊 Data Source Usage")
        
        fig_sources = go.Figure(data=[go.Pie(
            labels=["GitHub", "Confluence", "Slack", "Jira", "Other"],
            values=[35, 28, 15, 12, 10],
            hole=.3
        )])
        fig_sources.update_layout(height=300)
        st.plotly_chart(fig_sources, use_container_width=True)

# Footer
st.divider()
st.caption("💡 Tip: Use HIGH priority for urgent training jobs, MEDIUM for routine updates")

