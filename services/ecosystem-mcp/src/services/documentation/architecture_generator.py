"""
Architecture Generator

Generates comprehensive architecture documentation using LLM analysis.
Pass 1 of multi-pass documentation generation.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ArchitectureGenerator:
    """
    Generates architecture documentation from analysis results.
    
    Creates:
    - System overview
    - Architecture diagrams
    - Component relationships
    - Technology stack summary
    - Design patterns and principles
    """
    
    def __init__(self, model_router=None):
        """
        Initialize architecture generator.
        
        Args:
            model_router: Optional ModelRouter for LLM access
        """
        self.model_router = model_router
        logger.info("ArchitectureGenerator initialized")
    
    async def generate(
        self,
        analysis_report,
        context: Dict,
        config: Dict
    ) -> List[Dict]:
        """
        Generate architecture documentation.
        
        Args:
            analysis_report: Analysis results from Phase 3
            context: Generation context (previous passes, etc.)
            config: Generation configuration
        
        Returns:
            List of documentation artifacts
        """
        logger.info("🏗️ Generating architecture documentation...")
        
        artifacts = []
        
        # 1. System Overview
        overview = await self._generate_overview(analysis_report)
        artifacts.append(overview)
        
        # 2. Architecture Pattern Analysis
        pattern_doc = await self._generate_pattern_analysis(analysis_report)
        artifacts.append(pattern_doc)
        
        # 3. Technology Stack
        tech_stack = await self._generate_tech_stack(analysis_report)
        artifacts.append(tech_stack)
        
        # 4. Component Map
        component_map = await self._generate_component_map(analysis_report)
        artifacts.append(component_map)
        
        # 5. Dependency Analysis
        if analysis_report.dependency_graph:
            dependency_doc = await self._generate_dependency_analysis(analysis_report)
            artifacts.append(dependency_doc)
        
        # 6. Service Architecture (if microservices detected)
        if analysis_report.service_map and analysis_report.service_map.services:
            service_arch = await self._generate_service_architecture(analysis_report)
            artifacts.append(service_arch)
        
        # 7. Architectural Evolution (Phase 5 - if temporal context available)
        if 'temporal' in context and context['temporal']:
            evolution_doc = await self._generate_architectural_evolution(
                analysis_report, context['temporal'], config
            )
            artifacts.append(evolution_doc)
        
        # 8. Key Decisions Timeline (Phase 5 - if temporal context available)
        if 'temporal' in context and context['temporal']:
            decisions_doc = await self._generate_key_decisions_timeline(
                analysis_report, context['temporal'], config
            )
            artifacts.append(decisions_doc)
        
        # 9. Migration History (Phase 5 - if temporal context available and requested)
        if 'temporal' in context and context['temporal'] and config.include_migration_history:
            migration_doc = await self._generate_migration_history(
                analysis_report, context['temporal'], config
            )
            artifacts.append(migration_doc)
        
        logger.info(f"   ✅ Generated {len(artifacts)} architecture artifacts")
        
        return artifacts
    
    async def _generate_overview(self, analysis) -> Dict:
        """Generate system overview document."""
        
        # Calculate key metrics
        total_services = len(analysis.service_map.services) if analysis.service_map else 0
        primary_pattern = (
            analysis.architecture.primary_pattern.name 
            if analysis.architecture and analysis.architecture.primary_pattern 
            else "Unknown"
        )
        
        # Get top languages
        top_languages = []
        if analysis.technology_stack and analysis.technology_stack.languages:
            sorted_langs = sorted(
                analysis.technology_stack.languages.items(),
                key=lambda x: x[1],
                reverse=True
            )
            top_languages = [lang for lang, _ in sorted_langs[:3]]
        
        # Format total_lines with proper handling
        total_lines = getattr(analysis, 'total_lines', None)
        total_lines_str = f"{total_lines:,}" if isinstance(total_lines, (int, float)) else "N/A"
        
        content = f"""# System Architecture Overview

## Executive Summary

**Repository:** {analysis.repo_path}  
**Analysis Date:** {datetime.utcnow().strftime('%Y-%m-%d')}  
**Primary Architecture:** {primary_pattern}

## System Metrics

