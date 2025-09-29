"""Validation pipeline for orchestrating validation across the application."""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Type, Union

from .base_validator import (
    BaseValidator,
    ValidationResult,
    ValidationError,
    ValidationException,
    ValidationContext,
    CompositeValidator
)
from .command_validators import (
    CreateDocumentCommandValidator,
    UpdateDocumentCommandValidator,
    PerformAnalysisCommandValidator,
    CreateFindingCommandValidator
)
from .query_validators import (
    GetDocumentQueryValidator,
    GetAnalysisQueryValidator,
    ListFindingsQueryValidator
)
from .business_validators import (
    DocumentBusinessValidator,
    AnalysisBusinessValidator,
    FindingBusinessValidator
)
from ..cqrs.command_bus import CommandBus
from ..cqrs.query_bus import QueryBus


logger = logging.getLogger(__name__)


class ValidationPipeline:
    """Pipeline for orchestrating validation across commands and queries."""

    def __init__(self):
        """Initialize validation pipeline."""
        self.command_validators: Dict[Type, BaseValidator] = {}
        self.query_validators: Dict[Type, BaseValidator] = {}
        self.business_validators: Dict[str, BaseValidator] = {}
        self._setup_default_validators()

    def _setup_default_validators(self):
        """Setup default validators for common commands and queries."""
        # Command validators
        self.register_command_validator(CreateDocumentCommandValidator())
        self.register_command_validator(UpdateDocumentCommandValidator())
        self.register_command_validator(PerformAnalysisCommandValidator())
        self.register_command_validator(CreateFindingCommandValidator())

        # Query validators
        self.register_query_validator(GetDocumentQueryValidator())
        self.register_query_validator(GetAnalysisQueryValidator())
        self.register_query_validator(ListFindingsQueryValidator())

        # Business validators
        self.register_business_validator('document', DocumentBusinessValidator())
        self.register_business_validator('analysis', AnalysisBusinessValidator())
        self.register_business_validator('finding', FindingBusinessValidator())

    def register_command_validator(self, validator: BaseValidator):
        """Register a validator for a specific command type."""
        # Extract command type from validator name
        validator_name = validator.__class__.__name__
        if validator_name.endswith('Validator'):
            command_name = validator_name.replace('Validator', '').replace('Command', 'Command')
            # This is a simplified mapping - in practice you'd want a more robust system
            command_type = self._get_command_type_from_name(command_name)
            if command_type:
                self.command_validators[command_type] = validator
                logger.debug(f"Registered command validator: {validator_name}")

    def register_query_validator(self, validator: BaseValidator):
        """Register a validator for a specific query type."""
        # Extract query type from validator name
        validator_name = validator.__class__.__name__
        if validator_name.endswith('Validator'):
            query_name = validator_name.replace('Validator', '').replace('Query', 'Query')
            query_type = self._get_query_type_from_name(query_name)
            if query_type:
                self.query_validators[query_type] = validator
                logger.debug(f"Registered query validator: {validator_name}")

    def register_business_validator(self, entity_type: str, validator: BaseValidator):
        """Register a business validator for an entity type."""
        self.business_validators[entity_type] = validator
        logger.debug(f"Registered business validator for: {entity_type}")

    def _get_command_type_from_name(self, name: str):
        """Get command type from name. This is a simplified implementation."""
        # In a real implementation, you'd have a registry or use type hints
        command_mappings = {
            'CreateDocument': 'CreateDocumentCommand',
            'UpdateDocument': 'UpdateDocumentCommand',
            'PerformAnalysis': 'PerformAnalysisCommand',
            'CreateFinding': 'CreateFindingCommand'
        }
        return command_mappings.get(name)

    def _get_query_type_from_name(self, name: str):
        """Get query type from name. This is a simplified implementation."""
        query_mappings = {
            'GetDocument': 'GetDocumentQuery',
            'GetAnalysis': 'GetAnalysisQuery',
            'ListFindings': 'ListFindingsQuery'
        }
        return query_mappings.get(name)

    async def validate_command(self, command: Any, context: Optional[ValidationContext] = None) -> ValidationResult:
        """Validate a command using registered validators."""
        command_type = type(command)
        context = context or ValidationContext()

        # Get command validator
        validator = self.command_validators.get(command_type)
        if not validator:
            logger.debug(f"No validator found for command: {command_type.__name__}")
            return ValidationResult.success()

        # Validate command
        result = await validator.validate(command)

        if not result.is_valid:
            logger.warning(f"Command validation failed: {command_type.__name__}", extra={
                'command_type': command_type.__name__,
                'errors': [e.message for e in result.errors],
                'correlation_id': context.correlation_id
            })

        return result

    async def validate_query(self, query: Any, context: Optional[ValidationContext] = None) -> ValidationResult:
        """Validate a query using registered validators."""
        query_type = type(query)
        context = context or ValidationContext()

        # Get query validator
        validator = self.query_validators.get(query_type)
        if not validator:
            logger.debug(f"No validator found for query: {query_type.__name__}")
            return ValidationResult.success()

        # Validate query
        result = await validator.validate(query)

        if not result.is_valid:
            logger.warning(f"Query validation failed: {query_type.__name__}", extra={
                'query_type': query_type.__name__,
                'errors': [e.message for e in result.errors],
                'correlation_id': context.correlation_id
            })

        return result

    async def validate_business_rules(self, entity: Any, entity_type: str, context: Optional[ValidationContext] = None) -> ValidationResult:
        """Validate business rules for an entity."""
        context = context or ValidationContext()

        # Get business validator
        validator = self.business_validators.get(entity_type)
        if not validator:
            logger.debug(f"No business validator found for: {entity_type}")
            return ValidationResult.success()

        # Validate business rules
        result = await validator.validate(entity)

        if result.warnings:
            logger.info(f"Business rule warnings for {entity_type}", extra={
                'entity_type': entity_type,
                'warnings': [w.message for w in result.warnings],
                'correlation_id': context.correlation_id
            })

        return result

    async def validate_all(self, command_or_query: Any, context: Optional[ValidationContext] = None) -> ValidationResult:
        """Validate using all applicable validators."""
        context = context or ValidationContext()

        # Determine if it's a command or query
        obj_type = type(command_or_query)
        obj_name = obj_type.__name__

        validators = []

        # Add command/query validator
        if 'Command' in obj_name:
            validator = self.command_validators.get(obj_type)
            if validator:
                validators.append(validator)
        elif 'Query' in obj_name:
            validator = self.query_validators.get(obj_type)
            if validator:
                validators.append(validator)

        # Add business validators if applicable
        if hasattr(command_or_query, 'document_id'):
            doc_validator = self.business_validators.get('document')
            if doc_validator:
                validators.append(doc_validator)

        if hasattr(command_or_query, 'analysis_id'):
            analysis_validator = self.business_validators.get('analysis')
            if analysis_validator:
                validators.append(analysis_validator)

        if not validators:
            return ValidationResult.success()

        # Create composite validator
        composite = CompositeValidator(validators, f"CompositeValidator_{obj_name}")

        # Validate
        result = await composite.validate(command_or_query)

        if not result.is_valid:
            logger.warning(f"Validation failed for {obj_name}", extra={
                'object_type': obj_name,
                'errors': [e.message for e in result.errors],
                'warnings': [w.message for w in result.warnings],
                'correlation_id': context.correlation_id
            })

        return result


