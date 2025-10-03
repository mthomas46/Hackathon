"""
Tests for Skills Matching Engine
================================

Unit tests for intelligent skills matching and task-to-member assignment.
"""

import pytest
from datetime import date, timedelta
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.services.skills_matcher import (
    SkillsMatcher,
    TaskRequirement,
    MatchResult,
    MatchingStrategy
)
from domain.models.team_capacity import (
    TeamMember,
    Skill,
    ProficiencyLevel,
    MemberRole
)


@pytest.fixture
def skilled_team():
    """Create a team with varied skills."""
    # Senior Python developer
    senior_dev = TeamMember.create("user-1", "team-1", "Alice", MemberRole.SENIOR_DEVELOPER)
    senior_dev.add_skill(Skill("Python", ProficiencyLevel.EXPERT, 8.0, date.today()))
    senior_dev.add_skill(Skill("JavaScript", ProficiencyLevel.ADVANCED, 5.0, date.today()))
    senior_dev.add_skill(Skill("SQL", ProficiencyLevel.PROFICIENT, 6.0, date.today()))
    senior_dev.current_workload_hours = 20.0
    
    # Junior full-stack developer
    junior_dev = TeamMember.create("user-2", "team-1", "Bob", MemberRole.DEVELOPER)
    junior_dev.add_skill(Skill("Python", ProficiencyLevel.INTERMEDIATE, 2.0, date.today()))
    junior_dev.add_skill(Skill("JavaScript", ProficiencyLevel.PROFICIENT, 3.0, date.today()))
    junior_dev.current_workload_hours = 10.0
    
    # Specialized backend developer
    backend_dev = TeamMember.create("user-3", "team-1", "Charlie", MemberRole.DEVELOPER)
    backend_dev.add_skill(Skill("Python", ProficiencyLevel.ADVANCED, 6.0, date.today()))
    backend_dev.add_skill(Skill("SQL", ProficiencyLevel.EXPERT, 7.0, date.today()))
    backend_dev.add_skill(Skill("Redis", ProficiencyLevel.PROFICIENT, 4.0, date.today()))
    backend_dev.current_workload_hours = 35.0  # Almost full
    
    # QA engineer
    qa_engineer = TeamMember.create("user-4", "team-1", "Diana", MemberRole.QA_ENGINEER)
    qa_engineer.add_skill(Skill("Python", ProficiencyLevel.INTERMEDIATE, 3.0, date.today()))
    qa_engineer.add_skill(Skill("Testing", ProficiencyLevel.EXPERT, 5.0, date.today()))
    qa_engineer.current_workload_hours = 15.0
    
    return [senior_dev, junior_dev, backend_dev, qa_engineer]


@pytest.fixture
def python_task():
    """Create a Python development task."""
    return TaskRequirement(
        task_id="task-1",
        required_skills={
            "Python": ProficiencyLevel.PROFICIENT,
            "SQL": ProficiencyLevel.INTERMEDIATE
        },
        estimated_hours=8.0,
        priority=3
    )


class TestTaskRequirement:
    """Test suite for TaskRequirement model."""
    
    def test_task_requirement_creation(self):
        """Test basic task requirement creation."""
        task = TaskRequirement(
            task_id="task-1",
            required_skills={"Python": ProficiencyLevel.ADVANCED},
            estimated_hours=8.0,
            priority=3
        )
        
        assert task.task_id == "task-1"
        assert len(task.required_skills) == 1
        assert task.estimated_hours == 8.0
        assert task.priority == 3
    
    def test_task_validation_hours(self):
        """Test validation of estimated hours."""
        with pytest.raises(ValueError, match="must be positive"):
            TaskRequirement(
                task_id="task-1",
                required_skills={},
                estimated_hours=0.0
            )
    
    def test_task_validation_priority(self):
        """Test validation of priority."""
        with pytest.raises(ValueError, match="Priority must be between"):
            TaskRequirement(
                task_id="task-1",
                required_skills={},
                estimated_hours=8.0,
                priority=10
            )