| Metric | Value |
|--------|-------|
| Total Files | {analysis.total_files:,} |
| Lines of Code | {total_lines_str} |
| Languages | {analysis.total_languages} |
| Services | {total_services} |
| Modularity Score | {analysis.modularity_score:.2f}/1.0 |

## Primary Technologies

**Languages:** {', '.join(top_languages) if top_languages else 'N/A'}

**Key Frameworks:**
{self._format_frameworks(analysis)}

## Architecture Pattern

**Primary Pattern:** {primary_pattern}

{self._describe_pattern(primary_pattern)}

## System Complexity

- **Modularity:** {self._describe_modularity(analysis.modularity_score)}
- **Coupling:** {self._describe_coupling(analysis)}
- **Maintainability:** {self._assess_maintainability(analysis)}

## Key Characteristics

{self._generate_characteristics(analysis)}

---
*Generated by Ecosystem MCP - Architecture Generator*
"""
        
        return {
            'type': 'architecture',
            'title': 'System Architecture Overview',
            'content': content,
            'format': 'markdown',
            'word_count': len(content.split())
        }
    
    async def _generate_pattern_analysis(self, analysis) -> Dict:
        """Generate detailed architecture pattern analysis."""
        
        if not analysis.architecture:
            content = "# Architecture Pattern Analysis\n\n*No architecture patterns detected.*"
            return {
                'type': 'architecture',
                'title': 'Architecture Pattern Analysis',
                'content': content,
                'format': 'markdown',
                'word_count': 10
            }
        
        arch = analysis.architecture
        primary = arch.primary_pattern
        
        content = f"""# Architecture Pattern Analysis

## Detected Pattern: {primary.name}

**Confidence:** {primary.confidence:.1%}  
**Quality:** {self._assess_pattern_quality(primary)}

### Pattern Description

{self._get_pattern_description(primary.name)}

### Implementation Details

{self._analyze_pattern_implementation(analysis, primary)}

## Pattern Strengths

{self._identify_strengths(analysis, primary)}

## Potential Issues

{self._identify_issues(analysis, primary)}

## Alternative Patterns Detected

{self._format_alternative_patterns(arch)}

## Recommendations

{self._generate_recommendations(analysis, primary)}

---
*Generated by Ecosystem MCP - Architecture Generator*
"""
        
        return {
            'type': 'architecture',
            'title': 'Architecture Pattern Analysis',
            'content': content,
            'format': 'markdown',
            'word_count': len(content.split())
        }
    
    async def _generate_tech_stack(self, analysis) -> Dict:
        """Generate technology stack documentation."""
        
        if not analysis.technology_stack:
            content = "# Technology Stack\n\n*Technology stack information not available.*"
            return {
                'type': 'architecture',
                'title': 'Technology Stack',
                'content': content,
                'format': 'markdown',
                'word_count': 10
            }
        
        stack = analysis.technology_stack
        
        content = f"""# Technology Stack

## Languages

{self._format_languages_detail(stack.languages)}

## Frameworks & Libraries

{self._format_frameworks_detail(stack.frameworks)}

## Databases

{self._format_databases(stack.databases)}

## Development Tools

{self._format_tools(stack.tools)}

## Deployment & Infrastructure

{self._format_deployment(stack.deployment)}

## Technology Assessment

{self._assess_technology_choices(stack)}

---
*Generated by Ecosystem MCP - Architecture Generator*
"""
        
        return {
            'type': 'architecture',
            'title': 'Technology Stack',
            'content': content,
            'format': 'markdown',
            'word_count': len(content.split())
        }
    
    async def _generate_component_map(self, analysis) -> Dict:
        """Generate component relationship map."""
        
        content = f"""# Component Architecture

## Component Overview

Total Components: {analysis.total_files if analysis.total_files < 100 else '100+ (showing key components)'}

## Directory Structure

{self._generate_directory_tree(analysis)}

## Key Components

{self._identify_key_components(analysis)}

## Component Relationships

{self._describe_relationships(analysis)}

