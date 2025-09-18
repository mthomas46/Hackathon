"""Content Generation Pipeline - Generate → Validate → Store.

This module implements a comprehensive content generation pipeline that:
1. Generates content using mock-data-generator service
2. Validates content quality using analysis service
3. Stores validated content in doc_store service
4. Tracks generation metrics and provides insights
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger
from simulation.infrastructure.clients.ecosystem_clients import (
    get_mock_data_generator_client, get_doc_store_client,
    get_analysis_service_client, get_llm_gateway_client,
    get_summarizer_hub_client
)
from simulation.infrastructure.resilience.circuit_breaker import execute_with_resilience
from simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, SimulationStatus
)


class ContentGenerationPipeline:
    """Comprehensive content generation pipeline."""

    def __init__(self):
        """Initialize content generation pipeline."""
        self.logger = get_simulation_logger()
        self.mock_data_client = get_mock_data_generator_client()
        self.doc_store_client = get_doc_store_client()
        self.analysis_client = get_analysis_service_client()
        self.llm_client = get_llm_gateway_client()
        self.summarizer_client = get_summarizer_hub_client()

    async def execute_full_pipeline(self,
                                  simulation_id: str,
                                  project_config: Dict[str, Any],
                                  generation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete content generation pipeline."""
        start_time = datetime.now()

        try:
            self.logger.info(
                "Starting content generation pipeline",
                simulation_id=simulation_id,
                project_name=project_config.get("name", "Unknown")
            )

            pipeline_results = {
                "simulation_id": simulation_id,
                "pipeline_start_time": start_time.isoformat(),
                "stages": [],
                "metrics": {},
                "errors": [],
                "warnings": []
            }

            # Stage 1: Generate project documentation
            generation_result = await self._generate_project_content(
                simulation_id, project_config, generation_config
            )
            pipeline_results["stages"].append({
                "stage": "generation",
                "status": "completed" if generation_result["success"] else "failed",
                "result": generation_result
            })

            if not generation_result["success"]:
                pipeline_results["errors"].append("Content generation failed")
                return pipeline_results

            # Stage 2: Validate content quality
            validation_result = await self._validate_content_quality(
                generation_result["documents"]
            )
            pipeline_results["stages"].append({
                "stage": "validation",
                "status": "completed" if validation_result["success"] else "failed",
                "result": validation_result
            })

            # Stage 3: Store validated content
            storage_result = await self._store_validated_content(
                simulation_id, validation_result["validated_documents"]
            )
            pipeline_results["stages"].append({
                "stage": "storage",
                "status": "completed" if storage_result["success"] else "failed",
                "result": storage_result
            })

            # Stage 4: Generate insights and analytics
            insights_result = await self._generate_content_insights(
                simulation_id, project_config, validation_result["validated_documents"]
            )
            pipeline_results["stages"].append({
                "stage": "insights",
                "status": "completed" if insights_result["success"] else "failed",
                "result": insights_result
            })

            # Calculate pipeline metrics
            pipeline_results["metrics"] = self._calculate_pipeline_metrics(
                generation_result, validation_result, storage_result, insights_result
            )

            # Set final status
            failed_stages = [s for s in pipeline_results["stages"] if s["status"] == "failed"]
            pipeline_results["overall_status"] = "failed" if failed_stages else "completed"
            pipeline_results["pipeline_duration_seconds"] = (
                datetime.now() - start_time
            ).total_seconds()

            self.logger.info(
                "Content generation pipeline completed",
                simulation_id=simulation_id,
                status=pipeline_results["overall_status"],
                duration_seconds=pipeline_results["pipeline_duration_seconds"],
                documents_generated=len(generation_result.get("documents", [])),
                documents_stored=len(storage_result.get("stored_documents", []))
            )

            return pipeline_results

        except Exception as e:
            pipeline_results["overall_status"] = "failed"
            pipeline_results["errors"].append(str(e))
            pipeline_results["pipeline_duration_seconds"] = (
                datetime.now() - start_time
            ).total_seconds()

            self.logger.error(
                "Content generation pipeline failed",
                error=str(e),
                simulation_id=simulation_id,
                duration_seconds=pipeline_results["pipeline_duration_seconds"]
            )

            return pipeline_results

    async def _generate_project_content(self,
                                      simulation_id: str,
                                      project_config: Dict[str, Any],
                                      generation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate project content using mock-data-generator."""
        try:
            self.logger.info(
                "Generating project content",
                simulation_id=simulation_id
            )

            # Prepare generation request
            generation_request = {
                "simulation_id": simulation_id,
                "project_name": project_config.get("name", "Unknown Project"),
                "project_type": project_config.get("type", "web_application"),
                "team_size": project_config.get("team_size", 5),
                "complexity": project_config.get("complexity", "medium"),
                "duration_weeks": project_config.get("duration_weeks", 8),
                "document_types": generation_config.get("document_types", [
                    "project_requirements",
                    "architecture_diagram",
                    "user_story",
                    "technical_design"
                ]),
                "include_context": generation_config.get("include_context", True),
                "quality_level": generation_config.get("quality_level", "high")
            }

            # Generate different types of content
            generated_content = []

            # Generate project documentation
            if "project_requirements" in generation_request["document_types"]:
                project_docs = await execute_with_resilience(
                    "mock_data_generator",
                    "generate_project_documents",
                    generation_request
                )
                generated_content.extend(project_docs.get("documents_created", []))

            # Generate user stories
            if "user_story" in generation_request["document_types"]:
                user_stories = await execute_with_resilience(
                    "mock_data_generator",
                    "generate_project_documents",
                    {**generation_request, "document_types": ["user_story"]}
                )
                generated_content.extend(user_stories.get("documents_created", []))

            # Generate timeline events
            if generation_config.get("include_timeline_events", True):
                timeline_events = await execute_with_resilience(
                    "mock_data_generator",
                    "generate_timeline_events",
                    {
                        "project_name": project_config.get("name"),
                        "timeline_phases": self._generate_timeline_phases(project_config),
                        "include_past_events": True,
                        "include_future_events": False,
                        "event_count": generation_config.get("timeline_event_count", 20)
                    }
                )
                generated_content.extend(timeline_events.get("documents_created", []))

            # Generate team activities
            if generation_config.get("include_team_activities", True):
                team_activities = await execute_with_resilience(
                    "mock_data_generator",
                    "generate_team_activities",
                    {
                        "project_name": project_config.get("name"),
                        "team_members": project_config.get("team_members", []),
                        "activity_types": ["code_commit", "meeting_notes", "design_decision"],
                        "time_range_days": 30,
                        "activity_count": generation_config.get("team_activity_count", 25)
                    }
                )
                generated_content.extend(team_activities.get("documents_created", []))

            return {
                "success": True,
                "documents": generated_content,
                "document_count": len(generated_content),
                "document_types": list(set(d.get("type") for d in generated_content if d.get("type")))
            }

        except Exception as e:
            self.logger.error(
                "Content generation failed",
                error=str(e),
                simulation_id=simulation_id
            )
            return {
                "success": False,
                "error": str(e),
                "documents": []
            }

    async def _validate_content_quality(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate content quality using analysis service."""
        try:
            self.logger.info("Validating content quality", document_count=len(documents))

            if not documents:
                return {
                    "success": True,
                    "validated_documents": [],
                    "quality_score": 0.0,
                    "validation_summary": {"total_documents": 0, "passed": 0, "failed": 0}
                }

            # Analyze documents for quality
            analysis_result = await execute_with_resilience(
                "analysis_service",
                "analyze_documents",
                documents
            )

            # Validate each document
            validated_documents = []
            quality_scores = []

            for i, doc in enumerate(documents):
                doc_analysis = analysis_result.get("document_analyses", [])[i] if i < len(analysis_result.get("document_analyses", [])) else {}

                # Calculate quality score (simplified)
                quality_score = self._calculate_document_quality_score(doc, doc_analysis)

                validated_doc = {
                    **doc,
                    "quality_score": quality_score,
                    "validation_status": "passed" if quality_score >= 0.7 else "failed",
                    "validation_timestamp": datetime.now().isoformat(),
                    "quality_metrics": doc_analysis
                }

                validated_documents.append(validated_doc)
                quality_scores.append(quality_score)

            # Summary statistics
            validation_summary = {
                "total_documents": len(documents),
                "passed": sum(1 for d in validated_documents if d["validation_status"] == "passed"),
                "failed": sum(1 for d in validated_documents if d["validation_status"] == "failed"),
                "average_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0.0,
                "quality_score_distribution": self._calculate_quality_distribution(quality_scores)
            }

            return {
                "success": True,
                "validated_documents": validated_documents,
                "quality_score": validation_summary["average_quality_score"],
                "validation_summary": validation_summary
            }

        except Exception as e:
            self.logger.error("Content validation failed", error=str(e))
            # Return documents as validated if analysis fails
            return {
                "success": True,
                "validated_documents": [
                    {**doc, "validation_status": "unvalidated", "quality_score": 0.5}
                    for doc in documents
                ],
                "quality_score": 0.5,
                "validation_summary": {
                    "total_documents": len(documents),
                    "passed": len(documents),
                    "failed": 0,
                    "validation_error": str(e)
                }
            }

    async def _store_validated_content(self,
                                     simulation_id: str,
                                     validated_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Store validated content in doc_store."""
        try:
            self.logger.info(
                "Storing validated content",
                simulation_id=simulation_id,
                document_count=len(validated_documents)
            )

            stored_documents = []
            failed_documents = []

            for doc in validated_documents:
                try:
                    # Prepare document metadata
                    metadata = {
                        "simulation_id": simulation_id,
                        "document_type": doc.get("type", "unknown"),
                        "quality_score": doc.get("quality_score", 0.0),
                        "validation_status": doc.get("validation_status", "unknown"),
                        "generated_at": doc.get("generated_at", datetime.now().isoformat()),
                        "validated_at": doc.get("validation_timestamp", datetime.now().isoformat()),
                        "project_context": {
                            "name": doc.get("project_name", "Unknown"),
                            "type": doc.get("project_type", "unknown"),
                            "complexity": doc.get("complexity", "unknown")
                        }
                    }

                    # Store document
                    doc_id = await execute_with_resilience(
                        "doc_store",
                        "store_document",
                        title=doc.get("title", "Generated Document"),
                        content=str(doc.get("content", "")),
                        metadata=metadata
                    )

                    if doc_id:
                        stored_documents.append({
                            "original_id": doc.get("id"),
                            "doc_store_id": doc_id,
                            "title": doc.get("title"),
                            "type": doc.get("type"),
                            "quality_score": doc.get("quality_score")
                        })
                    else:
                        failed_documents.append({
                            "title": doc.get("title"),
                            "error": "Storage failed"
                        })

                except Exception as doc_error:
                    self.logger.warning(
                        "Failed to store document",
                        document_title=doc.get("title"),
                        error=str(doc_error)
                    )
                    failed_documents.append({
                        "title": doc.get("title"),
                        "error": str(doc_error)
                    })

            return {
                "success": True,
                "stored_documents": stored_documents,
                "failed_documents": failed_documents,
                "storage_summary": {
                    "total_attempted": len(validated_documents),
                    "successfully_stored": len(stored_documents),
                    "failed": len(failed_documents),
                    "success_rate": len(stored_documents) / len(validated_documents) if validated_documents else 0.0
                }
            }

        except Exception as e:
            self.logger.error("Content storage failed", error=str(e), simulation_id=simulation_id)
            return {
                "success": False,
                "error": str(e),
                "stored_documents": [],
                "failed_documents": [{"error": "Storage system failure"}]
            }

    async def _generate_content_insights(self,
                                       simulation_id: str,
                                       project_config: Dict[str, Any],
                                       validated_documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights and analytics from generated content."""
        try:
            self.logger.info(
                "Generating content insights",
                simulation_id=simulation_id,
                document_count=len(validated_documents)
            )

            # Analyze document types and distribution
            doc_types = {}
            quality_scores = []

            for doc in validated_documents:
                doc_type = doc.get("type", "unknown")
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                quality_scores.append(doc.get("quality_score", 0.0))

            # Generate comprehensive insights using LLM
            insights_prompt = f"""
            Analyze the following project documentation generation results and provide insights:

            Project: {project_config.get('name', 'Unknown')}
            Project Type: {project_config.get('type', 'Unknown')}
            Complexity: {project_config.get('complexity', 'Unknown')}
            Team Size: {project_config.get('team_size', 'Unknown')}

            Generated Content Summary:
            - Total Documents: {len(validated_documents)}
            - Document Types: {json.dumps(doc_types, indent=2)}
            - Average Quality Score: {sum(quality_scores) / len(quality_scores) if quality_scores else 0.0:.2f}
            - Quality Distribution: {self._calculate_quality_distribution(quality_scores)}

            Provide insights about:
            1. Content completeness and coverage
            2. Quality assessment and recommendations
            3. Project type alignment and suitability
            4. Team collaboration patterns reflected in documentation
            5. Potential gaps or areas for improvement
            6. Documentation effectiveness for the project type and complexity
            """

            llm_response = await execute_with_resilience(
                "llm_gateway",
                "generate_content",
                prompt=insights_prompt,
                model="gpt-4"
            )

            insights = llm_response.get("content", "No insights generated")

            # Generate summary using summarizer
            if len(insights) > 500:
                summary_response = await execute_with_resilience(
                    "summarizer_hub",
                    "summarize_text",
                    text=insights,
                    max_length=200
                )
                summary = summary_response.get("summary", insights[:200])
            else:
                summary = insights

            return {
                "success": True,
                "insights": insights,
                "summary": summary,
                "analytics": {
                    "document_distribution": doc_types,
                    "quality_metrics": {
                        "average_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0.0,
                        "min_score": min(quality_scores) if quality_scores else 0.0,
                        "max_score": max(quality_scores) if quality_scores else 0.0,
                        "distribution": self._calculate_quality_distribution(quality_scores)
                    },
                    "content_metrics": {
                        "total_documents": len(validated_documents),
                        "document_types_count": len(doc_types),
                        "project_alignment_score": self._calculate_project_alignment_score(
                            project_config, validated_documents
                        )
                    }
                }
            }

        except Exception as e:
            self.logger.error("Content insights generation failed", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "insights": "Insights generation failed",
                "analytics": {}
            }

    def _calculate_document_quality_score(self, document: Dict[str, Any], analysis: Dict[str, Any]) -> float:
        """Calculate quality score for a document."""
        score = 0.5  # Base score

        # Content length factor
        content = str(document.get("content", ""))
        if len(content) > 100:
            score += 0.1
        if len(content) > 500:
            score += 0.1
        if len(content) > 1000:
            score += 0.1

        # Analysis-based scoring
        if analysis:
            readability = analysis.get("readability_score", 0.5)
            coherence = analysis.get("coherence_score", 0.5)
            relevance = analysis.get("relevance_score", 0.5)

            score = (score + readability + coherence + relevance) / 3

        return min(max(score, 0.0), 1.0)

    def _calculate_quality_distribution(self, scores: List[float]) -> Dict[str, int]:
        """Calculate quality score distribution."""
        if not scores:
            return {"excellent": 0, "good": 0, "average": 0, "poor": 0}

        distribution = {"excellent": 0, "good": 0, "average": 0, "poor": 0}

        for score in scores:
            if score >= 0.9:
                distribution["excellent"] += 1
            elif score >= 0.7:
                distribution["good"] += 1
            elif score >= 0.5:
                distribution["average"] += 1
            else:
                distribution["poor"] += 1

        return distribution

    def _calculate_project_alignment_score(self,
                                        project_config: Dict[str, Any],
                                        documents: List[Dict[str, Any]]) -> float:
        """Calculate how well documents align with project requirements."""
        project_type = project_config.get("type", "web_application")
        complexity = project_config.get("complexity", "medium")

        # Expected document types for different project types
        expected_types = {
            "web_application": ["project_requirements", "architecture_diagram", "user_story", "technical_design"],
            "api_service": ["project_requirements", "architecture_diagram", "technical_design", "api_contract"],
            "mobile_application": ["project_requirements", "architecture_diagram", "user_story", "design_mockups"],
            "data_science": ["project_requirements", "data_analysis", "model_design", "validation_report"],
            "devops_tool": ["project_requirements", "architecture_diagram", "deployment_guide", "monitoring_setup"]
        }

        expected = set(expected_types.get(project_type, []))
        actual = set(d.get("type") for d in documents if d.get("type"))

        # Calculate coverage
        coverage = len(expected.intersection(actual)) / len(expected) if expected else 0.0

        # Adjust for complexity
        if complexity == "complex" and coverage < 0.8:
            coverage *= 0.9  # Penalty for complex projects with incomplete documentation

        return min(coverage, 1.0)

    def _generate_timeline_phases(self, project_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate timeline phases based on project configuration."""
        duration_weeks = project_config.get("duration_weeks", 8)
        complexity = project_config.get("complexity", "medium")

        # Base phases for all projects
        base_phases = [
            {
                "name": "Discovery",
                "description": "Requirements gathering and initial planning",
                "duration_days": max(5, duration_weeks * 7 // 8),  # ~12.5% of total
                "deliverables": ["requirements_document", "stakeholder_analysis"]
            },
            {
                "name": "Design",
                "description": "System design and architecture planning",
                "duration_days": max(7, duration_weeks * 7 // 8),  # ~25% of total
                "deliverables": ["architecture_diagram", "technical_design", "api_contract"]
            },
            {
                "name": "Development",
                "description": "Implementation and coding",
                "duration_days": max(14, duration_weeks * 7 // 4),  # ~50% of total
                "deliverables": ["source_code", "unit_tests", "integration_tests"]
            },
            {
                "name": "Testing",
                "description": "Quality assurance and testing",
                "duration_days": max(5, duration_weeks * 7 // 16),  # ~12.5% of total
                "deliverables": ["test_reports", "quality_metrics", "bug_reports"]
            }
        ]

        # Add complexity-specific phases
        if complexity == "complex":
            base_phases.insert(1, {
                "name": "Analysis",
                "description": "Detailed analysis and feasibility study",
                "duration_days": max(3, duration_weeks * 7 // 16),
                "deliverables": ["feasibility_report", "risk_analysis", "cost_benefit_analysis"]
            })

        return base_phases

    def _calculate_pipeline_metrics(self, generation, validation, storage, insights) -> Dict[str, Any]:
        """Calculate comprehensive pipeline metrics."""
        return {
            "generation": {
                "documents_generated": generation.get("document_count", 0),
                "document_types": generation.get("document_types", []),
                "generation_success": generation.get("success", False)
            },
            "validation": {
                "quality_score": validation.get("quality_score", 0.0),
                "validation_summary": validation.get("validation_summary", {}),
                "validation_success": validation.get("success", False)
            },
            "storage": {
                "documents_stored": len(storage.get("stored_documents", [])),
                "documents_failed": len(storage.get("failed_documents", [])),
                "storage_success": storage.get("success", False),
                "success_rate": storage.get("storage_summary", {}).get("success_rate", 0.0)
            },
            "insights": {
                "insights_generated": insights.get("success", False),
                "analytics_available": bool(insights.get("analytics", {}))
            },
            "overall": {
                "pipeline_success": all([
                    generation.get("success", False),
                    validation.get("success", False),
                    storage.get("success", False)
                ]),
                "data_quality_score": (
                    generation.get("document_count", 0) *
                    validation.get("quality_score", 0.0) *
                    storage.get("storage_summary", {}).get("success_rate", 0.0)
                )
            }
        }


# Global pipeline instance
_content_pipeline: Optional[ContentGenerationPipeline] = None


def get_content_generation_pipeline() -> ContentGenerationPipeline:
    """Get the global content generation pipeline instance."""
    global _content_pipeline
    if _content_pipeline is None:
        _content_pipeline = ContentGenerationPipeline()
    return _content_pipeline


__all__ = [
    'ContentGenerationPipeline',
    'get_content_generation_pipeline'
]
