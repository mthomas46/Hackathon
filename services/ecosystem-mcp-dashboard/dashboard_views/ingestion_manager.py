"""
Ingestion Manager Page

Provides controls for:
- Starting new ingestion jobs
- Viewing job status
- Clearing data from all datastores
- Managing ingestion configuration
"""

import streamlit as st
import httpx
from datetime import datetime
import json


def display_active_job(job, api_base_url):
    """Display an active job with live progress indicators."""
    job_id = job.get('job_id', 'Unknown')[:12]
    full_job_id = job.get('job_id', 'Unknown')
    processed = job.get('processed_documents', 0)
    total_docs = job.get('total_documents')
    embeddings = job.get('embeddings_generated', 0)
    
    with st.container():
        # Header with cancel button
        header_col1, header_col2 = st.columns([4, 1])
        with header_col1:
            st.markdown(f"#### ⏳ Job `{job_id}...`")
        with header_col2:
            if st.button("🛑 Cancel", key=f"cancel_active_{job_id}", type="secondary", use_container_width=True):
                st.session_state[f'confirm_cancel_active_{job_id}'] = True
        
        # Cancel confirmation
        if st.session_state.get(f'confirm_cancel_active_{job_id}', False):
            st.warning("⚠️ Cancel this job?")
            conf_col1, conf_col2 = st.columns(2)
            with conf_col1:
                if st.button("✅ Yes, Cancel", key=f"yes_cancel_active_{job_id}", type="primary"):
                    try:
                        response = httpx.post(
                            f"{api_base_url}/api/v1/admin/ingest/{full_job_id}/cancel",
                            timeout=10.0
                        )
                        if response.status_code == 200:
                            st.success("✅ Job cancelled")
                            st.session_state[f'confirm_cancel_active_{job_id}'] = False
                            st.rerun()
                        else:
                            st.error(f"❌ Failed: HTTP {response.status_code}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            with conf_col2:
                if st.button("❌ No", key=f"no_cancel_active_{job_id}"):
                    st.session_state[f'confirm_cancel_active_{job_id}'] = False
                    st.rerun()
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if total_docs and total_docs > 0:
                progress = processed / total_docs
                st.progress(progress)
                st.caption(f"{processed}/{total_docs} documents ({progress*100:.1f}%)")
            else:
                st.progress(0)
                st.caption(f"{processed} documents processed (total unknown)")
        
        with col2:
            st.metric("Embeddings", embeddings)
        
        with col3:
            # Estimate time remaining
            if total_docs and processed > 0:
                remaining = total_docs - processed
                st.metric("Remaining", remaining)
            else:
                st.metric("Status", "Processing")
        
        # Live activity indicator
        st.markdown("🔄 **Active** - Processing documents...")
        
        st.markdown("---")


def show(api_base_url: str):
    """Display ingestion manager page."""
    
    st.title("📥 Ingestion Manager")
    st.markdown("Manage document ingestion and data cleanup operations")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🚀 Start Ingestion", "📊 Job Status", "🗑️ Clear Data"])
    
    # ============================================================================
    # Tab 1: Start Ingestion
    # ============================================================================
    with tab1:
        st.header("🚀 Start New Ingestion")
        
        with st.form("ingestion_form_unique"):
            st.markdown("### Configuration")
            
            # Path type selector
            path_type = st.radio(
                "Path Type",
                options=["Container Path", "Host Machine Path"],
                help="""
                - **Container Path**: Path inside the Docker container (e.g., /app)
                - **Host Machine Path**: Path on your local machine (automatically resolved)
                """
            )
            
            # Repository path
            if path_type == "Host Machine Path":
                # Initialize recent paths in session state with Hackathon as default
                if 'recent_host_paths' not in st.session_state:
                    st.session_state.recent_host_paths = [
                        "/Users/mykalthomas/Documents/work/Hackathon",  # Default primary path
                        "/Users/mykalthomas/Documents/work",
                    ]
                
                # Path selection method
                path_method = st.radio(
                    "Path Selection",
                    options=["Enter Path", "Recent Paths", "Quick Select"],
                    horizontal=True,
                    help="Choose how to specify the repository path"
                )
                
                if path_method == "Enter Path":
                    repo_path = st.text_input(
                        "Repository Path",
                        value="/Users/mykalthomas/Documents/work/Hackathon",
                        help="Path on your host machine (e.g., ~/projects/my-repo). Git root will be auto-detected."
                    )
                    
                    # Show path suggestions
                    with st.expander("💡 Common Path Examples"):
                        st.markdown("""
                        **macOS:**
                        - `/Users/USERNAME/Documents/projects`
                        - `/Users/USERNAME/Developer`
                        - `~/Documents/work`
                        
                        **Linux:**
                        - `/home/USERNAME/projects`
                        - `/opt/projects`
                        - `~/dev`
                        
                        **Windows (WSL):**
                        - `/mnt/c/Users/USERNAME/Documents`
                        - `/mnt/d/projects`
                        """)
                
                elif path_method == "Recent Paths":
                    if st.session_state.recent_host_paths:
                        selected_recent = st.selectbox(
                            "Select from Recent Paths",
                            options=st.session_state.recent_host_paths,
                            help="Previously used paths"
                        )
                        repo_path = selected_recent
                        
                        # Option to clear recent paths
                        if st.button("🗑️ Clear Recent Paths", key="clear_recent"):
                            st.session_state.recent_host_paths = []
                            st.rerun()
                    else:
                        st.info("No recent paths saved. Use 'Enter Path' to add one.")
                        repo_path = "/Users/mykalthomas/Documents/work/Hackathon"
                
                else:  # Quick Select
                    st.markdown("**Quick Select Common Locations:**")
                    
                    # Quick select buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if st.button("📁 Documents", key="quick_docs", use_container_width=True):
                            repo_path = "/Users/mykalthomas/Documents"
                            st.session_state.quick_selected_path = repo_path
                    
                    with col2:
                        if st.button("💼 Work", key="quick_work", use_container_width=True):
                            repo_path = "/Users/mykalthomas/Documents/work"
                            st.session_state.quick_selected_path = repo_path
                    
                    with col3:
                        if st.button("🚀 Hackathon", key="quick_hack", use_container_width=True):
                            repo_path = "/Users/mykalthomas/Documents/work/Hackathon"
                            st.session_state.quick_selected_path = repo_path
                    
                    # Show selected or allow custom
                    if 'quick_selected_path' in st.session_state:
                        repo_path = st.text_input(
                            "Selected Path",
                            value=st.session_state.quick_selected_path,
                            help="You can modify this path if needed"
                        )
                    else:
                        repo_path = st.text_input(
                            "Or Enter Custom Path",
                            value="/Users/mykalthomas/Documents/work/Hackathon",
                            help="Enter a custom path"
                        )
                resolve_host_path = True
                
                # Add path validation button
                if st.form_submit_button("🔍 Validate Path", type="secondary"):
                    with st.spinner("Validating path..."):
                        try:
                            response = httpx.post(
                                f"{api_base_url}/api/v1/path/validate",
                                json={"path": repo_path},
                                timeout=10.0
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                
                                if result["is_valid"]:
                                    st.success(f"✅ {result['message']}")
                                    
                                    # Add to recent paths if valid
                                    if repo_path not in st.session_state.recent_host_paths:
                                        st.session_state.recent_host_paths.insert(0, repo_path)
                                        # Keep only last 10 paths
                                        st.session_state.recent_host_paths = st.session_state.recent_host_paths[:10]
                                    
                                    if result["resolved_path"]:
                                        resolved = result["resolved_path"]
                                        st.info(f"📂 Git Root: `{resolved['git_root']}`")
                                        
                                        # Show if targeting a subdirectory
                                        if resolved.get("is_subdirectory"):
                                            st.info(f"📁 Target Subdirectory: `{resolved['target_subdir']}`")
                                            st.caption("Will ingest only files in this subdirectory")
                                        
                                        if resolved["mount_suggestion"]:
                                            with st.expander("⚙️ Mount Configuration Needed"):
                                                st.code(resolved["mount_suggestion"], language="yaml")
                                else:
                                    st.error(f"❌ {result['message']}")
                            else:
                                st.error(f"❌ Validation failed: HTTP {response.status_code}")
                        
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            else:
                repo_path = st.text_input(
                    "Repository Path",
                    value="/app",
                    help="Path inside the container (e.g., /app)"
                )
                resolve_host_path = False
            
            # Ingestion mode
            mode = st.selectbox(
                "Ingestion Mode",
                options=["quick", "full", "incremental"],
                help="""
                - **quick**: Fast ingestion, skip embeddings
                - **full**: Complete ingestion with embeddings
                - **incremental**: Only process new/changed files
                """
            )
            
            # Service name (for filtering)
            service_name = st.text_input(
                "Service Name (Optional)",
                value="ecosystem-mcp",
                help="Service identifier for filtering"
            )
            
            # Advanced options
            with st.expander("⚙️ Advanced Options"):
                file_patterns = st.text_area(
                    "File Patterns (one per line)",
                    value="*.py\n*.md\n*.yaml\n*.json",
                    help="File patterns to include in ingestion"
                )
                
                exclude_patterns = st.text_area(
                    "Exclude Patterns (one per line)",
                    value="__pycache__\n*.pyc\nvenv\nnode_modules",
                    help="Patterns to exclude from ingestion"
                )
                
                max_file_size_mb = st.number_input(
                    "Max File Size (MB)",
                    value=10,
                    min_value=1,
                    max_value=100,
                    help="Maximum file size to process"
                )
                
                st.markdown("---")
                st.markdown("### 🕐 Temporal Versioning")
                
                enable_versioning = st.checkbox(
                    "Enable Content-Based Versioning",
                    value=True,
                    help="Use temporal content versioning for deduplication and change tracking"
                )
                
                if enable_versioning:
                    st.info("""
                    ✅ **Enabled**: Content-addressable storage with temporal ordering
                    - Deduplicates identical content across versions
                    - Tracks changes with content hashing (SHA-256)
                    - Maintains temporal ordering for history
                    - Enables "as of date" queries
                    """)
                else:
                    st.warning("""
                    ⚠️ **Disabled**: Standard versioning (git-only)
                    - No content deduplication
                    - Relies solely on git commits
                    - Higher storage usage
                    """)
            
            # Submit button
            submit = st.form_submit_button("🚀 Start Ingestion", use_container_width=True)
            
            if submit:
                st.info("⏳ Starting ingestion job...")
                
                # If using host path, validate and resolve it first
                resolved_path = repo_path
                if resolve_host_path:
                    with st.spinner("🔍 Resolving host path..."):
                        try:
                            validate_response = httpx.post(
                                f"{api_base_url}/api/v1/path/validate",
                                json={"path": repo_path},
                                timeout=10.0
                            )
                            
                            if validate_response.status_code == 200:
                                validation = validate_response.json()
                                if validation.get("is_valid"):
                                    resolved_path = validation.get("container_path", repo_path)
                                    st.success(f"✅ Path validated: {resolved_path}")
                                    
                                    # Save to recent paths if successful
                                    if repo_path not in st.session_state.recent_host_paths:
                                        st.session_state.recent_host_paths.insert(0, repo_path)
                                        st.session_state.recent_host_paths = st.session_state.recent_host_paths[:10]
                                else:
                                    st.error(f"❌ Path validation failed: {validation.get('message')}")
                                    st.stop()
                            else:
                                st.warning("⚠️ Could not validate path, using as-is")
                        except Exception as e:
                            st.warning(f"⚠️ Path validation error: {e}")
                            st.info("Continuing with original path...")
                
                # Auto-check worker health before starting
                try:
                    worker_check = httpx.get(
                        f"{api_base_url}/api/v1/admin/workers/ingestion/status",
                        timeout=5.0
                    )
                    
                    if worker_check.status_code == 200:
                        worker_status = worker_check.json()
                        if not worker_status.get("healthy", False):
                            st.warning("⚠️ Worker appears unhealthy, attempting auto-recovery...")
                            
                            # Attempt auto-recovery
                            recovery_response = httpx.post(
                                f"{api_base_url}/api/v1/admin/workers/ingestion/auto-recover",
                                timeout=30.0
                            )
                            
                            if recovery_response.status_code == 200:
                                recovery_result = recovery_response.json()
                                if recovery_result.get("recovered"):
                                    st.success("✅ Worker recovered successfully!")
                                else:
                                    st.info(f"ℹ️ {recovery_result.get('message', 'Worker check complete')}")
                            else:
                                st.warning("⚠️ Could not auto-recover worker, but continuing anyway...")
                except Exception as e:
                    st.warning(f"⚠️ Could not check worker health: {e}")
                    st.info("Continuing with ingestion anyway...")
                
                try:
                    # Prepare request with resolved path
                    request_data = {
                        "repo_path": resolved_path,
                        "mode": mode,
                        "resolve_host_path": False  # Already resolved, don't re-resolve
                    }
                    
                    # Show what we're sending (helpful for debugging)
                    with st.expander("🔍 Request Details", expanded=False):
                        st.json(request_data)
                    
                    # Call ingestion endpoint
                    response = httpx.post(
                        f"{api_base_url}/api/v1/admin/ingest",
                        json=request_data,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ {data.get('message', 'Ingestion started!')}")
                        st.info(f"📋 Job ID: `{data.get('job_id')}`")
                        st.markdown("Monitor progress in the **Job Status** tab")
                    else:
                        # Better error handling
                        try:
                            error_data = response.json()
                            error_detail = error_data.get('detail', 'Unknown error')
                        except:
                            error_detail = response.text or 'Unknown error'
                        
                        st.error(f"❌ Failed to start ingestion (HTTP {response.status_code})")
                        st.error(f"**Error:** {error_detail}")
                        
                        # Provide helpful suggestions based on error
                        if response.status_code == 400:
                            st.warning("""
                            💡 **Common fixes for HTTP 400:**
                            - If using Host Machine Path, try clicking 🔍 Validate Path first
                            - Make sure the path exists and is a git repository
                            - Check if Docker has access to the path
                            - Try using Container Path with /app instead
                            """)
                        elif "mount" in error_detail.lower():
                            st.info("""
                            📌 **Path Mounting Issue:**
                            The host path needs to be mounted in Docker.
                            See the suggested mount configuration above.
                            """)
                        
                except httpx.RequestError as e:
                    st.error(f"❌ Connection error: {e}")
                    st.info("💡 Make sure the ecosystem-mcp service is running")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {e}")
        
        # Quick start guide
        st.markdown("---")
        st.markdown("### 💡 Quick Start")
        st.markdown("""
        **Default Settings:**
        - Path: `/app` (the ecosystem-mcp service directory)
        - Mode: `quick` (fast, no embeddings)
        - Service: `ecosystem-mcp`
        
        **Recommended for First Run:**
        1. Use **full** mode to generate embeddings
        2. Keep default path `/app`
        3. Monitor in Job Status tab
        4. Check ChromaDB Explorer to verify results
        
        **Note:** Ingestion runs in the background via the ingestion worker.
        """)
    
    # ============================================================================
    # Tab 2: Job Status
    # ============================================================================
    with tab2:
        st.header("📊 Ingestion Job Status")
        
        # Controls
        col1, col2, col3, col4 = st.columns([1, 1, 1, 3])
        with col1:
            if st.button("🔄 Refresh Now", use_container_width=True, key="manual_refresh"):
                # Clear any cached data
                if 'job_cache' in st.session_state:
                    del st.session_state['job_cache']
                st.rerun()
        
        with col2:
            auto_refresh = st.checkbox("Auto-refresh", value=False, key="auto_refresh_toggle")
        
        with col3:
            refresh_interval = st.selectbox(
                "Interval",
                options=[3, 5, 10, 15, 30],
                index=1,
                key="refresh_interval",
                disabled=not auto_refresh
            )
        
        with col4:
            filter_status = st.selectbox(
                "Filter",
                options=["All", "processing", "completed", "failed", "queued"],
                key="status_filter"
            )
        
        # Clear jobs section
        st.markdown("---")
        clear_col1, clear_col2, clear_col3 = st.columns([1, 1, 4])
        with clear_col1:
            if st.button("🗑️ Clear Completed", use_container_width=True, key="clear_completed_btn", type="secondary"):
                st.session_state['confirm_clear_completed'] = True
        
        with clear_col2:
            if st.button("🗑️ Clear Failed", use_container_width=True, key="clear_failed_btn", type="secondary"):
                st.session_state['confirm_clear_failed'] = True
        
        # Confirmation dialogs
        if st.session_state.get('confirm_clear_completed', False):
            with st.expander("⚠️ Confirm Clear Completed Jobs", expanded=True):
                st.warning("This will permanently delete all completed job records from the database. This action cannot be undone.")
                conf_col1, conf_col2 = st.columns(2)
                with conf_col1:
                    if st.button("✅ Yes, Clear Completed Jobs", key="confirm_clear_completed_yes", type="primary"):
                        try:
                            response = httpx.delete(
                                f"{api_base_url}/api/v1/admin/jobs/completed",
                                timeout=30.0
                            )
                            if response.status_code == 200:
                                data = response.json()
                                st.success(f"✅ {data.get('message', 'Jobs cleared successfully')}")
                                st.session_state['confirm_clear_completed'] = False
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to clear jobs: HTTP {response.status_code}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                with conf_col2:
                    if st.button("❌ Cancel", key="confirm_clear_completed_no"):
                        st.session_state['confirm_clear_completed'] = False
                        st.rerun()
        
        if st.session_state.get('confirm_clear_failed', False):
            with st.expander("⚠️ Confirm Clear Failed Jobs", expanded=True):
                st.warning("This will permanently delete all failed job records from the database. This action cannot be undone.")
                conf_col1, conf_col2 = st.columns(2)
                with conf_col1:
                    if st.button("✅ Yes, Clear Failed Jobs", key="confirm_clear_failed_yes", type="primary"):
                        try:
                            response = httpx.delete(
                                f"{api_base_url}/api/v1/admin/jobs/failed",
                                timeout=30.0
                            )
                            if response.status_code == 200:
                                data = response.json()
                                st.success(f"✅ {data.get('message', 'Jobs cleared successfully')}")
                                st.session_state['confirm_clear_failed'] = False
                                st.rerun()
                            else:
                                st.error(f"❌ Failed to clear jobs: HTTP {response.status_code}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                with conf_col2:
                    if st.button("❌ Cancel", key="confirm_clear_failed_no"):
                        st.session_state['confirm_clear_failed'] = False
                        st.rerun()
        
        # Auto-refresh - display info only, let user manually refresh
        # Note: Automatic page refresh in tabs context is disabled to prevent navigation loss
        if auto_refresh:
            import time
            
            # Initialize refresh tracking
            if 'manual_refresh_count' not in st.session_state:
                st.session_state.manual_refresh_count = 0
            
            current_time = datetime.now().strftime('%H:%M:%S')
            
            # Show manual refresh button with countdown
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(
                    f"🔄 Auto-refresh mode • Current time: {current_time} • "
                    f"Manual refreshes: {st.session_state.manual_refresh_count}"
                )
            with col2:
                if st.button("🔄 Refresh Now", key="manual_refresh_btn", use_container_width=True):
                    st.session_state.manual_refresh_count += 1
                    st.rerun()
            
            # Add a note about manual refresh
            st.caption(
                f"💡 Tip: Click '🔄 Refresh Now' or refresh your browser to update data. "
                f"Expected refresh interval: {refresh_interval}s"
            )
        
        st.markdown("---")
        
        # Fetch job status
        try:
            response = httpx.get(
                f"{api_base_url}/api/v1/admin/ingest/status",
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                jobs = data.get("jobs", [])
                total = data.get("total", 0)
                
                # Apply status filter
                if filter_status != "All":
                    jobs = [j for j in jobs if j.get('status') == filter_status]
                
                if total == 0:
                    st.info("📭 No ingestion jobs found")
                    st.markdown("Start a new job in the **Start Ingestion** tab")
                else:
                    # Summary metrics
                    active_jobs = [j for j in jobs if j.get('status') == 'processing']
                    completed_jobs = [j for j in jobs if j.get('status') == 'completed']
                    failed_jobs = [j for j in jobs if j.get('status') == 'failed']
                    
                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                    with metric_col1:
                        st.metric("Total Jobs", total)
                    with metric_col2:
                        st.metric("⏳ Processing", len(active_jobs))
                    with metric_col3:
                        st.metric("✅ Completed", len(completed_jobs))
                    with metric_col4:
                        st.metric("❌ Failed", len(failed_jobs))
                    
                    st.markdown("---")
                    
                    # Display active jobs first with progress
                    if active_jobs:
                        st.markdown("### ⏳ Active Jobs")
                        
                        # Live stream viewer for first active job
                        if len(active_jobs) > 0:
                            first_job = active_jobs[0]
                            job_id = first_job.get('job_id', '')
                            
                            with st.expander("📡 Live Progress Stream", expanded=True):
                                st.markdown(f"**Job:** `{job_id[:12]}...`")
                                
                                # Fetch current progress from job data (non-blocking)
                                processed = first_job.get('processed_documents', 0)
                                total = first_job.get('total_documents', 0)
                                skipped = first_job.get('skipped_documents', 0)
                                failed = first_job.get('failed_documents', 0)
                                embeddings = first_job.get('embeddings_generated', 0)
                                
                                # Calculate progress
                                progress_pct = (processed / total * 100) if total > 0 else 0
                                
                                # Display progress bar
                                if total > 0:
                                    st.progress(
                                        min(progress_pct / 100, 1.0),
                                        text=f"{processed}/{total} documents ({progress_pct:.1f}%)"
                                    )
                                else:
                                    st.progress(0, text=f"{processed} documents processed (calculating total...)")
                                
                                # Try to get last file from metadata (non-blocking single request)
                                try:
                                    # Make quick request to get job details with metadata
                                    response = httpx.get(
                                        f"{api_base_url}/api/v1/admin/ingest/{job_id}",
                                        timeout=2.0
                                    )
                                    
                                    if response.status_code == 200:
                                        job_details = response.json()
                                        metadata = job_details.get('job_metadata', {})
                                        
                                        last_file = metadata.get('last_processed_file', '')
                                        current_commit = metadata.get('current_commit', '')
                                        current_file_index = metadata.get('current_file_index', 0)
                                        total_files = metadata.get('total_files_in_commit', 0)
                                        progress_pct = metadata.get('progress_pct', 0)
                                        
                                        if last_file:
                                            # Show detailed file-level progress
                                            st.info(
                                                f"📄 **Current file:** `{last_file}`\n\n"
                                                f"📊 **Progress:** {current_file_index}/{total_files} files ({progress_pct}%)\n\n"
                                                f"🔖 **Commit:** `{current_commit}`"
                                            )
                                            
                                            # Show progress bar for current commit
                                            if total_files > 0:
                                                st.progress(progress_pct / 100.0, text=f"Processing files: {current_file_index}/{total_files}")
                                        else:
                                            st.info("⏳ Starting to process files...")
                                    else:
                                        st.info("⏳ Processing...")
                                        
                                except Exception as e:
                                    st.info("⏳ Processing...")
                                
                                # Display metrics grid
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("Processed", processed)
                                with col2:
                                    st.metric("Skipped", skipped)
                                with col3:
                                    st.metric("Failed", failed)
                                with col4:
                                    st.metric("Embeddings", embeddings)
                                
                                # Auto-refresh hint
                                if auto_refresh:
                                    st.caption(f"🔄 Auto-refreshing every {refresh_interval}s for live updates")
                                else:
                                    st.caption("💡 Enable auto-refresh above for live updates")
                        
                        # Display active jobs
                        for job in active_jobs:
                            display_active_job(job, api_base_url)
                        st.markdown("---")
                    
                    # Display all jobs
                    st.markdown(f"### 📋 All Jobs ({len(jobs)} shown)")
                    
                    # Show jobs in a more compact format
                    for idx, job in enumerate(jobs):
                        job_id = job.get('job_id', 'Unknown')[:12]
                        status = job.get('status', 'unknown')
                        mode = job.get('mode', 'unknown')
                        processed = job.get('processed_documents', 0)
                        total_docs = job.get('total_documents')
                        embeddings = job.get('embeddings_generated', 0)
                        failed = job.get('failed_documents', 0)
                        skipped = job.get('skipped_documents', 0)  # NEW
                        started = job.get('started_at', 'N/A')
                        completed = job.get('completed_at')
                        error = job.get('error_message')
                        
                        # Status emoji
                        status_emoji = {
                            'processing': '⏳',
                            'completed': '✅',
                            'failed': '❌',
                            'queued': '📋'
                        }.get(status, '❓')
                        
                        # Expandable job details
                        with st.expander(f"{status_emoji} {job_id}... - {status.upper()} - {processed} docs", expanded=(status == 'processing')):
                            # Job header
                            header_col1, header_col2, header_col3 = st.columns([3, 1, 1])
                            with header_col1:
                                st.markdown(f"**Job ID:** `{job.get('job_id')}`")
                                st.markdown(f"**Mode:** {mode}")
                            with header_col2:
                                # Copy job ID button
                                if st.button("📋 Copy ID", key=f"copy_{idx}"):
                                    st.code(job.get('job_id'), language=None)
                            with header_col3:
                                # Cancel button (only for processing/queued jobs)
                                if status in ['processing', 'queued']:
                                    if st.button("🛑 Cancel", key=f"cancel_{idx}", type="secondary"):
                                        st.session_state[f'confirm_cancel_{idx}'] = True
                            
                            # Cancel confirmation
                            if st.session_state.get(f'confirm_cancel_{idx}', False):
                                st.warning("⚠️ Are you sure you want to cancel this job?")
                                conf_col1, conf_col2 = st.columns(2)
                                with conf_col1:
                                    if st.button("✅ Yes, Cancel Job", key=f"confirm_cancel_yes_{idx}", type="primary"):
                                        try:
                                            response = httpx.post(
                                                f"{api_base_url}/api/v1/admin/ingest/{job.get('job_id')}/cancel",
                                                timeout=10.0
                                            )
                                            if response.status_code == 200:
                                                data = response.json()
                                                st.success(f"✅ {data.get('message')}")
                                                st.info(data.get('note', ''))
                                                st.session_state[f'confirm_cancel_{idx}'] = False
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Failed to cancel: HTTP {response.status_code}")
                                        except Exception as e:
                                            st.error(f"❌ Error: {str(e)}")
                                with conf_col2:
                                    if st.button("❌ No, Keep Running", key=f"confirm_cancel_no_{idx}"):
                                        st.session_state[f'confirm_cancel_{idx}'] = False
                                        st.rerun()
                            
                            # Progress bar for processing jobs
                            if status == 'processing' and total_docs and total_docs > 0:
                                progress = processed / total_docs
                                st.progress(progress)
                                st.caption(f"Progress: {processed}/{total_docs} documents ({progress*100:.1f}%)")
                            
                            # Metrics
                            st.markdown("#### 📊 Metrics")
                            metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
                            with metric_col1:
                                st.metric("✅ Processed", processed)
                            with metric_col2:
                                st.metric("⏭️  Skipped", skipped, help="Duplicates (not errors)")
                            with metric_col3:
                                st.metric("🧬 Embeddings", embeddings)
                            with metric_col4:
                                st.metric("❌ Failed", failed, delta=None if failed == 0 else f"-{failed}", help="Actual errors")
                            with metric_col5:
                                if total_docs:
                                    remaining = total_docs - processed - skipped
                                    st.metric("📝 Remaining", max(0, remaining))
                                else:
                                    st.metric("📁 Total", "Unknown")
                            
                            # Timeline
                            st.markdown("#### ⏰ Timeline")
                            time_col1, time_col2 = st.columns(2)
                            with time_col1:
                                st.markdown(f"**Started:** {started[:19] if started != 'N/A' else 'N/A'}")
                            with time_col2:
                                if completed:
                                    st.markdown(f"**Completed:** {completed[:19]}")
                                elif status == 'processing':
                                    if started != 'N/A':
                                        try:
                                            start_time = datetime.fromisoformat(started.replace('Z', '+00:00'))
                                            elapsed = datetime.now() - start_time.replace(tzinfo=None)
                                            st.markdown(f"**Elapsed:** {str(elapsed).split('.')[0]}")
                                        except:
                                            st.markdown(f"**Status:** Processing...")
                                    else:
                                        st.markdown(f"**Status:** Processing...")
                            
                            # Error message
                            if error:
                                st.markdown("#### ❌ Error Details")
                                st.error(error)
                            
                            # Status-specific info
                            if status == 'processing':
                                st.info("💡 Job is actively processing. Enable auto-refresh to see live updates.")
                            elif status == 'completed':
                                st.success("✅ Job completed successfully!")
                            elif status == 'failed':
                                st.error("❌ Job failed. Check error details above.")
                            elif status == 'queued':
                                st.info("📋 Job is queued and waiting to be processed.")
                    
            else:
                st.warning(f"⚠️ Could not fetch job status (HTTP {response.status_code})")
                st.info("Try clicking **🔄 Refresh Now** or check if the backend service is running.")
                
        except httpx.RequestError as e:
            st.error(f"❌ Connection error: {e}")
            st.info("💡 Make sure the ecosystem-mcp service is running")
        except Exception as e:
            st.error(f"❌ Error fetching job status: {e}")
            st.exception(e)
    
    # ============================================================================
    # Tab 3: Clear Data
    # ============================================================================
    with tab3:
        st.header("🗑️ Clear Data")
        st.warning("⚠️ **CAUTION:** These operations will permanently delete data!")
        
        st.markdown("### Data Stores")
        
        # PostgreSQL
        with st.expander("🗄️ PostgreSQL (Documents & Metadata)"):
            st.markdown("""
            **Contains:**
            - All ingested documents
            - Document metadata
            - Version history
            - Git commit information
            
            **Impact:** Will delete all documents and their metadata.
            """)
            
            if st.button("🗑️ Clear PostgreSQL", key="clear_postgres", type="secondary"):
                st.session_state.confirm_postgres = True
            
            if st.session_state.get("confirm_postgres", False):
                st.error("⚠️ Are you ABSOLUTELY sure? This cannot be undone!")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, DELETE ALL", key="confirm_postgres_yes", type="primary"):
                        try:
                            response = httpx.delete(
                                f"{api_base_url}/api/v1/admin/data/postgres",
                                timeout=30.0
                            )
                            if response.status_code == 200:
                                st.success("✅ PostgreSQL data cleared!")
                                st.session_state.confirm_postgres = False
                                st.rerun()
                            else:
                                st.error(f"❌ Failed (HTTP {response.status_code})")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                
                with col2:
                    if st.button("❌ Cancel", key="cancel_postgres"):
                        st.session_state.confirm_postgres = False
                        st.rerun()
        
        # ChromaDB
        with st.expander("🔮 ChromaDB (Embeddings)"):
            st.markdown("""
            **Contains:**
            - All document embeddings (768D vectors)
            - Vector metadata
            - Collection data
            
            **Impact:** Will delete all embeddings. Documents in PostgreSQL will remain.
            """)
            
            if st.button("🗑️ Clear ChromaDB", key="clear_chroma", type="secondary"):
                st.session_state.confirm_chroma = True
            
            if st.session_state.get("confirm_chroma", False):
                st.error("⚠️ Are you sure? All embeddings will be deleted!")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, DELETE ALL EMBEDDINGS", key="confirm_chroma_yes", type="primary"):
                        try:
                            response = httpx.delete(
                                f"{api_base_url}/api/v1/admin/data/chromadb",
                                timeout=30.0
                            )
                            if response.status_code == 200:
                                st.success("✅ ChromaDB data cleared!")
                                st.session_state.confirm_chroma = False
                                st.rerun()
                            else:
                                st.error(f"❌ Failed (HTTP {response.status_code})")
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                
                with col2:
                    if st.button("❌ Cancel", key="cancel_chroma"):
                        st.session_state.confirm_chroma = False
                        st.rerun()
        
        # Redis Cache
        with st.expander("⚡ Redis (Cache)"):
            st.markdown("""
            **Contains:**
            - Cached RAG responses
            - Query results
            - Temporary data
            
            **Impact:** Will clear cache. No permanent data loss, but queries will be slower until cache rebuilds.
            """)
            
            if st.button("🗑️ Clear Redis Cache", key="clear_redis", type="secondary"):
                try:
                    response = httpx.delete(
                        f"{api_base_url}/api/v1/admin/clear-all-cache",
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ {data.get('message', 'Cache cleared!')}")
                    else:
                        st.error(f"❌ Failed (HTTP {response.status_code})")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        # Clear ALL
        st.markdown("---")
        st.markdown("### 💣 Nuclear Option")
        st.error("⚠️ **DANGER ZONE:** Clear EVERYTHING and start fresh")
        
        if st.button("💣 Clear ALL Data (PostgreSQL + ChromaDB + Redis)", key="clear_all", type="primary"):
            st.session_state.confirm_nuclear = True
        
        if st.session_state.get("confirm_nuclear", False):
            st.error("🚨 **THIS WILL DELETE EVERYTHING!** 🚨")
            st.error("All documents, embeddings, metadata, and cache will be permanently deleted!")
            
            confirm_text = st.text_input(
                "Type 'DELETE EVERYTHING' to confirm:",
                key="nuclear_confirm_text"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💥 YES, DELETE EVERYTHING", key="nuclear_yes", disabled=(confirm_text != "DELETE EVERYTHING")):
                    with st.spinner("🔥 Clearing all data..."):
                        try:
                            # Clear all in sequence
                            errors = []
                            
                            # 1. Clear PostgreSQL
                            try:
                                resp = httpx.delete(f"{api_base_url}/api/v1/admin/data/postgres", timeout=30.0)
                                if resp.status_code != 200:
                                    errors.append(f"PostgreSQL: {resp.status_code}")
                            except Exception as e:
                                errors.append(f"PostgreSQL: {e}")
                            
                            # 2. Clear ChromaDB
                            try:
                                resp = httpx.delete(f"{api_base_url}/api/v1/admin/data/chromadb", timeout=30.0)
                                if resp.status_code != 200:
                                    errors.append(f"ChromaDB: {resp.status_code}")
                            except Exception as e:
                                errors.append(f"ChromaDB: {e}")
                            
                            # 3. Clear Redis
                            try:
                                resp = httpx.delete(f"{api_base_url}/api/v1/admin/clear-all-cache", timeout=10.0)
                                if resp.status_code != 200:
                                    errors.append(f"Redis: {resp.status_code}")
                            except Exception as e:
                                errors.append(f"Redis: {e}")
                            
                            if errors:
                                st.error(f"❌ Some operations failed: {', '.join(errors)}")
                            else:
                                st.success("✅ ALL DATA CLEARED! System is now empty.")
                            
                            st.session_state.confirm_nuclear = False
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Critical error: {e}")
            
            with col2:
                if st.button("❌ Cancel", key="nuclear_cancel"):
                    st.session_state.confirm_nuclear = False
                    st.rerun()
        
        # Statistics
        st.markdown("---")
        st.markdown("### 📊 Current Data Statistics")
        
        try:
            # Fetch stats from API
            response = httpx.get(
                f"{api_base_url}/api/v1/admin/data/stats",
                timeout=10.0
            )
            
            if response.status_code == 200:
                stats = response.json()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Documents", stats.get("documents", "N/A"))
                with col2:
                    st.metric("Embeddings", stats.get("embeddings", "N/A"))
                with col3:
                    st.metric("Cache Keys", stats.get("cache_keys", "N/A"))
            else:
                st.info("📊 Statistics not available (endpoint not implemented)")
                
        except Exception as e:
            st.info("📊 Statistics temporarily unavailable")

