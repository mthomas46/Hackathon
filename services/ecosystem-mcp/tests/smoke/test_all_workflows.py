"""
Comprehensive Smoke Tests for All Major Workflows

Tests against the actual codebase to validate:
1. Discovery → Sub-Job Execution workflow
2. Analysis → Documentation workflow
3. Quality Validation workflow
4. End-to-end pipeline

These tests use the project's own code as test data.
"""

import pytest
import asyncio
from pathlib import Path
import tempfile
import shutil


# Test against actual codebase paths
TEST_REPO_PATH = Path("/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp")
SMALL_TEST_PATH = Path("/Users/mykalthomas/Documents/work/Hackathon/services/ecosystem-mcp/src/services/quality")


@pytest.mark.smoke
@pytest.mark.slow
class TestDiscoveryWorkflow:
    """Test Discovery Engine workflow against real code."""
    
    @pytest.mark.asyncio
    async def test_scan_real_codebase(self):
        """Test scanning the actual ecosystem-mcp codebase."""
        from src.services.discovery.repository_scanner import RepositoryScanner
        
        scanner = RepositoryScanner()
        
        # Scan a small portion (quality module)
        inventory = await scanner.scan(SMALL_TEST_PATH)
        
        # Validate results
        assert inventory is not None
        assert inventory.total_files > 0
        assert len(inventory.files) > 0
        assert inventory.total_size_bytes > 0
        
        # Should detect Python files
        python_key = "Python" if "Python" in inventory.languages else "python"
        assert python_key in inventory.languages
        assert inventory.languages[python_key] > 0
        
        print(f"✅ Scanned {inventory.total_files} files, {inventory.total_size_bytes} bytes")
        print(f"   Languages: {inventory.languages}")
    
    @pytest.mark.asyncio
    async def test_classify_real_files(self):
        """Test file classification on real code files."""
        from src.services.discovery.file_classifier import FileClassifier
        
        classifier = FileClassifier()
        
        # Test on actual source files
        test_files = [
            SMALL_TEST_PATH / "completeness_checker.py",
            SMALL_TEST_PATH / "accuracy_validator.py",
            SMALL_TEST_PATH / "__init__.py"
        ]
        
        # Filter existing files and convert to FileInfo format
        from src.services.discovery.repository_scanner import FileInfo
        from pathlib import Path
        existing_files = [f for f in test_files if f.exists()]
        
        if existing_files:
            # Convert to FileInfo objects with all required fields
            file_infos = [
                FileInfo(
                    path=f,
                    relative_path=f.name,
                    size_bytes=f.stat().st_size,
                    extension=f.suffix,
                    language="python" if f.suffix == ".py" else "unknown",
                    is_code=f.suffix == ".py",
                    is_test="test_" in f.name or "_test" in f.name,
                    is_doc=f.suffix in [".md", ".rst", ".txt"],
                    is_config=f.suffix in [".json", ".yaml", ".yml", ".toml"]
                )
                for f in existing_files
            ]
            
            classifications = await classifier.classify(file_infos)
            
            assert classifications is not None
            assert len(classifications) > 0
            
            for classified in classifications:
                print(f"✅ Classified {classified.file_info.path}: importance={classified.importance_level}")
    
    @pytest.mark.asyncio
    async def test_create_processing_plan(self):
        """Test processing plan creation for real codebase."""
        from src.services.discovery.repository_scanner import RepositoryScanner
        from src.services.discovery.processing_planner import ProcessingPlanner
        
        scanner = RepositoryScanner()
        planner = ProcessingPlanner()
        
        # Scan small test path
        inventory = await scanner.scan(SMALL_TEST_PATH)
        
        # Create plan (provide empty classified_files list for now)
        plan = await planner.create_plan(inventory, classified_files=[], repo_path=str(SMALL_TEST_PATH))
        
        assert plan is not None
        # Plan is created even with empty classified_files
        assert len(plan.sub_jobs) > 0
        assert plan.repo_path is not None
        
        print(f"✅ Created plan: {plan.total_files} files, {len(plan.sub_jobs)} sub-jobs")


