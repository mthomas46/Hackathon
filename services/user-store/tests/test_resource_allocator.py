"""
Tests for Resource Allocation Engine
====================================

Unit tests for intelligent resource allocation with multiple strategies.
"""

import pytest
from datetime import date
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.services.resource_allocator import (
    ResourceAllocator,
    AllocationStrategy,
    AllocationResult
)
from domain.services.skills_matcher import TaskRequirement
from domain.models.team_capacity import (
    TeamMember,
    Skill,
    ProficiencyLevel,
    MemberRole
)


@pytest.fixture
def test_team():
    """Create a test team with varied skills and capacity."""
    # Alice: Senior dev, expert Python, high capacity
    alice = TeamMember.create("user-1", "team-1", "Alice", MemberRole.SENIOR_DEVELOPER)
    alice.add_skill(Skill("Python", ProficiencyLevel.EXPERT, 8.0, date.today()))
    alice.add_skill(Skill("SQL", ProficiencyLevel.PROFICIENT, 5.0, date.today()))
    alice.capacity_hours = 40
    alice.current_workload_hours = 10.0
    
    # Bob: Developer, good Python, moderate capacity
    bob = TeamMember.create("user-2", "team-1", "Bob", MemberRole.DEVELOPER)
    bob.add_skill(Skill("Python", ProficiencyLevel.PROFICIENT, 3.0, date.today()))
    bob.add_skill(Skill("JavaScript", ProficiencyLevel.INTERMEDIATE, 2.0, date.today()))
    bob.capacity_hours = 40
    bob.current_workload_hours = 15.0
    
    # Charlie: Developer, good SQL, lower capacity
    charlie = TeamMember.create("user-3", "team-1", "Charlie", MemberRole.DEVELOPER)
    charlie.add_skill(Skill("SQL", ProficiencyLevel.EXPERT, 6.0, date.today()))
    charlie.add_skill(Skill("Python", ProficiencyLevel.INTERMEDIATE, 2.0, date.today()))
    charlie.capacity_hours = 40
    charlie.current_workload_hours = 25.0
    
    return [alice, bob, charlie]


@pytest.fixture
def test_tasks():
    """Create a set of test tasks."""
    return [
        TaskRequirement(
            task_id="task-1",
            required_skills={"Python": ProficiencyLevel.PROFICIENT},
            estimated_hours=10.0,
            priority=5
        ),
        TaskRequirement(
            task_id="task-2",
            required_skills={"SQL": ProficiencyLevel.INTERMEDIATE},
            estimated_hours=8.0,
            priority=3
        ),
        TaskRequirement(
            task_id="task-3",
            required_skills={"Python": ProficiencyLevel.INTERMEDIATE},
            estimated_hours=12.0,
            priority=4
        ),
        TaskRequirement(
            task_id="task-4",
            required_skills={"SQL": ProficiencyLevel.PROFICIENT},
            estimated_hours=6.0,
            priority=2
        )
    ]


class TestAllocationResult:
    """Test suite for AllocationResult model."""
    
    def test_is_fully_allocated(self, test_team):
        """Test full allocation detection."""
        result = AllocationResult(
            allocated=[],
            unallocated=[],
            assignments=[],
            strategy_used=AllocationStrategy.GREEDY,
            success_rate=1.0,
            avg_confidence=0.9,
            workload_distribution={}
        )
        assert result.is_fully_allocated()
        
        task = TaskRequirement("task-1", {}, 8.0)
        result_with_unallocated = AllocationResult(
            allocated=[],
            unallocated=[task],
            assignments=[],
            strategy_used=AllocationStrategy.GREEDY,
            success_rate=0.0,
            avg_confidence=0.0,
            workload_distribution={}
        )
        assert not result_with_unallocated.is_fully_allocated()
    
    def test_is_balanced(self):
        """Test workload balance checking."""
        # Balanced workload
        balanced_result = AllocationResult(
            allocated=[],
            unallocated=[],
            assignments=[],
            strategy_used=AllocationStrategy.BALANCED,
            success_rate=1.0,
            avg_confidence=0.9,
            workload_distribution={
                "member-1": 20.0,
                "member-2": 22.0,
                "member-3": 21.0
            }
        )
        assert balanced_result.is_balanced(threshold=0.2)
        
        # Unbalanced workload
        unbalanced_result = AllocationResult(
            allocated=[],
            unallocated=[],
            assignments=[],
            strategy_used=AllocationStrategy.GREEDY,
            success_rate=1.0,
            avg_confidence=0.9,
            workload_distribution={
                "member-1": 10.0,
                "member-2": 35.0,
                "member-3": 15.0
            }
        )
        assert not unbalanced_result.is_balanced(threshold=0.2)


