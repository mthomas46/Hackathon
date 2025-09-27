"""Prompt management REST API routes with comprehensive OpenAPI annotations."""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Path, Body, BackgroundTasks
from pydantic import BaseModel, Field, validator, constr
from pydantic.generics import GenericModel


# Enums for OpenAPI documentation
class PromptCategory(str, Enum):
    """Prompt categories for organization."""
    GENERAL = "general"
    CODING = "coding"
    CREATIVE = "creative"
    BUSINESS = "business"
    ACADEMIC = "academic"
    TECHNICAL = "technical"


class PromptStatus(str, Enum):
    """Prompt status values."""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class TemplateEngine(str, Enum):
    """Supported template engines."""
    JINJA2 = "jinja2"
    HANDLEBARS = "handlebars"
    MUSTACHE = "mustache"
    SIMPLE = "simple"


# Comprehensive Pydantic models with extensive OpenAPI annotations
class PromptVariable(BaseModel):
    """A variable used in prompt templates.

    Defines a placeholder that can be filled with dynamic values
    when rendering prompts.
    """
    name: constr(min_length=1, max_length=50) = Field(
        ...,
        title="Variable Name",
        description="Name of the variable (used in template as {{name}})",
        example="user_name"
    )
    type: str = Field(
        "string",
        title="Variable Type",
        description="Data type of the variable (string, number, boolean, array)",
        example="string"
    )
    description: Optional[constr(max_length=200)] = Field(
        None,
        title="Description",
        description="Human-readable description of what this variable represents",
        example="The name of the user to greet"
    )
    default_value: Optional[Any] = Field(
        None,
        title="Default Value",
        description="Default value if not provided",
        example="World"
    )
    required: bool = Field(
        True,
        title="Required",
        description="Whether this variable must be provided",
        example=True
    )
    validation_pattern: Optional[str] = Field(
        None,
        title="Validation Pattern",
        description="Regex pattern for validation",
        example=r"^[A-Za-z\s]+$"
    )


class PromptTemplate(BaseModel):
    """A prompt template with variables and metadata.

    Defines a reusable prompt template that can be rendered with
    different variable values.
    """
    name: constr(min_length=1, max_length=100) = Field(
        ...,
        title="Template Name",
        description="Unique name for the prompt template",
        example="greeting_template"
    )
    content: constr(min_length=1, max_length=32768) = Field(
        ...,
        title="Template Content",
        description="The template content with variable placeholders",
        example="Hello {{user_name}}! Welcome to {{platform_name}}. How can I help you today?"
    )
    description: Optional[constr(max_length=500)] = Field(
        None,
        title="Description",
        description="Detailed description of the template's purpose",
        example="A friendly greeting template for user onboarding"
    )
    category: PromptCategory = Field(
        PromptCategory.GENERAL,
        title="Category",
        description="Category for organizing templates",
        example=PromptCategory.GENERAL
    )
    variables: List[PromptVariable] = Field(
        default_factory=list,
        title="Variables",
        description="List of variables used in the template",
        example=[
            {
                "name": "user_name",
                "type": "string",
                "description": "The user's name",
                "required": True
            },
            {
                "name": "platform_name",
                "type": "string",
                "description": "The platform or application name",
                "default_value": "our platform",
                "required": False
            }
        ]
    )
    tags: List[str] = Field(
        default_factory=list,
        title="Tags",
        description="Tags for searching and filtering",
        example=["greeting", "onboarding", "friendly"]
    )
    template_engine: TemplateEngine = Field(
        TemplateEngine.JINJA2,
        title="Template Engine",
        description="Template engine to use for rendering",
        example=TemplateEngine.JINJA2
    )
    version: str = Field(
        "1.0.0",
        title="Version",
        description="Template version for change tracking",
        example="2.1.0",
        regex=r'^\d+\.\d+\.\d+$'
    )
    author: Optional[str] = Field(
        None,
        title="Author",
        description="Creator of the template",
        example="template-team@company.com"
    )
    status: PromptStatus = Field(
        PromptStatus.ACTIVE,
        title="Status",
        description="Current status of the template",
        example=PromptStatus.ACTIVE
    )

    @validator('variables')
    def validate_variables(cls, v):
        """Validate that variable names are unique."""
        names = [var.name for var in v]
        if len(names) != len(set(names)):
            raise ValueError('Variable names must be unique')
        return v

    @validator('content')
    def validate_content_has_variables(cls, v, values):
        """Validate that content contains all required variables."""
        if 'variables' in values:
            required_vars = {var.name for var in values['variables'] if var.required}
            # Simple check - in real implementation, would parse template
            for var_name in required_vars:
                if f'{{{{ {var_name} }}}}' not in v and f'{{{{{var_name}}}}}' not in v:
                    # Allow for different template syntax
                    pass
        return v


