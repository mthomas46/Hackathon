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
    
    # New keys for enhanced management
    DOCUMENT_MANAGER_KEY = "document_manager"  # Organized generated documents
    QUERY_CACHE_KEY = "query_cache"  # Full RAG query cache with metadata
    
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
            StateManager.PAGE_STATE_KEY: {},
            StateManager.DOCUMENT_MANAGER_KEY: {},
            StateManager.QUERY_CACHE_KEY: {}
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
    # Document Manager
    # ========================================================================
    
    @staticmethod
    def add_document(
        doc_id: str,
        title: str,
        content: str,
        doc_type: str,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> None:
        """
        Add a document to the document manager.
        
        Args:
            doc_id: Unique document identifier
            title: Document title
            content: Full document content
            doc_type: Type (documentation, report, analysis, etc.)
            metadata: Optional metadata (source, generation method, etc.)
            tags: Optional tags for categorization
        """
        StateManager.initialize()
        
        document = {
            "doc_id": doc_id,
            "title": title,
            "content": content,
            "doc_type": doc_type,
            "metadata": metadata or {},
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "word_count": len(content.split()),
            "char_count": len(content)
        }
        
        st.session_state[StateManager.DOCUMENT_MANAGER_KEY][doc_id] = document
        logger.info(f"📄 Added document: {title} ({doc_type})")
    
    @staticmethod
    def get_document(doc_id: str) -> Optional[Dict]:
        """Retrieve a document by ID."""
        StateManager.initialize()
        return st.session_state[StateManager.DOCUMENT_MANAGER_KEY].get(doc_id)
    
    @staticmethod
    def update_document(
        doc_id: str,
        content: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Update an existing document."""
        StateManager.initialize()
        
        if doc_id not in st.session_state[StateManager.DOCUMENT_MANAGER_KEY]:
            return False
        
        doc = st.session_state[StateManager.DOCUMENT_MANAGER_KEY][doc_id]
        
        if content is not None:
            doc["content"] = content
            doc["word_count"] = len(content.split())
            doc["char_count"] = len(content)
        
        if metadata is not None:
            doc["metadata"].update(metadata)
        
        if tags is not None:
            doc["tags"] = tags
        
        doc["updated_at"] = datetime.now().isoformat()
        
        logger.info(f"📝 Updated document: {doc_id}")
        return True
    
    @staticmethod
    def delete_document(doc_id: str) -> bool:
        """Delete a document."""
        StateManager.initialize()
        
        if doc_id in st.session_state[StateManager.DOCUMENT_MANAGER_KEY]:
            del st.session_state[StateManager.DOCUMENT_MANAGER_KEY][doc_id]
            logger.info(f"🗑️ Deleted document: {doc_id}")
            return True
        return False
    
    @staticmethod
    def list_documents(
        doc_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sort_by: str = "created_at",
        reverse: bool = True
    ) -> List[Dict]:
        """
        List all documents with optional filtering and sorting.
        
        Args:
            doc_type: Filter by document type
            tags: Filter by tags (documents must have all tags)
            sort_by: Sort field (created_at, updated_at, title, word_count)
            reverse: Sort in reverse order (newest first by default)
        """
        StateManager.initialize()
        
        docs = list(st.session_state[StateManager.DOCUMENT_MANAGER_KEY].values())
        
        # Filter by type
        if doc_type:
            docs = [d for d in docs if d["doc_type"] == doc_type]
        
        # Filter by tags
        if tags:
            docs = [d for d in docs if all(tag in d["tags"] for tag in tags)]
        
        # Sort
        if sort_by in ["created_at", "updated_at", "title", "word_count", "char_count"]:
            docs.sort(key=lambda d: d.get(sort_by, ""), reverse=reverse)
        
        return docs
    
    @staticmethod
    def search_documents(
        search_query: str,
        search_in: List[str] = ["title", "content", "tags"]
    ) -> List[Dict]:
        """
        Search documents by query string.
        
        Args:
            search_query: Query string to search for
            search_in: Fields to search in (title, content, tags, metadata)
        """
        StateManager.initialize()
        
        query_lower = search_query.lower()
        results = []
        
        for doc in st.session_state[StateManager.DOCUMENT_MANAGER_KEY].values():
            match = False
            
            if "title" in search_in and query_lower in doc["title"].lower():
                match = True
            
            if "content" in search_in and query_lower in doc["content"].lower():
                match = True
            
            if "tags" in search_in:
                for tag in doc["tags"]:
                    if query_lower in tag.lower():
                        match = True
                        break
            
            if "metadata" in search_in:
                for key, value in doc["metadata"].items():
                    if query_lower in str(value).lower():
                        match = True
                        break
            
            if match:
                results.append(doc)
        
        return results
    
    @staticmethod
    def get_document_stats() -> Dict:
        """Get document manager statistics."""
        StateManager.initialize()
        
        docs = st.session_state[StateManager.DOCUMENT_MANAGER_KEY].values()
        
        if not docs:
            return {
                "total_documents": 0,
                "total_words": 0,
                "total_chars": 0,
                "by_type": {},
                "total_tags": 0
            }
        
        by_type = {}
        all_tags = set()
        
        for doc in docs:
            doc_type = doc["doc_type"]
            by_type[doc_type] = by_type.get(doc_type, 0) + 1
            all_tags.update(doc["tags"])
        
        return {
            "total_documents": len(docs),
            "total_words": sum(d["word_count"] for d in docs),
            "total_chars": sum(d["char_count"] for d in docs),
            "by_type": by_type,
            "total_tags": len(all_tags),
            "unique_tags": sorted(list(all_tags))
        }
    
    # ========================================================================
    # Query Cache
    # ========================================================================
    
    @staticmethod
    def cache_query(
        query_id: str,
        question: str,
        answer: str,
        query_type: str,
        query_metadata: Dict,
        retrieved_documents: List[Dict],
        generation_metadata: Optional[Dict] = None
    ) -> None:
        """
        Cache a RAG query with full metadata.
        
        Args:
            query_id: Unique query identifier
            question: Original question text
            answer: Generated answer
            query_type: Type (basic, contextual, rag, multi-pass, temporal, etc.)
            query_metadata: Metadata used for query (tier, n_results, temperature, etc.)
            retrieved_documents: List of documents used to generate answer
            generation_metadata: Optional generation metadata (timing, costs, etc.)
        """
        StateManager.initialize()
        
        cache_entry = {
            "query_id": query_id,
            "question": question,
            "answer": answer,
            "query_type": query_type,
            "query_metadata": query_metadata,
            "retrieved_documents": retrieved_documents,
            "generation_metadata": generation_metadata or {},
            "timestamp": datetime.now().isoformat(),
            "answer_length": len(answer),
            "num_documents": len(retrieved_documents)
        }
        
        st.session_state[StateManager.QUERY_CACHE_KEY][query_id] = cache_entry
        logger.info(f"💾 Cached query: {question[:50]}... ({query_type})")
    
    @staticmethod
    def get_cached_query(query_id: str) -> Optional[Dict]:
        """Retrieve a cached query by ID."""
        StateManager.initialize()
        return st.session_state[StateManager.QUERY_CACHE_KEY].get(query_id)
    
    @staticmethod
    def find_similar_cached_query(
        question: str,
        query_type: Optional[str] = None,
        threshold: float = 0.8
    ) -> Optional[Dict]:
        """
        Find a similar cached query (simple string similarity).
        
        Args:
            question: Question to match
            query_type: Optional filter by query type
            threshold: Similarity threshold (0.0-1.0)
        """
        StateManager.initialize()
        
        question_lower = question.lower()
        best_match = None
        best_score = 0.0
        
        for entry in st.session_state[StateManager.QUERY_CACHE_KEY].values():
            # Filter by type if specified
            if query_type and entry["query_type"] != query_type:
                continue
            
            cached_question_lower = entry["question"].lower()
            
            # Simple similarity: ratio of matching words
            question_words = set(question_lower.split())
            cached_words = set(cached_question_lower.split())
            
            if not question_words or not cached_words:
                continue
            
            intersection = question_words & cached_words
            union = question_words | cached_words
            
            similarity = len(intersection) / len(union) if union else 0.0
            
            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = {**entry, "similarity_score": similarity}
        
        return best_match
    
    @staticmethod
    def list_cached_queries(
        query_type: Optional[str] = None,
        sort_by: str = "timestamp",
        reverse: bool = True,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        List cached queries with optional filtering.
        
        Args:
            query_type: Filter by query type
            sort_by: Sort field (timestamp, answer_length, num_documents)
            reverse: Sort in reverse order
            limit: Maximum number of results
        """
        StateManager.initialize()
        
        queries = list(st.session_state[StateManager.QUERY_CACHE_KEY].values())
        
        # Filter by type
        if query_type:
            queries = [q for q in queries if q["query_type"] == query_type]
        
        # Sort
        if sort_by in ["timestamp", "answer_length", "num_documents"]:
            queries.sort(key=lambda q: q.get(sort_by, ""), reverse=reverse)
        
        # Limit
        if limit:
            queries = queries[:limit]
        
        return queries
    
    @staticmethod
    def search_cached_queries(search_query: str) -> List[Dict]:
        """Search cached queries by question or answer content."""
        StateManager.initialize()
        
        query_lower = search_query.lower()
        results = []
        
        for entry in st.session_state[StateManager.QUERY_CACHE_KEY].values():
            if (query_lower in entry["question"].lower() or 
                query_lower in entry["answer"].lower()):
                results.append(entry)
        
        return results
    
    @staticmethod
    def delete_cached_query(query_id: str) -> bool:
        """Delete a cached query."""
        StateManager.initialize()
        
        if query_id in st.session_state[StateManager.QUERY_CACHE_KEY]:
            del st.session_state[StateManager.QUERY_CACHE_KEY][query_id]
            logger.info(f"🗑️ Deleted cached query: {query_id}")
            return True
        return False
    
    @staticmethod
    def clear_query_cache(query_type: Optional[str] = None) -> int:
        """
        Clear query cache, optionally by type.
        
        Returns:
            Number of queries cleared
        """
        StateManager.initialize()
        
        if query_type is None:
            count = len(st.session_state[StateManager.QUERY_CACHE_KEY])
            st.session_state[StateManager.QUERY_CACHE_KEY] = {}
            logger.info(f"🧹 Cleared {count} cached queries")
            return count
        else:
            cache = st.session_state[StateManager.QUERY_CACHE_KEY]
            to_delete = [
                qid for qid, entry in cache.items() 
                if entry["query_type"] == query_type
            ]
            for qid in to_delete:
                del cache[qid]
            logger.info(f"🧹 Cleared {len(to_delete)} cached queries of type {query_type}")
            return len(to_delete)
    
    @staticmethod
    def get_query_cache_stats() -> Dict:
        """Get query cache statistics."""
        StateManager.initialize()
        
        queries = st.session_state[StateManager.QUERY_CACHE_KEY].values()
        
        if not queries:
            return {
                "total_queries": 0,
                "by_type": {},
                "total_documents_retrieved": 0,
                "avg_answer_length": 0
            }
        
        by_type = {}
        for query in queries:
            qtype = query["query_type"]
            by_type[qtype] = by_type.get(qtype, 0) + 1
        
        return {
            "total_queries": len(queries),
            "by_type": by_type,
            "total_documents_retrieved": sum(q["num_documents"] for q in queries),
            "avg_answer_length": sum(q["answer_length"] for q in queries) / len(queries),
            "avg_documents_per_query": sum(q["num_documents"] for q in queries) / len(queries)
        }
    
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
            "page_state": st.session_state[StateManager.PAGE_STATE_KEY],
            "document_manager": st.session_state[StateManager.DOCUMENT_MANAGER_KEY],
            "query_cache": st.session_state[StateManager.QUERY_CACHE_KEY]
        }
    
    @staticmethod
    def clear_all_state() -> None:
        """Clear all managed state (use with caution)."""
        for key in [
            StateManager.GENERATED_CONTENT_KEY,
            StateManager.ACTIVE_PROCESSES_KEY,
            StateManager.QUERY_HISTORY_KEY,
            StateManager.TIMELINE_CACHE_KEY,
            StateManager.PAGE_STATE_KEY,
            StateManager.DOCUMENT_MANAGER_KEY,
            StateManager.QUERY_CACHE_KEY
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
            "page_states_saved": len(st.session_state[StateManager.PAGE_STATE_KEY]),
            "documents_count": len(st.session_state[StateManager.DOCUMENT_MANAGER_KEY]),
            "cached_queries_count": len(st.session_state[StateManager.QUERY_CACHE_KEY])
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

