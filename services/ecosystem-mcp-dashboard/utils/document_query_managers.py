"""
Document Manager and Query Cache UI Widgets

Provides comprehensive UI for managing generated documents and cached RAG queries.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import hashlib
import logging

from .state_manager import StateManager

logger = logging.getLogger(__name__)


# ============================================================================
# Document Manager Widget
# ============================================================================

def show_document_manager(expanded: bool = False):
    """
    Show document manager widget with browse, search, and export.
    
    Args:
        expanded: Whether to expand the widget by default
    """
    StateManager.initialize()
    
    stats = StateManager.get_document_stats()
    
    if stats["total_documents"] == 0:
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📚 Document Manager")
    st.sidebar.markdown(f"**{stats['total_documents']}** documents ({stats['total_words']:,} words)")
    
    with st.sidebar.expander("📋 Browse Documents", expanded=expanded):
        # Document type filter
        doc_types = list(stats["by_type"].keys())
        doc_type_filter = st.selectbox(
            "Filter by Type",
            options=["All"] + doc_types,
            key="doc_manager_type_filter"
        )
        
        # Tag filter
        if stats["unique_tags"]:
            tag_filter = st.multiselect(
                "Filter by Tags",
                options=stats["unique_tags"],
                key="doc_manager_tag_filter"
            )
        else:
            tag_filter = []
        
        # Sort options
        sort_col1, sort_col2 = st.columns(2)
        
        with sort_col1:
            sort_by = st.selectbox(
                "Sort By",
                options=["created_at", "updated_at", "title", "word_count"],
                key="doc_manager_sort_by"
            )
        
        with sort_col2:
            sort_order = st.radio(
                "Order",
                options=["Newest", "Oldest"],
                key="doc_manager_sort_order",
                horizontal=True
            )
        
        # Get filtered documents
        docs = StateManager.list_documents(
            doc_type=None if doc_type_filter == "All" else doc_type_filter,
            tags=tag_filter if tag_filter else None,
            sort_by=sort_by,
            reverse=(sort_order == "Newest")
        )
        
        # Display documents
        for doc in docs[:10]:  # Show first 10
            with st.container():
                st.markdown(f"**{doc['title']}**")
                st.caption(
                    f"{doc['doc_type']} • "
                    f"{doc['word_count']:,} words • "
                    f"{_format_time_ago(datetime.now() - datetime.fromisoformat(doc['created_at']))} ago"
                )
                
                # Tags
                if doc['tags']:
                    st.markdown(f"🏷️ {', '.join(doc['tags'])}")
                
                # Actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("👁️", key=f"view_doc_{doc['doc_id']}", help="View"):
                        st.session_state[f"viewing_doc"] = doc['doc_id']
                        st.rerun()
                
                with col2:
                    st.download_button(
                        "💾",
                        data=doc['content'],
                        file_name=f"{doc['title']}.md",
                        mime="text/markdown",
                        key=f"download_doc_{doc['doc_id']}",
                        help="Download"
                    )
                
                with col3:
                    if st.button("🗑️", key=f"delete_doc_{doc['doc_id']}", help="Delete"):
                        StateManager.delete_document(doc['doc_id'])
                        st.rerun()
                
                st.markdown("---")
        
        if len(docs) > 10:
            st.caption(f"Showing 10 of {len(docs)} documents")
        
        # Export all button
        if st.button("📦 Export All Documents", key="export_all_docs", use_container_width=True):
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "documents": docs,
                "stats": stats
            }
            
            import json
            st.download_button(
                "💾 Download JSON",
                data=json.dumps(export_data, indent=2),
                file_name=f"documents_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                key="download_all_docs"
            )


def show_document_viewer():
    """Show full document viewer if a document is being viewed."""
    if "viewing_doc" not in st.session_state:
        return
    
    doc_id = st.session_state["viewing_doc"]
    doc = StateManager.get_document(doc_id)
    
    if not doc:
        del st.session_state["viewing_doc"]
        return
    
    # Show in main area
    st.markdown("---")
    st.subheader(f"📄 {doc['title']}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Type", doc['doc_type'])
    
    with col2:
        st.metric("Words", f"{doc['word_count']:,}")
    
    with col3:
        created = datetime.fromisoformat(doc['created_at'])
        st.metric("Created", created.strftime("%Y-%m-%d"))
    
    # Tags
    if doc['tags']:
        st.markdown(f"**Tags:** {', '.join(f'`{tag}`' for tag in doc['tags'])}")
    
    # Metadata
    if doc['metadata']:
        with st.expander("🔍 Metadata", expanded=False):
            st.json(doc['metadata'])
    
    # Content
    st.markdown("---")
    st.markdown(doc['content'])
    
    # Actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            "💾 Download Markdown",
            data=doc['content'],
            file_name=f"{doc['title']}.md",
            mime="text/markdown",
            key="download_viewing_doc"
        )
    
    with col2:
        if st.button("✏️ Edit Tags", key="edit_doc_tags"):
            st.session_state["editing_doc_tags"] = doc_id
    
    with col3:
        if st.button("❌ Close", key="close_doc_viewer"):
            del st.session_state["viewing_doc"]
            st.rerun()


# ============================================================================
# Query Cache Widget
# ============================================================================

def show_query_cache(expanded: bool = False):
    """
    Show query cache widget with browse, search, and reuse.
    
    Args:
        expanded: Whether to expand the widget by default
    """
    StateManager.initialize()
    
    stats = StateManager.get_query_cache_stats()
    
    if stats["total_queries"] == 0:
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💾 Query Cache")
    st.sidebar.markdown(
        f"**{stats['total_queries']}** queries "
        f"({int(stats['avg_answer_length'])} avg chars)"
    )
    
    with st.sidebar.expander("📋 Browse Queries", expanded=expanded):
        # Query type filter
        query_types = list(stats["by_type"].keys())
        query_type_filter = st.selectbox(
            "Filter by Type",
            options=["All"] + query_types,
            key="query_cache_type_filter"
        )
        
        # Get filtered queries
        queries = StateManager.list_cached_queries(
            query_type=None if query_type_filter == "All" else query_type_filter,
            sort_by="timestamp",
            reverse=True,
            limit=10
        )
        
        # Display queries
        for query in queries:
            with st.container():
                # Question (truncated)
                question_short = query['question'][:60] + "..." if len(query['question']) > 60 else query['question']
                st.markdown(f"**Q:** {question_short}")
                
                # Metadata
                st.caption(
                    f"{query['query_type']} • "
                    f"{query['num_documents']} docs • "
                    f"{_format_time_ago(datetime.now() - datetime.fromisoformat(query['timestamp']))} ago"
                )
                
                # Query metadata tags
                qmeta = query['query_metadata']
                tags = []
                if 'tier' in qmeta:
                    tags.append(f"🎯 {qmeta['tier']}")
                if 'temperature' in qmeta:
                    tags.append(f"🌡️ {qmeta['temperature']}")
                if 'n_results' in qmeta:
                    tags.append(f"📚 {qmeta['n_results']}")
                
                if tags:
                    st.markdown(" • ".join(tags))
                
                # Actions
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("👁️", key=f"view_query_{query['query_id']}", help="View Full"):
                        st.session_state["viewing_query"] = query['query_id']
                        st.rerun()
                
                with col2:
                    if st.button("🔄", key=f"reuse_query_{query['query_id']}", help="Reuse"):
                        st.session_state["reuse_query"] = query['query_id']
                        st.rerun()
                
                with col3:
                    if st.button("🗑️", key=f"delete_query_{query['query_id']}", help="Delete"):
                        StateManager.delete_cached_query(query['query_id'])
                        st.rerun()
                
                st.markdown("---")
        
        if len(queries) == 10:
            st.caption(f"Showing 10 most recent queries")
        
        # Clear cache button
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧹 Clear All", key="clear_all_queries", use_container_width=True):
                count = StateManager.clear_query_cache()
                st.success(f"Cleared {count} queries!")
                st.rerun()
        
        with col2:
            if st.button("📦 Export", key="export_queries", use_container_width=True):
                all_queries = StateManager.list_cached_queries()
                export_data = {
                    "exported_at": datetime.now().isoformat(),
                    "queries": all_queries,
                    "stats": stats
                }
                
                import json
                st.download_button(
                    "💾 Download JSON",
                    data=json.dumps(export_data, indent=2),
                    file_name=f"query_cache_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="download_query_cache"
                )


def show_query_viewer():
    """Show full query viewer if a query is being viewed."""
    if "viewing_query" not in st.session_state:
        return
    
    query_id = st.session_state["viewing_query"]
    query = StateManager.get_cached_query(query_id)
    
    if not query:
        del st.session_state["viewing_query"]
        return
    
    # Show in main area
    st.markdown("---")
    st.subheader("💬 Cached Query")
    
    # Metadata
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Type", query['query_type'])
    
    with col2:
        st.metric("Documents", query['num_documents'])
    
    with col3:
        timestamp = datetime.fromisoformat(query['timestamp'])
        st.metric("Cached", timestamp.strftime("%Y-%m-%d %H:%M"))
    
    # Question
    st.markdown("### ❓ Question")
    st.info(query['question'])
    
    # Answer
    st.markdown("### ✅ Answer")
    st.success(query['answer'])
    
    # Query Metadata
    with st.expander("⚙️ Query Metadata", expanded=False):
        st.json(query['query_metadata'])
    
    # Retrieved Documents
    with st.expander(f"📚 Retrieved Documents ({query['num_documents']})", expanded=False):
        for i, doc in enumerate(query['retrieved_documents'][:10], 1):
            st.markdown(f"**{i}. {doc.get('title', doc.get('file_path', 'Untitled'))}**")
            st.caption(f"Score: {doc.get('score', 'N/A')} • Distance: {doc.get('distance', 'N/A')}")
            if doc.get('content'):
                content_preview = doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
                st.markdown(f"> {content_preview}")
            st.markdown("---")
    
    # Generation Metadata
    if query['generation_metadata']:
        with st.expander("🔍 Generation Metadata", expanded=False):
            st.json(query['generation_metadata'])
    
    # Actions
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reuse Query", key="reuse_viewing_query"):
            st.session_state["reuse_query"] = query_id
            del st.session_state["viewing_query"]
            st.rerun()
    
    with col2:
        # Export query as markdown report
        report = f"""# RAG Query Report

