"""Document management page."""

import streamlit as st
import httpx
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.health_check import HealthChecker

def show(api_base_url: str):
    """Show documents page."""
    st.title("📚 Document Management")
    
    # Check API health before proceeding
    health_checker = HealthChecker(api_base_url)
    if not health_checker.require_healthy_api(show_status=True):
        st.stop()  # Stop rendering if API is not healthy
    
    # Tabs for different operations
    tab1, tab2, tab3 = st.tabs(["📋 Browse Documents", "➕ Ingest Documents", "📊 Ingestion Jobs"])
    
    with tab1:
        st.subheader("Browse Documents")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            limit = st.number_input("Limit", min_value=1, max_value=100, value=20)
        
        with col2:
            file_type = st.selectbox("File Type", ["All", "md", "py", "txt", "json"])
        
        with col3:
            if st.button("🔍 Search", use_container_width=True):
                st.rerun()
        
        try:
            # Fetch documents using the documents endpoint
            response = httpx.get(
                f"{api_base_url}/api/v1/documents",
                params={"limit": limit, "offset": 0},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get("documents", [])
                
                st.info(f"Found {len(documents)} documents")
                
                for doc in documents:
                    with st.expander(f"📄 {doc.get('file_path', 'Unknown')[:80]}"):
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.markdown(f"**ID:** `{doc.get('id', 'N/A')}`")
                            st.markdown(f"**Type:** {doc.get('file_type', 'N/A')}")
                            st.markdown(f"**Size:** {doc.get('size', 0)} bytes")
                        
                        with col_b:
                            if doc.get('git_commit'):
                                st.markdown(f"**Commit:** `{doc.get('git_commit')[:8]}`")
                            st.markdown(f"**Created:** {doc.get('created_at', 'N/A')}")
                        
                        # Content preview
                        content = doc.get('content', 'No content available')
                        st.text_area(
                            "Content Preview",
                            value=content[:1000] + "..." if len(content) > 1000 else content,
                            height=200,
                            disabled=True
                        )
            else:
                st.error(f"Failed to fetch documents: {response.status_code}")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    with tab2:
        st.subheader("Ingest New Documents")
        
        with st.form("ingest_form"):
            repo_path = st.text_input(
                "Repository Path",
                placeholder="/path/to/repository",
                help="Full path to Git repository to ingest"
            )
            
            mode = st.selectbox(
                "Ingestion Mode",
                ["quick", "full", "incremental"],
                help="quick: Fast scan, full: Complete analysis, incremental: Only new changes"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                batch_size = st.number_input("Batch Size", min_value=1, max_value=100, value=10)
            
            with col2:
                include_git_history = st.checkbox("Include Git History", value=True)
            
            submitted = st.form_submit_button("🚀 Start Ingestion", use_container_width=True)
        
        if submitted and repo_path:
            with st.spinner("Starting ingestion..."):
                try:
                    response = httpx.post(
                        f"{api_base_url}/api/v1/admin/ingest",
                        json={
                            "repository_path": repo_path,
                            "mode": mode
                        },
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ Ingestion job started!")
                        st.json(data)
                    else:
                        st.error(f"Failed to start ingestion: {response.status_code}")
                        st.code(response.text)
                
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        elif submitted:
            st.warning("Please provide a repository path")
    
    with tab3:
        st.subheader("Ingestion Jobs")
        
        if st.button("🔄 Refresh Jobs", use_container_width=True):
            st.rerun()
        
        try:
            # Fetch queue status
            response = httpx.get(
                f"{api_base_url}/api/v1/admin/queue-status",
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Show stats
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Pending Jobs", data.get("pending_count", 0))
                
                with col2:
                    st.metric("Total Processed", data.get("total_processed", 0))
                
                with col3:
                    st.metric("Queue Length", data.get("queue_length", 0))
                
                # Show recent jobs
                st.markdown("---")
                jobs = data.get("jobs", [])
                
                if jobs:
                    for job in jobs:
                        status = job.get("status", "unknown")
                        
                        if status == "completed":
                            status_icon = "✅"
                        elif status == "failed":
                            status_icon = "❌"
                        elif status == "processing":
                            status_icon = "⚙️"
                        else:
                            status_icon = "⏳"
                        
                        with st.expander(f"{status_icon} Job {job.get('job_id', 'N/A')[:8]}... - {status}"):
                            st.json(job)
                else:
                    st.info("No recent jobs")
            
            else:
                st.error(f"Failed to fetch jobs: {response.status_code}")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")

