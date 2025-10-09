#!/usr/bin/env python3
"""
Service Documentation Enrichment Script

Adds AI-friendly metadata and navigation to service documentation for optimal
AI agent discoverability and context understanding.

Usage:
    python3 scripts/refactoring/enrich_service_documentation.py <service-name>

Example:
    python3 scripts/refactoring/enrich_service_documentation.py doc-store

Features:
- Adds YAML frontmatter with AI metadata
- Adds semantic section tags
- Adds navigation markers
- Adds cross-references to related docs
- Generates AI-optimized index
- Adds embeddings hints

Author: Hackathon Team
Version: 1.0.0
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import re


class DocumentationEnricher:
    """Enriches service documentation with AI-friendly metadata"""
    
    def __init__(self, service_name: str, project_root: Path):
        self.service_name = service_name
        self.project_root = project_root
        self.service_path = project_root / "services" / service_name
        self.readme_path = self.service_path / "README.md"
        
    def enrich(self) -> dict:
        """Main enrichment process"""
        results = {
            "service": self.service_name,
            "timestamp": datetime.utcnow().isoformat(),
            "enrichments": []
        }
        
        # 1. Check README exists
        if not self.readme_path.exists():
            return {
                **results,
                "success": False,
                "error": f"README not found at {self.readme_path}"
            }
        
        # 2. Read existing content
        content = self.readme_path.read_text()
        
        # 3. Add YAML frontmatter
        content, frontmatter_added = self._add_yaml_frontmatter(content)
        if frontmatter_added:
            results["enrichments"].append("yaml_frontmatter")
        
        # 4. Add semantic section tags
        content, sections_tagged = self._add_section_tags(content)
        results["enrichments"].append(f"tagged_{sections_tagged}_sections")
        
        # 5. Add navigation markers
        content, nav_markers = self._add_navigation_markers(content)
        results["enrichments"].append(f"added_{nav_markers}_nav_markers")
        
        # 6. Add cross-references
        content, xrefs = self._add_cross_references(content)
        results["enrichments"].append(f"added_{xrefs}_cross_references")
        
        # 7. Add AI hints
        content = self._add_ai_hints(content)
        results["enrichments"].append("ai_hints")
        
        # 8. Write enriched content
        self.readme_path.write_text(content)
        
        # 9. Generate AI index
        index_created = self._generate_ai_index(content)
        if index_created:
            results["enrichments"].append("ai_index")
        
        results["success"] = True
        results["readme_path"] = str(self.readme_path)
        
        return results
    
    def _add_yaml_frontmatter(self, content: str) -> tuple[str, bool]:
        """Add YAML frontmatter if not present"""
        
        # Check if frontmatter already exists
        if content.startswith("---\n"):
            return content, False
        
        # Generate frontmatter
        frontmatter = f"""---
# AI Agent Metadata
service_name: {self.service_name}
document_type: service_readme
priority: high
context_level: service
ai_tags:
  - service-documentation
  - {self.service_name}
  - architecture
  - api-reference
  - dependencies
semantic_hints:
  purpose: "Comprehensive service documentation"
  audience: ["developers", "ai-agents", "architects"]
  use_cases:
    - "Understanding service capabilities"
    - "Integration planning"
    - "Troubleshooting"
last_enriched: {datetime.utcnow().isoformat()}
---

