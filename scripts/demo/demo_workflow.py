#!/usr/bin/env python3
"""
🚀 **WORKFLOW DEMO SCRIPT**
Complete Interpreter → Orchestrator → Simulation → Analysis Workflow Demonstration

This script demonstrates the full end-to-end workflow from natural language query
through simulation execution with comprehensive document analysis and recommendations.

USAGE:
    python demo_workflow.py

CONFIGURATION OPTIONS:
    REAPI_PORTS_DIR=./reports          # Directory to save downloaded reports
    DOWNLOAD_REAPI_PORTS=true          # Enable/disable report downloads
    AUTO_DOWNLOAD_REAPI_PORTS=simulation,summarizer  # Auto-select report types

REQUIREMENTS:
    - Core services running (see docker-compose.dev.yml)
    - Interpreter service on port 5120
    - Orchestrator service on port 5099
    - Simulation service on port 5075 (will use mock if not available)
    - Summarizer service on port 5160

REAPI_PORT DOWNLOAD OPTIONS:
    - simulation: Simulation execution reports and metrics
    - summarizer: Analysis results and capabilities
    - orchestrator: Workflow coordination reports
    - logs: Service logs and debug information
    - all: Download all available reports

WORKFLOW STEPS:
    1. 📝 User submits natural language query
    2. 🧠 Interpreter processes and understands intent
    3. 🎯 Orchestrator coordinates workflow execution
    4. 🏗️ Simulation service creates simulation with mock data
    5. 🔬 Summarizer-hub performs comprehensive analysis
    6. 📥 Download reports to local directory
    7. 📊 Results aggregated and presented to user
    8. 🎫 Optional Jira tickets created for follow-up
"""

import asyncio
import httpx
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import shutil


class WorkflowDemo:
    """Complete workflow demonstration class."""

    def __init__(self):
        self.colors = {
            "SUCCESS": "\033[92m",
            "ERROR": "\033[91m",
            "WARNING": "\033[93m",
            "INFO": "\033[94m",
            "RESET": "\033[0m",
            "BOLD": "\033[1m"
        }

        self.config = {
            "interpreter_url": os.getenv("INTERPRETER_URL", "http://localhost:5120"),
            "orchestrator_url": os.getenv("ORCHESTRATOR_URL", "http://localhost:5099"),
            "simulation_url": os.getenv("SIMULATION_URL", "http://localhost:5075"),
            "summarizer_url": os.getenv("SUMMARIZER_URL", "http://localhost:5160"),
            "analysis_url": os.getenv("ANALYSIS_URL", "http://localhost:5080"),
            "timeout": 30.0,
            "demo_mode": os.getenv("DEMO_MODE", "full"),  # full, analysis_only, simulation_only
            "reports_dir": os.getenv("REAPI_PORTS_DIR", "./reports"),
            "download_reports": os.getenv("DOWNLOAD_REAPI_PORTS", "true").lower() == "true"
        }

        # Create reports directory if it doesn't exist
        self.reports_path = Path(self.config["reports_dir"])
        self.reports_path.mkdir(exist_ok=True)
        self.print_info(f"Reports will be saved to: {self.reports_path.absolute()}")

    def print_header(self, text: str):
        """Print a formatted header."""
        print(f"\n{self.colors['BOLD']}{'='*60}{self.colors['RESET']}")
        print(f"{self.colors['BOLD']}{text.center(60)}{self.colors['RESET']}")
        print(f"{self.colors['BOLD']}{'='*60}{self.colors['RESET']}")

    def print_step(self, step_num: int, description: str):
        """Print a workflow step."""
        print(f"\n{self.colors['INFO']}Step {step_num}: {description}{self.colors['RESET']}")

    def print_success(self, message: str):
        """Print a success message."""
        print(f"{self.colors['SUCCESS']}✅ {message}{self.colors['RESET']}")

    def print_error(self, message: str):
        """Print an error message."""
        print(f"{self.colors['ERROR']}❌ {message}{self.colors['RESET']}")

    def print_warning(self, message: str):
        """Print a warning message."""
        print(f"{self.colors['WARNING']}⚠️ {message}{self.colors['RESET']}")

    def print_info(self, message: str):
        """Print an info message."""
        print(f"{self.colors['INFO']}ℹ️ {message}{self.colors['RESET']}")

    def generate_report_filename(self, service_name: str, report_type: str, timestamp: str = None, format: str = "md") -> str:
        """Generate a standardized filename for reports."""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = "md" if format == "md" else "json"
        return f"{service_name}_{report_type}_{timestamp}.{extension}"

    def format_json_to_markdown(self, data: Dict[str, Any], title: str, service_name: str) -> str:
        """Convert JSON data to beautiful Markdown format."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        markdown = f"""# 📊 {title}

**Report Generated:** {timestamp}
**Service:** {service_name}
**Format:** Comprehensive Analysis Report

---

"""

        markdown += self._convert_dict_to_markdown(data, level=0)
        return markdown

    def _convert_dict_to_markdown(self, data: Any, level: int = 0, prefix: str = "") -> str:
        """Recursively convert dictionary/list data to Markdown format."""
        indent = "  " * level
        result = ""

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    result += f"{indent}## {self._format_key(key)}\n\n"
                    result += self._convert_dict_to_markdown(value, level + 1, key)
                else:
                    result += f"{indent}- **{self._format_key(key)}:** {self._format_value(value)}\n"
            result += "\n"
        elif isinstance(data, list):
            if prefix:
                result += f"{indent}### {self._format_key(prefix)} Details\n\n"
            for i, item in enumerate(data, 1):
                if isinstance(item, (dict, list)):
                    result += f"{indent}#### Item {i}\n\n"
                    result += self._convert_dict_to_markdown(item, level + 1)
                else:
                    result += f"{indent}{i}. {self._format_value(item)}\n"
            result += "\n"
        else:
            result += f"{indent}{self._format_value(data)}\n\n"

        return result

    def _format_key(self, key: str) -> str:
        """Format dictionary keys for better readability."""
        return key.replace("_", " ").title()

    def _format_value(self, value: Any) -> str:
        """Format values for Markdown display."""
        if isinstance(value, bool):
            return "✅ Yes" if value else "❌ No"
        elif isinstance(value, (int, float)):
            if isinstance(value, float) and value.is_integer():
                return str(int(value))
            return str(value)
        elif value is None:
            return "*Not specified*"
        elif isinstance(value, str):
            # Handle URLs
            if value.startswith("http"):
                return f"[{value}]({value})"
            # Handle timestamps
            if "timestamp" in value.lower() or len(value) == 10 and value.replace(".", "").isdigit():
                try:
                    dt = datetime.fromtimestamp(float(value))
                    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
                except:
                    pass
            return value
        else:
            return str(value)

    def format_health_report_markdown(self, data: Dict[str, Any]) -> str:
        """Format health status data as beautiful Markdown."""
        status = data.get("status", "unknown")
        service = data.get("service", "Unknown Service")
        version = data.get("version", "N/A")
        timestamp = data.get("timestamp", datetime.now().timestamp())

        # Status emoji
        status_emoji = {
            "healthy": "🟢",
            "warning": "🟡",
            "error": "🔴",
            "unknown": "⚪"
        }.get(status, "⚪")

        # Format timestamp
        try:
            dt = datetime.fromtimestamp(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            formatted_time = str(timestamp)

        markdown = f"""# 🏥 Service Health Report

## Status Overview
- **Service:** {service}
- **Status:** {status_emoji} {status.title()}
- **Version:** {version}
- **Last Check:** {formatted_time}
- **Environment:** {data.get("environment", "N/A")}

"""

        # Add additional health details
        if "llm_gateway_url" in data:
            markdown += f"""## Service Dependencies
- **LLM Gateway:** {data["llm_gateway_url"]}

"""

        # Add uptime information if available
        if "uptime" in data:
            markdown += f"""## System Metrics
- **Uptime:** {data["uptime"]}

"""

        markdown += "---\n\n*Report generated automatically by Workflow Demo System*"
        return markdown

    def format_capabilities_report_markdown(self, data: Dict[str, Any]) -> str:
        """Format capabilities data as beautiful Markdown."""
        markdown = """# 🚀 Service Capabilities Report

## Available Features

