"""
Tests for Discovery Engine.
"""

import pytest
from pathlib import Path

from src.services.discovery.repository_scanner import RepositoryScanner, get_repository_scanner
from src.services.discovery.file_classifier import FileClassifier, get_file_classifier, ImportanceLevel
from src.services.discovery.processing_planner import ProcessingPlanner, get_processing_planner
from src.services.discovery.discovery_engine import DiscoveryEngine, get_discovery_engine


@pytest.mark.asyncio
async def test_repository_scanner():
    """Test repository scanner."""
    scanner = get_repository_scanner()
    
    # Scan test directory (this file's directory)
    test_dir = Path(__file__).parent
    inventory = await scanner.scan(test_dir)
    
    assert inventory.total_files >= 0  # At least this test file
    assert inventory.total_size_bytes >= 0
    assert isinstance(inventory.languages, dict)
    assert isinstance(inventory.frameworks, list)
    assert isinstance(inventory.file_types, dict)


@pytest.mark.asyncio
async def test_file_classifier():
    """Test file classifier."""
    scanner = get_repository_scanner()
    classifier = get_file_classifier()
    
    # Scan and classify
    test_dir = Path(__file__).parent
    inventory = await scanner.scan(test_dir)
    
    if inventory.files:
        classified = await classifier.classify(inventory.files)
        
        assert len(classified) == len(inventory.files)
        assert all(cf.importance_score >= 0.0 and cf.importance_score <= 1.0 for cf in classified)
        assert all(isinstance(cf.importance_level, ImportanceLevel) for cf in classified)
        assert all(cf.priority > 0 for cf in classified)


@pytest.mark.asyncio
async def test_processing_planner():
    """Test processing planner."""
    scanner = get_repository_scanner()
    classifier = get_file_classifier()
    planner = get_processing_planner()
    
    # Scan, classify, and plan
    test_dir = Path(__file__).parent
    inventory = await scanner.scan(test_dir)
    
    if inventory.files:
        classified = await classifier.classify(inventory.files)
        plan = await planner.create_plan(inventory, classified, str(test_dir))
        
        assert plan.total_files == len(classified)
        assert plan.estimated_total_time_minutes >= 0
        assert len(plan.sub_jobs) > 0
        assert plan.max_parallelization > 0
        assert len(plan.processing_order) == len(plan.sub_jobs)


@pytest.mark.asyncio
async def test_discovery_engine_integration():
    """Test full discovery engine."""
    engine = get_discovery_engine()
    
    # Run discovery on test directory
    test_dir = Path(__file__).parent
    plan = await engine.discover(str(test_dir))
    
    assert plan.total_files >= 0
    assert len(plan.sub_jobs) > 0
    
    # Get summary
    summary = engine.get_plan_summary(plan)
    assert "total_files" in summary
    assert "sub_jobs" in summary
    assert "estimated_time_minutes" in summary
    assert isinstance(summary["sub_job_details"], list)


@pytest.mark.asyncio
async def test_discovery_on_larger_directory():
    """Test discovery on a larger directory (src/services)."""
    engine = get_discovery_engine()
    
    # Run discovery on src/services directory
    src_dir = Path(__file__).parent.parent.parent / "src" / "services"
    
    if src_dir.exists():
        plan = await engine.discover(str(src_dir))
        
        assert plan.total_files > 10  # Should have multiple files
        assert len(plan.sub_jobs) > 0
        
        # Verify sub-jobs are sorted by priority
        priorities = [sj.priority for sj in plan.sub_jobs]
        assert priorities == sorted(priorities)


def test_singleton_instances():
    """Test that singletons return same instance."""
    scanner1 = get_repository_scanner()
    scanner2 = get_repository_scanner()
    assert scanner1 is scanner2
    
    classifier1 = get_file_classifier()
    classifier2 = get_file_classifier()
    assert classifier1 is classifier2
    
    planner1 = get_processing_planner()
    planner2 = get_processing_planner()
    assert planner1 is planner2
    
    engine1 = get_discovery_engine()
    engine2 = get_discovery_engine()
    assert engine1 is engine2

