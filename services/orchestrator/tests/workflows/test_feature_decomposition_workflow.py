"""
Integration tests for Workflow A: Feature Decomposition
Phase 2 Day 2 - Enhanced Roadmap v2.0
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.orchestrator.domain.workflows.feature_decomposition_workflow import (
    FeatureDecompositionWorkflow,
    UserStory,
    TechnicalTask,
    FeatureBreakdown
)


@pytest.fixture
def mock_workflow_logger():
    """Mock WorkflowLogger for testing."""
    logger = MagicMock()
    logger.log_workflow_start = AsyncMock()
    logger.log_workflow_step = AsyncMock()
    logger.log_workflow_complete = AsyncMock()
    logger.log_error = AsyncMock()
    return logger


@pytest.fixture
def workflow(mock_workflow_logger):
    """Create FeatureDecompositionWorkflow instance with mocked logger."""
    return FeatureDecompositionWorkflow(
        llm_gateway_url="http://mock-llm:5000",
        prompt_store_url="http://mock-prompt:5110",
        analysis_service_url="http://mock-analysis:8004",
        workflow_logger=mock_workflow_logger
    )


class TestFeatureDecompositionWorkflow:
    """Test Workflow A: AI-Powered Feature Decomposition."""
    
    @pytest.mark.asyncio
    async def test_execute_with_basic_fallback(self, workflow, mock_workflow_logger):
        """Test execute method with basic fallback when services unavailable."""
        # Mock external services to fail (use fallback logic)
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            result = await workflow.execute(
                feature_title="User Authentication",
                feature_description="Implement OAuth2 authentication for mobile app",
                context={"platform": "mobile"}
            )
            
            # Verify result structure
            assert isinstance(result, FeatureBreakdown)
            assert result.feature_title == "User Authentication"
            assert len(result.user_stories) >= 1
            assert len(result.technical_tasks) >= 1
            assert result.total_story_points > 0
            assert result.total_estimated_hours > 0
            assert 0.0 <= result.complexity_score <= 1.0
            assert result.risk_level in ["low", "medium", "high"]
            
            # Verify logging was called
            mock_workflow_logger.log_workflow_start.assert_called_once()
            mock_workflow_logger.log_workflow_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_default_template(self, workflow):
        """Test default template is valid and contains required placeholders."""
        template = workflow._get_default_template()
        
        assert len(template) > 100
        assert "{feature_title}" in template
        assert "{feature_description}" in template
        assert "{context}" in template
        assert "user_stories" in template.lower()
        assert "technical_tasks" in template.lower()
    
    @pytest.mark.asyncio
    async def test_parse_llm_response_valid_json(self, workflow):
        """Test parsing valid JSON response from LLM."""
        llm_response = json.dumps({
            "user_stories": [
                {
                    "title": "User login",
                    "description": "As a user, I want to login",
                    "acceptance_criteria": ["Valid credentials work"],
                    "story_points": 5,
                    "priority": "high"
                }
            ],
            "technical_tasks": [
                {
                    "user_story_index": 0,
                    "title": "Implement login endpoint",
                    "description": "Create POST /login",
                    "task_type": "backend",
                    "estimated_hours": 8,
                    "complexity": "medium"
                }
            ]
        })
        
        result = workflow._parse_llm_response(llm_response)
        
        assert "user_stories" in result
        assert "technical_tasks" in result
        assert len(result["user_stories"]) == 1
        assert len(result["technical_tasks"]) == 1
    
    @pytest.mark.asyncio
    async def test_parse_llm_response_markdown_json(self, workflow):
        """Test parsing JSON wrapped in markdown code blocks."""
        llm_response = """Here's the breakdown:

```json
{
  "user_stories": [{"title": "Test story"}],
  "technical_tasks": []
}
```