class TestMatchResult:
    """Test suite for MatchResult model."""
    
    def test_is_qualified(self):
        """Test qualification checking."""
        member = TeamMember.create("user-1", "team-1", "Alice", MemberRole.DEVELOPER)
        task = TaskRequirement("task-1", {"Python": ProficiencyLevel.INTERMEDIATE}, 8.0)
        
        # Qualified (no missing skills)
        qualified_match = MatchResult(
            member=member,
            task_requirement=task,
            match_score=0.8,
            skill_match_score=0.9,
            availability_score=0.8,
            workload_score=0.7,
            role_match_score=1.0,
            missing_skills=[]
        )
        assert qualified_match.is_qualified()
        
        # Unqualified (missing skills)
        unqualified_match = MatchResult(
            member=member,
            task_requirement=task,
            match_score=0.3,
            skill_match_score=0.0,
            availability_score=0.8,
            workload_score=0.7,
            role_match_score=1.0,
            missing_skills=["Python"]
        )
        assert not unqualified_match.is_qualified()
    
    def test_is_available(self):
        """Test availability checking."""
        member = TeamMember.create("user-1", "team-1", "Alice", MemberRole.DEVELOPER)
        member.capacity_hours = 40
        member.current_workload_hours = 30.0
        
        # Available (10 hours free, task needs 8)
        small_task = TaskRequirement("task-1", {}, 8.0)
        match1 = MatchResult(
            member=member,
            task_requirement=small_task,
            match_score=0.8,
            skill_match_score=0.8,
            availability_score=0.8,
            workload_score=0.7,
            role_match_score=1.0
        )
        assert match1.is_available()
        
        # Not available (10 hours free, task needs 15)
        large_task = TaskRequirement("task-2", {}, 15.0)
        match2 = MatchResult(
            member=member,
            task_requirement=large_task,
            match_score=0.5,
            skill_match_score=0.8,
            availability_score=0.5,
            workload_score=0.7,
            role_match_score=1.0
        )
        assert not match2.is_available()
    
    def test_is_good_match(self):
        """Test good match evaluation."""
        member = TeamMember.create("user-1", "team-1", "Alice", MemberRole.DEVELOPER)
        member.capacity_hours = 40
        member.current_workload_hours = 20.0
        
        task = TaskRequirement("task-1", {}, 8.0)
        
        # Good match (score >= 0.6, qualified, available)
        good_match = MatchResult(
            member=member,
            task_requirement=task,
            match_score=0.8,
            skill_match_score=0.9,
            availability_score=0.8,
            workload_score=0.7,
            role_match_score=1.0,
            missing_skills=[]
        )
        assert good_match.is_good_match()
        
        # Poor match (low score)
        poor_match = MatchResult(
            member=member,
            task_requirement=task,
            match_score=0.3,
            skill_match_score=0.4,
            availability_score=0.8,
            workload_score=0.7,
            role_match_score=1.0,
            missing_skills=[]
        )
        assert not poor_match.is_good_match()


class TestMatchingStrategy:
    """Test suite for MatchingStrategy."""
    
    def test_strategy_defaults(self):
        """Test default strategy weights."""
        strategy = MatchingStrategy()
        
        assert strategy.skill_weight == 0.4
        assert strategy.availability_weight == 0.25
        assert strategy.workload_weight == 0.25
        assert strategy.role_weight == 0.1
        assert strategy.require_all_skills is True
    
    def test_strategy_validation(self):
        """Test strategy weight validation."""
        with pytest.raises(ValueError, match="must sum to 1.0"):
            MatchingStrategy(
                skill_weight=0.5,
                availability_weight=0.3,
                workload_weight=0.3,
                role_weight=0.1
            )


