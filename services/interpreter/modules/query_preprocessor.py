"""Advanced Query Preprocessing for Interpreter Service.

This module handles sophisticated query preprocessing, normalization, and enhancement
to improve intent recognition and workflow matching. It includes spell correction,
abbreviation expansion, context injection, and semantic enhancement.
"""

import re
from datetime import datetime
from typing import Any, Dict

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget

try:
    from .conversation_memory import conversation_memory
    from .ecosystem_context import ecosystem_context
except ImportError:
    from conversation_memory import conversation_memory
    from ecosystem_context import ecosystem_context


class QueryPreprocessor:
    """Advanced query preprocessing for enhanced interpretation."""

    def __init__(self):
        # Common abbreviations and expansions
        self.abbreviations = {
            "docs": "documents",
            "doc": "document",
            "repo": "repository",
            "repos": "repositories",
            "sec": "security",
            "qa": "quality assurance",
            "ai": "artificial intelligence",
            "ml": "machine learning",
            "nlp": "natural language processing",
            "api": "application programming interface",
            "ui": "user interface",
            "ux": "user experience",
            "db": "database",
            "config": "configuration",
            "auth": "authentication",
            "admin": "administration",
            "mgmt": "management",
            "dev": "development",
            "prod": "production",
            "env": "environment",
            "img": "image",
            "vid": "video",
            "pic": "picture",
            "pdf": "portable document format",
            "url": "uniform resource locator",
            "http": "hypertext transfer protocol",
            "https": "hypertext transfer protocol secure",
            "css": "cascading style sheets",
            "js": "javascript",
            "py": "python",
            "sql": "structured query language",
            "xml": "extensible markup language",
            "json": "javascript object notation",
            "yaml": "yet another markup language",
            "csv": "comma separated values",
        }

        # Service name variations and aliases
        self.service_aliases = {
            "document store": "doc_store",
            "document storage": "doc_store",
            "document service": "doc_store",
            "docs store": "doc_store",
            "prompt store": "prompt_store",
            "prompt storage": "prompt_store",
            "prompt service": "prompt_store",
            "prompts": "prompt_store",
            "analysis service": "analysis_service",
            "analyzer": "analysis_service",
            "analytics": "analysis_service",
            "code analyzer": "code-analyzer",
            "code analysis": "code-analyzer",
            "security analyzer": "secure-analyzer",
            "security scanner": "secure-analyzer",
            "security service": "secure-analyzer",
            "source agent": "source-agent",
            "source service": "source-agent",
            "github service": "github_mcp",
            "github agent": "github_mcp",
            "git service": "github_mcp",
            "orchestrator": "orchestrator",
            "orchestration": "orchestrator",
            "workflow engine": "orchestrator",
            "summarizer": "summarizer-hub",
            "summary service": "summarizer-hub",
            "bedrock": "bedrock_proxy",
            "aws bedrock": "bedrock_proxy",
            "llm gateway": "bedrock_proxy",
            "interpreter": "interpreter",
            "natural language": "interpreter",
            "memory agent": "memory_agent",
            "memory service": "memory_agent",
            "notification service": "notification-service",
            "notification": "notification-service",
            "alerts": "notification-service",
            "frontend": "frontend",
            "ui service": "frontend",
            "web interface": "frontend",
            "cli": "cli",
            "command line": "cli",
            "terminal": "cli",
        }

        # Common action synonyms
        self.action_synonyms = {
            "analyze": [
                "examine",
                "review",
                "assess",
                "evaluate",
                "inspect",
                "study",
                "investigate",
            ],
            "check": ["verify", "validate", "test", "confirm", "ensure", "audit"],
            "create": ["generate", "make", "build", "produce", "construct", "develop"],
            "find": ["search", "locate", "discover", "identify", "seek", "hunt"],
            "process": ["handle", "manage", "deal with", "work on", "execute"],
            "optimize": ["improve", "enhance", "refine", "tune", "perfect", "upgrade"],
            "scan": ["sweep", "survey", "examine", "inspect", "probe"],
            "summarize": ["abstract", "condense", "digest", "recap", "outline"],
            "document": ["record", "note", "log", "register", "catalog"],
            "monitor": ["watch", "observe", "track", "follow", "supervise"],
            "compare": ["contrast", "match", "relate", "collate", "diff"],
            "merge": ["combine", "unite", "join", "blend", "integrate"],
            "split": ["divide", "separate", "break", "partition", "segment"],
            "transform": ["convert", "change", "modify", "alter", "adapt"],
            "extract": ["pull", "retrieve", "get", "obtain", "derive"],
            "insert": ["add", "include", "inject", "append", "embed"],
            "remove": ["delete", "eliminate", "erase", "drop", "clear"],
            "update": ["modify", "change", "revise", "edit", "refresh"],
            "deploy": ["release", "publish", "launch", "distribute", "rollout"],
            "backup": ["save", "preserve", "archive", "store", "copy"],
            "restore": ["recover", "retrieve", "reinstate", "bring back"],
        }

        # Context patterns for entity enhancement
        self.context_patterns = {
            "time_references": [
                r"\b(today|yesterday|tomorrow|now|recently|lately|soon)\b",
                r"\b(this|last|next)\s+(week|month|year|time)\b",
                r"\b\d{1,2}:\d{2}\b",  # Time format
                r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",  # Date format
            ],
            "quality_indicators": [
                r"\b(good|bad|excellent|poor|high|low|best|worst)\s+(quality|performance)\b",
                r"\b(fast|slow|quick|rapid|efficient|inefficient)\b",
                r"\b(accurate|inaccurate|precise|imprecise|correct|incorrect)\b",
            ],
            "scope_indicators": [
                r"\b(all|every|entire|complete|full|total)\b",
                r"\b(some|few|several|many|most)\b",
                r"\b(part|portion|section|subset)\b",
            ],
            "priority_indicators": [
                r"\b(urgent|critical|important|high.priority|asap)\b",
                r"\b(low.priority|when.possible|eventually)\b",
                r"\b(emergency|immediate|rush)\b",
            ],
        }

    async def preprocess_query(
        self, query: str, user_id: str = None, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Main preprocessing method that applies all enhancements."""
        try:
            # Initial normalization
            original_query = query
            processed_query = await self._normalize_basic(query)

            # Get conversation context if user provided
            conversation_context = {}
            if user_id:
                conversation_context = (
                    await conversation_memory.get_conversation_context(user_id)
                )

            # Apply preprocessing steps
            processed_query = await self._expand_abbreviations(processed_query)
            processed_query = await self._normalize_service_references(processed_query)
            processed_query = await self._expand_action_synonyms(processed_query)
            processed_query = await self._inject_conversation_context(
                processed_query, conversation_context
            )
            processed_query = await self._enhance_with_ecosystem_context(
                processed_query
            )

            # Extract enhanced entities and context
            enhanced_entities = await self._extract_enhanced_entities(
                processed_query, original_query
            )
            query_metadata = await self._extract_query_metadata(
                processed_query, conversation_context
            )

            # Calculate query complexity and confidence
            complexity_score = await self._calculate_query_complexity(
                processed_query, enhanced_entities
            )
            processing_confidence = await self._calculate_processing_confidence(
                original_query, processed_query, enhanced_entities
            )

            result = {
                "original_query": original_query,
                "processed_query": processed_query,
                "enhanced_entities": enhanced_entities,
                "query_metadata": query_metadata,
                "complexity_score": complexity_score,
                "processing_confidence": processing_confidence,
                "preprocessing_steps": [
                    "basic_normalization",
                    "abbreviation_expansion",
                    "service_normalization",
                    "action_expansion",
                    "context_injection",
                    "ecosystem_enhancement",
                ],
                "conversation_context": conversation_context,
                "processing_timestamp": datetime.utcnow().isoformat(),
            }

            fire_and_forget(
                "query_preprocessed",
                f"Successfully preprocessed query for user {user_id or 'anonymous'}",
                ServiceNames.INTERPRETER,
                {
                    "original_length": len(original_query),
                    "processed_length": len(processed_query),
                    "complexity_score": complexity_score,
                    "user_id": user_id,
                },
            )

            return result

        except Exception as e:
            fire_and_forget(
                "query_preprocessing_error",
                f"Failed to preprocess query: {str(e)}",
                ServiceNames.INTERPRETER,
                {"query": query, "user_id": user_id, "error": str(e)},
            )

            # Return minimal result on error
            return {
                "original_query": query,
                "processed_query": query,
                "enhanced_entities": {},
                "query_metadata": {},
                "complexity_score": 0.5,
                "processing_confidence": 0.3,
                "preprocessing_steps": ["error_fallback"],
                "error": str(e),
                "processing_timestamp": datetime.utcnow().isoformat(),
            }

    async def _normalize_basic(self, query: str) -> str:
        """Apply basic normalization to the query."""
        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", query.strip())

        # Fix common punctuation issues
        normalized = re.sub(r"\s+([?.!,;:])", r"\1", normalized)
        normalized = re.sub(r"([?.!,;:])\s*([a-zA-Z])", r"\1 \2", normalized)

        # Handle contractions
        contractions = {
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "doesn't": "does not",
            "didn't": "did not",
            "isn't": "is not",
            "aren't": "are not",
            "wasn't": "was not",
            "weren't": "were not",
            "haven't": "have not",
            "hasn't": "has not",
            "hadn't": "had not",
            "shouldn't": "should not",
            "wouldn't": "would not",
            "couldn't": "could not",
        }

        for contraction, expansion in contractions.items():
            normalized = re.sub(
                r"\b" + re.escape(contraction) + r"\b",
                expansion,
                normalized,
                flags=re.IGNORECASE,
            )

        return normalized

    async def _expand_abbreviations(self, query: str) -> str:
        """Expand common abbreviations in the query."""
        expanded = query

        # Sort by length (longest first) to avoid partial replacements
        sorted_abbreviations = sorted(
            self.abbreviations.items(), key=lambda x: len(x[0]), reverse=True
        )

        for abbrev, expansion in sorted_abbreviations:
            # Use word boundaries to avoid partial matches
            pattern = r"\b" + re.escape(abbrev) + r"\b"
            expanded = re.sub(pattern, expansion, expanded, flags=re.IGNORECASE)

        return expanded

    async def _normalize_service_references(self, query: str) -> str:
        """Normalize service name references to canonical forms."""
        normalized = query

        # Sort by length (longest first) to avoid partial replacements
        sorted_aliases = sorted(
            self.service_aliases.items(), key=lambda x: len(x[0]), reverse=True
        )

        for alias, canonical_name in sorted_aliases:
            pattern = r"\b" + re.escape(alias) + r"\b"
            normalized = re.sub(
                pattern,
                canonical_name.replace("_", " "),
                normalized,
                flags=re.IGNORECASE,
            )

        return normalized

    async def _expand_action_synonyms(self, query: str) -> str:
        """Expand action words to include primary terms."""
        expanded = query
        words = query.lower().split()

        for primary_action, synonyms in self.action_synonyms.items():
            for synonym in synonyms:
                if synonym in words:
                    # Add primary action as alternative interpretation
                    synonym_pattern = r"\b" + re.escape(synonym) + r"\b"
                    expanded = re.sub(
                        synonym_pattern,
                        f"{synonym} {primary_action}",
                        expanded,
                        flags=re.IGNORECASE,
                    )
                    break  # Only expand first match to avoid over-expansion

        return expanded

    async def _inject_conversation_context(
        self, query: str, conversation_context: Dict[str, Any]
    ) -> str:
        """Inject relevant conversation context into the query."""
        if not conversation_context:
            return query

        context_additions = []

        # Add implied context
        implied_context = conversation_context.get("implied_context", "")
        if implied_context and len(query.split()) < 5:  # Only for short queries
            context_additions.append(implied_context)

        # Add domain context for ambiguous queries
        domain_context = conversation_context.get("domain_context", {})
        primary_domain = domain_context.get("primary_domain", "")
        if primary_domain and "general" in query.lower():
            context_additions.append(f"in {primary_domain.replace('_', ' ')} domain")

        # Add recent workflow context if relevant
        recent_workflows = conversation_context.get("recent_workflows", [])
        if recent_workflows and any(
            word in query.lower() for word in ["continue", "next", "also", "then"]
        ):
            last_workflow = recent_workflows[-1] if recent_workflows else ""
            if last_workflow:
                context_additions.append(
                    f"continuing from {last_workflow.replace('_', ' ')}"
                )

        # Combine context additions
        if context_additions:
            context_string = " ".join(context_additions)
            return f"{context_string} {query}"

        return query

    async def _enhance_with_ecosystem_context(self, query: str) -> str:
        """Enhance query with ecosystem-specific context."""
        try:
            # Get ecosystem capabilities
            ecosystem_capabilities = await ecosystem_context.get_service_capabilities()

            enhanced = query

            # Add service context for capability mentions
            for service_name, service_info in ecosystem_capabilities.items():
                capabilities = service_info.get("capabilities", [])
                for capability in capabilities:
                    capability_words = capability.replace("_", " ").split()
                    if any(word in query.lower() for word in capability_words):
                        # Add service context if not already mentioned
                        service_display = service_name.replace("_", " ")
                        if service_display not in enhanced.lower():
                            enhanced = f"{enhanced} using {service_display}"
                        break

            return enhanced

        except Exception:
            return query

    async def _extract_enhanced_entities(
        self, processed_query: str, original_query: str
    ) -> Dict[str, Any]:
        """Extract enhanced entities from processed query."""
        entities = {
            "urls": [],
            "file_paths": [],
            "repositories": [],
            "time_references": [],
            "quality_indicators": [],
            "scope_indicators": [],
            "priority_indicators": [],
            "services_mentioned": [],
            "actions_identified": [],
            "technical_terms": [],
            "numbers_and_metrics": [],
        }

        # URL extraction
        url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+'
        entities["urls"] = re.findall(url_pattern, processed_query)

        # File path extraction
        file_path_patterns = [
            r"/[^\s]+",  # Unix-style paths
            r"[A-Za-z]:\\[^\s]+",  # Windows-style paths
            r"[^\s]+\.[a-zA-Z]{2,4}(?:\s|$)",  # Files with extensions
        ]
        for pattern in file_path_patterns:
            entities["file_paths"].extend(re.findall(pattern, processed_query))

        # Repository references
        repo_patterns = [
            r"github\.com/[^\s]+",
            r"gitlab\.com/[^\s]+",
            r"bitbucket\.org/[^\s]+",
            r"\b[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+\b",  # Generic org/repo pattern
        ]
        for pattern in repo_patterns:
            entities["repositories"].extend(re.findall(pattern, processed_query))

        # Context pattern extraction
        for category, patterns in self.context_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, processed_query, re.IGNORECASE)
                entities[category].extend(matches)

        # Service mentions
        for service_alias in self.service_aliases.values():
            service_display = service_alias.replace("_", " ")
            if service_display in processed_query.lower():
                entities["services_mentioned"].append(service_alias)

        # Action identification
        for primary_action, synonyms in self.action_synonyms.items():
            all_actions = [primary_action] + synonyms
            for action in all_actions:
                if re.search(
                    r"\b" + re.escape(action) + r"\b", processed_query, re.IGNORECASE
                ):
                    entities["actions_identified"].append(primary_action)
                    break

        # Technical terms (file extensions, protocols, etc.)
        tech_terms_pattern = r"\b(?:html|css|js|py|java|cpp|xml|json|yaml|sql|csv|pdf|doc|docx|xls|xlsx|ppt|pptx|zip|tar|gz)\b"
        entities["technical_terms"] = re.findall(
            tech_terms_pattern, processed_query, re.IGNORECASE
        )

        # Numbers and metrics
        number_patterns = [
            r"\b\d+\.\d+\b",  # Decimal numbers
            r"\b\d+%\b",  # Percentages
            r"\b\d+\s*(?:MB|GB|TB|KB)\b",  # File sizes
            r"\b\d+\s*(?:seconds?|minutes?|hours?|days?)\b",  # Time durations
        ]
        for pattern in number_patterns:
            entities["numbers_and_metrics"].extend(
                re.findall(pattern, processed_query, re.IGNORECASE)
            )

        # Remove duplicates and empty values
        for key, value_list in entities.items():
            entities[key] = list(set([v for v in value_list if v and v.strip()]))

        return entities

    async def _extract_query_metadata(
        self, processed_query: str, conversation_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract metadata about the query using focused helper methods."""
        metadata = self._initialize_metadata()

        metadata["query_type"] = self._determine_query_type(processed_query)
        metadata["complexity_indicators"] = self._extract_complexity_indicators(processed_query)
        metadata["domain_hints"] = self._extract_domain_hints(conversation_context)
        metadata["requires_clarification"] = self._check_requires_clarification(processed_query)
        metadata["user_intent_confidence"] = self._calculate_intent_confidence(
            metadata["query_type"],
            metadata["requires_clarification"],
            metadata["complexity_indicators"],
            processed_query
        )

        return metadata

    def _initialize_metadata(self) -> Dict[str, Any]:
        """Initialize metadata dictionary with default values."""
        return {
            "query_type": "unknown",
            "complexity_indicators": [],
            "domain_hints": [],
            "user_intent_confidence": 0.0,
            "requires_clarification": False,
            "suggested_follow_ups": [],
        }

    def _determine_query_type(self, processed_query: str) -> str:
        """Determine the type of query based on keywords."""
        query_patterns = {
            "analysis_request": ["analyze", "check", "review", "examine"],
            "search_request": ["find", "search", "locate", "discover"],
            "creation_request": ["create", "generate", "make", "build"],
            "help_request": ["help", "how", "what", "explain"],
            "optimization_request": ["optimize", "improve", "enhance", "refine"],
        }

        query_lower = processed_query.lower()
        for query_type, keywords in query_patterns.items():
            if any(word in query_lower for word in keywords):
                return query_type

        return "unknown"

    def _extract_complexity_indicators(self, processed_query: str) -> list:
        """Extract indicators of query complexity."""
        indicators = []

        # Check query length
        if len(processed_query.split()) > 20:
            indicators.append("long_query")

        # Check for multiple requirements (and/or/then/also)
        connector_count = len(re.findall(
            r"\band\b|\bor\b|\bthen\b|\balso\b",
            processed_query,
            re.IGNORECASE
        ))
        if connector_count > 2:
            indicators.append("multiple_requirements")

        # Check for multiple questions
        if len(re.findall(r"[?.]", processed_query)) > 1:
            indicators.append("multiple_questions")

        return indicators

    def _extract_domain_hints(self, conversation_context: Dict[str, Any]) -> list:
        """Extract domain hints from conversation context."""
        if not conversation_context:
            return []

        domain_context = conversation_context.get("domain_context", {})
        primary_domain = domain_context.get("primary_domain", "")
        return [primary_domain] if primary_domain else []

    def _check_requires_clarification(self, processed_query: str) -> bool:
        """Check if the query requires clarification."""
        # Check for ambiguous terms
        ambiguous_terms = [
            "this", "that", "it", "them", "something",
            "anything", "stuff"
        ]
        has_ambiguous = any(term in processed_query.lower().split()
                           for term in ambiguous_terms)

        # Check query length
        too_short = len(processed_query.split()) < 3

        return has_ambiguous or too_short

    def _calculate_intent_confidence(
        self,
        query_type: str,
        requires_clarification: bool,
        complexity_indicators: list,
        processed_query: str
    ) -> float:
        """Calculate confidence score for user intent understanding."""
        confidence_factors = []

        if query_type != "unknown":
            confidence_factors.append(0.3)

        if not requires_clarification:
            confidence_factors.append(0.3)

        if len(complexity_indicators) <= 1:
            confidence_factors.append(0.2)

        # Check for politeness indicators
        polite_words = ["please", "can you", "i need", "i want"]
        if any(word in processed_query.lower() for word in polite_words):
            confidence_factors.append(0.2)

        return sum(confidence_factors)

    async def _calculate_query_complexity(
        self, processed_query: str, enhanced_entities: Dict[str, Any]
    ) -> float:
        """Calculate complexity score for the query."""
        complexity_score = 0.0

        # Length factor (normalized)
        word_count = len(processed_query.split())
        length_score = min(word_count / 20.0, 1.0) * 0.3
        complexity_score += length_score

        # Entity count factor
        total_entities = sum(
            len(entity_list) for entity_list in enhanced_entities.values()
        )
        entity_score = min(total_entities / 10.0, 1.0) * 0.2
        complexity_score += entity_score

        # Conjunction count (and, or, then, but, etc.)
        conjunctions = len(
            re.findall(
                r"\b(?:and|or|but|then|also|however|therefore|thus|meanwhile)\b",
                processed_query,
                re.IGNORECASE,
            )
        )
        conjunction_score = min(conjunctions / 5.0, 1.0) * 0.2
        complexity_score += conjunction_score

        # Question count
        questions = len(re.findall(r"[?]", processed_query))
        question_score = min(questions / 3.0, 1.0) * 0.1
        complexity_score += question_score

        # Technical term density
        technical_terms = enhanced_entities.get("technical_terms", [])
        tech_density = len(technical_terms) / max(word_count, 1)
        tech_score = min(tech_density * 2, 1.0) * 0.1
        complexity_score += tech_score

        # Service mention complexity
        services_mentioned = enhanced_entities.get("services_mentioned", [])
        service_score = min(len(services_mentioned) / 3.0, 1.0) * 0.1
        complexity_score += service_score

        return min(complexity_score, 1.0)

    async def _calculate_processing_confidence(
        self,
        original_query: str,
        processed_query: str,
        enhanced_entities: Dict[str, Any],
    ) -> float:
        """Calculate confidence in the preprocessing results."""
        confidence_score = 0.5  # Base confidence

        # If significant expansion occurred, increase confidence
        expansion_ratio = len(processed_query) / max(len(original_query), 1)
        if 1.1 < expansion_ratio < 2.0:  # Reasonable expansion
            confidence_score += 0.2
        elif expansion_ratio > 2.0:  # Too much expansion might be problematic
            confidence_score -= 0.1

        # If entities were successfully extracted, increase confidence
        total_entities = sum(
            len(entity_list) for entity_list in enhanced_entities.values()
        )
        if total_entities > 0:
            confidence_score += min(total_entities / 10.0, 0.3)

        # If no preprocessing errors occurred (basic check)
        if processed_query and len(processed_query.strip()) > 0:
            confidence_score += 0.1

        # If recognized patterns were found
        recognized_patterns = 0
        for pattern_category, patterns in self.context_patterns.items():
            for pattern in patterns:
                if re.search(pattern, processed_query, re.IGNORECASE):
                    recognized_patterns += 1
                    break

        if recognized_patterns > 0:
            confidence_score += min(recognized_patterns / 4.0, 0.2)

        return min(confidence_score, 1.0)

    async def get_preprocessing_statistics(self) -> Dict[str, Any]:
        """Get statistics about preprocessing performance."""
        return {
            "abbreviations_count": len(self.abbreviations),
            "service_aliases_count": len(self.service_aliases),
            "action_synonyms_count": len(self.action_synonyms),
            "context_patterns_count": sum(
                len(patterns) for patterns in self.context_patterns.values()
            ),
            "supported_features": [
                "abbreviation_expansion",
                "service_normalization",
                "action_synonym_expansion",
                "conversation_context_injection",
                "ecosystem_context_enhancement",
                "entity_extraction",
                "query_metadata_analysis",
                "complexity_scoring",
                "confidence_calculation",
            ],
        }


# Create singleton instance
query_preprocessor = QueryPreprocessor()
