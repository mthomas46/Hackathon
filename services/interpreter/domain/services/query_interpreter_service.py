"""Query Interpreter Domain Service.

Contains the business logic for interpreting user queries and determining intent.
"""

import re
import time
from typing import Dict, Any, Optional

from ..entities.query import UserQuery, QueryIntent, QueryResult


class QueryInterpreterService:
    """Domain service for query interpretation and intent recognition."""

    def __init__(self):
        """Initialize the query interpreter service."""
        # Keywords for intent detection
        self.intent_keywords = {
            QueryIntent.DOCUMENT_ANALYSIS: [
                "analyze", "analysis", "check", "review", "examine", "inspect",
                "evaluate", "assess", "validate", "verify", "audit"
            ],
            QueryIntent.CONTENT_GENERATION: [
                "generate", "create", "build", "make", "produce", "write",
                "develop", "construct", "form", "compose"
            ],
            QueryIntent.WORKFLOW_EXECUTION: [
                "execute", "run", "start", "launch", "perform", "do",
                "process", "handle", "manage", "workflow"
            ],
        }

    def interpret_query(self, user_query: UserQuery) -> QueryResult:
        """Interpret a user query and return structured results.

        Args:
            user_query: The user query to interpret

        Returns:
            QueryResult with intent, confidence, and entities
        """
        start_time = time.time()

        # Clean and preprocess query
        cleaned_query = user_query.get_cleaned_query().lower()

        # Determine intent and confidence
        intent, confidence = self._classify_intent(cleaned_query)

        # Extract entities
        entities = self._extract_entities(cleaned_query, intent)

        # Generate response text
        response_text = self._generate_response_text(intent, entities, user_query)

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        return QueryResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            response_text=response_text,
            query_id=user_query.id,
            processing_time_ms=processing_time_ms,
            metadata={
                "query_length": len(user_query.query),
                "has_context": user_query.has_context(),
                "processing_method": "keyword_matching"
            }
        )

    def _classify_intent(self, query_text: str) -> tuple[QueryIntent, float]:
        """Classify query intent based on keywords.

        Args:
            query_text: Lowercase cleaned query text

        Returns:
            Tuple of (intent, confidence_score)
        """
        intent_scores = {}

        # Score each intent based on keyword matches
        for intent, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in query_text:
                    score += 1
                    # Bonus for exact word matches
                    if re.search(r'\b' + re.escape(keyword) + r'\b', query_text):
                        score += 0.5

            if score > 0:
                intent_scores[intent] = min(score / len(keywords), 1.0)

        # Return highest scoring intent or unknown
        if intent_scores:
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]
            return best_intent, confidence

        return QueryIntent.GENERAL_QUERY, 0.3

    def _extract_entities(self, query_text: str, intent: QueryIntent) -> Dict[str, Any]:
        """Extract entities from query based on intent.

        Args:
            query_text: Lowercase cleaned query text
            intent: Classified intent

        Returns:
            Dictionary of extracted entities
        """
        entities = {}

        # Extract workflow types
        workflow_patterns = {
            "document_analysis": r'\b(document|analysis|review|audit)\b',
            "content_generation": r'\b(generate|create|build|write)\b',
            "workflow_execution": r'\b(execute|run|start|workflow)\b',
        }

        for workflow_type, pattern in workflow_patterns.items():
            if re.search(pattern, query_text):
                entities["workflow"] = workflow_type
                break

        # Extract project types
        project_types = ["web", "mobile", "api", "microservice", "data", "ml", "ai"]
        for project_type in project_types:
            if project_type in query_text:
                entities["project_type"] = project_type
                break

        # Extract output formats
        formats = ["json", "markdown", "html", "pdf", "text", "csv"]
        for fmt in formats:
            if fmt in query_text:
                entities["output_format"] = fmt
                break

        # Set primary entity
        if entities.get("workflow"):
            entities["primary"] = entities["workflow"]
        elif entities.get("project_type"):
            entities["primary"] = entities["project_type"]
        else:
            entities["primary"] = intent.value

        return entities

    def _generate_response_text(self, intent: QueryIntent, entities: Dict[str, Any], user_query: UserQuery) -> str:
        """Generate appropriate response text based on intent and entities.

        Args:
            intent: Classified intent
            entities: Extracted entities
            user_query: Original user query

        Returns:
            Human-readable response text
        """
        base_responses = {
            QueryIntent.DOCUMENT_ANALYSIS: "I can help you analyze documents and provide insights.",
            QueryIntent.CONTENT_GENERATION: "I can help you generate content and documentation.",
            QueryIntent.WORKFLOW_EXECUTION: "I can help you execute workflows and processes.",
            QueryIntent.GENERAL_QUERY: "I understand your query. Let me help you with that.",
        }

        response = base_responses.get(intent, "I understand your request.")

        # Add entity-specific information
        if entities.get("workflow"):
            response += f" This involves {entities['workflow'].replace('_', ' ')}."

        if entities.get("project_type"):
            response += f" This appears to be related to {entities['project_type']} development."

        return response

    def get_supported_intents(self) -> Dict[str, Any]:
        """Get information about supported intents.

        Returns:
            Dictionary with supported intents and their metadata
        """
        return {
            "supported_intents": [
                {
                    "intent": intent.value,
                    "description": self._get_intent_description(intent),
                    "examples": self._get_intent_examples(intent),
                    "confidence_threshold": 0.7,
                }
                for intent in QueryIntent if intent != QueryIntent.UNKNOWN
            ],
            "total_intents": len([i for i in QueryIntent if i != QueryIntent.UNKNOWN]),
        }

    def _get_intent_description(self, intent: QueryIntent) -> str:
        """Get description for an intent."""
        descriptions = {
            QueryIntent.DOCUMENT_ANALYSIS: "Analyze documents for quality, structure, and content insights",
            QueryIntent.CONTENT_GENERATION: "Generate documentation, code, and other content",
            QueryIntent.WORKFLOW_EXECUTION: "Execute predefined workflows and processes",
            QueryIntent.GENERAL_QUERY: "Handle general queries and provide assistance",
        }
        return descriptions.get(intent, "General query handling")

    def _get_intent_examples(self, intent: QueryIntent) -> list[str]:
        """Get example queries for an intent."""
        examples = {
            QueryIntent.DOCUMENT_ANALYSIS: [
                "Analyze this document for quality",
                "Review the code structure",
                "Check document formatting"
            ],
            QueryIntent.CONTENT_GENERATION: [
                "Generate API documentation",
                "Create a project README",
                "Write code documentation"
            ],
            QueryIntent.WORKFLOW_EXECUTION: [
                "Execute the deployment workflow",
                "Run the CI/CD pipeline",
                "Start the analysis process"
            ],
            QueryIntent.GENERAL_QUERY: [
                "How do I use this service?",
                "What can you help me with?",
                "Show me available options"
            ],
        }
        return examples.get(intent, [])
