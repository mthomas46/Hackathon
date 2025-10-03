"""
External Service Discovery Engine - Phase 9.1
Discovers relevant external services from feature requirements.
"""

from typing import List, Dict, Any, Optional, Set
import re
from datetime import datetime

from ..entities.external_service_entities import (
    ExternalServiceMatch,
    DiscoveryMethod,
    ServiceCategory
)


class ExternalServiceDiscoveryEngine:
    """
    Discovers external services relevant to a feature from:
    - Explicit mentions in the query
    - Topic matching
    - Technology matching
    - Team experience
    - Historical usage
    """
    
    def __init__(
        self,
        external_service_store_client=None,
        log_client=None
    ):
        """Initialize the discovery engine."""
        self.external_service_store = external_service_store_client
        self.log_client = log_client
        
        # Common external service names and aliases
        self.known_services = {
            "firebase": ["firebase", "fcm", "firebase cloud messaging"],
            "sendgrid": ["sendgrid", "send grid"],
            "twilio": ["twilio"],
            "stripe": ["stripe"],
            "auth0": ["auth0", "auth zero"],
            "okta": ["okta"],
            "aws": ["aws", "amazon web services"],
            "gcp": ["gcp", "google cloud"],
            "azure": ["azure", "microsoft azure"],
            "mongodb": ["mongodb", "mongo"],
            "redis": ["redis"],
            "elasticsearch": ["elasticsearch", "elastic"],
            "kafka": ["kafka", "apache kafka"],
            "rabbitmq": ["rabbitmq", "rabbit mq"],
        }
    
    async def discover_services(
        self,
        feature_query: str,
        extracted_requirements: Dict[str, Any]
    ) -> List[ExternalServiceMatch]:
        """
        Discover external services relevant to the feature.
        
        Args:
            feature_query: The original natural language query
            extracted_requirements: Structured requirements from interpreter
        
        Returns:
            List of discovered external services with relevance scores
        """
        if self.log_client:
            await self.log_client.log_info(
                "Starting external service discovery",
                context={"query_length": len(feature_query)}
            )
        
        all_matches: Dict[str, ExternalServiceMatch] = {}
        
        # Step 1: Extract explicitly mentioned services
        mentioned = self._extract_mentioned_services(feature_query, extracted_requirements)
        for service in mentioned:
            all_matches[service.service_id] = service
        
        # Step 2: Search by topic
        topics = self._extract_topics(feature_query, extracted_requirements)
        if self.external_service_store and topics:
            topic_matches = await self._search_by_topic(topics)
            for service in topic_matches:
                if service.service_id in all_matches:
                    # Merge discovery methods
                    all_matches[service.service_id].discovery_methods.extend(
                        service.discovery_methods
                    )
                    all_matches[service.service_id].relevance_score = max(
                        all_matches[service.service_id].relevance_score,
                        service.relevance_score
                    )
                else:
                    all_matches[service.service_id] = service
        
        # Step 3: Search by technology
        technologies = self._extract_technologies(feature_query, extracted_requirements)
        if self.external_service_store and technologies:
            tech_matches = await self._search_by_technology(technologies)
            for service in tech_matches:
                if service.service_id in all_matches:
                    all_matches[service.service_id].discovery_methods.extend(
                        service.discovery_methods
                    )
                    all_matches[service.service_id].relevance_score = max(
                        all_matches[service.service_id].relevance_score,
                        service.relevance_score
                    )
                else:
                    all_matches[service.service_id] = service
        
        # Step 4: Calculate final relevance scores
        for service in all_matches.values():
            service.relevance_score = self._calculate_final_relevance(
                service,
                feature_query,
                extracted_requirements
            )
            
            # Categorize based on relevance
            if service.relevance_score >= 0.85:
                service.initial_category = ServiceCategory.DIRECT
            elif service.relevance_score >= 0.60:
                service.initial_category = ServiceCategory.TANGENTIAL
            else:
                service.initial_category = ServiceCategory.EXCLUDED
        
        # Step 5: Rank and return top services
        ranked = sorted(
            all_matches.values(),
            key=lambda s: s.relevance_score,
            reverse=True
        )
        
        # Return top 15
        top_services = ranked[:15]
        
        if self.log_client:
            await self.log_client.log_info(
                f"Discovered {len(top_services)} relevant external services",
                context={
                    "total_found": len(all_matches),
                    "high_relevance": len([s for s in top_services if s.relevance_score >= 0.85]),
                    "medium_relevance": len([s for s in top_services if 0.60 <= s.relevance_score < 0.85])
                }
            )
        
        return top_services
    
    def _extract_mentioned_services(
        self,
        query: str,
        requirements: Dict[str, Any]
    ) -> List[ExternalServiceMatch]:
        """Extract services explicitly mentioned in the query."""
        mentioned = []
        query_lower = query.lower()
        
        for service_name, aliases in self.known_services.items():
            for alias in aliases:
                if alias in query_lower:
                    # Find context around the mention
                    pattern = rf'.{{0,50}}{re.escape(alias)}.{{0,50}}'
                    match = re.search(pattern, query_lower, re.IGNORECASE)
                    context = match.group(0) if match else None
                    
                    mentioned.append(ExternalServiceMatch(
                        service_id=f"{service_name}-api",
                        name=service_name.title(),
                        relevance_score=0.35,  # Base score for explicit mention
                        discovery_methods=[DiscoveryMethod.EXPLICIT_MENTION],
                        initial_category=ServiceCategory.DIRECT,
                        mentioned_context=context
                    ))
                    break  # Only count once per service
        
        return mentioned
    
    def _extract_topics(
        self,
        query: str,
        requirements: Dict[str, Any]
    ) -> List[str]:
        """Extract relevant topics from the query."""
        topics = set()
        query_lower = query.lower()
        
        # Topic mapping
        topic_keywords = {
            "notifications": ["notification", "notify", "alert", "push", "email", "sms"],
            "authentication": ["auth", "login", "oauth", "sso", "identity", "access"],
            "payments": ["payment", "checkout", "billing", "stripe", "subscription"],
            "storage": ["storage", "bucket", "blob", "file", "upload", "download"],
            "database": ["database", "db", "sql", "nosql", "storage", "persist"],
            "messaging": ["message", "queue", "pubsub", "kafka", "event"],
            "analytics": ["analytics", "tracking", "metrics", "monitoring"],
            "email": ["email", "mail", "sendgrid", "mailgun"],
            "sms": ["sms", "text", "twilio"],
            "push": ["push", "notification", "fcm", "apns"],
            "mobile": ["mobile", "ios", "android", "app"],
            "real-time": ["real-time", "realtime", "websocket", "live"],
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                topics.add(topic)
        
        # Also check extracted requirements
        if "feature_type" in requirements:
            feature_type = requirements["feature_type"].lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in feature_type for keyword in keywords):
                    topics.add(topic)
        
        return list(topics)
    
    def _extract_technologies(
        self,
        query: str,
        requirements: Dict[str, Any]
    ) -> List[str]:
        """Extract mentioned technologies."""
        technologies = set()
        query_lower = query.lower()
        
        # Technology keywords
        tech_keywords = {
            "iOS SDK": ["ios", "swift", "objective-c", "xcode", "apns"],
            "Android SDK": ["android", "kotlin", "java", "fcm"],
            "REST API": ["rest", "api", "http", "endpoint"],
            "WebSocket": ["websocket", "ws", "real-time"],
            "Python": ["python", "django", "flask"],
            "Node.js": ["node", "nodejs", "javascript", "express"],
            "React": ["react", "reactjs", "jsx"],
            "Mobile": ["mobile", "ios", "android"],
        }
        
        for tech, keywords in tech_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                technologies.add(tech)
        
        # Check integrations in requirements
        if "integrations" in requirements:
            for integration in requirements["integrations"]:
                technologies.add(integration)
        
        return list(technologies)
    
    async def _search_by_topic(self, topics: List[str]) -> List[ExternalServiceMatch]:
        """Search external service store by topics (mock implementation)."""
        # Mock implementation - would call external-service-store
        matches = []
        
        # Simulate topic-based matches
        topic_service_map = {
            "notifications": [
                ("firebase-fcm", "Firebase Cloud Messaging", 0.25, ["Mobile", "Push"]),
                ("sendgrid-api", "SendGrid Email API", 0.20, ["Email", "API"]),
                ("twilio-sms", "Twilio SMS API", 0.15, ["SMS", "API"]),
            ],
            "email": [
                ("sendgrid-api", "SendGrid Email API", 0.25, ["Email", "API"]),
            ],
            "push": [
                ("firebase-fcm", "Firebase Cloud Messaging", 0.25, ["Mobile", "Push"]),
                ("apple-apns", "Apple Push Notification Service", 0.20, ["iOS", "Push"]),
            ],
        }
        
        for topic in topics:
            if topic in topic_service_map:
                for service_id, name, score, techs in topic_service_map[topic]:
                    matches.append(ExternalServiceMatch(
                        service_id=service_id,
                        name=name,
                        relevance_score=score,
                        discovery_methods=[DiscoveryMethod.TOPIC_MATCH],
                        initial_category=ServiceCategory.DIRECT,
                        topics=[topic],
                        technologies=techs
                    ))
        
        return matches
    
    async def _search_by_technology(self, technologies: List[str]) -> List[ExternalServiceMatch]:
        """Search external service store by technologies (mock implementation)."""
        # Mock implementation - would call external-service-store
        matches = []
        
        tech_service_map = {
            "iOS SDK": [
                ("firebase-fcm", "Firebase Cloud Messaging", 0.20),
                ("apple-apns", "Apple Push Notification Service", 0.25),
            ],
            "Android SDK": [
                ("firebase-fcm", "Firebase Cloud Messaging", 0.20),
            ],
            "Mobile": [
                ("firebase-fcm", "Firebase Cloud Messaging", 0.15),
            ],
        }
        
        for tech in technologies:
            if tech in tech_service_map:
                for service_id, name, score in tech_service_map[tech]:
                    matches.append(ExternalServiceMatch(
                        service_id=service_id,
                        name=name,
                        relevance_score=score,
                        discovery_methods=[DiscoveryMethod.TECHNOLOGY_MATCH],
                        initial_category=ServiceCategory.DIRECT,
                        technologies=[tech]
                    ))
        
        return matches
    
    def _calculate_final_relevance(
        self,
        service: ExternalServiceMatch,
        query: str,
        requirements: Dict[str, Any]
    ) -> float:
        """
        Calculate final relevance score based on all factors.
        
        Scoring factors:
        - Explicitly mentioned: +0.35
        - Topic match: +0.25
        - Technology match: +0.20
        - Team experience: +0.15 (would check historical data)
        - Documentation quality: +0.05 (would check doc store)
        """
        score = service.relevance_score  # Start with base score
        
        # Bonus for multiple discovery methods
        unique_methods = set(service.discovery_methods)
        if len(unique_methods) > 1:
            score += 0.10 * (len(unique_methods) - 1)
        
        # Cap at 1.0
        return min(score, 1.0)

