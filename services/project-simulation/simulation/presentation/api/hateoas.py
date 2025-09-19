"""HATEOAS Navigation - Hypermedia Resource Navigation.

This module implements HATEOAS (Hypermedia as the Engine of Application State)
for the project-simulation REST API, providing discoverable resource navigation
and self-documenting API interactions.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Link(BaseModel):
    """HATEOAS link representation."""
    href: str = Field(..., description="The target URI of the link")
    rel: str = Field(..., description="The relationship type of the link")
    method: str = Field(default="GET", description="HTTP method for the link")
    title: Optional[str] = Field(None, description="Human-readable title for the link")
    type: Optional[str] = Field(None, description="Media type of the linked resource")
    templated: bool = Field(default=False, description="Whether the href is a URI template")

    def to_dict(self) -> Dict[str, Any]:
        """Convert link to dictionary."""
        result = {
            "href": self.href,
            "rel": self.rel,
            "method": self.method
        }
        if self.title:
            result["title"] = self.title
        if self.type:
            result["type"] = self.type
        if self.templated:
            result["templated"] = self.templated
        return result


class Links(BaseModel):
    """Collection of HATEOAS links."""
    self: Link = Field(..., description="Self-referencing link")
    links: List[Link] = Field(default_factory=list, description="Additional links")

    def add_link(self, link: Link) -> None:
        """Add a link to the collection."""
        self.links.append(link)

    def to_dict(self) -> List[Dict[str, Any]]:
        """Convert links to list format for JSON response."""
        result = [self.self.to_dict()]
        for link in self.links:
            result.append(link.to_dict())
        return result


class HateoasResponse(BaseModel):
    """Base class for HATEOAS-enabled API responses."""
    success: bool = Field(default=True, description="Operation success status")
    data: Any = Field(..., description="The response data")
    links: Links = Field(..., description="HATEOAS links", alias="_links")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Response timestamp")
    version: str = Field(default="1.0.0", description="API version")
    status: str = Field(default="success", description="Response status")

    class Config:
        """Pydantic configuration."""
        allow_population_by_field_name = True


class SimulationResource:
    """HATEOAS resource representation for simulations."""

    @staticmethod
    def create_simulation_links(simulation_id: str, base_url: str = "") -> Links:
        """Create HATEOAS links for a simulation resource."""
        base_path = f"{base_url}/api/v1/simulations"

        links = Links(
            self=Link(
                href=f"{base_path}/{simulation_id}",
                rel="self",
                method="GET",
                title="Get simulation details"
            )
        )

        # Add action links
        links.add_link(Link(
            href=f"{base_path}/{simulation_id}/execute",
            rel="execute",
            method="POST",
            title="Execute simulation"
        ))

        links.add_link(Link(
            href=f"{base_path}/{simulation_id}/results",
            rel="results",
            method="GET",
            title="Get simulation results"
        ))

        links.add_link(Link(
            href=f"{base_path}/{simulation_id}",
            rel="cancel",
            method="DELETE",
            title="Cancel simulation"
        ))

        links.add_link(Link(
            href=f"{base_path}",
            rel="collection",
            method="GET",
            title="List all simulations"
        ))

        return links

    @staticmethod
    def create_simulation_collection_links(base_url: str = "", pagination: Optional[Dict[str, Any]] = None) -> Links:
        """Create HATEOAS links for simulation collection."""
        base_path = f"{base_url}/api/v1/simulations"

        links = Links(
            self=Link(
                href=base_path,
                rel="self",
                method="GET",
                title="List simulations"
            )
        )

        links.add_link(Link(
            href=f"{base_path}",
            rel="create",
            method="POST",
            title="Create new simulation"
        ))

        # Add pagination links if provided
        if pagination:
            if pagination.get("has_previous"):
                links.add_link(Link(
                    href=f"{base_path}?page={pagination['current_page'] - 1}",
                    rel="previous",
                    method="GET",
                    title="Previous page"
                ))

            if pagination.get("has_next"):
                links.add_link(Link(
                    href=f"{base_path}?page={pagination['current_page'] + 1}",
                    rel="next",
                    method="GET",
                    title="Next page"
                ))

            links.add_link(Link(
                href=f"{base_path}?page=1",
                rel="first",
                method="GET",
                title="First page"
            ))

            links.add_link(Link(
                href=f"{base_path}?page={pagination.get('total_pages', 1)}",
                rel="last",
                method="GET",
                title="Last page"
            ))

        return links


class RootResource:
    """HATEOAS resource representation for API root."""

    @staticmethod
    def create_root_links(base_url: str = "") -> Links:
        """Create HATEOAS links for API root."""
        links = Links(
            self=Link(
                href=f"{base_url}/",
                rel="self",
                method="GET",
                title="API root"
            )
        )

        # API documentation links
        links.add_link(Link(
            href=f"{base_url}/docs",
            rel="documentation",
            method="GET",
            title="API documentation",
            type="text/html"
        ))

        links.add_link(Link(
            href=f"{base_url}/redoc",
            rel="redoc",
            method="GET",
            title="ReDoc API documentation",
            type="text/html"
        ))

        links.add_link(Link(
            href=f"{base_url}/openapi.json",
            rel="openapi",
            method="GET",
            title="OpenAPI specification",
            type="application/json"
        ))

        # Resource collection links
        links.add_link(Link(
            href=f"{base_url}/api/v1/simulations",
            rel="simulations",
            method="GET",
            title="List simulations"
        ))

        # Health and monitoring links
        links.add_link(Link(
            href=f"{base_url}/health",
            rel="health",
            method="GET",
            title="Service health check"
        ))

        links.add_link(Link(
            href=f"{base_url}/health/detailed",
            rel="health_detailed",
            method="GET",
            title="Detailed health information"
        ))

        return links


class HealthResource:
    """HATEOAS resource representation for health endpoints."""

    @staticmethod
    def create_health_links(base_url: str = "", include_system: bool = False) -> Links:
        """Create HATEOAS links for health endpoints."""
        links = Links(
            self=Link(
                href=f"{base_url}/health",
                rel="self",
                method="GET",
                title="Basic health check"
            )
        )

        links.add_link(Link(
            href=f"{base_url}/health/detailed",
            rel="detailed",
            method="GET",
            title="Detailed health information"
        ))

        if include_system:
            links.add_link(Link(
                href=f"{base_url}/health/system",
                rel="system",
                method="GET",
                title="System-wide health check"
            ))

        links.add_link(Link(
            href=f"{base_url}/",
            rel="root",
            method="GET",
            title="API root"
        ))

        return links


def create_hateoas_response(data: Any, links: Links, **kwargs) -> Dict[str, Any]:
    """Create a HATEOAS-enabled response."""
    response = HateoasResponse(data=data, _links=links, **kwargs)
    return response.dict(by_alias=True)


def add_cors_headers(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add CORS headers to response for browser compatibility."""
    # This would be handled by FastAPI CORS middleware in production
    # Including here for completeness
    return response_data


