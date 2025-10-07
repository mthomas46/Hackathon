"""Ollama REST API client for local LLM inference."""

from typing import List, Dict, Optional, Any, AsyncIterator
from dataclasses import dataclass
from datetime import datetime
import httpx
import json


@dataclass
class ModelInfo:
    """Information about an Ollama model."""
    name: str
    size: int  # Size in bytes
    parameter_count: int
    quantization: str
    family: str
    format: str
    modified_at: datetime
    digest: str


@dataclass
class GenerationRequest:
    """Request for text generation."""
    model: str
    prompt: str
    system: Optional[str] = None
    template: Optional[str] = None
    context: Optional[List[int]] = None
    stream: bool = False
    raw: bool = False
    format: Optional[str] = None
    
    # Generation parameters
    temperature: float = 0.8
    top_k: int = 40
    top_p: float = 0.9
    repeat_penalty: float = 1.1
    seed: Optional[int] = None
    num_predict: Optional[int] = None  # max_tokens
    stop: Optional[List[str]] = None
    
    @property
    def max_tokens(self) -> Optional[int]:
        """Alias for num_predict."""
        return self.num_predict
    
    @max_tokens.setter
    def max_tokens(self, value: Optional[int]):
        """Set max_tokens (sets num_predict)."""
        self.num_predict = value


@dataclass
class GenerationResponse:
    """Response from text generation."""
    model: str
    text: str
    context: Optional[List[int]]
    total_duration: int  # nanoseconds
    load_duration: int
    prompt_eval_duration: int
    eval_duration: int
    created_at: datetime
    done: bool
    
    @property
    def generation_time_ms(self) -> float:
        """Get generation time in milliseconds."""
        return self.total_duration / 1_000_000
    
    @property
    def tokens_generated(self) -> int:
        """Estimate tokens generated (rough approximation)."""
        return len(self.text.split())


@dataclass
class EmbeddingRequest:
    """Request for embedding generation."""
    model: str
    text: str


@dataclass
class EmbeddingResponse:
    """Response from embedding generation."""
    model: str
    embedding: List[float]
    
    @property
    def embedding_dimensions(self) -> int:
        """Get embedding dimensionality."""
        return len(self.embedding)


