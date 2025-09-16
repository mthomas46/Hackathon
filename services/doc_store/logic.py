from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
import json


def compute_quality_flags(rows: List[Tuple[str, str, str, str]], stale_threshold_days: int = 180, min_views: int = 3) -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    # rows: (id, content_hash, metadata_json, created_at)
    hash_counts: Dict[str, int] = {}
    for _, ch, _, _ in rows:
        ch = ch or ""
        hash_counts[ch] = hash_counts.get(ch, 0) + 1
    out: List[Dict[str, Any]] = []
    for doc_id, ch, meta_raw, created in rows:
        flags: List[str] = []
        # stale
        try:
            dt = datetime.fromisoformat(created)
            stale_days = max(0, int((now - dt).days))
        except Exception:
            stale_days = 0
        if stale_days >= max(1, stale_threshold_days):
            flags.append("stale")
        # redundant
        if hash_counts.get(ch or "", 0) > 1:
            flags.append("redundant")
        # metadata flags
        try:
            meta = json.loads(meta_raw or "{}")
        except Exception:
            meta = {}
        views = meta.get("views") if isinstance(meta, dict) else None
        unique_views = meta.get("unique_views") if isinstance(meta, dict) else None
        watchers = meta.get("watchers") if isinstance(meta, dict) else None
        updated_at = meta.get("updated_at") if isinstance(meta, dict) else None
        last_viewed = meta.get("last_viewed") if isinstance(meta, dict) else None
        try:
            if updated_at:
                dt_upd = datetime.fromisoformat(updated_at)
                stale_days = max(0, int((now - dt_upd).days))
        except Exception:
            pass
        try:
            if last_viewed:
                dt_lv = datetime.fromisoformat(last_viewed)
                if (now - dt_lv).days <= 30 and "stale" in flags:
                    flags.append("recently_viewed")
        except Exception:
            pass
        owner = meta.get("owner") if isinstance(meta, dict) else None
        labels = meta.get("labels") if isinstance(meta, dict) else None
        attachments = meta.get("attachments") if isinstance(meta, dict) else None
        attachments_referenced_by = meta.get("attachments_referenced_by") if isinstance(meta, dict) else None
        content_length = meta.get("content_length") if isinstance(meta, dict) else None
        if isinstance(views, int) and views < min_views:
            flags.append("low_views")
        if not owner:
            flags.append("missing_owner")
        # Confluence label entropy heuristic: penalize very generic labels
        GENERIC = {"documentation", "misc", "general", "notes"}
        try:
            if isinstance(labels, list) and any(str(l).lower() in GENERIC for l in labels):
                flags.append("generic_labels")
        except Exception:
            pass
        # Attachment presence/reference
        try:
            if isinstance(attachments, int) and attachments > 0:
                flags.append("has_attachments")
            if isinstance(attachments_referenced_by, int) and attachments_referenced_by > 0:
                flags.append("attachments_referenced")
        except Exception:
            pass
        # Thin content
        try:
            if isinstance(content_length, int) and content_length < 200:
                flags.append("thin_content")
        except Exception:
            pass
        # importance score (0-1): combines views, unique_views, watchers heuristically
        importance_score = 0.0
        try:
            v = int(views or 0)
            uv = int(unique_views or 0)
            w = int(watchers or 0)
            importance_score = min(1.0, (v / 100.0) * 0.5 + (uv / 50.0) * 0.3 + (w / 10.0) * 0.2)
            if importance_score >= 0.5:
                flags.append("high_importance")
        except Exception:
            pass
        # Backlinks: stronger orphan when zero inbound refs
        backlinks = meta.get("backlinks") if isinstance(meta, dict) else None
        if isinstance(backlinks, int) and backlinks == 0 and "orphan_candidate" not in flags:
            flags.append("orphan_candidate")
        out.append({
            "id": doc_id,
            "created_at": created,
            "content_hash": ch or "",
            "stale_days": stale_days,
            "flags": flags,
            "metadata": meta,
            "importance_score": round(importance_score, 2),
        })
    return out


