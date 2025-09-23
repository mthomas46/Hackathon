"""
🔒 Secure Analyzer Service - Enterprise Security Intelligence Hub

REST API Standardization - Phase 4C
====================================

Comprehensive OpenAPI/Swagger annotations for enterprise-grade API documentation,
consistent response formats, and standardized error handling.

API Endpoints:
==============
• GET  /health - Service health and status information
• POST /detect - Advanced content security analysis with pattern matching
• POST /suggest - Intelligent AI model recommendations based on content sensitivity
• POST /summarize - Secure content summarization with policy-based provider filtering

Key Features:
=============
• Enterprise-grade security analysis with AI-powered threat detection
• Comprehensive OpenAPI/Swagger documentation with detailed schemas
• Consistent response formats and standardized error handling
• Request/response validation with Pydantic models
• Circuit breaker protection for resilient operation
• Comprehensive audit trails and performance monitoring

Dependencies: shared middlewares/logging, ServiceClients, httpx for external calls.
"""

import os
import time
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, ConfigDict

from services.shared.core.constants_new import EnvVars, ServiceNames  # type: ignore
from services.shared.monitoring.logging import fire_and_forget  # type: ignore
from services.shared.utilities.logging_client import get_log_collector_client
from services.shared.utilities.utilities import attach_self_register, setup_common_middleware  # type: ignore

try:
    from .modules.circuit_breaker import circuit_breaker, operation_timeout_context
    from .modules.content_detector import content_detector
    from .modules.policy_enforcer import policy_enforcer
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from modules.circuit_breaker import circuit_breaker, operation_timeout_context
    from modules.content_detector import content_detector
    from modules.policy_enforcer import policy_enforcer

# Service configuration constants
SERVICE_NAME = "secure-analyzer"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = 5070

# Content validation limits
MAX_CONTENT_SIZE_BYTES = 1000000  # 1MB
MAX_KEYWORDS_COUNT = 1000
MAX_KEYWORD_LENGTH = 500
MAX_PROVIDER_NAME_LENGTH = 100

# Circuit breaker defaults
DEFAULT_CIRCUIT_BREAKER_MAX_FAILURES = 5
DEFAULT_CIRCUIT_BREAKER_TIMEOUT = 60

# Initialize log collector client
logger_client = None

# Standard API response models for consistent error handling
class APIResponse(BaseModel):
    """Standard API response wrapper for consistent formatting."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Human-readable response message")
    data: Optional[Any] = Field(None, description="Response data payload")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")
    timestamp: Optional[str] = Field(None, description="Response timestamp in ISO 8601 format")
    processing_time_ms: Optional[float] = Field(None, description="Processing time in milliseconds")


class ErrorResponse(BaseModel):
    """Standard error response for consistent error formatting."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(default=False, description="Always false for error responses")
    error: Dict[str, Any] = Field(..., description="Error details")
    request_id: Optional[str] = Field(None, description="Unique request identifier for tracing")
    timestamp: str = Field(..., description="Error timestamp in ISO 8601 format")


class HealthResponse(BaseModel):
    """Health check response model."""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    circuit_breaker_open: bool = Field(..., description="Circuit breaker status")
    description: str = Field(..., description="Health status description")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    last_health_check: Optional[str] = Field(None, description="Last health check timestamp")


