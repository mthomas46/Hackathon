"""
Embedding visualization utilities for ChromaDB Explorer.

Provides functions to visualize 768-dimensional embeddings using:
- t-SNE 2D/3D projections
- Similarity heatmaps
- Dimension distributions
- UMAP projections
"""

import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from sklearn.manifold import TSNE
import pandas as pd
from typing import List, Dict, Optional, Tuple

try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False


def create_tsne_plot(
    embeddings: List[List[float]],
    labels: List[str],
    metadata: Optional[List[Dict]] = None,
    perplexity: int = 30,
    n_components: int = 2,
    color_by: Optional[str] = None
) -> go.Figure:
    """
    Create t-SNE projection of embeddings.
    
    Args:
        embeddings: List of 768-dim vectors
        labels: Labels for each point (e.g., file paths)
        metadata: Additional metadata for hover info and coloring
        perplexity: t-SNE perplexity parameter (5-50, default 30)
        n_components: 2D or 3D projection
        color_by: Metadata field to color by (e.g., 'service', 'file_type')
    
    Returns:
        Plotly figure with t-SNE projection
    """
    # Validate inputs
    if len(embeddings) < 2:
        raise ValueError("Need at least 2 embeddings for t-SNE")
    
    if len(embeddings) != len(labels):
        raise ValueError(f"Mismatch: {len(embeddings)} embeddings but {len(labels)} labels")
    
    # Adjust perplexity if needed
    adjusted_perplexity = min(perplexity, len(embeddings) - 1)
    if adjusted_perplexity < perplexity:
        print(f"Adjusted perplexity from {perplexity} to {adjusted_perplexity} (n_samples={len(embeddings)})")
    
    # Convert to numpy array
    X = np.array(embeddings)
    
    # Apply t-SNE
    tsne = TSNE(
        n_components=n_components,
        perplexity=adjusted_perplexity,
        random_state=42,
        max_iter=1000,  # Changed from n_iter (deprecated) to max_iter
        verbose=0
    )
    
    X_embedded = tsne.fit_transform(X)
    
    # Create dataframe
    if n_components == 2:
        df = pd.DataFrame({
            'x': X_embedded[:, 0],
            'y': X_embedded[:, 1],
            'label': [str(l)[:80] for l in labels]  # Truncate labels
        })
        
        # Add metadata columns
        if metadata:
            for key in metadata[0].keys():
                df[key] = [str(m.get(key, 'N/A')) for m in metadata]
        
        # Determine color
        color_col = None
        if color_by and metadata and color_by in metadata[0]:
            color_col = color_by
        
        # Create scatter plot
        fig = px.scatter(
            df,
            x='x',
            y='y',
            color=color_col,
            hover_data=['label'] + ([k for k in metadata[0].keys()] if metadata else []),
            title=f't-SNE Projection of {len(embeddings)} Embeddings (2D)',
            labels={'x': 't-SNE Component 1', 'y': 't-SNE Component 2'}
        )
        
        fig.update_traces(marker=dict(size=10, opacity=0.7, line=dict(width=0.5, color='white')))
        
    else:  # 3D
        df = pd.DataFrame({
            'x': X_embedded[:, 0],
            'y': X_embedded[:, 1],
            'z': X_embedded[:, 2],
            'label': [str(l)[:80] for l in labels]
        })
        
        # Add metadata
        if metadata:
            for key in metadata[0].keys():
                df[key] = [str(m.get(key, 'N/A')) for m in metadata]
        
        color_col = None
        if color_by and metadata and color_by in metadata[0]:
            color_col = color_by
        
        fig = px.scatter_3d(
            df,
            x='x',
            y='y',
            z='z',
            color=color_col,
            hover_data=['label'] + ([k for k in metadata[0].keys()] if metadata else []),
            title=f't-SNE Projection of {len(embeddings)} Embeddings (3D)',
            labels={'x': 't-SNE 1', 'y': 't-SNE 2', 'z': 't-SNE 3'}
        )
        
        fig.update_traces(marker=dict(size=5, opacity=0.7))
    
    fig.update_layout(
        height=700,
        hovermode='closest',
        template='plotly_white'
    )
    
    return fig


