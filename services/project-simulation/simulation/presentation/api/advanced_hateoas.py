"""Advanced HATEOAS Navigation - Comprehensive REST API Hypermedia.

This module implements advanced HATEOAS (Hypermedia as the Engine of Application State)
navigation patterns for the Project Simulation Service, providing comprehensive
hypermedia controls for API exploration and state transitions.

Features:
- Dynamic link generation based on resource state
- Conditional links based on user permissions and resource state
- Embedded resources for reduced API calls
- Link templates for parameterized navigation
- Comprehensive relation types for semantic navigation
- State-aware navigation controls
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set
from datetime import datetime
from enum import Enum
import json

# Import from shared infrastructure
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "services" / "shared"))

from simulation.infrastructure.logging import get_simulation_logger


class LinkRelation(Enum):
    """Standard IANA link relations with custom extensions."""
    # Standard IANA relations
    SELF = "self"
    NEXT = "next"
    PREVIOUS = "prev"
    FIRST = "first"
    LAST = "last"
    COLLECTION = "collection"
    ITEM = "item"
    EDIT = "edit"
    DELETE = "delete"

    # Custom relations for project simulation
    SIMULATE = "simulate"
    EXECUTE = "execute"
    CANCEL = "cancel"
    RESULTS = "results"
    STATUS = "status"
    PROGRESS = "progress"
    ANALYTICS = "analytics"
    REPORTS = "reports"
    METRICS = "metrics"
    HEALTH = "health"
    CONFIGURE = "configure"
    VALIDATE = "validate"
    EXPORT = "export"
    IMPORT = "import"


class LinkTemplate:
    """Template for generating parameterized links."""

    def __init__(self,
                 relation: LinkRelation,
                 template: str,
                 parameters: Dict[str, Any] = None,
                 conditions: List[str] = None):
        """Initialize link template."""
        self.relation = relation
        self.template = template
        self.parameters = parameters or {}
        self.conditions = conditions or []

    def generate_link(self, **kwargs) -> Dict[str, Any]:
        """Generate link from template with parameters."""
        try:
            url = self.template.format(**kwargs)
            return {
                "rel": self.relation.value,
                "href": url,
                "templated": True,
                "parameters": self.parameters
            }
        except KeyError as e:
            raise ValueError(f"Missing parameter for link template: {e}")

    def check_conditions(self, context: Dict[str, Any]) -> bool:
        """Check if link conditions are met."""
        for condition in self.conditions:
            if not self._evaluate_condition(condition, context):
                return False
        return True

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition against context."""
        # Simple condition evaluation (can be extended)
        if "==" in condition:
            key, value = condition.split("==")
            key = key.strip()
            value = value.strip().strip("'\"")
            return context.get(key) == value
        elif "!=" in condition:
            key, value = condition.split("!=")
            key = key.strip()
            value = value.strip().strip("'\"")
            return context.get(key) != value
        return True


