"""
Enhanced Query Interface - Multiple Modes & Tier Selection.

Provides users with:
1. Three query modes (RAG, Contextual, Basic)
2. Manual tier selection
3. Real-time tier availability status
"""

import streamlit as st
import httpx
import os
from datetime import datetime

def show(api_base_url: str = None):
    """Display enhanced query interface."""
    # Use provided URL or fall back to environment variable
    if api_base_url is None:
        api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    st.title("🎯 Enhanced Query Interface")
    st.markdown("""
    Advanced querying with **multiple modes** and **manual tier selection**.
    
    Choose your query mode and LLM tier for optimal performance!
    """)
    
    # Fetch tier status
    st.markdown("---")
    st.subheader("🔌 LLM Tier Status")
    
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
                st.write(f"**Model:** {cursor_tier.get('model', 'Unknown')}")
                st.caption(cursor_tier.get('use_case', ''))
            
            with col2:
                desktop_tier = tiers.get("desktop", {})
                if desktop_tier.get("available"):
                    st.success("✅ **Tier 2: Desktop Ollama**")
                else:
                    st.warning("⚠️ **Tier 2: Desktop Ollama**")
                st.write(f"**Model:** {desktop_tier.get('model', 'Unknown')}")
                st.caption(desktop_tier.get('use_case', ''))
            
            with col3:
                docker_tier = tiers.get("docker", {})
                if docker_tier.get("available"):
                    st.success("✅ **Tier 3: Docker Ollama**")
                else:
                    st.error("❌ **Tier 3: Docker Ollama**")
                st.write(f"**Model:** {docker_tier.get('model', 'Unknown')}")
                st.caption(docker_tier.get('use_case', ''))
            
            recommendation = tier_data.get("recommendation", "auto")
            st.info(f"💡 **Recommended tier:** `{recommendation.upper()}`")
        else:
            st.warning("Could not fetch tier status")
    
    except Exception as e:
        st.warning(f"Tier status unavailable: {str(e)}")
    
    # Fetch mode information
    st.markdown("---")
    st.subheader("📋 Query Modes")
    
    try:
        modes_response = httpx.get(f"{api_base_url}/api/v1/query/modes", timeout=5.0)
        
        if modes_response.status_code == 200:
            modes_data = modes_response.json()
            modes = modes_data.get("modes", {})
            
            mode_col1, mode_col2, mode_col3 = st.columns(3)
            
            with mode_col1:
                rag_mode = modes.get("rag", {})
                with st.expander("🎯 **RAG Mode** (Full)", expanded=False):
                    st.write(f"**{rag_mode.get('description', '')}**")
                    st.write(f"⚡ Speed: {rag_mode.get('speed', '')}")
                    st.write(f"⭐ Quality: {rag_mode.get('quality', '')}")
                    st.write(f"✅ Best for: {rag_mode.get('best_for', '')}")
                    st.write("**Features:**")
                    for feature in rag_mode.get("features", []):
                        st.write(f"- {feature}")
            
            with mode_col2:
                contextual_mode = modes.get("contextual", {})
                with st.expander("📄 **Contextual Mode**", expanded=False):
                    st.write(f"**{contextual_mode.get('description', '')}**")
                    st.write(f"⚡ Speed: {contextual_mode.get('speed', '')}")
                    st.write(f"⭐ Quality: {contextual_mode.get('quality', '')}")
                    st.write(f"✅ Best for: {contextual_mode.get('best_for', '')}")
                    st.write("**Features:**")
                    for feature in contextual_mode.get("features", []):
                        st.write(f"- {feature}")
            
            with mode_col3:
                basic_mode = modes.get("basic", {})
                with st.expander("⚡ **Basic Mode** (LLM Only)", expanded=False):
                    st.write(f"**{basic_mode.get('description', '')}**")
                    st.write(f"⚡ Speed: {basic_mode.get('speed', '')}")
                    st.write(f"⭐ Quality: {basic_mode.get('quality', '')}")
                    st.write(f"✅ Best for: {basic_mode.get('best_for', '')}")
                    st.write("**Features:**")
                    for feature in basic_mode.get("features", []):
                        st.write(f"- {feature}")
    
    except Exception as e:
        st.warning(f"Mode information unavailable: {str(e)}")
    
    # Query interface
    st.markdown("---")
    st.subheader("🔍 Submit Query")
    
    # Create form
    with st.form("enhanced_query_form"):
        # Question input
        question = st.text_area(
            "Your Question",
            height=100,
            placeholder="Ask anything...",
            help="Enter your question here"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Mode selection
            mode = st.selectbox(
                "Query Mode",
                options=["rag", "contextual", "basic"],
                index=0,
                format_func=lambda x: {
                    "rag": "🎯 RAG (Full)",
                    "contextual": "📄 Contextual",
                    "basic": "⚡ Basic (LLM Only)"
                }[x],
                help="Select query processing mode"
            )
            
            # Tier selection
            tier = st.selectbox(
                "LLM Tier",
                options=["auto", "cursor", "desktop", "docker"],
                index=0,
                format_func=lambda x: {
                    "auto": "🤖 Auto (Recommended)",
                    "cursor": "🥇 Tier 1: Cursor IDE",
                    "desktop": "🥈 Tier 2: Desktop Ollama",
                    "docker": "🥉 Tier 3: Docker Ollama"
                }[x],
                help="Select which LLM tier to use (auto recommended)"
            )
        
        with col2:
            # N results (only for rag/contextual)
            if mode in ["rag", "contextual"]:
                n_results = st.slider(
                    "Documents to Retrieve",
                    min_value=1,
                    max_value=50,
                    value=10,
                    help="Number of documents to retrieve"
                )
            else:
                n_results = 10
                st.info("📌 Basic mode doesn't use documents")
            
            # Temperature
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher = more creative, Lower = more focused"
            )
        
        # Advanced settings
        with st.expander("⚙️ Advanced Settings"):
            max_retries = st.slider(
                "Max Retries",
                min_value=0,
                max_value=5,
                value=2,
                help="Max retry attempts if selected tier unavailable"
            )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Submit Query", use_container_width=True)
    
    # Process query
    if submitted and question:
        with st.spinner(f"🧠 Processing ({mode.upper()} mode)..."):
            try:
                start_time = datetime.now()
                
                # Make enhanced query request
                response = httpx.post(
                    f"{api_base_url}/api/v1/query/enhanced",
                    json={
                        "question": question,
                        "mode": mode,
                        "tier": tier,
                        "n_results": n_results,
                        "temperature": temperature,
                        "max_retries": max_retries
                    },
                    timeout=300.0  # 5 minutes
                )
                
                elapsed_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display answer
                    st.markdown("---")
                    st.subheader("💡 Answer")
                    
                    # Tier and mode badges
                    badge_col1, badge_col2, badge_col3, badge_col4 = st.columns(4)
                    with badge_col1:
                        st.metric("Mode", result.get("mode", "").upper())
                    with badge_col2:
                        tier_used = result.get("tier_used", "unknown")
                        st.metric("Tier Used", tier_used.upper())
                    with badge_col3:
                        tier_requested = result.get("tier_requested", "unknown")
                        st.metric("Tier Requested", tier_requested.upper())
                    with badge_col4:
                        st.metric("Time", f"{elapsed_time:.2f}s")
                    
                    # Tier fallback warning
                    if result.get("tier_used") != result.get("tier_requested"):
                        st.warning(f"⚠️ Requested tier `{tier_requested}` was unavailable. Fell back to `{tier_used}`.")
                    
                    # Answer text
                    st.markdown(result.get("answer", "No answer generated"))
                    
                    # Sources (if any)
                    sources = result.get("sources", [])
                    if sources:
                        st.markdown("---")
                        st.subheader(f"📚 Sources ({len(sources)})")
                        
                        for i, source in enumerate(sources, 1):
                            with st.expander(f"Source {i}: {source.get('file_path', source.get('id', 'Unknown'))}"):
                                if "file_path" in source:
                                    st.write(f"**File:** `{source['file_path']}`")
                                if "service" in source:
                                    st.write(f"**Service:** {source['service']}")
                                if "score" in source:
                                    st.write(f"**Relevance:** {source['score']:.2%}")
                                if "content_preview" in source:
                                    st.code(source["content_preview"], language="text")
                    
                    # Metadata
                    metadata = result.get("metadata", {})
                    if metadata:
                        with st.expander("🔍 Query Metadata"):
                            st.json(metadata)
                
                else:
                    st.error(f"❌ Query failed: HTTP {response.status_code}")
                    try:
                        error_detail = response.json()
                        st.json(error_detail)
                    except:
                        st.text(response.text)
            
            except httpx.TimeoutException:
                st.error("⏱️ Query timed out. Try with fewer documents or a simpler question.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    elif submitted:
        st.warning("⚠️ Please enter a question")
    
    # Help section
    st.markdown("---")
    with st.expander("❓ Help & Tips"):
        st.markdown("""
        ### Query Modes
        
        **🎯 RAG (Full):**
        - Retrieves relevant documents
        - Builds context from multiple sources
        - Synthesizes comprehensive answer
        - Provides source citations
        - Best for: Complex questions requiring accurate, cited answers
        - Speed: Slower (3-10s)
        
        **📄 Contextual:**
        - Retrieves documents
        - Simple context creation
        - Basic LLM generation
        - Best for: Quick answers with document context
        - Speed: Medium (1-3s)
        
        **⚡ Basic (LLM Only):**
        - No document retrieval
        - Direct LLM query
        - Answer from LLM's knowledge only
        - Best for: General questions, brainstorming
        - Speed: Fast (<1s)
        
        ### Tier Selection
        
        **🤖 Auto (Recommended):**
        - Analyzes query complexity
        - Automatically selects best tier
        - Guaranteed to work
        
        **🥇 Tier 1: Cursor IDE:**
        - Highest quality (Claude 4.5 Sonnet)
        - Best for extreme complexity
        - Requires Cursor IDE running
        
        **🥈 Tier 2: Desktop Ollama:**
        - GPU acceleration
        - Good performance
        - Requires desktop Ollama running on port 11435
        
        **🥉 Tier 3: Docker Ollama:**
        - Always available
        - CPU-based
        - Good for simple queries
        
        ### Tips
        
        1. **Use Auto tier** for best results
        2. **RAG mode** for technical questions about your codebase
        3. **Basic mode** for quick general questions
        4. **Increase documents** (n_results) for more comprehensive answers
        5. **Lower temperature** (0.3-0.5) for focused answers
        6. **Higher temperature** (0.7-0.9) for creative responses
        """)


if __name__ == "__main__":
    show()
else:
    show()

