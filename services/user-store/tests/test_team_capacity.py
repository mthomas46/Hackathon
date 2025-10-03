"""
Tests for Team Capacity Models
==============================

Unit tests for team capacity management domain models.
"""

import pytest
from datetime import datetime, date, timedelta
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.models.team_capacity import (
    Skill,
    TeamMember,
    TaskAssignment,
    TeamCapacity,
    TeamVelocity,
    ProficiencyLevel,
    MemberRole,
    AssignmentStatus
)


class TestSkill:
    """Test suite for Skill model."""
    
    def test_skill_creation(self):
        """Test basic skill creation."""
        skill = Skill(
            skill_name="Python",
            proficiency_level=ProficiencyLevel.ADVANCED,
            years_experience=5.0
        )
        
        assert skill.skill_name == "Python"
        assert skill.proficiency_level == ProficiencyLevel.ADVANCED
        assert skill.years_experience == 5.0
    
    def test_skill_validation_negative_experience(self):
        """Test validation prevents negative years of experience."""
        with pytest.raises(ValueError, match="cannot be negative"):
            Skill(
                skill_name="Python",
                proficiency_level=ProficiencyLevel.BEGINNER,
                years_experience=-1.0
            )
    
    def test_skill_is_recent(self):
        """Test recent skill usage detection."""
        recent_skill = Skill(
            skill_name="Python",
            proficiency_level=ProficiencyLevel.ADVANCED,
            last_used=date.today() - timedelta(days=30)
        )
        
        old_skill = Skill(
            skill_name="Java",
            proficiency_level=ProficiencyLevel.INTERMEDIATE,
            last_used=date.today() - timedelta(days=200)
        )
        
        assert recent_skill.is_recent(months=6)
        assert not old_skill.is_recent(months=6)
    
    def test_skill_proficiency_score(self):
        """Test proficiency score calculation."""
        skill = Skill(
            skill_name="Python",
            proficiency_level=ProficiencyLevel.ADVANCED,  # 4/5 = 0.8
            years_experience=5.0,  # Bonus: min(5/10, 0.2) = 0.2
            last_used=date.today()  # No penalty
        )
        
        # Expected: 0.8 + 0.2 = 1.0
        assert skill.proficiency_score() == 1.0
    
    def test_skill_proficiency_score_with_recency_penalty(self):
        """Test proficiency score with recency penalty."""
        skill = Skill(
            skill_name="Python",
            proficiency_level=ProficiencyLevel.PROFICIENT,  # 3/5 = 0.6
            years_experience=2.0,  # Bonus: min(2/10, 0.2) = 0.2
            last_used=date.today() - timedelta(days=200)  # Penalty: 0.1
        )
        
        # Expected: 0.6 + 0.2 - 0.1 = 0.7
        assert skill.proficiency_score() == pytest.approx(0.7)