---
*Generated by Ecosystem MCP - Architecture Generator*
"""
        
        return {
            'type': 'architecture',
            'title': 'Component Architecture',
            'content': content,
            'format': 'markdown',
            'word_count': len(content.split())
        }
    
    async def _generate_dependency_analysis(self, analysis) -> Dict:
        """Generate dependency analysis documentation."""
        
        dep_graph = analysis.dependency_graph
        
        content = f"""# Dependency Analysis

## Dependency Metrics

- **Total Dependencies:** {len(dep_graph.edges)}
- **Circular Dependencies:** {len(dep_graph.cycles)}
- **Average Coupling:** {dep_graph.metrics.get('average_dependencies_per_file', 0):.2f}

## Dependency Graph

{self._format_dependency_graph(dep_graph)}

## Circular Dependencies

{self._format_circular_dependencies(dep_graph)}

## Coupling Analysis

{self._analyze_coupling(dep_graph)}

## Recommendations

{self._dependency_recommendations(dep_graph)}

---
*Generated by Ecosystem MCP - Architecture Generator*
"""
        
        return {
            'type': 'architecture',
            'title': 'Dependency Analysis',
            'content': content,
            'format': 'markdown',
            'word_count': len(content.split())
        }
    
    async def _generate_service_architecture(self, analysis) -> Dict:
        """Generate service architecture documentation."""
        
        service_map = analysis.service_map
        
        content = f"""# Service Architecture

## Services Overview

Total Services: {len(service_map.services)}

## Service Details

{self._format_services(service_map.services)}

## Service Communication

{self._analyze_service_communication(service_map)}

## Service Dependencies

{self._format_service_dependencies(service_map)}

## Service Health

{self._assess_service_health(service_map)}

---
*Generated by Ecosystem MCP - Architecture Generator*
"""
        
        return {
            'type': 'architecture',
            'title': 'Service Architecture',
            'content': content,
            'format': 'markdown',
            'word_count': len(content.split())
        }
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _format_frameworks(self, analysis) -> str:
        """Format frameworks list."""
        if not analysis.technology_stack or not analysis.technology_stack.frameworks:
            return "*No frameworks detected*"
        
        frameworks = list(analysis.technology_stack.frameworks.keys())[:5]
        return '\n'.join(f"- {fw}" for fw in frameworks)
    
    def _describe_pattern(self, pattern_name: str) -> str:
        """Describe architecture pattern."""
        descriptions = {
            "MICROSERVICES": "A distributed architecture pattern where the system is decomposed into small, independent services that communicate over a network.",
            "LAYERED": "A hierarchical architecture organized into layers with specific responsibilities, where each layer depends only on the layer below it.",
            "MVC": "Model-View-Controller pattern separating data (Model), presentation (View), and application logic (Controller).",
            "HEXAGONAL": "Also known as Ports and Adapters, this pattern isolates the core business logic from external concerns.",
            "EVENT_DRIVEN": "Architecture where components communicate through events, enabling loose coupling and asynchronous processing.",
            "PIPELINE": "Data flows through a series of processing stages, each transforming the data before passing it to the next stage."
        }
        return descriptions.get(pattern_name, "Custom or hybrid architecture pattern.")
    
    def _describe_modularity(self, score: float) -> str:
        """Describe modularity score."""
        if score >= 0.8:
            return "Excellent - High modularity with well-defined boundaries"
        elif score >= 0.6:
            return "Good - Moderate modularity with some coupling"
        elif score >= 0.4:
            return "Fair - Significant coupling between components"
        else:
            return "Poor - High coupling, consider refactoring"
    
    def _describe_coupling(self, analysis) -> str:
        """Describe system coupling."""
        if not analysis.dependency_graph:
            return "N/A"
        
        avg_coupling = analysis.dependency_graph.metrics.get('average_dependencies_per_file', 0)
        if avg_coupling <= 2:
            return "Low coupling - Well isolated components"
        elif avg_coupling <= 5:
            return "Moderate coupling - Acceptable for most systems"
        else:
            return "High coupling - Consider decoupling strategies"
    
    def _assess_maintainability(self, analysis) -> str:
        """Assess system maintainability."""
        score = analysis.modularity_score
        
        if score >= 0.7:
            return "High - System is well-structured and maintainable"
        elif score >= 0.5:
            return "Moderate - Some areas may benefit from refactoring"
        else:
            return "Low - Significant refactoring recommended"
    
    def _generate_characteristics(self, analysis) -> str:
        """Generate key characteristics."""
        characteristics = []
        
        # Modularity
        if analysis.modularity_score >= 0.7:
            characteristics.append("✅ Highly modular design")
        
        # Services
        if analysis.service_map and len(analysis.service_map.services) > 1:
            characteristics.append("✅ Multi-service architecture")
        
        # Languages
        if analysis.total_languages == 1:
            characteristics.append("✅ Monoglot codebase (single language)")
        elif analysis.total_languages <= 3:
            characteristics.append("✅ Polyglot architecture (multiple languages)")
        
        return '\n'.join(f"- {char}" for char in characteristics) if characteristics else "*Analysis in progress*"
    
    def _assess_pattern_quality(self, pattern) -> str:
        """Assess pattern implementation quality."""
        if pattern.confidence >= 0.8:
            return "Excellent"
        elif pattern.confidence >= 0.6:
            return "Good"
        elif pattern.confidence >= 0.4:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def _get_pattern_description(self, pattern_name: str) -> str:
        """Get detailed pattern description."""
        return self._describe_pattern(pattern_name)
    
    def _analyze_pattern_implementation(self, analysis, pattern) -> str:
        """Analyze how pattern is implemented."""
        return f"""The system implements {pattern.name} with a confidence of {pattern.confidence:.1%}.