def create_umap_plot(
    embeddings: List[List[float]],
    labels: List[str],
    metadata: Optional[List[Dict]] = None,
    n_neighbors: int = 15,
    min_dist: float = 0.1,
    n_components: int = 2,
    color_by: Optional[str] = None
) -> go.Figure:
    """
    Create UMAP projection of embeddings.
    
    Args:
        embeddings: List of 768-dim vectors
        labels: Labels for each point
        metadata: Additional metadata
        n_neighbors: UMAP n_neighbors parameter (default 15)
        min_dist: UMAP min_dist parameter (default 0.1)
        n_components: 2D or 3D projection
        color_by: Metadata field to color by
    
    Returns:
        Plotly figure with UMAP projection
    """
    if not UMAP_AVAILABLE:
        raise ImportError("UMAP not available. Install with: pip install umap-learn")
    
    if len(embeddings) < 2:
        raise ValueError("Need at least 2 embeddings for UMAP")
    
    # Convert to numpy
    X = np.array(embeddings)
    
    # Apply UMAP
    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=min(n_neighbors, len(embeddings) - 1),
        min_dist=min_dist,
        random_state=42
    )
    
    X_embedded = reducer.fit_transform(X)
    
    # Create dataframe
    if n_components == 2:
        df = pd.DataFrame({
            'x': X_embedded[:, 0],
            'y': X_embedded[:, 1],
            'label': [str(l)[:80] for l in labels]
        })
        
        if metadata:
            for key in metadata[0].keys():
                df[key] = [str(m.get(key, 'N/A')) for m in metadata]
        
        color_col = None
        if color_by and metadata and color_by in metadata[0]:
            color_col = color_by
        
        fig = px.scatter(
            df,
            x='x',
            y='y',
            color=color_col,
            hover_data=['label'] + ([k for k in metadata[0].keys()] if metadata else []),
            title=f'UMAP Projection of {len(embeddings)} Embeddings (2D)',
            labels={'x': 'UMAP Component 1', 'y': 'UMAP Component 2'}
        )
        
        fig.update_traces(marker=dict(size=10, opacity=0.7, line=dict(width=0.5, color='white')))
    
    else:  # 3D
        df = pd.DataFrame({
            'x': X_embedded[:, 0],
            'y': X_embedded[:, 1],
            'z': X_embedded[:, 2],
            'label': [str(l)[:80] for l in labels]
        })
        
        if metadata:
            for key in metadata[0].keys():
                df[key] = [str(m.get(key, 'N/A')) for m in metadata]
        
        color_col = None
        if color_by and metadata and color_by in metadata[0]:
            color_col = color_by
        
        fig = px.scatter_3d(
            df,
            x='x',
            y='y',
            z='z',
            color=color_col,
            hover_data=['label'] + ([k for k in metadata[0].keys()] if metadata else []),
            title=f'UMAP Projection of {len(embeddings)} Embeddings (3D)',
            labels={'x': 'UMAP 1', 'y': 'UMAP 2', 'z': 'UMAP 3'}
        )
        
        fig.update_traces(marker=dict(size=5, opacity=0.7))
    
    fig.update_layout(
        height=700,
        hovermode='closest',
        template='plotly_white'
    )
    
    return fig


def create_similarity_heatmap(
    embeddings: List[List[float]],
    labels: List[str],
    max_items: int = 50,
    show_values: bool = True
) -> go.Figure:
    """
    Create similarity heatmap between embeddings.
    
    Args:
        embeddings: List of vectors
        labels: Labels for each vector
        max_items: Maximum number of items to show (default 50)
        show_values: Whether to show similarity values in cells
    
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
    
    # Truncate labels for display
    truncated_labels = [str(l)[:40] + "..." if len(str(l)) > 40 else str(l) for l in labels]
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=similarity_matrix,
        x=truncated_labels,
        y=truncated_labels,
        colorscale='RdYlGn',
        zmid=0.5,
        zmin=0,
        zmax=1,
        text=np.round(similarity_matrix, 3) if show_values else None,
        texttemplate='%{text}' if show_values else None,
        textfont={"size": 8},
        hovertemplate='<b>X:</b> %{x}<br><b>Y:</b> %{y}<br><b>Similarity:</b> %{z:.4f}<extra></extra>',
        colorbar=dict(title="Cosine<br>Similarity")
    ))
    
    fig.update_layout(
        title=f'Embedding Similarity Heatmap ({len(labels)} documents)',
        xaxis_title='Documents',
        yaxis_title='Documents',
        height=max(600, len(labels) * 15),  # Dynamic height
        width=max(800, len(labels) * 15),
        template='plotly_white'
    )
    
    fig.update_xaxes(tickangle=45)
    
    return fig


def create_dimension_distribution(
    embedding: List[float],
    title: str = "Embedding Dimension Distribution"
) -> go.Figure:
    """
    Visualize distribution across embedding dimensions.
    
    Args:
        embedding: Single 768-dim vector
        title: Plot title
    
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
        line=dict(color='royalblue', width=1.5),
        fill='tozeroy',
        fillcolor='rgba(65, 105, 225, 0.2)'
    ))
    
    # Add statistical lines
    mean_val = np.mean(vector)
    std_val = np.std(vector)
    
    fig.add_hline(
        y=mean_val,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Mean: {mean_val:.4f}",
        annotation_position="right"
    )
    
    fig.add_hline(
        y=mean_val + std_val,
        line_dash="dot",
        line_color="orange",
        annotation_text=f"+1 σ: {mean_val + std_val:.4f}",
        annotation_position="right"
    )
    
    fig.add_hline(
        y=mean_val - std_val,
        line_dash="dot",
        line_color="orange",
        annotation_text=f"-1 σ: {mean_val - std_val:.4f}",
        annotation_position="right"
    )
    
    fig.update_layout(
        title=title,
        xaxis_title='Dimension Index (0-767)',
        yaxis_title='Value',
        height=500,
        showlegend=True,
        template='plotly_white',
        hovermode='x'
    )
    
    # Add statistics box
    stats_text = f"""
    <b>Statistics:</b><br>
    Dimensions: {len(vector)}<br>
    Mean: {mean_val:.4f}<br>
    Std Dev: {std_val:.4f}<br>
    Min: {np.min(vector):.4f}<br>
    Max: {np.max(vector):.4f}<br>
    L2 Norm: {np.linalg.norm(vector):.4f}
    """
    
    fig.add_annotation(
        text=stats_text,
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        xanchor='left', yanchor='top',
        showarrow=False,
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="black",
        borderwidth=1
    )
    
    return fig


