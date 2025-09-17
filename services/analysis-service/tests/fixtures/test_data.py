"""Test Data Fixtures - Predefined test data for consistent testing."""

import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List

from ...domain.entities.document import Document, DocumentStatus
from ...domain.entities.analysis import Analysis, AnalysisStatus
from ...domain.entities.finding import Finding, FindingSeverity
from ...domain.value_objects.analysis_type import AnalysisType
from ...domain.value_objects.confidence import Confidence
from ...domain.value_objects.location import FileLocation, CodeLocation


class TestDataFactory:
    """Factory for creating consistent test data."""

    @staticmethod
    def create_sample_documents(count: int = 5) -> List[Document]:
        """Create sample documents for testing."""
        documents = []
        base_time = datetime.now(timezone.utc)

        for i in range(count):
            doc = Document(
                id=f'sample-doc-{i:03d}',
                title=f'Sample Document {i}',
                content=f'This is sample content for document {i}. It contains some text that can be analyzed for various purposes including sentiment analysis, semantic similarity, and content quality assessment.',
                repository_id='sample-repo',
                author=f'author-{i}@company.com',
                version=f'1.{i}.0',
                status=DocumentStatus.ACTIVE if i % 2 == 0 else DocumentStatus.DRAFT,
                metadata={
                    'language': 'en',
                    'word_count': 45 + i * 10,
                    'category': 'documentation',
                    'tags': [f'tag-{j}' for j in range(i % 3 + 1)]
                }
            )
            documents.append(doc)

        return documents

    @staticmethod
    def create_sample_analyses(document_ids: List[str], count_per_doc: int = 2) -> List[Analysis]:
        """Create sample analyses for documents."""
        analyses = []
        analysis_types = list(AnalysisType)

        for doc_id in document_ids:
            for i in range(count_per_doc):
                analysis_type = analysis_types[i % len(analysis_types)]
                status = AnalysisStatus.COMPLETED if i % 3 != 2 else AnalysisStatus.FAILED

                analysis = Analysis(
                    id=f'analysis-{doc_id.split("-")[-1]}-{i}',
                    document_id=doc_id,
                    analysis_type=analysis_type,
                    status=status,
                    confidence=Confidence(0.7 + (i * 0.1) % 0.3),
                    results={
                        'score': 0.75 + (i * 0.05) % 0.25,
                        'processing_time': 1.5 + i * 0.5,
                        'items_processed': 100 + i * 25
                    },
                    metadata={
                        'algorithm_version': '1.2.0',
                        'model_used': f'model-{analysis_type.value}',
                        'batch_size': 32 + i * 8
                    }
                )
                analyses.append(analysis)

        return analyses

    @staticmethod
    def create_sample_findings(analysis_ids: List[str], count_per_analysis: int = 3) -> List[Finding]:
        """Create sample findings for analyses."""
        findings = []
        severities = list(FindingSeverity)
        categories = ['security', 'performance', 'code_quality', 'documentation', 'style']

        for analysis_id in analysis_ids:
            for i in range(count_per_analysis):
                severity = severities[i % len(severities)]
                category = categories[i % len(categories)]

                # Create appropriate location based on category
                if category in ['code_quality', 'security']:
                    location = CodeLocation(
                        file_path=f'/src/module_{i % 5}.py',
                        start_line=10 + i * 15,
                        end_line=15 + i * 15,
                        start_column=5,
                        end_column=25
                    )
                else:
                    location = FileLocation(
                        file_path=f'/docs/document_{i % 3}.md',
                        line_number=50 + i * 20
                    )

                finding = Finding(
                    id=f'finding-{analysis_id.split("-")[-1]}-{i}',
                    analysis_id=analysis_id,
                    document_id=f'doc-{analysis_id.split("-")[1]}',
                    title=f'Sample Finding {i} - {category.title()}',
                    description=f'This is a sample finding of type {category} with severity {severity.value}. It demonstrates the finding structure and provides actionable recommendations.',
                    severity=severity,
                    confidence=Confidence(0.6 + (i * 0.15) % 0.4),
                    category=category,
                    location=location,
                    recommendation=f'Consider reviewing and addressing this {category} issue to improve code quality.',
                    metadata={
                        'rule_id': f'RULE-{category.upper()}-{i:03d}',
                        'cwe': f'CWE-{100 + i * 10}',
                        'tags': [category, severity.value, f'priority-{i % 3 + 1}'],
                        'automated_fix_available': (i % 3 == 0),  # Every 3rd finding has automated fix
                        'estimated_effort_minutes': 15 + i * 5
                    }
                )
                findings.append(finding)

        return findings

    @staticmethod
    def create_large_document() -> Document:
        """Create a large document for performance testing."""
        content_parts = []
        for i in range(100):  # Create 100 paragraphs
            content_parts.append(f"""
Paragraph {i + 1}: This is a substantial paragraph containing detailed information about topic {i}.
It includes multiple sentences with various vocabulary and complex sentence structures.
The content covers aspects such as implementation details, best practices, and potential challenges.
Furthermore, it provides comprehensive guidance on handling edge cases and optimization techniques.
This extensive content is designed to test analysis capabilities with large volumes of text.
""".strip())

        large_content = '\n\n'.join(content_parts)

        return Document(
            id='large-doc-001',
            title='Comprehensive Large Document',
            content=large_content,
            repository_id='large-repo',
            author='large-author@company.com',
            version='2.0.0',
            status=DocumentStatus.ACTIVE,
            metadata={
                'language': 'en',
                'word_count': len(large_content.split()),
                'size_bytes': len(large_content.encode('utf-8')),
                'paragraphs': 100,
                'category': 'documentation'
            }
        )

    @staticmethod
    def create_multilingual_documents() -> List[Document]:
        """Create documents in different languages for testing."""
        documents = []

        # English document
        en_doc = Document(
            id='doc-en-001',
            title='English Technical Documentation',
            content="""
Python Programming Best Practices

When writing Python code, follow these best practices:
1. Use descriptive variable names
2. Write comprehensive docstrings
3. Follow PEP 8 style guidelines
4. Use type hints for better code clarity
5. Write unit tests for your functions

These practices will make your code more maintainable and easier to understand.
""",
            repository_id='multilingual-repo',
            author='english-author@company.com',
            metadata={'language': 'en', 'word_count': 85}
        )
        documents.append(en_doc)

        # Spanish document
        es_doc = Document(
            id='doc-es-001',
            title='Documentación Técnica en Español',
            content="""
Mejores Prácticas de Programación en Python

Al escribir código Python, siga estas mejores prácticas:
1. Use nombres descriptivos para variables
2. Escriba docstrings completas
3. Siga las pautas de estilo PEP 8
4. Use sugerencias de tipo para mayor claridad
5. Escriba pruebas unitarias para sus funciones

Estas prácticas harán que su código sea más mantenible y fácil de entender.
""",
            repository_id='multilingual-repo',
            author='spanish-author@company.com',
            metadata={'language': 'es', 'word_count': 82}
        )
        documents.append(es_doc)

        # German document
        de_doc = Document(
            id='doc-de-001',
            title='Technische Dokumentation auf Deutsch',
            content="""
Bewährte Praktiken der Python-Programmierung

Beim Schreiben von Python-Code befolgen Sie diese bewährten Praktiken:
1. Verwenden Sie beschreibende Variablennamen
2. Schreiben Sie umfassende Docstrings
3. Befolgen Sie die PEP 8 Stilrichtlinien
4. Verwenden Sie Typ-Hinweise für bessere Code-Klarheit
5. Schreiben Sie Unit-Tests für Ihre Funktionen

Diese Praktiken machen Ihren Code wartbarer und leichter verständlich.
""",
            repository_id='multilingual-repo',
            author='german-author@company.com',
            metadata={'language': 'de', 'word_count': 78}
        )
        documents.append(de_doc)

        return documents

    @staticmethod
    def create_documents_with_issues() -> List[Document]:
        """Create documents with various quality issues for testing."""
        documents = []

        # Document with poor readability
        poor_readability = Document(
            id='doc-poor-readability',
            title='Complex Technical Specification',
            content="""
The implementation of the aforementioned algorithmic computational methodology necessitates the utilization of sophisticated mathematical transformations and computational paradigms that facilitate the execution of complex data processing operations within the confines of the established architectural framework, thereby enabling the systematic manipulation and analysis of multidimensional datasets through the application of advanced statistical methodologies and machine learning algorithms that have been specifically designed to accommodate the requirements of large-scale distributed computing environments.
""",
            repository_id='issues-repo',
            author='complex-author@company.com',
            metadata={'readability_issue': True, 'avg_sentence_length': 85}
        )
        documents.append(poor_readability)

        # Document with grammar issues
        grammar_issues = Document(
            id='doc-grammar-issues',
            title='Quick Start Guide',
            content="""
This guide help you get start with the system. First you need to install the software. Then you configure it. After that you can use it. There is many features available. The documentation is good but could be improve. You should follow the instruction carefully.
""",
            repository_id='issues-repo',
            author='grammar-author@company.com',
            metadata={'grammar_issues': True, 'error_count': 8}
        )
        documents.append(grammar_issues)

        # Document with structural issues
        structural_issues = Document(
            id='doc-structural-issues',
            title='API Reference',
            content="""
Authentication
To authenticate, use the login endpoint with your credentials.

User Management
Create users with the create endpoint. Update them with update. Delete with delete.

Data Operations
Get data with GET requests. Send data with POST. Update with PUT. Remove with DELETE.

Error Handling
Errors are returned with appropriate status codes.

Best Practices
Cache your requests. Use pagination. Handle rate limits.
""",
            repository_id='issues-repo',
            author='structure-author@company.com',
            metadata={'structural_issues': True, 'missing_headers': True}
        )
        documents.append(structural_issues)

        return documents

    @staticmethod
    def create_api_request_samples() -> Dict[str, Any]:
        """Create sample API request payloads."""
        return {
            'semantic_similarity': {
                'targets': ['doc-1', 'doc-2', 'doc-3'],
                'threshold': 0.8,
                'embedding_model': 'sentence-transformers/all-MiniLM-L6-v2',
                'options': {
                    'include_embeddings': False,
                    'batch_size': 32,
                    'normalize_embeddings': True
                }
            },
            'sentiment_analysis': {
                'document_id': 'test-doc-123',
                'analysis_options': {
                    'include_detailed_scores': True,
                    'language': 'en',
                    'model': 'cardiffnlp/twitter-roberta-base-sentiment-latest'
                }
            },
            'content_quality': {
                'document_id': 'test-doc-123',
                'quality_checks': ['readability', 'grammar', 'structure', 'completeness'],
                'options': {
                    'language': 'en',
                    'readability_target': 70.0,
                    'grammar_check_level': 'standard'
                }
            },
            'trend_analysis': {
                'document_id': 'test-doc-123',
                'time_range_days': 90,
                'trend_metrics': ['quality_score', 'complexity', 'sentiment'],
                'forecast_days': 30,
                'options': {
                    'include_seasonal_analysis': True,
                    'confidence_interval': 0.95
                }
            },
            'distributed_task': {
                'task_type': 'semantic_similarity',
                'data': {
                    'document_ids': ['doc-1', 'doc-2', 'doc-3', 'doc-4', 'doc-5'],
                    'threshold': 0.8,
                    'options': {'batch_size': 32}
                },
                'priority': 'high',
                'dependencies': [],
                'metadata': {
                    'user_id': 'user-123',
                    'session_id': 'session-456',
                    'source': 'api'
                }
            },
            'batch_tasks': {
                'tasks': [
                    {
                        'task_type': 'semantic_similarity',
                        'data': {'document_ids': ['batch-doc-1', 'batch-doc-2']},
                        'priority': 'high'
                    },
                    {
                        'task_type': 'sentiment_analysis',
                        'data': {'document_id': 'batch-doc-3'},
                        'priority': 'normal'
                    }
                ],
                'batch_options': {
                    'parallel_execution': True,
                    'max_concurrent': 3,
                    'timeout_seconds': 300,
                    'failure_policy': 'continue'
                }
            }
        }

    @staticmethod
    def create_performance_test_data() -> Dict[str, Any]:
        """Create data for performance testing."""
        return {
            'small_dataset': {
                'documents': TestDataFactory.create_sample_documents(10),
                'expected_analysis_time': 5.0,  # seconds
                'expected_memory_usage': 50.0  # MB
            },
            'medium_dataset': {
                'documents': TestDataFactory.create_sample_documents(100),
                'expected_analysis_time': 45.0,
                'expected_memory_usage': 200.0
            },
            'large_dataset': {
                'documents': [TestDataFactory.create_large_document()],
                'expected_analysis_time': 120.0,
                'expected_memory_usage': 500.0
            },
            'concurrent_load': {
                'users': 50,
                'requests_per_user': 10,
                'expected_total_time': 300.0,  # seconds
                'expected_avg_response_time': 2.0
            }
        }


