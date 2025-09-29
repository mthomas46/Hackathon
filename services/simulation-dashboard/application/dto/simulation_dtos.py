"""Simulation DTOs.

Data Transfer Objects for simulation API requests and responses.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class CreateSimulationRequest(BaseModel):
    """Request DTO for creating a simulation."""

    name: str = Field(..., description="Simulation name", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Simulation description", max_length=1000)
    simulation_type: str = Field("standard", description="Type of simulation")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Simulation parameters")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class UpdateSimulationRequest(BaseModel):
    """Request DTO for updating a simulation."""

    name: Optional[str] = Field(None, description="Simulation name", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Simulation description", max_length=1000)
    parameters: Optional[Dict[str, Any]] = Field(None, description="Simulation parameters to update")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata to update")


class SimulationResponse(BaseModel):
    """Response DTO for simulation data."""

    id: str = Field(..., description="Simulation unique identifier")
    name: str = Field(..., description="Simulation name")
    description: Optional[str] = Field(None, description="Simulation description")
    simulation_type: str = Field(..., description="Type of simulation")
    status: str = Field(..., description="Current simulation status")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Simulation parameters")
    user_id: Optional[str] = Field(None, description="User who created the simulation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    progress: Optional[float] = Field(None, description="Simulation progress (0-100)")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


class SimulationListResponse(BaseModel):
    """Response DTO for simulation list."""

    simulations: List[SimulationResponse] = Field(..., description="List of simulations")
    total: int = Field(..., description="Total number of simulations")
    limit: int = Field(..., description="Requested limit")
    offset: int = Field(..., description="Requested offset")


class SimulationProgressResponse(BaseModel):
    """Response DTO for simulation progress."""

    simulation_id: str = Field(..., description="Simulation identifier")
    status: str = Field(..., description="Current status")
    progress: float = Field(..., description="Progress percentage (0-100)", ge=0, le=100)
    current_step: Optional[str] = Field(None, description="Current execution step")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    logs: Optional[List[Dict[str, Any]]] = Field(None, description="Execution logs (if requested)")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")


class StartSimulationRequest(BaseModel):
    """Request DTO for starting a simulation."""

    execution_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Runtime execution parameters")


class StopSimulationRequest(BaseModel):
    """Request DTO for stopping a simulation."""

    reason: Optional[str] = Field(None, description="Reason for stopping the simulation", max_length=500)
