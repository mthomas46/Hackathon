"""Graph-of-Thought (GoT) pattern implementation."""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import asyncio

from .base import BasePatternEngine, PatternResult, PatternStep


class ThoughtGraphNode:
    """Node in the thought graph."""
    
    def __init__(self, node_id: str, thought: str, node_type: str = "thought"):
        self.node_id = node_id
        self.thought = thought
        self.node_type = node_type  # thought, question, answer, synthesis
        self.incoming: Set[str] = set()  # Node IDs
        self.outgoing: Set[str] = set()  # Node IDs
        self.score: float = 0.0
        self.metadata: Dict[str, Any] = {}
    
    def add_edge_to(self, target_id: str):
        """Add directed edge to target node."""
        self.outgoing.add(target_id)
    
    def add_edge_from(self, source_id: str):
        """Add directed edge from source node."""
        self.incoming.add(source_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "thought": self.thought,
            "node_type": self.node_type,
            "score": self.score,
            "incoming_count": len(self.incoming),
            "outgoing_count": len(self.outgoing),
            "metadata": self.metadata
        }


class GraphOfThoughtEngine(BasePatternEngine):
    """
    Graph-of-Thought pattern execution engine.
    
    Uses graph structures (not just trees) to represent reasoning.
    Allows for cycles, merging paths, and non-hierarchical relationships.
    
    Process:
    1. Generate initial thought nodes
    2. Identify relationships between thoughts
    3. Build directed graph
    4. Expand graph through reasoning
    5. Aggregate insights using graph structure
    6. Find critical paths and synthesis nodes
    
    Reference: "Graph of Thoughts: Solving Elaborate Problems with Large Language Models"
    https://arxiv.org/abs/2308.09687
    
    Advantages over ToT:
    - Can represent non-hierarchical relationships
    - Supports merging of reasoning paths
    - Handles circular dependencies
    - More flexible for complex problems
    """
    
    def __init__(self):
        super().__init__("graph_of_thought")
        self.graph: Dict[str, ThoughtGraphNode] = {}
        self.node_counter = 0
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Graph-of-Thought pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        # Reset graph
        self.graph = {}
        self.node_counter = 0
        
        try:
            # Configuration
            max_nodes = config.get("got_max_nodes", 15)
            expansion_rounds = config.get("got_expansion_rounds", 2)
            
            # Step 1: Generate initial thought nodes
            init_step = await self._generate_initial_nodes(
                query,
                context,
                config
            )
            steps.append(init_step)
            
            # Step 2: Build initial relationships
            relation_step = await self._build_relationships(
                query,
                context,
                config
            )
            steps.append(relation_step)
            
            # Step 3: Expand graph through multiple rounds
            for round_num in range(expansion_rounds):
                if len(self.graph) >= max_nodes:
                    break
                
                expand_step = await self._expand_graph(
                    query,
                    context,
                    config,
                    round_num
                )
                steps.append(expand_step)
            
            # Step 4: Aggregate insights
            aggregate_step = await self._aggregate_insights(
                query,
                context,
                config
            )
            steps.append(aggregate_step)
            
            # Step 5: Synthesize final answer
            synthesis_step = await self._synthesize_from_graph(
                query,
                context,
                config
            )
            steps.append(synthesis_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence
            confidence = self._calculate_graph_confidence()
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=synthesis_step.response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "graph_structure": self._get_graph_structure(),
                    "total_nodes": len(self.graph),
                    "total_edges": sum(len(n.outgoing) for n in self.graph.values()),
                    "expansion_rounds": expansion_rounds,
                    "critical_paths": self._find_critical_paths()
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing GoT pattern: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _generate_initial_nodes(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Generate initial thought nodes."""
        step = self.create_step(
            step_id="generate_nodes",
            step_type="node_generation",
            description="Generate initial thought nodes for graph",
            prompt=self._build_node_generation_prompt(query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            # Parse thoughts from response
            thoughts = self._extract_thoughts(response)
            
            # Create nodes
            for thought in thoughts[:5]:  # Limit initial nodes
                node_id = f"node_{self.node_counter}"
                self.node_counter += 1
                
                node = ThoughtGraphNode(
                    node_id=node_id,
                    thought=thought,
                    node_type="thought"
                )
                self.graph[node_id] = node
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "node_generation",
                    "nodes_created": len(thoughts[:5]),
                    "node_ids": list(self.graph.keys())
                }
            )
        
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _build_relationships(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Build relationships between thought nodes."""
        step = self.create_step(
            step_id="build_relationships",
            step_type="relationship_building",
            description="Identify relationships between thoughts",
            prompt=self._build_relationship_prompt(query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            # Parse relationships
            relationships = self._extract_relationships(response)
            
            # Add edges to graph
            edges_added = 0
            for source_id, target_id in relationships:
                if source_id in self.graph and target_id in self.graph:
                    self.graph[source_id].add_edge_to(target_id)
                    self.graph[target_id].add_edge_from(source_id)
                    edges_added += 1
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "relationship_building",
                    "edges_added": edges_added
                }
            )
        
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _expand_graph(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        round_num: int
    ) -> PatternStep:
        """Expand graph by adding new nodes and edges."""
        step = self.create_step(
            step_id=f"expand_{round_num}",
            step_type="graph_expansion",
            description=f"Expand graph (round {round_num + 1})",
            prompt=self._build_expansion_prompt(query, context, round_num)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            # Parse new thoughts and relationships
            new_thoughts = self._extract_thoughts(response)
            
            # Add new nodes
            new_node_ids = []
            for thought in new_thoughts[:3]:  # Limit per round
                node_id = f"node_{self.node_counter}"
                self.node_counter += 1
                
                node = ThoughtGraphNode(
                    node_id=node_id,
                    thought=thought,
                    node_type="thought"
                )
                self.graph[node_id] = node
                new_node_ids.append(node_id)
            
            # Connect to existing graph (heuristic: connect to most recent nodes)
            recent_nodes = list(self.graph.keys())[-5:]
            for new_id in new_node_ids:
                for old_id in recent_nodes[-2:]:  # Connect to 2 recent nodes
                    if new_id != old_id:
                        self.graph[old_id].add_edge_to(new_id)
                        self.graph[new_id].add_edge_from(old_id)
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "graph_expansion",
                    "round": round_num,
                    "nodes_added": len(new_node_ids)
                }
            )
        
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _aggregate_insights(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Aggregate insights from graph structure."""
        step = self.create_step(
            step_id="aggregate",
            step_type="insight_aggregation",
            description="Aggregate insights using graph structure",
            prompt=self._build_aggregation_prompt(query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "insight_aggregation",
                    "nodes_analyzed": len(self.graph)
                }
            )
        
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _synthesize_from_graph(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Synthesize final answer from graph."""
        step = self.create_step(
            step_id="synthesize",
            step_type="graph_synthesis",
            description="Synthesize answer from thought graph",
            prompt=self._build_synthesis_prompt(query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "graph_synthesis"
                }
            )
        
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_node_generation_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for node generation."""
        context_str = self._format_context(context)
        
        return f"""Generate 3-5 key thoughts/concepts that are relevant to solving this query.

Query: {query}

{context_str}

Instructions:
1. Each thought should be a distinct concept or approach
2. Thoughts should be complementary but independent
3. Focus on core ideas, not full solutions
4. Number each thought
5. Keep each thought to 1-2 sentences

Key Thoughts:"""
    
    def _build_relationship_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for relationship identification."""
        context_str = self._format_context(context)
        
        # List nodes
        nodes_str = "\n".join([
            f"{i+1}. [{node.node_id}] {node.thought}"
            for i, node in enumerate(self.graph.values())
        ])
        
        return f"""Identify relationships between these thoughts.

Query: {query}

{context_str}

Thoughts:
{nodes_str}

Instructions:
1. Identify which thoughts connect to or depend on others
2. Format: "Thought X → Thought Y: [relationship]"
3. A thought can connect to multiple others
4. Relationships can be: depends on, leads to, supports, contradicts
5. Not all thoughts need to be connected

Relationships:"""
    
    def _build_expansion_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        round_num: int
    ) -> str:
        """Build prompt for graph expansion."""
        context_str = self._format_context(context)
        
        # Sample existing thoughts
        sample_thoughts = "\n".join([
            f"- {node.thought[:100]}..."
            for node in list(self.graph.values())[-3:]
        ])
        
        return f"""Based on the existing thoughts, generate 2-3 new complementary thoughts.

Query: {query}

{context_str}

Existing Thoughts (sample):
{sample_thoughts}

Instructions:
1. Generate thoughts that build on or complement existing ones
2. Fill gaps in the reasoning
3. Add depth or alternative perspectives
4. Number each new thought

New Thoughts:"""
    
    def _build_aggregation_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for insight aggregation."""
        context_str = self._format_context(context)
        
        # Get all thoughts
        all_thoughts = "\n".join([
            f"{i+1}. {node.thought}"
            for i, node in enumerate(self.graph.values())
        ])
        
        return f"""Analyze this thought graph and extract key insights.

Query: {query}

{context_str}

All Thoughts:
{all_thoughts}

Graph Structure:
- Total nodes: {len(self.graph)}
- Total edges: {sum(len(n.outgoing) for n in self.graph.values())}

Instructions:
1. Identify the most central/important thoughts
2. Note patterns and themes
3. Find connections between concepts
4. Highlight key insights
5. Prepare for final synthesis

Key Insights:"""
    
    def _build_synthesis_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for final synthesis."""
        context_str = self._format_context(context)
        
        # Get critical nodes
        critical_nodes = self._find_critical_nodes()
        critical_str = "\n".join([
            f"- {node.thought}"
            for node in critical_nodes[:5]
        ])
        
        return f"""Synthesize a final answer using the thought graph.

Query: {query}

{context_str}

Critical Thoughts:
{critical_str}

Instructions:
1. Use the graph structure to inform your answer
2. Integrate insights from multiple thoughts
3. Address the query directly
4. Be comprehensive yet concise
5. Mention key concepts

Final Answer:"""
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompts."""
        if not context:
            return ""
        
        context_parts = []
        
        if "mcp_data" in context:
            context_parts.append(f"Context: {context['mcp_data'][:300]}...")
        
        if "entities" in context:
            entities = context["entities"]
            if entities:
                context_parts.append(f"Entities: {', '.join(entities[:5])}")
        
        if context_parts:
            return "\n".join(context_parts)
        
        return ""
    
    def _extract_thoughts(self, response: str) -> List[str]:
        """Extract thoughts from response."""
        if not response:
            return []
        
        thoughts = []
        lines = response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                # Remove numbering
                for prefix in ['1.', '2.', '3.', '4.', '5.', '6.', '-', '•', '*']:
                    if line.startswith(prefix):
                        line = line[len(prefix):].strip()
                        break
                
                if line:
                    thoughts.append(line)
        
        return thoughts
    
    def _extract_relationships(self, response: str) -> List[tuple[str, str]]:
        """Extract relationships from response."""
        relationships = []
        lines = response.strip().split('\n')
        
        for line in lines:
            # Look for "X → Y" or "Thought X → Thought Y" patterns
            if '→' in line or '->' in line:
                # Simple heuristic: extract node references
                parts = line.replace('→', '->').split('->')
                if len(parts) >= 2:
                    # Try to find node IDs in existing graph
                    source_text = parts[0].lower()
                    target_text = parts[1].lower()
                    
                    # Match to existing nodes (simple heuristic)
                    for src_id, src_node in self.graph.items():
                        if any(word in src_node.thought.lower()[:20] for word in source_text.split()[:3]):
                            for tgt_id, tgt_node in self.graph.items():
                                if src_id != tgt_id and any(word in tgt_node.thought.lower()[:20] for word in target_text.split()[:3]):
                                    relationships.append((src_id, tgt_id))
                                    break
                            break
        
        return relationships
    
    def _find_critical_nodes(self) -> List[ThoughtGraphNode]:
        """Find most critical nodes (highest connectivity)."""
        # Score nodes by total connectivity
        for node in self.graph.values():
            node.score = len(node.incoming) + len(node.outgoing)
        
        # Sort by score
        sorted_nodes = sorted(
            self.graph.values(),
            key=lambda n: n.score,
            reverse=True
        )
        
        return sorted_nodes
    
    def _find_critical_paths(self) -> List[List[str]]:
        """Find critical paths in graph."""
        # Simple heuristic: paths through highest scoring nodes
        critical_nodes = self._find_critical_nodes()[:3]
        paths = []
        
        for node in critical_nodes:
            # Build path from this node
            path = [node.node_id]
            
            # Follow outgoing edges
            current = node
            visited = {node.node_id}
            while current.outgoing:
                # Pick highest scoring outgoing
                next_nodes = [
                    self.graph[nid]
                    for nid in current.outgoing
                    if nid not in visited
                ]
                if not next_nodes:
                    break
                
                next_node = max(next_nodes, key=lambda n: n.score)
                path.append(next_node.node_id)
                visited.add(next_node.node_id)
                current = next_node
                
                if len(path) >= 5:  # Limit path length
                    break
            
            if len(path) > 1:
                paths.append(path)
        
        return paths
    
    def _get_graph_structure(self) -> Dict[str, Any]:
        """Get graph structure for metadata."""
        return {
            node_id: node.to_dict()
            for node_id, node in self.graph.items()
        }
    
    def _calculate_graph_confidence(self) -> float:
        """Calculate confidence based on graph structure."""
        if not self.graph:
            return 0.0
        
        # Factors:
        # 1. Graph density (connectivity)
        total_possible_edges = len(self.graph) * (len(self.graph) - 1)
        actual_edges = sum(len(n.outgoing) for n in self.graph.values())
        density = actual_edges / total_possible_edges if total_possible_edges > 0 else 0.0
        
        # 2. Number of nodes (more = more thorough)
        node_factor = min(len(self.graph) / 15, 1.0)
        
        # 3. Critical path existence
        path_factor = 1.0 if self._find_critical_paths() else 0.5
        
        # Combine
        confidence = density * 0.3 + node_factor * 0.4 + path_factor * 0.3
        
        return min(confidence, 1.0)