class TestTeamMember:
    """Test suite for TeamMember model."""
    
    def test_team_member_creation(self):
        """Test basic team member creation."""
        member = TeamMember.create(
            user_id="user-123",
            team_id="team-456",
            name="John Doe",
            role=MemberRole.DEVELOPER
        )
        
        assert member.user_id == "user-123"
        assert member.team_id == "team-456"
        assert member.name == "John Doe"
        assert member.role == MemberRole.DEVELOPER
        assert member.is_active
        assert member.capacity_hours == 40
    
    def test_team_member_validation(self):
        """Test team member validation."""
        with pytest.raises(ValueError, match="Capacity hours cannot be negative"):
            TeamMember(
                id="mem-123",
                user_id="user-123",
                team_id="team-456",
                name="John Doe",
                role=MemberRole.DEVELOPER,
                capacity_hours=-10
            )
    
    def test_add_skill(self):
        """Test adding skills to team member."""
        member = TeamMember.create("user-123", "team-456", "John Doe", MemberRole.DEVELOPER)
        
        skill = Skill(
            skill_name="Python",
            proficiency_level=ProficiencyLevel.ADVANCED,
            years_experience=5.0
        )
        
        member.add_skill(skill)
        
        assert "Python" in member.skills
        assert member.skills["Python"].proficiency_level == ProficiencyLevel.ADVANCED
    
    def test_has_skill(self):
        """Test skill checking."""
        member = TeamMember.create("user-123", "team-456", "John Doe", MemberRole.DEVELOPER)
        
        member.add_skill(Skill("Python", ProficiencyLevel.ADVANCED, 5.0))
        member.add_skill(Skill("JavaScript", ProficiencyLevel.BEGINNER, 0.5))
        
        # Has Python at any level
        assert member.has_skill("Python")
        
        # Has Python at intermediate or higher
        assert member.has_skill("Python", ProficiencyLevel.INTERMEDIATE)
        
        # Does not have JavaScript at intermediate level
        assert not member.has_skill("JavaScript", ProficiencyLevel.INTERMEDIATE)
        
        # Does not have skill at all
        assert not member.has_skill("Rust")
    
    def test_get_skill_score(self):
        """Test getting skill proficiency score."""
        member = TeamMember.create("user-123", "team-456", "John Doe", MemberRole.DEVELOPER)
        
        skill = Skill(
            skill_name="Python",
            proficiency_level=ProficiencyLevel.ADVANCED,
            years_experience=5.0,
            last_used=date.today()
        )
        member.add_skill(skill)
        
        # Skill exists
        assert member.get_skill_score("Python") == 1.0
        
        # Skill doesn't exist
        assert member.get_skill_score("Rust") == 0.0
    
    def test_available_capacity_hours(self):
        """Test available capacity calculation."""
        member = TeamMember(
            id="mem-123",
            user_id="user-123",
            team_id="team-456",
            name="John Doe",
            role=MemberRole.DEVELOPER,
            capacity_hours=40,
            availability=0.8,  # 80% available
            current_workload_hours=20.0
        )
        
        # Available: 40 * 0.8 - 20 = 32 - 20 = 12
        assert member.available_capacity_hours() == 12.0
    
    def test_capacity_utilization(self):
        """Test capacity utilization calculation."""
        member = TeamMember(
            id="mem-123",
            user_id="user-123",
            team_id="team-456",
            name="John Doe",
            role=MemberRole.DEVELOPER,
            capacity_hours=40,
            current_workload_hours=30.0
        )
        
        # Utilization: 30 / 40 = 0.75
        assert member.capacity_utilization() == 0.75
    
    def test_is_overloaded(self):
        """Test overload detection."""
        member = TeamMember(
            id="mem-123",
            user_id="user-123",
            team_id="team-456",
            name="John Doe",
            role=MemberRole.DEVELOPER,
            capacity_hours=40,
            availability=0.8,  # 32 hours available
            current_workload_hours=35.0  # Overloaded
        )
        
        assert member.is_overloaded()
    
    def test_is_available_for_hours(self):
        """Test availability checking for additional work."""
        member = TeamMember(
            id="mem-123",
            user_id="user-123",
            team_id="team-456",
            name="John Doe",
            role=MemberRole.DEVELOPER,
            capacity_hours=40,
            current_workload_hours=30.0
        )
        
        # Has 10 hours available
        assert member.is_available_for_hours(5.0)
        assert member.is_available_for_hours(10.0)
        assert not member.is_available_for_hours(15.0)
    
    def test_assign_work(self):
        """Test work assignment."""
        member = TeamMember.create("user-123", "team-456", "John Doe", MemberRole.DEVELOPER)
        
        initial_workload = member.current_workload_hours
        member.assign_work(10.0)
        
        assert member.current_workload_hours == initial_workload + 10.0
    
    def test_complete_work(self):
        """Test work completion."""
        member = TeamMember(
            id="mem-123",
            user_id="user-123",
            team_id="team-456",
            name="John Doe",
            role=MemberRole.DEVELOPER,
            capacity_hours=40,
            current_workload_hours=20.0
        )
        
        member.complete_work(10.0)
        
        assert member.current_workload_hours == 10.0


