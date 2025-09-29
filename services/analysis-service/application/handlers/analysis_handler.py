"""Analysis handler for HTTP requests."""

from typing import Dict, Any, Optional
from datetime import datetime

from ..services.analysis_application_service import AnalysisApplicationService


class AnalysisHandler:
    """Handler for analysis-related HTTP requests."""

    def __init__(self, analysis_application_service: AnalysisApplicationService):
        """Initialize handler with application service."""
        self.analysis_service = analysis_application_service

    async def handle_analyze_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document analysis request."""
        try:
            document_id = request_data.get('document_id')
            analysis_type = request_data.get('analysis_type', 'semantic_similarity')
            configuration = request_data.get('configuration', {})

            if not document_id:
                return {
                    'error': 'Document ID is required',
                    'status': 'error'
                }

            result = await self.analysis_service.perform_analysis(
                document_id, analysis_type, configuration
            )

            return {
                'status': 'success',
                'data': result,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }

    async def handle_get_analysis_result(self, analysis_id: str) -> Dict[str, Any]:
        """Handle get analysis result request."""
        try:
            result = await self.analysis_service.get_analysis_result(analysis_id)

            if not result:
                return {
                    'error': 'Analysis not found',
                    'status': 'error'
                }

            return {
                'status': 'success',
                'data': result,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }

    async def handle_get_document_analyses(self, document_id: str) -> Dict[str, Any]:
        """Handle get document analyses request."""
        try:
            analyses = await self.analysis_service.get_document_analyses(document_id)

            return {
                'status': 'success',
                'data': {
                    'document_id': document_id,
                    'analyses': analyses,
                    'total': len(analyses)
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }

    async def handle_get_findings(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get findings request."""
        try:
            document_id = query_params.get('document_id')
            category = query_params.get('category')
            severity = query_params.get('severity')

            findings = await self.analysis_service.get_findings(
                document_id=document_id,
                category=category,
                severity=severity
            )

            return {
                'status': 'success',
                'data': {
                    'findings': findings,
                    'total': len(findings),
                    'filters': {
                        'document_id': document_id,
                        'category': category,
                        'severity': severity
                    }
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }

    async def handle_create_document(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create document request."""
        try:
            title = request_data.get('title')
            content = request_data.get('content')
            content_format = request_data.get('format', 'markdown')
            author = request_data.get('author')
            tags = request_data.get('tags', [])

            if not title or not content:
                return {
                    'error': 'Title and content are required',
                    'status': 'error'
                }

            result = await self.analysis_service.create_document(
                title=title,
                content=content,
                content_format=content_format,
                author=author,
                tags=tags
            )

            return {
                'status': 'success',
                'data': result,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }

    async def handle_get_document(self, document_id: str) -> Dict[str, Any]:
        """Handle get document request."""
        try:
            document = await self.analysis_service.get_document(document_id)

            if not document:
                return {
                    'error': 'Document not found',
                    'status': 'error'
                }

            return {
                'status': 'success',
                'data': document,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }

    async def handle_health_check(self) -> Dict[str, Any]:
        """Handle health check request."""
        try:
            health = await self.analysis_service.get_system_health()

            return {
                'status': 'success',
                'data': health
            }

        except Exception as e:
            return {
                'error': str(e),
                'status': 'error',
                'timestamp': datetime.now().isoformat()
            }
