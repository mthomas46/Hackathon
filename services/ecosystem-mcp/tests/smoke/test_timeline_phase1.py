"""
Smoke tests for Timeline Phase 1.

Quick validation tests to ensure basic functionality works.
Run these before more comprehensive tests.
"""

import pytest
from datetime import datetime, timedelta

from src.models.timeline import (
    Timeline,
    TimelineCreate,
    TimePeriod,
    DocumentPlacement,
    TemporalConfidence,
    PeriodStrategy,
    PlacementSource,
    ConfidenceMetadata,
    TimelineMetadata,
)


class TestBasicModelCreation:
    """Smoke test: Basic model creation."""
    
    def test_can_create_timeline_model(self):
        """Test that we can create a basic Timeline model."""
        timeline = Timeline(
            name="Smoke Test Timeline",
            service_name="test-service",
            repo_path="/test/path",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
            confidence_level=TemporalConfidence.HIGH,
            confidence_metadata=ConfidenceMetadata(
                total_documents=100,
                git_history_documents=95,
                snapshot_documents=5,
                git_percentage=95.0,
                can_show_evolution=True,
                can_detect_drift=True,
                can_show_timeline=True,
                can_compare_periods=True,
                fallback_strategy="minimal_fallback"
            )
        )
        
        assert timeline.name == "Smoke Test Timeline"
        assert timeline.confidence_level == TemporalConfidence.HIGH
        print("✅ Timeline model creation works")
    
    def test_can_create_period_model(self):
        """Test that we can create a TimePeriod model."""
        from uuid import uuid4
        
        period = TimePeriod(
            timeline_id=uuid4(),
            name="Q1 2025",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 3, 31),
            sequence_number=1,
            document_count=42,
            commit_count=156
        )
        
        assert period.name == "Q1 2025"
        assert period.sequence_number == 1
        print("✅ TimePeriod model creation works")
    
    def test_can_create_placement_model(self):
        """Test that we can create a DocumentPlacement model."""
        from uuid import uuid4
        
        placement = DocumentPlacement(
            period_id=uuid4(),
            document_id=uuid4(),
            placement_date=datetime.utcnow(),
            placement_source=PlacementSource.GIT_COMMIT,
            git_commit_sha="a" * 40,
            relevance_score=1.0
        )
        
        assert placement.placement_source == PlacementSource.GIT_COMMIT
        assert placement.relevance_score == 1.0
        print("✅ DocumentPlacement model creation works")


class TestModelValidation:
    """Smoke test: Model validation."""
    
    def test_timeline_date_validation(self):
        """Test that date validation works."""
        with pytest.raises(ValueError):
            TimelineCreate(
                name="Invalid Timeline",
                service_name="test",
                repo_path="/test",
                start_date=datetime(2025, 12, 31),
                end_date=datetime(2025, 1, 1)  # Invalid: before start
            )
        
        print("✅ Timeline date validation works")
    
    def test_period_sequence_validation(self):
        """Test that sequence number validation works."""
        from uuid import uuid4
        
        with pytest.raises(ValueError):
            TimePeriod(
                timeline_id=uuid4(),
                name="Invalid Period",
                start_date=datetime(2025, 1, 1),
                end_date=datetime(2025, 1, 31),
                sequence_number=0  # Invalid: must be >= 1
            )
        
        print("✅ Period sequence validation works")
    
    def test_placement_score_validation(self):
        """Test that relevance score validation works."""
        from uuid import uuid4
        
        with pytest.raises(ValueError):
            DocumentPlacement(
                period_id=uuid4(),
                document_id=uuid4(),
                placement_date=datetime.utcnow(),
                placement_source=PlacementSource.CREATED_AT,
                relevance_score=1.5  # Invalid: must be <= 1.0
            )
        
        print("✅ Placement score validation works")