That's it!"""
        
        result = workflow._parse_llm_response(llm_response)
        
        assert "user_stories" in result
        assert len(result["user_stories"]) == 1
    
    @pytest.mark.asyncio
    async def test_parse_llm_response_invalid_json(self, workflow):
        """Test handling of invalid JSON response."""
        llm_response = "This is not JSON at all!"
        
        result = workflow._parse_llm_response(llm_response)
        
        # Should return empty structure
        assert "user_stories" in result
        assert "technical_tasks" in result
        assert len(result["user_stories"]) == 0
        assert len(result["technical_tasks"]) == 0
    
    @pytest.mark.asyncio
    async def test_create_user_stories(self, workflow):
        """Test conversion of dict data to UserStory objects."""
        stories_data = [
            {
                "title": "Login feature",
                "description": "User authentication",
                "acceptance_criteria": ["Criteria 1", "Criteria 2"],
                "story_points": 5,
                "priority": "high",
                "dependencies": ["story_0"],
                "tags": ["auth", "security"]
            },
            {
                "title": "Password reset",
                "description": "Reset forgotten password",
                "acceptance_criteria": ["Criteria 1"],
                "story_points": 3,
                "priority": "medium"
            }
        ]
        
        user_stories = workflow._create_user_stories(stories_data)
        
        assert len(user_stories) == 2
        assert all(isinstance(story, UserStory) for story in user_stories)
        assert user_stories[0].id == "story_1"
        assert user_stories[1].id == "story_2"
        assert user_stories[0].title == "Login feature"
        assert user_stories[0].story_points == 5
        assert user_stories[0].priority == "high"
        assert len(user_stories[0].tags) == 2
    
    @pytest.mark.asyncio
    async def test_create_technical_tasks(self, workflow):
        """Test conversion of dict data to TechnicalTask objects."""
        user_stories = [
            UserStory(
                id="story_1",
                title="Login",
                description="User login",
                acceptance_criteria=[]
            ),
            UserStory(
                id="story_2",
                title="Signup",
                description="User signup",
                acceptance_criteria=[]
            )
        ]
        
        tasks_data = [
            {
                "user_story_index": 0,
                "title": "Create login API",
                "description": "Backend API for login",
                "task_type": "backend",
                "estimated_hours": 8,
                "complexity": "medium",
                "dependencies": [],
                "required_skills": ["Python", "FastAPI"]
            },
            {
                "user_story_index": 1,
                "title": "Create signup form",
                "description": "Frontend signup form",
                "task_type": "frontend",
                "estimated_hours": 6,
                "complexity": "simple",
                "required_skills": ["React"]
            }
        ]
        
        technical_tasks = workflow._create_technical_tasks(tasks_data, user_stories)
        
        assert len(technical_tasks) == 2
        assert all(isinstance(task, TechnicalTask) for task in technical_tasks)
        assert technical_tasks[0].user_story_id == "story_1"
        assert technical_tasks[1].user_story_id == "story_2"
        assert technical_tasks[0].task_type == "backend"
        assert technical_tasks[1].task_type == "frontend"
        assert technical_tasks[0].estimated_hours == 8
        assert len(technical_tasks[0].required_skills) == 2
    
    @pytest.mark.asyncio
    async def test_create_basic_breakdown(self, workflow):
        """Test basic fallback breakdown creation."""
        feature_title = "Payment System"
        feature_description = "Implement payment processing"
        
        user_stories, technical_tasks = workflow._create_basic_breakdown(
            feature_title, feature_description
        )
        
        # Should create at least 1 story and 3 tasks (design, implement, test)
        assert len(user_stories) >= 1
        assert len(technical_tasks) >= 3
        assert user_stories[0].title == f"Implement {feature_title}"
        assert user_stories[0].story_points == 5.0
        assert all(task.user_story_id == "story_1" for task in technical_tasks)
    
    @pytest.mark.asyncio
    async def test_calculate_complexity_score_simple(self, workflow):
        """Test complexity calculation for simple features."""
        user_stories = [
            UserStory(
                id="story_1",
                title="Simple feature",
                description="Easy",
                acceptance_criteria=[],
                story_points=3
            )
        ]
        
        technical_tasks = [
            TechnicalTask(
                id="task_1",
                user_story_id="story_1",
                title="Simple task",
                description="Easy task",
                task_type="backend",
                estimated_hours=4,
                complexity="simple"
            )
        ]
        
        score = await workflow._calculate_complexity_score(
            user_stories, technical_tasks, "test_wf"
        )
        
        assert 0.0 <= score <= 1.0
        assert score < 0.3  # Should be low complexity
    
    @pytest.mark.asyncio
    async def test_calculate_complexity_score_complex(self, workflow):
        """Test complexity calculation for complex features."""
        user_stories = [
            UserStory(
                id=f"story_{i}",
                title=f"Story {i}",
                description="Complex",
                acceptance_criteria=[],
                story_points=8
            )
            for i in range(8)  # Many stories
        ]
        
        technical_tasks = [
            TechnicalTask(
                id=f"task_{i}",
                user_story_id="story_1",
                title=f"Task {i}",
                description="Complex task",
                task_type="backend",
                estimated_hours=16,
                complexity="complex",
                required_skills=["skill1", "skill2", "skill3"]
            )
            for i in range(15)  # Many complex tasks
        ]
        
        score = await workflow._calculate_complexity_score(
            user_stories, technical_tasks, "test_wf"
        )
        
        assert 0.0 <= score <= 1.0
        assert score > 0.6  # Should be high complexity
    
    @pytest.mark.asyncio
    async def test_assess_risks_low(self, workflow):
        """Test risk assessment for low-risk features."""
        user_stories = [
            UserStory(
                id="story_1",
                title="Simple",
                description="Easy",
                acceptance_criteria=[],
                story_points=3
            )
        ]
        
        technical_tasks = [
            TechnicalTask(
                id="task_1",
                user_story_id="story_1",
                title="Simple task",
                description="Easy",
                task_type="backend",
                estimated_hours=4,
                complexity="simple",
                required_skills=["Python"]
            )
        ]
        
        risk_level, risk_factors = await workflow._assess_risks(
            user_stories, technical_tasks, complexity_score=0.2, workflow_id="test"
        )
        
        assert risk_level in ["low", "medium", "high"]
        assert isinstance(risk_factors, list)
        # Low complexity should have few risk factors
        assert len(risk_factors) <= 2
    
    @pytest.mark.asyncio
    async def test_assess_risks_high(self, workflow):
        """Test risk assessment for high-risk features."""
        user_stories = [
            UserStory(
                id=f"story_{i}",
                title=f"Story {i}",
                description="Complex",
                acceptance_criteria=[],
                story_points=13,
                dependencies=[f"story_{i-1}"] if i > 0 else []
            )
            for i in range(10)  # Many stories with dependencies
        ]
        
        technical_tasks = [
            TechnicalTask(
                id=f"task_{i}",
                user_story_id="story_1",
                title=f"Task {i}",
                description="Complex",
                task_type="backend",
                estimated_hours=20,
                complexity="complex",
                required_skills=[f"skill_{i}"],  # Many diverse skills
                dependencies=[f"task_{i-1}"] if i > 0 else []
            )
            for i in range(15)
        ]
        
        risk_level, risk_factors = await workflow._assess_risks(
            user_stories, technical_tasks, complexity_score=0.9, workflow_id="test"
        )
        
        assert risk_level == "high"
        assert len(risk_factors) >= 3
        # Should identify various risk factors
        risk_text = " ".join(risk_factors).lower()
        assert any(keyword in risk_text for keyword in ["complexity", "dependencies", "skills", "story points"])


