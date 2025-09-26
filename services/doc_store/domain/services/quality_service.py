
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


def compute_quality_flags(
    rows: List[Tuple[str, str, str, str]],
    stale_threshold_days: int = 180,
    min_views: int = 3,
) -> List[Dict[str, Any]]:
    """Compute quality flags for documents based on various criteria."""
    now = datetime.now(timezone.utc)
    hash_counts = _count_content_hashes(rows)

    results = []
    for doc_id, content_hash, meta_raw, created in rows:
        flags = []
        stale_days = 0
        importance_score = 0.0
        metadata = {}

        # Basic flags
        stale_days = _calculate_stale_days(created, stale_threshold_days, now)
        if stale_days >= max(1, stale_threshold_days):
            flags.append("stale")

        if _is_content_redundant(content_hash, hash_counts):
            flags.append("redundant")

        # Parse and analyze metadata
        metadata = _parse_document_metadata(meta_raw)

        # Metadata-based flags
        flags.extend(_analyze_metadata_flags(metadata, min_views, now, stale_days))
        flags.extend(_analyze_attachment_flags(metadata))
        flags.extend(_analyze_content_flags(metadata))

        # Importance and relationship flags
        importance_score = _calculate_importance_score(metadata)
        if importance_score >= 0.5:
            flags.append("high_importance")

        flags.extend(_analyze_relationship_flags(metadata, flags))

        results.append({
            "id": doc_id,
            "created_at": created,
            "content_hash": content_hash or "",
            "stale_days": stale_days,
            "flags": flags,
            "metadata": metadata,
            "importance_score": round(importance_score, 2),
        })

    return results


def _count_content_hashes(rows: List[Tuple[str, str, str, str]]) -> Dict[str, int]:
    """Count occurrences of each content hash."""
    hash_counts = {}
    for _, content_hash, _, _ in rows:
        hash_key = content_hash or ""
        hash_counts[hash_key] = hash_counts.get(hash_key, 0) + 1
    return hash_counts


def _calculate_stale_days(created: str, threshold_days: int, now: datetime) -> int:
    """Calculate how many days a document has been stale."""
    try:
        created_dt = datetime.fromisoformat(created)
        return max(0, int((now - created_dt).days))
    except Exception:
        return 0


def _is_content_redundant(content_hash: str, hash_counts: Dict[str, int]) -> bool:
    """Check if content is redundant based on hash frequency."""
    return hash_counts.get(content_hash or "", 0) > 1


def _parse_document_metadata(meta_raw: str) -> Dict[str, Any]:
    """Safely parse document metadata from JSON string."""
    try:
        return json.loads(meta_raw or "{}")
    except Exception:
        return {}


def _extract_metadata_fields(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract commonly used metadata fields."""
    return {
        "views": metadata.get("views"),
        "updated_at": metadata.get("updated_at"),
        "last_viewed": metadata.get("last_viewed"),
        "owner": metadata.get("owner"),
        "labels": metadata.get("labels"),
    }


def _calculate_updated_stale_days(updated_at: str, now: datetime, current_stale_days: int) -> int:
    """Calculate updated stale days based on updated_at timestamp."""
    if not updated_at:
        return current_stale_days

    try:
        updated_dt = datetime.fromisoformat(updated_at)
        updated_stale_days = max(0, int((now - updated_dt).days))
        return min(updated_stale_days, current_stale_days)
    except Exception:
        return current_stale_days


def _check_recently_viewed(last_viewed: str, current_stale_days: int, now: datetime) -> bool:
    """Check if document was recently viewed despite being stale."""
    if not last_viewed or current_stale_days < 180:
        return False

    try:
        last_viewed_dt = datetime.fromisoformat(last_viewed)
        return (now - last_viewed_dt).days <= 30
    except Exception:
        return False


def _analyze_basic_metadata(views: Any, owner: Any, min_views: int) -> List[str]:
    """Analyze basic metadata fields for quality flags."""
    flags = []

    if isinstance(views, int) and views < min_views:
        flags.append("low_views")

    if not owner:
        flags.append("missing_owner")

    return flags


def _analyze_metadata_flags(
    metadata: Dict[str, Any],
    min_views: int,
    now: datetime,
    current_stale_days: int
) -> List[str]:
    """Analyze metadata to determine quality flags."""
    flags = []

    # Extract metadata fields
    fields = _extract_metadata_fields(metadata)

    # Update stale calculation based on updated_at
    current_stale_days = _calculate_updated_stale_days(
        fields["updated_at"], now, current_stale_days
    )

    # Check for recent viewing despite staleness
    if _check_recently_viewed(fields["last_viewed"], current_stale_days, now):
        flags.append("recently_viewed")

    # Basic metadata checks
    flags.extend(_analyze_basic_metadata(fields["views"], fields["owner"], min_views))

    # Check for generic labels
    flags.extend(_analyze_label_quality(fields["labels"]))

    return flags


def _analyze_label_quality(labels: Any) -> List[str]:
    """Analyze label quality for generic/meaningless labels."""
    flags = []
    GENERIC_LABELS = {"documentation", "misc", "general", "notes"}

    try:
        if isinstance(labels, list) and any(
            str(label).lower() in GENERIC_LABELS for label in labels
        ):
            flags.append("generic_labels")
    except Exception:
        pass

    return flags


def _analyze_attachment_flags(metadata: Dict[str, Any]) -> List[str]:
    """Analyze attachment-related flags."""
    flags = []

    attachments = metadata.get("attachments")
    attachments_referenced_by = metadata.get("attachments_referenced_by")

    try:
        if isinstance(attachments, int) and attachments > 0:
            flags.append("has_attachments")

        if isinstance(attachments_referenced_by, int) and attachments_referenced_by > 0:
            flags.append("attachments_referenced")
    except Exception:
        pass

    return flags


def _analyze_content_flags(metadata: Dict[str, Any]) -> List[str]:
    """Analyze content-related flags."""
    flags = []

    content_length = metadata.get("content_length")

    try:
        if isinstance(content_length, int) and content_length < 200:
            flags.append("thin_content")
    except Exception:
        pass

    return flags


def _calculate_importance_score(metadata: Dict[str, Any]) -> float:
    """Calculate document importance score based on engagement metrics."""
    try:
        views = int(metadata.get("views") or 0)
        unique_views = int(metadata.get("unique_views") or 0)
        watchers = int(metadata.get("watchers") or 0)

        # Weighted scoring: views (50%), unique views (30%), watchers (20%)
        score = (
            (views / 100.0) * 0.5 +
            (unique_views / 50.0) * 0.3 +
            (watchers / 10.0) * 0.2
        )
        return min(1.0, score)
    except Exception:
        return 0.0


def _analyze_relationship_flags(metadata: Dict[str, Any], existing_flags: List[str]) -> List[str]:
    """Analyze relationship-based flags like orphan candidates."""
    flags = []

    backlinks = metadata.get("backlinks")

    try:
        if (
            isinstance(backlinks, int)
            and backlinks == 0
            and "orphan_candidate" not in existing_flags
        ):
            flags.append("orphan_candidate")
    except Exception:
        pass

    return flags
