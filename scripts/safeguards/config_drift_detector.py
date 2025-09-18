#!/usr/bin/env python3
"""
Configuration Drift Detection and Automated Correction System
=============================================================

Comprehensive system for detecting configuration drift across the ecosystem.
Automatically scans, compares, and corrects configuration inconsistencies.

Features:
- Multi-format config file detection (YAML, JSON, .env, .ini, .toml)
- Cross-environment comparison (dev, staging, prod)
- Service-specific configuration validation
- Automated correction suggestions
- CI/CD integration
- Detailed drift reports and analytics

Author: Ecosystem Hardening Framework
"""

import json
import yaml
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
from configparser import ConfigParser
import tomllib
import re
from collections import defaultdict
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ConfigFile:
    """Represents a configuration file with metadata"""
    path: Path
    format: str
    content: Dict[str, Any]
    checksum: str
    last_modified: datetime
    environment: Optional[str] = None
    service: Optional[str] = None


@dataclass
class DriftIssue:
    """Represents a configuration drift issue"""
    issue_type: str  # "missing", "inconsistent", "redundant", "outdated"
    severity: str    # "critical", "warning", "info"
    file_a: ConfigFile
    key_path: str
    file_b: Optional[ConfigFile] = None
    expected_value: Any = None
    actual_value: Any = None
    description: str = ""
    suggestion: str = ""


@dataclass
class DriftReport:
    """Comprehensive configuration drift report"""
    total_files_scanned: int
    total_issues_found: int
    critical_issues: int
    warning_issues: int
    info_issues: int
    files_by_environment: Dict[str, List[ConfigFile]]
    issues_by_type: Dict[str, List[DriftIssue]]
    issues_by_file: Dict[str, List[DriftIssue]]
    recommendations: List[str]
    scan_timestamp: datetime = field(default_factory=datetime.now)
    scan_duration: float = 0.0


