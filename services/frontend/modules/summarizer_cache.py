"""Caching infrastructure for Summarizer Hub data.

Provides in-memory caching for summarizer hub job history, prompts, and models
to enable visualization and monitoring of summarizer processes.
"""
from typing import Dict, Any, List, Optional
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

from services.shared.utilities import utc_now


@dataclass
class SummarizerJob:
    """Represents a summarizer hub job execution."""

    job_id: str
    timestamp: datetime
    text_length: int
    providers: List[str]
    models: Dict[str, str]
    prompt: Optional[str] = None
    execution_time: Optional[float] = None
    status: str = "completed"
    results: Optional[Dict[str, Any]] = None
    consistency_analysis: Optional[Dict[str, Any]] = None


@dataclass
class SummarizerCache:
    """In-memory cache for summarizer hub data."""

    # Job history - keep last 100 jobs
    job_history: List[SummarizerJob] = field(default_factory=list)

    # Current active prompts and their usage
    active_prompts: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Model usage statistics
    model_usage: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Provider configurations and their models
    provider_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Performance metrics
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

    # Cache timestamps for invalidation
    last_updated: datetime = field(default_factory=utc_now)

    def add_job(self, job: SummarizerJob) -> None:
        """Add a new job to the history cache."""
        self.job_history.insert(0, job)  # Add to front for chronological order

        # Keep only the last 100 jobs
        if len(self.job_history) > 100:
            self.job_history = self.job_history[:100]

        self.last_updated = utc_now()

    def update_prompt_usage(self, prompt: str, provider: str, model: str) -> None:
        """Update prompt usage statistics."""
        prompt_hash = hash(prompt)
        if prompt_hash not in self.active_prompts:
            self.active_prompts[prompt_hash] = {
                "text": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                "usage_count": 0,
                "providers": set(),
                "models": set(),
                "last_used": utc_now()
            }

        self.active_prompts[prompt_hash]["usage_count"] += 1
        self.active_prompts[prompt_hash]["providers"].add(provider)
        self.active_prompts[prompt_hash]["models"].add(model)
        self.active_prompts[prompt_hash]["last_used"] = utc_now()

    def update_model_usage(self, provider: str, model: str, execution_time: float) -> None:
        """Update model usage statistics."""
        key = f"{provider}:{model}"
        if key not in self.model_usage:
            self.model_usage[key] = {
                "provider": provider,
                "model": model,
                "usage_count": 0,
                "total_execution_time": 0.0,
                "average_execution_time": 0.0,
                "last_used": utc_now()
            }

        stats = self.model_usage[key]
        stats["usage_count"] += 1
        stats["total_execution_time"] += execution_time
        stats["average_execution_time"] = stats["total_execution_time"] / stats["usage_count"]
        stats["last_used"] = utc_now()

    def update_provider_config(self, provider: str, config: Dict[str, Any]) -> None:
        """Update provider configuration cache."""
        self.provider_configs[provider] = {
            **config,
            "last_updated": utc_now()
        }

    def get_recent_jobs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent jobs as dictionaries."""
        return [
            {
                "job_id": job.job_id,
                "timestamp": job.timestamp.isoformat(),
                "text_length": job.text_length,
                "providers": job.providers,
                "models": job.models,
                "prompt": job.prompt,
                "execution_time": job.execution_time,
                "status": job.status,
                "results": job.results,
                "consistency_analysis": job.consistency_analysis
            }
            for job in self.job_history[:limit]
        ]

    def get_prompts_summary(self) -> List[Dict[str, Any]]:
        """Get summary of active prompts."""
        return [
            {
                "text": data["text"],
                "usage_count": data["usage_count"],
                "providers": list(data["providers"]),
                "models": list(data["models"]),
                "last_used": data["last_used"].isoformat()
            }
            for data in self.active_prompts.values()
        ]

    def get_models_summary(self) -> List[Dict[str, Any]]:
        """Get summary of model usage."""
        return list(self.model_usage.values())

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.job_history:
            return {
                "total_jobs": 0,
                "average_execution_time": 0.0,
                "total_providers_used": 0,
                "most_used_provider": None
            }

        total_execution_time = sum(job.execution_time for job in self.job_history if job.execution_time)
        avg_execution_time = total_execution_time / len([j for j in self.job_history if j.execution_time]) if total_execution_time > 0 else 0

        provider_counts = {}
        for job in self.job_history:
            for provider in job.providers:
                provider_counts[provider] = provider_counts.get(provider, 0) + 1

        most_used_provider = max(provider_counts.items(), key=lambda x: x[1]) if provider_counts else None

        return {
            "total_jobs": len(self.job_history),
            "average_execution_time": round(avg_execution_time, 2),
            "total_providers_used": len(provider_counts),
            "most_used_provider": most_used_provider[0] if most_used_provider else None
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert cache to dictionary for serialization."""
        return {
            "job_history": self.get_recent_jobs(50),  # Limit for serialization
            "active_prompts": self.get_prompts_summary(),
            "model_usage": self.get_models_summary(),
            "provider_configs": self.provider_configs,
            "performance_metrics": self.get_performance_summary(),
            "last_updated": self.last_updated.isoformat()
        }


# Global cache instance
summarizer_cache = SummarizerCache()


def record_summarizer_job(
    job_id: str,
    text_length: int,
    providers: List[str],
    models: Dict[str, str],
    prompt: Optional[str] = None,
    execution_time: Optional[float] = None,
    results: Optional[Dict[str, Any]] = None,
    consistency_analysis: Optional[Dict[str, Any]] = None
) -> None:
    """Record a new summarizer job in the cache."""
    job = SummarizerJob(
        job_id=job_id,
        timestamp=utc_now(),
        text_length=text_length,
        providers=providers,
        models=models,
        prompt=prompt,
        execution_time=execution_time,
        results=results,
        consistency_analysis=consistency_analysis
    )
    summarizer_cache.add_job(job)

    # Update related caches
    if prompt:
        for provider in providers:
            model = models.get(provider, "unknown")
            summarizer_cache.update_prompt_usage(prompt, provider, model)

    if execution_time:
        for provider in providers:
            model = models.get(provider, "unknown")
            summarizer_cache.update_model_usage(provider, model, execution_time)


def get_cached_summarizer_data() -> Dict[str, Any]:
    """Get all cached summarizer data."""
    return summarizer_cache.to_dict()