class TestWorkflowADataStructures:
    """Test data structures for Workflow A."""
    
    def test_user_story_creation(self):
        """Test UserStory dataclass creation."""
        story = UserStory(
            id="story_1",
            title="Login feature",
            description="User authentication",
            acceptance_criteria=["Criteria 1", "Criteria 2"],
            story_points=5.0,
            priority="high",
            dependencies=["story_0"],
            tags=["auth"]
        )
        
        assert story.id == "story_1"
        assert story.title == "Login feature"
        assert story.story_points == 5.0
        assert story.priority == "high"
        assert len(story.acceptance_criteria) == 2
        assert len(story.dependencies) == 1
        assert len(story.tags) == 1
    
    def test_technical_task_creation(self):
        """Test TechnicalTask dataclass creation."""
        task = TechnicalTask(
            id="task_1",
            user_story_id="story_1",
            title="Implement login API",
            description="Backend API",
            task_type="backend",
            estimated_hours=8.0,
            complexity="medium",
            dependencies=["task_0"],
            required_skills=["Python", "FastAPI"]
        )
        
        assert task.id == "task_1"
        assert task.user_story_id == "story_1"
        assert task.task_type == "backend"
        assert task.estimated_hours == 8.0
        assert task.complexity == "medium"
        assert len(task.required_skills) == 2
    
    def test_feature_breakdown_creation(self):
        """Test FeatureBreakdown dataclass creation."""
        breakdown = FeatureBreakdown(
            feature_id="feature_1",
            feature_title="Authentication",
            user_stories=[],
            technical_tasks=[],
            total_story_points=15.0,
            total_estimated_hours=40.0,
            complexity_score=0.6,
            risk_level="medium",
            risk_factors=["Factor 1", "Factor 2"],
            workflow_id="wf_123"
        )
        
        assert breakdown.feature_id == "feature_1"
        assert breakdown.total_story_points == 15.0
        assert breakdown.complexity_score == 0.6
        assert breakdown.risk_level == "medium"
        assert len(breakdown.risk_factors) == 2
        assert isinstance(breakdown.created_at, datetime)