@pytest.fixture
def sample_documents():
    """Fixture for sample documents."""
    return TestDataFactory.create_sample_documents(5)


@pytest.fixture
def sample_analyses(sample_documents):
    """Fixture for sample analyses."""
    doc_ids = [doc.id.value for doc in sample_documents]
    return TestDataFactory.create_sample_analyses(doc_ids, 2)


@pytest.fixture
def sample_findings(sample_analyses):
    """Fixture for sample findings."""
    analysis_ids = [analysis.id.value for analysis in sample_analyses]
    return TestDataFactory.create_sample_findings(analysis_ids, 2)


@pytest.fixture
def large_document():
    """Fixture for large document."""
    return TestDataFactory.create_large_document()


@pytest.fixture
def multilingual_documents():
    """Fixture for multilingual documents."""
    return TestDataFactory.create_multilingual_documents()


@pytest.fixture
def documents_with_issues():
    """Fixture for documents with quality issues."""
    return TestDataFactory.create_documents_with_issues()


@pytest.fixture
def api_request_samples():
    """Fixture for API request samples."""
    return TestDataFactory.create_api_request_samples()


@pytest.fixture
def performance_test_data():
    """Fixture for performance test data."""
    return TestDataFactory.create_performance_test_data()


@pytest.fixture
def test_user_context():
    """Fixture for test user context."""
    return {
        'user_id': 'test-user-123',
        'session_id': 'test-session-456',
        'permissions': ['read', 'write', 'analyze'],
        'preferences': {
            'language': 'en',
            'timezone': 'UTC',
            'notification_settings': {
                'email': True,
                'webhook': False
            }
        }
    }


