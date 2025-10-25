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
    
    # Use session state to ensure unique form key
    if 'multi_pass_form_counter' not in st.session_state:
        st.session_state.multi_pass_form_counter = 0
    
    with st.form(f"rag_multi_pass_form_{st.session_state.multi_pass_form_counter}"):
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
        
        # Additional settings row
        col3, col4 = st.columns(2)
        
        with col3:
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
        
        with col4:
            response_length = st.selectbox(
                "📏 Response Length",
                options=["S", "M", "L", "XL"],
                index=2,  # Default to Large for multi-pass
                format_func=lambda x: {
                    "S": "S (~500 chars)",
                    "M": "M (~1K chars)",
                    "L": "L (~2K chars)",
                    "XL": "XL (~4K chars)"
                }[x],
                help="Control response verbosity per answer"
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
                
                # Convert response length to max_tokens
                length_to_tokens = {
                    "S": 150,    # ~500 chars
                    "M": 300,    # ~1K chars
                    "L": 600,    # ~2K chars
                    "XL": 1200   # ~4K chars
                }
                max_tokens = length_to_tokens.get(response_length, 600)
                
                # Make request to multi-pass endpoint
                response = httpx.post(
                    f"{api_base_url}/api/v1/query/multi-pass",
                    json={
                        "query": query,
                        "num_sections": num_passes,
                        "questions_per_section": num_secondary_questions,
                        "n_results": n_results,
                        "temperature": temperature,
                        "response_length": max_tokens,
                        "use_enhancements": True  # Enable enhancements by default
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
                        st.metric("Sections", result.get("num_passes", num_passes))
                    
                    with metric_col2:
                        st.metric("Questions", result.get("total_questions_asked", 0))
                    
                    with metric_col3:
                        st.metric("Duration", f"{elapsed_time:.1f}s")
                    
                    with metric_col4:
                        st.metric("Total Sources", result.get("total_sources_used", 0))
                    
                    # Enhancement indicators
                    metadata = result.get("metadata", {})
                    enhancements = metadata.get("enhancements_applied", [])
                    matched_templates = metadata.get("matched_templates", [])
                    total_docs = metadata.get("total_documents_used", 0)
                    
                    if enhancements or matched_templates:
                        st.success("✨ **Enhancements Active!**")
                        
                        enh_col1, enh_col2, enh_col3 = st.columns(3)
                        
                        with enh_col1:
                            if enhancements:
                                st.markdown("**🎯 Enhancements Applied:**")
                                for enhancement in enhancements:
                                    st.markdown(f"- ✅ {enhancement}")
                        
                        with enh_col2:
                            if matched_templates:
                                st.markdown("**📋 Templates Matched:**")
                                for template in matched_templates:
                                    st.markdown(f"- ✅ {template}")
                        
                        with enh_col3:
                            if total_docs > 0:
                                st.metric("Documents Retrieved", total_docs)
                                st.caption("Across all sub-queries")
                    
                    # Answer
                    st.markdown("---")
                    st.markdown("### 📝 Comprehensive Answer")
                    st.markdown(result.get("final_synthesis", result.get("answer", "No answer generated")))
                    
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