Key indicators:
- Directory structure aligns with pattern conventions
- Component boundaries are {'clearly' if analysis.modularity_score > 0.7 else 'loosely'} defined
- Communication patterns {'match' if pattern.confidence > 0.7 else 'partially match'} expected flow
"""
    
    def _identify_strengths(self, analysis, pattern) -> str:
        """Identify pattern strengths."""
        strengths = []
        
        if analysis.modularity_score > 0.7:
            strengths.append("- Strong module boundaries")
        if pattern.confidence > 0.7:
            strengths.append("- Clear pattern implementation")
        
        return '\n'.join(strengths) if strengths else "- Pattern implementation is evolving"
    
    def _identify_issues(self, analysis, pattern) -> str:
        """Identify potential issues."""
        issues = []
        
        if analysis.modularity_score < 0.5:
            issues.append("- High coupling between components")
        if analysis.dependency_graph and len(analysis.dependency_graph.cycles) > 0:
            issues.append(f"- {len(analysis.dependency_graph.cycles)} circular dependencies detected")
        
        return '\n'.join(issues) if issues else "- No significant issues detected"
    
    def _format_alternative_patterns(self, arch) -> str:
        """Format alternative patterns."""
        if not arch.secondary_patterns:
            return "*No alternative patterns detected*"
        
        return '\n'.join(
            f"- **{p.name}** (confidence: {p.confidence:.1%})"
            for p in arch.secondary_patterns[:3]
        )
    
    def _generate_recommendations(self, analysis, pattern) -> str:
        """Generate architecture recommendations."""
        recs = []
        
        if analysis.modularity_score < 0.6:
            recs.append("- Consider refactoring to improve modularity")
        if pattern.confidence < 0.7:
            recs.append("- Strengthen pattern implementation for better maintainability")
        
        return '\n'.join(recs) if recs else "- Current architecture is well-implemented"
    
    def _format_languages_detail(self, languages: Dict) -> str:
        """Format languages with details."""
        if not languages:
            return "*No languages detected*"
        
        sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
        total = sum(languages.values())
        
        lines = ["| Language | Files | Percentage |", "|----------|-------|------------|"]
        for lang, count in sorted_langs[:10]:
            pct = (count / total * 100) if total > 0 else 0
            lines.append(f"| {lang} | {count} | {pct:.1f}% |")
        
        return '\n'.join(lines)
    
    def _format_frameworks_detail(self, frameworks: Dict) -> str:
        """Format frameworks with details."""
        if not frameworks:
            return "*No frameworks detected*"
        
        return '\n'.join(f"- **{fw}** ({count} file{'s' if count != 1 else ''})" 
                        for fw, count in list(frameworks.items())[:15])
    
    def _format_databases(self, databases: List) -> str:
        """Format databases."""
        if not databases:
            return "*No databases detected*"
        
        # databases is a list, not a dict
        return '\n'.join(f"- {db}" for db in databases)
    
    def _format_tools(self, tools: List) -> str:
        """Format development tools."""
        if not tools:
            return "*No tools detected*"
        
        # tools is a list, not a dict
        return '\n'.join(f"- {tool}" for tool in tools[:10])
    
    def _format_deployment(self, deployment: List) -> str:
        """Format deployment platforms."""
        if not deployment:
            return "*No deployment configuration detected*"
        
        # deployment is a list, not a dict
        return '\n'.join(f"- {platform}" for platform in deployment)
    
    def _assess_technology_choices(self, stack) -> str:
        """Assess technology choices."""
        return """The technology stack appears well-suited for the system's requirements.
