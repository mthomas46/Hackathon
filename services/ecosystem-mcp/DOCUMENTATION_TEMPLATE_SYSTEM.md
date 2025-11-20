**Date:** November 19, 2025  
**Status:** 🎨 **TEMPLATE SYSTEM DESIGN** - Production-Ready Documentation Structure  
**Purpose:** User-customizable, consistent documentation templates leveraging existing infrastructure  

---

# Documentation Template System: Design & Implementation

## 🔍 Infrastructure Audit: Current State

### **❌ FLAWS IDENTIFIED**

#### **Flaw 1: Hardcoded Templates**
```python
# Current approach in api_generator.py, component_generator.py, etc.
content = f"""# API Reference Overview

## Introduction

This document provides comprehensive API reference...
"""
```

**Problems:**
- ❌ Templates hardcoded in Python strings
- ❌ Not user-customizable
- ❌ Scattered across multiple generator classes
- ❌ No separation of structure vs content
- ❌ Difficult to maintain consistency
- ❌ No template versioning

---

#### **Flaw 2: Inconsistent Structure**
```python
# architecture_generator.py uses one structure:
content = f"""# System Overview
## Architecture
## Components
"""

# component_generator.py uses different structure:
content = f"""# Service: {name}
## Overview
## Purpose
## Metrics
"""
```

**Problems:**
- ❌ Each generator has its own structure
- ❌ No enforced consistency across doc types
- ❌ Hard to ensure all runbooks/API docs follow same pattern
- ❌ Manual effort to maintain uniformity

---

#### **Flaw 3: No Runbook Support**
```python
# Existing generators:
- ArchitectureGenerator
- ComponentGenerator  
- APIReferenceGenerator
- ExamplesGenerator
- SynthesisGenerator
```

**Problems:**
- ❌ No dedicated runbook generator
- ❌ No operational documentation templates
- ❌ Missing: incident response, deployment, troubleshooting
- ❌ Missing: health checks, monitoring, alerts
- ❌ Not production-ready

---

#### **Flaw 4: Limited Template Management**
```yaml
# .rag-config/templates.yaml only has query templates:
templates:
  architecture:
    description: "Architecture questions"
    patterns: [...]
    boost_paths: [...]
```

**Problems:**
- ❌ Only for RAG queries, not doc generation
- ❌ No documentation structure templates
- ❌ No user-supplied template support
- ❌ No template validation

---

## ✅ SOLUTIONS: Enhanced Template System

### **Solution 1: Template Database Schema**

```sql
-- 🆕 NEW TABLE: Store user-supplied templates
CREATE TABLE documentation_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Template identification
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,  -- api_reference, runbook, architecture, component
    version INTEGER NOT NULL DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Template structure (JSONB for flexibility)
    structure JSONB NOT NULL,
    -- {
    --   "sections": [
    --     {
    --       "name": "Overview",
    --       "order": 1,
    --       "required": true,
    --       "subsections": ["Purpose", "Scope", "Audience"],
    --       "prompt_template": "Provide overview of {service_name}...",
    --       "validation": {"min_words": 100, "max_words": 500}
    --     }
    --   ],
    --   "formatting": {
    --     "header_style": "atx",  -- # vs ###
    --     "code_fence": "```",
    --     "list_style": "ordered"
    --   }
    -- }
    
    -- Metadata
    description TEXT,
    target_framework VARCHAR(100),  -- scala_play, java_spring, generic
    target_audience VARCHAR(50),  -- developers, operators, business
    
    -- Rendering options
    render_options JSONB,
    -- {
    --   "include_toc": true,
    --   "include_citations": true,
    --   "citation_style": "endnotes",
    --   "include_diagrams": true,
    --   "include_code_examples": true
    -- }
    
    -- Usage tracking
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    
    -- Ownership
    created_by VARCHAR(255),
    is_system_template BOOLEAN DEFAULT FALSE,  -- System vs user-supplied
    is_public BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_category CHECK (category IN (
        'api_reference', 'runbook', 'architecture', 'component',
        'user_guide', 'deployment', 'troubleshooting', 'security'
    ))
);

CREATE INDEX idx_doc_templates_category ON documentation_templates(category);
CREATE INDEX idx_doc_templates_active ON documentation_templates(is_active);
CREATE INDEX idx_doc_templates_framework ON documentation_templates(target_framework);