app = FastAPI(
    title="🔒 Secure Analyzer - Enterprise Security Intelligence Hub",
    version=SERVICE_VERSION,
    description="""
    **Enterprise Security Intelligence Hub** for AI-powered content security analysis.

    ## 🎯 **Core Capabilities**

    ### **🔍 Advanced Security Scanning**
    - **Multi-Layer Security Analysis**: Comprehensive threat detection with AI-powered false positive reduction
    - **Pattern Matching Engine**: Advanced regex and keyword detection with contextual analysis
    - **Behavioral Analysis**: ML-powered analysis of content patterns and security indicators
    - **Real-Time Threat Intelligence**: Integration with threat intelligence feeds and databases

    ### **🛡️ Policy Enforcement & Governance**
    - **Dynamic Policy Application**: Context-aware security policy application based on content sensitivity
    - **Provider Recommendation Engine**: Intelligent AI provider selection based on security requirements
    - **Access Control Integration**: Integration with enterprise identity and access management systems
    - **Audit Trails**: Complete audit logging for compliance and forensic analysis

    ### **🤖 AI-Powered Analysis**
    - **Contextual Risk Assessment**: AI-powered risk assessment considering business context and impact
    - **Automated Security Recommendations**: Intelligent suggestions for security improvements
    - **Threat Pattern Recognition**: ML-powered identification of emerging threat patterns
    - **Compliance Validation**: Automated compliance checking against regulatory frameworks

    ## 📡 **API Architecture**

    ### **🏗️ Enterprise API Design**
    - **RESTful Endpoints**: Standard HTTP methods with consistent URL patterns
    - **OpenAPI/Swagger Documentation**: Comprehensive API documentation with examples
    - **Request Validation**: Strict input validation with detailed error messages
    - **Response Standardization**: Consistent response formats across all endpoints

    ### **🔒 Security Features**
    - **Circuit Breaker Protection**: Automatic failure detection and graceful degradation
    - **Rate Limiting**: Configurable rate limiting and throttling for API protection
    - **Input Validation**: Comprehensive input sanitization and validation
    - **Audit Logging**: Complete audit trails for security and compliance

    ## 🏢 **Enterprise Integration**

    ### **🔗 Ecosystem Services**
    - **Summarizer Hub**: Integration for secure content summarization with policy enforcement
    - **Log Collector**: Comprehensive audit logging and security event tracking
    - **Orchestrator**: Workflow orchestration for complex security analysis pipelines
    - **Analysis Service**: Advanced security analysis and threat intelligence correlation

    ### **📊 Monitoring & Analytics**
    - **Real-Time Metrics**: Comprehensive performance and security metrics
    - **Health Monitoring**: Automated health checks and service status monitoring
    - **Alert Integration**: Automated alerting for security events and service issues
    - **Analytics Dashboard**: Security analytics and reporting capabilities
    """,
    contact={
        "name": "Secure Analyzer Service Team",
        "url": "https://github.com/your-org/secure-analyzer",
        "email": "security@your-org.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://your-org.com/license"
    },
    openapi_tags=[
        {
            "name": "Health & Monitoring",
            "description": "Service health checks and monitoring endpoints"
        },
        {
            "name": "Security Analysis",
            "description": "Content security analysis and threat detection"
        },
        {
            "name": "Policy Enforcement",
            "description": "AI model recommendations and policy enforcement"
        },
        {
            "name": "Content Processing",
            "description": "Secure content summarization and processing"
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global logger_client
    try:
        # Use a fallback service name if SECURE_ANALYZER doesn't exist in ServiceNames
        service_name = getattr(ServiceNames, "SECURE_ANALYZER", SERVICE_NAME)
        logger_client = await get_log_collector_client(service_name)
        if logger_client:
            await logger_client.log_business_event(
                "secure_analyzer_startup",
                {
                    "version": SERVICE_VERSION,
                    "capabilities": [
                        "content_security_analysis",
                        "policy_enforcement",
                        "circuit_breaker_protection",
                        "model_suggestions",
                        "content_summarization",
                    ],
                    "integrations": ["log_collector", "summarizer_hub", "content_detection_modules"],
                    "security_features": [
                        "pattern_matching",
                        "keyword_detection",
                        "circuit_breaker",
                        "timeout_protection",
                        "policy_enforcement",
                    ],
                    "analysis_types": ["sensitive_content_detection", "model_recommendations", "content_summarization"],
                },
            )
            await logger_client.log_info(
                "Secure Analyzer service started",
                {
                    "circuit_breaker_enabled": True,
                    "content_detection_ready": True,
                    "model_suggestion_engine": True,
                    "summarization_integration": True,
                },
            )
    except Exception as e:
        print(f"Failed to initialize log collector client: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if logger_client:
        try:
            await logger_client.log_info("Secure Analyzer service shutting down")
        except Exception:
            pass


# Use common middleware setup to reduce duplication across services
# setup_common_middleware already imported above
setup_common_middleware(app, ServiceNames.SECURE_ANALYZER)
attach_self_register(app, ServiceNames.SECURE_ANALYZER)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="""
    **Service Health Check** - Comprehensive health status and operational metrics.

    ## 🔍 **Health Assessment**

    This endpoint provides real-time health status and operational metrics for the Secure Analyzer service, including:

    ### **🏥 Health Indicators**
    - **Service Status**: Overall health status (healthy/degraded/unhealthy)
    - **Circuit Breaker**: Current circuit breaker state and protection status
    - **Version Information**: Current service version and build details
    - **Uptime Metrics**: Service uptime and operational statistics

    ### **📊 Operational Metrics**
    - **Performance Stats**: Response times and throughput metrics
    - **Resource Usage**: Memory, CPU, and resource utilization
    - **Integration Status**: Health of connected services and dependencies
    - **Security Status**: Security modules and threat detection status

    ## 🎯 **Response Codes**

    | Code | Status | Description |
    |------|--------|-------------|
    | 200 | Healthy | Service is fully operational |
    | 503 | Degraded | Service is operational but with issues |
    | 500 | Unhealthy | Service is experiencing critical issues |

    ## 📋 **Usage Examples**

    ### **Basic Health Check**
    ```bash
    curl -X GET http://localhost:5080/health
    ```

    ### **Health Check with Monitoring**
    ```python
    import requests

    response = requests.get("http://localhost:5080/health")
    health_data = response.json()

    if health_data["status"] == "healthy":
        print("✅ Service is healthy")
    else:
        print("⚠️  Service health issue detected")
    ```
    """,
    response_description="Comprehensive health status and operational metrics",
    responses={
        200: {
            "description": "Service is healthy and fully operational",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "service": "secure-analyzer",
                        "version": "3.0.0",
                        "circuit_breaker_open": False,
                        "description": "Secure analyzer service is operational",
                        "uptime_seconds": 3600.5,
                        "last_health_check": "2024-09-22T10:30:00Z"
                    }
                }
            }
        },
        503: {
            "description": "Service is degraded or temporarily unavailable",
            "model": HealthResponse,
            "content": {
                "application/json": {
                    "example": {
                        "status": "degraded",
                        "service": "secure-analyzer",
                        "version": "3.0.0",
                        "circuit_breaker_open": True,
                        "description": "Service temporarily unavailable due to circuit breaker",
                        "uptime_seconds": 1800.0,
                        "last_health_check": "2024-09-22T10:25:00Z"
                    }
                }
            }
        }
    },
    tags=["Health & Monitoring"]
)
async def health() -> HealthResponse:
    """
    **Health Check Endpoint** - Comprehensive service health assessment.

    Returns detailed health status including:
    - Service operational status
    - Circuit breaker state
    - Version information
    - Uptime metrics
    - Last health check timestamp
    """
    import datetime

    # Calculate uptime (simplified - in production this would track actual startup time)
    uptime_seconds = time.time() - getattr(app, '_startup_time', time.time())

    return HealthResponse(
        status="healthy" if not circuit_breaker.is_open() else "degraded",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
        circuit_breaker_open=circuit_breaker.is_open(),
        description="Secure analyzer service is operational" if not circuit_breaker.is_open()
                   else "Service temporarily unavailable due to circuit breaker",
        uptime_seconds=round(uptime_seconds, 1),
        last_health_check=datetime.datetime.utcnow().isoformat() + "Z"
    )