class TestSkillsMatcher:
    """Test suite for Skills Matcher."""
    
    def test_matcher_initialization(self):
        """Test matcher initialization."""
        matcher = SkillsMatcher()
        assert matcher.strategy is not None
        assert matcher.strategy.skill_weight == 0.4
    
    def test_match_task_basic(self, skilled_team, python_task):
        """Test basic task matching."""
        matcher = SkillsMatcher()
        matches = matcher.match_task(python_task, skilled_team)
        
        # Should return matches for qualified members
        assert len(matches) > 0
        assert all(isinstance(m, MatchResult) for m in matches)
        
        # Matches should be sorted by score
        for i in range(len(matches) - 1):
            assert matches[i].match_score >= matches[i+1].match_score
    
    def test_match_task_skill_scoring(self, skilled_team):
        """Test skill-based scoring."""
        matcher = SkillsMatcher()
        
        # Task requiring Python expertise
        expert_task = TaskRequirement(
            task_id="expert-task",
            required_skills={"Python": ProficiencyLevel.EXPERT},
            estimated_hours=8.0
        )
        
        matches = matcher.match_task(expert_task, skilled_team)
        
        # Alice (EXPERT Python) should be top match
        assert matches[0].member.name == "Alice"
        assert matches[0].skill_match_score > 0.8
    
    def test_match_task_availability_consideration(self, skilled_team):
        """Test that availability affects matching."""
        matcher = SkillsMatcher()
        
        task = TaskRequirement(
            task_id="task-1",
            required_skills={"Python": ProficiencyLevel.INTERMEDIATE},
            estimated_hours=8.0
        )
        
        matches = matcher.match_task(task, skilled_team)
        
        # Charlie (almost full workload) should have lower availability score
        charlie_match = next(m for m in matches if m.member.name == "Charlie")
        bob_match = next(m for m in matches if m.member.name == "Bob")
        
        assert charlie_match.availability_score < bob_match.availability_score
    
    def test_match_task_missing_skills(self, skilled_team):
        """Test detection of missing skills."""
        matcher = SkillsMatcher()
        
        # Task requiring a skill no one has
        task = TaskRequirement(
            task_id="task-1",
            required_skills={
                "Rust": ProficiencyLevel.INTERMEDIATE,
                "Python": ProficiencyLevel.INTERMEDIATE
            },
            estimated_hours=8.0
        )
        
        matches = matcher.match_task(task, skilled_team, include_unqualified=True)
        
        # All matches should have missing skills
        assert all(len(m.missing_skills) > 0 for m in matches)
        assert all("Rust" in m.missing_skills for m in matches)
    
    def test_match_task_exclude_unqualified(self, skilled_team):
        """Test excluding unqualified members."""
        matcher = SkillsMatcher()
        
        # Task requiring skills not everyone has
        task = TaskRequirement(
            task_id="task-1",
            required_skills={
                "SQL": ProficiencyLevel.PROFICIENT,
                "Redis": ProficiencyLevel.INTERMEDIATE
            },
            estimated_hours=8.0
        )
        
        # Without unqualified
        matches = matcher.match_task(task, skilled_team, include_unqualified=False)
        
        # Should only return Charlie (has both skills)
        assert len(matches) == 1
        assert matches[0].member.name == "Charlie"
    
    def test_find_best_member(self, skilled_team, python_task):
        """Test finding best member for a task."""
        matcher = SkillsMatcher()
        best_match = matcher.find_best_member(python_task, skilled_team)
        
        assert best_match is not None
        assert best_match.is_qualified()
        assert best_match.is_available()
    
    def test_find_best_member_no_qualified(self, skilled_team):
        """Test finding best member when none qualified."""
        matcher = SkillsMatcher()
        
        # Task with impossible requirements
        task = TaskRequirement(
            task_id="task-1",
            required_skills={"Haskell": ProficiencyLevel.EXPERT},
            estimated_hours=8.0
        )
        
        best_match = matcher.find_best_member(task, skilled_team)
        
        assert best_match is None
    
    def test_identify_skill_gaps(self, skilled_team):
        """Test skill gap identification."""
        matcher = SkillsMatcher()
        
        task = TaskRequirement(
            task_id="task-1",
            required_skills={
                "Rust": ProficiencyLevel.INTERMEDIATE,  # No one has
                "SQL": ProficiencyLevel.EXPERT,  # Only Charlie has at EXPERT
                "Python": ProficiencyLevel.INTERMEDIATE  # Multiple people have
            },
            estimated_hours=8.0
        )
        
        gaps = matcher.identify_skill_gaps(task, skilled_team)
        
        assert "Rust" in gaps['missing_skills']
        assert "Python" not in gaps['missing_skills']
    
    def test_match_multiple_tasks(self, skilled_team):
        """Test matching multiple tasks."""
        matcher = SkillsMatcher()
        
        tasks = [
            TaskRequirement("task-1", {"Python": ProficiencyLevel.INTERMEDIATE}, 8.0, priority=3),
            TaskRequirement("task-2", {"SQL": ProficiencyLevel.PROFICIENT}, 6.0, priority=2),
            TaskRequirement("task-3", {"JavaScript": ProficiencyLevel.INTERMEDIATE}, 4.0, priority=1)
        ]
        
        results = matcher.match_multiple_tasks(tasks, skilled_team)
        
        assert len(results) == 3
        assert all(task.task_id in results for task in tasks)
        assert all(isinstance(results[task.task_id], list) for task in tasks)
    
    def test_recommended_assignments_priority(self, skilled_team):
        """Test that high-priority tasks are assigned first."""
        matcher = SkillsMatcher()
        
        tasks = [
            TaskRequirement("low-priority", {"Python": ProficiencyLevel.INTERMEDIATE}, 8.0, priority=1),
            TaskRequirement("high-priority", {"Python": ProficiencyLevel.INTERMEDIATE}, 8.0, priority=5),
            TaskRequirement("medium-priority", {"Python": ProficiencyLevel.INTERMEDIATE}, 8.0, priority=3)
        ]
        
        assignments = matcher.get_recommended_assignments(tasks, skilled_team)
        
        # High priority should be assigned first
        if len(assignments) > 0:
            assert assignments[0][0].task_id == "high-priority"
    
    def test_recommended_assignments_balanced(self, skilled_team):
        """Test balanced workload distribution."""
        matcher = SkillsMatcher()
        
        # Many similar tasks
        tasks = [
            TaskRequirement(f"task-{i}", {"Python": ProficiencyLevel.INTERMEDIATE}, 5.0, priority=3)
            for i in range(6)
        ]
        
        assignments = matcher.get_recommended_assignments(tasks, skilled_team, balanced=True)
        
        # Should distribute across multiple members
        assigned_members = {match.member.id for task, match in assignments}
        assert len(assigned_members) > 1
    
    def test_recommended_assignments_capacity_limit(self, skilled_team):
        """Test that assignments respect capacity limits."""
        matcher = SkillsMatcher()
        
        # More work than team can handle
        tasks = [
            TaskRequirement(f"task-{i}", {"Python": ProficiencyLevel.INTERMEDIATE}, 20.0)
            for i in range(10)
        ]
        
        assignments = matcher.get_recommended_assignments(tasks, skilled_team)
        
        # Should not assign more than capacity allows
        for task, match in assignments:
            assert match.is_available()
    
    def test_role_matching(self, skilled_team):
        """Test role-based matching."""
        matcher = SkillsMatcher()
        
        # Task preferring senior developer
        task = TaskRequirement(
            task_id="task-1",
            required_skills={"Python": ProficiencyLevel.INTERMEDIATE},
            estimated_hours=8.0,
            preferred_role="senior_developer"
        )
        
        matches = matcher.match_task(task, skilled_team)
        
        # Alice (senior developer) should have perfect role match
        alice_match = next(m for m in matches if m.member.name == "Alice")
        assert alice_match.role_match_score == 1.0
    
    def test_proficiency_buffer(self):
        """Test allowing proficiency buffer."""
        strategy = MatchingStrategy(
            skill_weight=1.0,
            availability_weight=0.0,
            workload_weight=0.0,
            role_weight=0.0,
            min_proficiency_buffer=1  # Allow 1 level below
        )
        
        matcher = SkillsMatcher(strategy)
        
        # Member with INTERMEDIATE Python
        member = TeamMember.create("user-1", "team-1", "Bob", MemberRole.DEVELOPER)
        member.add_skill(Skill("Python", ProficiencyLevel.INTERMEDIATE, 2.0, date.today()))
        
        # Task requiring PROFICIENT (one level above)
        task = TaskRequirement(
            task_id="task-1",
            required_skills={"Python": ProficiencyLevel.PROFICIENT},
            estimated_hours=8.0
        )
        
        matches = matcher.match_task(task, [member])
        
        # Should match with buffer
        assert len(matches) > 0
        assert matches[0].is_qualified()
    
    def test_inactive_members_excluded(self, skilled_team):
        """Test that inactive members are excluded."""
        matcher = SkillsMatcher()
        
        # Mark one member as inactive
        skilled_team[0].is_active = False
        
        task = TaskRequirement(
            task_id="task-1",
            required_skills={"Python": ProficiencyLevel.INTERMEDIATE},
            estimated_hours=8.0
        )
        
        matches = matcher.match_task(task, skilled_team)
        
        # Should not include inactive member
        assert all(m.member.is_active for m in matches)
        assert skilled_team[0].name not in [m.member.name for m in matches]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

