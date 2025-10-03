"""
Demo Data Persistence Client

Provides functions to save generated documents, prompts, and workflow data to actual stores:
- doc_store: Historical documents (Jira, Confluence, GitHub)
- prompt_store: Prompts used during planning
- memory-agent: Workflow contexts and execution results
"""

import asyncio
import httpx
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib


class DemoPersistenceClient:
    """Client for persisting demo data to actual stores."""
    
    def __init__(
        self,
        doc_store_url: str = "http://localhost:5087",
        prompt_store_url: str = "http://localhost:5110",
        memory_agent_url: str = "http://localhost:5090"
    ):
        self.doc_store_url = doc_store_url
        self.prompt_store_url = prompt_store_url
        self.memory_agent_url = memory_agent_url
        self.stats = {
            "documents_saved": 0,
            "prompts_saved": 0,
            "contexts_saved": 0,
            "errors": []
        }
    
    async def save_document_to_store(
        self,
        content: str,
        metadata: Dict[str, Any],
        doc_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Save a document to doc_store."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "id": doc_id,
                    "content": content,
                    "metadata": metadata
                }
                
                response = await client.post(
                    f"{self.doc_store_url}/api/v1/documents",
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    self.stats["documents_saved"] += 1
                    result = response.json()
                    return result.get("data")
                else:
                    error_msg = f"Failed to save document: {response.status_code} - {response.text}"
                    self.stats["errors"].append(error_msg)
                    print(f"⚠️  {error_msg}")
                    return None
        except Exception as e:
            error_msg = f"Error saving document: {str(e)}"
            self.stats["errors"].append(error_msg)
            print(f"⚠️  {error_msg}")
            return None
    
    async def save_jira_ticket(self, ticket: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save a Jira ticket as a document."""
        content = json.dumps({
            "key": ticket.get("key"),
            "summary": ticket.get("summary"),
            "description": ticket.get("description", ""),
            "status": ticket.get("status"),
            "story_points": ticket.get("story_points"),
            "tech_stack": ticket.get("tech_stack", []),
            "assignee": ticket.get("assignee"),
            "created": ticket.get("created"),
            "resolved": ticket.get("resolved")
        }, indent=2)
        
        metadata = {
            "source": "jira",
            "type": "ticket",
            "doc_type": "jira_ticket",
            "key": ticket.get("key"),
            "status": ticket.get("status"),
            "story_points": ticket.get("story_points"),
            "tech_stack": json.dumps(ticket.get("tech_stack", [])),
            "created_date": ticket.get("created"),
            "category": "historical_data"
        }
        
        return await self.save_document_to_store(content, metadata, doc_id=f"jira_{ticket.get('key')}")
    
    async def save_confluence_doc(self, doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save a Confluence document."""
        content = json.dumps({
            "doc_id": doc.get("doc_id"),
            "title": doc.get("title"),
            "space": doc.get("space"),
            "author": doc.get("author"),
            "sections": doc.get("sections", []),
            "word_count": doc.get("word_count"),
            "created": doc.get("created"),
            "last_updated": doc.get("last_updated"),
            "tags": doc.get("tags", [])
        }, indent=2)
        
        metadata = {
            "source": "confluence",
            "type": "document",
            "doc_type": "confluence_doc",
            "doc_id": doc.get("doc_id"),
            "title": doc.get("title"),
            "space": doc.get("space"),
            "author": doc.get("author"),
            "word_count": doc.get("word_count"),
            "created_date": doc.get("created"),
            "tags": json.dumps(doc.get("tags", [])),
            "category": "historical_data"
        }
        
        return await self.save_document_to_store(content, metadata, doc_id=f"conf_{doc.get('doc_id')}")
    
    async def save_github_pr(self, pr: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Save a GitHub PR as a document."""
        content = json.dumps({
            "pr_number": pr.get("pr_number"),
            "title": pr.get("title"),
            "author": pr.get("author"),
            "description": pr.get("description", ""),
            "status": pr.get("status"),
            "files_changed": pr.get("files_changed"),
            "additions": pr.get("additions"),
            "deletions": pr.get("deletions"),
            "created": pr.get("created"),
            "merged": pr.get("merged"),
            "tech_stack": pr.get("tech_stack", [])
        }, indent=2)
        
        metadata = {
            "source": "github",
            "type": "pull_request",
            "doc_type": "github_pr",
            "pr_number": pr.get("pr_number"),
            "status": pr.get("status"),
            "files_changed": pr.get("files_changed"),
            "tech_stack": json.dumps(pr.get("tech_stack", [])),
            "created_date": pr.get("created"),
            "category": "historical_data"
        }
        
        return await self.save_document_to_store(content, metadata, doc_id=f"github_pr_{pr.get('pr_number')}")
    
    async def save_prompt_to_store(
        self,
        name: str,
        template: str,
        category: str,
        description: str,
        tags: List[str],
        variables: Optional[List[str]] = None,
        model_params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Save a prompt to prompt_store."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "name": name,
                    "content": template,  # Changed from "template" to "content"
                    "category": category,
                    "description": description or "",
                    "tags": tags or [],
                    "variables": variables or [],
                    "is_template": True
                }
                
                response = await client.post(
                    f"{self.prompt_store_url}/api/v1/prompts",
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    self.stats["prompts_saved"] += 1
                    result = response.json()
                    return result.get("data")
                else:
                    error_msg = f"Failed to save prompt '{name}': {response.status_code} - {response.text}"
                    self.stats["errors"].append(error_msg)
                    print(f"⚠️  {error_msg}")
                    return None
        except Exception as e:
            error_msg = f"Error saving prompt '{name}': {str(e)}"
            self.stats["errors"].append(error_msg)
            print(f"⚠️  {error_msg}")
            return None
    
    async def save_workflow_context_to_memory(
        self,
        workflow_id: str,
        workflow_type: str,
        workflow_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        execution_metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Save workflow context to memory-agent."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create memory item in correct format for memory-agent
                # memory-agent expects: id, user_id, memory_type, content, metadata
                # Valid memory_type values: "conversation", "fact", "preference", "context", "session"
                item = {
                    "id": f"workflow:{workflow_type}:{workflow_id}",
                    "user_id": "demo_system",  # Required field
                    "memory_type": "context",  # Required field - using "context" for workflow executions
                    "content": json.dumps({
                        "workflow_id": workflow_id,
                        "workflow_type": workflow_type,
                        "workflow_name": workflow_name,
                        "input_data": input_data,
                        "output_data": output_data,
                        "execution_metadata": execution_metadata,
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    "metadata": {
                        "workflow_type": workflow_type,
                        "workflow_id": workflow_id,
                        "workflow_name": workflow_name,
                        "execution_time": execution_metadata.get("execution_time_seconds", 0),
                        "status": "completed",
                        "ttl": 604800  # 7 days
                    }
                }
                
                payload = {"item": item}
                
                response = await client.post(
                    f"{self.memory_agent_url}/memory/put",
                    json=payload
                )
                
                if response.status_code in [200, 201]:
                    self.stats["contexts_saved"] += 1
                    return response.json()
                else:
                    error_msg = f"Failed to save workflow context: {response.status_code} - {response.text}"
                    self.stats["errors"].append(error_msg)
                    print(f"⚠️  {error_msg}")
                    return None
        except Exception as e:
            error_msg = f"Error saving workflow context: {str(e)}"
            self.stats["errors"].append(error_msg)
            print(f"⚠️  {error_msg}")
            return None
    
    async def bulk_save_historical_data(
        self,
        jira_tickets: List[Dict[str, Any]],
        confluence_docs: List[Dict[str, Any]],
        github_prs: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Bulk save all historical data."""
        print(f"\n📊 Saving Historical Data to Stores...")
        print(f"   • Jira Tickets: {len(jira_tickets)}")
        print(f"   • Confluence Docs: {len(confluence_docs)}")
        print(f"   • GitHub PRs: {len(github_prs)}")
        
        # Save Jira tickets
        for ticket in jira_tickets:
            await self.save_jira_ticket(ticket)
        
        # Save Confluence docs
        for doc in confluence_docs:
            await self.save_confluence_doc(doc)
        
        # Save GitHub PRs
        for pr in github_prs:
            await self.save_github_pr(pr)
        
        print(f"\n✅ Historical Data Saved:")
        print(f"   • Documents in doc_store: {self.stats['documents_saved']}")
        if self.stats["errors"]:
            print(f"   • Errors: {len(self.stats['errors'])}")
        
        return {
            "documents_saved": self.stats["documents_saved"],
            "errors": len(self.stats["errors"])
        }
    
    async def save_all_workflow_prompts(self) -> Dict[str, int]:
        """Save all prompts used in workflows."""
        print(f"\n📝 Saving Workflow Prompts to Prompt Store...")
        
        prompts = [
            {
                "name": "feature_decomposition_prompt",
                "template": """Analyze the following feature request and break it down into user stories and technical tasks.

Feature Request: {feature_query}
Tech Stack: {tech_stack}
Team Size: {team_size}

Provide a detailed breakdown with story points, complexity assessment, and risk factors.""",
                "category": "planning",
                "description": "Decomposes features into user stories and tasks",
                "tags": ["workflow_a", "decomposition", "planning"],
                "variables": ["feature_query", "tech_stack", "team_size"]
            },
            {
                "name": "historical_context_analysis_prompt",
                "template": """Analyze historical project data to provide context for planning.

Historical Tickets: {num_tickets}
Tech Stack: {tech_stack}
Time Period: {time_period}

Identify patterns, velocity trends, and relevant historical insights.""",
                "category": "analysis",
                "description": "Extracts insights from historical data",
                "tags": ["workflow_b", "historical", "analysis"],
                "variables": ["num_tickets", "tech_stack", "time_period"]
            },
            {
                "name": "timeline_estimation_prompt",
                "template": """Estimate project timeline based on story points and team velocity.

Total Story Points: {story_points}
Team Velocity: {velocity}
Team Size: {team_size}
Buffer Factor: {buffer_factor}

Provide timeline estimate with confidence intervals.""",
                "category": "estimation",
                "description": "Estimates project timelines",
                "tags": ["workflow_c", "timeline", "estimation"],
                "variables": ["story_points", "velocity", "team_size", "buffer_factor"]
            },
            {
                "name": "team_skills_matching_prompt",
                "template": """Match team member skills to required tasks.

Required Skills: {required_skills}
Team Members: {team_members}
Task Complexity: {complexity}

Recommend optimal task assignments.""",
                "category": "resource_allocation",
                "description": "Matches skills to tasks",
                "tags": ["workflow_d", "skills", "allocation"],
                "variables": ["required_skills", "team_members", "complexity"]
            },
            {
                "name": "external_service_discovery_prompt",
                "template": """Discover external services relevant to the feature.

Feature Query: {feature_query}
Tech Stack: {tech_stack}
Integration Points: {integration_points}

Identify services, APIs, and dependencies.""",
                "category": "discovery",
                "description": "Discovers external services",
                "tags": ["workflow_e", "discovery", "external_services"],
                "variables": ["feature_query", "tech_stack", "integration_points"]
            },
            {
                "name": "compliance_validation_prompt",
                "template": """Validate compliance with external service contracts.

Service: {service_name}
API Version: {api_version}
Security Requirements: {security_reqs}

Identify compliance issues and remediation steps.""",
                "category": "validation",
                "description": "Validates service compliance",
                "tags": ["workflow_e", "compliance", "validation"],
                "variables": ["service_name", "api_version", "security_reqs"]
            },
            {
                "name": "knowledge_gap_detection_prompt",
                "template": """Detect knowledge gaps in team and documentation.

Required Skills: {required_skills}
Team Expertise: {team_expertise}
Available Documentation: {documentation}

Identify gaps and remediation actions.""",
                "category": "analysis",
                "description": "Detects knowledge gaps",
                "tags": ["workflow_e", "knowledge", "gap_analysis"],
                "variables": ["required_skills", "team_expertise", "documentation"]
            },
            {
                "name": "blindspot_detection_prompt",
                "template": """Detect development blindspots and hidden risks.

Feature Scope: {feature_scope}
Dependencies: {dependencies}
Historical Issues: {historical_issues}

Identify potential blindspots and mitigation strategies.""",
                "category": "risk_analysis",
                "description": "Detects development blindspots",
                "tags": ["workflow_e", "blindspot", "risk"],
                "variables": ["feature_scope", "dependencies", "historical_issues"]
            }
        ]
        
        for prompt_data in prompts:
            await self.save_prompt_to_store(**prompt_data)
        
        print(f"\n✅ Prompts Saved:")
        print(f"   • Prompts in prompt_store: {self.stats['prompts_saved']}")
        if self.stats["errors"]:
            print(f"   • Errors: {len(self.stats['errors'])}")
        
        return {
            "prompts_saved": self.stats["prompts_saved"],
            "errors": len(self.stats["errors"])
        }
    
    async def save_workflow_execution(
        self,
        workflow_type: str,
        workflow_name: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        execution_time: float
    ) -> Optional[Dict[str, Any]]:
        """Save a workflow execution to memory-agent."""
        workflow_id = f"{workflow_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        execution_metadata = {
            "execution_time_seconds": execution_time,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "completed"
        }
        
        return await self.save_workflow_context_to_memory(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            workflow_name=workflow_name,
            input_data=input_data,
            output_data=output_data,
            execution_metadata=execution_metadata
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get persistence statistics."""
        return self.stats
    
    async def verify_stores_accessible(self) -> Dict[str, bool]:
        """Verify that all stores are accessible."""
        results = {
            "doc_store": False,
            "prompt_store": False,
            "memory_agent": False
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check doc_store
            try:
                response = await client.get(f"{self.doc_store_url}/health")
                results["doc_store"] = response.status_code == 200
            except:
                pass
            
            # Check prompt_store
            try:
                response = await client.get(f"{self.prompt_store_url}/health")
                results["prompt_store"] = response.status_code == 200
            except:
                pass
            
            # Check memory_agent
            try:
                response = await client.get(f"{self.memory_agent_url}/health")
                results["memory_agent"] = response.status_code == 200
            except:
                pass
        
        return results


# Convenience functions for standalone use
async def save_demo_data_to_stores(
    jira_tickets: List[Dict[str, Any]],
    confluence_docs: List[Dict[str, Any]],
    github_prs: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Save all demo data to stores.
    Returns statistics about what was saved.
    """
    client = DemoPersistenceClient()
    
    # Verify stores are accessible
    accessible = await client.verify_stores_accessible()
    print(f"\n🔍 Store Accessibility:")
    print(f"   • doc_store: {'✅' if accessible['doc_store'] else '❌'}")
    print(f"   • prompt_store: {'✅' if accessible['prompt_store'] else '❌'}")
    print(f"   • memory_agent: {'✅' if accessible['memory_agent'] else '❌'}")
    
    if not accessible["doc_store"]:
        print(f"\n⚠️  doc_store not accessible. Historical data will not be saved.")
        print(f"   Start doc_store: cd services/doc_store && python main.py")
    
    if not accessible["prompt_store"]:
        print(f"\n⚠️  prompt_store not accessible. Prompts will not be saved.")
        print(f"   Start prompt_store: cd services/prompt_store && python main.py")
    
    if not accessible["memory_agent"]:
        print(f"\n⚠️  memory_agent not accessible. Workflow contexts will not be saved.")
        print(f"   Start memory_agent: cd services/memory-agent && python main.py")
    
    # Save data even if some stores are down
    historical_stats = await client.bulk_save_historical_data(
        jira_tickets, confluence_docs, github_prs
    )
    
    prompt_stats = await client.save_all_workflow_prompts()
    
    return {
        "store_accessibility": accessible,
        "historical_data": historical_stats,
        "prompts": prompt_stats,
        "total_saved": client.stats["documents_saved"] + client.stats["prompts_saved"],
        "errors": client.stats["errors"]
    }


if __name__ == "__main__":
    # Test the client
    async def test():
        client = DemoPersistenceClient()
        accessible = await client.verify_stores_accessible()
        print(f"Store accessibility: {accessible}")
    
    asyncio.run(test())

