"""Request and response models for Interpreter service.

Contains all Pydantic models used for API requests and responses.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class UserQuery(BaseModel):
    """User query model."""
    query: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class InterpretedIntent(BaseModel):
    """Interpreted intent from user query."""
    intent: str
    confidence: float
    entities: Dict[str, Any]
    workflow: Optional[Dict[str, Any]] = None
    response_text: str = ""


class WorkflowStep(BaseModel):
    """Workflow step definition."""
    step_id: str
    service: str
    action: str
    parameters: Dict[str, Any]
    dependencies: List[str] = []


class InterpretedWorkflow(BaseModel):
    """Complete interpreted workflow."""
    workflow_id: str
    steps: List[WorkflowStep]
    estimated_duration: int  # seconds
    required_services: List[str]
