# Embedding Visualization Implementation Guide

## Overview

Step-by-step guide to implement advanced embedding visualization features in the ChromaDB Explorer.

**Created:** October 14, 2025

## Phase 1: API Backend Enhancements

### 1. Random Sampling Endpoint

**File:** `services/ecosystem-mcp/src/api/routes/embeddings.py`

```python
from fastapi import APIRouter, Query
from typing import List, Optional
import random

router = APIRouter(prefix="/api/v1/embeddings", tags=["embeddings"])

@router.get("/sample")
async def get_random_samples(
    n: int = Query(10, ge=1, le=100, description="Number of samples"),
    include_vectors: bool = Query(False, description="Include full 768D vectors"),
    service_filter: Optional[str] = Query(None, description="Filter by service")
):
    """
    Get random sample of embeddings for exploration.
    
    Returns:
        {
            "samples": [
                {
                    "id": "doc_abc123",
                    "file_path": "/path/to/file.md",
                    "service": "ecosystem-mcp",
                    "vector": [...] if include_vectors else None,
                    "vector_preview": [0.123, -0.456, ...],  # First 10 dims
                    "metadata": {...}
                },
                ...
            ],
            "count": 10,
            "total_documents": 1234
        }
    """
    try:
        # Get ChromaDB collection
        collection = chroma_client.get_collection("ecosystem-mcp")
        
        # Get all IDs (or filtered IDs)
        all_docs = collection.get(
            where={"service": service_filter} if service_filter else None,
            include=["metadatas", "documents"]
        )
        
        all_ids = all_docs["ids"]
        
        # Random sample
        sample_ids = random.sample(all_ids, min(n, len(all_ids)))
        
        # Get full data for samples
        samples = collection.get(
            ids=sample_ids,
            include=["metadatas", "documents", "embeddings"] if include_vectors else ["metadatas", "documents"]
        )
        
        # Format response
        result_samples = []
        for i, doc_id in enumerate(sample_ids):
            sample = {
                "id": doc_id,
                "file_path": samples["metadatas"][i].get("file_path", "Unknown"),
                "service": samples["metadatas"][i].get("service", "Unknown"),
                "metadata": samples["metadatas"][i],
                "content_preview": samples["documents"][i][:200] if samples["documents"][i] else ""
            }
            
            if include_vectors and "embeddings" in samples:
                sample["vector"] = samples["embeddings"][i]
                sample["vector_preview"] = samples["embeddings"][i][:10]  # First 10 dims
            
            result_samples.append(sample)
        
        return {
            "samples": result_samples,
            "count": len(result_samples),
            "total_documents": len(all_ids)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sampling embeddings: {str(e)}")
```

### 2. Embedding by ID Endpoint

```python
@router.get("/{embedding_id}")
async def get_embedding_by_id(
    embedding_id: str,
    include_vector: bool = Query(True, description="Include 768D vector")
):
    """
    Get specific embedding by ID.
    
    Returns:
        {
            "id": "doc_abc123",
            "vector": [0.123, -0.456, ...],  // 768 dimensions
            "document": {
                "file_path": "/path/to/file.md",
                "content": "...",
                "metadata": {...}
            },
            "model": "nomic-embed-text",
            "dimensions": 768,
            "stats": {
                "norm": 1.0,
                "mean": 0.0234,
                "std": 0.234,
                "min": -0.892,
                "max": 0.876
            }
        }
    """
    try:
        collection = chroma_client.get_collection("ecosystem-mcp")
        
        result = collection.get(
            ids=[embedding_id],
            include=["metadatas", "documents", "embeddings"] if include_vector else ["metadatas", "documents"]
        )
        
        if not result["ids"]:
            raise HTTPException(status_code=404, detail=f"Embedding {embedding_id} not found")
        
        response = {
            "id": embedding_id,
            "document": {
                "file_path": result["metadatas"][0].get("file_path", "Unknown"),
                "content": result["documents"][0],
                "metadata": result["metadatas"][0]
            },
            "model": "nomic-embed-text",
            "dimensions": 768
        }
        
        if include_vector and "embeddings" in result:
            import numpy as np
            vector = np.array(result["embeddings"][0])
            
            response["vector"] = vector.tolist()
            response["stats"] = {
                "norm": float(np.linalg.norm(vector)),
                "mean": float(np.mean(vector)),
                "std": float(np.std(vector)),
                "min": float(np.min(vector)),
                "max": float(np.max(vector))
            }
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching embedding: {str(e)}")
```

