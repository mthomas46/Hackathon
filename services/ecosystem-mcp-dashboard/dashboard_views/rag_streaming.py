"""
Streaming RAG Query Interface - Real-time token streaming.

Provides real-time streaming of LLM responses for better UX.
"""

import streamlit as st
import httpx
import json
import time
from datetime import datetime
import sys
import os

# Import state manager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.state_manager import StateManager


def show(api_base_url: str):
    """Show streaming RAG query page."""
    # Initialize state manager
    StateManager.initialize()
    
    st.title("🌊 Streaming RAG Query")
    
    st.markdown("""
    **Real-time streaming responses** - See your answer being generated token-by-token!
    
    **Benefits:**
    - ⚡ Perceived latency reduced by 80-90%
    - 👀 Watch answer build in real-time
    - 📊 Progress updates during retrieval
    - ✨ Better UX for long answers
    """)
    
    # Feature comparison
    with st.expander("📊 Streaming vs Standard Comparison", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Standard Mode**")
            st.write("• Wait 10-15s")
            st.write("• No feedback")
            st.write("• Full answer appears at once")
            st.write("• Can feel slow")
        
        with col2:
            st.markdown("**Streaming Mode** ✨")
            st.write("• First token in ~1-2s")
            st.write("• Real-time progress")
            st.write("• Tokens stream continuously")
            st.write("• Feels much faster")
    
    st.markdown("---")
    
    # Query form
    st.subheader("🔍 Ask Your Question")
    
    with st.form("streaming_query_form"):
        question = st.text_area(
            "Question",
            height=100,
            placeholder="What is the MCP protocol and how does it work?",
            help="Your question will be answered with real-time streaming"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            n_results = st.slider(
                "📚 Sources",
                min_value=3,
                max_value=20,
                value=10,
                help="Number of documents to retrieve"
            )
        
        with col2:
            temperature = st.slider(
                "🌡️ Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="Higher = more creative, Lower = more focused"
            )
        
        with col3:
            use_enhancements = st.checkbox(
                "✨ Use Enhancements",
                value=True,
                help="Enable hybrid search, query rewriting, etc."
            )
        
        submitted = st.form_submit_button("🚀 Ask (Streaming)", type="primary", use_container_width=True)
    
    # Process streaming query
    if submitted and question:
        if 'streaming_history' not in st.session_state:
            st.session_state.streaming_history = []
        
        # Add to history
        st.session_state.streaming_history.append({
            'question': question,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'n_results': n_results,
            'temperature': temperature,
            'use_enhancements': use_enhancements
        })
        
        st.markdown("---")
        st.subheader("📝 Answer (Streaming)")
        
        # Create placeholders
        progress_placeholder = st.empty()
        answer_placeholder = st.empty()
        metadata_placeholder = st.empty()
        sources_placeholder = st.empty()
        
        start_time = time.time()
        answer_text = ""
        first_token_time = None
        token_count = 0
        sources = []
        
        try:
            # Make streaming request
            with httpx.stream(
                "POST",
                f"{api_base_url}/api/v1/ask/stream",
                json={
                    "question": question,
                    "n_results": n_results,
                    "use_enhancements": use_enhancements,
                    "temperature": temperature
                },
                timeout=120.0
            ) as response:
                
                if response.status_code != 200:
                    st.error(f"❌ Request failed: {response.status_code}")
                    st.code(response.text)
                    return
                
                # Process SSE stream
                for line in response.iter_lines():
                    if not line:
                        continue
                    
                    # Parse SSE format
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        
                        try:
                            data = json.loads(data_str)
                            event_type = data.get("type")
                            
                            # Progress updates
                            if event_type == "progress":
                                message = data.get("message", "")
                                progress_placeholder.info(f"🔄 {message}")
                            
                            # Token streaming
                            elif event_type == "token":
                                if first_token_time is None:
                                    first_token_time = time.time()
                                    elapsed = first_token_time - start_time
                                    progress_placeholder.success(f"✅ First token in {elapsed:.2f}s")
                                
                                token = data.get("content", "")
                                answer_text += token
                                token_count += 1
                                
                                # Update answer (with markdown formatting)
                                answer_placeholder.markdown(answer_text + "▊")  # Cursor effect
                            
                            # Completion
                            elif event_type == "done":
                                end_time = time.time()
                                total_time = end_time - start_time
                                first_token_latency = first_token_time - start_time if first_token_time else 0
                                
                                # Remove cursor
                                answer_placeholder.markdown(answer_text)
                                
                                # Clear progress
                                progress_placeholder.empty()
                                
                                # Show metadata
                                sources = data.get("sources", [])
                                confidence = data.get("confidence", 0.0)
                                metadata = data.get("metadata", {})
                                
                                with metadata_placeholder.container():
                                    st.success(f"✅ Complete in {total_time:.2f}s!")
                                    
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1:
                                        st.metric("First Token", f"{first_token_latency:.2f}s")
                                    with col2:
                                        st.metric("Total Time", f"{total_time:.2f}s")
                                    with col3:
                                        st.metric("Tokens", token_count)
                                    with col4:
                                        st.metric("Confidence", f"{confidence:.2%}")
                                
                                # Show sources
                                with sources_placeholder.container():
                                    st.markdown(f"### 📚 Sources ({len(sources)})")
                                    
                                    for i, source in enumerate(sources, 1):
                                        with st.expander(f"📄 {i}. {source.get('file_path', 'Unknown')}", expanded=False):
                                            st.write(f"**Relevance:** {source.get('relevance_score', 0):.2%}")
                                            if 'content_snippet' in source:
                                                st.code(source['content_snippet'][:500], language=None)
                                
                                break
                            
                            # Error
                            elif event_type == "error":
                                error_msg = data.get("message", "Unknown error")
                                progress_placeholder.error(f"❌ Error: {error_msg}")
                                break
                        
                        except json.JSONDecodeError:
                            st.warning(f"⚠️ Could not parse: {data_str}")
                            continue
        
        except httpx.TimeoutException:
            st.error("❌ Request timed out after 120 seconds")
        except httpx.RequestError as e:
            st.error(f"❌ Request error: {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            st.exception(e)
    
    elif submitted and not question:
        st.error("❌ Please enter a question")
    
    # Query history
    if 'streaming_history' in st.session_state and st.session_state.streaming_history:
        st.markdown("---")
        st.subheader("📜 Query History")
        
        for i, item in enumerate(reversed(st.session_state.streaming_history[-5:]), 1):
            with st.expander(f"{item['timestamp']} - {item['question'][:50]}...", expanded=False):
                st.write(f"**Question:** {item['question']}")
                st.write(f"**Sources:** {item['n_results']}")
                st.write(f"**Temperature:** {item['temperature']}")
                st.write(f"**Enhancements:** {'✅ Yes' if item['use_enhancements'] else '❌ No'}")


if __name__ == "__main__":
    # For testing
    show("http://localhost:8000")

