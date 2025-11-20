**Date:** November 19, 2025  
**Status:** 🏗️ **IMPLEMENTATION PLAN** - Production-Ready System  
**Builds On:** ADAPTIVE_DOCUMENTATION_ENHANCEMENT.md  

---

# Adaptive Documentation Generation: Implementation Guide

## 🎯 Design Principles

1. **Optional & Configurable** - Every feature can be toggled on/off
2. **Database-Backed** - All learnings and configs stored in PostgreSQL
3. **Existing Infrastructure** - Leverage current embedding/RAG systems
4. **Transparent** - Users see what's happening at every step
5. **User-Tunable** - Business logic, style, structure are customizable
6. **Template-Based** - Support custom templates for consistency
7. **Citable** - Clear source attribution for all generated content

---

## 📊 Database Schema Extensions

### New Tables for Adaptive System

```sql
-- =============================================================================
-- 1. Documentation Generation Configurations
-- =============================================================================

CREATE TABLE doc_generation_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    
    -- Feature toggles
    enable_adaptive_learning BOOLEAN DEFAULT FALSE,
    enable_knowledge_graph BOOLEAN DEFAULT FALSE,
    enable_prompt_evolution BOOLEAN DEFAULT FALSE,
    enable_reembedding BOOLEAN DEFAULT FALSE,
    enable_cross_repo_learning BOOLEAN DEFAULT FALSE,
    
    -- Generation settings
    passes_per_section INTEGER DEFAULT 3,
    queries_per_pass INTEGER DEFAULT 3,
    max_iterations INTEGER DEFAULT 10,
    
    -- Quality thresholds
    min_specificity_score DECIMAL(3,2) DEFAULT 0.70,
    min_completeness_score DECIMAL(3,2) DEFAULT 0.80,
    trigger_reembedding_threshold INTEGER DEFAULT 10, -- New concepts before reembedding
    
    -- User preferences
    business_domain VARCHAR(100),
    documentation_style VARCHAR(50) DEFAULT 'technical', -- technical, business, tutorial
    target_audience VARCHAR(50) DEFAULT 'developers', -- developers, business_users, mixed
    
    -- Template settings
    use_custom_template BOOLEAN DEFAULT FALSE,
    template_id UUID REFERENCES doc_templates(id),
    
    -- Citation settings
    include_citations BOOLEAN DEFAULT TRUE,
    citation_style VARCHAR(50) DEFAULT 'inline', -- inline, footnotes, endnotes
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    
    CONSTRAINT valid_style CHECK (documentation_style IN ('technical', 'business', 'tutorial', 'reference')),
    CONSTRAINT valid_audience CHECK (target_audience IN ('developers', 'business_users', 'mixed', 'executives'))
);

-- Default configuration
INSERT INTO doc_generation_configs (name, description) VALUES 
('default', 'Standard documentation generation without adaptive features'),
('adaptive_basic', 'Basic adaptive learning with knowledge graph'),
('adaptive_full', 'Full adaptive system with all features enabled');

CREATE INDEX idx_doc_gen_configs_name ON doc_generation_configs(name);


-- =============================================================================
-- 2. Custom Documentation Templates
-- =============================================================================

CREATE TABLE doc_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    
    -- Template content
    template_structure JSONB NOT NULL, -- Sections, headers, formatting rules
    
    -- Example:
    -- {
    --   "sections": [
    --     {"name": "Overview", "required": true, "max_length": 500},
    --     {"name": "Architecture", "required": true, "includes": ["diagram", "components"]},
    --     {"name": "API Reference", "required": false, "format": "table"}
    --   ],
    --   "style": {
    --     "header_prefix": "##",
    --     "code_fence": "```",
    --     "list_style": "ordered"
    --   },
    --   "citations": {
    --     "format": "markdown",
    --     "location": "end_of_section"
    --   }
    -- }
    
    -- Metadata
    framework_specific VARCHAR(100), -- null = generic, or 'scala_play', 'java_spring'
    is_public BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    
    CONSTRAINT valid_template_structure CHECK (jsonb_typeof(template_structure) = 'object')
);

CREATE INDEX idx_doc_templates_name ON doc_templates(name);
CREATE INDEX idx_doc_templates_framework ON doc_templates(framework_specific);


-- =============================================================================
-- 3. Knowledge Graph Storage
-- =============================================================================

CREATE TABLE knowledge_graph_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Node identification
    service_name VARCHAR(255) NOT NULL,
    node_type VARCHAR(50) NOT NULL, -- entity, service, endpoint, concept, file
    node_name VARCHAR(500) NOT NULL,
    
    -- Node data
    metadata JSONB NOT NULL,
    -- Example for entity:
    -- {
    --   "file_path": "app/models/Account.scala",
    --   "fields": [{"name": "id", "type": "UUID"}, ...],
    --   "relationships": ["User", "Organization"],
    --   "keywords": ["account", "supplier"]
    -- }
    
    -- Versioning
    version INTEGER DEFAULT 1,
    is_current BOOLEAN DEFAULT TRUE,
    
    -- Confidence scoring
    confidence_score DECIMAL(3,2) DEFAULT 1.00,
    extraction_method VARCHAR(100), -- manual, auto_discovery, prompt_evolution
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_node_type CHECK (node_type IN ('entity', 'service', 'endpoint', 'repository', 'concept', 'file', 'event', 'dependency')),
    CONSTRAINT valid_confidence CHECK (confidence_score BETWEEN 0 AND 1),
    UNIQUE (service_name, node_type, node_name, version)
);

CREATE INDEX idx_kg_nodes_service ON knowledge_graph_nodes(service_name);
CREATE INDEX idx_kg_nodes_type ON knowledge_graph_nodes(node_type);
CREATE INDEX idx_kg_nodes_current ON knowledge_graph_nodes(service_name, is_current);


CREATE TABLE knowledge_graph_edges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Edge definition
    from_node_id UUID NOT NULL REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,
    to_node_id UUID NOT NULL REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,
    edge_type VARCHAR(50) NOT NULL, -- uses, publishes, references, extends, implements
    
    -- Edge metadata
    metadata JSONB,
    -- Example:
    -- {
    --   "method": "inject",
    --   "file": "RegistrationService.scala",
    --   "line": 42
    -- }
    
    -- Weight/strength
    weight DECIMAL(3,2) DEFAULT 1.00,
    confidence_score DECIMAL(3,2) DEFAULT 1.00,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_edge_type CHECK (edge_type IN ('uses', 'publishes', 'consumes', 'references', 'extends', 'implements', 'calls', 'depends_on')),
    CONSTRAINT valid_edge_weight CHECK (weight BETWEEN 0 AND 1),
    CONSTRAINT no_self_reference CHECK (from_node_id != to_node_id)
);