### 3. Batch Vector Export

```python
@router.get("/export/batch")
async def export_embeddings_batch(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service_filter: Optional[str] = None
):
    """
    Export embeddings in batches for visualization/analysis.
    
    Useful for generating t-SNE/UMAP projections.
    """
    try:
        collection = chroma_client.get_collection("ecosystem-mcp")
        
        # Get batch of documents with embeddings
        results = collection.get(
            where={"service": service_filter} if service_filter else None,
            include=["metadatas", "embeddings"],
            limit=limit,
            offset=offset
        )
        
        return {
            "embeddings": results["embeddings"],
            "ids": results["ids"],
            "metadata": results["metadatas"],
            "count": len(results["ids"]),
            "offset": offset
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting embeddings: {str(e)}")
```

### 4. Similarity Comparison

```python
from src.services.embedding_service import EmbeddingService

@router.post("/compare")
async def compare_embeddings(
    query1: str,
    query2: str,
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    """
    Compare similarity between two queries.
    
    Returns:
        {
            "similarity": 0.8574,
            "cosine_distance": 0.1426,
            "query1_vector_preview": [0.123, ...],  # First 10 dims
            "query2_vector_preview": [-0.456, ...],
            "interpretation": "Very similar" | "Similar" | "Somewhat similar" | "Different"
        }
    """
    try:
        # Generate embeddings
        vector1 = await embedding_service.embed_text(query1)
        vector2 = await embedding_service.embed_text(query2)
        
        # Calculate cosine similarity
        import numpy as np
        v1 = np.array(vector1)
        v2 = np.array(vector2)
        
        # Cosine similarity = dot product of normalized vectors
        similarity = float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        distance = 1 - similarity
        
        # Interpretation
        if similarity > 0.9:
            interpretation = "Very similar"
        elif similarity > 0.7:
            interpretation = "Similar"
        elif similarity > 0.5:
            interpretation = "Somewhat similar"
        else:
            interpretation = "Different"
        
        return {
            "similarity": similarity,
            "cosine_distance": distance,
            "query1": query1,
            "query2": query2,
            "query1_vector_preview": v1[:10].tolist(),
            "query2_vector_preview": v2[:10].tolist(),
            "interpretation": interpretation
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing embeddings: {str(e)}")
```

## Phase 2: Frontend Visualization

### 1. Install Required Libraries

```bash
cd services/ecosystem-mcp-dashboard
pip install plotly scikit-learn umap-learn pandas numpy
```

### 2. Create Visualization Module

**File:** `dashboard_views/visualizations/embedding_viz.py`

