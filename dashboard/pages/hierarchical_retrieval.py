"""
Hierarchical Retrieval UI Page.

Provides interface for:
- Tier selection
- Token budget configuration
- Query execution
- Result visualization
"""

import streamlit as st
import sys
from pathlib import Path
from typing import List, Dict, Any
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# Add services directory to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_retrieval.src.hierarchical_retrieval import (
    HierarchicalRetriever,
    RetrievalResult,
)


# ============================================================================
# Page Configuration
# ============================================================================

def render():
    """Render the Hierarchical Retrieval page."""
    
    st.title("🔍 Hierarchical Retrieval")
    st.markdown("""
    Query across multiple MCP tiers with intelligent cascading and token budget management.
    """)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        render_configuration()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Query", "📊 Analytics", "ℹ️ About"])
    
    with tab1:
        render_query_interface()
    
    with tab2:
        render_analytics()
    
    with tab3:
        render_about()


# ============================================================================
# Configuration Section
# ============================================================================

def render_configuration():
    """Render configuration sidebar."""
    
    # Tier selection
    st.subheader("📁 MCP Tiers")
    
    available_tiers = ["client", "project", "company", "team", "ecosystem"]
    
    selected_tiers = []
    for tier in available_tiers:
        if st.checkbox(tier.title(), value=(tier in ["client", "project", "company"])):
            selected_tiers.append(tier)
    
    st.session_state['selected_tiers'] = selected_tiers or ["client"]
    
    # Token budget
    st.subheader("💰 Token Budget")
    token_budget = st.slider(
        "Maximum Tokens",
        min_value=500,
        max_value=8000,
        value=4000,
        step=500,
        help="Maximum tokens to retrieve across all tiers"
    )
    st.session_state['token_budget'] = token_budget
    
    # Tier weights
    st.subheader("⚖️ Tier Weights")
    st.markdown("*Customize tier prioritization*")
    
    weights = {}
    for tier in selected_tiers:
        default_weight = {
            "client": 0.4,
            "project": 0.3,
            "company": 0.15,
            "team": 0.1,
            "ecosystem": 0.05,
        }.get(tier, 0.1)
        
        weight = st.slider(
            f"{tier.title()}",
            min_value=0.0,
            max_value=1.0,
            value=default_weight,
            step=0.05,
            key=f"weight_{tier}"
        )
        weights[tier] = weight
    
    # Normalize weights
    total_weight = sum(weights.values())
    if total_weight > 0:
        weights = {k: v / total_weight for k, v in weights.items()}
    
    st.session_state['tier_weights'] = weights
    
    # Display normalized weights
    with st.expander("📊 Normalized Weights"):
        for tier, weight in weights.items():
            st.metric(tier.title(), f"{weight:.2%}")


# ============================================================================
# Query Interface
# ============================================================================

def render_query_interface():
    """Render query interface."""
    
    st.header("🔍 Execute Query")
    
    # Query input
    query = st.text_area(
        "Enter your query",
        height=100,
        placeholder="e.g., What are our customer support policies?",
        key="query_input"
    )
    
    # Query mode
    col1, col2 = st.columns([2, 1])
    
    with col1:
        mode = st.radio(
            "Query Mode",
            ["Standard Retrieval", "Budget-Constrained"],
            horizontal=True,
            help="Standard: Retrieve max results. Budget: Respect token budget."
        )
    
    with col2:
        if mode == "Standard Retrieval":
            max_results = st.number_input(
                "Max Results",
                min_value=1,
                max_value=100,
                value=10,
                step=1
            )
        else:
            max_results = None
    
    # Execute button
    if st.button("🚀 Execute Query", type="primary", use_container_width=True):
        if not query.strip():
            st.error("Please enter a query")
        else:
            execute_query(query, mode, max_results)
    
    # Display results
    if 'query_results' in st.session_state and st.session_state['query_results']:
        st.divider()
        render_results(st.session_state['query_results'])