CREATE INDEX idx_kg_edges_from ON knowledge_graph_edges(from_node_id);
CREATE INDEX idx_kg_edges_to ON knowledge_graph_edges(to_node_id);
CREATE INDEX idx_kg_edges_type ON knowledge_graph_edges(edge_type);


-- =============================================================================
-- 4. Documentation Generation Runs (with learnings)
-- =============================================================================

CREATE TABLE doc_generation_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Configuration
    config_id UUID NOT NULL REFERENCES doc_generation_configs(id),
    service_name VARCHAR(255) NOT NULL,
    
    -- Template used
    template_id UUID REFERENCES doc_templates(id),
    
    -- Generation metadata
    status VARCHAR(50) DEFAULT 'queued',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Results
    sections_generated JSONB, -- ["Overview", "Architecture", ...]
    total_queries INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    
    -- Quality metrics
    specificity_score DECIMAL(3,2),
    completeness_score DECIMAL(3,2),
    user_rating INTEGER, -- 1-5
    
    -- Learnings extracted
    new_concepts_count INTEGER DEFAULT 0,
    knowledge_graph_updated BOOLEAN DEFAULT FALSE,
    reembedding_triggered BOOLEAN DEFAULT FALSE,
    
    -- Output
    generated_content TEXT,
    citations JSONB, -- Array of source citations
    
    -- Error handling
    error_message TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    CONSTRAINT valid_rating CHECK (user_rating IS NULL OR user_rating BETWEEN 1 AND 5)
);

CREATE INDEX idx_doc_runs_service ON doc_generation_runs(service_name);
CREATE INDEX idx_doc_runs_status ON doc_generation_runs(status);
CREATE INDEX idx_doc_runs_config ON doc_generation_runs(config_id);


-- =============================================================================
-- 5. Prompt Evolution Tracking
-- =============================================================================

CREATE TABLE prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Template info
    name VARCHAR(255) NOT NULL,
    section_type VARCHAR(100) NOT NULL, -- Overview, Architecture, etc.
    framework VARCHAR(100), -- null = generic
    
    -- Template content
    prompt_template TEXT NOT NULL,
    -- Uses placeholders: {service_name}, {entities}, {dependencies}, etc.
    
    -- Effectiveness tracking
    times_used INTEGER DEFAULT 0,
    avg_effectiveness_score DECIMAL(3,2),
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    version INTEGER DEFAULT 1,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE (name, section_type, framework, version)
);

CREATE INDEX idx_prompt_templates_section ON prompt_templates(section_type);
CREATE INDEX idx_prompt_templates_framework ON prompt_templates(framework);
CREATE INDEX idx_prompt_templates_active ON prompt_templates(is_active);


CREATE TABLE prompt_execution_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to generation run
    run_id UUID NOT NULL REFERENCES doc_generation_runs(id) ON DELETE CASCADE,
    
    -- Prompt details
    template_id UUID REFERENCES prompt_templates(id),
    prompt_used TEXT NOT NULL,
    context_provided JSONB, -- What context was available when prompt was generated
    
    -- Execution
    pass_number INTEGER,
    section_name VARCHAR(100),
    executed_at TIMESTAMP DEFAULT NOW(),
    
    -- Results
    response TEXT,
    tokens_used INTEGER,
    
    -- Effectiveness
    effectiveness_score DECIMAL(3,2),
    specificity_score DECIMAL(3,2),
    code_examples_count INTEGER,
    
    -- Findings extracted
    findings JSONB,
    -- Example:
    -- {
    --   "entities": ["Account", "User"],
    --   "services": ["RegistrationService"],
    --   "keywords": ["async", "Future", "Slick"],
    --   "gaps_identified": ["error handling", "test coverage"]
    -- }
    
    CONSTRAINT valid_effectiveness CHECK (effectiveness_score IS NULL OR effectiveness_score BETWEEN 0 AND 1)
);

CREATE INDEX idx_prompt_history_run ON prompt_execution_history(run_id);
CREATE INDEX idx_prompt_history_template ON prompt_execution_history(template_id);
CREATE INDEX idx_prompt_history_effectiveness ON prompt_execution_history(effectiveness_score);


-- =============================================================================
-- 6. Enhanced Embeddings (Concept-Augmented)
-- =============================================================================

-- Extend existing embeddings table or create new one
CREATE TABLE enhanced_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to original document
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    
    -- Enhanced metadata from knowledge graph
    concepts JSONB, -- ["supplier_onboarding", "authentication"]
    keywords JSONB, -- ["account", "registration", "async"]
    related_entities JSONB, -- ["Account", "User", "Organization"]
    subject_area VARCHAR(255),
    importance_score DECIMAL(3,2),
    
    -- Enhanced embedding vector (if different from original)
    enhanced_embedding_id UUID REFERENCES embeddings(id),
    
    -- Versioning
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_importance CHECK (importance_score BETWEEN 0 AND 1)
);

CREATE INDEX idx_enhanced_emb_doc ON enhanced_embeddings(document_id);
CREATE INDEX idx_enhanced_emb_active ON enhanced_embeddings(is_active);
CREATE INDEX idx_enhanced_emb_concepts ON enhanced_embeddings USING gin(concepts);


-- =============================================================================
-- 7. Source Citations
-- =============================================================================

CREATE TABLE doc_source_citations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to generation run
    run_id UUID NOT NULL REFERENCES doc_generation_runs(id) ON DELETE CASCADE,
    
    -- Source document
    document_id UUID NOT NULL REFERENCES documents(id),
    
    -- Citation details
    section_name VARCHAR(255), -- Which section of generated doc used this source
    relevance_score DECIMAL(3,2),
    
    -- Excerpt
    excerpt TEXT, -- Specific portion used
    context TEXT, -- Surrounding context
    
    -- Metadata
    citation_text TEXT, -- Formatted citation for display
    citation_order INTEGER, -- Order in citation list
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT valid_relevance CHECK (relevance_score BETWEEN 0 AND 1)
);

CREATE INDEX idx_citations_run ON doc_source_citations(run_id);
CREATE INDEX idx_citations_doc ON doc_source_citations(document_id);
CREATE INDEX idx_citations_section ON doc_source_citations(run_id, section_name);