"""
        
        return frontmatter + content, True
    
    def _add_section_tags(self, content: str) -> tuple[str, int]:
        """Add semantic tags to major sections"""
        
        sections_tagged = 0
        
        # Define section patterns and their semantic tags
        section_patterns = {
            r"^##\s+Overview": "<!-- @ai-section: overview -->",
            r"^##\s+Architecture": "<!-- @ai-section: architecture -->",
            r"^##\s+Features": "<!-- @ai-section: features -->",
            r"^##\s+API\s+Endpoints": "<!-- @ai-section: api-endpoints -->",
            r"^##\s+Dependencies": "<!-- @ai-section: dependencies -->",
            r"^##\s+Service\s+Relationships": "<!-- @ai-section: relationships -->",
            r"^##\s+Quick\s+Start": "<!-- @ai-section: quick-start -->",
            r"^##\s+Configuration": "<!-- @ai-section: configuration -->",
            r"^##\s+Testing": "<!-- @ai-section: testing -->",
            r"^##\s+Deployment": "<!-- @ai-section: deployment -->",
            r"^##\s+Troubleshooting": "<!-- @ai-section: troubleshooting -->",
        }
        
        lines = content.split("\n")
        new_lines = []
        
        for line in lines:
            new_lines.append(line)
            
            # Check if line matches any section pattern
            for pattern, tag in section_patterns.items():
                if re.match(pattern, line, re.IGNORECASE):
                    # Only add tag if not already present
                    if tag not in content:
                        new_lines.append(tag)
                        sections_tagged += 1
                    break
        
        return "\n".join(new_lines), sections_tagged
    
    def _add_navigation_markers(self, content: str) -> tuple[str, int]:
        """Add navigation markers for AI agents"""
        
        markers_added = 0
        
        # Add markers at strategic locations
        navigation_markers = {
            "<!-- @ai-nav: start-of-document -->": 0,  # After frontmatter
            "<!-- @ai-nav: architecture-section -->": None,  # Before architecture
            "<!-- @ai-nav: api-section -->": None,  # Before API section
            "<!-- @ai-nav: end-of-document -->": -1,  # At end
        }
        
        lines = content.split("\n")
        
        # Find frontmatter end
        frontmatter_end = 0
        if lines[0].startswith("---"):
            for i, line in enumerate(lines[1:], 1):
                if line.startswith("---"):
                    frontmatter_end = i + 1
                    break
        
        # Insert start marker after frontmatter
        if "<!-- @ai-nav: start-of-document -->" not in content:
            lines.insert(frontmatter_end, "<!-- @ai-nav: start-of-document -->")
            lines.insert(frontmatter_end + 1, "")
            markers_added += 1
        
        # Insert end marker
        if "<!-- @ai-nav: end-of-document -->" not in content:
            lines.append("")
            lines.append("<!-- @ai-nav: end-of-document -->")
            markers_added += 1
        
        return "\n".join(lines), markers_added
    
    def _add_cross_references(self, content: str) -> tuple[str, int]:
        """Add cross-references to related documentation"""
        
        xrefs_added = 0
        
        # Generate cross-reference section
        xref_section = """

---

## 📚 Related Documentation

<!-- @ai-section: cross-references -->

**For AI Agents**: These documents provide additional context about this service.

### Refactoring Documentation
- [Master Refactoring Plan](../../docs/refactoring/MASTER_REFACTORING_PLAN.md) - Overall refactoring strategy
- [Service Documentation Strategy](../../docs/refactoring/SERVICE_DOCUMENTATION_STRATEGY.md) - Documentation standards
- [API Standardization Strategy](../../docs/refactoring/API_STANDARDIZATION_STRATEGY.md) - API guidelines
- [Comprehensive Testing Strategy](../../docs/refactoring/COMPREHENSIVE_TESTING_STRATEGY.md) - Testing requirements
- [Standardized Logging Strategy](../../docs/refactoring/STANDARDIZED_LOGGING_STRATEGY.md) - Logging standards

### Execution Guides
- [AI Agent Execution Guide](../../docs/refactoring/AI_AGENT_EXECUTION_GUIDE.md) - How to execute refactoring
- [Session Recovery Protocol](../../docs/refactoring/SESSION_RECOVERY_PROTOCOL.md) - Recovery from interruptions
- [AI Self-Review Checklist](../../docs/refactoring/AI_SELF_REVIEW_CHECKLIST.md) - Quality validation

### Service-Specific
- [Audit Report](./audit_report.json) - Service audit results
- [Domain Model](./design/domain_model.md) - Domain design (if exists)
- [API Specification](./design/openapi_v2.yaml) - OpenAPI spec (if exists)
- [Test Plan](./design/test_plan.md) - Testing strategy (if exists)

---
"""
        
        # Check if cross-references already exist
        if "## 📚 Related Documentation" not in content and \
           "## Related Documentation" not in content:
            content += xref_section
            xrefs_added = 1
        
        return content, xrefs_added
    
    def _add_ai_hints(self, content: str) -> str:
        """Add AI processing hints"""
        
        # Add hints at the end (before end-of-document marker if present)
        ai_hints = """

