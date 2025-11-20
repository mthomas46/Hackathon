"""
Dead Letter Queue Browser

Management interface for permanently failed documents.

Features:
- DLQ items table with pagination
- Error type filter
- File path search
- Manual retry button
- Bulk operations
- Delete permanently
- Error analytics

Created: 2025-10-26
Phase: 3.3 (Retry Infrastructure Monitoring)
"""

import streamlit as st
import requests
from datetime import datetime
import time
import pandas as pd
from typing import Dict, Any, List, Optional
from collections import Counter

# Configure API endpoint
API_BASE = "http://ecosystem-mcp:8000/api/v1"


def fetch_dlq_items(limit: int = 50, offset: int = 0) -> Optional[Dict[str, Any]]:
    """
    Fetch dead letter queue items.
    
    Args:
        limit: Maximum number of items
        offset: Number of items to skip
    
    Returns:
        Items response or None if error
    """
    try:
        response = requests.get(
            f"{API_BASE}/admin/dead-letter/items",
            params={"limit": limit, "offset": offset},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch DLQ items: {e}")
        return None


def delete_dlq_item(message_id: str) -> bool:
    """
    Permanently delete a DLQ item.
    
    Args:
        message_id: Redis stream message ID
    
    Returns:
        True if successful
    """
    try:
        response = requests.delete(
            f"{API_BASE}/admin/dead-letter/{message_id}",
            timeout=5
        )
        response.raise_for_status()
        st.success("✅ Item deleted")
        return True
    except Exception as e:
        st.error(f"Failed to delete item: {e}")
        return False


def reprocess_all_dlq() -> bool:
    """
    Reprocess all items in dead letter queue.
    
    Returns:
        True if successful
    """
    try:
        response = requests.post(
            f"{API_BASE}/admin/retry-queue/reprocess",
            json={"all": True},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        st.success(f"✅ {result['message']}")
        return True
    except Exception as e:
        st.error(f"Failed to reprocess all: {e}")
        return False


def reprocess_specific_items(message_ids: List[str]) -> bool:
    """
    Reprocess specific DLQ items.
    
    Args:
        message_ids: List of message IDs to reprocess
    
    Returns:
        True if successful
    """
    try:
        response = requests.post(
            f"{API_BASE}/admin/retry-queue/reprocess",
            json={"message_ids": message_ids},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        st.success(f"✅ {result['message']}")
        return True
    except Exception as e:
        st.error(f"Failed to reprocess items: {e}")
        return False


def analyze_errors(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze error patterns in DLQ.
    
    Args:
        items: List of DLQ items
    
    Returns:
        Analytics dict
    """
    error_types = Counter()
    file_extensions = Counter()
    retry_counts = []
    
    for item in items:
        # Error types
        error_type = item.get("error_type", "unknown")
        error_types[error_type] += 1
        
        # File extensions
        file_path = item.get("file_path", "")
        if "." in file_path:
            ext = file_path.split(".")[-1].lower()
            file_extensions[ext] += 1
        
        # Retry counts
        retry_count = item.get("retry_count", 0)
        retry_counts.append(retry_count)
    
    return {
        "error_types": dict(error_types),
        "file_extensions": dict(file_extensions),
        "avg_retry_count": sum(retry_counts) / len(retry_counts) if retry_counts else 0,
        "max_retry_count": max(retry_counts) if retry_counts else 0
    }


def show():
    """Main function to display dead letter queue browser."""
    
    st.title("💀 Dead Letter Queue Browser")
    st.markdown("Management interface for permanently failed documents")
    
    # ========================================================================
    # SECTION 1: Controls & Filters
    # ========================================================================
    
    st.subheader("🔧 Controls & Filters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        page_size = st.select_slider(
            "Items per page",
            options=[10, 25, 50, 100],
            value=50,
            key="dlq_page_size"
        )
    
    with col2:
        error_type_filter = st.selectbox(
            "Filter by error type",
            options=["All", "NETWORK", "TIMEOUT", "VALIDATION", "PARSE", "DATABASE", "EMBEDDING", "FILESYSTEM", "GIT", "PROCESSING", "UNKNOWN", "OTHER"],
            index=0,
            key="dlq_error_type_filter"
        )
    
    with col3:
        search_query = st.text_input(
            "Search file path",
            placeholder="Enter file path or pattern",
            key="dlq_search_query"
        )
    
    # Pagination controls
    col1, col2, col3, col4 = st.columns([1, 1, 2, 1])
    
    with col1:
        current_page = st.number_input(
            "Page",
            min_value=1,
            value=1,
            step=1,
            key="dlq_current_page"
        )
    
    with col2:
        if st.button("⬅️ Previous", key="dlq_prev_page"):
            if current_page > 1:
                st.session_state.dlq_current_page = current_page - 1
                st.rerun()
    
    with col3:
        st.markdown("")  # Spacer
    
    with col4:
        if st.button("Next ➡️", key="dlq_next_page"):
            st.session_state.dlq_current_page = current_page + 1
            st.rerun()
    
    st.markdown("---")
    
    # ========================================================================
    # SECTION 2: Bulk Operations
    # ========================================================================
    
    st.subheader("🔄 Bulk Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Retry All", key="dlq_retry_all_btn", type="primary"):
            with st.spinner("Reprocessing all items..."):
                if reprocess_all_dlq():
                    time.sleep(1)
                    st.rerun()
    
    with col2:
        if st.button("🗑️ Clear All", key="dlq_clear_all_btn"):
            st.warning("⚠️ This action will permanently delete all DLQ items!")
            if st.button("Confirm Clear All", key="dlq_confirm_clear_all"):
                # Note: Requires implementation of bulk delete endpoint
                st.error("Bulk delete endpoint not yet implemented")
    
    with col3:
        if st.button("📊 Refresh", key="dlq_refresh_btn"):
            st.rerun()
    
    st.markdown("---")
    
    # ========================================================================
    # SECTION 3: Fetch & Display Items
    # ========================================================================
    
    # Calculate offset
    offset = (current_page - 1) * page_size
    
    # Fetch items
    items_response = fetch_dlq_items(limit=page_size, offset=offset)
    
    if not items_response:
        st.error("Failed to load DLQ items. Please check API connectivity.")
        return
    
    items = items_response.get("items", [])
    total = items_response.get("total", 0)
    
    # Apply filters
    filtered_items = items
    
    if error_type_filter != "All":
        filtered_items = [
            item for item in filtered_items
            if item.get("error_type", "").upper() == error_type_filter
        ]
    
    if search_query:
        filtered_items = [
            item for item in filtered_items
            if search_query.lower() in item.get("file_path", "").lower()
        ]
    
    # ========================================================================
    # SECTION 4: Statistics
    # ========================================================================
    
    st.subheader("📊 Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total DLQ Items",
            value=total,
            help="Total documents in dead letter queue"
        )
    
    with col2:
        st.metric(
            label="Filtered Items",
            value=len(filtered_items),
            help="Items matching current filters"
        )
    
    with col3:
        st.metric(
            label="Current Page",
            value=f"{current_page}",
            help="Current pagination page"
        )
    
    with col4:
        total_pages = (total + page_size - 1) // page_size
        st.metric(
            label="Total Pages",
            value=total_pages,
            help="Total number of pages"
        )
    
    st.markdown("---")
    
    # ========================================================================
    # SECTION 5: Error Analytics
    # ========================================================================
    
    if items:
        st.subheader("📈 Error Analytics")
        
        analytics = analyze_errors(items)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Error Types Distribution**")
            error_types_df = pd.DataFrame(
                list(analytics["error_types"].items()),
                columns=["Error Type", "Count"]
            )
            st.bar_chart(error_types_df.set_index("Error Type"))
        
        with col2:
            st.markdown("**File Extensions Distribution**")
            if analytics["file_extensions"]:
                ext_df = pd.DataFrame(
                    list(analytics["file_extensions"].items()),
                    columns=["Extension", "Count"]
                )
                st.bar_chart(ext_df.set_index("Extension"))
            else:
                st.info("No file extension data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label="Average Retry Count",
                value=f"{analytics['avg_retry_count']:.1f}",
                help="Average number of retries before DLQ"
            )
        
        with col2:
            st.metric(
                label="Max Retry Count",
                value=analytics["max_retry_count"],
                help="Maximum retry count observed"
            )
        
        st.markdown("---")
    
    # ========================================================================
    # SECTION 6: Items Table
    # ========================================================================
    
    st.subheader("📋 Dead Letter Items")
    
    if filtered_items:
        st.markdown(f"**Showing {len(filtered_items)} items (Page {current_page})**")
        
        # Convert to DataFrame
        df_items = []
        for idx, item in enumerate(filtered_items):
            df_items.append({
                "Index": offset + idx + 1,
                "File Path": item.get("file_path", "unknown"),
                "Error Type": item.get("error_type", "unknown"),
                "Error Message": item.get("error_message", "")[:100] + "...",
                "Retry Count": item.get("retry_count", 0),
                "Failed At": item.get("failed_at", "unknown")[:19],
                "Job ID": item.get("job_id", "unknown")[:8],
                "Message ID": item.get("message_id", "")
            })
        
        df = pd.DataFrame(df_items)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # ========================================================================
        # SECTION 7: Item Actions
        # ========================================================================
        
        st.subheader("🔧 Item Actions")
        
        st.markdown("**Select an item to perform actions:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_index = st.selectbox(
                "Select item by index",
                options=range(1, len(filtered_items) + 1),
                format_func=lambda x: f"#{offset + x}: {filtered_items[x-1].get('file_path', 'unknown')[:50]}",
                key="dlq_selected_index"
            )
        
        if selected_index:
            selected_item = filtered_items[selected_index - 1]
            message_id = selected_item.get("message_id", "")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Retry This Item", key="dlq_retry_item_btn"):
                    with st.spinner("Reprocessing item..."):
                        if reprocess_specific_items([message_id]):
                            time.sleep(1)
                            st.rerun()
            
            with col2:
                if st.button("🗑️ Delete This Item", key="dlq_delete_item_btn"):
                    with st.spinner("Deleting item..."):
                        if delete_dlq_item(message_id):
                            time.sleep(1)
                            st.rerun()
            
            with col3:
                st.markdown("")  # Spacer
            
            # Show item details
            with st.expander("📄 Item Details"):
                st.json(selected_item)
    
    else:
        if total == 0:
            st.success("✅ Dead letter queue is empty - no permanent failures!")
        else:
            st.info(f"No items match your filters. Total DLQ items: {total}")
    
    st.markdown("---")
    
    # ========================================================================
    # SECTION 8: Help & Documentation
    # ========================================================================
    
    with st.expander("ℹ️ Help & Documentation"):
        st.markdown("""
        ### Dead Letter Queue (DLQ)
        
        The DLQ contains documents that have permanently failed processing after exhausting all retry attempts.
        
        **Common Causes:**
        - Network issues during ingestion
        - Invalid file formats or corrupted files
        - Database connection failures
        - Embedding service errors
        - Git repository access issues
        
        **Actions:**
        - **Retry:** Move item back to retry queue with reset retry count
        - **Delete:** Permanently remove item from DLQ
        - **Retry All:** Bulk retry all DLQ items
        
        **Best Practices:**
        1. Review error messages to identify root causes
        2. Fix underlying issues before bulk retry
        3. Monitor error type distribution for patterns
        4. Keep DLQ clean by deleting irrelevant failures
        
        **API Endpoints:**
        - `GET /admin/dead-letter/items` - List DLQ items
        - `DELETE /admin/dead-letter/{id}` - Delete specific item
        - `POST /admin/retry-queue/reprocess` - Reprocess items
        """)


if __name__ == "__main__":
    show()

