"""AI Request domain service."""

from typing import Optional
from ..entities.ai_request import AIRequest
from ..entities.ai_model import AIModel
from ..value_objects.request_id import RequestId
from ..value_objects.model_name import ModelName


class AIRequestService:
    """Domain service for AI request business logic."""

    def __init__(self):
        """Initialize the AI request service."""
        pass

    def create_request(
        self,
        prompt: str,
        model_name: str,
        template: Optional[str] = None,
        parameters: Optional[dict] = None,
        metadata: Optional[dict] = None
    ) -> AIRequest:
        """Create a new AI request with validation."""
        model = ModelName(model_name)
        request_id = RequestId.generate()

        request = AIRequest(
            id=request_id,
            model=model,
            prompt=prompt,
            template=template,
            parameters=parameters,
            metadata=metadata
        )

        request.validate()
        return request

    def validate_request_against_model(self, request: AIRequest, model: AIModel) -> bool:
        """Validate that a request is compatible with a model."""
        # Check if model supports the request
        if not model.is_active:
            return False

        # Basic token estimation (rough approximation)
        estimated_tokens = len(request.prompt.split()) * 1.3  # Rough token estimation
        return model.can_handle_request(int(estimated_tokens))

    def estimate_request_cost(self, request: AIRequest, model: AIModel) -> float:
        """Estimate the cost of processing a request."""
        # Rough token estimation for cost calculation
        input_tokens = len(request.prompt.split()) * 1.3
        estimated_output_tokens = min(input_tokens * 0.5, model.max_tokens * 0.3)  # Assume 30% of max tokens for output

        return model.estimate_cost(int(input_tokens), int(estimated_output_tokens))

    def should_use_template(self, request: AIRequest) -> bool:
        """Determine if request should use a template."""
        # Business rule: Use template if prompt is short and no template specified
        return len(request.prompt) < 100 and not request.template

    def enrich_request_metadata(self, request: AIRequest) -> AIRequest:
        """Enrich request with additional metadata."""
        enriched_metadata = dict(request.metadata) if request.metadata else {}

        # Add domain-specific metadata
        enriched_metadata.update({
            'model_provider': request.model.provider,
            'model_family': request.model.model_family,
            'estimated_complexity': self._estimate_prompt_complexity(request.prompt),
            'processed_at': request.created_at.isoformat() if request.created_at else None
        })

        return AIRequest(
            id=request.id,
            model=request.model,
            prompt=request.prompt,
            template=request.template,
            parameters=request.parameters,
            metadata=enriched_metadata,
            created_at=request.created_at
        )

    def _estimate_prompt_complexity(self, prompt: str) -> str:
        """Estimate the complexity of a prompt."""
        word_count = len(prompt.split())

        if word_count < 10:
            return 'simple'
        elif word_count < 50:
            return 'moderate'
        elif word_count < 200:
            return 'complex'
        else:
            return 'very_complex'
