"""
Documentation Run Manager

Manages documentation generation runs, persisting configuration,
progress, and generated documents.
"""

import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class DocumentationRun:
    """Represents a documentation generation run."""
    
    def __init__(
        self,
        id: UUID,
        name: str,
        description: str,
        status: str,
        source_directory: str,
        output_format: str,
        response_size: Optional[str],
        tier: Optional[str],
        num_passes: int,
        questions_per_pass: int,
        started_at: Optional[datetime],
        completed_at: Optional[datetime],
        duration_seconds: Optional[int],
        total_documents: int,
        successful_documents: int,
        failed_documents: int,
        output_directory: Optional[str],
        created_by: Optional[str],
        created_at: datetime,
        metadata: Optional[Dict] = None
    ):
        self.id = id
        self.name = name
        self.description = description
        self.status = status
        self.source_directory = source_directory
        self.output_format = output_format
        self.response_size = response_size
        self.tier = tier
        self.num_passes = num_passes
        self.questions_per_pass = questions_per_pass
        self.started_at = started_at
        self.completed_at = completed_at
        self.duration_seconds = duration_seconds
        self.total_documents = total_documents
        self.successful_documents = successful_documents
        self.failed_documents = failed_documents
        self.output_directory = output_directory
        self.created_by = created_by
        self.created_at = created_at
        self.metadata = metadata or {}


class GeneratedDocument:
    """Represents a generated document."""
    
    def __init__(
        self,
        id: UUID,
        run_id: UUID,
        title: str,
        filename: str,
        file_path: str,
        content: str,
        content_hash: str,
        content_size: int,
        pass_number: Optional[int],
        question: Optional[str],
        status: str,
        generation_time_seconds: Optional[float],
        word_count: Optional[int],
        created_at: datetime
    ):
        self.id = id
        self.run_id = run_id
        self.title = title
        self.filename = filename
        self.file_path = file_path
        self.content = content
        self.content_hash = content_hash
        self.content_size = content_size
        self.pass_number = pass_number
        self.question = question
        self.status = status
        self.generation_time_seconds = generation_time_seconds
        self.word_count = word_count
        self.created_at = created_at