class ConfigDriftDetector:
    """
    Configuration Drift Detection and Automated Correction System.

    This class provides comprehensive detection of configuration drift across
    the entire ecosystem, with automated correction capabilities.
    """

    def __init__(self, workspace_path: Optional[str] = None):
        """Initialize the configuration drift detector"""
        self.workspace_path = Path(workspace_path or Path.cwd())
        self.config_files: List[ConfigFile] = []
        self.drift_issues: List[DriftIssue] = []
        self.reports_dir = self.workspace_path / "reports" / "config_drift"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Supported configuration file patterns
        self.config_patterns = {
            "yaml": ["*.yml", "*.yaml"],
            "json": ["*.json"],
            "env": [".env*", "*.env"],
            "ini": ["*.ini", "*.cfg", "*.conf"],
            "toml": ["*.toml"],
            "properties": ["*.properties"]
        }

        # Environment-specific directories
        self.environment_dirs = {
            "development": ["config", "docker-compose.dev.yml"],
            "staging": ["config.staging", "docker-compose.staging.yml"],
            "production": ["config.prod", "docker-compose.prod.yml"]
        }

        # Critical configuration keys that should be consistent
        self.critical_keys = {
            "database": ["host", "port", "name", "user"],
            "redis": ["host", "port", "db"],
            "services": ["ports", "dependencies", "environment"],
            "security": ["secret_key", "jwt_secret", "api_keys"]
        }

        logger.info("🔍 Configuration Drift Detector initialized")

    def scan_configurations(self) -> List[ConfigFile]:
        """
        Scan all configuration files in the workspace.

        Returns:
            List of discovered ConfigFile objects
        """
        logger.info("🔍 Scanning configuration files...")

        config_files = []

        # Scan for configuration files
        for format_type, patterns in self.config_patterns.items():
            for pattern in patterns:
                for file_path in self.workspace_path.rglob(pattern):
                    # Skip certain directories
                    if any(skip in str(file_path) for skip in [
                        "__pycache__", ".git", "node_modules", ".venv", "venv"
                    ]):
                        continue

                    try:
                        config_file = self._load_config_file(file_path, format_type)
                        if config_file:
                            config_files.append(config_file)
                            logger.debug(f"✅ Loaded config: {file_path}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to load {file_path}: {e}")

        # Identify environments and services
        for config_file in config_files:
            config_file.environment = self._identify_environment(config_file.path)
            config_file.service = self._identify_service(config_file.path)

        self.config_files = config_files
        logger.info(f"🔍 Discovered {len(config_files)} configuration files")
        return config_files

    def _load_config_file(self, file_path: Path, format_type: str) -> Optional[ConfigFile]:
        """
        Load a configuration file based on its format.

        Args:
            file_path: Path to the configuration file
            format_type: Type of configuration file (yaml, json, etc.)

        Returns:
            ConfigFile object or None if loading fails
        """
        try:
            content = {}

            if format_type == "yaml":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f) or {}

            elif format_type == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)

            elif format_type == "env":
                content = self._parse_env_file(file_path)

            elif format_type == "ini":
                content = self._parse_ini_file(file_path)

            elif format_type == "toml":
                with open(file_path, 'rb') as f:
                    content = tomllib.load(f)

            elif format_type == "properties":
                content = self._parse_properties_file(file_path)

            # Generate checksum
            file_content = file_path.read_text(encoding='utf-8')
            checksum = hashlib.md5(file_content.encode()).hexdigest()

            # Get modification time
            stat = file_path.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime)

            return ConfigFile(
                path=file_path,
                format=format_type,
                content=content,
                checksum=checksum,
                last_modified=last_modified
            )

        except Exception as e:
            logger.error(f"❌ Failed to load {file_path}: {e}")
            return None

    def _parse_env_file(self, file_path: Path) -> Dict[str, str]:
        """Parse .env file format"""
        env_vars = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip().strip('"\'')
        return env_vars

    def _parse_ini_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse INI configuration file"""
        config = ConfigParser()
        config.read(file_path)

        result = {}
        for section in config.sections():
            result[section] = {}
            for key, value in config.items(section):
                result[section][key] = value

        return result

    def _parse_properties_file(self, file_path: Path) -> Dict[str, str]:
        """Parse Java properties file"""
        properties = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    properties[key.strip()] = value.strip()
        return properties

    def _identify_environment(self, file_path: Path) -> Optional[str]:
        """Identify the environment a config file belongs to"""
        path_str = str(file_path)

        if any(env in path_str.lower() for env in ["dev", "development"]):
            return "development"
        elif any(env in path_str.lower() for env in ["staging", "stage"]):
            return "staging"
        elif any(env in path_str.lower() for env in ["prod", "production"]):
            return "production"

        # Check for environment-specific files
        filename = file_path.name.lower()
        if "dev" in filename or filename.endswith(".dev"):
            return "development"
        elif "staging" in filename or "stage" in filename:
            return "staging"
        elif "prod" in filename:
            return "production"

        return "development"  # Default

    def _identify_service(self, file_path: Path) -> Optional[str]:
        """Identify the service a config file belongs to"""
        # Check if file is in a service directory
        for parent in file_path.parents:
            if parent.name.startswith("service") or parent.name in [
                "orchestrator", "doc_store", "llm_gateway", "frontend", "redis"
            ]:
                return parent.name

        # Try to infer from filename
        filename = file_path.name.lower()
        service_indicators = {
            "orchestrator": ["orchestrator", "orchestrator"],
            "doc_store": ["doc", "document"],
            "llm_gateway": ["llm", "gateway"],
            "frontend": ["frontend", "ui", "web"],
            "redis": ["redis", "cache"]
        }

        for service, indicators in service_indicators.items():
            if any(indicator in filename for indicator in indicators):
                return service

        return None

    def detect_drift(self) -> List[DriftIssue]:
        """
        Detect configuration drift across all scanned files.

        Returns:
            List of detected drift issues
        """
        logger.info("🔍 Detecting configuration drift...")

        issues = []

        # Group files by environment and service
        files_by_env = defaultdict(list)
        files_by_service = defaultdict(list)

        for config_file in self.config_files:
            if config_file.environment:
                files_by_env[config_file.environment].append(config_file)
            if config_file.service:
                files_by_service[config_file.service].append(config_file)

        # Check for environment-specific drift
        issues.extend(self._check_environment_drift(files_by_env))

        # Check for service-specific drift
        issues.extend(self._check_service_drift(files_by_service))

        # Check for critical configuration consistency
        issues.extend(self._check_critical_config_consistency())

        # Check for outdated or redundant configurations
        issues.extend(self._check_redundant_configs())

        self.drift_issues = issues
        logger.info(f"🔍 Detected {len(issues)} configuration drift issues")
        return issues

    def _check_environment_drift(self, files_by_env: Dict[str, List[ConfigFile]]) -> List[DriftIssue]:
        """Check for drift between environments"""
        issues = []

        # Compare development vs staging vs production
        environments = ["development", "staging", "production"]
        for i, env_a in enumerate(environments[:-1]):
            for env_b in environments[i+1:]:
                if env_a in files_by_env and env_b in files_by_env:
                    env_a_files = files_by_env[env_a]
                    env_b_files = files_by_env[env_b]

                    # Compare similar files between environments
                    for file_a in env_a_files:
                        for file_b in env_b_files:
                            if self._are_similar_files(file_a, file_b):
                                drift_issues = self._compare_config_files(file_a, file_b)
                                issues.extend(drift_issues)

        return issues

    def _check_service_drift(self, files_by_service: Dict[str, List[ConfigFile]]) -> List[DriftIssue]:
        """Check for drift within the same service across different files"""
        issues = []

        for service, files in files_by_service.items():
            if len(files) > 1:
                # Compare all files for the same service
                for i, file_a in enumerate(files[:-1]):
                    for file_b in files[i+1:]:
                        drift_issues = self._compare_config_files(file_a, file_b)
                        issues.extend(drift_issues)

        return issues

    def _are_similar_files(self, file_a: ConfigFile, file_b: ConfigFile) -> bool:
        """Check if two files are similar enough to compare"""
        # Same base filename (ignoring environment suffixes)
        name_a = file_a.path.name.replace(".dev", "").replace(".prod", "").replace(".staging", "")
        name_b = file_b.path.name.replace(".dev", "").replace(".prod", "").replace(".staging", "")

        return name_a == name_b and file_a.format == file_b.format

    def _compare_config_files(self, file_a: ConfigFile, file_b: ConfigFile) -> List[DriftIssue]:
        """Compare two configuration files for drift"""
        issues = []

        # Get all keys from both files
        keys_a = set(self._flatten_keys(file_a.content))
        keys_b = set(self._flatten_keys(file_b.content))

        # Find missing keys
        missing_in_b = keys_a - keys_b
        missing_in_a = keys_b - keys_a

        for key in missing_in_b:
            issues.append(DriftIssue(
                issue_type="missing",
                severity="warning",
                file_a=file_a,
                key_path=key,
                file_b=file_b,
                description=f"Key '{key}' exists in {file_a.path.name} but missing in {file_b.path.name}",
                suggestion=f"Add '{key}' to {file_b.path.name}"
            ))

        for key in missing_in_a:
            issues.append(DriftIssue(
                issue_type="missing",
                severity="warning",
                file_a=file_b,
                key_path=key,
                file_b=file_a,
                description=f"Key '{key}' exists in {file_b.path.name} but missing in {file_a.path.name}",
                suggestion=f"Add '{key}' to {file_a.path.name}"
            ))

        # Find inconsistent values
        common_keys = keys_a & keys_b
        for key in common_keys:
            value_a = self._get_nested_value(file_a.content, key)
            value_b = self._get_nested_value(file_b.content, key)

            if self._values_differ(value_a, value_b):
                severity = "critical" if self._is_critical_key(key) else "warning"
                issues.append(DriftIssue(
                    issue_type="inconsistent",
                    severity=severity,
                    file_a=file_a,
                    key_path=key,
                    file_b=file_b,
                    expected_value=value_a,
                    actual_value=value_b,
                    description=f"Inconsistent value for '{key}': {value_a} vs {value_b}",
                    suggestion=f"Standardize value for '{key}' across environments"
                ))

        return issues

    def _flatten_keys(self, data: Any, prefix: str = "") -> List[str]:
        """Flatten nested dictionary keys"""
        keys = []

        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                keys.append(full_key)
                if isinstance(value, dict):
                    keys.extend(self._flatten_keys(value, full_key))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                full_key = f"{prefix}[{i}]"
                keys.append(full_key)
                if isinstance(item, dict):
                    keys.extend(self._flatten_keys(item, full_key))

        return keys

    def _get_nested_value(self, data: Any, key_path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = key_path.split('.')
        current = data

        for key in keys:
            if '[' in key and ']' in key:
                # Handle array indexing
                base_key, index = key.split('[', 1)
                index = int(index.rstrip(']'))
                if base_key in current and isinstance(current[base_key], list):
                    current = current[base_key][index]
                else:
                    return None
            else:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None

        return current

    def _values_differ(self, value_a: Any, value_b: Any) -> bool:
        """Check if two values are different"""
        if type(value_a) != type(value_b):
            return True

        if isinstance(value_a, (int, float, str, bool)):
            return value_a != value_b

        if isinstance(value_a, dict):
            return json.dumps(value_a, sort_keys=True) != json.dumps(value_b, sort_keys=True)

        if isinstance(value_a, list):
            return sorted(value_a) != sorted(value_b)

        return str(value_a) != str(value_b)

    def _is_critical_key(self, key: str) -> bool:
        """Check if a key is considered critical"""
        key_lower = key.lower()
        for category, keys in self.critical_keys.items():
            if any(critical_key in key_lower for critical_key in keys):
                return True
        return False

    def _check_critical_config_consistency(self) -> List[DriftIssue]:
        """Check consistency of critical configuration values"""
        issues = []

        # Group files by service
        service_files = defaultdict(list)
        for config_file in self.config_files:
            if config_file.service:
                service_files[config_file.service].append(config_file)

        for service, files in service_files.items():
            if len(files) <= 1:
                continue

            # Check critical values across files for same service
            for category, keys in self.critical_keys.items():
                for key in keys:
                    values = []
                    for file in files:
                        value = self._get_nested_value(file.content, key)
                        if value is not None:
                            values.append((file, value))

                    if len(values) > 1:
                        # Check if all values are the same
                        first_value = values[0][1]
                        for file, value in values[1:]:
                            if self._values_differ(first_value, value):
                                issues.append(DriftIssue(
                                    issue_type="inconsistent",
                                    severity="critical",
                                    file_a=values[0][0],
                                    key_path=key,
                                    file_b=file,
                                    expected_value=first_value,
                                    actual_value=value,
                                    description=f"Critical config '{key}' differs across {service} files",
                                    suggestion=f"Ensure '{key}' is consistent across all {service} configuration files"
                                ))

        return issues

    def _check_redundant_configs(self) -> List[DriftIssue]:
        """Check for redundant or outdated configuration files"""
        issues = []

        # Check for duplicate configurations
        file_checksums = defaultdict(list)
        for config_file in self.config_files:
            file_checksums[config_file.checksum].append(config_file)

        for checksum, files in file_checksums.items():
            if len(files) > 1:
                # Multiple files with same content
                for i in range(1, len(files)):
                    issues.append(DriftIssue(
                        issue_type="redundant",
                        severity="info",
                        file_a=files[0],
                        key_path="",
                        file_b=files[i],
                        description=f"Duplicate configuration content in {files[i].path.name}",
                        suggestion=f"Consider consolidating duplicate configuration files"
                    ))

        # Check for potentially outdated files
        for config_file in self.config_files:
            days_old = (datetime.now() - config_file.last_modified).days
            if days_old > 90:  # Older than 3 months
                issues.append(DriftIssue(
                    issue_type="outdated",
                    severity="warning",
                    file_a=config_file,
                    key_path="",
                    description=f"Configuration file {config_file.path.name} hasn't been modified in {days_old} days",
                    suggestion="Review if this configuration file is still needed"
                ))

        return issues

    def generate_report(self) -> DriftReport:
        """
        Generate a comprehensive drift report.

        Returns:
            DriftReport with detailed analysis
        """
        # Group issues
        issues_by_type = defaultdict(list)
        issues_by_file = defaultdict(list)
        files_by_environment = defaultdict(list)

        for issue in self.drift_issues:
            issues_by_type[issue.issue_type].append(issue)
            issues_by_file[str(issue.file_a.path)].append(issue)

        for config_file in self.config_files:
            if config_file.environment:
                files_by_environment[config_file.environment].append(config_file)

        # Count issues by severity
        critical_issues = sum(1 for issue in self.drift_issues if issue.severity == "critical")
        warning_issues = sum(1 for issue in self.drift_issues if issue.severity == "warning")
        info_issues = sum(1 for issue in self.drift_issues if issue.severity == "info")

        # Generate recommendations
        recommendations = self._generate_recommendations()

        report = DriftReport(
            total_files_scanned=len(self.config_files),
            total_issues_found=len(self.drift_issues),
            critical_issues=critical_issues,
            warning_issues=warning_issues,
            info_issues=info_issues,
            files_by_environment=dict(files_by_environment),
            issues_by_type=dict(issues_by_type),
            issues_by_file=dict(issues_by_file),
            recommendations=recommendations
        )

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on detected issues"""
        recommendations = []

        if not self.drift_issues:
            recommendations.append("✅ No configuration drift detected - ecosystem is well-configured!")
            return recommendations

        critical_count = sum(1 for issue in self.drift_issues if issue.severity == "critical")
        if critical_count > 0:
            recommendations.append(f"🔴 CRITICAL: {critical_count} critical configuration issues found - fix immediately")

        # Environment-specific recommendations
        env_issues = defaultdict(int)
        for issue in self.drift_issues:
            if issue.file_a.environment:
                env_issues[issue.file_a.environment] += 1

        for env, count in env_issues.items():
            if count > 0:
                recommendations.append(f"📋 {env.upper()}: {count} configuration issues detected")

        # Issue type recommendations
        issue_types = set(issue.issue_type for issue in self.drift_issues)
        if "inconsistent" in issue_types:
            recommendations.append("🔧 Standardize critical configuration values across environments")
        if "missing" in issue_types:
            recommendations.append("➕ Add missing configuration keys to maintain consistency")
        if "redundant" in issue_types:
            recommendations.append("🗂️ Consolidate duplicate configuration files")
        if "outdated" in issue_types:
            recommendations.append("🗑️ Review and remove outdated configuration files")

        # General recommendations
        recommendations.extend([
            "📊 Implement automated configuration drift monitoring in CI/CD",
            "🔒 Use configuration management tools (Ansible, Terraform, etc.)",
            "📝 Document configuration standards and best practices",
            "🔄 Regular configuration audits and cleanup"
        ])

        return recommendations

    def print_report(self, report: DriftReport, verbose: bool = True):
        """
        Print a formatted drift report.

        Args:
            report: DriftReport to print
            verbose: Whether to include detailed issue information
        """
        print("\n" + "="*80)
        print("📊 CONFIGURATION DRIFT DETECTION REPORT")
        print("="*80)
        print(f"📁 Total Files Scanned: {report.total_files_scanned}")
        print(f"⚠️  Total Issues Found: {report.total_issues_found}")
        print(f"🔴 Critical Issues: {report.critical_issues}")
        print(f"🟡 Warning Issues: {report.warning_issues}")
        print(f"ℹ️  Info Issues: {report.info_issues}")

        if report.files_by_environment:
            print("\n🏗️  Files by Environment:")
            for env, files in report.files_by_environment.items():
                print(f"  • {env}: {len(files)} files")

        if verbose and report.issues_by_type:
            print("\n📋 Issues by Type:")
            for issue_type, issues in report.issues_by_type.items():
                print(f"  • {issue_type}: {len(issues)} issues")

        if verbose and report.total_issues_found > 0:
            print("\n🔍 Top Issues:")
            # Show top 10 most critical issues
            sorted_issues = sorted(
                report.issues_by_type.get("critical", []) +
                report.issues_by_type.get("warning", []) +
                report.issues_by_type.get("info", []),
                key=lambda x: {"critical": 3, "warning": 2, "info": 1}[x.severity],
                reverse=True
            )

            for i, issue in enumerate(sorted_issues[:10]):
                severity_icon = {"critical": "🔴", "warning": "🟡", "info": "ℹ️"}[issue.severity]
                print(f"  {i+1}. {severity_icon} {issue.description}")

        if report.recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for rec in report.recommendations:
                print(f"  • {rec}")

        print("="*80)

    def save_report(self, report: DriftReport, filename: Optional[str] = None) -> Path:
        """
        Save drift report to JSON file.

        Args:
            report: DriftReport to save
            filename: Optional custom filename

        Returns:
            Path to saved report file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"config_drift_report_{timestamp}.json"

        report_path = self.reports_dir / filename

        # Convert to serializable format
        report_dict = {
            "total_files_scanned": report.total_files_scanned,
            "total_issues_found": report.total_issues_found,
            "critical_issues": report.critical_issues,
            "warning_issues": report.warning_issues,
            "info_issues": report.info_issues,
            "scan_timestamp": report.scan_timestamp.isoformat(),
            "scan_duration": report.scan_duration,
            "recommendations": report.recommendations,
            "files_by_environment": {
                env: [{"path": str(f.path), "format": f.format, "checksum": f.checksum}
                     for f in files]
                for env, files in report.files_by_environment.items()
            },
            "issues_by_type": {
                issue_type: [{
                    "severity": issue.severity,
                    "file_a": str(issue.file_a.path),
                    "file_b": str(issue.file_b.path) if issue.file_b else None,
                    "key_path": issue.key_path,
                    "description": issue.description,
                    "suggestion": issue.suggestion
                } for issue in issues]
                for issue_type, issues in report.issues_by_type.items()
            }
        }

        with open(report_path, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)

        logger.info(f"💾 Report saved to: {report_path}")
        return report_path

    def apply_corrections(self, issues: List[DriftIssue], auto_apply: bool = False) -> Dict[str, Any]:
        """
        Apply automated corrections for detected issues.

        Args:
            issues: List of issues to correct
            auto_apply: Whether to apply corrections automatically

        Returns:
            Dictionary with correction results
        """
        logger.info("🔧 Applying configuration corrections...")

        results = {
            "total_corrections_attempted": 0,
            "successful_corrections": 0,
            "failed_corrections": 0,
            "corrections": []
        }

        for issue in issues:
            if issue.issue_type == "missing" and auto_apply:
                # Try to add missing keys
                success = self._add_missing_key(issue)
                results["total_corrections_attempted"] += 1

                if success:
                    results["successful_corrections"] += 1
                else:
                    results["failed_corrections"] += 1

                results["corrections"].append({
                    "issue": issue.description,
                    "action": "add_missing_key",
                    "success": success
                })

        logger.info(f"🔧 Applied {results['successful_corrections']} corrections")
        return results

    def _add_missing_key(self, issue: DriftIssue) -> bool:
        """
        Add a missing key to a configuration file.

        Args:
            issue: The drift issue to correct

        Returns:
            True if correction was successful
        """
        try:
            if issue.expected_value is None:
                return False

            # Load current content
            with open(issue.file_a.path, 'r', encoding='utf-8') as f:
                if issue.file_a.format == "yaml":
                    content = yaml.safe_load(f) or {}
                elif issue.file_a.format == "json":
                    content = json.load(f)
                else:
                    return False

            # Add the missing key
            self._set_nested_value(content, issue.key_path, issue.expected_value)

            # Write back to file
            with open(issue.file_a.path, 'w', encoding='utf-8') as f:
                if issue.file_a.format == "yaml":
                    yaml.dump(content, f, default_flow_style=False)
                elif issue.file_a.format == "json":
                    json.dump(content, f, indent=2)

            logger.info(f"✅ Added missing key '{issue.key_path}' to {issue.file_a.path}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to add missing key: {e}")
            return False

    def _set_nested_value(self, data: Dict[str, Any], key_path: str, value: Any):
        """Set a value in nested dictionary using dot notation"""
        keys = key_path.split('.')
        current = data

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value


def main():
    """Main entry point for configuration drift detection"""
    import argparse

    parser = argparse.ArgumentParser(description="Configuration Drift Detector")
    parser.add_argument("--workspace", help="Workspace path")
    parser.add_argument("--scan-only", action="store_true", help="Only scan, don't detect drift")
    parser.add_argument("--auto-correct", action="store_true", help="Automatically apply corrections")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--save-report", action="store_true", help="Save detailed report")
    parser.add_argument("--report-file", help="Custom report filename")

    args = parser.parse_args()

    # Initialize detector
    detector = ConfigDriftDetector(args.workspace)

    try:
        print("🔍 Configuration Drift Detector")
        print("=" * 50)

        # Scan configurations
        config_files = detector.scan_configurations()

        if not config_files:
            print("❌ No configuration files found!")
            return 1

        if args.scan_only:
            print(f"📁 Found {len(config_files)} configuration files:")
            for config_file in config_files:
                env = config_file.environment or "unknown"
                service = config_file.service or "unknown"
                print(f"  • {config_file.path.name} ({config_file.format}) - {env}/{service}")
            return 0

        # Detect drift
        issues = detector.detect_drift()

        # Generate and print report
        report = detector.generate_report()
        detector.print_report(report, args.verbose)

        # Save report if requested
        if args.save_report:
            report_path = detector.save_report(report, args.report_file)
            print(f"💾 Report saved: {report_path}")

        # Apply corrections if requested
        if args.auto_correct and issues:
            print("\n🔧 Applying automatic corrections...")
            correction_results = detector.apply_corrections(issues, True)
            print(f"✅ Applied {correction_results['successful_corrections']} corrections")

        # Return appropriate exit code
        if report.critical_issues > 0:
            print("❌ CRITICAL: Configuration drift issues found")
            return 1
        elif report.warning_issues > 0:
            print("⚠️ WARNING: Configuration inconsistencies detected")
            return 0
        else:
            print("✅ No critical configuration drift detected")
            return 0

    except KeyboardInterrupt:
        print("\n⚠️ Scan interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Scan failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