class HypermediaResource:
    """Base class for hypermedia-enabled resources."""

    def __init__(self, resource_id: str = None):
        """Initialize hypermedia resource."""
        self.resource_id = resource_id
        self.links: List[Dict[str, Any]] = []
        self.embedded: Dict[str, Any] = {}
        self.actions: List[Dict[str, Any]] = []

    def add_link(self,
                 relation: LinkRelation,
                 href: str,
                 method: str = "GET",
                 title: Optional[str] = None,
                 templated: bool = False):
        """Add a link to the resource."""
        link = {
            "rel": relation.value,
            "href": href,
            "method": method,
            "templated": templated
        }

        if title:
            link["title"] = title

        self.links.append(link)

    def add_embedded(self, relation: str, resource: Any):
        """Add an embedded resource."""
        self.embedded[relation] = resource

    def add_action(self,
                   name: str,
                   href: str,
                   method: str = "POST",
                   fields: List[Dict[str, Any]] = None,
                   title: Optional[str] = None):
        """Add an action to the resource."""
        action = {
            "name": name,
            "href": href,
            "method": method,
            "fields": fields or []
        }

        if title:
            action["title"] = title

        self.actions.append(action)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to hypermedia dictionary representation."""
        result = {
            "links": self.links,
            "_embedded": self.embedded,
            "_actions": self.actions
        }

        if self.resource_id:
            result["id"] = self.resource_id

        return result


class SimulationResource(HypermediaResource):
    """Hypermedia resource for simulations."""

    @staticmethod
    def create_simulation_links(simulation_id: str,
                               status: str = "pending",
                               user_permissions: List[str] = None) -> List[Dict[str, Any]]:
        """Create comprehensive links for a simulation resource."""
        links = []

        # Self link
        links.append({
            "rel": LinkRelation.SELF.value,
            "href": f"/api/v1/simulations/{simulation_id}",
            "method": "GET",
            "title": "Simulation details"
        })

        # Status-specific links
        if status in ["pending", "created"]:
            links.append({
                "rel": LinkRelation.EXECUTE.value,
                "href": f"/api/v1/simulations/{simulation_id}/execute",
                "method": "POST",
                "title": "Execute simulation"
            })

        if status in ["running", "executing"]:
            links.append({
                "rel": LinkRelation.STATUS.value,
                "href": f"/api/v1/simulations/{simulation_id}",
                "method": "GET",
                "title": "Check execution status"
            })
            links.append({
                "rel": LinkRelation.PROGRESS.value,
                "href": f"/api/v1/simulations/{simulation_id}/progress",
                "method": "GET",
                "title": "View execution progress"
            })

        if status in ["completed", "finished"]:
            links.append({
                "rel": LinkRelation.RESULTS.value,
                "href": f"/api/v1/simulations/{simulation_id}/results",
                "method": "GET",
                "title": "View simulation results"
            })
            links.append({
                "rel": LinkRelation.ANALYTICS.value,
                "href": f"/api/v1/simulations/{simulation_id}/analytics",
                "method": "GET",
                "title": "View analytics and insights"
            })
            links.append({
                "rel": LinkRelation.REPORTS.value,
                "href": f"/api/v1/simulations/{simulation_id}/reports",
                "method": "GET",
                "title": "Generate reports"
            })

        # Always available links
        links.append({
            "rel": LinkRelation.EDIT.value,
            "href": f"/api/v1/simulations/{simulation_id}",
            "method": "PUT",
            "title": "Update simulation"
        })

        if status not in ["running", "executing"]:
            links.append({
                "rel": LinkRelation.DELETE.value,
                "href": f"/api/v1/simulations/{simulation_id}",
                "method": "DELETE",
                "title": "Delete simulation"
            })

        if status in ["pending", "created", "paused"]:
            links.append({
                "rel": LinkRelation.CANCEL.value,
                "href": f"/api/v1/simulations/{simulation_id}",
                "method": "DELETE",
                "title": "Cancel simulation"
            })

        return links

    @staticmethod
    def create_simulation_collection_links(page: int = 1,
                                         page_size: int = 20,
                                         total_pages: int = 1) -> List[Dict[str, Any]]:
        """Create links for simulation collection."""
        links = []

        # Self link
        links.append({
            "rel": LinkRelation.SELF.value,
            "href": f"/api/v1/simulations?page={page}&page_size={page_size}",
            "method": "GET",
            "title": "Current page"
        })

        # Pagination links
        if page > 1:
            links.append({
                "rel": LinkRelation.PREVIOUS.value,
                "href": f"/api/v1/simulations?page={page-1}&page_size={page_size}",
                "method": "GET",
                "title": "Previous page"
            })
            links.append({
                "rel": LinkRelation.FIRST.value,
                "href": f"/api/v1/simulations?page=1&page_size={page_size}",
                "method": "GET",
                "title": "First page"
            })

        if page < total_pages:
            links.append({
                "rel": LinkRelation.NEXT.value,
                "href": f"/api/v1/simulations?page={page+1}&page_size={page_size}",
                "method": "GET",
                "title": "Next page"
            })
            links.append({
                "rel": LinkRelation.LAST.value,
                "href": f"/api/v1/simulations?page={total_pages}&page_size={page_size}",
                "method": "GET",
                "title": "Last page"
            })

        # Collection-level actions
        links.append({
            "rel": "create-form",
            "href": "/api/v1/simulations",
            "method": "POST",
            "title": "Create new simulation"
        })

        return links


class AnalyticsResource(HypermediaResource):
    """Hypermedia resource for analytics and insights."""

    @staticmethod
    def create_analytics_links(simulation_id: str,
                              available_analyses: List[str] = None) -> List[Dict[str, Any]]:
        """Create links for analytics resources."""
        links = []
        available_analyses = available_analyses or ["quality", "performance", "risk", "benefits"]

        # Base analytics link
        links.append({
            "rel": LinkRelation.SELF.value,
            "href": f"/api/v1/simulations/{simulation_id}/analytics",
            "method": "GET",
            "title": "Analytics overview"
        })

        # Specific analysis types
        analysis_types = {
            "quality": "Document and code quality analysis",
            "performance": "Performance metrics and trends",
            "risk": "Risk assessment and mitigation",
            "benefits": "ROI and benefit calculations"
        }

        for analysis_type, description in analysis_types.items():
            if analysis_type in available_analyses:
                links.append({
                    "rel": f"analysis:{analysis_type}",
                    "href": f"/api/v1/simulations/{simulation_id}/analytics/{analysis_type}",
                    "method": "GET",
                    "title": description
                })

        # Workflow execution links
        links.append({
            "rel": "execute-workflow",
            "href": f"/api/v1/simulations/{simulation_id}/analytics/workflows",
            "method": "POST",
            "title": "Execute analysis workflow"
        })

        return links

    @staticmethod
    def create_workflow_links(workflow_id: str, status: str = "pending") -> List[Dict[str, Any]]:
        """Create links for workflow resources."""
        links = []

        links.append({
            "rel": LinkRelation.SELF.value,
            "href": f"/api/v1/analytics/workflows/{workflow_id}",
            "method": "GET",
            "title": "Workflow status"
        })

        if status in ["pending", "running"]:
            links.append({
                "rel": LinkRelation.CANCEL.value,
                "href": f"/api/v1/analytics/workflows/{workflow_id}/cancel",
                "method": "POST",
                "title": "Cancel workflow"
            })

        if status == "completed":
            links.append({
                "rel": LinkRelation.RESULTS.value,
                "href": f"/api/v1/analytics/workflows/{workflow_id}/results",
                "method": "GET",
                "title": "Workflow results"
            })

        return links


class ReportResource(HypermediaResource):
    """Hypermedia resource for reports."""

    @staticmethod
    def create_report_links(simulation_id: str,
                           report_types: List[str] = None) -> List[Dict[str, Any]]:
        """Create links for report resources."""
        links = []
        report_types = report_types or ["summary", "detailed", "executive", "technical"]

        # Base reports link
        links.append({
            "rel": LinkRelation.SELF.value,
            "href": f"/api/v1/simulations/{simulation_id}/reports",
            "method": "GET",
            "title": "Available reports"
        })

        # Specific report types
        for report_type in report_types:
            links.append({
                "rel": f"report:{report_type}",
                "href": f"/api/v1/simulations/{simulation_id}/reports/{report_type}",
                "method": "GET",
                "title": f"Generate {report_type} report"
            })

        # Report generation
        links.append({
            "rel": "generate-report",
            "href": f"/api/v1/simulations/{simulation_id}/reports/generate",
            "method": "POST",
            "title": "Generate custom report"
        })

        return links


class AdvancedHATEOASManager:
    """Advanced HATEOAS manager for comprehensive API navigation."""

    def __init__(self):
        """Initialize HATEOAS manager."""
        self.logger = get_simulation_logger()
        self.templates: Dict[str, LinkTemplate] = {}
        self.resource_factories: Dict[str, callable] = {}

        # Register resource factories
        self._register_resource_factories()

        # Load link templates
        self._load_link_templates()

    def _register_resource_factories(self):
        """Register resource factories."""
        self.resource_factories = {
            "simulation": SimulationResource,
            "analytics": AnalyticsResource,
            "reports": ReportResource
        }

    def _load_link_templates(self):
        """Load predefined link templates."""
        # Simulation templates
        self.templates["simulation_detail"] = LinkTemplate(
            relation=LinkRelation.SELF,
            template="/api/v1/simulations/{simulation_id}",
            parameters={"simulation_id": "string"},
            conditions=["status != 'deleted'"]
        )

        self.templates["simulation_execute"] = LinkTemplate(
            relation=LinkRelation.EXECUTE,
            template="/api/v1/simulations/{simulation_id}/execute",
            parameters={"simulation_id": "string"},
            conditions=["status in ['pending', 'created', 'paused']"]
        )

        # Analytics templates
        self.templates["analytics_workflow"] = LinkTemplate(
            relation=LinkRelation.ANALYTICS,
            template="/api/v1/simulations/{simulation_id}/analytics/workflows/{workflow_type}",
            parameters={"simulation_id": "string", "workflow_type": "string"},
            conditions=["status == 'completed'"]
        )

    def create_resource_response(self,
                               resource_type: str,
                               resource_id: Optional[str] = None,
                               data: Any = None,
                               context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a comprehensive hypermedia response for a resource."""
        context = context or {}

        # Get appropriate resource factory
        resource_factory = self.resource_factories.get(resource_type)
        if not resource_factory:
            raise ValueError(f"Unknown resource type: {resource_type}")

        # Create resource instance
        resource = resource_factory(resource_id)

        # Generate context-aware links
        links = self._generate_context_aware_links(resource_type, resource_id, context)

        # Add links to resource
        for link in links:
            resource.add_link(
                relation=LinkRelation(link["rel"]),
                href=link["href"],
                method=link.get("method", "GET"),
                title=link.get("title")
            )

        # Generate actions based on context
        actions = self._generate_context_aware_actions(resource_type, resource_id, context)
        for action in actions:
            resource.add_action(**action)

        # Create response
        response = {
            "data": data,
            "_links": resource.links,
            "_embedded": resource.embedded,
            "_actions": resource.actions
        }

        return response

    def _generate_context_aware_links(self,
                                    resource_type: str,
                                    resource_id: str,
                                    context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate links based on resource type and context."""
        links = []

        if resource_type == "simulation":
            status = context.get("status", "pending")
            links.extend(SimulationResource.create_simulation_links(resource_id, status))

        elif resource_type == "analytics":
            simulation_id = context.get("simulation_id", resource_id)
            available_analyses = context.get("available_analyses", [])
            links.extend(AnalyticsResource.create_analytics_links(simulation_id, available_analyses))

        elif resource_type == "reports":
            simulation_id = context.get("simulation_id", resource_id)
            report_types = context.get("report_types", [])
            links.extend(ReportResource.create_report_links(simulation_id, report_types))

        # Add common navigation links
        links.extend(self._generate_common_links(resource_type, resource_id, context))

        return links

    def _generate_context_aware_actions(self,
                                      resource_type: str,
                                      resource_id: str,
                                      context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate actions based on resource type and context."""
        actions = []

        if resource_type == "simulation":
            status = context.get("status", "pending")

            if status in ["pending", "created"]:
                actions.append({
                    "name": "execute_simulation",
                    "href": f"/api/v1/simulations/{resource_id}/execute",
                    "method": "POST",
                    "title": "Start simulation execution",
                    "fields": [
                        {
                            "name": "priority",
                            "type": "string",
                            "required": False,
                            "description": "Execution priority"
                        }
                    ]
                })

            if status in ["running", "executing"]:
                actions.append({
                    "name": "cancel_execution",
                    "href": f"/api/v1/simulations/{resource_id}",
                    "method": "DELETE",
                    "title": "Cancel running simulation"
                })

        return actions

    def _generate_common_links(self,
                             resource_type: str,
                             resource_id: str,
                             context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate common navigation links."""
        links = []

        # Health link
        links.append({
            "rel": LinkRelation.HEALTH.value,
            "href": "/health",
            "method": "GET",
            "title": "Service health status"
        })

        # API documentation
        links.append({
            "rel": "documentation",
            "href": "/docs",
            "method": "GET",
            "title": "API documentation"
        })

        # Root resource
        links.append({
            "rel": "root",
            "href": "/",
            "method": "GET",
            "title": "API root"
        })

        return links

    def create_state_machine_links(self,
                                 current_state: str,
                                 resource_type: str,
                                 resource_id: str,
                                 allowed_transitions: List[str] = None) -> List[Dict[str, Any]]:
        """Create links based on state machine transitions."""
        links = []

        # Define state transitions for simulations
        state_transitions = {
            "pending": ["execute", "cancel", "update"],
            "running": ["cancel", "pause"],
            "paused": ["execute", "cancel"],
            "completed": ["results", "analytics", "reports", "delete"],
            "failed": ["retry", "delete"]
        }

        allowed_transitions = allowed_transitions or state_transitions.get(current_state, [])

        for transition in allowed_transitions:
            if transition == "execute":
                links.append({
                    "rel": LinkRelation.EXECUTE.value,
                    "href": f"/api/v1/simulations/{resource_id}/execute",
                    "method": "POST",
                    "title": "Execute simulation"
                })
            elif transition == "cancel":
                links.append({
                    "rel": LinkRelation.DELETE.value,
                    "href": f"/api/v1/simulations/{resource_id}",
                    "method": "DELETE",
                    "title": "Cancel simulation"
                })
            elif transition == "results":
                links.append({
                    "rel": LinkRelation.RESULTS.value,
                    "href": f"/api/v1/simulations/{resource_id}/results",
                    "method": "GET",
                    "title": "View results"
                })

        return links

    def create_conditional_links(self,
                               resource_type: str,
                               resource_id: str,
                               conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create links based on conditional logic."""
        links = []

        # User permission-based links
        user_permissions = conditions.get("user_permissions", [])
        if "admin" in user_permissions:
            links.append({
                "rel": "admin",
                "href": f"/api/v1/admin/{resource_type}/{resource_id}",
                "method": "GET",
                "title": "Administrative controls"
            })

        # Feature flag-based links
        feature_flags = conditions.get("feature_flags", {})
        if feature_flags.get("advanced_analytics", False):
            links.append({
                "rel": "advanced-analytics",
                "href": f"/api/v1/{resource_type}/{resource_id}/advanced-analytics",
                "method": "GET",
                "title": "Advanced analytics"
            })

        # Time-based links
        current_hour = conditions.get("current_hour", datetime.now().hour)
        if 9 <= current_hour <= 17:  # Business hours
            links.append({
                "rel": "support",
                "href": "/support/chat",
                "method": "GET",
                "title": "Live support"
            })

        return links

    def export_api_specification(self) -> Dict[str, Any]:
        """Export comprehensive API specification with hypermedia."""
        spec = {
            "openapi": "3.0.1",
            "info": {
                "title": "Project Simulation Service API",
                "version": "1.0.0",
                "description": "REST API with comprehensive HATEOAS navigation"
            },
            "servers": [
                {"url": "http://localhost:5075", "description": "Development server"},
                {"url": "https://api.project-simulation.com", "description": "Production server"}
            ],
            "links": self._generate_api_root_links(),
            "components": {
                "linkRelations": self._generate_link_relations_spec()
            }
        }

        return spec

    def _generate_api_root_links(self) -> List[Dict[str, Any]]:
        """Generate links for API root."""
        return [
            {
                "rel": "self",
                "href": "/",
                "title": "API Root"
            },
            {
                "rel": "simulations",
                "href": "/api/v1/simulations",
                "title": "Simulations collection"
            },
            {
                "rel": "health",
                "href": "/health",
                "title": "Service health"
            },
            {
                "rel": "docs",
                "href": "/docs",
                "title": "API documentation"
            }
        ]

    def _generate_link_relations_spec(self) -> Dict[str, Any]:
        """Generate specification for custom link relations."""
        return {
            "simulate": {
                "description": "Execute a simulation",
                "methods": ["POST"]
            },
            "execute": {
                "description": "Execute or run a resource",
                "methods": ["POST"]
            },
            "analytics": {
                "description": "Access analytics and insights",
                "methods": ["GET"]
            },
            "reports": {
                "description": "Generate and access reports",
                "methods": ["GET", "POST"]
            },
            "metrics": {
                "description": "Access performance metrics",
                "methods": ["GET"]
            }
        }


# Global HATEOAS manager instance
_hateoas_manager: Optional[AdvancedHATEOASManager] = None


def get_advanced_hateoas_manager() -> AdvancedHATEOASManager:
    """Get the global advanced HATEOAS manager instance."""
    global _hateoas_manager
    if _hateoas_manager is None:
        _hateoas_manager = AdvancedHATEOASManager()
    return _hateoas_manager


__all__ = [
    'LinkRelation',
    'LinkTemplate',
    'HypermediaResource',
    'SimulationResource',
    'AnalyticsResource',
    'ReportResource',
    'AdvancedHATEOASManager',
    'get_advanced_hateoas_manager'
]
