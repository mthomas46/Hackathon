"""Tests for cross-repository analysis functionality in Analysis Service.

Tests the cross-repository analyzer module and its integration with the analysis service.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'services'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'services', 'analysis-service'))

from modules.cross_repository_analyzer import (
    CrossRepositoryAnalyzer,
    analyze_repositories
)


@pytest.fixture
def sample_repository_data():
    """Create sample repository data for cross-repository analysis testing."""
    return [
        {
            'repository_id': 'repo-1',
            'repository_name': 'api-service',
            'branch': 'main',
            'commit_sha': 'abc123',
            'files': [
                {
                    'path': 'docs/api/README.md',
                    'content': '''
                    # API Service Documentation

                    This service provides REST API for user management.

                    ## Authentication
                    Use OAuth 2.0 with API keys.

                    ## Endpoints
                    - GET /users
                    - POST /users
                    - PUT /users/{id}
                    '''
                },
                {
                    'path': 'docs/api/endpoints.md',
                    'content': '''
                    # API Endpoints

                    ## GET /users
                    Retrieves users from the system.

                    ## POST /users
                    Creates a new user account.
                    '''
                },
                {
                    'path': 'src/main.py',
                    'content': '# Main application file'
                }
            ]
        },
        {
            'repository_id': 'repo-2',
            'repository_name': 'frontend-app',
            'branch': 'main',
            'commit_sha': 'def456',
            'files': [
                {
                    'path': 'docs/user-guide.md',
                    'content': '''
                    # User Guide

                    Welcome to our application.

                    ## Getting Started
                    First, create your account.

                    ## Features
                    - User management
                    - Data visualization
                    - Reports
                    '''
                },
                {
                    'path': 'docs/api-integration.md',
                    'content': '''
                    # API Integration

                    This guide shows how to integrate with our API service.

                    ## Authentication
                    Use the same OAuth flow as the API service.

                    ## Making Requests
                    Use the endpoints documented in the API service repo.
                    '''
                },
                {
                    'path': 'src/app.js',
                    'content': '// Main application file'
                }
            ]
        },
        {
            'repository_id': 'repo-3',
            'repository_name': 'data-service',
            'branch': 'main',
            'commit_sha': 'ghi789',
            'files': [
                {
                    'path': 'docs/architecture.md',
                    'content': '''
                    # System Architecture

                    ## Components
                    - API Service
                    - Frontend App
                    - Data Service

                    ## Data Flow
                    Frontend → API → Data Service
                    '''
                },
                {
                    'path': 'docs/data-models.md',
                    'content': '''
                    # Data Models

                    ## User Model
                    - id: integer
                    - name: string
                    - email: string

                    ## API Integration
                    See API service documentation for integration details.
                    '''
                },
                {
                    'path': 'src/database.py',
                    'content': '# Database connection file'
                }
            ]
        }
    ]


class TestCrossRepositoryAnalyzer:
    """Test the CrossRepositoryAnalyzer class."""

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test successful initialization of the cross-repository analyzer."""
        analyzer = CrossRepositoryAnalyzer()
        assert analyzer.initialized is True
        assert len(analyzer.analysis_frameworks) > 0
        assert len(analyzer.repository_connectors) > 0

    @pytest.mark.asyncio
    async def test_analyze_repository_structure(self, sample_repository_data):
        """Test repository structure analysis."""
        analyzer = CrossRepositoryAnalyzer()

        repo_analysis = analyzer._analyze_repository_structure(sample_repository_data[0])

        assert repo_analysis['repository_id'] == 'repo-1'
        assert repo_analysis['repository_name'] == 'api-service'
        assert len(repo_analysis['documentation_files']) > 0
        assert len(repo_analysis['code_files']) > 0
        assert repo_analysis['documentation_ratio'] > 0
        assert 'documentation_structure' in repo_analysis

    @pytest.mark.asyncio
    async def test_classify_file_type(self):
        """Test file type classification."""
        analyzer = CrossRepositoryAnalyzer()

        test_cases = [
            ('docs/api/README.md', 'documentation'),
            ('src/main.py', 'code'),
            ('docs/user-guide.rst', 'documentation'),
            ('src/app.js', 'code'),
            ('docker-compose.yml', 'configuration'),
            ('README.md', 'documentation'),
            ('package.json', 'configuration'),
            ('unknown.xyz', 'other')
        ]

        for file_path, expected_type in test_cases:
            result_type = analyzer._classify_file_type(file_path)
            assert result_type == expected_type, f"Failed for {file_path}: expected {expected_type}, got {result_type}"

    @pytest.mark.asyncio
    async def test_analyze_documentation_structure(self, sample_repository_data):
        """Test documentation structure analysis."""
        analyzer = CrossRepositoryAnalyzer()

        doc_files = sample_repository_data[0]['files'][:2]  # First two are documentation
        structure = analyzer._analyze_documentation_structure(doc_files)

        assert structure['total_docs'] == 2
        assert 'file_types' in structure
        assert 'directory_structure' in structure
        assert 'content_types' in structure

    @pytest.mark.asyncio
    async def test_calculate_consistency_metrics(self, sample_repository_data):
        """Test consistency metrics calculation."""
        analyzer = CrossRepositoryAnalyzer()

        # Create repository analyses
        repo_analyses = []
        for repo_data in sample_repository_data:
            analysis = analyzer._analyze_repository_structure(repo_data)
            repo_analyses.append(analysis)

        consistency = analyzer._calculate_consistency_metrics(repo_analyses)

        assert 'terminology_consistency' in consistency
        assert 'style_consistency' in consistency
        assert 'structure_consistency' in consistency
        assert isinstance(consistency['terminology_consistency'], float)
        assert 0.0 <= consistency['terminology_consistency'] <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_coverage_gaps(self, sample_repository_data):
        """Test coverage gap analysis."""
        analyzer = CrossRepositoryAnalyzer()

        # Create repository analyses
        repo_analyses = []
        for repo_data in sample_repository_data:
            analysis = analyzer._analyze_repository_structure(repo_data)
            repo_analyses.append(analysis)

        coverage = analyzer._analyze_coverage_gaps(repo_analyses)

        assert 'topic_coverage' in coverage
        assert 'missing_topics' in coverage
        assert 'coverage_score' in coverage
        assert isinstance(coverage['coverage_score'], float)
        assert 0.0 <= coverage['coverage_score'] <= 1.0

    @pytest.mark.asyncio
    async def test_identify_redundancies(self, sample_repository_data):
        """Test redundancy identification."""
        analyzer = CrossRepositoryAnalyzer()

        # Create repository analyses
        repo_analyses = []
        for repo_data in sample_repository_data:
            analysis = analyzer._analyze_repository_structure(repo_data)
            repo_analyses.append(analysis)

        redundancies = analyzer._identify_redundancies(repo_analyses)

        assert 'duplicate_files' in redundancies
        assert 'similar_content' in redundancies
        assert 'redundancy_score' in redundancies
        assert isinstance(redundancies['redundancy_score'], float)

    @pytest.mark.asyncio
    async def test_analyze_repositories_full(self, sample_repository_data):
        """Test full cross-repository analysis."""
        analyzer = CrossRepositoryAnalyzer()

        result = await analyzer.analyze_repositories(sample_repository_data)

        assert 'repository_count' in result
        assert 'repositories_analyzed' in result
        assert 'analysis_types' in result
        assert 'consistency_analysis' in result
        assert 'coverage_analysis' in result
        assert 'redundancy_analysis' in result
        assert 'overall_score' in result
        assert 'recommendations' in result
        assert 'processing_time' in result

        assert result['repository_count'] == 3
        assert len(result['repositories_analyzed']) == 3
        assert isinstance(result['overall_score'], float)
        assert 0.0 <= result['overall_score'] <= 1.0

    @pytest.mark.asyncio
    async def test_analyze_repository_connectivity(self, sample_repository_data):
        """Test repository connectivity analysis."""
        analyzer = CrossRepositoryAnalyzer()

        result = await analyzer.analyze_repository_connectivity(sample_repository_data)

        assert 'repository_count' in result
        assert 'cross_references' in result
        assert 'connectivity_score' in result
        assert 'processing_time' in result

        assert result['repository_count'] == 3
        assert isinstance(result['connectivity_score'], float)
        assert 0.0 <= result['connectivity_score'] <= 1.0

    @pytest.mark.asyncio
    async def test_find_cross_references(self, sample_repository_data):
        """Test cross-reference finding between repositories."""
        analyzer = CrossRepositoryAnalyzer()

        repo1 = sample_repository_data[0]
        repo2 = sample_repository_data[1]

        references = analyzer._find_cross_references(repo1, repo2)

        assert isinstance(references, list)
        # Should find references to API service in frontend app docs

    @pytest.mark.asyncio
    async def test_configure_repository_connector(self):
        """Test repository connector configuration."""
        analyzer = CrossRepositoryAnalyzer()

        config = {
            'base_url': 'https://api.github.com',
            'token': 'fake-token'
        }

        success = analyzer.configure_repository_connector('github', config)
        assert success is True

    @pytest.mark.asyncio
    async def test_get_supported_connectors(self):
        """Test getting supported connectors."""
        analyzer = CrossRepositoryAnalyzer()

        connectors = analyzer.get_supported_connectors()
        assert isinstance(connectors, list)
        assert len(connectors) > 0
        assert 'github' in connectors

    @pytest.mark.asyncio
    async def test_get_analysis_frameworks(self):
        """Test getting analysis frameworks."""
        analyzer = CrossRepositoryAnalyzer()

        frameworks = analyzer.get_analysis_frameworks()
        assert isinstance(frameworks, dict)
        assert len(frameworks) > 0
        assert 'consistency_analysis' in frameworks

    @pytest.mark.asyncio
    async def test_analyze_repositories_minimal(self):
        """Test cross-repository analysis with minimal data."""
        analyzer = CrossRepositoryAnalyzer()

        minimal_repos = [
            {
                'repository_id': 'test-repo',
                'repository_name': 'test',
                'files': [
                    {
                        'path': 'README.md',
                        'content': '# Test Repository\nThis is a test.'
                    }
                ]
            }
        ]

        result = await analyzer.analyze_repositories(minimal_repos)

        assert result['repository_count'] == 1
        assert 'overall_score' in result
        assert 'recommendations' in result

    @pytest.mark.asyncio
    async def test_analyze_repositories_empty(self):
        """Test cross-repository analysis with empty repository list."""
        analyzer = CrossRepositoryAnalyzer()

        result = await analyzer.analyze_repositories([])

        assert 'error' in result
        assert 'At least one repository is required' in result['message']


