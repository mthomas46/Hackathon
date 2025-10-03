"""
Feature Decomposition Workflow - Phase 2 Day 2
Part of Enhanced Roadmap v2.0 - Workflow A: AI Feature Decomposition

This workflow uses AI (LLM Gateway) to intelligently decompose high-level features
into detailed user stories and technical tasks with complexity and risk assessment.
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field

import httpx


@dataclass
class UserStory:
    """Represents a user story generated from feature decomposition."""
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    story_points: Optional[float] = None
    priority: str = "medium"  # low, medium, high, critical
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class TechnicalTask:
    """Represents a technical task for implementing a feature."""
    id: str
    user_story_id: str
    title: str
    description: str
    task_type: str  # frontend, backend, database, devops, testing
    estimated_hours: Optional[float] = None
    complexity: str = "medium"  # simple, medium, complex
    dependencies: List[str] = field(default_factory=list)
    required_skills: List[str] = field(default_factory=list)


@dataclass
class FeatureBreakdown:
    """Complete feature breakdown result from Workflow A."""
    feature_id: str
    feature_title: str
    user_stories: List[UserStory]
    technical_tasks: List[TechnicalTask]
    total_story_points: float
    total_estimated_hours: float
    complexity_score: float  # 0.0 - 1.0
    risk_level: str  # low, medium, high
    risk_factors: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    workflow_id: Optional[str] = None


class FeatureDecompositionWorkflow:
    """
    Workflow A: AI-Powered Feature Decomposition
    
    Uses LLM Gateway to intelligently break down high-level features into:
    - User stories with acceptance criteria
    - Technical tasks with complexity estimates
    - Risk assessment
    - Complexity scoring
    
    Part of Enhanced Roadmap v2.0 Phase 2 implementation.
    """
    
    def __init__(
        self,
        llm_gateway_url: str = "http://llm-gateway:5000",
        prompt_store_url: str = "http://prompt-store:5110",
        analysis_service_url: str = "http://analysis-service:8004",
        workflow_logger = None
    ):
        """
        Initialize Workflow A with service URLs.
        
        Args:
            llm_gateway_url: URL for LLM Gateway service
            prompt_store_url: URL for Prompt Store service
            analysis_service_url: URL for Analysis Service
            workflow_logger: WorkflowLogger instance for logging
        """
        self.llm_gateway_url = llm_gateway_url
        self.prompt_store_url = prompt_store_url
        self.analysis_service_url = analysis_service_url
        self.workflow_logger = workflow_logger
        self.timeout = 60.0  # Longer timeout for LLM calls
        
    async def execute(
        self,
        feature_description: str,
        feature_title: str,
        context: Optional[Dict[str, Any]] = None,
        parent_workflow_id: Optional[str] = None
    ) -> FeatureBreakdown:
        """
        Execute Workflow A: AI Feature Decomposition.
        
        Args:
            feature_description: High-level feature description
            feature_title: Feature title/name
            context: Additional context (platform, team_size, etc.)
            parent_workflow_id: Parent workflow ID for tracing
            
        Returns:
            FeatureBreakdown with complete decomposition results
        """
        # Generate workflow ID
        workflow_id = f"workflow_a_{str(uuid.uuid4())[:8]}"
        feature_id = f"feature_{str(uuid.uuid4())[:8]}"
        
        # Log workflow start
        if self.workflow_logger:
            await self.workflow_logger.log_workflow_start(
                workflow_id=workflow_id,
                operation="feature_decomposition_workflow_a",
                context={
                    "feature_title": feature_title,
                    "parent_workflow": parent_workflow_id,
                    "context": context or {}
                }
            )
        
        try:
            # Step 1: Get prompt template from Prompt Store
            prompt_template = await self._get_prompt_template()
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="prompt_template_retrieved",
                    step_data={"template_length": len(prompt_template)}
                )
            
            # Step 2: Generate feature breakdown using LLM
            user_stories, technical_tasks = await self._generate_breakdown_via_llm(
                feature_title=feature_title,
                feature_description=feature_description,
                prompt_template=prompt_template,
                context=context,
                workflow_id=workflow_id
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="llm_breakdown_complete",
                    step_data={
                        "user_stories_count": len(user_stories),
                        "technical_tasks_count": len(technical_tasks)
                    }
                )
            
            # Step 3: Calculate complexity score via Analysis Service
            complexity_score = await self._calculate_complexity_score(
                user_stories=user_stories,
                technical_tasks=technical_tasks,
                workflow_id=workflow_id
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="complexity_calculated",
                    step_data={"complexity_score": complexity_score}
                )
            
            # Step 4: Assess risks
            risk_level, risk_factors = await self._assess_risks(
                user_stories=user_stories,
                technical_tasks=technical_tasks,
                complexity_score=complexity_score,
                workflow_id=workflow_id
            )
            
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_step(
                    workflow_id=workflow_id,
                    step_name="risk_assessment_complete",
                    step_data={
                        "risk_level": risk_level,
                        "risk_factors_count": len(risk_factors)
                    }
                )
            
            # Step 5: Calculate totals
            total_story_points = sum(
                story.story_points or 0 for story in user_stories
            )
            total_estimated_hours = sum(
                task.estimated_hours or 0 for task in technical_tasks
            )
            
            # Create final breakdown
            breakdown = FeatureBreakdown(
                feature_id=feature_id,
                feature_title=feature_title,
                user_stories=user_stories,
                technical_tasks=technical_tasks,
                total_story_points=total_story_points,
                total_estimated_hours=total_estimated_hours,
                complexity_score=complexity_score,
                risk_level=risk_level,
                risk_factors=risk_factors,
                workflow_id=workflow_id
            )
            
            # Log workflow completion
            if self.workflow_logger:
                await self.workflow_logger.log_workflow_complete(
                    workflow_id=workflow_id,
                    duration_ms=0,  # Calculate if needed
                    success=True,
                    result_summary={
                        "user_stories": len(user_stories),
                        "technical_tasks": len(technical_tasks),
                        "total_story_points": total_story_points,
                        "complexity_score": complexity_score,
                        "risk_level": risk_level
                    }
                )
            
            return breakdown
            
        except Exception as e:
            # Log error
            if self.workflow_logger:
                await self.workflow_logger.log_error(
                    workflow_id=workflow_id,
                    error=e,
                    context={"stage": "feature_decomposition_workflow_a"}
                )
            raise
    
    async def _get_prompt_template(self) -> str:
        """Retrieve feature decomposition prompt template from Prompt Store."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Try to get specific template
                response = await client.get(
                    f"{self.prompt_store_url}/api/v1/prompts/feature_decomposition"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("template", self._get_default_template())
                else:
                    # Fallback to default template
                    return self._get_default_template()
                    
        except Exception as e:
            # Fallback to default template on error
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Default feature decomposition prompt template."""
        return """You are an expert software architect and product manager. Break down the following feature into detailed user stories and technical tasks.

Feature Title: {feature_title}
Feature Description: {feature_description}
Context: {context}

Please provide:

1. USER STORIES (3-7 stories):
   - Clear user story format: "As a [user type], I want [goal], so that [benefit]"
   - Detailed acceptance criteria (3-5 per story)
   - Story point estimates (1, 2, 3, 5, 8, 13)
   - Priority level (low, medium, high, critical)
   - Dependencies on other stories
   - Relevant tags

2. TECHNICAL TASKS (per user story):
   - Specific implementation tasks
   - Task type (frontend, backend, database, devops, testing)
   - Estimated hours
   - Complexity (simple, medium, complex)
   - Required skills
   - Dependencies

Respond in valid JSON format with this structure:
{{
  "user_stories": [
    {{
      "title": "string",
      "description": "string",
      "acceptance_criteria": ["string"],
      "story_points": number,
      "priority": "medium",
      "dependencies": ["story_id"],
      "tags": ["string"]
    }}
  ],
  "technical_tasks": [
    {{
      "user_story_index": number,
      "title": "string",
      "description": "string",
      "task_type": "backend",
      "estimated_hours": number,
      "complexity": "medium",
      "dependencies": ["task_id"],
      "required_skills": ["string"]
    }}
  ]
}}"""
    
    async def _generate_breakdown_via_llm(
        self,
        feature_title: str,
        feature_description: str,
        prompt_template: str,
        context: Optional[Dict[str, Any]],
        workflow_id: str
    ) -> tuple[List[UserStory], List[TechnicalTask]]:
        """Use LLM Gateway to generate feature breakdown."""
        # Format prompt
        prompt = prompt_template.format(
            feature_title=feature_title,
            feature_description=feature_description,
            context=json.dumps(context or {}, indent=2)
        )
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.llm_gateway_url}/query",
                    json={
                        "prompt": prompt,
                        "model": "mistral",
                        "provider": "ollama",
                        "max_tokens": 2000,
                        "temperature": 0.4  # Balanced creativity and consistency
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    llm_response = result.get("data", {}).get("response", "")
                    
                    # Parse JSON from LLM response
                    breakdown_data = self._parse_llm_response(llm_response)
                    
                    # Convert to UserStory and TechnicalTask objects
                    user_stories = self._create_user_stories(breakdown_data.get("user_stories", []))
                    technical_tasks = self._create_technical_tasks(
                        breakdown_data.get("technical_tasks", []),
                        user_stories
                    )
                    
                    return user_stories, technical_tasks
                else:
                    # Fallback to basic breakdown
                    return self._create_basic_breakdown(feature_title, feature_description)
                    
        except Exception as e:
            # Fallback to basic breakdown on error
            return self._create_basic_breakdown(feature_title, feature_description)
    
    def _parse_llm_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        try:
            # Try direct JSON parsing
            return json.loads(llm_response)
        except json.JSONDecodeError:
            # Try extracting JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', llm_response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # If still fails, return empty structure
            return {"user_stories": [], "technical_tasks": []}
    
    def _create_user_stories(self, stories_data: List[Dict]) -> List[UserStory]:
        """Convert dict data to UserStory objects."""
        user_stories = []
        for i, story_data in enumerate(stories_data):
            user_stories.append(UserStory(
                id=f"story_{i+1}",
                title=story_data.get("title", ""),
                description=story_data.get("description", ""),
                acceptance_criteria=story_data.get("acceptance_criteria", []),
                story_points=story_data.get("story_points"),
                priority=story_data.get("priority", "medium"),
                dependencies=story_data.get("dependencies", []),
                tags=story_data.get("tags", [])
            ))
        return user_stories
    
    def _create_technical_tasks(
        self,
        tasks_data: List[Dict],
        user_stories: List[UserStory]
    ) -> List[TechnicalTask]:
        """Convert dict data to TechnicalTask objects."""
        technical_tasks = []
        for i, task_data in enumerate(tasks_data):
            # Map user_story_index to user_story_id
            story_index = task_data.get("user_story_index", 0)
            user_story_id = user_stories[story_index].id if story_index < len(user_stories) else "story_1"
            
            technical_tasks.append(TechnicalTask(
                id=f"task_{i+1}",
                user_story_id=user_story_id,
                title=task_data.get("title", ""),
                description=task_data.get("description", ""),
                task_type=task_data.get("task_type", "backend"),
                estimated_hours=task_data.get("estimated_hours"),
                complexity=task_data.get("complexity", "medium"),
                dependencies=task_data.get("dependencies", []),
                required_skills=task_data.get("required_skills", [])
            ))
        return technical_tasks
    
    def _create_basic_breakdown(
        self,
        feature_title: str,
        feature_description: str
    ) -> tuple[List[UserStory], List[TechnicalTask]]:
        """Create a basic feature breakdown when LLM is unavailable."""
        # Create one simple user story
        user_story = UserStory(
            id="story_1",
            title=f"Implement {feature_title}",
            description=feature_description,
            acceptance_criteria=[
                "Feature is implemented as described",
                "Unit tests are written and passing",
                "Integration tests are passing"
            ],
            story_points=5.0,
            priority="medium"
        )
        
        # Create basic technical tasks
        tasks = [
            TechnicalTask(
                id="task_1",
                user_story_id="story_1",
                title=f"Design {feature_title}",
                description="Design the feature architecture",
                task_type="backend",
                estimated_hours=8.0,
                complexity="medium",
                required_skills=["architecture", "design"]
            ),
            TechnicalTask(
                id="task_2",
                user_story_id="story_1",
                title=f"Implement {feature_title}",
                description="Implement the core functionality",
                task_type="backend",
                estimated_hours=16.0,
                complexity="medium",
                required_skills=["programming"]
            ),
            TechnicalTask(
                id="task_3",
                user_story_id="story_1",
                title=f"Test {feature_title}",
                description="Write and run tests",
                task_type="testing",
                estimated_hours=8.0,
                complexity="simple",
                required_skills=["testing"]
            )
        ]
        
        return [user_story], tasks
    
    async def _calculate_complexity_score(
        self,
        user_stories: List[UserStory],
        technical_tasks: List[TechnicalTask],
        workflow_id: str
    ) -> float:
        """Calculate complexity score via Analysis Service."""
        # Calculate based on multiple factors
        factors = {
            "user_story_count": len(user_stories),
            "task_count": len(technical_tasks),
            "total_story_points": sum(s.story_points or 0 for s in user_stories),
            "total_hours": sum(t.estimated_hours or 0 for t in technical_tasks),
            "complex_tasks": sum(1 for t in technical_tasks if t.complexity == "complex"),
            "unique_skills": len(set(
                skill for task in technical_tasks for skill in task.required_skills
            ))
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.analysis_service_url}/api/v1/analyze/complexity",
                    json=factors
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("complexity_score", 0.5)
                    
        except Exception:
            pass  # Fall through to local calculation
        
        # Local complexity calculation if service unavailable
        # Normalize factors and calculate weighted score
        score = 0.0
        score += min(len(user_stories) / 10.0, 0.2)  # Max 0.2 from stories
        score += min(len(technical_tasks) / 20.0, 0.3)  # Max 0.3 from tasks
        score += min(factors["total_story_points"] / 50.0, 0.2)  # Max 0.2 from points
        score += min(factors["complex_tasks"] / 10.0, 0.3)  # Max 0.3 from complex tasks
        
        return min(score, 1.0)  # Cap at 1.0
    
    async def _assess_risks(
        self,
        user_stories: List[UserStory],
        technical_tasks: List[TechnicalTask],
        complexity_score: float,
        workflow_id: str
    ) -> tuple[str, List[str]]:
        """Assess risks based on breakdown analysis."""
        risk_factors = []
        
        # Check for high complexity
        if complexity_score > 0.7:
            risk_factors.append("High complexity score indicates challenging implementation")
        
        # Check for many dependencies
        total_dependencies = sum(len(s.dependencies) for s in user_stories)
        total_dependencies += sum(len(t.dependencies) for t in technical_tasks)
        if total_dependencies > 10:
            risk_factors.append("High number of dependencies may cause delays")
        
        # Check for diverse skill requirements
        unique_skills = set(
            skill for task in technical_tasks for skill in task.required_skills
        )
        if len(unique_skills) > 8:
            risk_factors.append("Wide range of skills required may limit resource availability")
        
        # Check for large story points
        total_points = sum(s.story_points or 0 for s in user_stories)
        if total_points > 40:
            risk_factors.append("Large total story points suggest extended timeline")
        
        # Check for many complex tasks
        complex_task_count = sum(1 for t in technical_tasks if t.complexity == "complex")
        if complex_task_count > 5:
            risk_factors.append("Multiple complex tasks increase implementation risk")
        
        # Determine overall risk level
        if len(risk_factors) >= 4 or complexity_score > 0.8:
            risk_level = "high"
        elif len(risk_factors) >= 2 or complexity_score > 0.5:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return risk_level, risk_factors

