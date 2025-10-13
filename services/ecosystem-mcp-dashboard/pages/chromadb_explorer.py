"""
ChromaDB Explorer Page.

Provides tools to:
- View collections
- Explore documents and embeddings
- Search vectors
- Inspect metadata
- Test similarity search
"""

import streamlit as st
import httpx
import json
import os
from datetime import datetime


def show(api_base_url: str):
    """Show ChromaDB explorer page."""
    st.title("🔍 ChromaDB Explorer")
    
    st.markdown("""
    Explore the **vector database** powering the RAG system.
    
    View collections, documents, embeddings, and test semantic search.
    """)
    
    # ChromaDB Health Check
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 ChromaDB Status")
    
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    try:
        health_response = httpx.get(f"{api_base_url}/health", timeout=5.0)
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            components = health_data.get("components", {})
            chromadb_status = components.get("chromadb", {})
            
            status = chromadb_status.get("status", "unknown")
            message = chromadb_status.get("message", "No status available")
            response_time = chromadb_status.get("response_time_ms", 0)
            
            if status == "healthy":
                st.success(f"✅ ChromaDB is **{status}** - {message}")
                st.caption(f"Response time: {response_time:.2f}ms")
            elif status == "unhealthy":
                st.error(f"❌ ChromaDB is **{status}** - {message}")
            else:
                st.warning(f"⚠️ ChromaDB status: **{status}** - {message}")
        else:
            st.error(f"Failed to fetch health status: HTTP {health_response.status_code}")
    
    except Exception as e:
        st.error(f"Error checking ChromaDB health: {str(e)}")
    
    # Collections
    st.markdown("---")
    st.subheader("📚 Collections")
    
    try:
        # Fetch collection info from stats endpoint
        stats_response = httpx.get(f"{api_base_url}/api/v1/admin/stats", timeout=10.0)
        
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            documents_data = stats_data.get("documents", {})
            
            total_docs = documents_data.get("total", 0)
            total_embeddings = documents_data.get("embeddings", 0)
            
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.metric("Total Documents", f"{total_docs:,}")
            
            with metric_col2:
                st.metric("Total Embeddings", f"{total_embeddings:,}")
            
            with metric_col3:
                embedding_coverage = (total_embeddings / total_docs * 100) if total_docs > 0 else 0
                st.metric("Embedding Coverage", f"{embedding_coverage:.1f}%")
            
            # Collection details
            st.markdown("#### Collection: `ecosystem-mcp`")
            
            col_detail1, col_detail2 = st.columns(2)
            
            with col_detail1:
                st.markdown(f"""
                **Documents:** {total_docs:,}  
                **Vectors:** {total_embeddings:,}  
                **Embedding Model:** nomic-embed-text (768 dimensions)
                """)
            
            with col_detail2:
                st.markdown(f"""
                **Vector Store:** ChromaDB  
                **Distance Metric:** Cosine Similarity  
                **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """)
        
        else:
            st.warning("Could not fetch collection stats")
    
    except Exception as e:
        st.error(f"Error fetching collection info: {str(e)}")
    
    # Search Interface
    st.markdown("---")
    st.subheader("🔎 Semantic Search")
    
    st.markdown("""
    Test semantic search directly against ChromaDB. Enter a query to find similar documents.
    """)
    
    with st.form("chromadb_search_form"):
        search_query = st.text_area(
            "Search Query",
            placeholder="e.g., How does caching work?",
            height=100,
            help="Enter a natural language query to search for similar documents"
        )
        
        search_col1, search_col2 = st.columns(2)
        
        with search_col1:
            n_results = st.slider(
                "Number of Results",
                min_value=1,
                max_value=50,
                value=10,
                help="How many similar documents to return"
            )
        
        with search_col2:
            show_scores = st.checkbox(
                "Show Similarity Scores",
                value=True,
                help="Display cosine similarity scores for each result"
            )
        
        search_submitted = st.form_submit_button("🔍 Search", use_container_width=True)
    
    if search_submitted and search_query:
        with st.spinner("Searching ChromaDB..."):
            try:
                # Use the query endpoint to search
                query_response = httpx.post(
                    f"{api_base_url}/api/v1/query",
                    json={
                        "query": search_query,
                        "n_results": n_results
                    },
                    timeout=30.0
                )
                
                if query_response.status_code == 200:
                    query_data = query_response.json()
                    results = query_data.get("results", [])
                    
                    if results:
                        st.success(f"Found {len(results)} similar documents")
                        
                        # Display results
                        for i, result in enumerate(results, 1):
                            score = result.get("score", result.get("similarity", 0))
                            file_path = result.get("file_path", "Unknown")
                            content = result.get("content", "No content available")
                            metadata = result.get("metadata", {})
                            
                            with st.expander(f"**Result {i}:** {file_path[:80]}", expanded=(i <= 3)):
                                result_col1, result_col2 = st.columns([3, 1])
                                
                                with result_col1:
                                    st.markdown(f"**File:** `{file_path}`")
                                    if metadata:
                                        service = metadata.get("service", "N/A")
                                        file_type = metadata.get("file_type", "N/A")
                                        st.markdown(f"**Service:** {service} | **Type:** {file_type}")
                                
                                with result_col2:
                                    if show_scores:
                                        st.metric("Similarity", f"{score:.3f}")
                                
                                # Content preview
                                st.markdown("**Content:**")
                                preview = content[:500] + "..." if len(content) > 500 else content
                                st.text_area(
                                    "Content Preview",
                                    value=preview,
                                    height=150,
                                    disabled=True,
                                    key=f"chromadb_result_{i}",
                                    label_visibility="collapsed"
                                )
                                
                                # Metadata
                                if metadata:
                                    with st.expander("🔍 Full Metadata"):
                                        st.json(metadata)
                    else:
                        st.info("No results found for this query")
                
                else:
                    st.error(f"Search failed: HTTP {query_response.status_code}")
                    st.code(query_response.text)
            
            except httpx.TimeoutException:
                st.error("Search timed out. Try a simpler query or reduce the number of results.")
            except Exception as e:
                st.error(f"Search error: {str(e)}")
    
    # Vector Analysis
    st.markdown("---")
    st.subheader("📊 Vector Analysis")
    
    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs([
        "📈 Statistics",
        "🎯 Similarity Testing",
        "🔧 Advanced"
    ])
    
    with analysis_tab1:
        st.markdown("""
        ### Embedding Statistics
        
        **Model:** nomic-embed-text  
        **Dimensions:** 768  
        **Normalization:** L2 (unit vectors)  
        **Distance Metric:** Cosine Similarity
        
        **Coverage:**
        """)
        
        try:
            if total_docs > 0 and total_embeddings > 0:
                coverage_pct = (total_embeddings / total_docs * 100)
                st.progress(coverage_pct / 100)
                st.caption(f"{total_embeddings:,} / {total_docs:,} documents have embeddings ({coverage_pct:.1f}%)")
                
                if coverage_pct < 100:
                    missing = total_docs - total_embeddings
                    st.warning(f"⚠️ {missing:,} documents are missing embeddings")
                    st.caption("Run the embedding queue processor to generate missing embeddings")
            else:
                st.info("No document statistics available yet")
        except:
            st.info("Statistics will appear after documents are ingested")
    
    with analysis_tab2:
        st.markdown("""
        ### Test Similarity Between Queries
        
        Compare two queries to see how similar they are in the embedding space.
        """)
        
        with st.form("similarity_test_form"):
            query1 = st.text_input(
                "Query 1",
                placeholder="e.g., How does caching work?"
            )
            
            query2 = st.text_input(
                "Query 2",
                placeholder="e.g., Explain the cache system"
            )
            
            similarity_submitted = st.form_submit_button("🎯 Compare Similarity")
        
        if similarity_submitted and query1 and query2:
            st.info("""
            **Note:** Direct embedding comparison requires an API endpoint.
            
            For now, you can compare by:
            1. Searching with Query 1 and noting top results
            2. Searching with Query 2 and seeing if similar results appear
            3. Overlap in top results indicates semantic similarity
            """)
    
    with analysis_tab3:
        st.markdown("""
        ### Advanced Vector Operations
        
        **Available Operations:**
        
        1. **Batch Embedding Generation**
           - Generate embeddings for documents missing them
           - Available via: Embedding Queue Processor
        
        2. **Vector Search with Filters**
           - Filter by service, file type, date range
           - Available via: Enhanced Query API
        
        3. **Reindex Collection**
           - Rebuild vector index for optimal performance
           - Contact system administrator
        
        4. **Export Embeddings**
           - Export vectors for analysis or migration
           - Available via: API `/api/v1/embeddings/export`
        """)
        
        st.markdown("#### Collection Management")
        
        st.warning("""
        **⚠️ Destructive Operations**
        
        These operations modify the vector database and should be used carefully:
        - Clear all embeddings
        - Reset collection
        - Rebuild index
        
        Contact your system administrator before performing these operations.
        """)
    
    # Help & Documentation
    st.markdown("---")
    with st.expander("📚 ChromaDB Documentation"):
        st.markdown("""
        ### About ChromaDB
        
        ChromaDB is an open-source embedding database optimized for:
        - Storing and searching embeddings
        - Semantic similarity search
        - Fast vector operations
        - Metadata filtering
        
        ### How It's Used in This System
        
        1. **Document Ingestion:**
           - Documents are processed and split into chunks
           - Each chunk is embedded using nomic-embed-text model
           - Embeddings stored in ChromaDB with metadata
        
        2. **RAG Queries:**
           - User query is embedded
           - ChromaDB finds most similar document chunks
           - Retrieved chunks used as context for LLM
        
        3. **Semantic Search:**
           - Natural language queries work out of the box
           - No exact keyword matching needed
           - Understands intent and meaning
        
        ### Key Concepts
        
        **Embedding:** A vector representation of text (768 dimensions)  
        **Cosine Similarity:** Measures angle between vectors (0-1)  
        **Collection:** A group of documents and their embeddings  
        **Metadata:** Additional info stored with each embedding
        
        ### Performance
        
        - **Search Speed:** O(log n) with HNSW index
        - **Embedding Time:** ~50-100ms per document chunk
        - **Storage:** ~3KB per embedding (768 float32)
        """)
    
    with st.expander("🔧 Troubleshooting"):
        st.markdown("""
        ### Common Issues
        
        **No results found:**
        - Ensure documents have been ingested
        - Check that embeddings have been generated
        - Try a simpler or more specific query
        
        **Slow search:**
        - Reduce number of results
        - Check ChromaDB health status
        - Verify system resources
        
        **Missing embeddings:**
        - Run embedding queue processor
        - Check ingestion logs
        - Verify embedding model is loaded
        
        **Connection errors:**
        - Check ChromaDB status in Health page
        - Verify Docker containers are running
        - Check network connectivity
        """)


if __name__ == "__main__":
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    show(api_base_url)