@pytest.mark.smoke
@pytest.mark.slow
class TestAnalysisWorkflow:
    """Test Analysis Engine workflow against real code."""
    
    @pytest.mark.asyncio
    async def test_detect_technology_stack(self):
        """Test technology stack detection on real codebase."""
        from src.services.analysis.stack_detector import TechnologyStackDetector
        
        detector = TechnologyStackDetector()
        
        # Analyze quality module
        files = list(SMALL_TEST_PATH.glob("*.py"))
        files = [str(f) for f in files if f.is_file()]
        
        if files:
            # Convert file paths to dict format expected by detect_stack
            file_dicts = [{"path": f, "type": "python"} for f in files]
            stack = await detector.detect_stack(file_dicts, str(SMALL_TEST_PATH))
            
            assert stack is not None
            assert len(stack.languages) > 0
            assert "Python" in stack.languages
            
            print(f"✅ Detected stack: {stack.languages}")
            if stack.frameworks:
                print(f"   Frameworks: {stack.frameworks}")
    
    @pytest.mark.asyncio
    async def test_detect_architecture_patterns(self):
        """Test architecture detection on real codebase."""
        from src.services.analysis.architecture_detector import ArchitectureDetector
        
        detector = ArchitectureDetector()
        
        # Get all Python files in test path
        files = list(SMALL_TEST_PATH.glob("*.py"))
        files = [str(f) for f in files if f.is_file()]
        
        if files:
            # Convert file paths to dict format expected by detect_architecture
            file_dicts = [{"path": f, "type": "python"} for f in files]
            patterns = await detector.detect_architecture(file_dicts, str(SMALL_TEST_PATH))
            
            assert patterns is not None
            
            print(f"✅ Detected architecture patterns: {patterns}")
    
    @pytest.mark.asyncio
    async def test_full_analysis_engine(self):
        """Test complete analysis engine workflow."""
        from src.services.analysis.analysis_engine import get_analysis_engine
        
        engine = get_analysis_engine()
        
        # Get files from quality module
        files = list(SMALL_TEST_PATH.glob("*.py"))
        file_dicts = [
            {
                'path': str(f),
                'relative_path': f.name,
                'language': 'python',
                'is_code': True
            }
            for f in files if f.is_file()
        ]
        
        if file_dicts:
            report = await engine.analyze(
                plan_id="smoke-test",
                files=file_dicts,
                repo_path=str(SMALL_TEST_PATH)
            )
            
            assert report is not None
            assert report.total_files > 0
            
            print(f"✅ Analysis complete: {report.total_files} files analyzed")
            print(f"   Modularity score: {report.modularity_score:.2f}")


@pytest.mark.smoke
@pytest.mark.slow
class TestQualityWorkflow:
    """Test Quality Assurance workflow."""
    
    @pytest.mark.asyncio
    async def test_validate_documentation_artifact(self):
        """Test quality validation on a sample documentation artifact."""
        from src.services.quality import (
            get_completeness_checker,
            get_accuracy_validator,
            get_confidence_scorer
        )
        
        # Create a realistic documentation artifact
        artifact = {
            'title': 'Quality Module Documentation',
            'type': 'guide',
            'content': '''# Quality Module Documentation

## Overview
The quality module provides comprehensive documentation quality assurance
through multi-dimensional validation including completeness, accuracy, and
confidence scoring.

## Architecture
The module consists of five main components:
- CompletenessChecker: Validates section coverage
- AccuracyValidator: Validates technical correctness
- ConfidenceScorer: Calculates weighted confidence scores
- ReviewWorkflowManager: Manages review queue
- QualityReporter: Generates quality reports

## Usage
```python
from src.services.quality import get_completeness_checker

checker = get_completeness_checker()
result = await checker.check(artifact)
```

## API Reference
- `check(artifact)`: Validate completeness
- `validate(artifact)`: Validate accuracy
- `score(artifact)`: Calculate confidence

## Examples
See the unit tests for comprehensive examples of each component.
''',
            'word_count': 150
        }
        
        # Step 1: Completeness
        checker = get_completeness_checker()
        comp_result = await checker.check(artifact)
        
        assert comp_result is not None
        assert comp_result.overall_score > 0
        
        # Step 2: Accuracy
        validator = get_accuracy_validator()
        acc_result = await validator.validate(artifact)
        
        assert acc_result is not None
        assert acc_result.overall_score > 0
        
        # Step 3: Confidence
        scorer = get_confidence_scorer()
        conf_score = await scorer.score(artifact, comp_result, acc_result)
        
        assert conf_score is not None
        assert 0 <= conf_score.overall_confidence <= 1
        
        print(f"✅ Quality validation complete:")
        print(f"   Completeness: {comp_result.overall_score:.2f}")
        print(f"   Accuracy: {acc_result.overall_score:.2f}")
        print(f"   Confidence: {conf_score.overall_confidence:.2f}")
        print(f"   Priority: {conf_score.review_priority}")


