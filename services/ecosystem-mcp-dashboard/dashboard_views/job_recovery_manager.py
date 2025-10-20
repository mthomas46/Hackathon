"""
Job Recovery Manager

Frontend interface for managing job checkpoints and recovery.
"""

import streamlit as st
import httpx
import time
from typing import Dict, Any, Optional
from datetime import datetime


def show():
    """Display job recovery management interface."""
    st.title("🔄 Job Recovery Manager")
    
    st.markdown("""
    Monitor and manage checkpoint-based recovery for long-running jobs.
    Jobs can be interrupted and resumed from the last successful checkpoint.
    """)
    
    # API URL
    api_url = st.session_state.get("api_url", "http://ecosystem-mcp-service:8000")
    
    # Tabs for different recovery operations
    tab1, tab2, tab3 = st.tabs([
        "📊 Job Status",
        "🔄 Resume Jobs",
        "🧹 Manage Checkpoints"
    ])
    
    with tab1:
        show_job_status_tab(api_url)
    
    with tab2:
        show_resume_jobs_tab(api_url)
    
    with tab3:
        show_checkpoint_management_tab(api_url)


def show_job_status_tab(api_url: str):
    """Show job status and recovery information."""
    st.header("📊 Job Recovery Status")
    
    st.markdown("""
    Check if jobs can be resumed from checkpoints.
    Enter a job ID to view its recovery status.
    """)
    
    # Job ID input
    job_id = st.text_input(
        "Job ID",
        placeholder="e.g., 2030f30a-d42c-4bf6-a4cc-6ce84cbb8d8e",
        help="Enter the UUID of the job to check"
    )
    
    if st.button("🔍 Check Status", type="primary", disabled=not job_id):
        with st.spinner("Fetching recovery status..."):
            try:
                response = httpx.get(
                    f"{api_url}/api/v1/recovery/status/{job_id}",
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    status = response.json()
                    
                    # Display status
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Job Type", status.get("job_type", "unknown"))
                    
                    with col2:
                        can_resume = status.get("can_resume", False)
                        st.metric(
                            "Can Resume",
                            "✅ Yes" if can_resume else "❌ No"
                        )
                    
                    with col3:
                        incomplete = status.get("incomplete_count", 0)
                        st.metric("Incomplete Checkpoints", incomplete)
                    
                    # Show progress if available
                    if can_resume and status.get("progress"):
                        st.subheader("📈 Progress")
                        
                        progress = status["progress"]
                        completed = progress.get("completed_checkpoints", 0)
                        total = progress.get("total_checkpoints", 0)
                        
                        if total > 0:
                            progress_pct = (completed / total) * 100
                            st.progress(min(progress_pct / 100, 1.0))  # Cap at 1.0 (100%)
                            st.caption(f"{completed}/{total} checkpoints completed ({progress_pct:.1f}%)")
                        
                        # Last checkpoint info
                        if status.get("last_checkpoint"):
                            with st.expander("📌 Last Checkpoint Details"):
                                last_cp = status["last_checkpoint"]
                                st.json(last_cp)
                    
                    elif not can_resume:
                        st.info("ℹ️ This job has no completed checkpoints and cannot be resumed.")
                
                else:
                    st.error(f"❌ Failed to fetch status: HTTP {response.status_code}")
            
            except httpx.TimeoutException:
                st.error("❌ Request timed out")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


def show_resume_jobs_tab(api_url: str):
    """Show interface for resuming interrupted jobs."""
    st.header("🔄 Resume Interrupted Jobs")
    
    st.markdown("""
    Resume jobs from their last successful checkpoint.
    This will continue processing from where the job was interrupted.
    """)
    
    # Job ID and type inputs
    col1, col2 = st.columns([2, 1])
    
    with col1:
        job_id = st.text_input(
            "Job ID",
            placeholder="e.g., 2030f30a-d42c-4bf6-a4cc-6ce84cbb8d8e",
            key="resume_job_id"
        )
    
    with col2:
        job_type = st.selectbox(
            "Job Type",
            ["ingestion", "embedding", "documentation"],
            help="Type of job to resume"
        )
    
    # Resume button
    if st.button("▶️ Resume Job", type="primary", disabled=not job_id):
        with st.spinner(f"Resuming {job_type} job..."):
            try:
                response = httpx.post(
                    f"{api_url}/api/v1/recovery/resume",
                    json={
                        "job_id": job_id,
                        "job_type": job_type
                    },
                    timeout=300.0  # 5 minutes for long-running operations
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success("✅ Job resumed successfully!")
                    
                    # Display resume information
                    with st.expander("📋 Resume Details", expanded=True):
                        st.json(result)
                    
                    # Show result if available
                    if result.get("result"):
                        st.subheader("📊 Result")
                        job_result = result["result"]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Processed", job_result.get("processed", 0))
                        
                        with col2:
                            st.metric("Skipped", job_result.get("skipped", 0))
                        
                        with col3:
                            st.metric("Failed", job_result.get("failed", 0))
                        
                        with col4:
                            success = job_result.get("success", False)
                            st.metric("Status", "✅ Success" if success else "❌ Failed")
                
                elif response.status_code == 400:
                    error = response.json()
                    st.error(f"❌ Cannot resume: {error.get('detail', 'Unknown error')}")
                
                else:
                    st.error(f"❌ Failed to resume: HTTP {response.status_code}")
            
            except httpx.TimeoutException:
                st.warning("⏱️ Request timed out. Job may still be processing in background.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


def show_checkpoint_management_tab(api_url: str):
    """Show checkpoint management interface."""
    st.header("🧹 Checkpoint Management")
    
    st.markdown("""
    View and manage checkpoints for jobs.
    Old checkpoints can be cleaned up to save space.
    """)
    
    # Job ID input
    job_id = st.text_input(
        "Job ID",
        placeholder="e.g., 2030f30a-d42c-4bf6-a4cc-6ce84cbb8d8e",
        key="checkpoint_job_id"
    )
    
    # View checkpoints button
    col1, col2 = st.columns([1, 1])
    
    with col1:
        view_checkpoints = st.button("📋 View Checkpoints", disabled=not job_id)
    
    if view_checkpoints:
        with st.spinner("Fetching checkpoints..."):
            try:
                response = httpx.get(
                    f"{api_url}/api/v1/recovery/checkpoints/{job_id}",
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Display summary
                    st.subheader("📊 Checkpoint Summary")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total", data.get("total_checkpoints", 0))
                    
                    with col2:
                        st.metric("✅ Completed", data.get("completed_checkpoints", 0))
                    
                    with col3:
                        st.metric("⏳ Pending", data.get("pending_checkpoints", 0))
                    
                    with col4:
                        st.metric("❌ Failed", data.get("failed_checkpoints", 0))
                    
                    # Display checkpoint list
                    checkpoints = data.get("checkpoints", [])
                    
                    if checkpoints:
                        st.subheader("📋 Checkpoint List")
                        
                        for cp in checkpoints:
                            status_emoji = {
                                "completed": "✅",
                                "in_progress": "⏳",
                                "pending": "⏸️",
                                "failed": "❌"
                            }.get(cp.get("status"), "❓")
                            
                            with st.expander(
                                f"{status_emoji} Checkpoint #{cp.get('sequence', '?')}: "
                                f"{cp.get('checkpoint_id', 'Unknown')} - "
                                f"{cp.get('status', 'unknown')}"
                            ):
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.caption("**Created:**")
                                    st.text(cp.get("created_at", "Unknown"))
                                    
                                    if cp.get("completed_at"):
                                        st.caption("**Completed:**")
                                        st.text(cp.get("completed_at"))
                                
                                with col2:
                                    st.caption("**Job Type:**")
                                    st.text(cp.get("job_type", "Unknown"))
                                    
                                    st.caption("**Status:**")
                                    st.text(cp.get("status", "Unknown"))
                                
                                if cp.get("data"):
                                    st.caption("**Data:**")
                                    st.json(cp["data"])
                    
                    else:
                        st.info("ℹ️ No checkpoints found for this job.")
                
                else:
                    st.error(f"❌ Failed to fetch checkpoints: HTTP {response.status_code}")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Cleanup section
    st.divider()
    
    st.subheader("🗑️ Cleanup Old Checkpoints")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        keep_last = st.number_input(
            "Keep Last N Checkpoints",
            min_value=1,
            max_value=10,
            value=3,
            help="Number of recent checkpoints to keep"
        )
    
    with col2:
        st.write("")  # Spacer
        st.write("")  # Spacer
        cleanup_btn = st.button("🗑️ Cleanup", type="secondary", disabled=not job_id)
    
    if cleanup_btn:
        with st.spinner("Cleaning up checkpoints..."):
            try:
                response = httpx.delete(
                    f"{api_url}/api/v1/recovery/checkpoints/{job_id}",
                    params={"keep_last": keep_last},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    removed = result.get("removed", 0)
                    
                    if removed > 0:
                        st.success(f"✅ Cleaned up {removed} old checkpoint(s)")
                    else:
                        st.info("ℹ️ No checkpoints to cleanup")
                    
                    # Show before/after
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Before", result.get("checkpoints_before", 0))
                    
                    with col2:
                        st.metric("After", result.get("checkpoints_after", 0))
                
                else:
                    st.error(f"❌ Failed to cleanup: HTTP {response.status_code}")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    show()

