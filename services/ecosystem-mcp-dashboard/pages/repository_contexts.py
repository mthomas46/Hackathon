"""
Repository Contexts Dashboard (Week 3, Day 3)

Dashboard page for managing and exploring repository contexts:
- List all ingested repositories
- View hierarchical context structure
- Display repository summaries
- Show technology stacks and API endpoints
- Context selector for RAG queries
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# from dashboard_views.api_client import get_api_client  # Module not available


def show(api_base_url: str):
    """Entry point for dashboard integration."""
    render_repository_contexts()


def render_repository_contexts():
    """Render repository contexts page."""
    st.title("📚 Repository Contexts")
    st.markdown("Explore hierarchical contexts and repository structures")
    
    # Get API client
    api_client = get_api_client()
    
    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "🗂️ All Repositories",
        "🔍 Context Explorer",
        "📊 Context Analytics"
    ])
    
    # Tab 1: All Repositories
    with tab1:
        render_repositories_tab(api_client)
    
    # Tab 2: Context Explorer
    with tab2:
        render_context_explorer_tab(api_client)
    
    # Tab 3: Context Analytics
    with tab3:
        render_context_analytics_tab(api_client)


def render_repositories_tab(api_client):
    """Render repositories overview tab."""
    st.subheader("🗂️ Ingested Repositories")
    
    try:
        # Get all repositories (would need an endpoint for this)
        # For now, we'll use a sample repository
        
        st.info("ℹ️ Select a repository to explore its contexts")
        
        # Repository selector
        repo_id = st.text_input(
            "Repository ID",
            value="ecosystem-mcp",
            help="Enter repository ID to explore"
        )
        
        if st.button("🔍 Load Repository", type="primary"):
            with st.spinner(f"Loading contexts for {repo_id}..."):
                # Get contexts for repository
                response = api_client.get(f"/query/contexts/{repo_id}")
                
                if response.status_code == 200:
                    contexts = response.json()
                    
                    if not contexts:
                        st.warning(f"No contexts found for repository: {repo_id}")
                        return
                    
                    st.success(f"✅ Loaded {len(contexts)} contexts")
                    
                    # Display repository summary
                    st.divider()
                    st.subheader("📊 Repository Summary")
                    
                    # Count contexts by level
                    level_counts = {}
                    for ctx in contexts:
                        level = ctx.get("level", "UNKNOWN")
                        level_counts[level] = level_counts.get(level, 0) + 1
                    
                    # Display metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Contexts", len(contexts))
                    
                    with col2:
                        st.metric("Services", level_counts.get("SERVICE", 0))
                    
                    with col3:
                        st.metric("Modules", level_counts.get("MODULE", 0))
                    
                    with col4:
                        st.metric("Components", level_counts.get("COMPONENT", 0))
                    
                    # Display context tree
                    st.divider()
                    st.subheader("🌳 Context Hierarchy")
                    
                    # Group by level
                    root_contexts = [c for c in contexts if c.get("level") == "ROOT"]
                    service_contexts = [c for c in contexts if c.get("level") == "SERVICE"]
                    module_contexts = [c for c in contexts if c.get("level") == "MODULE"]
                    component_contexts = [c for c in contexts if c.get("level") == "COMPONENT"]
                    
                    # Display tree
                    if root_contexts:
                        for root_ctx in root_contexts:
                            with st.expander(f"🔷 ROOT: {root_ctx.get('name', 'Unknown')}", expanded=True):
                                st.markdown(f"**Path:** `{root_ctx.get('full_path', 'N/A')}`")
                                st.markdown(f"**Files:** {root_ctx.get('level_files', 0):,}")
                                st.markdown(f"**Technologies:** {', '.join(root_ctx.get('technologies', []))}")
                    
                    if service_contexts:
                        st.markdown("### 🔸 Services")
                        for svc_ctx in service_contexts[:10]:  # Show first 10
                            with st.expander(f"{svc_ctx.get('name', 'Unknown')}"):
                                st.markdown(f"**Path:** `{svc_ctx.get('full_path', 'N/A')}`")
                                st.markdown(f"**Files:** {svc_ctx.get('level_files', 0)}")
                                st.markdown(f"**Language:** {svc_ctx.get('primary_language', 'Unknown')}")
                    
                    # Context distribution chart
                    st.divider()
                    st.subheader("📊 Context Distribution")
                    
                    fig = px.pie(
                        values=list(level_counts.values()),
                        names=list(level_counts.keys()),
                        title="Contexts by Level"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Technology breakdown
                    st.divider()
                    st.subheader("💻 Technology Stack")
                    
                    # Collect all technologies
                    all_techs = []
                    for ctx in contexts:
                        all_techs.extend(ctx.get("technologies", []))
                    
                    if all_techs:
                        tech_counts = {}
                        for tech in all_techs:
                            tech_counts[tech] = tech_counts.get(tech, 0) + 1
                        
                        # Sort by frequency
                        sorted_techs = sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                        
                        fig = px.bar(
                            x=[t[1] for t in sorted_techs],
                            y=[t[0] for t in sorted_techs],
                            orientation='h',
                            title="Top 10 Technologies",
                            labels={'x': 'Count', 'y': 'Technology'}
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                else:
                    st.error(f"❌ Failed to load contexts (HTTP {response.status_code})")
    
    except Exception as e:
        st.error(f"❌ Error loading repositories: {str(e)}")


def render_context_explorer_tab(api_client):
    """Render context explorer tab."""
    st.subheader("🔍 Context Explorer")
    
    st.markdown("""
    Explore individual contexts in detail:
    - View context metadata
    - See file lists
    - Explore technology stack
    - Query within context
    """)
    
    # Context ID input
    context_id = st.text_input(
        "Context ID",
        value="",
        help="Enter context ID to explore"
    )
    
    if context_id and st.button("🔍 Load Context", type="primary"):
        with st.spinner(f"Loading context {context_id}..."):
            try:
                # Get context summary
                response = api_client.get(f"/query/context/{context_id}/summary")
                
                if response.status_code == 200:
                    summary = response.json()
                    
                    st.success("✅ Context loaded successfully")
                    
                    # Display context info
                    st.divider()
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"## {summary.get('name', 'Unknown')}")
                        st.markdown(f"**Level:** {summary.get('level', 'Unknown')}")
                        st.markdown(f"**Full Path:** `{summary.get('full_path', 'N/A')}`")
                        st.markdown(f"**Description:** {summary.get('description', 'No description')}")
                    
                    with col2:
                        st.metric("Files", f"{summary.get('file_count', 0):,}")
                        st.metric("Lines of Code", f"{summary.get('lines_of_code', 0):,}")
                        st.metric("Children", summary.get('children_count', 0))
                    
                    # Technologies
                    st.divider()
                    st.subheader("💻 Technologies")
                    
                    techs = summary.get('technologies', [])
                    if techs:
                        cols = st.columns(min(len(techs), 5))
                        for idx, tech in enumerate(techs[:5]):
                            with cols[idx]:
                                st.info(f"🔹 {tech}")
                    else:
                        st.info("No technologies detected")
                    
                    # Services
                    if summary.get('services'):
                        st.divider()
                        st.subheader("🔧 Services")
                        for service in summary.get('services', []):
                            st.markdown(f"- {service}")
                    
                    # Quick query
                    st.divider()
                    st.subheader("🔍 Query This Context")
                    
                    query = st.text_input(
                        "Question",
                        value="",
                        placeholder="Ask a question about this context..."
                    )
                    
                    if query and st.button("🚀 Query"):
                        with st.spinner("Querying..."):
                            query_response = api_client.post(
                                "/query/context-aware",
                                json={
                                    "question": query,
                                    "context_id": context_id,
                                    "limit": 5
                                }
                            )
                            
                            if query_response.status_code == 200:
                                results = query_response.json()
                                
                                st.success(f"✅ Found {results.get('total', 0)} results")
                                
                                for idx, result in enumerate(results.get('results', []), 1):
                                    with st.expander(f"Result {idx} (Relevance: {result.get('relevance_score', 0):.2f})"):
                                        st.markdown(result.get('content', 'No content'))
                                        st.caption(f"Source: {result.get('metadata', {}).get('file', 'Unknown')}")
                            else:
                                st.error("❌ Query failed")
                
                elif response.status_code == 404:
                    st.error(f"❌ Context not found: {context_id}")
                else:
                    st.error(f"❌ Failed to load context (HTTP {response.status_code})")
            
            except Exception as e:
                st.error(f"❌ Error loading context: {str(e)}")


def render_context_analytics_tab(api_client):
    """Render context analytics tab."""
    st.subheader("📊 Context Analytics")
    
    st.markdown("""
    Analytics and insights about repository contexts:
    - Context size distribution
    - Technology adoption
    - Service complexity
    - Coverage metrics
    """)
    
    # Repository selector for analytics
    repo_id = st.text_input(
        "Repository ID (for analytics)",
        value="ecosystem-mcp",
        help="Enter repository ID for analytics"
    )
    
    if st.button("📊 Generate Analytics", type="primary"):
        with st.spinner("Generating analytics..."):
            try:
                # Get contexts
                response = api_client.get(f"/query/contexts/{repo_id}")
                
                if response.status_code == 200:
                    contexts = response.json()
                    
                    if not contexts:
                        st.warning("No contexts found")
                        return
                    
                    # Context size distribution
                    st.divider()
                    st.subheader("📏 Context Size Distribution")
                    
                    sizes = []
                    names = []
                    for ctx in contexts:
                        if ctx.get('level') in ['SERVICE', 'MODULE']:
                            sizes.append(ctx.get('level_files', 0))
                            names.append(ctx.get('name', 'Unknown'))
                    
                    if sizes:
                        fig = px.bar(
                            x=names[:20],
                            y=sizes[:20],
                            title="Context Size (Files) - Top 20",
                            labels={'x': 'Context', 'y': 'Files'}
                        )
                        fig.update_xaxis(tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Lines of code distribution
                    st.divider()
                    st.subheader("📝 Lines of Code Distribution")
                    
                    loc_data = []
                    for ctx in contexts:
                        if ctx.get('level') in ['SERVICE', 'MODULE'] and ctx.get('level_lines', 0) > 0:
                            loc_data.append({
                                'name': ctx.get('name', 'Unknown'),
                                'loc': ctx.get('level_lines', 0),
                                'level': ctx.get('level', 'Unknown')
                            })
                    
                    if loc_data:
                        df = pd.DataFrame(loc_data).sort_values('loc', ascending=False).head(15)
                        
                        fig = px.treemap(
                            df,
                            path=['level', 'name'],
                            values='loc',
                            title="Lines of Code by Context"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Language distribution
                    st.divider()
                    st.subheader("💬 Language Distribution")
                    
                    languages = {}
                    for ctx in contexts:
                        lang = ctx.get('primary_language')
                        if lang:
                            languages[lang] = languages.get(lang, 0) + 1
                    
                    if languages:
                        fig = px.pie(
                            values=list(languages.values()),
                            names=list(languages.keys()),
                            title="Primary Languages"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Summary stats
                    st.divider()
                    st.subheader("📈 Summary Statistics")
                    
                    total_files = sum(ctx.get('level_files', 0) for ctx in contexts)
                    total_loc = sum(ctx.get('level_lines', 0) for ctx in contexts)
                    avg_files_per_context = total_files / len(contexts) if contexts else 0
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Contexts", len(contexts))
                    
                    with col2:
                        st.metric("Total Files", f"{total_files:,}")
                    
                    with col3:
                        st.metric("Total LOC", f"{total_loc:,}")
                    
                    with col4:
                        st.metric("Avg Files/Context", f"{avg_files_per_context:.1f}")
                
                else:
                    st.error(f"❌ Failed to load contexts (HTTP {response.status_code})")
            
            except Exception as e:
                st.error(f"❌ Error generating analytics: {str(e)}")


# Main entry point
if __name__ == "__main__":
    render_repository_contexts()
else:
    render_repository_contexts()

