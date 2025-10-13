"""Metrics & Analytics page."""

import streamlit as st
import httpx
import plotly.graph_objects as go
from datetime import datetime

def show(api_base_url: str):
    """Show metrics & analytics page."""
    st.title("📊 Metrics & Analytics")
    
    # Refresh controls
    col1, col2 = st.columns([1, 5])
    
    with col1:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (30s)")
    
    try:
        # Fetch admin stats
        response = httpx.get(
            f"{api_base_url}/api/v1/admin/stats",
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # System metrics
            st.subheader("🖥️ System Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_docs = data.get("document_count", 0)
                st.metric("Total Documents", f"{total_docs:,}")
            
            with col2:
                collection_count = data.get("collection_count", 0)
                st.metric("Collections", collection_count)
            
            with col3:
                total_embeddings = data.get("total_embeddings", 0)
                st.metric("Embeddings", f"{total_embeddings:,}")
            
            with col4:
                cache_size = data.get("cache_size_mb", 0)
                st.metric("Cache Size", f"{cache_size:.1f} MB")
            
            # Document distribution
            st.markdown("---")
            st.subheader("📁 Document Distribution")
            
            doc_types = data.get("document_types", {})
            
            if doc_types:
                fig = go.Figure(data=[go.Bar(
                    x=list(doc_types.keys()),
                    y=list(doc_types.values()),
                    marker_color='#1f77b4'
                )])
                
                fig.update_layout(
                    title="Documents by Type",
                    xaxis_title="File Type",
                    yaxis_title="Count",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No document type data available")
            
            # Query performance
            st.markdown("---")
            st.subheader("⚡ Query Performance")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_query_time = data.get("avg_query_time_ms", 0)
                st.metric("Avg Query Time", f"{avg_query_time:.0f} ms")
            
            with col2:
                total_queries = data.get("total_queries", 0)
                st.metric("Total Queries", f"{total_queries:,}")
            
            with col3:
                queries_per_sec = data.get("queries_per_second", 0)
                st.metric("Queries/sec", f"{queries_per_sec:.2f}")
            
            # Database stats
            st.markdown("---")
            st.subheader("🗄️ Database Statistics")
            
            db_stats = data.get("database", {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("DB Size", f"{db_stats.get('size_mb', 0):.1f} MB")
                st.metric("Active Connections", db_stats.get('active_connections', 0))
            
            with col2:
                st.metric("Table Count", db_stats.get('table_count', 0))
                st.metric("Index Count", db_stats.get('index_count', 0))
            
            # Redis stats
            st.markdown("---")
            st.subheader("💾 Redis Statistics")
            
            redis_stats = data.get("redis", {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Used Memory", f"{redis_stats.get('used_memory_mb', 0):.1f} MB")
            
            with col2:
                st.metric("Connected Clients", redis_stats.get('connected_clients', 0))
            
            with col3:
                st.metric("Total Keys", f"{redis_stats.get('total_keys', 0):,}")
            
            # System health timeline (placeholder)
            st.markdown("---")
            st.subheader("📈 System Health Timeline")
            st.info("Health timeline visualization coming soon...")
            
            # Full stats
            with st.expander("🔍 Raw Statistics Data"):
                st.json(data)
        
        elif response.status_code == 404:
            st.warning("Statistics endpoint not available")
            st.info("The /api/v1/admin/stats endpoint may not be implemented yet")
        
        else:
            st.error(f"Failed to fetch statistics: {response.status_code}")
            st.code(response.text)
    
    except httpx.ConnectError:
        st.error(f"❌ Cannot connect to service at {api_base_url}")
        st.info("Make sure the ecosystem-mcp service is running and accessible.")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    # Export options
    st.markdown("---")
    st.subheader("💾 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Export Metrics (JSON)", use_container_width=True):
            st.info("Exporting metrics...")
    
    with col2:
        if st.button("📊 Generate Report", use_container_width=True):
            st.info("Report generation coming soon...")
    
    with col3:
        if st.button("📧 Email Report", use_container_width=True):
            st.info("Email functionality coming soon...")

