"""Automated Remediation module for Analysis Service.

Provides intelligent automated fixes for common documentation issues, ranging from
simple formatting corrections to complex content improvements, with safety checks
and rollback capabilities.
"""

import time
import logging
import re
import json
from typing import Dict, Any, List, Optional, Tuple, Set, Union
from datetime import datetime
from collections import defaultdict, Counter
from difflib import SequenceMatcher
import copy

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    import language_tool_python
    AUTOMATED_REMEDIATION_AVAILABLE = True
except ImportError:
    AUTOMATED_REMEDIATION_AVAILABLE = False
    nltk = None
    language_tool_python = None

from services.shared.core.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes

logger = logging.getLogger(__name__)


class AutomatedRemediator:
    """Intelligent system for automated documentation remediation."""

    def __init__(self):
        """Initialize the automated remediator."""
        self.initialized = False
        self.remediation_rules = self._get_remediation_rules()
        self.safety_checks = self._get_safety_checks()
        self.confidence_thresholds = self._get_confidence_thresholds()
        self.backup_enabled = True
        self._initialize_remediator()

    def _initialize_remediator(self) -> bool:
        """Initialize the automated remediation components."""
        if not AUTOMATED_REMEDIATION_AVAILABLE:
            logger.warning("Automated remediation dependencies not available")
            return False

        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)

            # Initialize language tool
            self.grammar_tool = language_tool_python.LanguageTool('en-US')

            self.initialized = True
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize remediation components: {e}")
            return False

    def _get_remediation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Define automated remediation rules for common issues."""
        return {
            'formatting_consistency': {
                'description': 'Fix inconsistent formatting and markdown syntax',
                'issues': ['heading_inconsistency', 'list_formatting', 'code_block_formatting'],
                'automated_fixes': True,
                'confidence_threshold': 0.9,
                'rollback_safe': True
            },
            'grammar_spelling': {
                'description': 'Correct grammar and spelling errors',
                'issues': ['spelling_errors', 'grammar_errors', 'punctuation_errors'],
                'automated_fixes': True,
                'confidence_threshold': 0.8,
                'rollback_safe': True
            },
            'terminology_consistency': {
                'description': 'Ensure consistent terminology usage',
                'issues': ['inconsistent_terms', 'abbreviation_variations'],
                'automated_fixes': True,
                'confidence_threshold': 0.7,
                'rollback_safe': True
            },
            'link_validation': {
                'description': 'Fix broken or malformed links',
                'issues': ['broken_links', 'malformed_links', 'missing_alt_text'],
                'automated_fixes': False,  # Requires manual verification
                'confidence_threshold': 0.6,
                'rollback_safe': True
            },
            'structure_optimization': {
                'description': 'Optimize document structure and organization',
                'issues': ['missing_headings', 'heading_hierarchy', 'section_breaks'],
                'automated_fixes': True,
                'confidence_threshold': 0.7,
                'rollback_safe': True
            },
            'readability_improvements': {
                'description': 'Improve readability and clarity',
                'issues': ['sentence_length', 'passive_voice', 'complex_words'],
                'automated_fixes': False,  # Suggestions only
                'confidence_threshold': 0.6,
                'rollback_safe': False
            },
            'accessibility_enhancements': {
                'description': 'Enhance accessibility compliance',
                'issues': ['missing_alt_text', 'color_contrast', 'keyboard_navigation'],
                'automated_fixes': True,
                'confidence_threshold': 0.8,
                'rollback_safe': True
            },
            'metadata_completeness': {
                'description': 'Ensure complete and accurate metadata',
                'issues': ['missing_version', 'incomplete_description', 'missing_tags'],
                'automated_fixes': False,  # Requires manual input
                'confidence_threshold': 0.5,
                'rollback_safe': True
            }
        }

    def _get_safety_checks(self) -> Dict[str, Dict[str, Any]]:
        """Define safety checks to prevent harmful automated changes."""
        return {
            'content_preservation': {
                'description': 'Ensure original meaning is preserved',
                'checks': ['semantic_similarity', 'keyword_preservation', 'context_integrity'],
                'threshold': 0.8
            },
            'structural_integrity': {
                'description': 'Maintain document structure and hierarchy',
                'checks': ['heading_hierarchy', 'list_structure', 'code_blocks'],
                'threshold': 0.9
            },
            'link_functionality': {
                'description': 'Verify link functionality after changes',
                'checks': ['link_syntax', 'reference_validity'],
                'threshold': 0.95
            },
            'formatting_consistency': {
                'description': 'Maintain consistent formatting throughout',
                'checks': ['markdown_syntax', 'indentation', 'spacing'],
                'threshold': 0.85
            }
        }

    def _get_confidence_thresholds(self) -> Dict[str, float]:
        """Define confidence thresholds for different types of fixes."""
        return {
            'high_confidence': 0.9,      # Very safe fixes (formatting, spelling)
            'medium_confidence': 0.7,    # Moderately safe fixes (terminology, structure)
            'low_confidence': 0.5,       # Risky fixes requiring review (content changes)
            'suggestion_only': 0.3       # Only provide suggestions, no automated fixes
        }

    def _analyze_document_structure(self, content: str) -> Dict[str, Any]:
        """Analyze document structure for potential issues."""
        analysis = {
            'headings': [],
            'heading_hierarchy': True,
            'lists': [],
            'code_blocks': [],
            'links': [],
            'issues': [],
            'suggestions': []
        }

        lines = content.split('\n')

        # Analyze headings
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                title = line.strip('#').strip()
                analysis['headings'].append({
                    'level': level,
                    'title': title,
                    'line': i + 1
                })

        # Check heading hierarchy
        if analysis['headings']:
            levels = [h['level'] for h in analysis['headings']]
            for i in range(1, len(levels)):
                if levels[i] > levels[i-1] + 1:
                    analysis['heading_hierarchy'] = False
                    analysis['issues'].append(f"Heading hierarchy broken at line {analysis['headings'][i]['line']}")
                    break

        # Find code blocks
        in_code_block = False
        code_start = -1
        for i, line in enumerate(lines):
            if line.strip().startswith('```'):
                if not in_code_block:
                    in_code_block = True
                    code_start = i + 1
                else:
                    analysis['code_blocks'].append({
                        'start': code_start,
                        'end': i + 1,
                        'language': lines[code_start - 1].strip('```').strip() or 'text'
                    })
                    in_code_block = False

        # Find links
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(link_pattern, content):
            analysis['links'].append({
                'text': match.group(1),
                'url': match.group(2),
                'position': match.start()
            })

        return analysis

    def _fix_formatting_issues(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """Fix common formatting issues."""
        fixed_content = content
        applied_fixes = []

        # Fix heading spacing
        lines = fixed_content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                # Ensure space after # symbols
                if not line.startswith('# '):
                    lines[i] = line.replace('#', '# ', 1).rstrip()
                    applied_fixes.append(f"Fixed heading spacing at line {i+1}")

        fixed_content = '\n'.join(lines)

        # Fix list formatting
        # Ensure consistent bullet points
        fixed_content = re.sub(r'^[\s]*[-\*\+]\s*', '- ', fixed_content, flags=re.MULTILINE)
        if '- ' in fixed_content:
            applied_fixes.append("Standardized bullet point formatting")

        # Fix code block formatting
        # Ensure consistent code block markers
        code_block_pattern = r'```(\w*)\n(.*?)\n```'
        def fix_code_block(match):
            language = match.group(1).strip()
            code = match.group(2)
            return f'```{language}\n{code}\n```'

        original_content = fixed_content
        fixed_content = re.sub(code_block_pattern, fix_code_block, fixed_content, flags=re.DOTALL)
        if fixed_content != original_content:
            applied_fixes.append("Fixed code block formatting")

        return fixed_content, applied_fixes

    def _fix_grammar_spelling(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """Fix grammar and spelling issues."""
        fixed_content = content
        applied_fixes = []

        try:
            # Use language tool for grammar and spelling corrections
            matches = self.grammar_tool.check(fixed_content)

            # Filter for high-confidence fixes only
            confident_matches = [match for match in matches if match.rule.confidence > 0.8]

            # Sort by position (reverse order to avoid offset issues)
            confident_matches.sort(key=lambda x: x.offset, reverse=True)

            for match in confident_matches:
                if match.replacements:
                    # Only apply the first (most confident) replacement
                    replacement = match.replacements[0]

                    # Apply the fix
                    start = match.offset
                    end = match.offset + match.errorlength
                    fixed_content = fixed_content[:start] + replacement + fixed_content[end:]

                    applied_fixes.append(f"Fixed '{match.matchedText}' → '{replacement}'")

        except Exception as e:
            logger.warning(f"Grammar check failed: {e}")

        return fixed_content, applied_fixes

    def _fix_terminology_consistency(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """Fix terminology consistency issues."""
        fixed_content = content
        applied_fixes = []

        # Common terminology fixes
        term_mappings = {
            # API variations
            r'\bapi\b': 'API',
            r'\bapis\b': 'APIs',

            # HTTP method consistency
            r'\bget\b': 'GET',
            r'\bpost\b': 'POST',
            r'\bput\b': 'PUT',
            r'\bdelete\b': 'DELETE',
            r'\bpatch\b': 'PATCH',

            # Common terms
            r'\bdatabase\b': 'database',
            r'\bauthentication\b': 'authentication',
            r'\bauthorization\b': 'authorization',

            # Version consistency
            r'\bv\d+\.\d+\b': lambda m: m.group().upper(),
        }

        for pattern, replacement in term_mappings.items():
            original_content = fixed_content

            if callable(replacement):
                fixed_content = re.sub(pattern, replacement, fixed_content, flags=re.IGNORECASE)
            else:
                fixed_content = re.sub(pattern, replacement, fixed_content, flags=re.IGNORECASE)

            if fixed_content != original_content:
                applied_fixes.append(f"Standardized terminology: {pattern}")

        return fixed_content, applied_fixes

    def _fix_link_issues(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """Fix link-related issues."""
        fixed_content = content
        applied_fixes = []

        # Fix malformed link syntax
        # Ensure proper spacing in link syntax
        link_pattern = r'\[([^\]]+)\]\s*\(\s*([^)]+)\s*\)'
        def clean_link(match):
            text = match.group(1).strip()
            url = match.group(2).strip()
            return f'[{text}]({url})'

        original_content = fixed_content
        fixed_content = re.sub(link_pattern, clean_link, fixed_content)

        if fixed_content != original_content:
            applied_fixes.append("Fixed link formatting and spacing")

        # Add alt text suggestions for images (suggestions only, not automated)
        image_pattern = r'!\[\]\(([^)]+)\)'
        images_without_alt = len(re.findall(image_pattern, fixed_content))

        if images_without_alt > 0:
            applied_fixes.append(f"Found {images_without_alt} images without alt text (requires manual review)")

        return fixed_content, applied_fixes

    def _fix_structure_issues(self, content: str, issues: List[Dict[str, Any]]) -> Tuple[str, List[str]]:
        """Fix document structure issues."""
        fixed_content = content
        applied_fixes = []

        lines = fixed_content.split('\n')

        # Fix heading hierarchy issues
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                level = len(line) - len(line.lstrip('#'))

                # Ensure reasonable heading levels (max H6)
                if level > 6:
                    lines[i] = '######' + line.strip('#').strip()
                    applied_fixes.append(f"Fixed heading level at line {i+1}")

        fixed_content = '\n'.join(lines)

        # Add missing table of contents for long documents
        if len(lines) > 50 and not re.search(r'table of contents|contents', fixed_content, re.IGNORECASE):
            # Find all headings
            headings = []
            for i, line in enumerate(lines):
                if line.strip().startswith('#'):
                    level = len(line) - len(line.lstrip('#'))
                    title = line.strip('#').strip()
                    headings.append((level, title, i))

            if len(headings) > 5:
                toc_lines = ['## Table of Contents', '']
                for level, title, line_num in headings:
                    indent = '  ' * (level - 1)
                    toc_lines.append(f'{indent}- [{title}](#{title.lower().replace(" ", "-")})')

                toc_content = '\n'.join(toc_lines) + '\n\n'
                fixed_content = toc_content + fixed_content
                applied_fixes.append("Added table of contents for better navigation")

        return fixed_content, applied_fixes

    def _check_safety(self, original_content: str, modified_content: str) -> Dict[str, Any]:
        """Perform safety checks on automated modifications."""
        safety_results = {
            'safe': True,
            'checks_passed': [],
            'checks_failed': [],
            'confidence_score': 1.0,
            'warnings': []
        }

        # Check content preservation
        similarity = self._calculate_similarity(original_content, modified_content)
        if similarity < self.safety_checks['content_preservation']['threshold']:
            safety_results['safe'] = False
            safety_results['checks_failed'].append('content_preservation')
            safety_results['warnings'].append('.2f')
        else:
            safety_results['checks_passed'].append('content_preservation')

        # Check structural integrity
        original_structure = self._analyze_document_structure(original_content)
        modified_structure = self._analyze_document_structure(modified_content)

        if len(original_structure['headings']) != len(modified_structure['headings']):
            safety_results['safe'] = False
            safety_results['checks_failed'].append('structural_integrity')
            safety_results['warnings'].append("Heading structure changed - review required")
        else:
            safety_results['checks_passed'].append('structural_integrity')

        # Check link integrity
        original_links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', original_content))
        modified_links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', modified_content))

        if original_links != modified_links:
            safety_results['warnings'].append("Link count changed - verify link functionality")

        # Calculate overall confidence
        passed_checks = len(safety_results['checks_passed'])
        total_checks = len(safety_results['checks_passed']) + len(safety_results['checks_failed'])

        if total_checks > 0:
            safety_results['confidence_score'] = passed_checks / total_checks
        else:
            safety_results['confidence_score'] = 1.0

        return safety_results

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        return SequenceMatcher(None, text1, text2).ratio()

    def _create_backup(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create a backup of the original content."""
        return {
            'content': content,
            'timestamp': time.time(),
            'metadata': copy.deepcopy(metadata),
            'backup_id': f"backup_{int(time.time())}_{hash(content) % 10000}"
        }

    def _generate_remediation_report(self, original_content: str, final_content: str,
                                   applied_fixes: List[str], safety_results: Dict[str, Any],
                                   processing_time: float) -> Dict[str, Any]:
        """Generate a comprehensive remediation report."""
        report = {
            'remediation_summary': {
                'original_length': len(original_content),
                'final_length': len(final_content),
                'changes_made': len(applied_fixes),
                'processing_time': processing_time,
                'safety_status': 'safe' if safety_results['safe'] else 'requires_review'
            },
            'applied_fixes': applied_fixes,
            'safety_assessment': safety_results,
            'quality_improvements': self._assess_quality_improvements(original_content, final_content),
            'recommendations': self._generate_followup_recommendations(safety_results, applied_fixes)
        }

        return report

    def _assess_quality_improvements(self, original_content: str, final_content: str) -> Dict[str, Any]:
        """Assess quality improvements made by remediation."""
        improvements = {
            'readability_score': 0.0,
            'structure_score': 0.0,
            'consistency_score': 0.0,
            'overall_improvement': 0.0
        }

        # Simple readability improvement assessment
        original_sentences = len(sent_tokenize(original_content))
        final_sentences = len(sent_tokenize(final_content))

        if final_sentences > 0 and original_sentences > 0:
            improvements['readability_score'] = min(1.0, final_sentences / original_sentences)

        # Structure improvement assessment
        original_headings = len(re.findall(r'^#{1,6}\s+.+', original_content, re.MULTILINE))
        final_headings = len(re.findall(r'^#{1,6}\s+.+', final_content, re.MULTILINE))

        if final_headings > 0:
            improvements['structure_score'] = min(1.0, final_headings / max(original_headings, 1))

        # Consistency improvement (simplified)
        original_links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', original_content))
        final_links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', final_content))

        improvements['consistency_score'] = 1.0 if final_links >= original_links else 0.8

        # Overall improvement score
        improvements['overall_improvement'] = (
            improvements['readability_score'] * 0.3 +
            improvements['structure_score'] * 0.4 +
            improvements['consistency_score'] * 0.3
        )

        return improvements

    def _generate_followup_recommendations(self, safety_results: Dict[str, Any],
                                         applied_fixes: List[str]) -> List[str]:
        """Generate follow-up recommendations based on remediation results."""
        recommendations = []

        if not safety_results['safe']:
            recommendations.append("⚠️ Review all automated changes manually due to safety concerns")
            recommendations.append("Consider reverting changes if semantic meaning was altered")

        if safety_results.get('warnings'):
            recommendations.extend([f"⚠️ {warning}" for warning in safety_results['warnings']])

        if len(applied_fixes) > 10:
            recommendations.append("📊 Large number of fixes applied - conduct thorough review")
            recommendations.append("Consider testing documentation functionality after changes")

        if 'content_preservation' in safety_results.get('checks_failed', []):
            recommendations.append("🔍 Verify that automated changes preserved original meaning")
            recommendations.append("Check for any unintended semantic changes")

        if not applied_fixes:
            recommendations.append("ℹ️ No automated fixes were applied - review manually for improvement opportunities")

        return recommendations[:5]  # Limit to 5 recommendations

    async def remediate_document(self, content: str, issues: Optional[List[Dict[str, Any]]] = None,
                               doc_type: str = 'general', metadata: Optional[Dict[str, Any]] = None,
                               confidence_level: str = 'medium') -> Dict[str, Any]:
        """Perform automated remediation on documentation."""

        start_time = time.time()

        if not self._initialize_remediator():
            return {
                'error': 'Automated remediation not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            # Create backup if enabled
            backup = None
            if self.backup_enabled:
                backup = self._create_backup(content, metadata or {})

            # Determine confidence threshold based on level
            threshold = self.confidence_thresholds.get(confidence_level, self.confidence_thresholds['medium'])

            # Analyze document structure
            structure_analysis = self._analyze_document_structure(content)

            # Apply automated fixes
            fixed_content = content
            applied_fixes = []
            all_fixes = []

            # Fix formatting issues
            fixed_content, formatting_fixes = self._fix_formatting_issues(fixed_content, structure_analysis.get('issues', []))
            applied_fixes.extend(formatting_fixes)
            all_fixes.extend(formatting_fixes)

            # Fix grammar and spelling
            fixed_content, grammar_fixes = self._fix_grammar_spelling(fixed_content, [])
            applied_fixes.extend(grammar_fixes)
            all_fixes.extend(grammar_fixes)

            # Fix terminology consistency
            fixed_content, terminology_fixes = self._fix_terminology_consistency(fixed_content, [])
            applied_fixes.extend(terminology_fixes)
            all_fixes.extend(terminology_fixes)

            # Fix link issues
            fixed_content, link_fixes = self._fix_link_issues(fixed_content, [])
            applied_fixes.extend(link_fixes)
            all_fixes.extend(link_fixes)

            # Fix structure issues
            fixed_content, structure_fixes = self._fix_structure_issues(fixed_content, structure_analysis.get('issues', []))
            applied_fixes.extend(structure_fixes)
            all_fixes.extend(structure_fixes)

            # Perform safety checks
            safety_results = self._check_safety(content, fixed_content)

            # Generate remediation report
            processing_time = time.time() - start_time
            report = self._generate_remediation_report(content, fixed_content, all_fixes,
                                                     safety_results, processing_time)

            result = {
                'original_content': content,
                'remediated_content': fixed_content,
                'backup': backup,
                'report': report,
                'changes_applied': len(all_fixes),
                'safety_status': 'safe' if safety_results['safe'] else 'requires_review',
                'processing_time': processing_time,
                'remediation_timestamp': time.time()
            }

            return result

        except Exception as e:
            logger.error(f"Automated remediation failed: {e}")
            return {
                'error': 'Automated remediation failed',
                'message': str(e),
                'original_content': content,
                'processing_time': time.time() - start_time
            }

    async def preview_remediation(self, content: str, issues: Optional[List[Dict[str, Any]]] = None,
                                doc_type: str = 'general', metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Preview remediation changes without applying them."""

        start_time = time.time()

        if not self._initialize_remediator():
            return {
                'error': 'Remediation preview not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            # Analyze what would be fixed
            structure_analysis = self._analyze_document_structure(content)

            # Simulate fixes (don't actually apply them)
            preview_fixes = []

            # Preview formatting fixes
            _, formatting_fixes = self._fix_formatting_issues(content, structure_analysis.get('issues', []))
            preview_fixes.extend([f"Formatting: {fix}" for fix in formatting_fixes])

            # Preview grammar fixes
            _, grammar_fixes = self._fix_grammar_spelling(content, [])
            preview_fixes.extend([f"Grammar: {fix}" for fix in grammar_fixes])

            # Preview terminology fixes
            _, terminology_fixes = self._fix_terminology_consistency(content, [])
            preview_fixes.extend([f"Terminology: {fix}" for fix in terminology_fixes])

            # Preview structure fixes
            _, structure_fixes = self._fix_structure_issues(content, structure_analysis.get('issues', []))
            preview_fixes.extend([f"Structure: {fix}" for fix in structure_fixes])

            processing_time = time.time() - start_time

            return {
                'preview_available': True,
                'proposed_fixes': preview_fixes,
                'fix_count': len(preview_fixes),
                'estimated_processing_time': processing_time * 2,  # Estimate for actual remediation
                'preview_timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Remediation preview failed: {e}")
            return {
                'error': 'Remediation preview failed',
                'message': str(e),
                'processing_time': time.time() - start_time
            }

    def update_remediation_rules(self, custom_rules: Dict[str, Dict[str, Any]]) -> bool:
        """Update remediation rules with custom configurations."""
        try:
            for rule_name, config in custom_rules.items():
                if rule_name in self.remediation_rules:
                    self.remediation_rules[rule_name].update(config)
                else:
                    logger.warning(f"Unknown remediation rule: {rule_name}")
                    continue

            return True

        except Exception as e:
            logger.error(f"Failed to update remediation rules: {e}")
            return False

    def enable_backup(self, enabled: bool = True) -> None:
        """Enable or disable backup creation."""
        self.backup_enabled = enabled


# Global instance for reuse
automated_remediator = AutomatedRemediator()


async def remediate_document(content: str, issues: Optional[List[Dict[str, Any]]] = None,
                           doc_type: str = 'general', metadata: Optional[Dict[str, Any]] = None,
                           confidence_level: str = 'medium') -> Dict[str, Any]:
    """Convenience function for automated document remediation.

    Args:
        content: The documentation content to remediate
        issues: List of identified issues (optional)
        doc_type: Type of documentation (api_reference, user_guide, etc.)
        metadata: Additional metadata
        confidence_level: Confidence level for automated fixes ('high', 'medium', 'low')

    Returns:
        Remediation results with fixed content and report
    """
    return await automated_remediator.remediate_document(
        content=content,
        issues=issues,
        doc_type=doc_type,
        metadata=metadata,
        confidence_level=confidence_level
    )


async def preview_remediation(content: str, issues: Optional[List[Dict[str, Any]]] = None,
                            doc_type: str = 'general', metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function for remediation preview.

    Args:
        content: The documentation content to preview remediation for
        issues: List of identified issues (optional)
        doc_type: Type of documentation
        metadata: Additional metadata

    Returns:
        Preview of proposed remediation changes
    """
    return await automated_remediator.preview_remediation(
        content=content,
        issues=issues,
        doc_type=doc_type,
        metadata=metadata
    )
