"""
Workflow E Orchestrator - Phase 9
Orchestrates the complete external service discovery, validation, and accuracy enhancement pipeline.
"""

from typing import Dict, Any, Optional
import time
from datetime import datetime

from .external_service_discovery_engine import ExternalServiceDiscoveryEngine
from .external_service_cataloger import ExternalServiceCataloger
from .integration_compliance_validator import IntegrationComplianceValidator
from .knowledge_gap_detector import KnowledgeGapDetector
from .development_blindspot_detector import DevelopmentBlindspotDetector
from .accuracy_enhancement_engine import AccuracyEnhancementEngine
from .workflow_e_fallback_engine import WorkflowEFallbackEngine

from ..entities.external_service_entities import WorkflowEResult


class WorkflowEOrchestrator:
    """
    Orchestrates Workflow E: External Service Discovery, Validation & Accuracy Enhancement
    
    Pipeline:
    1. Discovery (1.5s) - Find relevant external services
    2. Cataloging (1.0s) - Store and link to team/docs/history
    3. Validation (2.5s) - Compliance checking
    4. Gap Detection (2.2s) - Knowledge gaps
    5. Blindspot Detection (1.8s) - Development risks
    6. Accuracy Enhancement (1.0s) - Plan corrections
    
    Total: ~10 seconds
    """
    
    def __init__(
        self,
        # Discovery
        external_service_store_client=None,
        
        # Cataloging
        user_store_client=None,
        source_agent_client=None,
        doc_store_client=None,
        
        # Validation
        secure_analyzer_client=None,
        code_analyzer_client=None,
        analysis_service_client=None,
        
        # Gap Detection
        summarizer_hub_client=None,
        
        # Blindspot Detection
        github_mcp_client=None,
        project_simulation_client=None,
        
        # Logging
        log_client=None
    ):
        """Initialize Workflow E with all required service clients."""
        self.log_client = log_client
        
        # Check if any service clients are provided
        self.use_fallback = all(client is None for client in [
            external_service_store_client, user_store_client, source_agent_client,
            doc_store_client, secure_analyzer_client, code_analyzer_client,
            analysis_service_client, summarizer_hub_client, github_mcp_client,
            project_simulation_client
        ])
        
        # Initialize fallback engine if needed
        if self.use_fallback:
            self.fallback_engine = WorkflowEFallbackEngine()
            if log_client:
                # Log that we're using fallback mode (non-async, just set a flag)
                pass
        
        # Initialize all engines
        self.discovery_engine = ExternalServiceDiscoveryEngine(
            external_service_store_client=external_service_store_client,
            log_client=log_client
        )
        
        self.cataloger = ExternalServiceCataloger(
            external_service_store_client=external_service_store_client,
            user_store_client=user_store_client,
            source_agent_client=source_agent_client,
            doc_store_client=doc_store_client,
            log_client=log_client
        )
        
        self.validator = IntegrationComplianceValidator(
            secure_analyzer_client=secure_analyzer_client,
            code_analyzer_client=code_analyzer_client,
            analysis_service_client=analysis_service_client,
            log_client=log_client
        )
        
        self.gap_detector = KnowledgeGapDetector(
            doc_store_client=doc_store_client,
            user_store_client=user_store_client,
            summarizer_hub_client=summarizer_hub_client,
            log_client=log_client
        )
        
        self.blindspot_detector = DevelopmentBlindspotDetector(
            github_mcp_client=github_mcp_client,
            code_analyzer_client=code_analyzer_client,
            project_simulation_client=project_simulation_client,
            analysis_service_client=analysis_service_client,
            log_client=log_client
        )
        
        self.accuracy_engine = AccuracyEnhancementEngine(
            log_client=log_client
        )
    
    async def execute_workflow_e(
        self,
        feature_query: str,
        extracted_requirements: Dict[str, Any],
        original_plan: Dict[str, Any]
    ) -> WorkflowEResult:
        """
        Execute the complete Workflow E pipeline.
        
        Args:
            feature_query: The original natural language feature request
            extracted_requirements: Structured requirements from interpreter
            original_plan: Original planning estimates (SP, weeks, confidence)
        
        Returns:
            Complete Workflow E result with accuracy enhancement
        """
        start_time = time.time()
        
        # Check if using fallback mode
        if self.use_fallback:
            if self.log_client:
                await self.log_client.log_info(
                    "⚡ Using Fallback Mode: No service clients provided, using database + smart defaults",
                    context={
                        "query_length": len(feature_query),
                        "original_sp": original_plan.get("story_points", 0)
                    }
                )
            
            # Use fallback engine for realistic results
            result = self.fallback_engine.generate_realistic_workflow_e_result(
                feature_query, extracted_requirements, original_plan
            )
            
            if self.log_client:
                await self.log_client.log_info(
                    f"✅ Fallback Complete: {result.total_services_discovered} services, "
                    f"{result.total_validation_issues} issues, "
                    f"{result.total_knowledge_gaps} gaps, "
                    f"{result.total_blindspots} blindspots",
                    context={"execution_time": result.execution_time_seconds}
                )
            
            return result
        
        # Full service integration path
        if self.log_client:
            await self.log_client.log_info(
                "🚀 Starting Workflow E: External Service Discovery & Accuracy Enhancement",
                context={
                    "query_length": len(feature_query),
                    "original_sp": original_plan.get("story_points", 0),
                    "original_confidence": original_plan.get("confidence", 0)
                }
            )
        
        try:
            # Phase 1: Discovery (1.5s)
            phase1_start = time.time()
            discovered_services = await self.discovery_engine.discover_services(
                feature_query=feature_query,
                extracted_requirements=extracted_requirements
            )
            phase1_time = time.time() - phase1_start
            
            if self.log_client:
                await self.log_client.log_info(
                    f"✅ Phase 1 Complete: Discovered {len(discovered_services)} services ({phase1_time:.2f}s)",
                    context={
                        "services_found": len(discovered_services),
                        "high_relevance": len([s for s in discovered_services if s.relevance_score >= 0.85])
                    }
                )
            
            # Phase 2: Cataloging (1.0s)
            phase2_start = time.time()
            cataloged_services = await self.cataloger.catalog_services(
                services=discovered_services,
                feature_context=feature_query
            )
            phase2_time = time.time() - phase2_start
            
            if self.log_client:
                await self.log_client.log_info(
                    f"✅ Phase 2 Complete: Cataloged {len(cataloged_services)} services ({phase2_time:.2f}s)",
                    context={
                        "cataloged": len(cataloged_services),
                        "avg_coverage": sum(s.coverage_score for s in cataloged_services) / len(cataloged_services) if cataloged_services else 0
                    }
                )
            
            # Phase 3: Validation (2.5s)
            phase3_start = time.time()
            validation_results = await self.validator.validate_services(
                cataloged_services=cataloged_services,
                feature_requirements=extracted_requirements
            )
            phase3_time = time.time() - phase3_start
            
            total_validation_issues = sum(len(vr.issues) for vr in validation_results)
            if self.log_client:
                await self.log_client.log_info(
                    f"✅ Phase 3 Complete: Validated {len(validation_results)} services ({phase3_time:.2f}s)",
                    context={
                        "total_issues": total_validation_issues,
                        "critical_high": sum(len([i for i in vr.issues if i.severity.value in ["critical", "high"]]) for vr in validation_results)
                    }
                )
            
            # Phase 4: Gap Detection (2.2s)
            phase4_start = time.time()
            gap_analyses = await self.gap_detector.detect_gaps(
                cataloged_services=cataloged_services
            )
            phase4_time = time.time() - phase4_start
            
            total_gaps = sum(
                len(ga.documentation_gaps) + len(ga.skills_gaps) + len(ga.configuration_gaps)
                for ga in gap_analyses
            )
            if self.log_client:
                await self.log_client.log_info(
                    f"✅ Phase 4 Complete: Detected gaps for {len(gap_analyses)} services ({phase4_time:.2f}s)",
                    context={
                        "total_gaps": total_gaps,
                        "doc_gaps": sum(len(ga.documentation_gaps) for ga in gap_analyses),
                        "skills_gaps": sum(len(ga.skills_gaps) for ga in gap_analyses),
                        "config_gaps": sum(len(ga.configuration_gaps) for ga in gap_analyses)
                    }
                )
            
            # Phase 5: Blindspot Detection (1.8s)
            phase5_start = time.time()
            blindspot_analyses = await self.blindspot_detector.detect_blindspots(
                cataloged_services=cataloged_services,
                feature_requirements=extracted_requirements
            )
            phase5_time = time.time() - phase5_start
            
            total_blindspots = sum(len(ba.blindspots) for ba in blindspot_analyses)
            if self.log_client:
                await self.log_client.log_info(
                    f"✅ Phase 5 Complete: Detected blindspots for {len(blindspot_analyses)} services ({phase5_time:.2f}s)",
                    context={
                        "total_blindspots": total_blindspots,
                        "critical": sum(ba.severity_distribution.get("critical", 0) for ba in blindspot_analyses),
                        "high": sum(ba.severity_distribution.get("high", 0) for ba in blindspot_analyses)
                    }
                )
            
            # Phase 6: Accuracy Enhancement (1.0s)
            phase6_start = time.time()
            total_execution_time = time.time() - start_time
            workflow_result = await self.accuracy_engine.enhance_accuracy(
                original_plan=original_plan,
                discovered_services=discovered_services,
                cataloged_services=cataloged_services,
                validation_results=validation_results,
                gap_analyses=gap_analyses,
                blindspot_analyses=blindspot_analyses,
                execution_time=total_execution_time
            )
            phase6_time = time.time() - phase6_start
            
            acc = workflow_result.accuracy_enhancement
            if self.log_client:
                await self.log_client.log_info(
                    f"✅ Phase 6 Complete: Accuracy enhanced ({phase6_time:.2f}s)",
                    context={
                        "original_confidence": acc.original_confidence,
                        "adjusted_confidence": acc.adjusted_confidence,
                        "confidence_improvement": acc.confidence_improvement,
                        "sp_added": acc.story_points_added,
                        "weeks_added": acc.weeks_added
                    }
                )
            
            # Final Summary
            total_time = time.time() - start_time
            if self.log_client:
                await self.log_client.log_info(
                    f"🎉 Workflow E Complete in {total_time:.2f}s",
                    context={
                        "services_discovered": len(discovered_services),
                        "total_issues_found": total_validation_issues + total_gaps + total_blindspots,
                        "confidence_improvement": f"{acc.original_confidence}% → {acc.adjusted_confidence}%",
                        "sp_correction": f"{acc.original_story_points} → {acc.adjusted_story_points} (+{acc.story_points_added})",
                        "phase_times": {
                            "discovery": f"{phase1_time:.2f}s",
                            "cataloging": f"{phase2_time:.2f}s",
                            "validation": f"{phase3_time:.2f}s",
                            "gap_detection": f"{phase4_time:.2f}s",
                            "blindspot_detection": f"{phase5_time:.2f}s",
                            "accuracy_enhancement": f"{phase6_time:.2f}s"
                        }
                    }
                )
            
            return workflow_result
            
        except Exception as e:
            if self.log_client:
                await self.log_client.log_error(
                    f"❌ Workflow E failed: {str(e)}",
                    context={"error": str(e), "type": type(e).__name__}
                )
            raise
    
    async def get_workflow_feedback(
        self,
        workflow_result: WorkflowEResult
    ) -> Dict[str, Any]:
        """
        Generate feedback for Workflows A-D based on Workflow E results.
        
        Returns:
            Dict with updates for each workflow
        """
        return await self.accuracy_engine.generate_workflow_feedback(workflow_result)