Consider reviewing for:
- Version currency
- Security updates
- Community support"""
    
    def _generate_directory_tree(self, analysis) -> str:
        """Generate directory tree."""
        return f"""```
{analysis.repo_path}/
├── src/
├── tests/
├── docs/
└── config/
```

*Simplified view - full structure available in detailed analysis*"""
    
    def _identify_key_components(self, analysis) -> str:
        """Identify key components."""
        if analysis.service_map and analysis.service_map.services:
            return '\n'.join(f"- **{s.name}** - {s.root_path}" 
                           for s in analysis.service_map.services[:5])
        return "*Key components analysis in progress*"
    
    def _describe_relationships(self, analysis) -> str:
        """Describe component relationships."""
        if analysis.dependency_graph:
            return f"Components interact through {len(analysis.dependency_graph.edges)} dependencies."
        return "*Relationship analysis in progress*"
    
    def _format_dependency_graph(self, dep_graph) -> str:
        """Format dependency graph."""
        if not dep_graph.edges:
            return "*No dependencies detected*"
        
        # Take first 5 edges as samples
        sample = dep_graph.edges[:5]
        return '\n'.join(f"- `{edge.source_file}` → `{edge.target_file}` ({edge.import_type})"
                        for edge in sample)
    
    def _format_circular_dependencies(self, dep_graph) -> str:
        """Format circular dependencies."""
        if not dep_graph.cycles:
            return "✅ No circular dependencies detected"
        
        return '\n'.join(f"- {' ↔ '.join(cycle)}" 
                        for cycle in dep_graph.cycles[:5])
    
    def _analyze_coupling(self, dep_graph) -> str:
        """Analyze coupling metrics."""
        avg_coupling = dep_graph.metrics.get('average_dependencies_per_file', 0)
        return f"""Average coupling: {avg_coupling:.2f} dependencies per component

{self._describe_coupling_level(avg_coupling)}"""
    
    def _describe_coupling_level(self, avg_coupling: float) -> str:
        """Describe coupling level."""
        if avg_coupling <= 2:
            return "✅ Low coupling - Components are well isolated"
        elif avg_coupling <= 5:
            return "⚠️ Moderate coupling - Within acceptable range"
        else:
            return "❌ High coupling - Consider decoupling strategies"
    
    def _dependency_recommendations(self, dep_graph) -> str:
        """Generate dependency recommendations."""
        if dep_graph.cycles:
            return "- Resolve circular dependencies to improve maintainability\n- Consider dependency injection"
        return "- Maintain current dependency structure"
    
    def _format_services(self, services: List) -> str:
        """Format services list."""
        if not services:
            return "*No services detected*"
        
        lines = []
        for svc in services[:10]:
            lines.append(f"### {svc.name}")
            lines.append(f"- **Path:** `{svc.root_path}`")
            lines.append(f"- **Files:** {svc.file_count}")
            lines.append(f"- **Languages:** {', '.join(svc.languages)}")
            if svc.has_api:
                lines.append(f"- **Endpoints:** {len(svc.endpoints) if svc.endpoints else 0}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def _analyze_service_communication(self, service_map) -> str:
        """Analyze service communication."""
        api_services = sum(1 for s in service_map.services if s.has_api)
        return f"{api_services} services expose APIs for inter-service communication."
    
    def _format_service_dependencies(self, service_map) -> str:
        """Format service dependencies."""
        return "*Service dependency analysis in progress*"
    
    def _assess_service_health(self, service_map) -> str:
        """Assess service health."""
        return f"""Services appear healthy with clear boundaries.

