"""
Tests for Feature Decomposition Engine
======================================

Unit tests for AI-powered feature decomposition.
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.services.feature_decomposer import (
    FeatureDecomposer,
    DecompositionRequest,
    DecompositionResult,
    DecompositionStrategy,
    UserStory,
    TechnicalTask
)
from domain.entities.feature import Feature, FeaturePriority, FeatureStatus
from domain.entities.task import Task, TaskType, TaskStatus


@pytest.fixture
def decomposer():
    """Create feature decomposer instance."""
    return FeatureDecomposer()


@pytest.fixture
def sample_feature():
    """Create sample feature for testing."""
    return Feature(
        id="feat-auth",
        title="User Authentication System",
        description="Implement secure user authentication with login, signup, and password reset functionality",
        priority=FeaturePriority.HIGH,
        estimated_effort=13.0,
        status=FeatureStatus.DRAFT
    )


@pytest.fixture
def complex_feature():
    """Create complex feature for testing."""
    return Feature(
        id="feat-complex",
        title="E-commerce Payment Gateway Integration",
        description="Integrate multiple payment gateways with fraud detection, subscription management, and automated reconciliation",
        priority=FeaturePriority.CRITICAL,
        estimated_effort=34.0,
        status=FeatureStatus.DRAFT,
        dependencies=["feat-user-mgmt", "feat-security"]
    )


class TestFeatureDecomposer:
    """Test suite for Feature Decomposer."""
    
    def test_decomposer_initialization(self, decomposer):
        """Test decomposer initialization."""
        assert decomposer is not None
        assert decomposer.interpreter_client is None  # No client injected
        assert decomposer.llm_gateway_client is None
    
    @pytest.mark.asyncio
    async def test_decompose_feature_basic(self, decomposer, sample_feature):
        """Test basic feature decomposition."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.BALANCED
        )
        
        result = await decomposer.decompose_feature(request)
        
        assert isinstance(result, DecompositionResult)
        assert result.feature == sample_feature
        assert len(result.tasks) > 0
        assert result.total_estimated_hours > 0
    
    @pytest.mark.asyncio
    async def test_user_story_generation(self, decomposer, sample_feature):
        """Test user story generation."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.USER_STORY_FIRST,
            include_technical_tasks=False
        )
        
        result = await decomposer.decompose_feature(request)
        
        assert len(result.user_stories) > 0
        for story in result.user_stories:
            assert isinstance(story, UserStory)
            assert story.as_a is not None
            assert story.i_want is not None
            assert story.so_that is not None
            assert len(story.acceptance_criteria) > 0
    
    @pytest.mark.asyncio
    async def test_technical_task_generation(self, decomposer, sample_feature):
        """Test technical task generation."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.TECHNICAL_FIRST,
            include_user_stories=False
        )
        
        result = await decomposer.decompose_feature(request)
        
        assert len(result.technical_tasks) > 0
        for task in result.technical_tasks:
            assert isinstance(task, TechnicalTask)
            assert task.task_type in TaskType
            assert task.estimated_hours > 0
    
    @pytest.mark.asyncio
    async def test_balanced_decomposition(self, decomposer, sample_feature):
        """Test balanced decomposition strategy."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.BALANCED
        )
        
        result = await decomposer.decompose_feature(request)
        
        # Should have both user stories and technical tasks
        assert len(result.user_stories) > 0
        assert len(result.technical_tasks) > 0
        assert len(result.tasks) > 0
    
    @pytest.mark.asyncio
    async def test_minimal_decomposition(self, decomposer, sample_feature):
        """Test minimal decomposition strategy."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.MINIMAL
        )
        
        result = await decomposer.decompose_feature(request)
        
        # Minimal should have fewer tasks
        assert len(result.tasks) > 0
        assert len(result.tasks) < 10  # Should be relatively few
    
    @pytest.mark.asyncio
    async def test_task_limit(self, decomposer, sample_feature):
        """Test max_tasks limit."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.TECHNICAL_FIRST,
            max_tasks=3
        )
        
        result = await decomposer.decompose_feature(request)
        
        assert len(result.tasks) <= 3
    
    @pytest.mark.asyncio
    async def test_complexity_assessment(self, decomposer, sample_feature, complex_feature):
        """Test complexity assessment."""
        # Simple feature
        request1 = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.MINIMAL
        )
        result1 = await decomposer.decompose_feature(request1)
        
        # Complex feature
        request2 = DecompositionRequest(
            feature=complex_feature,
            strategy=DecompositionStrategy.TECHNICAL_FIRST
        )
        result2 = await decomposer.decompose_feature(request2)
        
        # Complex feature should have higher complexity
        complexity_order = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        assert complexity_order[result2.complexity_assessment] >= complexity_order[result1.complexity_assessment]
    
    @pytest.mark.asyncio
    async def test_risk_identification(self, decomposer, complex_feature):
        """Test risk factor identification."""
        request = DecompositionRequest(
            feature=complex_feature,
            strategy=DecompositionStrategy.BALANCED
        )
        
        result = await decomposer.decompose_feature(request)
        
        # Complex feature with dependencies and CRITICAL priority should have risks
        assert len(result.risk_factors) > 0
    
    @pytest.mark.asyncio
    async def test_recommendations_generation(self, decomposer, complex_feature):
        """Test recommendation generation."""
        request = DecompositionRequest(
            feature=complex_feature,
            strategy=DecompositionStrategy.TECHNICAL_FIRST
        )
        
        result = await decomposer.decompose_feature(request)
        
        # Complex feature should have recommendations
        assert len(result.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_task_conversion(self, decomposer, sample_feature):
        """Test conversion to Task entities."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.BALANCED
        )
        
        result = await decomposer.decompose_feature(request)
        
        # All tasks should be Task entities
        for task in result.tasks:
            assert isinstance(task, Task)
            assert task.feature_id == sample_feature.id
            assert task.status == TaskStatus.TODO
            assert task.estimated_hours > 0
    
    @pytest.mark.asyncio
    async def test_effort_calculation(self, decomposer, sample_feature):
        """Test total effort calculation."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.BALANCED
        )
        
        result = await decomposer.decompose_feature(request)
        
        # Total hours should match sum of task hours
        expected_hours = sum(t.estimated_hours for t in result.tasks if t.estimated_hours)
        assert result.total_estimated_hours == expected_hours
        assert result.total_estimated_hours > 0
    
    @pytest.mark.asyncio
    async def test_story_points_calculation(self, decomposer, sample_feature):
        """Test story points calculation."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.BALANCED
        )
        
        result = await decomposer.decompose_feature(request)
        
        assert result.total_story_points > 0
    
    def test_batch_decomposition(self, decomposer):
        """Test batch decomposition of multiple features."""
        features = [
            Feature("f1", "Feature 1", "Description 1", estimated_effort=5.0),
            Feature("f2", "Feature 2", "Description 2", estimated_effort=8.0),
            Feature("f3", "Feature 3", "Description 3", estimated_effort=13.0)
        ]
        
        results = decomposer.decompose_multiple_features(
            features,
            strategy=DecompositionStrategy.BALANCED
        )
        
        assert len(results) == 3
        assert "f1" in results
        assert "f2" in results
        assert "f3" in results
        
        for feature_id, result in results.items():
            assert isinstance(result, DecompositionResult)
            assert len(result.tasks) > 0
    
    @pytest.mark.asyncio
    async def test_task_dependencies(self, decomposer, sample_feature):
        """Test that technical tasks have proper dependencies."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.TECHNICAL_FIRST,
            include_user_stories=False
        )
        
        result = await decomposer.decompose_feature(request)
        
        # Check that later tasks may have dependencies on earlier tasks
        task_ids = [t.id for t in result.technical_tasks]
        for i, task in enumerate(result.technical_tasks):
            if i > 0:
                # Later tasks should have dependencies
                if task.dependencies:
                    # Dependencies should reference earlier tasks
                    for dep in task.dependencies:
                        assert dep in task_ids[:i]


class TestUserStory:
    """Test suite for UserStory dataclass."""
    
    def test_user_story_creation(self):
        """Test user story creation."""
        story = UserStory(
            id="story-1",
            title="Login Feature",
            description="User login functionality",
            as_a="registered user",
            i_want="login to my account",
            so_that="I can access my data",
            acceptance_criteria=["Can login with email", "Can login with username"],
            estimated_effort=5.0,
            priority="HIGH"
        )
        
        assert story.id == "story-1"
        assert story.as_a == "registered user"
        assert len(story.acceptance_criteria) == 2
        assert story.estimated_effort == 5.0


class TestTechnicalTask:
    """Test suite for TechnicalTask dataclass."""
    
    def test_technical_task_creation(self):
        """Test technical task creation."""
        task = TechnicalTask(
            id="task-1",
            title="Implement Auth API",
            description="Create authentication API endpoints",
            task_type=TaskType.DEVELOPMENT,
            estimated_hours=8.0,
            dependencies=["task-0"],
            tags=["backend", "api"],
            complexity="MEDIUM"
        )
        
        assert task.id == "task-1"
        assert task.task_type == TaskType.DEVELOPMENT
        assert task.estimated_hours == 8.0
        assert len(task.dependencies) == 1
        assert len(task.tags) == 2


class TestDecompositionResult:
    """Test suite for DecompositionResult."""
    
    @pytest.mark.asyncio
    async def test_task_count(self, decomposer, sample_feature):
        """Test task_count method."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.BALANCED
        )
        
        result = await decomposer.decompose_feature(request)
        
        assert result.task_count() == len(result.tasks)
        assert result.task_count() > 0
    
    @pytest.mark.asyncio
    async def test_average_task_size(self, decomposer, sample_feature):
        """Test average_task_size calculation."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.BALANCED
        )
        
        result = await decomposer.decompose_feature(request)
        
        avg_size = result.average_task_size()
        assert avg_size > 0
        
        # Calculate expected average
        expected_avg = result.total_estimated_hours / len(result.tasks)
        assert avg_size == expected_avg
    
    def test_average_task_size_no_tasks(self):
        """Test average_task_size with no tasks."""
        feature = Feature("f1", "Feature 1", "Description")
        result = DecompositionResult(
            feature=feature,
            user_stories=[],
            technical_tasks=[],
            tasks=[],
            total_estimated_hours=0.0,
            total_story_points=0.0,
            complexity_assessment="LOW"
        )
        
        assert result.average_task_size() == 0.0


class TestDecompositionStrategies:
    """Test different decomposition strategies."""
    
    @pytest.mark.asyncio
    async def test_user_story_first_strategy(self, decomposer, sample_feature):
        """Test USER_STORY_FIRST strategy."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.USER_STORY_FIRST
        )
        
        result = await decomposer.decompose_feature(request)
        
        # Should have more user stories than other strategies
        assert len(result.user_stories) >= 3
    
    @pytest.mark.asyncio
    async def test_technical_first_strategy(self, decomposer, sample_feature):
        """Test TECHNICAL_FIRST strategy."""
        request = DecompositionRequest(
            feature=sample_feature,
            strategy=DecompositionStrategy.TECHNICAL_FIRST
        )
        
        result = await decomposer.decompose_feature(request)
        
        # Should have comprehensive technical tasks
        assert len(result.technical_tasks) >= 4
        
        # Should include additional technical tasks like code review
        task_types = [t.task_type for t in result.technical_tasks]
        assert TaskType.DEVELOPMENT in task_types
        assert TaskType.TESTING in task_types
    
    @pytest.mark.asyncio
    async def test_strategy_comparison(self, decomposer, sample_feature):
        """Compare different strategies."""
        strategies = [
            DecompositionStrategy.USER_STORY_FIRST,
            DecompositionStrategy.TECHNICAL_FIRST,
            DecompositionStrategy.BALANCED,
            DecompositionStrategy.MINIMAL
        ]
        
        results = {}
        for strategy in strategies:
            request = DecompositionRequest(
                feature=sample_feature,
                strategy=strategy
            )
            result = await decomposer.decompose_feature(request)
            results[strategy] = result
        
        # Minimal should have fewest tasks
        minimal_result = results[DecompositionStrategy.MINIMAL]
        for strategy, result in results.items():
            if strategy != DecompositionStrategy.MINIMAL:
                assert result.task_count() >= minimal_result.task_count()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

