"""
Simulation Analyzer for processing and analyzing simulation data.
Following DDD principles with clean separation of concerns.
Integrates with ecosystem services for comprehensive analysis.
"""

import time
import httpx
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from simulation.domain.analysis.analysis_result import AnalysisResult, AnalysisType


class SimulationAnalyzer:
    """Analyzer for simulation data and execution results."""

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None):
        """Initialize the analyzer with optional HTTP client."""
        self.http_client = http_client or httpx.AsyncClient(timeout=30.0)
        self._is_docker_environment = self._detect_docker_environment()
        self.service_urls = self._configure_service_urls()

    def _detect_docker_environment(self) -> bool:
        """Detect if the service is running in a Docker container."""
        # Multiple indicators for Docker environment
        docker_indicators = [
            # Check for Docker-specific files
            os.path.exists('/.dockerenv'),
            # Check for container-specific cgroup
            os.path.exists('/proc/1/cgroup') and 'docker' in open('/proc/1/cgroup').read(),
            # Check environment variables
            (os.getenv('DOCKER_CONTAINER') or '').lower() in ('true', '1', 'yes'),
            # Check for Docker host
            os.getenv('DOCKER_HOST') is not None,
            # Check hostname pattern (common in Docker)
            (os.getenv('HOSTNAME') or '').startswith('docker-')
        ]

        return any(docker_indicators)

    def _configure_service_urls(self) -> Dict[str, str]:
        """Configure service URLs based on runtime environment."""
        # Base service configurations for different environments
        # Ports based on docker-compose.dev.yml configuration
        service_configs = {
            "summarizer_hub": {
                "docker": "http://summarizer-hub:5160",
                "local": "http://localhost:5160"
            },
            "doc_store": {
                "docker": "http://doc-store:5010",  # Internal Docker port
                "local": "http://localhost:5087"    # External Docker port for local access
            },
            "analysis_service": {
                "docker": "http://analysis-service:5020",  # Internal Docker port
                "local": "http://localhost:5080"           # External Docker port for local access
            },
            "code_analyzer": {
                "docker": "http://code-analyzer:5025",
                "local": "http://localhost:5025"
            }
        }

        # Determine environment
        environment = "docker" if self._is_docker_environment else "local"

        # Allow override via environment variables
        configured_urls = {}
        for service_name, urls in service_configs.items():
            # Check for explicit environment variable override
            env_var = f"{service_name.upper()}_URL"
            override_url = os.getenv(env_var)

            if override_url:
                configured_urls[service_name] = override_url
            else:
                configured_urls[service_name] = urls[environment]

        return configured_urls

    def get_environment_info(self) -> Dict[str, Any]:
        """Get information about the current runtime environment."""
        return {
            "is_docker_environment": self._is_docker_environment,
            "environment_type": "docker" if self._is_docker_environment else "local",
            "service_urls": self.service_urls,
            "hostname": os.getenv('HOSTNAME', 'unknown'),
            "docker_indicators": {
                "dockerenv_file": os.path.exists('/.dockerenv'),
                "docker_cgroup": os.path.exists('/proc/1/cgroup') and 'docker' in open('/proc/1/cgroup').read() if os.path.exists('/proc/1/cgroup') else False,
                "docker_env_var": os.getenv('DOCKER_CONTAINER', '').lower() in ('true', '1', 'yes'),
                "docker_host": os.getenv('DOCKER_HOST') is not None,
                "docker_hostname": os.getenv('HOSTNAME', '').startswith('docker-') if os.getenv('HOSTNAME') else False
            }
        }

    async def analyze_documents(self, simulation_id: str, documents: List[Dict[str, Any]]) -> AnalysisResult:
        """Analyze documents in the simulation using ecosystem services."""
        start_time = time.time()

        result = AnalysisResult(
            simulation_id=simulation_id,
            analysis_type=AnalysisType.DOCUMENT_ANALYSIS
        )

        result.add_metric("document_count", len(documents))

        if len(documents) == 0:
            result.add_finding("No documents found in simulation")
            result.add_recommendation("Consider adding documentation to the simulation")
        else:
            # Use summarizer-hub for document analysis
            summarizer_analysis = await self._analyze_with_summarizer_hub(documents)
            if summarizer_analysis:
                result.findings.extend(summarizer_analysis.get("findings", []))
                result.recommendations.extend(summarizer_analysis.get("recommendations", []))
                result.add_metric("summarizer_analysis", summarizer_analysis)

            # Use doc-store for document quality analysis
            doc_store_analysis = await self._analyze_with_doc_store(documents)
            if doc_store_analysis:
                result.findings.extend(doc_store_analysis.get("findings", []))
                result.recommendations.extend(doc_store_analysis.get("recommendations", []))
                result.add_metric("doc_store_analysis", doc_store_analysis)

            # Analyze document types and quality
            doc_types = {}
            quality_scores = []

            for doc in documents:
                doc_type = doc.get("type", "unknown")
                doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

                # Estimate quality score based on content length and completeness
                content = doc.get("content", "")
                quality_score = min(len(content) / 1000, 1.0)  # Simple quality heuristic
                quality_scores.append(quality_score)

            result.add_metric("document_types", doc_types)
            result.add_metric("average_quality_score", sum(quality_scores) / len(quality_scores) if quality_scores else 0)

            # Enhanced quality checks using ecosystem insights
            if len(doc_types) < 3:
                result.add_finding("Limited variety in document types")
                result.add_recommendation("Consider adding API documentation, user manuals, and architecture diagrams")

            avg_quality = result.metrics.get("average_quality_score", 0)
            if avg_quality < 0.5:
                result.add_finding("Low document quality detected")
                result.add_recommendation("Improve document completeness and detail")

        result.processing_time_seconds = time.time() - start_time
        result.confidence_score = result.calculate_confidence()

        return result

    async def analyze_timeline(self, simulation_id: str, timeline: List[Dict[str, Any]]) -> AnalysisResult:
        """Analyze project timeline."""
        start_time = time.time()

        result = AnalysisResult(
            simulation_id=simulation_id,
            analysis_type=AnalysisType.TIMELINE_ANALYSIS
        )

        if len(timeline) == 0:
            result.add_finding("No timeline defined")
            result.add_recommendation("Define project phases and timeline")
        else:
            # Calculate total duration
            total_duration = sum(phase.get("duration_weeks", 0) for phase in timeline)
            result.add_metric("total_duration", total_duration)
            result.add_metric("phase_count", len(timeline))

            # Analyze timeline structure
            if total_duration < 4:
                result.add_finding("Timeline too short for realistic project")
                result.add_recommendation("Consider extending timeline for more realistic simulation")

            if total_duration > 24:
                result.add_finding("Timeline very long")
                result.add_recommendation("Review if all phases are necessary")

            # Check for overlapping phases
            sorted_phases = sorted(timeline, key=lambda x: x.get("start_week", 0))
            for i in range(len(sorted_phases) - 1):
                current_end = sorted_phases[i]["start_week"] + sorted_phases[i]["duration_weeks"]
                next_start = sorted_phases[i + 1]["start_week"]

                if current_end > next_start:
                    result.add_finding("Potential phase overlap detected")
                    result.add_recommendation("Review phase scheduling to avoid overlaps")

        result.processing_time_seconds = time.time() - start_time
        result.confidence_score = result.calculate_confidence()

        return result

    async def analyze_team_dynamics(self, simulation_id: str, team_members: List[Dict[str, Any]]) -> AnalysisResult:
        """Analyze team dynamics and composition."""
        start_time = time.time()

        result = AnalysisResult(
            simulation_id=simulation_id,
            analysis_type=AnalysisType.TEAM_DYNAMICS
        )

        result.add_metric("team_size", len(team_members))

        if len(team_members) == 0:
            result.add_finding("No team members defined")
            result.add_recommendation("Define team members for realistic simulation")
        else:
            # Analyze roles
            roles = {}
            total_experience = 0
            skills_set = set()

            for member in team_members:
                role = member.get("role", "unknown")
                roles[role] = roles.get(role, 0) + 1
                total_experience += member.get("experience_years", 0)

                member_skills = member.get("skills", [])
                skills_set.update(member_skills)

            result.add_metric("role_distribution", roles)
            result.add_metric("total_experience_years", total_experience)
            result.add_metric("unique_skills_count", len(skills_set))

            # Team composition analysis
            if len(roles) < 3:
                result.add_finding("Limited role diversity")
                result.add_recommendation("Consider adding developers, QA engineers, and product owners")

            if total_experience / len(team_members) < 2:
                result.add_finding("Team has limited experience")
                result.add_recommendation("Consider adding more experienced team members")

            if len(skills_set) < 5:
                result.add_finding("Limited skill diversity")
                result.add_recommendation("Team could benefit from broader skill set")

        result.processing_time_seconds = time.time() - start_time
        result.confidence_score = result.calculate_confidence()

        return result

    async def assess_risks(self, simulation_id: str, simulation_data: Dict[str, Any]) -> AnalysisResult:
        """Perform risk assessment on simulation."""
        start_time = time.time()

        result = AnalysisResult(
            simulation_id=simulation_id,
            analysis_type=AnalysisType.RISK_ASSESSMENT
        )

        # Analyze various risk factors
        risk_factors = []

        # Timeline risk
        timeline = simulation_data.get("timeline", [])
        if timeline:
            total_duration = sum(phase.get("duration_weeks", 0) for phase in timeline)
            if total_duration > 16:
                risk_factors.append("Extended timeline increases delivery risk")
            elif total_duration < 6:
                risk_factors.append("Compressed timeline may lead to quality issues")

        # Team risk
        team_members = simulation_data.get("team_members", [])
        if len(team_members) < 3:
            risk_factors.append("Small team size increases workload risk")
        elif len(team_members) > 8:
            risk_factors.append("Large team may have coordination challenges")

        # Technology risk
        technologies = simulation_data.get("technologies", [])
        if len(technologies) > 8:
            risk_factors.append("Many technologies may increase complexity")
        elif len(technologies) < 3:
            risk_factors.append("Limited technology stack may constrain capabilities")

        # Budget risk
        budget = simulation_data.get("budget", 0)
        if budget > 500000:
            risk_factors.append("High budget may indicate scope creep risk")
        elif budget < 50000:
            risk_factors.append("Low budget may constrain quality and features")

        result.findings.extend(risk_factors)
        result.add_metric("risk_factor_count", len(risk_factors))

        # Risk level determination
        if len(risk_factors) == 0:
            risk_level = "low"
            result.recommendations.append("Project appears to have manageable risk profile")
        elif len(risk_factors) <= 2:
            risk_level = "medium"
            result.recommendations.append("Monitor identified risk factors closely")
        else:
            risk_level = "high"
            result.recommendations.append("Comprehensive risk mitigation plan recommended")

        result.add_metric("risk_level", risk_level)

        result.processing_time_seconds = time.time() - start_time
        result.confidence_score = result.calculate_confidence()

        return result

    async def analyze_cost_benefit(self, simulation_id: str, cost_data: Dict[str, Any]) -> AnalysisResult:
        """Analyze cost-benefit aspects of simulation."""
        start_time = time.time()

        result = AnalysisResult(
            simulation_id=simulation_id,
            analysis_type=AnalysisType.COST_BENEFIT_ANALYSIS
        )

        # Extract cost data
        budget = cost_data.get("budget", 0)
        team_cost_per_month = cost_data.get("team_cost_per_month", 0)
        infrastructure_cost = cost_data.get("infrastructure_cost", 0)
        duration_months = cost_data.get("estimated_duration_months", 1)

        # Calculate total costs
        total_team_cost = team_cost_per_month * duration_months
        total_infrastructure_cost = infrastructure_cost * duration_months
        total_estimated_cost = total_team_cost + total_infrastructure_cost

        result.add_metric("total_estimated_cost", total_estimated_cost)
        result.add_metric("team_cost_percentage", (total_team_cost / total_estimated_cost) * 100 if total_estimated_cost > 0 else 0)

        # Budget analysis
        if budget > 0:
            budget_utilization = (total_estimated_cost / budget) * 100
            result.add_metric("budget_utilization", budget_utilization)

            if budget_utilization > 120:
                result.add_finding("Estimated costs exceed budget")
                result.recommendations.append("Review scope or negotiate higher budget")
            elif budget_utilization < 70:
                result.add_finding("Significant budget underutilization")
                result.recommendations.append("Consider expanding scope or reducing timeline")

        # Break-even analysis (simplified)
        monthly_revenue_assumption = total_estimated_cost * 0.1  # Assume 10% monthly return
        break_even_months = duration_months + 3  # 3 months additional for break-even
        result.add_metric("estimated_break_even_months", break_even_months)

        result.processing_time_seconds = time.time() - start_time
        result.confidence_score = result.calculate_confidence()

        return result

    async def perform_comprehensive_analysis(self, simulation_id: str, simulation_data: Dict[str, Any]) -> List[AnalysisResult]:
        """Perform comprehensive analysis of all simulation aspects."""
        results = []

        # Analyze documents
        if "documents" in simulation_data:
            doc_result = await self.analyze_documents(simulation_id, simulation_data["documents"])
            results.append(doc_result)

        # Analyze timeline
        if "timeline" in simulation_data:
            timeline_result = await self.analyze_timeline(simulation_id, simulation_data["timeline"])
            results.append(timeline_result)

        # Analyze team dynamics
        if "team_members" in simulation_data:
            team_result = await self.analyze_team_dynamics(simulation_id, simulation_data["team_members"])
            results.append(team_result)

        # Perform risk assessment
        risk_result = await self.assess_risks(simulation_id, simulation_data)
        results.append(risk_result)

        # Perform cost-benefit analysis if cost data available
        if any(key in simulation_data for key in ["budget", "team_cost_per_month", "infrastructure_cost"]):
            cost_data = {
                key: simulation_data.get(key, 0)
                for key in ["budget", "team_cost_per_month", "infrastructure_cost", "estimated_duration_months"]
            }
            cost_result = await self.analyze_cost_benefit(simulation_id, cost_data)
            results.append(cost_result)

        return results

    # ============================================================================
    # ECOSYSTEM SERVICE INTEGRATION METHODS
    # ============================================================================

    async def _analyze_with_summarizer_hub(self, documents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze documents using the summarizer-hub service."""
        try:
            summarizer_url = f"{self.service_urls['summarizer_hub']}/api/v1/analyze"

            # Prepare document content for analysis
            analysis_request = {
                "documents": [
                    {
                        "id": doc.get("id", f"doc_{i}"),
                        "content": doc.get("content", ""),
                        "type": doc.get("type", "unknown"),
                        "title": doc.get("title", "")
                    }
                    for i, doc in enumerate(documents[:5])  # Limit to first 5 documents
                ],
                "analysis_type": "comprehensive",
                "include_recommendations": True
            }

            response = await self.http_client.post(
                summarizer_url,
                json=analysis_request,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                return response.json()
            else:
                # Fallback analysis if service unavailable
                return self._fallback_document_analysis(documents)

        except Exception as e:
            # Service unavailable - return fallback analysis
            return self._fallback_document_analysis(documents)

    async def _analyze_with_doc_store(self, documents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze documents using the doc-store service."""
        try:
            doc_store_url = f"{self.service_urls['doc_store']}/api/v1/analyze/quality"

            analysis_request = {
                "document_ids": [doc.get("id") for doc in documents if doc.get("id")],
                "analysis_type": "quality_check"
            }

            response = await self.http_client.post(
                doc_store_url,
                json=analysis_request,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception:
            return None

    async def _analyze_with_analysis_service(self, data: Dict[str, Any], analysis_type: str) -> Optional[Dict[str, Any]]:
        """Analyze data using the general analysis service."""
        try:
            analysis_url = f"{self.service_urls['analysis_service']}/api/v1/analyze/{analysis_type}"

            response = await self.http_client.post(
                analysis_url,
                json=data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception:
            return None

    async def _analyze_with_code_analyzer(self, code_content: str) -> Optional[Dict[str, Any]]:
        """Analyze code using the code analyzer service."""
        try:
            code_analyzer_url = f"{self.service_urls['code_analyzer']}/api/v1/analyze"

            analysis_request = {
                "code": code_content,
                "analysis_type": "quality_metrics"
            }

            response = await self.http_client.post(
                code_analyzer_url,
                json=analysis_request,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except Exception:
            return None

    def _fallback_document_analysis(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback document analysis when summarizer-hub is unavailable."""
        findings = []
        recommendations = []

        if len(documents) == 0:
            findings.append("No documents available for analysis")
            recommendations.append("Add documentation to improve simulation quality")
        elif len(documents) < 3:
            findings.append("Limited documentation coverage")
            recommendations.append("Consider adding more comprehensive documentation")
        else:
            findings.append("Basic documentation structure detected")
            recommendations.append("Consider using advanced analysis for deeper insights")

        return {
            "findings": findings,
            "recommendations": recommendations,
            "analysis_method": "fallback",
            "confidence": 0.6
        }

    async def _get_service_health_status(self, service_name: str) -> bool:
        """Check if a service is healthy and available."""
        try:
            service_url = self.service_urls.get(service_name)
            if not service_url:
                return False

            health_url = f"{service_url}/health"
            response = await self.http_client.get(health_url)

            return response.status_code == 200
        except Exception:
            return False