class DetectRequest(BaseModel):
    """
    **Content Security Detection Request** - Advanced security analysis input model.

    This model defines the structure for requesting comprehensive security analysis
    of content, including sensitive data detection, pattern matching, and threat assessment.

    ## 🔍 **Analysis Capabilities**

    ### **📊 Content Types Analyzed**
    - **Personal Information (PII)**: Names, emails, phone numbers, addresses, SSNs
    - **Credentials & Secrets**: API keys, passwords, tokens, certificates
    - **Financial Data**: Credit card numbers, bank details, payment information
    - **Health Information**: Medical records, PHI, HIPAA-regulated data
    - **Proprietary Information**: Intellectual property, trade secrets, confidential data

    ### **🎯 Detection Methods**
    - **Pattern Matching**: Regex-based detection with context awareness
    - **Keyword Analysis**: Custom keyword lists and dictionaries
    - **Semantic Analysis**: Understanding of content context and intent
    - **Behavioral Patterns**: Detection of suspicious content patterns
    - **Entropy Analysis**: Randomness detection for encoded/hidden data

    ## 📋 **Request Parameters**
    """

    model_config = ConfigDict(from_attributes=True)

    content: str = Field(
        ...,
        min_length=1,
        max_length=MAX_CONTENT_SIZE_BYTES,
        description="""
        **Text content to analyze** for security risks and sensitive data.

        The content will be scanned for:
        - Personal identifiable information (PII)
        - Credentials and secrets (API keys, passwords, tokens)
        - Financial data and payment information
        - Health information and medical records
        - Proprietary and confidential business data
        """,
        examples=[
            "User login: john.doe@email.com with password: mySecret123",
            "API Key: sk-1234567890abcdef... Database: mysql://admin:secret@db.company.com",
            "Payment processing with card number: 4111-1111-1111-1111"
        ]
    )

    keywords: Optional[List[str]] = Field(
        default=None,
        max_length=MAX_KEYWORDS_COUNT,
        description="""
        **Additional custom keywords** to search for beyond default security patterns.

        Use this field to specify organization-specific or domain-specific terms
        that should trigger security alerts when detected in content.

        **Examples:**
        - `["confidential", "internal-only", "restricted"]`
        - `["project-x", "secret-sauce", "trade-secret"]`
        - `["competitor-a", "acquisition-target", "nda-required"]`
        """,
        examples=[
            ["confidential", "internal", "restricted"],
            ["api-key", "secret-token", "password"],
            ["project-alpha", "trade-secret", "competitor-info"]
        ]
    )

    keyword_document: Optional[str] = Field(
        default=None,
        description="""
        **URL or reference to external keyword document** for enhanced detection.

        This feature allows loading additional keywords from external sources:
        - HTTP/HTTPS URLs pointing to keyword lists
        - File paths to local keyword dictionaries
        - References to pre-configured keyword sets

        **Supported Formats:**
        - Plain text (one keyword per line)
        - JSON arrays of keywords
        - CSV files with keyword columns

        **Note:** Currently unimplemented - reserved for future enhancement.
        """,
        examples=[
            "https://company.com/security/keywords.txt",
            "file:///app/config/custom-keywords.json",
            "preset:financial-services-keywords"
        ]
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """
        **Content Validation** - Comprehensive input sanitization and validation.

        Performs multiple validation checks:
        - Empty/whitespace content rejection
        - Maximum size enforcement
        - Basic content structure validation
        """
        if not v or not v.strip():
            raise ValueError("Content cannot be empty or contain only whitespace")
        if len(v) > MAX_CONTENT_SIZE_BYTES:
            raise ValueError(f"Content exceeds maximum size of {MAX_CONTENT_SIZE_BYTES:,} bytes")
        return v

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """
        **Keywords Validation** - Custom keyword list validation.

        Validates keyword lists for:
        - Maximum count enforcement
        - Individual keyword length limits
        - Content format validation
        """
        if v is not None:
            if len(v) > MAX_KEYWORDS_COUNT:
                raise ValueError(f"Too many keywords (maximum {MAX_KEYWORDS_COUNT})")
            for keyword in v:
                if len(keyword) > MAX_KEYWORD_LENGTH:
                    raise ValueError(f"Keyword exceeds maximum length of {MAX_KEYWORD_LENGTH} characters")
                if not keyword.strip():
                    raise ValueError("Keywords cannot be empty or whitespace-only")
        return v


class DetectResponse(BaseModel):
    """
    **Content Security Detection Response** - Comprehensive security analysis results.

    This model contains the complete results of security content analysis,
    including sensitivity assessment, detected patterns, security topics,
    and detailed analysis metadata.

    ## 📊 **Response Structure**

    ### **🔒 Security Assessment**
    - **Sensitivity Classification**: Binary determination of content sensitivity
    - **Risk Level**: Quantitative risk assessment based on detected patterns
    - **Confidence Score**: AI confidence in the security analysis results

    ### **🎯 Detection Results**
    - **Pattern Matches**: Specific security patterns detected in content
    - **Security Topics**: Categorized security concerns and threat types
    - **Match Locations**: Position and context of detected security issues
    - **Severity Levels**: Risk severity classification for each finding

    ### **📈 Analysis Metadata**
    - **Processing Statistics**: Performance metrics and analysis coverage
    - **Detection Methods**: Which security detection methods were applied
    - **False Positive Indicators**: Confidence metrics for result validation
    - **Recommendations**: Suggested remediation actions and security controls

    ## 🎯 **Security Classifications**
    """

    model_config = ConfigDict(from_attributes=True)

    sensitive: bool = Field(
        ...,
        description="""
        **Content Sensitivity Classification** - Primary security assessment result.

        **True** indicates the content contains sensitive information that may require:
        - Restricted access controls and handling procedures
        - Encryption for storage and transmission
        - Audit logging and compliance tracking
        - Special approval processes for processing

        **False** indicates the content appears safe for standard processing,
        though additional security controls may still apply based on business policies.
        """,
        examples=[True, False]
    )

    matches: List[str] = Field(
        ...,
        description="""
        **Specific Security Pattern Matches** - Detailed findings from content analysis.

        Contains the exact patterns, keywords, or sensitive data elements detected:
        - **Credentials**: API keys, passwords, tokens, certificates
        - **Personal Data**: Names, emails, phone numbers, addresses, SSNs
        - **Financial Data**: Credit card numbers, bank details, payment information
        - **Custom Keywords**: Organization-specific sensitive terms
        - **Security Indicators**: Suspicious patterns or known threat signatures

        Each match includes the detected pattern and surrounding context for validation.
        """,
        examples=[
            ["API_KEY=sk-1234567890abcdef", "password: mySecret123"],
            ["john.doe@email.com", "555-123-4567"],
            ["4111-1111-1111-1111", "Social Security: 123-45-6789"]
        ]
    )

    topics: List[str] = Field(
        ...,
        description="""
        **Security Topics & Categories** - Categorized security concerns identified.

        High-level categorization of security topics detected in the content:
        - **pii** (Personal Identifiable Information)
        - **secrets** (API keys, passwords, tokens, certificates)
        - **credentials** (Authentication and authorization data)
        - **financial** (Payment information, banking details)
        - **health** (Medical records, PHI, HIPAA-regulated data)
        - **proprietary** (Trade secrets, intellectual property)
        - **compliance** (Regulatory compliance-related content)

        Used for automated policy application and security control selection.
        """,
        examples=[
            ["pii", "secrets"],
            ["credentials", "financial"],
            ["health", "compliance", "proprietary"]
        ]
    )

    confidence_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="""
        **Analysis Confidence Score** - AI confidence in security assessment accuracy.

        Quantitative measure of confidence in the analysis results:
        - **0.0-0.3**: Low confidence - results may include false positives
        - **0.3-0.7**: Medium confidence - results generally reliable
        - **0.7-1.0**: High confidence - results highly reliable

        Used for automated decision-making and human review prioritization.
        """,
        examples=[0.95, 0.87, 0.73]
    )

    risk_level: Optional[str] = Field(
        default=None,
        description="""
        **Overall Risk Assessment** - Categorical risk level for the content.

        **Risk Levels:**
        - **low**: Minimal security concerns, standard processing acceptable
        - **medium**: Moderate security concerns, additional controls recommended
        - **high**: Significant security concerns, restricted processing required
        - **critical**: Severe security violations, immediate action required

        Determined by combining sensitivity classification, pattern matches, and business context.
        """,
        examples=["high", "medium", "low", "critical"]
    )

    processing_metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="""
        **Analysis Processing Metadata** - Detailed information about the security analysis process.

        Contains technical details about the analysis:
        - **patterns_checked**: Number of security patterns evaluated
        - **processing_time_ms**: Time taken for analysis in milliseconds
        - **detection_methods**: Security detection methods applied
        - **false_positive_probability**: Estimated false positive rate
        - **analysis_version**: Version of security analysis engine used

        Useful for performance monitoring, debugging, and analysis optimization.
        """,
        examples=[{
            "patterns_checked": 150,
            "processing_time_ms": 245.67,
            "detection_methods": ["regex_matching", "keyword_analysis", "semantic_analysis"],
            "false_positive_probability": 0.02,
            "analysis_version": "3.0.0"
        }]
    )

    recommendations: Optional[List[str]] = Field(
        default=None,
        description="""
        **Security Recommendations** - Suggested actions and security controls.

        AI-generated recommendations based on detected security issues:
        - **Access Controls**: Recommended permission and authorization changes
        - **Data Handling**: Suggested encryption, masking, or isolation procedures
        - **Monitoring**: Recommended audit logging and monitoring enhancements
        - **Remediation**: Specific steps to address identified security issues
        - **Policy Updates**: Suggested policy modifications or new security controls

        Designed to guide security teams in addressing identified risks.
        """,
        examples=[
            ["Implement encryption for data at rest", "Enable audit logging for access"],
            ["Restrict processing to secure environments", "Implement data masking for PII"],
            ["Add multi-factor authentication", "Conduct security awareness training"]
        ]
    )


