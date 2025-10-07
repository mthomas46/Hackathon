"""Conflict resolution for multiple MCP responses."""

from typing import Dict, Any, List
import logging
from collections import Counter

from services.mcp_composer.domain.entities import Composition, ConflictResolution


class ConflictResolver:
    """
    Resolves conflicts between multiple MCP responses.
    
    Implements various strategies: priority, merge, vote, expert, latest, consensus.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def resolve(
        self,
        responses: List[Dict[str, Any]],
        composition: Composition
    ) -> Dict[str, Any]:
        """
        Resolve conflicts between MCP responses.
        
        Args:
            responses: List of MCP responses
            composition: Composition defining resolution strategy
        
        Returns:
            Resolved response
        """
        # Filter successful responses
        successful = [r for r in responses if r.get("success")]
        
        if not successful:
            raise ValueError("No successful responses to resolve")
        
        self.logger.info(
            f"Resolving {len(successful)} responses using "
            f"{composition.conflict_resolution.value} strategy"
        )
        
        if composition.conflict_resolution == ConflictResolution.PRIORITY:
            return self._resolve_by_priority(successful, composition)
        elif composition.conflict_resolution == ConflictResolution.MERGE:
            return self._resolve_by_merge(successful, composition)
        elif composition.conflict_resolution == ConflictResolution.VOTE:
            return self._resolve_by_vote(successful, composition)
        elif composition.conflict_resolution == ConflictResolution.EXPERT:
            return self._resolve_by_expert(successful, composition)
        elif composition.conflict_resolution == ConflictResolution.LATEST:
            return self._resolve_by_latest(successful, composition)
        elif composition.conflict_resolution == ConflictResolution.CONSENSUS:
            return self._resolve_by_consensus(successful, composition)
        else:
            raise ValueError(f"Unknown resolution strategy: {composition.conflict_resolution}")
    
    def _resolve_by_priority(
        self,
        responses: List[Dict[str, Any]],
        composition: Composition
    ) -> Dict[str, Any]:
        """Use highest priority MCP response."""
        # Sort by MCP priority
        sorted_responses = sorted(
            responses,
            key=lambda r: self._get_mcp_priority(r["mcp_id"], composition)
        )
        
        chosen = sorted_responses[0]
        self.logger.info(f"Selected response from {chosen['mcp_id']} (highest priority)")
        
        return {
            "answer": chosen["response"].get("answer", ""),
            "source_mcp": chosen["mcp_id"],
            "resolution_strategy": "priority",
            "confidence": chosen["response"].get("confidence", 0.5),
            "sources": chosen["response"].get("sources", []),
            "all_responses": responses
        }
    
    def _resolve_by_merge(
        self,
        responses: List[Dict[str, Any]],
        composition: Composition
    ) -> Dict[str, Any]:
        """Merge all responses intelligently."""
        # Collect all answers
        answers = []
        all_sources = []
        total_confidence = 0.0
        
        for r in responses:
            resp = r["response"]
            answers.append(resp.get("answer", ""))
            all_sources.extend(resp.get("sources", []))
            total_confidence += resp.get("confidence", 0.5)
        
        # Deduplicate sources if requested
        if composition.deduplicate:
            all_sources = self._deduplicate_sources(all_sources)
        
        # Merge answers
        merged_answer = self._merge_answers(answers, composition)
        
        avg_confidence = total_confidence / len(responses) if responses else 0.0
        
        return {
            "answer": merged_answer,
            "resolution_strategy": "merge",
            "confidence": avg_confidence,
            "sources": all_sources,
            "num_responses_merged": len(responses),
            "all_responses": responses
        }
    
    def _resolve_by_vote(
        self,
        responses: List[Dict[str, Any]],
        composition: Composition
    ) -> Dict[str, Any]:
        """Democratic voting on answers."""
        # Extract answers
        answers = [r["response"].get("answer", "") for r in responses]
        
        # Count votes (using first 100 chars for similarity)
        answer_votes = Counter([a[:100] for a in answers])
        most_common_prefix, votes = answer_votes.most_common(1)[0]
        
        # Find full answer matching the winner
        winning_answer = next(a for a in answers if a[:100] == most_common_prefix)
        
        # Find winning response for full details
        winning_response = next(
            r for r in responses
            if r["response"].get("answer", "")[:100] == most_common_prefix
        )
        
        self.logger.info(f"Vote winner: {votes}/{len(responses)} votes")
        
        return {
            "answer": winning_answer,
            "source_mcp": winning_response["mcp_id"],
            "resolution_strategy": "vote",
            "confidence": votes / len(responses),
            "votes": votes,
            "total_votes": len(responses),
            "sources": winning_response["response"].get("sources", []),
            "all_responses": responses
        }
    
    def _resolve_by_expert(
        self,
        responses: List[Dict[str, Any]],
        composition: Composition
    ) -> Dict[str, Any]:
        """Defer to expert MCP (highest tier)."""
        tier_priority = {
            "client": 1,
            "project": 2,
            "company": 3,
            "team": 4,
            "ecosystem": 5
        }
        
        # Find highest tier response (lowest number = highest priority)
        expert_response = min(
            responses,
            key=lambda r: tier_priority.get(r["tier"], 10)
        )
        
        self.logger.info(f"Expert response from tier: {expert_response['tier']}")
        
        return {
            "answer": expert_response["response"].get("answer", ""),
            "source_mcp": expert_response["mcp_id"],
            "expert_tier": expert_response["tier"],
            "resolution_strategy": "expert",
            "confidence": expert_response["response"].get("confidence", 0.5),
            "sources": expert_response["response"].get("sources", []),
            "all_responses": responses
        }
    
    def _resolve_by_latest(
        self,
        responses: List[Dict[str, Any]],
        composition: Composition
    ) -> Dict[str, Any]:
        """Use the most recent/last response."""
        latest = responses[-1]
        
        return {
            "answer": latest["response"].get("answer", ""),
            "source_mcp": latest["mcp_id"],
            "resolution_strategy": "latest",
            "confidence": latest["response"].get("confidence", 0.5),
            "sources": latest["response"].get("sources", []),
            "all_responses": responses
        }
    
    def _resolve_by_consensus(
        self,
        responses: List[Dict[str, Any]],
        composition: Composition
    ) -> Dict[str, Any]:
        """Require consensus (similar answers)."""
        answers = [r["response"].get("answer", "") for r in responses]
        
        # Simple consensus: check if answers are similar
        # (In production, use semantic similarity)
        answer_prefixes = [a[:100] for a in answers]
        most_common_prefix = Counter(answer_prefixes).most_common(1)[0][0]
        consensus_count = answer_prefixes.count(most_common_prefix)
        
        consensus_threshold = composition.metadata.get("consensus_threshold", 0.66)
        has_consensus = (consensus_count / len(responses)) >= consensus_threshold
        
        if not has_consensus:
            raise ValueError(
                f"No consensus reached. {consensus_count}/{len(responses)} "
                f"agree (need {consensus_threshold:.0%})"
            )
        
        # Find consensus answer
        consensus_answer = next(a for a in answers if a[:100] == most_common_prefix)
        consensus_response = next(
            r for r in responses
            if r["response"].get("answer", "")[:100] == most_common_prefix
        )
        
        return {
            "answer": consensus_answer,
            "source_mcp": consensus_response["mcp_id"],
            "resolution_strategy": "consensus",
            "confidence": consensus_count / len(responses),
            "consensus_count": consensus_count,
            "total_responses": len(responses),
            "sources": consensus_response["response"].get("sources", []),
            "all_responses": responses
        }
    
    def _get_mcp_priority(self, mcp_id: str, composition: Composition) -> int:
        """Get priority for an MCP."""
        mcp = composition.get_mcp(mcp_id)
        return mcp.priority if mcp else 999
    
    def _deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate sources."""
        seen = set()
        unique = []
        
        for source in sources:
            # Use URL or ID as key
            key = source.get("url") or source.get("id") or str(source)
            if key not in seen:
                seen.add(key)
                unique.append(source)
        
        return unique
    
    def _merge_answers(self, answers: List[str], composition: Composition) -> str:
        """Merge multiple answers into one."""
        if not answers:
            return ""
        
        # Simple merge: concatenate with separator
        # In production, use LLM to synthesize
        merged = "\n\n".join([
            f"[Response {i+1}] {answer}"
            for i, answer in enumerate(answers)
            if answer
        ])
        
        # Truncate if too long
        max_length = composition.max_response_length
        if len(merged) > max_length:
            merged = merged[:max_length] + "... (truncated)"
        
        return merged
