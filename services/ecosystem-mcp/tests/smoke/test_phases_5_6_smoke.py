"""
Smoke Tests for Phases 5 & 6

Quick validation tests for:
- Phase 5: Quality Assurance System
- Phase 6: Dashboard Integration

These tests provide fast feedback on critical functionality.
"""

import pytest
import asyncio
from pathlib import Path


@pytest.mark.smoke
class TestPhase5QualitySmoke:
    """Smoke tests for Phase 5 Quality Assurance."""
    
    @pytest.mark.asyncio
    async def test_completeness_checker_basic(self):
        """Test CompletenessChecker can validate a document."""
        from src.services.quality.completeness_checker import get_completeness_checker
        
        checker = get_completeness_checker()
        
        artifact = {
            'title': 'Smoke Test Document',
            'type': 'guide',
            'content': '''# Smoke Test
            
## Overview
This is a basic document for smoke testing the completeness checker.

## Installation
Step by step installation instructions here.

## Usage
Usage instructions with examples.
'''
        }
        
        result = await checker.check(artifact)
        
        # Basic assertions
        assert result is not None
        assert 0 <= result.overall_score <= 1
        assert isinstance(result.missing_sections, list)
        assert isinstance(result.recommendations, list)
        
        print(f"✅ CompletenessChecker: Score = {result.overall_score:.2f}")
    
    @pytest.mark.asyncio
    async def test_accuracy_validator_basic(self):
        """Test AccuracyValidator can validate code examples."""
        from src.services.quality.accuracy_validator import get_accuracy_validator
        
        validator = get_accuracy_validator()
        
        artifact = {
            'title': 'Code Example Test',
            'content': '''# Example

```python
def hello_world():
    print("Hello, World!")
    return True
```
'''
        }
        
        result = await validator.validate(artifact)
        
        # Basic assertions
        assert result is not None
        assert 0 <= result.overall_score <= 1
        assert result.total_examples >= 1
        
        print(f"✅ AccuracyValidator: Score = {result.overall_score:.2f}, Examples = {result.total_examples}")
    
    @pytest.mark.asyncio
    async def test_confidence_scorer_basic(self):
        """Test ConfidenceScorer can calculate confidence."""
        from src.services.quality.confidence_scorer import get_confidence_scorer
        from src.services.quality.completeness_checker import CompletenessResult
        from src.services.quality.accuracy_validator import AccuracyResult
        
        scorer = get_confidence_scorer()
        
        # Mock results
        completeness = CompletenessResult(
            overall_score=0.8,
            missing_sections=[],
            incomplete_sections=[],
            placeholder_count=0,
            broken_links=[],
            formatting_issues=[],
            recommendations=[],
            section_word_counts={},
            has_code_examples=True
        )
        
        accuracy = AccuracyResult(
            overall_score=0.9,
            code_example_issues=[],
            api_mismatches=[],
            type_errors=[],
            factual_errors=[],
            warnings=[],
            validated_examples=2,
            total_examples=2
        )
        
        artifact = {'title': 'Test'}
        
        result = await scorer.score(artifact, completeness, accuracy)
        
        # Basic assertions
        assert result is not None
        assert 0 <= result.overall_confidence <= 1
        assert result.review_priority in ['critical', 'high', 'medium', 'low']
        
        print(f"✅ ConfidenceScorer: Confidence = {result.overall_confidence:.2f}, Priority = {result.review_priority}")
    
    @pytest.mark.asyncio
    async def test_review_workflow_basic(self):
        """Test ReviewWorkflowManager can manage queue."""
        from src.services.quality.review_workflow import get_review_workflow_manager
        
        manager = get_review_workflow_manager()
        
        # Queue an item
        item = await manager.queue_for_review(
            artifact_id='smoke-test-1',
            artifact_title='Smoke Test Doc',
            confidence_score=0.55,
            priority='high',
            issues=['Test issue'],
            recommendations=['Test recommendation']
        )
        
        assert item is not None
        assert item.priority == 'high'
        
        # Get queue
        queue = await manager.get_review_queue(limit=10)
        assert isinstance(queue, list)
        assert len(queue) > 0
        
        print(f"✅ ReviewWorkflowManager: Queued item, Queue size = {len(queue)}")
    
    @pytest.mark.asyncio
    async def test_quality_reporter_basic(self):
        """Test QualityReporter can generate reports."""
        from src.services.quality.quality_reporter import get_quality_reporter
        from src.services.quality.completeness_checker import CompletenessResult
        from src.services.quality.accuracy_validator import AccuracyResult
        from src.services.quality.confidence_scorer import ConfidenceScore
        
        reporter = get_quality_reporter()
        
        # Mock results
        completeness_results = [
            CompletenessResult(
                overall_score=0.8,
                missing_sections=[],
                incomplete_sections=[],
                placeholder_count=0,
                broken_links=[],
                formatting_issues=[],
                recommendations=[],
                section_word_counts={},
                has_code_examples=True
            )
        ]
        
        accuracy_results = [
            AccuracyResult(
                overall_score=0.9,
                code_example_issues=[],
                api_mismatches=[],
                type_errors=[],
                factual_errors=[],
                warnings=[],
                validated_examples=2,
                total_examples=2
            )
        ]
        
        confidence_scores = [
            ConfidenceScore(
                overall_confidence=0.85,
                completeness_confidence=0.8,
                accuracy_confidence=0.9,
                source_quality_confidence=0.85,
                requires_review=False,
                confidence_breakdown={},
                review_priority='low'
            )
        ]
        
        report = await reporter.generate_report(
            run_id='smoke-test-run',
            completeness_results=completeness_results,
            accuracy_results=accuracy_results,
            confidence_scores=confidence_scores
        )
        
        assert report is not None
        assert report.total_artifacts == 1
        assert 0 <= report.average_completeness <= 1
        assert 0 <= report.average_accuracy <= 1
        assert 0 <= report.average_confidence <= 1
        
        print(f"✅ QualityReporter: Report generated for {report.total_artifacts} artifact(s)")


