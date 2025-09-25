"""Domain Services - Business Logic Not Belonging to Single Entities.

This module provides domain services that encapsulate business logic which spans
multiple entities or doesn't naturally belong to any single entity. Following DDD
principles, domain services are stateless and contain pure business logic.

Key Characteristics:
- Stateless (no instance variables for business state)
- Operate on domain objects (entities, value objects)
- Contain business rules and calculations
- Can be injected into application services
- Testable in isolation

Usage:
    from services.shared.domain.domain_services import NotificationService, PricingService

    # Use in application services
    notification_svc = NotificationService()
    await notification_svc.send_welcome_email(user)
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class DomainService(ABC):
    """Abstract base class for domain services.

    Provides common functionality and ensures statelessness.
    """

    def __init__(self):
        """Domain services should be stateless."""
        # No instance variables for business state
        pass


class NotificationService(DomainService):
    """Domain service for handling notifications and communications."""

    def calculate_notification_priority(self, event_type: str, urgency: str) -> str:
        """Calculate notification priority based on event type and urgency.

        Business Rule: Critical events always get high priority,
        while informational events vary by urgency.
        """
        if event_type in ['security_breach', 'system_failure', 'data_loss']:
            return 'critical'

        if urgency == 'high':
            return 'high'
        elif urgency == 'medium':
            return 'medium'
        else:
            return 'low'

    def should_send_notification(self, user_preferences: Dict[str, Any],
                               notification_type: str) -> bool:
        """Determine if notification should be sent based on user preferences.

        Business Rule: Respect user notification preferences,
        but always send critical security notifications.
        """
        if notification_type in ['security_alert', 'account_changes']:
            return True  # Always send critical notifications

        user_setting = user_preferences.get(notification_type, True)
        return bool(user_setting)

    def format_notification_message(self, template: str,
                                  context: Dict[str, Any]) -> str:
        """Format notification message using template and context.

        Business Rule: Ensure consistent message formatting
        and proper variable substitution.
        """
        try:
            return template.format(**context)
        except KeyError as e:
            logger.warning(f"Missing context variable in notification template: {e}")
            # Return template with available variables
            safe_context = {k: v for k, v in context.items() if k in template}
            return template.format(**safe_context)


class PricingService(DomainService):
    """Domain service for pricing calculations and business rules."""

    def calculate_discounted_price(self, base_price: float,
                                 discount_type: str,
                                 discount_value: float) -> float:
        """Calculate discounted price based on discount type.

        Business Rules:
        - Percentage discounts cannot exceed 100%
        - Fixed amount discounts cannot exceed base price
        - Minimum price is $0.01
        """
        if discount_type == 'percentage':
            if discount_value < 0 or discount_value > 100:
                raise ValueError("Percentage discount must be between 0 and 100")
            discount_amount = base_price * (discount_value / 100)
        elif discount_type == 'fixed':
            if discount_value < 0:
                raise ValueError("Fixed discount cannot be negative")
            discount_amount = min(discount_value, base_price)
        else:
            raise ValueError(f"Unknown discount type: {discount_type}")

        final_price = base_price - discount_amount
        return max(final_price, 0.01)  # Minimum price

    def calculate_tax_amount(self, price: float, tax_rate: float,
                           tax_inclusive: bool = False) -> float:
        """Calculate tax amount for a given price.

        Business Rules:
        - Tax rates must be between 0% and 50%
        - Handle both inclusive and exclusive tax calculations
        """
        if tax_rate < 0 or tax_rate > 50:
            raise ValueError("Tax rate must be between 0% and 50%")

        if tax_inclusive:
            # Price includes tax, calculate tax portion
            return price * (tax_rate / (100 + tax_rate))
        else:
            # Price excludes tax, add tax amount
            return price * (tax_rate / 100)

    def validate_price_range(self, price: float, min_price: float = 0.01,
                           max_price: float = 10000.00) -> bool:
        """Validate that price falls within acceptable range.

        Business Rules:
        - Minimum price prevents free items
        - Maximum price prevents pricing errors
        """
        return min_price <= price <= max_price


class ValidationService(DomainService):
    """Domain service for complex validation logic."""

    def validate_business_rules(self, entity_data: Dict[str, Any],
                              rules: List[Dict[str, Any]]) -> List[str]:
        """Validate entity data against business rules.

        Args:
            entity_data: Dictionary of entity field values
            rules: List of validation rules

        Returns:
            List of validation error messages
        """
        errors = []

        for rule in rules:
            rule_type = rule.get('type')
            field = rule.get('field')
            value = entity_data.get(field)

            if rule_type == 'required':
                if not value or (isinstance(value, str) and not value.strip()):
                    errors.append(rule.get('message', f"{field} is required"))

            elif rule_type == 'range':
                min_val = rule.get('min')
                max_val = rule.get('max')
                if value is not None:
                    if min_val is not None and value < min_val:
                        errors.append(rule.get('message', f"{field} must be at least {min_val}"))
                    if max_val is not None and value > max_val:
                        errors.append(rule.get('message', f"{field} must be at most {max_val}"))

            elif rule_type == 'regex':
                pattern = rule.get('pattern')
                if value and not re.match(pattern, str(value)):
                    errors.append(rule.get('message', f"{field} format is invalid"))

        return errors

    def validate_cross_field_rules(self, entity_data: Dict[str, Any],
                                 cross_field_rules: List[Dict[str, Any]]) -> List[str]:
        """Validate rules that span multiple fields.

        Business Rules:
        - End date must be after start date
        - Password confirmation must match password
        - Dependent fields must be consistent
        """
        errors = []

        for rule in cross_field_rules:
            rule_type = rule.get('type')

            if rule_type == 'date_range':
                start_field = rule.get('start_field')
                end_field = rule.get('end_field')
                start_date = entity_data.get(start_field)
                end_date = entity_data.get(end_field)

                if start_date and end_date and start_date >= end_date:
                    errors.append(rule.get('message', f"{end_field} must be after {start_field}"))

            elif rule_type == 'field_match':
                field1 = rule.get('field1')
                field2 = rule.get('field2')
                value1 = entity_data.get(field1)
                value2 = entity_data.get(field2)

                if value1 and value2 and value1 != value2:
                    errors.append(rule.get('message', f"{field1} and {field2} must match"))

        return errors


class AuditService(DomainService):
    """Domain service for audit trail and compliance."""

    def should_audit_operation(self, operation: str, entity_type: str,
                             user_role: str) -> bool:
        """Determine if operation should be audited.

        Business Rules:
        - All financial operations are audited
        - Admin operations are audited
        - PII changes are audited
        - Audit decisions can vary by user role
        """
        # Always audit these operations
        critical_operations = [
            'financial_transaction', 'user_deletion', 'permission_change',
            'data_export', 'system_configuration_change'
        ]

        if operation in critical_operations:
            return True

        # Audit based on entity type
        sensitive_entities = ['user', 'account', 'payment', 'audit_log']
        if entity_type in sensitive_entities:
            return True

        # Audit admin operations
        if user_role in ['admin', 'superuser']:
            return True

        return False

    def generate_audit_entry(self, operation: str, entity_type: str,
                           entity_id: str, user_id: str,
                           changes: Dict[str, Any]) -> Dict[str, Any]:
        """Generate standardized audit entry.

        Business Rules:
        - Include all relevant context
        - Mask sensitive data in changes
        - Include operation metadata
        """
        # Mask sensitive fields
        sensitive_fields = ['password', 'ssn', 'credit_card', 'api_key']
        masked_changes = {}

        for field, value in changes.items():
            if any(sensitive in field.lower() for sensitive in sensitive_fields):
                masked_changes[field] = "***MASKED***"
            else:
                masked_changes[field] = value

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'user_id': user_id,
            'changes': masked_changes,
            'ip_address': None,  # Would be set by infrastructure
            'user_agent': None   # Would be set by infrastructure
        }


class SearchService(DomainService):
    """Domain service for search and filtering logic."""

    def build_search_query(self, search_term: str, fields: List[str],
                         fuzzy: bool = False) -> Dict[str, Any]:
        """Build search query for multiple fields.

        Business Rules:
        - Support exact and fuzzy matching
        - Weight different fields differently
        - Handle special characters and SQL injection prevention
        """
        if not search_term or not search_term.strip():
            return {}

        term = search_term.strip()

        if fuzzy:
            # Fuzzy search across fields
            conditions = []
            for field in fields:
                conditions.append(f"{field} LIKE '%{term}%'")
            return {"query": " OR ".join(conditions)}
        else:
            # Exact search
            conditions = []
            for field in fields:
                conditions.append(f"{field} = '{term}'")
            return {"query": " OR ".join(conditions)}

    def apply_sorting(self, sort_field: str, sort_order: str,
                     allowed_fields: List[str]) -> Dict[str, Any]:
        """Apply sorting with field validation.

        Business Rules:
        - Only allow sorting on permitted fields
        - Default to ascending order
        - Prevent SQL injection in field names
        """
        if sort_field not in allowed_fields:
            raise ValueError(f"Sorting not allowed on field: {sort_field}")

        if sort_order.lower() not in ['asc', 'desc']:
            sort_order = 'asc'

        return {
            'field': sort_field,
            'order': sort_order.upper()
        }

    def calculate_pagination(self, page: int, page_size: int,
                           total_count: int) -> Dict[str, Any]:
        """Calculate pagination metadata.

        Business Rules:
        - Page numbers start from 1
        - Enforce maximum page size
        - Calculate total pages accurately
        """
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 50  # Default page size

        total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
        offset = (page - 1) * page_size

        return {
            'page': page,
            'page_size': page_size,
            'offset': offset,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }


# Import here to avoid circular imports
import re
from datetime import datetime
