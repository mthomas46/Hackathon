"""RAG Query interface page."""

import streamlit as st
import httpx
import json
from datetime import datetime

def show(api_base_url: str):
    """Show RAG query page."""
    st.title("🤖 RAG Query Interface")
    
    st.markdown("""
    Ask questions about your ingested documents using the RAG (Retrieval Augmented Generation) system.
    The system will search relevant documents and generate intelligent answers using LLM.
    """)
    
    # Query form
    with st.form("rag_query_form"):
        question = st.text_area(
            "❓ Your Question",
            placeholder="e.g., How does the caching system work?",
            height=100,
            help="Ask any question about the ingested documents"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            n_results = st.slider("Documents to retrieve", 1, 25, 10)
        
        with col2:
            temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1,
                                   help="0 = deterministic, 1 = creative")
        
        with col3:
            use_cache = st.checkbox("Use cache", value=True,
                                   help="Use cached results if available")
        
        submitted = st.form_submit_button("🚀 Ask Question", use_container_width=True)
    
    if submitted and question:
        with st.spinner("🧠 Thinking..."):
            try:
                # Make RAG query
                response = httpx.post(
                    f"{api_base_url}/api/v1/ask",
                    json={
                        "question": question,
                        "n_results": n_results,
                        "temperature": temperature
                    },
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Show answer
                    st.markdown("---")
                    st.subheader("💡 Answer")
                    st.success(data.get("answer", "No answer generated"))
                    
                    # Show metadata
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Response Time", f"{data.get('response_time_seconds', 0):.2f}s")
                    
                    with col2:
                        st.metric("Sources", len(data.get("sources", [])))
                    
                    with col3:
                        model = data.get("model_used", "unknown")
                        st.metric("Model", model.split(':')[0] if ':' in model else model)
                    
                    with col4:
                        cache_status = "🎯 Cache Hit" if data.get("cache_hit") else "💾 Fresh Query"
                        st.metric("Cache", cache_status)
                    
                    # Show sources
                    st.markdown("---")
                    st.subheader("📚 Sources")
                    
                    sources = data.get("sources", [])
                    if sources:
                        for idx, source in enumerate(sources, 1):
                            with st.expander(f"Source {idx}: {source.get('file_path', 'Unknown')[:60]}..."):
                                col_a, col_b = st.columns([3, 1])
                                
                                with col_a:
                                    st.markdown(f"**File:** `{source.get('file_path', 'N/A')}`")
                                    st.markdown(f"**Type:** {source.get('file_type', 'N/A')}")
                                    if source.get('git_commit'):
                                        st.markdown(f"**Commit:** `{source.get('git_commit')[:8]}`")
                                
                                with col_b:
                                    score = source.get('relevance_score', source.get('score', 0))
                                    st.metric("Relevance", f"{score:.3f}")
                                
                                # Show content snippet
                                content = source.get('content', 'No content available')
                                st.text_area(
                                    "Content",
                                    value=content[:500] + "..." if len(content) > 500 else content,
                                    height=150,
                                    disabled=True
                                )
                    else:
                        st.info("No sources found")
                    
                    # Show full response
                    with st.expander("🔍 Full Response Details"):
                        st.json(data)
                
                elif response.status_code == 422:
                    st.error("❌ Validation Error")
                    st.error("Your query may be too long or contain invalid parameters.")
                    st.code(response.text)
                
                else:
                    st.error(f"Query failed: {response.status_code}")
                    st.code(response.text)
            
            except httpx.TimeoutException:
                st.error("⏱️ Query timed out. Try with fewer documents or a simpler question.")
            except httpx.ConnectError:
                st.error(f"❌ Cannot connect to service at {api_base_url}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    elif submitted:
        st.warning("Please enter a question")
    
    # Query history (placeholder)
    st.markdown("---")
    st.subheader("📜 Recent Queries")
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if st.session_state.query_history:
        for idx, hist in enumerate(reversed(st.session_state.query_history[-5:])):
            st.text(f"{idx+1}. {hist['question'][:80]}... ({hist['timestamp']})")
    else:
        st.info("No recent queries")

