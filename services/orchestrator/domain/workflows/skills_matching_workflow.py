"""
Skills Matching Workflow - Phase 2 Day 4
Part of Enhanced Roadmap v2.0 - Workflow D: Team Skills & Capacity Matching

This workflow matches features to team members based on skills, availability,
and capacity. Provides intelligent resource allocation recommendations.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, date
from dataclasses import dataclass, field

import httpx


@dataclass
class TeamMember:
    """Represents a team member with skills and availability."""
    member_id: str
    name: str
    role: str  # e.g., "Backend Developer", "Frontend Developer", "QA"
    skills: List[str]
    skill_levels: Dict[str, int]  # skill -> level (1-5)
    availability: float  # 0.0 - 1.0 (percentage available)
    current_capacity: float  # Story points currently assigned
    max_capacity: float  # Maximum story points per sprint
    hourly_rate: Optional[float] = None


@dataclass
class SkillGap:
    """Represents a gap between required and available skills."""
    skill_name: str
    required_level: int
    available_level: int
    gap_severity: str  # "minor", "moderate", "critical"
    mitigation: str  # Suggested mitigation


@dataclass
class ResourceAllocation:
    """Represents allocation of a team member to a task/story."""
    member_id: str
    member_name: str
    task_id: str
    task_title: str
    match_score: float  # 0.0 - 1.0
    estimated_hours: float
    confidence: float  # 0.0 - 1.0
    reasons: List[str]  # Why this member was chosen


@dataclass
class SkillsMatchingResult:
    """Complete skills matching result from Workflow D."""
    workflow_id: str
    feature_breakdown: Dict[str, Any]  # From Workflow A
    team_members: List[TeamMember]
    resource_allocations: List[ResourceAllocation]
    skill_gaps: List[SkillGap]
    team_capacity_utilization: float  # 0.0 - 1.0
    recommendations: List[str]
    training_needs: List[str]
    hiring_recommendations: List[str]
    overall_readiness: float  # 0.0 - 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)


class SkillsMatchingWorkflow:
    """
    Workflow D: Team Skills & Capacity Matching
    
    Matches features to team members based on:
    - Required skills vs available skills
    - Skill proficiency levels
    - Team member availability
    - Current capacity utilization
    
    Provides:
    - Resource allocation recommendations
    - Skill gap analysis
    - Training needs identification
    - Hiring recommendations
    
    Integrates with:
    - User Store (team data)
    - Project Planning (resource allocation)
    
    Part of Enhanced Roadmap v2.0 Phase 2 implementation.
    """
    
    def __init__(
        self,
        user_store_url: str = "http://user-store:5130",
        project_planning_url: str = "http://project-planning-service:8000",
        workflow_logger = None
    ):
        """
        Initialize Workflow D with service URLs.
        
        Args:
            user_store_url: URL for User Store service
            project_planning_url: URL for Project Planning service
            workflow_logger: WorkflowLogger instance for logging
        """
        self.user_store_url = user_store_url
        self.project_planning_url = project_planning_url
        self.workflow_logger = workflow_logger
        self.timeout = 30.0
        
    async def execute(
        self,
        feature_breakdown: Dict[str, Any],
        team_id: str,
        parent_workflow_id: Optional[str] = None
    ) -> SkillsMatchingResult:
        """
        Execute Workflow D: Skills Matching.
        
        Args:
            feature_breakdown: Feature breakdown from Workflow A
            team_id: Team identifier for skills data
            parent_workflow_id: Parent workflow ID for tracing
            
        Returns:
            SkillsMatchingResult with complete skills analysis
        """
        # Generate workflow ID
        workflow_id = f"workflow_d_{str(uuid.uuid4())[:8]}"
        
        # Log workflow start
        if self.workflow_logger:
            await self.workflow_logger.log_workflow_start(
                workflow_id=workflow_id,
                operation="skills_matching_workflow_d",
                context={
                    "feature_breakdown": bool(feature_breakdown),
                    "team_id": team_id,
                    "parent_workflow": parent_workflow_id
                }
            )
        
        try:
            # Step 1: Get team members and their skills
            team_members = await self._get_team_members(
                team_id=team_id,
                workflow_id=workflow_id
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="team_members_retrieved",
                    step_data={
                        "team_id": team_id,
                        "members_count": len(team_members)
                    }
                )
            
            # Step 2: Extract required skills from feature breakdown
            required_skills = self._extract_required_skills(feature_breakdown)
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="required_skills_extracted",
                    step_data={
                        "skills_count": len(required_skills)
                    }
                )
            
            # Step 3: Perform skills gap analysis
            skill_gaps = self._analyze_skill_gaps(
                required_skills=required_skills,
                team_members=team_members
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="skill_gaps_analyzed",
                    step_data={
                        "gaps_count": len(skill_gaps),
                        "critical_gaps": len([g for g in skill_gaps if g.gap_severity == "critical"])
                    }
                )
            
            # Step 4: Match tasks to team members
            resource_allocations = self._match_tasks_to_members(
                feature_breakdown=feature_breakdown,
                team_members=team_members,
                required_skills=required_skills
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="resource_allocations_created",
                    step_data={
                        "allocations_count": len(resource_allocations)
                    }
                )
            
            # Step 5: Calculate capacity utilization
            capacity_utilization = self._calculate_capacity_utilization(
                team_members=team_members,
                resource_allocations=resource_allocations
            )
            
            # Step 6: Generate recommendations
            recommendations = self._generate_recommendations(
                skill_gaps=skill_gaps,
                capacity_utilization=capacity_utilization,
                team_members=team_members
            )
            
            # Step 7: Identify training needs
            training_needs = self._identify_training_needs(skill_gaps)
            
            # Step 8: Generate hiring recommendations
            hiring_recommendations = self._generate_hiring_recommendations(
                skill_gaps=skill_gaps,
                capacity_utilization=capacity_utilization
            )
            
            # Step 9: Calculate overall readiness
            overall_readiness = self._calculate_overall_readiness(
                skill_gaps=skill_gaps,
                capacity_utilization=capacity_utilization
            )
            
            # Create result
            result = SkillsMatchingResult(
                workflow_id=workflow_id,
                feature_breakdown=feature_breakdown,
                team_members=team_members,
                resource_allocations=resource_allocations,
                skill_gaps=skill_gaps,
                team_capacity_utilization=capacity_utilization,
                recommendations=recommendations,
                training_needs=training_needs,
                hiring_recommendations=hiring_recommendations,
                overall_readiness=overall_readiness
            )
            
            # Log workflow completion
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_complete(
                    workflow_id=workflow_id,
                    duration_ms=0,
                    success=True,
                    result_summary={
                        "team_members": len(team_members),
                        "allocations": len(resource_allocations),
                        "skill_gaps": len(skill_gaps),
                        "capacity_utilization": capacity_utilization,
                        "overall_readiness": overall_readiness
                    }
                )
            
            return result
            
        except Exception as e:
            # Log error
            if self.workflow_logger:
                await self.workflow_logger.log_error(
                    workflow_id=workflow_id,
                    error=e,
                    context={"stage": "skills_matching_workflow_d"}
                )
            raise
    
    async def _get_team_members(
        self,
        team_id: str,
        workflow_id: str
    ) -> List[TeamMember]:
        """Get team members and their skills from User Store."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.user_store_url}/api/v1/teams/{team_id}/members"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    members = []
                    
                    for member_data in data.get("members", []):
                        members.append(TeamMember(
                            member_id=member_data.get("id", str(uuid.uuid4())),
                            name=member_data.get("name", "Unknown"),
                            role=member_data.get("role", "Developer"),
                            skills=member_data.get("skills", []),
                            skill_levels=member_data.get("skill_levels", {}),
                            availability=member_data.get("availability", 1.0),
                            current_capacity=member_data.get("current_capacity", 0.0),
                            max_capacity=member_data.get("max_capacity", 20.0),
                            hourly_rate=member_data.get("hourly_rate")
                        ))
                    
                    return members
                else:
                    return self._get_default_team()
                    
        except Exception:
            return self._get_default_team()
    
    def _get_default_team(self) -> List[TeamMember]:
        """Default team when service is unavailable."""
        return [
            TeamMember(
                member_id="member_1",
                name="Alice",
                role="Backend Developer",
                skills=["Python", "FastAPI", "PostgreSQL", "Redis"],
                skill_levels={"Python": 5, "FastAPI": 4, "PostgreSQL": 4, "Redis": 3},
                availability=1.0,
                current_capacity=5.0,
                max_capacity=20.0
            ),
            TeamMember(
                member_id="member_2",
                name="Bob",
                role="Frontend Developer",
                skills=["React", "TypeScript", "CSS", "JavaScript"],
                skill_levels={"React": 5, "TypeScript": 4, "CSS": 4, "JavaScript": 5},
                availability=0.8,
                current_capacity=8.0,
                max_capacity=20.0
            ),
            TeamMember(
                member_id="member_3",
                name="Charlie",
                role="Full Stack Developer",
                skills=["Python", "React", "PostgreSQL", "Docker"],
                skill_levels={"Python": 4, "React": 4, "PostgreSQL": 3, "Docker": 4},
                availability=1.0,
                current_capacity=3.0,
                max_capacity=20.0
            )
        ]
    
    def _extract_required_skills(
        self,
        feature_breakdown: Dict[str, Any]
    ) -> Dict[str, int]:
        """Extract required skills from feature breakdown."""
        required_skills = {}
        
        # Extract from technical tasks
        technical_tasks = feature_breakdown.get("technical_tasks", [])
        for task in technical_tasks:
            task_skills = task.get("required_skills", [])
            complexity = task.get("complexity", "medium")
            
            # Determine required skill level based on complexity
            required_level = {
                "simple": 2,
                "medium": 3,
                "complex": 4
            }.get(complexity, 3)
            
            for skill in task_skills:
                # Use highest required level if skill appears multiple times
                if skill in required_skills:
                    required_skills[skill] = max(required_skills[skill], required_level)
                else:
                    required_skills[skill] = required_level
        
        return required_skills
    
    def _analyze_skill_gaps(
        self,
        required_skills: Dict[str, int],
        team_members: List[TeamMember]
    ) -> List[SkillGap]:
        """Analyze gaps between required and available skills."""
        skill_gaps = []
        
        # Get all available skills from team
        available_skills = {}
        for member in team_members:
            for skill, level in member.skill_levels.items():
                if skill in available_skills:
                    available_skills[skill] = max(available_skills[skill], level)
                else:
                    available_skills[skill] = level
        
        # Check each required skill
        for skill, required_level in required_skills.items():
            available_level = available_skills.get(skill, 0)
            gap = required_level - available_level
            
            if gap > 0:
                # Determine severity
                if gap >= 3:
                    severity = "critical"
                    mitigation = f"Hire specialist with {skill} expertise"
                elif gap >= 2:
                    severity = "moderate"
                    mitigation = f"Provide advanced training in {skill}"
                else:
                    severity = "minor"
                    mitigation = f"Pair programming or mentoring in {skill}"
                
                skill_gaps.append(SkillGap(
                    skill_name=skill,
                    required_level=required_level,
                    available_level=available_level,
                    gap_severity=severity,
                    mitigation=mitigation
                ))
        
        return skill_gaps
    
    def _match_tasks_to_members(
        self,
        feature_breakdown: Dict[str, Any],
        team_members: List[TeamMember],
        required_skills: Dict[str, int]
    ) -> List[ResourceAllocation]:
        """Match tasks to best-fit team members."""
        allocations = []
        
        technical_tasks = feature_breakdown.get("technical_tasks", [])
        
        for task in technical_tasks:
            task_id = task.get("id", str(uuid.uuid4()))
            task_title = task.get("title", "Unknown Task")
            task_skills = task.get("required_skills", [])
            estimated_hours = task.get("estimated_hours", 8.0)
            
            # Find best match
            best_member = None
            best_score = 0.0
            best_reasons = []
            
            for member in team_members:
                score, reasons = self._calculate_match_score(
                    member=member,
                    task_skills=task_skills,
                    required_skills=required_skills
                )
                
                if score > best_score:
                    best_score = score
                    best_member = member
                    best_reasons = reasons
            
            if best_member:
                allocations.append(ResourceAllocation(
                    member_id=best_member.member_id,
                    member_name=best_member.name,
                    task_id=task_id,
                    task_title=task_title,
                    match_score=best_score,
                    estimated_hours=estimated_hours,
                    confidence=best_score,  # Use match score as confidence
                    reasons=best_reasons
                ))
        
        return allocations
    
    def _calculate_match_score(
        self,
        member: TeamMember,
        task_skills: List[str],
        required_skills: Dict[str, int]
    ) -> Tuple[float, List[str]]:
        """Calculate how well a member matches a task."""
        score = 0.0
        reasons = []
        
        if not task_skills:
            return 0.5, ["No specific skills required"]
        
        # Check skill matches
        matched_skills = 0
        total_skill_level = 0
        
        for skill in task_skills:
            if skill in member.skills:
                matched_skills += 1
                skill_level = member.skill_levels.get(skill, 1)
                required_level = required_skills.get(skill, 3)
                
                # Score based on skill level vs required
                if skill_level >= required_level:
                    total_skill_level += 1.0
                    reasons.append(f"Has {skill} at required level")
                else:
                    total_skill_level += (skill_level / required_level)
                    reasons.append(f"Has {skill} but below required level")
        
        # Calculate base score (0.0 - 0.7)
        if len(task_skills) > 0:
            skill_match_ratio = matched_skills / len(task_skills)
            skill_level_score = total_skill_level / len(task_skills) if matched_skills > 0 else 0
            score = (skill_match_ratio * 0.5) + (skill_level_score * 0.2)
        
        # Availability bonus (0.0 - 0.15)
        if member.availability > 0.8:
            score += 0.15
            reasons.append("High availability")
        elif member.availability > 0.5:
            score += 0.10
        
        # Capacity bonus (0.0 - 0.15)
        remaining_capacity = member.max_capacity - member.current_capacity
        if remaining_capacity > 15:
            score += 0.15
            reasons.append("Ample capacity available")
        elif remaining_capacity > 10:
            score += 0.10
        elif remaining_capacity > 5:
            score += 0.05
        
        return min(score, 1.0), reasons
    
    def _calculate_capacity_utilization(
        self,
        team_members: List[TeamMember],
        resource_allocations: List[ResourceAllocation]
    ) -> float:
        """Calculate team capacity utilization."""
        if not team_members:
            return 0.0
        
        total_capacity = sum(m.max_capacity for m in team_members)
        used_capacity = sum(m.current_capacity for m in team_members)
        
        # Add planned allocations (convert hours to story points, rough estimate)
        planned_sp = sum(a.estimated_hours / 4 for a in resource_allocations)  # 4 hours per SP
        
        total_used = used_capacity + planned_sp
        utilization = total_used / total_capacity if total_capacity > 0 else 0.0
        
        return min(utilization, 1.0)
    
    def _generate_recommendations(
        self,
        skill_gaps: List[SkillGap],
        capacity_utilization: float,
        team_members: List[TeamMember]
    ) -> List[str]:
        """Generate resource recommendations."""
        recommendations = []
        
        # Skill gap recommendations
        critical_gaps = [g for g in skill_gaps if g.gap_severity == "critical"]
        if critical_gaps:
            recommendations.append(f"Address {len(critical_gaps)} critical skill gaps immediately")
        
        # Capacity recommendations
        if capacity_utilization > 0.9:
            recommendations.append("Team capacity is near maximum - consider adding resources")
        elif capacity_utilization < 0.5:
            recommendations.append("Team has significant spare capacity for additional work")
        
        # Availability recommendations
        low_availability = [m for m in team_members if m.availability < 0.7]
        if low_availability:
            recommendations.append(f"{len(low_availability)} team members have reduced availability")
        
        return recommendations
    
    def _identify_training_needs(
        self,
        skill_gaps: List[SkillGap]
    ) -> List[str]:
        """Identify training needs based on skill gaps."""
        training_needs = []
        
        for gap in skill_gaps:
            if gap.gap_severity in ["minor", "moderate"]:
                training_needs.append(
                    f"Train team in {gap.skill_name} (current: {gap.available_level}, need: {gap.required_level})"
                )
        
        return training_needs
    
    def _generate_hiring_recommendations(
        self,
        skill_gaps: List[SkillGap],
        capacity_utilization: float
    ) -> List[str]:
        """Generate hiring recommendations."""
        hiring_recommendations = []
        
        # Critical skill gaps require hiring
        critical_gaps = [g for g in skill_gaps if g.gap_severity == "critical"]
        for gap in critical_gaps:
            hiring_recommendations.append(
                f"Hire {gap.skill_name} specialist (gap: {gap.required_level - gap.available_level} levels)"
            )
        
        # High capacity utilization may require additional resources
        if capacity_utilization > 0.85 and len(critical_gaps) == 0:
            hiring_recommendations.append("Consider hiring additional developers to increase capacity")
        
        return hiring_recommendations
    
    def _calculate_overall_readiness(
        self,
        skill_gaps: List[SkillGap],
        capacity_utilization: float
    ) -> float:
        """Calculate overall team readiness score."""
        readiness = 1.0
        
        # Reduce for skill gaps
        critical_gaps = len([g for g in skill_gaps if g.gap_severity == "critical"])
        moderate_gaps = len([g for g in skill_gaps if g.gap_severity == "moderate"])
        
        readiness -= (critical_gaps * 0.2)  # -20% per critical gap
        readiness -= (moderate_gaps * 0.1)  # -10% per moderate gap
        
        # Reduce for over-capacity
        if capacity_utilization > 0.95:
            readiness -= 0.15
        elif capacity_utilization > 0.85:
            readiness -= 0.05
        
        return max(readiness, 0.0)