-- 🆕 NEW TABLE: Track template usage and quality
CREATE TABLE template_execution_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Links
    template_id UUID NOT NULL REFERENCES documentation_templates(id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES documentation_runs(id) ON DELETE CASCADE,
    artifact_id UUID REFERENCES documentation_artifacts(id) ON DELETE CASCADE,
    
    -- Execution details
    section_name VARCHAR(255),
    executed_at TIMESTAMP DEFAULT NOW(),
    
    -- Quality metrics
    completeness_score FLOAT,  -- From quality_checks
    adherence_score FLOAT,  -- How well it followed template structure
    user_rating INTEGER,  -- 1-5 stars
    
    -- Issues encountered
    validation_errors JSONB,  -- Sections missing, word count violations
    rendering_errors JSONB,
    
    CONSTRAINT valid_completeness CHECK (completeness_score IS NULL OR completeness_score BETWEEN 0 AND 1),
    CONSTRAINT valid_adherence CHECK (adherence_score IS NULL OR adherence_score BETWEEN 0 AND 1),
    CONSTRAINT valid_rating CHECK (user_rating IS NULL OR user_rating BETWEEN 1 AND 5)
);

CREATE INDEX idx_template_exec_template ON template_execution_history(template_id);
CREATE INDEX idx_template_exec_run ON template_execution_history(run_id);
CREATE INDEX idx_template_exec_quality ON template_execution_history(completeness_score, adherence_score);
```

**✅ Benefits:**
- Database-backed (persistent, versioned, queryable)
- User-supplied templates supported
- Usage tracking for continuous improvement
- Quality metrics per template

---

### **Solution 2: Built-in Production Templates**

#### **2.1. API Reference Template (OpenAPI-style)**

```yaml
# Stored in documentation_templates table
name: "api_reference_openapi_style"
category: "api_reference"
version: 1
is_system_template: true
target_audience: "developers"

structure:
  sections:
    - name: "Overview"
      order: 1
      required: true
      subsections:
        - "Purpose"
        - "Base URL"
        - "API Version"
        - "Authentication"
      prompt_template: |
        Provide an overview of the {service_name} API.
        Include:
        - Primary purpose and use cases
        - Base URL: {base_url}
        - API version: {api_version}
        - Authentication method: {auth_method}
      validation:
        min_words: 100
        max_words: 300
    
    - name: "Authentication"
      order: 2
      required: true
      subsections:
        - "Methods Supported"
        - "Obtaining Credentials"
        - "Token Format"
        - "Token Expiration"
      prompt_template: |
        Describe authentication for {service_name}.
        Focus on:
        - Authentication schemes: {auth_schemes}
        - How to obtain credentials
        - Token format and usage
        - Security best practices
      validation:
        min_words: 150
        must_include_code_example: true
    
    - name: "Endpoints"
      order: 3
      required: true
      format: "grouped_by_resource"  # vs grouped_by_method
      endpoint_template:
        structure: |
          ### {method} {path}
          
          **Description:** {description}
          
          **Parameters:**
          {parameters_table}
          
          **Request Body:** (if applicable)
          ```json
          {request_example}
          ```
          
          **Response:** {status_code}
          ```json
          {response_example}
          ```
          
          **Errors:**
          {error_table}
          
          **Example:**
          ```bash
          {curl_example}
          ```
      prompt_template: |
        Document all endpoints for {resource_name}.
        For each endpoint in {endpoints}:
        - Extract HTTP method, path, description
        - List parameters (path, query, header)
        - Show request/response schemas
        - Include error codes
        - Provide curl examples
      validation:
        min_endpoints: 1
        must_include_examples: true
        must_include_error_codes: true
    
    - name: "Data Models"
      order: 4
      required: false
      subsections:
        - "Request Models"
        - "Response Models"
        - "Common Types"
      prompt_template: |
        Document data models used in {service_name} API.
        For each model in {models}:
        - Model name and purpose
        - Fields with types
        - Validation rules
        - Example JSON
      validation:
        must_include_json_schema: true
    
    - name: "Error Codes"
      order: 5
      required: true
      format: "table"
      prompt_template: |
        List all error codes for {service_name}.
        Format as table:
        | Code | Message | Description | Resolution |
      validation:
        min_errors: 5
    
    - name: "Rate Limiting"
      order: 6
      required: true
      prompt_template: |
        Describe rate limiting for {service_name}.
        Include:
        - Rate limits per endpoint or global
        - Headers returned (X-RateLimit-*)
        - How to handle 429 responses
      validation:
        min_words: 100
    
    - name: "Changelog"
      order: 7
      required: false
      prompt_template: |
        Document API version history and changes.
        Include:
        - Version numbers
        - Release dates
        - Breaking changes
        - Deprecated endpoints
        - New features
      validation:
        min_versions: 1