class DocumentationRunManager:
    """
    Manages documentation generation runs.
    
    Features:
    - Create and track runs
    - Store generated documents
    - Real-time progress updates
    - Run history and statistics
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    async def create_run(
        self,
        name: str,
        description: str,
        source_directory: str,
        output_format: str = "markdown",
        response_size: Optional[str] = None,
        tier: Optional[str] = None,
        num_passes: int = 3,
        questions_per_pass: int = 5,
        created_by: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> UUID:
        """
        Create a new documentation run.
        
        Returns:
            UUID of the created run
        """
        try:
            run_id = uuid4()
            
            # Calculate config hash for deduplication
            config_str = f"{source_directory}:{output_format}:{response_size}:{tier}:{num_passes}:{questions_per_pass}"
            config_hash = hashlib.sha256(config_str.encode()).hexdigest()
            
            query = text("""
                INSERT INTO documentation_runs (
                    id, name, description, status, source_directory, output_format,
                    response_size, tier, num_passes, questions_per_pass,
                    config_hash, created_by, metadata
                )
                VALUES (
                    :id, :name, :description, :status, :source_directory, :output_format,
                    :response_size, :tier, :num_passes, :questions_per_pass,
                    :config_hash, :created_by, :metadata
                )
                RETURNING id
            """)
            
            result = await self.db.execute(
                query,
                {
                    "id": run_id,
                    "name": name,
                    "description": description,
                    "status": "pending",
                    "source_directory": source_directory,
                    "output_format": output_format,
                    "response_size": response_size,
                    "tier": tier,
                    "num_passes": num_passes,
                    "questions_per_pass": questions_per_pass,
                    "config_hash": config_hash,
                    "created_by": created_by,
                    "metadata": metadata
                }
            )
            
            await self.db.commit()
            
            self.logger.info(f"Created documentation run: {run_id} - {name}")
            return run_id
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to create run: {e}", exc_info=True)
            raise
    
    async def start_run(self, run_id: UUID, output_directory: str):
        """Mark run as started."""
        try:
            query = text("""
                UPDATE documentation_runs
                SET status = 'running', started_at = NOW(), output_directory = :output_dir
                WHERE id = :run_id
            """)
            
            await self.db.execute(query, {"run_id": run_id, "output_dir": output_directory})
            await self.db.commit()
            
            self.logger.info(f"Started run: {run_id}")
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to start run: {e}", exc_info=True)
            raise
    
    async def complete_run(
        self,
        run_id: UUID,
        status: str = "completed",
        total_docs: Optional[int] = None,
        successful_docs: Optional[int] = None,
        failed_docs: Optional[int] = None
    ):
        """Mark run as completed or failed."""
        try:
            query = text("""
                SELECT update_documentation_run_status(
                    :run_id, :status, :total_docs, :successful_docs, :failed_docs
                )
            """)
            
            await self.db.execute(
                query,
                {
                    "run_id": run_id,
                    "status": status,
                    "total_docs": total_docs,
                    "successful_docs": successful_docs,
                    "failed_docs": failed_docs
                }
            )
            
            await self.db.commit()
            
            self.logger.info(f"Completed run: {run_id} with status: {status}")
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to complete run: {e}", exc_info=True)
            raise
    
    async def add_document(
        self,
        run_id: UUID,
        title: str,
        filename: str,
        content: str,
        pass_number: Optional[int] = None,
        question: Optional[str] = None,
        generation_time_seconds: Optional[float] = None,
        source_files: Optional[List[str]] = None
    ) -> UUID:
        """
        Add a generated document to a run.
        
        Returns:
            UUID of the created document
        """
        try:
            doc_id = uuid4()
            
            # Calculate content hash and metrics
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            content_size = len(content.encode())
            word_count = len(content.split())
            
            # Determine file path
            file_path = f"{filename}"
            
            query = text("""
                INSERT INTO generated_documents (
                    id, run_id, title, filename, file_path, content,
                    content_hash, content_size, pass_number, question,
                    generation_time_seconds, word_count, source_files, status
                )
                VALUES (
                    :id, :run_id, :title, :filename, :file_path, :content,
                    :content_hash, :content_size, :pass_number, :question,
                    :generation_time, :word_count, :source_files, :status
                )
                RETURNING id
            """)
            
            await self.db.execute(
                query,
                {
                    "id": doc_id,
                    "run_id": run_id,
                    "title": title,
                    "filename": filename,
                    "file_path": file_path,
                    "content": content,
                    "content_hash": content_hash,
                    "content_size": content_size,
                    "pass_number": pass_number,
                    "question": question,
                    "generation_time": generation_time_seconds,
                    "word_count": word_count,
                    "source_files": source_files,
                    "status": "generated"
                }
            )
            
            await self.db.commit()
            
            self.logger.info(f"Added document to run {run_id}: {filename}")
            return doc_id
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to add document: {e}", exc_info=True)
            raise
    
    async def update_progress(
        self,
        run_id: UUID,
        current_pass: int,
        total_passes: int,
        current_question: int,
        total_questions: int,
        current_operation: str,
        docs_generated: int,
        docs_failed: int
    ):
        """Update real-time progress for a run."""
        try:
            query = text("""
                SELECT update_run_progress(
                    :run_id, :current_pass, :total_passes, :current_question,
                    :total_questions, :current_operation, :docs_generated, :docs_failed
                )
            """)
            
            await self.db.execute(
                query,
                {
                    "run_id": run_id,
                    "current_pass": current_pass,
                    "total_passes": total_passes,
                    "current_question": current_question,
                    "total_questions": total_questions,
                    "current_operation": current_operation,
                    "docs_generated": docs_generated,
                    "docs_failed": docs_failed
                }
            )
            
            await self.db.commit()
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to update progress: {e}", exc_info=True)
            # Don't raise - progress updates are non-critical
    
    async def get_run(self, run_id: UUID) -> Optional[Dict]:
        """Get run details."""
        try:
            query = text("""
                SELECT * FROM documentation_runs WHERE id = :run_id
            """)
            
            result = await self.db.execute(query, {"run_id": run_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            return dict(row._mapping)
            
        except Exception as e:
            self.logger.error(f"Failed to get run: {e}", exc_info=True)
            raise
    
    async def list_runs(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """List documentation runs."""
        try:
            if status:
                query = text("""
                    SELECT * FROM documentation_run_summary
                    WHERE status = :status
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                params = {"status": status, "limit": limit, "offset": offset}
            else:
                query = text("""
                    SELECT * FROM documentation_run_summary
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                params = {"limit": limit, "offset": offset}
            
            result = await self.db.execute(query, params)
            rows = result.fetchall()
            
            return [dict(row._mapping) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Failed to list runs: {e}", exc_info=True)
            raise
    
    async def get_run_documents(
        self,
        run_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Get documents for a run."""
        try:
            query = text("""
                SELECT * FROM generated_documents
                WHERE run_id = :run_id
                ORDER BY created_at ASC
                LIMIT :limit OFFSET :offset
            """)
            
            result = await self.db.execute(
                query,
                {"run_id": run_id, "limit": limit, "offset": offset}
            )
            rows = result.fetchall()
            
            return [dict(row._mapping) for row in rows]
            
        except Exception as e:
            self.logger.error(f"Failed to get run documents: {e}", exc_info=True)
            raise
    
    async def get_run_progress(self, run_id: UUID) -> Optional[Dict]:
        """Get current progress for a run."""
        try:
            query = text("""
                SELECT * FROM documentation_run_progress WHERE run_id = :run_id
            """)
            
            result = await self.db.execute(query, {"run_id": run_id})
            row = result.fetchone()
            
            if not row:
                return None
            
            return dict(row._mapping)
            
        except Exception as e:
            self.logger.error(f"Failed to get run progress: {e}", exc_info=True)
            raise
    
    async def delete_run(self, run_id: UUID):
        """Delete a run and all its documents."""
        try:
            query = text("""
                DELETE FROM documentation_runs WHERE id = :run_id
            """)
            
            await self.db.execute(query, {"run_id": run_id})
            await self.db.commit()
            
            self.logger.info(f"Deleted run: {run_id}")
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Failed to delete run: {e}", exc_info=True)
            raise

