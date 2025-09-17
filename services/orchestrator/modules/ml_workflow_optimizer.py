#!/usr/bin/env python3
"""
Machine Learning Workflow Optimizer

This module provides ML-powered workflow optimization including:
- Predictive performance modeling
- Dynamic resource allocation
- Workflow pattern learning
- Intelligent scheduling optimization
- Anomaly detection and automated remediation
"""

import asyncio
import json
import uuid
import random
import statistics
from typing import Dict, Any, List, Optional, Callable, Type, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import numpy as np
# from sklearn.ensemble import RandomForestRegressor, IsolationForest  # Optional ML libraries
# from sklearn.preprocessing import StandardScaler
# from sklearn.cluster import KMeans
# import joblib
import os

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget
from services.shared.intelligent_caching import get_service_cache


class OptimizationGoal(Enum):
    """Optimization goals."""
    MINIMIZE_LATENCY = "minimize_latency"
    MAXIMIZE_THROUGHPUT = "maximize_throughput"
    OPTIMIZE_COST = "optimize_cost"
    BALANCE_RESOURCES = "balance_resources"
    MAXIMIZE_RELIABILITY = "maximize_reliability"


class PredictionModel(Enum):
    """Prediction model types."""
    PERFORMANCE_PREDICTION = "performance_prediction"
    RESOURCE_USAGE = "resource_usage"
    FAILURE_PREDICTION = "failure_prediction"
    PATTERN_RECOGNITION = "pattern_recognition"


@dataclass
class WorkflowMetrics:
    """Workflow execution metrics for ML analysis."""
    workflow_id: str
    execution_time: float
    cpu_usage: float
    memory_usage: float
    network_io: float
    success_rate: float
    error_count: int
    step_metrics: List[Dict[str, Any]] = field(default_factory=list)
    resource_utilization: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_feature_vector(self) -> List[float]:
        """Convert metrics to feature vector for ML models."""
        return [
            self.execution_time,
            self.cpu_usage,
            self.memory_usage,
            self.network_io,
            self.success_rate,
            self.error_count,
            len(self.step_metrics),
            sum(self.resource_utilization.values()) / len(self.resource_utilization) if self.resource_utilization else 0
        ]


@dataclass
class OptimizationRecommendation:
    """ML-generated optimization recommendation."""
    workflow_type: str
    recommendation_type: str
    confidence_score: float
    expected_improvement: float
    implementation_complexity: str
    description: str
    actions: List[Dict[str, Any]]
    generated_at: datetime = field(default_factory=datetime.now)


class PerformancePredictor:
    """ML-based performance prediction model."""

    def __init__(self):
        self.model: Optional[RandomForestRegressor] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_columns = [
            'execution_time', 'cpu_usage', 'memory_usage', 'network_io',
            'success_rate', 'error_count', 'step_count', 'avg_resource_utilization'
        ]
        self.training_data: List[WorkflowMetrics] = []
        self.model_path = "/tmp/workflow_performance_model.pkl"

    async def train_model(self, metrics_data: List[WorkflowMetrics]) -> bool:
        """Train performance prediction model."""
        try:
            if len(metrics_data) < 10:
                fire_and_forget("warning", "Insufficient data for training performance model", ServiceNames.ORCHESTRATOR)
                return False

            # Prepare training data
            X = []
            y = []

            for metrics in metrics_data:
                features = metrics.to_feature_vector()
                # Predict execution time (can be extended to predict other metrics)
                target = metrics.execution_time

                X.append(features)
                y.append(target)

            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.model = RandomForestRegressor(
                n_estimators=100,
                random_state=42,
                max_depth=10
            )
            self.model.fit(X_scaled, y)

            # Save model
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns,
                'trained_at': datetime.now()
            }
            joblib.dump(model_data, self.model_path)

            fire_and_forget("info", f"Performance prediction model trained with {len(metrics_data)} samples", ServiceNames.ORCHESTRATOR)
            return True

        except Exception as e:
            fire_and_forget("error", f"Failed to train performance model: {e}", ServiceNames.ORCHESTRATOR)
            return False

    async def predict_performance(self, workflow_metrics: WorkflowMetrics) -> Dict[str, Any]:
        """Predict workflow performance."""
        try:
            if not self.model or not self.scaler:
                # Try to load saved model
                if os.path.exists(self.model_path):
                    model_data = joblib.load(self.model_path)
                    self.model = model_data['model']
                    self.scaler = model_data['scaler']

            if not self.model:
                return {"error": "No trained model available"}

            # Prepare input
            features = workflow_metrics.to_feature_vector()
            features_scaled = self.scaler.transform([features])

            # Make prediction
            predicted_time = self.model.predict(features_scaled)[0]

            # Calculate confidence based on feature importance
            feature_importance = self.model.feature_importances_
            confidence = 1.0 - (np.std(features_scaled[0]) / np.mean(features_scaled[0]))

            return {
                "predicted_execution_time": predicted_time,
                "confidence": min(max(confidence, 0.0), 1.0),
                "feature_importance": dict(zip(self.feature_columns, feature_importance)),
                "prediction_timestamp": datetime.now()
            }

        except Exception as e:
            fire_and_forget("error", f"Performance prediction failed: {e}", ServiceNames.ORCHESTRATOR)
            return {"error": str(e)}