formatting:
  header_style: "atx"  # Use # for headers
  code_fence: "```"
  list_style: "unordered"
  table_alignment: "left"

render_options:
  include_toc: true
  toc_depth: 3
  include_citations: true
  citation_style: "endnotes"
  include_diagrams: false  # APIs don't typically need diagrams
  include_code_examples: true
  code_language_default: "bash"
```

---

#### **2.2. Runbook Template (SRE-style)**

```yaml
name: "runbook_sre_style"
category: "runbook"
version: 1
is_system_template: true
target_audience: "operators"

structure:
  sections:
    - name: "Service Overview"
      order: 1
      required: true
      subsections:
        - "Service Name"
        - "Team/Owner"
        - "SLA/SLO"
        - "Dependencies"
      prompt_template: |
        Provide operational overview for {service_name}.
        Include:
        - Service purpose (1-2 sentences)
        - Owning team: {team}
        - SLA: {sla}
        - Critical dependencies: {dependencies}
        - Deployment environment: {environment}
      validation:
        min_words: 100
        max_words: 300
        must_include_owner: true
    
    - name: "Architecture Summary"
      order: 2
      required: true
      subsections:
        - "Component Diagram"
        - "Data Flow"
        - "Infrastructure"
      prompt_template: |
        Describe architecture for operators.
        Focus on:
        - Key components: {components}
        - Data flow (simplified)
        - Infrastructure: {infrastructure}
        - Scalability model
      validation:
        min_words: 200
        must_include_diagram: true
    
    - name: "Deployment"
      order: 3
      required: true
      subsections:
        - "Deployment Process"
        - "Rollback Procedure"
        - "Deployment Checklist"
        - "Zero-Downtime Strategy"
      prompt_template: |
        Document deployment process for {service_name}.
        Include:
        - Deployment command: {deploy_command}
        - Pre-deployment checks
        - Post-deployment validation
        - Rollback command: {rollback_command}
        - Estimated downtime (if any)
      validation:
        min_words: 300
        must_include_commands: true
        must_include_rollback: true
    
    - name: "Monitoring & Alerts"
      order: 4
      required: true
      subsections:
        - "Key Metrics"
        - "Alert Definitions"
        - "Dashboard Links"
        - "Log Locations"
      prompt_template: |
        Document monitoring for {service_name}.
        Key metrics to monitor:
        {metrics}
        
        Alert definitions:
        {alerts}
        
        Dashboard: {dashboard_url}
        Logs: {log_location}
      validation:
        min_metrics: 3
        must_include_dashboard_link: true
    
    - name: "Health Checks"
      order: 5
      required: true
      subsections:
        - "Health Endpoint"
        - "Readiness Check"
        - "Liveness Check"
        - "Dependency Checks"
      prompt_template: |
        Document health checks for {service_name}.
        
        Health endpoint: {health_endpoint}
        Expected response: {health_response}
        
        How to verify:
        ```bash
        {health_check_command}
        ```
        
        Common failure modes:
        {failure_modes}
      validation:
        min_words: 200
        must_include_curl_example: true
    
    - name: "Troubleshooting"
      order: 6
      required: true
      format: "problem_solution_pairs"
      subsections:
        - "Common Issues"
        - "Diagnostic Commands"
        - "Log Analysis"
        - "Performance Issues"
      prompt_template: |
        Document common issues and solutions for {service_name}.
        
        For each known issue:
        - Symptom
        - Root cause
        - Resolution steps
        - Prevention
        
        Include diagnostic commands:
        {diagnostic_commands}
      validation:
        min_issues: 5
        must_include_commands: true
    
    - name: "Incident Response"
      order: 7
      required: true
      subsections:
        - "Severity Levels"
        - "Escalation Path"
        - "Communication Plan"
        - "Post-Incident Review"
      prompt_template: |
        Document incident response for {service_name}.
        
        Severity levels:
        {severity_definitions}
        
        Escalation path:
        1. On-call engineer: {oncall_contact}
        2. Team lead: {lead_contact}
        3. Director: {director_contact}
        
        Communication channels:
        {communication_channels}
      validation:
        must_include_contacts: true
        must_include_severity_levels: true
    
    - name: "Scaling & Capacity"
      order: 8
      required: true
      subsections:
        - "Current Capacity"
        - "Scaling Triggers"
        - "Scaling Procedure"
        - "Resource Limits"
      prompt_template: |
        Document scaling for {service_name}.
        
        Current capacity:
        - Instances: {current_instances}
        - CPU/Memory per instance: {resources}
        - Max throughput: {max_throughput}
        
        When to scale:
        {scaling_triggers}
        
        How to scale:
        {scaling_commands}
      validation:
        min_words: 200
        must_include_current_capacity: true
    
    - name: "Disaster Recovery"
      order: 9
      required: true
      subsections:
        - "Backup Strategy"
        - "Recovery Time Objective (RTO)"
        - "Recovery Point Objective (RPO)"
        - "Recovery Procedure"
      prompt_template: |
        Document DR for {service_name}.
        
        Backup:
        - Frequency: {backup_frequency}
        - Location: {backup_location}
        - Retention: {retention_period}
        
        RTO: {rto}
        RPO: {rpo}
        
        Recovery steps:
        {recovery_steps}
      validation:
        must_include_rto: true
        must_include_rpo: true
    
    - name: "Maintenance Windows"
      order: 10
      required: false
      prompt_template: |
        Document maintenance procedures for {service_name}.
        
        Scheduled maintenance:
        - Window: {maintenance_window}
        - Notification process
        - Maintenance checklist
        - Validation after maintenance
      validation:
        min_words: 150
    
    - name: "Runbook Changelog"
      order: 11
      required: true
      prompt_template: |
        Track changes to this runbook.
        
        | Date | Change | Author |
        |------|--------|--------|
        | {date} | Initial version | {author} |
      validation:
        min_entries: 1

