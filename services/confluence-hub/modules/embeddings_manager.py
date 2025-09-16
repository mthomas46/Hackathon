"""Embeddings manager for generating and managing document embeddings."""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone

from .openai_service import OpenAIService
from .vector_search_service import VectorSearchService

logger = logging.getLogger(__name__)


class EmbeddingsManager:
    """Manager for generating and managing document embeddings."""
    
    def __init__(self, openai_api_key: str, mongodb_client, vector_search_service: VectorSearchService):
        """Initialize the embeddings manager.
        
        Args:
            openai_api_key: OpenAI API key
            mongodb_client: MongoDB client instance
            vector_search_service: Vector search service instance
        """
        self.openai_service = OpenAIService(openai_api_key)
        self.mongodb_client = mongodb_client
        self.vector_search_service = vector_search_service
        self.initialized = False
        
    async def initialize(self) -> None:
        """Initialize the embeddings manager."""
        try:
            # Initialize OpenAI service
            await self.openai_service.initialize()
            
            # Check if OpenAI service was successfully initialized
            if not self.openai_service.initialized:
                logger.warning("OpenAI service failed to initialize, embeddings manager will be limited")
                self.initialized = False
                return
            
            # Initialize vector search service
            await self.vector_search_service.initialize(self.mongodb_client)
            
            self.initialized = True
            logger.info("Embeddings manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize embeddings manager: {str(e)}")
            self.initialized = False
            logger.warning("Embeddings manager will be unavailable")
    
    async def get_embedding_statistics(self) -> Dict[str, int]:
        """Get statistics about embeddings in the database.
        
        Returns:
            Dictionary with embedding statistics
        """
        try:
            total_documents = await self.mongodb_client.count_pages()
            documents_with_embeddings = await self.mongodb_client.count_pages_with_embeddings()
            documents_without_embeddings = total_documents - documents_with_embeddings
            
            return {
                "total_documents": total_documents,
                "documents_with_embeddings": documents_with_embeddings,
                "documents_without_embeddings": documents_without_embeddings
            }
            
        except Exception as e:
            logger.error(f"Error getting embedding statistics: {str(e)}")
            raise
    
    async def generate_embeddings_for_all_pages(
        self, 
        batch_size: int = 5,
        skip_existing: bool = True
    ) -> Dict[str, any]:
        """Generate embeddings for all pages in the database.
        
        Args:
            batch_size: Number of documents to process in parallel
            skip_existing: Whether to skip documents that already have embeddings
            
        Returns:
            Dictionary with generation results
        """
        if not self.initialized:
            raise ValueError("Embeddings manager not initialized. Call initialize() first.")
        
        logger.info("Starting embeddings generation for all pages...")
        
        start_time = datetime.now()
        
        try:
            # Get statistics
            stats = await self.get_embedding_statistics()
            logger.info(f"Embedding statistics: {stats}")
            
            if skip_existing and stats["documents_without_embeddings"] == 0:
                logger.info("All documents already have embeddings!")
                return {
                    "success": True,
                    "message": "All documents already have embeddings",
                    "statistics": stats,
                    "processing_time_seconds": 0
                }
            
            # Get documents that need embeddings
            if skip_existing:
                documents = await self.mongodb_client.get_pages_without_embeddings()
            else:
                documents = await self.mongodb_client.get_all_pages()
            
            logger.info(f"Processing {len(documents)} documents in batches of {batch_size}")
            
            success_count = 0
            error_count = 0
            errors = []
            
            # Process documents in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                batch_number = (i // batch_size) + 1
                total_batches = (len(documents) + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_number}/{total_batches}...")
                
                # Process batch in parallel
                batch_tasks = []
                for doc in batch:
                    task = self._process_document_embedding(doc)
                    batch_tasks.append(task)
                
                # Wait for batch to complete
                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
                
                # Process results
                for j, result in enumerate(batch_results):
                    doc = batch[j]
                    if isinstance(result, Exception):
                        error_count += 1
                        error_msg = str(result)
                        errors.append({"title": doc.get("title", "Unknown"), "error": error_msg})
                        logger.error(f"Failed to process {doc.get('title', 'Unknown')}: {error_msg}")
                    else:
                        success_count += 1
                        logger.info(f"✓ Generated embedding for: {doc.get('title', 'Unknown')}")
                
                # Progress update
                processed = min(i + batch_size, len(documents))
                percentage = (processed / len(documents)) * 100
                logger.info(f"Progress: {processed}/{len(documents)} ({percentage:.1f}%)")
                
                # Add delay between batches to respect rate limits
                if i + batch_size < len(documents):
                    logger.info("Waiting 2 seconds before next batch...")
                    await asyncio.sleep(2)
            
            # Refresh vector search cache with new embeddings
            logger.info("Refreshing vector search cache...")
            await self.vector_search_service.refresh(self.mongodb_client)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Final statistics
            final_stats = await self.get_embedding_statistics()
            
            result = {
                "success": True,
                "message": f"Generated embeddings for {success_count} documents",
                "statistics": {
                    "initial": stats,
                    "final": final_stats,
                    "processed": len(documents),
                    "successful": success_count,
                    "failed": error_count
                },
                "processing_time_seconds": processing_time,
                "errors": errors if errors else None
            }
            
            logger.info(f"Embeddings generation complete! Processed {success_count}/{len(documents)} documents in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during embeddings generation: {str(e)}")
            raise
    
    async def _process_document_embedding(self, document: Dict) -> None:
        """Process embedding for a single document.
        
        Args:
            document: Document dictionary from MongoDB
        """
        try:
            doc_id = str(document["_id"])
            title = document.get("title", "")
            content = document.get("content", "")
            confluence_page_id = document.get("confluence_page_id", "")
            
            # Combine title and content for embedding
            text_for_embedding = f"{title}\n\n{content}".strip()
            
            if not text_for_embedding:
                raise ValueError("Document has no content to generate embedding from")
            
            # Generate embedding
            embedding = await self.openai_service.generate_embedding(text_for_embedding)
            
            # Store embedding in database
            await self.mongodb_client.update_page_embedding(doc_id, embedding)
            
            # Update vector search cache
            await self.vector_search_service.update_vector(
                document_id=doc_id,
                embedding=embedding,
                title=title,
                confluence_page_id=confluence_page_id
            )
            
        except Exception as e:
            logger.error(f"Error processing document {document.get('_id', 'Unknown')}: {str(e)}")
            raise
    
    async def generate_embedding_for_page(self, page_id: str) -> Dict[str, any]:
        """Generate embedding for a specific page.
        
        Args:
            page_id: MongoDB document ID
            
        Returns:
            Dictionary with generation result
        """
        if not self.initialized:
            raise ValueError("Embeddings manager not initialized. Call initialize() first.")
        
        try:
            # Get the document
            document = await self.mongodb_client.get_page_by_id(page_id)
            if not document:
                raise ValueError(f"Document with ID {page_id} not found")
            
            # Process the document
            await self._process_document_embedding(document)
            
            return {
                "success": True,
                "message": f"Generated embedding for page: {document.get('title', 'Unknown')}",
                "page_id": page_id,
                "title": document.get("title", "Unknown")
            }
            
        except Exception as e:
            logger.error(f"Error generating embedding for page {page_id}: {str(e)}")
            raise
    
    async def search_similar_documents(
        self, 
        query_text: str, 
        limit: int = 5, 
        min_score: float = 0.15
    ) -> List[Dict[str, any]]:
        """Search for documents similar to the query text.
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results
            min_score: Minimum similarity score threshold
            
        Returns:
            List of similar documents
        """
        if not self.initialized:
            raise ValueError("Embeddings manager not initialized. Call initialize() first.")
        
        try:
            # Generate embedding for query text
            query_embedding = await self.openai_service.generate_embedding(query_text)
            
            # Search for similar documents
            matches = await self.vector_search_service.search_similar(
                query_embedding=query_embedding,
                limit=limit,
                min_score=min_score
            )
            
            # Convert to dictionaries and add additional info
            results = []
            for match in matches:
                # Get full document details
                document = await self.mongodb_client.get_page_by_id(match.document_id)
                if document:
                    results.append({
                        "document_id": match.document_id,
                        "title": match.title,
                        "confluence_page_id": match.confluence_page_id,
                        "similarity_score": match.score,
                        "content_preview": document.get("content", "")[:200] + "...",
                        "metadata": document.get("metadata", {})
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching similar documents: {str(e)}")
            raise
    
    async def get_service_status(self) -> Dict[str, any]:
        """Get status of all embeddings services.
        
        Returns:
            Dictionary with service status information
        """
        try:
            stats = await self.get_embedding_statistics()
            vector_stats = self.vector_search_service.get_stats()
            
            return {
                "initialized": self.initialized,
                "openai_service_initialized": self.openai_service.initialized,
                "vector_search_initialized": self.vector_search_service.is_initialized(),
                "embedding_model": self.openai_service.model,
                "embedding_dimension": self.openai_service.get_embedding_dimension(),
                "database_statistics": stats,
                "vector_cache_statistics": vector_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting service status: {str(e)}")
            raise
    
    async def close(self) -> None:
        """Close all services."""
        try:
            await self.openai_service.close()
            logger.info("Embeddings manager closed")
        except Exception as e:
            logger.error(f"Error closing embeddings manager: {str(e)}")