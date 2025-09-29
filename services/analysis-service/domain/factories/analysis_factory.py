"""Analysis factory for creating analysis entities with complex configuration."""

from typing import Dict, Any, List, Optional
from datetime import datetime

from ..entities import Analysis, AnalysisId, DocumentId
from ..entities.value_objects import AnalysisType, AnalysisConfiguration
from ..services import AnalysisService


class AnalysisFactory:
    """Factory for creating Analysis entities with complex configuration."""

    def __init__(self, analysis_service: Optional[AnalysisService] = None):
        """Initialize factory with optional analysis service."""
        self.analysis_service = analysis_service or AnalysisService({})

    def create_semantic_similarity_analysis(self, document_id: str,
                                          configuration: Optional[Dict[str, Any]] = None) -> Analysis:
        """Create semantic similarity analysis."""
        config = self._merge_config(configuration, {
            'detectors': ['semantic_similarity'],
            'options': {
                'threshold': 0.8,
                'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
                'similarity_metric': 'cosine'
            },
            'priority': 'normal',
            'timeout_seconds': 120
        })

        return self._create_analysis(document_id, AnalysisType.SEMANTIC_SIMILARITY, config)

    def create_sentiment_analysis(self, document_id: str,
                                 configuration: Optional[Dict[str, Any]] = None) -> Analysis:
        """Create sentiment analysis."""
        config = self._merge_config(configuration, {
            'detectors': ['sentiment'],
            'options': {
                'model': 'cardiffnlp/twitter-roberta-base-sentiment-latest',
                'include_confidence': True,
                'language': 'en'
            },
            'priority': 'normal',
            'timeout_seconds': 60
        })

        return self._create_analysis(document_id, AnalysisType.SENTIMENT, config)

    def create_content_quality_analysis(self, document_id: str,
                                       configuration: Optional[Dict[str, Any]] = None) -> Analysis:
        """Create content quality analysis."""
        config = self._merge_config(configuration, {
            'detectors': ['content_quality', 'readability', 'completeness'],
            'options': {
                'readability_metrics': ['flesch_kincaid', 'gunning_fog'],
                'quality_thresholds': {
                    'min_words': 50,
                    'max_complexity': 15.0
                },
                'check_completeness': True
            },
            'priority': 'normal',
            'timeout_seconds': 90
        })

        return self._create_analysis(document_id, AnalysisType.CONTENT_QUALITY, config)

    def create_trend_analysis(self, document_id: str,
                             configuration: Optional[Dict[str, Any]] = None) -> Analysis:
        """Create trend analysis."""
        config = self._merge_config(configuration, {
            'detectors': ['trend_analysis', 'quality_trends'],
            'options': {
                'time_window_days': 90,
                'metrics': ['quality_score', 'complexity', 'readability'],
                'forecast_period_days': 30,
                'confidence_interval': 0.95
            },
            'priority': 'normal',
            'timeout_seconds': 180
        })

        return self._create_analysis(document_id, AnalysisType.TREND_ANALYSIS, config)

    def create_risk_assessment(self, document_id: str,
                              configuration: Optional[Dict[str, Any]] = None) -> Analysis:
        """Create risk assessment analysis."""
        config = self._merge_config(configuration, {
            'detectors': ['risk_assessment', 'drift_detection'],
            'options': {
                'risk_factors': ['staleness', 'complexity', 'inconsistency'],
                'severity_thresholds': {
                    'high': 0.8,
                    'medium': 0.5,
                    'low': 0.2
                },
                'assessment_period_days': 180
            },
            'priority': 'high',
            'timeout_seconds': 120
        })

        return self._create_analysis(document_id, AnalysisType.RISK_ASSESSMENT, config)

    def create_maintenance_forecast(self, document_id: str,
                                   configuration: Optional[Dict[str, Any]] = None) -> Analysis:
        """Create maintenance forecast analysis."""
        config = self._merge_config(configuration, {
            'detectors': ['maintenance_forecast'],
            'options': {
                'forecast_horizon_days': 365,
                'update_frequency_days': 30,
                'confidence_level': 0.85,
                'factors': ['usage', 'complexity', 'team_size', 'dependencies']
            },
            'priority': 'normal',
            'timeout_seconds': 150
        })

        return self._create_analysis(document_id, AnalysisType.MAINTENANCE_FORECAST, config)

    def create_quality_degradation_detection(self, document_id: str,
                                           configuration: Optional[Dict[str, Any]] = None) -> Analysis:
        """Create quality degradation detection analysis."""
        config = self._merge_config(configuration, {
            'detectors': ['quality_degradation', 'trend_analysis'],
            'options': {
                'baseline_period_days': 90,
                'degradation_threshold': 0.1,
                'alert_sensitivity': 'medium',
                'metrics': ['readability', 'consistency', 'completeness']
            },
            'priority': 'high',
            'timeout_seconds': 120
        })

        return self._create_analysis(document_id, AnalysisType.QUALITY_DEGRADATION, config)

    def create_change_impact_analysis(self, document_id: str,
                                     configuration: Optional[Dict[str, Any]] = None) -> Analysis:
        """Create change impact analysis."""
        config = self._merge_config(configuration, {
            'detectors': ['change_impact', 'dependency_analysis'],
            'options': {
                'impact_scope': 'related_documents',
                'depth': 2,
                'include_external_dependencies': True,
                'risk_assessment': True
            },
            'priority': 'high',
            'timeout_seconds': 180
        })

        return self._create_analysis(document_id, AnalysisType.CHANGE_IMPACT, config)

    def create_cross_repository_analysis(self, document_id: str,
                                        configuration: Optional[Dict[str, Any]] = None) -> Analysis:
        """Create cross-repository analysis."""
        config = self._merge_config(configuration, {
            'detectors': ['cross_repository', 'consistency_check'],
            'options': {
                'repositories': [],  # To be filled by caller
                'analysis_scope': 'organization',
                'compare_metrics': ['quality', 'consistency', 'coverage'],
                'include_dependencies': True,
                'max_repositories': 50
            },
            'priority': 'normal',
            'timeout_seconds': 300
        })

        return self._create_analysis(document_id, AnalysisType.CROSS_REPOSITORY, config)

    def create_automated_remediation(self, document_id: str,
                                    configuration: Optional[Dict[str, Any]] = None) -> Analysis:
        """Create automated remediation analysis."""
        config = self._merge_config(configuration, {
            'detectors': ['automated_remediation'],
            'options': {
                'remediation_types': ['formatting', 'grammar', 'terminology'],
                'auto_apply': False,  # Preview mode by default
                'confidence_threshold': 0.9,
                'backup_original': True
            },
            'priority': 'normal',
            'timeout_seconds': 120
        })

        return self._create_analysis(document_id, AnalysisType.AUTOMATED_REMEDIATION, config)

    def create_comprehensive_analysis(self, document_id: str,
                                     configuration: Optional[Dict[str, Any]] = None) -> Analysis:
        """Create comprehensive analysis with all detectors."""
        base_config = {
            'detectors': [
                'semantic_similarity', 'sentiment', 'content_quality',
                'trend_analysis', 'risk_assessment', 'maintenance_forecast',
                'quality_degradation', 'change_impact', 'cross_repository'
            ],
            'options': {
                'parallel_execution': True,
                'fail_fast': False,
                'report_format': 'comprehensive'
            },
            'priority': 'high',
            'timeout_seconds': 600  # 10 minutes for comprehensive analysis
        }

        config = self._merge_config(configuration, base_config)

        # Custom analysis type for comprehensive analysis
        return self._create_analysis(document_id, AnalysisType.SEMANTIC_SIMILARITY, config)

    def create_custom_analysis(self, document_id: str, analysis_type: AnalysisType,
                              custom_config: Dict[str, Any]) -> Analysis:
        """Create custom analysis with user-defined configuration."""
        return self._create_analysis(document_id, analysis_type, custom_config)

    def create_batch_analysis(self, document_ids: List[str],
                             analysis_type: AnalysisType,
                             configuration: Optional[Dict[str, Any]] = None) -> List[Analysis]:
        """Create batch analysis for multiple documents."""
        analyses = []
        base_config = configuration or {}

        for doc_id in document_ids:
            # Add batch-specific configuration
            batch_config = self._merge_config(base_config, {
                'batch_id': f"batch_{datetime.now().timestamp()}",
                'batch_size': len(document_ids),
                'position_in_batch': len(analyses)
            })

            analysis = self._create_analysis(doc_id, analysis_type, batch_config)
            analyses.append(analysis)

        return analyses

    def _create_analysis(self, document_id: str, analysis_type: AnalysisType,
                        configuration: Dict[str, Any]) -> Analysis:
        """Internal method to create analysis with proper validation."""
        doc_id = DocumentId(document_id)
        analysis_config = AnalysisConfiguration(**configuration)

        return self.analysis_service.create_analysis(
            document=None,  # Will be set by caller
            analysis_type=analysis_type,
            configuration=analysis_config
        )

    def _merge_config(self, custom_config: Optional[Dict[str, Any]],
                     default_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge custom configuration with defaults."""
        if not custom_config:
            return default_config.copy()

        merged = default_config.copy()

        # Deep merge options
        if 'options' in custom_config:
            merged['options'] = {**merged.get('options', {}), **custom_config['options']}

        # Override other top-level keys
        for key, value in custom_config.items():
            if key != 'options':
                merged[key] = value

        return merged

    def get_available_analysis_types(self) -> List[str]:
        """Get list of available analysis types."""
        return [analysis_type.value for analysis_type in AnalysisType]

    def get_default_configuration(self, analysis_type: str) -> Dict[str, Any]:
        """Get default configuration for analysis type."""
        defaults = {
            'semantic_similarity': {
                'detectors': ['semantic_similarity'],
                'options': {'threshold': 0.8},
                'priority': 'normal',
                'timeout_seconds': 120
            },
            'sentiment': {
                'detectors': ['sentiment'],
                'options': {'model': 'default'},
                'priority': 'normal',
                'timeout_seconds': 60
            },
            'content_quality': {
                'detectors': ['content_quality'],
                'options': {'metrics': ['readability', 'completeness']},
                'priority': 'normal',
                'timeout_seconds': 90
            }
        }

        return defaults.get(analysis_type, {
            'detectors': [analysis_type],
            'options': {},
            'priority': 'normal',
            'timeout_seconds': 120
        })
