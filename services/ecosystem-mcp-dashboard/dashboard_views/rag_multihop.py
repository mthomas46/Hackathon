"""
Multi-Hop RAG Query Interface - Complex reasoning with visualization.

Provides multi-hop reasoning for complex questions with visual reasoning chain.
"""

import streamlit as st
import httpx
import json
from datetime import datetime
import sys
import os

# Import state manager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.state_manager import StateManager


def show(api_base_url: str):
    """Show multi-hop RAG query page."""
    # Initialize state manager
    StateManager.initialize()
    
    st.title("🔗 Multi-Hop RAG Query")
    
    st.markdown("""
    **Complex reasoning through iterative analysis** - Break down complex questions into sub-questions!
    
    **How it works:**
    1. 🎯 Decompose your question into 2-3 sub-questions
    2. 📚 Answer each sub-question independently
    3. 🔄 Synthesize a comprehensive final answer
    
    **Best for:**
    - Cause-and-effect questions ("How did X affect Y?")
    - Relationship questions ("What's the connection between A and B?")
    - Evolution questions ("How did Z change over time?")
    - Complex multi-part questions
    """)
    
    # Example queries
    with st.expander("💡 Example Queries", expanded=False):
        st.markdown("""
        **Good multi-hop questions:**
        - "How did the authentication refactor affect API performance and what were the main trade-offs?"
        - "What is the relationship between caching and response times across different services?"
        - "Trace the evolution of the ingestion pipeline from initial design to current implementation"
        - "How do Docker containers interact with the database and what are the security implications?"
        
        **Not ideal for:**
        - Simple factual questions ("What is Docker?")
        - Single-concept queries ("How does caching work?")
        """)
    
    st.markdown("---")
    
    # Query form
    st.subheader("🔍 Ask Complex Question")
    
    with st.form("multihop_query_form"):
        question = st.text_area(
            "Complex Question",
            height=120,
            placeholder="How did the authentication refactor affect API performance and what were the main trade-offs?",
            help="Ask a question that requires connecting information from multiple sources"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            max_hops = st.slider(
                "🔗 Max Hops",
                min_value=1,
                max_value=5,
                value=3,
                help="Maximum number of sub-questions (reasoning steps)"
            )
        
        with col2:
            n_results_per_hop = st.slider(
                "📚 Sources/Hop",
                min_value=3,
                max_value=10,
                value=5,
                help="Documents to retrieve per sub-question"
            )
        
        with col3:
            show_sources = st.checkbox(
                "📄 Show Sources",
                value=False,
                help="Display source documents for each hop"
            )
        
        submitted = st.form_submit_button("🚀 Analyze", type="primary", use_container_width=True)
    
    # Process multi-hop query
    if submitted and question:
        if 'multihop_history' not in st.session_state:
            st.session_state.multihop_history = []
        
        # Add to history
        st.session_state.multihop_history.append({
            'question': question,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'max_hops': max_hops
        })
        
        st.markdown("---")
        
        with st.spinner(f"🔗 Performing {max_hops}-hop reasoning..."):
            try:
                # Make multi-hop request
                response = httpx.post(
                    f"{api_base_url}/api/v1/multi-hop",
                    json={
                        "question": question,
                        "max_hops": max_hops,
                        "n_results_per_hop": n_results_per_hop
                    },
                    timeout=180.0  # 3 minutes for complex analysis
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Overall metrics
                    st.success("✅ Multi-hop analysis complete!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Hops", result["metadata"]["hops"])
                    with col2:
                        st.metric("Total Sources", result["metadata"]["total_sources"])
                    with col3:
                        st.metric("Confidence", f"{result['confidence']:.2%}")
                    with col4:
                        unique_files = len(set(s.get('file_path') for s in result.get('sources', [])))
                        st.metric("Unique Files", unique_files)
                    
                    # Reasoning chain visualization
                    st.markdown("---")
                    st.subheader("🔍 Reasoning Chain")
                    
                    # Create visual flow
                    flow_diagram = "**Question Flow:**\n\n"
                    flow_diagram += f"**Original:** {question}\n\n"
                    flow_diagram += "↓\n\n"
                    
                    for i, step in enumerate(result["reasoning_chain"], 1):
                        flow_diagram += f"**Hop {i}:** {step['question']}\n"
                        if i < len(result["reasoning_chain"]):
                            flow_diagram += "↓\n"
                    
                    flow_diagram += "\n↓\n\n**Final Answer**"
                    
                    with st.expander("📊 Question Decomposition Flow", expanded=True):
                        st.markdown(flow_diagram)
                    
                    # Detailed reasoning steps
                    st.markdown("### 🔗 Detailed Reasoning Steps")
                    
                    for step in result["reasoning_chain"]:
                        hop_num = step["hop"]
                        
                        # Create expandable section for each hop
                        with st.expander(
                            f"**Hop {hop_num}:** {step['question']}", 
                            expanded=(hop_num == 1)  # Expand first hop by default
                        ):
                            # Confidence indicator
                            confidence = step["confidence"]
                            if confidence >= 0.8:
                                conf_icon = "🟢"
                                conf_label = "High"
                            elif confidence >= 0.6:
                                conf_icon = "🟡"
                                conf_label = "Medium"
                            else:
                                conf_icon = "🔴"
                                conf_label = "Low"
                            
                            st.markdown(f"{conf_icon} **Confidence:** {conf_label} ({confidence:.2%})")
                            
                            # Answer
                            st.markdown("**Answer:**")
                            st.info(step["answer"])
                            
                            # Sources count
                            st.caption(f"📚 Based on {step['n_sources']} sources")
                            
                            # Show sources if requested
                            if show_sources and "sources" in result:
                                # Filter sources used in this hop (rough heuristic)
                                hop_sources = result["sources"][:step['n_sources']]
                                
                                with st.expander(f"📄 View {len(hop_sources)} sources", expanded=False):
                                    for i, source in enumerate(hop_sources, 1):
                                        st.markdown(f"**{i}.** `{source.get('file_path', 'Unknown')}`")
                                        st.caption(f"Relevance: {source.get('relevance_score', 0):.2%}")
                    
                    # Final synthesized answer
                    st.markdown("---")
                    st.subheader("📝 Final Synthesized Answer")
                    st.markdown(result["answer"])
                    
                    # All unique sources
                    st.markdown("---")
                    st.subheader(f"📚 All Sources ({len(result['sources'])})")
                    
                    # Group by file
                    file_groups = {}
                    for source in result["sources"]:
                        file_path = source.get('file_path', 'Unknown')
                        if file_path not in file_groups:
                            file_groups[file_path] = []
                        file_groups[file_path].append(source)
                    
                    # Display grouped sources
                    for file_path, sources_list in file_groups.items():
                        with st.expander(f"📄 {file_path} ({len(sources_list)} references)", expanded=False):
                            for source in sources_list:
                                st.write(f"**ID:** {source.get('id', 'N/A')}")
                                st.write(f"**Relevance:** {source.get('relevance_score', 0):.2%}")
                                if 'content_snippet' in source:
                                    st.code(source['content_snippet'][:300], language=None)
                                st.markdown("---")
                    
                    # Download reasoning chain
                    reasoning_json = json.dumps(result, indent=2)
                    st.download_button(
                        label="💾 Download Full Reasoning Chain (JSON)",
                        data=reasoning_json,
                        file_name=f"multihop_reasoning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
                
                else:
                    st.error(f"❌ Request failed: {response.status_code}")
                    st.code(response.text)
            
            except httpx.TimeoutException:
                st.error("❌ Request timed out after 3 minutes. Try reducing max_hops or n_results_per_hop.")
            except httpx.RequestError as e:
                st.error(f"❌ Request error: {e}")
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
                st.exception(e)
    
    elif submitted and not question:
        st.error("❌ Please enter a complex question")
    
    # Query history
    if 'multihop_history' in st.session_state and st.session_state.multihop_history:
        st.markdown("---")
        st.subheader("📜 Analysis History")
        
        for i, item in enumerate(reversed(st.session_state.multihop_history[-5:]), 1):
            with st.expander(f"{item['timestamp']} - {item['question'][:60]}...", expanded=False):
                st.write(f"**Question:** {item['question']}")
                st.write(f"**Max Hops:** {item['max_hops']}")
                
                if st.button(f"🔄 Re-run", key=f"rerun_{i}"):
                    st.session_state['rerun_question'] = item['question']
                    st.session_state['rerun_hops'] = item['max_hops']
                    st.rerun()


if __name__ == "__main__":
    # For testing
    show("http://localhost:8000")

