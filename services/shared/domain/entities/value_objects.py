"""Value Objects - Immutable Domain Concepts.

This module provides standardized value object implementations following
Domain-Driven Design principles. Value objects are immutable objects that
represent concepts in the domain and are defined by their values, not identity.

Key Characteristics:
- Immutable (no setters, frozen=True in dataclasses)
- Equality based on values, not identity
- Self-validating in __post_init__
- No side effects
- Can contain other value objects

Usage:
    from services.shared.domain.value_objects import EmailAddress, Money, Address

    email = EmailAddress("user@example.com")
    amount = Money(100.50, "USD")
"""

from abc import ABC
from dataclasses import dataclass
from typing import Any, Optional
import re


class ValueObject(ABC):
    """Abstract base class for all value objects.

    Provides common functionality and ensures immutability.
    """

    def __eq__(self, other: object) -> bool:
        """Value objects are equal if all their attributes are equal."""
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Value objects can be used in sets and as dict keys."""
        return hash((self.__class__,) + tuple(sorted(self.__dict__.items())))

    def __repr__(self) -> str:
        """String representation of the value object."""
        attrs = ", ".join(f"{k}={v!r}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"


@dataclass(frozen=True)
class EmailAddress(ValueObject):
    """Value object representing an email address."""

    value: str

    def __post_init__(self) -> None:
        """Validate email address format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Email address must be a non-empty string")

        # Basic email validation regex
        email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )

        if not email_pattern.match(self.value):
            raise ValueError(f"Invalid email address format: {self.value}")

        # Additional validation
        if len(self.value) > 254:  # RFC 5321 limit
            raise ValueError("Email address too long (max 254 characters)")

    @property
    def domain(self) -> str:
        """Extract domain from email address."""
        return self.value.split('@')[1]

    @property
    def local_part(self) -> str:
        """Extract local part from email address."""
        return self.value.split('@')[0]


@dataclass(frozen=True)
class Money(ValueObject):
    """Value object representing monetary amounts."""

    amount: float
    currency: str

    def __post_init__(self) -> None:
        """Validate money amount and currency."""
        if not isinstance(self.amount, (int, float)):
            raise ValueError("Amount must be a number")

        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

        if not isinstance(self.currency, str) or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")

        # Convert to uppercase for consistency
        object.__setattr__(self, 'currency', self.currency.upper())

    def add(self, other: 'Money') -> 'Money':
        """Add two money amounts (must be same currency)."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {self.currency} vs {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: 'Money') -> 'Money':
        """Subtract two money amounts (must be same currency)."""
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract different currencies: {self.currency} vs {other.currency}")
        if self.amount < other.amount:
            raise ValueError("Cannot subtract larger amount from smaller amount")
        return Money(self.amount - other.amount, self.currency)

    def multiply(self, factor: float) -> 'Money':
        """Multiply money by a factor."""
        if factor < 0:
            raise ValueError("Multiplication factor cannot be negative")
        return Money(self.amount * factor, self.currency)


@dataclass(frozen=True)
class Address(ValueObject):
    """Value object representing a physical address."""

    street: str
    city: str
    state: str
    postal_code: str
    country: str

    def __post_init__(self) -> None:
        """Validate address components."""
        required_fields = ['street', 'city', 'state', 'postal_code', 'country']
        for field in required_fields:
            value = getattr(self, field)
            if not value or not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} is required and cannot be empty")

        # Validate postal code format (basic)
        if not re.match(r'^[A-Za-z0-9\s\-]+$', self.postal_code):
            raise ValueError("Invalid postal code format")

    @property
    def full_address(self) -> str:
        """Get formatted full address."""
        return f"{self.street}, {self.city}, {self.state} {self.postal_code}, {self.country}"

    @property
    def short_address(self) -> str:
        """Get abbreviated address format."""
        return f"{self.city}, {self.state}"


@dataclass(frozen=True)
class PhoneNumber(ValueObject):
    """Value object representing a phone number."""

    value: str
    country_code: str = "+1"

    def __post_init__(self) -> None:
        """Validate phone number format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Phone number must be a non-empty string")

        # Remove all non-digit characters for validation
        digits_only = re.sub(r'\D', '', self.value)

        # Basic validation: 10-15 digits
        if not 10 <= len(digits_only) <= 15:
            raise ValueError("Phone number must contain 10-15 digits")

        # Validate country code format
        if not re.match(r'^\+\d{1,4}$', self.country_code):
            raise ValueError("Invalid country code format (should be like +1, +44, etc.)")

    @property
    def formatted(self) -> str:
        """Get formatted phone number."""
        digits = re.sub(r'\D', '', self.value)

        # US format (basic)
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"

        # International format
        return f"{self.country_code} {digits}"

    @property
    def digits_only(self) -> str:
        """Get phone number with digits only."""
        return re.sub(r'\D', '', self.value)


