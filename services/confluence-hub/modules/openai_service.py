"""OpenAI service for generating embeddings."""

import asyncio
import logging
from typing import List, Optional
import openai
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for interacting with OpenAI API to generate embeddings."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """Initialize OpenAI service.
        
        Args:
            api_key: OpenAI API key
            model: Embedding model to use (default: text-embedding-3-small)
        """
        self.api_key = api_key
        self.model = model
        self.client: Optional[AsyncOpenAI] = None
        self.initialized = False
        
    async def initialize(self) -> None:
        """Initialize the OpenAI client."""
        try:
            # Try different initialization approaches to handle version conflicts
            try:
                # First attempt: Standard initialization
                self.client = AsyncOpenAI(api_key=self.api_key)
            except TypeError as te:
                if "proxies" in str(te):
                    # Second attempt: Handle the proxies argument issue
                    logger.warning("OpenAI client proxies argument issue detected, trying alternative initialization")
                    # Try creating without any extra parameters
                    import openai
                    self.client = openai.AsyncOpenAI(api_key=self.api_key)
                else:
                    raise te
            
            # Test the connection by getting available models
            models = await self.client.models.list()
            logger.info(f"OpenAI service initialized successfully. Available models: {len(models.data)}")
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI service: {str(e)}")
            # Don't raise an exception, just mark as uninitialized
            self.initialized = False
            self.client = None
            logger.warning("OpenAI service will be unavailable due to initialization failure")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a given text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            ValueError: If service not initialized or text is empty
            Exception: If OpenAI API call fails
        """
        if not self.initialized or not self.client:
            raise ValueError("OpenAI service not initialized. Call initialize() first.")
        
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Truncate text if too long (OpenAI has token limits)
        max_chars = 8000  # Conservative limit to stay under token limits
        if len(text) > max_chars:
            text = text[:max_chars]
            logger.warning(f"Text truncated to {max_chars} characters for embedding generation")
        
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts to process in each API call
            
        Returns:
            List of embedding vectors
        """
        if not self.initialized or not self.client:
            raise ValueError("OpenAI service not initialized. Call initialize() first.")
        
        if not texts:
            return []
        
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            for text in batch:
                try:
                    embedding = await self.generate_embedding(text)
                    batch_embeddings.append(embedding)
                    
                    # Add small delay to respect rate limits
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Failed to generate embedding for text batch item: {str(e)}")
                    # Add empty embedding to maintain index alignment
                    batch_embeddings.append([])
            
            embeddings.extend(batch_embeddings)
            
            # Add delay between batches
            if i + batch_size < len(texts):
                await asyncio.sleep(1)
        
        return embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension size of embeddings for the current model.
        
        Returns:
            Embedding dimension size
        """
        # text-embedding-3-small produces 1536-dimensional embeddings
        # text-embedding-3-large produces 3072-dimensional embeddings
        if "large" in self.model:
            return 3072
        else:
            return 1536
    
    async def close(self) -> None:
        """Close the OpenAI client connection."""
        if self.client:
            await self.client.close()
            self.initialized = False
            logger.info("OpenAI service connection closed")