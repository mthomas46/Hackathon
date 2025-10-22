"""
Documentation Orchestrator

Coordinates multi-pass documentation generation process.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..analysis.analysis_engine import AnalysisReport

logger = logging.getLogger(__name__)


class PassType(Enum):
    """Documentation generation pass types."""
    ARCHITECTURE = "architecture"
    COMPONENT = "component"
    API_REFERENCE = "api_reference"
    EXAMPLES = "examples"
    SYNTHESIS = "synthesis"


class DocStatus(Enum):
    """Documentation generation status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DocConfig:
    """Documentation generation configuration."""
    # Pass configuration
    passes: List[PassType] = field(default_factory=lambda: [
        PassType.ARCHITECTURE,
        PassType.COMPONENT,
        PassType.API_REFERENCE,
        PassType.EXAMPLES,
        PassType.SYNTHESIS
    ])
    
    # Output configuration
    output_formats: List[str] = field(default_factory=lambda: ["markdown"])
    include_diagrams: bool = True
    include_examples: bool = True
    
    # Quality configuration
    validate_between_passes: bool = True
    min_quality_score: float = 0.7
    enable_quality_validation: bool = True  # Enable Phase 5 quality checks
    auto_queue_for_review: bool = True      # Auto-queue low-confidence docs
    
    # LLM configuration
    model: str = "llama3.2:latest"
    temperature: float = 0.7
    max_tokens: int = 4000


@dataclass
class PassResult:
    """Result of a single documentation pass."""
    pass_type: PassType
    status: DocStatus
    artifacts: List[Dict]  # Generated artifacts
    quality_score: float
    duration_seconds: float
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'pass_type': self.pass_type.value,
            'status': self.status.value,
            'artifacts': self.artifacts,
            'quality_score': self.quality_score,
            'duration_seconds': self.duration_seconds,
            'errors': self.errors
        }


@dataclass
class DocumentationSet:
    """Complete set of generated documentation."""
    run_id: str
    plan_id: str
    repo_id: str
    
    # Pass results
    pass_results: List[PassResult]
    
    # Overall metrics
    total_artifacts: int
    total_words: int
    overall_quality_score: float
    
    # Status
    status: DocStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    # Output
    output_path: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'run_id': self.run_id,
            'plan_id': self.plan_id,
            'repo_id': self.repo_id,
            'pass_results': [pr.to_dict() for pr in self.pass_results],
            'total_artifacts': self.total_artifacts,
            'total_words': self.total_words,
            'overall_quality_score': self.overall_quality_score,
            'status': self.status.value,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'output_path': self.output_path
        }


