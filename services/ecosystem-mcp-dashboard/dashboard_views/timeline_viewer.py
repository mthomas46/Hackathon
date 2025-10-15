"""
Timeline Viewer Dashboard Page

Provides visualization of document version timelines:
- Document version history
- Visual timeline with markers
- Version comparisons
- Activity analysis
"""

import streamlit as st
import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Get API URL from session state or environment
API_URL = st.session_state.get("api_url", "http://localhost:8000")


def show():
    """Display the Timeline Viewer page."""
    st.title("📈 Document Timeline Viewer")
    st.write("Explore document version history and changes over time")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Document Timeline",
        "🕰️ As Of Date Query",
        "📊 Changes Between Dates",
        "📈 Activity Summary"
    ])
    
    with tab1:
        show_document_timeline()
    
    with tab2:
        show_as_of_query()
    
    with tab3:
        show_changes_query()
    
    with tab4:
        show_activity_summary()


def show_document_timeline():
    """Show timeline for a specific document."""
    st.subheader("📋 Document Version Timeline")
    st.write("View the complete version history of a document")
    
    # Document ID input
    document_id = st.text_input(
        "Document ID",
        placeholder="Enter document UUID",
        help="UUID of the document to view timeline for"
    )
    
    # Date range filter (optional)
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date (optional)",
            value=None,
            help="Filter timeline from this date"
        )
    with col2:
        end_date = st.date_input(
            "End Date (optional)",
            value=None,
            help="Filter timeline to this date"
        )
    
    if st.button("🔍 View Timeline", type="primary"):
        if not document_id:
            st.error("Please enter a document ID")
            return
        
        with st.spinner("Fetching timeline..."):
            try:
                # Prepare request
                payload = {
                    "document_id": document_id,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                }
                
                # Query API
                response = httpx.post(
                    f"{API_URL}/api/v1/versioning/timeline",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data["total_events"] == 0:
                        st.info("📭 No timeline events found for this document")
                        return
                    
                    st.success(f"✅ Found {data['total_events']} events")
                    
                    # Display timeline visualization
                    display_timeline_chart(data["events"])
                    
                    # Display timeline table
                    st.subheader("📊 Timeline Events")
                    display_timeline_table(data["events"])
                    
                elif response.status_code == 404:
                    st.error("❌ Document not found")
                elif response.status_code == 400:
                    st.error(f"❌ Invalid request: {response.json().get('detail', 'Unknown error')}")
                else:
                    st.error(f"❌ Error: HTTP {response.status_code}")
                    
            except httpx.TimeoutException:
                st.error("⏱️ Request timed out. Please try again.")
            except Exception as e:
                st.error(f"❌ Error fetching timeline: {str(e)}")
                logger.error(f"Timeline query error: {e}", exc_info=True)


def display_timeline_chart(events: List[Dict]):
    """Display visual timeline chart."""
    if not events:
        return
    
    # Prepare data for plotting
    df = pd.DataFrame(events)
    df['event_timestamp'] = pd.to_datetime(df['event_timestamp'])
    
    # Create interactive timeline
    fig = go.Figure()
    
    # Add scatter points for each version
    fig.add_trace(go.Scatter(
        x=df['event_timestamp'],
        y=df['version_number'],
        mode='markers+lines',
        name='Versions',
        marker=dict(
            size=12,
            color=df['version_number'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Version")
        ),
        text=[
            f"v{row['version_number']}<br>{row['actor']}<br>{row['event_timestamp']}"
            for _, row in df.iterrows()
        ],
        hovertemplate='<b>%{text}</b><br>Hash: %{customdata}<extra></extra>',
        customdata=df['content_hash'].apply(lambda x: x[:16] + '...')
    ))
    
    # Highlight latest version
    latest = df[df['is_latest'] == True]
    if not latest.empty:
        fig.add_trace(go.Scatter(
            x=latest['event_timestamp'],
            y=latest['version_number'],
            mode='markers',
            name='Latest',
            marker=dict(
                size=20,
                color='red',
                symbol='star',
                line=dict(width=2, color='darkred')
            ),
            text=['Latest Version'],
            hoverinfo='text'
        ))
    
    # Update layout
    fig.update_layout(
        title="Document Version Timeline",
        xaxis_title="Date",
        yaxis_title="Version Number",
        hovermode='closest',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_timeline_table(events: List[Dict]):
    """Display timeline events in a table."""
    # Convert to DataFrame
    df = pd.DataFrame(events)
    
    # Format columns
    df['event_timestamp'] = pd.to_datetime(df['event_timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df['content_hash'] = df['content_hash'].apply(lambda x: x[:16] + '...')
    df['is_latest'] = df['is_latest'].apply(lambda x: '⭐ Latest' if x else '')
    
    # Select and rename columns
    display_df = df[[
        'version_number',
        'event_timestamp',
        'actor',
        'content_hash',
        'title',
        'is_latest'
    ]].rename(columns={
        'version_number': 'Version',
        'event_timestamp': 'Timestamp',
        'actor': 'Actor',
        'content_hash': 'Content Hash',
        'title': 'Title',
        'is_latest': 'Status'
    })
    
    # Display
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Export option
    if st.button("📥 Export to CSV"):
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="timeline_export.csv",
            mime="text/csv"
        )


def show_as_of_query():
    """Show documents as of a specific date."""
    st.subheader("🕰️ Time Travel: Documents As Of Date")
    st.write("View all documents as they existed at a specific point in time")
    
    # Date picker
    as_of_date = st.date_input(
        "View documents as of:",
        value=datetime.now() - timedelta(days=7),
        help="Select a date to see what documents existed then"
    )
    
    # Pagination
    col1, col2 = st.columns(2)
    with col1:
        limit = st.number_input("Results per page", min_value=10, max_value=500, value=100)
    with col2:
        page = st.number_input("Page", min_value=1, value=1)
    
    offset = (page - 1) * limit
    
    if st.button("🔍 Query", type="primary"):
        with st.spinner(f"Querying documents as of {as_of_date}..."):
            try:
                # Prepare request
                payload = {
                    "as_of_date": datetime.combine(as_of_date, datetime.min.time()).isoformat(),
                    "filters": {},
                    "limit": limit,
                    "offset": offset
                }
                
                # Query API
                response = httpx.post(
                    f"{API_URL}/api/v1/versioning/as-of",
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data["total_documents"] == 0:
                        st.info(f"📭 No documents found as of {as_of_date}")
                        return
                    
                    st.success(f"✅ Found {data['total_documents']} documents")
                    
                    # Display documents
                    display_as_of_results(data["documents"])
                    
                    # Pagination info
                    total_pages = (data["total_documents"] + limit - 1) // limit
                    st.info(f"Page {page} of ~{total_pages}")
                    
                else:
                    st.error(f"❌ Error: HTTP {response.status_code}")
                    
            except httpx.TimeoutException:
                st.error("⏱️ Request timed out. Please try again.")
            except Exception as e:
                st.error(f"❌ Error querying documents: {str(e)}")
                logger.error(f"As-of query error: {e}", exc_info=True)


def display_as_of_results(documents: List[Dict]):
    """Display 'as of' query results."""
    # Convert to DataFrame
    df = pd.DataFrame(documents)
    
    # Format columns
    df['modified_at'] = pd.to_datetime(df['modified_at']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df['content_hash'] = df['content_hash'].apply(lambda x: x[:16] + '...')
    df['content_size'] = df['content_size'].apply(lambda x: f"{x / 1024:.1f} KB" if x > 0 else "N/A")
    
    # Select and rename columns
    display_df = df[[
        'title',
        'version_number',
        'modified_at',
        'created_by',
        'source_path',
        'content_hash',
        'content_size'
    ]].rename(columns={
        'title': 'Title',
        'version_number': 'Version',
        'modified_at': 'Modified',
        'created_by': 'Author',
        'source_path': 'Path',
        'content_hash': 'Hash',
        'content_size': 'Size'
    })
    
    # Display
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Expanders for individual documents
    st.subheader("📄 Document Details")
    for doc in documents:
        with st.expander(f"📄 {doc['title']} (v{doc['version_number']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.text(f"Document ID: {doc['document_id']}")
                st.text(f"Version ID: {doc['version_id']}")
                st.text(f"Version: {doc['version_number']}")
                st.text(f"Author: {doc['created_by']}")
            
            with col2:
                st.text(f"Modified: {doc['modified_at']}")
                st.text(f"Content Hash: {doc['content_hash'][:16]}...")
                st.text(f"Size: {doc['content_size'] / 1024:.1f} KB")
                st.text(f"Path: {doc['source_path']}")


def show_changes_query():
    """Show changes between two dates."""
    st.subheader("📊 Changes Between Dates")
    st.write("See what documents changed in a specific time period")
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30)
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now()
        )
    
    limit = st.number_input("Max results", min_value=10, max_value=500, value=100)
    
    if st.button("🔍 Find Changes", type="primary"):
        with st.spinner(f"Analyzing changes from {start_date} to {end_date}..."):
            try:
                # Prepare request
                payload = {
                    "start_date": datetime.combine(start_date, datetime.min.time()).isoformat(),
                    "end_date": datetime.combine(end_date, datetime.max.time()).isoformat(),
                    "limit": limit
                }
                
                # Query API
                response = httpx.post(
                    f"{API_URL}/api/v1/versioning/changes",
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data["total_changes"] == 0:
                        st.info("📭 No changes found in this time period")
                        return
                    
                    st.success(f"✅ Found {data['total_changes']} documents with changes")
                    
                    # Display changes
                    display_changes_results(data["changes"])
                    
                else:
                    st.error(f"❌ Error: HTTP {response.status_code}")
                    
            except httpx.TimeoutException:
                st.error("⏱️ Request timed out. Please try again.")
            except Exception as e:
                st.error(f"❌ Error querying changes: {str(e)}")
                logger.error(f"Changes query error: {e}", exc_info=True)


def display_changes_results(changes: List[Dict]):
    """Display changes query results."""
    # Convert to DataFrame
    df = pd.DataFrame(changes)
    
    # Format columns
    df['first_change'] = pd.to_datetime(df['first_change']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df['last_change'] = pd.to_datetime(df['last_change']).dt.strftime('%Y-%m-%d %H:%M:%S')
    df['contributors_str'] = df['contributors'].apply(lambda x: ', '.join(x) if x else 'Unknown')
    
    # Select and rename columns
    display_df = df[[
        'title',
        'version_count',
        'first_change',
        'last_change',
        'contributors_str',
        'source_path'
    ]].rename(columns={
        'title': 'Title',
        'version_count': 'Versions',
        'first_change': 'First Change',
        'last_change': 'Last Change',
        'contributors_str': 'Contributors',
        'source_path': 'Path'
    })
    
    # Sort by version count (most active)
    display_df = display_df.sort_values('Versions', ascending=False)
    
    # Display
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Visualization: Top 10 most active documents
    st.subheader("📊 Most Active Documents")
    top_10 = df.nlargest(10, 'version_count')
    
    fig = px.bar(
        top_10,
        x='title',
        y='version_count',
        title='Top 10 Most Active Documents',
        labels={'title': 'Document', 'version_count': 'Number of Versions'},
        color='version_count',
        color_continuous_scale='Viridis'
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


def show_activity_summary():
    """Show activity summary and statistics."""
    st.subheader("📈 Activity Summary")
    st.write("Overall statistics and trends")
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            key="activity_start"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            key="activity_end"
        )
    
    # Auto-refresh option
    auto_refresh = st.checkbox("Auto-refresh every 30 seconds", value=False)
    if auto_refresh:
        st.markdown(
            '<meta http-equiv="refresh" content="30">',
            unsafe_allow_html=True
        )
    
    # Manual refresh button
    if st.button("🔄 Refresh", type="primary") or auto_refresh:
        with st.spinner("Fetching activity summary..."):
            try:
                # Query API
                response = httpx.get(
                    f"{API_URL}/api/v1/versioning/activity-summary",
                    params={
                        "start_date": datetime.combine(start_date, datetime.min.time()).isoformat(),
                        "end_date": datetime.combine(end_date, datetime.max.time()).isoformat()
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Display metrics
                    display_activity_metrics(data)
                    
                    # Display charts
                    display_activity_charts(data)
                    
                    # Display deduplication stats
                    display_deduplication_stats()
                    
                else:
                    st.error(f"❌ Error: HTTP {response.status_code}")
                    
            except httpx.TimeoutException:
                st.error("⏱️ Request timed out. Please try again.")
            except Exception as e:
                st.error(f"❌ Error fetching activity summary: {str(e)}")
                logger.error(f"Activity summary error: {e}", exc_info=True)


def display_activity_metrics(data: Dict):
    """Display activity metrics."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📄 Total Versions",
            data["total_versions"],
            help="Total number of versions created"
        )
    
    with col2:
        st.metric(
            "📚 Unique Documents",
            data["unique_documents"],
            help="Number of unique documents modified"
        )
    
    with col3:
        st.metric(
            "👥 Contributors",
            data["unique_contributors"],
            help="Number of unique contributors"
        )


def display_activity_charts(data: Dict):
    """Display activity visualization charts."""
    # Activity by day
    if data["activity_by_day"]:
        st.subheader("📅 Activity by Day")
        
        df_daily = pd.DataFrame([
            {"date": date, "versions": count}
            for date, count in data["activity_by_day"].items()
        ])
        df_daily['date'] = pd.to_datetime(df_daily['date'])
        df_daily = df_daily.sort_values('date')
        
        fig = px.line(
            df_daily,
            x='date',
            y='versions',
            title='Daily Version Activity',
            labels={'date': 'Date', 'versions': 'Versions Created'},
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Top contributors
    if data["top_contributors"]:
        st.subheader("👥 Top Contributors")
        
        df_contributors = pd.DataFrame([
            {"contributor": name, "contributions": count}
            for name, count in data["top_contributors"].items()
        ])
        df_contributors = df_contributors.sort_values('contributions', ascending=True)
        
        fig = px.bar(
            df_contributors,
            y='contributor',
            x='contributions',
            title='Top 10 Contributors',
            labels={'contributor': 'Contributor', 'contributions': 'Versions Created'},
            orientation='h',
            color='contributions',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)


def display_deduplication_stats():
    """Display content deduplication statistics."""
    st.subheader("💾 Content Deduplication Stats")
    
    try:
        response = httpx.get(
            f"{API_URL}/api/v1/versioning/deduplication-stats",
            timeout=15.0
        )
        
        if response.status_code == 200:
            data = response.json()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Unique Content Items",
                    data["unique_content_items"],
                    help="Number of unique content blobs stored"
                )
            
            with col2:
                st.metric(
                    "Total Versions",
                    data["total_versions"],
                    help="Total versions referencing content"
                )
            
            with col3:
                st.metric(
                    "Space Saved",
                    f"{data['space_saved'] / 1024 / 1024:.1f} MB",
                    help="Storage saved by deduplication"
                )
            
            with col4:
                st.metric(
                    "Dedup Ratio",
                    f"{data['deduplication_ratio']:.1f}%",
                    help="Percentage of storage saved"
                )
            
            # Progress bar for deduplication
            st.progress(data['deduplication_ratio'] / 100, text=f"{data['deduplication_ratio']:.1f}% storage efficiency")
            
        else:
            st.warning(f"Could not fetch deduplication stats (HTTP {response.status_code})")
    
    except Exception as e:
        st.warning(f"Could not fetch deduplication stats: {str(e)}")


if __name__ == "__main__":
    show()

