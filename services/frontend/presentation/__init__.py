"""Presentation layer for Frontend service.

This layer handles user interface, HTML templates, API responses,
and presentation logic for the web-based frontend.
"""

from . import api, routes, dtos, responses

__all__ = [
    "api",
    "routes",
    "dtos",
    "responses",
]
