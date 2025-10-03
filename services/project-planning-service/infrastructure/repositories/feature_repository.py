"""
Feature Repository - Data access layer for features
===================================================

Provides CRUD operations and queries for feature entities.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid

from ...domain.entities.feature import Feature, FeatureStatus, FeaturePriority
from ..database.models import FeatureModel


class FeatureRepository:
    """Repository for Feature entity persistence."""
    
    def __init__(self, session: Session):
        """Initialize repository with database session."""
        self.session = session
    
    def create(self, feature: Feature) -> Feature:
        """Create a new feature in the database."""
        # Convert domain entity to database model
        feature_model = FeatureModel(
            id=feature.id or str(uuid.uuid4()),
            title=feature.title,
            description=feature.description,
            status=feature.status.value if isinstance(feature.status, FeatureStatus) else feature.status,
            priority=feature.priority.value if isinstance(feature.priority, FeaturePriority) else feature.priority,
            business_value=feature.business_value,
            acceptance_criteria=feature.acceptance_criteria,
            estimated_effort=feature.estimated_effort,
            technical_complexity=feature.technical_complexity,
            dependencies=feature.dependencies,
            ai_analysis=feature.ai_analysis,
            risk_assessment=feature.risk_assessment,
            created_by=feature.created_by,
            project_id=getattr(feature, 'project_id', None),
            roadmap_id=feature.roadmap_id,
            parent_feature_id=feature.parent_feature_id
        )
        
        self.session.add(feature_model)
        self.session.flush()
        
        # Update domain entity with generated ID if needed
        feature.id = feature_model.id
        
        return feature
    
    def get_by_id(self, feature_id: str) -> Optional[Feature]:
        """Retrieve feature by ID."""
        feature_model = self.session.query(FeatureModel).filter(
            FeatureModel.id == feature_id
        ).first()
        
        if not feature_model:
            return None
        
        return self._model_to_entity(feature_model)
    
    def update(self, feature: Feature) -> Feature:
        """Update existing feature."""
        feature_model = self.session.query(FeatureModel).filter(
            FeatureModel.id == feature.id
        ).first()
        
        if not feature_model:
            raise ValueError(f"Feature with ID {feature.id} not found")
        
        # Update model fields
        feature_model.title = feature.title
        feature_model.description = feature.description
        feature_model.status = feature.status.value if isinstance(feature.status, FeatureStatus) else feature.status
        feature_model.priority = feature.priority.value if isinstance(feature.priority, FeaturePriority) else feature.priority
        feature_model.business_value = feature.business_value
        feature_model.acceptance_criteria = feature.acceptance_criteria
        feature_model.estimated_effort = feature.estimated_effort
        feature_model.technical_complexity = feature.technical_complexity
        feature_model.dependencies = feature.dependencies
        feature_model.ai_analysis = feature.ai_analysis
        feature_model.risk_assessment = feature.risk_assessment
        feature_model.roadmap_id = feature.roadmap_id
        feature_model.parent_feature_id = feature.parent_feature_id
        
        self.session.flush()
        
        return feature
    
    def delete(self, feature_id: str) -> bool:
        """Delete feature by ID."""
        feature_model = self.session.query(FeatureModel).filter(
            FeatureModel.id == feature_id
        ).first()
        
        if not feature_model:
            return False
        
        self.session.delete(feature_model)
        self.session.flush()
        
        return True
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[Feature]:
        """List all features with pagination."""
        feature_models = self.session.query(FeatureModel).limit(limit).offset(offset).all()
        return [self._model_to_entity(fm) for fm in feature_models]
    
    def find_by_roadmap(self, roadmap_id: str) -> List[Feature]:
        """Find all features associated with a roadmap."""
        feature_models = self.session.query(FeatureModel).filter(
            FeatureModel.roadmap_id == roadmap_id
        ).all()
        return [self._model_to_entity(fm) for fm in feature_models]
    
    def find_by_status(self, status: FeatureStatus) -> List[Feature]:
        """Find features by status."""
        status_value = status.value if isinstance(status, FeatureStatus) else status
        feature_models = self.session.query(FeatureModel).filter(
            FeatureModel.status == status_value
        ).all()
        return [self._model_to_entity(fm) for fm in feature_models]
    
    def find_by_priority(self, priority: FeaturePriority) -> List[Feature]:
        """Find features by priority."""
        priority_value = priority.value if isinstance(priority, FeaturePriority) else priority
        feature_models = self.session.query(FeatureModel).filter(
            FeatureModel.priority == priority_value
        ).all()
        return [self._model_to_entity(fm) for fm in feature_models]
    
    def search(self, query: str) -> List[Feature]:
        """Search features by title or description."""
        search_pattern = f"%{query}%"
        feature_models = self.session.query(FeatureModel).filter(
            or_(
                FeatureModel.title.ilike(search_pattern),
                FeatureModel.description.ilike(search_pattern)
            )
        ).all()
        return [self._model_to_entity(fm) for fm in feature_models]
    
    def _model_to_entity(self, model: FeatureModel) -> Feature:
        """Convert database model to domain entity."""
        return Feature(
            id=model.id,
            title=model.title,
            description=model.description,
            status=FeatureStatus(model.status) if isinstance(model.status, str) else model.status,
            priority=FeaturePriority(model.priority) if isinstance(model.priority, str) else model.priority,
            business_value=model.business_value,
            acceptance_criteria=model.acceptance_criteria or [],
            estimated_effort=model.estimated_effort,
            technical_complexity=model.technical_complexity,
            dependencies=model.dependencies or [],
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            ai_analysis=model.ai_analysis or {},
            risk_assessment=model.risk_assessment or {},
            roadmap_id=model.roadmap_id,
            parent_feature_id=model.parent_feature_id,
            child_features=[]  # Would need to load separately if needed
        )

