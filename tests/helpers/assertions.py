"""Shared assertion helpers to keep tests DRY and consistent."""

from typing import Dict, Any, Iterable


def assert_basic_ok_json(resp) -> Dict[str, Any]:
    assert resp.status_code == 200
    ctype = resp.headers.get("content-type", "").lower()
    assert "json" in ctype or ctype == ""  # some endpoints may not set explicitly
    return resp.json() if "json" in ctype or ctype == "application/json" else {}


def assert_has_keys(obj: Dict[str, Any], keys: Iterable[str]) -> None:
    for key in keys:
        assert key in obj


def assert_list_of_dicts(items, min_len: int = 0) -> None:
    assert isinstance(items, list)
    assert len(items) >= min_len
    for it in items:
        assert isinstance(it, dict)


