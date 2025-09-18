"""Query Interpreter Service Domain Service"""

from typing import Dict, Any, List, Optional, Tuple
import re

from ..value_objects.natural_language_query import NaturalLanguageQuery
from ..value_objects.query_interpretation import QueryInterpretation
from ..value_objects.query_intent import QueryIntent
from ..value_objects.query_confidence import QueryConfidence
from ..value_objects.query_type import QueryType


class QueryInterpreterService:
    """Domain service for interpreting natural language queries."""

    def __init__(self):
        """Initialize query interpreter service."""
        self._intent_patterns = self._load_intent_patterns()

    def _load_intent_patterns(self) -> Dict[QueryIntent, List[str]]:
        """Load regex patterns for intent recognition."""
        return {
            QueryIntent.SEARCH_DOCUMENTS: [
                r'\b(search|find|locate|get|retrieve|look)\b.*\b(document|doc|file|paper|article|info|information|data)\b',
                r'\b(show|give)\b.*\b(me|us)\b.*\b(document|file|info)\b',
                r'\bdocument|file|paper|article\b'
            ],
            QueryIntent.ANALYZE_CONTENT: [
                r'\b(analyze|analyse|examine|review|assess)\b.*\b(content|document|text|code)\b',
                r'\b(what is|what are|explain)\b.*\b(in|about)\b',
                r'\b(break down|understand|comprehend)\b'
            ],
            QueryIntent.EXECUTE_WORKFLOW: [
                r'\b(run|execute|start|launch|perform|do)\b.*\b(workflow|process|job|task|analysis)\b',
                r'\b(execute|run)\b.*\b(workflow|analysis|process)\b',
                r'\bworkflow|process|analysis\b'
            ],
            QueryIntent.CHECK_STATUS: [
                r'\b(status|health|condition|state)\b.*\b(of|for)\b',
                r'\b(is|are)\b.*\b(running|working|up|down|healthy)\b',
                r'\b(how is|what is)\b.*\b(status|doing)\b'
            ],
            QueryIntent.GET_METRICS: [
                r'\b(metrics|statistics|stats|numbers|data)\b',
                r'\b(performance|usage|efficiency)\b.*\b(of|for)\b',
                r'\b(show|give|tell)\b.*\b(metrics|stats)\b'
            ],
            QueryIntent.SUMMARIZE_CONTENT: [
                r'\b(summarize|summary|summarise|tl;dr|overview)\b',
                r'\b(short version|brief|concise)\b.*\b(of|for)\b',
                r'\b(what is|tell me about)\b.*\b(briefly|shortly)\b'
            ],
            QueryIntent.LIST_RESOURCES: [
                r'\b(list|show|display|get)\b.*\b(all|available|existing)\b',
                r'\b(what|which)\b.*\b(are there|exist|available)\b',
                r'\b(give me|show me)\b.*\b(list of)\b'
            ],
            QueryIntent.GREETING: [
                r'\b(hello|hi|hey|greetings|good morning|good afternoon)\b',
                r'\b(how are you|how do you do)\b',
                r'\b(nice to meet you|pleased to meet you)\b'
            ],
            QueryIntent.CLARIFICATION: [
                r'\b(can you|could you|would you)\b.*\b(clarify|explain|elaborate)\b',
                r'\b(what do you mean|what does that mean)\b',
                r'\b(i don\'t understand|i\'m confused)\b'
            ]
        }

    def interpret_query(self, query: NaturalLanguageQuery) -> QueryInterpretation:
        """
        Interpret a natural language query and return structured interpretation.

        Args:
            query: The natural language query to interpret

        Returns:
            QueryInterpretation: Structured interpretation of the query
        """
        # Analyze the query text
        intent_matches = self._identify_intents(query.query)

        # Select best intent match
        best_intent, confidence_score = self._select_best_intent(intent_matches)

        # Determine confidence level
        confidence_level = QueryConfidence.from_score(confidence_score)

        # Extract entities and parameters
        entities = self._extract_entities(query.query, best_intent)
        parameters = self._extract_parameters(query.query, best_intent, entities)

        # Generate suggestions
        suggested_actions = self._generate_suggested_actions(best_intent, confidence_level)
        clarification_questions = self._generate_clarification_questions(best_intent, confidence_level)

        # Alternative interpretations
        alternative_interpretations = self._generate_alternatives(intent_matches, best_intent)

        return QueryInterpretation(
            query_id=query.query_id,
            intent=best_intent,
            confidence=confidence_level,
            confidence_score=confidence_score,
            query_type=self._classify_query_type(query),
            entities=entities,
            parameters=parameters,
            suggested_actions=suggested_actions,
            clarification_questions=clarification_questions,
            alternative_interpretations=alternative_interpretations,
            metadata={
                'original_query': query.query,
                'word_count': query.word_count,
                'has_context': query.has_context,
                'intent_matches': len(intent_matches)
            }
        )

    def _identify_intents(self, query_text: str) -> Dict[QueryIntent, float]:
        """Identify possible intents from query text."""
        query_lower = query_text.lower()
        intent_scores = {}

        for intent, patterns in self._intent_patterns.items():
            max_score = 0.0
            for pattern in patterns:
                matches = re.findall(pattern, query_lower)
                if matches:
                    # Simple scoring based on number of matches and pattern specificity
                    score = min(len(matches) * 0.3, 0.9)  # Cap at 0.9
                    max_score = max(max_score, score)

            if max_score > 0:
                intent_scores[intent] = max_score

        return intent_scores

    def _select_best_intent(self, intent_matches: Dict[QueryIntent, float]) -> Tuple[QueryIntent, float]:
        """Select the best intent match."""
        if not intent_matches:
            return QueryIntent.UNKNOWN, 0.0

        # Sort by score, then by priority
        sorted_intents = sorted(
            intent_matches.items(),
            key=lambda x: (x[1], x[0].priority),
            reverse=True
        )

        best_intent, best_score = sorted_intents[0]

        # Apply minimum confidence threshold
        if best_score < 0.1:
            return QueryIntent.UNKNOWN, best_score

        return best_intent, best_score

    def _classify_query_type(self, query: NaturalLanguageQuery) -> QueryType:
        """Classify the query type."""
        if query.is_conversational:
            return QueryType.CONVERSATIONAL
        elif query.query.startswith(('run ', 'execute ', 'start ', 'create ')):
            return QueryType.COMMAND
        elif '?' in query.query or query.query.lower().startswith(('what ', 'how ', 'why ', 'when ', 'where ', 'who ')):
            return QueryType.NATURAL_LANGUAGE
        else:
            return QueryType.STRUCTURED

    def _extract_entities(self, query_text: str, intent: QueryIntent) -> Dict[str, Any]:
        """Extract entities from query text."""
        entities = {}

        # Simple entity extraction based on intent
        if intent == QueryIntent.SEARCH_DOCUMENTS:
            # Look for document types or topics
            doc_types = re.findall(r'\b(document|file|paper|article|report)\b', query_text, re.IGNORECASE)
            if doc_types:
                entities['document_type'] = doc_types[0].lower()

        elif intent == QueryIntent.CHECK_STATUS:
            # Look for service or component names
            services = re.findall(r'\b(orchestrator|analyzer|store|gateway)\b', query_text, re.IGNORECASE)
            if services:
                entities['service_name'] = services[0].lower()

        elif intent == QueryIntent.EXECUTE_WORKFLOW:
            # Look for workflow names or types
            workflow_indicators = re.findall(r'\b(workflow|process|task|job)\b', query_text, re.IGNORECASE)
            if workflow_indicators:
                entities['workflow_type'] = workflow_indicators[0].lower()

        return entities

    def _extract_parameters(self, query_text: str, intent: QueryIntent, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Extract parameters for execution."""
        parameters = {}

        if intent.requires_execution:
            # For executable intents, try to extract actionable parameters
            if intent == QueryIntent.EXECUTE_WORKFLOW:
                # Look for workflow identifiers - more specific patterns
                workflow_id_match = re.search(r'\b(workflow|analysis)[_-]?(\w+)\b', query_text, re.IGNORECASE)
                if workflow_id_match:
                    parameters['workflow_id'] = workflow_id_match.group(0)
                else:
                    # Look for any identifier after the intent words
                    words = query_text.lower().split()
                    for i, word in enumerate(words):
                        if word in ['workflow', 'analysis', 'process'] and i + 1 < len(words):
                            parameters['workflow_id'] = words[i + 1]
                            break

            elif intent == QueryIntent.SEARCH_DOCUMENTS:
                # Look for search terms
                search_terms = re.findall(r'"([^"]*)"|\b(\w+)\b(?=\s+(?:in|about|for|on))', query_text)
                if search_terms:
                    parameters['search_terms'] = [term for group in search_terms for term in group if term]

        return parameters

    def _generate_suggested_actions(self, intent: QueryIntent, confidence: QueryConfidence) -> List[str]:
        """Generate suggested actions based on intent and confidence."""
        actions = []

        if confidence.requires_clarification:
            actions.append("Request clarification from user")
        elif intent.requires_execution and confidence.can_auto_execute:
            actions.append("Execute query directly")
        elif intent.is_informational:
            actions.append("Retrieve and display information")
        elif intent.is_analytical:
            actions.append("Perform analysis and show results")

        return actions

    def _generate_clarification_questions(self, intent: QueryIntent, confidence: QueryConfidence) -> List[str]:
        """Generate clarification questions if needed."""
        questions = []

        if confidence.requires_clarification:
            if intent == QueryIntent.UNKNOWN:
                questions.append("Could you please rephrase your query?")
            elif intent == QueryIntent.SEARCH_DOCUMENTS:
                questions.append("What type of documents are you looking for?")
            elif intent == QueryIntent.EXECUTE_WORKFLOW:
                questions.append("Which workflow would you like to execute?")
            else:
                questions.append("Could you provide more details about what you need?")

        return questions

    def _generate_alternatives(self, intent_matches: Dict[QueryIntent, float], best_intent: QueryIntent) -> List[Dict[str, Any]]:
        """Generate alternative interpretations."""
        alternatives = []

        # Include intents with reasonable confidence (top 3, excluding the best)
        sorted_intents = sorted(
            [(intent, score) for intent, score in intent_matches.items() if intent != best_intent],
            key=lambda x: x[1],
            reverse=True
        )

        for intent, score in sorted_intents[:3]:
            if score > 0.2:  # Minimum threshold for alternatives
                alternatives.append({
                    'intent': intent.value,
                    'confidence_score': score,
                    'description': str(intent)
                })

        return alternatives