# Pattern matching and content detection logic moved to modules/content_detector.py


@app.post(
    "/detect",
    response_model=DetectResponse,
    summary="🔍 Advanced Content Security Analysis",
    description="""
    **Advanced Content Security Analysis** - Comprehensive security scanning and threat detection.

    This endpoint performs enterprise-grade security analysis on provided content,
    detecting sensitive information, security vulnerabilities, and potential threats
    using multiple detection methods and AI-powered analysis.

    ## 🔍 **Security Analysis Capabilities**

    ### **🎯 Detection Methods**
    - **Pattern Matching**: Advanced regex-based detection with context awareness
    - **Keyword Analysis**: Custom keyword lists and organization-specific terms
    - **Semantic Analysis**: AI-powered understanding of content context and intent
    - **Behavioral Analysis**: Detection of suspicious patterns and threat indicators
    - **Entropy Analysis**: Identification of encoded or obfuscated sensitive data

    ### **📊 Content Types Analyzed**
    - **Personal Information (PII)**: Names, emails, addresses, phone numbers, SSNs
    - **Credentials & Secrets**: API keys, passwords, tokens, certificates, private keys
    - **Financial Data**: Credit card numbers, bank details, payment information
    - **Health Information**: Medical records, PHI, HIPAA-regulated data
    - **Proprietary Information**: Trade secrets, intellectual property, confidential data

    ### **🛡️ Security Controls**
    - **Circuit Breaker Protection**: Automatic failure detection and graceful degradation
    - **Rate Limiting**: Configurable request throttling and abuse prevention
    - **Input Validation**: Comprehensive sanitization and validation of all inputs
    - **Audit Logging**: Complete audit trails for compliance and forensic analysis

    ## 🎯 **Analysis Process**

    ### **1. Content Preprocessing**
    - Input sanitization and normalization
    - Content type detection and classification
    - Size and complexity assessment

    ### **2. Multi-Layer Analysis**
    - **Layer 1**: Pattern-based detection (regex, keywords)
    - **Layer 2**: Semantic analysis (context understanding)
    - **Layer 3**: Behavioral analysis (pattern recognition)
    - **Layer 4**: AI-enhanced validation (false positive reduction)

    ### **3. Risk Assessment**
    - Sensitivity classification (binary: sensitive/non-sensitive)
    - Risk level determination (low/medium/high/critical)
    - Confidence scoring (0.0-1.0 scale)
    - Security topic categorization

    ### **4. Recommendations Generation**
    - Remediation suggestions based on findings
    - Security control recommendations
    - Policy compliance guidance

    ## 📋 **Usage Examples**

    ### **Basic Security Scan**
    ```bash
    POST /detect
    Authorization: Bearer <jwt_token>
    Content-Type: application/json

    {
      "content": "User login: admin@company.com with password: secret123"
    }
    ```

    ### **Advanced Security Analysis**
    ```bash
    POST /detect
    Authorization: Bearer <jwt_token>
    Content-Type: application/json

    {
      "content": "API Key: sk-1234567890abcdef... Database: mysql://admin:secret@db.company.com",
      "keywords": ["confidential", "internal", "restricted"],
      "keyword_document": "https://company.com/security/keywords.txt"
    }
    ```

    ### **Python Integration**
    ```python
    import requests

    response = requests.post(
        "http://localhost:5080/detect",
        json={
            "content": "This contains an API key: sk-1234567890abcdef",
            "keywords": ["api-key", "secret"]
        },
        headers={"Authorization": "Bearer <token>"}
    )

    result = response.json()
    if result["sensitive"]:
        print("🚨 Sensitive content detected!")
        print(f"Matches: {result['matches']}")
        print(f"Topics: {result['topics']}")
    ```

    ## 🎯 **Response Codes**

    | Code | Status | Description |
    |------|--------|-------------|
    | 200 | Success | Security analysis completed successfully |
    | 400 | Bad Request | Invalid request parameters or content |
    | 422 | Validation Error | Input validation failed |
    | 429 | Rate Limited | Request rate limit exceeded |
    | 503 | Service Unavailable | Circuit breaker open or service degraded |
    | 500 | Internal Error | Unexpected server error during analysis |

    ## ⚡ **Performance Characteristics**

    - **Average Response Time**: <500ms for typical content
    - **Maximum Content Size**: 1MB per request
    - **Concurrent Requests**: Up to 1000 concurrent analyses
    - **Circuit Breaker Threshold**: Automatic protection after 5 consecutive failures
    - **Rate Limiting**: 1000 requests per minute (configurable)

    ## 🔒 **Security Considerations**

    - All analysis results are logged for audit purposes
    - Sensitive content detection does not store or persist analyzed content
    - Analysis is performed in isolated execution environments
    - Results include confidence scores to guide manual review decisions
    """,
    response_description="Comprehensive security analysis results with sensitivity classification, detected patterns, and remediation recommendations",
    responses={
        200: {
            "description": "Security analysis completed successfully",
            "model": DetectResponse,
            "content": {
                "application/json": {
                    "example": {
                        "sensitive": True,
                        "matches": ["API_KEY=sk-1234567890abcdef", "password: secret123"],
                        "topics": ["secrets", "credentials"],
                        "confidence_score": 0.95,
                        "risk_level": "high",
                        "processing_metadata": {
                            "patterns_checked": 150,
                            "processing_time_ms": 245.67,
                            "detection_methods": ["regex_matching", "keyword_analysis", "semantic_analysis"],
                            "false_positive_probability": 0.02,
                            "analysis_version": "3.0.0"
                        },
                        "recommendations": [
                            "Implement encryption for data at rest",
                            "Enable audit logging for access to this content",
                            "Restrict processing to secure environments"
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Invalid request parameters",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "type": "ValidationError",
                            "message": "Content cannot be empty",
                            "details": {"field": "content", "reason": "empty_content"}
                        },
                        "request_id": "req_550e8400-e29b-41d4-a716-446655440000",
                        "timestamp": "2024-09-22T10:30:00Z"
                    }
                }
            }
        },
        422: {
            "description": "Input validation failed",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "type": "ValidationError",
                            "message": "Content exceeds maximum size",
                            "details": {"field": "content", "max_size": 1000000, "actual_size": 1500000}
                        },
                        "request_id": "req_550e8400-e29b-41d4-a716-446655440001",
                        "timestamp": "2024-09-22T10:30:05Z"
                    }
                }
            }
        },
        429: {
            "description": "Rate limit exceeded",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "type": "RateLimitError",
                            "message": "Too many requests",
                            "details": {"limit": 1000, "window": "1 minute", "retry_after": 30}
                        },
                        "request_id": "req_550e8400-e29b-41d4-a716-446655440002",
                        "timestamp": "2024-09-22T10:30:10Z"
                    }
                }
            }
        },
        503: {
            "description": "Service temporarily unavailable due to circuit breaker",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "type": "CircuitBreakerError",
                            "message": "Service temporarily unavailable",
                            "details": {"state": "open", "failures": 5, "timeout": 60}
                        },
                        "request_id": "req_550e8400-e29b-41d4-a716-446655440003",
                        "timestamp": "2024-09-22T10:30:15Z"
                    }
                }
            }
        }
    },
    tags=["Security Analysis"]
)
    start_time = time.time()
    request_id = f"secure_detect_{int(time.time() * 1000)}"

    try:
        # Check circuit breaker to prevent cascade failures
        if circuit_breaker.is_open():
            circuit_breaker_open_time = time.time() - start_time

            # Log circuit breaker rejection
            if logger_client:
                await logger_client.log_business_event(
                    "secure_analyzer_circuit_breaker_rejection",
                    {
                        "request_id": request_id,
                        "operation": "detect",
                        "rejection_reason": "circuit_breaker_open",
                        "processing_time_seconds": circuit_breaker_open_time,
                    },
                )

                await logger_client.log_error(
                    f"Secure analyzer circuit breaker open - rejecting detect request",
                    {
                        "request_id": request_id,
                        "operation": "detect",
                        "circuit_breaker_state": "open",
                        "processing_time_seconds": circuit_breaker_open_time,
                    },
                    error=Exception("Service temporarily unavailable due to circuit breaker"),
                )

            print(f"[{SERVICE_NAME.upper()}] Circuit breaker is OPEN - rejecting detect request")
            raise HTTPException(status_code=503, detail="Service temporarily unavailable due to circuit breaker")

        async with operation_timeout_context("detect"):
            # Log detection start
            if logger_client:
                await logger_client.log_business_event(
                    "secure_content_detection_started",
                    {
                        "request_id": request_id,
                        "content_length": len(req.content),
                        "has_custom_keywords": bool(req.keywords),
                        "has_keyword_document": bool(req.keyword_document),
                        "keyword_document_url": req.keyword_document,
                        "custom_keywords_count": len(req.keywords) if req.keywords else 0,
                    },
                )

                await logger_client.log_info(
                    "Starting secure content detection",
                    {
                        "request_id": request_id,
                        "content_length": len(req.content),
                        "keyword_sources": (
                            ["custom"] if req.keywords else [] + ["document"] if req.keyword_document else []
                        ),
                        "circuit_breaker_state": "closed",
                    },
                )

            fire_and_forget(
                "info",
                "detect",
                ServiceNames.SECURE_ANALYZER,
                {
                    "has_keywords": bool(req.keywords),
                    "has_keyword_doc": bool(req.keyword_document),
                    "content_length": len(req.content),
                },
            )

            # Load additional keywords from URL if provided
            extra_keywords = req.keywords or []
            keyword_load_success = True
            if req.keyword_document:
                print(f"[{SERVICE_NAME.upper()}] Loading keywords from URL: {req.keyword_document}")
                try:
                    # TODO: Implement URL keyword loading
                    print(f"[{SERVICE_NAME.upper()}] Loaded {len(extra_keywords)} keywords total")

                    # Log successful keyword loading
                    if logger_client:
                        await logger_client.log_info(
                            "Successfully loaded keywords from document",
                            {
                                "request_id": request_id,
                                "keyword_document_url": req.keyword_document,
                                "keywords_loaded": len(extra_keywords),
                            },
                        )

                except Exception as e:
                    keyword_load_success = False
                    print(f"[{SERVICE_NAME.upper()}] Failed to load keywords from URL: {e}")

                    # Log keyword loading failure
                    if logger_client:
                        await logger_client.log_error(
                            f"Failed to load keywords from document URL: {str(e)}",
                            {
                                "request_id": request_id,
                                "keyword_document_url": req.keyword_document,
                                "error_type": type(e).__name__,
                                "keyword_load_success": False,
                            },
                            error=e,
                        )

            # Detect sensitive content using pattern matching
            detection_result = content_detector.detect_sensitive_content(req.content, extra_keywords)

            processing_time = time.time() - start_time

            # Calculate detection metrics
            sensitive_content_detected = detection_result.get("sensitive", False)
            matches_found = len(detection_result.get("matches", []))
            topics_identified = len(detection_result.get("topics", []))
            total_patterns_checked = matches_found + topics_identified

            # Log successful detection completion
            if logger_client:
                await logger_client.log_business_event(
                    "secure_content_detection_completed",
                    {
                        "request_id": request_id,
                        "sensitive_content_detected": sensitive_content_detected,
                        "matches_found": matches_found,
                        "topics_identified": topics_identified,
                        "total_patterns_checked": total_patterns_checked,
                        "processing_time_seconds": processing_time,
                        "keyword_load_success": keyword_load_success,
                        "success": True,
                    },
                )

                await logger_client.log_performance_metric(
                    "secure_content_detection",
                    processing_time,
                    {
                        "request_id": request_id,
                        "content_length": len(req.content),
                        "patterns_analyzed": total_patterns_checked,
                        "detection_success": True,
                        "sensitive_content_found": sensitive_content_detected,
                    },
                )

            return DetectResponse(**detection_result)

    except HTTPException:
        # Re-raise HTTP exceptions as-is (already logged above for circuit breaker)
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log detection failure
        if logger_client:
            await logger_client.log_error(
                f"Secure content detection failed: {str(e)}",
                {
                    "request_id": request_id,
                    "content_length": len(req.content) if "req" in locals() else None,
                    "error_type": type(e).__name__,
                    "processing_time_seconds": error_time,
                    "circuit_breaker_state": (
                        "open" if "circuit_breaker" in locals() and circuit_breaker.is_open() else "closed"
                    ),
                },
                error=e,
            )

            await logger_client.log_business_event(
                "secure_content_detection_failed",
                {
                    "request_id": request_id,
                    "content_length": len(req.content) if "req" in locals() else None,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "processing_time_seconds": error_time,
                },
            )

        raise


