"""Query Interface - Tight Interpreter + Retrieval + Orchestrator Integration."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd

from integrations.interpreter_client import InterpreterClient
from integrations.retrieval_client import RetrievalClient

# Page config
st.set_page_config(
    page_title="Query Interface",
    page_icon="🔍",
    layout="wide"
)

# Initialize clients
@st.cache_resource
def get_clients():
    return {
        "interpreter": InterpreterClient(),
        "retrieval": RetrievalClient(),
    }

clients = get_clients()

st.title("🔍 Intelligent Query Interface")
st.markdown("Natural language queries with hierarchical context retrieval")

# Session state for query history
if "query_history" not in st.session_state:
    st.session_state.query_history = []

# Main query interface
col_query1, col_query2 = st.columns([3, 1])

with col_query1:
    query = st.text_area(
        "Ask a question...",
        placeholder="e.g., What are our API best practices for authentication?",
        height=100,
        key="query_input"
    )

with col_query2:
    st.markdown("#### Settings")
    
    selected_mcp = st.selectbox(
        "MCP Instance",
        ["acme-corp-dev", "customer-support-kb", "eng-docs", "sales-playbook"]
    )
    
    user_id = st.text_input("User ID", value="user-123", disabled=True)

# Query execution buttons
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])

with col_btn1:
    execute_query = st.button(
        "🚀 Execute Query",
        use_container_width=True,
        type="primary",
        disabled=not query
    )

with col_btn2:
    if st.button("🔄 Clear", use_container_width=True):
        st.session_state.query_input = ""
        st.rerun()

if execute_query and query:
    # Add to history
    st.session_state.query_history.append({
        "query": query,
        "mcp": selected_mcp,
        "timestamp": datetime.now()
    })
    
    # Step 1: Interpret query
    st.divider()
    st.subheader("🧠 Step 1: Query Interpretation")
    
    with st.spinner("Interpreting query..."):
        # Would call: clients["interpreter"].interpret_query(query, user_id)
        interpretation = {
            "intent": "information_retrieval",
            "confidence": 0.92,
            "entities": [
                {"text": "API best practices", "type": "TOPIC", "confidence": 0.95},
                {"text": "authentication", "type": "SUBTOPIC", "confidence": 0.89}
            ],
            "suggested_patterns": ["RAG", "Multi-hop QA"]
        }
        
        col_int1, col_int2, col_int3 = st.columns(3)
        
        with col_int1:
            st.metric("Intent", interpretation["intent"])
        
        with col_int2:
            st.metric("Confidence", f"{interpretation['confidence']*100:.1f}%")
        
        with col_int3:
            st.metric("Pattern", interpretation["suggested_patterns"][0])
        
        # Entities visualization
        st.markdown("**Extracted Entities:**")
        for entity in interpretation["entities"]:
            st.info(f"**{entity['type']}**: {entity['text']} (confidence: {entity['confidence']*100:.0f}%)")
    
    # Step 2: Hierarchical Retrieval
    st.divider()
    st.subheader("🔍 Step 2: Hierarchical Context Retrieval")
    
    with st.spinner("Retrieving context across tiers..."):
        # Would call: clients["retrieval"].hierarchical_retrieve(...)
        retrieval_results = {
            "Client": [
                {"title": "Personal Auth Notes", "score": 0.94, "tokens": 450},
                {"title": "My API Examples", "score": 0.88, "tokens": 320}
            ],
            "Project": [
                {"title": "Project API Guidelines", "score": 0.96, "tokens": 680},
                {"title": "Auth Implementation Guide", "score": 0.93, "tokens": 540},
                {"title": "Security Best Practices", "score": 0.91, "tokens": 420}
            ],
            "Team": [
                {"title": "Team Engineering Standards", "score": 0.89, "tokens": 510},
                {"title": "Code Review Guidelines", "score": 0.85, "tokens": 380}
            ],
            "Company": [
                {"title": "Company Security Policy", "score": 0.87, "tokens": 620},
                {"title": "Compliance Requirements", "score": 0.83, "tokens": 450}
            ]
        }
        
        # Token budget visualization
        total_tokens = sum(doc["tokens"] for tier_docs in retrieval_results.values() for doc in tier_docs)
        token_budget = 8000
        
        col_token1, col_token2, col_token3 = st.columns(3)
        
        with col_token1:
            st.metric("Total Tokens", f"{total_tokens:,}")
        
        with col_token2:
            st.metric("Budget", f"{token_budget:,}")
        
        with col_token3:
            utilization = (total_tokens / token_budget) * 100
            st.metric("Utilization", f"{utilization:.1f}%")
        
        st.progress(min(utilization / 100, 1.0))
        
        # Results by tier
        st.markdown("#### Results by Tier")
        
        for tier, docs in retrieval_results.items():
            with st.expander(f"**{tier}** tier - {len(docs)} documents", expanded=True):
                for doc in docs:
                    col_doc1, col_doc2, col_doc3 = st.columns([3, 1, 1])
                    
                    with col_doc1:
                        st.markdown(f"📄 **{doc['title']}**")
                    
                    with col_doc2:
                        st.caption(f"Score: {doc['score']:.2f}")
                    
                    with col_doc3:
                        st.caption(f"Tokens: {doc['tokens']}")
    
    # Step 3: Context Pruning
    st.divider()
    st.subheader("✂️ Step 3: Context Pruning")
    
    with st.spinner("Optimizing context..."):
        pruning_strategy = "HYBRID"
        
        # Show before/after
        col_prune1, col_prune2 = st.columns(2)
        
        with col_prune1:
            st.markdown("**Before Pruning**")
            st.metric("Documents", "12")
            st.metric("Total Tokens", f"{total_tokens:,}")
        
        with col_prune2:
            st.markdown("**After Pruning**")
            pruned_docs = 8
            pruned_tokens = 7850
            st.metric("Documents", f"{pruned_docs}", delta=f"-{12-pruned_docs}")
            st.metric("Total Tokens", f"{pruned_tokens:,}", delta=f"-{total_tokens-pruned_tokens}")
        
        st.info(f"✅ Pruned using **{pruning_strategy}** strategy - retained most relevant content")
    
    # Step 4: Pattern Execution
    st.divider()
    st.subheader("🎯 Step 4: Pattern Execution (RAG)")
    
    with st.spinner("Executing query with LLM..."):
        # Would call orchestrator to execute
        response = """
        Based on your organization's documentation, here are the API best practices for authentication:

        ## 1. Use OAuth 2.0 / OpenID Connect
        - Implement standard OAuth 2.0 flows for authentication
        - Use OpenID Connect for user identity
        - Never roll your own authentication

        ## 2. API Key Management
        - Rotate API keys every 90 days
        - Store keys in secure vaults (never in code)
        - Implement key-per-environment strategy

        ## 3. Token Security
        - Use short-lived access tokens (15 minutes)
        - Implement refresh token rotation
        - Store tokens securely (httpOnly cookies for web)

        ## 4. Rate Limiting
        - Implement per-user rate limits
        - Use exponential backoff for retries
        - Monitor and alert on suspicious patterns

        ## 5. Multi-Factor Authentication
        - Require MFA for all production access
        - Support TOTP and hardware tokens
        - Implement backup recovery codes

        These practices are derived from your project guidelines, team standards, and company security policies.
        """
        
        st.markdown(response)
        
        # Sources
        st.markdown("#### 📚 Sources")
        
        source_docs = [
            {"title": "Project API Guidelines", "tier": "Project", "relevance": "96%"},
            {"title": "Auth Implementation Guide", "tier": "Project", "relevance": "93%"},
            {"title": "Security Best Practices", "tier": "Project", "relevance": "91%"},
            {"title": "Company Security Policy", "tier": "Company", "relevance": "87%"}
        ]
        
        for doc in source_docs:
            col_src1, col_src2, col_src3 = st.columns([3, 1, 1])
            
            with col_src1:
                st.caption(f"📄 {doc['title']}")
            
            with col_src2:
                st.caption(f"{doc['tier']}")
            
            with col_src3:
                st.caption(f"⭐ {doc['relevance']}")
    
    # Execution metrics
    st.divider()
    st.subheader("📊 Execution Metrics")
    
    col_metric1, col_metric2, col_metric3, col_metric4 = st.columns(4)
    
    with col_metric1:
        st.metric("Total Time", "2.34s")
    
    with col_metric2:
        st.metric("Tokens (Prompt)", "7,850")
    
    with col_metric3:
        st.metric("Tokens (Response)", "420")
    
    with col_metric4:
        st.metric("Cost", "$0.15")

# Sidebar: Query History
with st.sidebar:
    st.subheader("📜 Query History")
    
    if st.session_state.query_history:
        for i, item in enumerate(reversed(st.session_state.query_history[-10:])):
            with st.expander(f"{item['timestamp'].strftime('%H:%M')} - {item['query'][:30]}..."):
                st.caption(f"**MCP:** {item['mcp']}")
                st.caption(f"**Time:** {item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                if st.button("🔄 Rerun", key=f"rerun_{i}"):
                    st.session_state.query_input = item['query']
                    st.rerun()
    else:
        st.info("No query history yet")
    
    st.divider()
    
    # Quick suggestions
    st.subheader("💡 Suggested Queries")
    
    suggestions = [
        "API authentication best practices",
        "How to deploy our services?",
        "What are our coding standards?",
        "Customer onboarding process",
        "Database schema guidelines"
    ]
    
    for suggestion in suggestions:
        if st.button(f"💬 {suggestion}", key=f"sug_{suggestion}", use_container_width=True):
            st.session_state.query_input = suggestion
            st.rerun()

# Footer
st.divider()
st.caption("💡 Tip: Be specific in your queries for better results. The system searches across all accessible tiers.")

