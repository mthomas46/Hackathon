"""
FAISS Vector Store for Fast Similarity Search

Provides 5-10x faster similarity search compared to ChromaDB for large document collections.

Usage:
    from services.rag.faiss_vector_store import FA ISSVectorStore
    
    # Create store
    store = FAISSVectorStore(dimension=768)
    
    # Add documents
    store.add_documents(documents, embeddings)
    
    # Search
    results = store.search(query_embedding, k=10)
    
    # Save/Load
    store.save("data/faiss_index")
    store.load("data/faiss_index")
"""

import logging
import pickle
from typing import List, Dict, Tuple, Optional
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store for fast similarity search."""
    
    def __init__(self, dimension: int = 768, index_type: str = "IndexFlatL2"):
        """
        Initialize FAISS index.
        
        Args:
            dimension: Embedding dimension (768 for sentence-transformers)
            index_type: FAISS index type:
                - IndexFlatL2: Exact search (best for < 100K docs)
                - IndexHNSWFlat: Hierarchical Navigable Small World (faster, approximate)
        
        Raises:
            ImportError: If FAISS is not installed
        """
        if not FAISS_AVAILABLE:
            raise ImportError(
                "FAISS is not installed. Install with: pip install faiss-cpu"
            )
        
        self.dimension = dimension
        self.index_type = index_type
        
        # Create FAISS index
        if index_type == "IndexFlatL2":
            self.index = faiss.IndexFlatL2(dimension)
        elif index_type == "IndexHNSWFlat":
            self.index = faiss.IndexHNSWFlat(dimension, 32)
        else:
            raise ValueError(f"Unknown index type: {index_type}")
        
        # Document ID mapping (FAISS indices → document metadata)
        self.id_to_doc: Dict[int, Dict] = {}
        self.doc_count = 0
        
        logger.info(f"✅ FAISS vector store initialized ({index_type}, dim={dimension})")
    
    def add_documents(self, documents: List[Dict], embeddings: np.ndarray):
        """
        Add documents and their embeddings to the index.
        
        Args:
            documents: List of document metadata dicts
            embeddings: numpy array of shape (n_docs, dimension)
        
        Raises:
            ValueError: If number of documents doesn't match embeddings
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Number of documents ({len(documents)}) must match "
                f"number of embeddings ({len(embeddings)})"
            )
        
        # Ensure embeddings are float32 (FAISS requirement)
        embeddings = embeddings.astype('float32')
        
        # Add embeddings to FAISS index
        self.index.add(embeddings)
        
        # Store document metadata (map FAISS internal indices to our docs)
        for i, doc in enumerate(documents):
            doc_id = self.doc_count + i
            self.id_to_doc[doc_id] = doc
        
        self.doc_count += len(documents)
        logger.info(f"✅ Added {len(documents)} documents (total: {self.doc_count})")
    
    def search(
        self,
        query_embedding: np.ndarray,
        k: int = 10
    ) -> List[Tuple[Dict, float]]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector (1D or 2D array)
            k: Number of results to return
        
        Returns:
            List of (document, similarity_score) tuples
            similarity_score is 0.0-1.0 (higher is better)
        """
        # Ensure query is 2D array
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Ensure float32
        query_embedding = query_embedding.astype('float32')
        
        # Search FAISS index
        # Returns: distances (L2), indices (internal FAISS IDs)
        distances, indices = self.index.search(query_embedding, k)
        
        # Convert to results
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            # Skip invalid indices
            if idx < 0 or idx >= self.doc_count:
                continue
            
            # Get document
            doc = self.id_to_doc.get(int(idx))
            if doc:
                # Convert L2 distance to similarity score (0-1)
                # Lower distance = higher similarity
                # Formula: similarity = 1 / (1 + distance)
                similarity = 1.0 / (1.0 + float(dist))
                results.append((doc, similarity))
        
        return results
    
    def save(self, path: str):
        """
        Save index and metadata to disk.
        
        Args:
            path: Base path (will create .faiss and .metadata.pkl files)
        """
        # Save FAISS index
        faiss.write_index(self.index, f"{path}.faiss")
        
        # Save metadata
        with open(f"{path}.metadata.pkl", "wb") as f:
            pickle.dump({
                "dimension": self.dimension,
                "index_type": self.index_type,
                "id_to_doc": self.id_to_doc,
                "doc_count": self.doc_count
            }, f)
        
        logger.info(f"✅ Saved FAISS index to {path}")
    
    def load(self, path: str):
        """
        Load index and metadata from disk.
        
        Args:
            path: Base path (will read .faiss and .metadata.pkl files)
        """
        # Load FAISS index
        self.index = faiss.read_index(f"{path}.faiss")
        
        # Load metadata
        with open(f"{path}.metadata.pkl", "rb") as f:
            metadata = pickle.load(f)
            self.dimension = metadata["dimension"]
            self.index_type = metadata["index_type"]
            self.id_to_doc = metadata["id_to_doc"]
            self.doc_count = metadata["doc_count"]
        
        logger.info(f"✅ Loaded FAISS index from {path} ({self.doc_count} docs)")
    
    def get_stats(self) -> Dict:
        """Get statistics about the index."""
        return {
            "doc_count": self.doc_count,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "memory_usage_mb": self.index.ntotal * self.dimension * 4 / (1024 * 1024)  # float32 = 4 bytes
        }


def is_faiss_available() -> bool:
    """Check if FAISS is installed and available."""
    return FAISS_AVAILABLE


# Singleton instance (optional)
_faiss_store: Optional[FAISSVectorStore] = None


def get_faiss_store(
    dimension: int = 768,
    index_type: str = "IndexFlatL2",
    force_new: bool = False
) -> FAISSVectorStore:
    """
    Get or create singleton FAISS store instance.
    
    Args:
        dimension: Embedding dimension
        index_type: FAISS index type
        force_new: Force creation of new instance
    
    Returns:
        FAISSVectorStore instance
    """
    global _faiss_store
    
    if _faiss_store is None or force_new:
        _faiss_store = FAISSVectorStore(dimension=dimension, index_type=index_type)
    
    return _faiss_store

