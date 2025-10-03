"""
Integration tests for Workflows C & D: Timeline Analysis and Skills Matching
Phase 2 Day 4 - Enhanced Roadmap v2.0
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date, timedelta

from services.orchestrator.domain.workflows.timeline_analysis_workflow import (
    TimelineAnalysisWorkflow,
    TimelineEstimate,
    HistoricalTrend,
    TimelineAnalysisResult
)

from services.orchestrator.domain.workflows.skills_matching_workflow import (
    SkillsMatchingWorkflow,
    TeamMember,
    SkillGap,
    ResourceAllocation,
    SkillsMatchingResult
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
def timeline_workflow(mock_workflow_logger):
    """Create TimelineAnalysisWorkflow instance."""
    return TimelineAnalysisWorkflow(
        project_simulation_url="http://mock-sim:5075",
        analysis_service_url="http://mock-analysis:8004",
        user_store_url="http://mock-user:5130",
        workflow_logger=mock_workflow_logger
    )


@pytest.fixture
def skills_workflow(mock_workflow_logger):
    """Create SkillsMatchingWorkflow instance."""
    return SkillsMatchingWorkflow(
        user_store_url="http://mock-user:5130",
        project_planning_url="http://mock-planning:8000",
        workflow_logger=mock_workflow_logger
    )


@pytest.fixture
def sample_feature_breakdown():
    """Sample feature breakdown for testing."""
    return {
        "feature_id": "test_feature",
        "feature_title": "Authentication System",
        "total_story_points": 40.0,
        "user_stories": [
            {"id": "story_1", "title": "User Login", "story_points": 8},
            {"id": "story_2", "title": "User Registration", "story_points": 5}
        ],
        "technical_tasks": [
            {
                "id": "task_1",
                "title": "Backend API",
                "estimated_hours": 16,
                "complexity": "medium",
                "required_skills": ["Python", "FastAPI"]
            },
            {
                "id": "task_2",
                "title": "Frontend UI",
                "estimated_hours": 12,
                "complexity": "simple",
                "required_skills": ["React", "TypeScript"]
            }
        ]
    }


class TestTimelineAnalysisWorkflow:
    """Test Workflow C: Timeline Analysis."""
    
    @pytest.mark.asyncio
    async def test_execute_with_defaults(self, timeline_workflow, sample_feature_breakdown, mock_workflow_logger):
        """Test execute with default fallback data."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            result = await timeline_workflow.execute(
                feature_breakdown=sample_feature_breakdown,
                team_id="test_team"
            )
            
            assert isinstance(result, TimelineAnalysisResult)
            assert len(result.timeline_estimates) > 0
            assert len(result.historical_trends) > 0
            assert 0.0 <= result.overall_confidence <= 1.0
            assert isinstance(result.estimated_completion_date, date)
            
            mock_workflow_logger.log_workflow_start.assert_called_once()
            mock_workflow_logger.log_workflow_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_default_velocity(self, timeline_workflow):
        """Test default velocity data."""
        velocity = timeline_workflow._get_default_velocity()
        
        assert "average_velocity" in velocity
        assert velocity["average_velocity"] > 0
        assert "sprint_duration_weeks" in velocity
        assert len(velocity["recent_sprints"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_default_trends(self, timeline_workflow):
        """Test default trend data."""
        trends = timeline_workflow._get_default_trends()
        
        assert len(trends) > 0
        assert all(isinstance(t, HistoricalTrend) for t in trends)
        assert any(t.metric_name == "velocity" for t in trends)
    
    @pytest.mark.asyncio
    async def test_calculate_timeline_estimates(self, timeline_workflow, sample_feature_breakdown):
        """Test timeline estimation calculation."""
        velocity_data = timeline_workflow._get_default_velocity()
        trends = timeline_workflow._get_default_trends()
        
        estimates = await timeline_workflow._calculate_timeline_estimates(
            feature_breakdown=sample_feature_breakdown,
            velocity_data=velocity_data,
            historical_trends=trends,
            workflow_id="test"
        )
        
        assert len(estimates) > 0
        for estimate in estimates:
            assert isinstance(estimate, TimelineEstimate)
            assert estimate.estimated_duration_days > 0
            assert estimate.estimated_sprints > 0
            assert 0.0 <= estimate.confidence_level <= 1.0
            assert estimate.best_case_days < estimate.most_likely_days < estimate.worst_case_days
    
    @pytest.mark.asyncio
    async def test_generate_velocity_forecast(self, timeline_workflow):
        """Test velocity forecasting."""
        velocity_data = {
            "average_velocity": 20.0,
            "velocity_trend": "increasing"
        }
        trends = timeline_workflow._get_default_trends()
        
        forecast = await timeline_workflow._generate_velocity_forecast(
            velocity_data=velocity_data,
            historical_trends=trends,
            workflow_id="test"
        )
        
        assert len(forecast) == 6  # 6 sprints
        # Increasing trend should show growth
        assert forecast["sprint_6"] > forecast["sprint_1"]
    
    def test_identify_timeline_risks(self, timeline_workflow):
        """Test risk identification."""
        estimates = [
            TimelineEstimate(
                feature_id="test",
                estimated_duration_days=120,  # Long duration
                estimated_sprints=12,
                confidence_level=0.5,  # Low confidence
                best_case_days=90,
                worst_case_days=150,
                most_likely_days=120,
                velocity_used=20.0
            )
        ]
        
        trends = timeline_workflow._get_default_trends()
        velocity_data = {"velocity_trend": "decreasing"}
        
        risks = timeline_workflow._identify_timeline_risks(
            timeline_estimates=estimates,
            historical_trends=trends,
            velocity_data=velocity_data
        )
        
        assert len(risks) > 0
        # Should identify long duration and decreasing velocity
        risk_text = " ".join(risks).lower()
        assert "90 days" in risk_text or "decreasing" in risk_text
    
    def test_generate_timeline_recommendations(self, timeline_workflow):
        """Test recommendation generation."""
        estimates = [
            TimelineEstimate(
                feature_id="test",
                estimated_duration_days=80,
                estimated_sprints=8,
                confidence_level=0.6,
                best_case_days=60,
                worst_case_days=100,
                most_likely_days=80,
                velocity_used=20.0
            )
        ]
        
        recommendations = timeline_workflow._generate_timeline_recommendations(
            timeline_estimates=estimates,
            risk_factors=[],
            velocity_data={"velocity_trend": "stable"}
        )
        
        assert len(recommendations) > 0
        # Should include general best practices
        rec_text = " ".join(recommendations).lower()
        assert "review" in rec_text or "monitor" in rec_text


class TestSkillsMatchingWorkflow:
    """Test Workflow D: Skills Matching."""
    
    @pytest.mark.asyncio
    async def test_execute_with_defaults(self, skills_workflow, sample_feature_breakdown, mock_workflow_logger):
        """Test execute with default team."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            
            result = await skills_workflow.execute(
                feature_breakdown=sample_feature_breakdown,
                team_id="test_team"
            )
            
            assert isinstance(result, SkillsMatchingResult)
            assert len(result.team_members) > 0
            assert len(result.resource_allocations) >= 0
            assert 0.0 <= result.team_capacity_utilization <= 1.0
            assert 0.0 <= result.overall_readiness <= 1.0
            
            mock_workflow_logger.log_workflow_start.assert_called_once()
            mock_workflow_logger.log_workflow_complete.assert_called_once()
    
    def test_get_default_team(self, skills_workflow):
        """Test default team data."""
        team = skills_workflow._get_default_team()
        
        assert len(team) > 0
        assert all(isinstance(m, TeamMember) for m in team)
        assert all(len(m.skills) > 0 for m in team)
        assert all(0.0 <= m.availability <= 1.0 for m in team)
    
    def test_extract_required_skills(self, skills_workflow, sample_feature_breakdown):
        """Test skills extraction from feature breakdown."""
        skills = skills_workflow._extract_required_skills(sample_feature_breakdown)
        
        assert len(skills) > 0
        assert "Python" in skills
        assert "React" in skills
        # Check skill levels are reasonable
        assert all(1 <= level <= 5 for level in skills.values())
    
    def test_analyze_skill_gaps_no_gaps(self, skills_workflow):
        """Test skill gap analysis with no gaps."""
        required_skills = {"Python": 3, "React": 3}
        team = skills_workflow._get_default_team()
        
        gaps = skills_workflow._analyze_skill_gaps(
            required_skills=required_skills,
            team_members=team
        )
        
        # Default team should have these skills
        assert len(gaps) == 0 or all(g.gap_severity != "critical" for g in gaps)
    
    def test_analyze_skill_gaps_with_gaps(self, skills_workflow):
        """Test skill gap analysis with gaps."""
        required_skills = {"Rust": 4, "Kubernetes": 5}  # Skills not in default team
        team = skills_workflow._get_default_team()
        
        gaps = skills_workflow._analyze_skill_gaps(
            required_skills=required_skills,
            team_members=team
        )
        
        assert len(gaps) > 0
        assert all(isinstance(g, SkillGap) for g in gaps)
        assert all(g.gap_severity in ["minor", "moderate", "critical"] for g in gaps)
    
    def test_match_tasks_to_members(self, skills_workflow, sample_feature_breakdown):
        """Test task matching to team members."""
        team = skills_workflow._get_default_team()
        required_skills = skills_workflow._extract_required_skills(sample_feature_breakdown)
        
        allocations = skills_workflow._match_tasks_to_members(
            feature_breakdown=sample_feature_breakdown,
            team_members=team,
            required_skills=required_skills
        )
        
        assert len(allocations) > 0
        assert all(isinstance(a, ResourceAllocation) for a in allocations)
        assert all(0.0 <= a.match_score <= 1.0 for a in allocations)
        assert all(a.estimated_hours > 0 for a in allocations)
    
    def test_calculate_match_score_perfect_match(self, skills_workflow):
        """Test match score calculation with perfect match."""
        member = TeamMember(
            member_id="test",
            name="Test",
            role="Developer",
            skills=["Python", "FastAPI"],
            skill_levels={"Python": 5, "FastAPI": 4},
            availability=1.0,
            current_capacity=0.0,
            max_capacity=20.0
        )
        
        task_skills = ["Python", "FastAPI"]
        required_skills = {"Python": 3, "FastAPI": 3}
        
        score, reasons = skills_workflow._calculate_match_score(
            member=member,
            task_skills=task_skills,
            required_skills=required_skills
        )
        
        assert score > 0.8  # Should be high match
        assert len(reasons) > 0
    
    def test_calculate_match_score_partial_match(self, skills_workflow):
        """Test match score with partial skills."""
        member = TeamMember(
            member_id="test",
            name="Test",
            role="Developer",
            skills=["Python"],  # Missing React
            skill_levels={"Python": 3},
            availability=0.5,
            current_capacity=15.0,
            max_capacity=20.0
        )
        
        task_skills = ["Python", "React"]
        required_skills = {"Python": 3, "React": 3}
        
        score, reasons = skills_workflow._calculate_match_score(
            member=member,
            task_skills=task_skills,
            required_skills=required_skills
        )
        
        assert 0.0 < score < 0.8  # Should be moderate match
    
    def test_calculate_capacity_utilization(self, skills_workflow):
        """Test capacity utilization calculation."""
        team = [
            TeamMember(
                member_id="m1",
                name="Alice",
                role="Dev",
                skills=[],
                skill_levels={},
                availability=1.0,
                current_capacity=10.0,
                max_capacity=20.0
            ),
            TeamMember(
                member_id="m2",
                name="Bob",
                role="Dev",
                skills=[],
                skill_levels={},
                availability=1.0,
                current_capacity=15.0,
                max_capacity=20.0
            )
        ]
        
        allocations = [
            ResourceAllocation(
                member_id="m1",
                member_name="Alice",
                task_id="t1",
                task_title="Task 1",
                match_score=0.9,
                estimated_hours=8.0,
                confidence=0.9,
                reasons=[]
            )
        ]
        
        utilization = skills_workflow._calculate_capacity_utilization(
            team_members=team,
            resource_allocations=allocations
        )
        
        assert 0.0 <= utilization <= 1.0
    
    def test_generate_recommendations(self, skills_workflow):
        """Test recommendations generation."""
        skill_gaps = [
            SkillGap(
                skill_name="Kubernetes",
                required_level=4,
                available_level=0,
                gap_severity="critical",
                mitigation="Hire specialist"
            )
        ]
        
        team = skills_workflow._get_default_team()
        
        recommendations = skills_workflow._generate_recommendations(
            skill_gaps=skill_gaps,
            capacity_utilization=0.5,
            team_members=team
        )
        
        assert len(recommendations) > 0
        rec_text = " ".join(recommendations).lower()
        assert "critical" in rec_text or "gap" in rec_text
    
    def test_identify_training_needs(self, skills_workflow):
        """Test training needs identification."""
        skill_gaps = [
            SkillGap(
                skill_name="Docker",
                required_level=3,
                available_level=1,
                gap_severity="moderate",
                mitigation="Training"
            ),
            SkillGap(
                skill_name="Kubernetes",
                required_level=4,
                available_level=0,
                gap_severity="critical",
                mitigation="Hire"
            )
        ]
        
        training_needs = skills_workflow._identify_training_needs(skill_gaps)
        
        # Should identify moderate gaps for training
        assert len(training_needs) > 0
        training_text = " ".join(training_needs).lower()
        assert "docker" in training_text
    
    def test_generate_hiring_recommendations(self, skills_workflow):
        """Test hiring recommendations."""
        skill_gaps = [
            SkillGap(
                skill_name="Security Expert",
                required_level=5,
                available_level=0,
                gap_severity="critical",
                mitigation="Hire"
            )
        ]
        
        hiring = skills_workflow._generate_hiring_recommendations(
            skill_gaps=skill_gaps,
            capacity_utilization=0.5
        )
        
        assert len(hiring) > 0
        hiring_text = " ".join(hiring).lower()
        assert "hire" in hiring_text or "security" in hiring_text
    
    def test_calculate_overall_readiness_high(self, skills_workflow):
        """Test readiness calculation with high readiness."""
        readiness = skills_workflow._calculate_overall_readiness(
            skill_gaps=[],  # No gaps
            capacity_utilization=0.7  # Good utilization
        )
        
        assert readiness >= 0.9  # Should be high
    
    def test_calculate_overall_readiness_low(self, skills_workflow):
        """Test readiness calculation with low readiness."""
        skill_gaps = [
            SkillGap("Skill1", 5, 0, "critical", "Hire"),
            SkillGap("Skill2", 4, 0, "critical", "Hire")
        ]
        
        readiness = skills_workflow._calculate_overall_readiness(
            skill_gaps=skill_gaps,
            capacity_utilization=0.98  # Over-capacity
        )
        
        assert readiness < 0.6  # Should be low


class TestWorkflowsIntegration:
    """Test integration between workflows C and D."""
    
    @pytest.mark.asyncio
    async def test_workflows_c_and_d_together(
        self,
        timeline_workflow,
        skills_workflow,
        sample_feature_breakdown,
        mock_workflow_logger
    ):
        """Test running workflows C and D in sequence."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            # Run Workflow C
            timeline_result = await timeline_workflow.execute(
                feature_breakdown=sample_feature_breakdown,
                team_id="test_team"
            )
            
            # Run Workflow D
            skills_result = await skills_workflow.execute(
                feature_breakdown=sample_feature_breakdown,
                team_id="test_team"
            )
            
            # Both should complete successfully
            assert isinstance(timeline_result, TimelineAnalysisResult)
            assert isinstance(skills_result, SkillsMatchingResult)
            
            # Results should be complementary
            assert timeline_result.estimated_completion_date > date.today()
            assert skills_result.overall_readiness >= 0.0

