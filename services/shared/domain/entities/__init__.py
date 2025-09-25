"""Domain Entities - Core Business Objects.

This module contains domain entities and value objects following
Domain-Driven Design principles.
"""

from .value_objects import (
    ValueObject, EmailAddress, Money, Address, PhoneNumber, URL, Coordinates, DateRange
)

__all__ = [
    "ValueObject", "EmailAddress", "Money", "Address", "PhoneNumber", "URL", "Coordinates", "DateRange"
]