class TestTaskAssignment:
    """Test suite for TaskAssignment model."""
    
    def test_assignment_creation(self):
        """Test basic assignment creation."""
        assignment = TaskAssignment.create(
            task_id="task-123",
            member_id="member-456",
            estimated_hours=8.0,
            confidence_score=0.85
        )
        
        assert assignment.task_id == "task-123"
        assert assignment.member_id == "member-456"
        assert assignment.estimated_hours == 8.0
        assert assignment.confidence_score == 0.85
        assert assignment.status == AssignmentStatus.ASSIGNED
    
    def test_assignment_validation(self):
        """Test assignment validation."""
        with pytest.raises(ValueError, match="Estimated hours cannot be negative"):
            TaskAssignment(
                id="asn-123",
                task_id="task-123",
                member_id="member-456",
                estimated_hours=-5.0
            )
    
    def test_assignment_start(self):
        """Test starting an assignment."""
        assignment = TaskAssignment.create("task-123", "member-456", 8.0)
        
        assignment.start()
        
        assert assignment.status == AssignmentStatus.IN_PROGRESS
        assert assignment.started_at is not None
    
    def test_assignment_complete(self):
        """Test completing an assignment."""
        assignment = TaskAssignment.create("task-123", "member-456", 8.0)
        
        assignment.complete(actual_hours=10.0)
        
        assert assignment.status == AssignmentStatus.COMPLETED
        assert assignment.actual_hours == 10.0
        assert assignment.completed_at is not None
    
    def test_assignment_block(self):
        """Test blocking an assignment."""
        assignment = TaskAssignment.create("task-123", "member-456", 8.0)
        
        assignment.block(notes="Waiting for API documentation")
        
        assert assignment.status == AssignmentStatus.BLOCKED
        assert "API documentation" in assignment.notes
    
    def test_assignment_cancel(self):
        """Test cancelling an assignment."""
        assignment = TaskAssignment.create("task-123", "member-456", 8.0)
        
        assignment.cancel(notes="Task no longer needed")
        
        assert assignment.status == AssignmentStatus.CANCELLED
        assert assignment.completed_at is not None
    
    def test_variance_calculation(self):
        """Test variance calculation."""
        assignment = TaskAssignment.create("task-123", "member-456", 8.0)
        assignment.complete(actual_hours=10.0)
        
        # Variance: 10 - 8 = 2
        assert assignment.variance_hours() == 2.0
        
        # Percentage: (2 / 8) * 100 = 25%
        assert assignment.variance_percentage() == 25.0


class TestTeamCapacity:
    """Test suite for TeamCapacity model."""
    
    def test_capacity_creation(self):
        """Test basic capacity creation."""
        capacity = TeamCapacity.create(
            team_id="team-123",
            week_start=date.today(),
            available_hours=160  # 4 people * 40 hours
        )
        
        assert capacity.team_id == "team-123"
        assert capacity.available_hours == 160
        assert capacity.allocated_hours == 0
        assert capacity.blocked_hours == 0
    
    def test_capacity_validation(self):
        """Test capacity validation."""
        with pytest.raises(ValueError, match="Available hours cannot be negative"):
            TeamCapacity(
                id="cap-123",
                team_id="team-456",
                week_start=date.today(),
                available_hours=-100
            )
    
    def test_remaining_hours(self):
        """Test remaining capacity calculation."""
        capacity = TeamCapacity(
            id="cap-123",
            team_id="team-456",
            week_start=date.today(),
            available_hours=160,
            allocated_hours=100,
            blocked_hours=20
        )
        
        # Remaining: 160 - 100 - 20 = 40
        assert capacity.remaining_hours() == 40
    
    def test_utilization_percentage(self):
        """Test utilization percentage calculation."""
        capacity = TeamCapacity(
            id="cap-123",
            team_id="team-456",
            week_start=date.today(),
            available_hours=160,
            allocated_hours=120,
            blocked_hours=20
        )
        
        # Utilization: (120 + 20) / 160 * 100 = 87.5%
        assert capacity.utilization_percentage() == 87.5
    
    def test_is_overallocated(self):
        """Test overallocation detection."""
        capacity = TeamCapacity(
            id="cap-123",
            team_id="team-456",
            week_start=date.today(),
            available_hours=160,
            allocated_hours=150,
            blocked_hours=20  # Total: 170 > 160
        )
        
        assert capacity.is_overallocated()
    
    def test_can_allocate_hours(self):
        """Test checking if hours can be allocated."""
        capacity = TeamCapacity(
            id="cap-123",
            team_id="team-456",
            week_start=date.today(),
            available_hours=160,
            allocated_hours=100,
            blocked_hours=20
        )
        
        # 40 hours remaining
        assert capacity.can_allocate_hours(30)
        assert capacity.can_allocate_hours(40)
        assert not capacity.can_allocate_hours(50)
    
    def test_allocate(self):
        """Test allocating hours."""
        capacity = TeamCapacity.create("team-123", date.today(), 160)
        
        capacity.allocate(50)
        assert capacity.allocated_hours == 50
        
        capacity.allocate(30)
        assert capacity.allocated_hours == 80
    
    def test_deallocate(self):
        """Test deallocating hours."""
        capacity = TeamCapacity(
            id="cap-123",
            team_id="team-456",
            week_start=date.today(),
            available_hours=160,
            allocated_hours=100
        )
        
        capacity.deallocate(30)
        assert capacity.allocated_hours == 70


