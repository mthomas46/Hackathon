"""
Multi-Pass RAG Query Interface Page.

Provides deep analysis through query decomposition and secondary questions.
"""

import streamlit as st
import httpx
import json
import os
from datetime import datetime


def show(api_base_url: str):
    """Show multi-pass RAG query page."""
    st.title("🔬 Multi-Pass RAG Query Interface")
    
    st.markdown("""
    **Deep Analysis Mode** - Decompose complex queries into sections with secondary questions 
    for comprehensive, multi-perspective answers.
    
    Perfect for:
    • Complex technical questions requiring deep analysis
    • Research queries needing multiple perspectives
    • Comprehensive system understanding
    • Documentation generation
    """)
    
    # Tier status
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
                status = "✅" if cursor_tier.get("available") else "❌"
                st.metric("Tier 1: Cursor", status)
                st.caption(cursor_tier.get('model', 'Claude 4.5 Sonnet'))
            
            with col2:
                desktop_tier = tiers.get("desktop", {})
                status = "✅" if desktop_tier.get("available") else "⚠️"
                st.metric("Tier 2: Desktop", status)
                st.caption(desktop_tier.get('model', 'llama3 (GPU)'))
            
            with col3:
                docker_tier = tiers.get("docker", {})
                status = "✅" if docker_tier.get("available") else "❌"
                st.metric("Tier 3: Docker", status)
                st.caption(docker_tier.get('model', 'llama3.2:3b'))
    
    except Exception as e:
        st.warning(f"Could not fetch tier status: {e}")
    
    # Multi-pass query form
    st.markdown("---")
    st.subheader("🔬 Configure Multi-Pass Analysis")
    
    with st.form("multi_pass_form"):
        # Query input
        query = st.text_area(
            "📝 Your Complex Query",
            height=120,
            placeholder="e.g., How does the caching system work, what are the implementation details, and what are the best practices?",
            help="Enter a complex question that benefits from multi-perspective analysis"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            num_passes = st.slider(
                "🎯 Number of Sections (Passes)",
                min_value=1,
                max_value=10,
                value=3,
                help="How many major concepts/sections to decompose the query into"
            )
            
            n_results = st.slider(
                "📚 Documents per Question",
                min_value=1,
                max_value=50,
                value=10,
                help="Number of documents to retrieve for each sub-question"
            )
        
        with col2:
            num_secondary_questions = st.slider(
                "❓ Questions per Section",
                min_value=1,
                max_value=10,
                value=3,
                help="Number of secondary questions to generate for each section"
            )
            
            temperature = st.slider(
                "🌡️ Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="LLM creativity: 0 = focused, 1 = creative"
            )
        
        # Tier selection
        tier = st.selectbox(
            "🔌 LLM Tier Preference",
            options=["auto", "cursor", "desktop", "docker"],
            index=0,
            format_func=lambda x: {
                "auto": "🤖 Auto (Recommended)",
                "cursor": "🥇 Tier 1: Cursor IDE",
                "desktop": "🥈 Tier 2: Desktop Ollama",
                "docker": "🥉 Tier 3: Docker Ollama"
            }[x],
            help="Select preferred LLM tier (auto-fallback enabled)"
        )
        
        # Calculate total questions
        total_questions = num_passes * num_secondary_questions
        estimated_time = total_questions * 2.5  # ~2.5s per question
        
        st.info(f"""
        **Analysis Configuration:**
        - Sections: {num_passes}
        - Questions per section: {num_secondary_questions}
        - **Total questions:** {total_questions}
        - **Estimated time:** ~{int(estimated_time)} seconds ({estimated_time/60:.1f} minutes)
        """)
        
        submitted = st.form_submit_button("🚀 Start Multi-Pass Analysis", use_container_width=True)
    
    # Process multi-pass query
    if submitted and query:
        # Initialize progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with st.spinner("🔬 Performing multi-pass analysis..."):
            try:
                start_time = datetime.now()
                
                status_text.text("📡 Sending request to API...")
                progress_bar.progress(5)
                
                # Make request using enhanced endpoint (single-pass RAG for now)
                # TODO: Switch to multi-pass endpoint when ready
                response = httpx.post(
                    f"{api_base_url}/api/v1/query/enhanced",
                    json={
                        "question": query,
                        "mode": "rag",
                        "tier": tier,
                        "n_results": n_results,
                        "temperature": temperature,
                        "max_retries": 2
                    },
                    timeout=900.0
                )
                
                progress_bar.progress(90)
                status_text.text("📊 Processing results...")
                
                elapsed_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    result = response.json()
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Analysis complete!")
                    
                    # Display results
                    st.markdown("---")
                    st.subheader("💡 Multi-Pass Analysis Results")
                    
                    # Metrics
                    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                    
                    with metric_col1:
                        st.metric("Mode", result.get("mode", "").upper())
                    
                    with metric_col2:
                        st.metric("Tier Used", result.get("tier_used", "").upper())
                    
                    with metric_col3:
                        st.metric("Duration", f"{elapsed_time:.1f}s")
                    
                    with metric_col4:
                        st.metric("Sources", len(result.get("sources", [])))
                    
                    # Tier fallback warning
                    if result.get("tier_used") != result.get("tier_requested"):
                        st.warning(f"⚠️ Tier fallback: {result.get('tier_requested', '').upper()} → {result.get('tier_used', '').upper()}")
                    
                    # Answer
                    st.markdown("### 📝 Comprehensive Answer")
                    st.markdown(result.get("answer", "No answer generated"))
                    
                    # Sources
                    sources = result.get("sources", [])
                    if sources:
                        st.markdown("---")
                        st.subheader(f"📚 Sources ({len(sources)})")
                        
                        for i, source in enumerate(sources, 1):
                            source_title = source.get('file_path', source.get('id', f'Source {i}'))
                            
                            with st.expander(f"**Source {i}:** {source_title[:80]}"):
                                source_col1, source_col2 = st.columns([3, 1])
                                
                                with source_col1:
                                    if "file_path" in source:
                                        st.markdown(f"**File:** `{source['file_path']}`")
                                    if "service" in source:
                                        st.markdown(f"**Service:** {source['service']}")
                                
                                with source_col2:
                                    if "score" in source:
                                        st.metric("Relevance", f"{source['score']:.2%}")
                                
                                if "content" in source:
                                    content = source["content"]
                                    preview = content[:500] + "..." if len(content) > 500 else content
                                    st.text_area(
                                        "Content",
                                        value=preview,
                                        height=150,
                                        disabled=True,
                                        key=f"mp_source_{i}"
                                    )
                    
                    # Metadata
                    metadata = result.get("metadata", {})
                    if metadata:
                        with st.expander("🔍 Analysis Metadata"):
                            st.json(metadata)
                    
                    # Download results
                    result_json = json.dumps(result, indent=2)
                    st.download_button(
                        label="💾 Download Results (JSON)",
                        data=result_json,
                        file_name=f"multi_pass_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                else:
                    st.error(f"❌ Analysis failed: HTTP {response.status_code}")
                    try:
                        error_detail = response.json()
                        st.json(error_detail)
                    except:
                        st.text(response.text)
            
            except httpx.TimeoutException:
                st.error("⏱️ Analysis timed out. Try reducing the number of passes or questions per section.")
            except httpx.ConnectError:
                st.error(f"❌ Cannot connect to API at {api_base_url}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    elif submitted:
        st.warning("⚠️ Please enter a query")
    
    # Help section
    st.markdown("---")
    with st.expander("❓ **How Multi-Pass Analysis Works**"):
        st.markdown("""
        ### Multi-Pass Workflow
        
        1. **Query Decomposition**
           - Your query is analyzed and broken into N major concepts/sections
           - Example: "How does caching work?" → Core Concepts, Implementation, Best Practices
        
        2. **Secondary Question Generation**
           - For each section, M specific questions are generated
           - Example: Section "Implementation" → "How is Redis configured?", "What strategies are used?"
        
        3. **RAG Execution**
           - Full RAG (Retrieval + Augmentation + Generation) for each question
           - Each question gets relevant documents and synthesized answer
        
        4. **Section Synthesis**
           - All Q&A for a section are integrated into a comprehensive section answer
        
        5. **Final Synthesis**
           - All section answers are combined into one authoritative, integrated response
        
        ### Configuration Guidelines
        
        **Quick Analysis (15-30s):**
        - Passes: 2
        - Questions: 2
        - Total: 4 questions
        
        **Standard Analysis (30-60s):**
        - Passes: 3
        - Questions: 3
        - Total: 9 questions
        
        **Deep Analysis (60-180s):**
        - Passes: 5
        - Questions: 4
        - Total: 20 questions
        
        **Comprehensive Research (3-5min):**
        - Passes: 8
        - Questions: 5
        - Total: 40 questions
        
        ### Tips
        
        - Use **Auto tier** for best results
        - Increase **passes** for broader coverage
        - Increase **questions per section** for more depth
        - **Lower temperature** (0.3-0.5) for technical accuracy
        - **Higher temperature** (0.7-0.9) for creative exploration
        """)


if __name__ == "__main__":
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    show(api_base_url)
else:
    show(os.getenv("API_BASE_URL", "http://localhost:8000"))

