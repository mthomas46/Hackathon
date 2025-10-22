"""
Document Consolidation API Routes (Phase 5)

Endpoints for analyzing and recommending document consolidation.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ...services.timeline import DocumentConsolidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/consolidation", tags=["consolidation"])


@router.post("/analyze")
async def analyze_consolidation(
    service_name: str = Query(..., description="Service to analyze"),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Similarity threshold (0.0-1.0)")
):
    """
    Analyze documents for consolidation opportunities.
    
    Features:
    - Redundancy detection
    - Version clustering
    - Merge recommendations
    - Reduction potential calculation
    
    Returns:
        Consolidation analysis with actionable recommendations
    """
    try:
        logger.info(f"Analyzing consolidation for service {service_name}")
        
        consolidator = DocumentConsolidator()
        
        result = await consolidator.analyze_consolidation_opportunities(
            service_name=service_name,
            similarity_threshold=similarity_threshold
        )
        
        logger.info(f"✅ Found {len(result.get('redundant_groups', []))} redundant groups")
        
        return {
            'success': True,
            'analysis': result
        }
        
    except Exception as e:
        logger.error(f"Error analyzing consolidation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend-merges")
async def recommend_merges(
    service_name: str = Query(..., description="Service to analyze"),
    min_similarity: float = Query(0.85, ge=0.0, le=1.0, description="Minimum similarity for merge (0.0-1.0)")
):
    """
    Get specific document merge recommendations.
    
    Features:
    - High-similarity pair detection
    - Merge strategy suggestions
    - Confidence assessment
    - Priority ranking
    
    Returns:
        List of merge recommendations sorted by similarity
    """
    try:
        logger.info(f"Generating merge recommendations for {service_name}")
        
        consolidator = DocumentConsolidator()
        
        recommendations = await consolidator.recommend_merges(
            service_name=service_name,
            min_similarity=min_similarity
        )
        
        logger.info(f"✅ Generated {len(recommendations)} merge recommendations")
        
        return {
            'success': True,
            'recommendations': recommendations,
            'total_recommendations': len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"Error generating merge recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_consolidation_metrics(
    service_name: str = Query(..., description="Service to analyze")
):
    """
    Get consolidation metrics for a service.
    
    Returns:
        Metrics including redundancy percentage, estimated savings, etc.
    """
    try:
        logger.info(f"Getting consolidation metrics for {service_name}")
        
        consolidator = DocumentConsolidator()
        
        analysis = await consolidator.analyze_consolidation_opportunities(
            service_name=service_name
        )
        
        metrics = {
            'service_name': service_name,
            'total_documents': analysis.get('total_documents', 0),
            'redundant_groups': len(analysis.get('redundant_groups', [])),
            'version_clusters': len(analysis.get('version_clusters', [])),
            'estimated_reduction': analysis.get('estimated_reduction', {}),
            'analyzed_at': analysis.get('analyzed_at')
        }
        
        return {
            'success': True,
            'metrics': metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting consolidation metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