@pytest.mark.asyncio
class TestCrossRepositoryIntegration:
    """Test the integration functions."""

    @pytest.mark.asyncio
    async def test_analyze_repositories_function(self, sample_repository_data):
        """Test the convenience function for cross-repository analysis."""
        with patch('modules.cross_repository_analyzer.analyze_repositories') as mock_analyze:
            mock_analyze.return_value = {
                'repository_count': 3,
                'repositories_analyzed': [],
                'analysis_types': ['consistency_analysis'],
                'consistency_analysis': {'terminology_consistency': 0.8},
                'coverage_analysis': {},
                'redundancy_analysis': {},
                'overall_score': 0.75,
                'recommendations': [],
                'processing_time': 2.5,
                'analysis_timestamp': 1234567890
            }

            result = await analyze_repositories(sample_repository_data)

            assert result['repository_count'] == 3
            assert result['overall_score'] == 0.75
            mock_analyze.assert_called_once()


class TestCrossRepositoryHandlers:
    """Test the analysis handlers integration."""

    @pytest.fixture
    def mock_service_client(self):
        """Mock service client for testing."""
        client = Mock()
        client.doc_store_url.return_value = "http://docstore:5000"
        client.get_json = Mock()
        return client

    @pytest.mark.asyncio
    async def test_handle_cross_repository_analysis_success(self, mock_service_client, sample_repository_data):
        """Test successful cross-repository analysis handling."""
        from modules.models import CrossRepositoryAnalysisRequest

        with patch('modules.cross_repository_analyzer.analyze_repositories') as mock_analyze:

            mock_analyze.return_value = {
                'repository_count': 3,
                'repositories_analyzed': [],
                'analysis_types': ['consistency_analysis'],
                'consistency_analysis': {'terminology_consistency': 0.8},
                'coverage_analysis': {},
                'redundancy_analysis': {},
                'overall_score': 0.75,
                'recommendations': [],
                'processing_time': 2.5,
                'analysis_timestamp': 1234567890
            }

            request = CrossRepositoryAnalysisRequest(
                repositories=sample_repository_data,
                analysis_types=['consistency_analysis']
            )

            # Import the handler method
            from modules.analysis_handlers import AnalysisHandlers

            result = await AnalysisHandlers.handle_cross_repository_analysis(request)

            assert result.repository_count == 3
            assert result.overall_score == 0.75
            assert len(result.analysis_types) > 0

    @pytest.mark.asyncio
    async def test_handle_repository_connectivity_success(self, mock_service_client, sample_repository_data):
        """Test successful repository connectivity analysis handling."""
        from modules.models import RepositoryConnectivityRequest

        with patch('modules.cross_repository_analyzer.cross_repository_analyzer') as mock_analyzer:

            mock_analyzer.analyze_repository_connectivity.return_value = {
                'repository_count': 3,
                'cross_references': [],
                'shared_dependencies': [],
                'integration_points': [],
                'connectivity_score': 0.6,
                'processing_time': 1.5
            }

            request = RepositoryConnectivityRequest(repositories=sample_repository_data)

            # Import the handler method
            from modules.analysis_handlers import AnalysisHandlers

            result = await AnalysisHandlers.handle_repository_connectivity(request)

            assert result.repository_count == 3
            assert result.connectivity_score == 0.6
            assert isinstance(result.cross_references, list)

    @pytest.mark.asyncio
    async def test_handle_repository_connector_config_success(self, mock_service_client):
        """Test successful repository connector configuration handling."""
        from modules.models import RepositoryConnectorConfigRequest

        with patch('modules.cross_repository_analyzer.cross_repository_analyzer') as mock_analyzer:

            mock_analyzer.configure_repository_connector.return_value = True
            mock_analyzer.repository_connectors = {
                'github': {
                    'supported_features': ['api_access', 'webhook_support'],
                    'rate_limits': {'requests_per_hour': 5000}
                }
            }

            request = RepositoryConnectorConfigRequest(
                connector_type='github',
                config={'base_url': 'https://api.github.com'}
            )

            # Import the handler method
            from modules.analysis_handlers import AnalysisHandlers

            result = await AnalysisHandlers.handle_repository_connector_config(request)

            assert result.connector_type == 'github'
            assert result.configured is True
            assert len(result.supported_features) > 0

    @pytest.mark.asyncio
    async def test_handle_supported_connectors_success(self, mock_service_client):
        """Test successful supported connectors retrieval."""
        with patch('modules.cross_repository_analyzer.cross_repository_analyzer') as mock_analyzer:

            mock_analyzer.get_supported_connectors.return_value = ['github', 'gitlab']
            mock_analyzer.repository_connectors = {
                'github': {'description': 'GitHub connector'},
                'gitlab': {'description': 'GitLab connector'}
            }

            # Import the handler method
            from modules.analysis_handlers import AnalysisHandlers

            result = await AnalysisHandlers.handle_supported_connectors()

            assert result.total_supported == 2
            assert 'github' in result.connectors
            assert 'gitlab' in result.connectors

    @pytest.mark.asyncio
    async def test_handle_analysis_frameworks_success(self, mock_service_client):
        """Test successful analysis frameworks retrieval."""
        with patch('modules.cross_repository_analyzer.cross_repository_analyzer') as mock_analyzer:

            mock_analyzer.get_analysis_frameworks.return_value = {
                'consistency_analysis': {'weight': 0.25},
                'coverage_analysis': {'weight': 0.20}
            }

            # Import the handler method
            from modules.analysis_handlers import AnalysisHandlers

            result = await AnalysisHandlers.handle_analysis_frameworks()

            assert result.total_frameworks == 2
            assert 'consistency_analysis' in result.frameworks
            assert 'coverage_analysis' in result.frameworks


if __name__ == "__main__":
    pytest.main([__file__])
