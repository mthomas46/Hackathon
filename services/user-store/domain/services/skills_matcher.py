"""
Skills Matching Engine
=====================

Intelligent matching of tasks to team members based on skills,
proficiency, availability, and current workload.
"""

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
import math

from ..models.team_capacity import TeamMember, ProficiencyLevel


@dataclass
class TaskRequirement:
    """Requirements for a task."""
    task_id: str
    required_skills: Dict[str, ProficiencyLevel]  # skill_name -> min_proficiency
    estimated_hours: float
    priority: int = 1  # 1-5, higher = more important
    preferred_role: Optional[str] = None
    
    def __post_init__(self):
        """Validate task requirements."""
        if self.estimated_hours <= 0:
            raise ValueError("Estimated hours must be positive")
        if not (1 <= self.priority <= 5):
            raise ValueError("Priority must be between 1 and 5")


@dataclass
class MatchResult:
    """Result of matching a task to a team member."""
    member: TeamMember
    task_requirement: TaskRequirement
    match_score: float  # 0-1, higher is better
    skill_match_score: float  # 0-1
    availability_score: float  # 0-1
    workload_score: float  # 0-1
    role_match_score: float  # 0-1
    missing_skills: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    
    def is_qualified(self) -> bool:
        """Check if member is qualified (no missing skills)."""
        return len(self.missing_skills) == 0
    
    def is_available(self) -> bool:
        """Check if member has capacity."""
        return self.member.is_available_for_hours(self.task_requirement.estimated_hours)
    
    def is_good_match(self, threshold: float = 0.6) -> bool:
        """Check if match score exceeds threshold."""
        return self.match_score >= threshold and self.is_qualified() and self.is_available()


@dataclass
class MatchingStrategy:
    """Configuration for matching strategy."""
    skill_weight: float = 0.4
    availability_weight: float = 0.25
    workload_weight: float = 0.25
    role_weight: float = 0.1
    require_all_skills: bool = True
    min_proficiency_buffer: int = 0  # Allow proficiency X levels below required
    
    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = self.skill_weight + self.availability_weight + self.workload_weight + self.role_weight
        if not math.isclose(total, 1.0, rel_tol=1e-5):
            raise ValueError(f"Weights must sum to 1.0, got {total}")