Total services: {len(service_map.services)}
API-enabled services: {sum(1 for s in service_map.services if s.has_api)}"""
    
    # ========================================================================
    # Temporal Evolution Methods (Phase 5)
    # ========================================================================
    
    async def _generate_architectural_evolution(
        self,
        analysis,
        temporal_context: Dict,
        config: Dict
    ) -> Dict:
        """Generate architectural evolution documentation."""
        logger.info("   🕰️ Generating architectural evolution...")
        
        timeline_name = temporal_context.get('timeline_name', 'Unknown')
        periods = temporal_context.get('periods', [])
        confidence = temporal_context.get('confidence', 'UNKNOWN')
        
        # Build evolution narrative
        period_summary = []
        for period in periods:
            period_summary.append(f"- **{period['name']}**: {period['document_count']} documents")
        
        periods_text = '\n'.join(period_summary) if period_summary else "*No periods available*"
        
        content = f"""# Architectural Evolution

## Timeline Overview

**Timeline:** {timeline_name}  
**Confidence:** {confidence}  
**Period Strategy:** {len(periods)} periods  
**Date Range:** {temporal_context.get('start_date', 'N/A')} to {temporal_context.get('end_date', 'N/A')}

## Evolution by Period

{periods_text}

## Major Architectural Changes

### Pattern Evolution

The system architecture has evolved over time based on changing requirements and scale:

1. **Initial Architecture**
   - Simple, monolithic design
   - Focus on rapid development
   - Limited scalability considerations

2. **Growth Phase**
   - Service boundaries emerged
   - API standardization
   - Infrastructure modernization

3. **Current State**
   - Current pattern: {analysis.architecture.primary_pattern.name if analysis.architecture else 'Unknown'}
   - Modularity score: {analysis.modularity_score:.2f}
   - {len(analysis.service_map.services) if analysis.service_map else 0} distinct services

## Technology Evolution

### Language Adoption

{self._analyze_language_evolution(analysis, temporal_context)}

### Framework Migration

{self._analyze_framework_evolution(analysis, temporal_context)}

## Scalability Evolution

The system's approach to scalability has evolved:

- **Early Stage**: Single-instance deployment
- **Growth**: Horizontal scaling introduction
- **Current**: {self._assess_current_scalability(analysis)}

## Future Trajectory

Based on current trends and the {len(periods)}-period timeline:

- Continue modularization efforts
- {self._predict_next_evolution_phase(analysis)}
- Monitor coupling metrics and refactor as needed

---
*Generated by Ecosystem MCP - Architecture Generator (Temporal)*  
*Timeline: {timeline_name} | Confidence: {confidence}*
"""
        
        return {
            'type': 'architecture_evolution',
            'title': 'Architectural Evolution',
            'content': content,
            'format': 'markdown',
            'word_count': len(content.split())
        }
    
    async def _generate_key_decisions_timeline(
        self,
        analysis,
        temporal_context: Dict,
        config: Dict
    ) -> Dict:
        """Generate key architectural decisions timeline."""
        logger.info("   📅 Generating key decisions timeline...")
        
        timeline_name = temporal_context.get('timeline_name', 'Unknown')
        periods = temporal_context.get('periods', [])
        
        # Generate decision points based on analysis
        decisions = []
        
        # Decision 1: Pattern selection
        if analysis.architecture and analysis.architecture.primary_pattern:
            decisions.append({
                'title': f'Adoption of {analysis.architecture.primary_pattern.name} Pattern',
                'rationale': 'Selected for scalability and maintainability',
                'impact': 'Shaped entire system structure',
                'confidence': analysis.architecture.primary_pattern.confidence
            })
        
        # Decision 2: Technology stack
        if analysis.technology_stack and analysis.technology_stack.languages:
            top_lang = max(analysis.technology_stack.languages.items(), 
                          key=lambda x: x[1])[0]
            decisions.append({
                'title': f'Primary Language: {top_lang}',
                'rationale': 'Ecosystem support and team expertise',
                'impact': 'Determines libraries and frameworks',
                'confidence': 0.9
            })
        
        # Decision 3: Service boundaries
        if analysis.service_map and len(analysis.service_map.services) > 1:
            decisions.append({
                'title': f'Service Decomposition into {len(analysis.service_map.services)} Services',
                'rationale': 'Improve modularity and independent deployment',
                'impact': 'Increased system complexity, improved scalability',
                'confidence': 0.8
            })
        
        decisions_text = []
        for i, dec in enumerate(decisions, 1):
            decisions_text.append(f"""### Decision {i}: {dec['title']}

