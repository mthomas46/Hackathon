"""
Feature Decomposition Engine
============================

AI-powered decomposition of high-level features into actionable tasks,
user stories, and implementation steps using the Interpreter service.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..entities.feature import Feature, FeatureStatus, FeaturePriority
from ..entities.task import Task, TaskType, TaskStatus


class DecompositionStrategy(Enum):
    """Strategy for feature decomposition."""
    USER_STORY_FIRST = "user_story_first"  # Break into user stories first
    TECHNICAL_FIRST = "technical_first"  # Focus on technical tasks
    BALANCED = "balanced"  # Mix of user stories and technical tasks
    MINIMAL = "minimal"  # Minimal viable decomposition


@dataclass
class UserStory:
    """User story extracted from feature."""
    id: str
    title: str
    description: str
    as_a: str  # "As a [user type]"
    i_want: str  # "I want to [action]"
    so_that: str  # "So that [benefit]"
    acceptance_criteria: List[str] = field(default_factory=list)
    estimated_effort: Optional[float] = None
    priority: str = "MEDIUM"


@dataclass
class TechnicalTask:
    """Technical implementation task."""
    id: str
    title: str
    description: str
    task_type: TaskType
    estimated_hours: float
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    complexity: str = "MEDIUM"  # LOW, MEDIUM, HIGH


@dataclass
class DecompositionRequest:
    """Request for feature decomposition."""
    feature: Feature
    strategy: DecompositionStrategy = DecompositionStrategy.BALANCED
    max_tasks: int = 20  # Maximum tasks to generate
    include_user_stories: bool = True
    include_technical_tasks: bool = True
    context: Dict[str, any] = field(default_factory=dict)


@dataclass
class DecompositionResult:
    """Result of feature decomposition."""
    feature: Feature
    user_stories: List[UserStory]
    technical_tasks: List[TechnicalTask]
    tasks: List[Task]  # Converted to Task entities
    total_estimated_hours: float
    total_story_points: float
    complexity_assessment: str
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def task_count(self) -> int:
        """Get total number of tasks generated."""
        return len(self.tasks)
    
    def average_task_size(self) -> float:
        """Calculate average task size in hours."""
        if not self.tasks:
            return 0.0
        return self.total_estimated_hours / len(self.tasks)


class FeatureDecomposer:
    """
    AI-powered feature decomposition engine.
    
    Breaks down high-level features into:
    - User stories with acceptance criteria
    - Technical implementation tasks
    - Effort estimates
    - Risk assessments
    - Dependencies
    """
    
    def __init__(self, interpreter_client=None, llm_gateway_client=None):
        """
        Initialize feature decomposer.
        
        Args:
            interpreter_client: Client for interpreter service (optional)
            llm_gateway_client: Client for LLM gateway (optional)
        """
        self.interpreter_client = interpreter_client
        self.llm_gateway_client = llm_gateway_client
    
    async def decompose_feature(
        self,
        request: DecompositionRequest
    ) -> DecompositionResult:
        """
        Decompose feature into tasks and user stories.
        
        Args:
            request: Decomposition request
            
        Returns:
            DecompositionResult with tasks and metadata
        """
        feature = request.feature
        
        # Generate user stories if requested
        user_stories = []
        if request.include_user_stories:
            user_stories = await self._generate_user_stories(feature, request)
        
        # Generate technical tasks if requested
        technical_tasks = []
        if request.include_technical_tasks:
            technical_tasks = await self._generate_technical_tasks(feature, request)
        
        # Convert to Task entities
        tasks = self._convert_to_tasks(user_stories, technical_tasks, feature)
        
        # Limit to max_tasks
        if len(tasks) > request.max_tasks:
            tasks = tasks[:request.max_tasks]
        
        # Calculate estimates
        total_hours = sum(t.estimated_hours for t in tasks if t.estimated_hours)
        total_points = feature.estimated_effort if feature.estimated_effort else total_hours / 8
        
        # Assess complexity
        complexity = self._assess_complexity(feature, tasks)
        
        # Identify risks
        risks = self._identify_risks(feature, tasks)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(feature, tasks, complexity)
        
        return DecompositionResult(
            feature=feature,
            user_stories=user_stories,
            technical_tasks=technical_tasks,
            tasks=tasks,
            total_estimated_hours=total_hours,
            total_story_points=total_points,
            complexity_assessment=complexity,
            risk_factors=risks,
            recommendations=recommendations
        )
    
    async def _generate_user_stories(
        self,
        feature: Feature,
        request: DecompositionRequest
    ) -> List[UserStory]:
        """
        Generate user stories from feature description.
        
        Uses AI to extract user stories if interpreter client available,
        otherwise uses rule-based generation.
        """
        if self.interpreter_client:
            # Use AI-powered generation
            return await self._ai_generate_user_stories(feature, request)
        else:
            # Use rule-based generation
            return self._rule_based_user_stories(feature, request)
    
    async def _ai_generate_user_stories(
        self,
        feature: Feature,
        request: DecompositionRequest
    ) -> List[UserStory]:
        """Generate user stories using AI (interpreter service)."""
        # This would call the actual interpreter service
        # For now, return rule-based results
        return self._rule_based_user_stories(feature, request)
    
    def _rule_based_user_stories(
        self,
        feature: Feature,
        request: DecompositionRequest
    ) -> List[UserStory]:
        """Generate user stories using rule-based logic."""
        stories = []
        
        # Extract key user stories from feature
        if request.strategy == DecompositionStrategy.USER_STORY_FIRST:
            story_count = 3
        elif request.strategy == DecompositionStrategy.BALANCED:
            story_count = 2
        elif request.strategy == DecompositionStrategy.MINIMAL:
            story_count = 1
        else:
            story_count = 1
        
        # Generate stories based on feature description
        for i in range(story_count):
            story = UserStory(
                id=f"{feature.id}-story-{i+1}",
                title=f"User Story {i+1} for {feature.title}",
                description=f"Story derived from: {feature.description[:100]}...",
                as_a="user",
                i_want=f"implement part {i+1} of {feature.title}",
                so_that="the feature is complete",
                acceptance_criteria=[
                    "Implementation is complete",
                    "Tests are passing",
                    "Documentation is updated"
                ],
                estimated_effort=feature.estimated_effort / story_count if feature.estimated_effort else 5.0,
                priority=feature.priority.value if feature.priority else "MEDIUM"
            )
            stories.append(story)
        
        return stories
    
    async def _generate_technical_tasks(
        self,
        feature: Feature,
        request: DecompositionRequest
    ) -> List[TechnicalTask]:
        """
        Generate technical implementation tasks.
        
        Uses AI if available, otherwise rule-based generation.
        """
        if self.llm_gateway_client:
            return await self._ai_generate_technical_tasks(feature, request)
        else:
            return self._rule_based_technical_tasks(feature, request)
    
    async def _ai_generate_technical_tasks(
        self,
        feature: Feature,
        request: DecompositionRequest
    ) -> List[TechnicalTask]:
        """Generate technical tasks using AI (LLM gateway)."""
        # This would call the actual LLM gateway
        # For now, return rule-based results
        return self._rule_based_technical_tasks(feature, request)
    
    def _rule_based_technical_tasks(
        self,
        feature: Feature,
        request: DecompositionRequest
    ) -> List[TechnicalTask]:
        """Generate technical tasks using rule-based logic."""
        tasks = []
        
        # Standard software development phases
        task_templates = [
            ("Design", TaskType.DESIGN, 4),
            ("Development", TaskType.DEVELOPMENT, 8),
            ("Testing", TaskType.TESTING, 4),
            ("Documentation", TaskType.DOCUMENTATION, 2),
        ]
        
        # Adjust based on strategy
        if request.strategy == DecompositionStrategy.TECHNICAL_FIRST:
            # Add more technical tasks
            task_templates.extend([
                ("Code Review", TaskType.REVIEW, 2),
                ("Performance Testing", TaskType.TESTING, 3),
            ])
        elif request.strategy == DecompositionStrategy.MINIMAL:
            # Only essential tasks
            task_templates = [
                ("Development", TaskType.DEVELOPMENT, 8),
                ("Testing", TaskType.TESTING, 4),
            ]
        
        for i, (name, task_type, hours) in enumerate(task_templates):
            task = TechnicalTask(
                id=f"{feature.id}-task-{i+1}",
                title=f"{name}: {feature.title}",
                description=f"{name} work for {feature.description[:100]}...",
                task_type=task_type,
                estimated_hours=hours,
                dependencies=[tasks[i-1].id] if i > 0 else [],
                tags=[task_type.value, feature.title.lower()],
                complexity=self._estimate_complexity(hours)
            )
            tasks.append(task)
        
        return tasks
    
    def _convert_to_tasks(
        self,
        user_stories: List[UserStory],
        technical_tasks: List[TechnicalTask],
        feature: Feature
    ) -> List[Task]:
        """Convert user stories and technical tasks to Task entities."""
        tasks = []
        
        # Convert user stories to tasks
        for story in user_stories:
            task = Task(
                id=story.id,
                feature_id=feature.id,
                created_by="system",
                title=story.title,
                description=f"{story.as_a}, {story.i_want} so that {story.so_that}",
                task_type=TaskType.ANALYSIS,  # User stories are analysis-type tasks
                estimated_hours=story.estimated_effort * 8 if story.estimated_effort else 8.0,
                status=TaskStatus.TODO
            )
            tasks.append(task)
        
        # Convert technical tasks to Task entities
        for tech_task in technical_tasks:
            task = Task(
                id=tech_task.id,
                feature_id=feature.id,
                created_by="system",
                title=tech_task.title,
                description=tech_task.description,
                task_type=tech_task.task_type,
                estimated_hours=tech_task.estimated_hours,
                status=TaskStatus.TODO
            )
            tasks.append(task)
        
        return tasks
    
    def _assess_complexity(self, feature: Feature, tasks: List[Task]) -> str:
        """Assess overall complexity of feature."""
        if not tasks:
            return "LOW"
        
        # Calculate based on task count and total hours
        task_count = len(tasks)
        total_hours = sum(t.estimated_hours for t in tasks if t.estimated_hours)
        
        if task_count > 10 or total_hours > 80:
            return "HIGH"
        elif task_count > 5 or total_hours > 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _estimate_complexity(self, hours: float) -> str:
        """Estimate task complexity based on hours."""
        if hours > 16:
            return "HIGH"
        elif hours > 8:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _identify_risks(self, feature: Feature, tasks: List[Task]) -> List[str]:
        """Identify potential risks in feature implementation."""
        risks = []
        
        # Check for large tasks
        large_tasks = [t for t in tasks if t.estimated_hours and t.estimated_hours > 16]
        if large_tasks:
            risks.append(f"{len(large_tasks)} tasks are very large (>16 hours) - consider splitting")
        
        # Check for missing dependencies
        if feature.dependencies:
            risks.append(f"Feature has {len(feature.dependencies)} dependencies - ensure they're completed first")
        
        # Check for critical priority
        if feature.priority == FeaturePriority.CRITICAL:
            risks.append("CRITICAL priority - needs careful planning and monitoring")
        
        # Check for high task count
        if len(tasks) > 15:
            risks.append(f"High task count ({len(tasks)}) - may need better organization")
        
        return risks
    
    def _generate_recommendations(
        self,
        feature: Feature,
        tasks: List[Task],
        complexity: str
    ) -> List[str]:
        """Generate recommendations for feature implementation."""
        recommendations = []
        
        # Complexity-based recommendations
        if complexity == "HIGH":
            recommendations.append("Consider breaking feature into smaller sub-features")
            recommendations.append("Allocate senior developers for complex tasks")
            recommendations.append("Add extra buffer time for unknowns")
        elif complexity == "MEDIUM":
            recommendations.append("Regular progress checkpoints recommended")
            recommendations.append("Ensure adequate testing coverage")
        
        # Task count recommendations
        if len(tasks) < 3:
            recommendations.append("Consider if feature needs more detailed breakdown")
        elif len(tasks) > 15:
            recommendations.append("Group related tasks into sub-features")
        
        # Estimation recommendations
        total_hours = sum(t.estimated_hours for t in tasks if t.estimated_hours)
        if total_hours > 80:
            recommendations.append("Total hours exceed 2 weeks - consider splitting")
        
        # Priority recommendations
        if feature.priority == FeaturePriority.CRITICAL:
            recommendations.append("Assign best-available resources")
            recommendations.append("Consider parallel work streams")
        
        return recommendations
    
    def decompose_multiple_features(
        self,
        features: List[Feature],
        strategy: DecompositionStrategy = DecompositionStrategy.BALANCED
    ) -> Dict[str, DecompositionResult]:
        """
        Decompose multiple features in batch.
        
        Args:
            features: List of features to decompose
            strategy: Decomposition strategy to use
            
        Returns:
            Dictionary mapping feature IDs to decomposition results
        """
        results = {}
        
        for feature in features:
            request = DecompositionRequest(
                feature=feature,
                strategy=strategy
            )
            # Note: This is synchronous, would need async version for production
            # For now, using sync wrapper
            result = self._decompose_sync(request)
            results[feature.id] = result
        
        return results
    
    def _decompose_sync(self, request: DecompositionRequest) -> DecompositionResult:
        """Synchronous wrapper for decompose_feature (for batch processing)."""
        # In production, this would use asyncio.run or similar
        # For now, using synchronous logic
        
        feature = request.feature
        
        user_stories = []
        if request.include_user_stories:
            user_stories = self._rule_based_user_stories(feature, request)
        
        technical_tasks = []
        if request.include_technical_tasks:
            technical_tasks = self._rule_based_technical_tasks(feature, request)
        
        tasks = self._convert_to_tasks(user_stories, technical_tasks, feature)
        
        if len(tasks) > request.max_tasks:
            tasks = tasks[:request.max_tasks]
        
        total_hours = sum(t.estimated_hours for t in tasks if t.estimated_hours)
        total_points = feature.estimated_effort if feature.estimated_effort else total_hours / 8
        
        complexity = self._assess_complexity(feature, tasks)
        risks = self._identify_risks(feature, tasks)
        recommendations = self._generate_recommendations(feature, tasks, complexity)
        
        return DecompositionResult(
            feature=feature,
            user_stories=user_stories,
            technical_tasks=technical_tasks,
            tasks=tasks,
            total_estimated_hours=total_hours,
            total_story_points=total_points,
            complexity_assessment=complexity,
            risk_factors=risks,
            recommendations=recommendations
        )

