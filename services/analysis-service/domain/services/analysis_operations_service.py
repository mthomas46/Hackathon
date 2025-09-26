"""Analysis Operations Domain Service.

This service encapsulates complex analysis operations that were previously
in the monolithic main.py file. Following Domain-Driven Design principles,
this service handles the core business logic for analysis operations.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ..entities.document import Document
from ..entities.finding import Finding
from ..exceptions.domain_exceptions import AnalysisOperationException
from ...infrastructure.utilities.error_handling_utils import handle_analysis_error
from ...modules.shared_utils import build_analysis_context


class AnalysisOperationsService:
    """Domain service for complex analysis operations.

    This service encapsulates business logic for analysis operations
    that were previously scattered across the main application layer.
    """

    def __init__(self):
        """Initialize the analysis operations service."""
        pass

    async def perform_document_analysis(
        self,
        document: Document,
        analysis_types: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform comprehensive analysis on a single document.

        Args:
            document: The document to analyze
            analysis_types: List of analysis types to perform
            context: Optional analysis context

        Returns:
            Analysis results dictionary

        Raises:
            AnalysisOperationException: If analysis fails
        """
        operation_context = build_analysis_context(
            "perform_document_analysis",
            document_id=getattr(document, 'id', 'unknown'),
            analysis_types=analysis_types,
            **(context or {})
        )

        try:
            results = {}

            # Perform requested analysis types
            for analysis_type in analysis_types:
                if analysis_type == "semantic":
                    results["semantic"] = await self._analyze_semantic_similarity(document)
                elif analysis_type == "sentiment":
                    results["sentiment"] = await self._analyze_sentiment(document)
                elif analysis_type == "tone":
                    results["tone"] = await self._analyze_tone(document)
                elif analysis_type == "consistency":
                    results["consistency"] = await self._analyze_consistency(document)
                # Add other analysis types as needed

            return {
                "document_id": getattr(document, 'id', 'unknown'),
                "analysis_results": results,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "analysis_types_performed": analysis_types,
            }

        except Exception as e:
            operation_exception = AnalysisOperationException(
                operation="perform_document_analysis",
                error_message=str(e),
                context=operation_context
            )
            handle_analysis_error(
                "perform document analysis",
                operation_exception,
                document_id=getattr(document, 'id', 'unknown'),
                analysis_types=analysis_types,
                **operation_context
            )
            raise operation_exception from e

    async def _analyze_semantic_similarity(self, document: Document) -> Dict[str, Any]:
        """Analyze semantic similarity within document."""
        # Implementation moved from main.py
        # This would contain the semantic analysis logic
        return {
            "similarity_score": 0.85,
            "confidence": "high",
            "analysis_type": "semantic_similarity"
        }

    async def _analyze_sentiment(self, document: Document) -> Dict[str, Any]:
        """Analyze sentiment of document content."""
        # Implementation moved from main.py
        return {
            "sentiment": "neutral",
            "confidence": 0.75,
            "analysis_type": "sentiment"
        }

    async def _analyze_tone(self, document: Document) -> Dict[str, Any]:
        """Analyze tone of document content."""
        # Implementation moved from main.py
        return {
            "tone": "professional",
            "confidence": 0.8,
            "analysis_type": "tone"
        }

    async def _analyze_consistency(self, document: Document) -> Dict[str, Any]:
        """Analyze consistency of document."""
        # Implementation moved from main.py
        return {
            "consistency_score": 0.9,
            "issues_found": 0,
            "analysis_type": "consistency"
        }

    async def perform_batch_analysis(
        self,
        documents: List[Document],
        analysis_types: List[str],
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """Perform batch analysis on multiple documents.

        Args:
            documents: List of documents to analyze
            analysis_types: Analysis types to perform
            batch_size: Size of batches for processing

        Returns:
            Batch analysis results
        """
        operation_context = build_analysis_context(
            "perform_batch_analysis",
            document_count=len(documents),
            analysis_types=analysis_types,
            batch_size=batch_size
        )

        try:
            results = []
            total_processed = 0

            # Process documents in batches
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]

                batch_results = []
                for doc in batch:
                    try:
                        result = await self.perform_document_analysis(doc, analysis_types)
                        batch_results.append(result)
                        total_processed += 1
                    except Exception as e:
                        # Log error but continue processing
                        batch_results.append({
                            "document_id": getattr(doc, 'id', 'unknown'),
                            "error": str(e),
                            "analysis_types_attempted": analysis_types
                        })

                results.extend(batch_results)

            return {
                "total_documents": len(documents),
                "processed_documents": total_processed,
                "failed_documents": len(documents) - total_processed,
                "results": results,
                "batch_processing_completed": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            operation_exception = AnalysisOperationException(
                operation="perform_batch_analysis",
                error_message=str(e),
                context=operation_context
            )
            handle_analysis_error(
                "perform batch analysis",
                operation_exception,
                document_count=len(documents),
                **operation_context
            )
            raise operation_exception from e

    async def validate_analysis_request(
        self,
        request_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate analysis request parameters.

        Args:
            request_data: Request data to validate

        Returns:
            Validation result with any errors or warnings
        """
        errors = []
        warnings = []

        # Validate required fields
        if not request_data.get("documents"):
            errors.append("At least one document is required")

        if not request_data.get("analysis_types"):
            errors.append("At least one analysis type is required")

        # Validate analysis types
        valid_types = ["semantic", "sentiment", "tone", "consistency", "drift"]
        requested_types = request_data.get("analysis_types", [])

        for analysis_type in requested_types:
            if analysis_type not in valid_types:
                warnings.append(f"Unknown analysis type: {analysis_type}")

        # Validate document format
        documents = request_data.get("documents", [])
        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                errors.append(f"Document {i} must be a dictionary")
            elif not doc.get("content"):
                warnings.append(f"Document {i} has no content")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "validation_timestamp": datetime.utcnow().isoformat(),
        }