**Query ID:** {query['query_id']}
**Type:** {query['query_type']}
**Timestamp:** {query['timestamp']}

## Question
{query['question']}

## Answer
{query['answer']}

## Metadata
- Documents Retrieved: {query['num_documents']}
- Answer Length: {query['answer_length']} characters

### Query Parameters
{_dict_to_markdown(query['query_metadata'])}

## Retrieved Documents
"""
        for i, doc in enumerate(query['retrieved_documents'], 1):
            report += f"\n### {i}. {doc.get('title', 'Untitled')}\n"
            report += f"- File: `{doc.get('file_path', 'N/A')}`\n"
            report += f"- Score: {doc.get('score', 'N/A')}\n\n"
        
        st.download_button(
            "💾 Download Report",
            data=report,
            file_name=f"query_report_{query_id[:8]}.md",
            mime="text/markdown",
            key="download_query_report"
        )
    
    with col3:
        if st.button("❌ Close", key="close_query_viewer"):
            del st.session_state["viewing_query"]
            st.rerun()


def check_for_similar_query(question: str, query_type: str) -> Optional[Dict]:
    """
    Check if a similar query exists in cache.
    
    Args:
        question: Question to check
        query_type: Query type to match
        
    Returns:
        Similar query if found, else None
    """
    similar = StateManager.find_similar_cached_query(
        question=question,
        query_type=query_type,
        threshold=0.7  # 70% similarity
    )
    
    if similar:
        logger.info(
            f"Found similar cached query with {similar['similarity_score']:.1%} similarity"
        )
    
    return similar


def show_similar_query_notification(similar_query: Dict):
    """
    Show a notification about a similar cached query.
    
    Args:
        similar_query: The similar query found in cache
    """
    st.info(f"""
    💡 **Similar Query Found in Cache ({similar_query['similarity_score']:.0%} match)**
    
    **Cached:** {_format_time_ago(datetime.now() - datetime.fromisoformat(similar_query['timestamp']))} ago
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("👁️ View Cached Answer", key="view_similar_query"):
            st.session_state["viewing_query"] = similar_query['query_id']
            st.rerun()
    
    with col2:
        if st.button("🔄 Reuse This Query", key="reuse_similar_query"):
            st.session_state["reuse_query"] = similar_query['query_id']
            st.rerun()


# ============================================================================
# Helper Functions
# ============================================================================

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


def _dict_to_markdown(d: Dict, indent: int = 0) -> str:
    """Convert a dictionary to markdown list."""
    result = []
    prefix = "  " * indent
    
    for key, value in d.items():
        if isinstance(value, dict):
            result.append(f"{prefix}- **{key}:**")
            result.append(_dict_to_markdown(value, indent + 1))
        elif isinstance(value, list):
            result.append(f"{prefix}- **{key}:** {', '.join(str(v) for v in value)}")
        else:
            result.append(f"{prefix}- **{key}:** {value}")
    
    return "\n".join(result)


def generate_query_id(question: str, query_type: str) -> str:
    """Generate a unique query ID from question and type."""
    content = f"{query_type}_{question}_{datetime.now().isoformat()}"
    return hashlib.md5(content.encode()).hexdigest()[:16]


def generate_doc_id(title: str, doc_type: str) -> str:
    """Generate a unique document ID from title and type."""
    content = f"{doc_type}_{title}_{datetime.now().isoformat()}"
    return hashlib.md5(content.encode()).hexdigest()[:16]