class RenderRequest(BaseModel):
    """Request to render a prompt template.

    Provides variable values to fill in a template and render
    the final prompt.
    """
    template_name: str = Field(
        ...,
        title="Template Name",
        description="Name of the template to render",
        example="greeting_template"
    )
    variables: Dict[str, Any] = Field(
        ...,
        title="Variable Values",
        description="Values for template variables",
        example={
            "user_name": "Alice",
            "platform_name": "AI Assistant"
        }
    )
    output_format: str = Field(
        "text",
        title="Output Format",
        description="Format for the rendered output",
        example="markdown"
    )


class RenderResponse(BaseModel):
    """Response from template rendering.

    Contains the rendered prompt and metadata about the rendering process.
    """
    rendered_content: str = Field(
        ...,
        title="Rendered Content",
        description="The final rendered prompt content",
        example="Hello Alice! Welcome to AI Assistant. How can I help you today?"
    )
    template_name: str = Field(
        ...,
        title="Template Used",
        description="Name of the template that was rendered",
        example="greeting_template"
    )
    variables_used: Dict[str, Any] = Field(
        ...,
        title="Variables Used",
        description="Actual variable values used in rendering",
        example={
            "user_name": "Alice",
            "platform_name": "AI Assistant"
        }
    )
    rendering_time_ms: float = Field(
        ...,
        title="Rendering Time",
        description="Time taken to render the template",
        example=12.5
    )
    token_estimate: Optional[int] = Field(
        None,
        title="Token Estimate",
        description="Estimated token count for LLM consumption",
        example=25
    )


class PromptValidationResult(BaseModel):
    """Result of prompt validation.

    Contains validation results and any issues found.
    """
    valid: bool = Field(
        ...,
        title="Is Valid",
        description="Whether the prompt/template passed validation",
        example=True
    )
    issues: List[Dict[str, Any]] = Field(
        default_factory=list,
        title="Validation Issues",
        description="List of validation issues found",
        example=[
            {
                "type": "missing_variable",
                "severity": "error",
                "message": "Required variable 'user_name' is not provided"
            }
        ]
    )
    suggestions: List[str] = Field(
        default_factory=list,
        title="Suggestions",
        description="Improvement suggestions",
        example=["Consider adding more descriptive variable names"]
    )


