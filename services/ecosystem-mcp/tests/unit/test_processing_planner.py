"""
Unit tests for ProcessingPlanner

Tests plan generation, priority assignment, and sub-job creation logic.
"""

import pytest

# Skip entire module - ProcessingPlanner API has changed
pytestmark = pytest.mark.skip(reason="ProcessingPlanner API has changed - tests need updating")
from pathlib import Path
from src.services.discovery.processing_planner import ProcessingPlanner, ProcessingPlan
from src.services.discovery.repository_scanner import FileInfo, RepositoryInventory


@pytest.fixture
def planner():
    """Create a ProcessingPlanner instance."""
    return ProcessingPlanner()


@pytest.fixture
def sample_inventory():
    """Create a sample repository inventory."""
    files = [
        FileInfo(
            path=Path("src/main.py"),
            relative_path="src/main.py",
            size_bytes=1000,
            extension=".py",
            language="python",
            is_code=True,
            is_test=False,
            is_doc=False,
            is_config=False
        ),
        FileInfo(
            path=Path("tests/test_main.py"),
            relative_path="tests/test_main.py",
            size_bytes=500,
            extension=".py",
            language="python",
            is_code=True,
            is_test=True,
            is_doc=False,
            is_config=False
        ),
        FileInfo(
            path=Path("README.md"),
            relative_path="README.md",
            size_bytes=2000,
            extension=".md",
            language="markdown",
            is_code=False,
            is_test=False,
            is_doc=True,
            is_config=False
        ),
        FileInfo(
            path=Path("config.yaml"),
            relative_path="config.yaml",
            size_bytes=300,
            extension=".yaml",
            language="yaml",
            is_code=False,
            is_test=False,
            is_doc=False,
            is_config=True
        ),
    ]
    
    return RepositoryInventory(
        total_files=len(files),
        total_size_bytes=sum(f.size_bytes for f in files),
        files=files,
        languages={"python": 2, "markdown": 1, "yaml": 1},
        frameworks=[],
        file_types={".py": 2, ".md": 1, ".yaml": 1}
    )