class TestModelSerialization:
    """Smoke test: Model serialization."""
    
    def test_timeline_to_dict(self):
        """Test that Timeline can be serialized to dict."""
        timeline = Timeline(
            name="Test",
            service_name="test",
            repo_path="/test",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31),
            confidence_level=TemporalConfidence.HIGH,
            confidence_metadata=ConfidenceMetadata(
                total_documents=100,
                git_history_documents=95,
                snapshot_documents=5,
                git_percentage=95.0,
                can_show_evolution=True,
                can_detect_drift=True,
                can_show_timeline=True,
                can_compare_periods=True,
                fallback_strategy="minimal_fallback"
            )
        )
        
        data = timeline.model_dump()
        assert isinstance(data, dict)
        assert data["name"] == "Test"
        assert data["service_name"] == "test"
        print("✅ Timeline serialization works")
    
    def test_timeline_from_dict(self):
        """Test that Timeline can be created from dict."""
        data = {
            "name": "Test",
            "service_name": "test",
            "repo_path": "/test",
            "start_date": "2025-01-01T00:00:00",
            "end_date": "2025-12-31T00:00:00",
            "confidence_level": "HIGH",
            "confidence_metadata": {
                "total_documents": 100,
                "git_history_documents": 95,
                "snapshot_documents": 5,
                "git_percentage": 95.0,
                "can_show_evolution": True,
                "can_detect_drift": True,
                "can_show_timeline": True,
                "can_compare_periods": True,
                "fallback_strategy": "minimal_fallback"
            }
        }
        
        timeline = Timeline(**data)
        assert timeline.name == "Test"
        assert timeline.confidence_level == TemporalConfidence.HIGH
        print("✅ Timeline deserialization works")


class TestEnums:
    """Smoke test: Enum definitions."""
    
    def test_confidence_levels_exist(self):
        """Test all confidence levels are defined."""
        assert TemporalConfidence.HIGH
        assert TemporalConfidence.MEDIUM
        assert TemporalConfidence.LOW
        assert TemporalConfidence.NONE
        print("✅ TemporalConfidence enum works")
    
    def test_period_strategies_exist(self):
        """Test all period strategies are defined."""
        assert PeriodStrategy.MONTHLY
        assert PeriodStrategy.QUARTERLY
        assert PeriodStrategy.ADAPTIVE
        print("✅ PeriodStrategy enum works")
    
    def test_placement_sources_exist(self):
        """Test all placement sources are defined."""
        assert PlacementSource.GIT_COMMIT
        assert PlacementSource.CREATED_AT
        assert PlacementSource.MANUAL
        print("✅ PlacementSource enum works")


class TestImports:
    """Smoke test: Module imports."""
    
    def test_can_import_services(self):
        """Test that we can import timeline services."""
        from src.services.timeline import (
            TemporalConfidenceCalculator,
            TimelineManager,
            PeriodGenerator,
            DocumentPlacer
        )
        
        assert TemporalConfidenceCalculator
        assert TimelineManager
        assert PeriodGenerator
        assert DocumentPlacer
        print("✅ Timeline services import works")
    
    def test_can_import_repositories(self):
        """Test that we can import timeline repositories."""
        from src.storage.repositories import (
            TimelineRepository,
            TimePeriodRepository,
            DocumentPlacementRepository
        )
        
        assert TimelineRepository
        assert TimePeriodRepository
        assert DocumentPlacementRepository
        print("✅ Timeline repositories import works")
    
    def test_can_import_models(self):
        """Test that we can import timeline models."""
        from src.storage.db_models import (
            TimelineModel,
            TimePeriodModel,
            DocumentPlacementModel
        )
        
        assert TimelineModel
        assert TimePeriodModel
        assert DocumentPlacementModel
        print("✅ Timeline database models import works")


def run_smoke_tests():
    """Run all smoke tests and print summary."""
    print("\n" + "="*60)
    print("TIMELINE PHASE 1 SMOKE TESTS")
    print("="*60 + "\n")
    
    test_classes = [
        TestBasicModelCreation,
        TestModelValidation,
        TestModelSerialization,
        TestEnums,
        TestImports
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        print("-" * 60)
        
        test_instance = test_class()
        test_methods = [
            method for method in dir(test_instance)
            if method.startswith('test_') and callable(getattr(test_instance, method))
        ]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                method()
                passed_tests += 1
            except Exception as e:
                failed_tests += 1
                print(f"❌ {method_name} FAILED: {e}")
    
    print("\n" + "="*60)
    print("SMOKE TEST SUMMARY")
    print("="*60)
    print(f"Total Tests:  {total_tests}")
    print(f"Passed:       {passed_tests} ✅")
    print(f"Failed:       {failed_tests} ❌")
    print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
    print("="*60 + "\n")
    
    if failed_tests == 0:
        print("🎉 ALL SMOKE TESTS PASSED! 🎉\n")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW ABOVE ⚠️\n")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(run_smoke_tests())

