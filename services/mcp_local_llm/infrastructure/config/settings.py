"""Application Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Service
    service_name: str = "mcp-local-llm"
    service_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8014
    
    # Ollama
    ollama_host: str = "localhost"
    ollama_port: int = 11434
    ollama_timeout: int = 300
    
    # Models
    default_model: str = "llama2"
    max_loaded_models: int = 3
    model_cache_dir: str = "./models"
    
    # Context
    default_context_window: int = 4096
    max_context_sessions: int = 100
    
    # Performance
    gpu_layers: int = -1  # -1 for all layers on GPU
    num_threads: int = 4
    
    class Config:
        env_file = ".env"
        env_prefix = "LOCAL_LLM_"

