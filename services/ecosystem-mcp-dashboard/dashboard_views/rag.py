"""Enhanced RAG Query interface page with multiple modes and tier selection."""

import streamlit as st
import httpx
import json
from datetime import datetime
import os
import sys

# Import state manager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.state_manager import StateManager
from utils.document_query_managers import (
    check_for_similar_query,
    show_similar_query_notification,
    generate_query_id
)

def show(api_base_url: str):
    """Show enhanced RAG query page."""
    # Initialize state manager
    StateManager.initialize()
    
    st.title("🤖 RAG Query Interface")
    
    st.markdown("""
    **Intelligent question answering** with multiple processing modes and tier selection.
    
    Choose your query mode and LLM tier for optimal performance!
    """)
    
    # Fetch and display tier status
    st.markdown("---")
    st.subheader("🔌 LLM Tier Status")
    
    tier_data = None
    try:
        tier_response = httpx.get(f"{api_base_url}/api/v1/query/tier-status", timeout=5.0)
        
        if tier_response.status_code == 200:
            tier_data = tier_response.json()
            tiers = tier_data.get("tiers", {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                cursor_tier = tiers.get("cursor", {})
                if cursor_tier.get("available"):
                    st.success("✅ **Tier 1: Cursor IDE**")
                else:
                    st.error("❌ **Tier 1: Cursor IDE**")
                st.caption(f"Model: {cursor_tier.get('model', 'Unknown')}")
                st.caption(cursor_tier.get('use_case', ''))
            
            with col2:
                desktop_tier = tiers.get("desktop", {})
                if desktop_tier.get("available"):
                    st.success("✅ **Tier 2: Desktop Ollama**")
                else:
                    st.warning("⚠️ **Tier 2: Desktop Ollama**")
                st.caption(f"Model: {desktop_tier.get('model', 'Unknown')}")
                st.caption(desktop_tier.get('use_case', ''))
            
            with col3:
                docker_tier = tiers.get("docker", {})
                if docker_tier.get("available"):
                    st.success("✅ **Tier 3: Docker Ollama**")
                else:
                    st.error("❌ **Tier 3: Docker Ollama**")
                st.caption(f"Model: {docker_tier.get('model', 'Unknown')}")
                st.caption(docker_tier.get('use_case', ''))
            
            recommendation = tier_data.get("recommendation", "auto")
            st.info(f"💡 **Recommended tier:** `{recommendation.upper()}`")
    
    except Exception as e:
        st.warning(f"⚠️ Tier status unavailable: {str(e)}")
    
    # Query mode info in expander
    with st.expander("ℹ️ **About Query Modes**", expanded=False):
        mode_col1, mode_col2, mode_col3 = st.columns(3)
        
        with mode_col1:
            st.markdown("**🎯 RAG Mode (Full)**")
            st.write("• Semantic document search")
            st.write("• Context building")
            st.write("• LLM synthesis")
            st.write("• Source citations")
            st.write("• Confidence scoring")
            st.write("⚡ Speed: 3-10s")
            st.write("⭐ Quality: Highest")
        
        with mode_col2:
            st.markdown("**📄 Contextual Mode**")
            st.write("• Document retrieval")
            st.write("• Simple context")
            st.write("• Basic LLM generation")
            st.write("")
            st.write("")
            st.write("⚡ Speed: 1-3s")
            st.write("⭐ Quality: Medium")
        
        with mode_col3:
            st.markdown("**⚡ Basic Mode**")
            st.write("• No document search")
            st.write("• Direct LLM query")
            st.write("• LLM knowledge only")
            st.write("")
            st.write("")
            st.write("⚡ Speed: <1s")
            st.write("⭐ Quality: Varies")
    
    # Query type selector
    st.markdown("---")
    query_type = st.radio(
        "Query Type",
        options=["standard", "multi-pass"],
        format_func=lambda x: {
            "standard": "🚀 Standard Query",
            "multi-pass": "🔬 Multi-Pass Deep Analysis"
        }[x],
        horizontal=True,
        help="Standard: Single query | Multi-Pass: Complex decomposition with multiple questions"
    )
    
    if query_type == "standard":
        st.subheader("🔍 Standard Query")
    else:
        st.subheader("🔬 Multi-Pass Deep Analysis")
        st.info("""
        **Multi-Pass Analysis** decomposes your query into sections with secondary questions for comprehensive answers.
        
        Perfect for:
        • Complex technical questions requiring deep analysis
        • Research queries needing multiple perspectives  
        • Comprehensive system understanding
        """)
    
    # Query form based on type
    # Initialize submitted to avoid UnboundLocalError
    submitted = False
    question = ""
    
    if query_type == "standard":
        with st.form("rag_query_form"):
            question = st.text_area(
                "❓ Your Question",
                placeholder="e.g., How does the caching system work?",
                height=100,
                help="Ask any question - mode determines how it's processed"
            )
            
            # Mode and tier selection
            col1, col2 = st.columns(2)
            
            with col1:
                mode = st.selectbox(
                "🎯 Query Mode",
                options=["rag", "contextual", "basic"],
                index=0,
                format_func=lambda x: {
                    "rag": "🎯 RAG (Full) - Best quality",
                    "contextual": "📄 Contextual - Quick with docs",
                    "basic": "⚡ Basic - Fastest, no docs"
                }[x],
                help="RAG: Full analysis | Contextual: Quick lookup | Basic: LLM only"
            )
            
            # Show mode description
            mode_descriptions = {
                "rag": "Full RAG with retrieval, augmentation, and synthesis",
                "contextual": "Simple document context + LLM generation",
                "basic": "Pure LLM query without documents"
            }
            st.caption(f"ℹ️ {mode_descriptions[mode]}")
            
            with col2:
                tier = st.selectbox(
                    "🔌 LLM Tier",
                    options=["auto", "cursor", "desktop", "docker"],
                    index=0,
                    format_func=lambda x: {
                        "auto": "🤖 Auto (Recommended)",
                        "cursor": "🥇 Tier 1: Cursor IDE",
                        "desktop": "🥈 Tier 2: Desktop Ollama",
                        "docker": "🥉 Tier 3: Docker Ollama"
                    }[x],
                    help="Auto: Best available | Manual: Force specific tier with fallback"
                )
                
                # Show tier warning if unavailable
                if tier_data and tier != "auto":
                    tier_info = tier_data.get("tiers", {}).get(tier, {})
                    if not tier_info.get("available", False):
                        st.caption(f"⚠️ {tier.title()} tier unavailable - will fallback")
                    else:
                        st.caption(f"✅ {tier.title()} tier available")
            
            # Settings (4 columns - including Response Length)
            st.markdown("##### ⚙️ Settings")
            settings_col1, settings_col2, settings_col3, settings_col4 = st.columns(4)
            
            with settings_col1:
                if mode in ["rag", "contextual"]:
                    n_results = st.slider(
                        "📚 Documents",
                        min_value=1,
                        max_value=50,
                        value=10,
                        help="Number of documents to retrieve"
                    )
                else:
                    n_results = 10
                    st.info("📌 Basic mode doesn't use documents")
            
            with settings_col2:
                temperature = st.slider(
                    "🌡️ Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.7,
                    step=0.1,
                    help="0 = focused, 1 = creative"
                )
            
            with settings_col3:
                max_retries = st.slider(
                    "🔄 Max Retries",
                    min_value=0,
                    max_value=5,
                    value=2,
                    help="Retry attempts if tier unavailable"
                )
            
            with settings_col4:
                response_length = st.selectbox(
                    "📏 Response Length",
                    options=["S", "M", "L", "XL"],
                    index=1,  # Default to Medium
                    format_func=lambda x: {
                        "S": "S (~500 chars)",
                        "M": "M (~1K chars)",
                        "L": "L (~2K chars)",
                        "XL": "XL (~4K chars)"
                    }[x],
                    help="Control response verbosity"
                )
            
            # Enhancement Controls
            st.markdown("##### ✨ Enhancement Controls")
            
            enh_col1, enh_col2, enh_col3, enh_col4 = st.columns(4)
            
            with enh_col1:
                use_enhancements = st.checkbox(
                    "Enable Enhancements",
                    value=True,
                    help="Use enhancement pipeline (hybrid search, query rewriting, etc.)"
                )
            
            with enh_col2:
                enable_hybrid_search = st.checkbox(
                    "Hybrid Search",
                    value=use_enhancements,
                    disabled=not use_enhancements,
                    help="Combine semantic + keyword search (BM25)"
                )
            
            with enh_col3:
                enable_query_rewriting = st.checkbox(
                    "Query Rewriting",
                    value=use_enhancements,
                    disabled=not use_enhancements,
                    help="Expand synonyms and clarify query"
                )
            
            with enh_col4:
                enable_context_optimization = st.checkbox(
                    "Context Optimization",
                    value=use_enhancements,
                    disabled=not use_enhancements,
                    help="Smart context selection and ordering"
                )
            
            if use_enhancements:
                st.info("✨ Enhancements enabled: +60% source retrieval, +8.8% confidence")
            else:
                st.warning("⚠️ Enhancements disabled: Using standard RAG only")
            
            submitted = st.form_submit_button("🚀 Submit Query", use_container_width=True)
    
    # Process query (outside form)
    if query_type == "standard" and submitted and question:
        # Add to history
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        
        st.session_state.query_history.append({
            'question': question,
            'mode': mode,
            'tier': tier,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
        with st.spinner(f"🧠 Processing ({mode.upper()} mode, {tier.upper()} tier)..."):
            try:
                start_time = datetime.now()
                
                # Convert response length to max_tokens
                length_to_tokens = {
                    "S": 150,    # ~500 chars (~125 tokens * 4 chars/token)
                    "M": 300,    # ~1K chars
                    "L": 600,    # ~2K chars
                    "XL": 1200   # ~4K chars
                }
                max_tokens = length_to_tokens.get(response_length, 300)
                
                # Make enhanced query request
                response = httpx.post(
                    f"{api_base_url}/api/v1/query/enhanced",
                    json={
                        "question": question,
                        "mode": mode,
                        "tier": tier,
                        "n_results": n_results,
                        "temperature": temperature,
                        "max_retries": max_retries,
                        "response_length": max_tokens,  # Send as integer (converted from S/M/L/XL)
                        "use_enhancements": use_enhancements,
                        "enable_hybrid_search": enable_hybrid_search if use_enhancements else False,
                        "enable_query_rewriting": enable_query_rewriting if use_enhancements else False,
                        "enable_context_optimization": enable_context_optimization if use_enhancements else False
                    },
                    timeout=300.0  # 5 minutes
                )
                
                elapsed_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display answer
                    st.markdown("---")
                    st.subheader("💡 Answer")
                    
                    # Metrics row
                    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
                    
                    with metric_col1:
                        st.metric("Mode", result.get("mode", "").upper())
                    
                    with metric_col2:
                        tier_used = result.get("tier_used", "unknown")
                        st.metric("Tier Used", tier_used.upper())
                    
                    with metric_col3:
                        tier_requested = result.get("tier_requested", "unknown")
                        st.metric("Tier Requested", tier_requested.upper())
                    
                    with metric_col4:
                        st.metric("Time", f"{elapsed_time:.2f}s")
                    
                    with metric_col5:
                        sources_count = len(result.get("sources", []))
                        st.metric("Sources", sources_count)
                    
                    # Tier fallback warning
                    if result.get("tier_used") != result.get("tier_requested"):
                        st.warning(f"⚠️ Requested `{tier_requested}` tier was unavailable. Fell back to `{tier_used}`.")
                    
                    # Answer text
                    st.markdown("### 📝 Answer")
                    answer_text = result.get("answer", "No answer generated")
                    st.markdown(answer_text)
                    
                    # Sources (if any)
                    sources = result.get("sources", [])
                    if sources:
                        st.markdown("---")
                        st.subheader(f"📚 Sources ({len(sources)})")
                        
                        for i, source in enumerate(sources, 1):
                            # Use file_path if available, otherwise use id
                            source_title = source.get('file_path', source.get('id', f'Source {i}'))
                            if len(source_title) > 80:
                                source_title = source_title[:77] + "..."
                            
                            with st.expander(f"**Source {i}:** {source_title}"):
                                source_col1, source_col2 = st.columns([3, 1])
                                
                                with source_col1:
                                    if "file_path" in source:
                                        st.markdown(f"**File:** `{source['file_path']}`")
                                    if "service" in source:
                                        st.markdown(f"**Service:** {source['service']}")
                                    if "file_type" in source:
                                        st.markdown(f"**Type:** {source['file_type']}")
                                    if "git_commit" in source:
                                        st.markdown(f"**Commit:** `{source['git_commit'][:8]}`")
                                
                                with source_col2:
                                    if "score" in source:
                                        score = source["score"]
                                        st.metric("Relevance", f"{score:.2%}")
                                    elif "relevance_score" in source:
                                        score = source["relevance_score"]
                                        st.metric("Relevance", f"{score:.3f}")
                                
                                # Show content
                                if "content" in source:
                                    content = source["content"]
                                    preview = content[:500] + "..." if len(content) > 500 else content
                                    st.text_area(
                                        "Content Preview",
                                        value=preview,
                                        height=150,
                                        disabled=True,
                                        key=f"enhanced_rag_content_{i}"
                                    )
                                elif "content_preview" in source:
                                    st.text_area(
                                        "Content Preview",
                                        value=source["content_preview"],
                                        height=150,
                                        disabled=True,
                                        key=f"enhanced_rag_preview_{i}"
                                    )
                    
                    # Metadata
                    metadata = result.get("metadata", {})
                    if metadata:
                        with st.expander("🔍 Query Metadata"):
                            meta_col1, meta_col2 = st.columns(2)
                            
                            with meta_col1:
                                if "confidence" in metadata:
                                    st.metric("Confidence", f"{metadata['confidence']:.2%}")
                                if "documents_used" in metadata:
                                    st.metric("Documents Used", metadata['documents_used'])
                                if "model" in metadata:
                                    st.write(f"**Model:** {metadata['model']}")
                            
                            with meta_col2:
                                if "note" in metadata:
                                    st.info(metadata['note'])
                                if "temperature" in metadata:
                                    st.write(f"**Temperature:** {metadata['temperature']}")
                            
                            # Full metadata JSON
                            st.json(metadata)
                
                elif response.status_code == 422:
                    st.error("❌ **Validation Error**")
                    st.error("Your query may be too long or contain invalid parameters.")
                    try:
                        error_data = response.json()
                        st.json(error_data)
                    except:
                        st.code(response.text)
                
                else:
                    st.error(f"❌ Query failed: HTTP {response.status_code}")
                    try:
                        error_detail = response.json()
                        st.json(error_detail)
                    except:
                        st.text(response.text)
            
            except httpx.TimeoutException:
                st.error("⏱️ **Query timed out**")
                st.error("Try with fewer documents or a simpler question.")
            except httpx.ConnectError:
                st.error(f"❌ **Cannot connect to service**")
                st.error(f"Service URL: {api_base_url}")
            except Exception as e:
                st.error(f"❌ **Error:** {str(e)}")
    
    elif query_type == "standard" and submitted and not question:
        st.warning("⚠️ Please enter a question")
    
    # Query history
    st.markdown("---")
    st.subheader("📜 Recent Queries")
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if st.session_state.query_history:
        # Show last 5 queries
        recent_queries = list(reversed(st.session_state.query_history[-5:]))
        
        for idx, hist in enumerate(recent_queries, 1):
            with st.expander(f"**{idx}.** {hist['question'][:60]}..." if len(hist['question']) > 60 else f"**{idx}.** {hist['question']}"):
                st.write(f"**Mode:** {hist['mode'].upper()}")
                st.write(f"**Tier:** {hist['tier'].upper()}")
                st.write(f"**Time:** {hist['timestamp']}")
                st.code(hist['question'])
    else:
        st.info("No recent queries yet. Submit a query above to get started!")
    
    # Help section
    st.markdown("---")
    with st.expander("❓ **Help & Tips**"):
        st.markdown("""
        ### Query Modes
        
        **🎯 RAG Mode (Recommended):**
        - Full Retrieval + Augmentation + Generation
        - Searches documents semantically
        - Builds context from multiple sources
        - Synthesizes comprehensive answer
        - Provides source citations and confidence
        - Best for: Technical questions about your codebase
        - Speed: 3-10 seconds
        
        **📄 Contextual Mode:**
        - Simple document context + LLM
        - Retrieves relevant documents
        - Creates basic context
        - Faster LLM generation
        - Best for: Quick lookups with document context
        - Speed: 1-3 seconds
        
        **⚡ Basic Mode:**
        - Pure LLM without documents
        - No document retrieval
        - Direct query to LLM
        - Answer from LLM's knowledge only
        - Best for: General questions, brainstorming
        - Speed: <1 second
        
        ### Tier Selection
        
        **🤖 Auto (Recommended):**
        - Analyzes query complexity
        - Automatically routes to best tier
        - Guaranteed to work (falls back if needed)
        
        **🥇 Tier 1: Cursor IDE:**
        - Highest quality (Claude 4.5 Sonnet)
        - Best for extreme complexity
        - Requires Cursor IDE running on port 3000
        - Falls back to Desktop → Docker if unavailable
        
        **🥈 Tier 2: Desktop Ollama:**
        - GPU acceleration
        - Good performance
        - Requires desktop Ollama on port 11435
        - Falls back to Docker if unavailable
        
        **🥉 Tier 3: Docker Ollama:**
        - Always available
        - CPU-based
        - Good for simple queries
        - No fallback needed (base tier)
        
        ### Settings
        
        **Documents (n_results):**
        - How many documents to retrieve
        - More = more comprehensive but slower
        - Recommended: 10 for most queries
        
        **Temperature:**
        - Controls LLM creativity
        - 0.0 = Focused, deterministic
        - 0.7 = Balanced (recommended)
        - 1.0 = Creative, varied
        
        **Max Retries:**
        - How many times to retry if tier unavailable
        - Recommended: 2 retries
        
        ### Tips
        
        1. **Use Auto tier** for best results
        2. **RAG mode** for technical questions
        3. **Basic mode** for quick general questions
        4. **Lower temperature** (0.3-0.5) for technical accuracy
        5. **Higher temperature** (0.7-0.9) for creative responses
        6. **More documents** = more comprehensive answers
        """)
