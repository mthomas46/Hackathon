"""Query Playground - Test queries against MCPs."""

import streamlit as st
import json


def render():
    """Render the query playground page."""
    
    st.title("🔍 Query Playground")
    st.markdown("Test queries and explore MCP responses")
    
    # Query input section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Query Input")
        
        query = st.text_area(
            "Enter your query:",
            placeholder="Ask anything about your knowledge base...",
            height=150
        )
        
        # Pattern selection
        pattern = st.selectbox(
            "LLM Pattern",
            ["RAG", "Chain-of-Thought", "ReAct", "Tree-of-Thoughts", "Self-Reflection", "Multi-Agent"]
        )
        
        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            col_a, col_b = st.columns(2)
            with col_a:
                temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
                max_tokens = st.number_input("Max Tokens", 100, 4000, 2000, 100)
            with col_b:
                top_k = st.number_input("Top-K Results", 1, 20, 5)
                include_sources = st.checkbox("Include Sources", value=True)
        
        if st.button("🚀 Execute Query", use_container_width=True):
            with st.spinner("Executing query..."):
                st.session_state['query_result'] = execute_mock_query(query, pattern)
    
    with col2:
        st.subheader("Target MCP")
        
        mcp = st.selectbox(
            "Select MCP:",
            ["customer-support", "product-docs", "code-analysis", "sales-insights"]
        )
        
        st.info(f"""
        **MCP:** {mcp}  
        **Pattern:** {pattern}  
        **Status:** 🟢 Ready
        """)
        
        st.markdown("---")
        st.subheader("Recent Queries")
        recent = [
            "How do I reset my password?",
            "What are the pricing tiers?",
            "Explain the API authentication"
        ]
        for q in recent:
            if st.button(f"↻ {q[:30]}...", key=f"recent_{q}", use_container_width=True):
                st.session_state['query'] = q
    
    # Results section
    if 'query_result' in st.session_state:
        st.markdown("---")
        st.subheader("📄 Results")
        
        result = st.session_state['query_result']
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Duration", f"{result['duration']}ms")
        with col2:
            st.metric("Tokens Used", result['tokens'])
        with col3:
            st.metric("Sources", result['sources'])
        with col4:
            st.metric("Confidence", f"{result['confidence']}%")
        
        # Response
        st.markdown("#### Response")
        st.markdown(result['response'])
        
        # Sources
        if result['sources'] > 0:
            with st.expander("📚 View Sources"):
                for i, source in enumerate(result['source_list'], 1):
                    st.markdown(f"**Source {i}:** {source}")


def execute_mock_query(query, pattern):
    """Execute a mock query (placeholder)."""
    import time
    time.sleep(1)  # Simulate processing
    
    return {
        "duration": 245,
        "tokens": 1247,
        "sources": 3,
        "confidence": 94,
        "response": f"Based on the knowledge base, here's the answer to your query using {pattern} pattern:\n\nThis is a mock response that would contain the actual answer from the MCP. The response is generated using the selected pattern and includes relevant context from the knowledge base.\n\n**Key Points:**\n- Point 1: Relevant information\n- Point 2: Additional context\n- Point 3: Supporting details",
        "source_list": [
            "Documentation > User Guide > Authentication",
            "Support Tickets > Ticket #12345",
            "Internal Wiki > Best Practices"
        ]
    }
