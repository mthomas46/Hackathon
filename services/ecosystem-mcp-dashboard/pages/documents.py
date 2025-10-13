"""Document management page with enhanced metadata display."""

import streamlit as st
import httpx
import json
import sys
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from utils.health_check import HealthChecker


def generate_unique_key(doc_id: str, index: int, prefix: str = "doc") -> str:
    """Generate a guaranteed unique key for Streamlit widgets."""
    doc_hash = hashlib.md5(str(doc_id).encode()).hexdigest()[:8]
    return f"{prefix}_{index}_{doc_hash}"


def format_file_size(bytes_size: int) -> str:
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def fetch_full_document(api_base_url: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch complete document details including content.
    Tries multiple endpoints to get the most complete data.
    """
    # Try the query endpoint first (should have content)
    try:
        response = httpx.get(
            f"{api_base_url}/api/v1/query/document/{doc_id}",
            timeout=5.0
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    # Try the documents endpoint
    try:
        response = httpx.get(
            f"{api_base_url}/api/v1/documents/{doc_id}",
            timeout=5.0
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    
    return None


def show(api_base_url: str):
    """Show documents page with enhanced metadata."""
    st.title("📚 Document Management")
    
    # Debug toggle
    debug_mode = st.sidebar.checkbox("🐛 Debug Mode", value=False, key="debug_toggle")
    
    if debug_mode:
        st.sidebar.markdown("### Debug Info")
        st.sidebar.markdown(f"**Script run at:** {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
        if 'widget_keys' not in st.session_state:
            st.session_state.widget_keys = []
        st.sidebar.markdown(f"**Keys created this run:** {len(st.session_state.widget_keys)}")
        st.session_state.widget_keys = []
    
    # Check API health
    health_checker = HealthChecker(api_base_url)
    if not health_checker.require_healthy_api(show_status=True):
        st.stop()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Browse Documents", "➕ Ingest Documents", "📊 Ingestion Jobs"])
    
    with tab1:
        st.subheader("Browse Documents")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        
        with col1:
            limit = st.number_input("Limit", min_value=1, max_value=100, value=20, key="doc_limit")
        
        with col2:
            service_filter = st.text_input("Service Filter", placeholder="Leave empty for all", key="service_filter")
        
        with col3:
            if st.button("🔍 Search", use_container_width=True, key="search_btn"):
                st.rerun()
        
        try:
            # Fetch documents
            params = {"limit": limit, "offset": 0}
            if service_filter:
                params["service"] = service_filter
            
            response = httpx.get(
                f"{api_base_url}/api/v1/documents",
                params=params,
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                documents = data.get("documents", [])
                total = data.get("total", 0)
                
                # Summary
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.metric("Total Documents", f"{total:,}")
                with col_b:
                    st.metric("Showing", len(documents))
                with col_c:
                    has_more = data.get("has_next", False)
                    st.metric("More Pages", "Yes" if has_more else "No")
                
                if not documents:
                    st.info("No documents found. Try ingesting some documents first!")
                    return
                
                # Track keys for debugging
                keys_used = set()
                
                # Display documents
                for i, doc in enumerate(documents):
                    doc_id = doc.get('id', f'unknown_{i}')
                    file_path = doc.get('file_path', 'Unknown')
                    
                    # Generate unique keys
                    widget_key = generate_unique_key(doc_id, i, "content")
                    
                    if debug_mode:
                        if widget_key in keys_used:
                            st.error(f"⚠️ DUPLICATE KEY: {widget_key}")
                        keys_used.add(widget_key)
                        st.session_state.widget_keys.append(widget_key)
                    
                    # Document expander with more info in title
                    file_type = doc.get('original_format', 'unknown')
                    word_count = doc.get('word_count', 0)
                    expander_title = f"📄 {file_path[:70]} · {file_type.upper()} · {word_count:,} words"
                    
                    with st.expander(expander_title, expanded=False):
                        if debug_mode:
                            st.caption(f"🔑 Key: `{widget_key}` | ID: `{doc_id}` | Index: {i}")
                        
                        # Metadata columns
                        col_left, col_mid, col_right = st.columns(3)
                        
                        with col_left:
                            st.markdown("### 📋 Basic Info")
                            st.markdown(f"**ID:** `{doc_id[:8]}...`")
                            st.markdown(f"**Service:** {doc.get('service_name', 'unknown')}")
                            st.markdown(f"**Format:** {file_type}")
                            st.markdown(f"**Latest:** {'✅ Yes' if doc.get('is_latest') else '❌ No'}")
                        
                        with col_mid:
                            st.markdown("### 📊 Content Stats")
                            st.markdown(f"**Word Count:** {word_count:,}")
                            
                            # Try to calculate content size if available
                            # We'll fetch it below
                            st.markdown(f"**Path:** `{file_path}`")
                        
                        with col_right:
                            st.markdown("### 🕐 Timestamps")
                            created = doc.get('created_at', 'N/A')
                            updated = doc.get('updated_at', 'N/A')
                            st.markdown(f"**Created:** {created[:19] if created != 'N/A' else 'N/A'}")
                            st.markdown(f"**Updated:** {updated[:19] if updated != 'N/A' else 'N/A'}")
                        
                        st.markdown("---")
                        
                        # Content section
                        st.markdown("### 📄 Content Preview")
                        
                        # Fetch full document to get content
                        with st.spinner("Loading content..."):
                            full_doc = fetch_full_document(api_base_url, doc_id)
                            
                            if full_doc:
                                # Try to get content from various fields
                                content = (
                                    full_doc.get('normalized_content') or 
                                    full_doc.get('original_content') or
                                    full_doc.get('content') or
                                    ''
                                )
                                
                                if content and len(content.strip()) > 0:
                                    # Show content
                                    content_size = len(content.encode('utf-8'))
                                    preview_length = 3000
                                    preview_text = content[:preview_length]
                                    if len(content) > preview_length:
                                        preview_text += "\n\n... (content truncated)"
                                    
                                    # Content stats
                                    stats_col1, stats_col2, stats_col3 = st.columns(3)
                                    with stats_col1:
                                        st.metric("Content Size", format_file_size(content_size))
                                    with stats_col2:
                                        st.metric("Characters", f"{len(content):,}")
                                    with stats_col3:
                                        st.metric("Lines", f"{content.count(chr(10)):,}")
                                    
                                    # Text area with content
                                    st.text_area(
                                        "Content",
                                        value=preview_text,
                                        height=300,
                                        disabled=True,
                                        key=widget_key,
                                        label_visibility="collapsed"
                                    )
                                    
                                    # Additional metadata from full doc
                                    if full_doc.get('metadata') or full_doc.get('doc_metadata'):
                                        with st.expander("📦 Additional Metadata"):
                                            metadata = full_doc.get('metadata') or full_doc.get('doc_metadata', {})
                                            if metadata:
                                                st.json(metadata)
                                            else:
                                                st.info("No additional metadata")
                                    
                                    if debug_mode:
                                        st.caption(f"✅ Loaded {len(content):,} chars | Showing {len(preview_text):,}")
                                else:
                                    # Empty content
                                    st.warning(f"""
                                    **⚠️ No Content Stored**
                                    
                                    This document exists in the database but has no content stored.
                                    
                                    **Possible reasons:**
                                    - Document was indexed without content extraction
                                    - Content extraction failed during ingestion
                                    - Database needs re-ingestion
                                    
                                    **To fix:** 
                                    1. Go to the "➕ Ingest Documents" tab
                                    2. Re-ingest with mode "full"
                                    3. Ensure the source file still exists at: `{file_path}`
                                    """)
                            else:
                                # Could not fetch document
                                st.error(f"""
                                **❌ Could Not Load Document**
                                
                                Failed to fetch full document details from the API.
                                
                                **Tried:**
                                - `/api/v1/query/document/{doc_id}`
                                - `/api/v1/documents/{doc_id}`
                                
                                This might indicate:
                                - Document was deleted
                                - API endpoint issue
                                - Database inconsistency
                                """)
                
                # Debug summary
                if debug_mode:
                    st.markdown("---")
                    st.markdown("### 🔍 Debug Summary")
                    st.markdown(f"- **Documents:** {len(documents)}")
                    st.markdown(f"- **Unique keys:** {len(keys_used)}")
                    st.markdown(f"- **Duplicates:** {len(documents) - len(keys_used)}")
                    
                    if len(documents) == len(keys_used):
                        st.success("✅ All keys unique")
                    else:
                        st.error("⚠️ Duplicate keys detected!")
                    
                    with st.expander("View all keys"):
                        for idx, key in enumerate(sorted(keys_used)):
                            st.code(f"{idx}: {key}")
            
            else:
                st.error(f"Failed to fetch documents: HTTP {response.status_code}")
                if debug_mode:
                    st.code(response.text[:500])
        
        except httpx.TimeoutException:
            st.error("⏱️ Request timed out. API may be slow or unavailable.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            if debug_mode:
                import traceback
                st.code(traceback.format_exc())
    
    with tab2:
        st.subheader("Ingest New Documents")
        
        st.info("""
        **💡 Tip:** Use "full" mode to ensure content is extracted and stored.
        
        - **quick**: Fast indexing (metadata only)
        - **full**: Complete analysis with content extraction ✅ Recommended
        - **incremental**: Only new/changed files
        """)
        
        with st.form("ingest_form"):
            repo_path = st.text_input(
                "Repository Path",
                value="/Users/mykalthomas/Documents/work/Hackathon",
                help="Full path to repository to ingest"
            )
            
            mode = st.selectbox(
                "Ingestion Mode",
                ["full", "quick", "incremental"],
                index=0,  # Default to "full"
                help="full = Complete analysis with content (recommended)"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                batch_size = st.number_input("Batch Size", min_value=1, max_value=100, value=10)
            with col2:
                include_git = st.checkbox("Include Git History", value=True)
            
            submitted = st.form_submit_button("🚀 Start Ingestion", use_container_width=True)
        
        if submitted and repo_path:
            with st.spinner("Starting ingestion..."):
                try:
                    response = httpx.post(
                        f"{api_base_url}/api/v1/admin/ingest",
                        json={"repository_path": repo_path, "mode": mode},
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"✅ Ingestion job started!")
                        st.json(data)
                        st.info("Check the 'Ingestion Jobs' tab to monitor progress.")
                    else:
                        st.error(f"Failed: HTTP {response.status_code}")
                        st.code(response.text)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        elif submitted:
            st.warning("Please provide a repository path")
    
    with tab3:
        st.subheader("Ingestion Jobs")
        
        if st.button("🔄 Refresh", use_container_width=True, key="refresh_jobs"):
            st.rerun()
        
        try:
            response = httpx.get(f"{api_base_url}/api/v1/admin/queue-status", timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                
                # Stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Pending", data.get("pending_count", 0))
                with col2:
                    st.metric("Processed", data.get("total_processed", 0))
                with col3:
                    st.metric("Queue Length", data.get("queue_length", 0))
                
                # Jobs
                st.markdown("---")
                jobs = data.get("jobs", [])
                
                if jobs:
                    for idx, job in enumerate(jobs):
                        status = job.get("status", "unknown")
                        job_id = job.get('job_id', f'job_{idx}')
                        
                        status_icons = {
                            "completed": "✅",
                            "failed": "❌",
                            "processing": "⚙️"
                        }
                        icon = status_icons.get(status, "⏳")
                        
                        job_key = f"job_{idx}_{hashlib.md5(str(job_id).encode()).hexdigest()[:8]}"
                        
                        with st.expander(f"{icon} {str(job_id)[:8]}... - {status}", key=job_key):
                            st.json(job)
                else:
                    st.info("No recent jobs")
            else:
                st.error(f"Failed to fetch jobs: HTTP {response.status_code}")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
            if debug_mode:
                import traceback
                st.code(traceback.format_exc())