@pytest.fixture
def test_repository_context():
    """Fixture for test repository context."""
    return {
        'repository_id': 'test-repo-789',
        'name': 'Test Repository',
        'type': 'git',
        'url': 'https://github.com/test/repo',
        'branch': 'main',
        'permissions': {
            'read': True,
            'write': True,
            'admin': False
        },
        'settings': {
            'auto_analyze': True,
            'webhook_enabled': True,
            'analysis_schedule': 'daily'
        }
    }


@pytest.fixture
def mock_external_services():
    """Fixture for mocked external services."""
    return {
        'semantic_analyzer': {
            'status': 'healthy',
            'response_time': 0.8,
            'supported_languages': ['en', 'es', 'fr', 'de'],
            'models': ['bert-base', 'roberta-large', 'gpt-3']
        },
        'sentiment_analyzer': {
            'status': 'healthy',
            'response_time': 0.5,
            'supported_languages': ['en', 'es', 'fr'],
            'accuracy': 0.87
        },
        'content_quality_scorer': {
            'status': 'healthy',
            'response_time': 1.2,
            'supported_checks': ['readability', 'grammar', 'structure'],
            'quality_thresholds': {'good': 80, 'excellent': 90}
        },
        'database': {
            'status': 'healthy',
            'connection_pool_size': 10,
            'active_connections': 3,
            'response_time': 0.05
        },
        'cache': {
            'status': 'healthy',
            'hit_rate': 0.85,
            'size_mb': 512,
            'eviction_policy': 'LRU'
        },
        'queue': {
            'status': 'healthy',
            'queue_length': 5,
            'processing_rate': 10,  # tasks per minute
            'worker_count': 3
        }
    }