-- =============================================================================
-- 8. User Tuning Profiles
-- =============================================================================

CREATE TABLE user_tuning_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Profile info
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    
    -- Business context
    business_domain VARCHAR(255), -- e.g., "B2B SaaS", "E-commerce"
    industry VARCHAR(100), -- e.g., "FinTech", "Healthcare"
    
    -- Style preferences
    writing_style JSONB,
    -- {
    --   "tone": "professional", // professional, casual, technical
    --   "perspective": "third_person", // first_person, third_person
    --   "sentence_length": "medium", // short, medium, long
    --   "technical_depth": "high" // low, medium, high
    -- }
    
    -- Structure preferences
    structure_preferences JSONB,
    -- {
    --   "prefer_tables": true,
    --   "prefer_diagrams": true,
    --   "code_example_placement": "inline", // inline, appendix
    --   "section_order": ["overview", "architecture", ...]
    -- }
    
    -- Domain-specific terminology
    custom_glossary JSONB,
    -- {
    --   "account": "customer",
    --   "supplier": "vendor",
    --   "external_id": "partner_reference"
    -- }
    
    -- Quality preferences
    quality_weights JSONB,
    -- {
    --   "completeness": 0.4,
    --   "accuracy": 0.4,
    --   "readability": 0.2
    -- }
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255)
);

CREATE INDEX idx_tuning_profiles_name ON user_tuning_profiles(name);


-- =============================================================================
-- 9. Feedback & Continuous Improvement
-- =============================================================================

CREATE TABLE doc_generation_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to generation
    run_id UUID NOT NULL REFERENCES doc_generation_runs(id) ON DELETE CASCADE,
    
    -- User feedback
    user_id VARCHAR(255),
    overall_rating INTEGER CHECK (overall_rating BETWEEN 1 AND 5),
    
    -- Section-specific feedback
    section_ratings JSONB,
    -- {
    --   "Overview": {"rating": 4, "comments": "Good but missing X"},
    --   "Architecture": {"rating": 5, "comments": "Excellent detail"}
    -- }
    
    -- Corrections
    inaccuracies JSONB, -- Array of corrections
    -- [
    --   {
    --     "section": "API Reference",
    --     "incorrect": "Uses OAuth2",
    --     "correct": "Uses JWT tokens"
    --   }
    -- ]
    
    -- Missing information
    gaps_identified JSONB,
    -- ["Error handling patterns", "Deployment process"]
    
    -- Best sections
    best_sections JSONB, -- ["Architecture", "Setup"]
    worst_sections JSONB, -- ["Examples"]
    
    -- Additional comments
    comments TEXT,
    
    -- Action taken
    incorporated BOOLEAN DEFAULT FALSE,
    incorporated_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_feedback_run ON doc_generation_feedback(run_id);
CREATE INDEX idx_feedback_rating ON doc_generation_feedback(overall_rating);
```

---

## 🔧 API Extensions

### New Endpoints

```python
# =============================================================================
# Configuration Management
# =============================================================================

@router.get("/api/v1/doc-generation/configs")
async def list_configs():
    """List all available documentation generation configurations."""
    pass

@router.get("/api/v1/doc-generation/configs/{config_id}")
async def get_config(config_id: UUID):
    """Get specific configuration details."""
    pass

@router.post("/api/v1/doc-generation/configs")
async def create_config(config: DocGenerationConfig):
    """Create new configuration profile."""
    pass

@router.put("/api/v1/doc-generation/configs/{config_id}")
async def update_config(config_id: UUID, updates: Dict[str, Any]):
    """Update existing configuration."""
    pass


# =============================================================================
# Template Management
# =============================================================================

@router.get("/api/v1/doc-generation/templates")
async def list_templates(framework: Optional[str] = None):
    """List available documentation templates."""
    pass

@router.post("/api/v1/doc-generation/templates")
async def create_template(template: DocTemplate):
    """
    Create custom documentation template.
    
    Example:
    {
      "name": "API Service Template",
      "description": "Template for REST API services",
      "template_structure": {
        "sections": [
          {
            "name": "Overview",
            "required": true,
            "prompt_template": "Provide a concise overview of {service_name}...",
            "max_length": 500
          },
          {
            "name": "Endpoints",
            "required": true,
            "format": "table",
            "columns": ["Method", "Path", "Description", "Auth"]
          }
        ],
        "style": {
          "code_fence": "```",
          "list_style": "unordered"
        }
      }
    }
    """
    pass


# =============================================================================
# Knowledge Graph Access
# =============================================================================

@router.get("/api/v1/knowledge-graph/{service_name}")
async def get_knowledge_graph(service_name: str):
    """Get knowledge graph for a service."""
    pass

@router.get("/api/v1/knowledge-graph/{service_name}/nodes")
async def get_nodes(service_name: str, node_type: Optional[str] = None):
    """Get nodes from knowledge graph."""
    pass

@router.get("/api/v1/knowledge-graph/{service_name}/concepts")
async def get_concepts(service_name: str):
    """Get extracted concepts for a service."""
    pass


# =============================================================================
# Enhanced Documentation Generation
# =============================================================================

@router.post("/api/v1/doc-generation/generate")
async def generate_documentation(request: DocGenerationRequest):
    """
    Generate documentation with adaptive features.
    
    Request:
    {
      "service_name": "adminservice",
      "config_id": "uuid-here", // or use "default", "adaptive_basic"
      "template_id": "uuid-here", // optional, use custom template
      "tuning_profile_id": "uuid-here", // optional, user tuning
      
      "options": {
        "enable_adaptive": true, // Override config
        "enable_citations": true,
        "citation_style": "inline",
        "transparency_mode": "verbose" // quiet, normal, verbose
      },
      
      "sections": ["Overview", "Architecture", "API Reference"],
      
      "custom_prompts": { // Optional custom prompts per section
        "Overview": "Focus on business value and ROI..."
      }
    }
    """
    pass

@router.get("/api/v1/doc-generation/runs/{run_id}")
async def get_run_status(run_id: UUID):
    """Get status and results of generation run."""
    pass

@router.get("/api/v1/doc-generation/runs/{run_id}/transparency")
async def get_run_transparency_log(run_id: UUID):
    """
    Get detailed transparency log showing what happened.
    
    Returns:
    {
      "phases": [
        {
          "phase": "Discovery",
          "queries": [
            {
              "prompt": "What framework is used?",
              "findings": {"framework": "Play Framework"},
              "sources": [...]
            }
          ]
        },
        {
          "phase": "Knowledge Graph Building",
          "nodes_created": 45,
          "edges_created": 87,
          "concepts_extracted": ["supplier_onboarding", ...]
        },
        {
          "phase": "Section Generation",
          "sections": [...]
        }
      ],
      "reembedding": {
        "triggered": true,
        "documents_affected": 100,
        "new_concepts": [...]
      }
    }
    """
    pass


