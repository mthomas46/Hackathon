"""Trend Analysis module for Analysis Service.

Provides predictive analytics for documentation quality trends, identifying patterns
in historical analysis results and forecasting future documentation issues.
"""

import logging
import time
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List

try:
    import warnings

    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller

    warnings.filterwarnings("ignore")
    TREND_ANALYSIS_AVAILABLE = True
except ImportError:
    TREND_ANALYSIS_AVAILABLE = False
    pd = None
    np = None
    LinearRegression = None
    RandomForestRegressor = None
    StandardScaler = None
    ARIMA = None
    adfuller = None
    seasonal_decompose = None


logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyzes trends in documentation analysis results and predicts future issues."""

    def __init__(self):
        """Initialize the trend analyzer."""
        self.initialized = False
        self._initialize_analyzer()

    def _initialize_analyzer(self) -> bool:
        """Initialize the trend analysis components."""
        if not TREND_ANALYSIS_AVAILABLE:
            logger.warning("Trend analysis dependencies not available")
            return False

        self.initialized = True
        return True

    def _extract_historical_data(self, analysis_results: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract and structure historical analysis data for trend analysis."""
        if not analysis_results:
            return pd.DataFrame()

        # Extract relevant metrics from analysis results
        historical_data = []

        for result in analysis_results:
            if "timestamp" not in result:
                continue

            timestamp = pd.to_datetime(result.get("timestamp", result.get("analysis_timestamp", datetime.now())))
            if pd.isna(timestamp):
                continue

            # Extract key metrics
            record = {
                "timestamp": timestamp,
                "document_id": result.get("document_id", "unknown"),
                "total_findings": result.get("total_findings", 0),
                "critical_findings": result.get("critical_findings", 0),
                "high_findings": result.get("high_findings", 0),
                "medium_findings": result.get("medium_findings", 0),
                "low_findings": result.get("low_findings", 0),
                "quality_score": result.get("quality_score", 0.0),
                "readability_score": result.get("readability_score", 0.0),
                "sentiment_score": result.get("sentiment_score", 0.0),
                "consistency_score": result.get("consistency_score", 0.0),
            }

            # Extract finding types if available
            findings = result.get("findings", [])
            finding_types = Counter(f.get("type", "unknown") for f in findings)
            for finding_type, count in finding_types.items():
                record[f"finding_type_{finding_type}"] = count

            historical_data.append(record)

        if not historical_data:
            return pd.DataFrame()

        # Create DataFrame and set timestamp as index
        df = pd.DataFrame(historical_data)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp").sort_index()

        return df

    def _analyze_trend_patterns(self, df: pd.DataFrame, window_days: int = 30) -> Dict[str, Any]:
        """Analyze trend patterns in the historical data."""
        if df.empty:
            return {
                "trend_direction": "insufficient_data",
                "confidence": 0.0,
                "patterns": [],
                "volatility": 0.0,
            }

        patterns = {}

        # Analyze quality score trends
        if "quality_score" in df.columns:
            quality_scores = df["quality_score"].dropna()
            if len(quality_scores) >= 2:
                # Calculate trend using linear regression
                X = np.arange(len(quality_scores)).reshape(-1, 1)
                y = quality_scores.values

                if len(X) > 1:
                    model = LinearRegression()
                    model.fit(X, y)

                    trend_slope = model.coef_[0]
                    r_squared = model.score(X, y)

                    if trend_slope > 0.001:
                        trend_direction = "improving"
                    elif trend_slope < -0.001:
                        trend_direction = "declining"
                    else:
                        trend_direction = "stable"

                    patterns["quality_trend"] = {
                        "direction": trend_direction,
                        "slope": float(trend_slope),
                        "r_squared": float(r_squared),
                        "confidence": min(float(r_squared), 1.0),
                    }

        # Analyze finding trends
        finding_columns = [col for col in df.columns if col.startswith("finding_type_")]
        for finding_col in finding_columns:
            finding_data = df[finding_col].dropna()
            if len(finding_data) >= 2:
                X = np.arange(len(finding_data)).reshape(-1, 1)
                y = finding_data.values

                model = LinearRegression()
                model.fit(X, y)

                trend_slope = model.coef_[0]
                if abs(trend_slope) > 0.01:  # Significant trend
                    finding_type = finding_col.replace("finding_type_", "")
                    patterns[f"{finding_type}_trend"] = {
                        "direction": "increasing" if trend_slope > 0 else "decreasing",
                        "slope": float(trend_slope),
                        "avg_count": float(finding_data.mean()),
                    }

        # Calculate overall volatility
        if "quality_score" in df.columns:
            quality_scores = df["quality_score"].dropna()
            if len(quality_scores) > 1:
                volatility = float(quality_scores.std())
            else:
                volatility = 0.0
        else:
            volatility = 0.0

        # Determine overall trend direction
        if patterns.get("quality_trend", {}).get("direction") == "improving":
            overall_direction = "improving"
        elif patterns.get("quality_trend", {}).get("direction") == "declining":
            overall_direction = "declining"
        else:
            overall_direction = "stable"

        confidence = patterns.get("quality_trend", {}).get("confidence", 0.0)

        return {
            "trend_direction": overall_direction,
            "confidence": confidence,
            "patterns": patterns,
            "volatility": volatility,
            "data_points": len(df),
        }

    def _predict_future_issues(self, df: pd.DataFrame, prediction_days: int = 30) -> Dict[str, Any]:
        """Predict future documentation issues using time series analysis."""
        predictions = {}

        if df.empty or len(df) < 3:
            return {
                "predictions": {},
                "confidence": 0.0,
                "message": "Insufficient historical data for predictions",
            }

        # Predict quality score trend
        if "quality_score" in df.columns:
            quality_scores = df["quality_score"].dropna()
            if len(quality_scores) >= 3:
                try:
                    # Use linear regression for prediction
                    X = np.arange(len(quality_scores)).reshape(-1, 1)
                    y = quality_scores.values

                    model = LinearRegression()
                    model.fit(X, y)

                    # Predict future values
                    future_X = np.arange(len(quality_scores), len(quality_scores) + prediction_days).reshape(-1, 1)
                    future_predictions = model.predict(future_X)

                    # Calculate prediction confidence
                    r_squared = model.score(X, y)
                    confidence = min(float(r_squared), 1.0)

                    predictions["quality_score"] = {
                        "current_trend": ("improving" if model.coef_[0] > 0 else "declining"),
                        "predicted_values": [float(pred) for pred in future_predictions],
                        "confidence": confidence,
                        "prediction_days": prediction_days,
                    }

                except Exception as e:
                    logger.warning(f"Quality score prediction failed: {e}")

        # Predict finding trends
        finding_columns = [col for col in df.columns if col.startswith("finding_type_")]
        for finding_col in finding_columns:
            finding_data = df[finding_col].dropna()
            if len(finding_data) >= 3:
                try:
                    X = np.arange(len(finding_data)).reshape(-1, 1)
                    y = finding_data.values

                    model = LinearRegression()
                    model.fit(X, y)

                    future_X = np.arange(len(finding_data), len(finding_data) + prediction_days).reshape(-1, 1)
                    future_predictions = model.predict(future_X)

                    finding_type = finding_col.replace("finding_type_", "")
                    predictions[f"{finding_type}_findings"] = {
                        "predicted_count": float(future_predictions[-1]),  # Final prediction
                        "trend": "increasing" if model.coef_[0] > 0 else "decreasing",
                        "confidence": 0.7,  # Simplified confidence for findings
                    }

                except Exception as e:
                    logger.warning(f"Finding prediction failed for {finding_col}: {e}")

        return {
            "predictions": predictions,
            "confidence": max([pred.get("confidence", 0.0) for pred in predictions.values()] + [0.0]),
            "prediction_horizon_days": prediction_days,
        }

    def _identify_risk_areas(self, df: pd.DataFrame, predictions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify high-risk areas based on trends and predictions."""
        risk_areas = []

        # Check for declining quality trends
        quality_trend = predictions.get("predictions", {}).get("quality_score", {})
        if quality_trend.get("current_trend") == "declining":
            risk_areas.append(
                {
                    "risk_type": "quality_decline",
                    "severity": "high",
                    "description": "Documentation quality is trending downward",
                    "predicted_impact": f"Quality may decrease to {quality_trend.get('predicted_values', [-1])[-1]:.2f}",
                    "recommendation": "Implement quality improvement measures and regular reviews",
                }
            )

        # Check for increasing finding trends
        for pred_key, pred_data in predictions.get("predictions", {}).items():
            if pred_key.endswith("_findings") and pred_data.get("trend") == "increasing":
                finding_type = pred_key.replace("_findings", "")
                predicted_count = pred_data.get("predicted_count", 0)
                risk_areas.append(
                    {
                        "risk_type": f"increasing_{finding_type}",
                        "severity": "medium" if predicted_count < 5 else "high",
                        "description": f'{finding_type.replace("_", " ").title()} issues are increasing',
                        "predicted_impact": f"May have {predicted_count:.1f} {finding_type} issues in 30 days",
                        "recommendation": f'Focus on reducing {finding_type.replace("_", " ")} issues',
                    }
                )

        # Check for high volatility
        if df is not None and "quality_score" in df.columns:
            quality_scores = df["quality_score"].dropna()
            if len(quality_scores) > 1:
                volatility = quality_scores.std()
                if volatility > 0.2:  # High volatility threshold
                    risk_areas.append(
                        {
                            "risk_type": "high_volatility",
                            "severity": "medium",
                            "description": "Documentation quality shows high variability",
                            "predicted_impact": "Inconsistent quality may confuse users",
                            "recommendation": "Standardize documentation processes and review guidelines",
                        }
                    )

        return risk_areas

    def _generate_trend_insights(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate actionable insights from trend analysis."""
        insights = []

        patterns = analysis_results.get("patterns", {})
        predictions = analysis_results.get("predictions", {})

        # Generate quality trend insights
        insights.extend(self._generate_quality_trend_insights(patterns))

        # Generate finding trend insights
        insights.extend(self._generate_finding_trend_insights(patterns))

        # Generate prediction insights
        insights.extend(self._generate_prediction_insights(predictions))

        # Default insights if none generated
        if not insights:
            insights.append("Trend analysis complete - monitor quality metrics regularly")

        return insights

    def _generate_quality_trend_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate insights for quality trends.

        Args:
            patterns: Pattern analysis results

        Returns:
            List of quality trend insights
        """
        insights = []
        quality_trend = patterns.get("quality_trend", {})

        if not quality_trend:
            return insights

        direction = quality_trend.get("direction", "stable")
        confidence = quality_trend.get("confidence", 0.0)

        if direction == "improving" and confidence > 0.7:
            insights.append("Documentation quality is improving steadily - continue current practices")
        elif direction == "declining" and confidence > 0.7:
            insights.append("Documentation quality is declining - implement immediate improvement measures")
        elif direction == "stable":
            insights.append("Documentation quality is stable - maintain current standards")

        return insights

    def _generate_finding_trend_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate insights for finding trends.

        Args:
            patterns: Pattern analysis results

        Returns:
            List of finding trend insights
        """
        insights = []

        for pattern_key, pattern_data in patterns.items():
            if not (pattern_key.endswith("_trend") and pattern_key != "quality_trend"):
                continue

            finding_type = pattern_key.replace("_trend", "").replace("_", " ")
            direction = pattern_data.get("direction", "stable")

            if direction == "increasing":
                insights.append(f"{finding_type.title()} issues are increasing - prioritize resolution")
            elif direction == "decreasing":
                insights.append(f"{finding_type.title()} issues are decreasing - good progress")

        return insights

    def _generate_prediction_insights(self, predictions: Dict[str, Any]) -> List[str]:
        """Generate insights for quality predictions.

        Args:
            predictions: Prediction analysis results

        Returns:
            List of prediction insights
        """
        insights = []
        quality_pred = predictions.get("predictions", {}).get("quality_score", {})

        if not quality_pred:
            return insights

        predicted_values = quality_pred.get("predicted_values", [])
        if not predicted_values:
            return insights

        final_prediction = predicted_values[-1]
        if final_prediction < 0.6:
            insights.append("Projected quality decline - implement preventive measures")
        elif final_prediction > 0.8:
            insights.append("Quality trajectory is positive - maintain momentum")

        return insights

    async def analyze_documentation_trends(
        self,
        document_id: str,
        analysis_results: List[Dict[str, Any]],
        prediction_days: int = 30,
        include_predictions: bool = True,
    ) -> Dict[str, Any]:
        """Perform comprehensive trend analysis for a document."""

        start_time = time.time()

        if not self._initialize_analyzer():
            return {
                "error": "Trend analysis not available",
                "message": "Required dependencies not installed or initialization failed",
            }

        try:
            # Extract historical data
            df = self._extract_historical_data(analysis_results)

            if df.empty:
                return {
                    "document_id": document_id,
                    "trend_direction": "insufficient_data",
                    "confidence": 0.0,
                    "patterns": [],
                    "predictions": {},
                    "risk_areas": [],
                    "insights": ["Insufficient historical data for trend analysis"],
                    "analysis_period_days": 0,
                    "data_points": 0,
                    "processing_time": time.time() - start_time,
                }

            # Analyze trend patterns
            trend_analysis = self._analyze_trend_patterns(df)

            # Generate predictions if requested
            predictions = {}
            if include_predictions:
                predictions = self._predict_future_issues(df, prediction_days)

            # Identify risk areas
            risk_areas = self._identify_risk_areas(df, predictions)

            # Generate insights
            insights = self._generate_trend_insights(
                {
                    "trend_direction": trend_analysis["trend_direction"],
                    "patterns": trend_analysis["patterns"],
                    "predictions": predictions,
                }
            )

            # Calculate analysis period
            if len(df) > 0:
                analysis_period = (df.index.max() - df.index.min()).days
            else:
                analysis_period = 0

            processing_time = time.time() - start_time

            return {
                "document_id": document_id,
                "trend_direction": trend_analysis["trend_direction"],
                "confidence": trend_analysis["confidence"],
                "patterns": trend_analysis["patterns"],
                "predictions": predictions,
                "risk_areas": risk_areas,
                "insights": insights,
                "analysis_period_days": analysis_period,
                "data_points": len(df),
                "volatility": trend_analysis["volatility"],
                "processing_time": processing_time,
                "analysis_timestamp": time.time(),
            }

        except Exception as e:
            logger.error(f"Trend analysis failed for document {document_id}: {e}")
            return {
                "error": "Trend analysis failed",
                "message": str(e),
                "document_id": document_id,
                "processing_time": time.time() - start_time,
            }

    async def analyze_portfolio_trends(
        self,
        analysis_results: List[Dict[str, Any]],
        group_by: str = "document_id",
        prediction_days: int = 30,
    ) -> Dict[str, Any]:
        """Analyze trends across a portfolio of documents."""

        start_time = time.time()

        if not self._initialize_analyzer():
            return {
                "error": "Trend analysis not available",
                "message": "Required dependencies not installed or initialization failed",
            }

        try:
            if not analysis_results:
                return {
                    "portfolio_summary": {},
                    "document_trends": [],
                    "overall_trend": "insufficient_data",
                    "high_risk_documents": [],
                    "processing_time": time.time() - start_time,
                }

            # Group results by document
            document_groups = defaultdict(list)
            for result in analysis_results:
                key = result.get(group_by, "unknown")
                document_groups[key].append(result)

            # Analyze each document
            document_trends = []
            for doc_id, results in document_groups.items():
                if len(results) >= 2:  # Need at least 2 data points for trends
                    trend_result = await self.analyze_documentation_trends(
                        doc_id, results, prediction_days, include_predictions=False
                    )
                    if "error" not in trend_result:
                        document_trends.append(trend_result)

            # Calculate portfolio summary
            portfolio_summary = self._calculate_portfolio_summary(document_groups, document_trends)
            else:
                portfolio_summary = {
                    "total_documents": len(document_groups),
                    "analyzed_documents": 0,
                    "overall_trend": "insufficient_data",
                    "message": "Not enough historical data for trend analysis",
                }

            processing_time = time.time() - start_time

            return {
                "portfolio_summary": portfolio_summary,
                "document_trends": document_trends,
                "processing_time": processing_time,
                "analysis_timestamp": time.time(),
            }

        except Exception as e:
            logger.error(f"Portfolio trend analysis failed: {e}")
            return {
                "error": "Portfolio trend analysis failed",
                "message": str(e),
                "processing_time": time.time() - start_time,
            }


# Global instance for reuse
trend_analyzer = TrendAnalyzer()


async def analyze_document_trends(
    document_id: str,
    analysis_results: List[Dict[str, Any]],
    prediction_days: int = 30,
    include_predictions: bool = True,
) -> Dict[str, Any]:
    """Convenience function for document trend analysis.

    Args:
        document_id: ID of the document to analyze
        analysis_results: Historical analysis results
        prediction_days: Number of days to predict
        include_predictions: Whether to include predictions

    Returns:
        Trend analysis results
    """
    return await trend_analyzer.analyze_documentation_trends(
        document_id=document_id,
        analysis_results=analysis_results,
        prediction_days=prediction_days,
        include_predictions=include_predictions,
    )


async def analyze_portfolio_trends(
    analysis_results: List[Dict[str, Any]],
    group_by: str = "document_id",
    prediction_days: int = 30,
) -> Dict[str, Any]:
    """Convenience function for portfolio trend analysis.

    Args:
        analysis_results: Historical analysis results across portfolio
        group_by: Field to group results by
        prediction_days: Number of days to predict

    Returns:
        Portfolio trend analysis results
    """
    return await trend_analyzer.analyze_portfolio_trends(
        analysis_results=analysis_results,
        group_by=group_by,
        prediction_days=prediction_days,
    )

    def _calculate_portfolio_summary(self, document_groups: Dict[str, List], document_trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate comprehensive portfolio summary from document trends.

        Args:
            document_groups: Groups of documents by ID
            document_trends: Individual document trend analyses

        Returns:
            Portfolio summary with overall trends, risk analysis, and statistics
        """
        if not document_trends:
            return {
                "total_documents": len(document_groups),
                "analyzed_documents": 0,
                "overall_trend": "insufficient_data",
                "average_confidence": 0.0,
                "trend_distribution": {},
                "high_risk_documents": [],
                "risk_area_summary": {},
                "most_common_risks": [],
            }

        # Calculate overall portfolio trend
        overall_trend = self._determine_overall_portfolio_trend(document_trends)

        # Calculate average confidence
        avg_confidence = sum(doc["confidence"] for doc in document_trends) / len(document_trends)

        # Identify high-risk documents
        high_risk_documents = self._identify_high_risk_documents(document_trends)

        # Analyze risk areas across portfolio
        risk_analysis = self._analyze_portfolio_risk_areas(document_trends)

        return {
            "total_documents": len(document_groups),
            "analyzed_documents": len(document_trends),
            "overall_trend": overall_trend,
            "average_confidence": round(avg_confidence, 3),
            "trend_distribution": self._count_trend_directions(document_trends),
            "high_risk_documents": high_risk_documents,
            "risk_area_summary": risk_analysis["risk_summary"],
            "most_common_risks": risk_analysis["most_common_risks"],
        }

    def _determine_overall_portfolio_trend(self, document_trends: List[Dict[str, Any]]) -> str:
        """Determine overall trend direction for the portfolio.

        Args:
            document_trends: Individual document trend analyses

        Returns:
            Overall trend: "improving", "declining", or "stable"
        """
        trend_directions = [doc["trend_direction"] for doc in document_trends]
        direction_counts = Counter(trend_directions)

        improving_count = direction_counts.get("improving", 0)
        declining_count = direction_counts.get("declining", 0)

        if improving_count > declining_count:
            return "improving"
        elif declining_count > improving_count:
            return "declining"
        else:
            return "stable"

    def _count_trend_directions(self, document_trends: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count occurrences of each trend direction.

        Args:
            document_trends: Individual document trend analyses

        Returns:
            Dictionary with counts for each trend direction
        """
        trend_directions = [doc["trend_direction"] for doc in document_trends]
        return dict(Counter(trend_directions))

    def _identify_high_risk_documents(self, document_trends: List[Dict[str, Any]]) -> List[str]:
        """Identify documents with high risk based on declining trends and confidence.

        Args:
            document_trends: Individual document trend analyses

        Returns:
            List of document IDs considered high risk
        """
        return [
            doc["document_id"]
            for doc in document_trends
            if doc["trend_direction"] == "declining" and doc["confidence"] > 0.6
        ]

    def _analyze_portfolio_risk_areas(self, document_trends: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze risk areas across the entire portfolio.

        Args:
            document_trends: Individual document trend analyses

        Returns:
            Risk analysis summary with risk types and most common risks
        """
        all_risk_areas = []
        for doc in document_trends:
            all_risk_areas.extend(doc.get("risk_areas", []))

        risk_summary = Counter(area["risk_type"] for area in all_risk_areas)

        return {
            "risk_summary": dict(risk_summary),
            "most_common_risks": risk_summary.most_common(3),
        }
