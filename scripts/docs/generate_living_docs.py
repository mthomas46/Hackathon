#!/usr/bin/env python3
"""
Living Documentation Generator

Automatically generates and updates service documentation based on audit results.
Integrates with the comprehensive audit framework to maintain up-to-date documentation.

Usage:
    python generate_living_docs.py --service doc_store
    python generate_living_docs.py --all-services
    python generate_living_docs.py --update-existing
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from audit_framework import AuditFramework, AuditResults

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LivingDocumentationGenerator:
    """Generates and maintains living documentation from audit results."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.docs_dir = project_root / "docs" / "service-standardization" / "living-docs"
        self.templates_dir = self.docs_dir / "templates"
        self.services_dir = self.docs_dir / "services"
        self.audit_framework = AuditFramework(project_root)

        # Ensure directories exist
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.services_dir.mkdir(parents=True, exist_ok=True)

    async def generate_service_documentation(self, service_name: str, force_update: bool = False) -> bool:
        """Generate documentation for a specific service."""
        try:
            logger.info(f"Generating living documentation for service: {service_name}")

            # Run audit
            audit_results = await self.audit_framework.audit_service(service_name)

            # Generate documentation
            doc_content = self._generate_service_doc(audit_results)

            # Save documentation
            doc_path = self.services_dir / f"{service_name}.md"
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)

            logger.info(f"Generated documentation: {doc_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to generate documentation for {service_name}: {e}")
            return False

    async def generate_all_services_documentation(self, force_update: bool = False) -> Dict[str, bool]:
        """Generate documentation for all services."""
        results = {}
        services = self.audit_framework.discover_services()

        logger.info(f"Generating documentation for {len(services)} services")

        for service in services:
            success = await self.generate_service_documentation(service.name, force_update)
            results[service.name] = success

        return results

    async def update_existing_documentation(self) -> Dict[str, bool]:
        """Update all existing service documentation."""
        results = {}
        existing_docs = list(self.services_dir.glob("*.md"))

        logger.info(f"Updating {len(existing_docs)} existing documentation files")

        for doc_path in existing_docs:
            service_name = doc_path.stem
            success = await self.generate_service_documentation(service_name, force_update=True)
            results[service_name] = success

        return results

    def _generate_service_doc(self, audit_results: AuditResults) -> str:
        """Generate service documentation from audit results."""
        template_path = self.docs_dir / "service-template.md"

        if not template_path.exists():
            raise FileNotFoundError(f"Service template not found: {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()

        # Replace template placeholders with actual data
        doc = template

        # Basic service information
        doc = self._replace_basic_info(doc, audit_results)

        # Architecture assessment
        doc = self._replace_architecture_section(doc, audit_results)

        # Code quality assessment
        doc = self._replace_code_quality_section(doc, audit_results)

        # Performance assessment
        doc = self._replace_performance_section(doc, audit_results)

        # Maintainability assessment
        doc = self._replace_maintainability_section(doc, audit_results)

        # Overall assessment
        doc = self._replace_overall_assessment(doc, audit_results)

        # Progress tracking
        doc = self._replace_progress_tracking(doc, audit_results)

        return doc

    def _replace_basic_info(self, template: str, results: AuditResults) -> str:
        """Replace basic service information in template."""
        # Get service info
        services = self.audit_framework.discover_services()
        service_info = next((s for s in services if s.name == results.service_name), None)

        replacements = {
            "[Service Name]": results.service_name.replace('-', ' ').title(),
            "[🏗️ In Development | ✅ Production | 🧪 Experimental | 🏁 Deprecated]": "🏗️ In Development",  # Could be determined by audit
            "[Date]": datetime.utcnow().strftime("%Y-%m-%d"),
            "[Auditor Name]": "AI Assistant",
            "[Brief description of what this service does and its role in the ecosystem]": f"Service providing {results.service_name} functionality within the LLM Documentation Ecosystem.",
            "[What domain this service owns and its boundaries]": f"The {results.service_name} service owns the domain of {results.service_name.replace('-', ' ')} operations.",
            "[Capability 1]": f"{results.service_name.replace('-', ' ').title()} Operations",
            "[Capability 2]": "REST API Endpoints",
            "[Capability 3]": "Data Persistence",
            "[Number] Python files": str(service_info.files if service_info else "Unknown"),
            "[Number] lines of code": str(service_info.lines if service_info else "Unknown"),
            "[Number] test files": str(service_info.tests if service_info else "Unknown"),
            "[Key external dependencies]": "FastAPI, SQLAlchemy, Pydantic"
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)

        return template

    def _replace_architecture_section(self, template: str, results: AuditResults) -> str:
        """Replace architecture assessment section."""
        arch = results.architecture

        replacements = {
            "Architecture Assessment Score: [Score]/100": f"Architecture Assessment Score: {arch.get('score', 0)}/100",
            "[Score]% - [Comments]": self._format_sub_scores(arch, ['ddd_compliance', 'rest_compliance', 'layer_separation']),
            "[Issue 1 - Priority: High/Medium/Low]": self._format_issues(arch.get('issues', [])),
            "[Improvement 1 - Effort: X days - Impact: High]": self._format_recommendations(
                [r for r in results.priority_improvements if r.get('dimension') == 'architecture']
            )
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)

        return template

    def _replace_code_quality_section(self, template: str, results: AuditResults) -> str:
        """Replace code quality assessment section."""
        cq = results.code_quality

        replacements = {
            "Static Analysis Score: [Score]/100": f"Static Analysis Score: {cq.get('score', 0)}/100",
            "Testing Coverage Score: [Score]/100": f"Testing Coverage Score: {cq.get('testing', 0)}/100",
            "Code Duplication Score: [Score]/100": f"Code Duplication Score: {cq.get('duplication', 0)}/100",
            "Documentation Score: [Score]/100": f"Documentation Score: {cq.get('documentation', 0)}/100",
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)

        # Replace the sub-scores and issues
        template = template.replace(
            "[Score]% - [Comments]",
            self._format_sub_scores(cq, ['complexity', 'testing', 'duplication', 'documentation'])
        )

        template = template.replace(
            "[Issue 1 - Priority: High/Medium/Low]",
            self._format_issues(cq.get('issues', []))
        )

        template = template.replace(
            "[Improvement 1 - Effort: X days - Impact: High]",
            self._format_recommendations(
                [r for r in results.priority_improvements if r.get('dimension') == 'code_quality']
            )
        )

        return template

    def _replace_performance_section(self, template: str, results: AuditResults) -> str:
        """Replace performance assessment section."""
        perf = results.performance

        replacements = {
            "Runtime Performance Score: [Score]/100": f"Runtime Performance Score: {perf.get('score', 0)}/100",
            "Database Performance Score: [Score]/100": f"Database Performance Score: {perf.get('score', 0)}/100",  # Note: using same score for now
            "Resource Optimization Score: [Score]/100": f"Resource Optimization Score: {perf.get('score', 0)}/100",
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)

        template = template.replace(
            "[Score]% - [Comments]",
            self._format_sub_scores(perf, ['runtime', 'database', 'resources'])
        )

        template = template.replace(
            "[Issue 1 - Priority: High/Medium/Low]",
            self._format_issues(perf.get('issues', []))
        )

        template = template.replace(
            "[Optimization 1 - Effort: X days - Impact: High]",
            self._format_recommendations(
                [r for r in results.priority_improvements if r.get('dimension') == 'performance']
            )
        )

        return template

    def _replace_maintainability_section(self, template: str, results: AuditResults) -> str:
        """Replace maintainability assessment section."""
        maint = results.maintainability

        replacements = {
            "Code Organization Score: [Score]/100": f"Code Organization Score: {maint.get('score', 0)}/100",
            "Error Handling Score: [Score]/100": f"Error Handling Score: {maint.get('score', 0)}/100",
            "Scalability Score: [Score]/100": f"Scalability Score: {maint.get('score', 0)}/100",
            "DevOps Readiness Score: [Score]/100": f"DevOps Readiness Score: {maint.get('score', 0)}/100",
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)

        template = template.replace(
            "[Score]% - [Comments]",
            self._format_sub_scores(maint, ['organization', 'error_handling', 'scalability', 'devops'])
        )

        template = template.replace(
            "[Issue 1 - Priority: High/Medium/Low]",
            self._format_issues(maint.get('issues', []))
        )

        template = template.replace(
            "[Improvement 1 - Effort: X days - Impact: High]",
            self._format_recommendations(
                [r for r in results.priority_improvements if r.get('dimension') == 'maintainability']
            )
        )

        return template

    def _replace_overall_assessment(self, template: str, results: AuditResults) -> str:
        """Replace overall assessment section."""
        replacements = {
            "Final Score: [Score]/100 - Grade: [Grade]": f"Final Score: {results.overall_score}/100 - Grade: {results.grade}",
            "[Score] ([Weight]%)": self._format_dimension_scores(results),
            "[Count]": str(len(results.critical_issues)),
            "[Count]": str(len(results.priority_improvements)),  # This will replace the second occurrence
            "[X] person-days": f"{results.estimated_effort_days} person-days"
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value, 1)  # Replace only first occurrence

        # Handle the critical issues list
        critical_issues_text = "\n".join([f"- {issue['issue']}" for issue in results.critical_issues]) if results.critical_issues else "No critical issues identified."
        template = template.replace("[List critical issues that require immediate attention]", critical_issues_text)

        # Handle priority improvements
        priority_text = "\n".join([f"- {rec['title']} ({rec['effort_days']} days, {rec['impact']} impact)" for rec in results.priority_improvements[:5]])  # Top 5
        template = template.replace("[List high-priority improvements with effort estimates]", priority_text)

        return template

    def _replace_progress_tracking(self, template: str, results: AuditResults) -> str:
        """Replace progress tracking section."""
        replacements = {
            "[Date]": results.audit_date[:10],  # Just the date part
            "[Score]": str(results.overall_score),
            "[Grade]": results.grade,
            "[Changes]": "Initial audit",
            "[X] points over [period]": f"{results.overall_score} points (baseline)",
            "[X]/[Y] ([Z]%)": f"0/{len(results.priority_improvements)} (0%)",
            "[X] person-days": f"{results.estimated_effort_days} person-days",
            "[Improving/Stagnant/Declining] (+/- X points)": "Baseline (+0 points)"
        }

        for placeholder, value in replacements.items():
            template = template.replace(placeholder, value)

        return template

    def _format_sub_scores(self, dimension_data: Dict[str, Any], sub_dimensions: List[str]) -> str:
        """Format sub-dimension scores with comments."""
        formatted = []
        for sub_dim in sub_dimensions:
            score = dimension_data.get(sub_dim, 0)
            comment = self._get_score_comment(sub_dim, score)
            formatted.append(f"{score}% - {comment}")

        return "\n- **".join(formatted)

    def _get_score_comment(self, dimension: str, score: float) -> str:
        """Get descriptive comment for score."""
        if score >= 80:
            return "Excellent"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Satisfactory"
        elif score >= 50:
            return "Needs improvement"
        else:
            return "Critical issues"

    def _format_issues(self, issues: List[str]) -> str:
        """Format issues list."""
        if not issues:
            return "No issues identified"
        return "\n".join(f"- {issue}" for issue in issues[:3])  # Top 3 issues

    def _format_recommendations(self, recommendations: List[Dict[str, Any]]) -> str:
        """Format recommendations list."""
        if not recommendations:
            return "No specific recommendations"
        formatted = []
        for rec in recommendations[:3]:  # Top 3 recommendations
            formatted.append(f"- {rec.get('title', 'Unknown')} - Effort: {rec.get('effort_days', '?')} days - Impact: {rec.get('impact', 'Unknown')}")

        return "\n".join(formatted)

    def _format_dimension_scores(self, results: AuditResults) -> str:
        """Format dimension scores with weights."""
        return "\n- **Architecture:** {0} (30%)\n- **Code Quality:** {1} (25%)\n- **Performance:** {2} (20%)\n- **Maintainability:** {3} (25%)".format(
            results.architecture.get('score', 0),
            results.code_quality.get('score', 0),
            results.performance.get('score', 0),
            results.maintainability.get('score', 0)
        )

    def generate_index_documentation(self, results: Dict[str, Dict[str, bool]]) -> None:
        """Generate index documentation for all services."""
        index_path = self.docs_dir / "README.md"

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("# 📚 Living Documentation Index\n\n")
            f.write(f"**Last Updated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n")

            f.write("## 📊 Services Overview\n\n")
            f.write("| Service | Status | Last Audit | Documentation |\n")
            f.write("|---------|--------|------------|---------------|\n")

            for service_name, success in results.items():
                status = "✅ Generated" if success else "❌ Failed"
                doc_link = f"[View](./services/{service_name}.md)" if success else "N/A"
                f.write(f"| {service_name} | {status} | {datetime.utcnow().strftime('%Y-%m-%d')} | {doc_link} |\n")

            f.write("\n## 🔄 Documentation Maintenance\n\n")
            f.write("This documentation is automatically generated and updated through:\n\n")
            f.write("- **Audit Framework:** Comprehensive 4-dimensional assessment\n")
            f.write("- **Automated Generation:** Service documentation from audit results\n")
            f.write("- **Continuous Updates:** Regular assessment and documentation refresh\n\n")

            f.write("## 📋 Usage\n\n")
            f.write("```bash\n")
            f.write("# Generate documentation for specific service\n")
            f.write("python scripts/docs/generate_living_docs.py --service doc_store\n\n")
            f.write("# Generate documentation for all services\n")
            f.write("python scripts/docs/generate_living_docs.py --all-services\n\n")
            f.write("# Update existing documentation\n")
            f.write("python scripts/docs/generate_living_docs.py --update-existing\n")
            f.write("```\n\n")

            f.write("---\n\n")
            f.write("*Generated by Living Documentation System*")


async def main():
    """Main entry point for living documentation generator."""
    import argparse

    parser = argparse.ArgumentParser(description='Living Documentation Generator')
    parser.add_argument('--service', help='Generate documentation for specific service')
    parser.add_argument('--all-services', action='store_true', help='Generate documentation for all services')
    parser.add_argument('--update-existing', action='store_true', help='Update all existing documentation')

    args = parser.parse_args()

    # Initialize generator
    project_root = Path(__file__).parent.parent.parent
    generator = LivingDocumentationGenerator(project_root)

    try:
        if args.service:
            success = await generator.generate_service_documentation(args.service)
            if success:
                logger.info(f"Successfully generated documentation for {args.service}")
                # Generate index
                generator.generate_index_documentation({args.service: success})
            else:
                logger.error(f"Failed to generate documentation for {args.service}")
                sys.exit(1)

        elif args.all_services:
            results = await generator.generate_all_services_documentation()
            generator.generate_index_documentation(results)

            successful = sum(1 for success in results.values() if success)
            total = len(results)

            logger.info(f"Generated documentation for {successful}/{total} services")

            if successful < total:
                logger.warning(f"Failed to generate documentation for: {[name for name, success in results.items() if not success]}")
                sys.exit(1)

        elif args.update_existing:
            results = await generator.update_existing_documentation()
            generator.generate_index_documentation(results)

            successful = sum(1 for success in results.values() if success)
            total = len(results)

            logger.info(f"Updated documentation for {successful}/{total} services")

        else:
            parser.print_help()
            sys.exit(1)

    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