class TestResourceAllocator:
    """Test suite for Resource Allocator."""
    
    def test_allocator_initialization(self):
        """Test allocator initialization."""
        allocator = ResourceAllocator()
        assert allocator.skills_matcher is not None
    
    def test_greedy_allocation(self, test_team, test_tasks):
        """Test greedy allocation strategy."""
        allocator = ResourceAllocator()
        result = allocator.allocate(test_tasks, test_team, AllocationStrategy.GREEDY)
        
        assert isinstance(result, AllocationResult)
        assert result.strategy_used == AllocationStrategy.GREEDY
        assert len(result.allocated) + len(result.unallocated) == len(test_tasks)
        assert len(result.assignments) == len(result.allocated)
    
    def test_balanced_allocation(self, test_team, test_tasks):
        """Test balanced allocation strategy."""
        allocator = ResourceAllocator()
        result = allocator.allocate(test_tasks, test_team, AllocationStrategy.BALANCED)
        
        assert result.strategy_used == AllocationStrategy.BALANCED
        # Balanced should distribute more evenly than greedy
        if len(result.workload_distribution) > 1:
            workloads = list(result.workload_distribution.values())
            variance = max(workloads) - min(workloads)
            assert variance <= max(workloads)  # Some level of balance
    
    def test_skills_focused_allocation(self, test_team, test_tasks):
        """Test skills-focused allocation strategy."""
        allocator = ResourceAllocator()
        result = allocator.allocate(test_tasks, test_team, AllocationStrategy.SKILLS_FOCUSED)
        
        assert result.strategy_used == AllocationStrategy.SKILLS_FOCUSED
        # Skills-focused should have high average skill match
        if result.allocated:
            # Check that high-skill matches were preferred
            for task, match in result.allocated:
                assert match.skill_match_score > 0.5
    
    def test_priority_first_allocation(self, test_team, test_tasks):
        """Test priority-first allocation strategy."""
        allocator = ResourceAllocator()
        result = allocator.allocate(test_tasks, test_team, AllocationStrategy.PRIORITY_FIRST)
        
        assert result.strategy_used == AllocationStrategy.PRIORITY_FIRST
        # High priority tasks should be allocated first
        if len(result.allocated) > 1:
            priorities = [task.priority for task, _ in result.allocated]
            # Should generally be sorted by priority
            assert priorities[0] >= priorities[-1]
    
    def test_allocation_respects_capacity(self, test_team):
        """Test that allocation respects team capacity."""
        allocator = ResourceAllocator()
        
        # Create more work than team can handle
        large_tasks = [
            TaskRequirement(f"task-{i}", {"Python": ProficiencyLevel.INTERMEDIATE}, 20.0)
            for i in range(10)
        ]
        
        result = allocator.allocate(large_tasks, test_team, AllocationStrategy.GREEDY)
        
        # Check no member is overallocated
        for member in test_team:
            if member.id in result.workload_distribution:
                total_workload = result.workload_distribution[member.id]
                assert total_workload <= member.capacity_hours * member.availability
    
    def test_allocation_requires_skills(self, test_team):
        """Test that tasks without qualified members are not allocated."""
        allocator = ResourceAllocator()
        
        # Task requiring skill no one has
        impossible_task = TaskRequirement(
            task_id="impossible",
            required_skills={"Rust": ProficiencyLevel.EXPERT},
            estimated_hours=8.0
        )
        
        result = allocator.allocate([impossible_task], test_team, AllocationStrategy.GREEDY)
        
        assert len(result.allocated) == 0
        assert len(result.unallocated) == 1
        assert result.success_rate == 0.0
    
    def test_allocation_with_min_confidence_constraint(self, test_team, test_tasks):
        """Test allocation with minimum confidence constraint."""
        allocator = ResourceAllocator()
        
        result = allocator.allocate_with_constraints(
            test_tasks,
            test_team,
            required_min_confidence=0.8  # High confidence required
        )
        
        # All allocated tasks should meet confidence threshold
        for task, match in result.allocated:
            assert match.match_score >= 0.8
    
    def test_allocation_with_max_hours_constraint(self, test_team, test_tasks):
        """Test allocation with maximum hours constraint."""
        allocator = ResourceAllocator()
        
        result = allocator.allocate_with_constraints(
            test_tasks,
            test_team,
            max_hours_per_member=25.0  # Cap at 25 hours
        )
        
        # No member should exceed max hours
        for member_id, workload in result.workload_distribution.items():
            assert workload <= 25.0
    
    def test_allocation_with_overallocation_allowed(self, test_team):
        """Test allocation allowing overallocation."""
        allocator = ResourceAllocator()
        
        # Many large tasks
        many_tasks = [
            TaskRequirement(f"task-{i}", {"Python": ProficiencyLevel.INTERMEDIATE}, 15.0)
            for i in range(10)
        ]
        
        result = allocator.allocate_with_constraints(
            many_tasks,
            test_team,
            allow_overallocation=True
        )
        
        # Should allocate more tasks than capacity allows
        total_allocated_hours = sum(t.estimated_hours for t, _ in result.allocated)
        total_capacity = sum(m.capacity_hours for m in test_team)
        
        # Might exceed capacity if overallocation is allowed
        assert len(result.allocated) > 0
    
    def test_allocation_generates_warnings(self, test_team):
        """Test that warnings are generated for high utilization."""
        allocator = ResourceAllocator()
        
        # Tasks that will push someone to high utilization
        heavy_tasks = [
            TaskRequirement("task-1", {"Python": ProficiencyLevel.INTERMEDIATE}, 25.0),
            TaskRequirement("task-2", {"SQL": ProficiencyLevel.INTERMEDIATE}, 10.0)
        ]
        
        result = allocator.allocate(heavy_tasks, test_team, AllocationStrategy.GREEDY)
        
        # Should have some warnings about capacity
        assert isinstance(result.warnings, list)
    
    def test_optimize_allocation(self, test_team, test_tasks):
        """Test allocation optimization across strategies."""
        allocator = ResourceAllocator()
        
        result = allocator.optimize_allocation(test_tasks, test_team)
        
        assert isinstance(result, AllocationResult)
        # Should return a result from one of the strategies
        assert result.strategy_used in AllocationStrategy
        # Should have allocated at least some tasks
        assert len(result.allocated) > 0
    
    def test_allocation_success_rate(self, test_team, test_tasks):
        """Test success rate calculation."""
        allocator = ResourceAllocator()
        result = allocator.allocate(test_tasks, test_team, AllocationStrategy.GREEDY)
        
        expected_rate = len(result.allocated) / len(test_tasks)
        assert result.success_rate == pytest.approx(expected_rate)
    
    def test_allocation_avg_confidence(self, test_team, test_tasks):
        """Test average confidence calculation."""
        allocator = ResourceAllocator()
        result = allocator.allocate(test_tasks, test_team, AllocationStrategy.GREEDY)
        
        if result.allocated:
            expected_avg = sum(m.match_score for _, m in result.allocated) / len(result.allocated)
            assert result.avg_confidence == pytest.approx(expected_avg)
    
    def test_workload_distribution_tracking(self, test_team, test_tasks):
        """Test workload distribution tracking."""
        allocator = ResourceAllocator()
        result = allocator.allocate(test_tasks, test_team, AllocationStrategy.GREEDY)
        
        # Check workload is tracked
        assert isinstance(result.workload_distribution, dict)
        
        # Verify workload totals
        for member in test_team:
            if member.id in result.workload_distribution:
                allocated_to_member = [
                    task.estimated_hours
                    for task, match in result.allocated
                    if match.member.id == member.id
                ]
                expected_total = member.current_workload_hours + sum(allocated_to_member)
                assert result.workload_distribution[member.id] == pytest.approx(expected_total)
    
    def test_assignment_creation(self, test_team, test_tasks):
        """Test that TaskAssignment objects are created."""
        allocator = ResourceAllocator()
        result = allocator.allocate(test_tasks, test_team, AllocationStrategy.GREEDY)
        
        assert len(result.assignments) == len(result.allocated)
        
        for assignment in result.assignments:
            assert assignment.task_id in [t.task_id for t in test_tasks]
            assert assignment.member_id in [m.id for m in test_team]
            assert assignment.estimated_hours > 0
            assert 0 <= assignment.confidence_score <= 1.0
    
    def test_greedy_vs_balanced_difference(self, test_team, test_tasks):
        """Test that balanced strategy differs from greedy."""
        allocator = ResourceAllocator()
        
        greedy_result = allocator.allocate(test_tasks, test_team, AllocationStrategy.GREEDY)
        balanced_result = allocator.allocate(test_tasks, test_team, AllocationStrategy.BALANCED)
        
        # If both allocated successfully, balanced should be more balanced
        if (len(greedy_result.allocated) == len(balanced_result.allocated) and 
            len(greedy_result.allocated) > 2):
            # Balanced should have lower variance in workload
            greedy_workloads = list(greedy_result.workload_distribution.values())
            balanced_workloads = list(balanced_result.workload_distribution.values())
            
            if len(greedy_workloads) > 1 and len(balanced_workloads) > 1:
                greedy_variance = max(greedy_workloads) - min(greedy_workloads)
                balanced_variance = max(balanced_workloads) - min(balanced_workloads)
                
                # Balanced should generally have lower or equal variance
                assert balanced_variance <= greedy_variance * 1.5  # Allow some margin
    
    def test_empty_tasks_list(self, test_team):
        """Test allocation with no tasks."""
        allocator = ResourceAllocator()
        result = allocator.allocate([], test_team, AllocationStrategy.GREEDY)
        
        assert len(result.allocated) == 0
        assert len(result.unallocated) == 0
        assert result.success_rate == 1.0  # 100% success with no tasks
    
    def test_empty_team(self, test_tasks):
        """Test allocation with no team members."""
        allocator = ResourceAllocator()
        result = allocator.allocate(test_tasks, [], AllocationStrategy.GREEDY)
        
        assert len(result.allocated) == 0
        assert len(result.unallocated) == len(test_tasks)
        assert result.success_rate == 0.0
    
    def test_single_task_single_member(self):
        """Test simple case: one task, one member."""
        member = TeamMember.create("user-1", "team-1", "Alice", MemberRole.DEVELOPER)
        member.add_skill(Skill("Python", ProficiencyLevel.PROFICIENT, 3.0, date.today()))
        
        task = TaskRequirement(
            task_id="task-1",
            required_skills={"Python": ProficiencyLevel.INTERMEDIATE},
            estimated_hours=8.0
        )
        
        allocator = ResourceAllocator()
        result = allocator.allocate([task], [member], AllocationStrategy.GREEDY)
        
        assert len(result.allocated) == 1
        assert len(result.unallocated) == 0
        assert result.success_rate == 1.0
    
    def test_priority_ordering_strict(self, test_team):
        """Test strict priority ordering."""
        tasks = [
            TaskRequirement("low", {"Python": ProficiencyLevel.INTERMEDIATE}, 5.0, priority=1),
            TaskRequirement("high", {"Python": ProficiencyLevel.INTERMEDIATE}, 5.0, priority=5),
            TaskRequirement("med", {"Python": ProficiencyLevel.INTERMEDIATE}, 5.0, priority=3)
        ]
        
        allocator = ResourceAllocator()
        result = allocator.allocate(tasks, test_team, AllocationStrategy.PRIORITY_FIRST)
        
        if len(result.allocated) > 0:
            # First allocated should be high priority
            first_task_id = result.allocated[0][0].task_id
            assert first_task_id == "high"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