class TestTeamVelocity:
    """Test suite for TeamVelocity model."""
    
    def test_velocity_creation(self):
        """Test basic velocity creation."""
        velocity = TeamVelocity(
            team_id="team-123",
            sprint_name="Sprint 1",
            start_date=date.today() - timedelta(days=14),
            end_date=date.today(),
            planned_story_points=50,
            completed_story_points=45,
            committed_hours=160.0,
            actual_hours=155.0,
            tasks_planned=20,
            tasks_completed=18
        )
        
        assert velocity.team_id == "team-123"
        assert velocity.sprint_name == "Sprint 1"
        assert velocity.planned_story_points == 50
        assert velocity.completed_story_points == 45
    
    def test_completion_rate(self):
        """Test completion rate calculation."""
        velocity = TeamVelocity(
            team_id="team-123",
            sprint_name="Sprint 1",
            start_date=date.today() - timedelta(days=14),
            end_date=date.today(),
            planned_story_points=50,
            completed_story_points=45
        )
        
        # Completion: 45 / 50 = 0.9
        assert velocity.completion_rate() == 0.9
    
    def test_task_completion_rate(self):
        """Test task completion rate."""
        velocity = TeamVelocity(
            team_id="team-123",
            sprint_name="Sprint 1",
            start_date=date.today() - timedelta(days=14),
            end_date=date.today(),
            tasks_planned=20,
            tasks_completed=18
        )
        
        # Task completion: 18 / 20 = 0.9
        assert velocity.task_completion_rate() == 0.9
    
    def test_hours_per_story_point(self):
        """Test hours per story point calculation."""
        velocity = TeamVelocity(
            team_id="team-123",
            sprint_name="Sprint 1",
            start_date=date.today() - timedelta(days=14),
            end_date=date.today(),
            completed_story_points=45,
            actual_hours=135.0
        )
        
        # Hours per point: 135 / 45 = 3.0
        assert velocity.hours_per_story_point() == 3.0
    
    def test_efficiency_ratio(self):
        """Test efficiency ratio calculation."""
        velocity = TeamVelocity(
            team_id="team-123",
            sprint_name="Sprint 1",
            start_date=date.today() - timedelta(days=14),
            end_date=date.today(),
            committed_hours=160.0,
            actual_hours=155.0
        )
        
        # Efficiency: 155 / 160 = 0.96875
        assert velocity.efficiency_ratio() == 0.96875
    
    def test_is_successful_sprint(self):
        """Test sprint success evaluation."""
        successful_velocity = TeamVelocity(
            team_id="team-123",
            sprint_name="Sprint 1",
            start_date=date.today() - timedelta(days=14),
            end_date=date.today(),
            planned_story_points=50,
            completed_story_points=45  # 90% completion
        )
        
        unsuccessful_velocity = TeamVelocity(
            team_id="team-123",
            sprint_name="Sprint 2",
            start_date=date.today() - timedelta(days=14),
            end_date=date.today(),
            planned_story_points=50,
            completed_story_points=35  # 70% completion
        )
        
        # Default threshold: 80%
        assert successful_velocity.is_successful_sprint()
        assert not unsuccessful_velocity.is_successful_sprint()
        
        # Custom threshold: 70%
        assert unsuccessful_velocity.is_successful_sprint(threshold=0.7)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