@dataclass(frozen=True)
class URL(ValueObject):
    """Value object representing a URL."""

    value: str

    def __post_init__(self) -> None:
        """Validate URL format."""
        if not self.value or not isinstance(self.value, str):
            raise ValueError("URL must be a non-empty string")

        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)  # path

        if not url_pattern.match(self.value):
            raise ValueError(f"Invalid URL format: {self.value}")

    @property
    def domain(self) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(self.value)
        return parsed.netloc

    @property
    def scheme(self) -> str:
        """Get URL scheme (http/https)."""
        from urllib.parse import urlparse
        parsed = urlparse(self.value)
        return parsed.scheme

    @property
    def is_https(self) -> bool:
        """Check if URL uses HTTPS."""
        return self.scheme == 'https'


@dataclass(frozen=True)
class Coordinates(ValueObject):
    """Value object representing geographic coordinates."""

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        """Validate coordinate ranges."""
        if not -90 <= self.latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")

        if not -180 <= self.longitude <= 180:
            raise ValueError("Longitude must be between -180 and 180 degrees")

    @property
    def is_valid(self) -> bool:
        """Check if coordinates are within valid ranges."""
        return (-90 <= self.latitude <= 90) and (-180 <= self.longitude <= 180)

    def distance_to(self, other: 'Coordinates') -> float:
        """Calculate distance to another coordinate in kilometers (Haversine formula)."""
        import math

        # Convert to radians
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        # Earth's radius in kilometers
        radius = 6371
        return radius * c


@dataclass(frozen=True)
class DateRange(ValueObject):
    """Value object representing a date range."""

    start_date: str  # ISO format date
    end_date: str    # ISO format date

    def __post_init__(self) -> None:
        """Validate date range."""
        from datetime import datetime

        try:
            start = datetime.fromisoformat(self.start_date)
            end = datetime.fromisoformat(self.end_date)
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")

        if start >= end:
            raise ValueError("Start date must be before end date")

    @property
    def duration_days(self) -> int:
        """Get duration in days."""
        from datetime import datetime
        start = datetime.fromisoformat(self.start_date)
        end = datetime.fromisoformat(self.end_date)
        return (end - start).days

    def contains_date(self, date: str) -> bool:
        """Check if date falls within this range."""
        from datetime import datetime
        check_date = datetime.fromisoformat(date)
        start = datetime.fromisoformat(self.start_date)
        end = datetime.fromisoformat(self.end_date)
        return start <= check_date <= end

    def overlaps_with(self, other: 'DateRange') -> bool:
        """Check if this range overlaps with another."""
        from datetime import datetime
        self_start = datetime.fromisoformat(self.start_date)
        self_end = datetime.fromisoformat(self.end_date)
        other_start = datetime.fromisoformat(other.start_date)
        other_end = datetime.fromisoformat(other.end_date)

        return max(self_start, other_start) <= min(self_end, other_end)
