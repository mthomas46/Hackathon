"""
PM Integration - Phase 5
Integrates with PM tools (Jira, Linear, Asana) for bidirectional sync.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from abc import ABC, abstractmethod

from .report_generator import ComprehensiveReport


class PMTool(Enum):
    """Supported PM tools."""
    JIRA = "jira"
    LINEAR = "linear"
    ASANA = "asana"


class PMIntegrator(ABC):
    """Abstract base class for PM tool integrators."""
    
    @abstractmethod
    async def sync_report(
        self,
        report: ComprehensiveReport,
        project_key: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Sync report to PM tool."""
        pass
    
    @abstractmethod
    async def create_epic(self, title: str, description: str) -> str:
        """Create epic/feature in PM tool."""
        pass
    
    @abstractmethod
    async def create_story(self, epic_id: str, story_data: Dict[str, Any]) -> str:
        """Create user story/issue in PM tool."""
        pass


class JiraIntegrator(PMIntegrator):
    """Jira integration (placeholder for actual implementation)."""
    
    def __init__(self, api_url: str, api_token: str):
        self.api_url = api_url
        self.api_token = api_token
    
    async def sync_report(
        self,
        report: ComprehensiveReport,
        project_key: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Sync report to Jira."""
        # Placeholder implementation
        return {
            "tool": "jira",
            "project_key": project_key,
            "status": "success",
            "epics_created": 0,
            "stories_created": 0,
            "message": "Jira sync placeholder - requires actual API integration"
        }
    
    async def create_epic(self, title: str, description: str) -> str:
        return f"EPIC-{hash(title) % 10000}"
    
    async def create_story(self, epic_id: str, story_data: Dict[str, Any]) -> str:
        return f"STORY-{hash(str(story_data)) % 10000}"


class LinearIntegrator(PMIntegrator):
    """Linear integration (placeholder)."""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
    
    async def sync_report(
        self,
        report: ComprehensiveReport,
        project_key: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {
            "tool": "linear",
            "project_key": project_key,
            "status": "success",
            "message": "Linear sync placeholder - requires actual API integration"
        }
    
    async def create_epic(self, title: str, description: str) -> str:
        return f"LIN-{hash(title) % 10000}"
    
    async def create_story(self, epic_id: str, story_data: Dict[str, Any]) -> str:
        return f"LIN-{hash(str(story_data)) % 10000}"


class AsanaIntegrator(PMIntegrator):
    """Asana integration (placeholder)."""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
    
    async def sync_report(
        self,
        report: ComprehensiveReport,
        project_key: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {
            "tool": "asana",
            "project_key": project_key,
            "status": "success",
            "message": "Asana sync placeholder - requires actual API integration"
        }
    
    async def create_epic(self, title: str, description: str) -> str:
        return f"ASA-{hash(title) % 10000}"
    
    async def create_story(self, epic_id: str, story_data: Dict[str, Any]) -> str:
        return f"ASA-{hash(str(story_data)) % 10000}"


class PMIntegratorFactory:
    """Factory for creating PM integrators."""
    
    @staticmethod
    def create_integrator(
        tool: PMTool,
        credentials: Dict[str, str]
    ) -> PMIntegrator:
        """Create integrator for specified PM tool."""
        if tool == PMTool.JIRA:
            return JiraIntegrator(
                api_url=credentials.get("api_url", ""),
                api_token=credentials.get("api_token", "")
            )
        elif tool == PMTool.LINEAR:
            return LinearIntegrator(
                api_token=credentials.get("api_token", "")
            )
        elif tool == PMTool.ASANA:
            return AsanaIntegrator(
                api_token=credentials.get("api_token", "")
            )
        else:
            raise ValueError(f"Unsupported PM tool: {tool}")

