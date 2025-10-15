"""
Documentation Browser Dashboard Page

Browse and manage documentation generation runs:
- View run history
- Browse generated documents
- Export runs as ZIP
- View document content
- Delete runs
"""

import streamlit as st
import httpx
import pandas as pd
from datetime import datetime
import json

# Get API URL from session state or environment
API_URL = st.session_state.get("api_url", "http://localhost:8000")


def show():
    """Display the Documentation Browser page."""
    st.title("📚 Documentation Browser")
    st.write("Browse and manage documentation generation runs")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "📋 Run History",
        "📄 Documents",
        "📊 Statistics"
    ])
    
    with tab1:
        show_run_history()
    
    with tab2:
        show_documents_tab()
    
    with tab3:
        show_statistics()


def show_run_history():
    """Show list of documentation runs."""
    st.subheader("📋 Documentation Run History")
    
    # Filters
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        status_filter = st.selectbox(
            "Filter by Status",
            ["All", "pending", "running", "completed", "failed", "cancelled"],
            key="run_status_filter"
        )
    
    with col2:
        limit = st.number_input("Results per page", min_value=10, max_value=100, value=20)
    
    with col3:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Fetch runs
    try:
        params = {"limit": limit, "offset": 0}
        if status_filter != "All":
            params["status"] = status_filter
        
        response = httpx.get(
            f"{API_URL}/api/v1/documentation/runs",
            params=params,
            timeout=30.0
        )
        
        if response.status_code == 200:
            runs = response.json()
            
            if not runs:
                st.info("📭 No documentation runs found")
                return
            
            st.success(f"✅ Found {len(runs)} runs")
            
            # Display runs
            for run in runs:
                display_run_card(run)
        
        else:
            st.error(f"❌ Failed to fetch runs: HTTP {response.status_code}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def display_run_card(run: dict):
    """Display a run as an expandable card."""
    # Status badge
    status_colors = {
        "pending": "🟡",
        "running": "🔵",
        "completed": "🟢",
        "failed": "🔴",
        "cancelled": "⚪"
    }
    
    status_icon = status_colors.get(run["status"], "⚪")
    
    # Calculate duration
    duration = run.get("duration_seconds")
    duration_str = f"{duration}s" if duration else "N/A"
    
    with st.expander(f"{status_icon} **{run['name']}** ({run['status']}) - {run['total_documents']} docs"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Description:** {run['description'] or 'No description'}")
            st.text(f"Source: {run['source_directory']}")
            st.text(f"Created: {format_datetime(run['created_at'])}")
            
            if run.get('started_at'):
                st.text(f"Started: {format_datetime(run['started_at'])}")
            
            if run.get('completed_at'):
                st.text(f"Completed: {format_datetime(run['completed_at'])}")
                st.text(f"Duration: {duration_str}")
        
        with col2:
            st.metric("Total Docs", run['total_documents'])
            st.metric("Successful", run['successful_documents'], delta=None)
            st.metric("Failed", run['failed_documents'], delta=None if run['failed_documents'] == 0 else f"-{run['failed_documents']}")
        
        # Action buttons
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        
        with col_btn1:
            if st.button("📄 View Documents", key=f"view_{run['id']}"):
                st.session_state['selected_run_id'] = run['id']
                st.session_state['view_run_documents'] = True
                st.rerun()
        
        with col_btn2:
            if st.button("📊 Details", key=f"details_{run['id']}"):
                show_run_details(run['id'])
        
        with col_btn3:
            if run['status'] == 'completed' and run['total_documents'] > 0:
                if st.button("📥 Export ZIP", key=f"export_{run['id']}"):
                    export_run_as_zip(run['id'], run['name'])
        
        with col_btn4:
            if run['status'] in ['completed', 'failed', 'cancelled']:
                if st.button("🗑️ Delete", key=f"delete_{run['id']}", type="secondary"):
                    if st.session_state.get(f"confirm_delete_{run['id']}", False):
                        delete_run(run['id'])
                    else:
                        st.session_state[f"confirm_delete_{run['id']}"] = True
                        st.warning("⚠️ Click again to confirm deletion")
        
        # Show progress for running jobs
        if run['status'] == 'running':
            show_run_progress(run['id'])


def show_run_progress(run_id: str):
    """Show real-time progress for a running job."""
    try:
        response = httpx.get(
            f"{API_URL}/api/v1/documentation/runs/{run_id}/progress",
            timeout=10.0
        )
        
        if response.status_code == 200:
            progress = response.json()
            
            if progress:
                st.markdown("**📈 Progress:**")
                
                # Progress bar
                progress_pct = progress.get('progress_percentage', 0)
                st.progress(progress_pct / 100.0, text=f"{progress_pct:.1f}%")
                
                # Current operation
                st.text(progress.get('current_operation', 'Processing...'))
                
                # Stats
                col1, col2 = st.columns(2)
                with col1:
                    st.text(f"Pass: {progress['current_pass']}/{progress['total_passes']}")
                    st.text(f"Question: {progress['current_question']}/{progress['total_questions']}")
                
                with col2:
                    st.text(f"Generated: {progress['documents_generated']}")
                    st.text(f"Failed: {progress['documents_failed']}")
    
    except Exception as e:
        st.warning(f"Could not fetch progress: {str(e)}")


def show_run_details(run_id: str):
    """Show detailed information about a run."""
    try:
        response = httpx.get(
            f"{API_URL}/api/v1/documentation/runs/{run_id}",
            timeout=30.0
        )
        
        if response.status_code == 200:
            run = response.json()
            
            st.markdown("### 📊 Run Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Configuration:**")
                st.json({
                    "Output Format": run['output_format'],
                    "Response Size": run.get('response_size', 'Default'),
                    "Tier": run.get('tier', 'Auto'),
                    "Passes": run['num_passes'],
                    "Questions per Pass": run['questions_per_pass']
                })
            
            with col2:
                st.markdown("**Timing:**")
                st.text(f"Created: {format_datetime(run['created_at'])}")
                st.text(f"Started: {format_datetime(run.get('started_at')) if run.get('started_at') else 'N/A'}")
                st.text(f"Completed: {format_datetime(run.get('completed_at')) if run.get('completed_at') else 'N/A'}")
                st.text(f"Duration: {run.get('duration_seconds', 0)}s")
                
                if run.get('output_directory'):
                    st.text(f"Output: {run['output_directory']}")
        
        else:
            st.error(f"❌ Failed to fetch run details: HTTP {response.status_code}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def export_run_as_zip(run_id: str, run_name: str):
    """Export a run as a ZIP file."""
    try:
        with st.spinner("Creating ZIP archive..."):
            response = httpx.get(
                f"{API_URL}/api/v1/documentation/runs/{run_id}/export/zip",
                timeout=120.0
            )
            
            if response.status_code == 200:
                # Provide download button
                st.download_button(
                    label="📥 Download ZIP",
                    data=response.content,
                    file_name=f"{run_name.replace(' ', '_')}_documents.zip",
                    mime="application/zip"
                )
                st.success("✅ ZIP file ready for download!")
            else:
                st.error(f"❌ Failed to export: HTTP {response.status_code}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def delete_run(run_id: str):
    """Delete a documentation run."""
    try:
        response = httpx.delete(
            f"{API_URL}/api/v1/documentation/runs/{run_id}",
            timeout=30.0
        )
        
        if response.status_code == 200:
            st.success("✅ Run deleted successfully!")
            st.rerun()
        else:
            st.error(f"❌ Failed to delete run: HTTP {response.status_code}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def show_documents_tab():
    """Show documents from selected run."""
    st.subheader("📄 Generated Documents")
    
    # Check if a run is selected
    if 'selected_run_id' not in st.session_state or not st.session_state.get('view_run_documents', False):
        st.info("👈 Select a run from the Run History tab to view its documents")
        return
    
    run_id = st.session_state['selected_run_id']
    
    # Clear view flag
    if st.button("⬅️ Back to Run History"):
        st.session_state['view_run_documents'] = False
        st.rerun()
    
    # Fetch documents
    try:
        response = httpx.get(
            f"{API_URL}/api/v1/documentation/runs/{run_id}/documents",
            params={"limit": 100, "offset": 0},
            timeout=30.0
        )
        
        if response.status_code == 200:
            documents = response.json()
            
            if not documents:
                st.info("📭 No documents found for this run")
                return
            
            st.success(f"✅ Found {len(documents)} documents")
            
            # Display documents
            for doc in documents:
                display_document_card(doc)
        
        else:
            st.error(f"❌ Failed to fetch documents: HTTP {response.status_code}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def display_document_card(doc: dict):
    """Display a document as an expandable card."""
    # Calculate size
    size_kb = doc['content_size'] / 1024
    
    with st.expander(f"📄 **{doc['title']}** ({size_kb:.1f} KB, {doc.get('word_count', 0)} words)"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.text(f"Filename: {doc['filename']}")
            st.text(f"Content Hash: {doc['content_hash'][:16]}...")
            st.text(f"Created: {format_datetime(doc['created_at'])}")
            
            if doc.get('pass_number'):
                st.text(f"Pass: {doc['pass_number']}")
            
            if doc.get('question'):
                st.markdown(f"**Question:** {doc['question']}")
        
        with col2:
            st.metric("Word Count", doc.get('word_count', 0))
            st.metric("Size", f"{size_kb:.1f} KB")
            
            if doc.get('generation_time_seconds'):
                st.metric("Gen Time", f"{doc['generation_time_seconds']:.1f}s")
        
        # Action buttons
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("👁️ View Content", key=f"view_content_{doc['id']}"):
                show_document_content(doc['id'])
        
        with col_btn2:
            if st.button("📋 Copy to Clipboard", key=f"copy_{doc['id']}"):
                st.info("Content copied! (Use View Content to see full text)")


def show_document_content(doc_id: str):
    """Show full document content."""
    try:
        response = httpx.get(
            f"{API_URL}/api/v1/documentation/documents/{doc_id}",
            timeout=30.0
        )
        
        if response.status_code == 200:
            doc = response.json()
            
            st.markdown("### 📄 Document Content")
            st.markdown(f"**Title:** {doc['title']}")
            st.markdown(f"**Filename:** {doc['filename']}")
            
            # Display content in a code block
            st.markdown("**Content:**")
            st.markdown(doc['content'])
            
            # Download button
            st.download_button(
                label="📥 Download",
                data=doc['content'],
                file_name=doc['filename'],
                mime="text/markdown"
            )
        
        else:
            st.error(f"❌ Failed to fetch document: HTTP {response.status_code}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def show_statistics():
    """Show statistics about documentation runs."""
    st.subheader("📊 Documentation Run Statistics")
    
    try:
        # Fetch all runs
        response = httpx.get(
            f"{API_URL}/api/v1/documentation/runs",
            params={"limit": 500, "offset": 0},
            timeout=30.0
        )
        
        if response.status_code == 200:
            runs = response.json()
            
            if not runs:
                st.info("📭 No documentation runs found")
                return
            
            # Calculate statistics
            total_runs = len(runs)
            completed_runs = len([r for r in runs if r['status'] == 'completed'])
            failed_runs = len([r for r in runs if r['status'] == 'failed'])
            running_runs = len([r for r in runs if r['status'] == 'running'])
            
            total_docs = sum(r['total_documents'] for r in runs)
            total_successful = sum(r['successful_documents'] for r in runs)
            total_failed = sum(r['failed_documents'] for r in runs)
            
            avg_duration = sum(r.get('duration_seconds', 0) for r in runs if r.get('duration_seconds')) / max(completed_runs, 1)
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Runs", total_runs)
                st.metric("Completed", completed_runs, delta=f"{completed_runs/max(total_runs,1)*100:.1f}%")
            
            with col2:
                st.metric("Failed", failed_runs, delta=f"-{failed_runs/max(total_runs,1)*100:.1f}%" if failed_runs > 0 else None)
                st.metric("Running", running_runs)
            
            with col3:
                st.metric("Total Documents", total_docs)
                st.metric("Successful", total_successful, delta=f"{total_successful/max(total_docs,1)*100:.1f}%")
            
            with col4:
                st.metric("Avg Duration", f"{avg_duration:.1f}s")
                st.metric("Avg Docs/Run", f"{total_docs/max(total_runs,1):.1f}")
            
            # Create DataFrame for charting
            df = pd.DataFrame(runs)
            
            if not df.empty:
                # Status distribution
                st.markdown("### 📊 Status Distribution")
                status_counts = df['status'].value_counts()
                st.bar_chart(status_counts)
                
                # Timeline
                st.markdown("### 📅 Runs Over Time")
                df['created_at'] = pd.to_datetime(df['created_at'])
                df_timeline = df.set_index('created_at').resample('D').size()
                st.line_chart(df_timeline)
        
        else:
            st.error(f"❌ Failed to fetch runs: HTTP {response.status_code}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def format_datetime(dt_str):
    """Format datetime string for display."""
    if not dt_str:
        return "N/A"
    
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return str(dt_str)


if __name__ == "__main__":
    show()