---

<!-- @ai-hints: processing-instructions -->
<!--
AI Agent Processing Hints:

1. **Context Priority**: This is a HIGH priority document for understanding the service
2. **Read Order**: Overview → Architecture → API Endpoints → Dependencies
3. **Key Sections**: Architecture and API Endpoints contain the most critical information
4. **Integration Context**: Service Relationships section shows how this fits in ecosystem
5. **Quick Start**: Use Quick Start section for understanding basic usage
6. **Troubleshooting**: Common issues and solutions in Troubleshooting section

Semantic Tags for Embedding:
- #service-documentation
- #architecture-diagram
- #api-specification
- #dependency-mapping
- #integration-guide
-->

"""
        
        # Insert before end-of-document marker if present
        if "<!-- @ai-nav: end-of-document -->" in content:
            content = content.replace(
                "<!-- @ai-nav: end-of-document -->",
                ai_hints + "<!-- @ai-nav: end-of-document -->"
            )
        else:
            content += ai_hints
        
        return content
    
    def _generate_ai_index(self, content: str) -> bool:
        """Generate AI-optimized index file"""
        
        index_path = self.service_path / ".ai-index.json"
        
        # Extract sections
        sections = []
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            # Match ## headers
            if re.match(r"^##\s+", line):
                title = re.sub(r"^##\s+", "", line).strip()
                
                # Find semantic tag if exists
                tag = None
                if i + 1 < len(lines):
                    tag_match = re.search(r"<!-- @ai-section: ([\w-]+) -->", lines[i + 1])
                    if tag_match:
                        tag = tag_match.group(1)
                
                sections.append({
                    "title": title,
                    "line": i + 1,
                    "semantic_tag": tag
                })
        
        # Extract API endpoints if present
        endpoints = []
        endpoint_pattern = r"`(GET|POST|PUT|DELETE|PATCH)\s+(/[\w/-]+)`"
        for match in re.finditer(endpoint_pattern, content):
            method, path = match.groups()
            endpoints.append({"method": method, "path": path})
        
        # Generate index
        index = {
            "service": self.service_name,
            "document": "README.md",
            "generated_at": datetime.utcnow().isoformat(),
            "sections": sections,
            "endpoints": endpoints,
            "ai_hints": {
                "primary_purpose": "service_documentation",
                "context_level": "service",
                "recommended_read_order": [s["semantic_tag"] for s in sections if s["semantic_tag"]],
                "key_sections": ["overview", "architecture", "api-endpoints", "dependencies"]
            }
        }
        
        # Write index
        index_path.write_text(json.dumps(index, indent=2))
        
        return True


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Enrich service documentation with AI-friendly metadata"
    )
    parser.add_argument(
        "service",
        help="Service name (e.g., doc-store)"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory (default: current directory)"
    )
    
    args = parser.parse_args()
    
    # Validate service exists
    service_path = args.project_root / "services" / args.service
    if not service_path.exists():
        print(f"❌ Error: Service '{args.service}' not found at {service_path}")
        sys.exit(1)
    
    print(f"🔧 Enriching documentation for service: {args.service}")
    print()
    
    # Create enricher
    enricher = DocumentationEnricher(args.service, args.project_root)
    
    # Enrich documentation
    try:
        results = enricher.enrich()
        
        if results["success"]:
            print("✅ Documentation enrichment complete!")
            print()
            print(f"📄 Enriched: {results['readme_path']}")
            print()
            print("🎯 Enrichments added:")
            for enrichment in results["enrichments"]:
                print(f"  ✓ {enrichment}")
            print()
            print("💡 AI agents can now:")
            print("  • Quickly discover this service documentation")
            print("  • Navigate efficiently with semantic tags")
            print("  • Understand context and relationships")
            print("  • Find relevant sections faster")
            print()
            
            # Output JSON for automation
            print(json.dumps(results, indent=2))
            
            sys.exit(0)
        else:
            print(f"❌ Enrichment failed: {results['error']}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error during enrichment: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