def create_pca_plot(
    embeddings: List[List[float]],
    labels: List[str],
    metadata: Optional[List[Dict]] = None,
    n_components: int = 2,
    color_by: Optional[str] = None
) -> Tuple[go.Figure, List[float]]:
    """
    Create PCA projection of embeddings.
    
    Args:
        embeddings: List of 768-dim vectors
        labels: Labels for each point
        metadata: Additional metadata
        n_components: Number of components (2 or 3)
        color_by: Metadata field to color by
    
    Returns:
        Tuple of (Plotly figure, explained variance ratios)
    """
    from sklearn.decomposition import PCA
    
    if len(embeddings) < 2:
        raise ValueError("Need at least 2 embeddings for PCA")
    
    # Convert to numpy
    X = np.array(embeddings)
    
    # Apply PCA
    pca = PCA(n_components=n_components, random_state=42)
    X_pca = pca.fit_transform(X)
    
    # Create dataframe
    if n_components == 2:
        df = pd.DataFrame({
            'x': X_pca[:, 0],
            'y': X_pca[:, 1],
            'label': [str(l)[:80] for l in labels]
        })
        
        if metadata:
            for key in metadata[0].keys():
                df[key] = [str(m.get(key, 'N/A')) for m in metadata]
        
        color_col = None
        if color_by and metadata and color_by in metadata[0]:
            color_col = color_by
        
        var_exp = pca.explained_variance_ratio_
        
        fig = px.scatter(
            df,
            x='x',
            y='y',
            color=color_col,
            hover_data=['label'] + ([k for k in metadata[0].keys()] if metadata else []),
            title=f'PCA Projection of {len(embeddings)} Embeddings (2D)',
            labels={
                'x': f'PC1 ({var_exp[0]*100:.1f}% var)',
                'y': f'PC2 ({var_exp[1]*100:.1f}% var)'
            }
        )
        
        fig.update_traces(marker=dict(size=10, opacity=0.7, line=dict(width=0.5, color='white')))
    
    else:  # 3D
        df = pd.DataFrame({
            'x': X_pca[:, 0],
            'y': X_pca[:, 1],
            'z': X_pca[:, 2],
            'label': [str(l)[:80] for l in labels]
        })
        
        if metadata:
            for key in metadata[0].keys():
                df[key] = [str(m.get(key, 'N/A')) for m in metadata]
        
        color_col = None
        if color_by and metadata and color_by in metadata[0]:
            color_col = color_by
        
        var_exp = pca.explained_variance_ratio_
        
        fig = px.scatter_3d(
            df,
            x='x',
            y='y',
            z='z',
            color=color_col,
            hover_data=['label'] + ([k for k in metadata[0].keys()] if metadata else []),
            title=f'PCA Projection of {len(embeddings)} Embeddings (3D)',
            labels={
                'x': f'PC1 ({var_exp[0]*100:.1f}%)',
                'y': f'PC2 ({var_exp[1]*100:.1f}%)',
                'z': f'PC3 ({var_exp[2]*100:.1f}%)'
            }
        )
        
        fig.update_traces(marker=dict(size=5, opacity=0.7))
    
    fig.update_layout(
        height=700,
        hovermode='closest',
        template='plotly_white'
    )
    
    return fig, pca.explained_variance_ratio_.tolist()

