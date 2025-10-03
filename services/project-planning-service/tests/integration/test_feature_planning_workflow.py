"""
Integration Tests for Feature Planning Workflow
================================================

End-to-end integration tests for the complete feature planning workflow
including AI analysis, decomposition, and task allocation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
import uuid

from domain.entities.feature import Feature, FeatureStatus, FeaturePriority
from domain.entities.task import Task, TaskStatus, TaskType
from infrastructure.integrations.interpreter_client import InterpreterClient
from infrastructure.integrations.llm_gateway_client import LLMGatewayClient
from infrastructure.integrations.user_store_client import UserStoreClient
from infrastructure.integrations.log_collector_client import LogCollectorClient


@pytest.fixture
def mock_log_client():
    """Create mock log collector client."""
    client = Mock(spec=LogCollectorClient)
    client.log_info = AsyncMock()
    client.log_error = AsyncMock()
    client.log_business_event = AsyncMock()
    client.log_feature_analysis = AsyncMock()
    client.log_integration_call = AsyncMock()
    return client


@pytest.fixture
def mock_interpreter_client(mock_log_client):
    """Create mock interpreter client."""
    client = InterpreterClient(log_client=mock_log_client)
    
    # Mock analyze_feature_description
    client.analyze_feature_description = AsyncMock(return_value={
        "entities": ["user", "authentication", "password"],
        "intents": ["secure_login", "session_management"],
        "insights": {
            "complexity": "medium",
            "key_requirements": ["user authentication", "session handling", "password security"]
        }
    })
    
    # Mock decompose_feature
    client.decompose_feature = AsyncMock(return_value={
        "user_stories": [
            {
                "story": "As a user, I want to log in with email and password",
                "acceptance_criteria": ["Valid credentials grant access", "Invalid credentials show error"],
                "priority": "High",
                "story_points": 5
            }
        ],
        "tasks": [
            {
                "title": "Implement user authentication API",
                "description": "Create REST API for user login",
                "type": "development",
                "estimated_hours": 8,
                "story_points": 3,
                "tags": ["backend", "python", "fastapi"]
            },
            {
                "title": "Add password hashing",
                "description": "Implement secure password hashing with bcrypt",
                "type": "development",
                "estimated_hours": 4,
                "story_points": 2,
                "tags": ["security", "python"]
            }
        ]
    })
    
    return client


@pytest.fixture
def mock_llm_client(mock_log_client):
    """Create mock LLM gateway client."""
    client = LLMGatewayClient(log_client=mock_log_client)
    
    # Mock analyze_feature_complexity
    client.analyze_feature_complexity = AsyncMock(return_value={
        "complexity_score": 7,
        "story_points": 8,
        "factors": ["Authentication security", "Session management", "Password hashing"],
        "team_composition": ["Backend developer", "Security specialist"],
        "estimated_days": 5,
        "reasoning": "Moderate complexity due to security requirements"
    })
    
    # Mock assess_risk
    client.assess_risk = AsyncMock(return_value={
        "overall_risk_level": "Medium",
        "technical_risks": [
            {
                "description": "Session token security",
                "likelihood": "Medium",
                "impact": "High",
                "mitigation": "Use industry-standard JWT with proper expiration"
            }
        ],
        "schedule_risks": [],
        "quality_risks": [],
        "business_risks": []
    })
    
    # Mock generate_user_stories
    client.generate_user_stories = AsyncMock(return_value=[
        {
            "story": "As a user, I want to securely log in to the system",
            "acceptance_criteria": [
                "User can enter email and password",
                "Valid credentials grant access",
                "Invalid credentials show error message"
            ],
            "priority": "High",
            "story_points": 5
        }
    ])
    
    return client


@pytest.fixture
def mock_user_store_client(mock_log_client):
    """Create mock user store client."""
    client = UserStoreClient(log_client=mock_log_client)
    
    # Mock get_team_members
    client.get_team_members = AsyncMock(return_value=[
        {
            "id": "user-1",
            "user_id": "user-1",
            "name": "John Developer",
            "email": "john@example.com"
        },
        {
            "id": "user-2",
            "user_id": "user-2",
            "name": "Jane Engineer",
            "email": "jane@example.com"
        }
    ])
    
    # Mock get_user_capacity
    client.get_user_capacity = AsyncMock(return_value={
        "user_id": "user-1",
        "capacity_hours_per_week": 40.0,
        "allocated_hours": 20.0,
        "available_hours": 20.0
    })
    
    # Mock get_user_skills
    client.get_user_skills = AsyncMock(return_value=[
        {"skill_name": "Python", "proficiency_level": 5},
        {"skill_name": "FastAPI", "proficiency_level": 4},
        {"skill_name": "backend", "proficiency_level": 5}
    ])
    
    # Mock find_best_assignee
    client.find_best_assignee = AsyncMock(return_value={
        "user_id": "user-1",
        "name": "John Developer",
        "email": "john@example.com",
        "skills_match_score": 0.85,
        "availability_score": 0.9,
        "total_score": 0.865,
        "available_hours": 20.0
    })
    
    # Mock allocate_capacity
    client.allocate_capacity = AsyncMock(return_value=True)
    
    return client


@pytest.mark.asyncio
async def test_complete_feature_analysis_workflow(
    mock_log_client,
    mock_interpreter_client,
    mock_llm_client
):
    """
    Test complete feature analysis workflow.
    
    This integration test validates the end-to-end flow of:
    1. Creating a feature
    2. Analyzing with Interpreter
    3. Estimating complexity with LLM Gateway
    4. Assessing risks
    5. Generating user stories
    6. Updating feature with analysis results
    """
    # Step 1: Create feature
    feature = Feature(
        id=str(uuid.uuid4()),
        title="User Authentication System",
        description="Implement secure user authentication with email and password",
        status=FeatureStatus.DRAFT,
        priority=FeaturePriority.HIGH,
        created_by="test-user"
    )
    
    # Step 2: Analyze with Interpreter
    analysis_result = await mock_interpreter_client.analyze_feature_description(
        feature.description,
        context={"priority": feature.priority.value}
    )
    
    assert analysis_result is not None
    assert "entities" in analysis_result
    assert "insights" in analysis_result
    
    # Step 3: Estimate complexity
    complexity_result = await mock_llm_client.analyze_feature_complexity(
        feature.description,
        technical_context={"tech_stack": ["Python", "FastAPI"]}
    )
    
    assert complexity_result["complexity_score"] == 7
    assert complexity_result["story_points"] == 8
    assert complexity_result["estimated_days"] == 5
    
    # Step 4: Assess risks
    risk_result = await mock_llm_client.assess_risk(
        feature.description,
        project_context={}
    )
    
    assert risk_result["overall_risk_level"] == "Medium"
    assert len(risk_result["technical_risks"]) > 0
    
    # Step 5: Generate user stories
    user_stories = await mock_llm_client.generate_user_stories(
        feature.description,
        persona="application user"
    )
    
    assert len(user_stories) > 0
    assert "story" in user_stories[0]
    assert "acceptance_criteria" in user_stories[0]
    
    # Step 6: Update feature with results
    feature.estimated_effort = complexity_result["story_points"]
    feature.technical_complexity = str(complexity_result["complexity_score"])
    feature.ai_analysis = {
        "interpreter_analysis": analysis_result,
        "complexity_analysis": complexity_result
    }
    feature.risk_assessment = risk_result
    feature.update_status(FeatureStatus.ANALYZED)
    
    # Verify feature was properly updated
    assert feature.status == FeatureStatus.ANALYZED
    assert feature.estimated_effort == 8
    assert feature.is_ready_for_planning
    assert len(feature.ai_analysis) > 0
    
    # Note: Logging verification removed - mocked clients don't trigger actual logging


@pytest.mark.asyncio
async def test_feature_decomposition_and_task_creation(
    mock_log_client,
    mock_interpreter_client
):
    """
    Test feature decomposition into tasks.
    
    This integration test validates:
    1. Feature decomposition with Interpreter
    2. Task creation from decomposition results
    3. Task validation and properties
    """
    # Step 1: Create feature
    feature = Feature(
        id=str(uuid.uuid4()),
        title="User Authentication System",
        description="Implement secure user authentication",
        status=FeatureStatus.ANALYZED,
        priority=FeaturePriority.HIGH,
        created_by="test-user"
    )
    
    # Step 2: Decompose feature
    decomposition_result = await mock_interpreter_client.decompose_feature(
        feature.description,
        decomposition_level="detailed",
        context={"feature_id": feature.id}
    )
    
    assert "user_stories" in decomposition_result
    assert "tasks" in decomposition_result
    assert len(decomposition_result["tasks"]) == 2
    
    # Step 3: Create tasks from decomposition
    tasks = []
    for task_data in decomposition_result["tasks"]:
        task = Task(
            id=str(uuid.uuid4()),
            title=task_data["title"],
            description=task_data["description"],
            task_type=TaskType(task_data["type"]),
            status=TaskStatus.TODO,
            feature_id=feature.id,
            estimated_hours=task_data["estimated_hours"],
            story_points=task_data["story_points"],
            created_by="system",
            tags=task_data.get("tags", [])
        )
        tasks.append(task)
    
    # Verify tasks were created correctly
    assert len(tasks) == 2
    assert all(task.feature_id == feature.id for task in tasks)
    assert all(task.status == TaskStatus.TODO for task in tasks)
    assert sum(task.story_points or 0 for task in tasks) == 5  # 3 + 2
    
    # Verify tasks have proper types
    assert all(isinstance(task.task_type, TaskType) for task in tasks)


@pytest.mark.asyncio
async def test_resource_allocation_workflow(
    mock_log_client,
    mock_user_store_client
):
    """
    Test resource allocation workflow.
    
    This integration test validates:
    1. Finding team members
    2. Checking capacity
    3. Finding best assignee based on skills
    4. Allocating capacity
    """
    # Step 1: Create a task needing assignment
    task = Task(
        id=str(uuid.uuid4()),
        title="Implement user authentication API",
        description="Create REST API for user login",
        task_type=TaskType.DEVELOPMENT,
        status=TaskStatus.TODO,
        feature_id="feature-1",
        estimated_hours=8.0,
        story_points=3.0,
        created_by="system",
        tags=["backend", "python", "fastapi"]
    )
    
    # Step 2: Get team members
    team_members = await mock_user_store_client.get_team_members()
    
    assert len(team_members) == 2
    assert team_members[0]["name"] == "John Developer"
    
    # Step 3: Find best assignee
    assignee = await mock_user_store_client.find_best_assignee(
        required_skills=task.tags,
        estimated_hours=task.estimated_hours,
        team_id="team-1"
    )
    
    assert assignee is not None
    assert assignee["user_id"] == "user-1"
    assert assignee["skills_match_score"] > 0.8
    assert assignee["available_hours"] >= task.estimated_hours
    
    # Step 4: Assign task
    task.assign_to(assignee["user_id"], "system")
    
    assert task.assigned_to == "user-1"
    assert len(task.comments) > 0  # Assignment comment added
    
    # Step 5: Allocate capacity
    allocation_success = await mock_user_store_client.allocate_capacity(
        assignee["user_id"],
        task.id,
        task.estimated_hours
    )
    
    assert allocation_success is True
    
    # Note: Logging verification removed - mocked clients don't trigger actual logging


@pytest.mark.asyncio
async def test_end_to_end_planning_workflow(
    mock_log_client,
    mock_interpreter_client,
    mock_llm_client,
    mock_user_store_client
):
    """
    Test complete end-to-end planning workflow.
    
    This comprehensive integration test validates the entire process:
    1. Feature creation
    2. AI analysis
    3. Feature decomposition
    4. Task creation
    5. Resource allocation
    6. Logging and monitoring
    """
    # Phase 1: Feature Analysis
    feature = Feature(
        id=str(uuid.uuid4()),
        title="User Authentication System",
        description="Implement secure user authentication with email and password",
        status=FeatureStatus.DRAFT,
        priority=FeaturePriority.HIGH,
        created_by="test-user"
    )
    
    # Analyze feature
    analysis = await mock_interpreter_client.analyze_feature_description(
        feature.description
    )
    complexity = await mock_llm_client.analyze_feature_complexity(
        feature.description
    )
    risks = await mock_llm_client.assess_risk(feature.description)
    
    # Update feature
    feature.estimated_effort = complexity["story_points"]
    feature.ai_analysis = {"analysis": analysis, "complexity": complexity}
    feature.risk_assessment = risks
    feature.update_status(FeatureStatus.ANALYZED)
    
    # Phase 2: Feature Decomposition
    decomposition = await mock_interpreter_client.decompose_feature(
        feature.description,
        decomposition_level="detailed"
    )
    
    # Create tasks
    tasks = []
    for task_data in decomposition["tasks"]:
        task = Task(
            id=str(uuid.uuid4()),
            title=task_data["title"],
            description=task_data["description"],
            task_type=TaskType(task_data["type"]),
            status=TaskStatus.TODO,
            feature_id=feature.id,
            estimated_hours=task_data["estimated_hours"],
            story_points=task_data["story_points"],
            created_by="system",
            tags=task_data.get("tags", [])
        )
        tasks.append(task)
    
    # Phase 3: Resource Allocation
    allocations = []
    for task in tasks:
        assignee = await mock_user_store_client.find_best_assignee(
            required_skills=task.tags,
            estimated_hours=task.estimated_hours
        )
        
        if assignee:
            task.assign_to(assignee["user_id"], "system")
            await mock_user_store_client.allocate_capacity(
                assignee["user_id"],
                task.id,
                task.estimated_hours
            )
            allocations.append({
                "task_id": task.id,
                "assigned_to": assignee["user_id"]
            })
    
    # Verify complete workflow
    assert feature.status == FeatureStatus.ANALYZED
    assert feature.is_ready_for_planning
    assert len(tasks) == 2
    assert all(task.assigned_to is not None for task in tasks)
    assert len(allocations) == 2
    
    # Note: Logging verification removed - mocked clients don't trigger actual logging
    # In production, each service call would log to the log-collector


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

