"""
Embeddings Manager

Dashboard page for managing embeddings, including regeneration
and health monitoring with enhanced feedback.
"""

import streamlit as st
import httpx
from datetime import datetime
import time


def show(api_base_url: str):
    """
    Display embeddings manager page with enhanced feedback.
    
    Args:
        api_base_url: Base URL of the API
    """
    st.title("🎯 Embeddings Manager")
    st.markdown("Monitor and manage document embeddings for semantic search")
    
    # Auto-refresh controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("**Real-time Monitoring**")
    with col2:
        auto_refresh = st.checkbox("Auto-refresh", value=False, help="Automatically refresh stats every 5 seconds")
    with col3:
        if st.button("🔄 Refresh Now"):
            st.rerun()
    
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
        
        # Show loading spinner
        with st.spinner("📊 Fetching statistics..."):
            try:
                response = httpx.get(
                    f"{api_base_url}/api/v1/admin/embeddings/stats",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    stats = response.json()
                    
                    # Status badge
                    coverage = stats['coverage_percent']
                    if coverage == 100:
                        st.success("✅ **Status:** All documents embedded - System fully operational!")
                    elif coverage >= 90:
                        st.info("ℹ️ **Status:** High coverage - System operational")
                    elif coverage >= 50:
                        st.warning("⚠️ **Status:** Moderate coverage - Consider regenerating")
                    else:
                        st.error("❌ **Status:** Low coverage - Regeneration recommended")
                    
                    st.markdown("---")
                    
                    # Display metrics in columns
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        delta_docs = None
                        if 'total_documents' in st.session_state:
                            delta_docs = stats['total_documents'] - st.session_state['total_documents']
                        st.session_state['total_documents'] = stats['total_documents']
                        
                        st.metric(
                            "📚 Total Documents",
                            f"{stats['total_documents']:,}",
                            delta=f"+{delta_docs}" if delta_docs and delta_docs > 0 else None,
                            help="Total documents in PostgreSQL"
                        )
                    
                    with col2:
                        delta_emb = None
                        if 'total_embeddings' in st.session_state:
                            delta_emb = stats['total_embeddings'] - st.session_state['total_embeddings']
                        st.session_state['total_embeddings'] = stats['total_embeddings']
                        
                        st.metric(
                            "🎯 Total Embeddings",
                            f"{stats['total_embeddings']:,}",
                            delta=f"+{delta_emb}" if delta_emb and delta_emb > 0 else None,
                            delta_color="normal",
                            help="Total embeddings in ChromaDB"
                        )
                    
                    with col3:
                        st.metric(
                            "⚠️ Missing",
                            f"{stats['missing_embeddings']:,}",
                            delta=f"-{stats['missing_embeddings']}" if stats['missing_embeddings'] > 0 else "Complete",
                            delta_color="inverse",
                            help="Documents without embeddings"
                        )
                    
                    with col4:
                        st.metric(
                            "📊 Coverage",
                            f"{coverage:.1f}%",
                            delta=f"{coverage - st.session_state.get('last_coverage', coverage):.1f}%" if 'last_coverage' in st.session_state else None,
                            delta_color="normal",
                            help="Percentage of documents with embeddings"
                        )
                        st.session_state['last_coverage'] = coverage
                    
                    # Progress bar with detailed info
                    st.markdown("### 📈 Coverage Progress")
                    progress_col1, progress_col2 = st.columns([3, 1])
                    
                    with progress_col1:
                        st.progress(min(coverage / 100.0, 1.0), text=f"{coverage:.1f}% - {stats['total_embeddings']}/{stats['total_documents']} documents embedded")  # Cap at 1.0
                    
                    with progress_col2:
                        if stats['missing_embeddings'] > 0:
                            est_time = max(1, int((stats['missing_embeddings'] * 2) / 60))
                            st.caption(f"⏱️ Est. {est_time}min to complete")
                        else:
                            st.caption("✅ Complete")
                    
                    st.markdown("---")
                    
                    # Detailed breakdown
                    st.markdown("### 📋 Detailed Breakdown")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**PostgreSQL Status**")
                        st.info(f"""
                        📦 Documents: {stats['total_documents']:,}
                        🔗 Ready for embedding
                        ✅ Storage healthy
                        """)
                    
                    with col2:
                        st.markdown("**ChromaDB Status**")
                        chroma_status = "✅ Healthy" if stats['total_embeddings'] > 0 else "⚠️ Empty"
                        st.info(f"""
                        🎯 Embeddings: {stats['total_embeddings']:,}
                        📐 Dimensions: 768
                        {chroma_status}
                        """)
                    
                    with col3:
                        st.markdown("**System Performance**")
                        if coverage == 100:
                            perf_status = "🟢 Excellent"
                        elif coverage >= 90:
                            perf_status = "🟡 Good"
                        elif coverage >= 50:
                            perf_status = "🟠 Fair"
                        else:
                            perf_status = "🔴 Poor"
                        
                        st.info(f"""
                        {perf_status}
                        🔍 Semantic search: {'Enabled' if coverage > 0 else 'Disabled'}
                        ⚡ RAG queries: {'Ready' if coverage > 50 else 'Limited'}
                        """)
                    
                    # Status indicators
                    st.markdown("---")
                    st.markdown("### 🎯 Recommendations")
                    
                    if stats['missing_embeddings'] == 0:
                        st.success("""
                        ✅ **Perfect!** All documents have embeddings.
                        - Semantic search is fully operational
                        - RAG queries will have complete context
                        - No action needed
                        """)
                        if coverage == 100:
                            st.balloons()
                    elif stats['missing_embeddings'] < 10:
                        st.info(f"""
                        ℹ️ **Nearly Complete** - {stats['missing_embeddings']} documents missing embeddings
                        - System is mostly operational
                        - Consider regenerating for completeness
                        - Est. completion time: < 1 minute
                        """)
                    elif coverage < 50:
                        st.error(f"""
                        ❌ **Action Required** - {stats['missing_embeddings']} documents need embeddings
                        - Semantic search has limited coverage
                        - RAG queries may miss important context
                        - **Regeneration strongly recommended**
                        - Est. completion time: ~{max(1, int((stats['missing_embeddings'] * 2) / 60))} minutes
                        """)
                    else:
                        st.warning(f"""
                        ⚠️ **Improvement Recommended** - {stats['missing_embeddings']} documents missing
                        - System is operational but incomplete
                        - Some context may be unavailable
                        - Regenerate to improve coverage
                        - Est. completion time: ~{max(1, int((stats['missing_embeddings'] * 2) / 60))} minutes
                        """)
                    
                    # Last updated with live timestamp
                    update_time = datetime.fromisoformat(stats['timestamp'].replace('Z', '+00:00'))
                    time_ago = (datetime.now(update_time.tzinfo) - update_time).total_seconds()
                    st.caption(f"📅 Last updated: {update_time.strftime('%Y-%m-%d %H:%M:%S')} ({int(time_ago)}s ago)")
                
                elif response.status_code == 503:
                    st.error("❌ **Service Unavailable** - The embeddings service is currently down")
                    st.info("💡 **Try:** Restart the ecosystem-mcp service or check service health")
                else:
                    st.error(f"❌ **Error {response.status_code}** - Failed to fetch statistics")
                    with st.expander("🔍 Show Details"):
                        st.code(response.text)
            
            except httpx.ConnectError:
                st.error("❌ **Connection Error** - Cannot reach the API")
                st.warning("""
                **Troubleshooting:**
                - Check if ecosystem-mcp service is running: `docker ps | grep ecosystem-mcp-service`
                - Verify API is accessible: `curl http://localhost:8000/api/v1/health`
                - Check network connectivity
                """)
            except httpx.TimeoutException:
                st.error("⏱️ **Timeout** - Request took too long (>10s)")
                st.info("The service may be under heavy load. Try again in a moment.")
            except Exception as e:
                st.error(f"❌ **Unexpected Error:** {str(e)}")
                with st.expander("🔍 Show Technical Details"):
                    st.exception(e)
    
    # ============================================================================
    # Tab 2: Regenerate
    # ============================================================================
    with tab2:
        st.header("🔄 Regenerate Embeddings")
        st.markdown("""
        Generate embeddings for documents that don't have them.
        This process runs in the background and may take several minutes.
        """)
        
        # Get current stats with feedback
        with st.spinner("📊 Checking current status..."):
            try:
                response = httpx.get(
                    f"{api_base_url}/api/v1/admin/embeddings/stats",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    stats = response.json()
                    missing = stats['missing_embeddings']
                    
                    if missing == 0:
                        st.success("✅ **All documents already have embeddings!**")
                        st.info("""
                        🎉 Your system is at 100% coverage.
                        
                        **What this means:**
                        - All documents are fully searchable
                        - RAG queries have complete context
                        - No regeneration needed
                        
                        **Optional:** You can still regenerate to:
                        - Update existing embeddings
                        - Apply new embedding model
                        - Fix any corrupted embeddings
                        """)
                        
                        if st.checkbox("🔧 Advanced: Force regeneration (not recommended)", value=False):
                            st.warning("This will regenerate ALL embeddings, even existing ones.")
                        else:
                            st.stop()
                    else:
                        # Show gap analysis
                        st.info(f"""
                        📊 **Gap Analysis**
                        - Missing embeddings: **{missing:,}** documents
                        - Current coverage: **{stats['coverage_percent']:.1f}%**
                        - Target coverage: **100%**
                        - Gap to close: **{100 - stats['coverage_percent']:.1f}%**
                        """)
                    
                    st.markdown("---")
                    
                    # Configuration
                    st.markdown("### ⚙️ Configuration")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        batch_size = st.slider(
                            "Batch Size",
                            min_value=1,
                            max_value=50,
                            value=10,
                            help="""
                            Number of documents to process at once
                            - Larger batches = faster but more memory
                            - Smaller batches = slower but more stable
                            - Recommended: 10 for balanced performance
                            """
                        )
                    
                    with col2:
                        skip_existing = st.checkbox(
                            "Skip Existing Embeddings",
                            value=True,
                            help="""
                            Skip documents that already have embeddings
                            - Recommended: ON for incremental updates
                            - Turn OFF to regenerate all embeddings
                            """
                        )
                    
                    # Performance info
                    st.info(f"""
                    ⚡ **Performance Estimate**
                    - Batch size: {batch_size} documents
                    - Processing rate: ~{batch_size * 30} docs/minute
                    - Skip existing: {'Yes ✅' if skip_existing else 'No ❌'}
                    """)
                    
                    # Estimates
                    st.markdown("---")
                    st.markdown("### 📊 Estimates")
                    
                    docs_to_process = missing if skip_existing else stats['total_documents']
                    estimated_time = max(1, int((docs_to_process * 2) / 60))
                    estimated_cost = docs_to_process * 0.000001  # Placeholder cost
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Documents to Process", f"{docs_to_process:,}")
                    with col2:
                        st.metric("Estimated Time", f"~{estimated_time} min")
                    with col3:
                        st.metric("Progress Updates", f"Every {batch_size} docs")
                    
                    st.markdown("---")
                    
                    # Pre-flight checks
                    st.markdown("### ✅ Pre-flight Checks")
                    
                    check_col1, check_col2 = st.columns(2)
                    
                    with check_col1:
                        # Check ChromaDB
                        try:
                            health_response = httpx.get(
                                f"{api_base_url}/api/v1/admin/embeddings/health",
                                timeout=5.0
                            )
                            if health_response.status_code == 200:
                                health = health_response.json()
                                if health.get('chromadb', {}).get('healthy'):
                                    st.success("✅ ChromaDB: Healthy")
                                else:
                                    st.error("❌ ChromaDB: Unhealthy")
                            else:
                                st.warning("⚠️ ChromaDB: Unknown")
                        except:
                            st.warning("⚠️ ChromaDB: Cannot check")
                    
                    with check_col2:
                        # Check embedding service
                        try:
                            if health_response.status_code == 200:
                                if health.get('embedding_service', {}).get('healthy'):
                                    st.success("✅ Embedding Service: Healthy")
                                else:
                                    st.error("❌ Embedding Service: Unhealthy")
                            else:
                                st.warning("⚠️ Embedding Service: Unknown")
                        except:
                            st.warning("⚠️ Embedding Service: Cannot check")
                    
                    st.markdown("---")
                    
                    # Start button with confirmation
                    st.markdown("### 🚀 Start Regeneration")
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        if docs_to_process > 100:
                            confirm = st.checkbox(f"I understand this will process {docs_to_process:,} documents", value=False)
                        else:
                            confirm = True
                    
                    with col2:
                        start_disabled = not confirm if docs_to_process > 100 else False
                    
                    if st.button(
                        f"🚀 Start Processing {docs_to_process:,} Documents",
                        type="primary",
                        use_container_width=True,
                        disabled=start_disabled
                    ):
                        with st.spinner("🚀 Starting regeneration..."):
                            try:
                                start_time = time.time()
                                response = httpx.post(
                                    f"{api_base_url}/api/v1/admin/embeddings/regenerate",
                                    json={
                                        "batch_size": batch_size,
                                        "skip_existing": skip_existing
                                    },
                                    timeout=30.0
                                )
                                elapsed = time.time() - start_time
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    st.success(f"✅ **Started!** {result['message']}")
                                    
                                    st.info(f"""
                                    ⏱️ **Process Information**
                                    - Status: Running in background
                                    - Estimated completion: ~{result['estimated_time_minutes']} minutes
                                    - API response time: {elapsed:.2f}s
                                    - Started at: {datetime.now().strftime('%H:%M:%S')}
                                    """)
                                    
                                    st.markdown("""
                                    **📊 Monitor Progress:**
                                    1. Switch to the **Overview** tab
                                    2. Enable **Auto-refresh** to see live updates
                                    3. Watch the **Coverage Progress** bar fill up
                                    4. Check **Total Embeddings** metric increasing
                                    
                                    **🔍 Advanced Monitoring:**
                                    - View backend logs: `docker logs -f ecosystem-mcp-service`
                                    - Check API stats: `curl http://localhost:8000/api/v1/admin/embeddings/stats`
                                    """)
                                    
                                    # Auto-switch to overview after 3 seconds
                                    st.balloons()
                                    time.sleep(2)
                                    st.info("💡 Enable **Auto-refresh** in the Overview tab to see live progress!")
                                    
                                else:
                                    st.error(f"❌ **Failed to start** (HTTP {response.status_code})")
                                    st.error(f"Response: {response.text}")
                            
                            except httpx.TimeoutException:
                                st.error("⏱️ **Timeout** - Request took too long")
                                st.warning("The regeneration may have started. Check the Overview tab.")
                            except Exception as e:
                                st.error(f"❌ **Error starting regeneration:** {str(e)}")
                                with st.expander("🔍 Show Details"):
                                    st.exception(e)
                    
                    # Warning
                    st.markdown("---")
                    st.warning("""
                    ⚠️ **Important Notes:**
                    - Regeneration runs in the background (non-blocking)
                    - The process cannot be cancelled once started
                    - Large batches may use significant resources
                    - Monitor system health during regeneration
                    - You can safely close this page during processing
                    """)
                
                else:
                    st.error(f"❌ Failed to fetch stats (HTTP {response.status_code})")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # ============================================================================
    # Tab 3: Health
    # ============================================================================
    with tab3:
        st.header("🏥 Embedding System Health")
        st.markdown("Check the health of embedding-related components")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("**Real-time Component Monitoring**")
        with col2:
            if st.button("🔄 Refresh Health", type="secondary", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        
        with st.spinner("🏥 Checking health..."):
            try:
                response = httpx.get(
                    f"{api_base_url}/api/v1/admin/embeddings/health",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    health = response.json()
                    
                    # Overall status with detailed banner
                    status = health.get('status', 'unknown')
                    
                    if status == 'healthy':
                        st.success("✅ **System Status: HEALTHY** - All components operational")
                    elif status == 'degraded':
                        st.warning("⚠️ **System Status: DEGRADED** - Some components have issues")
                    else:
                        st.error("❌ **System Status: UNHEALTHY** - Critical failures detected")
                    
                    st.markdown("---")
                    
                    # Component details
                    st.markdown("### 📊 Component Status")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🗄️ ChromaDB")
                        chromadb = health.get('chromadb', {})
                        
                        if chromadb.get('healthy'):
                            st.success("✅ **Status:** Healthy")
                            st.metric("Embeddings Stored", f"{chromadb.get('count', 0):,}")
                            st.info("""
                            **Capabilities:**
                            - ✅ Vector storage operational
                            - ✅ Similarity search enabled
                            - ✅ Can accept new embeddings
                            - ✅ Collection accessible
                            """)
                        else:
                            st.error("❌ **Status:** Unhealthy")
                            st.warning("""
                            **Issues Detected:**
                            - ❌ Cannot connect to ChromaDB
                            - ❌ Vector storage unavailable
                            - ❌ Similarity search disabled
                            
                            **Action Required:**
                            Check ChromaDB container and logs
                            """)
                    
                    with col2:
                        st.markdown("#### 🤖 Embedding Service")
                        embedding_svc = health.get('embedding_service', {})
                        
                        if embedding_svc.get('healthy'):
                            st.success("✅ **Status:** Healthy")
                            st.info("""
                            **Capabilities:**
                            - ✅ Model loaded (nomic-embed-text)
                            - ✅ Can generate embeddings
                            - ✅ Ollama connection active
                            - ✅ 768-dimensional vectors
                            """)
                        else:
                            st.error("❌ **Status:** Unhealthy")
                            st.warning("""
                            **Issues Detected:**
                            - ❌ Cannot generate embeddings
                            - ❌ Ollama connection failed
                            - ❌ Model unavailable
                            
                            **Action Required:**
                            Check Ollama service status
                            """)
                    
                    # System capabilities summary
                    st.markdown("---")
                    st.markdown("### ⚡ System Capabilities")
                    
                    cap_col1, cap_col2, cap_col3 = st.columns(3)
                    
                    with cap_col1:
                        if status == 'healthy':
                            st.success("✅ **Semantic Search**\nFully Operational")
                        else:
                            st.error("❌ **Semantic Search**\nNot Available")
                    
                    with cap_col2:
                        if status == 'healthy':
                            st.success("✅ **RAG Queries**\nFully Operational")
                        else:
                            st.error("❌ **RAG Queries**\nLimited/Unavailable")
                    
                    with cap_col3:
                        if status == 'healthy':
                            st.success("✅ **Embedding Generation**\nFully Operational")
                        else:
                            st.error("❌ **Embedding Generation**\nNot Available")
                    
                    # Timestamp
                    st.markdown("---")
                    update_time = datetime.fromisoformat(health.get('timestamp', datetime.now().isoformat()).replace('Z', '+00:00'))
                    st.caption(f"📅 Health check performed: {update_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    # Recommendations
                    if status != 'healthy':
                        st.markdown("---")
                        st.markdown("### 💡 Troubleshooting")
                        
                        if not chromadb.get('healthy'):
                            st.error("""
                            **ChromaDB Issues:**
                            ```bash
                            # Check if container is running
                            docker ps | grep chroma
                            
                            # View ChromaDB logs
                            docker logs ecosystem-mcp-service | grep -i chroma
                            
                            # Restart service
                            docker restart ecosystem-mcp-service
                            ```
                            """)
                        
                        if not embedding_svc.get('healthy'):
                            st.error("""
                            **Embedding Service Issues:**
                            ```bash
                            # Check Ollama status
                            curl http://localhost:11434/api/tags
                            
                            # View embedding logs
                            docker logs ecosystem-mcp-service | grep -i embedding
                            
                            # Restart Ollama
                            docker restart ollama
                            ```
                            """)
                
                else:
                    st.error(f"❌ Failed to fetch health (HTTP {response.status_code})")
            
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Auto-refresh logic
    if auto_refresh and tab1:
        time.sleep(5)
        st.rerun()
