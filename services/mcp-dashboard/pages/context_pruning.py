"""
Context Pruning UI Page.

Provides interface for:
- Strategy selection
- Token budget configuration
- Context item management
- Pruning execution
- Result visualization
"""

import streamlit as st
import sys
from pathlib import Path
from typing import List
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import random

# Add services directory to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_retrieval.src.context_pruning import (
    ContextPruner,
    PruningStrategy,
    ContextItem,
    create_context_item,
)


# ============================================================================
# Page Configuration
# ============================================================================

def render():
    """Render the Context Pruning page."""
    
    st.title("✂️ Dynamic Context Pruning")
    st.markdown("""
    Intelligently prune context to fit within token budgets while preserving the most valuable information.
    """)
    
    # Initialize session state
    if 'context_items' not in st.session_state:
        st.session_state['context_items'] = generate_sample_context()
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        render_configuration()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Context", "✂️ Prune", "📊 Analysis", "ℹ️ About"])
    
    with tab1:
        render_context_management()
    
    with tab2:
        render_pruning_interface()
    
    with tab3:
        render_analysis()
    
    with tab4:
        render_about()


# ============================================================================
# Configuration Section
# ============================================================================

def render_configuration():
    """Render configuration sidebar."""
    
    # Strategy selection
    st.subheader("🎯 Pruning Strategy")
    
    strategy_options = {
        "Relevance": PruningStrategy.RELEVANCE,
        "Recency": PruningStrategy.RECENCY,
        "Hybrid (50/50)": PruningStrategy.HYBRID,
        "Importance": PruningStrategy.IMPORTANCE,
    }
    
    selected_strategy_name = st.selectbox(
        "Select Strategy",
        options=list(strategy_options.keys()),
        index=2,  # Default to Hybrid
        help="Choose how to prioritize context items"
    )
    
    st.session_state['pruning_strategy'] = strategy_options[selected_strategy_name]
    
    # Strategy descriptions
    strategy_descriptions = {
        "Relevance": "📊 Keeps items with highest relevance scores",
        "Recency": "🕐 Keeps most recently created items",
        "Hybrid (50/50)": "⚖️ Balances relevance and recency equally",
        "Importance": "⭐ Keeps items with highest importance scores",
    }
    
    st.info(strategy_descriptions[selected_strategy_name])
    
    # Token budget
    st.subheader("💰 Token Budget")
    
    # Calculate current token usage
    if 'context_items' in st.session_state:
        total_tokens = sum(item.token_count for item in st.session_state['context_items'])
    else:
        total_tokens = 0
    
    st.metric("Current Usage", f"{total_tokens} tokens")
    
    target_tokens = st.slider(
        "Target Budget",
        min_value=50,
        max_value=total_tokens if total_tokens > 0 else 500,
        value=min(200, total_tokens) if total_tokens > 0 else 200,
        step=50,
        help="Maximum tokens after pruning"
    )
    
    st.session_state['target_tokens'] = target_tokens
    
    # Show pruning target
    if total_tokens > 0:
        pruning_ratio = (target_tokens / total_tokens) * 100
        st.metric("Target Ratio", f"{pruning_ratio:.1f}%")


# ============================================================================
# Context Management Section
# ============================================================================

def render_context_management():
    """Render context item management."""
    
    st.header("📋 Context Items")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Generate Sample", use_container_width=True):
            st.session_state['context_items'] = generate_sample_context()
            st.success("Generated new sample context")
            st.rerun()
    
    with col2:
        if st.button("➕ Add Item", use_container_width=True):
            add_context_item()
            st.rerun()
    
    with col3:
        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state['context_items'] = []
            st.success("Cleared all items")
            st.rerun()
    
    # Display context items
    if st.session_state['context_items']:
        display_context_items(st.session_state['context_items'])
    else:
        st.info("No context items. Generate sample or add items manually.")


