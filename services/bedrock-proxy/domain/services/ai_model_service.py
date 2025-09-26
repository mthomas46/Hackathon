"""AI Model domain service."""

from typing import List, Optional
from ..entities.ai_model import AIModel
from ..value_objects.model_name import ModelName


class AIModelService:
    """Domain service for AI model business logic."""

    # Default model configurations (in a real system, this would come from a repository)
    DEFAULT_MODELS = {
        'anthropic.claude-3-sonnet-20240229': {
            'provider': 'anthropic',
            'max_tokens': 4096,
            'supports_streaming': True,
            'context_window': 200000,
            'input_cost_per_token': 0.000003,
            'output_cost_per_token': 0.000015
        },
        'anthropic.claude-3-haiku-20240307': {
            'provider': 'anthropic',
            'max_tokens': 4096,
            'supports_streaming': True,
            'context_window': 200000,
            'input_cost_per_token': 0.00000025,
            'output_cost_per_token': 0.00000125
        },
        'meta.llama2-13b-chat-v1': {
            'provider': 'meta',
            'max_tokens': 4096,
            'supports_streaming': False,
            'context_window': 4096,
            'input_cost_per_token': 0.00000075,
            'output_cost_per_token': 0.000001
        },
        'amazon.titan-text-lite-v1': {
            'provider': 'amazon',
            'max_tokens': 4096,
            'supports_streaming': False,
            'context_window': 4096,
            'input_cost_per_token': 0.00000015,
            'output_cost_per_token': 0.0000002
        }
    }

    def __init__(self):
        """Initialize the AI model service."""
        pass

    def get_default_models(self) -> List[AIModel]:
        """Get list of default available models."""
        models = []
        for model_name_str, config in self.DEFAULT_MODELS.items():
            model_name = ModelName(model_name_str)
            model = AIModel(
                name=model_name,
                **config
            )
            models.append(model)
        return models

    def find_best_model_for_request(self, prompt: str, max_tokens: int = 4096) -> Optional[AIModel]:
        """Find the best available model for a given request."""
        models = self.get_default_models()
        active_models = [m for m in models if m.is_active]

        if not active_models:
            return None

        # Estimate token count
        estimated_tokens = len(prompt.split()) * 1.3

        # Find models that can handle the request
        suitable_models = [
            model for model in active_models
            if model.can_handle_request(int(estimated_tokens)) and model.max_tokens >= max_tokens
        ]

        if not suitable_models:
            return None

        # Return the cheapest suitable model
        return min(suitable_models, key=lambda m: m.input_cost_per_token)

    def validate_model_compatibility(self, model: AIModel, request_tokens: int) -> bool:
        """Validate if a model is compatible with request requirements."""
        return (model.is_active and
                model.can_handle_request(request_tokens) and
                request_tokens <= model.max_tokens)

    def calculate_optimal_batch_size(self, model: AIModel, total_requests: int) -> int:
        """Calculate optimal batch size for a model."""
        # Business rule: Batch size based on model capabilities
        if model.supports_streaming:
            return min(total_requests, 10)  # Larger batches for streaming models
        else:
            return min(total_requests, 5)   # Smaller batches for non-streaming models

    def get_model_by_name(self, model_name: str) -> Optional[AIModel]:
        """Get a specific model by name."""
        model_name_obj = ModelName(model_name)

        for name_str, config in self.DEFAULT_MODELS.items():
            if name_str == model_name:
                return AIModel(name=model_name_obj, **config)

        return None

    def get_models_by_provider(self, provider: str) -> List[AIModel]:
        """Get all models from a specific provider."""
        return [
            AIModel(name=ModelName(name_str), **config)
            for name_str, config in self.DEFAULT_MODELS.items()
            if config['provider'] == provider
        ]

    def estimate_total_cost(self, model: AIModel, requests: List[dict]) -> float:
        """Estimate total cost for processing multiple requests."""
        total_cost = 0.0

        for request in requests:
            prompt = request.get('prompt', '')
            input_tokens = len(prompt.split()) * 1.3
            # Estimate output as 30% of input tokens, capped by model max
            output_tokens = min(input_tokens * 0.3, model.max_tokens * 0.3)

            total_cost += model.estimate_cost(int(input_tokens), int(output_tokens))

        return total_cost
