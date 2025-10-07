"""Training Coordinator integration client - TIGHT COUPLING."""

import httpx
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio


class TrainingClient:
    """
    Tightly integrated client for Training Coordinator service.
    
    Provides seamless dashboard integration for:
    - Job creation and management
    - Real-time progress tracking
    - Worker status monitoring
    - Training analytics
    """
    
    def __init__(self, base_url: str = "http://mcp-training-coordinator:5600"):
        """
        Initialize Training Coordinator client.
        
        Args:
            base_url: Training Coordinator service URL
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def create_job(
        self,
        mcp_id: str,
        data_sources: List[str],
        priority: str = "MEDIUM",
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new training job from the dashboard.
        
        Args:
            mcp_id: MCP instance ID
            data_sources: List of data sources (GITHUB, CONFLUENCE, etc.)
            priority: Job priority (CRITICAL, HIGH, MEDIUM, LOW, DEFERRED)
            config: Source-specific configuration
        
        Returns:
            Job details with job_id
        """
        payload = {
            "mcp_id": mcp_id,
            "data_sources": data_sources,
            "priority": priority,
            "config": config or {}
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/jobs",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_job(self, job_id: str) -> Dict[str, Any]:
        """
        Get job details with current status.
        
        Args:
            job_id: Job ID
        
        Returns:
            Job details including status, progress, etc.
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/jobs/{job_id}"
        )
        response.raise_for_status()
        return response.json()
    
    async def list_jobs(
        self,
        status: Optional[str] = None,
        mcp_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List training jobs with optional filtering.
        
        Args:
            status: Filter by status (PENDING, EXECUTING, COMPLETED, FAILED)
            mcp_id: Filter by MCP ID
            limit: Max results
        
        Returns:
            List of jobs
        """
        params = {"limit": limit}
        if status:
            params["status"] = status
        if mcp_id:
            params["mcp_id"] = mcp_id
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/jobs",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def execute_job(self, job_id: str) -> Dict[str, Any]:
        """
        Execute a training job.
        
        Args:
            job_id: Job ID
        
        Returns:
            Execution status
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/jobs/{job_id}/execute"
        )
        response.raise_for_status()
        return response.json()
    
    async def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a running job.
        
        Args:
            job_id: Job ID
        
        Returns:
            Cancellation status
        """
        response = await self.client.delete(
            f"{self.base_url}/api/v1/jobs/{job_id}"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_job_progress(self, job_id: str) -> Dict[str, Any]:
        """
        Get real-time job progress (for progress bars).
        
        Args:
            job_id: Job ID
        
        Returns:
            Progress details {percent: 0-100, stage: str, message: str}
        """
        job = await self.get_job(job_id)
        
        # Calculate progress based on stage
        stage_progress = {
            "PENDING": 0,
            "VALIDATING": 10,
            "EXTRACTING": 30,
            "NORMALIZING": 50,
            "EMBEDDING": 70,
            "STORING": 85,
            "VALIDATING_RESULTS": 95,
            "COMPLETED": 100,
            "FAILED": 0
        }
        
        status = job.get("status", "PENDING")
        percent = stage_progress.get(status, 0)
        
        return {
            "job_id": job_id,
            "percent": percent,
            "stage": status,
            "message": job.get("message", ""),
            "updated_at": job.get("updated_at")
        }
    
    async def get_worker_status(self) -> Dict[str, Any]:
        """
        Get status of all workers (for worker grid display).
        
        Returns:
            Worker status by type
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/workers"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_job_analytics(
        self,
        mcp_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get training analytics for dashboard charts.
        
        Args:
            mcp_id: Optional MCP ID filter
            days: Number of days to analyze
        
        Returns:
            Analytics data
        """
        params = {"days": days}
        if mcp_id:
            params["mcp_id"] = mcp_id
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/analytics",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def stream_job_logs(self, job_id: str):
        """
        Stream job logs in real-time (for log viewer).
        
        Args:
            job_id: Job ID
        
        Yields:
            Log lines as they're generated
        """
        async with self.client.stream(
            "GET",
            f"{self.base_url}/api/v1/jobs/{job_id}/logs"
        ) as response:
            async for line in response.aiter_lines():
                yield line
    
    async def get_data_source_config(self, source: str) -> Dict[str, Any]:
        """
        Get configuration schema for a data source.
        
        Args:
            source: Data source name (GITHUB, CONFLUENCE, etc.)
        
        Returns:
            Configuration schema for UI form generation
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/sources/{source}/config"
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