class ValidationMiddleware:
    """Middleware for integrating validation into CQRS buses."""

    def __init__(self, validation_pipeline: ValidationPipeline):
        """Initialize validation middleware."""
        self.validation_pipeline = validation_pipeline

    async def validate_command(self, command: Any) -> None:
        """Validate command and raise exception if invalid."""
        context = ValidationContext(
            user_id=getattr(command, 'user_id', None),
            session_id=getattr(command, 'session_id', None),
            correlation_id=getattr(command, 'correlation_id', None)
        )

        result = await self.validation_pipeline.validate_command(command, context)

        if not result.is_valid:
            raise ValidationException(result)

    async def validate_query(self, query: Any) -> None:
        """Validate query and raise exception if invalid."""
        context = ValidationContext(
            user_id=getattr(query, 'user_id', None),
            session_id=getattr(query, 'session_id', None),
            correlation_id=getattr(query, 'correlation_id', None)
        )

        result = await self.validation_pipeline.validate_query(query, context)

        if not result.is_valid:
            raise ValidationException(result)

    async def validate_business_rules(self, entity: Any, entity_type: str) -> List[ValidationError]:
        """Validate business rules and return warnings/errors."""
        context = ValidationContext()

        result = await self.validation_pipeline.validate_business_rules(entity, entity_type, context)

        return result.errors + result.warnings


class ValidatingCommandBus(CommandBus):
    """Command bus with integrated validation."""

    def __init__(self, validation_pipeline: ValidationPipeline, event_bus=None):
        """Initialize validating command bus."""
        super().__init__(event_bus)
        self.validation_middleware = ValidationMiddleware(validation_pipeline)

    async def send(self, command: Any) -> Any:
        """Send command with validation."""
        # Validate command first
        await self.validation_middleware.validate_command(command)

        # Proceed with normal command processing
        return await super().send(command)


class ValidatingQueryBus(QueryBus):
    """Query bus with integrated validation."""

    def __init__(self, validation_pipeline: ValidationPipeline):
        """Initialize validating query bus."""
        super().__init__()
        self.validation_middleware = ValidationMiddleware(validation_pipeline)

    async def send(self, query: Any) -> Any:
        """Send query with validation."""
        # Validate query first
        await self.validation_middleware.validate_query(query)

        # Proceed with normal query processing
        return await super().send(query)


# Global validation pipeline instance
validation_pipeline = ValidationPipeline()
validation_middleware = ValidationMiddleware(validation_pipeline)