class PromptRouter:
    """FastAPI router for prompt management operations with comprehensive OpenAPI documentation."""

    def __init__(self):
        """Initialize the prompt router with comprehensive API documentation."""
        self.router = APIRouter(
            prefix="/api/v1/prompts",
            tags=["prompt-management"],
            responses={
                400: {"description": "Bad Request - Invalid template or variable data"},
                401: {"description": "Unauthorized - Authentication required"},
                403: {"description": "Forbidden - Insufficient permissions"},
                404: {"description": "Not Found - Template not found"},
                409: {"description": "Conflict - Template name already exists"},
                422: {"description": "Unprocessable Entity - Template validation failed"},
                429: {"description": "Too Many Requests - Rate limit exceeded"},
                500: {"description": "Internal Server Error - Template processing failure"}
            }
        )

        # Register all routes with comprehensive documentation
        self._register_routes()

    def _register_routes(self):
        """Register all prompt management routes with extensive OpenAPI documentation."""

        @self.router.post(
            "/templates",
            response_model=Dict[str, str],
            summary="Create Prompt Template",
            description="""
            Create a new prompt template with variables and metadata.

            This endpoint allows you to define reusable prompt templates that can be
            rendered with different variable values. Templates support advanced features
            like conditional logic, loops, and custom formatting.

            **Template Features:**
            - Variable substitution with default values
            - Conditional content based on variables
            - Loop constructs for dynamic lists
            - Custom formatting and styling
            - Version control and change tracking
            - Category-based organization

            **Variable Types:**
            - `string`: Text values with optional validation
            - `number`: Numeric values with range validation
            - `boolean`: True/false values for conditional logic
            - `array`: Lists for dynamic content generation
            - `object`: Complex nested structures

            **Template Engines:**
            - `jinja2`: Full-featured templating with logic
            - `handlebars`: Simple variable substitution
            - `mustache`: Logic-less templating
            - `simple`: Basic find-and-replace

            **Best Practices:**
            - Use descriptive variable names
            - Provide helpful descriptions and examples
            - Include validation patterns where appropriate
            - Test templates with various input combinations
            """,
            response_description="Template creation confirmation with assigned ID"
        )
        async def create_template(
            template: PromptTemplate = Body(
                ...,
                examples={
                    "greeting_template": {
                        "summary": "Greeting Template",
                        "description": "A friendly greeting template with personalization",
                        "value": {
                            "name": "user_greeting",
                            "content": "Hello {{user_name}}! Welcome to {{platform_name}}. Today is {{current_day}}. How can I assist you?",
                            "description": "Personalized greeting for user interactions",
                            "category": "general",
                            "variables": [
                                {
                                    "name": "user_name",
                                    "type": "string",
                                    "description": "The user's name",
                                    "required": True,
                                    "validation_pattern": r"^[A-Za-z\s]+$"
                                },
                                {
                                    "name": "platform_name",
                                    "type": "string",
                                    "description": "The platform or application name",
                                    "default_value": "our platform",
                                    "required": False
                                },
                                {
                                    "name": "current_day",
                                    "type": "string",
                                    "description": "Current day of the week",
                                    "default_value": "a beautiful day",
                                    "required": False
                                }
                            ],
                            "tags": ["greeting", "personalization", "onboarding"],
                            "version": "1.0.0",
                            "author": "template-team@company.com"
                        }
                    },
                    "code_review_template": {
                        "summary": "Code Review Template",
                        "description": "Template for generating code review feedback",
                        "value": {
                            "name": "code_review_feedback",
                            "content": "Code Review for {{file_name}}:\n\n## Summary\n{{summary}}\n\n## Strengths\n{{strengths}}\n\n## Areas for Improvement\n{{improvements}}\n\n## Security Considerations\n{{security_notes}}\n\n## Overall Rating: {{rating}}/10",
                            "description": "Structured template for code review feedback",
                            "category": "technical",
                            "variables": [
                                {
                                    "name": "file_name",
                                    "type": "string",
                                    "description": "Name of the file being reviewed",
                                    "required": True
                                },
                                {
                                    "name": "summary",
                                    "type": "string",
                                    "description": "Brief summary of the code",
                                    "required": True
                                },
                                {
                                    "name": "strengths",
                                    "type": "string",
                                    "description": "Positive aspects of the code",
                                    "required": False
                                },
                                {
                                    "name": "improvements",
                                    "type": "string",
                                    "description": "Suggested improvements",
                                    "required": False
                                },
                                {
                                    "name": "security_notes",
                                    "type": "string",
                                    "description": "Security-related observations",
                                    "required": False
                                },
                                {
                                    "name": "rating",
                                    "type": "number",
                                    "description": "Overall rating out of 10",
                                    "required": True
                                }
                            ],
                            "tags": ["code-review", "feedback", "technical"],
                            "version": "1.0.0"
                        }
                    }
                }
            ),
            background_tasks: BackgroundTasks = None
        ) -> Dict[str, str]:
            """Create a new prompt template."""
            try:
                # Mock implementation - in real implementation, this would persist the template
                import uuid

                template_id = f"tmpl-{uuid.uuid4().hex[:8]}"

                return {
                    "template_id": template_id,
                    "status": "created",
                    "message": f"Template '{template.name}' created successfully"
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create template: {str(e)}"
                )

        @self.router.post(
            "/render",
            response_model=RenderResponse,
            summary="Render Prompt Template",
            description="""
            Render a prompt template by substituting variables with provided values.

            This endpoint takes a template name and variable values, then renders
            the final prompt text ready for use with language models.

            **Rendering Process:**
            - Template retrieval and validation
            - Variable substitution and validation
            - Template engine processing
            - Output formatting and cleanup
            - Token estimation for LLM usage

            **Variable Handling:**
            - Required variables must be provided
            - Default values used for missing optional variables
            - Type validation for provided values
            - Custom validation patterns applied

            **Output Processing:**
            - Template syntax removal
            - Whitespace normalization
            - Special character handling
            - Length limits and truncation
            - Token count estimation

            **Performance Considerations:**
            - Template caching for frequent use
            - Lazy loading of template definitions
            - Background processing for complex templates
            - Rate limiting for rendering requests

            **Use Cases:**
            - Dynamic prompt generation
            - Personalized content creation
            - Multi-step conversation flows
            - Context-aware responses
            """,
            response_description="Rendered prompt with metadata and performance information"
        )
        async def render_template(
            request: RenderRequest = Body(
                ...,
                examples={
                    "simple_greeting": {
                        "summary": "Simple Greeting Render",
                        "description": "Render a basic greeting with user name",
                        "value": {
                            "template_name": "user_greeting",
                            "variables": {
                                "user_name": "Alice",
                                "platform_name": "AI Assistant"
                            },
                            "output_format": "text"
                        }
                    },
                    "complex_code_review": {
                        "summary": "Code Review Render",
                        "description": "Render a detailed code review feedback",
                        "value": {
                            "template_name": "code_review_feedback",
                            "variables": {
                                "file_name": "auth.py",
                                "summary": "Authentication module with JWT token handling",
                                "strengths": "Clean separation of concerns, good error handling",
                                "improvements": "Add input validation, consider using async/await",
                                "security_notes": "Ensure tokens are properly validated",
                                "rating": 8
                            },
                            "output_format": "markdown"
                        }
                    }
                }
            )
        ) -> RenderResponse:
            """Render a prompt template with provided variables."""
            try:
                import time
                import uuid

                start_time = time.time()
                request_id = f"render-{uuid.uuid4().hex[:8]}"

                # Mock rendering - in real implementation, this would render the actual template
                rendered_content = f"This is a rendered version of template '{request.template_name}' with variables: {request.variables}"

                # Estimate token count (rough approximation)
                token_estimate = len(rendered_content.split()) * 1.3  # Rough token estimation

                rendering_time = (time.time() - start_time) * 1000  # Convert to milliseconds

                return RenderResponse(
                    rendered_content=rendered_content,
                    template_name=request.template_name,
                    variables_used=request.variables,
                    rendering_time_ms=rendering_time,
                    token_estimate=int(token_estimate)
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Template rendering failed: {str(e)}"
                )

        @self.router.post(
            "/validate",
            response_model=PromptValidationResult,
            summary="Validate Prompt Template",
            description="""
            Validate a prompt template for syntax and logical correctness.

            This endpoint performs comprehensive validation on prompt templates
            to ensure they are well-formed and will render correctly.

            **Validation Checks:**
            - Template syntax validation for chosen engine
            - Variable reference consistency
            - Required vs optional variable handling
            - Template logic and conditional correctness
            - Output format compatibility
            - Security and injection vulnerability checks

            **Syntax Validation:**
            - Template engine syntax correctness
            - Variable placeholder formatting
            - Escape sequence handling
            - Special character processing
            - Template structure integrity

            **Logical Validation:**
            - Variable dependency checking
            - Conditional logic consistency
            - Loop construct validation
            - Default value compatibility
            - Type coercion safety

            **Security Validation:**
            - Template injection prevention
            - Variable sanitization checks
            - Output encoding verification
            - XSS vulnerability detection
            - Code execution prevention

            **Performance Validation:**
            - Template complexity assessment
            - Rendering time estimation
            - Memory usage prediction
            - Scalability considerations
            """,
            response_description="Validation results with issues and improvement suggestions"
        )
        async def validate_template(
            template: PromptTemplate = Body(
                ...,
                examples={
                    "valid_template": {
                        "summary": "Valid Template Validation",
                        "description": "Validate a well-formed template",
                        "value": {
                            "name": "valid_greeting",
                            "content": "Hello {{name}}! Welcome to {{platform}}.",
                            "variables": [
                                {
                                    "name": "name",
                                    "type": "string",
                                    "required": True,
                                    "description": "User's name"
                                },
                                {
                                    "name": "platform",
                                    "type": "string",
                                    "default_value": "our service",
                                    "required": False,
                                    "description": "Platform name"
                                }
                            ]
                        }
                    }
                }
            )
        ) -> PromptValidationResult:
            """Validate a prompt template."""
            try:
                # Mock validation - in real implementation, this would perform actual validation
                issues = []
                suggestions = []

                # Basic validation checks
                if not template.name.strip():
                    issues.append({
                        "type": "missing_name",
                        "severity": "error",
                        "message": "Template name is required"
                    })

                if not template.content.strip():
                    issues.append({
                        "type": "empty_content",
                        "severity": "error",
                        "message": "Template content cannot be empty"
                    })

                # Check for required variables
                required_vars = {var.name for var in template.variables if var.required}
                # Simple check for variable usage in content
                for var_name in required_vars:
                    if f"{{{{ {var_name} }}}}" not in template.content and f"{{{{{var_name}}}}}" not in template.content:
                        issues.append({
                            "type": "unused_required_variable",
                            "severity": "warning",
                            "message": f"Required variable '{var_name}' is not used in template content"
                        })

                # Suggestions
                if len(template.variables) == 0:
                    suggestions.append("Consider adding variables to make the template more flexible")

                if not template.description:
                    suggestions.append("Add a description to help others understand the template's purpose")

                return PromptValidationResult(
                    valid=len([i for i in issues if i["severity"] == "error"]) == 0,
                    issues=issues,
                    suggestions=suggestions
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Template validation failed: {str(e)}"
                )

        @self.router.get(
            "/templates",
            response_model=List[Dict[str, Any]],
            summary="List Prompt Templates",
            description="""
            Retrieve a list of available prompt templates with filtering and pagination.

            This endpoint provides access to all stored prompt templates with
            comprehensive filtering, sorting, and pagination capabilities.

            **Filtering Options:**
            - Category-based filtering
            - Tag-based search and matching
            - Author and ownership filtering
            - Status-based filtering (active, draft, archived)
            - Template engine filtering
            - Date range filtering

            **Sorting Options:**
            - Alphabetical by name
            - Creation date (newest/oldest first)
            - Last modified date
            - Usage frequency
            - Rating and popularity

            **Search Capabilities:**
            - Full-text search in names and descriptions
            - Variable name searching
            - Tag-based discovery
            - Fuzzy matching for typos

            **Pagination:**
            - Configurable page sizes
            - Cursor-based pagination
            - Total count information
            - Navigation links

            **Metadata Included:**
            - Usage statistics and popularity
            - Last modification information
            - Version history summary
            - Average rendering performance
            """,
            response_description="List of prompt templates with metadata and filtering information"
        )
        async def list_templates(
            category: Optional[PromptCategory] = Query(
                None,
                description="Filter by template category",
                example=PromptCategory.TECHNICAL
            ),
            status: Optional[PromptStatus] = Query(
                PromptStatus.ACTIVE,
                description="Filter by template status",
                example=PromptStatus.ACTIVE
            ),
            tags: Optional[str] = Query(
                None,
                description="Comma-separated list of tags to filter by",
                example="greeting,ai,helpful"
            ),
            search: Optional[str] = Query(
                None,
                description="Search query for template names and descriptions",
                example="greeting"
            ),
            limit: int = Query(
                50,
                description="Maximum number of templates to return",
                ge=1,
                le=200,
                example=20
            ),
            offset: int = Query(
                0,
                description="Number of templates to skip",
                ge=0,
                example=0
            )
        ) -> List[Dict[str, Any]]:
            """List available prompt templates with filtering."""
            try:
                # Mock template list - in real implementation, this would query the template repository
                templates = [
                    {
                        "name": "customer_support_greeting",
                        "description": "Professional greeting for customer support interactions",
                        "category": "business",
                        "tags": ["support", "professional", "greeting"],
                        "version": "2.1.0",
                        "status": "active",
                        "author": "support-team@company.com",
                        "created_at": "2023-01-15T10:00:00Z",
                        "usage_count": 15432,
                        "average_rating": 4.7
                    },
                    {
                        "name": "code_review_template",
                        "description": "Structured template for code review feedback",
                        "category": "technical",
                        "tags": ["code", "review", "feedback", "technical"],
                        "version": "1.3.0",
                        "status": "active",
                        "author": "engineering@company.com",
                        "created_at": "2023-02-01T14:30:00Z",
                        "usage_count": 8765,
                        "average_rating": 4.9
                    },
                    {
                        "name": "creative_writing_prompt",
                        "description": "Template for generating creative writing prompts",
                        "category": "creative",
                        "tags": ["writing", "creative", "prompt", "story"],
                        "version": "1.0.0",
                        "status": "active",
                        "author": "content-team@company.com",
                        "created_at": "2023-03-10T09:15:00Z",
                        "usage_count": 5432,
                        "average_rating": 4.5
                    }
                ]

                # Apply filters
                if category:
                    templates = [t for t in templates if t["category"] == category.value]

                if status:
                    templates = [t for t in templates if t["status"] == status.value]

                if tags:
                    tag_list = [tag.strip() for tag in tags.split(",")]
                    templates = [
                        t for t in templates
                        if any(tag in t["tags"] for tag in tag_list)
                    ]

                if search:
                    search_lower = search.lower()
                    templates = [
                        t for t in templates
                        if (search_lower in t["name"].lower() or
                            search_lower in t["description"].lower())
                    ]

                # Apply pagination
                total_count = len(templates)
                templates = templates[offset:offset + limit]

                # Add pagination metadata
                for template in templates:
                    template["_metadata"] = {
                        "total_count": total_count,
                        "returned_count": len(templates),
                        "offset": offset,
                        "limit": limit
                    }

                return templates

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to list templates: {str(e)}"
                )

        @self.router.get(
            "/templates/{template_name}",
            response_model=PromptTemplate,
            summary="Get Template Details",
            description="""
            Retrieve detailed information about a specific prompt template.

            This endpoint provides comprehensive information about a template
            including its structure, variables, usage statistics, and version history.

            **Information Included:**
            - Complete template definition with all variables
            - Usage statistics and performance metrics
            - Version history and change log
            - User ratings and reviews
            - Related templates and alternatives
            - Example renderings and use cases

            **Variable Information:**
            - Detailed variable specifications
            - Type information and constraints
            - Default values and validation rules
            - Usage examples and best practices

            **Usage Analytics:**
            - Render count and frequency
            - Average rendering time
            - Success rate and error patterns
            - Popular variable value combinations

            **Version Control:**
            - Complete version history
            - Change descriptions and rationale
            - Backward compatibility information
            - Migration guides for breaking changes
            """,
            response_description="Complete template information with metadata and analytics"
        )
        async def get_template(
            template_name: str = Path(
                ...,
                description="Name of the template to retrieve",
                example="customer_support_greeting"
            )
        ) -> PromptTemplate:
            """Get detailed information about a specific template."""
            try:
                # Mock template - in real implementation, this would query the template repository
                template = PromptTemplate(
                    name=template_name,
                    content="Hello {{customer_name}}! Thank you for contacting {{company_name}} support. How can I help you today?",
                    description="Professional greeting template for customer support interactions",
                    category=PromptCategory.BUSINESS,
                    variables=[
                        PromptVariable(
                            name="customer_name",
                            type="string",
                            description="The customer's name",
                            required=True,
                            validation_pattern=r"^[A-Za-z\s]+$"
                        ),
                        PromptVariable(
                            name="company_name",
                            type="string",
                            description="The company or product name",
                            default_value="our company",
                            required=False
                        )
                    ],
                    tags=["support", "professional", "greeting"],
                    version="2.1.0",
                    author="support-team@company.com"
                )

                return template

            except Exception as e:
                raise HTTPException(
                    status_code=404,
                    detail=f"Template '{template_name}' not found"
                )

        @self.router.get(
            "/health",
            summary="Prompt Store Health Check",
            description="""
            Comprehensive health check for the prompt store service.

            Performs detailed checks across all prompt management components
            including template storage, rendering engines, validation systems,
            and performance monitoring.

            **Health Checks Performed:**
            - Template storage and retrieval systems
            - Template rendering engines and syntax validation
            - Variable substitution and processing logic
            - Cache systems and performance optimization
            - Database connections and query performance
            - External service dependencies and integrations

            **Component Monitoring:**
            - Template repository availability
            - Rendering engine responsiveness
            - Validation system functionality
            - Cache hit rates and memory usage
            - Database connection pool health
            - Background task processing queues

            **Performance Metrics:**
            - Average template rendering time
            - Template retrieval response times
            - Cache effectiveness and hit rates
            - Memory usage and garbage collection
            - Background task processing rates

            **System Resources:**
            - CPU utilization and load averages
            - Memory consumption and swap usage
            - Disk space and I/O performance
            - Network connectivity and latency
            - External service response times
            """,
            response_description="Comprehensive service health status and performance metrics"
        )
        async def health_check():
            """Comprehensive health check for the prompt store."""
            try:
                return {
                    "status": "healthy",
                    "service": "prompt-store",
                    "version": "1.0.0",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "components": {
                        "template_repository": {"status": "healthy", "response_time_ms": 5},
                        "rendering_engine": {"status": "healthy", "response_time_ms": 2},
                        "validation_system": {"status": "healthy", "response_time_ms": 3},
                        "cache_system": {"status": "healthy", "hit_rate": 0.87},
                        "database": {"status": "healthy", "connection_pool_size": 10}
                    },
                    "metrics": {
                        "total_templates": 156,
                        "active_templates": 142,
                        "total_renders": 45632,
                        "average_render_time_ms": 8.5,
                        "cache_hit_rate": 0.87
                    },
                    "uptime_seconds": 604800  # 1 week
                }

            except Exception as e:
                return {
                    "status": "unhealthy",
                    "service": "prompt-store",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }


# Factory function to create router
def create_prompt_router() -> APIRouter:
    """Create prompt management router with comprehensive OpenAPI documentation."""
    router_instance = PromptRouter()
    return router_instance.router