def create_error_response(error: str, status_code: int = 500, links: Optional[Links] = None) -> Dict[str, Any]:
    """Create a HATEOAS-enabled error response."""
    if links is None:
        # Create basic root links for error recovery
        links = RootResource.create_root_links()

    return {
        "error": error,
        "status_code": status_code,
        "timestamp": datetime.now().isoformat(),
        "links": links.to_dict(),
        "version": "1.0.0"
    }


# API Resource Templates
SIMULATION_LINKS_TEMPLATE = {
    "self": {"href": "/api/v1/simulations/{id}", "rel": "self", "method": "GET"},
    "execute": {"href": "/api/v1/simulations/{id}/execute", "rel": "execute", "method": "POST"},
    "results": {"href": "/api/v1/simulations/{id}/results", "rel": "results", "method": "GET"},
    "cancel": {"href": "/api/v1/simulations/{id}", "rel": "cancel", "method": "DELETE"},
    "collection": {"href": "/api/v1/simulations", "rel": "collection", "method": "GET"}
}

COLLECTION_LINKS_TEMPLATE = {
    "self": {"href": "/api/v1/simulations", "rel": "self", "method": "GET"},
    "create": {"href": "/api/v1/simulations", "rel": "create", "method": "POST"},
    "first": {"href": "/api/v1/simulations?page=1", "rel": "first", "method": "GET"},
    "last": {"href": "/api/v1/simulations?page={total_pages}", "rel": "last", "method": "GET"}
}

def generate_pagination_links(base_url: str, current_page: int, total_pages: int, **params) -> List[Link]:
    """Generate pagination links based on current page and total pages."""
    links = []

    # Self link
    query_params = "&".join([f"{k}={v}" for k, v in params.items()])
    if query_params:
        query_params = f"?{query_params}&page={current_page}"
    else:
        query_params = f"?page={current_page}"

    links.append(Link(
        href=f"{base_url}{query_params}",
        rel="self",
        method="GET",
        title=f"Page {current_page}"
    ))

    # Previous page
    if current_page > 1:
        prev_params = f"?page={current_page - 1}"
        if query_params and "&page=" in query_params:
            prev_params = query_params.replace(f"page={current_page}", f"page={current_page - 1}")
        links.append(Link(
            href=f"{base_url}{prev_params}",
            rel="previous",
            method="GET",
            title="Previous page"
        ))

    # Next page
    if current_page < total_pages:
        next_params = f"?page={current_page + 1}"
        if query_params and "&page=" in query_params:
            next_params = query_params.replace(f"page={current_page}", f"page={current_page + 1}")
        links.append(Link(
            href=f"{base_url}{next_params}",
            rel="next",
            method="GET",
            title="Next page"
        ))

    # First page
    first_params = "?page=1"
    if query_params and "&page=" in query_params:
        first_params = query_params.replace(f"page={current_page}", "page=1")
    links.append(Link(
        href=f"{base_url}{first_params}",
        rel="first",
        method="GET",
        title="First page"
    ))

    # Last page
    last_params = f"?page={total_pages}"
    if query_params and "&page=" in query_params:
        last_params = query_params.replace(f"page={current_page}", f"page={total_pages}")
    links.append(Link(
        href=f"{base_url}{last_params}",
        rel="last",
        method="GET",
        title="Last page"
    ))

    return links
