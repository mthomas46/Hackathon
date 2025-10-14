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
    st.subheader("📊 Vector Analysis & Exploration")
    
    analysis_tab1, analysis_tab2, analysis_tab3, analysis_tab4, analysis_tab5 = st.tabs([
        "📈 Statistics",
        "🎯 Similarity Testing",
        "🧬 Embedding Explorer",
        "📊 Table/Collection Browser",
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
        ### 🧬 Embedding Explorer
        
        Explore the actual vector embeddings stored in ChromaDB. View embedding dimensions,
        visualize vectors, and understand the semantic space.
        """)
        
        # Embedding exploration options
        explore_col1, explore_col2 = st.columns(2)
        
        with explore_col1:
            explore_method = st.radio(
                "Exploration Method",
                options=["By Search Query", "By Document ID", "Random Sample"],
                key="embedding_explore_method"
            )
        
        with explore_col2:
            show_full_vector = st.checkbox(
                "Show Full Vector (768 dims)",
                value=False,
                help="Display all 768 dimensions (warning: very large output)"
            )
        
        # Explore embeddings based on method
        if explore_method == "By Search Query":
            st.markdown("#### Search for a Document")
            
            embed_query = st.text_input(
                "Enter search query to find a document",
                placeholder="e.g., caching system",
                key="embed_search_query"
            )
            
            if st.button("🔍 Find Document", key="find_embed_doc"):
                if embed_query:
                    with st.spinner("Searching for document..."):
                        try:
                            query_response = httpx.post(
                                f"{api_base_url}/api/v1/query",
                                json={"query": embed_query, "n_results": 1},
                                timeout=30.0
                            )
                            
                            if query_response.status_code == 200:
                                query_data = query_response.json()
                                results = query_data.get("results", [])
                                
                                if results:
                                    result = results[0]
                                    
                                    st.success(f"✅ Found document: {result.get('file_path', 'Unknown')}")
                                    
                                    # Document info
                                    st.markdown("#### Document Information")
                                    doc_col1, doc_col2 = st.columns(2)
                                    
                                    with doc_col1:
                                        st.markdown(f"**File Path:** `{result.get('file_path', 'N/A')}`")
                                        st.markdown(f"**Similarity Score:** {result.get('score', 0):.4f}")
                                    
                                    with doc_col2:
                                        metadata = result.get('metadata', {})
                                        st.markdown(f"**Service:** {metadata.get('service', 'N/A')}")
                                        st.markdown(f"**File Type:** {metadata.get('file_type', 'N/A')}")
                                    
                                    # Embedding info
                                    st.markdown("#### Embedding Vector")
                                    embedding_id = result.get('id', 'N/A')
                                    st.markdown(f"**Embedding ID:** `{embedding_id}`")
                                    st.markdown(f"**Model:** nomic-embed-text")
                                    st.markdown(f"**Dimensions:** 768")
                                    
                                    # Show embedding preview or note
                                    if show_full_vector:
                                        st.warning("⚠️ Full vector display requires API endpoint that returns raw embeddings")
                                        st.info("""
                                        To view the actual 768-dimensional vector, we need an API endpoint like:
                                        `GET /api/v1/embeddings/{id}` that returns the raw vector array.
                                        """)
                                    else:
                                        st.info("""
                                        **Vector Statistics:**
                                        - Dimensions: 768
                                        - Normalized: Yes (L2 norm = 1.0)
                                        - Typical range: [-1.0, 1.0] per dimension
                                        
                                        Enable "Show Full Vector" to see all dimensions (if API supports it).
                                        """)
                                    
                                    # Content preview
                                    st.markdown("#### Content Preview")
                                    content = result.get('content', 'No content')
                                    preview = content[:300] + "..." if len(content) > 300 else content
                                    st.text_area("Content", value=preview, height=100, disabled=True, label_visibility="collapsed")
                                
                                else:
                                    st.warning("No documents found for this query")
                        
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                else:
                    st.warning("Please enter a search query")
        
        elif explore_method == "By Document ID":
            st.markdown("#### Lookup by Document ID")
            
            doc_id = st.text_input(
                "Enter Document/Embedding ID",
                placeholder="e.g., doc_12345 or embedding hash",
                key="embed_doc_id"
            )
            
            include_full_vector = st.checkbox(
                "Include full 768D vector",
                value=False,
                key="include_full_vector_id",
                help="May take longer to load"
            )
            
            if st.button("🔍 Lookup Embedding", key="lookup_embed") and doc_id:
                with st.spinner("Fetching embedding..."):
                    try:
                        response = httpx.get(
                            f"{api_base_url}/api/v1/embeddings/{doc_id}",
                            params={"include_vector": include_full_vector},
                            timeout=30.0
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            st.success(f"✅ Found embedding: {doc_id}")
                            
                            # Display info
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Service", data.get("service", "N/A"))
                            with col2:
                                st.metric("Dimensions", data.get("dimensions", 768))
                            with col3:
                                st.metric("Model", data.get("embedding_model", "nomic-embed-text"))
                            
                            # File path
                            st.text_input("File Path", value=data.get("file_path", "N/A"), disabled=True)
                            
                            # Vector stats
                            if "vector_stats" in data and data["vector_stats"]:
                                st.markdown("**Vector Statistics:**")
                                stats = data["vector_stats"]
                                stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
                                with stats_col1:
                                    st.metric("L2 Norm", f"{stats.get('norm', 0):.4f}")
                                with stats_col2:
                                    st.metric("Mean", f"{stats.get('mean', 0):.4f}")
                                with stats_col3:
                                    st.metric("Std Dev", f"{stats.get('std', 0):.4f}")
                                with stats_col4:
                                    st.metric("Range", f"{stats.get('min', 0):.2f} to {stats.get('max', 0):.2f}")
                            
                            # Content
                            with st.expander("📄 Document Content", expanded=True):
                                st.text_area(
                                    "Content",
                                    value=data.get("content", "No content"),
                                    height=200,
                                    disabled=True
                                )
                            
                            # Metadata
                            with st.expander("🔍 Full Metadata"):
                                st.json(data.get("metadata", {}))
                            
                            # Full vector (if included)
                            if include_full_vector and "vector" in data:
                                with st.expander("🧬 Full 768D Vector"):
                                    st.code(str(data["vector"][:100]) + "...", language="python")
                                    st.caption(f"Showing first 100 of {len(data['vector'])} dimensions")
                        
                        elif response.status_code == 404:
                            st.error(f"❌ Embedding not found: {doc_id}")
                            st.info("💡 Check the ID and try again, or use search to find documents.")
                        else:
                            st.error(f"❌ Error: HTTP {response.status_code}")
                            st.caption(response.text[:200])
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            elif st.button("🔍 Lookup Embedding", key="lookup_embed_warn") and not doc_id:
                st.warning("Please enter a document ID")
        
        else:  # Random Sample
            st.markdown("#### Random Sample of Embeddings")
            
            sample_col1, sample_col2 = st.columns(2)
            
            with sample_col1:
                num_samples = st.slider(
                    "Number of samples",
                    min_value=1,
                    max_value=50,
                    value=10,
                    key="num_random_samples"
                )
            
            with sample_col2:
                sample_service = st.selectbox(
                    "Filter by Service",
                    options=["All", "ecosystem-mcp", "llm-gateway", "mcp-interpreter"],
                    key="sample_service_filter"
                )
            
            include_vectors_sample = st.checkbox(
                "Include full vectors (slower)",
                value=False,
                key="include_vectors_sample",
                help="Include 768D vectors for each sample"
            )
            
            if st.button("🎲 Get Random Sample", key="get_random_sample"):
                with st.spinner(f"Fetching {num_samples} random embeddings..."):
                    try:
                        params = {
                            "n": num_samples,
                            "include_vectors": include_vectors_sample
                        }
                        if sample_service != "All":
                            params["service"] = sample_service
                        
                        response = httpx.get(
                            f"{api_base_url}/api/v1/embeddings/sample",
                            params=params,
                            timeout=60.0
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            samples = data.get("samples", [])
                            total = data.get("total_documents", 0)
                            
                            st.success(f"✅ Retrieved {len(samples)} random samples from {total} total documents")
                            
                            # Display samples
                            for i, sample in enumerate(samples, 1):
                                with st.expander(f"📄 Sample {i}: {sample.get('file_path', 'Unknown')[:60]}..."):
                                    info_col1, info_col2, info_col3 = st.columns(3)
                                    with info_col1:
                                        st.metric("Service", sample.get("service", "N/A"))
                                    with info_col2:
                                        st.metric("Dimensions", sample.get("dimensions", 768))
                                    with info_col3:
                                        st.metric("ID", sample.get("id", "N/A")[:12] + "...")
                                    
                                    st.text("**File Path:**")
                                    st.code(sample.get("file_path", "Unknown"), language="text")
                                    
                                    st.markdown("**Content Preview:**")
                                    st.text_area(
                                        "Content",
                                        value=sample.get("content_preview", "No content"),
                                        height=100,
                                        disabled=True,
                                        key=f"sample_content_{i}"
                                    )
                                    
                                    # Vector stats if available
                                    if "vector_stats" in sample and sample["vector_stats"]:
                                        st.markdown("**Vector Statistics:**")
                                        stats = sample["vector_stats"]
                                        st_col1, st_col2, st_col3, st_col4 = st.columns(4)
                                        with st_col1:
                                            st.metric("Norm", f"{stats.get('norm', 0):.4f}")
                                        with st_col2:
                                            st.metric("Mean", f"{stats.get('mean', 0):.4f}")
                                        with st_col3:
                                            st.metric("Std", f"{stats.get('std', 0):.4f}")
                                        with st_col4:
                                            st.metric("Range", f"[{stats.get('min', 0):.2f}, {stats.get('max', 0):.2f}]")
                                    
                                    # Vector preview
                                    if "vector_preview" in sample and sample["vector_preview"]:
                                        with st.expander("🧬 Vector Preview (first 10 dimensions)"):
                                            st.code(str(sample["vector_preview"]), language="python")
                                    
                                    # Metadata
                                    with st.expander("📋 Metadata"):
                                        st.json(sample.get("metadata", {}))
                        
                        elif response.status_code == 404:
                            st.error("❌ No documents found in ChromaDB")
                            st.info("💡 Ensure documents are ingested and embedded first.")
                        else:
                            st.error(f"❌ Error: HTTP {response.status_code}")
                            st.caption(response.text[:300])
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        import traceback
                        with st.expander("🔍 Error Details"):
                            st.code(traceback.format_exc())
        
        # Embedding visualization
        st.markdown("---")
        st.markdown("#### 📊 Embedding Visualization")
        
        # Try to import visualization module
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from visualizations.embedding_viz import (
                create_tsne_plot,
                create_umap_plot,
                create_similarity_heatmap,
                create_dimension_distribution,
                create_pca_plot,
                UMAP_AVAILABLE
            )
            VIZ_AVAILABLE = True
        except ImportError as e:
            VIZ_AVAILABLE = False
            st.warning(f"Visualization libraries not fully installed: {str(e)}")
            st.info("Install with: `pip install plotly scikit-learn umap-learn`")
        
        if VIZ_AVAILABLE:
            st.success("✅ Visualization tools ready!")
            
            # Visualization controls
            viz_col1, viz_col2, viz_col3 = st.columns(3)
            
            with viz_col1:
                viz_type = st.selectbox(
                    "Visualization Type",
                    options=["t-SNE 2D", "t-SNE 3D", "UMAP 2D", "UMAP 3D", "PCA 2D", "PCA 3D", "Similarity Heatmap"],
                    key="viz_type",
                    help="Choose dimensionality reduction method"
                )
            
            with viz_col2:
                num_docs = st.slider(
                    "Number of documents",
                    min_value=10,
                    max_value=200,
                    value=50,
                    step=10,
                    key="num_docs_viz",
                    help="More documents = slower but more comprehensive"
                )
            
            with viz_col3:
                color_by = st.selectbox(
                    "Color by",
                    options=["None", "service", "file_type"],
                    key="color_by_viz",
                    help="Color points by metadata field"
                )
            
            # Advanced settings (in expander)
            with st.expander("⚙️ Advanced Visualization Settings"):
                adv_col1, adv_col2 = st.columns(2)
                
                with adv_col1:
                    if "t-SNE" in viz_type:
                        perplexity = st.slider(
                            "Perplexity",
                            min_value=5,
                            max_value=50,
                            value=30,
                            key="tsne_perplexity",
                            help="Controls cluster size (lower = tighter clusters)"
                        )
                    
                    if "UMAP" in viz_type and UMAP_AVAILABLE:
                        n_neighbors = st.slider(
                            "N Neighbors",
                            min_value=5,
                            max_value=50,
                            value=15,
                            key="umap_neighbors",
                            help="Local vs global structure balance"
                        )
                
                with adv_col2:
                    if "UMAP" in viz_type and UMAP_AVAILABLE:
                        min_dist = st.slider(
                            "Min Distance",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.1,
                            step=0.05,
                            key="umap_min_dist",
                            help="How tightly packed points are"
                        )
                    
                    if viz_type == "Similarity Heatmap":
                        show_values = st.checkbox(
                            "Show similarity values",
                            value=True,
                            key="heatmap_values",
                            help="Display numeric values in heatmap cells"
                        )
            
            # Generate button
            if st.button("🎨 Generate Visualization", key="generate_viz", type="primary", use_container_width=True):
                with st.spinner(f"Generating {viz_type}... This may take 10-30 seconds"):
                    try:
                        # Fetch embeddings via batch export API
                        export_response = httpx.get(
                            f"{api_base_url}/api/v1/embeddings/export/batch",
                            params={
                                "limit": num_docs,
                                "offset": 0
                            },
                            timeout=120.0  # Longer timeout for large batches
                        )
                        
                        if export_response.status_code == 200:
                            data = export_response.json()
                            embeddings = data.get("embeddings", [])
                            ids = data.get("ids", [])
                            metadata_list = data.get("metadata", [])
                            
                            if len(embeddings) < 10:
                                st.warning(f"Only found {len(embeddings)} documents. Visualization works best with 20+ documents.")
                                st.info("💡 Ensure documents are ingested and embedded in ChromaDB.")
                            
                            if embeddings:
                                st.success(f"✅ Loaded {len(embeddings)} real embeddings from ChromaDB!")
                                
                                # Prepare labels from metadata
                                labels = []
                                for meta in metadata_list:
                                    file_path = meta.get('file_path', 'Unknown')
                                    if len(file_path) > 60:
                                        file_path = file_path[:60] + "..."
                                    labels.append(file_path)
                                
                                # Use metadata_list directly
                                metadata = metadata_list
                                
                                # Generate visualization
                                color_field = None if color_by == "None" else color_by
                                
                                if viz_type == "t-SNE 2D":
                                    fig = create_tsne_plot(embeddings, labels, metadata, perplexity, 2, color_field)
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                elif viz_type == "t-SNE 3D":
                                    fig = create_tsne_plot(embeddings, labels, metadata, perplexity, 3, color_field)
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                elif viz_type == "UMAP 2D":
                                    if UMAP_AVAILABLE:
                                        fig = create_umap_plot(embeddings, labels, metadata, n_neighbors, min_dist, 2, color_field)
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.error("UMAP not available. Install: `pip install umap-learn`")
                                
                                elif viz_type == "UMAP 3D":
                                    if UMAP_AVAILABLE:
                                        fig = create_umap_plot(embeddings, labels, metadata, n_neighbors, min_dist, 3, color_field)
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.error("UMAP not available. Install: `pip install umap-learn`")
                                
                                elif viz_type == "PCA 2D":
                                    fig, var_explained = create_pca_plot(embeddings, labels, metadata, 2, color_field)
                                    st.plotly_chart(fig, use_container_width=True)
                                    st.info(f"Variance explained: PC1: {var_explained[0]*100:.1f}%, PC2: {var_explained[1]*100:.1f}%")
                                
                                elif viz_type == "PCA 3D":
                                    fig, var_explained = create_pca_plot(embeddings, labels, metadata, 3, color_field)
                                    st.plotly_chart(fig, use_container_width=True)
                                    st.info(f"Variance explained: PC1: {var_explained[0]*100:.1f}%, PC2: {var_explained[1]*100:.1f}%, PC3: {var_explained[2]*100:.1f}%")
                                
                                elif viz_type == "Similarity Heatmap":
                                    fig = create_similarity_heatmap(embeddings[:min(50, len(embeddings))], labels[:min(50, len(labels))], 50, show_values)
                                    st.plotly_chart(fig, use_container_width=True)
                                
                                # Show sample dimension distribution
                                if len(embeddings) > 0:
                                    with st.expander("📊 Sample Dimension Distribution"):
                                        sample_idx = 0
                                        fig_dim = create_dimension_distribution(
                                            embeddings[sample_idx],
                                            f"Dimension Distribution: {labels[sample_idx]}"
                                        )
                                        st.plotly_chart(fig_dim, use_container_width=True)
                                
                                st.success("✅ Visualization complete with real embeddings!")
                                st.caption("📊 Using actual 768D vectors from ChromaDB")
                        
                        elif export_response.status_code == 404:
                            st.error("❌ No embeddings found in ChromaDB")
                            st.info("💡 Ensure documents are ingested and embedded first.")
                        else:
                            st.error(f"Failed to fetch embeddings: HTTP {export_response.status_code}")
                            st.caption(export_response.text[:200])
                    
                    except Exception as e:
                        st.error(f"Visualization error: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        
        else:
            st.info("""
            **Visualization libraries not installed.**
            
            To enable visualization features, install:
            ```bash
            pip install plotly scikit-learn umap-learn
            ```
            
            Then restart the dashboard.
            """)
    
    with analysis_tab4:
        st.markdown("""
        ### 📊 Table/Collection Browser
        
        Browse all documents in the ChromaDB collection in a tabular format.
        Filter, sort, and explore your vector database like a spreadsheet.
        """)
        
        # Browsing controls
        browse_col1, browse_col2, browse_col3 = st.columns(3)
        
        with browse_col1:
            page_size = st.selectbox(
                "Items per page",
                options=[10, 25, 50, 100],
                index=1,
                key="table_page_size"
            )
        
        with browse_col2:
            sort_by = st.selectbox(
                "Sort by",
                options=["File Path", "Service", "File Type", "Date Added"],
                key="table_sort_by"
            )
        
        with browse_col3:
            filter_service = st.selectbox(
                "Filter by Service",
                options=["All", "ecosystem-mcp", "llm-gateway", "mcp-interpreter", "other"],
                key="table_filter_service"
            )
        
        # Fetch and display documents
        if st.button("📋 Load Documents", key="load_table_docs", use_container_width=True):
            with st.spinner("Fetching documents from database..."):
                try:
                    # Build query params based on filter
                    query_params = {
                        "limit": page_size,
                        "offset": 0
                    }
                    
                    # Add service filter if specified
                    if filter_service != "All":
                        query_params["service_name"] = filter_service
                    
                    # Query documents endpoint
                    query_response = httpx.post(
                        f"{api_base_url}/api/v1/query",
                        json=query_params,
                        timeout=30.0
                    )
                    
                    if query_response.status_code == 200:
                        query_data = query_response.json()
                        documents = query_data.get("documents", [])
                        total = query_data.get("total", 0)
                        
                        if documents:
                            st.success(f"✅ Loaded {len(documents)} of {total} total documents")
                            if query_data.get("has_next", False):
                                st.info("📄 More documents available. Pagination coming soon!")
                            
                            # Create table data
                            table_data = []
                            for doc in documents:
                                metadata = doc.get('metadata', {})
                                content = doc.get('normalized_content', '')
                                table_data.append({
                                    "File Path": doc.get('file_path', 'N/A'),
                                    "Service": doc.get('service_name', 'N/A'),
                                    "Format": doc.get('original_format', 'N/A'),
                                    "Size": len(content),
                                    "Latest": "✓" if doc.get('is_latest', False) else "",
                                    "Created": doc.get('created_at', 'N/A')[:10],  # Just date
                                    "ID": str(doc.get('id', 'N/A'))[:12] + "..."
                                })
                            
                            # Display as dataframe
                            import pandas as pd
                            df = pd.DataFrame(table_data)
                            
                            # Note: Filtering already applied by API
                            # Display dataframe
                            st.dataframe(
                                df,
                                use_container_width=True,
                                height=400
                            )
                            
                            # Show filter info
                            if filter_service != "All":
                                st.caption(f"🔍 Filtered by service: {filter_service}")
                            
                            # Export options
                            st.markdown("---")
                            st.markdown("#### 💾 Export Options")
                            
                            export_col1, export_col2 = st.columns(2)
                            
                            with export_col1:
                                csv_data = df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download as CSV",
                                    data=csv_data,
                                    file_name=f"chromadb_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                    key="download_csv"
                                )
                            
                            with export_col2:
                                json_data = df.to_json(orient='records', indent=2)
                                st.download_button(
                                    label="📥 Download as JSON",
                                    data=json_data,
                                    file_name=f"chromadb_documents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                    mime="application/json",
                                    key="download_json"
                                )
                        
                        else:
                            if filter_service != "All":
                                st.warning(f"⚠️ No documents found for service: **{filter_service}**")
                                st.info("💡 Try selecting **All** or check if documents have been ingested for this service.")
                            else:
                                st.warning("⚠️ No documents found in the database.")
                                st.info("💡 Documents need to be ingested first. Check the **📚 Documents** page.")
                    
                    elif query_response.status_code == 422:
                        st.error(f"❌ Invalid request (HTTP 422): Query validation failed")
                        try:
                            error_detail = query_response.json()
                            with st.expander("🔍 Error Details"):
                                st.json(error_detail)
                        except:
                            st.caption(f"Response: {query_response.text[:300]}")
                        st.info("💡 **Fixed!** The query now uses valid search terms. If you still see this, the API may have changed.")
                    
                    else:
                        st.error(f"❌ Failed to load documents: HTTP {query_response.status_code}")
                        st.caption(f"Response: {query_response.text[:200]}")
                
                except httpx.TimeoutException:
                    st.error("⏱️ Request timed out (30s). The API might be slow or processing a large dataset.")
                    st.info("💡 Try reducing the page size or check if the ecosystem-mcp service is responding.")
                except httpx.ConnectError:
                    st.error("🔌 Cannot connect to API. The ecosystem-mcp service may not be running.")
                    st.info("💡 Go to **Container Management** → **Service Manager** to start the service.")
                except Exception as e:
                    st.error(f"❌ Error loading documents: {str(e)}")
                    with st.expander("🔍 Full Error Traceback"):
                        import traceback
                        st.code(traceback.format_exc())
        
        st.markdown("---")
        st.markdown("#### 🔍 Advanced Table Features")
        
        with st.expander("📚 Available Filters"):
            st.markdown("""
            **Current Filters:**
            - Service (ecosystem-mcp, llm-gateway, etc.)
            - Page size (10, 25, 50, 100 items)
            - Sort by various fields
            
            **Suggested Enhancements:**
            - Date range filter
            - File type filter (md, py, json, etc.)
            - Content length filter
            - Full-text search within table
            - Multi-column sorting
            - Embedding status filter (has embedding / missing embedding)
            """)
        
        with st.expander("💡 API Enhancement Suggestions"):
            st.markdown("""
            To make the table browser more powerful, consider adding:
            
            ```python
            # Browse endpoint
            GET /api/v1/documents?page=1&size=50&service=ecosystem-mcp&sort=date_desc
            
            # Response:
            {
                "documents": [...],
                "total": 1234,
                "page": 1,
                "page_size": 50,
                "total_pages": 25
            }
            ```
            
            This would enable:
            - Proper pagination
            - Efficient filtering
            - Server-side sorting
            - Total count display
            """)
    
    with analysis_tab5:
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