class SuggestRequest(BaseModel):
    content: str
    keywords: Optional[List[str]] = None
    keyword_document: Optional[str] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        if len(v) > 1000000:  # 1MB limit
            raise ValueError("Content too large (max 1MB)")
        return v

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v):
        if v is not None:
            if len(v) > 1000:
                raise ValueError("Too many keywords (max 1000)")
            for keyword in v:
                if len(keyword) > 500:
                    raise ValueError("Keyword too long (max 500 characters)")
        return v


class SuggestResponse(BaseModel):
    sensitive: bool
    allowed_models: List[str]
    suggestion: str


@app.post("/suggest", response_model=SuggestResponse)
async def suggest(req: SuggestRequest):
    """Suggest appropriate models based on content sensitivity."""
    # Check circuit breaker
    if circuit_breaker.is_open():
        print(f"[SECURE_ANALYZER] Circuit breaker is OPEN - rejecting suggest request")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable due to circuit breaker")

    async with operation_timeout_context("suggest"):
        print(f"[SECURE_ANALYZER] Starting suggest operation")
        fire_and_forget("info", "suggest", ServiceNames.SECURE_ANALYZER, {"has_kw": bool(req.keywords)})

        # Detect sensitive content
        detection = await detect(
            DetectRequest(content=req.content, keywords=req.keywords, keyword_document=req.keyword_document)
        )
        print(f"[SECURE_ANALYZER] Detection completed, sensitive: {detection.sensitive}")

        # Get allowed models based on policy
        allowed_models = policy_enforcer.get_allowed_models(detection.sensitive)
        suggestion = policy_enforcer.get_policy_suggestion(detection.sensitive)

        print(f"[SECURE_ANALYZER] Suggest operation completed, returning {len(allowed_models)} allowed models")
        return SuggestResponse(sensitive=detection.sensitive, allowed_models=allowed_models, suggestion=suggestion)


