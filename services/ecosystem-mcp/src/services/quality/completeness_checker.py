"""
Completeness Checker

Validates documentation completeness and structure.
"""

import logging
import re
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SectionType(Enum):
    """Required documentation section types."""
    OVERVIEW = "overview"
    INSTALLATION = "installation"
    USAGE = "usage"
    API = "api"
    EXAMPLES = "examples"
    CONFIGURATION = "configuration"
    ARCHITECTURE = "architecture"
    COMPONENTS = "components"
    QUICKSTART = "quick start"
    TROUBLESHOOTING = "troubleshooting"


@dataclass
class CompletenessResult:
    """Completeness check result."""
    overall_score: float  # 0-1
    missing_sections: List[str]
    incomplete_sections: List[str]
    placeholder_count: int
    broken_links: List[str]
    formatting_issues: List[str]
    recommendations: List[str]
    section_word_counts: Dict[str, int]
    has_code_examples: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'overall_score': self.overall_score,
            'missing_sections': self.missing_sections,
            'incomplete_sections': self.incomplete_sections,
            'placeholder_count': self.placeholder_count,
            'broken_links': self.broken_links,
            'formatting_issues': self.formatting_issues,
            'recommendations': self.recommendations,
            'section_word_counts': self.section_word_counts,
            'has_code_examples': self.has_code_examples
        }