# =============================================================================
# User Tuning
# =============================================================================

@router.post("/api/v1/doc-generation/tuning-profiles")
async def create_tuning_profile(profile: UserTuningProfile):
    """
    Create user tuning profile.
    
    Example:
    {
      "name": "Enterprise SaaS Style",
      "business_domain": "B2B SaaS",
      "writing_style": {
        "tone": "professional",
        "technical_depth": "high"
      },
      "custom_glossary": {
        "account": "customer",
        "supplier": "vendor"
      },
      "structure_preferences": {
        "prefer_tables": true,
        "section_order": ["overview", "business_value", "architecture"]
      }
    }
    """
    pass


# =============================================================================
# Feedback & Improvement
# =============================================================================

@router.post("/api/v1/doc-generation/runs/{run_id}/feedback")
async def submit_feedback(run_id: UUID, feedback: DocFeedback):
    """
    Submit feedback on generated documentation.
    
    {
      "overall_rating": 4,
      "section_ratings": {
        "Overview": {"rating": 5, "comments": "Clear and concise"},
        "API Reference": {"rating": 3, "comments": "Missing error codes"}
      },
      "inaccuracies": [
        {
          "section": "Architecture",
          "incorrect": "Uses Redis for cache",
          "correct": "Uses Memcached for cache"
        }
      ],
      "gaps_identified": ["Deployment process", "Monitoring setup"]
    }
    """
    pass

@router.get("/api/v1/doc-generation/improvements")
async def get_improvement_metrics():
    """Get metrics showing system improvement over time."""
    pass
```

---

## 🏗️ Implementation Architecture

### Component Integration

```python
# =============================================================================
# Adaptive Documentation Generator (Integrated)
# =============================================================================

