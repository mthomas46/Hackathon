"""
Interpreter Service Integration Client
========================================

Client for interacting with the Interpreter service for AI-powered
content analysis, feature decomposition, and natural language processing.
"""

import httpx
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import time


class InterpreterClient:
    """Client for Interpreter service integration."""
    
    def __init__(self, base_url: Optional[str] = None, log_client=None):
        """
        Initialize interpreter client.
        
        Args:
            base_url: Interpreter service URL
            log_client: Log collector client for logging integration calls
        """
        self.base_url = base_url or os.getenv("INTERPRETER_URL", "http://interpreter:5120")
        self.timeout = httpx.Timeout(60.0, connect=10.0)  # Longer timeout for AI processing
        self.log_client = log_client
    
    async def analyze_feature_description(
        self,
        description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze feature description using NLP to extract key information.
        
        Args:
            description: Feature description text
            context: Additional context for analysis
            
        Returns:
            Analysis results including entities, intents, and insights
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "query": description,
                    "context": context or {},
                    "analysis_type": "feature_analysis"
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/analyze",
                    json=payload
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "interpreter",
                            "analyze_feature_description",
                            True,
                            duration_ms
                        )
                    
                    return result
                else:
                    error_msg = f"Analysis failed with status {response.status_code}"
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "interpreter",
                            "analyze_feature_description",
                            False,
                            duration_ms,
                            error_msg
                        )
                    
                    return {"error": error_msg, "status_code": response.status_code}
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Interpreter call failed: {str(e)}"
            
            if self.log_client:
                await self.log_client.log_integration_call(
                    "interpreter",
                    "analyze_feature_description",
                    False,
                    duration_ms,
                    error_msg
                )
            
            return {"error": error_msg}
    
    async def decompose_feature(
        self,
        feature_description: str,
        decomposition_level: str = "detailed",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Decompose feature into user stories and tasks.
        
        Args:
            feature_description: Feature description to decompose
            decomposition_level: Level of decomposition (high_level, detailed, granular)
            context: Additional context including team, technology stack, etc.
            
        Returns:
            Decomposed user stories and tasks with estimates
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "feature": feature_description,
                    "level": decomposition_level,
                    "context": context or {}
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/decompose",
                    json=payload
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "interpreter",
                            "decompose_feature",
                            True,
                            duration_ms
                        )
                    
                    return result
                else:
                    error_msg = f"Decomposition failed with status {response.status_code}"
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "interpreter",
                            "decompose_feature",
                            False,
                            duration_ms,
                            error_msg
                        )
                    
                    return {"error": error_msg, "user_stories": [], "tasks": []}
                    
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"Decomposition call failed: {str(e)}"
            
            if self.log_client:
                await self.log_client.log_integration_call(
                    "interpreter",
                    "decompose_feature",
                    False,
                    duration_ms,
                    error_msg
                )
            
            return {"error": error_msg, "user_stories": [], "tasks": []}
    
    async def generate_acceptance_criteria(
        self,
        feature_description: str,
        user_stories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate acceptance criteria for a feature.
        
        Args:
            feature_description: Feature description
            user_stories: Optional list of user stories
            
        Returns:
            Generated acceptance criteria
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "feature": feature_description,
                    "user_stories": user_stories or []
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/generate/acceptance-criteria",
                    json=payload
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "interpreter",
                            "generate_acceptance_criteria",
                            True,
                            duration_ms
                        )
                    
                    return result
                else:
                    return {"error": f"Failed with status {response.status_code}", "criteria": []}
                    
        except Exception as e:
            return {"error": str(e), "criteria": []}
    
    async def estimate_complexity(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Estimate task complexity using AI analysis.
        
        Args:
            task_description: Task description
            context: Additional context for estimation
            
        Returns:
            Complexity estimate with story points and confidence score
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "task": task_description,
                    "context": context or {}
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/estimate/complexity",
                    json=payload
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "interpreter",
                            "estimate_complexity",
                            True,
                            duration_ms
                        )
                    
                    return result
                else:
                    return {
                        "error": f"Failed with status {response.status_code}",
                        "story_points": 5,  # Default estimate
                        "confidence": 0.0
                    }
                    
        except Exception as e:
            return {
                "error": str(e),
                "story_points": 5,  # Default estimate
                "confidence": 0.0
            }
    
    async def extract_technical_requirements(
        self,
        feature_description: str
    ) -> Dict[str, Any]:
        """
        Extract technical requirements from feature description.
        
        Args:
            feature_description: Feature description text
            
        Returns:
            Extracted technical requirements, dependencies, and technologies
        """
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload = {
                    "text": feature_description,
                    "extraction_type": "technical_requirements"
                }
                
                response = await client.post(
                    f"{self.base_url}/api/v1/extract",
                    json=payload
                )
                
                duration_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if self.log_client:
                        await self.log_client.log_integration_call(
                            "interpreter",
                            "extract_technical_requirements",
                            True,
                            duration_ms
                        )
                    
                    return result
                else:
                    return {
                        "error": f"Failed with status {response.status_code}",
                        "requirements": [],
                        "technologies": [],
                        "dependencies": []
                    }
                    
        except Exception as e:
            return {
                "error": str(e),
                "requirements": [],
                "technologies": [],
                "dependencies": []
            }

