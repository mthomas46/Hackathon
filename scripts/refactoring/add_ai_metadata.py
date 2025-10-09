#!/usr/bin/env python3
"""
AI Metadata Generator

Adds AI-friendly metadata, tags, and navigation markers to refactoring documents
to help AI agents understand and navigate the plan.

Usage:
    python add_ai_metadata.py

This will add YAML frontmatter with AI tags to all refactoring documents.
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List


# Document metadata for AI agents
DOCUMENT_METADATA = {
    "MASTER_REFACTORING_PLAN.md": {
        "ai_purpose": "primary_strategy",
        "ai_read_priority": 1,
        "ai_context_level": "strategic",
        "ai_tags": ["strategy", "methodology", "phases", "quality-gates", "overview"],
        "ai_when_to_read": "Before starting any refactoring work",
        "ai_key_sections": [
            "Goals and Objectives",
            "Refactoring Methodology",
            "Quality Gates",
            "Service Categories"
        ],
        "ai_execution_relevance": "critical"
    },
    
    "AI_AGENT_EXECUTION_GUIDE.md": {
        "ai_purpose": "execution_instructions",
        "ai_read_priority": 1,
        "ai_context_level": "tactical",
        "ai_tags": ["ai-execution", "step-by-step", "context-management", "scope-control"],
        "ai_when_to_read": "At start of every session",
        "ai_key_sections": [
            "Execution Context Management",
            "Step-by-Step Execution Protocol",
            "Scope Control",
            "Context Maintenance"
        ],
        "ai_execution_relevance": "critical"
    },
    
    "LIVING_PROGRESS_TRACKER.md": {
        "ai_purpose": "progress_tracking",
        "ai_read_priority": 2,
        "ai_context_level": "operational",
        "ai_tags": ["progress", "status", "metrics", "tracking"],
        "ai_when_to_read": "Before selecting service and after completing work",
        "ai_key_sections": [
            "Service Progress Table",
            "Current Sprint",
            "Metrics Dashboard"
        ],
        "ai_execution_relevance": "high",
        "ai_update_frequency": "After each phase completion"
    },
    
    "NAMING_CONVENTIONS_STANDARDS.md": {
        "ai_purpose": "coding_standards",
        "ai_read_priority": 2,
        "ai_context_level": "reference",
        "ai_tags": ["standards", "naming", "conventions", "patterns"],
        "ai_when_to_read": "During implementation (Phase 3)",
        "ai_key_sections": [
            "Service Naming",
            "Directory Structure",
            "Python Conventions",
            "API Conventions"
        ],
        "ai_execution_relevance": "high",
        "ai_reference_type": "continuous"
    },
    
    "COMPREHENSIVE_TESTING_STRATEGY.md": {
        "ai_purpose": "testing_guidance",
        "ai_read_priority": 3,
        "ai_context_level": "tactical",
        "ai_tags": ["testing", "coverage", "tdd", "quality"],
        "ai_when_to_read": "During Phase 3 (TDD Implementation)",
        "ai_key_sections": [
            "Testing Pyramid",
            "Coverage Requirements",
            "Test Types",
            "Implementation Guide"
        ],
        "ai_execution_relevance": "phase-specific",
        "ai_relevant_phases": ["Phase 3"]
    },
    
    "STANDARDIZED_LOGGING_STRATEGY.md": {
        "ai_purpose": "logging_guidance",
        "ai_read_priority": 3,
        "ai_context_level": "tactical",
        "ai_tags": ["logging", "observability", "structured-logging", "log-collector"],
        "ai_when_to_read": "During Phase 3 (TDD Implementation)",
        "ai_key_sections": [
            "Logging Standards",
            "Log Levels",
            "Structured Logging",
            "Log-Collector Integration"
        ],
        "ai_execution_relevance": "phase-specific",
        "ai_relevant_phases": ["Phase 3"]
    },
    
    "SERVICE_DOCUMENTATION_STRATEGY.md": {
        "ai_purpose": "documentation_guidance",
        "ai_read_priority": 3,
        "ai_context_level": "tactical",
        "ai_tags": ["documentation", "readme", "diagrams", "relationships"],
        "ai_when_to_read": "During Phase 5 (Documentation)",
        "ai_key_sections": [
            "README Structure",
            "Visual Documentation",
            "Dependency Documentation",
            "Service Relationships"
        ],
        "ai_execution_relevance": "phase-specific",
        "ai_relevant_phases": ["Phase 5"]
    },
    
    "API_STANDARDIZATION_STRATEGY.md": {
        "ai_purpose": "api_guidance",
        "ai_read_priority": 3,
        "ai_context_level": "tactical",
        "ai_tags": ["api", "rest", "openapi", "swagger", "standard-endpoints"],
        "ai_when_to_read": "During Phase 5 (Documentation)",
        "ai_key_sections": [
            "Standard Endpoints",
            "OpenAPI Requirements",
            "Implementation Guide"
        ],
        "ai_execution_relevance": "phase-specific",
        "ai_relevant_phases": ["Phase 5"]
    },
    
    "SERVICE_AUDIT_TEMPLATE.md": {
        "ai_purpose": "audit_template",
        "ai_read_priority": 4,
        "ai_context_level": "reference",
        "ai_tags": ["audit", "template", "assessment"],
        "ai_when_to_read": "During Phase 1 (Audit & Analysis)",
        "ai_key_sections": [
            "Service Overview",
            "Architecture Assessment",
            "Gap Analysis"
        ],
        "ai_execution_relevance": "phase-specific",
        "ai_relevant_phases": ["Phase 1"]
    },
    
    "TDD_CHECKLIST.md": {
        "ai_purpose": "tdd_checklist",
        "ai_read_priority": 4,
        "ai_context_level": "tactical",
        "ai_tags": ["tdd", "checklist", "red-green-refactor"],
        "ai_when_to_read": "During Phase 3 (TDD Implementation)",
        "ai_key_sections": [
            "RED Phase",
            "GREEN Phase",
            "REFACTOR Phase"
        ],
        "ai_execution_relevance": "phase-specific",
        "ai_relevant_phases": ["Phase 3"]
    }
}


def generate_ai_frontmatter(document_name: str, metadata: Dict) -> str:
    """Generate AI-friendly YAML frontmatter"""
    frontmatter = {
        "ai_metadata": {
            "purpose": metadata.get("ai_purpose"),
            "read_priority": metadata.get("ai_read_priority"),
            "context_level": metadata.get("ai_context_level"),
            "tags": metadata.get("ai_tags", []),
            "when_to_read": metadata.get("ai_when_to_read"),
            "key_sections": metadata.get("ai_key_sections", []),
            "execution_relevance": metadata.get("ai_execution_relevance"),
        }
    }
    
    # Add optional fields
    if "ai_relevant_phases" in metadata:
        frontmatter["ai_metadata"]["relevant_phases"] = metadata["ai_relevant_phases"]
    
    if "ai_update_frequency" in metadata:
        frontmatter["ai_metadata"]["update_frequency"] = metadata["ai_update_frequency"]
    
    if "ai_reference_type" in metadata:
        frontmatter["ai_metadata"]["reference_type"] = metadata["ai_reference_type"]
    
    # Convert to YAML
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    
    return f"---\n{yaml_content}---\n\n"


def add_navigation_markers(content: str, metadata: Dict) -> str:
    """Add AI navigation markers to document"""
    markers = []
    
    # Add "AI_READ_PRIORITY" marker
    priority = metadata.get("ai_read_priority", 5)
    markers.append(f"<!-- AI_READ_PRIORITY: {priority} -->")
    
    # Add "AI_TAGS" marker
    tags = metadata.get("ai_tags", [])
    if tags:
        tags_str = ", ".join(tags)
        markers.append(f"<!-- AI_TAGS: {tags_str} -->")
    
    # Add "AI_KEY_SECTIONS" markers
    key_sections = metadata.get("ai_key_sections", [])
    if key_sections:
        sections_str = ", ".join(key_sections)
        markers.append(f"<!-- AI_KEY_SECTIONS: {sections_str} -->")
    
    # Insert markers at the beginning
    markers_text = "\n".join(markers) + "\n\n"
    
    return markers_text + content


def process_document(doc_path: Path, metadata: Dict):
    """Process a single document"""
    print(f"Processing: {doc_path.name}")
    
    # Read current content
    content = doc_path.read_text()
    
    # Skip if already has AI metadata
    if "ai_metadata:" in content:
        print(f"  ⊙ Already has AI metadata, skipping")
        return
    
    # Remove existing frontmatter if present
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            content = parts[2].strip()
    
    # Generate new content with AI metadata
    frontmatter = generate_ai_frontmatter(doc_path.name, metadata)
    new_content = frontmatter + content
    
    # Add navigation markers
    new_content = add_navigation_markers(new_content, metadata)
    
    # Write back
    doc_path.write_text(new_content)
    print(f"  ✓ Added AI metadata")


def create_ai_navigation_index(docs_dir: Path):
    """Create AI navigation index"""
    index_content = """# AI Agent Navigation Index

