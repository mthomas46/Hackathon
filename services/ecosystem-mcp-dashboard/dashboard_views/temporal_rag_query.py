"""
Temporal RAG Query Interface

Time-travel queries, evolution tracking, and period comparison.
Interfaces with the Temporal RAG API endpoints.
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import httpx

# Fallback if api_tracker not available
try:
    from utils.api_tracker import make_api_request, show_api_tracker_widget
except ImportError:
    def make_api_request(base_url, endpoint, method="GET", json_data=None, params=None, timeout=30.0, show_error=True):
        """Fallback API request function."""
        try:
            url = f"{base_url}{endpoint}"
            if method == "GET":
                response = httpx.get(url, params=params, timeout=timeout)
            else:
                response = httpx.post(url, json=json_data, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            if show_error:
                st.error(f"API Error: {e}")
            return None
    
    def show_api_tracker_widget():
        """Fallback tracker widget."""
        pass


def show(api_base_url: str):
    """Display Temporal RAG query interface."""
    st.title("⏰ Temporal RAG Query")
    st.markdown("Query documents at specific points in time or track evolution")
    
    # Query type selector
    query_type = st.radio(
        "Query Type",
        ["🕐 Query As Of (Point in Time)", "📈 Query Evolution", "🔄 Query What Changed", "📊 Analyze Period", "⚖️ Compare Periods"],
        horizontal=True
    )
    
    st.markdown("---")
    
    if query_type == "🕐 Query As Of (Point in Time)":
        show_query_as_of(api_base_url)
    elif query_type == "📈 Query Evolution":
        show_query_evolution(api_base_url)
    elif query_type == "🔄 Query What Changed":
        show_query_what_changed(api_base_url)
    elif query_type == "📊 Analyze Period":
        show_analyze_period(api_base_url)
    elif query_type == "⚖️ Compare Periods":
        show_compare_periods(api_base_url)


def show_query_as_of(api_base_url: str):
    """Query documents as they were at a specific date."""
    st.subheader("🕐 Query As Of (Point in Time)")
    st.markdown("Query documents as they existed at a specific date in the past.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        query = st.text_area(
            "Question",
            placeholder="What was the architecture of the authentication service?",
            height=100,
            help="Ask a question about your codebase at a specific point in time"
        )
    
    with col2:
        # Date selector
        as_of_date = st.date_input(
            "As Of Date",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now(),
            help="Query documents as they were on this date"
        )
        
        limit = st.slider("Max Results", 1, 20, 5)
    
    if st.button("🔍 Query As Of", type="primary", disabled=not query):
        with st.spinner("Querying temporal documents..."):
            result = make_api_request(
                api_base_url,
                "/api/v1/versioning/as-of",
                method="POST",
                json_data={
                    "query": query,
                    "as_of_date": as_of_date.isoformat(),
                    "limit": limit
                },
                timeout=30.0
            )
            
            if result:
                st.success("✅ Query completed!")
                
                # Display answer
                if "answer" in result:
                    st.markdown("### 💡 Answer")
                    st.info(result["answer"])
                
                # Display metadata
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Documents Found", result.get("document_count", 0))
                with col2:
                    st.metric("As Of Date", as_of_date.strftime("%Y-%m-%d"))
                with col3:
                    confidence = result.get("confidence", 0)
                    st.metric("Confidence", f"{confidence:.0%}")
                
                # Display sources
                if "sources" in result and result["sources"]:
                    st.markdown("### 📚 Sources")
                    for idx, source in enumerate(result["sources"], 1):
                        with st.expander(f"Source {idx}: {source.get('file_path', 'Unknown')}"):
                            st.markdown(f"**Version:** {source.get('version', 'N/A')}")
                            st.markdown(f"**Date:** {source.get('date', 'N/A')}")
                            st.code(source.get('content', ''), language="markdown")


def show_query_evolution(api_base_url: str):
    """Track how a topic evolved over time."""
    st.subheader("📈 Query Evolution")
    st.markdown("Track how documentation about a topic evolved over time.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        document_id = st.text_input(
            "Document ID",
            placeholder="Enter document UUID",
            help="UUID of the document to track"
        )
    
    with col2:
        # Date range
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input(
                "Start Date (optional)",
                value=None,
                max_value=datetime.now()
            )
        with col_end:
            end_date = st.date_input(
                "End Date (optional)",
                value=None,
                max_value=datetime.now()
            )
    
    if st.button("📈 Track Evolution", type="primary", disabled=not document_id):
        with st.spinner("Analyzing evolution..."):
            request_data = {"document_id": document_id}
            if start_date:
                request_data["start_date"] = datetime.combine(start_date, datetime.min.time()).isoformat()
            if end_date:
                request_data["end_date"] = datetime.combine(end_date, datetime.min.time()).isoformat()
            
            result = make_api_request(
                api_base_url,
                "/api/v1/versioning/timeline",
                method="POST",
                json_data=request_data,
                timeout=30.0
            )
            
            if result:
                st.success("✅ Evolution analysis completed!")
                
                # Display timeline
                if "timeline" in result and result["timeline"]:
                    st.markdown("### 📅 Evolution Timeline")
                    
                    for period in result["timeline"]:
                        with st.expander(f"{period.get('date', 'Unknown Date')} - {period.get('title', 'Change')}"):
                            st.markdown(period.get('summary', 'No summary available'))
                            if "changes" in period:
                                st.markdown("**Changes:**")
                                for change in period["changes"]:
                                    st.markdown(f"- {change}")
                
                # Display summary
                if "summary" in result:
                    st.markdown("### 📊 Summary")
                    st.info(result["summary"])


def show_query_what_changed(api_base_url: str):
    """Query what changed between two dates."""
    st.subheader("🔄 Query What Changed")
    st.markdown("Identify changes in documentation between two dates.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_input(
            "Topic (Optional)",
            placeholder="API endpoints",
            help="Focus on specific topic or leave blank for all changes"
        )
        
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now()
        )
    
    with col2:
        scope = st.selectbox(
            "Scope",
            ["All Changes", "Breaking Changes Only", "New Features Only", "Deprecations Only"]
        )
        
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            max_value=datetime.now()
        )
    
    if st.button("🔍 Find Changes", type="primary"):
        with st.spinner("Analyzing changes..."):
            result = make_api_request(
                api_base_url,
                "/api/v1/versioning/changes",
                method="GET",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                timeout=30.0
            )
            
            if result:
                st.success("✅ Change analysis completed!")
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Changes", result.get("total_changes", 0))
                with col2:
                    st.metric("Files Changed", result.get("files_changed", 0))
                with col3:
                    st.metric("Breaking Changes", result.get("breaking_changes", 0))
                with col4:
                    st.metric("New Features", result.get("new_features", 0))
                
                # Display changes
                if "changes" in result and result["changes"]:
                    st.markdown("### 📝 Changes")
                    
                    for change in result["changes"]:
                        severity = change.get("severity", "INFO")
                        icon = {"BREAKING": "🔴", "WARNING": "🟡", "INFO": "🔵"}.get(severity, "⚪")
                        
                        with st.expander(f"{icon} {change.get('title', 'Change')} - {change.get('file', 'Unknown file')}"):
                            st.markdown(f"**Type:** {change.get('type', 'N/A')}")
                            st.markdown(f"**Date:** {change.get('date', 'N/A')}")
                            st.markdown(change.get('description', 'No description available'))


def show_analyze_period(api_base_url: str):
    """Analyze documentation activity in a period."""
    st.subheader("📊 Analyze Period")
    st.markdown("Analyze documentation activity and changes within a time period.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now()
        )
    
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            max_value=datetime.now()
        )
    
    if st.button("📊 Analyze Period", type="primary"):
        with st.spinner("Analyzing period..."):
            result = make_api_request(
                api_base_url,
                "/api/v1/versioning/activity-summary",
                method="GET",
                params={
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                timeout=30.0
            )
            
            if result:
                st.success("✅ Period analysis completed!")
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Documents", result.get("document_count", 0))
                with col2:
                    st.metric("Changes", result.get("change_count", 0))
                with col3:
                    st.metric("Authors", result.get("author_count", 0))
                with col4:
                    st.metric("Activity Score", result.get("activity_score", 0))
                
                # Display activity chart
                if "activity_by_day" in result:
                    st.markdown("### 📈 Activity Over Time")
                    activity_df = pd.DataFrame(result["activity_by_day"])
                    st.line_chart(activity_df.set_index("date"))
                
                # Display top files
                if "top_files" in result and result["top_files"]:
                    st.markdown("### 📄 Most Active Files")
                    for file in result["top_files"][:10]:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{file.get('path', 'Unknown')}**")
                        with col2:
                            st.metric("Changes", file.get("changes", 0))


def show_compare_periods(api_base_url: str):
    """Compare documentation between two time periods."""
    st.subheader("⚖️ Compare Periods")
    st.markdown("Compare documentation state between two time periods.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Period 1 (Before)**")
        period1_start = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=60),
            max_value=datetime.now(),
            key="period1_start"
        )
        period1_end = st.date_input(
            "End Date",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now(),
            key="period1_end"
        )
    
    with col2:
        st.markdown("**Period 2 (After)**")
        period2_start = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now(),
            key="period2_start"
        )
        period2_end = st.date_input(
            "End Date",
            value=datetime.now(),
            max_value=datetime.now(),
            key="period2_end"
        )
    
    if st.button("⚖️ Compare Periods", type="primary"):
        with st.spinner("Comparing periods..."):
            # Compare using activity summary for both periods
            result1 = make_api_request(
                api_base_url,
                "/api/v1/versioning/activity-summary",
                method="GET",
                params={
                    "start_date": period1_start.isoformat(),
                    "end_date": period1_end.isoformat()
                },
                timeout=30.0,
                show_error=False
            )
            
            result2 = make_api_request(
                api_base_url,
                "/api/v1/versioning/activity-summary",
                method="GET",
                params={
                    "start_date": period2_start.isoformat(),
                    "end_date": period2_end.isoformat()
                },
                timeout=30.0,
                show_error=False
            )
            
            # Combine results for comparison
            result = {
                "period1": result1 if result1 else {},
                "period2": result2 if result2 else {},
                "differences": []
            } if (result1 or result2) else None
            
            if result:
                st.success("✅ Comparison completed!")
                
                # Display comparison metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("### Period 1")
                    st.metric("Documents", result.get("period1", {}).get("document_count", 0))
                    st.metric("Changes", result.get("period1", {}).get("changes", 0))
                
                with col2:
                    st.markdown("### Period 2")
                    st.metric("Documents", result.get("period2", {}).get("document_count", 0))
                    st.metric("Changes", result.get("period2", {}).get("changes", 0))
                
                with col3:
                    st.markdown("### Delta")
                    doc_delta = result.get("period2", {}).get("document_count", 0) - result.get("period1", {}).get("document_count", 0)
                    change_delta = result.get("period2", {}).get("changes", 0) - result.get("period1", {}).get("changes", 0)
                    st.metric("Documents", doc_delta, delta=doc_delta)
                    st.metric("Changes", change_delta, delta=change_delta)
                
                # Display differences
                if "differences" in result and result["differences"]:
                    st.markdown("### 🔍 Key Differences")
                    for diff in result["differences"]:
                        st.markdown(f"- {diff}")