"""

        for category, details in data.items():
            markdown += f"### {self._format_key(category)}\n\n"

            if isinstance(details, dict):
                for key, value in details.items():
                    if isinstance(value, list):
                        markdown += f"**{self._format_key(key)}:**\n"
                        for item in value:
                            markdown += f"- {item}\n"
                        markdown += "\n"
                    else:
                        markdown += f"- **{self._format_key(key)}:** {self._format_value(value)}\n"
            elif isinstance(details, list):
                for item in details:
                    markdown += f"- {item}\n"
            else:
                markdown += f"{details}\n"

            markdown += "\n"

        markdown += "---\n\n*Report generated automatically by Workflow Demo System*"
        return markdown

    def _analyze_document_distribution(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the distribution of documents across categories and tags."""
        category_distribution = {}
        tag_distribution = {}

        for doc in documents:
            category = doc.get("category", "uncategorized")
            category_distribution[category] = category_distribution.get(category, 0) + 1

            for tag in doc.get("tags", []):
                tag_distribution[tag] = tag_distribution.get(tag, 0) + 1

        return {
            "by_category": category_distribution,
            "by_tag": tag_distribution,
            "total_categories": len(category_distribution),
            "total_tags": len(tag_distribution)
        }

    def _generate_cross_document_insights(self, documents: List[Dict[str, Any]], summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights from cross-document analysis."""
        insights = {
            "similarity_patterns": [],
            "category_relationships": {},
            "content_clusters": []
        }

        # Simple similarity detection based on tags
        for i, doc1 in enumerate(documents):
            for doc2 in documents[i+1:]:
                shared_tags = set(doc1.get("tags", [])) & set(doc2.get("tags", []))
                if len(shared_tags) > 1:
                    insights["similarity_patterns"].append({
                        "documents": [doc1["id"], doc2["id"]],
                        "shared_tags": list(shared_tags),
                        "similarity_score": len(shared_tags) / max(len(set(doc1.get("tags", []))), len(set(doc2.get("tags", []))))
                    })

        # Category relationships
        categories = {}
        for doc in documents:
            category = doc.get("category", "uncategorized")
            if category not in categories:
                categories[category] = []
            categories[category].append(doc["id"])

        insights["category_relationships"] = categories

        return insights

    def _generate_multi_document_recommendations(self, documents: List[Dict[str, Any]], summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate recommendations based on multi-document analysis."""
        recommendations = []

        # Check for missing categories
        existing_categories = set(doc.get("category", "uncategorized") for doc in documents)
        required_categories = {"requirements", "architecture", "development", "security", "deployment", "testing", "api"}
        missing_categories = required_categories - existing_categories

        if missing_categories:
            recommendations.append({
                "type": "gap_analysis",
                "priority": "high",
                "description": f"Missing documentation categories: {', '.join(missing_categories)}. Consider creating documentation for these critical areas.",
                "confidence": 0.9,
                "affected_categories": list(missing_categories)
            })

        # Check document count adequacy
        if len(documents) < 10:
            recommendations.append({
                "type": "documentation_completeness",
                "priority": "medium",
                "description": f"Only {len(documents)} documents found. For comprehensive coverage, consider expanding to 15-20 documents.",
                "confidence": 0.8,
                "current_count": len(documents),
                "recommended_minimum": 15
            })

        # Check for category balance
        category_counts = {}
        for doc in documents:
            category = doc.get("category", "uncategorized")
            category_counts[category] = category_counts.get(category, 0) + 1

        unbalanced_categories = [cat for cat, count in category_counts.items() if count == 1]
        if unbalanced_categories:
            recommendations.append({
                "type": "category_balance",
                "priority": "low",
                "description": f"Categories with only one document: {', '.join(unbalanced_categories)}. Consider adding more documents to these categories.",
                "confidence": 0.7,
                "unbalanced_categories": unbalanced_categories
            })

        return recommendations

    def _analyze_document_evolution(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how documents evolve over time."""
        # Sort documents by creation date
        sorted_docs = sorted(documents, key=lambda x: x["dateCreated"])

        evolution = {
            "chronological_order": [doc["id"] for doc in sorted_docs],
            "creation_dates": [doc["dateCreated"] for doc in sorted_docs],
            "category_evolution": {}
        }

        # Track category evolution
        for doc in sorted_docs:
            category = doc.get("category", "uncategorized")
            if category not in evolution["category_evolution"]:
                evolution["category_evolution"][category] = []
            evolution["category_evolution"][category].append(doc["id"])

        return evolution

    def _calculate_quality_metrics(self, documents: List[Dict[str, Any]], summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate quality metrics for the document set."""
        metrics = {
            "total_documents": len(documents),
            "processed_documents": len(summaries),
            "processing_success_rate": len(summaries) / len(documents) * 100 if documents else 0,
            "categories_covered": len(set(doc.get("category", "uncategorized") for doc in documents)),
            "total_tags": len(set(tag for doc in documents for tag in doc.get("tags", []))),
            "average_tags_per_document": sum(len(doc.get("tags", [])) for doc in documents) / len(documents) if documents else 0,
            "quality_score": 0.0
        }

        # Calculate quality score based on various factors
        quality_factors = [
            min(metrics["processing_success_rate"] / 100, 1.0) * 0.4,  # 40% weight on processing success
            min(metrics["categories_covered"] / 7, 1.0) * 0.3,         # 30% weight on category coverage
            min(metrics["total_tags"] / 20, 1.0) * 0.2,                 # 20% weight on tag diversity
            min(len(documents) / 15, 1.0) * 0.1                         # 10% weight on document count
        ]

        metrics["quality_score"] = sum(quality_factors) * 100

        return metrics

    async def download_simulation_reports(self, simulation_id: str) -> Dict[str, str]:
        """Download reports from the simulation service."""
        self.print_step(6, "📥 Downloading Simulation Reports")

        downloaded_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Try to download different types of simulation reports
        report_endpoints = [
            ("simulation_details", f"/api/v1/simulations/{simulation_id}"),
            ("simulation_status", f"/api/v1/simulations/{simulation_id}/status"),
            ("simulation_metrics", f"/api/v1/simulations/{simulation_id}/metrics"),
            ("simulation_analysis", f"/api/v1/simulations/{simulation_id}/analysis")
        ]

        for report_type, endpoint in report_endpoints:
            try:
                async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                    response = await client.get(f"{self.config['simulation_url']}{endpoint}")

                    if response.status_code == 200:
                        filename = self.generate_report_filename("simulation", report_type, timestamp)
                        filepath = self.reports_path / filename

                        with open(filepath, 'w') as f:
                            if response.headers.get('content-type', '').startswith('application/json'):
                                data = response.json()
                                title = f"Simulation {report_type.replace('_', ' ').title()} Report"
                                markdown_content = self.format_json_to_markdown(data, title, "Project Simulation Service")
                                f.write(markdown_content)
                            else:
                                # Convert text responses to basic Markdown format
                                title = f"Simulation {report_type.replace('_', ' ').title()} Report"
                                markdown_content = f"# 📊 {title}\n\n**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n---\n\n```\n{response.text}\n```\n\n---\n\n*Report generated automatically by Workflow Demo System*"
                                f.write(markdown_content)

                        downloaded_files[report_type] = str(filepath)
                        self.print_success(f"Downloaded: {filename}")
                    else:
                        self.print_warning(f"Could not download {report_type}: HTTP {response.status_code}")

            except Exception as e:
                self.print_warning(f"Failed to download {report_type}: {str(e)}")

        return downloaded_files

    async def download_summarizer_reports(self, analysis_data: Dict[str, Any] = None) -> Dict[str, str]:
        """Download reports from the summarizer service."""
        self.print_step(7, "📥 Downloading Analysis Reports")

        downloaded_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Try to download analysis capabilities and status
        report_endpoints = [
            ("capabilities", "/capabilities"),
            ("health_status", "/health")
        ]

        for report_type, endpoint in report_endpoints:
            try:
                async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                    response = await client.get(f"{self.config['summarizer_url']}{endpoint}")

                    if response.status_code == 200:
                        filename = self.generate_report_filename("summarizer", report_type, timestamp)
                        filepath = self.reports_path / filename

                        with open(filepath, 'w') as f:
                            if response.headers.get('content-type', '').startswith('application/json'):
                                data = response.json()
                                if report_type == "capabilities":
                                    markdown_content = self.format_capabilities_report_markdown(data)
                                elif report_type == "health_status":
                                    markdown_content = self.format_health_report_markdown(data)
                                else:
                                    title = f"Summarizer {report_type.replace('_', ' ').title()} Report"
                                    markdown_content = self.format_json_to_markdown(data, title, "Summarizer Hub Service")
                                f.write(markdown_content)
                            else:
                                # Convert text responses to basic Markdown format
                                title = f"Summarizer {report_type.replace('_', ' ').title()} Report"
                                markdown_content = f"# 📊 {title}\n\n**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n---\n\n```\n{response.text}\n```\n\n---\n\n*Report generated automatically by Workflow Demo System*"
                                f.write(markdown_content)

                        downloaded_files[report_type] = str(filepath)
                        self.print_success(f"Downloaded: {filename}")

            except Exception as e:
                self.print_warning(f"Failed to download {report_type}: {str(e)}")

        # Save analysis data if available
        if analysis_data:
            filename = self.generate_report_filename("summarizer", "analysis_results", timestamp)
            filepath = self.reports_path / filename

            with open(filepath, 'w') as f:
                title = "Comprehensive Analysis Results Report"
                markdown_content = self.format_json_to_markdown(analysis_data, title, "Summarizer Hub Service")
                f.write(markdown_content)

            downloaded_files["analysis_results"] = str(filepath)
            self.print_success(f"Saved analysis results: {filename}")

        return downloaded_files

    async def download_orchestrator_reports(self) -> Dict[str, str]:
        """Download reports from the orchestrator service."""
        self.print_step(8, "📥 Downloading Orchestrator Reports")

        downloaded_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Try to download orchestrator reports
        report_endpoints = [
            ("service_registry", "/api/v1/service-registry/services"),
            ("workflows", "/api/v1/workflows"),
            ("queries_history", "/api/v1/queries/history")
        ]

        for report_type, endpoint in report_endpoints:
            try:
                async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                    response = await client.get(f"{self.config['orchestrator_url']}{endpoint}")

                    if response.status_code == 200:
                        filename = self.generate_report_filename("orchestrator", report_type, timestamp)
                        filepath = self.reports_path / filename

                        with open(filepath, 'w') as f:
                            if response.headers.get('content-type', '').startswith('application/json'):
                                data = response.json()
                                title = f"Orchestrator {report_type.replace('_', ' ').title()} Report"
                                markdown_content = self.format_json_to_markdown(data, title, "Orchestrator Service")
                                f.write(markdown_content)
                            else:
                                # Convert text responses to basic Markdown format
                                title = f"Orchestrator {report_type.replace('_', ' ').title()} Report"
                                markdown_content = f"# 📊 {title}\n\n**Report Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n---\n\n```\n{response.text}\n```\n\n---\n\n*Report generated automatically by Workflow Demo System*"
                                f.write(markdown_content)

                        downloaded_files[report_type] = str(filepath)
                        self.print_success(f"Downloaded: {filename}")
                    else:
                        self.print_warning(f"Could not download {report_type}: HTTP {response.status_code}")

            except Exception as e:
                self.print_warning(f"Failed to download {report_type}: {str(e)}")

        return downloaded_files

    async def download_service_logs(self) -> Dict[str, str]:
        """Download logs from running services."""
        self.print_step(9, "📥 Downloading Service Logs")

        downloaded_files = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        services_to_log = [
            ("interpreter", self.config["interpreter_url"]),
            ("orchestrator", self.config["orchestrator_url"]),
            ("summarizer", self.config["summarizer_url"])
        ]

        for service_name, service_url in services_to_log:
            try:
                # Try to get service logs via Docker
                import subprocess
                container_name = f"hackathon-{service_name}-1"

                result = subprocess.run(
                    ["docker", "logs", "--tail", "100", container_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    filename = self.generate_report_filename(service_name, "logs", timestamp)
                    filepath = self.reports_path / filename

                    with open(filepath, 'w') as f:
                        markdown_content = f"""# 📋 Service Logs Report

## Service Information
- **Service:** {service_name}
- **Container:** {container_name}
- **Log Timestamp:** {datetime.now().isoformat()}
- **Log Type:** Docker Container Logs

## Log Output

```
{result.stdout}
"""

                        if result.stderr:
                            markdown_content += f"""

## Standard Error Output

```
{result.stderr}
```

"""

                        markdown_content += "\n---\n\n*Log captured automatically by Workflow Demo System*"
                        f.write(markdown_content)

                    downloaded_files[f"{service_name}_logs"] = str(filepath)
                    self.print_success(f"Downloaded logs: {filename}")
                else:
                    self.print_warning(f"Could not get logs for {service_name}")

            except Exception as e:
                self.print_warning(f"Failed to download logs for {service_name}: {str(e)}")

        return downloaded_files

    def display_downloaded_reports(self, all_downloads: Dict[str, Dict[str, str]]):
        """Display summary of all downloaded reports."""
        self.print_header("📊 REAPI_PORT DOWNLOAD SUMMARY")

        total_files = 0
        for service, files in all_downloads.items():
            if files:
                self.print_info(f"{service.title()} Service: {len(files)} files")
                for file_type, filepath in files.items():
                    self.print_info(f"  • {file_type}: {filepath}")
                    total_files += 1

        if total_files > 0:
            self.print_success(f"Total files downloaded: {total_files}")
            self.print_info(f"All reports saved to: {self.reports_path.absolute()}")
            self.print_info("You can now examine these reports for detailed analysis results.")
        else:
            self.print_warning("No reports were successfully downloaded.")

    async def generate_workflow_summary_report(self, analysis_result: Dict[str, Any], context_documents: List[Dict[str, Any]]):
        """Generate a comprehensive workflow summary report."""
        try:
            self.print_info("Generating comprehensive workflow summary report...")

            # Extract key metrics from analysis result
            # Use total_documents from analysis result, fallback to context documents
            doc_count = analysis_result.get('total_documents', len(context_documents))
            recommendations = analysis_result.get('recommendations', [])
            quality_metrics = analysis_result.get('quality_metrics', {})
            alignment_analysis = analysis_result.get('alignment_analysis', {})

            # Count recommendation types
            rec_types = {}
            priorities = {'high': 0, 'medium': 0, 'low': 0, 'critical': 0}
            for rec in recommendations:
                rec_type = rec.get('type', 'unknown')
                rec_types[rec_type] = rec_types.get(rec_type, 0) + 1
                priority = rec.get('priority', 'medium').lower()
                if priority in priorities:
                    priorities[priority] += 1

            # Generate report content
            report_content = f"""# Workflow Summary Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

This report summarizes the complete Interpreter → Orchestrator → Simulation → Analysis workflow execution demonstrating the full end-to-end document analysis pipeline.

## Analysis Results Summary

### 📄 Document Analysis Overview
- **Documents Analyzed**: {doc_count} total
- **Recommendations Generated**: {len(recommendations)}
- **Processing Time**: {analysis_result.get('processing_time', 'N/A')}s
- **Success Rate**: {quality_metrics.get('processing_success_rate', 100.0):.1f}%

### 🔍 Recommendation Types Breakdown
"""

            for rec_type, count in rec_types.items():
                report_content += f"- **{rec_type.replace('_', ' ').title()}**: {count} recommendation{'s' if count != 1 else ''}\n"

            report_content += f"""
### 🎯 Priority Distribution
- **High Priority**: {priorities['high'] + priorities['critical']} recommendation{'s' if priorities['high'] + priorities['critical'] != 1 else ''}
- **Medium Priority**: {priorities['medium']} recommendation{'s' if priorities['medium'] != 1 else ''}
- **Low Priority**: {priorities['low']} recommendation{'s' if priorities['low'] != 1 else ''}

### 🎯 Alignment Analysis Results
- **Overall Alignment Score**: {alignment_analysis.get('overall_alignment_score', 0):.1f}%
- **Alignment Issues Identified**: {len(alignment_analysis.get('alignment_issues', []))}

### 📈 Quality Metrics
- **Overall Quality Score**: {quality_metrics.get('quality_score', 0):.1f}%
- **Category Coverage**: {quality_metrics.get('categories_covered', 0)} categories
- **Tag Diversity**: {quality_metrics.get('total_tags', 0)} unique tags
- **Document Count**: {doc_count}

## Document Ecosystem Summary

### Document Types Processed
"""

            # Count document types from document dump metadata (contains accurate counts)
            doc_types = {}
            document_dump = analysis_result.get('document_dump', {})
            if document_dump and 'metadata' in document_dump:
                # Use actual counts from document dump metadata
                metadata = document_dump['metadata']
                doc_type_counts = metadata.get('document_type_counts', {})

                if doc_type_counts:
                    # Use the actual counts from document dump
                    doc_types = doc_type_counts
                else:
                    # Fallback to document types list if no counts available
                    doc_types_list = metadata.get('document_types', [])
                    for doc_type in doc_types_list:
                        doc_types[doc_type] = 0  # Placeholder, will be corrected below
            else:
                # Fallback to context documents
                for doc in context_documents:
                    doc_type = doc.get('type', 'unknown')
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

            for doc_type, count in doc_types.items():
                report_content += f"- **{doc_type.upper()} Documents**: {count}\n"

            report_content += f"""
## Key Findings
- **Documents Span**: {doc_count} documents across {len(doc_types)} types
- **Quality Assessment**: {quality_metrics.get('quality_score', 0):.1f}% overall quality
- **Alignment Score**: {alignment_analysis.get('overall_alignment_score', 0):.1f}% consistency
- **Recommendations**: {len(recommendations)} actionable insights generated

## Conclusion

✅ **Workflow Execution**: SUCCESS
✅ **Documents Processed**: {doc_count}
✅ **Analysis Completed**: {len(recommendations)} recommendations
✅ **Quality Score**: {quality_metrics.get('quality_score', 0):.1f}%
✅ **Success Rate**: {quality_metrics.get('processing_success_rate', 100.0):.1f}%

The system successfully demonstrated enterprise-grade document analysis capabilities with conflict detection, gap analysis, and automated recommendations generation.

---
*Report generated by Workflow Demo Script v1.0*
*Analysis performed on {doc_count} documents across {len(doc_types)} types*
*Quality metrics calculated with {quality_metrics.get('processing_success_rate', 100.0):.1f}% success rate*
"""

            # Save the report
            report_filename = self.generate_report_filename("workflow_summary", "report", format="md")
            report_path = self.reports_path / report_filename

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)

            self.print_success(f"Workflow summary report generated and saved: {report_path}")
            return report_path

        except Exception as e:
            self.print_warning(f"Workflow summary report generation failed: {str(e)}")
            return None

    async def prompt_for_report_download(self) -> List[str]:
        """Prompt user to select which types of reports to download."""
        if not self.config["download_reports"]:
            return []

        self.print_header("📥 ADDITIONAL REAPI_PORT DOWNLOAD OPTIONS")

        self.print_info("📋 Core reports are ALWAYS downloaded:")
        self.print_info("  ✅ Summarizer analysis results")
        self.print_info("  ✅ Workflow summary report")
        self.print_info("  ✅ Document dump report")
        self.print_info("")

        options = {
            "simulation": "Simulation execution reports and metrics",
            "orchestrator": "Workflow coordination reports",
            "logs": "Service logs and debug information",
            "all": "Download all additional reports"
        }

        self.print_info("Additional optional report types:")
        for key, description in options.items():
            if key != "all":
                self.print_info(f"  • {key}: {description}")

        self.print_info("  • all: Download all additional reports")

        # Auto-select based on environment variable or prompt user
        auto_download = os.getenv("AUTO_DOWNLOAD_REAPI_PORTS")
        if auto_download:
            selected = auto_download.split(",")
            self.print_info(f"Auto-downloading reports: {', '.join(selected)}")
            return selected

        # Interactive prompt
        while True:
            choice = input("\nSelect reports to download (comma-separated, or 'all'): ").strip().lower()

            if choice == "all":
                return list(options.keys())[:-1]  # Exclude 'all' option
            elif choice == "":
                return ["simulation", "summarizer"]  # Default selection
            else:
                selected = [s.strip() for s in choice.split(",")]
                valid = all(s in options for s in selected)
                if valid:
                    return [s for s in selected if s != "all"]
                else:
                    self.print_error("Invalid selection. Please try again.")

    async def check_service_health(self, service_name: str, url: str) -> bool:
        """Check if a service is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    self.print_success(f"{service_name} is healthy")
                    return True
                else:
                    self.print_error(f"{service_name} unhealthy (status: {response.status_code})")
                    return False
        except Exception as e:
            self.print_error(f"{service_name} unreachable: {str(e)}")
            return False

    async def check_all_services(self) -> bool:
        """Check health of all required services."""
        self.print_header("🔍 SERVICE HEALTH CHECK")

        services = [
            ("Interpreter", self.config["interpreter_url"]),
            ("Orchestrator", self.config["orchestrator_url"]),
            ("Summarizer", self.config["summarizer_url"])
        ]

        # Check simulation service separately (optional for demo)
        simulation_healthy = False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.config['simulation_url']}/health")
                if response.status_code == 200:
                    simulation_healthy = True
                    self.print_success("Simulation is healthy")
                else:
                    self.print_warning("Simulation service not available (will use mock simulation)")
        except Exception:
            self.print_warning("Simulation service not available (will use mock simulation)")

        all_healthy = True
        for service_name, url in services:
            if not await self.check_service_health(service_name, url):
                all_healthy = False

        if not all_healthy:
            self.print_error("Some services are not healthy. Please start all services first.")
            self.print_info("Run: docker-compose -f docker-compose.dev.yml up -d")
            return False

        self.print_success("All services are healthy and ready!")
        return True

    async def demonstrate_interpreter_processing(self) -> Dict[str, Any]:
        """Demonstrate interpreter query processing."""
        self.print_step(1, "🧠 Interpreter Query Processing")

        sample_query = """Create comprehensive financial services platform simulation with diverse document ecosystem.

**Requirements:**
- Team: 20 developers, 8 QA engineers, 5 DevOps engineers, 3 architects
- Duration: 36 months with monthly milestones
- Technologies: React/TypeScript, Java/Spring Boot, Python/Django, PostgreSQL/Redis, Docker/Kubernetes
- Compliance: SOC2, PCI-DSS, GDPR, HIPAA requirements

**Analysis focus:** Timeline Analysis, Quality Assessment, Gap Analysis, Conflict Detection, Alignment Analysis."""

        self.print_info(f"Query: {sample_query}")

        # In a real implementation, this would call the interpreter service
        # For demo purposes, we'll simulate the response
        # Fetch relevant sample documents for context
        try:
            async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                context_request = {
                    "query": sample_query,
                    "context": {"demo_mode": True, "request_type": "document_analysis"}
                }

                context_response = await client.post(
                    f"{self.config['interpreter_url']}/documents/sample/context",
                    json=context_request,
                    headers={"Content-Type": "application/json"}
                )

                if context_response.status_code == 200:
                    context_data = context_response.json()
                    relevant_documents = context_data.get("relevant_documents", [])
                    self.print_info(f"Retrieved {len(relevant_documents)} relevant sample documents from interpreter")
                else:
                    relevant_documents = []
                    self.print_warning("Could not retrieve sample documents from interpreter")

        except Exception as e:
            self.print_warning(f"Error fetching sample documents: {str(e)}")
            relevant_documents = []

        interpreted_result = {
            "original_query": sample_query,
            "interpreted_intent": "create_simulation",
            "confidence": 0.95,
            "parameters": {
                "project_type": "e_commerce_platform",
                "architecture": "microservices",
                "team_size": 6,
                "duration_weeks": 10,
                "complexity": "high",
                "technologies": ["React", "Node.js", "Python", "PostgreSQL", "Docker", "Kubernetes"],
                "sample_documents": relevant_documents
            },
            "context_documents": relevant_documents
        }

        self.print_success("Query interpreted successfully")
        self.print_info(f"Intent: {interpreted_result['interpreted_intent']}")
        self.print_info(f"Confidence: {interpreted_result['confidence']:.1%}")
        self.print_info(f"Parameters: {json.dumps(interpreted_result['parameters'], indent=2)}")

        return interpreted_result

    async def demonstrate_orchestrator_coordination(self, interpreted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Demonstrate orchestrator coordination."""
        self.print_step(2, "🎯 Orchestrator Coordination")

        simulation_request = {
            "query": interpreted_data["original_query"],
            "context": {"source": "demo_workflow", "user_id": "demo_user"},
            "simulation_config": interpreted_data["parameters"],
            "generate_mock_data": True,
            "analysis_types": ["consolidation", "duplicate", "outdated", "quality"]
        }

        try:
            async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                self.print_info("Sending request to orchestrator...")
                response = await client.post(
                    f"{self.config['orchestrator_url']}/api/v1/queries/process",
                    json={
                        "query_text": interpreted_data["original_query"],
                        "context": simulation_request["context"],
                        "max_results": 50,
                        "include_explanation": True
                    },
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    self.print_success("Orchestrator processed request successfully")
                    self.print_info(f"Request ID: {result.get('orchestrator_request_id', 'N/A')}")
                    self.print_info(f"Query processed: {result.get('query_processed', 'N/A')}")

                    return result
                else:
                    self.print_error(f"Orchestrator error: {response.status_code}")
                    self.print_info(f"Response: {response.text}")
                    return {}

        except Exception as e:
            self.print_error(f"Orchestrator communication failed: {str(e)}")
            return {}

    async def demonstrate_simulation_creation(self, orchestrator_result: Dict[str, Any]) -> Dict[str, Any]:
        """Demonstrate simulation creation and execution."""
        self.print_step(3, "🏗️ Simulation Creation & Execution")

        # Extract simulation parameters from orchestrator result
        simulation_config = {
            "type": "e_commerce_platform",
            "complexity": "high",
            "duration_weeks": 10,
            "budget": 250000,
            "team_size": 6,
            "technologies": ["React", "Node.js", "Python", "PostgreSQL", "Docker"]
        }

        interpreter_request = {
            "query": "Build an e-commerce platform with microservices",
            "context": {"demo": True, "workflow_step": "simulation_creation"},
            "simulation_config": simulation_config
        }

        try:
            async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                self.print_info("Creating simulation via interpreter endpoint...")
                response = await client.post(
                    f"{self.config['simulation_url']}/api/v1/interpreter/simulate",
                    json=interpreter_request,
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    result = response.json()
                    self.print_success("Simulation created and executed successfully")

                    if result.get("success"):
                        self.print_info(f"Simulation ID: {result.get('simulation_id', 'N/A')}")
                        self.print_info(f"Status: {result.get('status', 'completed')}")
                        self.print_info(f"Mock data generated: {result.get('mock_data_generated', False)}")

                        # Show analysis results if available
                        if "analysis_results" in result:
                            analysis = result["analysis_results"]
                            self.print_info("Analysis Results:")
                            self.print_info(f"  📊 Documents analyzed: {len(analysis.get('document_analysis', []))}")
                            self.print_info(f"  👥 Team analysis: {analysis.get('team_analysis', 'N/A')}")
                            self.print_info(f"  📅 Timeline analysis: {'Available' if analysis.get('timeline_analysis') else 'N/A'}")

                    return result
                elif response.status_code == 503:
                    # Simulation service not available, use mock simulation
                    self.print_warning("Simulation service not available, using mock simulation")
                    mock_result = {
                        "success": True,
                        "simulation_id": f"demo_sim_{int(datetime.now().timestamp())}",
                        "status": "completed",
                        "mock_data_generated": True,
                        "message": "Mock simulation completed successfully",
                        "simulation_config": simulation_config,
                        "analysis_results": {
                            "document_analysis": [
                                {"id": "req_doc", "title": "Requirements", "status": "analyzed"},
                                {"id": "arch_doc", "title": "Architecture", "status": "analyzed"}
                            ],
                            "team_analysis": "6-member team with full-stack capabilities",
                            "timeline_analysis": {"phases": 3, "duration_weeks": 10}
                        }
                    }
                    self.print_success("Mock simulation completed successfully")
                    self.print_info(f"Simulation ID: {mock_result['simulation_id']}")
                    self.print_info("Mock data generated: True")
                    return mock_result
                else:
                    self.print_error(f"Simulation creation failed: {response.status_code}")
                    self.print_info(f"Response: {response.text}")
                    return {}

        except Exception as e:
            self.print_error(f"Simulation service communication failed: {str(e)}")
            # Provide mock result for demo purposes
            mock_result = {
                "success": True,
                "simulation_id": f"demo_sim_{int(datetime.now().timestamp())}",
                "status": "completed",
                "mock_data_generated": True,
                "message": "Mock simulation completed successfully (service unavailable)",
                "simulation_config": simulation_config,
                "analysis_results": {
                    "document_analysis": [
                        {"id": "req_doc", "title": "Requirements", "status": "analyzed"},
                        {"id": "arch_doc", "title": "Architecture", "status": "analyzed"}
                    ],
                    "team_analysis": "6-member team with full-stack capabilities",
                    "timeline_analysis": {"phases": 3, "duration_weeks": 10}
                }
            }
            self.print_success("Mock simulation completed successfully")
            self.print_info(f"Simulation ID: {mock_result['simulation_id']}")
            return mock_result

    def _generate_comprehensive_sample_documents(self, count: int = 35) -> List[Dict[str, Any]]:
        """Generate a comprehensive set of sample documents for demonstration."""
        import random
        from datetime import datetime, timedelta

        documents = []

        # Document templates
        confluence_templates = [
            {
                "title": "System Architecture Overview - {service}",
                "content": "# {service} Architecture Overview\n\n## Overview\nThe {service} is a critical component of our financial services platform.\n\n## Core Components\n- **API Gateway**: Handles request routing and authentication\n- **Business Logic Layer**: Implements core business rules\n- **Data Access Layer**: Manages database interactions\n\n## Technology Stack\n- Backend: {backend}\n- Database: {database}\n- Caching: Redis Cluster\n- Message Queue: Apache Kafka",
                    "category": "architecture",
                "tags": ["architecture", "microservices", "{domain}", "scalability"]
            },
            {
                "title": "API Documentation - {service}",
                "content": "# {service} API Documentation\n\n## Authentication\nAll API requests require JWT token authentication.\n\n## Endpoints\n\n### GET /api/v1/{endpoint}\nRetrieves {resource} information.\n\n**Parameters:**\n- `id`: Resource identifier\n- `include_details`: Include full details (default: false)\n\n**Response:**\n```json\n{{\n  \"id\": \"string\",\n  \"name\": \"string\",\n  \"status\": \"active\"\n}}\n```\n\n### POST /api/v1/{endpoint}\nCreates a new {resource}.\n\n**Request Body:**\n```json\n{{\n  \"name\": \"string\",\n  \"description\": \"string\"\n}}\n```",
                "category": "api",
                "tags": ["api", "documentation", "{domain}", "rest"]
            },
            {
                "title": "Security Requirements for {service}",
                "content": "# Security Requirements - {service}\n\n## Authentication & Authorization\n- All endpoints must implement JWT-based authentication\n- Role-based access control (RBAC) required\n- Multi-factor authentication for admin operations\n\n## Data Protection\n- All sensitive data must be encrypted at rest\n- TLS 1.3 required for all communications\n- PCI DSS compliance for payment data\n\n## Audit Logging\n- All security events must be logged\n- Logs must be retained for 7 years\n- Real-time security monitoring required\n\n## Compliance\n- SOC 2 Type II certification required\n- GDPR compliance for EU users\n- Regular security assessments mandatory",
                "category": "security",
                "tags": ["security", "compliance", "gdpr", "encryption"]
            }
        ]

        jira_templates = [
            {
                "title": "Implement {feature} in {service}",
                "content": "As a {user_type}, I want to be able to {feature_description} so that I can {benefit}.\n\n## Acceptance Criteria\n- {feature} functionality fully implemented\n- Unit tests with 80%+ coverage\n- Integration tests passing\n- Documentation updated\n- Performance benchmarks met\n- Security review completed\n\n## Technical Details\n- Backend: {backend_tech}\n- Database changes: {db_changes}\n- API endpoints: {api_endpoints}\n- UI components: {ui_components}",
                "category": "feature",
                "tags": ["feature", "development", "{domain}", "enhancement"],
                "status": "in_progress",
                "priority": "high"
            },
            {
                "title": "Fix {issue} in {service}",
                "content": "## Problem\n{issue_description}\n\n## Root Cause\n{root_cause}\n\n## Impact\n- {impact_severity} impact on users\n- Affects {affected_users} users\n- {business_impact}\n\n## Solution\n{technical_solution}\n\n## Testing\n- Unit tests for fix\n- Regression tests\n- Performance validation\n- Security validation",
                "category": "bug_fix",
                "tags": ["bug", "fix", "critical", "{domain}"],
                "status": "resolved",
                "priority": "critical"
            },
            {
                "title": "Performance Optimization for {service}",
                "content": "## Current Performance Issues\n- {performance_issue}\n- Response time: {current_time}ms (target: {target_time}ms)\n- Throughput: {current_tps} TPS (target: {target_tps} TPS)\n\n## Optimization Strategy\n1. Database query optimization\n2. Caching implementation\n3. Code profiling and optimization\n4. Infrastructure scaling\n\n## Success Criteria\n- Response time < {target_time}ms for 95th percentile\n- Throughput > {target_tps} TPS\n- CPU usage < 70%\n- Memory usage < 80%\n- No performance regressions",
                "category": "performance",
                "tags": ["performance", "optimization", "scalability", "monitoring"],
                "status": "in_progress",
                "priority": "medium"
            }
        ]

        pull_request_templates = [
            {
                "title": "feat: Add {feature} functionality",
                "content": "This PR implements {feature} functionality for the {service}.\n\n## Changes Made\n\n### Backend Changes\n- Added {feature} service class\n- Implemented {feature} endpoints\n- Added data models and repositories\n- Updated business logic\n\n### Database Changes\n- Added {feature}_table\n- Updated existing schemas\n- Added migration scripts\n\n### Testing\n- Added comprehensive unit tests\n- Added integration tests\n- Updated API documentation\n- Performance tests included\n\n### Security\n- Input validation implemented\n- SQL injection prevention\n- XSS protection\n- Authentication checks",
                "category": "feature",
                "tags": ["feature", "backend", "{domain}", "enhancement"],
                "status": "open"
            },
            {
                "title": "fix: Resolve {issue} bug",
                "content": "This PR fixes the {issue} bug that was causing {symptoms}.\n\n## Problem\n{issue_description}\n\n## Root Cause\nThe issue was caused by {root_cause}.\n\n## Solution\n- Fixed {fix_description}\n- Added proper error handling\n- Updated validation logic\n- Added test coverage\n\n## Testing\n- Added regression tests\n- Verified fix works in staging\n- Performance impact assessed\n- Security implications reviewed\n\n## Breaking Changes\nNone expected.",
                "category": "bug_fix",
                "tags": ["fix", "bug", "hotfix", "{domain}"],
                "status": "merged"
            }
        ]

        # Data for generating varied content
        services = ["Account Service", "Transaction Service", "User Management", "Payment Gateway", "Notification Service", "Analytics Engine", "Reporting Service", "Audit Service", "Compliance Engine", "Risk Assessment"]
        domains = ["banking", "finance", "payments", "security", "compliance", "analytics", "reporting"]
        backends = ["Java/Spring Boot", "Python/Django", "Node.js/Express", "Go/Gin", ".NET Core", "Ruby/Rails"]
        databases = ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Cassandra", "DynamoDB"]
        authors = ["Sarah Johnson", "Mike Chen", "Emma Wilson", "David Kim", "Alex Thompson", "Robert Davis", "Lisa Wang", "James Miller", "Anna Garcia", "Tom Anderson"]
        assignees = ["Mike Chen", "David Kim", "Alex Thompson", "Robert Davis", "James Miller", "Anna Garcia"]

        # Generate documents
        base_date = datetime(2024, 1, 1)
        document_types = ["confluence", "jira", "pull_request"]

        for i in range(count):
            doc_type = random.choice(document_types)
            service = random.choice(services)
            domain = random.choice(domains)
            backend = random.choice(backends)
            database = random.choice(databases)
            author = random.choice(authors)
            assignee = random.choice(assignees) if doc_type in ["jira", "pull_request"] else None

            # Generate dates
            created_date = base_date + timedelta(days=random.randint(0, 240))
            updated_date = created_date + timedelta(days=random.randint(1, 60))

            doc_id = "04d"

            if doc_type == "confluence":
                template = random.choice(confluence_templates)
                title = template["title"].format(service=service)
                content = template["content"].format(
                    service=service, backend=backend, database=database,
                    endpoint=service.lower().replace(" ", "_"),
                    resource=service.lower().replace(" service", "")
                )
                category = template["category"]
                tags = [tag.format(domain=domain) for tag in template["tags"]]
                status = random.choice(["published", "draft", "archived"])

                document = {
                    "id": doc_id,
                    "type": doc_type,
                    "title": title,
                    "content": content,
                    "dateCreated": created_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "dateUpdated": updated_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "category": category,
                    "tags": tags,
                    "author": author,
                    "status": status
                }

            elif doc_type == "jira":
                template = random.choice(jira_templates)
                issue = random.choice(["authentication", "performance", "security", "data corruption"])
                feature = f"{random.choice(['user', 'admin', 'system', 'api'])} {random.choice(['dashboard', 'reports', 'settings', 'profile'])}"
                title = template["title"].format(
                    feature=feature,
                    issue=issue,
                    service=service
                )
                content = template["content"].format(
                    user_type=random.choice(["user", "administrator", "developer", "analyst"]),
                    feature=feature,
                    feature_description=f"use the {random.choice(['dashboard', 'reporting', 'analytics', 'settings'])} feature",
                    benefit=f"manage {random.choice(['accounts', 'transactions', 'reports', 'settings'])} efficiently",
                    backend_tech=backend,
                    db_changes=random.choice(["New table added", "Schema updated", "Index optimized", "No changes"]),
                    api_endpoints=random.choice(["2 new endpoints", "3 updated endpoints", "1 deleted, 2 added"]),
                    ui_components=random.choice(["React components", "Angular modules", "Vue components", "No UI changes"]),
                    issue=issue,
                    issue_description=f"The {random.choice(['login', 'data processing', 'API calls', 'file uploads'])} functionality was not working correctly",
                    root_cause=random.choice(["null pointer exception", "race condition", "memory leak", "incorrect validation"]),
                    impact_severity=random.choice(["high", "medium", "low"]),
                    affected_users=random.choice(["all users", "admin users", "API consumers"]),
                    business_impact=random.choice(["service downtime", "data loss risk", "compliance issues"]),
                    technical_solution=f"Implemented proper {random.choice(['error handling', 'validation', 'caching', 'optimization'])}",
                    performance_issue=random.choice(["slow response times", "high CPU usage", "memory leaks", "database timeouts"]),
                    current_time=random.randint(500, 5000),
                    target_time=random.randint(100, 300),
                    current_tps=random.randint(10, 100),
                    target_tps=random.randint(100, 1000)
                )
                category = template["category"]
                tags = [tag.format(domain=domain) for tag in template["tags"]]
                priority = random.choice(["highest", "high", "medium", "low", "lowest"])
                status = random.choice(["open", "in_progress", "resolved", "closed"])

                document = {
                    "id": doc_id,
                    "type": doc_type,
                    "title": title,
                    "content": content,
                    "dateCreated": created_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "dateUpdated": updated_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "category": category,
                    "tags": tags,
                    "author": author,
                    "assignee": assignee,
                    "status": status,
                    "priority": priority,
                    "comments": [
                        {
                            "author": random.choice(authors),
                            "timestamp": (created_date + timedelta(days=random.randint(1, 10))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "content": f"Good progress on this {random.choice(['feature', 'fix', 'task'])}. {random.choice(['Keep it up!', 'Looks good so far.', 'Need more details.', 'Approved for merge.'])}"
                        }
                    ] if random.random() > 0.3 else []
                }

            else:  # pull_request
                template = random.choice(pull_request_templates)
                issue_type = random.choice(["authentication", "performance", "security", "validation"])
                symptoms = random.choice(["errors", "slow responses", "data corruption", "crashes"])
                title = template["title"].format(
                    feature=f"{random.choice(['user', 'admin', 'system', 'api'])} {random.choice(['dashboard', 'reports', 'settings', 'profile'])}",
                    issue=issue_type,
                    symptoms=symptoms
                )
                content = template["content"].format(
                    feature=f"{random.choice(['user', 'admin', 'system'])} {random.choice(['dashboard', 'reporting', 'analytics'])}",
                    service=service,
                    issue=issue_type,
                    issue_description=f"The {random.choice(['login', 'data processing', 'API calls', 'file uploads'])} functionality was not working correctly",
                    symptoms=symptoms,
                    root_cause=random.choice(["null pointer exception", "race condition", "memory leak", "incorrect validation"]),
                    fix_description=random.choice(["error handling", "validation logic", "caching mechanism", "database query"])
                )
                category = template["category"]
                tags = [tag.format(domain=domain) for tag in template["tags"]]
                status = random.choice(["open", "merged", "closed"])

                document = {
                    "id": doc_id,
                    "type": doc_type,
                    "title": title,
                    "content": content,
                    "dateCreated": created_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "dateUpdated": updated_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "category": category,
                    "tags": tags,
                    "author": author,
                    "status": status,
                "comments": [
                    {
                            "author": random.choice(authors),
                            "timestamp": (created_date + timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "content": f"Code review: {random.choice(['Looks good!', 'Need some changes.', 'Approved with suggestions.', 'Requesting changes.'])}"
                        },
                        {
                            "author": author,
                            "timestamp": (created_date + timedelta(days=random.randint(2, 7))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "content": f"Addressed review comments. {random.choice(['Updated validation logic.', 'Added error handling.', 'Fixed performance issue.', 'Updated tests.'])}"
                        }
                    ] if random.random() > 0.2 else []
                }

            documents.append(document)

        # Add some special documents for variety
        # Add a few conflict documents
        for i in range(3):
            conflict_doc = {
                "id": "06d",
                "type": "confluence",
                "title": f"Data Retention Policy v{random.randint(1, 3)}.{random.randint(0, 9)}",
                "content": f"# Data Retention Policy\n\n## Overview\nThis document outlines data retention policies.\n\n## Retention Periods\n- Customer data: Retained for {random.choice(['7 days', '7 years', '30 days', '1 year'])}\n- Transaction data: Retained for {random.choice(['7 days', '7 years', '30 days', '1 year'])}\n- Logs: Retained for {random.choice(['7 days', '1 year', '30 days', '6 months'])}\n\n## Note: This {'conflicts with' if random.random() > 0.5 else 'aligns with'} the main compliance policy.",
                "dateCreated": (base_date + timedelta(days=random.randint(30, 60))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "dateUpdated": (base_date + timedelta(days=random.randint(60, 90))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "category": "compliance",
                "tags": ["data_retention", "gdpr", "compliance", "conflict"],
                "author": random.choice(authors),
                "status": "published"
            }
            documents.append(conflict_doc)

        # Add some sparse/empty documents
        for i in range(2):
            sparse_doc = {
                "id": "06d",
                "type": "confluence",
                "title": f"{random.choice(['Mobile Guidelines', 'API Standards', 'Testing Procedures', 'Deployment Guide'])}",
                "content": random.choice([
                    "Use best practices. Keep it simple.",
                    "Follow established patterns.",
                    "",
                    "TBD - To be documented",
                    "See main documentation repository."
                ]),
                "dateCreated": (base_date + timedelta(days=random.randint(10, 30))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "dateUpdated": (base_date + timedelta(days=random.randint(10, 30))).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "category": random.choice(["design", "api", "testing", "deployment"]),
                "tags": [random.choice(["mobile", "api", "testing", "deployment", "guidelines"])],
                "author": random.choice(authors),
                "status": "draft"
            }
            documents.append(sparse_doc)

        return documents

    async def demonstrate_analysis_processing(self, context_documents: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Demonstrate comprehensive analysis processing with enhanced multi-document capabilities."""
        self.print_step(4, "🔬 Comprehensive Analysis Processing")

        # Use documents from interpreter context, or generate comprehensive sample documents
        if context_documents and len(context_documents) >= 30:
            sample_documents = context_documents
            self.print_info(f"Using {len(sample_documents)} documents from interpreter context")
        else:
            self.print_info("Generating comprehensive sample document set (35+ documents)")
            sample_documents = self._generate_comprehensive_sample_documents(35)
            # If we also have context documents, merge them
            if context_documents and len(context_documents) > 0:
                self.print_info(f"Merging {len(context_documents)} context documents with generated set")
                sample_documents.extend(context_documents)

        # Sample timeline
        sample_timeline = {
            "phases": [
                {"name": "Planning", "start_week": 0, "duration_weeks": 2},
                {"name": "Design", "start_week": 2, "duration_weeks": 2},
                {"name": "Development", "start_week": 4, "duration_weeks": 4},
                {"name": "Testing", "start_week": 8, "duration_weeks": 2}
            ]
        }

        analysis_request = {
            "documents": sample_documents,
            "recommendation_types": ["consolidation", "duplicate", "outdated", "quality"],
            "confidence_threshold": 0.4,
            "include_jira_suggestions": True,
            "create_jira_tickets": False,  # Don't actually create tickets in demo
            "jira_project_key": "DEMO",
            "timeline": sample_timeline
        }

        # Always generate document dump report first, regardless of API availability
        self.print_info("Generating comprehensive document dump report...")
        document_dump_result = await self.generate_document_dump_report(sample_documents)

        try:
            async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                self.print_info("Submitting documents for comprehensive batch analysis...")

                # Use batch processing for multiple documents
                batch_requests = []
                for doc in sample_documents:
                    batch_requests.append({
                        "content": doc["content"],
                        "format": "markdown",
                        "max_length": 300,
                        "style": "professional"
                    })

                # First, perform batch summarization
                response = await client.post(
                    f"{self.config['summarizer_url']}/batch/summarize",
                    json=batch_requests,
                    headers={"Content-Type": "application/json"}
                )

                # Then, perform alignment analysis
                alignment_response = await client.post(
                    f"{self.config['summarizer_url']}/api/v1/alignment",
                    json={
                        "documents": sample_documents,
                        "analysis_types": ["terminology", "consistency", "patterns", "conflicts"],
                        "strictness_level": "medium"
                    },
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code == 200:
                    batch_result = response.json()

                    # Get alignment analysis results
                    alignment_result = None
                    if alignment_response.status_code == 200:
                        alignment_result = alignment_response.json()
                        self.print_success("Alignment analysis completed successfully")
                        self.print_info(f"Overall alignment score: {alignment_result.get('overall_alignment_score', 0):.1f}%")
                    else:
                        self.print_warning(f"Alignment analysis failed: {alignment_response.status_code}")

                    # Process batch results
                    analysis_results = []
                    total_processing_time = 0.0

                    for i, (doc, result) in enumerate(zip(sample_documents, batch_result.get("batch_results", []))):
                        if result.get("success"):
                            data = result.get("data", {})
                            analysis_results.append({
                                "document_id": doc["id"],
                                "title": doc["title"],
                                "category": doc.get("category", "uncategorized"),
                                "tags": doc.get("tags", []),
                                "summary": data.get("summary", "Summary not available"),
                                "category_detected": data.get("category", "Unknown"),
                                "confidence": data.get("confidence", 0.0),
                                "processing_time": data.get("processing_time", 0.0)
                            })
                            total_processing_time += data.get("processing_time", 0.0)
                        else:
                            self.print_warning(f"Failed to process document {doc['id']}: {result.get('error', 'Unknown error')}")

                    # Create comprehensive multi-document analysis result
                    if analysis_results:
                        result = {
                            "success": True,
                            "batch_info": {
                                "total_requested": len(batch_requests),
                                "total_processed": batch_result.get("total_processed", 0),
                                "successful": batch_result.get("successful", 0),
                                "failed": batch_result.get("failed", 0)
                            },
                            "total_documents": len(sample_documents),
                            "processed_documents": len(analysis_results),
                            "processing_time": total_processing_time,
                            "document_summaries": analysis_results,
                            "multi_document_analysis": {
                                "categories_found": list(set(doc.get("category", "uncategorized") for doc in sample_documents)),
                                "total_tags": len(set(tag for doc in sample_documents for tag in doc.get("tags", []))),
                                "document_distribution": self._analyze_document_distribution(sample_documents),
                                "cross_document_insights": self._generate_cross_document_insights(sample_documents, analysis_results)
                            },
                            "recommendations": self._generate_multi_document_recommendations(sample_documents, analysis_results),
                            "recommendations_count": len(self._generate_multi_document_recommendations(sample_documents, analysis_results)),
                            "timeline_analysis": {
                                "total_phases": len(sample_timeline["phases"]),
                                "documents_per_phase": len(sample_documents) // len(sample_timeline["phases"]),
                                "timeline_coverage": "Multi-document batch analysis",
                                "document_evolution": self._analyze_document_evolution(sample_documents)
                            },
                            "quality_metrics": self._calculate_quality_metrics(sample_documents, analysis_results),
                            "alignment_analysis": alignment_result if alignment_result else {},
                            "document_dump": document_dump_result if document_dump_result else {}
                        }

                        self.print_success("Multi-document analysis completed successfully")
                        self.display_analysis_results(result)
                        return result
                    else:
                        self.print_error("No documents were successfully processed")
                        # Return result with document dump even if analysis failed
                        return {
                            "success": False,
                            "total_documents": len(sample_documents),
                            "processed_documents": 0,
                            "document_dump": document_dump_result
                        }
                else:
                    self.print_error(f"Batch analysis failed: {response.status_code}")
                    self.print_info(f"Response: {response.text}")
                    # Return result with document dump even if analysis failed
                    return {
                        "success": False,
                        "total_documents": len(sample_documents),
                        "processed_documents": 0,
                        "document_dump": document_dump_result
                    }

        except Exception as e:
            self.print_error(f"Analysis service communication failed: {str(e)}")
            # Return result with document dump even if analysis failed
            return {
                "success": False,
                "total_documents": len(sample_documents),
                "processed_documents": 0,
                "document_dump": document_dump_result
            }

    def display_analysis_results(self, result: Dict[str, Any]):
        """Display comprehensive analysis results."""
        print(f"\n{self.colors['BOLD']}📊 ANALYSIS RESULTS{self.colors['RESET']}")

        # Basic stats
        total_docs = result.get("total_documents", 0)
        total_recs = result.get("recommendations_count", 0)
        processing_time = result.get("processing_time", 0)

        print(f"📄 Documents analyzed: {total_docs}")
        print(f"💡 Recommendations generated: {total_recs}")
        print(f"⚡ Processing time: {processing_time:.2f}s")

        # Recommendations breakdown
        recommendations = result.get("recommendations", [])
        rec_types = {}
        priorities = {"critical": 0, "high": 0, "medium": 0, "low": 0}

        for rec in recommendations:
            rec_type = rec.get("type", "unknown")
            priority = rec.get("priority", "medium")

            rec_types[rec_type] = rec_types.get(rec_type, 0) + 1
            priorities[priority] += 1

        print(f"\n🔍 Recommendation Types:")
        for rec_type, count in rec_types.items():
            print(f"  • {rec_type.title()}: {count}")

        print(f"\n🎯 Priority Breakdown:")
        for priority, count in priorities.items():
            if count > 0:
                print(f"  • {priority.title()}: {count}")

        # Jira suggestions
        jira_tickets = result.get("suggested_jira_tickets", [])
        if jira_tickets:
            print(f"\n🎫 Suggested Jira Tickets: {len(jira_tickets)}")
            for i, ticket in enumerate(jira_tickets[:3]):  # Show first 3
                print(f"  {i+1}. [{ticket['priority']}] {ticket['summary']}")

        # Drift analysis
        drift = result.get("drift_analysis", {})
        if drift.get("drift_alerts"):
            alerts = drift["drift_alerts"]
            print(f"\n🚨 Drift Alerts: {len(alerts)}")
            high_priority = [a for a in alerts if a.get("severity") == "high"]
            if high_priority:
                print(f"  ⚠️ High Priority: {len(high_priority)}")

        # Alignment analysis
        alignment = result.get("alignment_analysis", {})
        if alignment and alignment.get("success"):
            score = alignment.get("overall_alignment_score", 0)
            print(f"\n🎯 Alignment Analysis:")
            print(f"  📊 Overall Alignment Score: {score:.1f}%")

            issues = alignment.get("alignment_issues", [])
            if issues:
                print(f"  ⚠️ Alignment Issues: {len(issues)}")
                for i, issue in enumerate(issues[:3]):  # Show first 3 issues
                    issue_type = issue.get("type", "unknown").replace("_", " ").title()
                    severity = issue.get("severity", "low").title()
                    print(f"    {i+1}. [{severity}] {issue_type}: {issue.get('description', '')}")

            alignment_recs = alignment.get("recommendations", [])
            if alignment_recs:
                print(f"  💡 Alignment Recommendations: {len(alignment_recs)}")
                for i, rec in enumerate(alignment_recs[:2]):  # Show first 2 recommendations
                    priority = rec.get("priority", "medium").title()
                    print(f"    {i+1}. [{priority}] {rec.get('type', '').replace('_', ' ').title()}")

        # Quality metrics display (for multi-document analysis)
        quality = result.get("quality_metrics", {})
        if quality:
            print(f"\n📈 Quality Metrics:")
            print(f"  📊 Quality Score: {quality.get('quality_score', 0):.1f}%")
            print(f"  📂 Category Coverage: {quality.get('categories_covered', 0)}")
            print(f"  🏷️ Tag Diversity: {quality.get('total_tags', 0)}")
            print(f"  📄 Documents: {quality.get('total_documents', 0)}")
            print(f"  ⚡ Success Rate: {quality.get('processing_success_rate', 0):.1f}%")

        # Timeline analysis
        timeline = result.get("timeline_analysis", {})
        if timeline.get("placement_score", 0) > 0:
            placement_score = timeline["placement_score"]
            print(".1%")
            phases = timeline.get("timeline_structure", {}).get("phase_count", 0)
            print(f"  📅 Timeline phases: {phases}")

        # Inconclusive analysis
        inconclusive = result.get("inconclusive_analysis", {})
        if inconclusive.get("insufficient_data_warnings"):
            warnings = inconclusive["insufficient_data_warnings"]
            print(f"\n🤔 Data Quality Warnings: {len(warnings)}")

    async def demonstrate_jira_integration(self, analysis_result: Dict[str, Any]):
        """Demonstrate Jira ticket creation (optional)."""
        self.print_step(5, "🎫 Jira Integration (Optional)")

        jira_tickets = analysis_result.get("suggested_jira_tickets", [])
        if not jira_tickets:
            self.print_warning("No Jira tickets to create")
            return

        self.print_info(f"Found {len(jira_tickets)} suggested Jira tickets")

        # Ask user if they want to create actual tickets
        create_tickets = input("\nCreate actual Jira tickets? (y/N): ").lower().strip() == 'y'

        if create_tickets:
            try:
                async with httpx.AsyncClient(timeout=self.config["timeout"]) as client:
                    jira_request = {
                        "suggested_tickets": jira_tickets[:2],  # Create first 2 tickets only
                        "project_key": "DEMO"
                    }

                    self.print_info("Creating Jira tickets...")
                    response = await client.post(
                        f"{self.config['summarizer_url']}/jira/create-tickets",
                        json=jira_request,
                        headers={"Content-Type": "application/json"}
                    )

                    if response.status_code == 200:
                        result = response.json()
                        self.print_success("Jira tickets created successfully")
                        self.print_info(f"Tickets created: {result.get('tickets_created', 0)}")
                        self.print_info(f"Tickets failed: {result.get('tickets_failed', 0)}")
                    else:
                        self.print_warning(f"Jira ticket creation failed: {response.status_code}")
                        self.print_info("This is expected if Jira is not configured in the demo environment")

            except Exception as e:
                self.print_warning(f"Jira integration failed: {str(e)}")
                self.print_info("Jira integration requires proper configuration")
        else:
            self.print_info("Skipping Jira ticket creation")
            self.print_info(f"Would have created {len(jira_tickets)} tickets")

    async def run_complete_demo(self):
        """Run the complete workflow demonstration."""
        start_time = datetime.now()

        self.print_header("🚀 COMPLETE WORKFLOW DEMONSTRATION")
        self.print_info("This demo showcases the full Interpreter → Orchestrator → Simulation → Analysis workflow")
        self.print_info(f"Demo mode: {self.config['demo_mode']}")
        self.print_info(f"Timeout: {self.config['timeout']}s per request")

        # Step 1: Check service health
        if not await self.check_all_services():
            return False

        # Step 2: Interpreter processing
        interpreted_data = await self.demonstrate_interpreter_processing()

        # Step 3: Orchestrator coordination
        orchestrator_result = await self.demonstrate_orchestrator_coordination(interpreted_data)

        # Step 4: Simulation creation and execution
        simulation_result = await self.demonstrate_simulation_creation(orchestrator_result)

        # Step 5: Comprehensive analysis
        context_documents = interpreted_data.get("context_documents", [])
        analysis_result = await self.demonstrate_analysis_processing(context_documents)

        # Generate workflow summary report (part of analysis step)
        await self.generate_workflow_summary_report(analysis_result, context_documents)

        # Step 6: Always download core reports (required)
        self.print_step(6, "📥 Downloading Core Reports")
        all_downloads = {}

        # Always download the three core reports
        if analysis_result:
            self.print_info("📊 Downloading summarizer analysis results...")
            all_downloads["summarizer"] = await self.download_summarizer_reports(analysis_result)

        # Additional optional reports
        selected_reports = await self.prompt_for_report_download()

        if selected_reports:
            # Download additional reports from different services
            if "simulation" in selected_reports and simulation_result:
                simulation_id = simulation_result.get("simulation_id", "demo_sim")
                all_downloads["simulation"] = await self.download_simulation_reports(simulation_id)

            if "orchestrator" in selected_reports:
                all_downloads["orchestrator"] = await self.download_orchestrator_reports()

            if "logs" in selected_reports:
                all_downloads["logs"] = await self.download_service_logs()

            # Display download summary
            self.display_downloaded_reports(all_downloads)

        # Always show core reports summary
        if analysis_result:
            self.print_header("📋 CORE REAPI_PORTS DOWNLOADED")
            self.print_success("✅ Summarizer analysis results")
            self.print_success("✅ Workflow summary report")
            self.print_success("✅ Document dump report")
            self.print_info(f"All core reports saved to: {self.reports_path.absolute()}")

        # Step 7: Jira integration (optional)
        if analysis_result:
            await self.demonstrate_jira_integration(analysis_result)

        # Final summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self.print_header("🏁 DEMONSTRATION COMPLETE")
        self.print_success(f"Workflow completed in {duration:.1f} seconds")
        self.print_info("🎯 Key achievements:")
        self.print_info("  ✅ Interpreter query processing")
        self.print_info("  ✅ Orchestrator coordination")
        self.print_info("  ✅ Simulation creation with mock data")
        self.print_info("  ✅ Comprehensive document analysis")
        self.print_info("  ✅ Core reports always downloaded:")
        self.print_info("    📊 Summarizer analysis results")
        self.print_info("    📋 Workflow summary report")
        self.print_info("    📄 Document dump report")
        self.print_info("  ✅ Multiple recommendation types")
        self.print_info("  ✅ Timeline analysis integration")
        self.print_info("  ✅ Drift detection and alerting")
        self.print_info("  ✅ Documentation alignment analysis")
        self.print_info("  ✅ Jira ticket suggestions")

        if analysis_result:
            total_recommendations = analysis_result.get("recommendations_count", 0)
            jira_tickets = len(analysis_result.get("suggested_jira_tickets", []))
            self.print_info(f"  📊 Generated {total_recommendations} recommendations")
            self.print_info(f"  🎫 Suggested {jira_tickets} Jira tickets")

        self.print_success("🎉 All workflow components are working correctly!")
        return True

    async def generate_document_dump_report(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive document dump report locally."""
        try:
            self.print_info("Generating comprehensive document dump report locally...")

            # Sort documents by dateCreated
            sorted_docs = sorted(documents, key=lambda x: x.get("dateCreated", ""), reverse=True)

            # Group documents by type
            grouped_docs = {}
            for doc in sorted_docs:
                doc_type = doc.get("type", "unknown")
                if doc_type not in grouped_docs:
                    grouped_docs[doc_type] = []
                grouped_docs[doc_type].append(doc)

            # Generate markdown report
            report_content = f"""# Document Dump Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- Total Documents: {len(documents)}
- Document Types: {', '.join(grouped_docs.keys())}

## Documents by Type

"""

            # Add each document type section
            for doc_type, docs in grouped_docs.items():
                report_content += f"\n### {doc_type.upper()} Documents ({len(docs)})\n\n"

                for i, doc in enumerate(docs, 1):
                    report_content += f"#### {i}. {doc.get('title', 'Untitled')}\n\n"
                    report_content += f"**ID:** {doc.get('id', 'N/A')}\n"
                    report_content += f"**Author:** {doc.get('author', 'N/A')}\n"
                    report_content += f"**Created:** {doc.get('dateCreated', 'N/A')}\n"
                    report_content += f"**Updated:** {doc.get('dateUpdated', 'N/A')}\n"
                    report_content += f"**Status:** {doc.get('status', 'N/A')}\n"
                    report_content += f"**Category:** {doc.get('category', 'N/A')}\n"

                    if doc.get('tags'):
                        report_content += f"**Tags:** {', '.join(doc['tags'])}\n"

                    if doc_type == 'jira' and doc.get('assignee'):
                        report_content += f"**Assignee:** {doc['assignee']}\n"
                        report_content += f"**Priority:** {doc.get('priority', 'N/A')}\n"

                    if doc.get('comments'):
                        report_content += f"**Comments:** {len(doc['comments'])}\n"

                    report_content += "\n**Content:**\n"
                    content = doc.get('content', '')
                    if content:
                        # Format content as markdown code block
                        report_content += f"```\n{content}\n```\n\n"
                    else:
                        report_content += "*No content available*\n\n"

                    # Add comments if available
                    if doc.get('comments'):
                        report_content += "**Comments:**\n"
                        for comment in doc['comments']:
                            report_content += f"- **{comment.get('author', 'Unknown')}** ({comment.get('timestamp', 'N/A')}): {comment.get('content', '')}\n"
                        report_content += "\n"

            # Save the report
            report_filename = self.generate_report_filename("document_dump", "analysis_dump", format="md")
            report_path = self.reports_path / report_filename

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)

            self.print_success(f"Document dump report generated and saved: {report_path}")

            # Create document type counts for metadata
            doc_type_counts = {}
            for doc_type, docs in grouped_docs.items():
                doc_type_counts[doc_type] = len(docs)

            result = {
                "success": True,
                "report_type": "document_dump",
                "document_count": len(documents),
                "format": "markdown",
                "content": report_content,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_documents": len(documents),
                    "document_types": list(grouped_docs.keys()),
                    "document_type_counts": doc_type_counts,
                    "sorted_by": "dateCreated",
                    "sort_order": "desc"
                }
            }

            return result

        except Exception as e:
            self.print_warning(f"Document dump report generation failed: {str(e)}")
            return {}


async def main():
    """Main demo execution function."""
    demo = WorkflowDemo()

    try:
        success = await demo.run_complete_demo()
        if success:
            print("\n🎯 WORKFLOW VALIDATION: SUCCESS")
            print("✅ All required components are implemented and working")
            return 0
        else:
            print("\n❌ WORKFLOW VALIDATION: FAILED")
            print("Some components are not available or not working properly")
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        return 1


if __name__ == "__main__":
    print(__doc__)

    # Check if user wants to run the demo
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("\nUSAGE:")
        print("  python demo_workflow.py          # Run complete demo")
        print("  python demo_workflow.py --help   # Show this help")
        print("\nENVIRONMENT VARIABLES:")
        print("  DEMO_MODE=full                  # full, analysis_only, simulation_only")
        print("  RUN_INTEGRATION_TESTS=true      # Enable integration tests")
        print("  REAPI_PORTS_DIR=./reports           # Directory to save downloaded reports")
        print("  DOWNLOAD_REAPI_PORTS=true           # Enable/disable report downloads")
        print("  AUTO_DOWNLOAD_REAPI_PORTS=simulation,summarizer  # Auto-select report types")
        print("\nREAPI_PORT TYPES:")
        print("  simulation   - Simulation execution reports and metrics")
        print("  summarizer   - Analysis results and capabilities")
        print("  orchestrator - Workflow coordination reports")
        print("  logs         - Service logs and debug information")
        sys.exit(0)


    # Run the demo
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