This file helps AI agents quickly find the right document for their current task.

## Quick Navigation by Task

### Starting Refactoring
1. Read: [AI_AGENT_EXECUTION_GUIDE.md](./AI_AGENT_EXECUTION_GUIDE.md) (Priority 1)
2. Read: [MASTER_REFACTORING_PLAN.md](./MASTER_REFACTORING_PLAN.md) (Priority 1)
3. Check: [LIVING_PROGRESS_TRACKER.md](./LIVING_PROGRESS_TRACKER.md) (Priority 2)

### During Phase 1 (Audit & Analysis)
- [SERVICE_AUDIT_TEMPLATE.md](./SERVICE_AUDIT_TEMPLATE.md)
- [MASTER_REFACTORING_PLAN.md](./MASTER_REFACTORING_PLAN.md) → "Phase 1: Audit & Analysis"

### During Phase 2 (Design & Planning)
- [NAMING_CONVENTIONS_STANDARDS.md](./NAMING_CONVENTIONS_STANDARDS.md)
- [MASTER_REFACTORING_PLAN.md](./MASTER_REFACTORING_PLAN.md) → "Phase 2: Design & Planning"

### During Phase 3 (TDD Implementation)
- [TDD_CHECKLIST.md](./TDD_CHECKLIST.md)
- [COMPREHENSIVE_TESTING_STRATEGY.md](./COMPREHENSIVE_TESTING_STRATEGY.md)
- [STANDARDIZED_LOGGING_STRATEGY.md](./STANDARDIZED_LOGGING_STRATEGY.md)
- [NAMING_CONVENTIONS_STANDARDS.md](./NAMING_CONVENTIONS_STANDARDS.md)