formatting:
  header_style: "atx"
  code_fence: "```"
  list_style: "ordered"  # Runbooks benefit from numbered steps
  emphasis_style: "**"

render_options:
  include_toc: true
  toc_depth: 2
  include_citations: false  # Runbooks don't need citations
  include_diagrams: true
  highlight_critical_sections: true  # Bold/color for critical procedures
  include_timestamps: true
```

---

#### **2.3. Architecture Document Template (C4 Model-inspired)**

```yaml
name: "architecture_c4_style"
category: "architecture"
version: 1
is_system_template: true
target_audience: "developers"

structure:
  sections:
    - name: "System Context"
      order: 1
      required: true
      diagram_type: "c4_context"
      prompt_template: |
        Describe the system context for {service_name}.
        
        System boundary:
        - What the system does
        - External actors/users: {actors}
        - External systems: {external_systems}
        - Key interactions
      validation:
        min_words: 200
        must_include_diagram: true
    
    - name: "Container View"
      order: 2
      required: true
      diagram_type: "c4_container"
      prompt_template: |
        Describe containers (deployable units) in {service_name}.
        
        For each container:
        - Name and technology
        - Responsibilities
        - Data stores
        - Communication protocols
        
        Containers: {containers}
      validation:
        min_containers: 1
        must_include_diagram: true
    
    - name: "Component View"
      order: 3
      required: true
      diagram_type: "c4_component"
      prompt_template: |
        Describe components within key containers.
        
        For {component_name}:
        - Internal components
        - Responsibilities
        - Interactions
        - Patterns used
      validation:
        must_include_diagram: true
    
    - name: "Code Organization"
      order: 4
      required: false
      prompt_template: |
        Describe code organization for {service_name}.
        
        Directory structure:
        {directory_structure}
        
        Key modules:
        {modules}
        
        Coding conventions:
        {conventions}
      validation:
        min_words: 200
    
    - name: "Data Architecture"
      order: 5
      required: true
      prompt_template: |
        Describe data architecture.
        
        Databases: {databases}
        - Schemas
        - Key tables/collections
        - Relationships
        - Indexing strategy
        
        Data flow:
        {data_flow}
      validation:
        min_words: 300
    
    - name: "Security Architecture"
      order: 6
      required: true
      prompt_template: |
        Describe security architecture.
        
        Authentication: {auth_method}
        Authorization: {authz_method}
        
        Security controls:
        - Network security
        - Data encryption
        - Secrets management
        - Audit logging
      validation:
        min_words: 200
        must_include_auth: true
    
    - name: "Quality Attributes"
      order: 7
      required: true
      prompt_template: |
        Describe quality attributes and trade-offs.
        
        - Performance: {performance_targets}
        - Scalability: {scalability_approach}
        - Availability: {availability_target}
        - Maintainability: {maintainability_practices}
        - Testability: {testing_strategy}
      validation:
        min_words: 300
    
    - name: "Architecture Decisions"
      order: 8
      required: true
      format: "adr"  # Architecture Decision Records
      prompt_template: |
        Document key architecture decisions.
        
        For each decision:
        - Context
        - Decision
        - Consequences
        - Alternatives considered
      validation:
        min_decisions: 3

formatting:
  header_style: "atx"
  diagram_format: "mermaid"  # vs plantuml
  code_fence: "```"