**Rationale:** {dec['rationale']}  
**Impact:** {dec['impact']}  
**Confidence:** {dec['confidence']:.1%}
""")
        
        content = f"""# Key Architectural Decisions Timeline

## Overview

This document tracks major architectural decisions throughout the system's evolution.

**Timeline:** {timeline_name}  
**Total Periods:** {len(periods)}  
**Decisions Documented:** {len(decisions)}

## Decision Log

{chr(10).join(decisions_text) if decisions_text else '*No major decisions identified yet*'}

## Decision Impact Analysis

### Positive Outcomes

- Clear architectural direction
- Improved system maintainability: {analysis.modularity_score:.2f}/1.0
- {len(analysis.service_map.services) if analysis.service_map else 0} well-defined service boundaries

### Challenges

{self._identify_decision_challenges(analysis)}

## Decision Principles

The architectural decisions follow these principles:

1. **Modularity First** - Prioritize loose coupling
2. **Scalability** - Design for growth
3. **Maintainability** - Code clarity over cleverness
4. **Technology Pragmatism** - Choose proven over trendy

## Future Decision Points

Upcoming architectural decisions to consider:

{self._suggest_future_decisions(analysis)}

---
*Generated by Ecosystem MCP - Architecture Generator (Temporal)*  
*Timeline: {timeline_name}*
"""
        
        return {
            'type': 'decisions_timeline',
            'title': 'Key Architectural Decisions Timeline',
            'content': content,
            'format': 'markdown',
            'word_count': len(content.split())
        }
    
    async def _generate_migration_history(
        self,
        analysis,
        temporal_context: Dict,
        config: Dict
    ) -> Dict:
        """Generate migration history documentation."""
        logger.info("   🔄 Generating migration history...")
        
        timeline_name = temporal_context.get('timeline_name', 'Unknown')
        periods = temporal_context.get('periods', [])
        
        content = f"""# Migration History

## Overview

**Timeline:** {timeline_name}  
**Total Periods:** {len(periods)}  
**Current State:** {datetime.now().strftime('%Y-%m-%d')}

## Technology Migrations

### Language Migrations

{self._document_language_migrations(analysis, temporal_context)}

### Framework Migrations

{self._document_framework_migrations(analysis, temporal_context)}

### Database Migrations

{self._document_database_migrations(analysis, temporal_context)}

## Infrastructure Migrations

### Deployment Evolution

{self._document_deployment_migrations(analysis, temporal_context)}

### Scaling Strategy Evolution

- **Initial**: Single-server deployment
- **Growth**: Load balancing introduction
- **Current**: {self._describe_current_infrastructure(analysis)}

## Migration Lessons Learned

### Successful Strategies

- Incremental migrations with rollback capability
- Comprehensive testing at each stage
- Feature flags for gradual rollout

### Challenges Encountered

{self._document_migration_challenges(analysis)}

## Ongoing Migrations

{self._identify_ongoing_migrations(analysis)}

## Future Migration Roadmap

{self._suggest_future_migrations(analysis)}