### During Phase 4 (Integration Testing)
- [WORKFLOW_TESTING_STRATEGY.md](./WORKFLOW_TESTING_STRATEGY.md)
- [API_VERSIONING_STRATEGY.md](./API_VERSIONING_STRATEGY.md)

### During Phase 5 (Documentation)
- [SERVICE_DOCUMENTATION_STRATEGY.md](./SERVICE_DOCUMENTATION_STRATEGY.md)
- [API_STANDARDIZATION_STRATEGY.md](./API_STANDARDIZATION_STRATEGY.md)

### During Phase 6 (Deployment)
- [MASTER_REFACTORING_PLAN.md](./MASTER_REFACTORING_PLAN.md) → "Quality Gates"

## Documents by Priority

### Priority 1 (Read First)
- AI_AGENT_EXECUTION_GUIDE.md
- MASTER_REFACTORING_PLAN.md

### Priority 2 (Read Early)
- LIVING_PROGRESS_TRACKER.md
- NAMING_CONVENTIONS_STANDARDS.md

### Priority 3 (Phase-Specific)
- COMPREHENSIVE_TESTING_STRATEGY.md (Phase 3)
- STANDARDIZED_LOGGING_STRATEGY.md (Phase 3)
- SERVICE_DOCUMENTATION_STRATEGY.md (Phase 5)
- API_STANDARDIZATION_STRATEGY.md (Phase 5)

### Priority 4 (Reference)
- SERVICE_AUDIT_TEMPLATE.md
- TDD_CHECKLIST.md
- WORKFLOW_TESTING_STRATEGY.md

## AI Agent Tips

1. **Always start** with AI_AGENT_EXECUTION_GUIDE.md
2. **Load context** from .ai_execution/context.json
3. **Check current phase** and read phase-specific docs
4. **Update context** every 30 minutes
5. **Stay in scope** - don't modify other services
6. **Follow TDD** - Red → Green → Refactor
7. **Validate often** - run checks after each step

## Metadata Explanation

Each document has AI metadata in YAML frontmatter:

```yaml
ai_metadata:
  purpose: "what this document is for"
  read_priority: 1-5 (1 = highest priority)
  context_level: strategic|tactical|operational|reference
  tags: [list, of, relevant, tags]
  when_to_read: "when AI agent should read this"
  key_sections: [list, of, important, sections]
  execution_relevance: critical|high|phase-specific|reference
```

Use these metadata to:
- Determine reading order
- Understand document purpose
- Navigate to relevant sections
- Know when to reference

---

**For AI Agents**: This index is your starting point for navigation.
"""
    
    index_path = docs_dir / "AI_NAVIGATION_INDEX.md"
    index_path.write_text(index_content)
    print(f"\n✓ Created AI navigation index: {index_path}")


def main():
    """Main entry point"""
    # Determine repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    docs_dir = repo_root / "docs" / "refactoring"
    
    print("\n🤖 Adding AI Metadata to Refactoring Documents\n")
    
    # Process each document
    processed_count = 0
    for doc_name, metadata in DOCUMENT_METADATA.items():
        doc_path = docs_dir / doc_name
        if doc_path.exists():
            process_document(doc_path, metadata)
            processed_count += 1
        else:
            print(f"⚠️ Document not found: {doc_name}")
    
    # Create AI navigation index
    create_ai_navigation_index(docs_dir)
    
    print(f"\n📊 Summary:")
    print(f"   Processed: {processed_count} documents")
    print(f"   Index: AI_NAVIGATION_INDEX.md created")
    print(f"\n✓ AI metadata added successfully!")
    
    print(f"\n📝 AI agents can now:")
    print(f"   - Navigate documents by priority")
    print(f"   - Understand document purpose")
    print(f"   - Know when to read each document")
    print(f"   - Find key sections quickly")


if __name__ == "__main__":
    main()

