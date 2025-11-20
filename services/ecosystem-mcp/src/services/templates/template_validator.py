"""
Template Structure Validator

Validates generated documentation against template structure to ensure:
- All required sections are present
- Subsections match template definition
- Content meets quality standards
- Formatting is consistent
"""

import logging
import re
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class TemplateValidator:
    """
    Validates generated documentation against template structure.
    
    Ensures that generated content:
    - Contains all required sections
    - Has proper subsection structure
    - Meets minimum content length requirements
    - Follows template formatting rules
    """
    
    def __init__(self):
        """Initialize template validator."""
        logger.info("TemplateValidator initialized")
    
    def validate_structure(
        self,
        template: Dict[str, Any],
        generated_sections: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate generated sections against template structure.
        
        Args:
            template: Template definition
            generated_sections: List of generated sections
        
        Returns:
            Validation result with score and issues
        """
        validation_result = {
            "valid": True,
            "score": 1.0,
            "issues": [],
            "warnings": [],
            "section_scores": {},
            "overall_quality": "excellent"
        }
        
        # Get template sections
        template_sections = template.get("structure", {}).get("sections", [])
        
        # Check for missing required sections
        missing_sections = self._check_missing_sections(
            template_sections,
            generated_sections
        )
        
        if missing_sections:
            validation_result["valid"] = False
            validation_result["issues"].append({
                "type": "missing_sections",
                "severity": "high",
                "sections": missing_sections
            })
            # Reduce score based on missing sections
            validation_result["score"] *= (1 - len(missing_sections) / len(template_sections))
        
        # Validate each section
        for section in generated_sections:
            section_name = section.get("name")
            section_validation = self._validate_section(
                section,
                template_sections,
                template
            )
            
            validation_result["section_scores"][section_name] = section_validation
            
            # Accumulate issues and warnings
            validation_result["issues"].extend(section_validation.get("issues", []))
            validation_result["warnings"].extend(section_validation.get("warnings", []))
            
            # Update overall score (average)
            if section_validation.get("score", 1.0) < 1.0:
                validation_result["score"] = (
                    validation_result["score"] + section_validation["score"]
                ) / 2
        
        # Determine overall quality
        validation_result["overall_quality"] = self._determine_quality(
            validation_result["score"]
        )
        
        logger.info(
            f"Validation complete: score={validation_result['score']:.2f}, "
            f"quality={validation_result['overall_quality']}, "
            f"issues={len(validation_result['issues'])}"
        )
        
        return validation_result
    
    def _check_missing_sections(
        self,
        template_sections: List[Dict[str, Any]],
        generated_sections: List[Dict[str, Any]]
    ) -> List[str]:
        """Check for missing required sections."""
        generated_names = {s.get("name") for s in generated_sections}
        missing = []
        
        for template_section in template_sections:
            if template_section.get("required", False):
                section_name = template_section.get("name")
                if section_name not in generated_names:
                    missing.append(section_name)
        
        return missing
    
    def _validate_section(
        self,
        section: Dict[str, Any],
        template_sections: List[Dict[str, Any]],
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a single section against template.
        
        Checks:
        - Content length meets minimum
        - Subsections are present (if defined)
        - Formatting follows template rules
        """
        section_name = section.get("name")
        content = section.get("content", "")
        
        result = {
            "section": section_name,
            "score": 1.0,
            "issues": [],
            "warnings": []
        }
        
        # Find template definition for this section
        template_def = next(
            (s for s in template_sections if s.get("name") == section_name),
            None
        )
        
        if not template_def:
            result["warnings"].append({
                "type": "undefined_section",
                "message": f"Section '{section_name}' not in template"
            })
            return result
        
        # Check minimum content length
        min_words = template_def.get("min_words", 50)
        word_count = len(content.split())
        
        if word_count < min_words:
            result["issues"].append({
                "type": "insufficient_content",
                "severity": "medium",
                "expected": min_words,
                "actual": word_count,
                "message": f"Section has only {word_count} words (min: {min_words})"
            })
            result["score"] *= (word_count / min_words)
        
        # Check for required subsections
        required_subsections = template_def.get("subsections", [])
        if required_subsections:
            missing_subsections = self._check_subsections(
                content,
                required_subsections
            )
            
            if missing_subsections:
                result["warnings"].append({
                    "type": "missing_subsections",
                    "subsections": missing_subsections,
                    "message": f"Missing subsections: {', '.join(missing_subsections)}"
                })
                result["score"] *= (1 - len(missing_subsections) / len(required_subsections))
        
        # Check formatting rules
        formatting_issues = self._check_formatting(
            content,
            template_def.get("formatting_rules", {})
        )
        
        if formatting_issues:
            result["warnings"].extend(formatting_issues)
            result["score"] *= 0.95  # Small penalty for formatting issues
        
        return result
    
    def _check_subsections(
        self,
        content: str,
        required_subsections: List[str]
    ) -> List[str]:
        """Check for required subsections in content."""
        missing = []
        
        for subsection in required_subsections:
            # Look for markdown headers (### Subsection Name)
            pattern = rf"###\s+{re.escape(subsection)}"
            if not re.search(pattern, content, re.IGNORECASE):
                missing.append(subsection)
        
        return missing
    
    def _check_formatting(
        self,
        content: str,
        rules: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Check content formatting against rules."""
        issues = []
        
        # Check for code blocks if required
        if rules.get("require_code_examples", False):
            if "```" not in content:
                issues.append({
                    "type": "missing_code_examples",
                    "message": "Section should include code examples"
                })
        
        # Check for lists if required
        if rules.get("require_lists", False):
            if not re.search(r"^[\*\-]\s", content, re.MULTILINE):
                issues.append({
                    "type": "missing_lists",
                    "message": "Section should include bullet/numbered lists"
                })
        
        # Check for links if required
        if rules.get("require_links", False):
            if not re.search(r"\[.*?\]\(.*?\)", content):
                issues.append({
                    "type": "missing_links",
                    "message": "Section should include hyperlinks"
                })
        
        return issues
    
    def _determine_quality(self, score: float) -> str:
        """Determine overall quality from score."""
        if score >= 0.95:
            return "excellent"
        elif score >= 0.85:
            return "good"
        elif score >= 0.70:
            return "acceptable"
        elif score >= 0.50:
            return "poor"
        else:
            return "failing"
    
    def validate_adherence(
        self,
        template: Dict[str, Any],
        section_name: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Validate a single section's adherence to template.
        
        This is called during generation to provide real-time feedback.
        
        Args:
            template: Template definition
            section_name: Section name
            content: Generated content
        
        Returns:
            Adherence validation result
        """
        template_sections = template.get("structure", {}).get("sections", [])
        template_def = next(
            (s for s in template_sections if s.get("name") == section_name),
            None
        )
        
        if not template_def:
            return {
                "valid": True,
                "adherence_score": 1.0,
                "issues": [],
                "warnings": [f"Section '{section_name}' not in template"]
            }
        
        # Validate this section
        section_data = {"name": section_name, "content": content}
        result = self._validate_section(section_data, template_sections, template)
        
        return {
            "valid": result["score"] >= 0.5,  # 50% threshold
            "adherence_score": result["score"],
            "issues": result.get("issues", []),
            "warnings": result.get("warnings", [])
        }
    
    def generate_validation_report(
        self,
        validation_result: Dict[str, Any]
    ) -> str:
        """
        Generate a human-readable validation report.
        
        Args:
            validation_result: Validation result from validate_structure()
        
        Returns:
            Markdown-formatted report
        """
        lines = [
            "# Documentation Validation Report",
            "",
            f"**Overall Quality:** {validation_result['overall_quality'].upper()}",
            f"**Score:** {validation_result['score']:.2f}/1.00",
            f"**Valid:** {'✅ Yes' if validation_result['valid'] else '❌ No'}",
            "",
            "---",
            ""
        ]
        
        # Issues
        issues = validation_result.get("issues", [])
        if issues:
            lines.append("## ❌ Issues")
            lines.append("")
            for issue in issues:
                severity = issue.get("severity", "unknown")
                issue_type = issue.get("type", "unknown")
                message = issue.get("message", str(issue))
                lines.append(f"- **{severity.upper()}** ({issue_type}): {message}")
            lines.append("")
        
        # Warnings
        warnings = validation_result.get("warnings", [])
        if warnings:
            lines.append("## ⚠️ Warnings")
            lines.append("")
            for warning in warnings:
                warning_type = warning.get("type", "unknown")
                message = warning.get("message", str(warning))
                lines.append(f"- ({warning_type}): {message}")
            lines.append("")
        
        # Section scores
        section_scores = validation_result.get("section_scores", {})
        if section_scores:
            lines.append("## 📊 Section Scores")
            lines.append("")
            lines.append("| Section | Score | Quality |")
            lines.append("|---------|-------|---------|")
            
            for section_name, section_data in section_scores.items():
                score = section_data.get("score", 0.0)
                quality = self._determine_quality(score)
                lines.append(f"| {section_name} | {score:.2f} | {quality} |")
            lines.append("")
        
        return "\n".join(lines)


# Singleton instance
_template_validator: Optional[TemplateValidator] = None


def get_template_validator() -> TemplateValidator:
    """Get or create singleton template validator."""
    global _template_validator
    if _template_validator is None:
        _template_validator = TemplateValidator()
    return _template_validator

