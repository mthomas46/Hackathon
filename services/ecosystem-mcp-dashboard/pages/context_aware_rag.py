"""
Context-Aware RAG Query Dashboard (Week 3, Day 3)

Enhanced RAG query page with context filtering:
- Repository context selector
- Hierarchical level filtering
- Technology stack filtering
- Service filtering
- Language filtering
- Time range filtering
- Model selection
"""

import streamlit as st
from datetime import datetime, timedelta
import time

from dashboard_views.api_client import get_api_client


def show(api_base_url: str):
    """Entry point for dashboard integration."""
    render_context_aware_rag()


def render_context_aware_rag():
    """Render context-aware RAG query page."""
    st.title("🔍 Context-Aware RAG Query")
    st.markdown("Query documents with hierarchical context filtering")
    
    # Get API client
    api_client = get_api_client()
    
    # Query form
    with st.form("context_aware_query_form"):
        # Question input
        question = st.text_area(
            "❓ Question",
            value="",
            placeholder="Ask a question about your codebase...",
            height=100,
            help="Enter your question. Results will be filtered by selected contexts."
        )
        
        # Filters section
        st.divider()
        st.subheader("🎯 Filters")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Repository filter
            repo_id = st.text_input(
                "Repository ID",
                value="",
                placeholder="e.g., ecosystem-mcp",
                help="Filter by repository"
            )
            
            # Context ID filter
            context_id = st.text_input(
                "Context ID",
                value="",
                placeholder="e.g., service-ingestion",
                help="Filter by specific hierarchical context"
            )
            
            # Context level filter
            context_level = st.selectbox(
                "Context Level",
                options=["", "ROOT", "SERVICE", "MODULE", "COMPONENT"],
                index=0,
                help="Filter by hierarchical level"
            )
            
            # Service filter
            service_filter = st.text_input(
                "Service Name",
                value="",
                placeholder="e.g., api-service",
                help="Filter by service name"
            )
        
        with col2:
            # Technology filter
            tech_filter = st.multiselect(
                "Technology Stack",
                options=["python", "javascript", "typescript", "fastapi", "react", "docker", "postgres", "redis"],
                default=[],
                help="Filter by technologies (OR logic)"
            )
            
            # Language filter
            language_filter = st.selectbox(
                "Programming Language",
                options=["", "python", "javascript", "typescript", "java", "go", "rust"],
                index=0,
                help="Filter by programming language"
            )
            
            # Time range filter
            time_range_hours = st.selectbox(
                "Time Range",
                options=[None, 1, 6, 24, 168, 720],
                format_func=lambda x: "All time" if x is None else f"Last {x} hours" if x < 168 else f"Last {x//24} days",
                index=0,
                help="Only include recent documents"
            )
            
            # Result limit
            limit = st.slider(
                "Max Results",
                min_value=1,
                max_value=50,
                value=10,
                help="Maximum number of results to return"
            )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Query", type="primary", use_container_width=True)
    
    # Process query
    if submitted:
        if not question:
            st.error("❌ Please enter a question")
            return
        
        with st.spinner("🔍 Searching with context filters..."):
            try:
                # Build request
                request_data = {
                    "question": question,
                    "limit": limit
                }
                
                # Add filters if provided
                if repo_id:
                    request_data["repo_id"] = repo_id
                if context_id:
                    request_data["context_id"] = context_id
                if context_level:
                    request_data["context_level"] = context_level
                if service_filter:
                    request_data["service_filter"] = service_filter
                if tech_filter:
                    request_data["tech_filter"] = tech_filter
                if language_filter:
                    request_data["language_filter"] = language_filter
                if time_range_hours:
                    request_data["time_range_hours"] = time_range_hours
                
                # Execute query
                response = api_client.post(
                    "/query/context-aware",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display results
                    st.success(f"✅ Found {result.get('total', 0)} results")
                    
                    # Show applied filters
                    st.divider()
                    st.subheader("🎯 Applied Filters")
                    
                    filters = result.get('filters', {})
                    filter_cols = st.columns(4)
                    
                    with filter_cols[0]:
                        if filters.get('repo_id'):
                            st.info(f"📦 Repo: {filters['repo_id']}")
                    
                    with filter_cols[1]:
                        if filters.get('context_level'):
                            st.info(f"🔷 Level: {filters['context_level']}")
                    
                    with filter_cols[2]:
                        if filters.get('tech_stack'):
                            st.info(f"💻 Tech: {', '.join(filters['tech_stack'][:2])}")
                    
                    with filter_cols[3]:
                        if filters.get('language'):
                            st.info(f"🔤 Lang: {filters['language']}")
                    
                    # Show context info if available
                    if result.get('context_info'):
                        st.divider()
                        st.subheader("📍 Context Information")
                        
                        ctx_info = result['context_info']
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Context Name", ctx_info.get('name', 'N/A'))
                        
                        with col2:
                            st.metric("Level", ctx_info.get('level', 'N/A'))
                        
                        with col3:
                            st.metric("Files", ctx_info.get('file_count', 0))
                        
                        with col4:
                            if ctx_info.get('full_path'):
                                st.caption(f"Path: `{ctx_info['full_path']}`")
                    
                    # Display results
                    st.divider()
                    st.subheader("📄 Results")
                    
                    for idx, res in enumerate(result.get('results', []), 1):
                        with st.expander(
                            f"Result {idx} - Relevance: {res.get('relevance_score', 0):.3f}",
                            expanded=(idx == 1)
                        ):
                            # Display content
                            st.markdown(res.get('content', 'No content'))
                            
                            # Display metadata
                            st.divider()
                            
                            meta_col1, meta_col2, meta_col3 = st.columns(3)
                            
                            with meta_col1:
                                st.caption(f"**Vector Score:** {res.get('vector_score', 0):.3f}")
                            
                            with meta_col2:
                                st.caption(f"**Keyword Score:** {res.get('keyword_score', 0):.3f}")
                            
                            with meta_col3:
                                metadata = res.get('metadata', {})
                                if metadata.get('file'):
                                    st.caption(f"**File:** `{metadata['file']}`")
                            
                            # Display context if available
                            if res.get('context'):
                                st.caption(f"**Context:** {res['context'].get('name', 'N/A')} ({res['context'].get('level', 'N/A')})")
                
                elif response.status_code == 400:
                    st.error(f"❌ Invalid request: {response.json().get('detail', 'Unknown error')}")
                else:
                    st.error(f"❌ Query failed (HTTP {response.status_code})")
            
            except Exception as e:
                st.error(f"❌ Error executing query: {str(e)}")
    
    # Example queries
    st.divider()
    st.subheader("💡 Example Queries")
    
    examples = [
        {
            "title": "Service-Specific Query",
            "question": "How does authentication work?",
            "context_level": "SERVICE",
            "service_filter": "api-service"
        },
        {
            "title": "Technology-Specific Query",
            "question": "Show me FastAPI endpoints",
            "tech_filter": ["python", "fastapi"]
        },
        {
            "title": "Recent Changes",
            "question": "What changed recently?",
            "time_range_hours": 24
        },
        {
            "title": "Language-Specific Query",
            "question": "Show Python error handling",
            "language_filter": "python"
        }
    ]
    
    cols = st.columns(2)
    for idx, example in enumerate(examples):
        with cols[idx % 2]:
            with st.expander(f"📝 {example['title']}"):
                st.code(f"Question: {example['question']}", language="text")
                for key, value in example.items():
                    if key != 'title' and key != 'question':
                        st.caption(f"**{key}:** {value}")


# Main entry point
if __name__ == "__main__":
    render_context_aware_rag()
else:
    render_context_aware_rag()

