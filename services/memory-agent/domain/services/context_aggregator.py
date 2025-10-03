"""
Context Aggregator - Phase 3 Day 4
Aggregates and synthesizes results from multiple workflows into unified views.
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from collections import defaultdict

from ..entities.memory_context import (
    MemoryContext,
    WorkflowResult,
    WorkflowType
)


class ContextAggregator:
    """
    Aggregates results from multiple workflows for Phase 3.
    
    Responsibilities:
    - Aggregate results from parallel workflows
    - Create unified context views
    - Extract key insights across workflows
    - Synthesize recommendations
    - Identify patterns and trends
    
    Part of Enhanced Roadmap v2.0 Phase 3 implementation.
    """
    
    def __init__(self):
        """Initialize Context Aggregator."""
        pass
    
    async def aggregate_parallel_workflows(
        self,
        workflow_contexts: List[MemoryContext]
    ) -> Dict[str, Any]:
        """
        Aggregate results from parallel workflows.
        
        Args:
            workflow_contexts: List of MemoryContext instances to aggregate
            
        Returns:
            Aggregated results dictionary
        """
        if not workflow_contexts:
            return self._empty_aggregation()
        
        aggregated = {
            "aggregation_timestamp": datetime.utcnow().isoformat(),
            "total_workflows": len(workflow_contexts),
            "workflow_types": {},
            "overall_success_rate": 0.0,
            "total_artifacts": 0,
            "total_duration_ms": 0.0,
            "services_called": set(),
            "documents": [],
            "prompts": [],
            "users": [],
            "custom_artifacts": [],
            "by_workflow_type": {},
            "insights": []
        }
        
        # Aggregate by workflow type
        successful_count = 0
        total_workflows_count = 0
        
        for context in workflow_contexts:
            workflow_type = context.workflow_type.value if isinstance(context.workflow_type, WorkflowType) else context.workflow_type
            
            # Count workflow types
            if workflow_type not in aggregated["workflow_types"]:
                aggregated["workflow_types"][workflow_type] = 0
            aggregated["workflow_types"][workflow_type] += 1
            
            # Aggregate success rate
            total_workflows_count += context.total_workflows
            successful_count += context.successful_workflows
            
            # Aggregate artifacts
            aggregated["total_artifacts"] += len(context.get_all_artifacts())
            aggregated["documents"].extend(context.linked_documents)
            aggregated["prompts"].extend(context.linked_prompts)
            aggregated["users"].extend(context.linked_users)
            
            # Aggregate workflow results
            for wf_id, result in context.workflow_results.items():
                aggregated["total_duration_ms"] += result.duration_ms
                aggregated["services_called"].update(result.services_called)
            
            # Store by workflow type
            if workflow_type not in aggregated["by_workflow_type"]:
                aggregated["by_workflow_type"][workflow_type] = []
            aggregated["by_workflow_type"][workflow_type].append({
                "workflow_id": context.workflow_id,
                "success_rate": context.success_rate,
                "total_artifacts": len(context.get_all_artifacts()),
                "created_at": context.created_at.isoformat()
            })
        
        # Calculate overall success rate
        if total_workflows_count > 0:
            aggregated["overall_success_rate"] = successful_count / total_workflows_count
        
        # Convert services set to list
        aggregated["services_called"] = list(aggregated["services_called"])
        
        # Remove duplicates from artifact lists
        aggregated["documents"] = list(set(aggregated["documents"]))
        aggregated["prompts"] = list(set(aggregated["prompts"]))
        aggregated["users"] = list(set(aggregated["users"]))
        
        return aggregated
    
    async def create_unified_view(
        self,
        workflow_results: List[WorkflowResult]
    ) -> Dict[str, Any]:
        """
        Create unified view of all workflow results.
        
        Args:
            workflow_results: List of WorkflowResult instances
            
        Returns:
            Unified view dictionary
        """
        if not workflow_results:
            return self._empty_unified_view()
        
        unified = {
            "created_at": datetime.utcnow().isoformat(),
            "total_results": len(workflow_results),
            "successful_results": 0,
            "failed_results": 0,
            "total_duration_ms": 0.0,
            "average_duration_ms": 0.0,
            "workflow_breakdown": defaultdict(int),
            "service_usage": defaultdict(int),
            "timeline": [],
            "performance_metrics": {},
            "error_summary": []
        }
        
        # Process each result
        for result in workflow_results:
            # Count successes and failures
            if result.success:
                unified["successful_results"] += 1
            else:
                unified["failed_results"] += 1
                if result.error_message:
                    unified["error_summary"].append({
                        "workflow_id": result.workflow_id,
                        "error": result.error_message
                    })
            
            # Aggregate durations
            unified["total_duration_ms"] += result.duration_ms
            
            # Count workflow types
            workflow_type = result.workflow_type.value if isinstance(result.workflow_type, WorkflowType) else result.workflow_type
            unified["workflow_breakdown"][workflow_type] += 1
            
            # Count service usage
            for service in result.services_called:
                unified["service_usage"][service] += 1
            
            # Add to timeline
            unified["timeline"].append({
                "workflow_id": result.workflow_id,
                "workflow_type": workflow_type,
                "started_at": result.started_at.isoformat(),
                "completed_at": result.completed_at.isoformat(),
                "duration_ms": result.duration_ms,
                "success": result.success
            })
        
        # Calculate averages
        if len(workflow_results) > 0:
            unified["average_duration_ms"] = unified["total_duration_ms"] / len(workflow_results)
        
        # Convert defaultdicts to regular dicts
        unified["workflow_breakdown"] = dict(unified["workflow_breakdown"])
        unified["service_usage"] = dict(unified["service_usage"])
        
        # Sort timeline by started_at
        unified["timeline"].sort(key=lambda x: x["started_at"])
        
        # Add performance metrics
        unified["performance_metrics"] = self._calculate_performance_metrics(workflow_results)
        
        return unified
    
    async def extract_key_insights(
        self,
        aggregated_results: Dict[str, Any]
    ) -> List[str]:
        """
        Extract key insights from aggregated results.
        
        Args:
            aggregated_results: Aggregated results dictionary
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Success rate insights
        success_rate = aggregated_results.get("overall_success_rate", 0.0)
        if success_rate == 1.0:
            insights.append("✅ Perfect success rate: All workflows completed successfully")
        elif success_rate >= 0.9:
            insights.append(f"✅ Excellent success rate: {success_rate*100:.0f}% of workflows succeeded")
        elif success_rate >= 0.7:
            insights.append(f"⚠️ Good success rate: {success_rate*100:.0f}% of workflows succeeded")
        else:
            insights.append(f"❌ Low success rate: {success_rate*100:.0f}% of workflows succeeded - investigate failures")
        
        # Artifact insights
        total_artifacts = aggregated_results.get("total_artifacts", 0)
        if total_artifacts > 100:
            insights.append(f"📊 High artifact volume: {total_artifacts} artifacts generated")
        elif total_artifacts > 50:
            insights.append(f"📊 Moderate artifact volume: {total_artifacts} artifacts generated")
        elif total_artifacts > 0:
            insights.append(f"📊 Low artifact volume: {total_artifacts} artifacts generated")
        
        # Service usage insights
        services_called = aggregated_results.get("services_called", [])
        if len(services_called) > 5:
            insights.append(f"🔗 High service integration: {len(services_called)} services utilized")
        elif len(services_called) > 0:
            insights.append(f"🔗 Service integration: {len(services_called)} services utilized")
        
        # Duration insights
        total_duration_ms = aggregated_results.get("total_duration_ms", 0.0)
        if total_duration_ms > 60000:  # > 1 minute
            insights.append(f"⏱️ Long execution: {total_duration_ms/1000:.1f}s total duration")
        elif total_duration_ms > 30000:  # > 30 seconds
            insights.append(f"⏱️ Moderate execution: {total_duration_ms/1000:.1f}s total duration")
        elif total_duration_ms > 0:
            insights.append(f"⚡ Fast execution: {total_duration_ms/1000:.1f}s total duration")
        
        # Workflow type diversity
        workflow_types = aggregated_results.get("workflow_types", {})
        if len(workflow_types) >= 4:
            insights.append(f"🌐 Comprehensive analysis: {len(workflow_types)} workflow types executed")
        elif len(workflow_types) > 1:
            insights.append(f"🌐 Multi-workflow execution: {len(workflow_types)} workflow types")
        
        # Team collaboration insights
        users = aggregated_results.get("users", [])
        if len(users) > 10:
            insights.append(f"👥 Large team: {len(users)} team members involved")
        elif len(users) > 5:
            insights.append(f"👥 Medium team: {len(users)} team members involved")
        elif len(users) > 0:
            insights.append(f"👥 Small team: {len(users)} team members involved")
        
        return insights
    
    async def synthesize_recommendations(
        self,
        aggregated_results: Dict[str, Any],
        unified_view: Dict[str, Any]
    ) -> List[str]:
        """
        Synthesize recommendations based on aggregated data.
        
        Args:
            aggregated_results: Aggregated results dictionary
            unified_view: Unified view dictionary
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Success rate recommendations
        success_rate = aggregated_results.get("overall_success_rate", 0.0)
        if success_rate < 0.9:
            failed_count = unified_view.get("failed_results", 0)
            recommendations.append(f"🔍 Investigate {failed_count} failed workflows to improve reliability")
        
        # Performance recommendations
        avg_duration = unified_view.get("average_duration_ms", 0.0)
        if avg_duration > 5000:  # > 5 seconds
            recommendations.append("⚡ Consider optimizing workflow performance - average duration exceeds 5s")
        
        # Service recommendations
        service_usage = unified_view.get("service_usage", {})
        if len(service_usage) < 3:
            recommendations.append("🔗 Consider leveraging more services for comprehensive analysis")
        
        # Artifact recommendations
        total_artifacts = aggregated_results.get("total_artifacts", 0)
        if total_artifacts < 10:
            recommendations.append("📊 Increase artifact generation for better traceability")
        
        # Workflow balance recommendations
        workflow_breakdown = unified_view.get("workflow_breakdown", {})
        if len(workflow_breakdown) == 1:
            recommendations.append("🌐 Consider running multiple workflow types for comprehensive planning")
        
        return recommendations
    
    async def identify_patterns(
        self,
        workflow_contexts: List[MemoryContext]
    ) -> Dict[str, Any]:
        """
        Identify patterns across multiple workflows.
        
        Args:
            workflow_contexts: List of MemoryContext instances
            
        Returns:
            Patterns dictionary
        """
        patterns = {
            "common_services": [],
            "frequent_artifacts": [],
            "workflow_sequences": [],
            "timing_patterns": {},
            "success_patterns": {}
        }
        
        if not workflow_contexts:
            return patterns
        
        # Find common services
        service_counts = defaultdict(int)
        for context in workflow_contexts:
            for result in context.workflow_results.values():
                for service in result.services_called:
                    service_counts[service] += 1
        
        # Services used in most workflows
        threshold = len(workflow_contexts) * 0.5
        patterns["common_services"] = [
            service for service, count in service_counts.items()
            if count >= threshold
        ]
        
        # Find frequent artifact types
        artifact_type_counts = defaultdict(int)
        for context in workflow_contexts:
            for artifact in context.get_all_artifacts():
                artifact_type_counts[artifact.artifact_type] += 1
        
        patterns["frequent_artifacts"] = [
            art_type for art_type, count in
            sorted(artifact_type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        # Analyze timing patterns
        durations_by_type = defaultdict(list)
        for context in workflow_contexts:
            workflow_type = context.workflow_type.value if isinstance(context.workflow_type, WorkflowType) else context.workflow_type
            for result in context.workflow_results.values():
                durations_by_type[workflow_type].append(result.duration_ms)
        
        for wf_type, durations in durations_by_type.items():
            if durations:
                patterns["timing_patterns"][wf_type] = {
                    "average_ms": sum(durations) / len(durations),
                    "min_ms": min(durations),
                    "max_ms": max(durations)
                }
        
        # Analyze success patterns
        for context in workflow_contexts:
            workflow_type = context.workflow_type.value if isinstance(context.workflow_type, WorkflowType) else context.workflow_type
            if workflow_type not in patterns["success_patterns"]:
                patterns["success_patterns"][workflow_type] = {
                    "total": 0,
                    "successful": 0
                }
            patterns["success_patterns"][workflow_type]["total"] += context.total_workflows
            patterns["success_patterns"][workflow_type]["successful"] += context.successful_workflows
        
        return patterns
    
    def _calculate_performance_metrics(
        self,
        workflow_results: List[WorkflowResult]
    ) -> Dict[str, Any]:
        """Calculate performance metrics from results."""
        if not workflow_results:
            return {}
        
        durations = [r.duration_ms for r in workflow_results]
        
        return {
            "fastest_ms": min(durations),
            "slowest_ms": max(durations),
            "median_ms": sorted(durations)[len(durations)//2],
            "total_ms": sum(durations),
            "p95_ms": sorted(durations)[int(len(durations)*0.95)] if len(durations) > 20 else max(durations)
        }
    
    def _empty_aggregation(self) -> Dict[str, Any]:
        """Return empty aggregation structure."""
        return {
            "aggregation_timestamp": datetime.utcnow().isoformat(),
            "total_workflows": 0,
            "workflow_types": {},
            "overall_success_rate": 0.0,
            "total_artifacts": 0,
            "total_duration_ms": 0.0,
            "services_called": [],
            "documents": [],
            "prompts": [],
            "users": [],
            "custom_artifacts": [],
            "by_workflow_type": {},
            "insights": []
        }
    
    def _empty_unified_view(self) -> Dict[str, Any]:
        """Return empty unified view structure."""
        return {
            "created_at": datetime.utcnow().isoformat(),
            "total_results": 0,
            "successful_results": 0,
            "failed_results": 0,
            "total_duration_ms": 0.0,
            "average_duration_ms": 0.0,
            "workflow_breakdown": {},
            "service_usage": {},
            "timeline": [],
            "performance_metrics": {},
            "error_summary": []
        }

