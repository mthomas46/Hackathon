"""Peer Review Enhancement module for Summarizer Hub.

Provides AI-assisted code review capabilities specifically focused on documentation quality,
offering comprehensive feedback, suggestions, and best practice recommendations.
"""

import time
import logging
import re
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from collections import defaultdict, Counter
import json

try:
    import nltk
    from nltk.tokenize import sent_tokenize, word_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    import spacy
    from textblob import TextBlob
    import language_tool_python
    PEER_REVIEW_AVAILABLE = True
except ImportError:
    PEER_REVIEW_AVAILABLE = False
    nltk = None
    spacy = None
    TextBlob = None
    language_tool_python = None

from services.shared.core.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes

logger = logging.getLogger(__name__)


class PeerReviewEnhancer:
    """Enhances documentation quality through AI-assisted peer review."""

    def __init__(self):
        """Initialize the peer review enhancer."""
        self.initialized = False
        self.quality_criteria = self._get_quality_criteria()
        self.best_practices = self._get_best_practices()
        self.review_categories = self._get_review_categories()
        self._initialize_enhancer()

    def _extract_document_features(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from document for peer review analysis."""
        content = document_data.get('content', '')
        metadata = document_data.get('metadata', {})

        features = {
            'document_id': document_data.get('document_id', ''),
            'title': document_data.get('title', ''),
            'document_type': document_data.get('document_type', 'unknown'),
            'tags': document_data.get('tags', []),
            'word_count': len(content.split()) if content else 0,
            'character_count': len(content) if content else 0,
            'code_blocks': len(re.findall(r'```[\s\S]*?```', content)),
            'links': len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)),
            'headings': len(re.findall(r'^#{1,6}\s+.+', content, re.MULTILINE)),
            'api_endpoints': len(re.findall(r'`(GET|POST|PUT|DELETE|PATCH)\s+[^`]+`', content)),
            'technical_terms': self._extract_technical_terms(content),
            'stakeholder_groups': self._identify_stakeholder_groups(document_data),
            'business_criticality': metadata.get('business_criticality', 'medium')
        }

        return features

    def _extract_technical_terms(self, content: str) -> List[str]:
        """Extract technical terms from document content."""
        # Common technical terms and patterns
        technical_patterns = [
            r'\b(API|REST|HTTP|JSON|XML|database|authentication|authorization)\b',
            r'\b(function|method|class|interface|component|service)\b',
            r'\b(configuration|deployment|integration|migration|upgrade)\b',
            r'\b(security|encryption|authentication|authorization|SSL|TLS)\b',
            r'\b(performance|optimization|caching|load\s+balancing)\b',
            r'\b(error|exception|handling|debugging|logging|monitoring)\b'
        ]

        technical_terms = []
        for pattern in technical_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            technical_terms.extend(matches)

        return list(set(technical_terms))  # Remove duplicates

    def _identify_stakeholder_groups(self, document_data: Dict[str, Any]) -> List[str]:
        """Identify stakeholder groups affected by the document."""
        content = document_data.get('content', '').lower()
        document_type = document_data.get('document_type', '').lower()
        tags = [tag.lower() for tag in document_data.get('tags', [])]

        stakeholder_groups = []

        # Analyze content for stakeholder indicators
        if any(term in content for term in ['user', 'customer', 'end-user', 'consumer']):
            stakeholder_groups.append('end_users')
        if any(term in content for term in ['developer', 'engineer', 'programmer', 'coder']):
            stakeholder_groups.append('developers')
        if any(term in content for term in ['admin', 'administrator', 'operator', 'devops']):
            stakeholder_groups.append('administrators')
        if any(term in content for term in ['manager', 'lead', 'architect', 'director']):
            stakeholder_groups.append('management')
        if any(term in content for term in ['security', 'compliance', 'audit', 'governance']):
            stakeholder_groups.append('security_compliance')
        if any(term in content for term in ['support', 'helpdesk', 'customer service']):
            stakeholder_groups.append('support_team')

        # Analyze document type
        if document_type in ['api_reference', 'developer_guide']:
            stakeholder_groups.extend(['developers', 'administrators'])
        elif document_type in ['user_guide', 'tutorial', 'getting_started']:
            stakeholder_groups.extend(['end_users', 'support_team'])
        elif document_type in ['security', 'compliance']:
            stakeholder_groups.extend(['security_compliance', 'management'])
        elif document_type in ['internal', 'architecture']:
            stakeholder_groups.extend(['developers', 'management'])

        # Analyze tags
        if 'api' in tags or 'integration' in tags:
            stakeholder_groups.extend(['developers', 'administrators'])
        if 'security' in tags or 'compliance' in tags:
            stakeholder_groups.extend(['security_compliance', 'management'])

        return list(set(stakeholder_groups))  # Remove duplicates

    def _initialize_enhancer(self) -> bool:
        """Initialize the peer review enhancement components."""
        if not PEER_REVIEW_AVAILABLE:
            logger.warning("Peer review enhancement dependencies not available")
            return False

        try:
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('wordnet', quiet=True)

            # Initialize NLP components
            self.lemmatizer = WordNetLemmatizer()
            self.stop_words = set(stopwords.words('english'))

            # Initialize grammar checker
            self.grammar_tool = language_tool_python.LanguageTool('en-US')

            self.initialized = True
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize NLP components: {e}")
            return False

    def _get_quality_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Define quality criteria for documentation review."""
        return {
            'completeness': {
                'weight': 0.25,
                'description': 'Content completeness and coverage',
                'checks': ['introduction_coverage', 'prerequisites_coverage', 'examples_coverage', 'troubleshooting_coverage'],
                'thresholds': {'excellent': 0.9, 'good': 0.75, 'fair': 0.6, 'poor': 0.4}
            },
            'accuracy': {
                'weight': 0.20,
                'description': 'Technical accuracy and correctness',
                'checks': ['factual_accuracy', 'technical_correctness', 'consistency_check', 'version_accuracy'],
                'thresholds': {'excellent': 0.95, 'good': 0.85, 'fair': 0.7, 'poor': 0.5}
            },
            'clarity': {
                'weight': 0.18,
                'description': 'Clarity and readability',
                'checks': ['sentence_complexity', 'vocabulary_appropriateness', 'structure_clarity', 'logical_flow'],
                'thresholds': {'excellent': 0.9, 'good': 0.75, 'fair': 0.6, 'poor': 0.4}
            },
            'structure': {
                'weight': 0.15,
                'description': 'Organization and structure',
                'checks': ['heading_hierarchy', 'section_organization', 'navigation_aids', 'content_chunking'],
                'thresholds': {'excellent': 0.9, 'good': 0.75, 'fair': 0.6, 'poor': 0.4}
            },
            'compliance': {
                'weight': 0.12,
                'description': 'Standards and best practices compliance',
                'checks': ['style_guide_compliance', 'accessibility_compliance', 'seo_optimization', 'brand_consistency'],
                'thresholds': {'excellent': 0.9, 'good': 0.75, 'fair': 0.6, 'poor': 0.4}
            },
            'engagement': {
                'weight': 0.10,
                'description': 'User engagement and effectiveness',
                'checks': ['tone_appropriateness', 'audience_targeting', 'actionability', 'value_proposition'],
                'thresholds': {'excellent': 0.85, 'good': 0.7, 'fair': 0.55, 'poor': 0.35}
            }
        }

    def _get_best_practices(self) -> Dict[str, List[str]]:
        """Define documentation best practices."""
        return {
            'content_structure': [
                'Use clear, descriptive headings that accurately reflect content',
                'Maintain consistent heading hierarchy (H1 → H2 → H3)',
                'Include a table of contents for documents longer than 3 sections',
                'Use bullet points and numbered lists for better readability',
                'Break long paragraphs into shorter, digestible chunks'
            ],
            'writing_style': [
                'Use active voice instead of passive voice when possible',
                'Write in second person (you) for user-facing documentation',
                'Keep sentences under 25 words for better comprehension',
                'Use consistent terminology throughout the document',
                'Avoid jargon or explain it when necessary'
            ],
            'technical_accuracy': [
                'Verify all code examples work with current versions',
                'Include version information for APIs and tools mentioned',
                'Test all links and references for accessibility',
                'Ensure command-line examples include expected outputs',
                'Validate that screenshots match the current interface'
            ],
            'user_experience': [
                'Start with the most common use cases or problems',
                'Include search keywords in headings and early content',
                'Provide examples before detailed explanations',
                'Include troubleshooting sections for common issues',
                'End with next steps or related documentation links'
            ],
            'accessibility': [
                'Use alt text for all images and screenshots',
                'Ensure sufficient color contrast for text readability',
                'Use descriptive link text instead of "click here"',
                'Structure content logically for screen readers',
                'Include captions for tables and complex diagrams'
            ]
        }

    def _get_review_categories(self) -> Dict[str, Dict[str, Any]]:
        """Define review categories and their priorities."""
        return {
            'critical': {
                'priority': 'high',
                'issues': ['broken_links', 'incorrect_information', 'missing_prerequisites', 'security_vulnerabilities'],
                'description': 'Issues that prevent proper use or pose security risks'
            },
            'major': {
                'priority': 'medium',
                'issues': ['outdated_information', 'missing_examples', 'poor_structure', 'grammar_errors'],
                'description': 'Issues that significantly impact usability or comprehension'
            },
            'minor': {
                'priority': 'low',
                'issues': ['style_inconsistencies', 'formatting_issues', 'wording_improvements', 'minor_typos'],
                'description': 'Issues that could be improved but don\'t prevent proper use'
            },
            'enhancement': {
                'priority': 'lowest',
                'issues': ['additional_examples', 'cross_references', 'accessibility_improvements', 'seo_optimization'],
                'description': 'Suggestions for making documentation even better'
            }
        }

    def _analyze_content_completeness(self, content: str, doc_type: str) -> Dict[str, Any]:
        """Analyze content completeness for the given document type."""
        analysis = {
            'score': 0.5,
            'issues': [],
            'suggestions': []
        }

        # Define required sections based on document type
        required_sections = {
            'api_reference': ['authentication', 'endpoints', 'parameters', 'examples', 'errors'],
            'user_guide': ['introduction', 'prerequisites', 'steps', 'examples', 'troubleshooting'],
            'tutorial': ['overview', 'prerequisites', 'steps', 'examples', 'next_steps'],
            'architecture': ['overview', 'components', 'data_flow', 'deployment', 'monitoring'],
            'troubleshooting': ['symptoms', 'causes', 'solutions', 'prevention', 'references']
        }

        expected_sections = required_sections.get(doc_type, ['introduction', 'content', 'examples'])
        content_lower = content.lower()

        found_sections = 0
        missing_sections = []

        for section in expected_sections:
            # Check for section presence using various patterns
            patterns = [
                f'# {section}',
                f'## {section}',
                f'### {section}',
                section.replace('_', ' '),
                section.replace('_', '-')
            ]

            section_found = any(pattern.lower() in content_lower for pattern in patterns)
            if section_found:
                found_sections += 1
            else:
                missing_sections.append(section)

        # Calculate completeness score
        completeness_ratio = found_sections / len(expected_sections)
        analysis['score'] = min(1.0, completeness_ratio + 0.2)  # Boost for partial coverage

        # Generate issues and suggestions
        if missing_sections:
            analysis['issues'].append(f"Missing sections: {', '.join(missing_sections[:3])}")
            analysis['suggestions'].append(f"Consider adding sections for: {', '.join(missing_sections)}")

        if completeness_ratio < 0.6:
            analysis['issues'].append("Content appears incomplete - missing key information")
        elif completeness_ratio < 0.8:
            analysis['suggestions'].append("Content coverage could be improved with additional sections")

        return analysis

    def _analyze_technical_accuracy(self, content: str) -> Dict[str, Any]:
        """Analyze technical accuracy and correctness."""
        analysis = {
            'score': 0.7,
            'issues': [],
            'suggestions': []
        }

        # Check for version information
        version_patterns = [
            r'v\d+\.\d+',
            r'version \d+',
            r'release \d+',
            r'updated.*\d{4}'
        ]

        has_version_info = any(re.search(pattern, content, re.IGNORECASE) for pattern in version_patterns)

        if not has_version_info:
            analysis['issues'].append("Missing version information for APIs, tools, or software mentioned")
            analysis['suggestions'].append("Include version numbers and compatibility information")
            analysis['score'] -= 0.1

        # Check for code examples
        code_blocks = len(re.findall(r'```[\s\S]*?```', content))
        if code_blocks == 0:
            analysis['issues'].append("No code examples found - consider adding practical examples")
            analysis['suggestions'].append("Add code snippets, command examples, or configuration samples")
            analysis['score'] -= 0.15

        # Check for links and references
        links = len(re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content))
        if links == 0:
            analysis['suggestions'].append("Consider adding links to related documentation or external resources")

        # Check for outdated language patterns
        outdated_terms = ['old', 'deprecated', 'obsolete', 'no longer supported']
        outdated_count = sum(1 for term in outdated_terms if term in content.lower())

        if outdated_count > 2:
            analysis['issues'].append("Multiple references to outdated or deprecated features")
            analysis['suggestions'].append("Review and update references to deprecated features")

        return analysis

    def _analyze_clarity_and_readability(self, content: str) -> Dict[str, Any]:
        """Analyze clarity and readability."""
        analysis = {
            'score': 0.7,
            'issues': [],
            'suggestions': []
        }

        # Tokenize content
        sentences = sent_tokenize(content)
        words = word_tokenize(content)

        if not sentences or not words:
            analysis['score'] = 0.3
            analysis['issues'].append("Content appears to be poorly structured or incomplete")
            return analysis

        # Calculate readability metrics
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)

        # Check sentence complexity
        complex_sentences = [s for s in sentences if len(word_tokenize(s)) > 30]
        if len(complex_sentences) > len(sentences) * 0.3:
            analysis['issues'].append("Many sentences are overly complex and hard to read")
            analysis['suggestions'].append("Break down long sentences into shorter, clearer statements")
            analysis['score'] -= 0.15

        # Check for passive voice (simple heuristic)
        passive_indicators = ['is', 'are', 'was', 'were', 'be', 'been', 'being']
        passive_sentences = 0

        for sentence in sentences:
            words_in_sentence = word_tokenize(sentence.lower())
            if any(indicator in words_in_sentence for indicator in passive_indicators):
                passive_sentences += 1

        passive_ratio = passive_sentences / len(sentences)
        if passive_ratio > 0.4:
            analysis['suggestions'].append("Consider using more active voice to improve clarity")
            analysis['score'] -= 0.1

        # Check for jargon density
        technical_terms = ['api', 'endpoint', 'authentication', 'configuration', 'deployment']
        technical_count = sum(1 for word in words if word.lower() in technical_terms)

        if technical_count > len(words) * 0.1:  # More than 10% technical terms
            analysis['suggestions'].append("Consider defining technical terms or providing a glossary")
            analysis['score'] -= 0.05

        return analysis

    def _analyze_structure_and_organization(self, content: str) -> Dict[str, Any]:
        """Analyze structure and organization."""
        analysis = {
            'score': 0.7,
            'issues': [],
            'suggestions': []
        }

        # Analyze heading hierarchy
        headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
        heading_levels = [len(level) for level, _ in headings]

        # Check for proper heading hierarchy
        if heading_levels:
            # Check if hierarchy starts with H1
            if 1 not in heading_levels:
                analysis['issues'].append("Document should start with H1 heading")
                analysis['score'] -= 0.1

            # Check for logical progression
            sorted_levels = sorted(set(heading_levels))
            expected_progression = list(range(min(sorted_levels), max(sorted_levels) + 1))

            if sorted_levels != expected_progression:
                analysis['issues'].append("Heading hierarchy is not logical or has gaps")
                analysis['suggestions'].append("Use consistent heading levels (H1→H2→H3) without skipping levels")
                analysis['score'] -= 0.1

        # Check for table of contents
        toc_indicators = ['table of contents', 'contents', 'navigation']
        has_toc = any(indicator in content.lower() for indicator in toc_indicators)

        if len(headings) > 5 and not has_toc:
            analysis['suggestions'].append("Consider adding a table of contents for better navigation")
            analysis['score'] -= 0.05

        # Check for lists and structure
        bullet_points = len(re.findall(r'^[\s]*[-\*\+]\s+', content, re.MULTILINE))
        numbered_lists = len(re.findall(r'^[\s]*\d+\.\s+', content, re.MULTILINE))

        if bullet_points == 0 and numbered_lists == 0 and len(sentences) > 10:
            analysis['suggestions'].append("Consider using bullet points or numbered lists to improve readability")
            analysis['score'] -= 0.05

        return analysis

    def _analyze_grammar_and_style(self, content: str) -> Dict[str, Any]:
        """Analyze grammar and writing style."""
        analysis = {
            'score': 0.8,
            'issues': [],
            'suggestions': []
        }

        try:
            # Check grammar and spelling (sample check due to performance)
            sample_text = content[:2000]  # Check first 2000 chars for performance
            matches = self.grammar_tool.check(sample_text)

            if matches:
                error_count = len(matches)
                analysis['issues'].append(f"Found {error_count} potential grammar/spelling issues")

                # Categorize errors
                error_types = Counter(match.rule.category for match in matches)
                common_errors = error_types.most_common(3)

                for error_type, count in common_errors:
                    if error_type == 'GRAMMAR':
                        analysis['suggestions'].append("Review sentence structure and grammar")
                    elif error_type == 'SPELLING':
                        analysis['suggestions'].append("Check spelling and consider using spell check")
                    elif error_type == 'STYLE':
                        analysis['suggestions'].append("Review writing style and consistency")

                analysis['score'] -= min(0.2, error_count * 0.02)  # Reduce score for errors

        except Exception as e:
            logger.warning(f"Grammar check failed: {e}")
            analysis['issues'].append("Could not perform automated grammar check")

        # Check for consistency in terminology
        words = word_tokenize(content.lower())
        words = [w for w in words if w.isalnum() and w not in self.stop_words]

        # Look for common inconsistent terms
        inconsistent_pairs = [
            (['api', 'apis'], 'API vs APIs'),
            (['database', 'db'], 'database vs db'),
            (['user', 'users'], 'user vs users'),
            (['server', 'servers'], 'server vs servers')
        ]

        for terms, description in inconsistent_pairs:
            term_counts = {term: words.count(term) for term in terms if term in terms}
            if len([count for count in term_counts.values() if count > 0]) > 1:
                analysis['suggestions'].append(f"Inconsistent terminology: {description}")
                analysis['score'] -= 0.05

        return analysis

    def _generate_overall_review_score(self, criteria_scores: Dict[str, float]) -> Dict[str, Any]:
        """Generate overall review score from individual criteria."""
        if not criteria_scores:
            return {
                'overall_score': 0.5,
                'grade': 'C',
                'description': 'Insufficient data for comprehensive review'
            }

        # Calculate weighted average
        total_weight = sum(criterion['weight'] for criterion in self.quality_criteria.values())
        weighted_sum = sum(
            criteria_scores.get(criterion_name, 0.5) * criterion_config['weight']
            for criterion_name, criterion_config in self.quality_criteria.items()
        )

        overall_score = weighted_sum / total_weight if total_weight > 0 else 0.5

        # Assign grade
        if overall_score >= 0.9:
            grade = 'A'
            description = 'Excellent documentation quality'
        elif overall_score >= 0.8:
            grade = 'B'
            description = 'Good documentation quality with minor improvements needed'
        elif overall_score >= 0.7:
            grade = 'C'
            description = 'Average documentation quality requiring attention'
        elif overall_score >= 0.6:
            grade = 'D'
            description = 'Below average quality needing significant improvements'
        else:
            grade = 'F'
            description = 'Poor documentation quality requiring major revisions'

        return {
            'overall_score': round(overall_score, 3),
            'grade': grade,
            'description': description
        }

    def _generate_review_feedback(self, criteria_analyses: Dict[str, Dict[str, Any]],
                                overall_score: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehensive review feedback."""
        feedback = []

        # Overall assessment
        feedback.append({
            'type': 'overall_assessment',
            'priority': 'high',
            'title': f'Overall Quality: {overall_score["grade"]}',
            'message': overall_score['description'],
            'score': overall_score['overall_score']
        })

        # Individual criteria feedback
        for criterion_name, analysis in criteria_analyses.items():
            if analysis['issues']:
                feedback.append({
                    'type': 'issue',
                    'priority': self._determine_feedback_priority(criterion_name, analysis),
                    'category': criterion_name,
                    'title': f'{criterion_name.replace("_", " ").title()} Issues',
                    'message': '; '.join(analysis['issues']),
                    'score': analysis['score']
                })

            if analysis['suggestions']:
                feedback.append({
                    'type': 'suggestion',
                    'priority': 'medium',
                    'category': criterion_name,
                    'title': f'{criterion_name.replace("_", " ").title()} Suggestions',
                    'message': '; '.join(analysis['suggestions'][:2]),  # Limit suggestions
                    'score': analysis['score']
                })

        # Best practices recommendations
        feedback.append({
            'type': 'best_practices',
            'priority': 'low',
            'title': 'Best Practices Recommendations',
            'message': 'Consider following documentation best practices for improved quality',
            'recommendations': self.best_practices
        })

        return feedback

    def _determine_feedback_priority(self, criterion_name: str, analysis: Dict[str, Any]) -> str:
        """Determine feedback priority based on criterion and issues."""
        if criterion_name in ['accuracy', 'completeness'] and analysis['score'] < 0.6:
            return 'high'
        elif analysis['score'] < 0.5:
            return 'high'
        elif analysis['score'] < 0.7:
            return 'medium'
        else:
            return 'low'

    async def review_documentation(self, content: str, doc_type: str = 'general',
                                 title: str = '', metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform comprehensive peer review of documentation."""

        start_time = time.time()

        if not self._initialize_enhancer():
            return {
                'error': 'Peer review enhancement not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            # Initialize analysis results
            criteria_analyses = {}
            criteria_scores = {}

            # Analyze each quality criterion
            criteria_analyses['completeness'] = self._analyze_content_completeness(content, doc_type)
            criteria_scores['completeness'] = criteria_analyses['completeness']['score']

            criteria_analyses['accuracy'] = self._analyze_technical_accuracy(content)
            criteria_scores['accuracy'] = criteria_analyses['accuracy']['score']

            criteria_analyses['clarity'] = self._analyze_clarity_and_readability(content)
            criteria_scores['clarity'] = criteria_analyses['clarity']['score']

            criteria_analyses['structure'] = self._analyze_structure_and_organization(content)
            criteria_scores['structure'] = criteria_analyses['structure']['score']

            criteria_analyses['compliance'] = self._analyze_grammar_and_style(content)
            criteria_scores['compliance'] = criteria_analyses['compliance']['score']

            # Calculate engagement score based on other factors
            engagement_score = (criteria_scores['clarity'] + criteria_scores['structure']) / 2
            criteria_analyses['engagement'] = {
                'score': engagement_score,
                'issues': [],
                'suggestions': ['Consider user engagement best practices for better adoption']
            }
            criteria_scores['engagement'] = engagement_score

            # Generate overall assessment
            overall_assessment = self._generate_overall_review_score(criteria_scores)

            # Generate feedback
            feedback = self._generate_review_feedback(criteria_analyses, overall_assessment)

            processing_time = time.time() - start_time

            return {
                'document_title': title or 'Untitled Document',
                'document_type': doc_type,
                'overall_assessment': overall_assessment,
                'criteria_analyses': criteria_analyses,
                'criteria_scores': criteria_scores,
                'feedback': feedback,
                'review_summary': self._generate_review_summary(overall_assessment, feedback),
                'processing_time': processing_time,
                'review_timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Documentation peer review failed: {e}")
            return {
                'error': 'Documentation peer review failed',
                'message': str(e),
                'document_title': title or 'Untitled Document',
                'processing_time': time.time() - start_time
            }

    def _generate_review_summary(self, overall_assessment: Dict[str, Any],
                               feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive review summary."""
        summary = {
            'grade': overall_assessment['grade'],
            'score': overall_assessment['overall_score'],
            'description': overall_assessment['description']
        }

        # Count issues by priority
        issue_counts = {'high': 0, 'medium': 0, 'low': 0}
        suggestion_counts = {'high': 0, 'medium': 0, 'low': 0}

        for item in feedback:
            if item['type'] == 'issue':
                priority = item.get('priority', 'medium')
                issue_counts[priority] = issue_counts.get(priority, 0) + 1
            elif item['type'] == 'suggestion':
                priority = item.get('priority', 'medium')
                suggestion_counts[priority] = suggestion_counts.get(priority, 0) + 1

        summary['issues_found'] = sum(issue_counts.values())
        summary['suggestions_provided'] = sum(suggestion_counts.values())
        summary['issues_by_priority'] = issue_counts
        summary['suggestions_by_priority'] = suggestion_counts

        # Generate improvement roadmap
        if overall_assessment['grade'] in ['A', 'B']:
            summary['improvement_roadmap'] = 'Maintain current quality standards and consider minor enhancements'
        elif overall_assessment['grade'] == 'C':
            summary['improvement_roadmap'] = 'Focus on addressing high-priority issues and implementing suggested improvements'
        else:
            summary['improvement_roadmap'] = 'Comprehensive review and revision required - consider starting over with best practices'

        return summary

    async def compare_document_versions(self, old_content: str, new_content: str,
                                      doc_type: str = 'general') -> Dict[str, Any]:
        """Compare two versions of documentation to assess improvements."""

        start_time = time.time()

        if not self._initialize_enhancer():
            return {
                'error': 'Document comparison not available',
                'message': 'Required dependencies not installed or initialization failed'
            }

        try:
            # Review both versions
            old_review = await self.review_documentation(old_content, doc_type, 'Previous Version')
            new_review = await self.review_documentation(new_content, doc_type, 'Current Version')

            if 'error' in old_review or 'error' in new_review:
                return {
                    'error': 'Document comparison failed',
                    'message': 'Failed to review one or both document versions'
                }

            # Compare assessments
            comparison = {
                'old_version': {
                    'score': old_review['overall_assessment']['overall_score'],
                    'grade': old_review['overall_assessment']['grade']
                },
                'new_version': {
                    'score': new_review['overall_assessment']['overall_score'],
                    'grade': new_review['overall_assessment']['grade']
                },
                'improvement': {
                    'score_change': new_review['overall_assessment']['overall_score'] - old_review['overall_assessment']['overall_score'],
                    'grade_change': f"{old_review['overall_assessment']['grade']} → {new_review['overall_assessment']['grade']}"
                }
            }

            # Analyze specific improvements
            improvements = []
            regressions = []

            for criterion in self.quality_criteria.keys():
                old_score = old_review['criteria_scores'].get(criterion, 0)
                new_score = new_review['criteria_scores'].get(criterion, 0)
                score_diff = new_score - old_score

                if score_diff > 0.1:
                    improvements.append(f"{criterion.replace('_', ' ').title()}: +{score_diff:.2f}")
                elif score_diff < -0.1:
                    regressions.append(f"{criterion.replace('_', ' ').title()}: {score_diff:.2f}")

            comparison['improvements'] = improvements
            comparison['regressions'] = regressions

            processing_time = time.time() - start_time

            return {
                'comparison': comparison,
                'old_review': old_review,
                'new_review': new_review,
                'processing_time': processing_time,
                'comparison_timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"Document version comparison failed: {e}")
            return {
                'error': 'Document version comparison failed',
                'message': str(e),
                'processing_time': time.time() - start_time
            }


# Global instance for reuse
peer_review_enhancer = PeerReviewEnhancer()


async def review_documentation(content: str, doc_type: str = 'general',
                             title: str = '', metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Convenience function for documentation peer review.

    Args:
        content: The documentation content to review
        doc_type: Type of documentation (api_reference, user_guide, etc.)
        title: Document title
        metadata: Additional metadata

    Returns:
        Comprehensive peer review results
    """
    return await peer_review_enhancer.review_documentation(content, doc_type, title, metadata)


async def compare_document_versions(old_content: str, new_content: str,
                                  doc_type: str = 'general') -> Dict[str, Any]:
    """Convenience function for comparing document versions.

    Args:
        old_content: Previous version content
        new_content: Current version content
        doc_type: Type of documentation

    Returns:
        Comparison results between versions
    """
    return await peer_review_enhancer.compare_document_versions(old_content, new_content, doc_type)
