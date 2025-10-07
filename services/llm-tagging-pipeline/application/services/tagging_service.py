"""Tagging Application Service."""

import logging
from typing import List

from ...domain.entities.document import Document
from ...domain.entities.tagging_job import TaggingJob
from ...domain.entities.llm_metadata import LLMMetadata
from ...domain.services.tag_extractor import TagExtractorService
from ...domain.repositories.document_repository import DocumentRepository
from ...domain.repositories.job_repository import JobRepository
from ...infrastructure.llm.ollama_tagger import OllamaTagger

logger = logging.getLogger(__name__)


class TaggingService:
    """
    Application service for document tagging.
    
    Coordinates tagging operations across domain and infrastructure layers.
    """
    
    def __init__(
        self,
        document_repository: DocumentRepository,
        job_repository: JobRepository,
        ollama_tagger: OllamaTagger,
        tag_extractor: TagExtractorService
    ):
        """
        Initialize service.
        
        Args:
            document_repository: Document repository
            job_repository: Job repository
            ollama_tagger: Ollama tagger
            tag_extractor: Tag extractor service
        """
        self.document_repository = document_repository
        self.job_repository = job_repository
        self.ollama_tagger = ollama_tagger
        self.tag_extractor = tag_extractor
    
    async def tag_document(self, document: Document) -> Document:
        """
        Tag a single document.
        
        Args:
            document: Document to tag
            
        Returns:
            Tagged document
        """
        try:
            # Extract metadata using Ollama
            metadata = await self.ollama_tagger.tag_document(document)
            
            # Clean and validate metadata
            cleaned_keywords = self.tag_extractor.clean_keywords(metadata.keywords)
            cleaned_tags = self.tag_extractor.clean_tags(metadata.tags)
            cleaned_categories = self.tag_extractor.clean_categories(metadata.categories)
            
            # Update document
            document.set_summary(metadata.summary)
            document.add_keywords(cleaned_keywords)
            document.add_tags(cleaned_tags)
            document.add_categories(cleaned_categories)
            document.topics = metadata.topics
            document.entities = metadata.entities
            
            if metadata.sentiment:
                document.set_sentiment(metadata.sentiment)
            
            if metadata.complexity_score is not None:
                document.set_complexity_score(metadata.complexity_score)
            
            # Mark as tagged
            document.mark_as_tagged(
                model=metadata.model_name,
                confidence=metadata.get_overall_confidence()
            )
            
            # Validate
            document.validate()
            
            # Save
            await self.document_repository.update(document)
            
            logger.info(f"Successfully tagged document {document.document_id}")
            
            return document
            
        except Exception as e:
            logger.error(f"Error tagging document {document.document_id}: {e}")
            raise
    
    async def tag_batch(self, document_ids: List[str], job: TaggingJob) -> TaggingJob:
        """
        Tag a batch of documents.
        
        Args:
            document_ids: List of document IDs
            job: Tagging job
            
        Returns:
            Updated job
        """
        # Start job
        job.start()
        await self.job_repository.update(job)
        
        # Process documents
        for document_id in document_ids:
            try:
                # Get document
                document = await self.document_repository.get_by_id(document_id)
                if not document:
                    logger.warning(f"Document {document_id} not found")
                    job.record_document_processed(
                        document_id=document_id,
                        succeeded=False,
                        processing_time=0.0,
                        error="Document not found"
                    )
                    continue
                
                # Tag document
                import time
                start_time = time.time()
                
                tagged_document = await self.tag_document(document)
                
                processing_time = time.time() - start_time
                
                # Record success
                job.record_document_processed(
                    document_id=document_id,
                    succeeded=True,
                    processing_time=processing_time,
                    tokens_used=0,  # Would get from metadata
                )
                
            except Exception as e:
                logger.error(f"Error processing document {document_id}: {e}")
                job.record_document_processed(
                    document_id=document_id,
                    succeeded=False,
                    processing_time=0.0,
                    error=str(e)
                )
            
            # Update job after each document
            await self.job_repository.update(job)
        
        # Complete job
        job.complete()
        await self.job_repository.update(job)
        
        logger.info(
            f"Job {job.job_id} completed: "
            f"{job.documents_succeeded}/{job.total_documents} succeeded"
        )
        
        return job

