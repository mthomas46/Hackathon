"""Client factory utilities for consistent request options.

Provides helpers to build request kwargs (headers/auth) and a thin wrapper
to send requests with default headers (e.g., auth tokens) in tests.
"""

from typing import Dict, Optional, Any


def build_request_kwargs(headers: Optional[Dict[str, str]] = None,
                         auth_token: Optional[str] = None,
                         extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    final_headers: Dict[str, str] = {}
    if headers:
        final_headers.update(headers)
    if auth_token:
        final_headers.setdefault("Authorization", f"Bearer {auth_token}")
    kwargs: Dict[str, Any] = {}
    if final_headers:
        kwargs["headers"] = final_headers
    if extra:
        kwargs.update(extra)
    return kwargs


def request_with_defaults(client, method: str, url: str,
                          headers: Optional[Dict[str, str]] = None,
                          auth_token: Optional[str] = None,
                          **kwargs):
    req_kwargs = build_request_kwargs(headers=headers, auth_token=auth_token, extra=kwargs)
    method_lower = method.lower()
    assert hasattr(client, method_lower), f"Unsupported method: {method}"
    func = getattr(client, method_lower)
    return func(url, **req_kwargs)