@pytest.mark.smoke
@pytest.mark.slow
class TestEndToEndPipeline:
    """Test complete end-to-end workflows."""
    
    @pytest.mark.asyncio
    async def test_discovery_to_analysis_pipeline(self):
        """Test Discovery → Analysis pipeline."""
        from src.services.discovery.repository_scanner import RepositoryScanner
        from src.services.discovery.processing_planner import ProcessingPlanner
        from src.services.analysis.analysis_engine import get_analysis_engine
        
        # Step 1: Discover
        scanner = RepositoryScanner()
        inventory = await scanner.scan(SMALL_TEST_PATH)
        
        assert inventory.total_files > 0
        print(f"✅ Step 1: Discovered {inventory.total_files} files")
        
        # Step 2: Plan
        planner = ProcessingPlanner()
        plan = await planner.create_plan(inventory, classified_files=[], repo_path=str(SMALL_TEST_PATH))
        
        assert len(plan.sub_jobs) > 0
        print(f"✅ Step 2: Created {len(plan.sub_jobs)} sub-jobs")
        
        # Step 3: Analyze (use first sub-job)
        if plan.sub_jobs:
            first_job = plan.sub_jobs[0]
            file_dicts = [
                {
                    'path': str(f.path),
                    'relative_path': f.relative_path,
                    'language': f.language,
                    'is_code': f.is_code
                }
                for f in first_job.files[:5]  # Just first 5 files
            ]
            
            engine = get_analysis_engine()
            report = await engine.analyze(
                plan_id="e2e-smoke-test",
                files=file_dicts,
                repo_path=str(SMALL_TEST_PATH)
            )
            
            assert report is not None
            print(f"✅ Step 3: Analysis complete")
            print(f"   Files analyzed: {report.total_files}")
            print(f"   Modularity: {report.modularity_score:.2f}")
    
    @pytest.mark.asyncio
    async def test_analysis_to_quality_pipeline(self):
        """Test Analysis → Documentation → Quality pipeline."""
        from src.services.quality import (
            get_completeness_checker,
            get_accuracy_validator,
            get_confidence_scorer,
            get_quality_reporter
        )
        
        # Simulate documentation generation output
        artifacts = [
            {
                'title': 'Architecture Overview',
                'type': 'architecture',
                'content': '''# System Architecture

## Overview
Comprehensive system architecture description with proper structure.

## Components
- Discovery Engine
- Analysis Engine
- Documentation Generator
- Quality Assurance

## Data Flow
Documents flow through discovery, analysis, generation, and validation.
''',
                'word_count': 50
            },
            {
                'title': 'API Reference',
                'type': 'api_reference',
                'content': '''# API Reference

## Endpoints
GET /api/v1/health
POST /api/v1/documents
GET /api/v1/quality/report/{id}

## Authentication
Bearer token required for all endpoints.
''',
                'word_count': 30
            }
        ]
        
        # Validate all artifacts
        checker = get_completeness_checker()
        validator = get_accuracy_validator()
        scorer = get_confidence_scorer()
        
        completeness_results = []
        accuracy_results = []
        confidence_scores = []
        
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
            run_id="e2e-quality-test",
            completeness_results=completeness_results,
            accuracy_results=accuracy_results,
            confidence_scores=confidence_scores
        )
        
        assert report is not None
        assert report.total_artifacts == len(artifacts)
        
        print(f"✅ Quality pipeline complete:")
        print(f"   Artifacts: {report.total_artifacts}")
        print(f"   Avg Completeness: {report.average_completeness:.2f}")
        print(f"   Avg Accuracy: {report.average_accuracy:.2f}")
        print(f"   Avg Confidence: {report.average_confidence:.2f}")


@pytest.mark.smoke
class TestSystemIntegration:
    """Test system integration and health."""
    
    def test_all_modules_importable(self):
        """Test all major modules can be imported."""
        modules = [
            "src.services.discovery.repository_scanner",
            "src.services.discovery.file_classifier",
            "src.services.discovery.processing_planner",
            "src.services.orchestration.job_orchestrator",
            "src.services.analysis.analysis_engine",
            "src.services.analysis.stack_detector",
            "src.services.analysis.architecture_detector",
            "src.services.documentation.doc_orchestrator",
            "src.services.quality.completeness_checker",
            "src.services.quality.accuracy_validator",
            "src.services.quality.confidence_scorer",
        ]
        
        failed = []
        succeeded = []
        
        for module_name in modules:
            try:
                __import__(module_name)
                succeeded.append(module_name)
                print(f"✅ {module_name}")
            except ModuleNotFoundError as e:
                # Skip if missing dependencies (e.g., running outside Docker)
                print(f"⚠️  {module_name} - Missing dependency: {e}")
                pytest.skip(f"Missing dependency for {module_name}: {e}")
            except Exception as e:
                failed.append((module_name, str(e)))
                print(f"❌ {module_name}: {e}")
        
        # Report summary
        print(f"\n✅ Imported: {len(succeeded)}/{len(modules)}")
        
        # Only fail if there are actual import errors (not missing deps)
        if failed:
            pytest.fail(f"❌ Failed to import {len(failed)} modules: {failed}")
    
    def test_all_singletons_accessible(self):
        """Test all singleton getters work."""
        from src.services.analysis.analysis_engine import get_analysis_engine
        from src.services.quality import (
            get_completeness_checker,
            get_accuracy_validator,
            get_confidence_scorer,
            get_review_workflow_manager,
            get_quality_reporter
        )
        
        singletons = {
            "AnalysisEngine": get_analysis_engine,
            "CompletenessChecker": get_completeness_checker,
            "AccuracyValidator": get_accuracy_validator,
            "ConfidenceScorer": get_confidence_scorer,
            "ReviewWorkflowManager": get_review_workflow_manager,
            "QualityReporter": get_quality_reporter,
        }
        
        for name, getter in singletons.items():
            try:
                instance = getter()
                assert instance is not None
                print(f"✅ {name} singleton")
            except Exception as e:
                pytest.fail(f"❌ Failed to get {name}: {e}")


if __name__ == "__main__":
    # Run smoke tests
    pytest.main([__file__, "-v", "-m", "smoke", "--tb=short", "-s"])