class AdaptiveDocumentationGenerator:
    """
    Production-ready adaptive documentation generator.
    Integrates with existing ecosystem-mcp infrastructure.
    """
    
    def __init__(
        self,
        config_id: UUID,
        template_id: Optional[UUID] = None,
        tuning_profile_id: Optional[UUID] = None
    ):
        # Load configuration from database
        self.config = self._load_config(config_id)
        self.template = self._load_template(template_id) if template_id else None
        self.tuning_profile = self._load_tuning_profile(tuning_profile_id) if tuning_profile_id else None
        
        # Initialize components (conditional based on config)
        self.knowledge_graph = KnowledgeGraph() if self.config.enable_knowledge_graph else None
        self.prompt_evolver = PromptEvolver() if self.config.enable_prompt_evolution else None
        
        # Use existing infrastructure
        self.embedding_service = get_embedding_service()  # Existing
        self.chroma_client = get_chroma_client()  # Existing
        self.database = get_database()  # Existing
        
        # Transparency tracking
        self.transparency_log = TransparencyLog()
        
        # Citation tracking
        self.citations = CitationTracker()
    
    async def generate(
        self,
        service_name: str,
        sections: List[str],
        custom_prompts: Optional[Dict[str, str]] = None,
        transparency_mode: str = "normal"
    ) -> Dict[str, Any]:
        """
        Generate documentation with full transparency and citation.
        
        Returns:
        {
          "run_id": "uuid",
          "content": "# Documentation\n\n...",
          "citations": [...],
          "transparency_log": {...},
          "metrics": {...}
        }
        """
        
        # Create generation run in database
        run_id = await self._create_run(service_name, sections)
        
        self.transparency_log.start_phase("Initialization")
        self.transparency_log.log(f"Config: {self.config.name}")
        self.transparency_log.log(f"Template: {self.template.name if self.template else 'Default'}")
        self.transparency_log.log(f"Adaptive features: {self.config.enable_adaptive_learning}")
        
        try:
            # Phase 1: Discovery (if adaptive enabled)
            if self.config.enable_adaptive_learning:
                await self._discovery_phase(service_name)
            
            # Phase 2: Generate sections
            generated_sections = []
            for section in sections:
                section_content = await self._generate_section(
                    service_name,
                    section,
                    custom_prompts.get(section) if custom_prompts else None
                )
                generated_sections.append(section_content)
            
            # Phase 3: Apply template (if specified)
            if self.template:
                final_content = self._apply_template(generated_sections)
            else:
                final_content = self._combine_sections(generated_sections)
            
            # Phase 4: Add citations
            if self.config.include_citations:
                final_content = self._add_citations(final_content)
            
            # Phase 5: Store results
            await self._save_results(run_id, final_content)
            
            # Phase 6: Trigger reembedding if needed
            if self.config.enable_reembedding and self._should_reembed():
                await self._trigger_reembedding(service_name)
            
            return {
                "run_id": str(run_id),
                "content": final_content,
                "citations": self.citations.get_all(),
                "transparency_log": self.transparency_log.export() if transparency_mode == "verbose" else None,
                "metrics": self._calculate_metrics()
            }
            
        except Exception as e:
            await self._handle_error(run_id, str(e))
            raise
    
    async def _discovery_phase(self, service_name: str):
        """Phase 1: Initial discovery to build knowledge graph."""
        
        self.transparency_log.start_phase("Discovery")
        
        # Query 1: Structural analysis
        structural_query = self._build_structural_query(service_name)
        self.transparency_log.log(f"Query: {structural_query[:100]}...")
        
        structural_results = await self._execute_query(structural_query, service_name)
        self.transparency_log.log(f"Found: {len(structural_results)} relevant documents")
        
        # Extract metadata
        metadata = self._extract_metadata(structural_results)
        self.transparency_log.log(f"Extracted: framework={metadata.get('framework')}, patterns={metadata.get('patterns')}")
        
        # Store in knowledge graph
        if self.knowledge_graph:
            await self.knowledge_graph.add_metadata(service_name, metadata)
            self.transparency_log.log(f"Knowledge graph updated: {self.knowledge_graph.node_count()} nodes")
        
        # More discovery queries...
        # (Technology stack, domain concepts, etc.)
        
        self.transparency_log.end_phase()
    
    async def _generate_section(
        self,
        service_name: str,
        section_name: str,
        custom_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a single documentation section."""
        
        self.transparency_log.start_phase(f"Generate {section_name}")
        
        # Get template for this section if available
        section_template = None
        if self.template:
            section_template = self.template.get_section_template(section_name)
        
        # Build context from knowledge graph
        context = {}
        if self.knowledge_graph:
            context = self.knowledge_graph.get_context_for_section(service_name, section_name)
            self.transparency_log.log(f"Context: {len(context)} concepts available")
        
        # Multi-pass generation
        section_content = ""
        for pass_num in range(self.config.passes_per_section):
            self.transparency_log.log(f"Pass {pass_num + 1}/{self.config.passes_per_section}")
            
            # Build prompt
            if custom_prompt:
                prompt = custom_prompt
            elif section_template:
                prompt = self._fill_template(section_template, context)
            else:
                prompt = self._build_prompt(section_name, pass_num, context, section_content)
            
            # Evolve prompt if enabled
            if self.prompt_evolver and pass_num > 0:
                prompt = self.prompt_evolver.refine(prompt, section_content, context)
                self.transparency_log.log(f"Prompt evolved based on previous results")
            
            self.transparency_log.log(f"Prompt preview: {prompt[:150]}...")
            
            # Execute query
            response = await self._execute_query_with_citations(prompt, service_name, section_name)
            
            self.transparency_log.log(f"Response: {len(response['content'])} chars, {len(response['sources'])} sources")
            
            # Track sources for citations
            for source in response['sources']:
                self.citations.add(
                    run_id=self.current_run_id,
                    section=section_name,
                    document_id=source['id'],
                    relevance=source['score'],
                    excerpt=source['excerpt']
                )
            
            # Accumulate content
            section_content += response['content'] + "\n\n"
            
            # Update context for next pass
            if pass_num < self.config.passes_per_section - 1:
                findings = self._extract_findings(response['content'])
                context.update(findings)
                self.transparency_log.log(f"Findings: {list(findings.keys())}")
        
        self.transparency_log.end_phase()
        
        return {
            "name": section_name,
            "content": section_content,
            "sources": self.citations.get_for_section(section_name)
        }
    
    async def _execute_query_with_citations(
        self,
        prompt: str,
        service_name: str,
        section_name: str
    ) -> Dict[str, Any]:
        """
        Execute RAG query and track sources.
        Uses EXISTING ecosystem-mcp RAG infrastructure.
        """
        
        # Use existing enhanced query endpoint
        from ...api.routes.context_aware_query import execute_context_aware_query
        
        query_params = {
            "question": prompt,
            "service_filter": service_name,
            "n_results": self.config.queries_per_pass * 5,  # Get more for better coverage
            "temperature": 0.3,  # Lower for more deterministic
            "max_tokens": 2048
        }
        
        # Execute using existing infrastructure
        response = await execute_context_aware_query(**query_params)
        
        # Store prompt execution in database
        await self._store_prompt_execution(
            prompt=prompt,
            response=response['answer'],
            sources=response['sources'],
            section=section_name
        )
        
        return {
            "content": response['answer'],
            "sources": response['sources']
        }
    
    def _add_citations(self, content: str) -> str:
        """Add citations to generated documentation."""
        
        citations = self.citations.get_all()
        
        if not citations:
            return content
        
        # Format based on citation style
        if self.config.citation_style == "inline":
            # Already included in text
            return content
        
        elif self.config.citation_style == "footnotes":
            # Add footnotes at bottom of each section
            return self._format_footnotes(content, citations)
        
        elif self.config.citation_style == "endnotes":
            # Add all citations at end
            citations_section = self._format_citations(citations)
            return f"{content}\n\n---\n\n## Sources\n\n{citations_section}"
    
    def _format_citations(self, citations: List[Dict]) -> str:
        """Format citations list."""
        
        formatted = []
        for idx, citation in enumerate(citations, 1):
            formatted.append(f"""
{idx}. **{citation['file_path']}**
   - Relevance: {citation['relevance_score']:.2f}
   - Section: {citation['section']}
   - Excerpt: _{citation['excerpt'][:200]}..._
""")
        
        return "\n".join(formatted)
    
    async def _trigger_reembedding(self, service_name: str):
        """Trigger re-embedding with enhanced concepts."""
        
        self.transparency_log.start_phase("Re-embedding")
        
        # Get new concepts from knowledge graph
        new_concepts = self.knowledge_graph.get_recent_concepts(
            service_name,
            since=self.last_reembedding_time
        )
        
        self.transparency_log.log(f"New concepts: {len(new_concepts)}")
        
        # Get documents for this service
        documents = await self._get_service_documents(service_name)
        self.transparency_log.log(f"Documents to re-embed: {len(documents)}")
        
        # For each document, add concept metadata
        for doc in documents:
            # Match concepts to document
            relevant_concepts = self.knowledge_graph.match_concepts(doc.content, new_concepts)
            
            if relevant_concepts:
                # Create enhanced embedding record
                await self._create_enhanced_embedding(doc.id, relevant_concepts)
        
        self.transparency_log.log(f"Re-embedding complete")
        self.transparency_log.end_phase()
    
    async def _create_enhanced_embedding(self, document_id: UUID, concepts: List[str]):
        """Create enhanced embedding record in database."""
        
        async with self.database.session() as session:
            # Get original document
            doc = await session.get(DocumentModel, document_id)
            
            # Extract metadata
            keywords = self._extract_keywords(doc.normalized_content, concepts)
            related_entities = self.knowledge_graph.get_related_entities(concepts)
            subject_area = self.knowledge_graph.classify_subject_area(concepts)
            importance = self.knowledge_graph.calculate_importance(document_id)
            
            # Create enhanced embedding record
            enhanced = EnhancedEmbeddingModel(
                document_id=document_id,
                concepts=concepts,
                keywords=keywords,
                related_entities=related_entities,
                subject_area=subject_area,
                importance_score=importance,
                version=1,
                is_active=True
            )
            
            session.add(enhanced)
            await session.commit()
```

---

## 🎨 Dashboard UI Integration

### Enhanced Configuration Page

```python
# dashboard_views/doc_generation_advanced.py

def show_advanced_doc_generation(api_base_url: str):
    """Enhanced documentation generation with full configurability."""
    
    st.title("📖 Advanced Documentation Generation")
    
    # Tabs for different aspects
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚙️ Configuration",
        "📝 Template",
        "🧠 Adaptive Features",
        "🎨 Style Tuning",
        "▶️ Generate"
    ])
    
    # =========================================================================
    # Tab 1: Configuration
    # =========================================================================
    with tab1:
        st.header("Generation Configuration")
        
        # Load available configs
        configs = fetch_configs(api_base_url)
        
        config_choice = st.radio(
            "Choose Configuration",
            options=["Use Existing", "Create New"],
            horizontal=True
        )
        
        if config_choice == "Use Existing":
            selected_config = st.selectbox(
                "Select Configuration",
                options=[c['name'] for c in configs],
                format_func=lambda x: f"{x} - {next(c['description'] for c in configs if c['name'] == x)}"
            )
            
            # Show config details
            config = next(c for c in configs if c['name'] == selected_config)
            
            with st.expander("📋 Configuration Details", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Feature Toggles**")
                    st.checkbox("Adaptive Learning", value=config['enable_adaptive_learning'], key="view_adaptive", disabled=True)
                    st.checkbox("Knowledge Graph", value=config['enable_knowledge_graph'], key="view_kg", disabled=True)
                    st.checkbox("Prompt Evolution", value=config['enable_prompt_evolution'], key="view_prompt", disabled=True)
                    st.checkbox("Re-embedding", value=config['enable_reembedding'], key="view_reembed", disabled=True)
                
                with col2:
                    st.markdown("**Generation Settings**")
                    st.write(f"Passes per section: {config['passes_per_section']}")
                    st.write(f"Queries per pass: {config['queries_per_pass']}")
                    st.write(f"Documentation style: {config['documentation_style']}")
                    st.write(f"Target audience: {config['target_audience']}")
        
        else:  # Create New
            st.markdown("### Create Custom Configuration")
            
            config_name = st.text_input("Configuration Name")
            config_desc = st.text_area("Description")
            
            st.markdown("#### 🎛️ Feature Toggles")
            
            col1, col2 = st.columns(2)
            
            with col1:
                enable_adaptive = st.checkbox(
                    "Enable Adaptive Learning",
                    value=False,
                    help="""
                    **Adaptive Learning**: System learns from each query to improve subsequent ones.
                    
                    What it does:
                    - Extracts metadata (frameworks, patterns, concepts)
                    - Builds knowledge graph
                    - Refines prompts based on findings
                    
                    Trade-off: Slower but much more accurate
                    """
                )
                
                enable_kg = st.checkbox(
                    "Enable Knowledge Graph",
                    value=False,
                    help="""
                    **Knowledge Graph**: Build graph of entities, services, relationships.
                    
                    What it does:
                    - Maps code structure
                    - Identifies relationships
                    - Enables intelligent query routing
                    
                    Requires: Database storage
                    """
                )
                
                enable_prompt_evolution = st.checkbox(
                    "Enable Prompt Evolution",
                    value=False,
                    help="""
                    **Prompt Evolution**: Learn which prompts work best over time.
                    
                    What it does:
                    - Tracks prompt effectiveness
                    - Refines prompts based on results
                    - Improves quality over generations
                    
                    Requires: Multiple generation runs
                    """
                )
            
            with col2:
                enable_reembedding = st.checkbox(
                    "Enable Re-embedding",
                    value=False,
                    help="""
                    **Re-embedding**: Enhance embeddings with learned concepts.
                    
                    What it does:
                    - Augments documents with concept metadata
                    - Improves retrieval accuracy
                    - Uses existing embedding infrastructure
                    
                    Triggers: When >10 new concepts learned
                    """
                )
                
                enable_cross_repo = st.checkbox(
                    "Enable Cross-Repo Learning",
                    value=False,
                    help="""
                    **Cross-Repo Learning**: Learn patterns from other repositories.
                    
                    What it does:
                    - Applies patterns from similar repos
                    - Improves first-time generation
                    - Builds universal knowledge base
                    
                    Requires: Multiple repos processed
                    """
                )
            
            st.markdown("---")
            st.markdown("#### ⚙️ Generation Settings")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                passes = st.slider("Passes per Section", 1, 5, 3,
                    help="More passes = more detail, but slower")
            
            with col2:
                queries = st.slider("Queries per Pass", 1, 5, 3,
                    help="More queries = broader coverage")
            
            with col3:
                max_iter = st.slider("Max Iterations", 5, 20, 10,
                    help="Safety limit for refinement loops")
            
            st.markdown("---")
            st.markdown("#### 🎯 Quality Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                min_specificity = st.slider(
                    "Minimum Specificity",
                    0.0, 1.0, 0.7, 0.05,
                    help="Threshold for considering response specific enough"
                )
            
            with col2:
                reembed_threshold = st.number_input(
                    "Re-embedding Threshold",
                    1, 50, 10,
                    help="Trigger re-embedding after N new concepts"
                )
            
            st.markdown("---")
            st.markdown("#### 📊 User Preferences")
            
            col1, col2 = st.columns(2)
            
            with col1:
                doc_style = st.selectbox(
                    "Documentation Style",
                    options=["technical", "business", "tutorial", "reference"],
                    help="""
                    - **Technical**: For developers, includes code details
                    - **Business**: For stakeholders, focuses on value
                    - **Tutorial**: Step-by-step, learning-oriented
                    - **Reference**: Comprehensive, lookup-focused
                    """
                )
            
            with col2:
                target_audience = st.selectbox(
                    "Target Audience",
                    options=["developers", "business_users", "mixed", "executives"],
                    help="Adjusts language and depth accordingly"
                )
            
            if st.button("💾 Save Configuration"):
                # Create config via API
                new_config = {
                    "name": config_name,
                    "description": config_desc,
                    "enable_adaptive_learning": enable_adaptive,
                    "enable_knowledge_graph": enable_kg,
                    "enable_prompt_evolution": enable_prompt_evolution,
                    "enable_reembedding": enable_reembedding,
                    "enable_cross_repo_learning": enable_cross_repo,
                    "passes_per_section": passes,
                    "queries_per_pass": queries,
                    "max_iterations": max_iter,
                    "min_specificity_score": min_specificity,
                    "trigger_reembedding_threshold": reembed_threshold,
                    "documentation_style": doc_style,
                    "target_audience": target_audience
                }
                
                response = httpx.post(
                    f"{api_base_url}/api/v1/doc-generation/configs",
                    json=new_config
                )
                
                if response.status_code == 200:
                    st.success(f"✅ Configuration '{config_name}' created!")
                else:
                    st.error(f"❌ Error: {response.text}")
    
    # =========================================================================
    # Tab 2: Template Selection/Creation
    # =========================================================================
    with tab2:
        st.header("Documentation Template")
        
        template_choice = st.radio(
            "Template Options",
            options=["Use Default", "Select Existing", "Create Custom"],
            horizontal=True
        )
        
        if template_choice == "Select Existing":
            templates = fetch_templates(api_base_url)
            
            selected_template = st.selectbox(
                "Select Template",
                options=[t['name'] for t in templates],
                format_func=lambda x: f"{x} ({next(t['framework_specific'] or 'Generic' for t in templates if t['name'] == x)})"
            )
            
            # Preview template structure
            template = next(t for t in templates if t['name'] == selected_template)
            
            with st.expander("📋 Template Structure", expanded=True):
                st.json(template['template_structure'])
        
        elif template_choice == "Create Custom":
            st.markdown("### Create Custom Template")
            
            template_name = st.text_input("Template Name", "My Custom Template")
            template_desc = st.text_area("Description")
            
            st.markdown("#### 📚 Sections")
            
            num_sections = st.number_input("Number of Sections", 1, 15, 6)
            
            sections = []
            for i in range(num_sections):
                with st.expander(f"Section {i+1}", expanded=(i < 3)):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        section_name = st.text_input(f"Section Name", "Overview", key=f"name_{i}")
                        required = st.checkbox("Required", value=True, key=f"req_{i}")
                    
                    with col2:
                        max_length = st.number_input("Max Length (words)", 0, 5000, 0, 100, key=f"len_{i}")
                        format_type = st.selectbox("Format", ["paragraph", "table", "list", "code"], key=f"fmt_{i}")
                    
                    prompt_template = st.text_area(
                        "Prompt Template (use {placeholders})",
                        value=f"Explain the {section_name.lower()} of {{service_name}}...",
                        key=f"prompt_{i}",
                        help="Use {service_name}, {entities}, {dependencies}, etc."
                    )
                    
                    sections.append({
                        "name": section_name,
                        "required": required,
                        "max_length": max_length if max_length > 0 else None,
                        "format": format_type,
                        "prompt_template": prompt_template
                    })
            
            st.markdown("---")
            st.markdown("#### 🎨 Style Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                header_prefix = st.text_input("Header Prefix", "##")
                code_fence = st.text_input("Code Fence", "```")
            
            with col2:
                list_style = st.selectbox("List Style", ["unordered", "ordered"])
                citation_location = st.selectbox("Citation Location", ["inline", "end_of_section", "end_of_document"])
            
            if st.button("💾 Save Template"):
                new_template = {
                    "name": template_name,
                    "description": template_desc,
                    "template_structure": {
                        "sections": sections,
                        "style": {
                            "header_prefix": header_prefix,
                            "code_fence": code_fence,
                            "list_style": list_style
                        },
                        "citations": {
                            "format": "markdown",
                            "location": citation_location
                        }
                    }
                }
                
                response = httpx.post(
                    f"{api_base_url}/api/v1/doc-generation/templates",
                    json=new_template
                )
                
                if response.status_code == 200:
                    st.success(f"✅ Template '{template_name}' created!")
    
    # =========================================================================
    # Tab 3: Adaptive Features (Transparency)
    # =========================================================================
    with tab3:
        st.header("🧠 Adaptive Features")
        
        st.info("""
        **Transparency Mode**: See exactly what the adaptive system is doing.
        
        This view shows:
        - What queries are being executed
        - What metadata is being extracted
        - How the knowledge graph is built
        - Which prompts are being refined
        - When re-embedding is triggered
        """)
        
        transparency_mode = st.radio(
            "Transparency Level",
            options=["quiet", "normal", "verbose"],
            index=1,
            help="""
            - **Quiet**: Only show major phases
            - **Normal**: Show phases + key decisions
            - **Verbose**: Show every query, finding, and decision
            """
        )
        
        st.markdown("---")
        
        # If there's a recent run, show its transparency log
        if st.checkbox("📊 Show Recent Run Transparency"):
            run_id = st.text_input("Run ID", placeholder="Enter run UUID")
            
            if run_id:
                response = httpx.get(
                    f"{api_base_url}/api/v1/doc-generation/runs/{run_id}/transparency"
                )
                
                if response.status_code == 200:
                    log = response.json()
                    
                    for phase in log['phases']:
                        with st.expander(f"📍 {phase['phase']}", expanded=True):
                            if 'queries' in phase:
                                for idx, query in enumerate(phase['queries'], 1):
                                    st.markdown(f"**Query {idx}**")
                                    st.code(query['prompt'], language="text")
                                    st.json(query['findings'])
                                    st.caption(f"Sources: {len(query['sources'])}")
                                    st.markdown("---")
                            
                            if 'nodes_created' in phase:
                                st.metric("Nodes Created", phase['nodes_created'])
                                st.metric("Edges Created", phase['edges_created'])
                                st.write("Concepts:", ", ".join(phase['concepts_extracted'][:10]))
                else:
                    st.error("Run not found")
    
    # =========================================================================
    # Tab 4: Style Tuning
    # =========================================================================
    with tab4:
        st.header("🎨 Style & Business Tuning")
        
        st.markdown("""
        Customize documentation to match your business context and writing style.
        """)
        
        # Business Context
        with st.expander("🏢 Business Context", expanded=True):
            business_domain = st.text_input(
                "Business Domain",
                placeholder="e.g., B2B SaaS, E-commerce, FinTech"
            )
            
            industry = st.text_input(
                "Industry",
                placeholder="e.g., Software, Healthcare, Finance"
            )
        
        # Writing Style
        with st.expander("✍️ Writing Style", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                tone = st.selectbox(
                    "Tone",
                    options=["professional", "casual", "technical", "friendly"]
                )
                
                perspective = st.selectbox(
                    "Perspective",
                    options=["third_person", "first_person", "second_person"]
                )
            
            with col2:
                sentence_length = st.selectbox(
                    "Sentence Length",
                    options=["short", "medium", "long"]
                )
                
                technical_depth = st.selectbox(
                    "Technical Depth",
                    options=["low", "medium", "high"]
                )
        
        # Custom Glossary
        with st.expander("📖 Custom Glossary", expanded=True):
            st.markdown("""
            Replace technical terms with business-specific terminology.
            """)
            
            glossary_entries = st.number_input("Number of Terms", 1, 20, 5)
            
            glossary = {}
            for i in range(glossary_entries):
                col1, col2 = st.columns(2)
                with col1:
                    term = st.text_input(f"Technical Term {i+1}", key=f"term_{i}")
                with col2:
                    replacement = st.text_input(f"Business Term {i+1}", key=f"repl_{i}")
                
                if term and replacement:
                    glossary[term] = replacement
            
            if glossary:
                st.success(f"✅ {len(glossary)} terms defined")
                st.json(glossary)
        
        # Structure Preferences
        with st.expander("🏗️ Structure Preferences", expanded=True):
            prefer_tables = st.checkbox("Prefer Tables", value=True)
            prefer_diagrams = st.checkbox("Prefer Diagrams", value=True)
            
            code_placement = st.radio(
                "Code Example Placement",
                options=["inline", "appendix"],
                help="Inline: Within sections | Appendix: At the end"
            )
        
        if st.button("💾 Save Tuning Profile"):
            profile = {
                "name": f"{business_domain} Profile",
                "business_domain": business_domain,
                "industry": industry,
                "writing_style": {
                    "tone": tone,
                    "perspective": perspective,
                    "sentence_length": sentence_length,
                    "technical_depth": technical_depth
                },
                "custom_glossary": glossary,
                "structure_preferences": {
                    "prefer_tables": prefer_tables,
                    "prefer_diagrams": prefer_diagrams,
                    "code_example_placement": code_placement
                }
            }
            
            response = httpx.post(
                f"{api_base_url}/api/v1/doc-generation/tuning-profiles",
                json=profile
            )
            
            if response.status_code == 200:
                st.success("✅ Tuning profile saved!")
    
    # =========================================================================
    # Tab 5: Generate
    # =========================================================================
    with tab5:
        st.header("▶️ Generate Documentation")
        
        # Service selection
        service_name = st.selectbox(
            "Target Service",
            options=["adminservice", "authservice", "Hackathon"]
        )
        
        # Section selection
        st.markdown("### 📚 Sections to Generate")
        
        sections = []
        col1, col2 = st.columns(2)
        
        with col1:
            if st.checkbox("Overview", value=True):
                sections.append("Overview")
            if st.checkbox("Architecture", value=True):
                sections.append("Architecture")
            if st.checkbox("API Reference", value=True):
                sections.append("API Reference")
            if st.checkbox("Data Models"):
                sections.append("Data Models")
        
        with col2:
            if st.checkbox("Setup Guide"):
                sections.append("Setup")
            if st.checkbox("Examples"):
                sections.append("Examples")
            if st.checkbox("Security"):
                sections.append("Security")
            if st.checkbox("Troubleshooting"):
                sections.append("Troubleshooting")
        
        # Citation settings
        st.markdown("---")
        st.markdown("### 📎 Citations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            include_citations = st.checkbox("Include Source Citations", value=True)
        
        with col2:
            if include_citations:
                citation_style = st.selectbox(
                    "Citation Style",
                    options=["inline", "footnotes", "endnotes"]
                )
        
        # Custom prompts (optional)
        if st.checkbox("🎯 Use Custom Prompts"):
            custom_prompts = {}
            for section in sections:
                prompt = st.text_area(
                    f"Custom Prompt for {section}",
                    placeholder=f"Enter custom prompt for {section} section..."
                )
                if prompt:
                    custom_prompts[section] = prompt
        else:
            custom_prompts = {}
        
        # Generate button
        st.markdown("---")
        
        if st.button("🚀 Generate Documentation", type="primary"):
            with st.spinner("Generating documentation..."):
                # Build request
                request = {
                    "service_name": service_name,
                    "config_id": st.session_state.get('selected_config_id', 'default'),
                    "template_id": st.session_state.get('selected_template_id'),
                    "tuning_profile_id": st.session_state.get('tuning_profile_id'),
                    "sections": sections,
                    "options": {
                        "include_citations": include_citations,
                        "citation_style": citation_style if include_citations else None,
                        "transparency_mode": transparency_mode
                    },
                    "custom_prompts": custom_prompts if custom_prompts else None
                }
                
                # Execute
                response = httpx.post(
                    f"{api_base_url}/api/v1/doc-generation/generate",
                    json=request,
                    timeout=600.0  # 10 minutes
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    st.success(f"✅ Documentation generated! Run ID: {result['run_id']}")
                    
                    # Display result
                    st.markdown("---")
                    st.markdown("### 📄 Generated Documentation")
                    
                    st.markdown(result['content'])
                    
                    # Download button
                    st.download_button(
                        "📥 Download Documentation",
                        data=result['content'],
                        file_name=f"{service_name}_documentation.md",
                        mime="text/markdown"
                    )
                    
                    # Show transparency log if verbose
                    if transparency_mode == "verbose" and result.get('transparency_log'):
                        with st.expander("🔍 Transparency Log"):
                            st.json(result['transparency_log'])
                    
                    # Show citations
                    if include_citations and result.get('citations'):
                        with st.expander(f"📚 Sources ({len(result['citations'])} documents)"):
                            for citation in result['citations']:
                                st.markdown(f"- **{citation['file_path']}** (relevance: {citation['relevance_score']:.2f})")
                else:
                    st.error(f"❌ Error: {response.text}")
```

---

## 📈 Migration Guide

### For Existing Users

**Step 1: Enable Adaptive Features Gradually**

```python
# Start with basic config (no adaptive features)
curl -X POST http://localhost:8000/api/v1/doc-generation/generate \
  -d '{"service_name": "myservice", "config_id": "default"}'

# Then enable knowledge graph only
curl -X POST http://localhost:8000/api/v1/doc-generation/generate \
  -d '{"service_name": "myservice", "config_id": "adaptive_basic"}'

# Finally, full adaptive system
curl -X POST http://localhost:8000/api/v1/doc-generation/generate \
  -d '{"service_name": "myservice", "config_id": "adaptive_full"}'
```

**Step 2: Create Custom Templates**

Start with built-in template, customize incrementally.

**Step 3: Tune for Your Business**

Create tuning profile, test, refine.

---

## 🎯 Success Metrics

| Feature | Metric | Target |
|---------|--------|--------|
| Transparency | User understanding | 95%+ |
| Customization | Config options used | 60%+ |
| Citations | Sources per doc | 20-50 |
| Consistency | Template adherence | 100% |
| Improvement | Quality over time | +15% per generation |

---

**Status**: 🏗️ **PRODUCTION-READY IMPLEMENTATION**  
**Effort**: 8-12 weeks (phased rollout)  
**Impact**: 🚀 **TRANSFORMATIVE** + **USER-CONTROLLED**  
**Compatibility**: ✅ **Backward Compatible** (all features optional)

