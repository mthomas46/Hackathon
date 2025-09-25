"""Service: Analysis Service

Endpoints:
- POST /analyze: Analyze documents for consistency and issues with configurable detectors
- POST /analyze/semantic-similarity: Analyze semantic similarity between documents using embeddings
- POST /analyze/sentiment: Analyze sentiment, tone, and clarity of documentation
- POST /analyze/tone: Analyze tone patterns and writing style in documents
- POST /analyze/quality: Analyze content quality with comprehensive assessment and recommendations
- POST /analyze/trends: Analyze trends and predict future issues for a document
- POST /analyze/trends/portfolio: Analyze trends across a portfolio of documents
- POST /analyze/risk: Assess risk factors for documentation drift and quality degradation
- POST /analyze/risk/portfolio: Assess risks across a portfolio of documents
- POST /analyze/maintenance/forecast: Forecast maintenance needs and schedule for documentation
- POST /analyze/maintenance/forecast/portfolio: Forecast maintenance needs across a portfolio of documents
- POST /analyze/quality/degradation: Detect quality degradation in documentation over time
- POST /analyze/quality/degradation/portfolio: Monitor quality degradation across a portfolio of documents
- POST /analyze/change/impact: Analyze the impact of changes to documentation on related content
- POST /analyze/change/impact/portfolio: Analyze the impact of changes across a document portfolio
- POST /remediate: Apply automated fixes to documentation issues
- POST /remediate/preview: Preview automated remediation changes without applying them
- POST /workflows/events: Process workflow events and trigger appropriate analyses
- GET /workflows/{workflow_id}: Get the status of a workflow analysis
- GET /workflows/queue/status: Get the status of workflow analysis queues
- POST /workflows/webhook/config: Configure webhook settings for workflow integration
- POST /repositories/analyze: Analyze documentation across multiple repositories
- POST /repositories/connectivity: Analyze connectivity and dependencies between repositories
- POST /repositories/connectors/config: Configure repository connectors for external systems
- GET /repositories/connectors: Get list of supported repository connectors
- GET /repositories/frameworks: Get available cross-repository analysis frameworks
- POST /distributed/tasks: Submit a task for distributed processing
- POST /distributed/tasks/batch: Submit multiple tasks for batch distributed processing
- GET /distributed/tasks/{task_id}: Get the status of a distributed task
- DELETE /distributed/tasks/{task_id}: Cancel a distributed task
- GET /distributed/workers: Get status of all distributed processing workers
- GET /distributed/stats: Get distributed processing statistics
- POST /distributed/workers/scale: Scale the number of distributed processing workers
- POST /distributed/start: Start the distributed processing system
- PUT /distributed/load-balancing/strategy: Configure load balancing strategy
- GET /distributed/queue/status: Get detailed status of the distributed processing queue
- PUT /distributed/load-balancing/config: Configure comprehensive load balancing settings
- GET /distributed/load-balancing/config: Get current load balancing configuration
- GET /findings: Retrieve analysis findings with filtering by severity and type
- GET /detectors: List available analysis detectors and their capabilities
- POST /reports/generate: Generate various types of reports (summary, trends, etc.)
- GET /reports/confluence/consolidation: Analyze Confluence pages for duplicates and consolidation opportunities
- GET /reports/jira/staleness: Identify stale Jira tickets requiring review or closure
- POST /reports/findings/notify-owners: Send notifications for findings to document owners
- GET /integration/health: Check integration health with other services
- POST /integration/analyze-with-prompt: Analyze using prompts from Prompt Store
- POST /integration/natural-language-analysis: Analyze using natural language queries
- GET /integration/prompts/categories: Get available prompt categories
- POST /integration/log-analysis: Log analysis usage for analytics

Responsibilities:
- Perform document consistency analysis and issue detection
- Analyze semantic similarity between documents using embeddings
- Analyze sentiment, tone, and clarity of documentation
- Assess readability and communication effectiveness
- Evaluate content quality with comprehensive scoring and recommendations
- Provide automated quality assessment for documentation improvement
- Analyze trends and predict future documentation issues
- Perform portfolio-wide trend analysis across multiple documents
- Assess risk factors for documentation drift and quality degradation
- Perform portfolio-wide risk assessment across multiple documents
- Identify high-risk areas requiring immediate attention
- Generate actionable recommendations for risk mitigation
- Forecast maintenance needs and schedule for documentation
- Perform portfolio-wide maintenance forecasting across multiple documents
- Predict when documentation will need updates based on multiple factors
- Generate maintenance schedules and resource planning recommendations
- Detect quality degradation in documentation over time
- Monitor quality degradation across portfolio of documents
- Generate alerts for quality degradation patterns
- Provide analysis of degradation causes and trends
- Analyze the impact of changes to documentation on related content
- Perform portfolio-wide change impact analysis across multiple documents
- Identify affected stakeholders and dependent systems
- Generate change management recommendations and risk mitigation strategies
- Apply automated fixes to common documentation issues
- Preview remediation changes before applying them
- Ensure safety and rollback capabilities for automated changes
- Fix formatting inconsistencies, grammar errors, and terminology issues
- Generate comprehensive remediation reports and recommendations
- Process workflow events and trigger appropriate analyses
- Support webhook integrations for GitHub, GitLab, and CI/CD systems
- Provide intelligent analysis queuing and prioritization
- Monitor workflow analysis status and queue management
- Generate workflow-triggered analysis reports and notifications
- Analyze documentation across multiple repositories
- Identify patterns, inconsistencies, and redundancies across repository ecosystem
- Assess documentation coverage and quality at organizational level
- Analyze repository connectivity and cross-references
- Configure repository connectors for external systems
- Generate cross-repository analysis reports and recommendations
- Process analysis tasks in parallel across multiple workers
- Submit and manage distributed processing tasks
- Scale worker pools dynamically based on workload demands
- Monitor distributed processing performance and throughput
- Handle task queuing, prioritization, and load balancing
- Implement intelligent load balancing strategies (round-robin, least-loaded, performance-based, adaptive)
- Configure and optimize load balancing algorithms for different workload patterns
- Monitor queue efficiency and processing rates
- Generate reports on documentation quality and trends
- Identify duplicate content and consolidation opportunities
- Monitor Jira ticket staleness and maintenance needs
- Provide natural language analysis capabilities
- Integrate with Prompt Store for customizable analysis
- Support cross-service coordination and health monitoring

Dependencies: Document Store, Prompt Store, Interpreter, Source Agent, Orchestrator.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException
from services.shared.infrastructure.config import load_service_config

# ============================================================================
# SHARED MODULES - Optimized import consolidation for consistency
# ============================================================================
from services.shared.monitoring.health import register_health_endpoints
from services.shared.monitoring.logging import fire_and_forget
from services.shared.presentation.responses import (
    create_error_response,
    create_success_response,
)
from services.shared.utilities.error_handling import install_error_handlers
from services.shared.utilities.utilities import (
    attach_self_register,
    get_service_client,
    setup_common_middleware,
)

try:
    import redis.asyncio as aioredis
except Exception:
    aioredis = None


# Create shared client instance for all analysis operations
service_client = get_service_client(timeout=30)

# Load standardized configuration
config = load_service_config(
    service_type="analysis-service",
    config_file="./config.yaml",  # Optional config file override
)

# Service configuration from standardized config
SERVICE_NAME = config.service_name
SERVICE_TITLE = config.service_description or "Analysis Service"
SERVICE_VERSION = config.service_version
DEFAULT_PORT = config.port

# ============================================================================
# HANDLER MODULES - Extracted business logic
# ============================================================================
try:
    # Try relative imports first (when run as module)
    from .modules.analysis_handlers import analysis_handlers
    from .modules.integration_handlers import integration_handlers
    from .modules.models import (
        AnalysisRequest,
        ArchitectureAnalysisRequest,
        AutomatedRemediationRequest,
        BatchTasksRequest,
        CancelTaskRequest,
        ChangeImpactAnalysisRequest,
        ContentQualityRequest,
        CrossRepositoryAnalysisRequest,
        DistributedTaskRequest,
        DocumentDumpRequest,
        LoadBalancingConfigRequest,
        LoadBalancingStrategyRequest,
        MaintenanceForecastRequest,
        NotifyOwnersRequest,
        PortfolioChangeImpactRequest,
        PortfolioMaintenanceForecastRequest,
        PortfolioQualityDegradationRequest,
        PortfolioRiskAssessmentRequest,
        PortfolioTrendAnalysisRequest,
        QualityDegradationDetectionRequest,
        RemediationPreviewRequest,
        ReportRequest,
        RepositoryConnectivityRequest,
        RepositoryConnectorConfigRequest,
        RiskAssessmentRequest,
        ScaleWorkersRequest,
        SemanticSimilarityRequest,
        SentimentAnalysisRequest,
        TaskStatusRequest,
        ToneAnalysisRequest,
        TrendAnalysisRequest,
        WebhookConfigRequest,
        WorkflowEventRequest,
    )
    from .modules.report_handlers import report_handlers
except ImportError:
    # Fallback to absolute imports (when run as script)
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from modules.analysis_handlers import analysis_handlers
    from modules.integration_handlers import integration_handlers
    from modules.models import (
        AnalysisRequest,
        ArchitectureAnalysisRequest,
        AutomatedRemediationRequest,
        BatchTasksRequest,
        CancelTaskRequest,
        ChangeImpactAnalysisRequest,
        ContentQualityRequest,
        CrossRepositoryAnalysisRequest,
        DistributedTaskRequest,
        DocumentDumpRequest,
        LoadBalancingConfigRequest,
        LoadBalancingStrategyRequest,
        MaintenanceForecastRequest,
        NotifyOwnersRequest,
        PortfolioChangeImpactRequest,
        PortfolioMaintenanceForecastRequest,
        PortfolioQualityDegradationRequest,
        PortfolioRiskAssessmentRequest,
        PortfolioTrendAnalysisRequest,
        QualityDegradationDetectionRequest,
        RemediationPreviewRequest,
        ReportRequest,
        RepositoryConnectivityRequest,
        RepositoryConnectorConfigRequest,
        RiskAssessmentRequest,
        ScaleWorkersRequest,
        SemanticSimilarityRequest,
        SentimentAnalysisRequest,
        TaskStatusRequest,
        ToneAnalysisRequest,
        TrendAnalysisRequest,
        WebhookConfigRequest,
        WorkflowEventRequest,
    )
    from modules.report_handlers import report_handlers

# ============================================================================
# ROUTER REGISTRATION
# ============================================================================
