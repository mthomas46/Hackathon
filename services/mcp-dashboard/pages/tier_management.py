"""
Tier Management UI Page.

Provides interface for:
- Creating and managing tiers
- Viewing tier hierarchy
- Managing tier relationships
- Tier statistics and monitoring
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Add services directory to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_tier_manager.src.tier_manager import (
    TierManager,
    TierConfig,
    TierType,
    InheritancePolicy
)


# ============================================================================
# Page Configuration
# ============================================================================

def render():
    """Render the Tier Management page."""
    
    st.title("🗂️ Tier Management")
    st.markdown("""
    Manage the 5-tier hierarchical MCP system:
    **Ecosystem** → **Company** → **Team** → **Project** → **Client**
    """)
    
    # Initialize session state
    if 'tier_manager' not in st.session_state:
        st.session_state['tier_manager'] = TierManager()
    
    tier_manager = st.session_state['tier_manager']
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "➕ Create Tier",
        "🔗 Relationships",
        "📈 Statistics",
        "🔍 Query"
    ])
    
    with tab1:
        render_overview(tier_manager)
    
    with tab2:
        render_create_tier(tier_manager)
    
    with tab3:
        render_relationships(tier_manager)
    
    with tab4:
        render_statistics(tier_manager)
    
    with tab5:
        render_query(tier_manager)


# ============================================================================
# Overview Section
# ============================================================================

def render_overview(tier_manager: TierManager):
    """Render tier overview."""
    
    st.header("📊 Tier System Overview")
    
    # Get all tiers
    all_tiers = tier_manager.get_all_tiers_overview()
    
    if not all_tiers:
        st.info("No tiers created yet. Create your first tier in the 'Create Tier' tab!")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    tier_counts = {}
    for tier in all_tiers:
        tier_type = tier["tier_type"]
        tier_counts[tier_type] = tier_counts.get(tier_type, 0) + 1
    
    with col1:
        st.metric("Total Tiers", len(all_tiers))
    with col2:
        st.metric("Ecosystems", tier_counts.get("ecosystem", 0))
    with col3:
        st.metric("Projects", tier_counts.get("project", 0))
    with col4:
        st.metric("Clients", tier_counts.get("client", 0))
    
    # Hierarchy visualization
    st.subheader("🌳 Tier Hierarchy")
    
    # Group by tier type
    tiers_by_type = {}
    for tier in all_tiers:
        tier_type = tier["tier_type"]
        if tier_type not in tiers_by_type:
            tiers_by_type[tier_type] = []
        tiers_by_type[tier_type].append(tier)
    
    # Display hierarchy
    tier_order = ["ecosystem", "company", "team", "project", "client"]
    
    for tier_type in tier_order:
        if tier_type in tiers_by_type:
            st.markdown(f"### 📁 {tier_type.title()} Tier")
            for tier in tiers_by_type[tier_type]:
                with st.expander(f"{tier['name']} ({tier['knowledge_count']} items)"):
                    st.write(f"**ID:** {tier['tier_id']}")
                    st.write(f"**Status:** {tier['status']}")
                    st.write(f"**Created:** {tier['created_at']}")
                    st.write(f"**Knowledge Items:** {tier['knowledge_count']}")


# ============================================================================
# Create Tier Section
# ============================================================================

def render_create_tier(tier_manager: TierManager):
    """Render tier creation interface."""
    
    st.header("➕ Create New Tier")
    
    # Tier configuration form
    with st.form("create_tier_form"):
        tier_name = st.text_input(
            "Tier Name",
            placeholder="e.g., my_project, user_session"
        )
        
        tier_type = st.selectbox(
            "Tier Type",
            options=["client", "project", "team", "company", "ecosystem"],
            format_func=lambda x: x.title()
        )
        
        # Parent tier selection
        all_tiers = tier_manager.get_all_tiers_overview()
        parent_options = ["None"] + [
            f"{t['name']} ({t['tier_type']})"
            for t in all_tiers
        ]
        
        parent_selection = st.selectbox(
            "Parent Tier (Optional)",
            options=parent_options
        )
        
        # Advanced options
        with st.expander("⚙️ Advanced Options"):
            max_size_mb = st.number_input(
                "Max Size (MB)",
                min_value=1,
                max_value=10000,
                value=1000
            )
            
            retention_days = st.number_input(
                "Retention Days",
                min_value=1,
                max_value=365,
                value=90
            )
            
            inheritance_policy = st.selectbox(
                "Inheritance Policy",
                options=["auto", "explicit_only", "selective"],
                format_func=lambda x: x.replace('_', ' ').title()
            )
        
        submit_button = st.form_submit_button("Create Tier", type="primary")
        
        if submit_button:
            if not tier_name:
                st.error("Please provide a tier name")
            else:
                try:
                    # Get parent tier ID if selected
                    parent_id = None
                    if parent_selection != "None":
                        parent_name = parent_selection.split(" (")[0]
                        for t in all_tiers:
                            if t['name'] == parent_name:
                                parent_id = t['tier_id']
                                break
                    
                    # Create config
                    config = TierConfig(
                        name=tier_name,
                        tier_type=TierType(tier_type),
                        parent_tier_id=parent_id,
                        max_size_mb=max_size_mb,
                        retention_days=retention_days,
                        inheritance_policy=InheritancePolicy(inheritance_policy)
                    )
                    
                    # Create tier
                    tier = tier_manager.create_tier(config)
                    
                    st.success(f"✅ Tier '{tier_name}' created successfully!")
                    st.json({
                        "tier_id": tier.tier_id,
                        "name": tier.name,
                        "type": tier.tier_type.value,
                        "status": tier.status
                    })
                    
                except ValueError as e:
                    st.error(f"❌ Error: {str(e)}")


# ============================================================================
# Relationships Section
# ============================================================================

def render_relationships(tier_manager: TierManager):
    """Render tier relationships."""
    
    st.header("🔗 Tier Relationships")
    
    all_tiers = tier_manager.get_all_tiers_overview()
    
    if not all_tiers:
        st.info("No tiers to display relationships")
        return
    
    # Build relationship tree
    st.subheader("🌳 Hierarchy Tree")
    
    # Find root tiers (no parent)
    root_tiers = [
        t for t in all_tiers
        if tier_manager.get_tier(t['tier_id']).parent_tier_id is None
    ]
    
    for root in root_tiers:
        render_tier_tree(tier_manager, root['tier_id'], level=0)
    
    # Inheritance operations
    st.subheader("📥 Inheritance Operations")
    
    tier_options = [f"{t['name']} ({t['tier_type']})" for t in all_tiers]
    selected_tier = st.selectbox("Select Tier", options=tier_options)
    
    if selected_tier:
        tier_name = selected_tier.split(" (")[0]
        tier_id = next(t['tier_id'] for t in all_tiers if t['name'] == tier_name)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Inherit from Parent"):
                try:
                    result = tier_manager.inherit_from_parent(tier_id)
                    st.success(f"✅ Inherited {result.items_inherited} items!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col2:
            max_levels = st.number_input("Max Levels", 1, 5, 3)
            if st.button("Cascading Inherit"):
                try:
                    result = tier_manager.inherit_cascading(tier_id, max_levels)
                    st.success(f"✅ Inherited {result.items_inherited} items from {result.levels_inherited} levels!")
                except Exception as e:
                    st.error(f"Error: {str(e)}")


def render_tier_tree(tier_manager: TierManager, tier_id: str, level: int):
    """Render tier tree recursively."""
    tier = tier_manager.get_tier(tier_id)
    if not tier:
        return
    
    indent = "    " * level
    knowledge_count = len(tier_manager.get_tier_knowledge(tier_id))
    
    st.markdown(f"{indent}📁 **{tier.name}** ({tier.tier_type.value}) - {knowledge_count} items")
    
    # Get children
    children = tier_manager.get_tier_children(tier_id)
    for child_id in children:
        render_tier_tree(tier_manager, child_id, level + 1)


# ============================================================================
# Statistics Section
# ============================================================================

def render_statistics(tier_manager: TierManager):
    """Render tier statistics."""
    
    st.header("📈 Tier Statistics")
    
    all_tiers = tier_manager.get_all_tiers_overview()
    
    if not all_tiers:
        st.info("No tiers to display statistics")
        return
    
    # Overall statistics
    st.subheader("📊 Overall Statistics")
    
    total_knowledge = sum(t['knowledge_count'] for t in all_tiers)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tiers", len(all_tiers))
    with col2:
        st.metric("Total Knowledge Items", total_knowledge)
    with col3:
        avg_knowledge = total_knowledge / len(all_tiers) if all_tiers else 0
        st.metric("Avg Items per Tier", f"{avg_knowledge:.1f}")
    
    # Knowledge distribution by tier type
    st.subheader("📊 Knowledge Distribution")
    
    tier_type_data = {}
    for tier in all_tiers:
        tier_type = tier['tier_type']
        if tier_type not in tier_type_data:
            tier_type_data[tier_type] = 0
        tier_type_data[tier_type] += tier['knowledge_count']
    
    if tier_type_data:
        fig = px.pie(
            values=list(tier_type_data.values()),
            names=[t.title() for t in tier_type_data.keys()],
            title="Knowledge Items by Tier Type"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed tier stats
    st.subheader("📋 Detailed Tier Statistics")
    
    for tier in all_tiers:
        tier_id = tier['tier_id']
        try:
            stats = tier_manager.get_tier_stats(tier_id)
            
            with st.expander(f"📁 {tier['name']} ({tier['tier_type']})"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Knowledge Count", stats.knowledge_count)
                with col2:
                    st.metric("Size (MB)", f"{stats.size_mb:.2f}")
                with col3:
                    st.metric("Type", stats.tier_type.value.title())
                
                st.write(f"**Created:** {stats.created_at.strftime('%Y-%m-%d %H:%M')}")
                st.write(f"**Last Updated:** {stats.last_updated.strftime('%Y-%m-%d %H:%M')}")
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")


# ============================================================================
# Query Section
# ============================================================================

def render_query(tier_manager: TierManager):
    """Render tier query interface."""
    
    st.header("🔍 Query Tiers")
    
    all_tiers = tier_manager.get_all_tiers_overview()
    
    if not all_tiers:
        st.info("Create tiers first to use query functionality")
        return
    
    # Query form
    tier_options = [f"{t['name']} ({t['tier_type']})" for t in all_tiers]
    selected_tier = st.selectbox("Starting Tier", options=tier_options)
    
    query = st.text_input("Search Query", placeholder="Enter search terms...")
    
    col1, col2 = st.columns(2)
    with col1:
        max_tiers = st.slider("Max Tiers to Search", 1, 5, 3)
    with col2:
        max_tokens = st.slider("Max Tokens", 500, 8000, 2000)
    
    if st.button("🔍 Search", type="primary"):
        if not query:
            st.warning("Please enter a search query")
        else:
            tier_name = selected_tier.split(" (")[0]
            tier_id = next(t['tier_id'] for t in all_tiers if t['name'] == tier_name)
            
            try:
                result = tier_manager.cascade_query(
                    query=query,
                    starting_tier_id=tier_id,
                    max_tiers=max_tiers,
                    max_tokens=max_tokens
                )
                
                # Display results
                st.success(f"✅ Found {len(result.results)} results from {result.tiers_searched} tiers")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Results", len(result.results))
                with col2:
                    st.metric("Total Tokens", result.total_tokens)
                
                # Results by tier
                st.subheader("📋 Results")
                
                tiers_with_results = {}
                for r in result.results:
                    if r.tier_type not in tiers_with_results:
                        tiers_with_results[r.tier_type] = []
                    tiers_with_results[r.tier_type].append(r)
                
                for tier_type, results in tiers_with_results.items():
                    st.markdown(f"### 📁 {tier_type.value.title()} Tier")
                    for r in results:
                        with st.expander(f"Relevance: {r.relevance:.2f} | Tokens: {r.token_count}"):
                            st.markdown(r.content)
                            if r.metadata:
                                st.json(r.metadata)
            
            except Exception as e:
                st.error(f"Query error: {str(e)}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    render()

