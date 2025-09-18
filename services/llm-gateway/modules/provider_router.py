"""Provider Router for LLM Gateway Service.

Handles intelligent routing of LLM requests to appropriate providers based on
content analysis, availability, cost optimization, and performance requirements.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
import httpx

from services.shared.clients import ServiceClients
from services.shared.config import get_config_value
from services.shared.logging import fire_and_forget
from services.shared.constants_new import ServiceNames

# Import service integrations for enhanced provider selection
try:
    from .service_integrations import ServiceIntegrations
    service_integrations = ServiceIntegrations()
except ImportError:
    service_integrations = None


class ProviderResponse:
    """Response from an LLM provider."""
    def __init__(self, response: str, provider: str, tokens_used: int = 0,
                 cost: float = 0.0, success: bool = True, error: str = ""):
        self.response = response
        self.provider = provider
        self.tokens_used = tokens_used
        self.cost = cost
        self.success = success
        self.error = error


class ProviderRouter:
    """Intelligent routing of LLM requests to appropriate providers."""

    def __init__(self):
        self.client = ServiceClients()
        self.providers = self._initialize_providers()

    def _initialize_providers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize available LLM providers."""
        return {
            "ollama": {
                "name": "ollama",
                "type": "local",
                "endpoint": get_config_value("OLLAMA_ENDPOINT", "http://ollama-consistency:11434", section="ollama"),
                "model": get_config_value("OLLAMA_MODEL", "llama3", section="ollama"),
                "timeout": 60,
                "cost_per_token": 0.0,  # Free for local
                "security_level": "high",  # Local, secure
                "status": "unknown"
            },
            "openai": {
                "name": "openai",
                "type": "cloud",
                "api_key": get_config_value("OPENAI_API_KEY", "", section="openai"),
                "model": get_config_value("OPENAI_MODEL", "gpt-4o", section="openai"),
                "endpoint": "https://api.openai.com/v1/chat/completions",
                "timeout": 30,
                "cost_per_token": 0.00003,  # Approximate for GPT-4
                "security_level": "medium",
                "status": "unknown"
            },
            "anthropic": {
                "name": "anthropic",
                "type": "cloud",
                "api_key": get_config_value("ANTHROPIC_API_KEY", "", section="anthropic"),
                "model": get_config_value("ANTHROPIC_MODEL", "claude-3.5-sonnet", section="anthropic"),
                "endpoint": "https://api.anthropic.com/v1/messages",
                "timeout": 30,
                "cost_per_token": 0.000015,  # Approximate for Claude
                "security_level": "medium",
                "status": "unknown"
            },
            "bedrock": {
                "name": "bedrock",
                "type": "cloud",
                "model": get_config_value("BEDROCK_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0", section="bedrock"),
                "endpoint": get_config_value("BEDROCK_ENDPOINT", "", section="bedrock"),
                "timeout": 60,
                "cost_per_token": 0.000015,  # Approximate
                "security_level": "high",  # AWS security
                "status": "unknown"
            },
            "grok": {
                "name": "grok",
                "type": "cloud",
                "api_key": get_config_value("GROK_API_KEY", "", section="grok"),
                "model": get_config_value("GROK_MODEL", "grok-1", section="grok"),
                "endpoint": "https://api.x.ai/v1/chat/completions",
                "timeout": 30,
                "cost_per_token": 0.00001,  # Approximate
                "security_level": "medium",
                "status": "unknown"
            }
        }

    async def route_and_execute(self, request) -> ProviderResponse:
        """Route request to appropriate provider and execute."""
        try:
            # Select optimal provider
            selected_provider = await self._select_provider(request)

            if not selected_provider:
                return ProviderResponse(
                    response="",
                    provider="none",
                    success=False,
                    error="No suitable provider available"
                )

            # Execute request with selected provider
            return await self._execute_with_provider(request, selected_provider)

        except Exception as e:
            return ProviderResponse(
                response="",
                provider="error",
                success=False,
                error=str(e)
            )

    async def _select_provider(self, request) -> Optional[Dict[str, Any]]:
        """Select the optimal provider for the request."""
        available_providers = await self._get_available_providers()

        if not available_providers:
            return None

        # If specific provider requested, use it if available
        if hasattr(request, 'provider') and request.provider:
            if request.provider in available_providers:
                return available_providers[request.provider]

        # Intelligent provider selection based on:
        # 1. Security requirements
        # 2. Cost optimization
        # 3. Performance requirements
        # 4. Content sensitivity

        content = getattr(request, 'prompt', '') + getattr(request, 'context', '')

        # Check for sensitive content (simplified)
        is_sensitive = any(keyword in content.lower() for keyword in [
            'password', 'secret', 'token', 'key', 'credential', 'confidential'
        ])

        if is_sensitive:
            # Prefer secure providers for sensitive content
            secure_providers = [p for p in available_providers.values()
                              if p.get('security_level') == 'high']
            if secure_providers:
                return secure_providers[0]

        # Cost optimization: prefer cheaper providers for non-critical requests
        sorted_providers = sorted(available_providers.values(),
                                key=lambda x: x.get('cost_per_token', 0))

        return sorted_providers[0] if sorted_providers else None

    async def _execute_with_provider(self, request, provider_config: Dict[str, Any]) -> ProviderResponse:
        """Execute LLM request with specific provider."""
        provider_name = provider_config['name']

        try:
            if provider_name == "ollama":
                return await self._execute_ollama(request, provider_config)
            elif provider_name == "openai":
                return await self._execute_openai(request, provider_config)
            elif provider_name == "anthropic":
                return await self._execute_anthropic(request, provider_config)
            elif provider_name == "bedrock":
                return await self._execute_bedrock(request, provider_config)
            elif provider_name == "grok":
                return await self._execute_grok(request, provider_config)
            else:
                return ProviderResponse(
                    response="",
                    provider=provider_name,
                    success=False,
                    error=f"Unsupported provider: {provider_name}"
                )

        except Exception as e:
            return ProviderResponse(
                response="",
                provider=provider_name,
                success=False,
                error=str(e)
            )

    async def _execute_ollama(self, request, provider_config: Dict[str, Any]) -> ProviderResponse:
        """Execute request with Ollama."""
        url = f"{provider_config['endpoint']}/api/generate"

        payload = {
            "model": provider_config['model'],
            "prompt": getattr(request, 'prompt', ''),
            "stream": False
        }

        # Add context if provided
        if hasattr(request, 'context') and request.context:
            payload['prompt'] = f"Context: {request.context}\n\n{request.prompt}"

        start_time = time.time()

        async with httpx.AsyncClient(timeout=provider_config['timeout']) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        processing_time = time.time() - start_time

        return ProviderResponse(
            response=data.get('response', ''),
            provider="ollama",
            tokens_used=0,  # Ollama doesn't provide token counts easily
            cost=0.0,  # Local, no cost
            success=True
        )

    async def _execute_openai(self, request, provider_config: Dict[str, Any]) -> ProviderResponse:
        """Execute request with OpenAI."""
        headers = {
            "Authorization": f"Bearer {provider_config['api_key']}",
            "Content-Type": "application/json"
        }

        messages = []
        if hasattr(request, 'context') and request.context:
            messages.append({"role": "system", "content": request.context})

        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": provider_config['model'],
            "messages": messages,
            "temperature": getattr(request, 'temperature', 0.7)
        }

        async with httpx.AsyncClient(timeout=provider_config['timeout']) as client:
            response = await client.post(
                provider_config['endpoint'],
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

        choice = data['choices'][0]
        response_text = choice['message']['content']

        # Calculate approximate cost
        tokens_used = data.get('usage', {}).get('total_tokens', 0)
        cost = tokens_used * provider_config['cost_per_token']

        return ProviderResponse(
            response=response_text,
            provider="openai",
            tokens_used=tokens_used,
            cost=cost,
            success=True
        )

    async def _execute_anthropic(self, request, provider_config: Dict[str, Any]) -> ProviderResponse:
        """Execute request with Anthropic."""
        headers = {
            "x-api-key": provider_config['api_key'],
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        system_prompt = getattr(request, 'context', '') or "You are a helpful assistant."
        user_prompt = request.prompt

        payload = {
            "model": provider_config['model'],
            "max_tokens": getattr(request, 'max_tokens', 1024),
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }

        async with httpx.AsyncClient(timeout=provider_config['timeout']) as client:
            response = await client.post(
                provider_config['endpoint'],
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

        response_text = data['content'][0]['text'] if data.get('content') else ""

        # Calculate approximate cost
        tokens_used = data.get('usage', {}).get('input_tokens', 0) + data.get('usage', {}).get('output_tokens', 0)
        cost = tokens_used * provider_config['cost_per_token']

        return ProviderResponse(
            response=response_text,
            provider="anthropic",
            tokens_used=tokens_used,
            cost=cost,
            success=True
        )

    async def _execute_bedrock(self, request, provider_config: Dict[str, Any]) -> ProviderResponse:
        """Execute request with AWS Bedrock."""
        # Use existing bedrock proxy service
        bedrock_payload = {
            "prompt": request.prompt,
            "model": provider_config['model'],
            "max_tokens": getattr(request, 'max_tokens', 1024)
        }

        if hasattr(request, 'context') and request.context:
            bedrock_payload['system'] = request.context

        # Route through bedrock proxy
        response = await self.client.post_json(
            "http://bedrock-proxy:7090/invoke",
            bedrock_payload
        )

        if response.get('success'):
            return ProviderResponse(
                response=response.get('response', ''),
                provider="bedrock",
                tokens_used=0,  # Would need to parse from response
                cost=0.0,  # Would need cost calculation
                success=True
            )
        else:
            return ProviderResponse(
                response="",
                provider="bedrock",
                success=False,
                error=response.get('error', 'Bedrock request failed')
            )

    async def _execute_grok(self, request, provider_config: Dict[str, Any]) -> ProviderResponse:
        """Execute request with Grok (placeholder)."""
        # Placeholder implementation
        return ProviderResponse(
            response="Grok integration coming soon...",
            provider="grok",
            success=False,
            error="Grok integration not yet implemented"
        )

    async def _get_available_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get providers that are currently available and configured."""
        available = {}

        for name, config in self.providers.items():
            if await self._check_provider_availability(config):
                available[name] = config

        return available

    async def _check_provider_availability(self, provider_config: Dict[str, Any]) -> bool:
        """Check if a provider is available and properly configured."""
        try:
            provider_name = provider_config['name']

            if provider_name == "ollama":
                # Check Ollama health
                url = f"{provider_config['endpoint']}/api/tags"
                async with httpx.AsyncClient(timeout=5) as client:
                    response = await client.get(url)
                    return response.status_code == 200

            elif provider_name in ["openai", "anthropic", "grok"]:
                # Check if API key is configured
                return bool(provider_config.get('api_key'))

            elif provider_name == "bedrock":
                # Check if bedrock proxy is available
                try:
                    response = await self.client.get_json("http://bedrock-proxy:7090/health")
                    return response.get('status') == 'healthy'
                except:
                    return False

            return False

        except Exception:
            return False

    async def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers with their status."""
        available_providers = await self._get_available_providers()

        provider_list = []
        for name, config in available_providers.items():
            provider_info = {
                "name": name,
                "type": config.get('type', 'unknown'),
                "model": config.get('model', 'unknown'),
                "security_level": config.get('security_level', 'unknown'),
                "cost_per_token": config.get('cost_per_token', 0.0),
                "status": "available"
            }
            provider_list.append(provider_info)

        return provider_list

    async def check_provider_health(self) -> Dict[str, Any]:
        """Check health status of all providers."""
        health_status = {}

        for name, config in self.providers.items():
            try:
                available = await self._check_provider_availability(config)
                health_status[name] = {
                    "available": available,
                    "status": "healthy" if available else "unhealthy",
                    "last_checked": time.time()
                }
            except Exception as e:
                health_status[name] = {
                    "available": False,
                    "status": "error",
                    "error": str(e),
                    "last_checked": time.time()
                }

        return health_status

    async def generate_embeddings(self, text: str, model: str, provider: str) -> List[float]:
        """Generate embeddings for text (placeholder)."""
        # This would integrate with embedding providers
        # For now, return a mock embedding
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        # Convert hash to list of floats (mock implementation)
        embedding = [int(hash_obj.hexdigest()[i:i+2], 16) / 255.0 for i in range(0, 32, 2)]
        return embedding

    async def stream_response(self, request):
        """Stream LLM response (placeholder)."""
        # This would implement streaming for compatible providers
        # For now, return a simple response
        yield {"chunk": "Streaming not yet implemented", "finished": True}