render_options:
  include_toc: true
  toc_depth: 3
  include_diagrams: true
  diagram_tool: "mermaid"
  include_citations: true
```

---

### **Solution 3: Template Manager Service**

```python
"""
Template Manager Service

Handles loading, validation, rendering, and tracking of documentation templates.
Integrates with existing infrastructure.
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
import yaml
import json
from jinja2 import Template as Jinja2Template, Environment, FileSystemLoader
from sqlalchemy import select

from ...storage.database import get_database
from ...storage.db_models import Base
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
import uuid
from datetime import datetime


class DocumentationTemplateModel(Base):
    """SQLAlchemy model for documentation templates."""
    __tablename__ = "documentation_templates"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    category = Column(String(100), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, default=True)
    
    structure = Column(JSONB, nullable=False)
    description = Column(Text)
    target_framework = Column(String(100))
    target_audience = Column(String(50))
    render_options = Column(JSONB)
    
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime)
    
    created_by = Column(String(255))
    is_system_template = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint(
            "category IN ('api_reference', 'runbook', 'architecture', 'component', 'user_guide', 'deployment', 'troubleshooting', 'security')",
            name="valid_category"
        ),
    )


class TemplateExecutionHistoryModel(Base):
    """SQLAlchemy model for template execution tracking."""
    __tablename__ = "template_execution_history"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(PGUUID(as_uuid=True), ForeignKey("documentation_templates.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(PGUUID(as_uuid=True), ForeignKey("documentation_runs.id", ondelete="CASCADE"), nullable=False)
    artifact_id = Column(PGUUID(as_uuid=True), ForeignKey("documentation_artifacts.id", ondelete="CASCADE"))
    
    section_name = Column(String(255))
    executed_at = Column(DateTime, default=datetime.utcnow)
    
    completeness_score = Column(Float)
    adherence_score = Column(Float)
    user_rating = Column(Integer)
    
    validation_errors = Column(JSONB)
    rendering_errors = Column(JSONB)
    
    __table_args__ = (
        CheckConstraint("completeness_score IS NULL OR completeness_score BETWEEN 0 AND 1", name="valid_completeness"),
        CheckConstraint("adherence_score IS NULL OR adherence_score BETWEEN 0 AND 1", name="valid_adherence"),
        CheckConstraint("user_rating IS NULL OR user_rating BETWEEN 1 AND 5", name="valid_rating"),
    )


class TemplateManager:
    """
    Manages documentation templates.
    
    Responsibilities:
    - Load templates from database or files
    - Validate template structure
    - Render templates with context
    - Track template usage
    - Provide template recommendations
    """
    
    def __init__(self):
        self.jinja_env = Environment(
            loader=FileSystemLoader('.rag-config/doc-templates/'),
            autoescape=False  # We control the input
        )
        self.cache = {}  # Template cache
    
    async def load_template(
        self,
        template_name: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Load template from database.
        
        Args:
            template_name: Template name or ID
            category: Optional category filter
        
        Returns:
            Template structure dict
        """
        # Check cache first
        cache_key = f"{template_name}_{category}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        async with get_database().session() as session:
            query = select(DocumentationTemplateModel).filter(
                DocumentationTemplateModel.name == template_name,
                DocumentationTemplateModel.is_active == True
            )
            
            if category:
                query = query.filter(DocumentationTemplateModel.category == category)
            
            result = await session.execute(query)
            template_model = result.scalar_one_or_none()
            
            if not template_model:
                raise ValueError(f"Template not found: {template_name}")
            
            template_dict = {
                "id": str(template_model.id),
                "name": template_model.name,
                "category": template_model.category,
                "version": template_model.version,
                "structure": template_model.structure,
                "render_options": template_model.render_options or {}
            }
            
            # Cache it
            self.cache[cache_key] = template_dict
            
            return template_dict
    
    async def create_template(
        self,
        name: str,
        category: str,
        structure: Dict[str, Any],
        created_by: str,
        **kwargs
    ) -> UUID:
        """
        Create new user-supplied template.
        
        Args:
            name: Template name
            category: Template category
            structure: Template structure (validated)
            created_by: Username
            **kwargs: Additional fields
        
        Returns:
            Template ID
        """
        # Validate structure
        self._validate_template_structure(structure)
        
        async with get_database().session() as session:
            template = DocumentationTemplateModel(
                name=name,
                category=category,
                structure=structure,
                created_by=created_by,
                **kwargs
            )
            
            session.add(template)
            await session.commit()
            await session.refresh(template)
            
            return template.id
    
    def _validate_template_structure(self, structure: Dict[str, Any]) -> None:
        """
        Validate template structure.
        
        Checks:
        - Required fields present
        - Section order is sequential
        - Prompt templates are valid
        - Validation rules are valid
        """
        if "sections" not in structure:
            raise ValueError("Template must have 'sections' field")
        
        sections = structure["sections"]
        if not isinstance(sections, list) or len(sections) == 0:
            raise ValueError("Template must have at least one section")
        
        seen_orders = set()
        for section in sections:
            # Check required fields
            required_fields = ["name", "order", "required"]
            for field in required_fields:
                if field not in section:
                    raise ValueError(f"Section missing required field: {field}")
            
            # Check order uniqueness
            order = section["order"]
            if order in seen_orders:
                raise ValueError(f"Duplicate section order: {order}")
            seen_orders.add(order)
            
            # Validate prompt template if present
            if "prompt_template" in section:
                # Basic validation - check for balanced braces
                prompt = section["prompt_template"]
                if prompt.count("{") != prompt.count("}"):
                    raise ValueError(f"Unbalanced braces in prompt for section: {section['name']}")
    
    async def render_section(
        self,
        template: Dict[str, Any],
        section_name: str,
        context: Dict[str, Any],
        content: str
    ) -> str:
        """
        Render a section using template structure.
        
        Args:
            template: Template dict
            section_name: Section to render
            context: Context variables
            content: Generated content
        
        Returns:
            Formatted section markdown
        """
        # Find section in template
        section = next(
            (s for s in template["structure"]["sections"] if s["name"] == section_name),
            None
        )
        
        if not section:
            raise ValueError(f"Section not found in template: {section_name}")
        
        # Get formatting options
        formatting = template["structure"].get("formatting", {})
        header_style = formatting.get("header_style", "atx")
        
        # Build section header
        header_level = 2  # Assuming top-level sections are ##
        if header_style == "atx":
            header = f"{'#' * header_level} {section_name}"
        else:
            header = f"{section_name}\n{'=' * len(section_name)}"
        
        # Build subsections
        rendered = f"{header}\n\n"
        
        if "subsections" in section:
            for subsection in section["subsections"]:
                rendered += f"{'#' * (header_level + 1)} {subsection}\n\n"
        
        # Add content
        rendered += content
        
        # Add validation markers if in verbose mode
        if context.get("transparency_mode") == "verbose":
            validation = section.get("validation", {})
            rendered += f"\n\n<!-- Template: {template['name']}, Section: {section_name}, Validation: {validation} -->\n"
        
        return rendered
    
    async def validate_generated_content(
        self,
        template: Dict[str, Any],
        section_name: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Validate generated content against template rules.
        
        Args:
            template: Template dict
            section_name: Section name
            content: Generated content
        
        Returns:
            Validation result with errors/warnings
        """
        section = next(
            (s for s in template["structure"]["sections"] if s["name"] == section_name),
            None
        )
        
        if not section:
            return {"valid": True, "errors": [], "warnings": []}
        
        validation = section.get("validation", {})
        errors = []
        warnings = []
        
        # Check word count
        word_count = len(content.split())
        
        if "min_words" in validation:
            if word_count < validation["min_words"]:
                errors.append(f"Content too short: {word_count} words (min: {validation['min_words']})")
        
        if "max_words" in validation:
            if word_count > validation["max_words"]:
                warnings.append(f"Content too long: {word_count} words (max: {validation['max_words']})")
        
        # Check for code examples
        if validation.get("must_include_code_example", False):
            if "```" not in content:
                errors.append("Section must include code example")
        
        # Check for specific keywords
        if "must_include" in validation:
            for keyword in validation["must_include"]:
                if keyword.lower() not in content.lower():
                    warnings.append(f"Section should mention: {keyword}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "word_count": word_count,
            "adherence_score": 1.0 if len(errors) == 0 else max(0.0, 1.0 - (len(errors) * 0.2))
        }
    
    async def track_template_usage(
        self,
        template_id: UUID,
        run_id: UUID,
        artifact_id: Optional[UUID],
        section_name: str,
        validation_result: Dict[str, Any]
    ) -> None:
        """
        Track template usage for analytics.
        
        Args:
            template_id: Template ID
            run_id: Documentation run ID
            artifact_id: Artifact ID (if created)
            section_name: Section name
            validation_result: Validation result
        """
        async with get_database().session() as session:
            # Update usage count
            template = await session.get(DocumentationTemplateModel, template_id)
            if template:
                template.usage_count += 1
                template.last_used_at = datetime.utcnow()
            
            # Create execution history
            execution = TemplateExecutionHistoryModel(
                template_id=template_id,
                run_id=run_id,
                artifact_id=artifact_id,
                section_name=section_name,
                adherence_score=validation_result.get("adherence_score"),
                validation_errors=validation_result.get("errors", []),
                rendering_errors=[]
            )
            
            session.add(execution)
            await session.commit()
    
    async def get_recommended_template(
        self,
        category: str,
        framework: Optional[str] = None,
        audience: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get recommended template based on criteria.
        
        Args:
            category: Template category
            framework: Target framework (optional)
            audience: Target audience (optional)
        
        Returns:
            Best matching template
        """
        async with get_database().session() as session:
            query = select(DocumentationTemplateModel).filter(
                DocumentationTemplateModel.category == category,
                DocumentationTemplateModel.is_active == True
            )
            
            # Prioritize templates matching framework and audience
            if framework:
                query = query.filter(
                    (DocumentationTemplateModel.target_framework == framework) |
                    (DocumentationTemplateModel.target_framework == None)
                )
            
            if audience:
                query = query.filter(
                    (DocumentationTemplateModel.target_audience == audience) |
                    (DocumentationTemplateModel.target_audience == None)
                )
            
            # Order by usage count (popular templates first)
            query = query.order_by(DocumentationTemplateModel.usage_count.desc())
            
            result = await session.execute(query)
            template_model = result.scalar_one_or_none()
            
            if not template_model:
                raise ValueError(f"No template found for category: {category}")
            
            return await self.load_template(template_model.name, category)
    
    async def list_templates(
        self,
        category: Optional[str] = None,
        framework: Optional[str] = None,
        user_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List available templates.
        
        Args:
            category: Filter by category
            framework: Filter by framework
            user_only: Only user-supplied templates
        
        Returns:
            List of template summaries
        """
        async with get_database().session() as session:
            query = select(DocumentationTemplateModel).filter(
                DocumentationTemplateModel.is_active == True
            )
            
            if category:
                query = query.filter(DocumentationTemplateModel.category == category)
            
            if framework:
                query = query.filter(DocumentationTemplateModel.target_framework == framework)
            
            if user_only:
                query = query.filter(DocumentationTemplateModel.is_system_template == False)
            
            result = await session.execute(query)
            templates = result.scalars().all()
            
            return [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "category": t.category,
                    "version": t.version,
                    "description": t.description,
                    "target_framework": t.target_framework,
                    "target_audience": t.target_audience,
                    "usage_count": t.usage_count,
                    "is_system_template": t.is_system_template
                }
                for t in templates
            ]


# Singleton instance
_template_manager = None

def get_template_manager() -> TemplateManager:
    """Get or create singleton template manager."""
    global _template_manager
    if _template_manager is None:
        _template_manager = TemplateManager()
    return _template_manager
```

---

### **Solution 4: Integration with Existing Generators**

```python
"""
Enhanced Documentation Generator with Template Support
"""

class TemplateAwareDocumentationGenerator:
    """
    Documentation generator that uses templates.
    
    Replaces hardcoded templates with database-backed, user-customizable templates.
    """
    
    def __init__(self):
        self.template_manager = get_template_manager()
        self.model_router = None  # LLM router
    
    async def generate_from_template(
        self,
        template_name: str,
        category: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate documentation using specified template.
        
        Args:
            template_name: Template to use
            category: Template category
            context: Generation context (service_name, frameworks, etc.)
            config: Generation config (adaptive settings, etc.)
        
        Returns:
            List of documentation artifacts
        """
        # Load template
        template = await self.template_manager.load_template(template_name, category)
        
        artifacts = []
        
        # Generate each section
        for section in template["structure"]["sections"]:
            if not section["required"] and not config.get("include_optional_sections", False):
                continue
            
            artifact = await self._generate_section(
                template=template,
                section=section,
                context=context,
                config=config
            )
            
            artifacts.append(artifact)
        
        return artifacts
    
    async def _generate_section(
        self,
        template: Dict[str, Any],
        section: Dict[str, Any],
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate single section from template."""
        
        section_name = section["name"]
        
        # Build prompt from template
        prompt_template = section.get("prompt_template", "")
        
        try:
            # Fill prompt template with context
            from jinja2 import Template
            jinja_template = Template(prompt_template)
            filled_prompt = jinja_template.render(**context)
        except Exception as e:
            raise ValueError(f"Failed to render prompt for section {section_name}: {e}")
        
        # Execute query (use existing RAG infrastructure)
        from ...services.rag.enhanced_rag_service import get_enhanced_rag_service
        rag_service = get_enhanced_rag_service()
        
        response = await rag_service.query(
            question=filled_prompt,
            service_filter=context.get("service_name"),
            n_results=section.get("documents_needed", 20),
            use_enhancements=True
        )
        
        content = response["answer"]
        
        # Render section using template formatting
        rendered_content = await self.template_manager.render_section(
            template=template,
            section_name=section_name,
            context=context,
            content=content
        )
        
        # Validate content against template rules
        validation_result = await self.template_manager.validate_generated_content(
            template=template,
            section_name=section_name,
            content=rendered_content
        )
        
        # Track template usage
        if config.get("run_id"):
            await self.template_manager.track_template_usage(
                template_id=UUID(template["id"]),
                run_id=UUID(config["run_id"]),
                artifact_id=None,  # Will be set after artifact is saved
                section_name=section_name,
                validation_result=validation_result
            )
        
        # Create artifact
        artifact = {
            "type": template["category"],
            "title": section_name,
            "content": rendered_content,
            "format": "markdown",
            "word_count": validation_result["word_count"],
            "template_id": template["id"],
            "template_name": template["name"],
            "validation": validation_result
        }
        
        return artifact
```

---

## 📊 Template File Storage

### **File Structure**

```
.rag-config/
├── doc-templates/              # 🆕 NEW: Documentation templates
│   ├── api-reference/
│   │   ├── openapi-style.yaml
│   │   ├── rest-api-minimal.yaml
│   │   └── graphql-style.yaml
│   ├── runbooks/
│   │   ├── sre-style.yaml      # Comprehensive SRE runbook
│   │   ├── devops-minimal.yaml
│   │   └── incident-response.yaml
│   ├── architecture/
│   │   ├── c4-model.yaml
│   │   ├── arc42-style.yaml
│   │   └── lightweight.yaml
│   └── README.md
│
├── glossary.yaml               # ✅ EXISTING: Extended with service-specific
├── templates.yaml              # ✅ EXISTING: Query templates
└── config.yaml                 # ✅ EXISTING: Feature flags
```

---

## 🎯 API Endpoints

```python
# Template Management
POST   /api/v1/templates                      # Create template
GET    /api/v1/templates                      # List templates
GET    /api/v1/templates/{id}                 # Get template
PUT    /api/v1/templates/{id}                 # Update template
DELETE /api/v1/templates/{id}                 # Delete template

GET    /api/v1/templates/categories           # List categories
GET    /api/v1/templates/recommend            # Get recommendation

# Template Usage
GET    /api/v1/templates/{id}/usage           # Usage statistics
GET    /api/v1/templates/{id}/quality         # Quality metrics

# Template Validation
POST   /api/v1/templates/validate             # Validate template structure
POST   /api/v1/templates/{id}/test            # Test render with sample context
```

---

## 🚀 Implementation Timeline

### **Week 1: Database & Models** (3 days)
- ✅ Create 2 new tables (documentation_templates, template_execution_history)
- ✅ Create SQLAlchemy models
- ✅ Migration scripts

### **Week 2: Template Manager** (5 days)
- ✅ Implement TemplateManager class
- ✅ Template loading, validation, rendering
- ✅ Usage tracking

### **Week 3: Built-in Templates** (3 days)
- ✅ Create 3 system templates (API Reference, Runbook, Architecture)
- ✅ Seed database with templates
- ✅ Test rendering

### **Week 4: Integration** (5 days)
- ✅ Update documentation generators to use templates
- ✅ Add template selection to orchestrator
- ✅ Test end-to-end

### **Week 5: API & UI** (5 days)
- ✅ Template management API endpoints
- ✅ Dashboard UI for template selection/creation
- ✅ Template preview functionality

### **Week 6: Testing & Polish** (5 days)
- ✅ Unit tests
- ✅ Integration tests
- ✅ Documentation
- ✅ User guide

**Total: 6 weeks**

---

## 📈 Success Metrics

| Metric | Target |
|--------|--------|
| Template usage | 80%+ of generations use templates |
| User-created templates | 5+ within 3 months |
| Structure consistency | 95%+ adherence to template |
| Template quality | 4.5/5 average rating |
| Documentation completeness | 90%+ sections complete |

---

**Status**: 🎨 **TEMPLATE SYSTEM DESIGNED**  
**Flaws Identified**: 4 major issues  
**Solutions Proposed**: 4 comprehensive fixes  
**New Tables**: 2 (vs 9 in original plan, vs 3 in audit)  
**Leverage**: 95% existing infrastructure  
**Production-Ready**: Runbooks + API Docs supported  
**User-Customizable**: ✅ Full template CRUD

