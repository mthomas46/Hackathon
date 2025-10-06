"""Celery application for MCP workers."""

import os
from celery import Celery

# Celery configuration
broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/8")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/8")

# Create Celery app
app = Celery(
    "mcp_workers",
    broker=broker_url,
    backend=result_backend,
    include=[
        "services.workers.extractors.github_extractor",
        "services.workers.extractors.confluence_extractor",
        "services.workers.extractors.jira_extractor",
        "services.workers.normalizers.markdown_normalizer",
        "services.workers.normalizers.scope_classifier",
        "services.workers.embedders.vector_generator",
        "services.workers.embedders.auto_tagger",
        "services.workers.embedders.entity_extractor",
    ]
)

# Configure Celery
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)

if __name__ == "__main__":
    app.start()

