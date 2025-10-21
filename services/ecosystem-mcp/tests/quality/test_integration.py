"""
Integration tests for Phase 5 Quality Assurance workflow.
"""

import pytest
from src.services.quality import (
    get_completeness_checker,
    get_accuracy_validator,
    get_confidence_scorer,
    get_review_workflow_manager,
    get_quality_reporter
)


@pytest.mark.asyncio
@pytest.mark.integration
class TestQualityWorkflow:
    """Test complete quality workflow integration."""
    
    async def test_complete_validation_workflow(self):
        """Test complete validation workflow from artifact to report."""
        # Sample artifact
        artifact = {
            'title': 'Integration Test Document',
            'type': 'guide',
            'content': '''# Integration Test Document

## Overview
This is a comprehensive test document with sufficient content to validate
the complete quality assurance workflow from start to finish.

## Installation
```bash
pip install example-package
```

## Usage
```python
from example import feature

result = feature.process()
print(result)
```

## Examples
Multiple examples demonstrating the API usage and common patterns.

## Configuration
Configuration details and options explained in detail.
''',
            'word_count': 150
        }
        
        # Step 1: Completeness check
        completeness_checker = get_completeness_checker()
        completeness_result = await completeness_checker.check(artifact)
        
        assert completeness_result.overall_score > 0
        assert completeness_result.has_code_examples is True
        
        # Step 2: Accuracy validation
        accuracy_validator = get_accuracy_validator()
        accuracy_result = await accuracy_validator.validate(artifact)
        
        assert accuracy_result.overall_score > 0
        assert accuracy_result.total_examples >= 2
        
        # Step 3: Confidence scoring
        confidence_scorer = get_confidence_scorer()
        confidence_score = await confidence_scorer.score(
            artifact,
            completeness_result,
            accuracy_result,
            source_quality=0.8
        )
        
        assert 0 <= confidence_score.overall_confidence <= 1
        assert confidence_score.review_priority in ['critical', 'high', 'medium', 'low']
        
        # Step 4: Review queue (if needed)
        if confidence_score.requires_review:
            review_manager = get_review_workflow_manager()
            review_item = await review_manager.queue_for_review(
                artifact_id='test-123',
                artifact_title=artifact['title'],
                confidence_score=confidence_score.overall_confidence,
                priority=confidence_score.review_priority,
                issues=completeness_result.missing_sections,
                recommendations=completeness_result.recommendations
            )
            
            assert review_item is not None
            assert review_item.confidence_score == confidence_score.overall_confidence
        
        # Step 5: Quality report
        reporter = get_quality_reporter()
        report = await reporter.generate_report(
            run_id='integration-test-run',
            completeness_results=[completeness_result],
            accuracy_results=[accuracy_result],
            confidence_scores=[confidence_score]
        )
        
        assert report.total_artifacts == 1
        assert 0 <= report.average_completeness <= 1
        assert 0 <= report.average_accuracy <= 1
        assert 0 <= report.average_confidence <= 1
    
    async def test_multiple_artifacts_workflow(self):
        """Test workflow with multiple artifacts."""
        artifacts = [
            {
                'title': 'Doc 1',
                'type': 'guide',
                'content': '# Doc 1\n\n## Overview\nGood overview.\n\n## Usage\nDetailed usage.',
                'word_count': 50
            },
            {
                'title': 'Doc 2',
                'type': 'api_reference',
                'content': '# Doc 2\n\nTODO: Add content',
                'word_count': 10
            },
            {
                'title': 'Doc 3',
                'type': 'guide',
                'content': '# Doc 3\n\n```python\ndef test(): pass\n```\n\nExcellent documentation.',
                'word_count': 30
            }
        ]
        
        completeness_results = []
        accuracy_results = []
        confidence_scores = []
        
        checker = get_completeness_checker()
        validator = get_accuracy_validator()
        scorer = get_confidence_scorer()
        
        for artifact in artifacts:
            comp = await checker.check(artifact)
            acc = await validator.validate(artifact)
            conf = await scorer.score(artifact, comp, acc)
            
            completeness_results.append(comp)
            accuracy_results.append(acc)
            confidence_scores.append(conf)
        
        # Generate report
        reporter = get_quality_reporter()
        report = await reporter.generate_report(
            run_id='multi-artifact-test',
            completeness_results=completeness_results,
            accuracy_results=accuracy_results,
            confidence_scores=confidence_scores
        )
        
        assert report.total_artifacts == 3
        assert len(report.top_recommendations) > 0
        
        # Check that different quality levels were detected
        scores = [cs.overall_confidence for cs in confidence_scores]
        assert max(scores) > min(scores)  # Should have variance


@pytest.mark.asyncio
@pytest.mark.integration
class TestReviewWorkflow:
    """Test review workflow integration."""
    
    async def test_review_lifecycle(self):
        """Test complete review lifecycle."""
        manager = get_review_workflow_manager()
        
        # Queue item
        item = await manager.queue_for_review(
            artifact_id='review-test-1',
            artifact_title='Test Doc',
            confidence_score=0.55,
            priority='high',
            issues=['Missing sections', 'Placeholders'],
            recommendations=['Add overview', 'Replace TODOs']
        )
        
        assert item.status.value == 'pending'
        assert item.priority == 'high'
        
        # Get queue
        queue = await manager.get_review_queue(limit=10)
        assert len(queue) > 0
        assert any(i.id == item.id for i in queue)
        
        # Assign review
        assigned = await manager.assign_review(item.id, 'reviewer@example.com')
        assert assigned.status.value == 'in_review'
        assert assigned.assigned_to == 'reviewer@example.com'
        
        # Complete review
        from src.services.quality.review_workflow import ReviewStatus
        completed = await manager.complete_review(
            item.id,
            ReviewStatus.APPROVED,
            'Looks good after fixes'
        )
        assert completed.status == ReviewStatus.APPROVED
        assert completed.reviewer_notes == 'Looks good after fixes'
        assert completed.reviewed_at is not None
    
    async def test_priority_sorting(self):
        """Test that queue is sorted by priority."""
        manager = get_review_workflow_manager()
        
        # Clear queue for this test
        manager.review_queue = {}
        
        # Add items with different priorities
        await manager.queue_for_review(
            artifact_id='low-1',
            artifact_title='Low Priority',
            confidence_score=0.75,
            priority='low',
            issues=[],
            recommendations=[]
        )
        
        await manager.queue_for_review(
            artifact_id='critical-1',
            artifact_title='Critical Priority',
            confidence_score=0.35,
            priority='critical',
            issues=['Major issues'],
            recommendations=['Fix immediately']
        )
        
        await manager.queue_for_review(
            artifact_id='high-1',
            artifact_title='High Priority',
            confidence_score=0.55,
            priority='high',
            issues=['Issues'],
            recommendations=['Fix soon']
        )
        
        # Get queue
        queue = await manager.get_review_queue()
        
        # Should be sorted: critical, high, low
        assert queue[0].priority == 'critical'
        assert queue[1].priority == 'high'
        assert queue[2].priority == 'low'

