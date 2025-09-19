"""
Simulation Analyzer for processing and analyzing simulation data.
Following DDD principles with clean separation of concerns.
Integrates with ecosystem services for comprehensive analysis.
"""

import time
import httpx
import os
import json
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
        else:
            # Get recommendations report from summarizer-hub
            recommendations_report = await self._get_recommendations_report_from_summarizer_hub(simulation_id, documents)
            if recommendations_report:
                result.add_metric("recommendations_report_id", recommendations_report["report_id"])
                result.add_metric("recommendations_summary", recommendations_report["summary"])
                result.add_finding("Recommendations report generated and stored")
            else:
                result.add_finding("No recommendations report generated")

            # Get comprehensive analysis report from analysis-service
            analysis_report = await self._get_analysis_report_from_analysis_service(simulation_id, documents)
            if analysis_report:
                result.add_metric("analysis_report_id", analysis_report["report_id"])
                result.add_metric("analysis_summary", analysis_report["summary"])
                result.add_finding("Analysis report received and stored")
            else:
                result.add_finding("No analysis report received")

            # Use doc-store for document quality analysis (without local recommendations)
            doc_store_analysis = await self._analyze_with_doc_store(documents)
            if doc_store_analysis:
                result.findings.extend(doc_store_analysis.get("findings", []))
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

            avg_quality = result.metrics.get("average_quality_score", 0)
            if avg_quality < 0.5:
                result.add_finding("Low document quality detected")

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
        else:
            # Calculate total duration
            total_duration = sum(phase.get("duration_weeks", 0) for phase in timeline)
            result.add_metric("total_duration", total_duration)
            result.add_metric("phase_count", len(timeline))

            # Analyze timeline structure
            if total_duration < 4:
                result.add_finding("Timeline too short for realistic project")

            if total_duration > 24:
                result.add_finding("Timeline very long")

            # Check for overlapping phases
            sorted_phases = sorted(timeline, key=lambda x: x.get("start_week", 0))
            for i in range(len(sorted_phases) - 1):
                current_end = sorted_phases[i]["start_week"] + sorted_phases[i]["duration_weeks"]
                next_start = sorted_phases[i + 1]["start_week"]

                if current_end > next_start:
                    result.add_finding("Potential phase overlap detected")

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
    # RECOMMENDATIONS REPORT MANAGEMENT
    # ============================================================================

    async def _get_recommendations_report_from_summarizer_hub(self, simulation_id: str, documents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get recommendations report from summarizer-hub and store it."""
        try:
            # Get recommendations from summarizer-hub
            recommendations = await self._get_recommendations_from_summarizer_hub(documents)

            if not recommendations:
                return None

            # Generate report data
            report_data = {
                "simulation_id": simulation_id,
                "timestamp": datetime.now().isoformat(),
                "documents_analyzed": len(documents),
                "recommendations": recommendations,
                "summary": {
                    "total_recommendations": len(recommendations),
                    "recommendation_types": list(set(r.get("type", "unknown") for r in recommendations)),
                    "priority_breakdown": {
                        "high": len([r for r in recommendations if r.get("priority") == "high"]),
                        "medium": len([r for r in recommendations if r.get("priority") == "medium"]),
                        "low": len([r for r in recommendations if r.get("priority") == "low"])
                    }
                }
            }

            # Store report in doc-store
            report_id = await self._store_recommendations_report(report_data)

            return {
                "report_id": report_id,
                "summary": report_data["summary"]
            }

        except Exception as e:
            print(f"Error getting recommendations report: {e}")
            return None

    async def _get_recommendations_from_summarizer_hub(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get recommendations from summarizer-hub service."""
        try:
            summarizer_url = self.service_urls.get('summarizer_hub', 'http://localhost:5160')

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{summarizer_url}/api/v1/recommendations",
                    json={
                        "documents": documents,
                        "recommendation_types": ["consolidation", "duplicate", "outdated", "quality"]
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        return result.get("recommendations", [])
                    else:
                        print(f"Summarizer Hub error: {result.get('error', 'Unknown error')}")
                        return []
                else:
                    print(f"Summarizer Hub request failed: {response.status_code}")
                    return []

        except Exception as e:
            print(f"Error communicating with Summarizer Hub: {e}")
            return []

    async def _get_analysis_report_from_analysis_service(self, simulation_id: str, documents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get comprehensive analysis report from analysis-service."""
        try:
            # Request analysis report generation from analysis-service
            analysis_report = await self._request_analysis_report_from_service(simulation_id, documents)

            if not analysis_report:
                return None

            # Store the received report in doc-store
            report_id = await self._store_received_analysis_report(analysis_report, simulation_id)

            return {
                "report_id": report_id,
                "summary": analysis_report.get("summary", {})
            }

        except Exception as e:
            print(f"Error getting analysis report from analysis-service: {e}")
            return None

    async def _request_analysis_report_from_service(self, simulation_id: str, documents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Request a complete analysis report from analysis-service."""
        try:
            analysis_url = self.service_urls.get('analysis_service', 'http://localhost:5020')

            async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for report generation
                response = await client.post(
                    f"{analysis_url}/api/v1/analyze/generate-report",
                    json={
                        "simulation_id": simulation_id,
                        "documents": documents,
                        "report_type": "comprehensive_simulation_analysis",
                        "include_markdown": True,
                        "include_json": True
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success") and result.get("report"):
                        return result["report"]
                    else:
                        print(f"Analysis service report generation failed: {result.get('error', 'Unknown error')}")
                        return None
                else:
                    print(f"Analysis service report request failed: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            print(f"Error requesting analysis report from analysis-service: {e}")
            return None

    async def _store_recommendations_report(self, report_data: Dict[str, Any]) -> str:
        """Store recommendations report in doc-store and generate files."""
        try:
            # Generate unique report ID
            report_id = f"rec_report_{report_data['simulation_id']}_{int(datetime.now().timestamp())}"

            # Store JSON version in doc-store
            json_content = {
                "id": report_id,
                "type": "recommendations_report",
                "simulation_id": report_data["simulation_id"],
                "title": f"Recommendations Report - {report_data['simulation_id']}",
                "content": json.dumps(report_data, indent=2),
                "format": "json",
                "timestamp": report_data["timestamp"],
                "metadata": {
                    "document_count": report_data["documents_analyzed"],
                    "recommendations_count": report_data["summary"]["total_recommendations"],
                    "report_type": "simulation_recommendations"
                }
            }

            # Store in doc-store
            await self._save_to_doc_store(json_content)

            # Generate and store Markdown version
            md_content = self._generate_markdown_report(report_data)
            await self._save_markdown_report(md_content, report_id)

            # Link to simulation run data
            await self._link_report_to_simulation(report_id, report_data["simulation_id"])

            return report_id

        except Exception as e:
            print(f"Error storing recommendations report: {e}")
            raise

    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Generate Markdown version of the recommendations report."""
        md_lines = []

        md_lines.append("# 📋 Simulation Recommendations Report")
        md_lines.append("")
        md_lines.append(f"**Simulation ID:** {report_data['simulation_id']}")
        md_lines.append(f"**Generated:** {report_data['timestamp']}")
        md_lines.append(f"**Documents Analyzed:** {report_data['documents_analyzed']}")
        md_lines.append("")

        # Summary section
        summary = report_data["summary"]
        md_lines.append("## 📊 Summary")
        md_lines.append("")
        md_lines.append(f"- **Total Recommendations:** {summary['total_recommendations']}")
        md_lines.append(f"- **Recommendation Types:** {', '.join(summary['recommendation_types'])}")
        md_lines.append("")

        # Priority breakdown
        priority = summary["priority_breakdown"]
        md_lines.append("### Priority Breakdown")
        md_lines.append("")
        md_lines.append(f"- 🔴 **High Priority:** {priority['high']}")
        md_lines.append(f"- 🟡 **Medium Priority:** {priority['medium']}")
        md_lines.append(f"- 🟢 **Low Priority:** {priority['low']}")
        md_lines.append("")

        # Recommendations section
        md_lines.append("## 💡 Recommendations")
        md_lines.append("")

        for i, rec in enumerate(report_data["recommendations"], 1):
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.get("priority", "medium"), "🟡")
            md_lines.append(f"### {i}. {priority_emoji} {rec['description']}")
            md_lines.append("")
            md_lines.append(f"**Type:** {rec.get('type', 'unknown').title()}")
            md_lines.append(f"**Priority:** {rec.get('priority', 'medium').title()}")
            md_lines.append(f"**Rationale:** {rec.get('rationale', 'N/A')}")
            md_lines.append(f"**Impact:** {rec.get('expected_impact', 'N/A')}")
            md_lines.append(f"**Effort:** {rec.get('effort_level', 'medium').title()}")
            md_lines.append("")

            if rec.get("affected_documents"):
                md_lines.append("**Affected Documents:**")
                for doc_id in rec["affected_documents"]:
                    md_lines.append(f"- {doc_id}")
                md_lines.append("")

            if rec.get("tags"):
                md_lines.append(f"**Tags:** {', '.join(rec['tags'])}")
                md_lines.append("")

            md_lines.append("---")
            md_lines.append("")

        return "\n".join(md_lines)

    async def _save_to_doc_store(self, document: Dict[str, Any]) -> None:
        """Save document to doc-store."""
        try:
            doc_store_url = self.service_urls.get("doc_store", "http://localhost:5000")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{doc_store_url}/api/documents",
                    json=document,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code not in [200, 201]:
                    print(f"Failed to save to doc-store: {response.status_code} - {response.text}")

        except Exception as e:
            print(f"Error saving to doc-store: {e}")

    async def _save_markdown_report(self, md_content: str, report_id: str) -> None:
        """Save Markdown report to reports directory."""
        try:
            # Save to doc-store as markdown document
            md_document = {
                "id": f"{report_id}_md",
                "type": "recommendations_report_md",
                "title": f"Recommendations Report (Markdown) - {report_id}",
                "content": md_content,
                "format": "markdown",
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "parent_report_id": report_id,
                    "format": "markdown",
                    "report_type": "simulation_recommendations"
                }
            }

            await self._save_to_doc_store(md_document)

        except Exception as e:
            print(f"Error saving markdown report: {e}")

    async def _link_report_to_simulation(self, report_id: str, simulation_id: str) -> None:
        """Link the recommendations report to the simulation run data."""
        try:
            # Update simulation run data with report linkage
            simulation_repo = self._get_simulation_repository()

            # Get the simulation run
            simulation = await simulation_repo.find_by_id(simulation_id)
            if simulation:
                # Add report linkage to simulation metadata
                if not hasattr(simulation, 'metadata') or simulation.metadata is None:
                    simulation.metadata = {}

                simulation.metadata['recommendations_report_id'] = report_id
                simulation.metadata['recommendations_report_timestamp'] = datetime.now().isoformat()

                # Save updated simulation
                await simulation_repo.save(simulation)

                print(f"Linked recommendations report {report_id} to simulation {simulation_id}")
            else:
                print(f"Simulation {simulation_id} not found for linking report")

        except Exception as e:
            print(f"Error linking report to simulation: {e}")

    async def _store_received_analysis_report(self, analysis_report: Dict[str, Any], simulation_id: str) -> str:
        """Store a pre-generated analysis report from analysis-service."""
        try:
            # Use the report ID from the analysis-service or generate one
            report_id = analysis_report.get("report_id", f"analysis_report_{simulation_id}_{int(datetime.now().timestamp())}")

            # Store JSON version in doc-store
            json_content = {
                "id": report_id,
                "type": "analysis_report",
                "simulation_id": simulation_id,
                "title": f"Analysis Report - {simulation_id}",
                "content": json.dumps(analysis_report, indent=2),
                "format": "json",
                "timestamp": analysis_report.get("timestamp", datetime.now().isoformat()),
                "metadata": {
                    "source": "analysis-service",
                    "report_type": "simulation_analysis",
                    "documents_analyzed": analysis_report.get("documents_analyzed", 0),
                    **analysis_report.get("metadata", {})
                }
            }

            # Store in doc-store
            await self._save_to_doc_store(json_content)

            # Store Markdown version if provided by analysis-service
            if analysis_report.get("markdown_content"):
                await self._save_markdown_report(analysis_report["markdown_content"], report_id)
            elif analysis_report.get("markdown"):
                await self._save_markdown_report(analysis_report["markdown"], report_id)

            # Link to simulation run data
            await self._link_analysis_report_to_simulation(report_id, simulation_id)

            return report_id

        except Exception as e:
            print(f"Error storing received analysis report: {e}")
            raise


    async def _link_analysis_report_to_simulation(self, report_id: str, simulation_id: str) -> None:
        """Link the analysis report to the simulation run data."""
        try:
            # Update simulation run data with analysis report linkage
            simulation_repo = self._get_simulation_repository()

            # Get the simulation run
            simulation = await simulation_repo.find_by_id(simulation_id)
            if simulation:
                # Add analysis report linkage to simulation metadata
                if not hasattr(simulation, 'metadata') or simulation.metadata is None:
                    simulation.metadata = {}

                simulation.metadata['analysis_report_id'] = report_id
                simulation.metadata['analysis_report_timestamp'] = datetime.now().isoformat()

                # Save updated simulation
                await simulation_repo.save(simulation)

                print(f"Linked analysis report {report_id} to simulation {simulation_id}")
            else:
                print(f"Simulation {simulation_id} not found for linking analysis report")

        except Exception as e:
            print(f"Error linking analysis report to simulation: {e}")

    def _get_simulation_repository(self):
        """Get simulation repository instance."""
        # This would be injected via DI in a real implementation
        from simulation.infrastructure.repositories.sqlite_repositories import SQLiteSimulationRepository
        return SQLiteSimulationRepository()

    # ============================================================================
    # TIMELINE-BASED DOCUMENT PLACEMENT
    # ============================================================================

    async def place_documents_on_timeline(self, simulation_id: str, documents: List[Dict[str, Any]], timeline: Dict[str, Any]) -> Dict[str, Any]:
        """Place documents on the simulation timeline based on timestamps and relevance.

        This method organizes documents chronologically within the simulation timeline,
        associating them with relevant phases and milestones based on their creation/update dates
        and content analysis.
        """
        try:
            # Parse timeline phases
            timeline_phases = []
            if "phases" in timeline:
                for phase_data in timeline["phases"]:
                    phase = {
                        "id": phase_data.get("id", ""),
                        "name": phase_data.get("name", ""),
                        "start_date": phase_data.get("start_date"),
                        "end_date": phase_data.get("end_date"),
                        "planned_end_date": phase_data.get("planned_end_date"),
                        "status": phase_data.get("status", "pending")
                    }
                    timeline_phases.append(phase)

            # Analyze document timestamps and place on timeline
            document_placements = await self._analyze_document_timestamps(documents, timeline_phases)

            # Group documents by timeline phases
            phase_documents = self._group_documents_by_phases(document_placements, timeline_phases)

            # Generate timeline placement report
            placement_report = await self._generate_timeline_placement_report(simulation_id, phase_documents, timeline_phases)

            return {
                "simulation_id": simulation_id,
                "timeline_phases": len(timeline_phases),
                "total_documents": len(documents),
                "placed_documents": len(document_placements),
                "phase_breakdown": phase_documents,
                "placement_report": placement_report
            }

        except Exception as e:
            print(f"Error placing documents on timeline: {e}")
            return {
                "simulation_id": simulation_id,
                "error": str(e),
                "timeline_phases": 0,
                "total_documents": len(documents),
                "placed_documents": 0
            }

    async def _analyze_document_timestamps(self, documents: List[Dict[str, Any]], timeline_phases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze document timestamps and determine timeline placement."""

        placements = []

        for doc in documents:
            try:
                # Extract timestamp information
                created_date = None
                updated_date = None

                # Try to parse dateCreated and dateUpdated fields
                if "dateCreated" in doc:
                    created_date = self._parse_timestamp(doc["dateCreated"])
                if "dateUpdated" in doc:
                    updated_date = self._parse_timestamp(doc["dateUpdated"])

                # Use updated_date if available, otherwise created_date
                primary_date = updated_date or created_date

                if not primary_date:
                    # Skip documents without timestamp information
                    continue

                # Find the most relevant timeline phase
                relevant_phase = self._find_relevant_timeline_phase(primary_date, timeline_phases)

                if relevant_phase:
                    placement = {
                        "document_id": doc.get("id", ""),
                        "title": doc.get("title", ""),
                        "type": doc.get("type", ""),
                        "primary_date": primary_date.isoformat(),
                        "created_date": created_date.isoformat() if created_date else None,
                        "updated_date": updated_date.isoformat() if updated_date else None,
                        "timeline_phase": relevant_phase["id"],
                        "phase_name": relevant_phase["name"],
                        "placement_reason": self._determine_placement_reason(primary_date, relevant_phase),
                        "relevance_score": self._calculate_timeline_relevance(primary_date, relevant_phase)
                    }
                    placements.append(placement)

            except Exception as e:
                print(f"Error analyzing timestamps for document {doc.get('id', 'unknown')}: {e}")
                continue

        return placements

    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string into datetime object."""
        from datetime import datetime

        if not timestamp_str:
            return None

        try:
            # Try ISO format first
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass

        # Try common timestamp formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y"
        ]

        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue

        print(f"Could not parse timestamp: {timestamp_str}")
        return None

    def _find_relevant_timeline_phase(self, doc_date: datetime, timeline_phases: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the most relevant timeline phase for a document date."""
        if not timeline_phases:
            return None

        # Find phases that overlap with the document date
        relevant_phases = []

        for phase in timeline_phases:
            start_date = self._parse_timestamp(phase.get("start_date"))
            end_date = self._parse_timestamp(phase.get("end_date")) or self._parse_timestamp(phase.get("planned_end_date"))

            if start_date and end_date:
                if start_date <= doc_date <= end_date:
                    relevant_phases.append(phase)

        # If no overlapping phases, find the closest phase
        if not relevant_phases:
            closest_phase = None
            min_distance = float('inf')

            for phase in timeline_phases:
                start_date = self._parse_timestamp(phase.get("start_date"))
                if start_date:
                    distance = abs((doc_date - start_date).days)
                    if distance < min_distance:
                        min_distance = distance
                        closest_phase = phase

            if closest_phase and min_distance <= 30:  # Within 30 days
                relevant_phases.append(closest_phase)

        # Return the most relevant phase (prefer in-progress phases)
        for phase in relevant_phases:
            if phase.get("status") == "in_progress":
                return phase

        return relevant_phases[0] if relevant_phases else None

    def _determine_placement_reason(self, doc_date: datetime, phase: Dict[str, Any]) -> str:
        """Determine why a document was placed in a particular timeline phase."""
        start_date = self._parse_timestamp(phase.get("start_date"))
        end_date = self._parse_timestamp(phase.get("end_date")) or self._parse_timestamp(phase.get("planned_end_date"))

        if start_date and end_date:
            if start_date <= doc_date <= end_date:
                return "within_phase_dates"
            elif doc_date < start_date:
                days_before = (start_date - doc_date).days
                return f"before_phase_start_{days_before}_days"
            else:
                days_after = (doc_date - end_date).days
                return f"after_phase_end_{days_after}_days"

        return "closest_phase_match"

    def _calculate_timeline_relevance(self, doc_date: datetime, phase: Dict[str, Any]) -> float:
        """Calculate how relevant a document is to a timeline phase."""
        start_date = self._parse_timestamp(phase.get("start_date"))
        end_date = self._parse_timestamp(phase.get("end_date")) or self._parse_timestamp(phase.get("planned_end_date"))

        if not start_date:
            return 0.0

        # Perfect match if within phase dates
        if end_date and start_date <= doc_date <= end_date:
            return 1.0

        # Calculate distance-based relevance
        if doc_date < start_date:
            days_before = (start_date - doc_date).days
            return max(0.0, 1.0 - (days_before / 30.0))  # Decrease relevance with distance
        elif end_date:
            days_after = (doc_date - end_date).days
            return max(0.0, 1.0 - (days_after / 30.0))  # Decrease relevance with distance

        return 0.5  # Default relevance

    def _group_documents_by_phases(self, document_placements: List[Dict[str, Any]], timeline_phases: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Group documents by timeline phases."""
        phase_groups = {}

        # Initialize phase groups
        for phase in timeline_phases:
            phase_groups[phase["id"]] = {
                "phase_name": phase["name"],
                "documents": [],
                "document_count": 0,
                "avg_relevance": 0.0,
                "date_range": {
                    "start": phase.get("start_date"),
                    "end": phase.get("end_date") or phase.get("planned_end_date")
                }
            }

        # Group documents
        for placement in document_placements:
            phase_id = placement["timeline_phase"]
            if phase_id in phase_groups:
                phase_groups[phase_id]["documents"].append(placement)
                phase_groups[phase_id]["document_count"] += 1

        # Calculate average relevance for each phase
        for phase_id, phase_data in phase_groups.items():
            if phase_data["documents"]:
                total_relevance = sum(doc["relevance_score"] for doc in phase_data["documents"])
                phase_data["avg_relevance"] = total_relevance / len(phase_data["documents"])

        return phase_groups

    async def _generate_timeline_placement_report(self, simulation_id: str, phase_documents: Dict[str, Dict[str, Any]], timeline_phases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive timeline placement report."""
        try:
            # Calculate summary statistics
            total_documents = sum(phase["document_count"] for phase in phase_documents.values())
            phases_with_documents = sum(1 for phase in phase_documents.values() if phase["document_count"] > 0)

            # Find best and worst performing phases
            phase_performance = []
            for phase_id, phase_data in phase_documents.items():
                if phase_data["document_count"] > 0:
                    performance = {
                        "phase_id": phase_id,
                        "phase_name": phase_data["phase_name"],
                        "document_count": phase_data["document_count"],
                        "avg_relevance": phase_data["avg_relevance"]
                    }
                    phase_performance.append(performance)

            # Sort by relevance
            phase_performance.sort(key=lambda x: x["avg_relevance"], reverse=True)

            report = {
                "simulation_id": simulation_id,
                "total_phases": len(timeline_phases),
                "phases_with_documents": phases_with_documents,
                "total_documents_placed": total_documents,
                "phase_performance": phase_performance,
                "timeline_coverage": phases_with_documents / len(timeline_phases) if timeline_phases else 0,
                "recommendations": self._generate_timeline_recommendations(phase_documents, timeline_phases)
            }

            return report

        except Exception as e:
            print(f"Error generating timeline placement report: {e}")
            return {
                "simulation_id": simulation_id,
                "error": str(e),
                "total_documents_placed": 0
            }

    def _generate_timeline_recommendations(self, phase_documents: Dict[str, Dict[str, Any]], timeline_phases: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on timeline document placement."""
        recommendations = []

        # Check for phases with no documents
        empty_phases = []
        for phase_id, phase_data in phase_documents.items():
            if phase_data["document_count"] == 0:
                phase = next((p for p in timeline_phases if p["id"] == phase_id), None)
                if phase:
                    empty_phases.append(phase["name"])

        if empty_phases:
            recommendations.append(f"Consider adding documentation for phases: {', '.join(empty_phases[:3])}")

        # Check for phases with low relevance scores
        low_relevance_phases = []
        for phase_id, phase_data in phase_documents.items():
            if phase_data["document_count"] > 0 and phase_data["avg_relevance"] < 0.5:
                low_relevance_phases.append(phase_data["phase_name"])

        if low_relevance_phases:
            recommendations.append(f"Review document placement for phases with low relevance: {', '.join(low_relevance_phases[:3])}")

        # Check timeline coverage
        coverage = sum(1 for phase in phase_documents.values() if phase["document_count"] > 0) / len(phase_documents) if phase_documents else 0

        if coverage < 0.5:
            recommendations.append("Timeline coverage is low. Consider expanding documentation across more phases.")

        if not recommendations:
            recommendations.append("Timeline document placement looks good with adequate coverage and relevance.")

        return recommendations

    # ============================================================================
    # COMPREHENSIVE SUMMARY REPORT GENERATION
    # ============================================================================

    async def generate_comprehensive_summary_report(self, simulation_id: str, documents: List[Dict[str, Any]], timeline: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate a comprehensive summary report combining recommendations and analysis.

        This method creates a unified report that combines:
        - Recommendations from summarizer-hub
        - Analysis reports from analysis-service
        - Timeline placement analysis
        - Executive summary and actionable insights

        This keeps the simulation service pure by orchestrating report generation
        across multiple specialized services.
        """
        try:
            print(f"Generating comprehensive summary report for simulation {simulation_id}")

            # Step 1: Get recommendations from summarizer-hub
            recommendations_report = await self._get_recommendations_report_from_summarizer_hub(simulation_id, documents)

            # Step 2: Get analysis report from analysis-service
            analysis_report = await self._get_analysis_report_from_analysis_service(simulation_id, documents)

            # Step 3: Generate timeline placement if timeline provided
            timeline_placement = None
            if timeline:
                timeline_placement = await self.place_documents_on_timeline(simulation_id, documents, timeline)

            # Step 4: Combine all reports into comprehensive summary
            comprehensive_report = await self._combine_reports_into_summary(
                simulation_id,
                recommendations_report,
                analysis_report,
                timeline_placement,
                documents
            )

            # Step 5: Store the comprehensive report
            await self._store_comprehensive_summary_report(simulation_id, comprehensive_report)

            return {
                "simulation_id": simulation_id,
                "report_generated": True,
                "comprehensive_report_id": comprehensive_report.get("report_id"),
                "sections_included": list(comprehensive_report.keys()),
                "total_documents": len(documents),
                "processing_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error generating comprehensive summary report: {e}")
            return {
                "simulation_id": simulation_id,
                "error": str(e),
                "report_generated": False
            }

    async def _get_recommendations_report_from_summarizer_hub(self, simulation_id: str, documents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get recommendations report from summarizer-hub service."""
        try:
            # Prepare documents for summarizer-hub
            docs_for_analysis = []
            for doc in documents:
                if "content" in doc and doc["content"]:
                    docs_for_analysis.append({
                        "id": doc.get("id", ""),
                        "content": doc["content"],
                        "title": doc.get("title", ""),
                        "type": doc.get("type", "document")
                    })

            if not docs_for_analysis:
                return None

            # Request recommendations from summarizer-hub
            recommendations_result = await self._request_recommendations_from_summarizer_hub(simulation_id, docs_for_analysis)

            if recommendations_result:
                return {
                    "source": "summarizer-hub",
                    "recommendations": recommendations_result.get("recommendations", []),
                    "consolidation_suggestions": recommendations_result.get("consolidation_suggestions", []),
                    "duplicate_analysis": recommendations_result.get("duplicate_analysis", []),
                    "outdated_analysis": recommendations_result.get("outdated_analysis", []),
                    "quality_improvements": recommendations_result.get("quality_improvements", [])
                }

            return None

        except Exception as e:
            print(f"Error getting recommendations from summarizer-hub: {e}")
            return None

    async def _get_analysis_report_from_analysis_service(self, simulation_id: str, documents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get analysis report from analysis-service."""
        try:
            # Prepare documents for analysis-service
            docs_for_analysis = []
            for doc in documents:
                if "content" in doc and doc["content"]:
                    docs_for_analysis.append({
                        "id": doc.get("id", ""),
                        "content": doc["content"],
                        "title": doc.get("title", ""),
                        "type": doc.get("type", "document")
                    })

            if not docs_for_analysis:
                return None

            # Request analysis from analysis-service
            analysis_result = await self._request_analysis_report_from_service(simulation_id, docs_for_analysis)

            if analysis_result:
                return {
                    "source": "analysis-service",
                    "quality_analysis": analysis_result.get("report", {}).get("analysis_results", []),
                    "summary_statistics": analysis_result.get("report", {}).get("summary", {}),
                    "processing_metadata": {
                        "documents_processed": analysis_result.get("documents_processed", 0),
                        "processing_time": analysis_result.get("processing_time", "completed")
                    }
                }

            return None

        except Exception as e:
            print(f"Error getting analysis from analysis-service: {e}")
            return None

    async def _combine_reports_into_summary(self, simulation_id: str, recommendations: Optional[Dict], analysis: Optional[Dict], timeline: Optional[Dict], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine all reports into a comprehensive summary."""
        try:
            # Generate unique report ID
            report_id = f"comprehensive_summary_{simulation_id}_{int(datetime.now().timestamp())}"

            # Executive Summary
            executive_summary = self._generate_executive_summary(recommendations, analysis, timeline, documents)

            # Detailed Sections
            summary_report = {
                "report_id": report_id,
                "simulation_id": simulation_id,
                "generated_at": datetime.now().isoformat(),
                "executive_summary": executive_summary,
                "sections": {}
            }

            # Add recommendations section
            if recommendations:
                summary_report["sections"]["recommendations"] = {
                    "source": recommendations["source"],
                    "total_recommendations": len(recommendations.get("recommendations", [])),
                    "consolidation_opportunities": len(recommendations.get("consolidation_suggestions", [])),
                    "duplicate_issues": len(recommendations.get("duplicate_analysis", [])),
                    "outdated_documents": len(recommendations.get("outdated_analysis", [])),
                    "quality_improvements": len(recommendations.get("quality_improvements", [])),
                    "details": recommendations
                }

            # Add analysis section
            if analysis:
                summary_report["sections"]["analysis"] = {
                    "source": analysis["source"],
                    "documents_analyzed": analysis["processing_metadata"]["documents_processed"],
                    "average_quality_score": analysis["summary_statistics"].get("average_quality_score", 0),
                    "documents_with_issues": analysis["summary_statistics"].get("documents_with_issues", 0),
                    "total_issues_found": analysis["summary_statistics"].get("total_issues_found", 0),
                    "details": analysis
                }

            # Add timeline section
            if timeline:
                summary_report["sections"]["timeline"] = {
                    "total_phases": timeline.get("timeline_phases", 0),
                    "documents_placed": timeline.get("placed_documents", 0),
                    "timeline_coverage": timeline.get("placement_report", {}).get("timeline_coverage", 0),
                    "phase_breakdown": timeline.get("phase_breakdown", {}),
                    "recommendations": timeline.get("placement_report", {}).get("recommendations", []),
                    "details": timeline
                }

            # Overall Assessment
            summary_report["overall_assessment"] = self._generate_overall_assessment(summary_report["sections"])

            # Action Items
            summary_report["action_items"] = self._generate_action_items(summary_report["sections"])

            return summary_report

        except Exception as e:
            print(f"Error combining reports into summary: {e}")
            return {
                "report_id": f"error_{simulation_id}_{int(datetime.now().timestamp())}",
                "simulation_id": simulation_id,
                "error": str(e),
                "sections": {}
            }

    def _generate_executive_summary(self, recommendations: Optional[Dict], analysis: Optional[Dict], timeline: Optional[Dict], documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate executive summary from all report data."""
        summary = {
            "total_documents": len(documents),
            "processing_completed": datetime.now().isoformat(),
            "key_findings": [],
            "critical_issues": 0,
            "improvement_opportunities": 0
        }

        # Analyze recommendations
        if recommendations:
            rec_count = len(recommendations.get("recommendations", []))
            summary["improvement_opportunities"] += rec_count
            summary["key_findings"].append(f"Found {rec_count} recommendation opportunities")

            # Check for critical recommendations
            for rec in recommendations.get("recommendations", []):
                if rec.get("priority", "").lower() in ["critical", "high"]:
                    summary["critical_issues"] += 1

        # Analyze quality metrics
        if analysis:
            avg_quality = analysis["summary_statistics"].get("average_quality_score", 0)
            issues_count = analysis["summary_statistics"].get("total_issues_found", 0)

            if avg_quality < 0.6:
                summary["key_findings"].append(f"Low average quality score: {avg_quality:.2f}")
                summary["critical_issues"] += 1
            elif avg_quality < 0.8:
                summary["key_findings"].append(f"Moderate quality score: {avg_quality:.2f}")

            if issues_count > 0:
                summary["key_findings"].append(f"Identified {issues_count} quality issues")

        # Analyze timeline coverage
        if timeline:
            coverage = timeline.get("placement_report", {}).get("timeline_coverage", 0)
            placed_docs = timeline.get("placed_documents", 0)

            if coverage < 0.5:
                summary["key_findings"].append(f"Poor timeline coverage: {coverage:.1%}")
            elif coverage < 0.8:
                summary["key_findings"].append(f"Moderate timeline coverage: {coverage:.1%}")
            else:
                summary["key_findings"].append(f"Good timeline coverage: {coverage:.1%}")

            summary["key_findings"].append(f"Placed {placed_docs} documents on timeline")

        # Default findings if no data
        if not summary["key_findings"]:
            summary["key_findings"].append("Analysis completed - no significant issues found")

        return summary

    def _generate_overall_assessment(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall assessment from all sections."""
        assessment = {
            "overall_health_score": 0.0,
            "risk_level": "unknown",
            "strengths": [],
            "weaknesses": [],
            "recommendations": []
        }

        scores = []
        risk_factors = 0

        # Assess recommendations section
        if "recommendations" in sections:
            rec_section = sections["recommendations"]
            rec_score = max(0, 1.0 - (rec_section["total_recommendations"] / 20.0))  # Normalize
            scores.append(rec_score)

            if rec_section["total_recommendations"] > 10:
                risk_factors += 1
                assessment["weaknesses"].append("High number of recommendations indicates significant improvement needs")
            else:
                assessment["strengths"].append("Manageable number of recommendations")

        # Assess analysis section
        if "analysis" in sections:
            analysis_section = sections["analysis"]
            quality_score = analysis_section["average_quality_score"]
            scores.append(quality_score)

            if quality_score < 0.6:
                risk_factors += 1
                assessment["weaknesses"].append("Low document quality scores")
            elif quality_score > 0.8:
                assessment["strengths"].append("High document quality standards")

            if analysis_section["documents_with_issues"] > 0:
                assessment["recommendations"].append("Address identified quality issues")

        # Assess timeline section
        if "timeline" in sections:
            timeline_section = sections["timeline"]
            coverage = timeline_section["timeline_coverage"]
            scores.append(coverage)

            if coverage < 0.5:
                risk_factors += 1
                assessment["weaknesses"].append("Poor timeline coverage")
            elif coverage > 0.8:
                assessment["strengths"].append("Good timeline coverage")

        # Calculate overall score
        if scores:
            assessment["overall_health_score"] = sum(scores) / len(scores)

            # Determine risk level
            if assessment["overall_health_score"] > 0.8:
                assessment["risk_level"] = "low"
            elif assessment["overall_health_score"] > 0.6:
                assessment["risk_level"] = "medium"
            else:
                assessment["risk_level"] = "high"

        return assessment

    def _generate_action_items(self, sections: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized action items from all sections."""
        action_items = []

        # Extract from recommendations
        if "recommendations" in sections:
            rec_section = sections["recommendations"]
            for rec in rec_section["details"].get("recommendations", []):
                action_items.append({
                    "type": "recommendation",
                    "priority": rec.get("priority", "medium"),
                    "description": rec.get("description", ""),
                    "category": rec.get("type", "general"),
                    "estimated_effort": rec.get("estimated_effort", "medium")
                })

        # Extract from analysis issues
        if "analysis" in sections:
            analysis_section = sections["analysis"]
            for result in analysis_section["details"].get("quality_analysis", []):
                if result.get("issues_found", 0) > 0:
                    action_items.append({
                        "type": "quality_fix",
                        "priority": "high" if result.get("quality_score", 0) < 0.5 else "medium",
                        "description": f"Fix quality issues in document {result.get('document_id', '')}",
                        "category": "quality",
                        "estimated_effort": "low" if len(result.get("issues", [])) <= 2 else "medium"
                    })

        # Extract from timeline recommendations
        if "timeline" in sections:
            timeline_section = sections["timeline"]
            for rec in timeline_section.get("recommendations", []):
                action_items.append({
                    "type": "timeline_optimization",
                    "priority": "medium",
                    "description": rec,
                    "category": "organization",
                    "estimated_effort": "low"
                })

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        action_items.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return action_items[:10]  # Return top 10 action items

    async def _store_comprehensive_summary_report(self, simulation_id: str, report: Dict[str, Any]) -> None:
        """Store the comprehensive summary report in doc-store."""
        try:
            # Generate JSON report content
            json_content = json.dumps(report, indent=2, default=str)

            # Generate Markdown report content
            markdown_content = self._generate_comprehensive_markdown_report(report)

            # Store JSON version
            json_doc_id = f"{report['report_id']}_json"
            await self._store_document_in_doc_store(json_doc_id, json_content, "json", "comprehensive_summary")

            # Store Markdown version
            md_doc_id = f"{report['report_id']}_md"
            await self._store_document_in_doc_store(md_doc_id, markdown_content, "markdown", "comprehensive_summary")

            # Link reports to simulation
            await self._link_report_to_simulation(simulation_id, report['report_id'], "comprehensive_summary")

            print(f"Stored comprehensive summary report for simulation {simulation_id}")

        except Exception as e:
            print(f"Error storing comprehensive summary report: {e}")

    def _generate_comprehensive_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate comprehensive Markdown report."""
        md_lines = []

        # Header
        md_lines.append("# 📊 Comprehensive Simulation Summary Report")
        md_lines.append("")
        md_lines.append(f"**Simulation ID:** {report['simulation_id']}")
        md_lines.append(f"**Report ID:** {report['report_id']}")
        md_lines.append(f"**Generated:** {report['generated_at']}")
        md_lines.append("")

        # Executive Summary
        exec_summary = report.get("executive_summary", {})
        md_lines.append("## 📈 Executive Summary")
        md_lines.append("")
        md_lines.append(f"- **Total Documents:** {exec_summary.get('total_documents', 0)}")
        md_lines.append(f"- **Critical Issues:** {exec_summary.get('critical_issues', 0)}")
        md_lines.append(f"- **Improvement Opportunities:** {exec_summary.get('improvement_opportunities', 0)}")
        md_lines.append("")

        if exec_summary.get("key_findings"):
            md_lines.append("### Key Findings")
            md_lines.append("")
            for finding in exec_summary["key_findings"]:
                md_lines.append(f"- {finding}")
            md_lines.append("")

        # Overall Assessment
        assessment = report.get("overall_assessment", {})
        md_lines.append("## 🎯 Overall Assessment")
        md_lines.append("")
        health_score = assessment.get("overall_health_score", 0)
        risk_level = assessment.get("risk_level", "unknown")

        # Health score indicator
        if health_score >= 0.8:
            health_indicator = "🟢 **Excellent**"
        elif health_score >= 0.6:
            health_indicator = "🟡 **Good**"
        else:
            health_indicator = "🔴 **Needs Attention**"

        md_lines.append(f"**Health Score:** {health_indicator} ({health_score:.2f})")
        md_lines.append(f"**Risk Level:** {risk_level.title()}")
        md_lines.append("")

        if assessment.get("strengths"):
            md_lines.append("### Strengths")
            for strength in assessment["strengths"]:
                md_lines.append(f"- ✅ {strength}")
            md_lines.append("")

        if assessment.get("weaknesses"):
            md_lines.append("### Areas for Improvement")
            for weakness in assessment["weaknesses"]:
                md_lines.append(f"- ⚠️ {weakness}")
            md_lines.append("")

        # Detailed Sections
        sections = report.get("sections", {})

        # Recommendations Section
        if "recommendations" in sections:
            rec_section = sections["recommendations"]
            md_lines.append("## 💡 Recommendations")
            md_lines.append("")
            md_lines.append(f"**Total Recommendations:** {rec_section['total_recommendations']}")
            md_lines.append(f"**Consolidation Opportunities:** {rec_section['consolidation_opportunities']}")
            md_lines.append(f"**Duplicate Issues:** {rec_section['duplicate_issues']}")
            md_lines.append(f"**Outdated Documents:** {rec_section['outdated_documents']}")
            md_lines.append(f"**Quality Improvements:** {rec_section['quality_improvements']}")
            md_lines.append("")

        # Analysis Section
        if "analysis" in sections:
            analysis_section = sections["analysis"]
            md_lines.append("## 🔍 Quality Analysis")
            md_lines.append("")
            md_lines.append(f"**Documents Analyzed:** {analysis_section['documents_analyzed']}")
            md_lines.append(f"**Average Quality Score:** {analysis_section['average_quality_score']:.2f}")
            md_lines.append(f"**Documents with Issues:** {analysis_section['documents_with_issues']}")
            md_lines.append(f"**Total Issues Found:** {analysis_section['total_issues_found']}")
            md_lines.append("")

        # Timeline Section
        if "timeline" in sections:
            timeline_section = sections["timeline"]
            md_lines.append("## 📅 Timeline Analysis")
            md_lines.append("")
            md_lines.append(f"**Total Phases:** {timeline_section['total_phases']}")
            md_lines.append(f"**Documents Placed:** {timeline_section['documents_placed']}")
            md_lines.append(f"**Timeline Coverage:** {timeline_section['timeline_coverage']:.1%}")
            md_lines.append("")

            if timeline_section.get("recommendations"):
                md_lines.append("### Timeline Recommendations")
                for rec in timeline_section["recommendations"]:
                    md_lines.append(f"- {rec}")
                md_lines.append("")

        # Action Items
        action_items = report.get("action_items", [])
        if action_items:
            md_lines.append("## ✅ Action Items")
            md_lines.append("")

            for i, item in enumerate(action_items[:10], 1):  # Top 10
                priority_emoji = {
                    "critical": "🚨",
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }.get(item.get("priority", "medium"), "🟡")

                md_lines.append(f"{i}. {priority_emoji} **{item.get('priority', 'medium').title()}** - {item.get('description', '')}")
                md_lines.append(f"   - Category: {item.get('category', 'general')}")
                md_lines.append(f"   - Effort: {item.get('estimated_effort', 'medium')}")
                md_lines.append("")

        # Footer
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("*Report generated by Simulation Service - Comprehensive Analysis*")
        md_lines.append(f"*Processing completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(md_lines)

    # ============================================================================
    # PULL REQUEST ANALYSIS VIA ANALYSIS SERVICE
    # ============================================================================

    async def analyze_pull_request(self, simulation_id: str, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze pull request changes via the analysis service.

        This method delegates PR analysis to the specialized analysis service,
        maintaining clean separation of concerns and leveraging the analysis
        service's comprehensive PR analysis capabilities.

        Args:
            simulation_id: Unique identifier for the simulation
            pr_data: Pull request data including files, commits, and metadata

        Returns:
            Comprehensive analysis report from analysis service
        """
        try:
            print(f"Delegating PR analysis to analysis service for simulation {simulation_id}")

            # Prepare request for analysis service
            analysis_request = {
                "simulation_id": simulation_id,
                "pull_request": pr_data
            }

            # Call analysis service PR analysis endpoint
            analysis_result = await self._request_pr_analysis_from_service(simulation_id, analysis_request)

            if analysis_result:
                # Store the PR analysis report in doc-store
                await self._store_pr_analysis_report_from_service(simulation_id, analysis_result)

                return {
                    "simulation_id": simulation_id,
                    "analysis_completed": True,
                    "pr_health_score": analysis_result.get("health_score", 0),
                    "risk_level": analysis_result.get("risk_level", "unknown"),
                    "refactoring_suggestions_count": len(analysis_result.get("refactoring_suggestions", [])),
                    "recommendations_count": len(analysis_result.get("recommendations", []))
                }
            else:
                return {
                    "simulation_id": simulation_id,
                    "analysis_completed": False,
                    "error": "Failed to get analysis from analysis service"
                }

        except Exception as e:
            print(f"Error analyzing pull request: {e}")
            return {
                "simulation_id": simulation_id,
                "analysis_completed": False,
                "error": str(e)
            }

    async def _request_pr_analysis_from_service(self, simulation_id: str, analysis_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Request PR analysis from the analysis service."""
        try:
            analysis_service_url = self.service_urls.get('analysis_service', 'http://localhost:5020')

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{analysis_service_url}/analyze/pull-request",
                    json=analysis_request,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        return result.get("data")
                    else:
                        print(f"Analysis service returned error: {result}")
                        return None
                else:
                    print(f"Analysis service request failed with status {response.status_code}: {response.text}")
                    return None

        except Exception as e:
            print(f"Error calling analysis service for PR analysis: {e}")
            return None

    async def _store_pr_analysis_report_from_service(self, simulation_id: str, analysis_result: Dict[str, Any]) -> None:
        """Store PR analysis report received from analysis service."""
        try:
            # Store the analysis result in doc-store
            json_content = json.dumps(analysis_result, indent=2, default=str)

            # Generate a simple markdown summary
            markdown_content = self._generate_pr_analysis_summary_markdown(analysis_result)

            # Store JSON version
            json_doc_id = f"pr_analysis_{simulation_id}_{int(datetime.now().timestamp())}_json"
            await self._store_document_in_doc_store(json_doc_id, json_content, "json", "pr_analysis")

            # Store Markdown version
            md_doc_id = f"pr_analysis_{simulation_id}_{int(datetime.now().timestamp())}_md"
            await self._store_document_in_doc_store(md_doc_id, markdown_content, "markdown", "pr_analysis")

            # Link reports to simulation
            await self._link_report_to_simulation(simulation_id, json_doc_id, "pr_analysis")

            print(f"Stored PR analysis report from analysis service for simulation {simulation_id}")

        except Exception as e:
            print(f"Error storing PR analysis report from service: {e}")

    def _generate_pr_analysis_summary_markdown(self, analysis_result: Dict[str, Any]) -> str:
        """Generate a summary markdown report for PR analysis."""
        md_lines = []

        # Header
        md_lines.append("# 🔍 Pull Request Analysis Summary")
        md_lines.append("")
        md_lines.append(f"**Simulation ID:** {analysis_result.get('simulation_id', 'N/A')}")
        md_lines.append(f"**PR Title:** {analysis_result.get('pr_title', 'N/A')}")
        md_lines.append(f"**Author:** {analysis_result.get('pr_author', 'N/A')}")
        md_lines.append(f"**Analysis Date:** {analysis_result.get('analysis_timestamp', 'N/A')}")
        md_lines.append("")

        # Health Score
        health_score = analysis_result.get("health_score", 0)
        risk_level = analysis_result.get("risk_level", "unknown")

        if health_score >= 0.8:
            health_indicator = "🟢 **Good**"
        elif health_score >= 0.6:
            health_indicator = "🟡 **Needs Attention**"
        else:
            health_indicator = "🔴 **High Risk**"

        md_lines.append("## 📊 Health Assessment")
        md_lines.append("")
        md_lines.append(f"**Overall Health Score:** {health_indicator} ({health_score:.2f})")
        md_lines.append(f"**Risk Level:** {risk_level.title()}")
        md_lines.append(f"**Files Analyzed:** {analysis_result.get('files_analyzed', 0)}")
        md_lines.append(f"**Commits Analyzed:** {analysis_result.get('commits_analyzed', 0)}")
        md_lines.append("")

        # Refactoring Suggestions Count
        refactoring_count = len(analysis_result.get("refactoring_suggestions", []))
        if refactoring_count > 0:
            md_lines.append(f"**Refactoring Suggestions:** {refactoring_count}")
            md_lines.append("")

        # Recommendations
        recommendations = analysis_result.get("recommendations", [])
        if recommendations:
            md_lines.append("## 💡 Key Recommendations")
            md_lines.append("")
            for recommendation in recommendations[:5]:  # Top 5
                md_lines.append(f"- {recommendation}")
            md_lines.append("")

        # Footer
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("*Pull request analysis performed by Analysis Service*")
        md_lines.append(f"*Processed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(md_lines)


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
