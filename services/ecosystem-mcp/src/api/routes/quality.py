"""
Quality Validation API Routes

Endpoints for documentation quality validation, scoring, and review workflow.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from ...services.quality import (
    get_completeness_checker,
    get_accuracy_validator,
    get_confidence_scorer,
    get_review_workflow_manager,
    get_quality_reporter,
    ReviewStatus
)
from ...storage.database import get_db
from ...storage.models_quality import QualityCheckModel, QualityReportModel
from ...storage.models_documentation import DocumentationArtifactModel, DocumentationRunModel

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models

class ValidateArtifactRequest(BaseModel):
    """Request to validate a single artifact."""
    artifact_id: str = Field(..., description="Documentation artifact ID")
    source_quality: Optional[float] = Field(None, ge=0, le=1, description="Optional source quality score")


class ValidateArtifactResponse(BaseModel):
    """Response from artifact validation."""
    success: bool
    artifact_id: str
    completeness_score: float
    accuracy_score: float
    overall_confidence: float
    requires_review: bool
    review_priority: str
    recommendations: List[str]
    quality_check_id: str


class ValidateRunRequest(BaseModel):
    """Request to validate entire documentation run."""
    run_id: str = Field(..., description="Documentation run ID")


class ValidateRunResponse(BaseModel):
    """Response from run validation."""
    success: bool
    run_id: str
    total_artifacts: int
    validated_artifacts: int
    average_completeness: float
    average_accuracy: float
    average_confidence: float
    artifacts_requiring_review: int
    report_id: str


class QualityReportResponse(BaseModel):
    """Quality report response."""
    report_id: str
    run_id: str
    total_artifacts: int
    average_completeness: float
    average_accuracy: float
    average_confidence: float
    total_issues: int
    critical_issues: int
    artifacts_requiring_review: int
    review_priority_breakdown: dict
    top_recommendations: List[str]
    generated_at: str


class ReviewQueueItem(BaseModel):
    """Review queue item."""
    review_id: str
    artifact_id: str
    artifact_title: str
    confidence_score: float
    priority: str
    status: str
    issues: List[str]
    recommendations: List[str]
    created_at: str


class AssignReviewRequest(BaseModel):
    """Request to assign review."""
    reviewer: str = Field(..., description="Reviewer identifier")


class CompleteReviewRequest(BaseModel):
    """Request to complete review."""
    status: str = Field(..., description="Review status: approved, rejected, needs_revision")
    reviewer_notes: Optional[str] = Field(None, description="Optional reviewer notes")


# Endpoints

@router.post("/validate", response_model=ValidateArtifactResponse)
async def validate_artifact(
    request: ValidateArtifactRequest,
    db = Depends(get_db)
):
    """
    Validate a single documentation artifact.
    
    Performs:
    - Completeness checking
    - Accuracy validation
    - Confidence scoring
    - Review determination
    """
    try:
        logger.info(f"Validating artifact: {request.artifact_id}")
        
        # Get artifact from database
        artifact_model = db.query(DocumentationArtifactModel).filter(
            DocumentationArtifactModel.id == UUID(request.artifact_id)
        ).first()
        
        if not artifact_model:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        # Convert to dict for validation
        artifact_dict = {
            'title': artifact_model.title,
            'content': artifact_model.content,
            'type': artifact_model.type,
            'word_count': artifact_model.word_count
        }
        
        # Run quality checks
        completeness_checker = get_completeness_checker()
        accuracy_validator = get_accuracy_validator()
        confidence_scorer = get_confidence_scorer()
        
        completeness_result = await completeness_checker.check(artifact_dict)
        accuracy_result = await accuracy_validator.validate(artifact_dict)
        confidence_score = await confidence_scorer.score(
            artifact_dict,
            completeness_result,
            accuracy_result,
            source_quality=request.source_quality
        )
        
        # Save to database
        quality_check = QualityCheckModel(
            run_id=artifact_model.run_id,
            artifact_id=artifact_model.id,
            completeness_score=completeness_result.overall_score,
            missing_sections=completeness_result.missing_sections,
            incomplete_sections=completeness_result.incomplete_sections,
            placeholder_count=completeness_result.placeholder_count,
            broken_links=completeness_result.broken_links,
            formatting_issues=completeness_result.formatting_issues,
            section_word_counts=completeness_result.section_word_counts,
            has_code_examples=completeness_result.has_code_examples,
            accuracy_score=accuracy_result.overall_score,
            code_example_issues=accuracy_result.code_example_issues,
            api_mismatches=accuracy_result.api_mismatches,
            type_errors=accuracy_result.type_errors,
            factual_errors=accuracy_result.factual_errors,
            accuracy_warnings=accuracy_result.warnings,
            validated_examples=accuracy_result.validated_examples,
            total_examples=accuracy_result.total_examples,
            overall_confidence=confidence_score.overall_confidence,
            completeness_confidence=confidence_score.completeness_confidence,
            accuracy_confidence=confidence_score.accuracy_confidence,
            source_quality_confidence=confidence_score.source_quality_confidence,
            confidence_breakdown=confidence_score.confidence_breakdown,
            requires_review=confidence_score.requires_review,
            review_priority=confidence_score.review_priority,
            review_status='pending' if confidence_score.requires_review else None,
            recommendations=completeness_result.recommendations + accuracy_result.warnings[:5]
        )
        
        db.add(quality_check)
        db.commit()
        db.refresh(quality_check)
        
        # Queue for review if needed
        if confidence_score.requires_review:
            review_manager = get_review_workflow_manager()
            await review_manager.queue_for_review(
                artifact_id=request.artifact_id,
                artifact_title=artifact_model.title,
                confidence_score=confidence_score.overall_confidence,
                priority=confidence_score.review_priority,
                issues=(completeness_result.missing_sections + 
                       accuracy_result.code_example_issues[:3]),
                recommendations=completeness_result.recommendations[:5]
            )
        
        logger.info(f"✅ Validation complete: {request.artifact_id}")
        
        return ValidateArtifactResponse(
            success=True,
            artifact_id=request.artifact_id,
            completeness_score=completeness_result.overall_score,
            accuracy_score=accuracy_result.overall_score,
            overall_confidence=confidence_score.overall_confidence,
            requires_review=confidence_score.requires_review,
            review_priority=confidence_score.review_priority,
            recommendations=completeness_result.recommendations[:10],
            quality_check_id=str(quality_check.id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate-run", response_model=ValidateRunResponse)
async def validate_run(
    request: ValidateRunRequest,
    db = Depends(get_db)
):
    """
    Validate entire documentation run.
    
    Validates all artifacts in the run and generates quality report.
    """
    try:
        logger.info(f"Validating run: {request.run_id}")
        
        # Get run from database
        run = db.query(DocumentationRunModel).filter(
            DocumentationRunModel.id == UUID(request.run_id)
        ).first()
        
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Get all artifacts for this run
        artifacts = db.query(DocumentationArtifactModel).filter(
            DocumentationArtifactModel.run_id == UUID(request.run_id)
        ).all()
        
        if not artifacts:
            raise HTTPException(status_code=404, detail="No artifacts found for run")
        
        # Validate each artifact
        completeness_results = []
        accuracy_results = []
        confidence_scores = []
        validated_count = 0
        
        completeness_checker = get_completeness_checker()
        accuracy_validator = get_accuracy_validator()
        confidence_scorer = get_confidence_scorer()
        
        for artifact in artifacts:
            try:
                artifact_dict = {
                    'title': artifact.title,
                    'content': artifact.content,
                    'type': artifact.type,
                    'word_count': artifact.word_count
                }
                
                comp_result = await completeness_checker.check(artifact_dict)
                acc_result = await accuracy_validator.validate(artifact_dict)
                conf_score = await confidence_scorer.score(
                    artifact_dict,
                    comp_result,
                    acc_result
                )
                
                completeness_results.append(comp_result)
                accuracy_results.append(acc_result)
                confidence_scores.append(conf_score)
                validated_count += 1
                
                # Save quality check
                quality_check = QualityCheckModel(
                    run_id=artifact.run_id,
                    artifact_id=artifact.id,
                    completeness_score=comp_result.overall_score,
                    accuracy_score=acc_result.overall_score,
                    overall_confidence=conf_score.overall_confidence,
                    completeness_confidence=conf_score.completeness_confidence,
                    accuracy_confidence=conf_score.accuracy_confidence,
                    source_quality_confidence=conf_score.source_quality_confidence,
                    requires_review=conf_score.requires_review,
                    review_priority=conf_score.review_priority,
                    review_status='pending' if conf_score.requires_review else None
                )
                db.add(quality_check)
                
            except Exception as e:
                logger.warning(f"Failed to validate artifact {artifact.id}: {e}")
                continue
        
        # Generate quality report
        reporter = get_quality_reporter()
        quality_report = await reporter.generate_report(
            run_id=request.run_id,
            completeness_results=completeness_results,
            accuracy_results=accuracy_results,
            confidence_scores=confidence_scores
        )
        
        # Save report to database
        report_model = QualityReportModel(
            run_id=UUID(request.run_id),
            total_artifacts=quality_report.total_artifacts,
            average_completeness=quality_report.average_completeness,
            average_accuracy=quality_report.average_accuracy,
            average_confidence=quality_report.average_confidence,
            completeness_breakdown=quality_report.completeness_breakdown,
            accuracy_breakdown=quality_report.accuracy_breakdown,
            confidence_breakdown=quality_report.confidence_breakdown,
            total_issues=quality_report.total_issues,
            critical_issues=quality_report.critical_issues,
            issues_by_type=quality_report.issues_by_type,
            artifacts_requiring_review=quality_report.artifacts_requiring_review,
            review_priority_breakdown=quality_report.review_priority_breakdown,
            top_recommendations=quality_report.top_recommendations
        )
        db.add(report_model)
        db.commit()
        db.refresh(report_model)
        
        logger.info(f"✅ Run validation complete: {validated_count}/{len(artifacts)} artifacts")
        
        return ValidateRunResponse(
            success=True,
            run_id=request.run_id,
            total_artifacts=len(artifacts),
            validated_artifacts=validated_count,
            average_completeness=quality_report.average_completeness,
            average_accuracy=quality_report.average_accuracy,
            average_confidence=quality_report.average_confidence,
            artifacts_requiring_review=quality_report.artifacts_requiring_review,
            report_id=str(report_model.id)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Run validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{run_id}", response_model=QualityReportResponse)
async def get_quality_report(
    run_id: str,
    db = Depends(get_db)
):
    """Get quality report for a documentation run."""
    try:
        report = db.query(QualityReportModel).filter(
            QualityReportModel.run_id == UUID(run_id)
        ).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="Quality report not found")
        
        return QualityReportResponse(
            report_id=str(report.id),
            run_id=str(report.run_id),
            total_artifacts=report.total_artifacts,
            average_completeness=report.average_completeness,
            average_accuracy=report.average_accuracy,
            average_confidence=report.average_confidence,
            total_issues=report.total_issues,
            critical_issues=report.critical_issues,
            artifacts_requiring_review=report.artifacts_requiring_review,
            review_priority_breakdown=report.review_priority_breakdown,
            top_recommendations=report.top_recommendations,
            generated_at=report.generated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review/queue", response_model=List[ReviewQueueItem])
async def get_review_queue(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum items to return")
):
    """Get review queue with optional filtering."""
    try:
        manager = get_review_workflow_manager()
        
        # Convert status string to enum
        status_enum = ReviewStatus(status) if status else None
        
        items = await manager.get_review_queue(
            status=status_enum,
            priority=priority,
            limit=limit
        )
        
        return [
            ReviewQueueItem(
                review_id=item.id,
                artifact_id=item.artifact_id,
                artifact_title=item.artifact_title,
                confidence_score=item.confidence_score,
                priority=item.priority,
                status=item.status.value,
                issues=item.issues,
                recommendations=item.recommendations,
                created_at=item.created_at.isoformat()
            )
            for item in items
        ]
        
    except Exception as e:
        logger.error(f"❌ Error fetching review queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/{review_id}/assign")
async def assign_review(
    review_id: str,
    request: AssignReviewRequest
):
    """Assign a review to a reviewer."""
    try:
        manager = get_review_workflow_manager()
        
        item = await manager.assign_review(review_id, request.reviewer)
        
        if not item:
            raise HTTPException(status_code=404, detail="Review item not found")
        
        return {
            "success": True,
            "review_id": review_id,
            "assigned_to": request.reviewer,
            "status": item.status.value
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error assigning review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/review/{review_id}/complete")
async def complete_review(
    review_id: str,
    request: CompleteReviewRequest
):
    """Complete a review."""
    try:
        manager = get_review_workflow_manager()
        
        # Convert status string to enum
        status_enum = ReviewStatus(request.status)
        
        item = await manager.complete_review(
            review_id,
            status_enum,
            request.reviewer_notes
        )
        
        if not item:
            raise HTTPException(status_code=404, detail="Review item not found")
        
        return {
            "success": True,
            "review_id": review_id,
            "status": item.status.value,
            "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error completing review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{run_id}")
async def get_quality_metrics(
    run_id: str,
    db = Depends(get_db)
):
    """Get quality metrics for a documentation run."""
    try:
        # Get all quality checks for this run
        checks = db.query(QualityCheckModel).filter(
            QualityCheckModel.run_id == UUID(run_id)
        ).all()
        
        if not checks:
            raise HTTPException(status_code=404, detail="No quality checks found for run")
        
        # Calculate metrics
        total = len(checks)
        avg_completeness = sum(c.completeness_score for c in checks) / total
        avg_accuracy = sum(c.accuracy_score for c in checks) / total
        avg_confidence = sum(c.overall_confidence for c in checks) / total
        
        requiring_review = sum(1 for c in checks if c.requires_review)
        
        by_priority = {
            'critical': sum(1 for c in checks if c.review_priority == 'critical'),
            'high': sum(1 for c in checks if c.review_priority == 'high'),
            'medium': sum(1 for c in checks if c.review_priority == 'medium'),
            'low': sum(1 for c in checks if c.review_priority == 'low')
        }
        
        return {
            "success": True,
            "run_id": run_id,
            "total_artifacts": total,
            "average_completeness": avg_completeness,
            "average_accuracy": avg_accuracy,
            "average_confidence": avg_confidence,
            "requiring_review": requiring_review,
            "review_rate": requiring_review / total if total > 0 else 0,
            "by_priority": by_priority
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

