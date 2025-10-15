"""
Embeddings Manager

Dashboard page for managing embeddings, including regeneration
and health monitoring.
"""

import streamlit as st
import httpx
from datetime import datetime


def show(api_base_url: str):
    """
    Display embeddings manager page.
    
    Args:
        api_base_url: Base URL of the API
    """
    st.title("🎯 Embeddings Manager")
    st.markdown("Monitor and manage document embeddings for semantic search")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Overview",
        "🔄 Regenerate",
        "🏥 Health"
    ])
    
    # ============================================================================
    # Tab 1: Overview
    # ============================================================================
    with tab1:
        st.header("📊 Embedding Statistics")
        
        try:
            response = httpx.get(
                f"{api_base_url}/api/v1/admin/embeddings/stats",
                timeout=10.0
            )
            
            if response.status_code == 200:
                stats = response.json()
                
                # Display metrics in columns
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total Documents",
                        f"{stats['total_documents']:,}",
                        help="Total documents in PostgreSQL"
                    )
                
                with col2:
                    st.metric(
                        "Total Embeddings",
                        f"{stats['total_embeddings']:,}",
                        help="Total embeddings in ChromaDB"
                    )
                
                with col3:
                    st.metric(
                        "Missing",
                        f"{stats['missing_embeddings']:,}",
                        delta=f"-{stats['missing_embeddings']}" if stats['missing_embeddings'] > 0 else None,
                        delta_color="inverse",
                        help="Documents without embeddings"
                    )
                
                with col4:
                    coverage = stats['coverage_percent']
                    st.metric(
                        "Coverage",
                        f"{coverage:.1f}%",
                        help="Percentage of documents with embeddings"
                    )
                
                # Progress bar
                st.markdown("### Coverage Progress")
                st.progress(coverage / 100.0, text=f"{coverage:.1f}% coverage")
                
                # Status indicators
                st.markdown("---")
                st.markdown("### Status")
                
                if stats['missing_embeddings'] == 0:
                    st.success("✅ All documents have embeddings!")
                    st.balloons()
                elif stats['missing_embeddings'] < 10:
                    st.info(f"⚠️ {stats['missing_embeddings']} documents missing embeddings")
                elif coverage < 50:
                    st.error(f"❌ Low coverage: {stats['missing_embeddings']} documents need embeddings")
                else:
                    st.warning(f"⚠️ {stats['missing_embeddings']} documents missing embeddings")
                
                # Last updated
                st.caption(f"Last updated: {stats['timestamp']}")
            
            else:
                st.error(f"❌ Failed to fetch stats (HTTP {response.status_code})")
        
        except httpx.RequestError as e:
            st.error(f"❌ Connection error: {e}")
            st.info("💡 Make sure the ecosystem-mcp service is running")
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    # ============================================================================
    # Tab 2: Regenerate
    # ============================================================================
    with tab2:
        st.header("🔄 Regenerate Embeddings")
        st.markdown("""
        Generate embeddings for documents that don't have them.
        This process runs in the background and may take several minutes.
        """)
        
        # Get current stats
        try:
            response = httpx.get(
                f"{api_base_url}/api/v1/admin/embeddings/stats",
                timeout=10.0
            )
            
            if response.status_code == 200:
                stats = response.json()
                missing = stats['missing_embeddings']
                
                if missing == 0:
                    st.success("✅ All documents already have embeddings!")
                    st.info("No regeneration needed. All documents are fully embedded.")
                else:
                    # Configuration
                    st.markdown("### Configuration")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        batch_size = st.slider(
                            "Batch Size",
                            min_value=1,
                            max_value=50,
                            value=10,
                            help="Number of documents to process at once"
                        )
                    
                    with col2:
                        skip_existing = st.checkbox(
                            "Skip Existing",
                            value=True,
                            help="Skip documents that already have embeddings"
                        )
                    
                    # Estimates
                    st.markdown("### Estimates")
                    estimated_time = max(1, int((missing * 2) / 60))  # ~2 sec per doc
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Documents to Process", f"{missing:,}")
                    with col2:
                        st.metric("Estimated Time", f"~{estimated_time} min")
                    
                    st.markdown("---")
                    
                    # Start button
                    if st.button("🚀 Start Regeneration", type="primary", use_container_width=True):
                        with st.spinner("Starting regeneration..."):
                            try:
                                response = httpx.post(
                                    f"{api_base_url}/api/v1/admin/embeddings/regenerate",
                                    json={
                                        "batch_size": batch_size,
                                        "skip_existing": skip_existing
                                    },
                                    timeout=30.0
                                )
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    st.success(f"✅ {result['message']}")
                                    st.info(f"⏱️ Estimated completion: ~{result['estimated_time_minutes']} minutes")
                                    st.markdown("""
                                    **Process started in background!**
                                    
                                    Monitor progress:
                                    - Check the Overview tab
                                    - Watch the logs in the terminal
                                    - Refresh this page periodically
                                    """)
                                else:
                                    st.error(f"❌ Failed to start regeneration (HTTP {response.status_code})")
                            
                            except Exception as e:
                                st.error(f"❌ Error starting regeneration: {e}")
                    
                    # Warning
                    st.markdown("---")
                    st.warning("""
                    ⚠️ **Note:** 
                    - Regeneration runs in the background
                    - The process cannot be cancelled once started
                    - Large batches may use significant resources
                    - Monitor system health during regeneration
                    """)
            
            else:
                st.error(f"❌ Failed to fetch stats (HTTP {response.status_code})")
        
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    # ============================================================================
    # Tab 3: Health
    # ============================================================================
    with tab3:
        st.header("🏥 Embedding System Health")
        st.markdown("Check the health of embedding-related components")
        
        if st.button("🔄 Refresh Health", type="secondary"):
            st.rerun()
        
        try:
            response = httpx.get(
                f"{api_base_url}/api/v1/admin/embeddings/health",
                timeout=10.0
            )
            
            if response.status_code == 200:
                health = response.json()
                
                # Overall status
                status = health.get('status', 'unknown')
                
                if status == 'healthy':
                    st.success("✅ Embedding system is healthy")
                elif status == 'degraded':
                    st.warning("⚠️ Embedding system is degraded")
                else:
                    st.error("❌ Embedding system is unhealthy")
                
                st.markdown("---")
                
                # Component details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 🗄️ ChromaDB")
                    chromadb = health.get('chromadb', {})
                    
                    if chromadb.get('healthy'):
                        st.success("✅ Healthy")
                        st.metric("Embeddings", f"{chromadb.get('count', 0):,}")
                    else:
                        st.error("❌ Unhealthy")
                
                with col2:
                    st.markdown("### 🤖 Embedding Service")
                    embedding_svc = health.get('embedding_service', {})
                    
                    if embedding_svc.get('healthy'):
                        st.success("✅ Healthy")
                        st.info("Service can generate embeddings")
                    else:
                        st.error("❌ Unhealthy")
                        st.warning("Cannot generate embeddings")
                
                # Timestamp
                st.markdown("---")
                st.caption(f"Last checked: {health.get('timestamp', 'N/A')}")
                
                # Recommendations
                if status != 'healthy':
                    st.markdown("---")
                    st.markdown("### 💡 Troubleshooting")
                    
                    if not chromadb.get('healthy'):
                        st.markdown("""
                        **ChromaDB Issues:**
                        - Check if ChromaDB container is running
                        - Verify data directory is accessible
                        - Check circuit breaker status
                        - Review ChromaDB logs for errors
                        """)
                    
                    if not embedding_svc.get('healthy'):
                        st.markdown("""
                        **Embedding Service Issues:**
                        - Check if Ollama is running
                        - Verify nomic-embed-text model is available
                        - Check Ollama logs for errors
                        - Test: `curl http://ollama:11434/api/tags`
                        """)
            
            else:
                st.error(f"❌ Failed to fetch health (HTTP {response.status_code})")
        
        except Exception as e:
            st.error(f"❌ Error: {e}")

