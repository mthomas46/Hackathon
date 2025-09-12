"""Analysis processing logic for code analyzer service."""

from typing import Dict, List, Any, Optional
from services.shared.models import Document  # type: ignore
from services.shared.envelopes import DocumentEnvelope  # type: ignore
from services.shared.utilities import stable_hash  # type: ignore

from .endpoint_extractor import extract_endpoints_from_text
from .style_manager import style_manager


def create_analysis_result(
    source_type: str,
    title: str,
    content: str,
    source_refs: List[Dict[str, Any]],
    repo: Optional[str] = None,
    path: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a standardized analysis result document and envelope."""

    # Prepare metadata, handling source_link specially
    final_metadata = metadata or {}
    if "source_link" not in final_metadata:
        final_metadata["source_link"] = {"repo": repo, **({"path": path} if path else {})}

    # Create document
    doc = Document(
        id=f"code:{source_type}:{stable_hash(content)[:8]}",
        source_type="code",
        title=title,
        content=content,
        content_hash=stable_hash(content),
        metadata=final_metadata,
        correlation_id=correlation_id,
    )

    # Create envelope
    envelope = DocumentEnvelope(
        id=doc.id,
        version=doc.version_tag,
        correlation_id=doc.correlation_id,
        source_refs=source_refs or [doc.metadata.get("source_link") or {}],
        content_hash=doc.content_hash,
        document=doc.model_dump(),
    )

    return envelope.model_dump()


def process_text_analysis(
    content: str,
    repo: Optional[str] = None,
    path: Optional[str] = None,
    correlation_id: Optional[str] = None,
    language: Optional[str] = None,
    style_examples: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Process text analysis request."""

    # Extract endpoints
    endpoints = extract_endpoints_from_text(content)
    summary = "\n".join(sorted(endpoints)) or "(no endpoints)"

    # Build style examples
    style_used: List[Dict[str, Any]] = []
    if style_examples:
        style_used.extend(style_examples)

    lang = (language or "").lower().strip()
    if lang:
        existing_examples = style_manager.get_examples(lang)
        if "items" in existing_examples:
            style_used.extend(existing_examples["items"])

    style_meta = {"style_examples_used": style_used} if style_used else {}

    # Create result
    return create_analysis_result(
        source_type="text",
        title="Code Analysis",
        content=summary,
        source_refs=[{"repo": repo, "path": path}],
        repo=repo,
        path=path,
        correlation_id=correlation_id,
        metadata=style_meta
    )


def process_files_analysis(
    files: List[Dict[str, Any]],
    repo: Optional[str] = None,
    correlation_id: Optional[str] = None,
    language: Optional[str] = None,
    style_examples: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Process files analysis request."""

    # Combine all file contents (handle both dict and object formats)
    contents = []
    paths = []
    for f in files:
        if hasattr(f, 'content') and hasattr(f, 'path'):
            # FileItem object
            contents.append(f.content)
            paths.append(f.path)
        else:
            # Dictionary format
            contents.append(f.get("content", ""))
            paths.append(f.get("path", ""))

    text = "\n".join(contents)

    # Extract endpoints
    endpoints = sorted(set(extract_endpoints_from_text(text)))
    summary = "\n".join(endpoints) or "(no endpoints)"

    # Build style examples
    style_used: List[Dict[str, Any]] = []
    if style_examples:
        style_used.extend(style_examples)

    lang = (language or "").lower().strip()
    if lang:
        existing_examples = style_manager.get_examples(lang)
        if "items" in existing_examples:
            style_used.extend(existing_examples["items"])

    style_meta = {"style_examples_used": style_used} if style_used else {}
    style_meta["files_analyzed"] = len(files)

    # Create result with files in source_link metadata to match test expectations
    metadata = {
        **style_meta,
        "files_analyzed": len(files),
        "source_link": {"repo": repo, "files": paths}
    }

    return create_analysis_result(
        source_type="files",
        title="Code Analysis (files)",
        content=summary,
        source_refs=[metadata["source_link"]],
        repo=repo,
        correlation_id=correlation_id,
        metadata=metadata
    )


def process_patch_analysis(
    patch: str,
    repo: Optional[str] = None,
    correlation_id: Optional[str] = None,
    language: Optional[str] = None,
    style_examples: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Process patch analysis request."""

    from .endpoint_extractor import extract_endpoints_from_patch

    # Extract endpoints from patch
    endpoints = sorted(set(extract_endpoints_from_patch(patch)))
    summary = "\n".join(endpoints) or "(no endpoints)"

    # Build style examples
    style_used: List[Dict[str, Any]] = []
    if style_examples:
        style_used.extend(style_examples)

    lang = (language or "").lower().strip()
    if lang:
        existing_examples = style_manager.get_examples(lang)
        if "items" in existing_examples:
            style_used.extend(existing_examples["items"])

    style_meta = {"style_examples_used": style_used} if style_used else {}

    # Create result
    return create_analysis_result(
        source_type="patch",
        title="Code Analysis (patch)",
        content=summary,
        source_refs=[{"repo": repo}],
        repo=repo,
        correlation_id=correlation_id,
        metadata=style_meta
    )
