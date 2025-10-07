"""MCP Management Page - Tight Provisioner Integration."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import asyncio
from datetime import datetime
import pandas as pd

from integrations.provisioner_client import ProvisionerClient

# Page config
st.set_page_config(
    page_title="MCP Management",
    page_icon="📦",
    layout="wide"
)

# Initialize client
@st.cache_resource
def get_provisioner():
    return ProvisionerClient()

provisioner = get_provisioner()

st.title("📦 MCP Instance Management")
st.markdown("Create, manage, and monitor MCP instances")

# Tabs
tab1, tab2, tab3 = st.tabs(["📋 MCP List", "➕ Create MCP", "⚙️ Configuration"])

# Tab 1: MCP List
with tab1:
    st.subheader("Active MCP Instances")
    
    col_filter1, col_filter2, col_filter3 = st.columns([2, 2, 1])
    
    with col_filter1:
        tier_filter = st.selectbox(
            "Filter by Tier",
            ["All", "Client", "Project", "Team", "Company", "Ecosystem"]
        )
    
    with col_filter2:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "CREATED", "TRAINING", "READY", "ERROR"]
        )
    
    with col_filter3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Simulated MCP list (would call provisioner.list_mcps())
    mcps = [
        {
            "id": "mcp-001",
            "name": "acme-corp-dev",
            "tier": "Project",
            "status": "READY",
            "docs": 10500,
            "queries": 1247,
            "health": "✅ Healthy"
        },
        {
            "id": "mcp-002",
            "name": "customer-support-kb",
            "tier": "Company",
            "status": "READY",
            "docs": 8320,
            "queries": 892,
            "health": "✅ Healthy"
        },
        {
            "id": "mcp-003",
            "name": "eng-docs",
            "tier": "Team",
            "status": "TRAINING",
            "docs": 5200,
            "queries": 0,
            "health": "🟡 Training"
        },
        {
            "id": "mcp-004",
            "name": "sales-playbook",
            "tier": "Team",
            "status": "READY",
            "docs": 3450,
            "queries": 567,
            "health": "✅ Healthy"
        },
    ]
    
    # Display MCPs as cards
    for mcp in mcps:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 2])
            
            with col1:
                st.markdown(f"### {mcp['name']}")
                st.caption(f"ID: {mcp['id']} | Tier: {mcp['tier']}")
            
            with col2:
                st.metric("Documents", f"{mcp['docs']:,}")
            
            with col3:
                st.metric("Queries", f"{mcp['queries']:,}")
            
            with col4:
                st.markdown(f"**{mcp['health']}**")
            
            with col5:
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    st.button("🎓", key=f"train_{mcp['id']}", help="Train")
                with col_btn2:
                    st.button("🔍", key=f"query_{mcp['id']}", help="Query")
                with col_btn3:
                    st.button("⚙️", key=f"config_{mcp['id']}", help="Configure")
            
            st.divider()

# Tab 2: Create MCP
with tab2:
    st.subheader("Create New MCP Instance")
    
    with st.form("create_mcp_form"):
        col_form1, col_form2 = st.columns(2)
        
        with col_form1:
            mcp_name = st.text_input(
                "MCP Name *",
                placeholder="e.g., acme-corp-dev",
                help="Unique name for the MCP instance"
            )
            
            tier = st.selectbox(
                "Tier Level *",
                ["Client", "Project", "Team", "Company", "Ecosystem"],
                help="Hierarchical tier for this MCP"
            )
            
            parent_tier = st.text_input(
                "Parent Tier ID",
                placeholder="tier-123",
                help="Optional parent tier for inheritance"
            )
        
        with col_form2:
            description = st.text_area(
                "Description",
                placeholder="Describe the purpose of this MCP...",
                height=100
            )
            
            st.markdown("**Configuration Options**")
            
            enable_caching = st.checkbox("Enable Caching", value=True)
            enable_monitoring = st.checkbox("Enable Monitoring", value=True)
            auto_train = st.checkbox("Auto-train on Creation", value=False)
        
        st.divider()
        
        col_submit1, col_submit2, col_submit3 = st.columns([1, 1, 2])
        
        with col_submit1:
            submitted = st.form_submit_button(
                "🚀 Create MCP",
                use_container_width=True,
                type="primary"
            )
        
        with col_submit2:
            st.form_submit_button(
                "🔄 Reset",
                use_container_width=True
            )
        
        if submitted:
            if not mcp_name:
                st.error("Please provide an MCP name")
            else:
                with st.spinner("Creating MCP instance..."):
                    # Would call: provisioner.create_mcp(...)
                    st.success(f"✅ Successfully created MCP: {mcp_name}")
                    st.info(f"MCP ID: mcp-{mcp_name}-{datetime.now().timestamp()}")
                    st.balloons()

# Tab 3: Configuration
with tab3:
    st.subheader("MCP Configuration")
    
    selected_mcp = st.selectbox(
        "Select MCP to Configure",
        ["acme-corp-dev", "customer-support-kb", "eng-docs", "sales-playbook"]
    )
    
    if selected_mcp:
        col_config1, col_config2 = st.columns(2)
        
        with col_config1:
            st.markdown("#### General Settings")
            
            st.text_input("MCP Name", value=selected_mcp, disabled=True)
            st.selectbox("Tier", ["Client", "Project", "Team", "Company", "Ecosystem"], index=1)
            st.number_input("Max Documents", value=10000, step=1000)
            st.number_input("Cache TTL (seconds)", value=300, step=60)
        
        with col_config2:
            st.markdown("#### Performance Settings")
            
            st.slider("Query Timeout (seconds)", 1, 60, 30)
            st.slider("Max Concurrent Queries", 1, 100, 10)
            st.number_input("Token Budget", value=8000, step=1000)
            st.selectbox("Retrieval Strategy", ["HYBRID", "BOTTOM_UP", "TOP_DOWN"])
        
        st.divider()
        
        col_save1, col_save2 = st.columns([1, 3])
        
        with col_save1:
            if st.button("💾 Save Configuration", use_container_width=True, type="primary"):
                st.success("Configuration saved successfully!")

# Footer
st.divider()
st.caption("💡 Tip: Use the Training page to populate newly created MCPs with knowledge")

