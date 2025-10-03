"""
LLM Gateway Integration Client
================================

Client for interacting with the LLM Gateway for advanced AI processing,
multi-provider routing, and intelligent caching.
"""

import httpx
import os
from typing import Dict, Any, List, Optional
import time


class LLMGatewayClient:
    """Client for LLM Gateway service integration."""
    
    def __init__(self, base_url: Optional[str] = None, log_client=None):
        """
        Initialize LLM Gateway client.
        
        Args:
            base_url: LLM Gateway service URL
            log_client: Log collector client for logging
        """
        self.base_url = base_url or os.getenv("LLM_GATEWAY_URL", "http://llm-gateway:5055")
        self.timeout = httpx.Timeout(120.0, connect=10.0)  # Extended timeout for LLM calls
        self.log_client = log_client
    
    async def process_prompt(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a prompt through LLM Gateway.
        
        Args:
            prompt: Prompt text
            context: Additional context for the prompt
            provider: Optional AI provider (openai, anthropic, etc.)
            model: Optional specific model
            
        Returns:
            LLM response with text and metadata
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "prompt": prompt,
                    "context": context or {},
                    "provider": provider,
                    "model": model
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/process",
                    json=payload
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "llm-gateway",
                            "process_prompt",
                            True,
                            duration_ms
                        )
                    
                    return result
                else:
                    error_msg = f"LLM processing failed with status {response.status_code}"
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "llm-gateway",
                            "process_prompt",
                            False,
                            duration_ms,
                            error_msg
                        )
                    
                    return {"error": error_msg, "text": ""}
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"LLM Gateway call failed: {str(e)}"
            
            if self.log_client:
                await self.log_client.log_integration_call(
                    "llm-gateway",
                    "process_prompt",
                    False,
                    duration_ms,
                    error_msg
                )
            
            return {"error": error_msg, "text": ""}
    
    async def analyze_feature_complexity(
        self,
        feature_description: str,
        technical_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze feature complexity using AI.
        
        Args:
            feature_description: Feature description
            technical_context: Technical context (tech stack, team skills, etc.)
            
        Returns:
            Complexity analysis with score and reasoning
        """
        prompt = f"""
        Analyze the complexity of this software feature and provide:
        1. Complexity score (1-10, where 10 is most complex)
        2. Story point estimate (Fibonacci: 1, 2, 3, 5, 8, 13, 21)
        3. Key complexity factors
        4. Recommended team composition
        5. Estimated duration in days
        
        Feature: {feature_description}
        
        Technical Context: {technical_context or 'Not provided'}
        
        Respond in JSON format.
        """
        
        result = await self.process_prompt(prompt, context={"type": "complexity_analysis"})
        
        return {
            "complexity_score": result.get("complexity_score", 5),
            "story_points": result.get("story_points", 5),
            "factors": result.get("factors", []),
            "team_composition": result.get("team_composition", []),
            "estimated_days": result.get("estimated_days", 5),
            "reasoning": result.get("text", "")
        }
    
    async def generate_user_stories(
        self,
        feature_description: str,
        persona: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate user stories from feature description.
        
        Args:
            feature_description: Feature description
            persona: User persona/type
            
        Returns:
            List of generated user stories
        """
        prompt = f"""
        Generate user stories for this feature following the format:
        "As a [user type], I want [functionality] so that [benefit]"
        
        Feature: {feature_description}
        User Persona: {persona or 'general user'}
        
        Generate 3-5 detailed user stories with:
        - User story text
        - Acceptance criteria (3-5 items)
        - Priority (High/Medium/Low)
        - Story points estimate
        
        Respond in JSON format as a list of user stories.
        """
        
        result = await self.process_prompt(prompt, context={"type": "user_story_generation"})
        
        # Parse user stories from response
        user_stories = result.get("user_stories", [])
        if not user_stories and "text" in result:
            # Fallback parsing if needed
            user_stories = self._parse_user_stories_from_text(result["text"])
        
        return user_stories
    
    async def assess_risk(
        self,
        feature_description: str,
        project_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Assess risks associated with a feature.
        
        Args:
            feature_description: Feature description
            project_context: Project context including constraints, dependencies
            
        Returns:
            Risk assessment with identified risks and mitigation strategies
        """
        prompt = f"""
        Assess the risks associated with implementing this feature:
        
        Feature: {feature_description}
        Project Context: {project_context or 'Not provided'}
        
        Identify:
        1. Technical risks (complexity, dependencies, unknowns)
        2. Schedule risks (estimates, resource availability)
        3. Quality risks (testing challenges, edge cases)
        4. Business risks (market changes, stakeholder alignment)
        
        For each risk provide:
        - Risk description
        - Likelihood (Low/Medium/High)
        - Impact (Low/Medium/High)
        - Mitigation strategy
        
        Respond in JSON format.
        """
        
        result = await self.process_prompt(prompt, context={"type": "risk_assessment"})
        
        return {
            "overall_risk_level": result.get("overall_risk_level", "Medium"),
            "technical_risks": result.get("technical_risks", []),
            "schedule_risks": result.get("schedule_risks", []),
            "quality_risks": result.get("quality_risks", []),
            "business_risks": result.get("business_risks", []),
            "mitigation_strategies": result.get("mitigation_strategies", [])
        }
    
    async def generate_technical_approach(
        self,
        feature_description: str,
        tech_stack: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate technical approach for implementing a feature.
        
        Args:
            feature_description: Feature description
            tech_stack: Technology stack being used
            
        Returns:
            Technical approach with architecture, components, and implementation plan
        """
        prompt = f"""
        Propose a technical approach for implementing this feature:
        
        Feature: {feature_description}
        Technology Stack: {', '.join(tech_stack) if tech_stack else 'Not specified'}
        
        Provide:
        1. High-level architecture
        2. Key components/modules needed
        3. Data models and schemas
        4. API endpoints required
        5. External integrations
        6. Testing strategy
        
        Respond in JSON format.
        """
        
        result = await self.process_prompt(prompt, context={"type": "technical_approach"})
        
        return {
            "architecture": result.get("architecture", ""),
            "components": result.get("components", []),
            "data_models": result.get("data_models", []),
            "api_endpoints": result.get("api_endpoints", []),
            "integrations": result.get("integrations", []),
            "testing_strategy": result.get("testing_strategy", "")
        }
    
    def _parse_user_stories_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        Parse user stories from unstructured text response.
        
        Args:
            text: Response text
            
        Returns:
            Parsed user stories
        """
        # Simple parser - in production would use more sophisticated parsing
        stories = []
        
        # Split by "As a" pattern
        parts = text.split("As a ")
        for part in parts[1:]:  # Skip first empty part
            story = {
                "story": f"As a {part.split('Acceptance')[0].strip()}",
                "acceptance_criteria": [],
                "priority": "Medium",
                "story_points": 5
            }
            stories.append(story)
        
        return stories

