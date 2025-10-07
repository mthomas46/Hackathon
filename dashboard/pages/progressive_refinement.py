"""
Progressive Refinement UI Page.

Provides interface for:
- Progressive context refinement
- Strategy selection
- Token budget management
- Refinement visualization
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# Add services directory to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_tier_manager.src.tier_manager import TierManager
from mcp_tier_manager.src.progressive_refinement import (
    ProgressiveRefiner,
    RefinementConfig,
    RefinementStrategy
)


# ============================================================================
# Page Configuration
# ============================================================================

def render():
    """Render the Progressive Refinement page."""
    
    st.title("🔄 Progressive Context Refinement")
    st.markdown("""
    Intelligently refine context by progressively traversing the tier hierarchy.
    """)
    
    # Initialize session state
    if 'tier_manager' not in st.session_state:
        st.session_state['tier_manager'] = TierManager()
    
    if 'refiner' not in st.session_state:
        st.session_state['refiner'] = ProgressiveRefiner(st.session_state['tier_manager'])
    
    tier_manager = st.session_state['tier_manager']
    refiner = st.session_state['refiner']
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔄 Refine",
        "📊 Results",
        "📈 Analytics",
        "ℹ️ Help"
    ])
    
    with tab1:
        render_refine(tier_manager, refiner)
    
    with tab2:
        render_results()
    
    with tab3:
        render_analytics()
    
    with tab4:
        render_help()


# ============================================================================
# Refine Section
# ============================================================================

def render_refine(tier_manager: TierManager, refiner: ProgressiveRefiner):
    """Render refinement interface."""
    
    st.header("🔄 Refine Context")
    
    all_tiers = tier_manager.get_all_tiers_overview()
    
    if not all_tiers:
        st.warning("⚠️ No tiers available. Create tiers in the Tier Management page first.")
        return
    
    # Configuration
    st.subheader("⚙️ Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Starting tier
        tier_options = [f"{t['name']} ({t['tier_type']})" for t in all_tiers]
        selected_tier = st.selectbox(
            "Starting Tier",
            options=tier_options,
            help="Tier to start refinement from"
        )
    
    with col2:
        # Refinement strategy
        strategy = st.selectbox(
            "Refinement Strategy",
            options=["bottom_up", "top_down", "balanced"],
            format_func=lambda x: {
                "bottom_up": "🔺 Bottom-Up (Specific → General)",
                "top_down": "🔻 Top-Down (General → Specific)",
                "balanced": "⚖️ Balanced (Mixed)"
            }[x],
            help="Strategy for traversing the hierarchy"
        )
    
    # Advanced options
    with st.expander("⚙️ Advanced Options"):
        token_budget = st.slider(
            "Token Budget",
            min_value=500,
            max_value=8000,
            value=4000,
            step=500,
            help="Maximum tokens to retrieve"
        )
        
        max_tiers = st.slider(
            "Max Tiers",
            min_value=1,
            max_value=5,
            value=5,
            help="Maximum number of tiers to search"
        )
        
        min_relevance = st.slider(
            "Min Relevance",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            step=0.1,
            help="Minimum relevance score for results"
        )
    
    # Query input
    st.subheader("🔍 Query")
    query = st.text_area(
        "Enter your query",
        height=100,
        placeholder="What information are you looking for?"
    )
    
    # Refine button
    if st.button("🔄 Refine Context", type="primary", use_container_width=True):
        if not query:
            st.warning("Please enter a query")
        else:
            with st.spinner("Refining context..."):
                try:
                    # Get tier ID
                    tier_name = selected_tier.split(" (")[0]
                    tier_id = next(t['tier_id'] for t in all_tiers if t['name'] == tier_name)
                    
                    # Create config
                    config = RefinementConfig(
                        strategy=RefinementStrategy(strategy),
                        token_budget=token_budget,
                        max_tiers=max_tiers,
                        min_relevance=min_relevance
                    )
                    
                    # Refine
                    result = refiner.refine_context(query, tier_id, config)
                    
                    # Store in session state
                    st.session_state['refinement_result'] = result
                    st.session_state['refinement_query'] = query
                    
                    st.success(f"✅ Refinement complete! Found {len(result.get_all_results())} results from {len(result.tiers_used)} tiers")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Refinement error: {str(e)}")


# ============================================================================
# Results Section
# ============================================================================

def render_results():
    """Render refinement results."""
    
    st.header("📊 Refinement Results")
    
    if 'refinement_result' not in st.session_state:
        st.info("Run a refinement query to see results")
        return
    
    result = st.session_state['refinement_result']
    query = st.session_state.get('refinement_query', 'N/A')
    
    # Summary metrics
    st.subheader("📈 Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Strategy", result.strategy.value.replace('_', ' ').title())
    with col2:
        st.metric("Tiers Used", len(result.tiers_used))
    with col3:
        st.metric("Total Results", len(result.get_all_results()))
    with col4:
        st.metric("Total Tokens", result.total_tokens)
    
    # Quality score
    st.subheader("⭐ Refinement Quality")
    
    quality_percent = result.refinement_score * 100
    
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=quality_percent,
        title={'text': "Quality Score"},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "green" if quality_percent >= 70 else "orange" if quality_percent >= 40 else "red"},
            'steps': [
                {'range': [0, 40], 'color': "lightcoral"},
                {'range': [40, 70], 'color': "lightyellow"},
                {'range': [70, 100], 'color': "lightgreen"}
            ]
        }
    ))
    
    st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Tier breakdown
    st.subheader("📁 Results by Tier")
    
    summary = result.get_tier_summary()
    
    if summary:
        # Create DataFrame for visualization
        tier_data = {
            'Tier': [t.title() for t in summary.keys()],
            'Results': [v['count'] for v in summary.values()],
            'Tokens': [v['tokens'] for v in summary.values()],
            'Avg Relevance': [v['avg_relevance'] for v in summary.values()]
        }
        
        # Bar chart
        fig_bar = go.Figure(data=[
            go.Bar(name='Results', x=tier_data['Tier'], y=tier_data['Results']),
            go.Bar(name='Tokens', x=tier_data['Tier'], y=tier_data['Tokens'])
        ])
        fig_bar.update_layout(barmode='group', title="Results and Tokens by Tier")
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Detailed results
    st.subheader("📋 Detailed Results")
    
    for tier_type, results in result.results_by_tier.items():
        with st.expander(f"📁 {tier_type.value.title()} Tier ({len(results)} results)"):
            for i, r in enumerate(results, 1):
                st.markdown(f"**Result {i}** (Relevance: {r.relevance:.2f}, Tokens: {r.token_count})")
                st.markdown(r.content)
                if r.metadata:
                    with st.expander("Metadata"):
                        st.json(r.metadata)
                st.divider()


# ============================================================================
# Analytics Section
# ============================================================================

def render_analytics():
    """Render refinement analytics."""
    
    st.header("📈 Refinement Analytics")
    
    if 'refinement_result' not in st.session_state:
        st.info("Run refinements to see analytics")
        return
    
    result = st.session_state['refinement_result']
    
    # Token utilization
    st.subheader("💾 Token Utilization")
    
    token_used_percent = (result.total_tokens / 8000) * 100  # Assuming 8000 max
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Tokens Used", result.total_tokens)
    with col2:
        st.metric("Utilization", f"{token_used_percent:.1f}%")
    
    # Token distribution
    st.subheader("📊 Token Distribution")
    
    summary = result.get_tier_summary()
    if summary:
        fig_pie = px.pie(
            values=[v['tokens'] for v in summary.values()],
            names=[k.title() for k in summary.keys()],
            title="Token Distribution by Tier"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Relevance distribution
    st.subheader("⭐ Relevance Distribution")
    
    all_results = result.get_all_results()
    if all_results:
        relevances = [r.relevance for r in all_results]
        
        fig_hist = px.histogram(
            x=relevances,
            nbins=20,
            title="Distribution of Relevance Scores",
            labels={'x': 'Relevance Score', 'y': 'Count'}
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Min Relevance", f"{min(relevances):.2f}")
        with col2:
            st.metric("Avg Relevance", f"{sum(relevances)/len(relevances):.2f}")
        with col3:
            st.metric("Max Relevance", f"{max(relevances):.2f}")


# ============================================================================
# Help Section
# ============================================================================

def render_help():
    """Render help information."""
    
    st.header("ℹ️ Help & Information")
    
    st.subheader("🔄 What is Progressive Refinement?")
    st.markdown("""
    Progressive refinement intelligently traverses the tier hierarchy to gather relevant context
    for your query. It balances specific user context with general organizational knowledge.
    """)
    
    st.subheader("📊 Refinement Strategies")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🔺 Bottom-Up**
        
        Starts with the most specific tier (Client) and progressively adds broader context.
        
        **Best for:**
        - User-specific queries
        - Personalized responses
        - Task-focused questions
        """)
    
    with col2:
        st.markdown("""
        **🔻 Top-Down**
        
        Starts with the most general tier (Ecosystem) and adds specific details.
        
        **Best for:**
        - General knowledge queries
        - Policy questions
        - Best practices
        """)
    
    with col3:
        st.markdown("""
        **⚖️ Balanced**
        
        Balances specific and general context based on relevance.
        
        **Best for:**
        - Mixed queries
        - Exploratory searches
        - Unsure context needs
        """)
    
    st.subheader("🎯 Tips for Better Results")
    st.markdown("""
    1. **Choose the right strategy:** Match the strategy to your query type
    2. **Adjust token budget:** More tokens = more context, but slower
    3. **Set min relevance:** Filter out low-relevance results
    4. **Start from the right tier:** Choose the most appropriate starting point
    5. **Refine iteratively:** Adjust parameters based on results
    """)
    
    st.subheader("📊 Understanding Quality Score")
    st.markdown("""
    The quality score combines:
    - **Tier diversity (30%):** How many different tiers contributed
    - **Average relevance (50%):** How relevant the results are
    - **Token utilization (20%):** How efficiently tokens were used
    
    **Score Ranges:**
    - 70-100%: Excellent refinement
    - 40-70%: Good refinement
    - 0-40%: Needs improvement
    """)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    render()