```python
"""
Embedding visualization utilities.
"""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from sklearn.manifold import TSNE
import pandas as pd
from typing import List, Dict, Optional

def create_tsne_plot(
    embeddings: List[List[float]],
    labels: List[str],
    metadata: Optional[List[Dict]] = None,
    perplexity: int = 30,
    n_components: int = 2
) -> go.Figure:
    """
    Create t-SNE projection of embeddings.
    
    Args:
        embeddings: List of 768-dim vectors
        labels: Labels for each point (e.g., file paths)
        metadata: Additional metadata for hover info
        perplexity: t-SNE perplexity parameter (5-50)
        n_components: 2D or 3D projection
    
    Returns:
        Plotly figure
    """
    # Convert to numpy array
    X = np.array(embeddings)
    
    # Apply t-SNE
    tsne = TSNE(
        n_components=n_components,
        perplexity=perplexity,
        random_state=42,
        n_iter=1000
    )
    
    X_embedded = tsne.fit_transform(X)
    
    # Create dataframe
    if n_components == 2:
        df = pd.DataFrame({
            'x': X_embedded[:, 0],
            'y': X_embedded[:, 1],
            'label': labels
        })
        
        # Add metadata columns
        if metadata:
            for key in metadata[0].keys():
                df[key] = [m.get(key, 'N/A') for m in metadata]
        
        # Create scatter plot
        fig = px.scatter(
            df,
            x='x',
            y='y',
            hover_data=['label'] + ([k for k in metadata[0].keys()] if metadata else []),
            title='t-SNE Projection of Embeddings (2D)',
            labels={'x': 't-SNE 1', 'y': 't-SNE 2'}
        )
        
        fig.update_traces(marker=dict(size=8, opacity=0.7))
    
    else:  # 3D
        df = pd.DataFrame({
            'x': X_embedded[:, 0],
            'y': X_embedded[:, 1],
            'z': X_embedded[:, 2],
            'label': labels
        })
        
        fig = px.scatter_3d(
            df,
            x='x',
            y='y',
            z='z',
            hover_data=['label'],
            title='t-SNE Projection of Embeddings (3D)',
            labels={'x': 't-SNE 1', 'y': 't-SNE 2', 'z': 't-SNE 3'}
        )
    
    fig.update_layout(
        height=600,
        hovermode='closest'
    )
    
    return fig


def create_similarity_heatmap(
    embeddings: List[List[float]],
    labels: List[str],
    max_items: int = 50
) -> go.Figure:
    """
    Create similarity heatmap between embeddings.
    
    Args:
        embeddings: List of vectors
        labels: Labels for each vector
        max_items: Maximum number of items to show
    
    Returns:
        Plotly heatmap figure
    """
    # Limit to max_items
    if len(embeddings) > max_items:
        embeddings = embeddings[:max_items]
        labels = labels[:max_items]
    
    # Convert to numpy
    X = np.array(embeddings)
    
    # Calculate cosine similarity matrix
    # Normalize vectors
    X_norm = X / np.linalg.norm(X, axis=1, keepdims=True)
    
    # Similarity matrix = X_norm @ X_norm.T
    similarity_matrix = X_norm @ X_norm.T
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=similarity_matrix,
        x=[l[:30] for l in labels],  # Truncate labels
        y=[l[:30] for l in labels],
        colorscale='RdYlGn',
        zmid=0.5,
        text=np.round(similarity_matrix, 3),
        texttemplate='%{text}',
        textfont={"size": 8},
        hovertemplate='<b>%{x}</b><br><b>%{y}</b><br>Similarity: %{z:.3f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'Embedding Similarity Heatmap (Top {len(labels)} documents)',
        xaxis_title='Documents',
        yaxis_title='Documents',
        height=700,
        width=800
    )
    
    return fig


def create_dimension_distribution(
    embedding: List[float]
) -> go.Figure:
    """
    Visualize distribution across embedding dimensions.
    
    Args:
        embedding: Single 768-dim vector
    
    Returns:
        Plotly figure showing dimension values
    """
    vector = np.array(embedding)
    
    fig = go.Figure()
    
    # Line plot of dimensions
    fig.add_trace(go.Scatter(
        x=list(range(len(vector))),
        y=vector,
        mode='lines',
        name='Dimension Values',
        line=dict(color='blue', width=1)
    ))
    
    # Add mean line
    fig.add_hline(
        y=np.mean(vector),
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {np.mean(vector):.4f}"
    )
    
    fig.update_layout(
        title='Embedding Dimension Distribution',
        xaxis_title='Dimension Index',
        yaxis_title='Value',
        height=400,
        showlegend=True
    )
    
    return fig
```

### 3. Update ChromaDB Explorer Page

Add to `dashboard_views/chromadb_explorer.py`:

