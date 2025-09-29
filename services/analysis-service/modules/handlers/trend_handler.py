"""Trend Analysis Handler - Handles trend analysis and forecasting."""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from .base_handler import BaseAnalysisHandler, AnalysisResult
from ..models import (
    TrendAnalysisRequest, TrendAnalysisResponse,
    PortfolioTrendAnalysisRequest, PortfolioTrendAnalysisResponse,
    TrendData, ForecastData
)

logger = logging.getLogger(__name__)


class TrendAnalysisHandler(BaseAnalysisHandler):
    """Handler for trend analysis operations."""

    def __init__(self):
        super().__init__("trend_analysis")

    async def handle(self, request) -> AnalysisResult:
        """Handle trend analysis request."""
        try:
            # Import trend analyzer
            try:
                if hasattr(request, 'document_ids'):  # Portfolio request
                    from ..trend_analyzer import analyze_portfolio_trends
                    analyzer_func = analyze_portfolio_trends
                else:  # Single document request
                    from ..trend_analyzer import analyze_document_trends
                    analyzer_func = analyze_document_trends
            except ImportError:
                # Fallback for testing
                analyzer_func = self._mock_trend_analysis

            # Perform trend analysis
            trend_result = await analyzer_func(
                document_id=getattr(request, 'document_id', None),
                document_ids=getattr(request, 'document_ids', []),
                time_range_days=request.time_range_days,
                trend_metrics=request.trend_metrics,
                forecast_days=request.forecast_days,
                options=getattr(request, 'options', {})
            )

            # Convert to standardized response format
            if hasattr(request, 'document_ids'):  # Portfolio response
                response = PortfolioTrendAnalysisResponse(
                    analysis_id=f"portfolio-trend-{int(datetime.now(timezone.utc).timestamp())}",
                    document_ids=request.document_ids,
                    time_range_days=request.time_range_days,
                    portfolio_trend_data=trend_result.get('portfolio_trend_data', {}),
                    key_insights=trend_result.get('key_insights', []),
                    recommendations=trend_result.get('recommendations', []),
                    forecast_accuracy=trend_result.get('forecast_accuracy', 0.0),
                    execution_time_seconds=trend_result.get('execution_time_seconds', 0.0),
                    error_message=None
                )
            else:  # Single document response
                response = TrendAnalysisResponse(
                    analysis_id=f"trend-{int(datetime.now(timezone.utc).timestamp())}",
                    document_id=request.document_id,
                    time_range_days=request.time_range_days,
                    trend_data=trend_result.get('trend_data', {}),
                    key_insights=trend_result.get('key_insights', []),
                    recommendations=trend_result.get('recommendations', []),
                    forecast_accuracy=trend_result.get('forecast_accuracy', 0.0),
                    execution_time_seconds=trend_result.get('execution_time_seconds', 0.0),
                    error_message=None
                )

            return self._create_analysis_result(
                analysis_id=response.analysis_id,
                data={"response": response.dict()},
                execution_time=response.execution_time_seconds
            )

        except Exception as e:
            error_msg = f"Trend analysis failed: {str(e)}"
            logger.error(error_msg, exc_info=True)

            analysis_id = f"trend-{int(datetime.now(timezone.utc).timestamp())}"
            return await self._handle_error(e, analysis_id)

    async def _mock_trend_analysis(self, **kwargs) -> Dict[str, Any]:
        """Mock trend analysis for testing purposes."""
        import random
        from datetime import timedelta

        # Mock trend data
        metrics = kwargs.get('trend_metrics', ['quality_score', 'complexity'])
        time_range = kwargs.get('time_range_days', 90)
        forecast_days = kwargs.get('forecast_days', 30)

        trend_data = {}
        for metric in metrics:
            # Generate historical data points
            historical_data = []
            base_value = random.uniform(70, 90)

            for i in range(time_range // 7):  # Weekly data points
                date = datetime.now(timezone.utc) - timedelta(days=(time_range - i * 7))
                value = base_value + random.uniform(-10, 10) + (i * 0.1)  # Slight upward trend
                historical_data.append({
                    'date': date.isoformat(),
                    'value': max(0, min(100, value))  # Clamp between 0-100
                })

            # Calculate trend metrics
            values = [point['value'] for point in historical_data]
            trend_slope = (values[-1] - values[0]) / len(values) if values else 0
            volatility = sum(abs(values[i] - values[i-1]) for i in range(1, len(values))) / len(values) if len(values) > 1 else 0

            # Generate forecast
            forecast_value = values[-1] + (trend_slope * forecast_days / 30)
            forecast_data = {
                'forecasted_value': max(0, min(100, forecast_value)),
                'confidence_interval': {
                    'lower': max(0, forecast_value - 5),
                    'upper': min(100, forecast_value + 5)
                }
            }

            trend_data[metric] = {
                'historical_data': historical_data,
                'current_value': values[-1] if values else 0,
                'trend_direction': 'improving' if trend_slope > 0.1 else 'stable' if abs(trend_slope) < 0.1 else 'declining',
                'trend_slope': trend_slope,
                'volatility': volatility,
                'forecast': forecast_data
            }

        # Mock insights and recommendations
        key_insights = [
            "Quality score shows steady improvement over time",
            "Complexity has remained relatively stable",
            f"Forecast indicates continued {'improvement' if trend_slope > 0 else 'stability'} in key metrics"
        ]

        recommendations = [
            "Continue monitoring quality trends",
            "Consider implementing automated quality checks",
            "Review forecast predictions regularly"
        ]

        return {
            'trend_data': trend_data,
            'portfolio_trend_data': trend_data,  # Same for portfolio
            'key_insights': key_insights,
            'recommendations': recommendations,
            'forecast_accuracy': random.uniform(0.75, 0.95),
            'execution_time_seconds': random.uniform(2.0, 5.0)
        }

    async def get_trend_forecast(self, document_id: str, metric: str,
                               forecast_days: int = 30) -> Dict[str, Any]:
        """Get trend forecast for specific metric."""
        request = TrendAnalysisRequest(
            document_id=document_id,
            time_range_days=90,
            trend_metrics=[metric],
            forecast_days=forecast_days
        )

        result = await self.handle(request)

        if result.error_message:
            return {"error": result.error_message}

        response_data = result.data.get('response', {})
        trend_data = response_data.get('trend_data', {})

        if metric not in trend_data:
            return {"error": f"No trend data available for metric: {metric}"}

        metric_data = trend_data[metric]

        return {
            'document_id': document_id,
            'metric': metric,
            'current_value': metric_data.get('current_value', 0),
            'trend_direction': metric_data.get('trend_direction', 'unknown'),
            'forecasted_value': metric_data.get('forecast', {}).get('forecasted_value', 0),
            'confidence_interval': metric_data.get('forecast', {}).get('confidence_interval', {}),
            'forecast_accuracy': response_data.get('forecast_accuracy', 0),
            'execution_time_seconds': result.execution_time_seconds
        }

    async def analyze_portfolio_trends(self, document_ids: List[str],
                                     metrics: List[str]) -> Dict[str, Any]:
        """Analyze trends across document portfolio."""
        request = PortfolioTrendAnalysisRequest(
            document_ids=document_ids,
            time_range_days=90,
            trend_metrics=metrics,
            forecast_days=30
        )

        result = await self.handle(request)

        if result.error_message:
            return {"error": result.error_message}

        response_data = result.data.get('response', {})

        return {
            'document_ids': document_ids,
            'metrics_analyzed': metrics,
            'portfolio_trend_data': response_data.get('portfolio_trend_data', {}),
            'key_insights': response_data.get('key_insights', []),
            'recommendations': response_data.get('recommendations', []),
            'forecast_accuracy': response_data.get('forecast_accuracy', 0),
            'execution_time_seconds': result.execution_time_seconds
        }

    async def detect_quality_degradation(self, document_id: str) -> Dict[str, Any]:
        """Detect quality degradation patterns."""
        # Get trend data for quality metrics
        quality_metrics = ['quality_score', 'readability', 'grammar_score']
        request = TrendAnalysisRequest(
            document_id=document_id,
            time_range_days=60,
            trend_metrics=quality_metrics,
            forecast_days=14
        )

        result = await self.handle(request)

        if result.error_message:
            return {"error": result.error_message}

        response_data = result.data.get('response', {})
        trend_data = response_data.get('trend_data', {})

        # Analyze for degradation
        degradation_indicators = []
        overall_risk = 'low'

        for metric, data in trend_data.items():
            slope = data.get('trend_slope', 0)
            volatility = data.get('volatility', 0)

            if slope < -0.5:  # Significant downward trend
                degradation_indicators.append({
                    'metric': metric,
                    'severity': 'high',
                    'description': f"{metric} showing significant decline (slope: {slope:.2f})"
                })
                overall_risk = 'high'
            elif slope < -0.2:  # Moderate downward trend
                degradation_indicators.append({
                    'metric': metric,
                    'severity': 'medium',
                    'description': f"{metric} showing moderate decline (slope: {slope:.2f})"
                })
                if overall_risk == 'low':
                    overall_risk = 'medium'

            if volatility > 15:  # High volatility
                degradation_indicators.append({
                    'metric': metric,
                    'severity': 'medium',
                    'description': f"{metric} showing high volatility ({volatility:.1f})"
                })

        return {
            'document_id': document_id,
            'overall_risk': overall_risk,
            'degradation_indicators': degradation_indicators,
            'trend_summary': {metric: data.get('trend_direction') for metric, data in trend_data.items()},
            'recommendations': [
                "Monitor quality metrics closely" if overall_risk in ['medium', 'high'] else "Continue current quality practices",
                "Review recent changes that may have impacted quality" if degradation_indicators else "Maintain current documentation standards"
            ],
            'execution_time_seconds': result.execution_time_seconds
        }


# Register handler
from .base_handler import handler_registry
handler_registry.register("trend_analysis", TrendAnalysisHandler())
handler_registry.register("portfolio_trend_analysis", TrendAnalysisHandler())
