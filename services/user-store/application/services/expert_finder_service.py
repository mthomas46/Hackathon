"""
Expert Finder Service

Intelligent user discovery service tightly coupled with user-store.
Uses user data, relationships, and document associations to find relevant experts.

This service:
- Directly queries user-store database for efficient lookups
- Analyzes user-document relationships
- Scores expertise based on interactions and topics
- Supports natural language queries for finding experts
- Can integrate with LLM-gateway for advanced query understanding
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

from ...domain.entities.user import User
from ...domain.repositories.user_repository import UserRepository


@dataclass
class ExpertMatch:
    """A matched expert with relevance scoring."""
    user: User
    relevance_score: float  # 0.0 to 1.0
    explanation: str
    evidence: List[str]
    metadata: Dict[str, Any]


@dataclass
class ExpertSearchResult:
    """Result of expert search."""
    query: str
    matches: List[ExpertMatch]
    total_candidates: int
    execution_time_ms: float


class ExpertFinderService:
    """
    Service for intelligent expert discovery within user-store.
    Tightly coupled with user repository for efficient database access.
    """
    
    def __init__(self, user_repository: UserRepository):
        """Initialize with user repository for direct database access."""
        self.user_repo = user_repository
    
    def extract_keywords(self, query: str) -> Dict[str, List[str]]:
        """Extract keywords from query using pattern matching."""
        query_lower = query.lower()
        
        # Technology keywords
        tech_keywords = [
            "python", "java", "javascript", "typescript", "go", "rust", "c++", "c#",
            "react", "vue", "angular", "node", "django", "flask", "spring", "express",
            "kubernetes", "docker", "aws", "gcp", "azure", "terraform",
            "postgresql", "mongodb", "redis", "mysql",
            "ios", "android", "swift", "kotlin", "react native"
        ]
        
        # Role/domain keywords
        role_keywords = [
            "backend", "frontend", "fullstack", "full stack", "full-stack",
            "devops", "mobile", "ios", "android", "architect", "engineer", 
            "developer", "senior", "junior", "lead", "principal"
        ]
        
        # Skill/action keywords
        skill_keywords = [
            "expert", "experienced", "specialist", "knows", "familiar",
            "worked on", "created", "built", "designed", "implemented"
        ]
        
        found_tech = [k for k in tech_keywords if k in query_lower]
        found_roles = [k for k in role_keywords if k in query_lower]
        found_skills = [k for k in skill_keywords if k in query_lower]
        
        return {
            "technologies": found_tech,
            "roles": found_roles,
            "skills": found_skills
        }
    
    def score_user_relevance(
        self,
        user: User,
        keywords: Dict[str, List[str]],
        query: str
    ) -> Tuple[float, List[str]]:
        """
        Score how relevant a user is to the query.
        Returns (score, evidence_list).
        """
        score = 0.0
        evidence = []
        
        # 1. Role matching (30% weight)
        user_role = user.role.value.lower() if hasattr(user.role, 'value') else str(user.role).lower()
        for role_keyword in keywords.get("roles", []):
            if role_keyword in user_role or role_keyword in user.display_name.lower():
                score += 0.3
                evidence.append(f"Role: {user_role}")
                break
        
        # 2. Topic/Interest matching (40% weight)
        user_topics = [t.lower() for t in user.topic_interests]
        for tech in keywords.get("technologies", []):
            matching_topics = [t for t in user_topics if tech in t]
            if matching_topics:
                score += 0.2  # 0.2 per tech (up to 0.4 for 2+ techs)
                evidence.append(f"Topic expertise: {', '.join(matching_topics[:3])}")
        
        # 3. Service subscriptions (20% weight)
        user_services = [s.lower() for s in user.service_subscriptions]
        for tech in keywords.get("technologies", []):
            matching_services = [s for s in user_services if tech in s]
            if matching_services:
                score += 0.1
                evidence.append(f"Service: {', '.join(matching_services[:2])}")
        
        # 4. Document relationships (10% weight - shows actual work)
        doc_count = len(user.document_relationships)
        if doc_count > 0:
            doc_score = min(doc_count * 0.02, 0.1)  # Cap at 0.1
            score += doc_score
            evidence.append(f"{doc_count} related documents")
        
        # 5. User tags (inferred expertise) - bonus
        if hasattr(user, 'user_tags') and user.user_tags:
            for tech in keywords.get("technologies", []):
                if any(tech in tag.lower() for tag in user.user_tags):
                    score += 0.1
                    evidence.append(f"Tagged: {tech}")
                    break
        
        # 6. Name/username relevance - bonus
        query_words = set(query.lower().split())
        name_words = set(user.display_name.lower().split())
        username_words = set(user.username.lower().split('_') + user.username.lower().split('.'))
        
        if query_words & (name_words | username_words):
            score += 0.05
            evidence.append("Name match")
        
        return min(score, 1.0), evidence
    
    async def find_experts(
        self,
        query: str,
        max_results: int = 5,
        min_score: float = 0.1,
        team_id: Optional[str] = None,
        exclude_team: bool = False
    ) -> ExpertSearchResult:
        """
        Find experts matching a natural language query.
        
        Args:
            query: Natural language query (e.g., "Who knows Python backend?")
            max_results: Maximum number of results to return
            min_score: Minimum relevance score threshold
            team_id: If provided, can include/exclude team members
            exclude_team: If True and team_id provided, exclude team members
        
        Returns:
            ExpertSearchResult with matched users
        """
        start_time = datetime.utcnow()
        
        # Get all users from database
        all_users = await self.user_repo.find_all()
        
        # Filter by team if specified
        if team_id:
            if exclude_team:
                # Exclude team members (find external experts)
                all_users = [u for u in all_users if u.team_id != team_id]
            else:
                # Only team members
                all_users = [u for u in all_users if u.team_id == team_id]
        
        # Extract keywords from query
        keywords = self.extract_keywords(query)
        
        # Score all users
        scored_users = []
        for user in all_users:
            score, evidence = self.score_user_relevance(user, keywords, query)
            
            if score >= min_score:
                scored_users.append({
                    "user": user,
                    "score": score,
                    "evidence": evidence
                })
        
        # Sort by score (highest first)
        scored_users.sort(key=lambda x: x["score"], reverse=True)
        
        # Convert to ExpertMatch objects
        matches = []
        for item in scored_users[:max_results]:
            user = item["user"]
            matches.append(ExpertMatch(
                user=user,
                relevance_score=item["score"],
                explanation=f"Matched on: {', '.join(item['evidence'][:3])}",
                evidence=item["evidence"],
                metadata={
                    "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                    "topics": user.topic_interests[:3],
                    "services": user.service_subscriptions[:3],
                    "document_count": len(user.document_relationships),
                    "team_id": user.team_id
                }
            ))
        
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return ExpertSearchResult(
            query=query,
            matches=matches,
            total_candidates=len(scored_users),
            execution_time_ms=execution_time
        )
    
    async def find_experts_by_topic(
        self,
        topic: str,
        max_results: int = 5
    ) -> List[ExpertMatch]:
        """Find experts for a specific topic."""
        result = await self.find_experts(
            query=f"Who knows {topic}?",
            max_results=max_results
        )
        return result.matches
    
    async def find_experts_by_service(
        self,
        service: str,
        max_results: int = 5
    ) -> List[ExpertMatch]:
        """Find experts who worked on a specific service."""
        all_users = await self.user_repo.find_all()
        
        matches = []
        for user in all_users:
            # Check if user subscribed to this service
            if any(service.lower() in s.lower() for s in user.service_subscriptions):
                score = 0.8  # High score for direct service subscription
                evidence = [f"Subscribed to {service}"]
                
                # Bonus for document relationships
                if user.document_relationships:
                    score = min(score + 0.1, 1.0)
                    evidence.append(f"{len(user.document_relationships)} related documents")
                
                matches.append(ExpertMatch(
                    user=user,
                    relevance_score=score,
                    explanation=f"Works on {service}",
                    evidence=evidence,
                    metadata={
                        "services": user.service_subscriptions,
                        "document_count": len(user.document_relationships)
                    }
                ))
        
        # Sort by score
        matches.sort(key=lambda x: x.relevance_score, reverse=True)
        return matches[:max_results]
    
    async def find_teammates(
        self,
        user_id: str,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find potential teammates for a user based on shared interests.
        """
        # Get the target user
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            return []
        
        # Get all other users
        all_users = await self.user_repo.find_all()
        
        user_topics = set(user.topic_interests)
        user_services = set(user.service_subscriptions)
        
        potential_teammates = []
        
        for other_user in all_users:
            if other_user.id == user_id:
                continue  # Skip self
            
            other_topics = set(other_user.topic_interests)
            other_services = set(other_user.service_subscriptions)
            
            # Calculate overlap
            shared_topics = user_topics & other_topics
            shared_services = user_services & other_services
            
            if shared_topics or shared_services:
                # Score based on overlap
                topic_score = len(shared_topics) * 0.3
                service_score = len(shared_services) * 0.7
                total_score = min(topic_score + service_score, 1.0)
                
                potential_teammates.append({
                    "user": other_user,
                    "collaboration_score": total_score,
                    "shared_topics": list(shared_topics),
                    "shared_services": list(shared_services),
                    "same_team": other_user.team_id == user.team_id if user.team_id else False
                })
        
        # Sort by collaboration score
        potential_teammates.sort(key=lambda x: x["collaboration_score"], reverse=True)
        
        return potential_teammates[:max_results]
    
    async def find_subject_matter_experts(
        self,
        area: str,
        min_documents: int = 3,
        max_results: int = 5
    ) -> List[ExpertMatch]:
        """
        Find subject matter experts in a specific area.
        Requires users to have meaningful document relationships (actual work).
        """
        # Use expert finder with higher threshold
        result = await self.find_experts(
            query=f"Expert in {area}",
            max_results=max_results * 2,  # Get more candidates
            min_score=0.3  # Higher threshold for SMEs
        )
        
        # Filter to those with sufficient document history
        smes = [
            match for match in result.matches
            if len(match.user.document_relationships) >= min_documents
        ]
        
        # Re-score with document count emphasis
        for match in smes:
            doc_bonus = min(len(match.user.document_relationships) * 0.05, 0.3)
            match.relevance_score = min(match.relevance_score + doc_bonus, 1.0)
            match.evidence.append(f"SME: {len(match.user.document_relationships)} documents")
        
        # Re-sort and limit
        smes.sort(key=lambda x: x.relevance_score, reverse=True)
        return smes[:max_results]
    
    async def get_team_expertise_summary(
        self,
        team_id: str
    ) -> Dict[str, Any]:
        """
        Get expertise summary for a team.
        """
        # Find users by team
        team_members = await self.user_repo.find_by_team_id(team_id)
        
        if not team_members:
            return {
                "team_id": team_id,
                "member_count": 0,
                "topics": [],
                "services": [],
                "total_documents": 0
            }
        
        # Aggregate expertise
        all_topics = []
        all_services = []
        total_docs = 0
        
        for member in team_members:
            all_topics.extend(member.topic_interests)
            all_services.extend(member.service_subscriptions)
            total_docs += len(member.document_relationships)
        
        # Count frequencies
        from collections import Counter
        topic_counts = Counter(all_topics)
        service_counts = Counter(all_services)
        
        return {
            "team_id": team_id,
            "member_count": len(team_members),
            "topics": [{"topic": k, "count": v} for k, v in topic_counts.most_common(10)],
            "services": [{"service": k, "count": v} for k, v in service_counts.most_common(10)],
            "total_documents": total_docs,
            "avg_documents_per_member": total_docs / len(team_members) if team_members else 0
        }