class DocumentationOrchestrator:
    """
    Orchestrates multi-pass documentation generation.
    
    Coordinates:
    - Pass 1: Architecture overview
    - Pass 2: Component details
    - Pass 3: API reference
    - Pass 4: Examples & guides
    - Pass 5: Synthesis & polish
    """
    
    def __init__(self):
        self.current_run = None
        logger.info("DocumentationOrchestrator initialized")
    
    async def generate_documentation(
        self,
        plan_id: str,
        analysis_report: AnalysisReport,
        config: Optional[DocConfig] = None
    ) -> DocumentationSet:
        """
        Generate complete documentation set.
        
        Args:
            plan_id: Processing plan ID
            analysis_report: Analysis results from Phase 3
            config: Documentation configuration
        
        Returns:
            Complete documentation set
        """
        if config is None:
            config = DocConfig()
        
        import uuid
        run_id = str(uuid.uuid4())
        
        logger.info(f"📚 Starting documentation generation for plan {plan_id}")
        logger.info(f"   Run ID: {run_id}")
        logger.info(f"   Passes: {[p.value for p in config.passes]}")
        
        started_at = datetime.utcnow()
        pass_results = []
        
        # Context accumulation across passes
        context = {
            'analysis_report': analysis_report,
            'previous_passes': []
        }
        
        try:
            # Execute each pass in sequence
            for pass_num, pass_type in enumerate(config.passes, 1):
                logger.info(f"\n{'='*60}")
                logger.info(f"Pass {pass_num}/{len(config.passes)}: {pass_type.value}")
                logger.info(f"{'='*60}")
                
                pass_result = await self._execute_pass(
                    pass_type=pass_type,
                    context=context,
                    config=config
                )
                
                pass_results.append(pass_result)
                
                # Add to context for next pass
                context['previous_passes'].append(pass_result)
                
                # Validate quality if configured
                if config.validate_between_passes:
                    if pass_result.quality_score < config.min_quality_score:
                        logger.warning(
                            f"⚠️ Quality score ({pass_result.quality_score:.2f}) below threshold "
                            f"({config.min_quality_score})"
                        )
                
                if pass_result.status == DocStatus.FAILED:
                    logger.error(f"❌ Pass {pass_type.value} failed, stopping generation")
                    break
            
            # Calculate overall metrics
            total_artifacts = sum(len(pr.artifacts) for pr in pass_results)
            total_words = sum(
                artifact.get('word_count', 0)
                for pr in pass_results
                for artifact in pr.artifacts
            )
            overall_quality = (
                sum(pr.quality_score for pr in pass_results) / len(pass_results)
                if pass_results else 0.0
            )
            
            # Determine final status
            if all(pr.status == DocStatus.COMPLETED for pr in pass_results):
                final_status = DocStatus.COMPLETED
            elif any(pr.status == DocStatus.FAILED for pr in pass_results):
                final_status = DocStatus.FAILED
            else:
                final_status = DocStatus.RUNNING
            
            doc_set = DocumentationSet(
                run_id=run_id,
                plan_id=plan_id,
                repo_id=analysis_report.repo_path.replace("/", "_")[-500:],
                pass_results=pass_results,
                total_artifacts=total_artifacts,
                total_words=total_words,
                overall_quality_score=overall_quality,
                status=final_status,
                started_at=started_at,
                completed_at=datetime.utcnow() if final_status == DocStatus.COMPLETED else None
            )
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ Documentation generation complete!")
            logger.info(f"   Run ID: {run_id}")
            logger.info(f"   Status: {final_status.value}")
            logger.info(f"   Total artifacts: {total_artifacts}")
            logger.info(f"   Total words: {total_words:,}")
            logger.info(f"   Quality score: {overall_quality:.2f}/1.0")
            logger.info(f"{'='*60}")
            
            # Run Phase 5 quality validation if enabled
            if config.enable_quality_validation and final_status == DocStatus.COMPLETED:
                logger.info("\n🔍 Running quality validation (Phase 5)...")
                if not config.auto_queue_for_review:
                    logger.info("   ⏭️  Review queue disabled - artifacts will not be queued for review")
                try:
                    quality_results = await self._run_quality_validation(
                        doc_set=doc_set,
                        analysis_report=analysis_report,
                        config=config
                    )
                    logger.info(f"   ✅ Quality validation complete")
                    logger.info(f"   📊 Avg Completeness: {quality_results['avg_completeness']:.2f}")
                    logger.info(f"   📊 Avg Accuracy: {quality_results['avg_accuracy']:.2f}")
                    logger.info(f"   📊 Avg Confidence: {quality_results['avg_confidence']:.2f}")
                    if quality_results['requiring_review'] > 0:
                        logger.info(f"   ⚠️  Requiring review: {quality_results['requiring_review']}/{total_artifacts}")
                except Exception as e:
                    logger.warning(f"   ⚠️  Quality validation failed: {e}")
            
            return doc_set
        
        except Exception as e:
            logger.error(f"❌ Documentation generation failed: {e}", exc_info=True)
            
            doc_set = DocumentationSet(
                run_id=run_id,
                plan_id=plan_id,
                repo_id=analysis_report.repo_path.replace("/", "_")[-500:],
                pass_results=pass_results,
                total_artifacts=0,
                total_words=0,
                overall_quality_score=0.0,
                status=DocStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
            
            return doc_set
    
    async def _execute_pass(
        self,
        pass_type: PassType,
        context: Dict,
        config: DocConfig
    ) -> PassResult:
        """Execute a single documentation pass."""
        import time
        start_time = time.time()
        
        try:
            artifacts = []
            errors = []
            
            if pass_type == PassType.ARCHITECTURE:
                artifacts = await self._generate_architecture_docs(context, config)
            elif pass_type == PassType.COMPONENT:
                artifacts = await self._generate_component_docs(context, config)
            elif pass_type == PassType.API_REFERENCE:
                artifacts = await self._generate_api_docs(context, config)
            elif pass_type == PassType.EXAMPLES:
                artifacts = await self._generate_examples(context, config)
            elif pass_type == PassType.SYNTHESIS:
                artifacts = await self._synthesize_docs(context, config)
            
            # Calculate quality score (placeholder - would be more sophisticated)
            quality_score = self._calculate_quality_score(artifacts)
            
            duration = time.time() - start_time
            
            logger.info(f"   ✅ Generated {len(artifacts)} artifact(s)")
            logger.info(f"   ⏱️ Duration: {duration:.1f}s")
            logger.info(f"   📊 Quality: {quality_score:.2f}/1.0")
            
            return PassResult(
                pass_type=pass_type,
                status=DocStatus.COMPLETED,
                artifacts=artifacts,
                quality_score=quality_score,
                duration_seconds=duration,
                errors=errors
            )
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"   ❌ Pass failed: {e}")
            
            return PassResult(
                pass_type=pass_type,
                status=DocStatus.FAILED,
                artifacts=[],
                quality_score=0.0,
                duration_seconds=duration,
                errors=[str(e)]
            )
    
    async def _generate_architecture_docs(
        self,
        context: Dict,
        config: DocConfig
    ) -> List[Dict]:
        """Generate architecture documentation (Pass 1)."""
        logger.info("   📐 Generating architecture overview...")
        
        # Use ArchitectureGenerator
        from .architecture_generator import ArchitectureGenerator
        
        generator = ArchitectureGenerator(model_router=getattr(self, 'model_router', None))
        analysis = context['analysis_report']
        
        artifacts = await generator.generate(
            analysis_report=analysis,
            context=context,
            config=config
        )
        
        return artifacts
    
    async def _generate_component_docs(
        self,
        context: Dict,
        config: DocConfig
    ) -> List[Dict]:
        """Generate component documentation (Pass 2)."""
        logger.info("   🧩 Generating component documentation...")
        
        # Use ComponentGenerator
        from .component_generator import ComponentGenerator
        
        generator = ComponentGenerator(model_router=getattr(self, 'model_router', None))
        analysis = context['analysis_report']
        
        artifacts = await generator.generate(
            analysis_report=analysis,
            context=context,
            config=config
        )
        
        return artifacts
    
    async def _generate_api_docs(
        self,
        context: Dict,
        config: DocConfig
    ) -> List[Dict]:
        """Generate API reference documentation (Pass 3)."""
        logger.info("   🔌 Generating API reference...")
        
        # Use APIReferenceGenerator
        from .api_generator import APIReferenceGenerator
        
        generator = APIReferenceGenerator(model_router=getattr(self, 'model_router', None))
        analysis = context['analysis_report']
        
        artifacts = await generator.generate(
            analysis_report=analysis,
            context=context,
            config=config
        )
        
        return artifacts
    
    async def _generate_examples(
        self,
        context: Dict,
        config: DocConfig
    ) -> List[Dict]:
        """Generate examples and guides (Pass 4)."""
        logger.info("   📚 Generating examples and guides...")
        
        # Use ExamplesGenerator
        from .examples_generator import ExamplesGenerator
        
        generator = ExamplesGenerator(model_router=getattr(self, 'model_router', None))
        analysis = context['analysis_report']
        
        artifacts = await generator.generate(
            analysis_report=analysis,
            context=context,
            config=config
        )
        
        return artifacts
    
    async def _synthesize_docs(
        self,
        context: Dict,
        config: DocConfig
    ) -> List[Dict]:
        """Synthesize and polish documentation (Pass 5)."""
        logger.info("   ✨ Synthesizing and polishing documentation...")
        
        # Use SynthesisGenerator
        from .synthesis_generator import SynthesisGenerator
        
        generator = SynthesisGenerator(model_router=getattr(self, 'model_router', None))
        analysis = context['analysis_report']
        
        artifacts = await generator.generate(
            analysis_report=analysis,
            context=context,
            config=config
        )
        
        return artifacts
    
    def _calculate_quality_score(self, artifacts: List[Dict]) -> float:
        """Calculate quality score for artifacts."""
        if not artifacts:
            return 0.0
        
        # Placeholder scoring - would be more sophisticated
        # Check for minimum content
        total_words = sum(a.get('word_count', 0) for a in artifacts)
        
        if total_words < 100:
            return 0.5
        elif total_words < 500:
            return 0.75
        else:
            return 0.9
    
    async def _run_quality_validation(
        self,
        doc_set: DocumentationSet,
        analysis_report: AnalysisReport,
        config: DocConfig
    ) -> Dict:
        """
        Run Phase 5 quality validation on generated documentation.
        
        Args:
            doc_set: Generated documentation set
            analysis_report: Analysis report from Phase 3
            config: Documentation configuration
        
        Returns:
            Dictionary of quality metrics
        """
        from ..quality import (
            get_completeness_checker,
            get_accuracy_validator,
            get_confidence_scorer,
            get_review_workflow_manager,
            get_quality_reporter
        )
        
        completeness_checker = get_completeness_checker()
        accuracy_validator = get_accuracy_validator()
        confidence_scorer = get_confidence_scorer()
        review_manager = get_review_workflow_manager()
        quality_reporter = get_quality_reporter()
        
        completeness_results = []
        accuracy_results = []
        confidence_scores = []
        requiring_review = 0
        
        # Validate each artifact
        for pass_result in doc_set.pass_results:
            for artifact in pass_result.artifacts:
                try:
                    # Run completeness check
                    comp_result = await completeness_checker.check(artifact)
                    completeness_results.append(comp_result)
                    
                    # Run accuracy validation
                    # Convert analysis_report to dict for validation
                    analysis_dict = {
                        'api_endpoints': getattr(analysis_report.service_map, 'endpoints', [])
                        if analysis_report.service_map else [],
                        'modularity_score': analysis_report.modularity_score
                    }
                    acc_result = await accuracy_validator.validate(
                        artifact,
                        analysis_report=analysis_dict
                    )
                    accuracy_results.append(acc_result)
                    
                    # Calculate confidence score
                    conf_score = await confidence_scorer.score(
                        artifact,
                        comp_result,
                        acc_result,
                        source_quality=analysis_report.modularity_score,
                        analysis_report=analysis_dict
                    )
                    confidence_scores.append(conf_score)
                    
                    # Queue for review if needed
                    if conf_score.requires_review:
                        if config.auto_queue_for_review:
                            await review_manager.queue_for_review(
                                artifact_id=artifact.get('id', 'unknown'),
                                artifact_title=artifact.get('title', 'Untitled'),
                                confidence_score=conf_score.overall_confidence,
                                priority=conf_score.review_priority,
                                issues=(
                                    comp_result.missing_sections[:3] +
                                    acc_result.code_example_issues[:3]
                                ),
                                recommendations=comp_result.recommendations[:5]
                            )
                            logger.info(f"📋 Queued for review: {artifact.get('title', 'Untitled')} (confidence: {conf_score.overall_confidence:.2f}, priority: {conf_score.review_priority})")
                            requiring_review += 1
                        else:
                            logger.info(f"⏭️  Skipped review queue: {artifact.get('title', 'Untitled')} (confidence: {conf_score.overall_confidence:.2f}) - review disabled by request")
                            # Still count as requiring review for metrics, but don't queue
                            requiring_review += 1
                
                except Exception as e:
                    logger.warning(f"Failed to validate artifact {artifact.get('title', 'unknown')}: {e}")
                    continue
        
        # Generate quality report
        if completeness_results and accuracy_results and confidence_scores:
            quality_report = await quality_reporter.generate_report(
                run_id=doc_set.run_id,
                completeness_results=completeness_results,
                accuracy_results=accuracy_results,
                confidence_scores=confidence_scores
            )
            
            return {
                'avg_completeness': quality_report.average_completeness,
                'avg_accuracy': quality_report.average_accuracy,
                'avg_confidence': quality_report.average_confidence,
                'requiring_review': requiring_review,
                'total_issues': quality_report.total_issues,
                'critical_issues': quality_report.critical_issues
            }
        else:
            return {
                'avg_completeness': 0.0,
                'avg_accuracy': 0.0,
                'avg_confidence': 0.0,
                'requiring_review': 0,
                'total_issues': 0,
                'critical_issues': 0
            }


# Singleton
_orchestrator_instance = None

def get_doc_orchestrator() -> DocumentationOrchestrator:
    """Get singleton documentation orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = DocumentationOrchestrator()
    return _orchestrator_instance

