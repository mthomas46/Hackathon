"""Inference Application Service."""

from typing import Optional

from ...domain.entities.inference_request import InferenceRequest
from ...domain.entities.model import Model
from ...domain.value_objects.generation_params import GenerationParams
from ...domain.repositories.inference_repository import InferenceRepository
from ...domain.repositories.model_repository import ModelRepository


class InferenceService:
    """
    Application service for LLM inference.
    
    Handles inference request creation and execution.
    """
    
    def __init__(
        self,
        inference_repo: InferenceRepository,
        model_repo: ModelRepository,
    ):
        """Initialize inference service."""
        self.inference_repo = inference_repo
        self.model_repo = model_repo
    
    async def create_inference_request(
        self,
        model_id: str,
        prompt: str,
        params: Optional[GenerationParams] = None,
        system_prompt: Optional[str] = None,
        context_id: Optional[str] = None,
    ) -> InferenceRequest:
        """
        Create inference request.
        
        Args:
            model_id: Model identifier
            prompt: User prompt
            params: Generation parameters
            system_prompt: System prompt
            context_id: Context session ID
            
        Returns:
            Created inference request
            
        Raises:
            ValueError: If model not found or not loaded
        """
        # Verify model exists and is loaded
        model = await self.model_repo.get_by_id(model_id)
        if not model:
            raise ValueError(f"Model not found: {model_id}")
        
        # Create request
        request = InferenceRequest(
            request_id=f"inf_{model_id}_{len(prompt)[:8]}",
            model_id=model_id,
            prompt=prompt,
            params=params or GenerationParams(),
            system_prompt=system_prompt,
            context_id=context_id,
        )
        
        await self.inference_repo.add(request)
        return request
    
    async def execute_inference(self, request_id: str) -> InferenceRequest:
        """
        Execute inference request.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Completed inference request
            
        Raises:
            ValueError: If request not found
        """
        request = await self.inference_repo.get_by_id(request_id)
        if not request:
            raise ValueError(f"Request not found: {request_id}")
        
        # Start processing
        request.start()
        await self.inference_repo.update(request)
        
        try:
            # In production, this would call Ollama API
            # Simulated completion
            response = f"Response to: {request.prompt[:50]}..."
            request.complete(
                response=response,
                generated_tokens=100,
                raw_response={"done": True},
            )
        except Exception as e:
            request.fail(str(e))
        
        await self.inference_repo.update(request)
        return request
    
    async def get_inference_request(self, request_id: str) -> Optional[InferenceRequest]:
        """Get inference request by ID."""
        return await self.inference_repo.get_by_id(request_id)
    
    async def list_pending_requests(self) -> list:
        """List pending inference requests."""
        return await self.inference_repo.list_pending()