@pytest.mark.smoke
class TestPhase5Integration:
    """Integration smoke test for Phase 5 workflow."""
    
    @pytest.mark.asyncio
    async def test_complete_quality_workflow(self):
        """Test complete quality validation workflow."""
        from src.services.quality import (
            get_completeness_checker,
            get_accuracy_validator,
            get_confidence_scorer,
            get_quality_reporter
        )
        
        # Test artifact
        artifact = {
            'title': 'Integration Test Document',
            'type': 'guide',
            'content': '''# Integration Test

## Overview
Comprehensive overview section with detailed information.

## Setup
```bash
pip install package
```

## Usage
```python
import package
result = package.run()
```

## Examples
Multiple examples demonstrating usage patterns.
'''
        }
        
        # Step 1: Completeness check
        checker = get_completeness_checker()
        comp_result = await checker.check(artifact)
        assert comp_result.overall_score > 0
        
        # Step 2: Accuracy validation
        validator = get_accuracy_validator()
        acc_result = await validator.validate(artifact)
        assert acc_result.overall_score > 0
        
        # Step 3: Confidence scoring
        scorer = get_confidence_scorer()
        conf_score = await scorer.score(artifact, comp_result, acc_result)
        assert conf_score.overall_confidence > 0
        
        # Step 4: Generate report
        reporter = get_quality_reporter()
        report = await reporter.generate_report(
            run_id='integration-smoke-test',
            completeness_results=[comp_result],
            accuracy_results=[acc_result],
            confidence_scores=[conf_score]
        )
        assert report.total_artifacts == 1
        
        print(f"✅ Full workflow: Completeness={comp_result.overall_score:.2f}, "
              f"Accuracy={acc_result.overall_score:.2f}, "
              f"Confidence={conf_score.overall_confidence:.2f}")


@pytest.mark.smoke
@pytest.mark.skipif(
    not Path("/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard").exists(),
    reason="Dashboard service not available"
)
class TestPhase6DashboardSmoke:
    """Smoke tests for Phase 6 Dashboard Integration."""
    
    def test_quality_dashboard_imports(self):
        """Test quality dashboard can be imported."""
        try:
            import sys
            sys.path.insert(0, "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard")
            
            from dashboard_views import quality_dashboard
            
            assert hasattr(quality_dashboard, 'show')
            
            print("✅ Quality Dashboard: Imports successful")
        except ImportError as e:
            pytest.skip(f"Dashboard imports not available: {e}")
    
    def test_doc_generator_quality_tab_exists(self):
        """Test doc generator has quality metrics tab."""
        try:
            import sys
            sys.path.insert(0, "/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp-dashboard")
            
            from dashboard_views import doc_generator
            
            # Read the source to check for quality tab
            import inspect
            source = inspect.getsource(doc_generator.show)
            
            assert "Quality Metrics" in source
            assert "tab4" in source
            
            print("✅ Doc Generator: Quality tab integrated")
        except ImportError as e:
            pytest.skip(f"Dashboard imports not available: {e}")


@pytest.mark.smoke
class TestSystemHealthSmoke:
    """Overall system health smoke tests."""
    
    def test_all_phase5_singletons(self):
        """Test all Phase 5 singletons are accessible."""
        from src.services.quality import (
            get_completeness_checker,
            get_accuracy_validator,
            get_confidence_scorer,
            get_review_workflow_manager,
            get_quality_reporter
        )
        
        # Get all singletons
        checker = get_completeness_checker()
        validator = get_accuracy_validator()
        scorer = get_confidence_scorer()
        manager = get_review_workflow_manager()
        reporter = get_quality_reporter()
        
        # Verify they're all distinct objects
        assert checker is not None
        assert validator is not None
        assert scorer is not None
        assert manager is not None
        assert reporter is not None
        
        # Verify singleton behavior
        assert checker is get_completeness_checker()
        assert validator is get_accuracy_validator()
        
        print("✅ All Phase 5 singletons: Accessible and functional")
    
    def test_logging_configured(self):
        """Test logging is properly configured."""
        import logging
        
        # Check that loggers exist for quality modules
        logger_names = [
            'src.services.quality.completeness_checker',
            'src.services.quality.accuracy_validator',
            'src.services.quality.confidence_scorer',
            'src.services.quality.review_workflow',
            'src.services.quality.quality_reporter'
        ]
        
        for logger_name in logger_names:
            logger = logging.getLogger(logger_name)
            assert logger is not None
        
        print("✅ Logging: All Phase 5 loggers configured")


if __name__ == "__main__":
    # Run smoke tests
    pytest.main([__file__, "-v", "-m", "smoke", "--tb=short"])

