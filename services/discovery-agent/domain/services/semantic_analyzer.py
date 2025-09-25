"""Semantic Analysis Module for Discovery Agent service.

This module provides Phase 4 semantic analysis capabilities using LLM
to intelligently categorize and analyze discovered tools.
"""

import re
from typing import Any, Dict, List

from .shared_utils import safe_service_clients_call, TIMEOUT_LLM_ANALYSIS
from ..exceptions.domain_exceptions import (
    SemanticAnalysisException,
    LLMAnalysisException,
    ParsingException,
    ValidationException,
)


class SemanticToolAnalyzer:
    """Semantic analyzer for tool categorization and analysis using LLM"""

    def __init__(self, interpreter_url: str = "http://localhost:5120"):
        self.interpreter_url = interpreter_url
        self.service_client = safe_service_clients_call()

        # Semantic categories and their characteristics
        self.semantic_categories = {
            "content_generation": {
                "keywords": ["generate", "create", "produce", "build", "construct"],
                "capabilities": ["text_generation", "content_creation", "synthesis"],
                "use_cases": ["writing", "creation", "synthesis"],
            },
            "content_analysis": {
                "keywords": ["analyze", "review", "evaluate", "assess", "examine"],
                "capabilities": ["analysis", "evaluation", "assessment"],
                "use_cases": ["quality_check", "review", "validation"],
            },
            "data_processing": {
                "keywords": ["process", "transform", "convert", "format", "clean"],
                "capabilities": ["data_transformation", "formatting", "processing"],
                "use_cases": ["data_prep", "transformation", "cleaning"],
            },
            "storage_management": {
                "keywords": ["store", "save", "retrieve", "persist", "archive"],
                "capabilities": ["data_storage", "retrieval", "persistence"],
                "use_cases": ["data_management", "archival", "backup"],
            },
            "communication": {
                "keywords": ["send", "notify", "alert", "message", "contact"],
                "capabilities": ["messaging", "notification", "communication"],
                "use_cases": ["alerting", "notification", "messaging"],
            },
            "search_retrieval": {
                "keywords": ["search", "find", "query", "lookup", "discover"],
                "capabilities": ["search", "retrieval", "querying"],
                "use_cases": ["information_retrieval", "search", "lookup"],
            },
            "ai_interaction": {
                "keywords": ["prompt", "llm", "ai", "model", "inference"],
                "capabilities": ["ai_interaction", "prompting", "model_usage"],
                "use_cases": ["ai_tasks", "prompt_engineering", "model_interaction"],
            },
            "system_operations": {
                "keywords": ["execute", "run", "command", "system", "infrastructure"],
                "capabilities": ["execution", "system_interaction", "infrastructure"],
                "use_cases": ["automation", "system_tasks", "infrastructure"],
            },
        }

    async def analyze_tool_semantics(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive semantic analysis of a tool using LLM understanding.

        Analyzes tool characteristics using both LLM-powered semantic understanding
        and rule-based categorization to provide detailed insights about tool purpose,
        capabilities, and relationships.

        Args:
            tool: Tool definition containing name, description, method, path, etc.

        Returns:
            Dict containing:
            - tool_name: Original tool name
            - semantic_categories: List of applicable semantic categories
            - primary_category: Most relevant category
            - confidence_score: Analysis confidence (0.0-1.0)
            - capabilities_identified: Tool capabilities
            - use_cases_identified: Typical use cases
            - relationships: Related tools/concepts
            - llm_analysis: Raw LLM response (if successful)
        """

        semantic_analysis = {
            "tool_name": tool["name"],
            "original_category": tool.get("category", "unknown"),
            "semantic_categories": [],
            "primary_category": "",
            "confidence_score": 0.0,
            "semantic_description": "",
            "capabilities_identified": [],
            "use_cases_identified": [],
            "relationships": {},
            "llm_analysis": None,
        }

        try:
            # Use LLM for semantic analysis
            llm_analysis = await self._perform_llm_semantic_analysis(tool)

            if llm_analysis.get("success"):
                semantic_analysis["llm_analysis"] = llm_analysis["analysis"]

                # Parse LLM response for semantic insights
                parsed_semantics = self._parse_llm_semantic_response(
                    llm_analysis["analysis"]
                )
                semantic_analysis.update(parsed_semantics)
            else:
                # Fallback to rule-based semantic analysis
                print(f"LLM analysis failed for {tool['name']}, using rule-based analysis")
                rule_based = self._rule_based_semantic_analysis(tool)
                semantic_analysis.update(rule_based)
        except LLMAnalysisException as e:
            # LLM analysis failed, use rule-based fallback
            print(f"LLM analysis exception for {tool['name']}: {e}, using rule-based analysis")
            rule_based = self._rule_based_semantic_analysis(tool)
            semantic_analysis.update(rule_based)
        except ParsingException as e:
            # Parsing failed, use rule-based fallback
            print(f"LLM parsing exception for {tool['name']}: {e}, using rule-based analysis")
            rule_based = self._rule_based_semantic_analysis(tool)
            semantic_analysis.update(rule_based)
        except Exception as e:
            # Unexpected error, use rule-based fallback
            print(f"Unexpected semantic analysis error for {tool['name']}: {e}, using rule-based analysis")
            rule_based = self._rule_based_semantic_analysis(tool)
            semantic_analysis.update(rule_based)

        # Calculate confidence score
        semantic_analysis["confidence_score"] = self._calculate_semantic_confidence(
            semantic_analysis
        )

        return semantic_analysis

    async def _perform_llm_semantic_analysis(
        self, tool: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform semantic analysis using LLM interpretation service.

        Sends a structured prompt to the LLM service to analyze tool characteristics
        and extract semantic meaning, capabilities, and relationships.

        Args:
            tool: Tool definition dictionary with metadata

        Returns:
            Dict with 'success' boolean and 'analysis' string containing LLM response
        """

        analysis_prompt = f"""
        Analyze the following API tool and provide semantic understanding:

        Tool Name: {tool.get('name', 'Unknown')}
        Description: {tool.get('description', 'No description')}
        Method: {tool.get('method', 'Unknown')}
        Path: {tool.get('path', 'Unknown')}
        Category: {tool.get('category', 'Unknown')}

        Parameters: {len(tool.get('parameters', {}).get('properties', {}))} parameters

        Please provide semantic analysis in JSON format with:
        1. semantic_categories: Array of applicable semantic categories
        2. primary_category: Most appropriate single category
        3. capabilities: What this tool can do
        4. use_cases: Typical use cases for this tool
        5. description: Natural language description of tool purpose
        6. relationships: Related tools or complementary capabilities
        7. complexity_score: 1-10 scale of tool complexity

        Focus on understanding what the tool actually does, not just its technical specification.
        """

        try:
            async with self.service_client.session() as session:
                url = f"{self.interpreter_url}/interpret"

                payload = {
                    "query": analysis_prompt,
                    "context": "tool_semantic_analysis",
                    "response_format": "json",
                }

                async with session.post(url, json=payload, timeout=TIMEOUT_LLM_ANALYSIS) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "analysis": result.get("interpretation", ""),
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Interpreter returned {response.status}",
                        }

        except TimeoutError as e:
            raise LLMAnalysisException("llm_semantic_analysis", f"Request timed out after {TIMEOUT_LLM_ANALYSIS} seconds")
        except Exception as e:
            raise LLMAnalysisException("llm_semantic_analysis", str(e))

    def _parse_llm_semantic_response(self, llm_response: str) -> Dict[str, Any]:
        """Parse and extract structured data from LLM semantic analysis response.

        Attempts to extract JSON from the LLM response and map it to standardized
        semantic analysis fields. Falls back to empty defaults if parsing fails.

        Args:
            llm_response: Raw text response from LLM analysis

        Returns:
            Dict with parsed semantic fields: categories, primary_category,
            capabilities, use_cases, description, relationships
        """

        try:
            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", llm_response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "semantic_categories": parsed.get("semantic_categories", []),
                    "primary_category": parsed.get("primary_category", ""),
                    "capabilities_identified": parsed.get("capabilities", []),
                    "use_cases_identified": parsed.get("use_cases", []),
                    "semantic_description": parsed.get("description", ""),
                    "relationships": parsed.get("relationships", {}),
                    "complexity_score": parsed.get("complexity_score", 5),
                }
        except Exception as e:
            # Log the parsing error but continue with fallback
            print(f"LLM response parsing error: {e}, using fallback")

        # Fallback parsing
        return {
            "semantic_categories": ["utility"],
            "primary_category": "utility",
            "capabilities_identified": ["unknown"],
            "use_cases_identified": ["general_use"],
            "semantic_description": "Tool purpose could not be determined semantically",
            "relationships": {},
            "complexity_score": 5,
        }

    def _rule_based_semantic_analysis(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based semantic analysis as fallback when LLM is unavailable.

        Performs comprehensive semantic analysis using keyword matching and
        scoring algorithms to categorize tools and identify capabilities.
        """
        # Extract and prepare text for analysis
        combined_text = self._prepare_tool_text_for_analysis(tool)

        # Score semantic categories based on keyword matching
        semantic_matches = self._score_semantic_categories(combined_text)
        semantic_matches.sort(key=lambda x: x["score"], reverse=True)

        # Determine primary category and collect capabilities
        analysis_results = self._process_semantic_matches(semantic_matches)

        return self._build_semantic_analysis_result(
            tool, semantic_matches, **analysis_results
        )

    def _process_semantic_matches(self, semantic_matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process semantic matches to extract primary category and capabilities."""
        primary_category = self._determine_primary_category(semantic_matches)
        capabilities, use_cases = self._collect_capabilities_and_use_cases(semantic_matches)

        return {
            "primary_category": primary_category,
            "capabilities": capabilities,
            "use_cases": use_cases
        }

    def _prepare_tool_text_for_analysis(self, tool: Dict[str, Any]) -> str:
        """Prepare combined text from tool attributes for analysis"""
        tool_name = tool.get("name", "").lower()
        description = tool.get("description", "").lower()
        path = tool.get("path", "").lower()
        category = tool.get("category", "").lower()
        return f"{tool_name} {description} {path} {category}"

    def _score_semantic_categories(self, combined_text: str) -> List[Dict[str, Any]]:
        """Score semantic categories based on keyword matching and relevance.

        Evaluates each semantic category against the combined tool text,
        calculating relevance scores and filtering out low-confidence matches.
        """
        semantic_matches = []

        for category_name, category_data in self.semantic_categories.items():
            score = self._calculate_category_score(category_name, category_data, combined_text)

            if self._is_category_relevant(score):
                match_data = self._create_semantic_match(category_name, score, category_data)
                semantic_matches.append(match_data)

        return semantic_matches

    def _is_category_relevant(self, score: int) -> bool:
        """Determine if a category score indicates relevance."""
        return score >= 2

    def _create_semantic_match(
        self, category_name: str, score: int, category_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a semantic match data structure."""
        return {
            "category": category_name,
            "score": score,
            "capabilities": category_data["capabilities"],
            "use_cases": category_data["use_cases"],
        }

    def _calculate_category_score(self, sem_category: str, category_data: Dict[str, Any], combined_text: str) -> int:
        """Calculate relevance score for a semantic category.

        Uses multiple scoring mechanisms to determine how well a category
        matches the tool's semantic content.
        """
        score = 0

        # Score based on keyword matches
        score += self._calculate_keyword_score(category_data["keywords"], combined_text)

        # Score based on category name matches
        score += self._calculate_category_name_score(sem_category, combined_text)

        return score

    def _calculate_keyword_score(self, keywords: List[str], combined_text: str) -> int:
        """Calculate score based on keyword matches."""
        score = 0
        for keyword in keywords:
            if keyword in combined_text:
                score += 2
        return score

    def _calculate_category_name_score(self, category_name: str, combined_text: str) -> int:
        """Calculate score based on category name matches."""
        readable_category = category_name.replace("_", " ")
        return 3 if readable_category in combined_text else 0

    def _determine_primary_category(self, semantic_matches: List[Dict[str, Any]]) -> str:
        """Determine the primary semantic category"""
        return semantic_matches[0]["category"] if semantic_matches else "utility"

    def _collect_capabilities_and_use_cases(self, semantic_matches: List[Dict[str, Any]]) -> tuple:
        """Collect and deduplicate capabilities and use cases from semantic matches.

        Aggregates capabilities and use cases from the top 3 most relevant
        semantic matches, removing duplicates to provide clean lists.
        """
        capabilities = []
        use_cases = []

        # Collect from top 3 most relevant matches
        top_matches = self._get_top_semantic_matches(semantic_matches, limit=3)

        for match in top_matches:
            capabilities.extend(match["capabilities"])
            use_cases.extend(match["use_cases"])

        # Remove duplicates while preserving order
        return self._deduplicate_list(capabilities), self._deduplicate_list(use_cases)

    def _get_top_semantic_matches(self, semantic_matches: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]:
        """Get the top N semantic matches by relevance."""
        return semantic_matches[:limit]

    def _deduplicate_list(self, items: List[str]) -> List[str]:
        """Remove duplicates from list while preserving order."""
        return list(dict.fromkeys(items))

    def _build_semantic_analysis_result(
        self, tool: Dict[str, Any], semantic_matches: List[Dict[str, Any]],
        primary_category: str, capabilities: List[str], use_cases: List[str]
    ) -> Dict[str, Any]:
        """Build the final semantic analysis result"""
        return {
            "semantic_categories": [match["category"] for match in semantic_matches],
            "primary_category": primary_category,
            "capabilities_identified": capabilities,
            "use_cases_identified": use_cases,
            "semantic_description": f"Tool appears to be related to {primary_category.replace('_', ' ')} based on keyword analysis",
            "relationships": {},
            "complexity_score": min(
                len(tool.get("parameters", {}).get("properties", {})), 10
            ),
        }

    def _calculate_semantic_confidence(
        self, semantic_analysis: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for semantic analysis"""

        confidence = 0.0

        # Base confidence from categories found
        categories_count = len(semantic_analysis.get("semantic_categories", []))
        confidence += min(categories_count * 0.2, 0.6)  # Up to 60% from categories

        # Add confidence from LLM analysis
        if semantic_analysis.get("llm_analysis"):
            confidence += 0.3  # 30% bonus for LLM analysis
        else:
            confidence += 0.1  # 10% for rule-based

        # Add confidence from detailed analysis
        capabilities = semantic_analysis.get("capabilities_identified", [])
        use_cases = semantic_analysis.get("use_cases_identified", [])

        if capabilities:
            confidence += 0.1
        if use_cases:
            confidence += 0.1
        if semantic_analysis.get("relationships"):
            confidence += 0.1

        return min(confidence, 1.0)

    async def analyze_tool_relationships(
        self, tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze relationships between tools using semantic understanding"""

        relationship_analysis = {
            "tool_count": len(tools),
            "relationships_found": 0,
            "relationship_types": {},
            "complementary_pairs": [],
            "workflow_suggestions": [],
        }

        print(f"🔗 Analyzing relationships between {len(tools)} tools...")

        # Analyze each pair of tools for relationships
        for i, tool1 in enumerate(tools):
            for j, tool2 in enumerate(tools):
                if i >= j:  # Avoid duplicate pairs
                    continue

                relationship = await self._analyze_tool_pair_relationship(tool1, tool2)

                if relationship["has_relationship"]:
                    relationship_analysis["relationships_found"] += 1

                    rel_type = relationship["relationship_type"]
                    if rel_type not in relationship_analysis["relationship_types"]:
                        relationship_analysis["relationship_types"][rel_type] = 0
                    relationship_analysis["relationship_types"][rel_type] += 1

                    relationship_analysis["complementary_pairs"].append(
                        {
                            "tool1": tool1["name"],
                            "tool2": tool2["name"],
                            "relationship": rel_type,
                            "strength": relationship["strength"],
                            "description": relationship["description"],
                        }
                    )

        # Generate workflow suggestions
        relationship_analysis["workflow_suggestions"] = (
            self._generate_workflow_suggestions(
                relationship_analysis["complementary_pairs"]
            )
        )

        return relationship_analysis

    async def _analyze_tool_pair_relationship(
        self, tool1: Dict[str, Any], tool2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze relationship between two tools"""

        # Get semantic information
        sem1 = tool1.get("semantic_analysis", {})
        sem2 = tool2.get("semantic_analysis", {})

        categories1 = set(sem1.get("semantic_categories", []))
        categories2 = set(sem2.get("semantic_categories", []))

        capabilities1 = set(sem1.get("capabilities_identified", []))
        capabilities2 = set(sem2.get("capabilities_identified", []))

        use_cases1 = set(sem1.get("use_cases_identified", []))
        use_cases2 = set(sem2.get("use_cases_identified", []))

        # Check for sequential relationships
        sequential_patterns = [
            ({"content_generation"}, {"content_analysis"}, "generation_to_analysis"),
            ({"content_analysis"}, {"storage_management"}, "analysis_to_storage"),
            ({"search_retrieval"}, {"content_analysis"}, "retrieval_to_analysis"),
            ({"data_processing"}, {"storage_management"}, "processing_to_storage"),
            ({"ai_interaction"}, {"content_analysis"}, "ai_to_analysis"),
            ({"content_analysis"}, {"communication"}, "analysis_to_notification"),
        ]

        for input_cats, output_cats, rel_type in sequential_patterns:
            if (categories1 & input_cats) and (categories2 & output_cats):
                return {
                    "has_relationship": True,
                    "relationship_type": rel_type,
                    "strength": 0.8,
                    "description": f"{tool1['name']} output can be analyzed/processed by {tool2['name']}",
                }
            elif (categories1 & output_cats) and (categories2 & input_cats):
                return {
                    "has_relationship": True,
                    "relationship_type": rel_type,
                    "strength": 0.8,
                    "description": f"{tool2['name']} output can be analyzed/processed by {tool1['name']}",
                }

        # Check for complementary capabilities
        if capabilities1 & capabilities2:  # Overlapping capabilities
            return {
                "has_relationship": True,
                "relationship_type": "complementary_capabilities",
                "strength": 0.6,
                "description": f"Both tools share capabilities: {', '.join(capabilities1 & capabilities2)}",
            }

        # Check for same use case (potential alternatives)
        if use_cases1 & use_cases2:
            return {
                "has_relationship": True,
                "relationship_type": "alternative_implementations",
                "strength": 0.4,
                "description": f"Both tools serve similar use cases: {', '.join(use_cases1 & use_cases2)}",
            }

        return {
            "has_relationship": False,
            "relationship_type": "none",
            "strength": 0.0,
            "description": "No significant relationship detected",
        }

    def _generate_workflow_suggestions(
        self, complementary_pairs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate workflow suggestions based on tool relationships"""

        suggestions = []

        # Group by relationship type
        workflows_by_type = {}
        for pair in complementary_pairs:
            rel_type = pair["relationship"]
            if rel_type not in workflows_by_type:
                workflows_by_type[rel_type] = []
            workflows_by_type[rel_type].append(pair)

        # Generate suggestions for each relationship type
        for rel_type, pairs in workflows_by_type.items():
            if len(pairs) >= 2:  # Need at least 2 related pairs for a workflow
                suggestion = {
                    "workflow_type": rel_type,
                    "description": f"Multi-step workflow using {rel_type.replace('_', ' ')}",
                    "tools_involved": list(
                        set([p["tool1"] for p in pairs] + [p["tool2"] for p in pairs])
                    ),
                    "estimated_steps": len(pairs) + 1,
                    "complexity": "medium" if len(pairs) <= 3 else "high",
                }
                suggestions.append(suggestion)

        return suggestions

    async def enhance_tool_categorization(
        self, tools: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enhance tool categorization using semantic analysis"""

        enhanced_tools = []

        print(
            f"🧠 Enhancing categorization for {len(tools)} tools using semantic analysis..."
        )

        for tool in tools:
            # Perform semantic analysis
            semantic_analysis = await self.analyze_tool_semantics(tool)

            # Enhance the tool with semantic information
            enhanced_tool = tool.copy()
            enhanced_tool["semantic_analysis"] = semantic_analysis

            # Update category if semantic analysis provides better categorization
            if semantic_analysis["confidence_score"] > 0.7:
                original_category = tool.get("category", "unknown")
                semantic_category = semantic_analysis["primary_category"]

                if (
                    semantic_category != "utility"
                ):  # Only override if we have a meaningful semantic category
                    enhanced_tool["enhanced_category"] = semantic_category
                    enhanced_tool["categorization_method"] = "semantic_analysis"
                    print(
                        f"  📋 Enhanced {tool['name']}: {original_category} → {semantic_category}"
                    )

            enhanced_tools.append(enhanced_tool)

        return enhanced_tools


# Create singleton instance
semantic_tool_analyzer = SemanticToolAnalyzer()
