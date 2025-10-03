"""
Resource Allocation Engine
=========================

Intelligent allocation of multiple tasks to team members with
constraint satisfaction, optimization, and multiple strategies.
"""

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .skills_matcher import SkillsMatcher, TaskRequirement, MatchResult
from ..models.team_capacity import TeamMember, TaskAssignment


class AllocationStrategy(Enum):
    """Available allocation strategies."""
    GREEDY = "greedy"  # Best match first, fastest
    BALANCED = "balanced"  # Even workload distribution
    SKILLS_FOCUSED = "skills_focused"  # Maximize skill utilization
    PRIORITY_FIRST = "priority_first"  # Strict priority ordering


@dataclass
class AllocationResult:
    """Result of resource allocation."""
    allocated: List[Tuple[TaskRequirement, MatchResult]]  # Successfully allocated
    unallocated: List[TaskRequirement]  # Could not allocate
    assignments: List[TaskAssignment]  # Created task assignments
    strategy_used: AllocationStrategy
    success_rate: float  # Percentage of tasks allocated
    avg_confidence: float  # Average match confidence
    workload_distribution: Dict[str, float]  # member_id -> total hours
    warnings: List[str] = field(default_factory=list)
    
    def is_fully_allocated(self) -> bool:
        """Check if all tasks were allocated."""
        return len(self.unallocated) == 0
    
    def is_balanced(self, threshold: float = 0.2) -> bool:
        """Check if workload is reasonably balanced."""
        if not self.workload_distribution:
            return True
        
        workloads = list(self.workload_distribution.values())
        if not workloads:
            return True
        
        avg_workload = sum(workloads) / len(workloads)
        if avg_workload == 0:
            return True
        
        # Check if all workloads are within threshold of average
        for workload in workloads:
            deviation = abs(workload - avg_workload) / avg_workload
            if deviation > threshold:
                return False
        
        return True