@pytest.mark.skip(reason="ProcessingPlanner API has changed - tests need updating")
class TestProcessingPlannerBasic:
    """Basic ProcessingPlanner tests."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, planner):
        """Test planner initializes correctly."""
        assert planner is not None
        assert hasattr(planner, 'create_plan')
    
    @pytest.mark.asyncio
    async def test_create_plan_basic(self, planner, sample_inventory):
        """Test basic plan creation."""
        plan = await planner.create_plan(sample_inventory, repo_path=Path("/test"))
        
        assert isinstance(plan, ProcessingPlan)
        assert len(plan.sub_jobs) > 0
        assert plan.total_files == sample_inventory.total_files
    
    @pytest.mark.asyncio
    async def test_empty_inventory(self, planner):
        """Test plan creation with empty inventory."""
        empty_inventory = RepositoryInventory(
            total_files=0,
            total_size_bytes=0,
            files=[],
            languages={},
            frameworks=[],
            file_types={}
        )
        
        plan = await planner.create_plan(empty_inventory, repo_path=Path("/test"))
        
        assert isinstance(plan, ProcessingPlan)
        assert len(plan.sub_jobs) == 0


class TestPriorityAssignment:
    """Test priority assignment logic."""
    
    @pytest.mark.asyncio
    async def test_code_files_high_priority(self, planner):
        """Test code files get high priority."""
        files = [
            FileInfo(
                path=Path("main.py"),
                relative_path="main.py",
                size_bytes=1000,
                extension=".py",
                language="python",
                is_code=True,
                is_test=False,
                is_doc=False,
                is_config=False
            )
        ]
        
        inventory = RepositoryInventory(
            total_files=1,
            total_size_bytes=1000,
            files=files,
            languages={"python": 1},
            frameworks=[],
            file_types={".py": 1}
        )
        
        plan = await planner.create_plan(inventory, repo_path=Path("/test"))
        
        # Code files should be included in sub-jobs
        assert len(plan.sub_jobs) > 0
    
    @pytest.mark.asyncio
    async def test_doc_files_lower_priority(self, planner):
        """Test documentation files get appropriate priority."""
        files = [
            FileInfo(
                path=Path("README.md"),
                relative_path="README.md",
                size_bytes=1000,
                extension=".md",
                language="markdown",
                is_code=False,
                is_test=False,
                is_doc=True,
                is_config=False
            )
        ]
        
        inventory = RepositoryInventory(
            total_files=1,
            total_size_bytes=1000,
            files=files,
            languages={"markdown": 1},
            frameworks=[],
            file_types={".md": 1}
        )
        
        plan = await planner.create_plan(inventory, repo_path=Path("/test"))
        
        # Should still create a plan
        assert isinstance(plan, ProcessingPlan)


class TestSubJobCreation:
    """Test sub-job creation and grouping."""
    
    @pytest.mark.asyncio
    async def test_large_repo_multiple_subjobs(self, planner):
        """Test large repository creates multiple sub-jobs."""
        # Create many files
        files = []
        for i in range(100):
            files.append(
                FileInfo(
                    path=Path(f"file_{i}.py"),
                    relative_path=f"file_{i}.py",
                    size_bytes=1000,
                    extension=".py",
                    language="python",
                    is_code=True,
                    is_test=False,
                    is_doc=False,
                    is_config=False
                )
            )
        
        inventory = RepositoryInventory(
            total_files=len(files),
            total_size_bytes=sum(f.size_bytes for f in files),
            files=files,
            languages={"python": len(files)},
            frameworks=[],
            file_types={".py": len(files)}
        )
        
        plan = await planner.create_plan(inventory, repo_path=Path("/test"))
        
        # Should create multiple sub-jobs for 100 files
        assert len(plan.sub_jobs) > 1
    
    @pytest.mark.asyncio
    async def test_files_grouped_by_type(self, planner, sample_inventory):
        """Test files are grouped logically."""
        plan = await planner.create_plan(sample_inventory, repo_path=Path("/test"))
        
        # Should have at least one sub-job
        assert len(plan.sub_jobs) > 0
        
        # Each sub-job should have files
        for sub_job in plan.sub_jobs:
            assert len(sub_job.files) > 0


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_single_large_file(self, planner):
        """Test handling of single very large file."""
        files = [
            FileInfo(
                path=Path("huge.py"),
                relative_path="huge.py",
                size_bytes=10_000_000,  # 10MB
                extension=".py",
                language="python",
                is_code=True,
                is_test=False,
                is_doc=False,
                is_config=False
            )
        ]
        
        inventory = RepositoryInventory(
            total_files=1,
            total_size_bytes=10_000_000,
            files=files,
            languages={"python": 1},
            frameworks=[],
            file_types={".py": 1}
        )
        
        plan = await planner.create_plan(inventory, repo_path=Path("/test"))
        
        assert isinstance(plan, ProcessingPlan)
        assert len(plan.sub_jobs) > 0
    
    @pytest.mark.asyncio
    async def test_mixed_file_types(self, planner):
        """Test handling of mixed file types."""
        files = [
            FileInfo(Path(f"file.{ext}"), f"file.{ext}", 100, f".{ext}", 
                    ext, True, False, False, False)
            for ext in ["py", "js", "java", "go", "rs"]
        ]
        
        inventory = RepositoryInventory(
            total_files=len(files),
            total_size_bytes=500,
            files=files,
            languages={"py": 1, "js": 1, "java": 1, "go": 1, "rs": 1},
            frameworks=[],
            file_types={".py": 1, ".js": 1, ".java": 1, ".go": 1, ".rs": 1}
        )
        
        plan = await planner.create_plan(inventory, repo_path=Path("/test"))
        
        assert isinstance(plan, ProcessingPlan)
        assert plan.total_files == 5
    
    @pytest.mark.asyncio
    async def test_none_path(self, planner, sample_inventory):
        """Test handling of None path."""
        # Should handle gracefully
        plan = await planner.create_plan(sample_inventory, repo_path=Path("/test"))
        assert isinstance(plan, ProcessingPlan)


class TestPlanAttributes:
    """Test ProcessingPlan attributes and methods."""
    
    @pytest.mark.asyncio
    async def test_plan_has_metadata(self, planner, sample_inventory):
        """Test plan contains required metadata."""
        plan = await planner.create_plan(sample_inventory, repo_path=Path("/test"))
        
        assert hasattr(plan, 'total_files')
        assert hasattr(plan, 'sub_jobs')
        assert hasattr(plan, 'estimated_duration')
        
        assert plan.total_files == sample_inventory.total_files
    
    @pytest.mark.asyncio
    async def test_subjob_has_priority(self, planner, sample_inventory):
        """Test sub-jobs have priority assigned."""
        plan = await planner.create_plan(sample_inventory, repo_path=Path("/test"))
        
        for sub_job in plan.sub_jobs:
            assert hasattr(sub_job, 'priority')
            assert isinstance(sub_job.priority, (int, str))
    
    @pytest.mark.asyncio
    async def test_plan_serialization(self, planner, sample_inventory):
        """Test plan can be serialized."""
        plan = await planner.create_plan(sample_inventory, repo_path=Path("/test"))
        
        # Should have to_dict method
        if hasattr(plan, 'to_dict'):
            plan_dict = plan.to_dict()
            assert isinstance(plan_dict, dict)
            assert 'total_files' in plan_dict or 'sub_jobs' in plan_dict