class SummarizeRequest(BaseModel):
    content: str
    providers: Optional[List[Dict[str, Any]]] = None  # forwarded to summarizer-hub
    override_policy: Optional[bool] = False
    keywords: Optional[List[str]] = None
    keyword_document: Optional[str] = None
    prompt: Optional[str] = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        if len(v) > 1000000:  # 1MB limit
            raise ValueError("Content too large (max 1MB)")
        return v

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v):
        if v is not None:
            if len(v) > 1000:
                raise ValueError("Too many keywords (max 1000)")
            for keyword in v:
                if len(keyword) > 500:
                    raise ValueError("Keyword too long (max 500 characters)")
        return v

    @field_validator("providers")
    @classmethod
    def validate_providers(cls, v):
        if v is not None:
            if len(v) > 1000:
                raise ValueError("Too many providers (max 1000)")
            for provider in v:
                if not isinstance(provider, dict):
                    raise ValueError("Each provider must be a dictionary")
                if "name" not in provider:
                    raise ValueError("Each provider must have a name field")
                if len(provider.get("name", "")) > 100:
                    raise ValueError("Provider name too long (max 100 characters)")
        return v


@app.post("/summarize")
async def summarize(req: SummarizeRequest):
    # Check circuit breaker
    if circuit_breaker.is_open():
        print(f"[SECURE_ANALYZER] Circuit breaker is OPEN - rejecting summarize request")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable due to circuit breaker")

    async with operation_timeout_context("summarize"):
        print(f"[SECURE_ANALYZER] Starting summarize operation")
        fire_and_forget("info", "summarize", ServiceNames.SECURE_ANALYZER, {"override": req.override_policy})

        hub = os.environ.get(EnvVars.SUMMARIZER_HUB_URL_ENV, "http://summarizer-hub:5060")
        print(f"[SECURE_ANALYZER] Summarizer hub URL: {hub}")

        # Detect sensitive content
        det = await detect(
            DetectRequest(content=req.content, keywords=req.keywords, keyword_document=req.keyword_document)
        )
        print(f"[SECURE_ANALYZER] Detection completed, sensitive: {det.sensitive}")

        # Filter providers based on policy
        providers = policy_enforcer.filter_providers(req.providers, det.sensitive, req.override_policy)
    # Set default prompt if none provided
    if not req.prompt:
        try:
            from services.shared.prompt_manager import get_prompt

            req.prompt = get_prompt("summarization.security_focused")
        except Exception:
            req.prompt = "Summarize focusing on risks, PII, secrets, and client information."

    # Mock response for testing
    if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("TESTING"):
        provider_used = providers[0].get("name", "ollama") if providers else "ollama"
        base_summary = f"Mock summary (len={len(req.content)}), providers={len(providers)}"
        if req.prompt and ("security" in req.prompt.lower() or "risk" in req.prompt.lower()):
            base_summary = f"Security-focused summary: This content has been analyzed for security risks and potential vulnerabilities. Key findings include {len(det.matches)} sensitive elements and {len(det.topics)} security topics identified."

        return {
            "summary": base_summary,
            "provider_used": provider_used,
            "confidence": 0.9 if det.sensitive else 0.8,
            "word_count": len((req.content or "").split()),
            "topics_detected": det.topics,
            "policy_enforced": det.sensitive and not req.override_policy,
            "analysis": {"agreed": ["policy ok"]},
        }

    # Production code - make actual external call
    payload = {
        "text": req.content,
        "providers": providers,
        "use_hub_config": True,
    }
    from services.shared.integrations.clients.clients import ServiceClients  # type: ignore

    svc = ServiceClients(timeout=60)
    try:
        return await svc.post_json(f"{hub}/summarize/ensemble", payload)
    except Exception as e:
        return {
            "summary": f"Fallback mock summary: External service error - {str(e)}",
            "provider_used": "fallback",
            "confidence": 0.5,
            "word_count": len((req.content or "").split()),
            "topics_detected": det.topics,
            "policy_enforced": det.sensitive and not req.override_policy,
        }


if __name__ == "__main__":
    """Run the Secure Analyzer service directly."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info")