class OllamaClient:
    """
    Client for Ollama REST API.
    
    Provides:
    - Model management (list, pull, delete)
    - Text generation
    - Streaming generation
    - Embedding generation
    - Health checks
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 120):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def list_models(self) -> List[ModelInfo]:
        """
        List all available models.
        
        Returns:
            List of ModelInfo objects
        """
        response = await self.client.get(f"{self.base_url}/api/tags")
        response.raise_for_status()
        
        data = response.json()
        models = []
        
        for model_data in data.get("models", []):
            models.append(ModelInfo(
                name=model_data["name"],
                size=model_data["size"],
                parameter_count=self._extract_param_count(model_data),
                quantization=self._extract_quantization(model_data),
                family=model_data.get("details", {}).get("family", "unknown"),
                format=model_data.get("details", {}).get("format", "unknown"),
                modified_at=datetime.fromisoformat(
                    model_data["modified_at"].replace("Z", "+00:00")
                ),
                digest=model_data.get("digest", "")
            ))
        
        return models
    
    async def pull_model(
        self,
        model_name: str,
        insecure: bool = False
    ) -> Dict[str, Any]:
        """
        Pull a model from Ollama registry.
        
        Args:
            model_name: Name of model to pull (e.g., "llama2:7b")
            insecure: Allow insecure connections
        
        Returns:
            Result dict with status and model info
        """
        payload = {
            "name": model_name,
            "insecure": insecure
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/pull",
            json=payload,
            timeout=600  # Pulling can take a while
        )
        response.raise_for_status()
        
        # Read all progress lines
        lines = response.text.strip().split('\n')
        final_line = json.loads(lines[-1])
        
        return {
            "status": "success" if final_line.get("status") == "success" else "error",
            "model": model_name,
            "total_size": final_line.get("total", 0)
        }
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate text completion.
        
        Args:
            request: GenerationRequest with prompt and parameters
        
        Returns:
            GenerationResponse with generated text
        """
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "top_k": request.top_k,
                "top_p": request.top_p,
                "repeat_penalty": request.repeat_penalty,
            }
        }
        
        if request.system:
            payload["system"] = request.system
        if request.template:
            payload["template"] = request.template
        if request.context:
            payload["context"] = request.context
        if request.raw:
            payload["raw"] = request.raw
        if request.format:
            payload["format"] = request.format
        if request.seed is not None:
            payload["options"]["seed"] = request.seed
        if request.num_predict is not None:
            payload["options"]["num_predict"] = request.num_predict
        if request.stop:
            payload["options"]["stop"] = request.stop
        
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        
        return GenerationResponse(
            model=data["model"],
            text=data["response"],
            context=data.get("context"),
            total_duration=data.get("total_duration", 0),
            load_duration=data.get("load_duration", 0),
            prompt_eval_duration=data.get("prompt_eval_duration", 0),
            eval_duration=data.get("eval_duration", 0),
            created_at=datetime.fromisoformat(
                data["created_at"].replace("Z", "+00:00")
            ),
            done=data.get("done", True)
        )
    
    async def generate_stream(
        self,
        request: GenerationRequest
    ) -> AsyncIterator[str]:
        """
        Generate text with streaming.
        
        Args:
            request: GenerationRequest (stream will be set to True)
        
        Yields:
            Text chunks as they're generated
        """
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": True,
            "options": {
                "temperature": request.temperature,
                "top_k": request.top_k,
                "top_p": request.top_p,
                "repeat_penalty": request.repeat_penalty,
            }
        }
        
        if request.system:
            payload["system"] = request.system
        if request.num_predict is not None:
            payload["options"]["num_predict"] = request.num_predict
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/generate",
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
    
    async def generate_embeddings(
        self,
        request: EmbeddingRequest
    ) -> EmbeddingResponse:
        """
        Generate embeddings for text.
        
        Args:
            request: EmbeddingRequest with text
        
        Returns:
            EmbeddingResponse with embedding vector
        """
        payload = {
            "model": request.model,
            "prompt": request.text
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/embeddings",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        
        return EmbeddingResponse(
            model=request.model,
            embedding=data["embedding"]
        )
    
    async def batch_embeddings(
        self,
        model: str,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            model: Model name
            texts: List of texts
        
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for text in texts:
            request = EmbeddingRequest(model=model, text=text)
            response = await self.generate_embeddings(request)
            embeddings.append(response.embedding)
        
        return embeddings
    
    async def get_model_info(self, model_name: str) -> ModelInfo:
        """
        Get detailed information about a model.
        
        Args:
            model_name: Model name
        
        Returns:
            ModelInfo object
        """
        response = await self.client.post(
            f"{self.base_url}/api/show",
            json={"name": model_name}
        )
        response.raise_for_status()
        
        data = response.json()
        
        return ModelInfo(
            name=model_name,
            size=data.get("size", 0),
            parameter_count=self._extract_param_count(data),
            quantization=self._extract_quantization(data),
            family=data.get("details", {}).get("family", "unknown"),
            format=data.get("details", {}).get("format", "unknown"),
            modified_at=datetime.now(),  # Not in show response
            digest=data.get("digest", "")
        )
    
    async def delete_model(self, model_name: str) -> bool:
        """
        Delete a model.
        
        Args:
            model_name: Model name to delete
        
        Returns:
            True if deleted successfully
        """
        try:
            response = await self.client.delete(
                f"{self.base_url}/api/delete",
                json={"name": model_name}
            )
            response.raise_for_status()
            return True
        except Exception:
            return False
    
    async def health_check(self) -> bool:
        """
        Check if Ollama server is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _extract_param_count(self, data: Dict[str, Any]) -> int:
        """Extract parameter count from model data."""
        # Try to parse from model name (e.g., "llama2:7b" -> 7B parameters)
        name = data.get("name", "")
        if ":" in name:
            variant = name.split(":")[1].lower()
            if "b" in variant:
                try:
                    return int(variant.replace("b", "")) * 1_000_000_000
                except ValueError:
                    pass
        
        # Fallback: try to get from details
        details = data.get("details", {})
        param_size = details.get("parameter_size", "")
        if param_size:
            try:
                if "B" in param_size:
                    return int(param_size.replace("B", "")) * 1_000_000_000
                elif "M" in param_size:
                    return int(param_size.replace("M", "")) * 1_000_000
            except ValueError:
                pass
        
        return 0
    
    def _extract_quantization(self, data: Dict[str, Any]) -> str:
        """Extract quantization type from model data."""
        details = data.get("details", {})
        quant = details.get("quantization_level", "")
        
        if quant:
            return quant
        
        # Try to infer from model name
        name = data.get("name", "").lower()
        if "q4" in name:
            return "Q4"
        elif "q5" in name:
            return "Q5"
        elif "q8" in name:
            return "Q8"
        elif "fp16" in name:
            return "FP16"
        elif "fp32" in name:
            return "FP32"
        
        return "unknown"