class ResourceAllocator:
    """
    Intelligent resource allocation engine.
    
    Allocates multiple tasks to team members using various strategies,
    considering skills, capacity, workload balance, and priorities.
    """
    
    def __init__(self, skills_matcher: Optional[SkillsMatcher] = None):
        """
        Initialize resource allocator.
        
        Args:
            skills_matcher: Skills matcher instance (creates default if None)
        """
        self.skills_matcher = skills_matcher or SkillsMatcher()
    
    def allocate(
        self,
        tasks: List[TaskRequirement],
        team: List[TeamMember],
        strategy: AllocationStrategy = AllocationStrategy.GREEDY
    ) -> AllocationResult:
        """
        Allocate tasks to team members.
        
        Args:
            tasks: List of tasks to allocate
            team: List of team members
            strategy: Allocation strategy to use
            
        Returns:
            AllocationResult with allocated and unallocated tasks
        """
        if strategy == AllocationStrategy.GREEDY:
            return self._allocate_greedy(tasks, team)
        elif strategy == AllocationStrategy.BALANCED:
            return self._allocate_balanced(tasks, team)
        elif strategy == AllocationStrategy.SKILLS_FOCUSED:
            return self._allocate_skills_focused(tasks, team)
        elif strategy == AllocationStrategy.PRIORITY_FIRST:
            return self._allocate_priority_first(tasks, team)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def allocate_with_constraints(
        self,
        tasks: List[TaskRequirement],
        team: List[TeamMember],
        max_hours_per_member: Optional[float] = None,
        required_min_confidence: float = 0.6,
        allow_overallocation: bool = False
    ) -> AllocationResult:
        """
        Allocate tasks with additional constraints.
        
        Args:
            tasks: List of tasks to allocate
            team: List of team members
            max_hours_per_member: Maximum hours any member can take
            required_min_confidence: Minimum match confidence required
            allow_overallocation: Allow allocating beyond capacity
            
        Returns:
            AllocationResult with constraint-aware allocation
        """
        allocated = []
        unallocated = []
        assignments = []
        warnings = []
        workload_tracker = {m.id: m.current_workload_hours for m in team}
        
        # Sort by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        for task in sorted_tasks:
            # Find matches
            matches = self.skills_matcher.match_task(task, team)
            
            allocated_this_task = False
            
            for match in matches:
                # Check minimum confidence
                if match.match_score < required_min_confidence:
                    continue
                
                # Check if member is qualified
                if not match.is_qualified():
                    continue
                
                # Calculate would-be workload
                new_workload = workload_tracker[match.member.id] + task.estimated_hours
                
                # Check max hours constraint
                if max_hours_per_member and new_workload > max_hours_per_member:
                    continue
                
                # Check capacity unless overallocation allowed
                if not allow_overallocation:
                    available = (
                        match.member.capacity_hours * match.member.availability -
                        workload_tracker[match.member.id]
                    )
                    if available < task.estimated_hours:
                        continue
                
                # Allocate!
                assignment = TaskAssignment.create(
                    task_id=task.task_id,
                    member_id=match.member.id,
                    estimated_hours=task.estimated_hours,
                    confidence_score=match.match_score
                )
                
                allocated.append((task, match))
                assignments.append(assignment)
                workload_tracker[match.member.id] = new_workload
                allocated_this_task = True
                
                # Check for overload warning
                utilization = new_workload / match.member.capacity_hours
                if utilization > 0.9:
                    warnings.append(
                        f"{match.member.name} approaching full capacity ({utilization:.0%})"
                    )
                
                break
            
            if not allocated_this_task:
                unallocated.append(task)
        
        # Calculate metrics
        success_rate = len(allocated) / len(tasks) if tasks else 1.0
        avg_confidence = (
            sum(match.match_score for _, match in allocated) / len(allocated)
            if allocated else 0.0
        )
        
        workload_distribution = {
            member.id: workload_tracker[member.id]
            for member in team
            if workload_tracker[member.id] > 0
        }
        
        return AllocationResult(
            allocated=allocated,
            unallocated=unallocated,
            assignments=assignments,
            strategy_used=AllocationStrategy.GREEDY,  # Using greedy with constraints
            success_rate=success_rate,
            avg_confidence=avg_confidence,
            workload_distribution=workload_distribution,
            warnings=warnings
        )
    
    def optimize_allocation(
        self,
        tasks: List[TaskRequirement],
        team: List[TeamMember],
        max_iterations: int = 100
    ) -> AllocationResult:
        """
        Try multiple strategies and return best result.
        
        Args:
            tasks: List of tasks to allocate
            team: List of team members
            max_iterations: Maximum optimization iterations
            
        Returns:
            Best allocation result found
        """
        strategies = [
            AllocationStrategy.GREEDY,
            AllocationStrategy.BALANCED,
            AllocationStrategy.SKILLS_FOCUSED,
            AllocationStrategy.PRIORITY_FIRST
        ]
        
        best_result = None
        best_score = -1
        
        for strategy in strategies:
            result = self.allocate(tasks, team, strategy)
            
            # Score = success_rate * 0.6 + avg_confidence * 0.3 + balance_score * 0.1
            balance_score = 1.0 if result.is_balanced() else 0.5
            score = (
                result.success_rate * 0.6 +
                result.avg_confidence * 0.3 +
                balance_score * 0.1
            )
            
            if score > best_score:
                best_score = score
                best_result = result
        
        return best_result
    
    def _allocate_greedy(
        self,
        tasks: List[TaskRequirement],
        team: List[TeamMember]
    ) -> AllocationResult:
        """Greedy allocation: best match first, fastest strategy."""
        allocated = []
        unallocated = []
        assignments = []
        workload_tracker = {m.id: m.current_workload_hours for m in team}
        
        # Sort by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        for task in sorted_tasks:
            matches = self.skills_matcher.match_task(task, team)
            
            allocated_this_task = False
            
            for match in matches:
                if not match.is_qualified():
                    continue
                
                # Check simulated capacity
                available = (
                    match.member.capacity_hours * match.member.availability -
                    workload_tracker[match.member.id]
                )
                
                if available >= task.estimated_hours:
                    # Allocate
                    assignment = TaskAssignment.create(
                        task_id=task.task_id,
                        member_id=match.member.id,
                        estimated_hours=task.estimated_hours,
                        confidence_score=match.match_score
                    )
                    
                    allocated.append((task, match))
                    assignments.append(assignment)
                    workload_tracker[match.member.id] += task.estimated_hours
                    allocated_this_task = True
                    break
            
            if not allocated_this_task:
                unallocated.append(task)
        
        return self._create_result(
            allocated, unallocated, assignments,
            AllocationStrategy.GREEDY, workload_tracker, team
        )
    
    def _allocate_balanced(
        self,
        tasks: List[TaskRequirement],
        team: List[TeamMember]
    ) -> AllocationResult:
        """Balanced allocation: distribute workload evenly."""
        allocated = []
        unallocated = []
        assignments = []
        workload_tracker = {m.id: m.current_workload_hours for m in team}
        
        # Sort by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        for task in sorted_tasks:
            matches = self.skills_matcher.match_task(task, team)
            
            # Filter to qualified matches with capacity
            viable_matches = [
                match for match in matches
                if match.is_qualified() and
                (match.member.capacity_hours * match.member.availability -
                 workload_tracker[match.member.id]) >= task.estimated_hours
            ]
            
            if not viable_matches:
                unallocated.append(task)
                continue
            
            # Sort by current workload (lowest first for balance)
            viable_matches.sort(
                key=lambda m: (
                    workload_tracker[m.member.id],  # Lower workload first
                    -m.match_score  # Then by match score
                )
            )
            
            # Allocate to least loaded member
            match = viable_matches[0]
            assignment = TaskAssignment.create(
                task_id=task.task_id,
                member_id=match.member.id,
                estimated_hours=task.estimated_hours,
                confidence_score=match.match_score
            )
            
            allocated.append((task, match))
            assignments.append(assignment)
            workload_tracker[match.member.id] += task.estimated_hours
        
        return self._create_result(
            allocated, unallocated, assignments,
            AllocationStrategy.BALANCED, workload_tracker, team
        )
    
    def _allocate_skills_focused(
        self,
        tasks: List[TaskRequirement],
        team: List[TeamMember]
    ) -> AllocationResult:
        """Skills-focused allocation: maximize skill utilization and learning."""
        allocated = []
        unallocated = []
        assignments = []
        workload_tracker = {m.id: m.current_workload_hours for m in team}
        
        # Sort by priority
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        for task in sorted_tasks:
            matches = self.skills_matcher.match_task(task, team)
            
            # Filter to qualified matches with capacity
            viable_matches = [
                match for match in matches
                if match.is_qualified() and
                (match.member.capacity_hours * match.member.availability -
                 workload_tracker[match.member.id]) >= task.estimated_hours
            ]
            
            if not viable_matches:
                unallocated.append(task)
                continue
            
            # Sort by skill match score (highest first)
            viable_matches.sort(key=lambda m: m.skill_match_score, reverse=True)
            
            # Allocate to best skill match
            match = viable_matches[0]
            assignment = TaskAssignment.create(
                task_id=task.task_id,
                member_id=match.member.id,
                estimated_hours=task.estimated_hours,
                confidence_score=match.match_score
            )
            
            allocated.append((task, match))
            assignments.append(assignment)
            workload_tracker[match.member.id] += task.estimated_hours
        
        return self._create_result(
            allocated, unallocated, assignments,
            AllocationStrategy.SKILLS_FOCUSED, workload_tracker, team
        )
    
    def _allocate_priority_first(
        self,
        tasks: List[TaskRequirement],
        team: List[TeamMember]
    ) -> AllocationResult:
        """Priority-first allocation: strictly honor task priorities."""
        allocated = []
        unallocated = []
        assignments = []
        workload_tracker = {m.id: m.current_workload_hours for m in team}
        
        # Strictly sort by priority (no other consideration)
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (t.priority, -t.estimated_hours),
            reverse=True
        )
        
        for task in sorted_tasks:
            matches = self.skills_matcher.match_task(task, team)
            
            allocated_this_task = False
            
            for match in matches:
                if not match.is_qualified():
                    continue
                
                # Check capacity
                available = (
                    match.member.capacity_hours * match.member.availability -
                    workload_tracker[match.member.id]
                )
                
                if available >= task.estimated_hours:
                    assignment = TaskAssignment.create(
                        task_id=task.task_id,
                        member_id=match.member.id,
                        estimated_hours=task.estimated_hours,
                        confidence_score=match.match_score
                    )
                    
                    allocated.append((task, match))
                    assignments.append(assignment)
                    workload_tracker[match.member.id] += task.estimated_hours
                    allocated_this_task = True
                    break
            
            if not allocated_this_task:
                unallocated.append(task)
        
        return self._create_result(
            allocated, unallocated, assignments,
            AllocationStrategy.PRIORITY_FIRST, workload_tracker, team
        )
    
    def _create_result(
        self,
        allocated: List[Tuple[TaskRequirement, MatchResult]],
        unallocated: List[TaskRequirement],
        assignments: List[TaskAssignment],
        strategy: AllocationStrategy,
        workload_tracker: Dict[str, float],
        team: List[TeamMember]
    ) -> AllocationResult:
        """Create allocation result with calculated metrics."""
        total_tasks = len(allocated) + len(unallocated)
        success_rate = len(allocated) / total_tasks if total_tasks > 0 else 1.0
        
        avg_confidence = (
            sum(match.match_score for _, match in allocated) / len(allocated)
            if allocated else 0.0
        )
        
        workload_distribution = {
            member.id: workload_tracker[member.id]
            for member in team
            if workload_tracker[member.id] > 0
        }
        
        # Generate warnings
        warnings = []
        for member in team:
            workload = workload_tracker[member.id]
            utilization = workload / member.capacity_hours
            
            if utilization > 1.0:
                warnings.append(f"{member.name} overallocated ({utilization:.0%})")
            elif utilization > 0.9:
                warnings.append(f"{member.name} near capacity ({utilization:.0%})")
        
        return AllocationResult(
            allocated=allocated,
            unallocated=unallocated,
            assignments=assignments,
            strategy_used=strategy,
            success_rate=success_rate,
            avg_confidence=avg_confidence,
            workload_distribution=workload_distribution,
            warnings=warnings
        )

