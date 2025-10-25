"""Comprehensive home dashboard page with feature overview."""

import streamlit as st
import httpx
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

def show(api_base_url: str):
    """Show comprehensive home dashboard."""
    
    # Header with service status
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("🧠 Ecosystem MCP Dashboard")
        st.caption("Intelligent Documentation Analysis & RAG System")
    
    # Fetch health status
    try:
        health_response = httpx.get(f"{api_base_url}/health", timeout=5.0)
        if health_response.status_code == 200:
            health_data = health_response.json()
            is_healthy = health_data.get("status") == "healthy"
            
            with col2:
                if is_healthy:
                    st.success("🟢 System Healthy")
                else:
                    st.error("🔴 System Issues")
            
            with col3:
                uptime = health_data.get("uptime_seconds", 0)
                if uptime < 60:
                    st.metric("Uptime", f"{int(uptime)}s")
                elif uptime < 3600:
                    st.metric("Uptime", f"{int(uptime/60)}m")
                else:
                    st.metric("Uptime", f"{int(uptime/3600)}h")
        else:
            with col2:
                st.error("🔴 API Unreachable")
    except Exception as e:
        with col2:
            st.error("🔴 Connection Failed")
    
    st.markdown("---")
    
    # Quick Stats
    try:
        stats_response = httpx.get(f"{api_base_url}/api/v1/admin/stats", timeout=5.0)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                doc_count = stats.get("documents", {}).get("total", 0)
                st.metric("📚 Documents", f"{doc_count:,}")
            
            with col2:
                emb_count = stats.get("documents", {}).get("embeddings", 0)
                st.metric("🔮 Embeddings", f"{emb_count:,}")
            
            with col3:
                queue_count = stats.get("queues", {}).get("ingestion", 0)
                st.metric("📥 Queue", queue_count)
            
            with col4:
                cost = stats.get("cost", {}).get("total_usd", 0)
                st.metric("💰 Cost", f"${cost:.2f}")
    except:
        pass
    
    st.markdown("---")
    
    # Feature Categories
    st.header("🎯 Feature Categories")
    
    # Create tabs for feature categories
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔍 Query & Search",
        "📥 Data Management", 
        "📖 Documentation",
        "📊 Analysis & Reports",
        "🏗️ Infrastructure",
        "📈 Monitoring"
    ])
    
    with tab1:
        st.subheader("🔍 Query & Search Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Core RAG")
            st.markdown("✅ **Standard RAG Query** - Basic question answering")
            st.markdown("✅ **Enhanced Query** - Mode and tier selection")
            st.markdown("✅ **Multi-Pass RAG** - Iterative refinement")
            st.markdown("✅ **Context-Aware RAG** - Hierarchical filtering")
            
        with col2:
            st.markdown("#### Advanced Search")
            st.markdown("✅ **Document Search** - Full-text and semantic")
            st.markdown("⚠️ **Temporal RAG** - Time-travel queries (API ready)")
            st.markdown("⚠️ **Dynamic Temporal** - Auto-timeline (API ready)")
            st.markdown("✅ **Vector Search** - Embedding-based retrieval")
        
        st.info("💡 **Tip:** Use Context-Aware RAG for service-specific queries")
    
    with tab2:
        st.subheader("📥 Data Management Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Ingestion")
            st.markdown("✅ **Ingestion Manager** - Job creation and monitoring")
            st.markdown("✅ **Mode Comparison** - Quick/Standard/Historical/Full")
            st.markdown("✅ **Job Recovery** - Orphaned job detection")
            st.markdown("✅ **Worker Monitor** - Worker health and status")
            
        with col2:
            st.markdown("#### Documents")
            st.markdown("✅ **Document Browser** - Search and view documents")
            st.markdown("✅ **Embeddings Manager** - Vector management")
            st.markdown("✅ **Timeline Viewer** - Version history")
            st.markdown("⚠️ **Discovery Scanner** - Repo scanning (API ready)")
        
        st.success("✨ **4 Ingestion Modes:** Quick (1-2min), Standard (5-10min), Historical (15-30min), Full (1-3hr)")
    
    with tab3:
        st.subheader("📖 Documentation Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Generation")
            st.markdown("✅ **Documentation Generator** - Multi-pass generation")
            st.markdown("✅ **Documentation Browser** - View generated docs")
            st.markdown("⚠️ **Run Management** - Track generation runs (API ready)")
            st.markdown("⚠️ **Quality Metrics** - Doc quality scoring (API ready)")
            
        with col2:
            st.markdown("#### Maintenance")
            st.markdown("⚠️ **Staleness Detection** - Outdated docs (API ready)")
            st.markdown("⚠️ **Coverage Analysis** - Gap detection (API ready)")
            st.markdown("⚠️ **Consistency Checker** - Conflict detection (API ready)")
            st.markdown("⚠️ **Auto-Refresher** - Smart updates (API ready)")
        
        st.warning("⚠️ **Note:** Maintenance features available via API - UI coming soon")
    
    with tab4:
        st.subheader("📊 Analysis & Reports Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Timeline Analysis")
            st.markdown("✅ **Timeline Viewer** - Document evolution")
            st.markdown("✅ **Timeline Analysis** - Period-based queries")
            st.markdown("⚠️ **Evolution Tracking** - Change over time (API ready)")
            st.markdown("⚠️ **Period Comparison** - Before/after analysis (API ready)")
            
        with col2:
            st.markdown("#### Reports")
            st.markdown("⚠️ **Gap Analysis** - Documentation gaps (API ready)")
            st.markdown("⚠️ **Drift Detection** - Code-doc drift (API ready)")
            st.markdown("⚠️ **Progression Reports** - Timeline reports (API ready)")
            st.markdown("⚠️ **Consolidation** - Redundancy detection (API ready)")
        
        st.info("📊 **Export Formats:** Markdown, HTML, JSON")
    
    with tab5:
        st.subheader("🏗️ Infrastructure Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Core Services")
            st.markdown("✅ **Container Management** - Docker control")
            st.markdown("✅ **Redis Explorer** - Key-value browser")
            st.markdown("✅ **PostgreSQL Explorer** - Database browser")
            st.markdown("✅ **ChromaDB Explorer** - Vector DB browser")
            
        with col2:
            st.markdown("#### Management")
            st.markdown("✅ **Embeddings Manager** - Vector operations")
            st.markdown("✅ **Worker Monitor** - Worker health")
            st.markdown("⚠️ **Orchestration** - Parallel execution (API ready)")
            st.markdown("✅ **Configuration** - System settings")
        
        st.success("🐳 **6 Services:** PostgreSQL, Redis, Ollama, ChromaDB, API, Dashboard")
    
    with tab6:
        st.subheader("📈 Monitoring Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Performance")
            st.markdown("✅ **Cache Performance** - Hit rates and stats")
            st.markdown("✅ **Metrics & Analytics** - System-wide metrics")
            st.markdown("✅ **Performance Monitor** - Real-time monitoring")
            st.markdown("✅ **Quality Dashboard** - Documentation quality")
            
        with col2:
            st.markdown("#### Health")
            st.markdown("✅ **Health & Infrastructure** - Component status")
            st.markdown("✅ **Diagnostics** - System diagnostics")
            st.markdown("✅ **Logs Viewer** - Real-time logs")
            st.markdown("✅ **Repository Contexts** - Context analytics")
        
        st.success("⚡ **10-50× Faster:** Embedding service with ONNX optimization")
    
    st.markdown("---")
    
    # System Architecture Overview
    st.header("🏗️ System Architecture")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🎯 API Layer")
        st.markdown("- **172 Endpoints**")
        st.markdown("- **47 Route Modules**")
        st.markdown("- **REST + MCP Protocol**")
        st.markdown("- **Rate Limited**")
    
    with col2:
        st.markdown("### 💾 Storage Layer")
        st.markdown("- **PostgreSQL** (Metadata)")
        st.markdown("- **ChromaDB** (Vectors)")
        st.markdown("- **Redis** (Cache/Queue)")
        st.markdown("- **Git** (Versioning)")
    
    with col3:
        st.markdown("### 🤖 AI Layer")
        st.markdown("- **Ollama** (Local LLM)")
        st.markdown("- **FastEmbed** (Vectors)")
        st.markdown("- **Multi-Model Routing**")
        st.markdown("- **Cost Tracking**")
    
    st.markdown("---")
    
    # Quick Actions
    st.header("🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🤖 Query Documents", use_container_width=True):
            st.info("Navigate to: Query & Search > RAG Query")
    
    with col2:
        if st.button("📥 Start Ingestion", use_container_width=True):
            st.info("Navigate to: Data Management > Ingestion Manager")
    
    with col3:
        if st.button("📖 Generate Docs", use_container_width=True):
            st.info("Navigate to: Documentation > Documentation Generator")
    
    with col4:
        if st.button("🏥 Check Health", use_container_width=True):
            st.info("Navigate to: Overview > Health & Infrastructure")
    
    st.markdown("---")
    
    # Status Summary
    st.header("📊 Feature Status Summary")
    
    # Create status table
    status_data = {
        "Category": [
            "Query & Search",
            "Data Management",
            "Documentation",
            "Analysis & Reports",
            "Infrastructure",
            "Monitoring"
        ],
        "Available Features": [8, 8, 4, 4, 9, 8],
        "API Ready": [10, 12, 16, 12, 12, 8],
        "Coverage": ["80%", "67%", "25%", "33%", "75%", "100%"]
    }
    
    import pandas as pd
    df = pd.DataFrame(status_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("✅ Total Features in UI", "41", help="Features accessible through dashboard")
    
    with col2:
        st.metric("⚠️ API-Only Features", "29", help="Features available via API, UI coming soon")
    
    st.markdown("---")
    
    # Footer
    st.caption(f"🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("📚 Ecosystem MCP Dashboard v1.0.0 - 70% API Coverage")