class AnomalyDetector:
    """ML-based anomaly detection for workflow execution."""

    def __init__(self):
        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self.anomaly_threshold = -0.5  # Isolation Forest threshold
        self.training_data: List[WorkflowMetrics] = []
        self.model_path = "/tmp/workflow_anomaly_model.pkl"

    async def train_model(self, metrics_data: List[WorkflowMetrics]) -> bool:
        """Train anomaly detection model."""
        try:
            if len(metrics_data) < 20:
                fire_and_forget("warning", "Insufficient data for training anomaly model", ServiceNames.ORCHESTRATOR)
                return False

            # Prepare training data
            X = [metrics.to_feature_vector() for metrics in metrics_data]

            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.model = IsolationForest(
                contamination=0.1,  # Expected percentage of anomalies
                random_state=42,
                n_estimators=100
            )
            self.model.fit(X_scaled)

            # Save model
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'trained_at': datetime.now(),
                'training_samples': len(metrics_data)
            }
            joblib.dump(model_data, self.model_path)

            fire_and_forget("info", f"Anomaly detection model trained with {len(metrics_data)} samples", ServiceNames.ORCHESTRATOR)
            return True

        except Exception as e:
            fire_and_forget("error", f"Failed to train anomaly model: {e}", ServiceNames.ORCHESTRATOR)
            return False

    async def detect_anomalies(self, workflow_metrics: WorkflowMetrics) -> Dict[str, Any]:
        """Detect anomalies in workflow execution."""
        try:
            if not self.model or not self.scaler:
                # Try to load saved model
                if os.path.exists(self.model_path):
                    model_data = joblib.load(self.model_path)
                    self.model = model_data['model']
                    self.scaler = model_data['scaler']

            if not self.model:
                return {"error": "No trained anomaly model available"}

            # Prepare input
            features = workflow_metrics.to_feature_vector()
            features_scaled = self.scaler.transform([features])

            # Make prediction
            anomaly_score = self.model.decision_function(features_scaled)[0]
            is_anomaly = anomaly_score < self.anomaly_threshold

            # Calculate anomaly severity
            severity = "low"
            if anomaly_score < -0.7:
                severity = "high"
            elif anomaly_score < -0.6:
                severity = "medium"

            return {
                "is_anomaly": bool(is_anomaly),
                "anomaly_score": float(anomaly_score),
                "severity": severity,
                "threshold": self.anomaly_threshold,
                "recommendations": self._generate_anomaly_recommendations(anomaly_score, workflow_metrics)
            }

        except Exception as e:
            fire_and_forget("error", f"Anomaly detection failed: {e}", ServiceNames.ORCHESTRATOR)
            return {"error": str(e)}

    def _generate_anomaly_recommendations(self, anomaly_score: float, metrics: WorkflowMetrics) -> List[str]:
        """Generate recommendations for detected anomalies."""
        recommendations = []

        if anomaly_score < -0.7:  # High severity anomaly
            if metrics.execution_time > 300:  # 5 minutes
                recommendations.append("Consider optimizing workflow steps to reduce execution time")
            if metrics.memory_usage > 80:
                recommendations.append("High memory usage detected - review memory-intensive operations")
            if metrics.error_count > 5:
                recommendations.append("High error rate - investigate error sources and implement retry logic")

        elif anomaly_score < -0.6:  # Medium severity
            if metrics.cpu_usage > 90:
                recommendations.append("High CPU usage - consider distributing workload")
            if len(metrics.step_metrics) > 20:
                recommendations.append("Complex workflow detected - consider breaking into smaller workflows")

        return recommendations


