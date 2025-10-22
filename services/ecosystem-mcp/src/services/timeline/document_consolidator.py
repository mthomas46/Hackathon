"""
Document Consolidator (Phase 5)

Detects redundancy and recommends document consolidation.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class DocumentConsolidator:
    """
    Analyzes documents to detect redundancy and recommend consolidation.
    
    Features:
    - Redundancy detection across versions
    - Content similarity clustering
    - Merge recommendations
    - Consolidation strategy suggestions
    """
    
    def __init__(self):
        logger.info("DocumentConsolidator initialized")
    
    async def analyze_consolidation_opportunities(
        self,
        service_name: str,
        similarity_threshold: float = 0.7
    ) -> Dict:
        """
        Analyze documents for consolidation opportunities.
        
        Args:
            service_name: Service to analyze
            similarity_threshold: Minimum similarity to consider redundancy (0.0-1.0)
        
        Returns:
            Consolidation analysis with recommendations
        """
        logger.info(f"Analyzing consolidation opportunities for {service_name}")
        
        try:
            # Fetch documents for service
            documents = await self._fetch_service_documents(service_name)
            
            if not documents:
                return {
                    'service_name': service_name,
                    'total_documents': 0,
                    'redundant_groups': [],
                    'consolidation_recommendations': [],
                    'estimated_reduction': 0
                }
            
            # Detect redundancy
            redundant_groups = await self._detect_redundancy(
                documents, similarity_threshold
            )
            
            # Cluster versions
            version_clusters = await self._cluster_versions(documents)
            
            # Generate recommendations
            recommendations = await self._generate_consolidation_recommendations(
                documents, redundant_groups, version_clusters
            )
            
            # Calculate potential reduction
            estimated_reduction = self._calculate_reduction_potential(
                documents, redundant_groups
            )
            
            return {
                'service_name': service_name,
                'total_documents': len(documents),
                'redundant_groups': redundant_groups,
                'version_clusters': version_clusters,
                'consolidation_recommendations': recommendations,
                'estimated_reduction': estimated_reduction,
                'similarity_threshold': similarity_threshold,
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing consolidation opportunities: {e}")
            raise
    
    async def recommend_merges(
        self,
        service_name: str,
        min_similarity: float = 0.85
    ) -> List[Dict]:
        """
        Recommend specific document merges.
        
        Args:
            service_name: Service to analyze
            min_similarity: Minimum similarity for merge recommendation
        
        Returns:
            List of merge recommendations
        """
        logger.info(f"Generating merge recommendations for {service_name}")
        
        try:
            documents = await self._fetch_service_documents(service_name)
            
            if not documents:
                return []
            
            # Find high-similarity pairs
            merge_candidates = []
            
            for i, doc1 in enumerate(documents):
                for doc2 in documents[i+1:]:
                    similarity = self._calculate_similarity(doc1, doc2)
                    
                    if similarity >= min_similarity:
                        merge_candidates.append({
                            'source_document': doc1['path'],
                            'target_document': doc2['path'],
                            'similarity': similarity,
                            'reason': self._determine_merge_reason(doc1, doc2, similarity),
                            'strategy': self._suggest_merge_strategy(doc1, doc2),
                            'confidence': self._calculate_merge_confidence(similarity)
                        })
            
            # Sort by similarity (highest first)
            merge_candidates.sort(key=lambda x: x['similarity'], reverse=True)
            
            return merge_candidates
            
        except Exception as e:
            logger.error(f"Error generating merge recommendations: {e}")
            raise
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    async def _fetch_service_documents(self, service_name: str) -> List[Dict]:
        """Fetch documents for a service."""
        try:
            from ...storage.repositories import DocumentRepository
            from ...storage.database import get_db_session
            
            async with get_db_session() as session:
                repo = DocumentRepository(session)
                
                # Get documents by service name
                documents = await repo.find_by_metadata({'service': service_name})
                
                return [
                    {
                        'id': str(doc.id),
                        'path': doc.file_path,
                        'content': doc.content,
                        'ingestion_mode': doc.ingestion_mode,
                        'version': getattr(doc, 'version', None),
                        'created_at': doc.created_at,
                        'updated_at': doc.updated_at
                    }
                    for doc in documents
                ]
                
        except Exception as e:
            logger.error(f"Error fetching documents: {e}")
            return []
    
    async def _detect_redundancy(
        self,
        documents: List[Dict],
        threshold: float
    ) -> List[Dict]:
        """Detect redundant document groups."""
        redundant_groups = []
        processed = set()
        
        for i, doc1 in enumerate(documents):
            if i in processed:
                continue
            
            group = [doc1]
            group_indices = {i}
            
            for j, doc2 in enumerate(documents[i+1:], start=i+1):
                if j in processed:
                    continue
                
                similarity = self._calculate_similarity(doc1, doc2)
                
                if similarity >= threshold:
                    group.append(doc2)
                    group_indices.add(j)
            
            if len(group) > 1:
                redundant_groups.append({
                    'group_id': len(redundant_groups) + 1,
                    'document_count': len(group),
                    'documents': [
                        {
                            'path': doc['path'],
                            'version': doc.get('version'),
                            'size': len(doc.get('content', ''))
                        }
                        for doc in group
                    ],
                    'avg_similarity': self._calculate_group_similarity(group)
                })
                processed.update(group_indices)
        
        return redundant_groups
    
    async def _cluster_versions(self, documents: List[Dict]) -> List[Dict]:
        """Cluster documents by version."""
        version_map = defaultdict(list)
        
        for doc in documents:
            version = doc.get('version', 'unversioned')
            version_map[version].append(doc)
        
        clusters = []
        for version, docs in version_map.items():
            clusters.append({
                'version': version,
                'document_count': len(docs),
                'documents': [doc['path'] for doc in docs],
                'total_size': sum(len(doc.get('content', '')) for doc in docs)
            })
        
        return clusters
    
    async def _generate_consolidation_recommendations(
        self,
        documents: List[Dict],
        redundant_groups: List[Dict],
        version_clusters: List[Dict]
    ) -> List[Dict]:
        """Generate consolidation recommendations."""
        recommendations = []
        
        # Recommendation 1: Merge redundant groups
        for group in redundant_groups:
            if group['document_count'] > 2:
                recommendations.append({
                    'type': 'merge_redundant',
                    'priority': 'HIGH',
                    'description': f"Merge {group['document_count']} highly similar documents",
                    'target_group': group['group_id'],
                    'estimated_savings': f"{(group['document_count'] - 1) * 100 / len(documents):.1f}%",
                    'action': 'Review and consolidate into single authoritative document'
                })
        
        # Recommendation 2: Version consolidation
        for cluster in version_clusters:
            if cluster['document_count'] > 5:
                recommendations.append({
                    'type': 'version_consolidation',
                    'priority': 'MEDIUM',
                    'description': f"Consolidate {cluster['document_count']} documents from version {cluster['version']}",
                    'version': cluster['version'],
                    'estimated_savings': f"{cluster['document_count'] * 20 / len(documents):.1f}%",
                    'action': 'Archive old versions or create version index'
                })
        
        # Recommendation 3: Duplicate removal
        exact_duplicates = self._find_exact_duplicates(documents)
        if exact_duplicates:
            recommendations.append({
                'type': 'remove_duplicates',
                'priority': 'CRITICAL',
                'description': f"Remove {len(exact_duplicates)} exact duplicate documents",
                'duplicates': exact_duplicates,
                'estimated_savings': f"{len(exact_duplicates) * 100 / len(documents):.1f}%",
                'action': 'Delete duplicate files immediately'
            })
        
        return recommendations
    
    def _calculate_reduction_potential(
        self,
        documents: List[Dict],
        redundant_groups: List[Dict]
    ) -> Dict:
        """Calculate potential document reduction."""
        total_docs = len(documents)
        redundant_docs = sum(group['document_count'] - 1 
                            for group in redundant_groups)
        
        return {
            'total_documents': total_docs,
            'redundant_documents': redundant_docs,
            'percentage_redundant': (redundant_docs / total_docs * 100) if total_docs > 0 else 0,
            'potential_reduction': redundant_docs,
            'recommended_count': total_docs - redundant_docs
        }
    
    def _calculate_similarity(self, doc1: Dict, doc2: Dict) -> float:
        """Calculate similarity between two documents."""
        # Simplified similarity calculation
        # In production, would use advanced NLP/embedding techniques
        
        content1 = doc1.get('content', '')
        content2 = doc2.get('content', '')
        
        if not content1 or not content2:
            return 0.0
        
        # Simple token-based similarity
        tokens1 = set(content1.lower().split())
        tokens2 = set(content2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_group_similarity(self, group: List[Dict]) -> float:
        """Calculate average similarity within a group."""
        if len(group) < 2:
            return 1.0
        
        similarities = []
        for i, doc1 in enumerate(group):
            for doc2 in group[i+1:]:
                similarities.append(self._calculate_similarity(doc1, doc2))
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _find_exact_duplicates(self, documents: List[Dict]) -> List[List[str]]:
        """Find exact duplicate documents."""
        content_map = defaultdict(list)
        
        for doc in documents:
            content = doc.get('content', '')
            if content:
                content_map[hash(content)].append(doc['path'])
        
        # Return only groups with duplicates
        return [paths for paths in content_map.values() if len(paths) > 1]
    
    def _determine_merge_reason(self, doc1: Dict, doc2: Dict, similarity: float) -> str:
        """Determine reason for merge recommendation."""
        if similarity >= 0.95:
            return "Near-identical content"
        elif similarity >= 0.85:
            return "Highly similar content with minor variations"
        else:
            return "Significant content overlap"
    
    def _suggest_merge_strategy(self, doc1: Dict, doc2: Dict) -> str:
        """Suggest merge strategy."""
        # Check if one is clearly newer
        if doc1.get('updated_at') > doc2.get('updated_at'):
            return f"Keep {doc1['path']} as primary, archive {doc2['path']}"
        elif doc2.get('updated_at') > doc1.get('updated_at'):
            return f"Keep {doc2['path']} as primary, archive {doc1['path']}"
        else:
            return "Manual review recommended to determine primary version"
    
    def _calculate_merge_confidence(self, similarity: float) -> str:
        """Calculate confidence level for merge."""
        if similarity >= 0.95:
            return "HIGH"
        elif similarity >= 0.85:
            return "MEDIUM"
        else:
            return "LOW"