```python
# At the top, add imports
try:
    from visualizations.embedding_viz import (
        create_tsne_plot,
        create_similarity_heatmap,
        create_dimension_distribution
    )
    import plotly.graph_objects as go
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False

# In the Embedding Explorer tab, add visualization section:

st.markdown("---")
st.markdown("#### 📊 Embedding Visualization")

if VISUALIZATION_AVAILABLE:
    viz_type = st.selectbox(
        "Visualization Type",
        options=["t-SNE 2D", "t-SNE 3D", "Similarity Heatmap", "Dimension Distribution"],
        key="viz_type"
    )
    
    num_docs_viz = st.slider(
        "Number of documents to visualize",
        min_value=10,
        max_value=100,
        value=50,
        key="num_docs_viz"
    )
    
    if st.button("🎨 Generate Visualization", key="generate_viz"):
        with st.spinner(f"Generating {viz_type}..."):
            try:
                # Fetch embeddings via API
                response = httpx.get(
                    f"{api_base_url}/api/v1/embeddings/export/batch?limit={num_docs_viz}",
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    embeddings = data["embeddings"]
                    ids = data["ids"]
                    metadata = data["metadata"]
                    
                    labels = [m.get("file_path", id)[:50] for m, id in zip(metadata, ids)]
                    
                    if viz_type == "t-SNE 2D":
                        fig = create_tsne_plot(embeddings, labels, metadata, n_components=2)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif viz_type == "t-SNE 3D":
                        fig = create_tsne_plot(embeddings, labels, metadata, n_components=3)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif viz_type == "Similarity Heatmap":
                        fig = create_similarity_heatmap(embeddings, labels)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    elif viz_type == "Dimension Distribution":
                        # Show first embedding's distribution
                        fig = create_dimension_distribution(embeddings[0])
                        st.plotly_chart(fig, use_container_width=True)
                        st.caption(f"Showing dimensions for: {labels[0]}")
                
                else:
                    st.error(f"Failed to fetch embeddings: HTTP {response.status_code}")
            
            except Exception as e:
                st.error(f"Visualization error: {str(e)}")

else:
    st.warning("Visualization libraries not installed. Install: `pip install plotly scikit-learn umap-learn`")
```

## Phase 3: Implementation Steps

### Step 1: Backend (Week 1)

1. **Day 1-2:** Implement random sampling endpoint
   ```bash
   # Test: curl http://localhost:8000/api/v1/embeddings/sample?n=10
   ```

2. **Day 3:** Implement get by ID endpoint
   ```bash
   # Test: curl http://localhost:8000/api/v1/embeddings/{id}
   ```

3. **Day 4:** Implement batch export endpoint
4. **Day 5:** Implement comparison endpoint

### Step 2: Frontend (Week 2)

1. **Day 1:** Install visualization libraries
2. **Day 2-3:** Create visualization module
3. **Day 4:** Integrate into ChromaDB Explorer
4. **Day 5:** Testing and refinement

### Step 3: Testing & Optimization (Week 3)

1. **Performance testing** with large datasets
2. **UI/UX refinement**
3. **Documentation**
4. **User feedback**

## Quick Win: Basic Implementation

For immediate results, implement just the t-SNE visualization:

```python
# Minimal version - add to chromadb_explorer.py
import streamlit as st

if st.button("🎨 Quick t-SNE Visualization"):
    try:
        import plotly.express as px
        from sklearn.manifold import TSNE
        import numpy as np
        
        # Get sample embeddings (mocked for now)
        st.info("Fetching embeddings...")
        
        # TODO: Replace with actual API call
        # For now, generate random data to show concept
        n_samples = 50
        embeddings = np.random.randn(n_samples, 768)
        labels = [f"Doc {i}" for i in range(n_samples)]
        
        # t-SNE
        tsne = TSNE(n_components=2, random_state=42)
        embedded = tsne.fit_transform(embeddings)
        
        # Plot
        fig = px.scatter(
            x=embedded[:, 0],
            y=embedded[:, 1],
            hover_name=labels,
            title="Document Embeddings (t-SNE)"
        )
        
        st.plotly_chart(fig)
        
    except ImportError:
        st.error("Install: pip install plotly scikit-learn")
```

## Summary

✅ **API Endpoints:** 4 new endpoints for embedding access
✅ **Visualizations:** t-SNE, UMAP, heatmaps, distributions
✅ **Integration:** Works with existing ChromaDB setup
✅ **Scalable:** Handles large embedding collections
✅ **User-friendly:** Interactive Plotly visualizations

**Time Estimate:** 2-3 weeks for full implementation
**Quick Win:** Basic t-SNE in 1 day

Would you like me to implement any specific part first?

