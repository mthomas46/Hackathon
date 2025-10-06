"""Tree-of-Thought (ToT) pattern implementation."""

from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from .base import BasePatternEngine, PatternResult, PatternStep


class ThoughtNode:
    """Node in the thought tree."""
    
    def __init__(
        self,
        node_id: str,
        thought: str,
        parent_id: Optional[str] = None,
        depth: int = 0
    ):
        self.node_id = node_id
        self.thought = thought
        self.parent_id = parent_id
        self.depth = depth
        self.children: List['ThoughtNode'] = []
        self.score: float = 0.0
        self.is_terminal: bool = False
        self.evaluation: Optional[str] = None
    
    def add_child(self, child: 'ThoughtNode'):
        """Add child node."""
        self.children.append(child)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "thought": self.thought,
            "parent_id": self.parent_id,
            "depth": self.depth,
            "score": self.score,
            "is_terminal": self.is_terminal,
            "evaluation": self.evaluation,
            "children_count": len(self.children)
        }


class TreeOfThoughtEngine(BasePatternEngine):
    """
    Tree-of-Thought pattern execution engine.
    
    Explores multiple reasoning paths as a tree structure.
    
    Process:
    1. Generate multiple initial thoughts (breadth)
    2. Evaluate each thought's promise
    3. Expand most promising thoughts (depth)
    4. Repeat until terminal states reached
    5. Select best path through tree
    
    Reference: https://arxiv.org/abs/2305.10601
    "Tree of Thoughts: Deliberate Problem Solving with Large Language Models"
    """
    
    def __init__(self):
        super().__init__("tree_of_thought")
        self.thought_tree: Dict[str, ThoughtNode] = {}
        self.node_counter = 0
    
    async def execute(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternResult:
        """Execute Tree-of-Thought pattern."""
        start_time = datetime.utcnow()
        steps: List[PatternStep] = []
        
        # Reset tree
        self.thought_tree = {}
        self.node_counter = 0
        
        try:
            # Configuration
            max_depth = config.get("tot_max_depth", 3)
            branching_factor = config.get("tot_branching_factor", 3)
            top_k = config.get("tot_top_k", 2)  # How many branches to explore
            
            # Step 1: Generate initial thoughts (root level)
            root_step = await self._generate_initial_thoughts(
                query,
                context,
                config,
                branching_factor
            )
            steps.append(root_step)
            
            # Step 2: Build tree through iterative expansion
            expansion_steps = await self._expand_tree(
                query,
                context,
                config,
                max_depth,
                branching_factor,
                top_k
            )
            steps.extend(expansion_steps)
            
            # Step 3: Select best path
            selection_step = await self._select_best_path(
                query,
                context,
                config
            )
            steps.append(selection_step)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Calculate confidence based on best path score
            confidence = self._calculate_tree_confidence()
            
            # Get tree structure for metadata
            tree_structure = self._get_tree_structure()
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=True,
                steps=steps,
                final_answer=selection_step.response,
                confidence=confidence,
                total_duration_ms=duration_ms,
                metadata={
                    "tree_structure": tree_structure,
                    "total_nodes": len(self.thought_tree),
                    "max_depth_reached": max([n.depth for n in self.thought_tree.values()] or [0]),
                    "terminal_nodes": sum(1 for n in self.thought_tree.values() if n.is_terminal)
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error executing ToT pattern: {e}", exc_info=True)
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            return PatternResult(
                pattern_type=self.pattern_type,
                success=False,
                steps=steps,
                total_duration_ms=duration_ms,
                error=str(e)
            )
    
    async def _generate_initial_thoughts(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        count: int
    ) -> PatternStep:
        """Generate initial thoughts (root level)."""
        step = self.create_step(
            step_id="generate_root",
            step_type="generation",
            description=f"Generate {count} initial reasoning paths",
            prompt=self._build_generation_prompt(query, context, None, count)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            # Parse thoughts from response
            thoughts = self._extract_thoughts(response, count)
            
            # Create root nodes
            for thought in thoughts:
                node_id = f"node_{self.node_counter}"
                self.node_counter += 1
                
                node = ThoughtNode(
                    node_id=node_id,
                    thought=thought,
                    parent_id=None,
                    depth=0
                )
                self.thought_tree[node_id] = node
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "root_generation",
                    "thoughts_generated": len(thoughts),
                    "root_nodes": [n.node_id for n in self.thought_tree.values()]
                }
            )
        
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _expand_tree(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        max_depth: int,
        branching_factor: int,
        top_k: int
    ) -> List[PatternStep]:
        """Expand tree iteratively."""
        expansion_steps = []
        
        for depth in range(1, max_depth + 1):
            # Get nodes at previous depth
            parent_nodes = [
                n for n in self.thought_tree.values()
                if n.depth == depth - 1 and not n.is_terminal
            ]
            
            if not parent_nodes:
                break
            
            # Evaluate parent nodes
            eval_step = await self._evaluate_nodes(
                parent_nodes,
                query,
                context,
                config
            )
            expansion_steps.append(eval_step)
            
            # Select top-k nodes to expand
            parent_nodes.sort(key=lambda n: n.score, reverse=True)
            nodes_to_expand = parent_nodes[:top_k]
            
            # Expand selected nodes
            for parent_node in nodes_to_expand:
                expand_step = await self._expand_node(
                    parent_node,
                    query,
                    context,
                    config,
                    branching_factor,
                    depth
                )
                expansion_steps.append(expand_step)
        
        return expansion_steps
    
    async def _evaluate_nodes(
        self,
        nodes: List[ThoughtNode],
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Evaluate promise of nodes."""
        step = self.create_step(
            step_id=f"evaluate_depth_{nodes[0].depth}",
            step_type="evaluation",
            description=f"Evaluate {len(nodes)} thoughts at depth {nodes[0].depth}",
            prompt=self._build_evaluation_prompt(nodes, query, context)
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            # Parse evaluations
            evaluations = self._extract_evaluations(response, len(nodes))
            
            # Update node scores
            for node, (score, evaluation) in zip(nodes, evaluations):
                node.score = score
                node.evaluation = evaluation
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "evaluation",
                    "nodes_evaluated": len(nodes),
                    "scores": [n.score for n in nodes]
                }
            )
        
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _expand_node(
        self,
        parent_node: ThoughtNode,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any],
        branching_factor: int,
        depth: int
    ) -> PatternStep:
        """Expand a single node."""
        step = self.create_step(
            step_id=f"expand_{parent_node.node_id}",
            step_type="expansion",
            description=f"Expand node {parent_node.node_id} (score: {parent_node.score:.2f})",
            prompt=self._build_generation_prompt(
                query,
                context,
                parent_node,
                branching_factor
            )
        )
        
        try:
            response = await self.call_llm(step.prompt, config)
            
            # Parse child thoughts
            thoughts = self._extract_thoughts(response, branching_factor)
            
            # Create child nodes
            child_ids = []
            for thought in thoughts:
                node_id = f"node_{self.node_counter}"
                self.node_counter += 1
                
                child_node = ThoughtNode(
                    node_id=node_id,
                    thought=thought,
                    parent_id=parent_node.node_id,
                    depth=depth
                )
                
                # Check if terminal (simple heuristic)
                if "answer:" in thought.lower() or "conclusion:" in thought.lower():
                    child_node.is_terminal = True
                
                self.thought_tree[node_id] = child_node
                parent_node.add_child(child_node)
                child_ids.append(node_id)
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "expansion",
                    "parent_node": parent_node.node_id,
                    "child_nodes": child_ids,
                    "depth": depth
                }
            )
        
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    async def _select_best_path(
        self,
        query: str,
        context: Dict[str, Any],
        config: Dict[str, Any]
    ) -> PatternStep:
        """Select best path through tree."""
        step = self.create_step(
            step_id="select_path",
            step_type="selection",
            description="Select best reasoning path through tree",
            prompt=""  # Will build based on best path
        )
        
        try:
            # Find best terminal node
            terminal_nodes = [
                n for n in self.thought_tree.values()
                if n.is_terminal or not n.children
            ]
            
            if not terminal_nodes:
                # No terminal nodes, use leaf nodes
                terminal_nodes = [
                    n for n in self.thought_tree.values()
                    if not n.children
                ]
            
            # Sort by score (use parent score if not evaluated)
            for node in terminal_nodes:
                if node.score == 0.0 and node.parent_id:
                    parent = self.thought_tree.get(node.parent_id)
                    if parent:
                        node.score = parent.score * 0.9  # Inherit with penalty
            
            terminal_nodes.sort(key=lambda n: n.score, reverse=True)
            best_node = terminal_nodes[0] if terminal_nodes else None
            
            if not best_node:
                return self.complete_step(step, "No valid path found", {"error": True})
            
            # Trace path from best node to root
            path = self._trace_path(best_node)
            
            # Build synthesis prompt
            step.prompt = self._build_path_synthesis_prompt(query, path, context)
            
            # Generate final answer from best path
            response = await self.call_llm(step.prompt, config)
            
            self.complete_step(
                step,
                response,
                {
                    "stage": "selection",
                    "best_node": best_node.node_id,
                    "path_length": len(path),
                    "final_score": best_node.score,
                    "path": [n.node_id for n in path]
                }
            )
        
        except Exception as e:
            self.complete_step(step, f"Error: {e}", {"error": True})
        
        return step
    
    def _build_generation_prompt(
        self,
        query: str,
        context: Dict[str, Any],
        parent_node: Optional[ThoughtNode],
        count: int
    ) -> str:
        """Build prompt for thought generation."""
        context_str = self._format_context(context)
        
        if parent_node is None:
            # Root level
            return f"""Generate {count} distinct initial reasoning approaches to solve this query.

Query: {query}

{context_str}

Instructions:
1. Think of {count} different ways to approach this problem
2. Each approach should be unique and promising
3. Be specific about the reasoning strategy
4. Number each approach
5. Keep each approach to 2-3 sentences

Approaches:"""
        else:
            # Expanding a node
            return f"""Continue the following reasoning path by generating {count} possible next steps.

Original Query: {query}

Previous reasoning: {parent_node.thought}

{context_str}

Instructions:
1. Build on the previous reasoning
2. Generate {count} distinct next steps
3. Each step should advance toward the solution
4. Number each step
5. If you reach a conclusion, start with "Answer:" or "Conclusion:"

Next steps:"""
    
    def _build_evaluation_prompt(
        self,
        nodes: List[ThoughtNode],
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for node evaluation."""
        context_str = self._format_context(context)
        
        thoughts_str = "\n\n".join([
            f"{i+1}. {node.thought}"
            for i, node in enumerate(nodes)
        ])
        
        return f"""Evaluate how promising each reasoning path is for solving the query.

Query: {query}

{context_str}

Reasoning paths to evaluate:
{thoughts_str}

Instructions:
1. For each path, rate its promise on a scale of 0-10
2. Consider: relevance, correctness, completeness
3. Format: "Path X: [score]/10 - [brief reasoning]"
4. Be critical but fair

Evaluations:"""
    
    def _build_path_synthesis_prompt(
        self,
        query: str,
        path: List[ThoughtNode],
        context: Dict[str, Any]
    ) -> str:
        """Build prompt for synthesizing final answer from path."""
        context_str = self._format_context(context)
        
        path_str = "\n\n".join([
            f"Step {i+1} (depth {node.depth}): {node.thought}"
            for i, node in enumerate(path)
        ])
        
        return f"""Based on the best reasoning path below, provide a clear final answer to the query.

Query: {query}

{context_str}

Reasoning path (highest scoring):
{path_str}

Instructions:
1. Synthesize the reasoning into a coherent answer
2. Address the original query directly
3. Be concise but complete
4. Mention key insights

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
    
    def _extract_thoughts(self, response: str, count: int) -> List[str]:
        """Extract thoughts from response."""
        if not response:
            return []
        
        thoughts = []
        lines = response.strip().split('\n')
        current_thought = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_thought:
                    thoughts.append(' '.join(current_thought))
                    current_thought = []
                continue
            
            # Check if new thought starts
            if line[0].isdigit() or line.startswith('-') or line.startswith('•'):
                if current_thought:
                    thoughts.append(' '.join(current_thought))
                current_thought = [line]
            else:
                current_thought.append(line)
        
        if current_thought:
            thoughts.append(' '.join(current_thought))
        
        # Clean numbering
        cleaned = []
        for thought in thoughts:
            for prefix in ['1.', '2.', '3.', '4.', '5.', '-', '•', '*']:
                if thought.startswith(prefix):
                    thought = thought[len(prefix):].strip()
                    break
            cleaned.append(thought)
        
        return cleaned[:count]
    
    def _extract_evaluations(
        self,
        response: str,
        count: int
    ) -> List[tuple[float, str]]:
        """Extract scores and evaluations from response."""
        evaluations = []
        lines = response.strip().split('\n')
        
        for line in lines:
            # Look for pattern like "Path 1: 8/10 - reasoning"
            if '/' in line and '/10' in line:
                try:
                    # Extract score
                    score_part = line.split('/10')[0]
                    score_str = score_part.split(':')[-1].strip()
                    score = float(score_str) / 10.0
                    
                    # Extract reasoning
                    if '-' in line:
                        reasoning = line.split('-', 1)[1].strip()
                    else:
                        reasoning = "No specific reasoning provided"
                    
                    evaluations.append((score, reasoning))
                except:
                    continue
        
        # Fill missing evaluations with default
        while len(evaluations) < count:
            evaluations.append((0.5, "No evaluation available"))
        
        return evaluations[:count]
    
    def _trace_path(self, node: ThoughtNode) -> List[ThoughtNode]:
        """Trace path from node to root."""
        path = []
        current = node
        
        while current:
            path.insert(0, current)
            if current.parent_id:
                current = self.thought_tree.get(current.parent_id)
            else:
                current = None
        
        return path
    
    def _get_tree_structure(self) -> Dict[str, Any]:
        """Get tree structure for metadata."""
        return {
            node_id: node.to_dict()
            for node_id, node in self.thought_tree.items()
        }
    
    def _calculate_tree_confidence(self) -> float:
        """Calculate confidence based on tree exploration."""
        if not self.thought_tree:
            return 0.0
        
        # Find best terminal node
        terminal_nodes = [
            n for n in self.thought_tree.values()
            if n.is_terminal or not n.children
        ]
        
        if not terminal_nodes:
            return 0.5
        
        # Get best score
        best_score = max(n.score for n in terminal_nodes)
        
        # Adjust by tree depth (deeper = more thorough)
        max_depth = max(n.depth for n in self.thought_tree.values())
        depth_factor = min(max_depth / 3.0, 1.0)
        
        # Combine factors
        confidence = best_score * 0.7 + depth_factor * 0.3
        
        return min(confidence, 1.0)

