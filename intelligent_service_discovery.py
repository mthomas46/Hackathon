"""
Intelligent Service Discovery Engine

Analyzes historical documents (Jira, Confluence, GitHub) to:
1. Extract service mentions and references
2. Store discovered services in external-service-store
3. Create linkings between documents and services
"""

import re
import asyncio
import httpx
from typing import Dict, List, Any, Set, Optional
from datetime import datetime
import json


class IntelligentServiceDiscovery:
    """
    Discovers services from historical documents and creates intelligent linkings.
    """
    
    def __init__(
        self,
        external_service_store_url: str = "http://localhost:5140",
        doc_store_url: str = "http://localhost:5087"
    ):
        self.external_service_store_url = external_service_store_url
        self.doc_store_url = doc_store_url
        self.discovered_services = []
        self.document_service_links = []
        self.stats = {
            "services_discovered": 0,
            "services_stored": 0,
            "links_created": 0,
            "documents_analyzed": 0,
            "errors": []
        }
        
        # Patterns for service detection
        self.service_patterns = [
            # API/Service names
            r'(?:using|with|via|through|implements?|integrates?)\s+([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)?)\s+(?:API|api|service|Service)',
            # Framework/Library mentions
            r'(?:using|with|via)\s+([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)?)\s+(?:framework|Framework|library|Library)',
            # Database mentions
            r'(?:using|with|stored in|persisted to|database)\s+([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)?)\s+(?:database|Database|DB)',
            # Tech stack mentions
            r'(?:tech stack|stack|technologies?):\s*([A-Za-z0-9,\s&]+)',
            # Common service patterns
            r'\b(PostgreSQL|MySQL|MongoDB|Redis|Kafka|RabbitMQ|Elasticsearch|Nginx|Docker|Kubernetes)\b',
            r'\b(HTTP4s|Circe|Doobie|Tapir|ScalaTest|SBT|Flyway)\b',
            r'\b(React|Angular|Vue|Elm|TypeScript|JavaScript)\b',
            r'\b(Scala|Java|Python|Go|Rust|Kotlin)\b',
        ]
    
    def extract_services_from_text(self, text: str, source_type: str) -> List[Dict[str, Any]]:
        """Extract service mentions from text."""
        discovered = []
        seen_services = set()
        
        for pattern in self.service_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                service_name = match.group(1).strip() if match.groups() else match.group(0).strip()
                
                # Clean up service name
                if ',' in service_name:
                    # Split tech stack lists
                    for item in service_name.split(','):
                        item = item.strip().strip('&').strip()
                        if item and item not in seen_services and len(item) > 2:
                            seen_services.add(item)
                            discovered.append({
                                "name": item,
                                "source_type": source_type,
                                "confidence": 0.8
                            })
                elif service_name and service_name not in seen_services and len(service_name) > 2:
                    seen_services.add(service_name)
                    discovered.append({
                        "name": service_name,
                        "source_type": source_type,
                        "confidence": 0.9
                    })
        
        return discovered
    
    def extract_from_jira_ticket(self, ticket: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract services from Jira ticket."""
        services = []
        
        # Analyze summary
        if ticket.get("summary"):
            services.extend(self.extract_services_from_text(ticket["summary"], "jira"))
        
        # Analyze description
        if ticket.get("description"):
            services.extend(self.extract_services_from_text(ticket["description"], "jira"))
        
        # Use tech_stack if provided
        if ticket.get("tech_stack"):
            for tech in ticket["tech_stack"]:
                services.append({
                    "name": tech,
                    "source_type": "jira",
                    "confidence": 1.0  # High confidence from explicit tech stack
                })
        
        # Add document reference
        for service in services:
            service["source_document"] = {
                "type": "jira_ticket",
                "key": ticket.get("key"),
                "summary": ticket.get("summary", "")[:100]
            }
        
        return services
    
    def extract_from_confluence_doc(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract services from Confluence document."""
        services = []
        
        # Analyze title
        if doc.get("title"):
            services.extend(self.extract_services_from_text(doc["title"], "confluence"))
        
        # Analyze sections
        if doc.get("sections"):
            for section in doc["sections"]:
                # Section names often contain service/tech names
                services.extend(self.extract_services_from_text(section, "confluence"))
        
        # Use tags if provided
        if doc.get("tags"):
            for tag in doc["tags"]:
                services.append({
                    "name": tag,
                    "source_type": "confluence",
                    "confidence": 0.9
                })
        
        # Add document reference
        for service in services:
            service["source_document"] = {
                "type": "confluence_doc",
                "doc_id": doc.get("doc_id"),
                "title": doc.get("title", "")[:100]
            }
        
        return services
    
    def extract_from_github_pr(self, pr: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract services from GitHub PR."""
        services = []
        
        # Analyze title
        if pr.get("title"):
            services.extend(self.extract_services_from_text(pr["title"], "github"))
        
        # Analyze description
        if pr.get("description"):
            services.extend(self.extract_services_from_text(pr["description"], "github"))
        
        # Use tech_stack if provided
        if pr.get("tech_stack"):
            for tech in pr["tech_stack"]:
                services.append({
                    "name": tech,
                    "source_type": "github",
                    "confidence": 1.0
                })
        
        # Add document reference
        for service in services:
            service["source_document"] = {
                "type": "github_pr",
                "pr_number": pr.get("pr_number"),
                "title": pr.get("title", "")[:100]
            }
        
        return services
    
    def extract_from_tangential_doc(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract services from tangential service document."""
        services = []
        
        # Use service_name (guaranteed to be there)
        if doc.get("service_name"):
            services.append({
                "name": doc["service_name"],
                "source_type": "tangential",
                "confidence": 1.0  # High confidence - it's explicitly about this service
            })
        
        # Use tech_stack
        if doc.get("tech_stack"):
            for tech in doc["tech_stack"]:
                if tech != doc.get("service_name"):  # Avoid duplicate
                    services.append({
                        "name": tech,
                        "source_type": "tangential",
                        "confidence": 0.95
                    })
        
        # Add related services
        if doc.get("related_services"):
            for related in doc["related_services"]:
                services.append({
                    "name": related,
                    "source_type": "tangential",
                    "confidence": 0.7  # Lower confidence for related services
                })
        
        # Add document reference
        for service in services:
            service["source_document"] = {
                "type": "tangential_doc",
                "doc_id": doc.get("doc_id"),
                "title": doc.get("title", "")[:100],
                "service_type": doc.get("service_type")
            }
        
        return services
    
    def analyze_historical_documents(
        self,
        jira_tickets: List[Dict[str, Any]],
        confluence_docs: List[Dict[str, Any]],
        github_prs: List[Dict[str, Any]],
        tangential_docs: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze all historical documents and extract services.
        Returns aggregated service data with source linkings.
        """
        print(f"\n🔍 ANALYZING HISTORICAL DOCUMENTS FOR SERVICES...")
        print("="*80)
        
        all_services = []
        tangential_docs = tangential_docs or []
        
        # Extract from Jira
        print(f"   Analyzing {len(jira_tickets)} Jira tickets...")
        for ticket in jira_tickets:
            services = self.extract_from_jira_ticket(ticket)
            all_services.extend(services)
            self.stats["documents_analyzed"] += 1
        
        # Extract from Confluence
        print(f"   Analyzing {len(confluence_docs)} Confluence docs...")
        for doc in confluence_docs:
            services = self.extract_from_confluence_doc(doc)
            all_services.extend(services)
            self.stats["documents_analyzed"] += 1
        
        # Extract from GitHub
        print(f"   Analyzing {len(github_prs)} GitHub PRs...")
        for pr in github_prs:
            services = self.extract_from_github_pr(pr)
            all_services.extend(services)
            self.stats["documents_analyzed"] += 1
        
        # Extract from Tangential
        if tangential_docs:
            print(f"   Analyzing {len(tangential_docs)} tangential service docs...")
            for doc in tangential_docs:
                services = self.extract_from_tangential_doc(doc)
                all_services.extend(services)
                self.stats["documents_analyzed"] += 1
        
        # Aggregate services (combine duplicates)
        service_map = {}
        for service in all_services:
            name = service["name"]
            if name in service_map:
                # Merge with existing
                service_map[name]["sources"].append(service["source_document"])
                service_map[name]["confidence"] = max(service_map[name]["confidence"], service["confidence"])
                service_map[name]["mention_count"] += 1
            else:
                # New service
                service_map[name] = {
                    "name": name,
                    "sources": [service["source_document"]],
                    "source_types": [service["source_type"]],
                    "confidence": service["confidence"],
                    "mention_count": 1
                }
        
        self.discovered_services = list(service_map.values())
        self.stats["services_discovered"] = len(self.discovered_services)
        
        print(f"\n✅ Services Discovered: {len(self.discovered_services)}")
        print(f"   Top Services:")
        sorted_services = sorted(self.discovered_services, key=lambda x: x["mention_count"], reverse=True)
        for service in sorted_services[:10]:
            print(f"   • {service['name']}: {service['mention_count']} mentions, confidence {service['confidence']:.2f}")
        
        return {
            "total_discovered": len(self.discovered_services),
            "services": self.discovered_services,
            "stats": self.stats
        }
    
    async def store_services_in_external_store(self) -> Dict[str, Any]:
        """Store discovered services in external-service-store."""
        print(f"\n💾 STORING SERVICES IN EXTERNAL-SERVICE-STORE...")
        print("="*80)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for service_data in self.discovered_services:
                try:
                    # Determine service type based on name/context
                    service_type = self._determine_service_type(service_data["name"])
                    
                    # Create service payload
                    payload = {
                        "name": service_data["name"].lower().replace(" ", "-"),
                        "display_name": service_data["name"],
                        "service_type": service_type,
                        "description": f"Discovered from {len(service_data['sources'])} historical documents",
                        "version": "1.0.0",  # Fixed: use semantic version instead of "latest"
                        "technologies": [service_data["name"]],
                        "tags": list(set(service_data["source_types"])),
                        "run_requirements": {},  # Added: required field
                        "metadata": {
                            "discovery_method": "intelligent_document_analysis",
                            "confidence": service_data["confidence"],
                            "mention_count": service_data["mention_count"],
                            "source_documents": service_data["sources"],
                            "discovered_at": datetime.utcnow().isoformat()
                        }
                    }
                    
                    # Try to store
                    response = await client.post(
                        f"{self.external_service_store_url}/services",
                        json=payload
                    )
                    
                    if response.status_code in [200, 201]:
                        self.stats["services_stored"] += 1
                        result = response.json()
                        service_data["stored_id"] = result.get("id") or result.get("data", {}).get("id")
                        print(f"   ✅ Stored: {service_data['name']}")
                    else:
                        error_msg = f"Failed to store {service_data['name']}: {response.status_code}"
                        self.stats["errors"].append(error_msg)
                        print(f"   ⚠️  {error_msg}")
                
                except Exception as e:
                    error_msg = f"Error storing {service_data['name']}: {str(e)}"
                    self.stats["errors"].append(error_msg)
                    print(f"   ⚠️  {error_msg}")
        
        print(f"\n✅ Services Stored: {self.stats['services_stored']}/{self.stats['services_discovered']}")
        return {
            "stored": self.stats["services_stored"],
            "total": self.stats["services_discovered"],
            "errors": len(self.stats["errors"])
        }
    
    async def create_document_service_linkings(self, doc_to_service_map: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Create linkings between documents in doc_store and services in external-service-store.
        """
        print(f"\n🔗 CREATING DOCUMENT-SERVICE LINKINGS...")
        print("="*80)
        
        # This would involve updating document metadata with service references
        # and potentially creating a separate linking table
        
        for service in self.discovered_services:
            for source_doc in service["sources"]:
                link = {
                    "service_id": service.get("stored_id"),
                    "service_name": service["name"],
                    "document_type": source_doc["type"],
                    "document_id": source_doc.get("key") or source_doc.get("doc_id") or source_doc.get("pr_number"),
                    "relationship": "mentions",
                    "confidence": service["confidence"]
                }
                self.document_service_links.append(link)
                self.stats["links_created"] += 1
        
        print(f"✅ Links Created: {self.stats['links_created']}")
        print(f"   Linking {self.stats['documents_analyzed']} documents to {self.stats['services_discovered']} services")
        
        return {
            "links_created": self.stats["links_created"],
            "document_service_links": self.document_service_links
        }
    
    def _determine_service_type(self, name: str) -> str:
        """Determine service type based on name."""
        name_lower = name.lower()
        
        if any(db in name_lower for db in ["postgres", "mysql", "mongo", "redis", "database"]):
            return "DATABASE"
        elif any(fw in name_lower for fw in ["http4s", "react", "angular", "vue", "elm", "express"]):
            return "FRAMEWORK"
        elif any(lib in name_lower for lib in ["circe", "doobie", "tapir", "library"]):
            return "LIBRARY"
        elif any(tool in name_lower for tool in ["docker", "kubernetes", "nginx", "kafka", "sbt"]):
            return "TOOL"
        elif any(lang in name_lower for lang in ["scala", "java", "python", "go", "rust", "javascript", "typescript"]):
            return "LANGUAGE"
        else:
            return "API"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get discovery and storage statistics."""
        return self.stats
    
    def get_discovered_services(self) -> List[Dict[str, Any]]:
        """Get list of discovered services."""
        return self.discovered_services
    
    def get_document_service_links(self) -> List[Dict[str, Any]]:
        """Get document-service linkings."""
        return self.document_service_links


# Convenience function
async def discover_and_store_services(
    jira_tickets: List[Dict[str, Any]],
    confluence_docs: List[Dict[str, Any]],
    github_prs: List[Dict[str, Any]],
    tangential_docs: List[Dict[str, Any]] = None,
    external_service_store_url: str = "http://localhost:5140"
) -> Dict[str, Any]:
    """
    Complete pipeline: discover services from documents and store them.
    """
    discovery = IntelligentServiceDiscovery(external_service_store_url=external_service_store_url)
    
    # Analyze documents (including tangential docs if provided)
    analysis_result = discovery.analyze_historical_documents(
        jira_tickets, confluence_docs, github_prs, tangential_docs or []
    )
    
    # Store services
    storage_result = await discovery.store_services_in_external_store()
    
    # Create linkings
    linking_result = await discovery.create_document_service_linkings({})
    
    return {
        "analysis": analysis_result,
        "storage": storage_result,
        "linking": linking_result,
        "discovered_services": discovery.get_discovered_services(),
        "document_service_links": discovery.get_document_service_links(),
        "stats": discovery.get_stats()
    }


if __name__ == "__main__":
    # Test the discovery engine
    async def test():
        sample_jira = [{
            "key": "PROJ-123",
            "summary": "Implement Scala HTTP4s API with Circe JSON",
            "description": "Build REST API using HTTP4s framework with Circe for JSON serialization",
            "tech_stack": ["Scala", "HTTP4s", "Circe"]
        }]
        
        sample_confluence = [{
            "doc_id": "CONF-001",
            "title": "PostgreSQL Database Architecture",
            "sections": ["Setup", "Migrations with Flyway", "Connection Pooling"],
            "tags": ["PostgreSQL", "Database", "Architecture"]
        }]
        
        sample_github = [{
            "pr_number": 42,
            "title": "Add Docker containerization",
            "description": "Containerize app using Docker and docker-compose",
            "tech_stack": ["Docker"]
        }]
        
        result = await discover_and_store_services(sample_jira, sample_confluence, sample_github)
        print(f"\n\nDiscovered {result['analysis']['total_discovered']} services!")
        print(f"Stored {result['storage']['stored']} services")
        print(f"Created {result['linking']['links_created']} linkings")
    
    asyncio.run(test())

