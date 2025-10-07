"""Model Management Application Service."""

from typing import List, Optional

from ...domain.entities.model import Model
from ...domain.value_objects.model_config import ModelConfig
from ...domain.repositories.model_repository import ModelRepository


class ModelService:
    """
    Application service for model management.
    
    Handles model loading, unloading, and lifecycle operations.
    """
    
    def __init__(self, model_repo: ModelRepository):
        """Initialize model service."""
        self.model_repo = model_repo
    
    async def load_model(
        self,
        model_id: str,
        name: str,
        config: Optional[ModelConfig] = None,
    ) -> Model:
        """
        Load model.
        
        Args:
            model_id: Model identifier
            name: Model name
            config: Model configuration
            
        Returns:
            Loaded model
        """
        model = Model(
            model_id=model_id,
            name=name,
            config=config or ModelConfig(),
        )
        
        model.load()
        await self.model_repo.add(model)
        
        return model
    
    async def unload_model(self, model_id: str) -> Model:
        """
        Unload model.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Unloaded model
            
        Raises:
            ValueError: If model not found
        """
        model = await self.model_repo.get_by_id(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        
        model.unload()
        await self.model_repo.update(model)
        
        return model
    
    async def get_model(self, model_id: str) -> Optional[Model]:
        """Get model by ID."""
        return await self.model_repo.get_by_id(model_id)
    
    async def list_models(self) -> List[Model]:
        """List all models."""
        return await self.model_repo.list_all()
    
    async def get_loaded_models(self) -> List[Model]:
        """Get all loaded models."""
        return await self.model_repo.list_loaded()