def display_context_items(items: List[ContextItem]):
    """Display context items in a table."""
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_items = len(items)
    total_tokens = sum(item.token_count for item in items)
    avg_relevance = sum(item.relevance_score for item in items) / len(items)
    avg_importance = sum(item.importance_score for item in items) / len(items)
    
    with col1:
        st.metric("Total Items", total_items)
    with col2:
        st.metric("Total Tokens", total_tokens)
    with col3:
        st.metric("Avg Relevance", f"{avg_relevance:.2f}")
    with col4:
        st.metric("Avg Importance", f"{avg_importance:.2f}")
    
    # Items table
    st.subheader("Items")
    
    df_data = []
    for i, item in enumerate(items):
        age = datetime.now() - item.timestamp
        age_str = f"{age.days}d {age.seconds // 3600}h" if age.days > 0 else f"{age.seconds // 3600}h {(age.seconds % 3600) // 60}m"
        
        df_data.append({
            "#": i + 1,
            "Content": item.content[:50] + "..." if len(item.content) > 50 else item.content,
            "Tokens": item.token_count,
            "Relevance": f"{item.relevance_score:.2f}",
            "Importance": f"{item.importance_score:.2f}",
            "Age": age_str,
            "Priority": item.metadata.get("priority", "N/A"),
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def generate_sample_context() -> List[ContextItem]:
    """Generate sample context items for testing."""
    now = datetime.now()
    
    sample_items = [
        {
            "content": "Critical authentication bug fix needed urgently for production",
            "hours_ago": 1,
            "relevance": 0.95,
            "importance": 0.98,
            "priority": "critical"
        },
        {
            "content": "User reported slow dashboard loading times in analytics section",
            "hours_ago": 3,
            "relevance": 0.85,
            "importance": 0.75,
            "priority": "high"
        },
        {
            "content": "Update documentation for new API endpoints released last sprint",
            "hours_ago": 48,
            "relevance": 0.65,
            "importance": 0.60,
            "priority": "medium"
        },
        {
            "content": "Refactor legacy code in payment processing module for maintainability",
            "hours_ago": 72,
            "relevance": 0.55,
            "importance": 0.50,
            "priority": "medium"
        },
        {
            "content": "Customer requested custom export feature for quarterly reports",
            "hours_ago": 120,
            "relevance": 0.70,
            "importance": 0.65,
            "priority": "medium"
        },
        {
            "content": "Add unit tests for newly implemented user permissions system",
            "hours_ago": 168,
            "relevance": 0.60,
            "importance": 0.55,
            "priority": "low"
        },
        {
            "content": "Review and merge pending pull requests from external contributors",
            "hours_ago": 200,
            "relevance": 0.45,
            "importance": 0.40,
            "priority": "low"
        },
        {
            "content": "Update dependencies to latest versions and address security patches",
            "hours_ago": 240,
            "relevance": 0.50,
            "importance": 0.70,
            "priority": "medium"
        },
        {
            "content": "Optimize database queries causing high CPU usage during peak hours",
            "hours_ago": 10,
            "relevance": 0.90,
            "importance": 0.85,
            "priority": "high"
        },
        {
            "content": "Plan architecture for upcoming microservices migration project",
            "hours_ago": 24,
            "relevance": 0.75,
            "importance": 0.80,
            "priority": "high"
        },
    ]
    
    items = []
    for sample in sample_items:
        items.append(create_context_item(
            content=sample["content"],
            timestamp=now - timedelta(hours=sample["hours_ago"]),
            relevance_score=sample["relevance"],
            importance_score=sample["importance"],
            metadata={"priority": sample["priority"]}
        ))
    
    return items


def add_context_item():
    """Add a new context item."""
    # This would open a form, but for simplicity, we'll add a random one
    new_item = create_context_item(
        content=f"New item added at {datetime.now().strftime('%H:%M:%S')}",
        timestamp=datetime.now(),
        relevance_score=random.uniform(0.5, 1.0),
        importance_score=random.uniform(0.5, 1.0),
        metadata={"priority": random.choice(["low", "medium", "high"])}
    )
    
    st.session_state['context_items'].append(new_item)
    st.success("Added new item")


# ============================================================================
# Pruning Interface
# ============================================================================

def render_pruning_interface():
    """Render pruning execution interface."""
    
    st.header("✂️ Execute Pruning")
    
    if not st.session_state.get('context_items'):
        st.warning("No context items to prune. Add items in the Context tab.")
        return
    
    # Display configuration
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Pruning Strategy", st.session_state.get('pruning_strategy', PruningStrategy.HYBRID).value.title())
    
    with col2:
        st.metric("Target Budget", f"{st.session_state.get('target_tokens', 200)} tokens")
    
    # Execute pruning button
    if st.button("🚀 Execute Pruning", type="primary", use_container_width=True):
        execute_pruning()
    
    # Display results
    if 'pruned_result' in st.session_state:
        st.divider()
        render_pruning_results()


def execute_pruning():
    """Execute context pruning."""
    
    try:
        with st.spinner("Pruning context..."):
            # Initialize pruner
            pruner = ContextPruner(
                strategy=st.session_state.get('pruning_strategy', PruningStrategy.HYBRID)
            )
            
            # Execute pruning
            result = pruner.prune(
                items=st.session_state['context_items'],
                target_tokens=st.session_state.get('target_tokens', 200)
            )
            
            # Store result
            st.session_state['pruned_result'] = result
            
            # Success message
            st.success(f"✅ Pruned {len(st.session_state['context_items'])} items down to {len(result.items)} items ({result.token_count} tokens)")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def render_pruning_results():
    """Render pruning results."""
    
    result = st.session_state['pruned_result']
    
    st.header("📊 Pruning Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Items Kept", len(result.items))
    with col2:
        st.metric("Tokens Used", result.token_count)
    with col3:
        st.metric("Pruning Ratio", f"{result.pruning_ratio:.1%}")
    with col4:
        st.metric("Items Removed", result.metadata.get("items_removed", 0))
    
    # Before/after comparison
    st.subheader("📊 Before vs After")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Before Pruning:**")
        st.metric("Items", result.metadata.get("original_item_count", 0))
        st.metric("Tokens", result.metadata.get("original_token_count", 0))
    
    with col2:
        st.markdown("**After Pruning:**")
        st.metric("Items", result.metadata.get("pruned_item_count", 0))
        st.metric("Tokens", result.token_count)
    
    # Visualizations
    render_pruning_visualizations(result)
    
    # Pruned items list
    st.subheader("✂️ Kept Items")
    
    for i, item in enumerate(result.items):
        with st.expander(f"Item {i+1}: {item.content[:60]}...", expanded=(i < 3)):
            st.markdown(f"""
            **Content:** {item.content}
            
            **Metrics:**
            - Relevance: {item.relevance_score:.2f}
            - Importance: {item.importance_score:.2f}
            - Tokens: {item.token_count}
            - Priority: {item.metadata.get('priority', 'N/A')}
            """)


def render_pruning_visualizations(result):
    """Render pruning visualizations."""
    
    st.subheader("📈 Visualizations")
    
    # Token distribution
    col1, col2 = st.columns(2)
    
    with col1:
        # Before/after token comparison
        fig_tokens = go.Figure(data=[
            go.Bar(
                x=["Before", "After"],
                y=[
                    result.metadata.get("original_token_count", 0),
                    result.token_count
                ],
                marker_color=['lightblue', 'lightgreen']
            )
        ])
        fig_tokens.update_layout(
            title="Token Usage",
            yaxis_title="Tokens",
            showlegend=False
        )
        st.plotly_chart(fig_tokens, use_container_width=True)
    
    with col2:
        # Item count comparison
        fig_items = go.Figure(data=[
            go.Bar(
                x=["Before", "After"],
                y=[
                    result.metadata.get("original_item_count", 0),
                    result.metadata.get("pruned_item_count", 0)
                ],
                marker_color=['lightcoral', 'lightgreen']
            )
        ])
        fig_items.update_layout(
            title="Item Count",
            yaxis_title="Items",
            showlegend=False
        )
        st.plotly_chart(fig_items, use_container_width=True)
    
    # Score distribution of kept items
    if result.items:
        df_scores = pd.DataFrame([
            {
                "Item": i + 1,
                "Relevance": item.relevance_score,
                "Importance": item.importance_score,
                "Tokens": item.token_count
            }
            for i, item in enumerate(result.items)
        ])
        
        fig_scores = px.scatter(
            df_scores,
            x="Relevance",
            y="Importance",
            size="Tokens",
            hover_data=["Item"],
            title="Kept Items: Relevance vs Importance"
        )
        st.plotly_chart(fig_scores, use_container_width=True)


# ============================================================================
# Analysis Section
# ============================================================================

def render_analysis():
    """Render analysis dashboard."""
    
    st.header("📊 Context Analysis")
    
    if not st.session_state.get('context_items'):
        st.info("No context items to analyze. Add items in the Context tab.")
        return
    
    items = st.session_state['context_items']
    
    # Distribution analysis
    st.subheader("📈 Score Distributions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Relevance distribution
        relevance_scores = [item.relevance_score for item in items]
        fig_rel = px.histogram(
            x=relevance_scores,
            nbins=10,
            title="Relevance Score Distribution",
            labels={"x": "Relevance Score", "y": "Count"}
        )
        st.plotly_chart(fig_rel, use_container_width=True)
    
    with col2:
        # Importance distribution
        importance_scores = [item.importance_score for item in items]
        fig_imp = px.histogram(
            x=importance_scores,
            nbins=10,
            title="Importance Score Distribution",
            labels={"x": "Importance Score", "y": "Count"}
        )
        st.plotly_chart(fig_imp, use_container_width=True)
    
    # Token analysis
    st.subheader("💰 Token Analysis")
    
    df_tokens = pd.DataFrame([
        {
            "Item": i + 1,
            "Content": item.content[:30] + "...",
            "Tokens": item.token_count,
            "Relevance": item.relevance_score,
            "Importance": item.importance_score
        }
        for i, item in enumerate(items)
    ])
    
    fig_tokens = px.bar(
        df_tokens,
        x="Item",
        y="Tokens",
        title="Token Count per Item",
        hover_data=["Content", "Relevance", "Importance"]
    )
    st.plotly_chart(fig_tokens, use_container_width=True)
    
    # Age analysis
    st.subheader("🕐 Age Analysis")
    
    now = datetime.now()
    ages_hours = [(now - item.timestamp).total_seconds() / 3600 for item in items]
    
    fig_age = px.histogram(
        x=ages_hours,
        nbins=15,
        title="Item Age Distribution",
        labels={"x": "Age (hours)", "y": "Count"}
    )
    st.plotly_chart(fig_age, use_container_width=True)


# ============================================================================
# About Section
# ============================================================================

def render_about():
    """Render about/help section."""
    
    st.header("ℹ️ About Context Pruning")
    
    st.markdown("""
    ## Overview
    
    Dynamic Context Pruning intelligently reduces context size while preserving the most valuable information.
    
    ## Pruning Strategies
    
    ### 1. 📊 Relevance
    - Keeps items with highest relevance scores
    - Best for: Query-focused tasks
    - Order: Descending by relevance
    
    ### 2. 🕐 Recency
    - Keeps most recently created items
    - Best for: Time-sensitive updates
    - Order: Newest first
    
    ### 3. ⚖️ Hybrid (50/50)
    - Balances relevance and recency equally
    - Best for: General purpose pruning
    - Order: Combined score (50% relevance + 50% recency)
    
    ### 4. ⭐ Importance
    - Keeps items with highest importance scores
    - Best for: Priority-based tasks
    - Order: Descending by importance
    
    ## How It Works
    
    1. **Select Strategy** - Choose pruning approach
    2. **Set Budget** - Define target token count
    3. **Add Context** - Load or generate context items
    4. **Execute** - Run pruning algorithm
    5. **Review** - Analyze results and pruned context
    
    ## Use Cases
    
    ✅ **LLM Context Optimization** - Fit context within model limits  
    ✅ **Cost Reduction** - Minimize token usage and costs  
    ✅ **Performance** - Reduce processing time with smaller contexts  
    ✅ **Focus** - Keep only most relevant information  
    
    ## Tips
    
    💡 Use **Relevance** for query-specific tasks  
    💡 Use **Recency** for real-time monitoring  
    💡 Use **Hybrid** when unsure (balanced approach)  
    💡 Use **Importance** for priority-driven workflows  
    💡 Set realistic token budgets (50-80% of original)  
    💡 Review pruned items to ensure quality  
    
    ## Metrics
    
    - **Pruning Ratio**: Percentage of tokens kept
    - **Items Removed**: Count of pruned items
    - **Token Count**: Final token usage
    - **Score Distributions**: Quality of kept items
    """)


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    render()