def execute_query(query: str, mode: str, max_results: int = None):
    """Execute hierarchical retrieval query."""
    
    try:
        with st.spinner("Retrieving results..."):
            # Initialize retriever
            retriever = HierarchicalRetriever(
                tiers=st.session_state.get('selected_tiers', ["client"]),
                token_budget=st.session_state.get('token_budget', 4000),
                tier_weights=st.session_state.get('tier_weights', {}),
            )
            
            # Execute query
            if mode == "Standard Retrieval":
                results = retriever.retrieve(
                    query=query,
                    max_results=max_results
                )
            else:  # Budget-Constrained
                results = retriever.retrieve_with_budget(query=query)
            
            # Store results
            st.session_state['query_results'] = results
            st.session_state['last_query'] = query
            
            # Success message
            total_tokens = sum(r.token_count for r in results)
            st.success(f"✅ Retrieved {len(results)} results ({total_tokens} tokens)")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def render_results(results: List[RetrievalResult]):
    """Render query results."""
    
    st.header("📊 Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_tokens = sum(r.token_count for r in results)
    tiers = set(r.tier for r in results)
    avg_score = sum(r.score for r in results) / len(results) if results else 0
    
    with col1:
        st.metric("Total Results", len(results))
    with col2:
        st.metric("Total Tokens", total_tokens)
    with col3:
        st.metric("Tiers Used", len(tiers))
    with col4:
        st.metric("Avg Score", f"{avg_score:.3f}")
    
    # Tier distribution chart
    st.subheader("📁 Results by Tier")
    tier_counts = {}
    tier_tokens = {}
    
    for result in results:
        tier_counts[result.tier] = tier_counts.get(result.tier, 0) + 1
        tier_tokens[result.tier] = tier_tokens.get(result.tier, 0) + result.token_count
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Count distribution
        fig_counts = px.pie(
            values=list(tier_counts.values()),
            names=list(tier_counts.keys()),
            title="Result Count by Tier"
        )
        st.plotly_chart(fig_counts, use_container_width=True)
    
    with col2:
        # Token distribution
        fig_tokens = px.pie(
            values=list(tier_tokens.values()),
            names=list(tier_tokens.keys()),
            title="Token Distribution by Tier"
        )
        st.plotly_chart(fig_tokens, use_container_width=True)
    
    # Score distribution
    st.subheader("📈 Score Distribution")
    scores_df = pd.DataFrame([
        {"tier": r.tier, "score": r.score, "tokens": r.token_count}
        for r in results
    ])
    
    fig_scores = px.scatter(
        scores_df,
        x=range(len(results)),
        y="score",
        color="tier",
        size="tokens",
        title="Result Scores",
        labels={"x": "Result Index", "y": "Score", "tier": "Tier"}
    )
    st.plotly_chart(fig_scores, use_container_width=True)
    
    # Results table
    st.subheader("📋 Detailed Results")
    
    # Group by tier
    for tier in sorted(tiers, key=lambda t: ["client", "project", "company", "team", "ecosystem"].index(t)):
        tier_results = [r for r in results if r.tier == tier]
        
        with st.expander(f"📁 {tier.title()} Tier ({len(tier_results)} results)", expanded=True):
            for i, result in enumerate(tier_results[:5]):  # Show top 5 per tier
                st.markdown(f"""
                **Result {i+1}** | Score: `{result.score:.3f}` | Tokens: `{result.token_count}`
                
                {result.content}
                """)
                
                if i < len(tier_results) - 1:
                    st.divider()
            
            if len(tier_results) > 5:
                st.info(f"+ {len(tier_results) - 5} more results")


# ============================================================================
# Analytics Section
# ============================================================================

def render_analytics():
    """Render analytics dashboard."""
    
    st.header("📊 Analytics")
    
    if 'query_results' not in st.session_state or not st.session_state['query_results']:
        st.info("Execute a query to see analytics")
        return
    
    results = st.session_state['query_results']
    
    # Token efficiency
    st.subheader("💰 Token Efficiency")
    
    total_tokens = sum(r.token_count for r in results)
    budget = st.session_state.get('token_budget', 4000)
    efficiency = (total_tokens / budget) * 100 if budget > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Tokens Used", total_tokens)
    with col2:
        st.metric("Token Budget", budget)
    with col3:
        st.metric("Budget Utilization", f"{efficiency:.1f}%")
    
    # Progress bar
    st.progress(min(1.0, total_tokens / budget))
    
    # Score analysis
    st.subheader("📈 Score Analysis")
    
    scores = [r.score for r in results]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Min Score", f"{min(scores):.3f}")
    with col2:
        st.metric("Max Score", f"{max(scores):.3f}")
    with col3:
        st.metric("Mean Score", f"{sum(scores)/len(scores):.3f}")
    with col4:
        st.metric("Median Score", f"{sorted(scores)[len(scores)//2]:.3f}")
    
    # Score histogram
    fig_hist = px.histogram(
        x=scores,
        nbins=20,
        title="Score Distribution",
        labels={"x": "Score", "y": "Count"}
    )
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Tier performance
    st.subheader("🏆 Tier Performance")
    
    tier_stats = {}
    for result in results:
        if result.tier not in tier_stats:
            tier_stats[result.tier] = {
                "count": 0,
                "total_score": 0,
                "total_tokens": 0
            }
        
        tier_stats[result.tier]["count"] += 1
        tier_stats[result.tier]["total_score"] += result.score
        tier_stats[result.tier]["total_tokens"] += result.token_count
    
    tier_df = pd.DataFrame([
        {
            "Tier": tier.title(),
            "Results": stats["count"],
            "Avg Score": stats["total_score"] / stats["count"],
            "Total Tokens": stats["total_tokens"],
        }
        for tier, stats in tier_stats.items()
    ])
    
    st.dataframe(tier_df, use_container_width=True)


# ============================================================================
# About Section
# ============================================================================

def render_about():
    """Render about/help section."""
    
    st.header("ℹ️ About Hierarchical Retrieval")
    
    st.markdown("""
    ## Overview
    
    Hierarchical Retrieval enables intelligent querying across multiple MCP tiers with:
    
    - **Cascading Retrieval**: Automatically searches from highest to lowest priority tiers
    - **Token Budget Management**: Distributes token budget across tiers based on weights
    - **Custom Prioritization**: Configure tier weights to match your needs
    
    ## MCP Tier Hierarchy
    
    1. **Client** 👤 - Most specific, client-focused knowledge
    2. **Project** 📁 - Project-specific information
    3. **Company** 🏢 - Company-wide knowledge
    4. **Team** 👥 - Team-specific context
    5. **Ecosystem** 🌐 - Broadest, industry knowledge
    
    ## Query Modes
    
    ### Standard Retrieval
    - Retrieves up to specified max results
    - Cascades across tiers until limit reached
    - Best for: Comprehensive queries
    
    ### Budget-Constrained
    - Respects strict token budget
    - Distributes budget across tiers by weight
    - Best for: Cost-sensitive queries
    
    ## Tier Weights
    
    Tier weights control:
    - Budget distribution across tiers
    - Result prioritization
    - Score boosting
    
    **Default Weights:**
    - Client: 40%
    - Project: 30%
    - Company: 15%
    - Team: 10%
    - Ecosystem: 5%
    
    ## Tips
    
    ✅ Use client-focused queries for specific requirements  
    ✅ Use budget-constrained mode to control costs  
    ✅ Adjust weights based on your use case  
    ✅ Review analytics to optimize configuration  
    
    ## Example Queries
    
    - "What are our customer support policies?"
    - "Explain the authentication requirements for Project X"
    - "What tools does the engineering team use?"
    - "What are industry best practices for API design?"
    """)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    render()