class SkillsMatcher:
    """
    Intelligent skills matching engine.
    
    Matches tasks to team members based on:
    - Required skills and proficiency levels
    - Member availability and current workload
    - Role compatibility
    - Learning opportunities (can assign slightly above current level)
    """
    
    def __init__(self, strategy: Optional[MatchingStrategy] = None):
        """
        Initialize skills matcher.
        
        Args:
            strategy: Matching strategy configuration
        """
        self.strategy = strategy or MatchingStrategy()
    
    def match_task(
        self,
        task: TaskRequirement,
        team: List[TeamMember],
        include_unqualified: bool = False
    ) -> List[MatchResult]:
        """
        Match a task to team members.
        
        Args:
            task: Task requirements
            team: List of team members
            include_unqualified: Include members missing required skills
            
        Returns:
            List of match results sorted by score (best first)
        """
        matches = []
        
        for member in team:
            if not member.is_active:
                continue
            
            match = self._calculate_match(task, member)
            
            # Filter unqualified if requested
            if not include_unqualified and not match.is_qualified():
                continue
            
            matches.append(match)
        
        # Sort by match score (descending)
        matches.sort(key=lambda m: m.match_score, reverse=True)
        
        return matches
    
    def match_multiple_tasks(
        self,
        tasks: List[TaskRequirement],
        team: List[TeamMember]
    ) -> Dict[str, List[MatchResult]]:
        """
        Match multiple tasks to team members.
        
        Args:
            tasks: List of task requirements
            team: List of team members
            
        Returns:
            Dictionary mapping task_id to list of matches
        """
        results = {}
        
        for task in tasks:
            matches = self.match_task(task, team)
            results[task.task_id] = matches
        
        return results
    
    def find_best_member(
        self,
        task: TaskRequirement,
        team: List[TeamMember]
    ) -> Optional[MatchResult]:
        """
        Find the best team member for a task.
        
        Args:
            task: Task requirements
            team: List of team members
            
        Returns:
            Best match result or None if no qualified members
        """
        matches = self.match_task(task, team, include_unqualified=False)
        
        if not matches:
            return None
        
        return matches[0]
    
    def identify_skill_gaps(
        self,
        task: TaskRequirement,
        team: List[TeamMember]
    ) -> Dict[str, List[str]]:
        """
        Identify skill gaps for a task.
        
        Args:
            task: Task requirements
            team: List of team members
            
        Returns:
            Dictionary with:
            - 'missing_skills': Skills no one has
            - 'insufficient_proficiency': Skills present but below required level
        """
        all_member_skills = set()
        proficiency_issues = {}
        
        for member in team:
            if not member.is_active:
                continue
            all_member_skills.update(member.skills.keys())
        
        missing_skills = []
        insufficient_proficiency = []
        
        for skill_name, required_level in task.required_skills.items():
            # Check if any member has this skill
            if skill_name not in all_member_skills:
                missing_skills.append(skill_name)
                continue
            
            # Check if anyone has it at required level
            has_sufficient = False
            for member in team:
                if not member.is_active:
                    continue
                if member.has_skill(skill_name, required_level):
                    has_sufficient = True
                    break
            
            if not has_sufficient:
                insufficient_proficiency.append(skill_name)
        
        return {
            'missing_skills': missing_skills,
            'insufficient_proficiency': insufficient_proficiency
        }
    
    def get_recommended_assignments(
        self,
        tasks: List[TaskRequirement],
        team: List[TeamMember],
        balanced: bool = True
    ) -> List[Tuple[TaskRequirement, MatchResult]]:
        """
        Get recommended task assignments for a team.
        
        Args:
            tasks: List of tasks to assign
            team: List of team members
            balanced: If True, balance workload across team
            
        Returns:
            List of (task, match) tuples representing recommended assignments
        """
        # Sort tasks by priority (high to low)
        sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)
        
        assignments = []
        assigned_members = set()
        
        # Track simulated workload for balancing
        simulated_workload = {member.id: member.current_workload_hours for member in team}
        
        for task in sorted_tasks:
            matches = self.match_task(task, team)
            
            if not matches:
                continue
            
            # If balancing, prefer members with lower simulated workload
            if balanced:
                matches.sort(
                    key=lambda m: (
                        -m.match_score,  # Higher score better (negate for sort)
                        simulated_workload.get(m.member.id, 0)  # Lower workload better
                    )
                )
            
            # Find first qualified and available member
            for match in matches:
                if not match.is_qualified():
                    continue
                
                # Check simulated availability
                available = (
                    match.member.capacity_hours * match.member.availability -
                    simulated_workload.get(match.member.id, 0)
                )
                
                if available >= task.estimated_hours:
                    assignments.append((task, match))
                    simulated_workload[match.member.id] = (
                        simulated_workload.get(match.member.id, 0) + task.estimated_hours
                    )
                    break
        
        return assignments
    
    def _calculate_match(
        self,
        task: TaskRequirement,
        member: TeamMember
    ) -> MatchResult:
        """Calculate match score between task and member."""
        # Calculate individual scores
        skill_score, missing_skills = self._calculate_skill_score(task, member)
        availability_score = self._calculate_availability_score(task, member)
        workload_score = self._calculate_workload_score(member)
        role_score = self._calculate_role_score(task, member)
        
        # Weighted overall score
        match_score = (
            skill_score * self.strategy.skill_weight +
            availability_score * self.strategy.availability_weight +
            workload_score * self.strategy.workload_weight +
            role_score * self.strategy.role_weight
        )
        
        # Generate reasons
        reasons = self._generate_reasons(
            task, member, skill_score, availability_score, workload_score, role_score
        )
        
        return MatchResult(
            member=member,
            task_requirement=task,
            match_score=match_score,
            skill_match_score=skill_score,
            availability_score=availability_score,
            workload_score=workload_score,
            role_match_score=role_score,
            missing_skills=missing_skills,
            reasons=reasons
        )
    
    def _calculate_skill_score(
        self,
        task: TaskRequirement,
        member: TeamMember
    ) -> Tuple[float, List[str]]:
        """Calculate skill match score."""
        if not task.required_skills:
            return 1.0, []
        
        total_score = 0.0
        missing_skills = []
        
        for skill_name, required_level in task.required_skills.items():
            # Check if member has skill
            if skill_name not in member.skills:
                missing_skills.append(skill_name)
                if self.strategy.require_all_skills:
                    continue  # Don't count missing skills
                else:
                    continue  # Skip but don't fail completely
            
            skill = member.skills[skill_name]
            
            # Check proficiency level with buffer
            min_level = max(1, required_level.value - self.strategy.min_proficiency_buffer)
            
            if skill.proficiency_level.value < min_level:
                missing_skills.append(f"{skill_name} (insufficient proficiency)")
                if self.strategy.require_all_skills:
                    continue
            
            # Score based on how much they exceed requirement
            proficiency_ratio = skill.proficiency_level.value / required_level.value
            skill_score = min(proficiency_ratio, 1.2) / 1.2  # Cap at 120% of requirement
            
            # Apply skill proficiency score (considers experience, recency)
            skill_score *= skill.proficiency_score()
            
            total_score += skill_score
        
        # Average across all required skills
        if self.strategy.require_all_skills and missing_skills:
            return 0.0, missing_skills
        
        if task.required_skills:
            avg_score = total_score / len(task.required_skills)
        else:
            avg_score = 1.0
        
        return min(avg_score, 1.0), missing_skills
    
    def _calculate_availability_score(
        self,
        task: TaskRequirement,
        member: TeamMember
    ) -> float:
        """Calculate availability score."""
        available_hours = member.available_capacity_hours()
        
        if available_hours <= 0:
            return 0.0
        
        if available_hours >= task.estimated_hours:
            # Has full capacity
            return 1.0
        else:
            # Partial capacity
            return available_hours / task.estimated_hours
    
    def _calculate_workload_score(self, member: TeamMember) -> float:
        """Calculate workload score (lower workload = higher score)."""
        utilization = member.capacity_utilization()
        
        # Score decreases as utilization increases
        # 0% utilization = 1.0 score
        # 100% utilization = 0.0 score
        return max(0.0, 1.0 - utilization)
    
    def _calculate_role_score(
        self,
        task: TaskRequirement,
        member: TeamMember
    ) -> float:
        """Calculate role match score."""
        if not task.preferred_role:
            return 1.0  # No preference, perfect match
        
        if member.role.value == task.preferred_role:
            return 1.0
        
        # Partial credit for related roles
        role_compatibility = {
            'senior_developer': {'developer': 0.8, 'tech_lead': 0.6},
            'tech_lead': {'senior_developer': 0.8, 'architect': 0.6, 'developer': 0.5},
            'architect': {'tech_lead': 0.7, 'senior_developer': 0.5},
            'developer': {'senior_developer': 0.7, 'qa_engineer': 0.3},
            'qa_engineer': {'developer': 0.5},
            'devops_engineer': {'developer': 0.4},
        }
        
        if member.role.value in role_compatibility:
            return role_compatibility[member.role.value].get(task.preferred_role, 0.2)
        
        return 0.2  # Some minimal score for any active member
    
    def _generate_reasons(
        self,
        task: TaskRequirement,
        member: TeamMember,
        skill_score: float,
        availability_score: float,
        workload_score: float,
        role_score: float
    ) -> List[str]:
        """Generate human-readable reasons for match score."""
        reasons = []
        
        # Skill reasons
        if skill_score >= 0.9:
            reasons.append("Excellent skill match")
        elif skill_score >= 0.7:
            reasons.append("Good skill match")
        elif skill_score >= 0.5:
            reasons.append("Adequate skills")
        elif skill_score > 0:
            reasons.append("Some skills present")
        else:
            reasons.append("Missing required skills")
        
        # Availability reasons
        if availability_score >= 0.9:
            reasons.append("Full capacity available")
        elif availability_score >= 0.5:
            reasons.append("Partial capacity available")
        elif availability_score > 0:
            reasons.append("Limited capacity")
        else:
            reasons.append("No capacity available")
        
        # Workload reasons
        utilization = member.capacity_utilization()
        if utilization <= 0.5:
            reasons.append("Low current workload")
        elif utilization <= 0.8:
            reasons.append("Moderate workload")
        else:
            reasons.append("High workload")
        
        # Role reasons
        if role_score >= 0.9:
            reasons.append("Perfect role match")
        elif role_score >= 0.6:
            reasons.append("Compatible role")
        
        return reasons

