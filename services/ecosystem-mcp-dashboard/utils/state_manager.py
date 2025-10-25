"""
Global State Manager for Dashboard

Provides centralized state management with persistence, 
navigation guards, and refresh safety.
"""

import streamlit as st
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)


class StateManager:
    """Centralized state management for the dashboard."""
    
    # State keys for persistence
    GENERATED_CONTENT_KEY = "generated_content"
    ACTIVE_PROCESSES_KEY = "active_processes"
    QUERY_HISTORY_KEY = "query_history"
    TIMELINE_CACHE_KEY = "timeline_cache"
    UNSAVED_CHANGES_KEY = "unsaved_changes"
    LAST_PAGE_KEY = "last_page"
    PAGE_STATE_KEY = "page_state"
    
    @staticmethod
    def initialize():
        """Initialize all state keys if they don't exist."""
        defaults = {
            StateManager.GENERATED_CONTENT_KEY: {},
            StateManager.ACTIVE_PROCESSES_KEY: {},
            StateManager.QUERY_HISTORY_KEY: [],
            StateManager.TIMELINE_CACHE_KEY: {},
            StateManager.UNSAVED_CHANGES_KEY: False,
            StateManager.LAST_PAGE_KEY: None,
            StateManager.PAGE_STATE_KEY: {}
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    # ========================================================================
    # Generated Content Management
    # ========================================================================
    
    @staticmethod
    def save_generated_content(
        key: str, 
        content: str, 
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Save generated content with metadata.
        
        Args:
            key: Unique identifier for the content
            content: The generated content text
            metadata: Optional metadata (timestamp, query, etc.)
        """
        StateManager.initialize()
        
        entry = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        st.session_state[StateManager.GENERATED_CONTENT_KEY][key] = entry
        logger.info(f"💾 Saved generated content: {key}")
    
    @staticmethod
    def get_generated_content(key: str) -> Optional[Dict]:
        """
        Retrieve generated content by key.
        
        Args:
            key: Content identifier
            
        Returns:
            Content dictionary with 'content', 'timestamp', 'metadata'
        """
        StateManager.initialize()
        return st.session_state[StateManager.GENERATED_CONTENT_KEY].get(key)
    
    @staticmethod
    def list_generated_content() -> List[Dict]:
        """List all generated content with metadata."""
        StateManager.initialize()
        return [
            {"key": k, **v} 
            for k, v in st.session_state[StateManager.GENERATED_CONTENT_KEY].items()
        ]
    
    @staticmethod
    def delete_generated_content(key: str) -> bool:
        """Delete generated content by key."""
        StateManager.initialize()
        if key in st.session_state[StateManager.GENERATED_CONTENT_KEY]:
            del st.session_state[StateManager.GENERATED_CONTENT_KEY][key]
            logger.info(f"🗑️ Deleted generated content: {key}")
            return True
        return False
    
    # ========================================================================
    # Active Process Management
    # ========================================================================
    
    @staticmethod
    def register_process(
        process_id: str, 
        process_type: str, 
        description: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Register an active process (ingestion, generation, etc.).
        
        Args:
            process_id: Unique process identifier (e.g., job ID)
            process_type: Type of process (ingestion, generation, query)
            description: Human-readable description
            metadata: Optional process metadata
        """
        StateManager.initialize()
        
        process_info = {
            "process_id": process_id,
            "process_type": process_type,
            "description": description,
            "started_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "status": "running"
        }
        
        st.session_state[StateManager.ACTIVE_PROCESSES_KEY][process_id] = process_info
        logger.info(f"▶️ Registered process: {process_id} ({process_type})")
    
    @staticmethod
    def update_process_status(
        process_id: str, 
        status: str, 
        progress: Optional[float] = None
    ) -> None:
        """Update process status and optional progress percentage."""
        StateManager.initialize()
        
        if process_id in st.session_state[StateManager.ACTIVE_PROCESSES_KEY]:
            st.session_state[StateManager.ACTIVE_PROCESSES_KEY][process_id]["status"] = status
            st.session_state[StateManager.ACTIVE_PROCESSES_KEY][process_id]["updated_at"] = datetime.now().isoformat()
            
            if progress is not None:
                st.session_state[StateManager.ACTIVE_PROCESSES_KEY][process_id]["progress"] = progress
            
            logger.info(f"📊 Updated process {process_id}: {status}")
    
    @staticmethod
    def complete_process(process_id: str, result: Optional[Any] = None) -> None:
        """Mark a process as completed and optionally store result."""
        StateManager.initialize()
        
        if process_id in st.session_state[StateManager.ACTIVE_PROCESSES_KEY]:
            st.session_state[StateManager.ACTIVE_PROCESSES_KEY][process_id]["status"] = "completed"
            st.session_state[StateManager.ACTIVE_PROCESSES_KEY][process_id]["completed_at"] = datetime.now().isoformat()
            
            if result is not None:
                st.session_state[StateManager.ACTIVE_PROCESSES_KEY][process_id]["result"] = result
            
            logger.info(f"✅ Completed process: {process_id}")
    
    @staticmethod
    def fail_process(process_id: str, error: str) -> None:
        """Mark a process as failed with error message."""
        StateManager.initialize()
        
        if process_id in st.session_state[StateManager.ACTIVE_PROCESSES_KEY]:
            st.session_state[StateManager.ACTIVE_PROCESSES_KEY][process_id]["status"] = "failed"
            st.session_state[StateManager.ACTIVE_PROCESSES_KEY][process_id]["failed_at"] = datetime.now().isoformat()
            st.session_state[StateManager.ACTIVE_PROCESSES_KEY][process_id]["error"] = error
            
            logger.error(f"❌ Process failed: {process_id} - {error}")
    
    @staticmethod
    def unregister_process(process_id: str) -> None:
        """Remove a process from active tracking."""
        StateManager.initialize()
        
        if process_id in st.session_state[StateManager.ACTIVE_PROCESSES_KEY]:
            del st.session_state[StateManager.ACTIVE_PROCESSES_KEY][process_id]
            logger.info(f"⏹️ Unregistered process: {process_id}")
    
    @staticmethod
    def get_active_processes() -> Dict[str, Dict]:
        """Get all active processes."""
        StateManager.initialize()
        return st.session_state[StateManager.ACTIVE_PROCESSES_KEY]
    
    @staticmethod
    def has_active_processes() -> bool:
        """Check if there are any active processes."""
        StateManager.initialize()
        active = st.session_state[StateManager.ACTIVE_PROCESSES_KEY]
        return any(
            p.get("status") == "running" 
            for p in active.values()
        )
    
    @staticmethod
    def get_running_processes() -> List[Dict]:
        """Get only currently running processes."""
        StateManager.initialize()
        return [
            p for p in st.session_state[StateManager.ACTIVE_PROCESSES_KEY].values()
            if p.get("status") == "running"
        ]
    
    # ========================================================================
    # Navigation Guards
    # ========================================================================
    
    @staticmethod
    def check_navigation_safety(current_page: str) -> bool:
        """
        Check if it's safe to navigate away from current page.
        
        Shows warning if there are:
        - Active processes running
        - Unsaved changes
        - Generated content not exported
        
        Returns:
            True if safe to navigate, False otherwise
        """
        StateManager.initialize()
        
        # Check for active processes
        running_processes = StateManager.get_running_processes()
        if running_processes:
            st.warning("⚠️ **Active Processes Running**")
            st.markdown("The following processes are currently active:")
            
            for process in running_processes:
                st.markdown(
                    f"- **{process['description']}** "
                    f"({process['process_type']}) - "
                    f"Started {process['started_at']}"
                )
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("⏸️ Stay on Page", key="stay_on_page", use_container_width=True):
                    return False
            
            with col2:
                if st.button("⚠️ Leave Anyway", key="leave_anyway", use_container_width=True, type="secondary"):
                    return True
            
            st.stop()  # Prevent navigation until user makes a choice
            return False
        
        # Check for unsaved changes
        if st.session_state.get(StateManager.UNSAVED_CHANGES_KEY):
            st.warning("⚠️ **Unsaved Changes**")
            st.markdown("You have unsaved changes that will be lost.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("💾 Save First", key="save_first", use_container_width=True):
                    return False
            
            with col2:
                if st.button("⚠️ Discard", key="discard_changes", use_container_width=True, type="secondary"):
                    st.session_state[StateManager.UNSAVED_CHANGES_KEY] = False
                    return True
            
            st.stop()
            return False
        
        return True
    
    @staticmethod
    def mark_unsaved_changes(has_changes: bool = True) -> None:
        """Mark that the current page has unsaved changes."""
        st.session_state[StateManager.UNSAVED_CHANGES_KEY] = has_changes
    
    # ========================================================================
    # Page State Management
    # ========================================================================
    
    @staticmethod
    def save_page_state(page: str, state: Dict) -> None:
        """Save current page state for restoration."""
        StateManager.initialize()
        st.session_state[StateManager.PAGE_STATE_KEY][page] = {
            "state": state,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"💾 Saved page state: {page}")
    
    @staticmethod
    def get_page_state(page: str) -> Optional[Dict]:
        """Retrieve saved page state."""
        StateManager.initialize()
        page_data = st.session_state[StateManager.PAGE_STATE_KEY].get(page)
        return page_data.get("state") if page_data else None
    
    @staticmethod
    def clear_page_state(page: str) -> None:
        """Clear saved state for a page."""
        StateManager.initialize()
        if page in st.session_state[StateManager.PAGE_STATE_KEY]:
            del st.session_state[StateManager.PAGE_STATE_KEY][page]
    
    # ========================================================================
    # Query History Management
    # ========================================================================
    
    @staticmethod
    def add_to_query_history(
        query: str, 
        query_type: str, 
        result_summary: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """Add a query to history."""
        StateManager.initialize()
        
        entry = {
            "query": query,
            "query_type": query_type,
            "result_summary": result_summary,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        st.session_state[StateManager.QUERY_HISTORY_KEY].append(entry)
        
        # Keep only last 100 queries
        if len(st.session_state[StateManager.QUERY_HISTORY_KEY]) > 100:
            st.session_state[StateManager.QUERY_HISTORY_KEY] = \
                st.session_state[StateManager.QUERY_HISTORY_KEY][-100:]
    
    @staticmethod
    def get_query_history(limit: Optional[int] = None) -> List[Dict]:
        """Get query history, optionally limited."""
        StateManager.initialize()
        history = st.session_state[StateManager.QUERY_HISTORY_KEY]
        
        if limit:
            return history[-limit:]
        return history
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    @staticmethod
    def export_state() -> Dict:
        """Export all state for backup/debugging."""
        StateManager.initialize()
        
        return {
            "exported_at": datetime.now().isoformat(),
            "generated_content": st.session_state[StateManager.GENERATED_CONTENT_KEY],
            "active_processes": st.session_state[StateManager.ACTIVE_PROCESSES_KEY],
            "query_history": st.session_state[StateManager.QUERY_HISTORY_KEY],
            "page_state": st.session_state[StateManager.PAGE_STATE_KEY]
        }
    
    @staticmethod
    def clear_all_state() -> None:
        """Clear all managed state (use with caution)."""
        for key in [
            StateManager.GENERATED_CONTENT_KEY,
            StateManager.ACTIVE_PROCESSES_KEY,
            StateManager.QUERY_HISTORY_KEY,
            StateManager.TIMELINE_CACHE_KEY,
            StateManager.PAGE_STATE_KEY
        ]:
            if key in st.session_state:
                st.session_state[key] = {} if key != StateManager.QUERY_HISTORY_KEY else []
        
        st.session_state[StateManager.UNSAVED_CHANGES_KEY] = False
        logger.info("🧹 Cleared all managed state")
    
    @staticmethod
    def get_state_summary() -> Dict:
        """Get summary statistics of current state."""
        StateManager.initialize()
        
        return {
            "generated_content_count": len(st.session_state[StateManager.GENERATED_CONTENT_KEY]),
            "active_processes_count": len(StateManager.get_running_processes()),
            "query_history_count": len(st.session_state[StateManager.QUERY_HISTORY_KEY]),
            "has_unsaved_changes": st.session_state.get(StateManager.UNSAVED_CHANGES_KEY, False),
            "page_states_saved": len(st.session_state[StateManager.PAGE_STATE_KEY])
        }


def show_state_debug_panel():
    """Show a debug panel with current state (for development)."""
    with st.expander("🔍 State Debug Panel", expanded=False):
        summary = StateManager.get_state_summary()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Generated Content", summary["generated_content_count"])
            st.metric("Query History", summary["query_history_count"])
        
        with col2:
            st.metric("Active Processes", summary["active_processes_count"])
            st.metric("Page States", summary["page_states_saved"])
        
        with col3:
            unsaved_status = "⚠️ Yes" if summary["has_unsaved_changes"] else "✅ No"
            st.metric("Unsaved Changes", unsaved_status)
        
        st.markdown("---")
        
        if st.button("📥 Export State", key="export_state"):
            state_export = StateManager.export_state()
            st.download_button(
                "💾 Download State JSON",
                data=json.dumps(state_export, indent=2),
                file_name=f"dashboard_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        if st.button("🧹 Clear All State", key="clear_state"):
            if st.checkbox("I understand this will clear ALL state"):
                StateManager.clear_all_state()
                st.success("✅ State cleared!")
                st.rerun()

