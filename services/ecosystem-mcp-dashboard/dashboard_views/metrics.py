"""Metrics & Analytics page."""

import streamlit as st
import httpx
import plotly.graph_objects as go
from datetime import datetime

def show(api_base_url: str):
    """Show metrics & analytics page."""
    st.title("📊 Metrics & Analytics")
    
    st.markdown("""
    View comprehensive system metrics including document counts, queue status, 
    processing costs, and embedding coverage.
    """)
    
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
            
            # Extract nested data
            documents_data = data.get("documents", {})
            queues_data = data.get("queues", {})
            cost_data = data.get("cost", {})
            
            # System metrics
            st.subheader("🖥️ System Metrics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_docs = documents_data.get("total", 0)
                st.metric("Total Documents", f"{total_docs:,}")
            
            with col2:
                total_embeddings = documents_data.get("embeddings", 0)
                st.metric("Embeddings", f"{total_embeddings:,}")
            
            with col3:
                ingestion_queue = queues_data.get("ingestion", 0)
                st.metric("Ingestion Queue", f"{ingestion_queue:,}")
            
            with col4:
                total_cost = cost_data.get("total_usd", 0)
                st.metric("Total Cost", f"${total_cost:.2f}")
            
            # Queue Status
            st.markdown("---")
            st.subheader("📋 Queue Status")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                ingestion_queue = queues_data.get("ingestion", 0)
                st.metric(
                    "Ingestion Queue", 
                    f"{ingestion_queue:,}",
                    delta=None,
                    help="Documents waiting to be ingested"
                )
            
            with col2:
                embedding_queue = queues_data.get("embedding", 0)
                st.metric(
                    "Embedding Queue", 
                    f"{embedding_queue:,}",
                    delta=None,
                    help="Documents waiting for embeddings"
                )
            
            with col3:
                failed_queue = queues_data.get("failed", 0)
                st.metric(
                    "Failed Jobs", 
                    f"{failed_queue:,}",
                    delta=None,
                    help="Jobs that failed processing"
                )
            
            # Queue visualization
            if ingestion_queue > 0 or embedding_queue > 0 or failed_queue > 0:
                fig = go.Figure(data=[go.Bar(
                    x=['Ingestion', 'Embedding', 'Failed'],
                    y=[ingestion_queue, embedding_queue, failed_queue],
                    marker_color=['#1f77b4', '#ff7f0e', '#d62728']
                )])
                
                fig.update_layout(
                    title="Queue Status",
                    xaxis_title="Queue Type",
                    yaxis_title="Count",
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("✅ All queues are empty!")
            
            # Cost Tracking
            st.markdown("---")
            st.subheader("💰 Cost Tracking")
            
            col1, col2 = st.columns(2)
            
            with col1:
                total_cost = cost_data.get("total_usd", 0)
                st.metric(
                    "Total Cost (All Time)", 
                    f"${total_cost:.4f}",
                    help="Total API costs incurred"
                )
            
            with col2:
                today_cost = cost_data.get("today_usd", 0)
                st.metric(
                    "Today's Cost", 
                    f"${today_cost:.4f}",
                    help="Costs incurred today"
                )
            
            # Cost visualization
            if total_cost > 0:
                remaining_today = max(0, total_cost - today_cost)
                
                fig = go.Figure(data=[go.Pie(
                    labels=['Today', 'Previous Days'],
                    values=[today_cost, remaining_today],
                    marker=dict(colors=['#ff7f0e', '#1f77b4']),
                    hole=.4
                )])
                
                fig.update_layout(
                    title="Cost Distribution",
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("💡 No costs tracked yet. Costs will appear as you use the API.")
            
            # Document & Embedding Ratio
            st.markdown("---")
            st.subheader("📊 Document Processing Status")
            
            total_docs = documents_data.get("total", 0)
            total_embeddings = documents_data.get("embeddings", 0)
            
            if total_docs > 0:
                embedded_percent = (total_embeddings / total_docs) * 100
                not_embedded = total_docs - total_embeddings
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Embedding Coverage",
                        f"{embedded_percent:.1f}%",
                        help="Percentage of documents with embeddings"
                    )
                
                with col2:
                    st.metric(
                        "Documents Without Embeddings",
                        f"{not_embedded:,}",
                        help="Documents that still need embeddings"
                    )
                
                # Progress bar
                st.progress(embedded_percent / 100)
                
                if embedded_percent == 100:
                    st.success("✅ All documents have embeddings!")
                elif embedded_percent > 90:
                    st.info("🟡 Almost there! Most documents are embedded.")
                elif embedded_percent < 50:
                    st.warning("⚠️ Less than half of documents have embeddings.")
            else:
                st.info("No documents in the system yet.")
            
            # Infrastructure Health
            st.markdown("---")
            st.subheader("🏥 Infrastructure Health")
            
            try:
                # Fetch health check data
                health_response = httpx.get(
                    f"{api_base_url}/api/v1/health/datasources",
                    timeout=5.0
                )
                
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        postgres_status = health_data.get("postgresql", {}).get("status", "unknown")
                        postgres_latency = health_data.get("postgresql", {}).get("latency_ms", 0)
                        
                        if postgres_status == "healthy":
                            st.success(f"✅ PostgreSQL\n\n{postgres_latency:.0f}ms")
                        else:
                            st.error(f"❌ PostgreSQL\n\n{postgres_status}")
                    
                    with col2:
                        redis_status = health_data.get("redis", {}).get("status", "unknown")
                        redis_latency = health_data.get("redis", {}).get("latency_ms", 0)
                        
                        if redis_status == "healthy":
                            st.success(f"✅ Redis\n\n{redis_latency:.0f}ms")
                        else:
                            st.error(f"❌ Redis\n\n{redis_status}")
                    
                    with col3:
                        qdrant_status = health_data.get("qdrant", {}).get("status", "unknown")
                        qdrant_latency = health_data.get("qdrant", {}).get("latency_ms", 0)
                        
                        if qdrant_status == "healthy":
                            st.success(f"✅ Qdrant\n\n{qdrant_latency:.0f}ms")
                        else:
                            st.error(f"❌ Qdrant\n\n{qdrant_status}")
                else:
                    st.info("Infrastructure health data not available")
            
            except Exception as health_error:
                st.info(f"Could not fetch infrastructure health: {str(health_error)}")
            
            # Full stats
            st.markdown("---")
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
    
    # Data Export
    st.markdown("---")
    st.subheader("💾 Data Export")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export All Metrics (JSON)", use_container_width=True):
            try:
                stats_response = httpx.get(f"{api_base_url}/api/v1/admin/stats", timeout=10.0)
                if stats_response.status_code == 200:
                    st.download_button(
                        "💾 Download Metrics",
                        data=stats_response.text,
                        file_name=f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                else:
                    st.error("Failed to fetch metrics")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("🔄 Refresh All Data", use_container_width=True):
            st.rerun()

