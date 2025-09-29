"""Cross-Repository Analysis module for Analysis Service.

Provides comprehensive analysis capabilities across multiple repositories,
identifying patterns, inconsistencies, and opportunities for documentation
improvement at the organizational level.
"""

import time
import logging
import json
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio
import re

try:
    from services.shared.core.responses import create_success_response, create_error_response
    from services.shared.core.constants_new import ErrorCodes
except ImportError:
    # Fallback for testing or when shared services are not available
    def create_success_response(message, data=None, **kwargs):
        return {"message": message, "data": data, "status": "success"}

    def create_error_response(message, error_code=None, **kwargs):
        return {"message": message, "error": error_code, "status": "error"}

    class ErrorCodes:
        ANALYSIS_FAILED = "ANALYSIS_FAILED"

logger = logging.getLogger(__name__)


class CrossRepositoryAnalyzer:
    """Intelligent system for cross-repository documentation analysis."""

    def __init__(self):
        """Initialize the cross-repository analyzer."""
        self.initialized = False
        self.analysis_frameworks = self._get_analysis_frameworks()
        self.repository_connectors = self._get_repository_connectors()
        self.analysis_cache = {}
        self.max_workers = 10
        self._initialize_analyzer()

    def _initialize_analyzer(self) -> bool:
        """Initialize the cross-repository analysis components."""
        try:
            # Initialize analysis frameworks
            self._setup_analysis_frameworks()
            self.initialized = True
            logger.info("Cross-repository analyzer initialized successfully")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize cross-repository analyzer: {e}")
            self.initialized = False
            return False

    def _get_analysis_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Define analysis frameworks for cross-repository analysis."""
        return {
            'consistency_analysis': {
                'description': 'Analyze consistency across repositories',
                'metrics': ['terminology_consistency', 'style_consistency', 'structure_consistency'],
                'weight': 0.25,
                'thresholds': {'excellent': 0.9, 'good': 0.75, 'fair': 0.6}
            },
            'coverage_analysis': {
                'description': 'Analyze documentation coverage across repositories',
                'metrics': ['topic_coverage', 'depth_coverage', 'breadth_coverage'],
                'weight': 0.20,
                'thresholds': {'excellent': 0.9, 'good': 0.75, 'fair': 0.6}
            },
            'quality_analysis': {
                'description': 'Analyze overall documentation quality across repositories',
                'metrics': ['quality_consistency', 'standards_compliance', 'best_practices_adoption'],
                'weight': 0.25,
                'thresholds': {'excellent': 0.9, 'good': 0.75, 'fair': 0.6}
            },
            'redundancy_analysis': {
                'description': 'Identify redundant or overlapping documentation',
                'metrics': ['duplicate_content', 'overlapping_topics', 'consolidation_opportunities'],
                'weight': 0.15,
                'thresholds': {'excellent': 0.1, 'good': 0.2, 'fair': 0.3}  # Lower is better
            },
            'dependency_analysis': {
                'description': 'Analyze documentation dependencies across repositories',
                'metrics': ['cross_references', 'dependency_clarity', 'integration_documentation'],
                'weight': 0.15,
                'thresholds': {'excellent': 0.9, 'good': 0.75, 'fair': 0.6}
            }
        }

    def _get_repository_connectors(self) -> Dict[str, Dict[str, Any]]:
        """Define connectors for different repository systems."""
        return {
            'github': {
                'description': 'GitHub repository connector',
                'supported_features': ['api_access', 'webhook_support', 'file_listing', 'content_retrieval'],
                'authentication_methods': ['token', 'oauth'],
                'rate_limits': {'requests_per_hour': 5000}
            },
            'gitlab': {
                'description': 'GitLab repository connector',
                'supported_features': ['api_access', 'webhook_support', 'file_listing', 'content_retrieval'],
                'authentication_methods': ['token', 'oauth'],
                'rate_limits': {'requests_per_hour': 2000}
            },
            'bitbucket': {
                'description': 'Bitbucket repository connector',
                'supported_features': ['api_access', 'webhook_support', 'file_listing', 'content_retrieval'],
                'authentication_methods': ['token', 'oauth'],
                'rate_limits': {'requests_per_hour': 1000}
            },
            'azure_devops': {
                'description': 'Azure DevOps repository connector',
                'supported_features': ['api_access', 'webhook_support', 'file_listing', 'content_retrieval'],
                'authentication_methods': ['token', 'oauth'],
                'rate_limits': {'requests_per_hour': 3000}
            },
            'filesystem': {
                'description': 'Local filesystem repository connector',
                'supported_features': ['file_listing', 'content_retrieval', 'local_analysis'],
                'authentication_methods': ['none'],
                'rate_limits': {'requests_per_hour': float('inf')}
            }
        }

    def _setup_analysis_frameworks(self) -> None:
        """Set up analysis frameworks and metrics."""
        # Initialize analysis metrics and thresholds
        self.analysis_metrics = {
            'terminology_consistency': {
                'description': 'Consistency of technical terminology across repositories',
                'calculation_method': 'semantic_similarity',
                'target_range': [0.8, 1.0]
            },
            'style_consistency': {
                'description': 'Consistency of writing style and formatting',
                'calculation_method': 'pattern_matching',
                'target_range': [0.7, 1.0]
            },
            'structure_consistency': {
                'description': 'Consistency of document structure and organization',
                'calculation_method': 'structural_analysis',
                'target_range': [0.8, 1.0]
            },
            'topic_coverage': {
                'description': 'Coverage of topics across repositories',
                'calculation_method': 'topic_modeling',
                'target_range': [0.6, 1.0]
            },
            'depth_coverage': {
                'description': 'Depth of documentation coverage',
                'calculation_method': 'content_analysis',
                'target_range': [0.7, 1.0]
            },
            'breadth_coverage': {
                'description': 'Breadth of documentation coverage',
                'calculation_method': 'coverage_analysis',
                'target_range': [0.8, 1.0]
            },
            'duplicate_content': {
                'description': 'Amount of duplicate content across repositories',
                'calculation_method': 'similarity_detection',
                'target_range': [0.0, 0.2]  # Lower is better
            },
            'overlapping_topics': {
                'description': 'Overlap in topic coverage between repositories',
                'calculation_method': 'topic_overlap_analysis',
                'target_range': [0.3, 0.7]  # Moderate overlap is good
            }
        }

    def _analyze_repository_structure(self, repository_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the structure and content of a repository."""
        repo_analysis = {
            'repository_id': repository_data.get('repository_id', ''),
            'repository_name': repository_data.get('repository_name', ''),
            'documentation_files': [],
            'documentation_structure': {},
            'code_files': [],
            'configuration_files': [],
            'total_files': 0,
            'documentation_ratio': 0.0,
            'last_updated': repository_data.get('last_updated', ''),
            'branch': repository_data.get('branch', 'main'),
            'commit_sha': repository_data.get('commit_sha', '')
        }

        # Analyze files in the repository
        files = repository_data.get('files', [])
        repo_analysis['total_files'] = len(files)

        for file_info in files:
            file_path = file_info.get('path', '')
            file_type = self._classify_file_type(file_path)

            if file_type == 'documentation':
                repo_analysis['documentation_files'].append(file_info)
            elif file_type == 'code':
                repo_analysis['code_files'].append(file_info)
            elif file_type == 'configuration':
                repo_analysis['configuration_files'].append(file_info)

        # Calculate documentation ratio
        if repo_analysis['total_files'] > 0:
            repo_analysis['documentation_ratio'] = len(repo_analysis['documentation_files']) / repo_analysis['total_files']

        # Analyze documentation structure
        repo_analysis['documentation_structure'] = self._analyze_documentation_structure(repo_analysis['documentation_files'])

        return repo_analysis

    def _classify_file_type(self, file_path: str) -> str:
        """Classify file type based on path and extension."""
        # Documentation file patterns
        doc_patterns = [
            r'\.md$', r'\.rst$', r'\.txt$', r'\.adoc$', r'\.wiki$',
            r'README', r'CHANGELOG', r'HISTORY', r'CONTRIBUTING',
            r'docs/', r'documentation/', r'wiki/', r'help/'
        ]

        # Code file patterns
        code_patterns = [
            r'\.py$', r'\.js$', r'\.ts$', r'\.java$', r'\.cpp$', r'\.c$', r'\.h$',
            r'\.cs$', r'\.php$', r'\.rb$', r'\.go$', r'\.rs$', r'\.scala$',
            r'\.kt$', r'\.swift$', r'\.dart$', r'\.lua$', r'\.perl$'
        ]

        # Configuration file patterns
        config_patterns = [
            r'\.yml$', r'\.yaml$', r'\.json$', r'\.toml$', r'\.ini$', r'\.cfg$',
            r'\.xml$', r'\.properties$', r'Dockerfile', r'\.dockerfile$',
            r'package\.json$', r'requirements\.txt$', r'\.lock$', r'\.sum$'
        ]

        file_path_lower = file_path.lower()

        for pattern in doc_patterns:
            if re.search(pattern, file_path_lower, re.IGNORECASE):
                return 'documentation'

        for pattern in code_patterns:
            if re.search(pattern, file_path_lower, re.IGNORECASE):
                return 'code'

        for pattern in config_patterns:
            if re.search(pattern, file_path_lower, re.IGNORECASE):
                return 'configuration'

        return 'other'

    def _analyze_documentation_structure(self, documentation_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the structure of documentation files."""
        structure_analysis = {
            'total_docs': len(documentation_files),
            'file_types': Counter(),
            'directory_structure': defaultdict(list),
            'content_types': Counter(),
            'readme_files': 0,
            'api_docs': 0,
            'user_guides': 0,
            'tutorials': 0,
            'architecture_docs': 0,
            'troubleshooting_docs': 0
        }

        for file_info in documentation_files:
            file_path = file_info.get('path', '')
            file_name = file_path.split('/')[-1].lower()

            # Count file types
            if file_path.endswith('.md'):
                structure_analysis['file_types']['markdown'] += 1
            elif file_path.endswith('.rst'):
                structure_analysis['file_types']['rst'] += 1
            elif file_path.endswith('.txt'):
                structure_analysis['file_types']['text'] += 1

            # Analyze directory structure
            directory = '/'.join(file_path.split('/')[:-1])
            structure_analysis['directory_structure'][directory].append(file_path)

            # Classify content types
            if 'readme' in file_name:
                structure_analysis['readme_files'] += 1
                structure_analysis['content_types']['readme'] += 1
            elif 'api' in file_name or 'endpoint' in file_name:
                structure_analysis['api_docs'] += 1
                structure_analysis['content_types']['api'] += 1
            elif 'guide' in file_name or 'manual' in file_name:
                structure_analysis['user_guides'] += 1
                structure_analysis['content_types']['guide'] += 1
            elif 'tutorial' in file_name or 'getting-started' in file_name:
                structure_analysis['tutorials'] += 1
                structure_analysis['content_types']['tutorial'] += 1
            elif 'architecture' in file_name or 'design' in file_name:
                structure_analysis['architecture_docs'] += 1
                structure_analysis['content_types']['architecture'] += 1
            elif 'troubleshoot' in file_name or 'faq' in file_name:
                structure_analysis['troubleshooting_docs'] += 1
                structure_analysis['content_types']['troubleshooting'] += 1

        return structure_analysis

    def _calculate_consistency_metrics(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate consistency metrics across repositories."""
        consistency_metrics = {
            'terminology_consistency': 0.0,
            'style_consistency': 0.0,
            'structure_consistency': 0.0,
            'terminology_variations': {},
            'style_variations': {},
            'structure_variations': {}
        }

        if len(repositories) < 2:
            return consistency_metrics

        # Extract common terms and patterns from all repositories
        all_terms = set()
        all_styles = set()
        all_structures = set()

        for repo in repositories:
            # Extract terms from documentation files
            for doc_file in repo.get('documentation_files', []):
                content = doc_file.get('content', '')
                terms = self._extract_technical_terms(content)
                all_terms.update(terms)

            # Extract style patterns
            style_patterns = self._extract_style_patterns(repo)
            all_styles.update(style_patterns)

            # Extract structure patterns
            structure_patterns = self._extract_structure_patterns(repo)
            all_structures.update(structure_patterns)

        # Calculate consistency scores
        consistency_metrics['terminology_consistency'] = self._calculate_term_consistency(all_terms, repositories)
        consistency_metrics['style_consistency'] = self._calculate_style_consistency(all_styles, repositories)
        consistency_metrics['structure_consistency'] = self._calculate_structure_consistency(all_structures, repositories)

        return consistency_metrics

    def _extract_technical_terms(self, content: str) -> Set[str]:
        """Extract technical terms from content."""
        technical_patterns = [
            r'\b(API|REST|HTTP|JSON|XML|database|authentication|authorization)\b',
            r'\b(function|method|class|interface|component|service)\b',
            r'\b(configuration|deployment|integration|migration|upgrade)\b',
            r'\b(security|encryption|authentication|authorization|SSL|TLS)\b'
        ]

        terms = set()
        for pattern in technical_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            terms.update(matches)

        return terms

    def _extract_style_patterns(self, repository: Dict[str, Any]) -> Set[str]:
        """Extract style patterns from repository."""
        style_patterns = set()

        for doc_file in repository.get('documentation_files', []):
            content = doc_file.get('content', '')

            # Check for consistent heading styles
            if re.search(r'^#{1,6}\s+.+', content, re.MULTILINE):
                style_patterns.add('markdown_headings')

            # Check for consistent list styles
            if re.search(r'^[\s]*[-\*\+]\s+', content, re.MULTILINE):
                style_patterns.add('bullet_lists')

            # Check for consistent code block styles
            if re.search(r'```[\s\S]*?```', content):
                style_patterns.add('code_blocks')

        return style_patterns

    def _extract_structure_patterns(self, repository: Dict[str, Any]) -> Set[str]:
        """Extract structure patterns from repository."""
        structure_patterns = set()

        doc_structure = repository.get('documentation_structure', {})

        # Check for common documentation patterns
        if doc_structure.get('readme_files', 0) > 0:
            structure_patterns.add('has_readme')

        if doc_structure.get('api_docs', 0) > 0:
            structure_patterns.add('has_api_docs')

        if doc_structure.get('user_guides', 0) > 0:
            structure_patterns.add('has_user_guides')

        # Check directory structure
        directory_structure = doc_structure.get('directory_structure', {})
        if len(directory_structure) > 1:
            structure_patterns.add('organized_directories')

        return structure_patterns

    def _calculate_term_consistency(self, all_terms: Set[str], repositories: List[Dict[str, Any]]) -> float:
        """Calculate terminology consistency across repositories."""
        if not all_terms or len(repositories) < 2:
            return 0.0

        # Calculate how many repositories use each term
        term_usage = {}
        for term in all_terms:
            term_usage[term] = 0
            for repo in repositories:
                repo_terms = set()
                for doc_file in repo.get('documentation_files', []):
                    content = doc_file.get('content', '')
                    repo_terms.update(self._extract_technical_terms(content))

                if term in repo_terms:
                    term_usage[term] += 1

        # Calculate consistency score
        total_terms = len(all_terms)
        consistent_terms = sum(1 for count in term_usage.values() if count == len(repositories))

        return consistent_terms / total_terms if total_terms > 0 else 0.0

    def _calculate_style_consistency(self, all_styles: Set[str], repositories: List[Dict[str, Any]]) -> float:
        """Calculate style consistency across repositories."""
        if not all_styles or len(repositories) < 2:
            return 0.0

        # Calculate how many repositories use each style
        style_usage = {}
        for style in all_styles:
            style_usage[style] = 0
            for repo in repositories:
                repo_styles = self._extract_style_patterns(repo)
                if style in repo_styles:
                    style_usage[style] += 1

        # Calculate consistency score
        total_styles = len(all_styles)
        consistent_styles = sum(1 for count in style_usage.values() if count == len(repositories))

        return consistent_styles / total_styles if total_styles > 0 else 0.0

    def _calculate_structure_consistency(self, all_structures: Set[str], repositories: List[Dict[str, Any]]) -> float:
        """Calculate structure consistency across repositories."""
        if not all_structures or len(repositories) < 2:
            return 0.0

        # Calculate how many repositories have each structure element
        structure_usage = {}
        for structure in all_structures:
            structure_usage[structure] = 0
            for repo in repositories:
                repo_structures = self._extract_structure_patterns(repo)
                if structure in repo_structures:
                    structure_usage[structure] += 1

        # Calculate consistency score
        total_structures = len(all_structures)
        consistent_structures = sum(1 for count in structure_usage.values() if count == len(repositories))

        return consistent_structures / total_structures if total_structures > 0 else 0.0

    def _analyze_coverage_gaps(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze coverage gaps across repositories."""
        coverage_analysis = {
            'topic_coverage': {},
            'missing_topics': [],
            'under_documented_areas': [],
            'over_documented_areas': [],
            'coverage_score': 0.0
        }

        # Define expected documentation topics
        expected_topics = {
            'getting_started': ['readme', 'getting-started', 'quick-start', 'setup'],
            'api_documentation': ['api', 'endpoint', 'swagger', 'openapi'],
            'user_guides': ['guide', 'manual', 'how-to', 'tutorial'],
            'troubleshooting': ['troubleshoot', 'faq', 'error', 'debug'],
            'architecture': ['architecture', 'design', 'system', 'overview'],
            'security': ['security', 'authentication', 'authorization', 'ssl'],
            'deployment': ['deploy', 'installation', 'setup', 'configuration'],
            'contributing': ['contribute', 'developer', 'guidelines', 'standards']
        }

        # Check topic coverage across repositories
        for topic, keywords in expected_topics.items():
            coverage_analysis['topic_coverage'][topic] = {
                'keywords': keywords,
                'repositories_with_topic': 0,
                'total_repositories': len(repositories)
            }

            for repo in repositories:
                has_topic = False
                for doc_file in repo.get('documentation_files', []):
                    content = doc_file.get('content', '').lower()
                    if any(keyword in content for keyword in keywords):
                        has_topic = True
                        break

                if has_topic:
                    coverage_analysis['topic_coverage'][topic]['repositories_with_topic'] += 1

        # Identify missing topics
        for topic, coverage in coverage_analysis['topic_coverage'].items():
            coverage_ratio = coverage['repositories_with_topic'] / coverage['total_repositories']
            if coverage_ratio < 0.5:  # Less than 50% coverage
                coverage_analysis['missing_topics'].append({
                    'topic': topic,
                    'coverage_ratio': coverage_ratio,
                    'keywords': coverage['keywords']
                })

        # Calculate overall coverage score
        total_topics = len(expected_topics)
        well_covered_topics = sum(1 for coverage in coverage_analysis['topic_coverage'].values()
                                if coverage['repositories_with_topic'] / coverage['total_repositories'] >= 0.7)

        coverage_analysis['coverage_score'] = well_covered_topics / total_topics if total_topics > 0 else 0.0

        return coverage_analysis

    def _identify_redundancies(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify redundant or overlapping documentation."""
        redundancy_analysis = {
            'duplicate_files': [],
            'similar_content': [],
            'overlapping_topics': [],
            'consolidation_opportunities': [],
            'redundancy_score': 0.0
        }

        # Check for duplicate file names across repositories
        file_names = defaultdict(list)
        for repo in repositories:
            repo_name = repo.get('repository_name', '')
            for doc_file in repo.get('documentation_files', []):
                file_name = doc_file.get('path', '').split('/')[-1]
                file_names[file_name].append(repo_name)

        # Identify files that exist in multiple repositories
        for file_name, repo_list in file_names.items():
            if len(repo_list) > 1:
                redundancy_analysis['duplicate_files'].append({
                    'file_name': file_name,
                    'repositories': repo_list,
                    'occurrence_count': len(repo_list)
                })

        # Simple content similarity check (in a real implementation, this would use more sophisticated similarity detection)
        content_hashes = defaultdict(list)
        for repo in repositories:
            repo_name = repo.get('repository_name', '')
            for doc_file in repo.get('documentation_files', []):
                content = doc_file.get('content', '')
                # Simple hash-based similarity (real implementation would use semantic similarity)
                content_hash = hash(content[:1000])  # Hash first 1000 chars
                content_hashes[content_hash].append({
                    'repository': repo_name,
                    'file_path': doc_file.get('path', ''),
                    'content_length': len(content)
                })

        # Identify similar content
        for content_hash, files in content_hashes.items():
            if len(files) > 1:
                redundancy_analysis['similar_content'].append({
                    'content_hash': content_hash,
                    'files': files,
                    'similarity_count': len(files)
                })

        # Calculate redundancy score (lower is better)
        total_docs = sum(len(repo.get('documentation_files', [])) for repo in repositories)
        duplicate_docs = len(redundancy_analysis['duplicate_files']) + len(redundancy_analysis['similar_content'])

        redundancy_analysis['redundancy_score'] = duplicate_docs / total_docs if total_docs > 0 else 0.0

        return redundancy_analysis

    def _generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate recommendations based on analysis results."""
        recommendations = []

        # Consistency recommendations
        consistency_metrics = analysis_results.get('consistency_analysis', {})
        if consistency_metrics.get('terminology_consistency', 0) < 0.7:
            recommendations.append({
                'type': 'consistency',
                'priority': 'high',
                'category': 'terminology',
                'title': 'Standardize Technical Terminology',
                'description': 'Inconsistent use of technical terms across repositories',
                'impact': 'High - affects documentation clarity and user experience',
                'effort': 'Medium - requires coordination across teams',
                'suggested_actions': [
                    'Create a shared terminology glossary',
                    'Review and standardize key technical terms',
                    'Implement automated terminology checking in CI/CD'
                ]
            })

        # Coverage recommendations
        coverage_analysis = analysis_results.get('coverage_analysis', {})
        missing_topics = coverage_analysis.get('missing_topics', [])
        if missing_topics:
            recommendations.append({
                'type': 'coverage',
                'priority': 'medium',
                'category': 'documentation_gaps',
                'title': 'Address Documentation Coverage Gaps',
                'description': f'Missing documentation for {len(missing_topics)} key topics',
                'impact': 'Medium - affects user onboarding and support',
                'effort': 'High - requires content creation',
                'suggested_actions': [
                    f'Create documentation for: {", ".join([t["topic"] for t in missing_topics[:3]])}',
                    'Audit existing documentation coverage',
                    'Prioritize missing topics by user impact'
                ]
            })

        # Redundancy recommendations
        redundancy_analysis = analysis_results.get('redundancy_analysis', {})
        duplicate_files = redundancy_analysis.get('duplicate_files', [])
        if duplicate_files:
            recommendations.append({
                'type': 'efficiency',
                'priority': 'low',
                'category': 'redundancy',
                'title': 'Consolidate Duplicate Documentation',
                'description': f'Found {len(duplicate_files)} potentially duplicate files',
                'impact': 'Low - affects maintenance efficiency',
                'effort': 'Medium - requires content review and consolidation',
                'suggested_actions': [
                    'Review duplicate files for consolidation opportunities',
                    'Create shared documentation components',
                    'Establish guidelines for documentation organization'
                ]
            })

        return recommendations

    async def analyze_repositories(self, repositories: List[Dict[str, Any]],
                                 analysis_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform comprehensive cross-repository analysis."""

        start_time = time.time()

        try:
            if not repositories:
                return {
                    'error': 'No repositories provided for analysis',
                    'message': 'At least one repository is required'
                }

            # Default analysis types
            if not analysis_types:
                analysis_types = ['consistency_analysis', 'coverage_analysis',
                                'quality_analysis', 'redundancy_analysis']

            analysis_results = {
                'repository_count': len(repositories),
                'repositories_analyzed': [],
                'analysis_types': analysis_types,
                'consistency_analysis': {},
                'coverage_analysis': {},
                'quality_analysis': {},
                'redundancy_analysis': {},
                'dependency_analysis': {},
                'overall_score': 0.0,
                'recommendations': [],
                'processing_time': 0.0,
                'analysis_timestamp': time.time()
            }

            # Analyze each repository
            repository_analyses = []
            for repo_data in repositories:
                repo_analysis = self._analyze_repository_structure(repo_data)
                repository_analyses.append(repo_analysis)
                analysis_results['repositories_analyzed'].append({
                    'repository_id': repo_analysis['repository_id'],
                    'repository_name': repo_analysis['repository_name'],
                    'documentation_files': len(repo_analysis['documentation_files']),
                    'documentation_ratio': repo_analysis['documentation_ratio']
                })

            # Perform cross-repository analyses
            if 'consistency_analysis' in analysis_types:
                analysis_results['consistency_analysis'] = self._calculate_consistency_metrics(repository_analyses)

            if 'coverage_analysis' in analysis_types:
                analysis_results['coverage_analysis'] = self._analyze_coverage_gaps(repository_analyses)

            if 'redundancy_analysis' in analysis_types:
                analysis_results['redundancy_analysis'] = self._identify_redundancies(repository_analyses)

            # Calculate overall score
            analysis_results['overall_score'] = self._calculate_overall_score(analysis_results)

            # Generate recommendations
            analysis_results['recommendations'] = self._generate_recommendations(analysis_results)

            processing_time = time.time() - start_time
            analysis_results['processing_time'] = processing_time

            return analysis_results

        except Exception as e:
            logger.error(f"Cross-repository analysis failed: {e}")
            return {
                'error': 'Cross-repository analysis failed',
                'message': str(e),
                'repository_count': len(repositories),
                'processing_time': time.time() - start_time
            }

    def _calculate_overall_score(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate overall cross-repository analysis score."""
        scores = []

        # Consistency score (weighted)
        consistency = analysis_results.get('consistency_analysis', {})
        if consistency:
            consistency_score = (
                consistency.get('terminology_consistency', 0) * 0.4 +
                consistency.get('style_consistency', 0) * 0.3 +
                consistency.get('structure_consistency', 0) * 0.3
            )
            scores.append((consistency_score, 0.25))

        # Coverage score
        coverage = analysis_results.get('coverage_analysis', {})
        if coverage:
            coverage_score = coverage.get('coverage_score', 0)
            scores.append((coverage_score, 0.20))

        # Quality score (placeholder - would be calculated from individual repo quality scores)
        scores.append((0.75, 0.25))  # Placeholder

        # Redundancy score (lower is better, so invert)
        redundancy = analysis_results.get('redundancy_analysis', {})
        if redundancy:
            redundancy_score = 1.0 - min(redundancy.get('redundancy_score', 0), 1.0)
            scores.append((redundancy_score, 0.15))

        # Dependency score (placeholder)
        scores.append((0.7, 0.15))  # Placeholder

        # Calculate weighted average
        total_weight = sum(weight for _, weight in scores)
        if total_weight == 0:
            return 0.0

        weighted_sum = sum(score * weight for score, weight in scores)
        return weighted_sum / total_weight

    async def analyze_repository_connectivity(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze connectivity and dependencies between repositories."""

        start_time = time.time()

        try:
            connectivity_analysis = {
                'repository_count': len(repositories),
                'cross_references': [],
                'shared_dependencies': [],
                'integration_points': [],
                'connectivity_score': 0.0,
                'processing_time': 0.0
            }

            # Analyze cross-references between repositories
            for i, repo1 in enumerate(repositories):
                for j, repo2 in enumerate(repositories):
                    if i != j:
                        cross_refs = self._find_cross_references(repo1, repo2)
                        if cross_refs:
                            connectivity_analysis['cross_references'].append({
                                'from_repository': repo1.get('repository_name', ''),
                                'to_repository': repo2.get('repository_name', ''),
                                'references': cross_refs
                            })

            # Calculate connectivity score based on cross-references
            total_possible_refs = len(repositories) * (len(repositories) - 1)
            actual_refs = len(connectivity_analysis['cross_references'])

            connectivity_analysis['connectivity_score'] = actual_refs / total_possible_refs if total_possible_refs > 0 else 0.0
            connectivity_analysis['processing_time'] = time.time() - start_time

            return connectivity_analysis

        except Exception as e:
            logger.error(f"Repository connectivity analysis failed: {e}")
            return {
                'error': 'Repository connectivity analysis failed',
                'message': str(e),
                'processing_time': time.time() - start_time
            }

    def _find_cross_references(self, repo1: Dict[str, Any], repo2: Dict[str, Any]) -> List[str]:
        """Find cross-references between two repositories."""
        references = []

        repo1_name = repo1.get('repository_name', '').lower()
        repo2_name = repo2.get('repository_name', '').lower()

        # Check for repository name mentions in documentation
        for doc_file in repo1.get('documentation_files', []):
            content = doc_file.get('content', '').lower()
            if repo2_name in content:
                references.append(f"{doc_file.get('path', '')} mentions {repo2_name}")

        for doc_file in repo2.get('documentation_files', []):
            content = doc_file.get('content', '').lower()
            if repo1_name in content:
                references.append(f"{doc_file.get('path', '')} mentions {repo1_name}")

        return references

    def configure_repository_connector(self, connector_type: str, config: Dict[str, Any]) -> bool:
        """Configure a repository connector."""
        try:
            if connector_type not in self.repository_connectors:
                logger.warning(f"Unknown connector type: {connector_type}")
                return False

            # Store configuration (in a real implementation, this would set up API connections)
            self.repository_connectors[connector_type]['config'] = config
            logger.info(f"Configured {connector_type} connector")
            return True

        except Exception as e:
            logger.error(f"Failed to configure repository connector: {e}")
            return False

    def get_supported_connectors(self) -> List[str]:
        """Get list of supported repository connectors."""
        return list(self.repository_connectors.keys())

    def get_analysis_frameworks(self) -> Dict[str, Dict[str, Any]]:
        """Get available analysis frameworks."""
        return self.analysis_frameworks


# Global instance for reuse
cross_repository_analyzer = CrossRepositoryAnalyzer()


async def analyze_repositories(repositories: List[Dict[str, Any]],
                             analysis_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convenience function for cross-repository analysis.

    Args:
        repositories: List of repository data to analyze
        analysis_types: Types of analysis to perform

    Returns:
        Comprehensive cross-repository analysis results
    """
    return await cross_repository_analyzer.analyze_repositories(repositories, analysis_types)
