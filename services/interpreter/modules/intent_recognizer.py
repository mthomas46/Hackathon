"""Intent recognition functionality for the Interpreter service.

This module contains the IntentRecognizer class and related functionality,
extracted from the main interpreter service to improve maintainability.
"""

import re
from typing import Dict, Any, List, Tuple, Optional

from services.shared.core.models.models import Document, Finding

# Import shared utilities for consistent error handling
from .shared_utils import (
    handle_interpreter_error,
    build_interpreter_context
)


class IntentRecognizer:
    """NLP-based intent recognition engine."""

    def __init__(self):
        # Define intent patterns
        self.intent_patterns = {
            # Analysis intents
            "analyze_document": [
                r"analyze\s+(?:this|the|that|my|your|a)?\s*(?:document|file|content|code)",
                r"check\s+(?:this|the|that|my|your|a)?\s*(?:document|file)",
                r"review\s+(?:this|the|that|my|your|a)?\s*(?:document|content)",
                r"examine\s+(?:this|the|that|my|your|a)?\s*(?:document|file)"
            ],

            "consistency_check": [
                r"check\s+consistency",
                r"find\s+inconsistencies",
                r"consistency\s+analysis",
                r"validate\s+consistency"
            ],

            "security_scan": [
                r"security\s+(?:scan|check|analysis)",
                r"scan\s+for\s+security",
                r"check\s+security",
                r"security\s+vulnerabilities"
            ],

            # Ingestion intents
            "ingest_github": [
                r"ingest\s+(?:from\s+)?github",
                r"pull\s+from\s+github",
                r"import\s+github\s+(?:repo|repository)",
                r"sync\s+github"
            ],

            "ingest_jira": [
                r"ingest\s+(?:from\s+)?jira",
                r"pull\s+from\s+jira",
                r"import\s+jira\s+tickets",
                r"sync\s+jira"
            ],

            "ingest_confluence": [
                r"ingest\s+(?:from\s+)?confluence",
                r"pull\s+from\s+confluence",
                r"import\s+confluence\s+pages",
                r"sync\s+confluence"
            ],

            # Prompt management intents
            "create_prompt": [
                r"create\s+(?:a\s+)?(?:new\s+)?prompt",
                r"make\s+(?:a\s+)?prompt",
                r"add\s+(?:a\s+)?prompt",
                r"new\s+prompt"
            ],

            "find_prompt": [
                r"find\s+(?:a\s+)?prompt",
                r"search\s+(?:for\s+)?prompts?",
                r"get\s+(?:a\s+)?prompt",
                r"show\s+(?:me\s+)?prompts?"
            ],

            # Report generation intents
            "generate_report": [
                r"generate\s+(?:a\s+)?report",
                r"create\s+(?:a\s+)?report",
                r"make\s+(?:a\s+)?report",
                r"run\s+(?:a\s+)?report"
            ],

            # System intents
            "help": [
                r"help(?:\s+me)?",
                r"what\s+can\s+you\s+do",
                r"show\s+commands",
                r"list\s+(?:available\s+)?commands"
            ],

            "status": [
                r"(?:show\s+)?status",
                r"(?:system\s+)?status",
                r"health\s+(?:check|status)",
                r"how\s+are\s+you"
            ]
        }

        # Define entity patterns
        self.entity_patterns = {
            "url": r'https?://[^\s\'"]+',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "repo": r'(?:github\.com/)?([A-Za-z0-9._-]+)/([A-Za-z0-9._-]+)',
            "jira_key": r'\b[A-Z]{2,}-\d+\b',
            "file_path": r'(?:/[^/\s]+)+/\S+',
            "version": r'\bv?\d+(?:\.\d+)*(?:\.\d+)*\b'
        }

    def recognize_intent(self, query: str) -> Tuple[str, float, Dict[str, Any]]:
        """Recognize intent from user query."""
        context = build_interpreter_context("recognize_intent", query_length=len(query))

        try:
            query_lower = query.lower()

            best_intent = "unknown"
            best_score = 0.0

            # Check each intent pattern
            for intent, patterns in self.intent_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, query_lower, re.IGNORECASE):
                        # Better scoring based on pattern specificity and match quality
                        if intent == "analyze_document" and "analyze" in query_lower:
                            score = 0.9  # High confidence for clear analyze intent
                        elif len(re.findall(r'\b(?:analyze|check|review|examine)\b', query_lower)) > 0:
                            score = 0.8  # Good confidence for action verbs
                        else:
                            score = 0.6  # Medium confidence for partial matches

                        if score > best_score:
                            best_score = score
                            best_intent = intent
                            break

            # Extract entities
            entities = self.extract_entities(query)

            return best_intent, best_score, entities

        except Exception as e:
            # Return unknown intent with error context on failure
            handle_interpreter_error("recognize intent", e, query_length=len(query), **context)
            return "unknown", 0.0, {"error": str(e)}

    def extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract entities from query using regex patterns."""
        context = build_interpreter_context("extract_entities", query_length=len(query))

        try:
            entities = {}

            for entity_type, pattern in self.entity_patterns.items():
                matches = re.findall(pattern, query, re.IGNORECASE)
                if matches:
                    # Clean up matches
                    if entity_type == "repo":
                        # Special handling for repo patterns
                        cleaned_matches = []
                        for match in matches:
                            if isinstance(match, tuple):
                                cleaned_matches.append(f"{match[0]}/{match[1]}")
                            else:
                                cleaned_matches.append(match)
                        entities[entity_type] = cleaned_matches
                    else:
                        entities[entity_type] = list(set(matches))  # Remove duplicates

            return entities

        except Exception as e:
            # Return empty entities with error context on failure
            handle_interpreter_error("extract entities", e, query_length=len(query), **context)
            return {"error": str(e)}