@pytest.fixture
def error_scenarios():
    """Fixture for error scenario test data."""
    return {
        'network_errors': [
            {'type': 'timeout', 'message': 'Request timed out after 30 seconds'},
            {'type': 'connection_refused', 'message': 'Connection refused by server'},
            {'type': 'dns_failure', 'message': 'DNS resolution failed'},
            {'type': 'ssl_error', 'message': 'SSL certificate verification failed'}
        ],
        'validation_errors': [
            {'field': 'document_id', 'error': 'Document ID is required'},
            {'field': 'threshold', 'error': 'Threshold must be between 0.0 and 1.0'},
            {'field': 'targets', 'error': 'At least one target document is required'},
            {'field': 'analysis_type', 'error': 'Invalid analysis type specified'}
        ],
        'business_logic_errors': [
            {'type': 'document_not_found', 'message': 'Specified document does not exist'},
            {'type': 'analysis_in_progress', 'message': 'Analysis is already in progress'},
            {'type': 'quota_exceeded', 'message': 'Daily analysis quota exceeded'},
            {'type': 'insufficient_permissions', 'message': 'User lacks required permissions'}
        ],
        'system_errors': [
            {'type': 'database_unavailable', 'message': 'Database connection failed'},
            {'type': 'external_service_down', 'message': 'External analysis service unavailable'},
            {'type': 'disk_full', 'message': 'Insufficient disk space'},
            {'type': 'memory_exhausted', 'message': 'System memory exhausted'}
        ]
    }


