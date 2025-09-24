"""Provider implementations for Summarizer Hub.

Contains the actual implementation functions for different LLM providers.
"""

import json as pyjson
import os
from typing import Optional

import httpx

from services.shared.auth.credentials import get_secret
# Config now handled by standardized config system in main.py
import os


class ProviderImplementations:
    """Handles different LLM provider implementations."""

    @staticmethod
    async def summarize_with_ollama(
        provider_config, prompt: Optional[str], text: str
    ) -> str:
        """Summarize using Ollama API."""
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        url = (provider_config.endpoint or ollama_host).rstrip("/") + "/api/generate"
        payload = {
            "model": provider_config.model or "llama3",
            "prompt": ((prompt + "\n\n") if prompt else "") + text,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            try:
                r = await client.post(url, json=payload)
                r.raise_for_status()
                data = r.json()
                return str(data.get("response") or "")
            except Exception:
                return ""

    @staticmethod
    async def summarize_with_openai(
        provider_config, prompt: Optional[str], text: str
    ) -> str:
        """Summarize using OpenAI API (placeholder)."""
        return ((prompt + "\n\n") if prompt else "") + text

    @staticmethod
    async def summarize_with_anthropic(
        provider_config, prompt: Optional[str], text: str
    ) -> str:
        """Summarize using Anthropic API (placeholder)."""
        return ((prompt + "\n\n") if prompt else "") + text

    @staticmethod
    async def summarize_with_grok(
        provider_config, prompt: Optional[str], text: str
    ) -> str:
        """Summarize using Grok API (placeholder)."""
        return ((prompt + "\n\n") if prompt else "") + text

    @staticmethod
    async def summarize_with_bedrock(
        provider_config, prompt: Optional[str], text: str
    ) -> str:
        """Summarize using Amazon Bedrock."""
        content = ((prompt + "\n\n") if prompt else "") + text

        # Try native SDK
        try:
            import boto3

            region = provider_config.region or os.getenv(
                "BEDROCK_REGION", os.environ.get("AWS_REGION") or "us-east-1"
            )
            model_id = provider_config.model or os.getenv(
                "BEDROCK_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0"
            )
            client = boto3.client(
                "bedrock-runtime",
                region_name=region,
                aws_access_key_id=get_secret("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=get_secret("AWS_SECRET_ACCESS_KEY"),
                aws_session_token=get_secret("AWS_SESSION_TOKEN"),
            )
            # Anthropic Messages format
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 512,
                "messages": [{"role": "user", "content": content}],
            }
            resp = client.invoke_model(modelId=model_id, body=pyjson.dumps(body))
            payload = pyjson.loads(resp.get("body", b"{}"))
            if isinstance(payload, dict):
                parts = payload.get("content") or []
                texts = []
                for part in parts:
                    t = part.get("text") or part.get("content")
                    if t:
                        texts.append(t)
                return "\n".join(texts)
            return ""
        except Exception:
            pass

        # Fallback: HTTP proxy
        url = (
            provider_config.endpoint
            or os.getenv("BEDROCK_ENDPOINT", "")
            or ""
        ).strip()
        if not url:
            return content
        headers = {}
        api_key = (
            provider_config.api_key
            or get_secret("BEDROCK_API_KEY")
            or os.getenv("BEDROCK_API_KEY")
        )
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": provider_config.model
            or os.getenv("BEDROCK_MODEL", "anthropic.claude-3-sonnet-20240229-v1:0"),
            "region": provider_config.region
            or os.getenv("BEDROCK_REGION", os.environ.get("AWS_REGION", "us-east-1")),
            "prompt": content,
        }
        async with httpx.AsyncClient(timeout=90) as client:
            try:
                r = await client.post(url, json=payload, headers=headers)
                r.raise_for_status()
                data = r.json()
                return str(data.get("output") or data.get("response") or "")
            except Exception:
                return ""


# Create singleton instance
provider_implementations = ProviderImplementations()
