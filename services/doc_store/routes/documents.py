from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional

try:
    import redis.asyncio as aioredis  # type: ignore
except Exception:
    aioredis = None

from services.shared.envelopes import DocumentEnvelope
from services.shared.constants_new import ErrorCodes
from services.shared.config import get_config_value

# Import with fallback for different loading contexts
try:
    from ..modules.shared_utils import (
        create_doc_store_success_response,
        build_doc_store_context,
        handle_doc_store_error,
    )
    from ..modules.document_ops import create_document_enveloped_logic
except ImportError:
    try:
        from modules.shared_utils import (
            create_doc_store_success_response,
            build_doc_store_context,
            handle_doc_store_error,
        )
        from modules.document_ops import create_document_enveloped_logic
    except ImportError:
        # Fallback for when loaded via importlib
        import sys
        import os
        parent_dir = os.path.dirname(os.path.dirname(__file__))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from modules.shared_utils import (
            create_doc_store_success_response,
            build_doc_store_context,
            handle_doc_store_error,
        )
        from modules.document_ops import create_document_enveloped_logic


router = APIRouter()


@router.post("/documents/enveloped")
async def put_document_enveloped(env: DocumentEnvelope):
    try:
        result = create_document_enveloped_logic(env)

        if aioredis and result.get("id"):
            try:
                host = get_config_value("REDIS_HOST", None, section="redis", env_key="REDIS_HOST")
                if host:
                    client = aioredis.from_url(f"redis://{host}")
                    inner = env.document or {}
                    content = inner.get("content") or ""
                    doc_id = result.get("id")
                    chash = result.get("content_hash")

                    env_out = DocumentEnvelope(
                        id=doc_id,
                        version=env.version,
                        correlation_id=env.correlation_id,
                        source_refs=env.source_refs,
                        content_hash=chash,
                        document={
                            "id": doc_id,
                            "content": content,
                            "content_hash": chash,
                            "metadata": inner.get("metadata") or {}
                        },
                    )
                    await client.publish("docs.stored", env_out.model_dump_json())
                    await client.aclose()
            except Exception:
                pass

        context = build_doc_store_context("enveloped_document_creation", doc_id=result.get("id"))
        return create_doc_store_success_response("created from envelope", result, **context)

    except Exception as e:
        context = build_doc_store_context("enveloped_document_creation")
        return handle_doc_store_error("create document from envelope", e, **context)