@pytest.fixture
def performance_benchmarks():
    """Fixture for performance benchmarking data."""
    return {
        'response_time_targets': {
            'semantic_similarity': 2.0,  # seconds
            'sentiment_analysis': 1.0,
            'content_quality': 3.0,
            'trend_analysis': 5.0,
            'distributed_task': 10.0
        },
        'throughput_targets': {
            'requests_per_second': 15,
            'concurrent_users': 100,
            'documents_per_minute': 60,
            'analyses_per_minute': 30
        },
        'resource_limits': {
            'max_memory_mb': 1024,
            'max_cpu_percent': 80,
            'max_disk_mb': 5120,
            'max_concurrent_connections': 50
        },
        'quality_targets': {
            'min_accuracy': 0.85,
            'max_error_rate': 0.01,  # 1%
            'min_uptime_percent': 99.9,
            'max_response_time_p95': 5.0  # seconds
        }
    }


@pytest.fixture
def security_test_data():
    """Fixture for security testing data."""
    return {
        'valid_tokens': [
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.valid.signature',
            'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.valid.signature'
        ],
        'invalid_tokens': [
            'invalid.jwt.token',
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature',
            'expired.jwt.token',
            ''
        ],
        'malicious_payloads': [
            {'document_id': '../../../etc/passwd'},
            {'content': '<script>alert("xss")</script>'},
            {'threshold': '1; DROP TABLE documents;'},
            {'targets': ['doc-1', 'doc-2', 'doc-3'] * 1000}  # Large array
        ],
        'rate_limit_scenarios': [
            {'requests': 100, 'window_seconds': 60, 'expected_rejected': 10},
            {'requests': 1000, 'window_seconds': 300, 'expected_rejected': 50},
            {'requests': 50, 'window_seconds': 10, 'expected_rejected': 0}
        ]
    }


@pytest.fixture
def integration_test_scenarios():
    """Fixture for integration test scenarios."""
    return {
        'happy_path': {
            'description': 'Complete successful workflow',
            'steps': [
                'create_document',
                'perform_analysis',
                'retrieve_findings',
                'export_results'
            ],
            'expected_outcome': 'success'
        },
        'error_recovery': {
            'description': 'Workflow with error and recovery',
            'steps': [
                'create_document',
                'perform_failing_analysis',
                'retry_analysis',
                'retrieve_findings'
            ],
            'expected_outcome': 'success_after_retry'
        },
        'concurrent_users': {
            'description': 'Multiple users performing operations',
            'users': 10,
            'operations_per_user': 5,
            'expected_outcome': 'all_operations_complete'
        },
        'resource_limits': {
            'description': 'Operations near resource limits',
            'large_documents': 5,
            'concurrent_analyses': 20,
            'expected_outcome': 'handled_gracefully'
        },
        'external_service_failure': {
            'description': 'Workflow when external services fail',
            'failed_services': ['semantic_analyzer', 'sentiment_analyzer'],
            'fallback_behavior': 'degraded_mode',
            'expected_outcome': 'partial_success'
        }
    }
