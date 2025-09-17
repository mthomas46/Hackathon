from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List, Callable, Awaitable
from datetime import datetime, timezone
from functools import wraps


class DocumentEnvelope(BaseModel):
    version_tag: str | None = "v1"
    id: str
    version: Optional[str] = None
    correlation_id: Optional[str] = None
    source_refs: List[Dict[str, Any]] = Field(default_factory=list)
    content_hash: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    document: Dict[str, Any] = Field(default_factory=dict)


class ApiSchemaEnvelope(BaseModel):
    version_tag: str | None = "v1"
    id: str
    version: Optional[str] = None
    correlation_id: Optional[str] = None
    source_refs: List[Dict[str, Any]] = Field(default_factory=list)
    content_hash: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    schema: Dict[str, Any] = Field(default_factory=dict)


def validate_envelope(model: BaseModel):
    """Decorator to validate request bodies against an envelope model.

    Usage:
        @app.post("/ingest")
        @validate_envelope(ApiSchemaEnvelope)
        async def ingest(env: ApiSchemaEnvelope):
            ...
    """
    def _decorator(func: Callable[..., Awaitable[Any]]):
        @wraps(func)
        async def _wrapped(*args, **kwargs):
            # If FastAPI already parsed the model, pass-through
            if args and isinstance(args[-1], model.__class__):  # pragma: no cover
                return await func(*args, **kwargs)
            # Otherwise, validate kwargs or first arg
            body = kwargs.get("env") or kwargs.get("payload") or (args[-1] if args else {})
            try:
                _ = model.model_validate(body)
            except Exception as e:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail=f"Invalid envelope: {e}")
            return await func(*args, **kwargs)
        return _wrapped
    return _decorator


