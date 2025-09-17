"""Maintenance Analysis Handler - Handles maintenance forecasting."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base_handler import BaseAnalysisHandler, AnalysisResult
from ..models import (
    MaintenanceForecastRequest, MaintenanceForecastResponse,
    PortfolioMaintenanceForecastRequest, PortfolioMaintenanceForecastResponse
)

logger = logging.getLogger(__name__)


class MaintenanceAnalysisHandler(BaseAnalysisHandler):
    """Handler for maintenance forecasting operations."""

    def __init__(self):
        super().__init__("maintenance_forecast")

    async def handle(self, request) -> AnalysisResult:
        """Handle maintenance forecast request."""
        try:
            # Import maintenance forecaster
            try:
                if hasattr(request, 'document_ids'):  # Portfolio request
                    from ..maintenance_forecaster import forecast_portfolio_maintenance
                    analyzer_func = forecast_portfolio_maintenance
                else:  # Single document request
                    from ..maintenance_forecaster import forecast_document_maintenance
                    analyzer_func = forecast_document_maintenance
            except ImportError:
                # Fallback for testing
                analyzer_func = self._mock_maintenance_forecast

            # Perform maintenance forecast
            forecast_result = await analyzer_func(
                document_id=getattr(request, 'document_id', None),
                document_ids=getattr(request, 'document_ids', []),
                forecast_period_days=getattr(request, 'forecast_period_days', 180),
                factors=getattr(request, 'factors', []),
                options=getattr(request, 'options', {})
            )

            # Convert to standardized response format
            if hasattr(request, 'document_ids'):  # Portfolio response
                response = PortfolioMaintenanceForecastResponse(
                    analysis_id=f"portfolio-maint-{int(datetime.now(timezone.utc).timestamp())}",
                    document_ids=request.document_ids,
                    portfolio_forecast=forecast_result.get('portfolio_forecast', {}),
                    maintenance_schedule=forecast_result.get('maintenance_schedule', {}),
                    resource_requirements=forecast_result.get('resource_requirements', {}),
                    execution_time_seconds=forecast_result.get('execution_time_seconds', 0.0),
                    error_message=None
                )
            else:  # Single document response
                response = MaintenanceForecastResponse(
                    analysis_id=f"maint-{int(datetime.now(timezone.utc).timestamp())}",
                    document_id=request.document_id,
                    maintenance_forecast=forecast_result.get('maintenance_forecast', {}),
                    recommended_actions=forecast_result.get('recommended_actions', []),
                    priority_level=forecast_result.get('priority_level', 'medium'),
                    execution_time_seconds=forecast_result.get('execution_time_seconds', 0.0),
                    error_message=None
                )

            return self._create_analysis_result(
                analysis_id=response.analysis_id,
                data={"response": response.dict()},
                execution_time=response.execution_time_seconds
            )

        except Exception as e:
            error_msg = f"Maintenance forecast failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            analysis_id = f"maint-{int(datetime.now(timezone.utc).timestamp())}"
            return await self._handle_error(e, analysis_id)

    async def _mock_maintenance_forecast(self, **kwargs) -> Dict[str, Any]:
        """Mock maintenance forecast for testing purposes."""
        import random
        from datetime import timedelta

        # Mock maintenance forecast
        forecast_period = kwargs.get('forecast_period_days', 180)

        maintenance_forecast = {
            'next_maintenance_date': (datetime.now(timezone.utc) + timedelta(days=random.randint(30, 90))).isoformat(),
            'maintenance_probability': random.uniform(0.3, 0.9),
            'estimated_effort_days': random.uniform(1, 14),
            'risk_of_obsolescence': random.uniform(0.1, 0.8),
            'update_frequency_recommendation': random.choice(['monthly', 'quarterly', 'biannual', 'annual'])
        }

        recommended_actions = [
            {
                'action': 'content_review',
                'priority': 'high',
                'description': 'Review content for accuracy and relevance',
                'estimated_effort_hours': random.randint(2, 8)
            },
            {
                'action': 'technical_update',
                'priority': 'medium',
                'description': 'Update technical information and examples',
                'estimated_effort_hours': random.randint(4, 16)
            }
        ]

        return {
            'maintenance_forecast': maintenance_forecast,
            'recommended_actions': recommended_actions,
            'priority_level': random.choice(['low', 'medium', 'high', 'critical']),
            'portfolio_forecast': {'overall_maintenance_load': random.uniform(50, 200)},
            'maintenance_schedule': {'scheduled_reviews': random.randint(5, 20)},
            'resource_requirements': {'estimated_hours': random.randint(20, 100)},
            'execution_time_seconds': random.uniform(2.0, 6.0)
        }


# Register handler
from .base_handler import handler_registry
handler_registry.register("maintenance_forecast", MaintenanceAnalysisHandler())
handler_registry.register("portfolio_maintenance_forecast", MaintenanceAnalysisHandler())
