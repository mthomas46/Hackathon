"""
Active Process Widget

Displays active processes in the sidebar with status updates.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List
import logging

from .state_manager import StateManager

logger = logging.getLogger(__name__)


def show_active_processes():
    """
    Display active processes in a compact widget.
    
    Should be called from app.py sidebar to show ongoing operations.
    """
    StateManager.initialize()
    
    running_processes = StateManager.get_running_processes()
    all_processes = StateManager.get_active_processes()
    
    # Count processes by status
    completed_count = sum(1 for p in all_processes.values() if p.get("status") == "completed")
    failed_count = sum(1 for p in all_processes.values() if p.get("status") == "failed")
    
    # Show header with count
    if running_processes:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚡ Active Processes")
        st.sidebar.markdown(f"**{len(running_processes)}** running")
        
        # Show each running process
        for process in running_processes:
            with st.sidebar.expander(f"▶️ {process['description']}", expanded=True):
                # Process type badge
                type_emoji = {
                    "ingestion": "📥",
                    "generation": "📄",
                    "query": "🔍",
                    "analysis": "📊",
                    "default": "⚙️"
                }
                emoji = type_emoji.get(process.get("process_type", "").lower(), type_emoji["default"])
                
                st.markdown(f"{emoji} **Type:** {process['process_type']}")
                
                # Calculate duration
                started_at = datetime.fromisoformat(process["started_at"])
                duration = datetime.now() - started_at
                duration_str = str(duration).split('.')[0]  # Remove microseconds
                
                st.markdown(f"⏱️ **Duration:** {duration_str}")
                
                # Show progress if available
                progress = process.get("progress")
                if progress is not None:
                    st.progress(progress / 100.0)
                    st.caption(f"{progress:.1f}% complete")
                
                # Show metadata if available
                metadata = process.get("metadata", {})
                if metadata:
                    st.markdown("**📋 Details:**")
                    for key, value in metadata.items():
                        st.markdown(f"  - **{key}:** {value}")
                
                # Action buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("⏹️ Stop", key=f"stop_{process['process_id']}", use_container_width=True):
                        StateManager.fail_process(process['process_id'], "Stopped by user")
                        st.rerun()
                
                with col2:
                    if st.button("🗑️ Remove", key=f"remove_{process['process_id']}", use_container_width=True):
                        StateManager.unregister_process(process['process_id'])
                        st.rerun()
    
    # Show completed/failed summary if any
    if completed_count > 0 or failed_count > 0:
        with st.sidebar.expander("📊 Process History", expanded=False):
            if completed_count > 0:
                st.success(f"✅ {completed_count} completed")
            
            if failed_count > 0:
                st.error(f"❌ {failed_count} failed")
            
            # Show recent completed processes
            recent_completed = [
                p for p in all_processes.values()
                if p.get("status") in ["completed", "failed"]
            ][:5]  # Last 5
            
            for process in recent_completed:
                status_emoji = "✅" if process["status"] == "completed" else "❌"
                st.markdown(f"{status_emoji} {process['description']}")
                
                if process.get("error"):
                    st.caption(f"Error: {process['error']}")
            
            # Clear history button
            if st.button("🧹 Clear History", key="clear_process_history", use_container_width=True):
                # Remove completed and failed processes
                for process_id, process in list(all_processes.items()):
                    if process.get("status") in ["completed", "failed"]:
                        StateManager.unregister_process(process_id)
                st.rerun()


def show_process_guard(page_name: str):
    """
    Show navigation guard if there are active processes.
    
    Args:
        page_name: Current page name for context
    """
    StateManager.initialize()
    
    if StateManager.has_active_processes():
        running = StateManager.get_running_processes()
        
        st.warning("⚠️ **Active Processes Running**")
        st.markdown(
            f"You are navigating away from **{page_name}** while "
            f"**{len(running)}** process(es) are running."
        )
        
        for process in running:
            st.markdown(
                f"- 🔄 **{process['description']}** "
                f"({process['process_type']})"
            )
        
        st.markdown("**These processes will continue running in the background.**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("⏸️ Stay Here", key="guard_stay", use_container_width=True, type="primary"):
                return False
        
        with col2:
            if st.button("⏹️ Stop & Leave", key="guard_stop", use_container_width=True):
                # Stop all running processes
                for process in running:
                    StateManager.fail_process(process['process_id'], "Stopped by navigation")
                return True
        
        with col3:
            if st.button("▶️ Leave Running", key="guard_continue", use_container_width=True):
                return True
        
        st.stop()  # Block navigation until user chooses
        return False
    
    return True


def show_generated_content_manager():
    """
    Show a widget for managing generated content.
    
    Allows users to view, export, and delete saved content.
    """
    StateManager.initialize()
    
    content_list = StateManager.list_generated_content()
    
    if content_list:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📄 Generated Content")
        st.sidebar.markdown(f"**{len(content_list)}** items saved")
        
        with st.sidebar.expander("📋 View Content", expanded=False):
            for item in reversed(content_list[-10:]):  # Last 10 items
                key = item["key"]
                timestamp = datetime.fromisoformat(item["timestamp"])
                time_ago = datetime.now() - timestamp
                
                st.markdown(f"**{key}**")
                st.caption(f"Generated {_format_time_ago(time_ago)} ago")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    content_data = StateManager.get_generated_content(key)
                    if content_data and st.button("📥 Export", key=f"export_{key}", use_container_width=True):
                        st.download_button(
                            "💾 Download",
                            data=content_data["content"],
                            file_name=f"{key}_{timestamp.strftime('%Y%m%d')}.md",
                            mime="text/markdown",
                            key=f"download_{key}"
                        )
                
                with col2:
                    if st.button("🗑️", key=f"delete_content_{key}", use_container_width=True):
                        StateManager.delete_generated_content(key)
                        st.rerun()
                
                st.markdown("---")
            
            # Clear all button
            if len(content_list) > 0:
                if st.button("🧹 Clear All", key="clear_all_content", use_container_width=True):
                    for item in content_list:
                        StateManager.delete_generated_content(item["key"])
                    st.rerun()


def _format_time_ago(delta: timedelta) -> str:
    """Format a timedelta as a human-readable 'time ago' string."""
    seconds = delta.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m"
    elif seconds < 86400:
        return f"{int(seconds / 3600)}h"
    else:
        return f"{int(seconds / 86400)}d"


def show_state_persistence_indicator():
    """
    Show a small indicator that state is being persisted.
    
    Useful for user confidence that their work is safe.
    """
    summary = StateManager.get_state_summary()
    
    total_items = (
        summary["generated_content_count"] +
        summary["query_history_count"] +
        summary["active_processes_count"]
    )
    
    if total_items > 0:
        st.sidebar.caption(f"💾 {total_items} items in memory")


def show_unsaved_changes_warning():
    """
    Show a warning banner if there are unsaved changes.
    """
    if st.session_state.get(StateManager.UNSAVED_CHANGES_KEY):
        st.warning("⚠️ **Unsaved Changes** - Your work will be lost if you navigate away without saving.")