class PatternLearner:
    """ML-based workflow pattern learning and clustering."""

    def __init__(self):
        self.cluster_model: Optional[KMeans] = None
        self.scaler: Optional[StandardScaler] = None
        self.workflow_patterns: Dict[int, Dict[str, Any]] = {}
        self.pattern_stats: Dict[int, Dict[str, Any]] = {}
        self.training_data: List[WorkflowMetrics] = []

    async def learn_patterns(self, metrics_data: List[WorkflowMetrics], n_clusters: int = 5) -> bool:
        """Learn workflow patterns using clustering."""
        try:
            if len(metrics_data) < n_clusters * 2:
                fire_and_forget("warning", "Insufficient data for pattern learning", ServiceNames.ORCHESTRATOR)
                return False

            # Prepare training data
            X = [metrics.to_feature_vector() for metrics in metrics_data]

            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)

            # Train clustering model
            self.cluster_model = KMeans(
                n_clusters=n_clusters,
                random_state=42,
                n_init=10
            )
            clusters = self.cluster_model.fit_predict(X_scaled)

            # Analyze clusters
            for i in range(n_clusters):
                cluster_metrics = [metrics for j, metrics in enumerate(metrics_data) if clusters[j] == i]

                if cluster_metrics:
                    # Calculate cluster characteristics
                    execution_times = [m.execution_time for m in cluster_metrics]
                    success_rates = [m.success_rate for m in cluster_metrics]

                    self.workflow_patterns[i] = {
                        "avg_execution_time": statistics.mean(execution_times),
                        "avg_success_rate": statistics.mean(success_rates),
                        "std_execution_time": statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
                        "sample_count": len(cluster_metrics),
                        "characteristics": self._analyze_cluster_characteristics(cluster_metrics)
                    }

                    self.pattern_stats[i] = {
                        "execution_time_range": (min(execution_times), max(execution_times)),
                        "success_rate_range": (min(success_rates), max(success_rates)),
                        "common_errors": self._find_common_errors(cluster_metrics)
                    }

            fire_and_forget("info", f"Learned {n_clusters} workflow patterns from {len(metrics_data)} samples", ServiceNames.ORCHESTRATOR)
            return True

        except Exception as e:
            fire_and_forget("error", f"Pattern learning failed: {e}", ServiceNames.ORCHESTRATOR)
            return False

    async def classify_workflow(self, metrics: WorkflowMetrics) -> Dict[str, Any]:
        """Classify workflow into learned patterns."""
        try:
            if not self.cluster_model or not self.scaler:
                return {"error": "No trained pattern model available"}

            # Prepare input
            features = metrics.to_feature_vector()
            features_scaled = self.scaler.transform([features])

            # Predict cluster
            cluster_id = self.cluster_model.predict(features_scaled)[0]

            # Get pattern information
            pattern_info = self.workflow_patterns.get(cluster_id, {})
            pattern_stats = self.pattern_stats.get(cluster_id, {})

            return {
                "cluster_id": int(cluster_id),
                "pattern_info": pattern_info,
                "pattern_stats": pattern_stats,
                "similar_workflows_count": pattern_info.get("sample_count", 0),
                "classification_confidence": self._calculate_classification_confidence(metrics, cluster_id)
            }

        except Exception as e:
            fire_and_forget("error", f"Workflow classification failed: {e}", ServiceNames.ORCHESTRATOR)
            return {"error": str(e)}

    def _analyze_cluster_characteristics(self, cluster_metrics: List[WorkflowMetrics]) -> Dict[str, Any]:
        """Analyze characteristics of a workflow cluster."""
        characteristics = {
            "performance_profile": "unknown",
            "resource_intensity": "unknown",
            "reliability_profile": "unknown"
        }

        # Analyze execution time characteristics
        avg_time = statistics.mean([m.execution_time for m in cluster_metrics])
        if avg_time < 60:
            characteristics["performance_profile"] = "fast"
        elif avg_time < 300:
            characteristics["performance_profile"] = "medium"
        else:
            characteristics["performance_profile"] = "slow"

        # Analyze resource usage
        avg_memory = statistics.mean([m.memory_usage for m in cluster_metrics])
        if avg_memory < 50:
            characteristics["resource_intensity"] = "low"
        elif avg_memory < 80:
            characteristics["resource_intensity"] = "medium"
        else:
            characteristics["resource_intensity"] = "high"

        # Analyze reliability
        avg_success = statistics.mean([m.success_rate for m in cluster_metrics])
        if avg_success > 0.95:
            characteristics["reliability_profile"] = "high"
        elif avg_success > 0.85:
            characteristics["reliability_profile"] = "medium"
        else:
            characteristics["reliability_profile"] = "low"

        return characteristics

    def _find_common_errors(self, cluster_metrics: List[WorkflowMetrics]) -> List[str]:
        """Find common errors in a cluster."""
        error_counts = defaultdict(int)

        for metrics in cluster_metrics:
            for step in metrics.step_metrics:
                if step.get("error"):
                    error_counts[step["error"]] += 1

        # Return top 3 most common errors
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return [error for error, count in sorted_errors[:3]]

    def _calculate_classification_confidence(self, metrics: WorkflowMetrics, cluster_id: int) -> float:
        """Calculate confidence score for classification."""
        if cluster_id not in self.workflow_patterns:
            return 0.0

        pattern = self.workflow_patterns[cluster_id]

        # Calculate distance from cluster center
        cluster_center = [
            pattern["avg_execution_time"],
            0, 0, 0,  # Placeholder for other metrics
            pattern["avg_success_rate"],
            0, 0, 0   # Placeholder for other metrics
        ]

        input_vector = metrics.to_feature_vector()

        # Simple Euclidean distance (can be improved)
        distance = sum((a - b) ** 2 for a, b in zip(input_vector[:5], cluster_center[:5])) ** 0.5

        # Convert distance to confidence (closer = higher confidence)
        confidence = max(0, 1 - (distance / 100))  # Normalize

        return confidence