class CompletenessChecker:
    """
    Checks documentation completeness.
    
    Validates:
    - Required sections present
    - No placeholder content
    - Cross-references valid
    - Consistent formatting
    - Adequate content depth
    """
    
    def __init__(self):
        # Required sections by document type
        self.required_sections = {
            'architecture': {
                SectionType.OVERVIEW,
                SectionType.ARCHITECTURE,
                SectionType.COMPONENTS
            },
            'component': {
                SectionType.OVERVIEW,
                SectionType.USAGE,
                SectionType.API
            },
            'api_reference': {
                SectionType.API,
                SectionType.EXAMPLES,
                SectionType.USAGE
            },
            'guide': {
                SectionType.OVERVIEW,
                SectionType.INSTALLATION,
                SectionType.USAGE,
                SectionType.EXAMPLES
            },
            'quickstart': {
                SectionType.QUICKSTART,
                SectionType.EXAMPLES,
                SectionType.USAGE
            }
        }
        
        # Placeholder patterns
        self.placeholder_patterns = [
            'TODO',
            'TBD',
            'FIXME',
            'XXX',
            'To be generated',
            'Coming soon',
            '[INSERT',
            '<INSERT',
            'PLACEHOLDER',
            'Fill in',
            'Add content'
        ]
        
        # Minimum word count per section
        self.min_section_words = 50
        
        logger.info("CompletenessChecker initialized")
    
    async def check(self, artifact: Dict) -> CompletenessResult:
        """
        Check documentation completeness.
        
        Args:
            artifact: Documentation artifact with 'content', 'type', 'title'
        
        Returns:
            Completeness result with score and issues
        """
        title = artifact.get('title', 'Unknown')
        logger.info(f"🔍 Checking completeness: {title}")
        
        content = artifact.get('content', '')
        doc_type = artifact.get('type', 'unknown')
        
        # Check required sections
        missing_sections = await self._check_required_sections(
            content, doc_type
        )
        
        # Check for placeholders
        placeholder_count = self._count_placeholders(content)
        
        # Check for incomplete sections
        incomplete_sections, section_word_counts = await self._find_incomplete_sections(content)
        
        # Check cross-references
        broken_links = self._check_links(content)
        
        # Check formatting
        formatting_issues = self._check_formatting(content)
        
        # Check for code examples
        has_code_examples = self._has_code_examples(content)
        
        # Calculate score
        score = self._calculate_score(
            missing_sections,
            placeholder_count,
            incomplete_sections,
            broken_links,
            formatting_issues,
            has_code_examples,
            doc_type
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            missing_sections,
            incomplete_sections,
            placeholder_count,
            has_code_examples,
            doc_type
        )
        
        result = CompletenessResult(
            overall_score=score,
            missing_sections=missing_sections,
            incomplete_sections=incomplete_sections,
            placeholder_count=placeholder_count,
            broken_links=broken_links,
            formatting_issues=formatting_issues,
            recommendations=recommendations,
            section_word_counts=section_word_counts,
            has_code_examples=has_code_examples
        )
        
        logger.info(f"   ✅ Completeness score: {score:.2f}")
        if missing_sections:
            logger.warning(f"   ⚠️  Missing sections: {missing_sections}")
        if placeholder_count > 0:
            logger.warning(f"   ⚠️  Placeholders: {placeholder_count}")
        
        return result
    
    async def _check_required_sections(
        self,
        content: str,
        doc_type: str
    ) -> List[str]:
        """Check for required sections."""
        required = self.required_sections.get(doc_type, set())
        content_lower = content.lower()
        
        missing = []
        for section in required:
            section_name = section.value
            # Check for section as header or in content
            if not (
                f"# {section_name}" in content_lower or
                f"## {section_name}" in content_lower or
                f"### {section_name}" in content_lower or
                section_name in content_lower
            ):
                missing.append(section_name)
        
        return missing
    
    def _count_placeholders(self, content: str) -> int:
        """Count placeholder occurrences."""
        count = 0
        content_upper = content.upper()
        for pattern in self.placeholder_patterns:
            count += content_upper.count(pattern.upper())
        return count
    
    async def _find_incomplete_sections(
        self,
        content: str
    ) -> tuple[List[str], Dict[str, int]]:
        """
        Find sections with minimal content.
        
        Returns:
            Tuple of (incomplete_sections, section_word_counts)
        """
        incomplete = []
        word_counts = {}
        
        # Split by markdown headers
        sections = re.split(r'\n#+\s+', content)
        
        for i, section in enumerate(sections):
            if not section.strip():
                continue
            
            lines = section.strip().split('\n')
            if not lines:
                continue
            
            # First line is the section title
            section_title = lines[0].strip().rstrip('#')
            
            # Count words in content (excluding title)
            section_content = '\n'.join(lines[1:])
            word_count = len(section_content.split())
            word_counts[section_title] = word_count
            
            # Check if section is too short
            if word_count < self.min_section_words and i > 0:  # Skip doc title
                incomplete.append(section_title)
        
        return incomplete, word_counts
    
    def _check_links(self, content: str) -> List[str]:
        """Check for broken cross-references."""
        broken = []
        
        # Find markdown links
        links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
        
        for text, url in links:
            # Check for empty or placeholder URLs
            if not url or url in ['#', 'TODO', 'TBD', '']:
                broken.append(f"[{text}]({url or 'empty'})")
            # Check for malformed URLs
            elif url.startswith('http') and ' ' in url:
                broken.append(f"[{text}]({url}) - contains spaces")
        
        return broken
    
    def _check_formatting(self, content: str) -> List[str]:
        """Check markdown formatting."""
        issues = []
        
        # Check for unbalanced code blocks
        triple_backticks = content.count('```')
        if triple_backticks % 2 != 0:
            issues.append("Unbalanced code blocks (``` not closed)")
        
        # Check for empty headers
        if re.search(r'#+\s*\n', content):
            issues.append("Empty headers found")
        
        # Check for consecutive blank lines (>3)
        if '\n\n\n\n' in content:
            issues.append("Excessive blank lines (>3 consecutive)")
        
        # Check for missing newline before headers
        if re.search(r'[^\n]\n#+\s', content):
            issues.append("Headers should have blank line before them")
        
        # Check for inconsistent header levels
        headers = re.findall(r'^(#+)\s+', content, re.MULTILINE)
        if headers:
            levels = [len(h) for h in headers]
            # Check for skipped levels (e.g., # then ###)
            for i in range(len(levels) - 1):
                if levels[i+1] - levels[i] > 1:
                    issues.append(f"Skipped header level: {levels[i]} to {levels[i+1]}")
                    break
        
        return issues
    
    def _has_code_examples(self, content: str) -> bool:
        """Check if document contains code examples."""
        return '```' in content
    
    def _calculate_score(
        self,
        missing_sections: List[str],
        placeholder_count: int,
        incomplete_sections: List[str],
        broken_links: List[str],
        formatting_issues: List[str],
        has_code_examples: bool,
        doc_type: str
    ) -> float:
        """Calculate overall completeness score."""
        score = 1.0
        
        # Penalize missing sections (heavy penalty)
        score -= len(missing_sections) * 0.15
        
        # Penalize placeholders
        score -= min(placeholder_count * 0.05, 0.3)
        
        # Penalize incomplete sections
        score -= len(incomplete_sections) * 0.05
        
        # Penalize broken links
        score -= len(broken_links) * 0.03
        
        # Penalize formatting issues (light penalty)
        score -= len(formatting_issues) * 0.02
        
        # Bonus for code examples in certain doc types
        if doc_type in ['guide', 'api_reference', 'quickstart'] and not has_code_examples:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
    
    def _generate_recommendations(
        self,
        missing_sections: List[str],
        incomplete_sections: List[str],
        placeholder_count: int,
        has_code_examples: bool,
        doc_type: str
    ) -> List[str]:
        """Generate actionable recommendations."""
        recs = []
        
        if missing_sections:
            recs.append(
                f"Add missing sections: {', '.join(missing_sections[:5])}"
            )
        
        if incomplete_sections:
            recs.append(
                f"Expand incomplete sections (< {self.min_section_words} words): "
                f"{', '.join(incomplete_sections[:3])}"
            )
        
        if placeholder_count > 0:
            recs.append(
                f"Replace {placeholder_count} placeholder(s) with actual content"
            )
        
        if not has_code_examples and doc_type in ['guide', 'api_reference', 'quickstart']:
            recs.append("Add code examples to illustrate usage")
        
        return recs


# Singleton instance
_completeness_checker: Optional[CompletenessChecker] = None


def get_completeness_checker() -> CompletenessChecker:
    """Get or create singleton completeness checker."""
    global _completeness_checker
    if _completeness_checker is None:
        _completeness_checker = CompletenessChecker()
    return _completeness_checker