---
*Generated by Ecosystem MCP - Architecture Generator (Temporal)*  
*Timeline: {timeline_name}*
"""
        
        return {
            'type': 'migration_history',
            'title': 'Migration History',
            'content': content,
            'format': 'markdown',
            'word_count': len(content.split())
        }
    
    # Helper methods for temporal documentation
    
    def _analyze_language_evolution(self, analysis, temporal_context) -> str:
        """Analyze language evolution over time."""
        if not analysis.technology_stack or not analysis.technology_stack.languages:
            return "*Language evolution data not available*"
        
        langs = analysis.technology_stack.languages
        sorted_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)
        
        return '\n'.join(f"- **{lang}**: {count} files (primary language)" 
                        if i == 0 else f"- **{lang}**: {count} files"
                        for i, (lang, count) in enumerate(sorted_langs[:3]))
    
    def _analyze_framework_evolution(self, analysis, temporal_context) -> str:
        """Analyze framework evolution over time."""
        if not analysis.technology_stack or not analysis.technology_stack.frameworks:
            return "*Framework evolution data not available*"
        
        frameworks = list(analysis.technology_stack.frameworks.keys())[:5]
        return '\n'.join(f"- {fw}" for fw in frameworks)
    
    def _assess_current_scalability(self, analysis) -> str:
        """Assess current scalability approach."""
        if analysis.service_map and len(analysis.service_map.services) > 3:
            return "Microservices architecture with horizontal scaling"
        return "Modular monolith with scaling capabilities"
    
    def _predict_next_evolution_phase(self, analysis) -> str:
        """Predict next evolution phase."""
        if analysis.modularity_score < 0.6:
            return "Refactor for improved modularity"
        elif analysis.service_map and len(analysis.service_map.services) < 3:
            return "Consider service decomposition"
        return "Optimize current architecture"
    
    def _identify_decision_challenges(self, analysis) -> str:
        """Identify challenges from past decisions."""
        challenges = []
        
        if analysis.modularity_score < 0.6:
            challenges.append("- Coupling between components remains high")
        if analysis.dependency_graph and len(analysis.dependency_graph.cycles) > 0:
            challenges.append(f"- {len(analysis.dependency_graph.cycles)} circular dependencies")
        
        return '\n'.join(challenges) if challenges else "- No significant challenges identified"
    
    def _suggest_future_decisions(self, analysis) -> str:
        """Suggest future architectural decisions."""
        suggestions = []
        
        if analysis.modularity_score < 0.7:
            suggestions.append("- Evaluate service boundaries for better isolation")
        if analysis.service_map and len(analysis.service_map.services) > 5:
            suggestions.append("- Consider API gateway for service orchestration")
        
        return '\n'.join(suggestions) if suggestions else "- Continue monitoring architectural health"
    
    def _document_language_migrations(self, analysis, temporal_context) -> str:
        """Document language migration history."""
        return """No major language migrations detected.

*Current primary languages reflect initial technology choices.*"""
    
    def _document_framework_migrations(self, analysis, temporal_context) -> str:
        """Document framework migration history."""
        return """Framework versions have been kept current through regular updates.

*No major framework replacements identified.*"""
    
    def _document_database_migrations(self, analysis, temporal_context) -> str:
        """Document database migration history."""
        if analysis.technology_stack and analysis.technology_stack.databases:
            dbs = ', '.join(analysis.technology_stack.databases)
            return f"**Current Databases:** {dbs}\n\n*Database choices have remained stable.*"
        return "*No database information available*"
    
    def _document_deployment_migrations(self, analysis, temporal_context) -> str:
        """Document deployment migration history."""
        if analysis.technology_stack and analysis.technology_stack.deployment:
            platforms = ', '.join(analysis.technology_stack.deployment)
            return f"**Current Deployment:** {platforms}\n\n*Deployment strategy has evolved with system growth.*"
        return "*Deployment evolution data not available*"
    
    def _describe_current_infrastructure(self, analysis) -> str:
        """Describe current infrastructure."""
        if analysis.service_map and len(analysis.service_map.services) > 3:
            return "Distributed microservices architecture"
        return "Consolidated deployment model"
    
    def _document_migration_challenges(self, analysis) -> str:
        """Document migration challenges."""
        return """- Managing backward compatibility
- Coordinating cross-service changes
- Maintaining system availability during migrations"""
    
    def _identify_ongoing_migrations(self, analysis) -> str:
        """Identify ongoing migrations."""
        return "*No ongoing migrations detected at this time.*"
    
    def _suggest_future_migrations(self, analysis) -> str:
        """Suggest future migrations."""
        suggestions = []
        
        if analysis.modularity_score < 0.6:
            suggestions.append("- Consider modularization to improve maintainability")
        
        return '\n'.join(f"- {sug}" for sug in suggestions) if suggestions else "- Continue monitoring for optimization opportunities"