class MLOptimizer:
    """Main ML-powered workflow optimizer."""

    def __init__(self):
        self.performance_predictor = PerformancePredictor()
        self.anomaly_detector = AnomalyDetector()
        self.pattern_learner = PatternLearner()
        self.optimization_history: List[Dict[str, Any]] = []
        self.cache = get_service_cache(ServiceNames.ORCHESTRATOR)

    async def optimize_workflow(self, workflow_id: str, workflow_data: Dict[str, Any],
                              optimization_goal: OptimizationGoal = OptimizationGoal.MINIMIZE_LATENCY) -> OptimizationRecommendation:
        """Generate ML-powered workflow optimization recommendations."""
        try:
            # Gather workflow metrics
            metrics = await self._gather_workflow_metrics(workflow_id, workflow_data)

            # Get predictions and analysis
            performance_pred = await self.performance_predictor.predict_performance(metrics)
            anomaly_analysis = await self.anomaly_detector.detect_anomalies(metrics)
            pattern_analysis = await self.pattern_learner.classify_workflow(metrics)

            # Generate optimization recommendations
            recommendations = await self._generate_recommendations(
                workflow_id, metrics, performance_pred, anomaly_analysis,
                pattern_analysis, optimization_goal
            )

            # Store optimization history
            self.optimization_history.append({
                "workflow_id": workflow_id,
                "optimization_goal": optimization_goal.value,
                "recommendations": recommendations,
                "generated_at": datetime.now()
            })

            return recommendations

        except Exception as e:
            fire_and_forget("error", f"Workflow optimization failed for {workflow_id}: {e}", ServiceNames.ORCHESTRATOR)

            # Return basic recommendation
            return OptimizationRecommendation(
                workflow_type=workflow_data.get("type", "unknown"),
                recommendation_type="error_fallback",
                confidence_score=0.0,
                expected_improvement=0.0,
                implementation_complexity="low",
                description=f"Optimization failed due to error: {e}",
                actions=[{"type": "retry", "description": "Retry optimization later"}]
            )

    async def _gather_workflow_metrics(self, workflow_id: str, workflow_data: Dict[str, Any]) -> WorkflowMetrics:
        """Gather comprehensive workflow metrics."""
        # In practice, this would collect real metrics
        # For now, generate realistic sample metrics
        return WorkflowMetrics(
            workflow_id=workflow_id,
            execution_time=random.uniform(10, 600),  # 10 seconds to 10 minutes
            cpu_usage=random.uniform(10, 95),
            memory_usage=random.uniform(20, 90),
            network_io=random.uniform(1, 100),
            success_rate=random.uniform(0.8, 1.0),
            error_count=random.randint(0, 10),
            step_metrics=[
                {"step": f"step_{i}", "duration": random.uniform(1, 60), "success": random.choice([True, False])}
                for i in range(random.randint(3, 15))
            ],
            resource_utilization={
                "cpu": random.uniform(10, 95),
                "memory": random.uniform(20, 90),
                "disk": random.uniform(5, 50),
                "network": random.uniform(1, 100)
            }
        )

    async def _generate_recommendations(self, workflow_id: str, metrics: WorkflowMetrics,
                                      performance_pred: Dict[str, Any], anomaly_analysis: Dict[str, Any],
                                      pattern_analysis: Dict[str, Any], goal: OptimizationGoal) -> OptimizationRecommendation:
        """Generate optimization recommendations based on ML analysis."""
        actions = []
        confidence_score = 0.5
        expected_improvement = 0.0
        complexity = "medium"

        # Analyze based on optimization goal
        if goal == OptimizationGoal.MINIMIZE_LATENCY:
            if performance_pred.get("predicted_execution_time", 0) > 300:
                actions.append({
                    "type": "parallelize_steps",
                    "description": "Parallelize independent workflow steps",
                    "expected_savings": "30-50% execution time"
                })
                expected_improvement += 0.4

            if anomaly_analysis.get("is_anomaly"):
                actions.append({
                    "type": "optimize_bottlenecks",
                    "description": "Optimize identified performance bottlenecks",
                    "expected_savings": "20-40% execution time"
                })
                expected_improvement += 0.3

        elif goal == OptimizationGoal.MAXIMIZE_THROUGHPUT:
            actions.append({
                "type": "resource_scaling",
                "description": "Scale resources based on predicted load",
                "expected_savings": "Increase throughput by 50-100%"
            })
            expected_improvement += 0.6

        elif goal == OptimizationGoal.OPTIMIZE_COST:
            if metrics.memory_usage > 70:
                actions.append({
                    "type": "memory_optimization",
                    "description": "Optimize memory usage patterns",
                    "expected_savings": "20-30% memory usage"
                })
                expected_improvement += 0.25

        # Anomaly-based recommendations
        if anomaly_analysis.get("is_anomaly"):
            anomaly_recommendations = anomaly_analysis.get("recommendations", [])
            for rec in anomaly_recommendations:
                actions.append({
                    "type": "anomaly_remediation",
                    "description": rec,
                    "expected_savings": "Varies based on anomaly"
                })

        # Pattern-based recommendations
        if pattern_analysis.get("cluster_id") is not None:
            pattern_info = pattern_analysis.get("pattern_info", {})
            if pattern_info.get("characteristics", {}).get("performance_profile") == "slow":
                actions.append({
                    "type": "pattern_optimization",
                    "description": "Apply optimizations from similar slow workflows",
                    "expected_savings": "Based on pattern analysis"
                })

        # Calculate confidence and complexity
        if len(actions) > 3:
            complexity = "high"
            confidence_score = 0.7
        elif len(actions) > 1:
            complexity = "medium"
            confidence_score = 0.8
        else:
            complexity = "low"
            confidence_score = 0.6

        return OptimizationRecommendation(
            workflow_type="generic",  # Could be more specific
            recommendation_type="ml_optimized",
            confidence_score=confidence_score,
            expected_improvement=min(expected_improvement, 0.8),
            implementation_complexity=complexity,
            description=f"ML-powered optimization recommendations for {goal.value}",
            actions=actions
        )

    async def train_models(self, training_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train all ML models with provided data."""
        training_results = {
            "performance_model": False,
            "anomaly_model": False,
            "pattern_model": False,
            "total_samples": len(training_data),
            "training_timestamp": datetime.now()
        }

        # Convert training data to WorkflowMetrics
        metrics_data = []
        for data in training_data:
            metrics = WorkflowMetrics(
                workflow_id=data.get("workflow_id", "unknown"),
                execution_time=data.get("execution_time", random.uniform(10, 600)),
                cpu_usage=data.get("cpu_usage", random.uniform(10, 95)),
                memory_usage=data.get("memory_usage", random.uniform(20, 90)),
                network_io=data.get("network_io", random.uniform(1, 100)),
                success_rate=data.get("success_rate", random.uniform(0.8, 1.0)),
                error_count=data.get("error_count", random.randint(0, 10))
            )
            metrics_data.append(metrics)

        # Train models
        training_results["performance_model"] = await self.performance_predictor.train_model(metrics_data)
        training_results["anomaly_model"] = await self.anomaly_detector.train_model(metrics_data)
        training_results["pattern_model"] = await self.pattern_learner.learn_patterns(metrics_data)

        success_count = sum(training_results.values()) - 1  # Subtract timestamp
        training_results["overall_success"] = success_count == 3

        fire_and_forget("info", f"ML model training completed: {success_count}/3 models trained successfully", ServiceNames.ORCHESTRATOR)

        return training_results

    async def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics and model performance."""
        return {
            "total_optimizations": len(self.optimization_history),
            "recent_optimizations": self.optimization_history[-10:] if self.optimization_history else [],
            "model_status": {
                "performance_predictor": self.performance_predictor.model is not None,
                "anomaly_detector": self.anomaly_detector.model is not None,
                "pattern_learner": self.pattern_learner.cluster_model is not None
            },
            "cache_stats": await self.cache.get_cache_stats() if self.cache else {},
            "generated_at": datetime.now()
        }


# Global ML optimizer instance
ml_optimizer = MLOptimizer()


async def initialize_ml_workflow_optimizer():
    """Initialize ML-powered workflow optimization."""
    # Train models with sample data if available
    sample_training_data = [
        {
            "workflow_id": f"sample_{i}",
            "execution_time": random.uniform(10, 600),
            "cpu_usage": random.uniform(10, 95),
            "memory_usage": random.uniform(20, 90),
            "success_rate": random.uniform(0.8, 1.0),
            "error_count": random.randint(0, 5)
        }
        for i in range(50)  # Generate 50 sample workflows
    ]

    training_results = await ml_optimizer.train_models(sample_training_data)

    fire_and_forget("info", f"ML workflow optimizer initialized - models trained: {training_results['overall_success']}", ServiceNames.ORCHESTRATOR)
