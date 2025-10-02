"""Analytics and insights for configuration drift patterns"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict, Counter

from monitoring.database.manager import DatabaseManager
from monitoring.database.models import ConfigurationDrift, DriftPattern

logger = logging.getLogger(__name__)


class DriftAnalytics:
    """Analyzes configuration drift patterns and provides insights"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def analyze_drift_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analyze drift trends over time"""
        logger.info(f"📊 Analyzing drift trends for the last {days} days")

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        drifts = self.db_manager.get_configuration_drift(limit=2000)

        # Filter by date
        recent_drifts = [d for d in drifts if d.timestamp >= cutoff_date]

        # Group by day
        daily_drift = defaultdict(int)
        for drift in recent_drifts:
            day = drift.timestamp.date()
            daily_drift[day] += 1

        # Calculate trend
        days_list = sorted(daily_drift.keys())
        if len(days_list) >= 7:
            recent_week = sum(daily_drift.get(day, 0) for day in days_list[-7:])
            previous_week = sum(daily_drift.get(day, 0) for day in days_list[-14:-7]) if len(days_list) >= 14 else 0

            if previous_week > 0:
                trend_percentage = ((recent_week - previous_week) / previous_week) * 100
            else:
                trend_percentage = 0
        else:
            trend_percentage = 0

        # Identify peak drift days
        peak_days = sorted(daily_drift.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_drifts": len(recent_drifts),
            "daily_breakdown": dict(daily_drift),
            "trend_percentage": trend_percentage,
            "peak_drift_days": peak_days,
            "analysis_period_days": days
        }

    def identify_risky_services(self, min_drift_threshold: int = 3) -> List[Dict[str, Any]]:
        """Identify services with high drift frequency"""
        drifts = self.db_manager.get_configuration_drift(resolved=False, limit=1000)

        # Count drifts per service
        service_counts = Counter(drift.service_name for drift in drifts)

        # Get services with high drift counts
        risky_services = []
        for service_name, count in service_counts.items():
            if count >= min_drift_threshold:
                # Get recent drifts for this service
                recent_drifts = [d for d in drifts if d.service_name == service_name]

                # Calculate severity distribution
                severity_counts = Counter(drift.severity for drift in recent_drifts)

                risky_services.append({
                    "service_name": service_name,
                    "total_drifts": count,
                    "severity_breakdown": dict(severity_counts),
                    "most_common_drift_type": Counter(d.drift_type for d in recent_drifts).most_common(1)[0][0],
                    "risk_level": self._calculate_risk_level(count, severity_counts)
                })

        # Sort by risk level and total drifts
        risky_services.sort(key=lambda x: (x["risk_level"], x["total_drifts"]), reverse=True)

        return risky_services

    def _calculate_risk_level(self, total_drifts: int, severity_counts: Counter) -> str:
        """Calculate risk level based on drift count and severity"""
        high_severity = severity_counts.get("high", 0) + severity_counts.get("critical", 0)

        if total_drifts >= 10 or high_severity >= 3:
            return "critical"
        elif total_drifts >= 5 or high_severity >= 1:
            return "high"
        elif total_drifts >= 2:
            return "medium"
        else:
            return "low"

    def analyze_seasonal_patterns(self) -> Dict[str, Any]:
        """Analyze if drift occurs at specific times/days"""
        drifts = self.db_manager.get_configuration_drift(limit=1000)

        # Analyze by hour of day
        hourly_distribution = defaultdict(int)
        for drift in drifts:
            hour = drift.timestamp.hour
            hourly_distribution[hour] += 1

        # Analyze by day of week
        weekday_distribution = defaultdict(int)
        for drift in drifts:
            weekday = drift.timestamp.weekday()  # 0=Monday, 6=Sunday
            weekday_distribution[weekday] += 1

        # Find peak hours and days
        peak_hour = max(hourly_distribution.items(), key=lambda x: x[1]) if hourly_distribution else None
        peak_weekday = max(weekday_distribution.items(), key=lambda x: x[1]) if weekday_distribution else None

        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        return {
            "hourly_distribution": dict(hourly_distribution),
            "weekday_distribution": dict(weekday_distribution),
            "peak_hour": peak_hour[0] if peak_hour else None,
            "peak_hour_count": peak_hour[1] if peak_hour else 0,
            "peak_weekday": weekday_names[peak_weekday[0]] if peak_weekday else None,
            "peak_weekday_count": peak_weekday[1] if peak_weekday else None
        }

    def generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations based on drift analysis"""
        recommendations = []

        # Analyze risky services
        risky_services = self.identify_risky_services()

        for service in risky_services:
            if service["risk_level"] in ["critical", "high"]:
                recommendations.append({
                    "type": "service_review",
                    "priority": "high",
                    "service": service["service_name"],
                    "title": f"Review {service['service_name']} configuration management",
                    "description": f"Service has {service['total_drifts']} unresolved configuration changes",
                    "action_items": [
                        "Review recent configuration changes",
                        "Implement configuration validation",
                        "Consider automated deployment controls"
                    ]
                })

        # Analyze trend
        trend_analysis = self.analyze_drift_trends(days=30)
        trend_pct = trend_analysis.get("trend_percentage", 0)

        if trend_pct > 50:
            recommendations.append({
                "type": "trend_alert",
                "priority": "medium",
                "title": "Increasing configuration drift trend",
                "description": f"Configuration drift has increased by {trend_pct:.1f}% in the last week",
                "action_items": [
                    "Investigate root causes of configuration changes",
                    "Review change management processes",
                    "Consider implementing configuration freeze periods"
                ]
            })

        # Analyze patterns
        patterns = self.db_manager.get_drift_patterns()
        for pattern in patterns:
            if pattern.impact == "high":
                recommendations.append({
                    "type": "pattern_remediation",
                    "priority": "high",
                    "service": pattern.service_name,
                    "title": f"Address {pattern.pattern_type} pattern",
                    "description": pattern.description,
                    "action_items": pattern.recommendations
                })

        return recommendations

    def predict_future_drift(self, service_name: Optional[str] = None, days_ahead: int = 7) -> Dict[str, Any]:
        """Simple prediction of future drift based on historical patterns"""
        drifts = self.db_manager.get_configuration_drift(service_name=service_name, limit=100)

        if len(drifts) < 7:  # Need minimum data for prediction
            return {"prediction": "insufficient_data", "confidence": 0}

        # Simple moving average prediction
        recent_drifts = [d for d in drifts if d.timestamp >= datetime.utcnow() - timedelta(days=14)]
        daily_average = len(recent_drifts) / 14

        predicted_drift = daily_average * days_ahead

        # Calculate confidence based on data consistency
        daily_counts = defaultdict(int)
        for drift in recent_drifts:
            day = drift.timestamp.date()
            daily_counts[day] += 1

        # Simple variance calculation
        counts = list(daily_counts.values())
        if len(counts) > 1:
            mean = sum(counts) / len(counts)
            variance = sum((x - mean) ** 2 for x in counts) / len(counts)
            std_dev = variance ** 0.5
            cv = std_dev / mean if mean > 0 else 0  # Coefficient of variation
            confidence = max(0, 1 - cv)  # Lower variation = higher confidence
        else:
            confidence = 0.5

        return {
            "predicted_drift_incidents": round(predicted_drift, 1),
            "prediction_period_days": days_ahead,
            "confidence_score": round(confidence, 2),
            "historical_average_daily": round(daily_average, 2),
            "data_points_used": len(recent_drifts)
        }

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive drift analysis report"""
        logger.info("📊 Generating comprehensive drift analysis report")

        # Gather all analytics
        drift_stats = self.db_manager.get_drift_statistics()
        health_stats = self.db_manager.get_health_statistics()
        trend_analysis = self.analyze_drift_trends()
        seasonal_patterns = self.analyze_seasonal_patterns()
        risky_services = self.identify_risky_services()
        recommendations = self.generate_recommendations()

        # Calculate overall risk score
        risk_score = self._calculate_overall_risk_score(
            drift_stats, health_stats, risky_services
        )

        return {
            "generated_at": datetime.utcnow().isoformat(),
            "risk_score": risk_score,
            "risk_level": self._risk_score_to_level(risk_score),
            "drift_statistics": drift_stats,
            "health_statistics": health_stats,
            "trend_analysis": trend_analysis,
            "seasonal_patterns": seasonal_patterns,
            "risky_services": risky_services,
            "recommendations": recommendations,
            "summary": {
                "total_unresolved_drifts": drift_stats.get("unresolved_drift", 0),
                "services_at_risk": len(risky_services),
                "recommendations_count": len(recommendations),
                "overall_health_percentage": health_stats.get("service_availability", {}).get("average", 0)
            }
        }

    def _calculate_overall_risk_score(self, drift_stats: Dict, health_stats: Dict,
                                    risky_services: List) -> float:
        """Calculate overall risk score (0-100)"""
        score = 0

        # Drift risk (40% weight)
        unresolved_drifts = drift_stats.get("unresolved_drift", 0)
        if unresolved_drifts > 10:
            score += 40
        elif unresolved_drifts > 5:
            score += 25
        elif unresolved_drifts > 0:
            score += 10

        # Health risk (30% weight)
        health_pct = health_stats.get("service_availability", {}).get("average", 100)
        if health_pct < 80:
            score += 30
        elif health_pct < 90:
            score += 15

        # Service risk (30% weight)
        critical_services = len([s for s in risky_services if s.get("risk_level") == "critical"])
        high_risk_services = len([s for s in risky_services if s.get("risk_level") == "high"])

        score += min(critical_services * 10 + high_risk_services * 5, 30)

        return min(score, 100)

    def _risk_score_to_level(self, score: float) -> str:
        """Convert risk score to risk level"""
        if score >= 70:
            return "critical"
        elif score >= 40:
            return "high"
        elif score >= 20:
            return "medium"
        else:
            return "low"
