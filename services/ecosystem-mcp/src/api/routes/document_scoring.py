"""
Document Scoring API Endpoints

Provides endpoints for:
- Scoring individual documents
- Bulk scoring of existing documents
- Loading custom glossaries
- Viewing score statistics
"""

import logging
from typing import Optional, List, Set
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import select, update, and_

from ...storage import get_database
from ...storage.db_models import DocumentModel
from ...utils.document_scorer import (
    get_document_scorer,
    score_document,
    load_custom_glossary,
    DocumentScore
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ScoreDocumentRequest(BaseModel):
    """Request to score a single document."""
    document_id: str = Field(..., description="Document ID to score")


class BulkScoreRequest(BaseModel):
    """Request to score multiple documents."""
    document_ids: Optional[List[str]] = Field(None, description="Specific document IDs to score (optional)")
    score_all: bool = Field(False, description="Score all documents")
    only_unscored: bool = Field(True, description="Only score documents without scores")
    batch_size: int = Field(100, description="Batch size for commits")


class CustomGlossaryRequest(BaseModel):
    """Request to add custom glossary terms."""
    terms: List[str] = Field(..., description="Custom glossary terms to add")


class ScoreFilterRequest(BaseModel):
    """Request to filter documents by score."""
    min_score: Optional[float] = Field(None, description="Minimum quality score")
    max_score: Optional[float] = Field(None, description="Maximum quality score")
    grade: Optional[str] = Field(None, description="Quality grade (S, A, B, C, D, F)")
    limit: int = Field(50, description="Max results")


@router.post("/score")
async def score_single_document(request: ScoreDocumentRequest):
    """
    Score a single document.
    
    Calculates quality score and saves to database.
    
    Example:
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/score \
      -H 'Content-Type: application/json' \
      -d '{"document_id": "abc-123"}' | jq
    ```
    """
    try:
        async with get_database().session() as session:
            # Get document
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.id == request.document_id)
            )
            doc = result.scalar_one_or_none()
            
            if not doc:
                raise HTTPException(status_code=404, detail=f"Document {request.document_id} not found")
            
            # Score document
            logger.info(f"📊 Scoring document: {doc.file_path}")
            score_result = score_document(
                content=doc.normalized_content,
                file_path=doc.file_path,
                category=doc.doc_metadata.get("category")
            )
            
            # Update database
            doc.quality_score = score_result.total_score
            doc.quality_grade = score_result.quality_grade
            doc.score_breakdown = score_result.breakdown
            
            await session.commit()
            
            logger.info(
                f"✅ Scored {doc.file_path}: "
                f"{score_result.total_score:.1f} (Grade {score_result.quality_grade})"
            )
            
            return {
                "success": True,
                "document_id": str(doc.id),
                "file_path": doc.file_path,
                "score": score_result.total_score,
                "grade": score_result.quality_grade,
                "breakdown": score_result.breakdown,
                "reasoning": score_result.reasoning,
                "matched_terms": score_result.matched_terms[:10],  # First 10
                "matched_systems": score_result.matched_systems
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to score document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score/bulk")
async def score_documents_bulk(request: BulkScoreRequest):
    """
    Score multiple documents in bulk.
    
    Can score specific documents or all documents in database.
    
    Example (score all unscored):
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/score/bulk \
      -H 'Content-Type: application/json' \
      -d '{"score_all": true, "only_unscored": true}' | jq
    ```
    
    Example (score specific docs):
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/score/bulk \
      -H 'Content-Type: application/json' \
      -d '{"document_ids": ["abc-123", "def-456"]}' | jq
    ```
    """
    try:
        logger.info(f"📊 Starting bulk scoring (score_all={request.score_all})")
        
        async with get_database().session() as session:
            # Build query
            if request.document_ids:
                query = select(DocumentModel).where(DocumentModel.id.in_(request.document_ids))
            elif request.score_all:
                query = select(DocumentModel)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Must provide either document_ids or set score_all=true"
                )
            
            # Filter for unscored only
            if request.only_unscored:
                query = query.where(DocumentModel.quality_score.is_(None))
            
            result = await session.execute(query)
            documents = result.scalars().all()
            
            if not documents:
                return {
                    "success": True,
                    "message": "No documents to score",
                    "scored": 0,
                    "failed": 0
                }
            
            logger.info(f"📚 Found {len(documents)} documents to score")
            
            # Score documents
            scored_count = 0
            failed_count = 0
            scores_by_grade = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
            
            for i, doc in enumerate(documents):
                try:
                    # Score
                    score_result = score_document(
                        content=doc.normalized_content,
                        file_path=doc.file_path,
                        category=doc.doc_metadata.get("category")
                    )
                    
                    # Update
                    doc.quality_score = score_result.total_score
                    doc.quality_grade = score_result.quality_grade
                    doc.score_breakdown = score_result.breakdown
                    
                    scored_count += 1
                    scores_by_grade[score_result.quality_grade] += 1
                    
                    # Batch commit
                    if (i + 1) % request.batch_size == 0:
                        await session.commit()
                        logger.info(f"💾 Committed batch: {i + 1}/{len(documents)} documents")
                
                except Exception as e:
                    logger.error(f"Failed to score {doc.file_path}: {e}")
                    failed_count += 1
            
            # Final commit
            await session.commit()
            
            logger.info(
                f"✅ Bulk scoring complete: "
                f"{scored_count} scored, {failed_count} failed"
            )
            
            return {
                "success": True,
                "scored": scored_count,
                "failed": failed_count,
                "total_documents": len(documents),
                "scores_by_grade": scores_by_grade
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk scoring failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/score/statistics")
async def get_score_statistics():
    """
    Get statistics about document scores.
    
    Returns distribution, averages, and breakdowns.
    
    Example:
    ```bash
    curl http://localhost:8000/api/v1/documents/score/statistics | jq
    ```
    """
    try:
        async with get_database().session() as session:
            # Get all scored documents
            result = await session.execute(
                select(DocumentModel).where(DocumentModel.quality_score.isnot(None))
            )
            documents = result.scalars().all()
            
            if not documents:
                return {
                    "success": True,
                    "message": "No scored documents found",
                    "total_documents": 0
                }
            
            # Calculate statistics
            scores = [doc.quality_score for doc in documents]
            avg_score = sum(scores) / len(scores)
            
            # Grade distribution
            grade_dist = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
            for doc in documents:
                if doc.quality_grade:
                    grade_dist[doc.quality_grade] += 1
            
            # Score ranges
            score_ranges = {
                "90-100": len([s for s in scores if s >= 90]),
                "75-89": len([s for s in scores if 75 <= s < 90]),
                "60-74": len([s for s in scores if 60 <= s < 75]),
                "40-59": len([s for s in scores if 40 <= s < 60]),
                "20-39": len([s for s in scores if 20 <= s < 40]),
                "0-19": len([s for s in scores if s < 20])
            }
            
            # Top scoring documents
            top_docs = sorted(documents, key=lambda d: d.quality_score, reverse=True)[:10]
            top_list = [
                {
                    "file_path": doc.file_path,
                    "score": doc.quality_score,
                    "grade": doc.quality_grade
                }
                for doc in top_docs
            ]
            
            # Bottom scoring documents
            bottom_docs = sorted(documents, key=lambda d: d.quality_score)[:10]
            bottom_list = [
                {
                    "file_path": doc.file_path,
                    "score": doc.quality_score,
                    "grade": doc.quality_grade
                }
                for doc in bottom_docs
            ]
            
            return {
                "success": True,
                "total_scored": len(documents),
                "average_score": round(avg_score, 2),
                "min_score": min(scores),
                "max_score": max(scores),
                "grade_distribution": grade_dist,
                "score_ranges": score_ranges,
                "top_documents": top_list,
                "bottom_documents": bottom_list
            }
    
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score/custom-glossary")
async def add_custom_glossary(request: CustomGlossaryRequest):
    """
    Add custom glossary terms for scoring.
    
    These terms will be matched against documents and increase their scores.
    
    Example:
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/score/custom-glossary \
      -H 'Content-Type: application/json' \
      -d '{"terms": ["kubernetes", "helm", "argocd", "gitops"]}' | jq
    ```
    """
    try:
        # Add terms to scorer
        custom_terms = set(term.lower() for term in request.terms)
        
        # Reinitialize scorer with custom terms
        scorer = get_document_scorer(custom_glossary=custom_terms)
        
        logger.info(f"📖 Added {len(custom_terms)} custom glossary terms")
        
        return {
            "success": True,
            "terms_added": len(custom_terms),
            "terms": sorted(list(custom_terms))
        }
    
    except Exception as e:
        logger.error(f"Failed to add custom glossary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score/filter")
async def filter_by_score(request: ScoreFilterRequest):
    """
    Filter documents by quality score or grade.
    
    Example (get all A-grade docs):
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/score/filter \
      -H 'Content-Type: application/json' \
      -d '{"grade": "A", "limit": 20}' | jq
    ```
    
    Example (get high-scoring docs):
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/score/filter \
      -H 'Content-Type: application/json' \
      -d '{"min_score": 80, "limit": 50}' | jq
    ```
    """
    try:
        async with get_database().session() as session:
            # Build query
            query = select(DocumentModel).where(DocumentModel.quality_score.isnot(None))
            
            # Apply filters
            if request.min_score is not None:
                query = query.where(DocumentModel.quality_score >= request.min_score)
            
            if request.max_score is not None:
                query = query.where(DocumentModel.quality_score <= request.max_score)
            
            if request.grade:
                query = query.where(DocumentModel.quality_grade == request.grade.upper())
            
            # Order by score descending
            query = query.order_by(DocumentModel.quality_score.desc()).limit(request.limit)
            
            result = await session.execute(query)
            documents = result.scalars().all()
            
            # Format results
            docs_list = [
                {
                    "id": str(doc.id),
                    "file_path": doc.file_path,
                    "score": doc.quality_score,
                    "grade": doc.quality_grade,
                    "breakdown": doc.score_breakdown,
                    "is_latest": doc.is_latest,
                    "service_name": doc.service_name
                }
                for doc in documents
            ]
            
            return {
                "success": True,
                "count": len(docs_list),
                "documents": docs_list
            }
    
    except Exception as e:
        logger.error(f"Failed to filter documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/score/upload-glossary")
async def upload_glossary_file(file: UploadFile = File(...)):
    """
    Upload a custom glossary file.
    
    File format: One term per line, lines starting with # are comments.
    
    Example:
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/score/upload-glossary \
      -F "file=@my_glossary.txt" | jq
    ```
    """
    try:
        # Read file content
        content = await file.read()
        text = content.decode('utf-8')
        
        # Parse terms
        terms = set()
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                terms.add(line.lower())
        
        if not terms:
            raise HTTPException(status_code=400, detail="No valid terms found in file")
        
        # Add to scorer
        scorer = get_document_scorer(custom_glossary=terms)
        
        logger.info(f"📖 Loaded {len(terms)} terms from uploaded glossary")
        
        return {
            "success": True,
            "terms_loaded": len(terms),
            "sample_terms": sorted(list(terms))[:20]  # First 20
        }
    
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded text")
    except Exception as e:
        logger.error(f"Failed to upload glossary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

