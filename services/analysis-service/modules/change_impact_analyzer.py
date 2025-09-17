"""Change Impact Analysis module for Analysis Service.

Analyzes how document changes affect related content, dependencies, and the overall
documentation ecosystem, providing insights for change management and impact assessment.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json
import re

try:
    import pandas as pd
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.preprocessing import normalize
    import networkx as nx
    from difflib import SequenceMatcher
    import warnings
    warnings.filterwarnings('ignore')
    CHANGE_IMPACT_AVAILABLE = True
except ImportError:
    CHANGE_IMPACT_AVAILABLE = False
    pd = None
    np = None
    cosine_similarity = None
    TfidfVectorizer = None
    normalize = None
    nx = None
    SequenceMatcher = None

from services.shared.core.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes

logger = logging.getLogger(__name__)


class ChangeImpactAnalyzer:
    """Analyzes the impact of document changes on related content and dependencies."""

    def __init__(self):
        """Initialize the change impact analyzer."""
        self.initialized = False
        self.impact_thresholds = self._get_default_impact_thresholds()
        self.relationship_types = self._get_relationship_types()
        self._initialize_analyzer()

    def _initialize_analyzer(self) -> bool:
        """Initialize the change impact analysis components."""
        if not CHANGE_IMPACT_AVAILABLE:
            logger.warning("Change impact analysis dependencies not available")
            return False

        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.initialized = True
        return True

    def _get_default_impact_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Define default impact analysis thresholds."""
        return {
            'semantic_similarity': {
                'high_impact': 0.8,      # High similarity indicates strong relationship
                'medium_impact': 0.6,    # Medium similarity indicates moderate relationship
                'low_impact': 0.4,       # Low similarity indicates weak relationship
                'minimal_impact': 0.2    # Minimal similarity indicates negligible relationship
            },
            'content_overlap': {
                'critical_overlap': 0.8,  # Critical overlap requiring immediate attention
                'high_overlap': 0.6,      # High overlap requiring review
                'medium_overlap': 0.4,    # Medium overlap for awareness
                'low_overlap': 0.2        # Low overlap, minimal concern
            },
            'stakeholder_impact': {
                'critical': ['api_reference', 'security', 'compliance'],
                'high': ['user_guide', 'tutorial', 'getting_started'],
                'medium': ['internal_docs', 'developer_guide'],
                'low': ['changelog', 'readme', 'contributing']
            },
            'change_severity': {
                'breaking_change': ['api_endpoint_removal', 'parameter_removal', 'response_format_change'],
                'major_change': ['new_feature', 'behavior_change', 'deprecation'],
                'minor_change': ['bug_fix', 'documentation_update', 'formatting_change'],
                'trivial_change': ['typo_fix', 'grammar_correction']
            }
        }

    def _get_relationship_types(self) -> Dict[str, Dict[str, Any]]:
        """Define relationship types between documents."""
        return {
            'parent_child': {
                'description': 'Hierarchical relationship (e.g., guide -> section)',
                'impact_multiplier': 1.0,
                'propagation_rules': ['direct', 'inherited']
            },
            'reference_link': {
                'description': 'Explicit reference or link between documents',
                'impact_multiplier': 0.9,
                'propagation_rules': ['direct', 'referenced']
            },
            'semantic_similarity': {
                'description': 'Content similarity based on meaning and context',
                'impact_multiplier': 0.7,
                'propagation_rules': ['similar', 'contextual']
            },
            'dependency': {
                'description': 'One document depends on information from another',
                'impact_multiplier': 0.8,
                'propagation_rules': ['direct', 'dependent']
            },
            'prerequisite': {
                'description': 'One document is a prerequisite for understanding another',
                'impact_multiplier': 0.6,
                'propagation_rules': ['prerequisite', 'sequential']
            },
            'complementary': {
                'description': 'Documents complement each other but are not directly related',
                'impact_multiplier': 0.4,
                'propagation_rules': ['complementary', 'supporting']
            }
        }

    def _extract_document_features(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from document for impact analysis."""
        content = document_data.get('content', '')
        metadata = document_data.get('metadata', {})

        features = {
            'document_id': document_data.get('document_id', ''),
            'title': document_data.get('title', ''),
            'document_type': document_data.get('document_type', 'unknown'),
            'tags': document_data.get('tags', []),
            'word_count': len(content.split()) if content else 0,
            'character_count': len(content) if content else 0,
            'code_blocks': len(re.findall(r'```[\s\S]*?```', content)),
            'links': len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)),
            'headings': len(re.findall(r'^#{1,6}\s+.+', content, re.MULTILINE)),
            'api_endpoints': len(re.findall(r'`(GET|POST|PUT|DELETE|PATCH)\s+[^`]+`', content)),
            'technical_terms': self._extract_technical_terms(content),
            'stakeholder_groups': self._identify_stakeholder_groups(document_data),
            'business_criticality': metadata.get('business_criticality', 'medium')
        }

        return features

    def _extract_technical_terms(self, content: str) -> List[str]:
        """Extract technical terms from document content."""
        # Common technical terms and patterns
        technical_patterns = [
            r'\b(API|REST|HTTP|JSON|XML|database|authentication|authorization)\b',
            r'\b(function|method|class|interface|component|service)\b',
            r'\b(configuration|deployment|integration|migration|upgrade)\b',
            r'\b(security|encryption|authentication|authorization|SSL|TLS)\b',
            r'\b(performance|optimization|caching|load\s+balancing)\b',
            r'\b(error|exception|handling|debugging|logging|monitoring)\b'
        ]

        technical_terms = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            technical_terms.extend(matches)

        return list(set(technical_terms))  # Remove duplicates

    def _identify_stakeholder_groups(self, document_data: Dict[str, Any]) -> List[str]:
        """Identify stakeholder groups affected by the document."""
        content = document_data.get('content', '').lower()
        document_type = document_data.get('document_type', '').lower()
        tags = [tag.lower() for tag in document_data.get('tags', [])]

        stakeholder_groups = []

        # Analyze content for stakeholder indicators
        if any(term in content for term in ['user', 'customer', 'end-user', 'consumer']):
            stakeholder_groups.append('end_users')
        if any(term in content for term in ['developer', 'engineer', 'programmer', 'coder']):
            stakeholder_groups.append('developers')
        if any(term in content for term in ['admin', 'administrator', 'operator', 'devops']):
            stakeholder_groups.append('administrators')
        if any(term in content for term in ['manager', 'lead', 'architect', 'director']):
            stakeholder_groups.append('management')
        if any(term in content for term in ['security', 'compliance', 'audit', 'governance']):
            stakeholder_groups.append('security_compliance')
        if any(term in content for term in ['support', 'helpdesk', 'customer service']):
            stakeholder_groups.append('support_team')

        # Analyze document type
        if document_type in ['api_reference', 'developer_guide']:
            stakeholder_groups.extend(['developers', 'administrators'])
        elif document_type in ['user_guide', 'tutorial', 'getting_started']:
            stakeholder_groups.extend(['end_users', 'support_team'])
        elif document_type in ['security', 'compliance']:
            stakeholder_groups.extend(['security_compliance', 'management'])
        elif document_type in ['internal', 'architecture']:
            stakeholder_groups.extend(['developers', 'management'])

        # Analyze tags
        if 'api' in tags or 'integration' in tags:
            stakeholder_groups.extend(['developers', 'administrators'])
        if 'security' in tags or 'compliance' in tags:
            stakeholder_groups.extend(['security_compliance', 'management'])

        return list(set(stakeholder_groups))  # Remove duplicates

    def _analyze_semantic_similarity(self, source_doc: Dict[str, Any], target_docs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze semantic similarity between source document and target documents."""
        if not target_docs:
            return {}

        # Extract content for similarity analysis
        documents = [source_doc.get('content', '')] + [doc.get('content', '') for doc in target_docs]
        document_ids = [source_doc.get('document_id', 'source')] + [doc.get('document_id', '') for doc in target_docs]

        # Remove empty documents
        valid_docs = [(i, doc) for i, doc in enumerate(documents) if doc.strip()]
        if len(valid_docs) < 2:
            return {}

        try:
            # Create TF-IDF vectors
            tfidf_matrix = self.vectorizer.fit_transform([doc for _, doc in valid_docs])
            similarity_matrix = cosine_similarity(tfidf_matrix)

            # Analyze similarities
            similarities = {}
            source_idx = 0  # Source document is always first

            for i, (original_idx, _) in enumerate(valid_docs):
                if i == source_idx:  # Skip self-comparison
                    continue

                target_doc_id = document_ids[original_idx]
                similarity_score = similarity_matrix[source_idx, i]

                # Classify similarity level
                if similarity_score >= self.impact_thresholds['semantic_similarity']['high_impact']:
                    similarity_level = 'high'
                elif similarity_score >= self.impact_thresholds['semantic_similarity']['medium_impact']:
                    similarity_level = 'medium'
                elif similarity_score >= self.impact_thresholds['semantic_similarity']['low_impact']:
                    similarity_level = 'low'
                else:
                    similarity_level = 'minimal'

                similarities[target_doc_id] = {
                    'similarity_score': float(similarity_score),
                    'similarity_level': similarity_level,
                    'confidence': min(0.95, similarity_score + 0.1),  # Simplified confidence
                    'shared_terms': self._find_shared_terms(source_doc.get('content', ''),
                                                           target_docs[original_idx - 1].get('content', ''))
                }

            return similarities

        except Exception as e:
            logger.warning(f"Semantic similarity analysis failed: {e}")
            return {}

    def _find_shared_terms(self, source_content: str, target_content: str, max_terms: int = 10) -> List[str]:
        """Find shared technical terms between two documents."""
        source_terms = set(self._extract_technical_terms(source_content))
        target_terms = set(self._extract_technical_terms(target_content))

        shared_terms = list(source_terms.intersection(target_terms))
        return shared_terms[:max_terms]

    def _analyze_content_overlap(self, source_doc: Dict[str, Any], target_docs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze content overlap between source document and target documents."""
        if not target_docs:
            return {}

        overlaps = {}

        for target_doc in target_docs:
            target_id = target_doc.get('document_id', '')
            if not target_id:
                continue

            source_content = source_doc.get('content', '').lower()
            target_content = target_doc.get('content', '').lower()

            if not source_content or not target_content:
                overlaps[target_id] = {
                    'overlap_score': 0.0,
                    'overlap_level': 'none',
                    'shared_sentences': 0,
                    'overlap_percentage': 0.0
                }
                continue

            # Simple sentence-level overlap analysis
            source_sentences = set(re.split(r'[.!?]+', source_content))
            target_sentences = set(re.split(r'[.!?]+', target_content))

            source_sentences = {s.strip() for s in source_sentences if s.strip()}
            target_sentences = {s.strip() for s in target_sentences if s.strip()}

            shared_sentences = source_sentences.intersection(target_sentences)
            overlap_score = len(shared_sentences) / max(len(source_sentences), len(target_sentences)) if source_sentences else 0

            # Classify overlap level
            if overlap_score >= self.impact_thresholds['content_overlap']['critical_overlap']:
                overlap_level = 'critical'
            elif overlap_score >= self.impact_thresholds['content_overlap']['high_overlap']:
                overlap_level = 'high'
            elif overlap_score >= self.impact_thresholds['content_overlap']['medium_overlap']:
                overlap_level = 'medium'
            elif overlap_score >= self.impact_thresholds['content_overlap']['low_overlap']:
                overlap_level = 'low'
            else:
                overlap_level = 'minimal'

            overlaps[target_id] = {
                'overlap_score': float(overlap_score),
                'overlap_level': overlap_level,
                'shared_sentences': len(shared_sentences),
                'overlap_percentage': round(overlap_score * 100, 2)
            }

        return overlaps

    def _analyze_relationships(self, source_doc: Dict[str, Any], target_docs: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Analyze relationships between source document and target documents."""
        if not target_docs:
            return {}

        relationships = {}

        for target_doc in target_docs:
            target_id = target_doc.get('document_id', '')
            if not target_id:
                continue

            relationship_score = 0.0
            relationship_factors = []

            # Check document type compatibility
            source_type = source_doc.get('document_type', '')
            target_type = target_doc.get('document_type', '')

            if self._are_related_types(source_type, target_type):
                relationship_score += 0.3
                relationship_factors.append('document_type_compatibility')

            # Check tag overlap
            source_tags = set(source_doc.get('tags', []))
            target_tags = set(target_doc.get('tags', []))
            tag_overlap = len(source_tags.intersection(target_tags))
            if tag_overlap > 0:
                relationship_score += min(0.2, tag_overlap * 0.1)
                relationship_factors.append('tag_overlap')

            # Check stakeholder overlap
            source_stakeholders = set(self._identify_stakeholder_groups(source_doc))
            target_stakeholders = set(self._identify_stakeholder_groups(target_doc))
            stakeholder_overlap = len(source_stakeholders.intersection(target_stakeholders))
            if stakeholder_overlap > 0:
                relationship_score += min(0.2, stakeholder_overlap * 0.1)
                relationship_factors.append('stakeholder_overlap')

            # Check for explicit references
            source_content = source_doc.get('content', '')
            target_title = target_doc.get('title', '')
            if target_title.lower() in source_content.lower():
                relationship_score += 0.3
                relationship_factors.append('explicit_reference')

            # Determine primary relationship type
            primary_relationship = self._determine_relationship_type(relationship_factors, source_type, target_type)

            relationships[target_id] = {
                'relationship_score': float(relationship_score),
                'primary_relationship': primary_relationship,
                'relationship_factors': relationship_factors,
                'impact_multiplier': self.relationship_types.get(primary_relationship, {}).get('impact_multiplier', 0.5)
            }

        return relationships

    def _are_related_types(self, source_type: str, target_type: str) -> bool:
        """Check if two document types are related."""
        type_relationships = {
            'api_reference': ['developer_guide', 'user_guide', 'tutorial', 'architecture'],
            'user_guide': ['tutorial', 'getting_started', 'faq', 'troubleshooting'],
            'developer_guide': ['api_reference', 'architecture', 'internal_docs'],
            'tutorial': ['user_guide', 'getting_started', 'api_reference'],
            'architecture': ['developer_guide', 'api_reference', 'internal_docs'],
            'security': ['compliance', 'developer_guide', 'api_reference'],
            'compliance': ['security', 'user_guide', 'internal_docs']
        }

        return target_type in type_relationships.get(source_type, [])

    def _determine_relationship_type(self, factors: List[str], source_type: str, target_type: str) -> str:
        """Determine the primary relationship type based on factors."""
        if 'explicit_reference' in factors:
            return 'reference_link'
        elif 'document_type_compatibility' in factors:
            return 'parent_child'
        elif len(factors) >= 2:
            return 'dependency'
        elif 'stakeholder_overlap' in factors:
            return 'complementary'
        else:
            return 'semantic_similarity'

    def _calculate_change_impact(self, change_description: Dict[str, Any],
                               document_features: Dict[str, Any],
                               related_documents: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate the overall impact of the change."""

        change_severity = self._assess_change_severity(change_description)
        stakeholder_impact = self._assess_stakeholder_impact(document_features, change_severity)

        # Calculate impact scores for each related document
        impact_scores = {}
        for doc_id, relationship_data in related_documents.items():
            impact_score = self._calculate_document_impact(change_severity, relationship_data)
            impact_scores[doc_id] = {
                'impact_score': impact_score,
                'impact_level': self._classify_impact_level(impact_score),
                'relationship_strength': relationship_data.get('relationship_score', 0),
                'propagation_path': relationship_data.get('primary_relationship', 'unknown')
            }

        # Aggregate overall impact
        if impact_scores:
            avg_impact = sum(score['impact_score'] for score in impact_scores.values()) / len(impact_scores)
            max_impact = max(score['impact_score'] for score in impact_scores.values())
            high_impact_docs = [doc_id for doc_id, score in impact_scores.items()
                              if score['impact_level'] in ['critical', 'high']]
        else:
            avg_impact = 0.0
            max_impact = 0.0
            high_impact_docs = []

        overall_impact = {
            'overall_impact_score': round(avg_impact, 3),
            'maximum_impact_score': round(max_impact, 3),
            'impact_level': self._classify_impact_level(avg_impact),
            'affected_documents_count': len(impact_scores),
            'high_impact_documents_count': len(high_impact_docs),
            'high_impact_documents': high_impact_docs,
            'change_severity': change_severity,
            'stakeholder_impact': stakeholder_impact
        }

        return {
            'overall_impact': overall_impact,
            'document_impacts': impact_scores,
            'change_analysis': change_description
        }

    def _assess_change_severity(self, change_description: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the severity of the change."""
        change_type = change_description.get('change_type', 'unknown')
        change_scope = change_description.get('change_scope', 'unknown')

        severity_score = 0.0
        severity_factors = []

        # Assess change type severity
        if change_type in self.impact_thresholds['change_severity']['breaking_change']:
            severity_score += 0.8
            severity_factors.append('breaking_change')
        elif change_type in self.impact_thresholds['change_severity']['major_change']:
            severity_score += 0.6
            severity_factors.append('major_change')
        elif change_type in self.impact_thresholds['change_severity']['minor_change']:
            severity_score += 0.3
            severity_factors.append('minor_change')
        else:
            severity_score += 0.1
            severity_factors.append('trivial_change')

        # Assess scope impact
        if change_scope == 'entire_document':
            severity_score += 0.3
            severity_factors.append('full_document_scope')
        elif change_scope == 'major_section':
            severity_score += 0.2
            severity_factors.append('major_section_scope')
        elif change_scope == 'minor_section':
            severity_score += 0.1
            severity_factors.append('minor_section_scope')
        else:
            severity_factors.append('minimal_scope')

        severity_level = 'critical' if severity_score >= 0.8 else \
                        'high' if severity_score >= 0.6 else \
                        'medium' if severity_score >= 0.3 else \
                        'low' if severity_score >= 0.1 else 'minimal'

        return {
            'severity_score': round(severity_score, 3),
            'severity_level': severity_level,
            'severity_factors': severity_factors
        }

    def _assess_stakeholder_impact(self, document_features: Dict[str, Any], change_severity: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the impact on stakeholders."""
        document_type = document_features.get('document_type', '')
        stakeholder_groups = document_features.get('stakeholder_groups', [])
        business_criticality = document_features.get('business_criticality', 'medium')

        stakeholder_impact_score = 0.0

        # Document type impact
        if document_type in self.impact_thresholds['stakeholder_impact']['critical']:
            stakeholder_impact_score += 0.4
        elif document_type in self.impact_thresholds['stakeholder_impact']['high']:
            stakeholder_impact_score += 0.3
        elif document_type in self.impact_thresholds['stakeholder_impact']['medium']:
            stakeholder_impact_score += 0.2
        else:
            stakeholder_impact_score += 0.1

        # Stakeholder group count impact
        stakeholder_impact_score += min(0.3, len(stakeholder_groups) * 0.1)

        # Business criticality impact
        if business_criticality == 'critical':
            stakeholder_impact_score += 0.3
        elif business_criticality == 'high':
            stakeholder_impact_score += 0.2
        elif business_criticality == 'medium':
            stakeholder_impact_score += 0.1

        # Change severity multiplier
        severity_multiplier = change_severity['severity_score'] + 0.5
        stakeholder_impact_score *= severity_multiplier

        impact_level = 'critical' if stakeholder_impact_score >= 0.8 else \
                      'high' if stakeholder_impact_score >= 0.6 else \
                      'medium' if stakeholder_impact_score >= 0.4 else \
                      'low' if stakeholder_impact_score >= 0.2 else 'minimal'

        return {
            'stakeholder_impact_score': round(stakeholder_impact_score, 3),
            'impact_level': impact_level,
            'affected_stakeholder_groups': stakeholder_groups,
            'business_criticality': business_criticality
        }

    def _calculate_document_impact(self, change_severity: Dict[str, Any], relationship_data: Dict[str, Any]) -> float:
        """Calculate the impact score for a specific document."""
        severity_score = change_severity['severity_score']
        relationship_score = relationship_data.get('relationship_score', 0)
        impact_multiplier = relationship_data.get('impact_multiplier', 0.5)

        # Base impact calculation
        base_impact = severity_score * relationship_score * impact_multiplier

        # Apply diminishing returns for very high relationships
        if relationship_score > 0.8:
            base_impact *= 0.9  # Slight reduction to prevent over-weighting

        return round(base_impact, 3)

    def _classify_impact_level(self, impact_score: float) -> str:
        """Classify impact level based on score."""
        if impact_score >= 0.8:
            return 'critical'
        elif impact_score >= 0.6:
            return 'high'
        elif impact_score >= 0.4:
            return 'medium'
        elif impact_score >= 0.2:
            return 'low'
        else:
            return 'minimal'

    def _generate_impact_recommendations(self, impact_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on impact analysis."""
        recommendations = []

        overall_impact = impact_analysis['overall_impact']
        document_impacts = impact_analysis['document_impacts']
        change_analysis = impact_analysis['change_analysis']

        impact_level = overall_impact['impact_level']
        change_severity = change_analysis.get('severity_level', 'unknown')

        # Overall impact recommendations
        if impact_level == 'critical':
            recommendations.append("🚨 CRITICAL IMPACT: Immediate change management required")
            recommendations.append("Schedule comprehensive impact assessment meeting with all stakeholders")
            recommendations.append("Prepare rollback plan and communication strategy")
            recommendations.append("Consider phased rollout to minimize disruption")

        elif impact_level == 'high':
            recommendations.append("⚠️ HIGH IMPACT: Schedule change review within 1 week")
            recommendations.append("Notify all affected stakeholders and teams")
            recommendations.append("Prepare detailed impact analysis and mitigation plan")
            recommendations.append("Monitor closely after implementation")

        elif impact_level == 'medium':
            recommendations.append("📊 MEDIUM IMPACT: Include in next change management cycle")
            recommendations.append("Inform key stakeholders of potential impacts")
            recommendations.append("Monitor implementation and gather feedback")

        else:
            recommendations.append("✅ LOW IMPACT: Standard change management process")
            recommendations.append("Document change for future reference")

        # Change-specific recommendations
        if change_severity == 'breaking_change':
            recommendations.append("Breaking change detected - ensure comprehensive testing and validation")
            recommendations.append("Update all dependent systems and documentation")
        elif change_severity == 'major_change':
            recommendations.append("Major change - validate impact on all dependent components")
            recommendations.append("Consider user communication and training needs")

        # Document-specific recommendations
        high_impact_docs = overall_impact.get('high_impact_documents', [])
        if high_impact_docs:
            recommendations.append(f"Focus immediate attention on {len(high_impact_docs)} high-impact documents")
            recommendations.append("Prioritize testing and validation for critical dependencies")

        # Stakeholder recommendations
        stakeholder_impact = overall_impact.get('stakeholder_impact', {})
        stakeholder_level = stakeholder_impact.get('impact_level', 'unknown')
        if stakeholder_level in ['critical', 'high']:
            recommendations.append("High stakeholder impact - prepare detailed communication plan")
            recommendations.append("Consider user training and support requirements")

        return recommendations[:8]  # Limit to 8 recommendations

    async def analyze_change_impact(
        self,
        document_id: str,
        document_data: Dict[str, Any],
        change_description: Dict[str, Any],
        related_documents: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Analyze the impact of changes to a document on related content."""

        start_time = time.time()

        if not self._initialize_analyzer():
            return {
                'error': 'Change impact analysis not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            # Extract document features
            document_features = self._extract_document_features(document_data)

            # Analyze relationships with related documents
            if related_documents:
                semantic_similarities = self._analyze_semantic_similarity(document_data, related_documents)
                content_overlaps = self._analyze_content_overlap(document_data, related_documents)
                relationships = self._analyze_relationships(document_data, related_documents)

                # Combine relationship data
                combined_relationships = {}
                for doc_id in related_documents:
                    doc_id_key = doc_id.get('document_id', '')
                    if doc_id_key:
                        combined_relationships[doc_id_key] = {
                            'semantic_similarity': semantic_similarities.get(doc_id_key, {}),
                            'content_overlap': content_overlaps.get(doc_id_key, {}),
                            'relationship': relationships.get(doc_id_key, {}),
                            'relationship_score': relationships.get(doc_id_key, {}).get('relationship_score', 0)
                        }
            else:
                combined_relationships = {}

            # Calculate overall change impact
            impact_analysis = self._calculate_change_impact(
                change_description, document_features, combined_relationships
            )

            # Generate recommendations
            recommendations = self._generate_impact_recommendations(impact_analysis)

            processing_time = time.time() - start_time

            return {
                'document_id': document_id,
                'change_description': change_description,
                'document_features': document_features,
                'impact_analysis': impact_analysis,
                'related_documents_analysis': combined_relationships,
                'recommendations': recommendations,
                'processing_time': processing_time,
                'analysis_timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Change impact analysis failed for document {document_id}: {e}")
            return {
                'error': 'Change impact analysis failed',
                'message': str(e),
                'document_id': document_id,
                'processing_time': time.time() - start_time
            }

    async def analyze_portfolio_change_impact(
        self,
        changes: List[Dict[str, Any]],
        document_portfolio: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze the impact of multiple changes across a document portfolio."""

        start_time = time.time()

        if not self._initialize_analyzer():
            return {
                'error': 'Portfolio change impact analysis not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            if not changes or not document_portfolio:
                return {
                    'portfolio_summary': {},
                    'change_impacts': [],
                    'processing_time': time.time() - start_time
                }

            # Create document lookup for efficient access
            document_lookup = {doc.get('document_id', ''): doc for doc in document_portfolio}

            # Analyze each change
            change_impacts = []
            portfolio_impacts = defaultdict(list)

            for change in changes:
                document_id = change.get('document_id', '')
                document_data = document_lookup.get(document_id)

                if document_data:
                    # Find related documents for this change
                    related_docs = [
                        doc for doc in document_portfolio
                        if doc.get('document_id') != document_id
                    ]

                    impact_result = await self.analyze_change_impact(
                        document_id, document_data, change, related_docs
                    )

                    if 'error' not in impact_result:
                        change_impacts.append(impact_result)

                        # Track portfolio-level impacts
                        overall_impact = impact_result['impact_analysis']['overall_impact']
                        portfolio_impacts[overall_impact['impact_level']].append(document_id)

            if not change_impacts:
                return {
                    'portfolio_summary': {'total_changes': len(changes), 'analyzed_changes': 0},
                    'change_impacts': [],
                    'processing_time': time.time() - start_time
                }

            # Calculate portfolio summary
            total_changes = len(changes)
            analyzed_changes = len(change_impacts)

            impact_distribution = dict(Counter(
                impact['impact_analysis']['overall_impact']['impact_level']
                for impact in change_impacts
            ))

            avg_impact_score = sum(
                impact['impact_analysis']['overall_impact']['overall_impact_score']
                for impact in change_impacts
            ) / analyzed_changes if analyzed_changes > 0 else 0

            high_impact_changes = [
                impact['document_id'] for impact in change_impacts
                if impact['impact_analysis']['overall_impact']['impact_level'] in ['critical', 'high']
            ]

            portfolio_summary = {
                'total_changes': total_changes,
                'analyzed_changes': analyzed_changes,
                'average_impact_score': round(avg_impact_score, 3),
                'impact_distribution': impact_distribution,
                'high_impact_changes_count': len(high_impact_changes),
                'high_impact_changes': high_impact_changes,
                'most_impacted_documents': self._find_most_impacted_documents(change_impacts)
            }

            processing_time = time.time() - start_time

            return {
                'portfolio_summary': portfolio_summary,
                'change_impacts': change_impacts,
                'processing_time': processing_time,
                'analysis_timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Portfolio change impact analysis failed: {e}")
            return {
                'error': 'Portfolio change impact analysis failed',
                'message': str(e),
                'processing_time': time.time() - start_time
            }

    def _find_most_impacted_documents(self, change_impacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find documents that are most frequently impacted by changes."""
        impact_counts = Counter()

        for change_impact in change_impacts:
            document_impacts = change_impact.get('impact_analysis', {}).get('document_impacts', {})
            for doc_id in document_impacts.keys():
                impact_score = document_impacts[doc_id].get('impact_score', 0)
                if impact_score >= 0.3:  # Only count significant impacts
                    impact_counts[doc_id] += 1

        # Return top 10 most impacted documents
        most_impacted = impact_counts.most_common(10)
        return [
            {'document_id': doc_id, 'impact_frequency': count}
            for doc_id, count in most_impacted
        ]

    def update_impact_thresholds(self, custom_thresholds: Dict[str, Dict[str, Any]]) -> bool:
        """Update change impact analysis thresholds."""
        try:
            for threshold_name, config in custom_thresholds.items():
                if threshold_name in self.impact_thresholds:
                    self.impact_thresholds[threshold_name].update(config)
                else:
                    logger.warning(f"Unknown threshold type: {threshold_name}")
                    continue

            return True

        except Exception as e:
            logger.error(f"Failed to update impact thresholds: {e}")
            return False


# Global instance for reuse
change_impact_analyzer = ChangeImpactAnalyzer()


async def analyze_change_impact(
    document_id: str,
    document_data: Dict[str, Any],
    change_description: Dict[str, Any],
    related_documents: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Convenience function for change impact analysis.

    Args:
        document_id: ID of the document being changed
        document_data: Current document data
        change_description: Description of the change
        related_documents: List of potentially related documents

    Returns:
        Change impact analysis results
    """
    return await change_impact_analyzer.analyze_change_impact(
        document_id=document_id,
        document_data=document_data,
        change_description=change_description,
        related_documents=related_documents
    )


async def analyze_portfolio_change_impact(
    changes: List[Dict[str, Any]],
    document_portfolio: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Convenience function for portfolio change impact analysis.

    Args:
        changes: List of change descriptions
        document_portfolio: Complete document portfolio

    Returns:
        Portfolio change impact analysis results
    """
    return await change_impact_analyzer.analyze_portfolio_change_impact(
        changes=changes,
        document_portfolio=document_portfolio
    )
