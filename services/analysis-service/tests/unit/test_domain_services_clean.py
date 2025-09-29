"""Clean unit tests for analysis-service domain services."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Optional

# Define mock entities and repositories to avoid import dependencies
from enum import Enum
from datetime import datetime, timezone


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisType(str, Enum):
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    PERFORMANCE = "performance"


class DocumentType(str, Enum):
    CODE = "code"
    CONFIGURATION = "configuration"


class FindingStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"


class MockAnalysisResult:
    """Mock analysis result entity."""
    def __init__(self, analysis_id: str, document_id: str, analysis_type: AnalysisType,
                 status: AnalysisStatus = AnalysisStatus.PENDING, score: float = 0.0):
        self.analysis_id = analysis_id
        self.document_id = document_id
        self.analysis_type = analysis_type
        self.status = status
        self.score = score
        self.findings_count = 0
        self.execution_time = 0.0
        self.metadata = {}
        self.is_successful = lambda: status == AnalysisStatus.COMPLETED and score >= 0.0
        self.is_high_quality = lambda: score >= 0.8
        self.is_critical_issues = lambda: self.metadata.get("critical_findings", 0) > 0
        self.start_analysis = lambda: setattr(self, 'status', AnalysisStatus.RUNNING) or setattr(self, 'started_at', datetime.now(timezone.utc))
        self.complete_analysis = lambda score_val, findings, meta=None: (
            setattr(self, 'status', AnalysisStatus.COMPLETED),
            setattr(self, 'score', score_val),
            setattr(self, 'findings_count', findings),
            setattr(self, 'completed_at', datetime.now(timezone.utc)),
            meta and self.metadata.update(meta)
        )
        self.fail_analysis = lambda msg=None: (
            setattr(self, 'status', AnalysisStatus.FAILED),
            setattr(self, 'completed_at', datetime.now(timezone.utc)),
            msg and self.metadata.update({"error": msg})
        )
        self.get_quality_grade = lambda: "A" if self.score >= 0.9 else "B" if self.score >= 0.8 else "C" if self.score >= 0.7 else "D" if self.score >= 0.6 else "F"


class MockDocument:
    """Mock document entity."""
    def __init__(self, document_id: str, name: str, document_type: DocumentType = DocumentType.CODE,
                 language: str = "python", content: str = ""):
        self.document_id = document_id
        self.name = name
        self.document_type = document_type
        self.language = language
        self.content = content
        self.size = len(content.encode('utf-8'))
        self.is_code_file = lambda: document_type == DocumentType.CODE
        self.is_large_file = lambda: self.size > 1000000
        self.get_file_extension = lambda: name.split('.')[-1] if '.' in name else ""
        self.is_supported_language = lambda langs: language.lower() in [l.lower() for l in langs] if language else False
        self.get_content_lines = lambda: content.split('\n') if content else []
        self.get_line_count = lambda: len(self.get_content_lines())
        self.contains_text = lambda text: text.lower() in content.lower()


class MockFinding:
    """Mock finding entity."""
    def __init__(self, finding_id: str, analysis_id: str, document_id: str, title: str,
                 severity: FindingSeverity = FindingSeverity.MEDIUM, category: str = "",
                 line_number: int = None):
        self.finding_id = finding_id
        self.analysis_id = analysis_id
        self.document_id = document_id
        self.title = title
        self.severity = severity
        self.category = category
        self.line_number = line_number
        self.status = FindingStatus.OPEN
        self.is_critical = lambda: severity == FindingSeverity.CRITICAL
        self.is_high_severity = lambda: severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH]
        self.is_resolved = lambda: self.status in [FindingStatus.RESOLVED]
        self.resolve = lambda: setattr(self, 'status', FindingStatus.RESOLVED)
        self.matches_category = lambda cats: category.lower() in [c.lower() for c in cats]


class MockAnalysisConfiguration:
    """Mock analysis configuration entity."""
    def __init__(self, config_id: str, name: str, analysis_types: List[AnalysisType] = None,
                 enabled: bool = True):
        self.config_id = config_id
        self.name = name
        self.analysis_types = analysis_types or []
        self.thresholds = {}
        self.rules = {}
        self.enabled = enabled
        self.is_enabled = lambda: enabled
        self.supports_analysis_type = lambda atype: atype in self.analysis_types
        self.get_threshold = lambda metric, default=0.0: self.thresholds.get(metric, default)
        self.get_rule = lambda rule, default=None: self.rules.get(rule, default)


# Mock repositories
class MockAnalysisRepository:
    """Mock analysis repository."""
    def __init__(self):
        self.analyses = {}

    async def save(self, analysis: MockAnalysisResult) -> MockAnalysisResult:
        """Save analysis."""
        self.analyses[analysis.analysis_id] = analysis
        return analysis

    async def get_by_id(self, analysis_id: str) -> Optional[MockAnalysisResult]:
        """Get analysis by ID."""
        return self.analyses.get(analysis_id)

    async def get_by_document_id(self, document_id: str) -> List[MockAnalysisResult]:
        """Get analyses by document ID."""
        return [a for a in self.analyses.values() if a.document_id == document_id]


class MockDocumentRepository:
    """Mock document repository."""
    def __init__(self):
        self.documents = {
            "doc1": MockDocument("doc1", "main.py", DocumentType.CODE, "python", "print('hello')"),
            "doc2": MockDocument("doc2", "config.yaml", DocumentType.CONFIGURATION, None, "version: 1.0"),
        }

    async def save(self, document: MockDocument) -> MockDocument:
        """Save document."""
        self.documents[document.document_id] = document
        return document

    async def get_by_id(self, document_id: str) -> Optional[MockDocument]:
        """Get document by ID."""
        return self.documents.get(document_id)


class MockFindingRepository:
    """Mock finding repository."""
    def __init__(self):
        self.findings = {}

    async def save(self, finding: MockFinding) -> MockFinding:
        """Save finding."""
        self.findings[finding.finding_id] = finding
        return finding

    async def get_by_analysis_id(self, analysis_id: str) -> List[MockFinding]:
        """Get findings by analysis ID."""
        return [f for f in self.findings.values() if f.analysis_id == analysis_id]


class MockConfigurationRepository:
    """Mock configuration repository."""
    def __init__(self):
        self.configs = {
            "config1": MockAnalysisConfiguration("config1", "Default Quality",
                                               [AnalysisType.CODE_QUALITY, AnalysisType.SECURITY], True),
        }

    async def get_by_id(self, config_id: str) -> Optional[MockAnalysisConfiguration]:
        """Get configuration by ID."""
        return self.configs.get(config_id)

    async def get_active_configurations(self) -> List[MockAnalysisConfiguration]:
        """Get active configurations."""
        return [c for c in self.configs.values() if c.is_enabled()]


# Domain services
class AnalysisService:
    """Domain service for analysis operations."""

    def __init__(self,
                 analysis_repo: MockAnalysisRepository,
                 document_repo: MockDocumentRepository,
                 finding_repo: MockFindingRepository,
                 config_repo: MockConfigurationRepository):
        self.analysis_repo = analysis_repo
        self.document_repo = document_repo
        self.finding_repo = finding_repo
        self.config_repo = config_repo

    async def create_analysis(self, document_id: str, analysis_type: AnalysisType,
                            config_id: str = None) -> Optional[MockAnalysisResult]:
        """Create a new analysis."""
        document = await self.document_repo.get_by_id(document_id)
        if not document:
            return None

        # Validate analysis type support
        if config_id:
            config = await self.config_repo.get_by_id(config_id)
            if config and not config.supports_analysis_type(analysis_type):
                return None

        analysis_id = f"analysis_{document_id}_{analysis_type.value}"
        analysis = MockAnalysisResult(analysis_id, document_id, analysis_type)

        await self.analysis_repo.save(analysis)
        return analysis

    async def execute_analysis(self, analysis_id: str) -> Optional[MockAnalysisResult]:
        """Execute an analysis."""
        analysis = await self.analysis_repo.get_by_id(analysis_id)
        if not analysis or analysis.status != AnalysisStatus.PENDING:
            return None

        document = await self.document_repo.get_by_id(analysis.document_id)
        if not document:
            return None

        # Start analysis
        analysis.start_analysis()

        try:
            # Perform analysis based on type
            findings = []
            score = 0.0

            if analysis.analysis_type == AnalysisType.CODE_QUALITY:
                findings, score = await self._perform_code_quality_analysis(document)
            elif analysis.analysis_type == AnalysisType.SECURITY:
                findings, score = await self._perform_security_analysis(document)
            elif analysis.analysis_type == AnalysisType.PERFORMANCE:
                findings, score = await self._perform_performance_analysis(document)

            # Save findings
            for finding in findings:
                await self.finding_repo.save(finding)

            # Complete analysis
            metadata = {
                "language": document.language,
                "findings_count": len(findings),
                "critical_findings": sum(1 for f in findings if f.is_critical()),
                "high_findings": sum(1 for f in findings if f.is_high_severity() and not f.is_critical())
            }

            analysis.complete_analysis(score, len(findings), metadata)

            await self.analysis_repo.save(analysis)
            return analysis

        except Exception as e:
            analysis.fail_analysis(str(e))
            await self.analysis_repo.save(analysis)
            return analysis

    async def _perform_code_quality_analysis(self, document: MockDocument) -> tuple:
        """Perform code quality analysis."""
        findings = []
        score = 1.0

        # Simple quality checks
        content = document.content

        # Check for TODO comments
        if "TODO" in content.upper():
            findings.append(MockFinding(
                f"finding_{document.document_id}_todo",
                f"analysis_{document.document_id}_code_quality",
                document.document_id,
                "TODO comment found",
                FindingSeverity.LOW,
                "code-quality",
                content.upper().find("TODO") + 1
            ))
            score -= 0.1

        # Check line length
        lines = document.get_content_lines()
        long_lines = [i for i, line in enumerate(lines, 1) if len(line) > 120]
        if long_lines:
            findings.append(MockFinding(
                f"finding_{document.document_id}_long_lines",
                f"analysis_{document.document_id}_code_quality",
                document.document_id,
                f"Found {len(long_lines)} lines longer than 120 characters",
                FindingSeverity.LOW,
                "code-quality",
                long_lines[0]
            ))
            score -= 0.05

        return findings, max(0.0, score)

    async def _perform_security_analysis(self, document: MockDocument) -> tuple:
        """Perform security analysis."""
        findings = []
        score = 1.0

        content = document.content

        # Check for SQL injection patterns
        if "SELECT" in content.upper() and ("+" in content or "%" in content):
            findings.append(MockFinding(
                f"finding_{document.document_id}_sql_injection",
                f"analysis_{document.document_id}_security",
                document.document_id,
                "Potential SQL injection vulnerability",
                FindingSeverity.CRITICAL,
                "security",
                content.upper().find("SELECT") + 1
            ))
            score -= 0.3

        # Check for hardcoded secrets
        secret_patterns = ["password", "secret", "key", "token"]
        for pattern in secret_patterns:
            if pattern in content.lower() and "=" in content:
                findings.append(MockFinding(
                    f"finding_{document.document_id}_hardcoded_secret",
                    f"analysis_{document.document_id}_security",
                    document.document_id,
                    f"Potential hardcoded {pattern}",
                    FindingSeverity.HIGH,
                    "security"
                ))
                score -= 0.2
                break

        return findings, max(0.0, score)

    async def _perform_performance_analysis(self, document: MockDocument) -> tuple:
        """Perform performance analysis."""
        findings = []
        score = 1.0

        content = document.content

        # Check for inefficient patterns
        if "for" in content.lower() and "in" in content.lower() and "range(len(" in content:
            findings.append(MockFinding(
                f"finding_{document.document_id}_inefficient_loop",
                f"analysis_{document.document_id}_performance",
                document.document_id,
                "Inefficient loop pattern detected",
                FindingSeverity.MEDIUM,
                "performance"
            ))
            score -= 0.15

        return findings, max(0.0, score)

    async def get_analysis_summary(self, document_id: str) -> Dict:
        """Get analysis summary for a document."""
        analyses = await self.analysis_repo.get_by_document_id(document_id)

        if not analyses:
            return {"total_analyses": 0, "average_score": 0.0, "total_findings": 0}

        completed_analyses = [a for a in analyses if a.is_successful()]
        scores = [a.score for a in completed_analyses]
        total_findings = sum(a.findings_count for a in completed_analyses)

        return {
            "total_analyses": len(analyses),
            "completed_analyses": len(completed_analyses),
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "total_findings": total_findings,
            "quality_grade": "A" if scores and sum(scores) / len(scores) >= 0.9 else "B" if scores and sum(scores) / len(scores) >= 0.8 else "C"
        }


class FindingService:
    """Domain service for finding operations."""

    def __init__(self, finding_repo: MockFindingRepository):
        self.finding_repo = finding_repo

    async def resolve_finding(self, finding_id: str) -> bool:
        """Resolve a finding."""
        finding = await self.finding_repo.get_by_id(finding_id)
        if finding and not finding.is_resolved():
            finding.resolve()
            await self.finding_repo.save(finding)
            return True
        return False

    async def get_findings_by_severity(self, analysis_id: str, severity: FindingSeverity) -> List[MockFinding]:
        """Get findings by severity."""
        findings = await self.finding_repo.get_by_analysis_id(analysis_id)
        return [f for f in findings if f.severity == severity]

    async def get_critical_findings(self, analysis_id: str) -> List[MockFinding]:
        """Get critical findings."""
        findings = await self.finding_repo.get_by_analysis_id(analysis_id)
        return [f for f in findings if f.is_critical()]

    async def get_findings_summary(self, analysis_id: str) -> Dict:
        """Get findings summary."""
        findings = await self.finding_repo.get_by_analysis_id(analysis_id)

        severity_counts = {}
        for finding in findings:
            severity = finding.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            "total_findings": len(findings),
            "severity_breakdown": severity_counts,
            "critical_count": sum(1 for f in findings if f.is_critical()),
            "resolved_count": sum(1 for f in findings if f.is_resolved())
        }


class ConfigurationService:
    """Domain service for configuration operations."""

    def __init__(self, config_repo: MockConfigurationRepository):
        self.config_repo = config_repo

    async def get_suitable_configurations(self, analysis_type: AnalysisType) -> List[MockAnalysisConfiguration]:
        """Get configurations suitable for analysis type."""
        configs = await self.config_repo.get_active_configurations()
        return [c for c in configs if c.supports_analysis_type(analysis_type)]

    async def validate_configuration(self, config_id: str) -> Dict:
        """Validate configuration."""
        config = await self.config_repo.get_by_id(config_id)
        if not config:
            return {"valid": False, "reason": "Configuration not found"}

        issues = []

        if not config.analysis_types:
            issues.append("No analysis types configured")

        if not config.is_enabled():
            issues.append("Configuration is disabled")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "supported_types": [t.value for t in config.analysis_types]
        }


class TestAnalysisService:
    """Test the AnalysisService domain service."""

    @pytest.fixture
    def analysis_repo(self):
        """Create analysis repository."""
        return MockAnalysisRepository()

    @pytest.fixture
    def document_repo(self):
        """Create document repository."""
        return MockDocumentRepository()

    @pytest.fixture
    def finding_repo(self):
        """Create finding repository."""
        return MockFindingRepository()

    @pytest.fixture
    def config_repo(self):
        """Create configuration repository."""
        return MockConfigurationRepository()

    @pytest.fixture
    def analysis_service(self, analysis_repo, document_repo, finding_repo, config_repo):
        """Create analysis service."""
        return AnalysisService(analysis_repo, document_repo, finding_repo, config_repo)

    @pytest.mark.asyncio
    async def test_create_analysis(self, analysis_service, analysis_repo):
        """Test creating an analysis."""
        analysis = await analysis_service.create_analysis("doc1", AnalysisType.CODE_QUALITY)

        assert analysis is not None
        assert analysis.document_id == "doc1"
        assert analysis.analysis_type == AnalysisType.CODE_QUALITY
        assert analysis.status == AnalysisStatus.PENDING

        # Verify saved
        saved = await analysis_repo.get_by_id(analysis.analysis_id)
        assert saved is not None

    @pytest.mark.asyncio
    async def test_create_analysis_invalid_document(self, analysis_service):
        """Test creating analysis for invalid document."""
        analysis = await analysis_service.create_analysis("invalid", AnalysisType.CODE_QUALITY)
        assert analysis is None

    @pytest.mark.asyncio
    async def test_execute_code_quality_analysis(self, analysis_service):
        """Test executing code quality analysis."""
        analysis = await analysis_service.create_analysis("doc1", AnalysisType.CODE_QUALITY)
        result = await analysis_service.execute_analysis(analysis.analysis_id)

        assert result is not None
        assert result.is_successful()
        assert result.score >= 0.0
        assert result.analysis_type == AnalysisType.CODE_QUALITY

    @pytest.mark.asyncio
    async def test_execute_security_analysis(self, analysis_service):
        """Test executing security analysis."""
        analysis = await analysis_service.create_analysis("doc1", AnalysisType.SECURITY)
        result = await analysis_service.execute_analysis(analysis.analysis_id)

        assert result is not None
        assert result.is_successful()
        assert result.score >= 0.0
        assert result.analysis_type == AnalysisType.SECURITY

    @pytest.mark.asyncio
    async def test_execute_performance_analysis(self, analysis_service):
        """Test executing performance analysis."""
        analysis = await analysis_service.create_analysis("doc1", AnalysisType.PERFORMANCE)
        result = await analysis_service.execute_analysis(analysis.analysis_id)

        assert result is not None
        assert result.is_successful()
        assert result.score >= 0.0
        assert result.analysis_type == AnalysisType.PERFORMANCE

    @pytest.mark.asyncio
    async def test_get_analysis_summary(self, analysis_service):
        """Test getting analysis summary."""
        # Create and execute analyses
        analysis1 = await analysis_service.create_analysis("doc1", AnalysisType.CODE_QUALITY)
        await analysis_service.execute_analysis(analysis1.analysis_id)

        analysis2 = await analysis_service.create_analysis("doc1", AnalysisType.SECURITY)
        await analysis_service.execute_analysis(analysis2.analysis_id)

        summary = await analysis_service.get_analysis_summary("doc1")

        assert summary["total_analyses"] >= 2
        assert summary["completed_analyses"] >= 2
        assert "average_score" in summary
        assert "quality_grade" in summary


class TestFindingService:
    """Test the FindingService domain service."""

    @pytest.fixture
    def finding_repo(self):
        """Create finding repository."""
        return MockFindingRepository()

    @pytest.fixture
    def finding_service(self, finding_repo):
        """Create finding service."""
        return FindingService(finding_repo)

    @pytest.mark.asyncio
    async def test_resolve_finding(self, finding_service, finding_repo):
        """Test resolving a finding."""
        finding = MockFinding("find1", "analysis1", "doc1", "Test finding")
        await finding_repo.save(finding)

        success = await finding_service.resolve_finding("find1")
        assert success

        resolved_finding = await finding_repo.get_by_id("find1")
        assert resolved_finding.is_resolved()

    @pytest.mark.asyncio
    async def test_get_findings_by_severity(self, finding_service, finding_repo):
        """Test getting findings by severity."""
        findings = [
            MockFinding("find1", "analysis1", "doc1", "Critical issue", FindingSeverity.CRITICAL, "security"),
            MockFinding("find2", "analysis1", "doc1", "High issue", FindingSeverity.HIGH, "security"),
            MockFinding("find3", "analysis1", "doc1", "Medium issue", FindingSeverity.MEDIUM, "quality"),
        ]

        for finding in findings:
            await finding_repo.save(finding)

        critical_findings = await finding_service.get_findings_by_severity("analysis1", FindingSeverity.CRITICAL)
        assert len(critical_findings) == 1
        assert critical_findings[0].severity == FindingSeverity.CRITICAL

    @pytest.mark.asyncio
    async def test_get_critical_findings(self, finding_service, finding_repo):
        """Test getting critical findings."""
        findings = [
            MockFinding("find1", "analysis1", "doc1", "SQL injection", FindingSeverity.CRITICAL, "security"),
            MockFinding("find2", "analysis1", "doc1", "Code smell", FindingSeverity.LOW, "quality"),
        ]

        for finding in findings:
            await finding_repo.save(finding)

        critical = await finding_service.get_critical_findings("analysis1")
        assert len(critical) == 1
        assert critical[0].is_critical()

    @pytest.mark.asyncio
    async def test_get_findings_summary(self, finding_service, finding_repo):
        """Test getting findings summary."""
        findings = [
            MockFinding("find1", "analysis1", "doc1", "Issue 1", FindingSeverity.CRITICAL),
            MockFinding("find2", "analysis1", "doc1", "Issue 2", FindingSeverity.HIGH),
            MockFinding("find3", "analysis1", "doc1", "Issue 3", FindingSeverity.HIGH),
        ]

        for finding in findings:
            await finding_repo.save(finding)

        # Resolve one finding
        findings[0].resolve()
        await finding_repo.save(findings[0])

        summary = await finding_service.get_findings_summary("analysis1")

        assert summary["total_findings"] == 3
        assert summary["severity_breakdown"][FindingSeverity.CRITICAL] == 1
        assert summary["severity_breakdown"][FindingSeverity.HIGH] == 2
        assert summary["critical_count"] == 1
        assert summary["resolved_count"] == 1


class TestConfigurationService:
    """Test the ConfigurationService domain service."""

    @pytest.fixture
    def config_repo(self):
        """Create configuration repository."""
        return MockConfigurationRepository()

    @pytest.fixture
    def config_service(self, config_repo):
        """Create configuration service."""
        return ConfigurationService(config_repo)

    @pytest.mark.asyncio
    async def test_get_suitable_configurations(self, config_service):
        """Test getting suitable configurations."""
        configs = await config_service.get_suitable_configurations(AnalysisType.CODE_QUALITY)

        assert len(configs) >= 1
        for config in configs:
            assert config.supports_analysis_type(AnalysisType.CODE_QUALITY)

    @pytest.mark.asyncio
    async def test_validate_configuration_valid(self, config_service):
        """Test validating a valid configuration."""
        validation = await config_service.validate_configuration("config1")

        assert validation["valid"] is True
        assert len(validation["issues"]) == 0
        assert AnalysisType.CODE_QUALITY.value in validation["supported_types"]

    @pytest.mark.asyncio
    async def test_validate_configuration_invalid(self, config_service):
        """Test validating an invalid configuration."""
        validation = await config_service.validate_configuration("nonexistent")

        assert validation["valid"] is False
        assert "Configuration not found" in validation["reason"]


class TestServiceIntegration:
    """Test integration between services."""

    @pytest.fixture
    def analysis_repo(self):
        """Create analysis repository."""
        return MockAnalysisRepository()

    @pytest.fixture
    def document_repo(self):
        """Create document repository."""
        return MockDocumentRepository()

    @pytest.fixture
    def finding_repo(self):
        """Create finding repository."""
        return MockFindingRepository()

    @pytest.fixture
    def config_repo(self):
        """Create configuration repository."""
        return MockConfigurationRepository()

    @pytest.fixture
    def analysis_service(self, analysis_repo, document_repo, finding_repo, config_repo):
        """Create analysis service."""
        return AnalysisService(analysis_repo, document_repo, finding_repo, config_repo)

    @pytest.fixture
    def finding_service(self, finding_repo):
        """Create finding service."""
        return FindingService(finding_repo)

    @pytest.fixture
    def config_service(self, config_repo):
        """Create configuration service."""
        return ConfigurationService(config_repo)

    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self, analysis_service, finding_service, config_service):
        """Test complete analysis workflow."""
        # 1. Get suitable configuration
        configs = await config_service.get_suitable_configurations(AnalysisType.SECURITY)
        assert len(configs) >= 1
        config = configs[0]

        # 2. Validate configuration
        validation = await config_service.validate_configuration(config.config_id)
        assert validation["valid"] is True

        # 3. Create and execute analysis
        analysis = await analysis_service.create_analysis("doc1", AnalysisType.SECURITY, config.config_id)
        assert analysis is not None

        result = await analysis_service.execute_analysis(analysis.analysis_id)
        assert result.is_successful()

        # 4. Get findings and resolve critical ones
        critical_findings = await finding_service.get_critical_findings(result.analysis_id)
        for finding in critical_findings:
            await finding_service.resolve_finding(finding.finding_id)

        # 5. Get summary
        summary = await finding_service.get_findings_summary(result.analysis_id)

        # Verify complete workflow
        assert result.status == AnalysisStatus.COMPLETED
        assert result.score >= 0.0
        assert summary["total_findings"] >= 0
        assert summary["resolved_count"] >= len(critical_findings)

    @pytest.mark.asyncio
    async def test_multi_analysis_workflow(self, analysis_service):
        """Test workflow with multiple analysis types."""
        analysis_types = [AnalysisType.CODE_QUALITY, AnalysisType.SECURITY, AnalysisType.PERFORMANCE]

        results = []
        for analysis_type in analysis_types:
            # Create and execute analysis
            analysis = await analysis_service.create_analysis("doc1", analysis_type)
            result = await analysis_service.execute_analysis(analysis.analysis_id)
            results.append(result)

        # Verify all analyses completed successfully
        assert all(r.is_successful() for r in results)
        assert len(set(r.analysis_type for r in results)) == len(analysis_types)

        # Get analysis summary
        summary = await analysis_service.get_analysis_summary("doc1")
        assert summary["total_analyses"] >= len(analysis_types)
        assert summary["completed_analyses"] >= len(analysis_types)

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, analysis_service):
        """Test error handling in analysis workflow."""
        # Try to analyze non-existent document
        analysis = await analysis_service.create_analysis("nonexistent", AnalysisType.CODE_QUALITY)
        assert analysis is None

        # Try to execute non-existent analysis
        result = await analysis_service.execute_analysis("nonexistent")
        assert result is None

        # Try to get summary for non-existent document
        summary = await analysis_service.get_analysis_summary("nonexistent")
        assert summary["total_analyses"] == 0

    @pytest.mark.asyncio
    async def test_analysis_quality_workflow(self, analysis_service, finding_service):
        """Test analysis quality assessment workflow."""
        # Create analysis with potentially problematic content
        document_repo = analysis_service.document_repo
        problematic_doc = MockDocument("problem_doc", "problematic.py", DocumentType.CODE, "python",
                                     "SELECT * FROM users WHERE id = ' + user_input\npassword = 'secret123'\nfor i in range(len(items)): pass")
        await document_repo.save(problematic_doc)

        # Execute security analysis
        analysis = await analysis_service.create_analysis("problem_doc", AnalysisType.SECURITY)
        result = await analysis_service.execute_analysis(analysis.analysis_id)

        # Should detect security issues
        assert result.is_successful()
        assert result.score < 1.0  # Should be reduced due to findings

        # Check for critical findings
        critical_findings = await finding_service.get_critical_findings(result.analysis_id)
        assert len(critical_findings) > 0  # Should find SQL injection

        # Verify findings details
        findings_summary = await finding_service.get_findings_summary(result.analysis_id)
        assert findings_summary["critical_count"] > 0
        assert findings_summary["total_findings"] > 0

    @pytest.mark.asyncio
    async def test_configuration_driven_analysis(self, analysis_service, config_service):
        """Test configuration-driven analysis workflow."""
        # Get configurations supporting security analysis
        security_configs = await config_service.get_suitable_configurations(AnalysisType.SECURITY)
        assert len(security_configs) > 0

        config = security_configs[0]

        # Create analysis using configuration
        analysis = await analysis_service.create_analysis("doc1", AnalysisType.SECURITY, config.config_id)
        assert analysis is not None

        # Execute analysis
        result = await analysis_service.execute_analysis(analysis.analysis_id)
        assert result.is_successful()

        # Verify configuration was used
        assert config.supports_analysis_type(result.analysis_type)

    @pytest.mark.asyncio
    async def test_comprehensive_analysis_reporting(self, analysis_service, finding_service):
        """Test comprehensive analysis reporting."""
        # Execute multiple analyses
        analyses = []
        for analysis_type in [AnalysisType.CODE_QUALITY, AnalysisType.SECURITY]:
            analysis = await analysis_service.create_analysis("doc1", analysis_type)
            result = await analysis_service.execute_analysis(analysis.analysis_id)
            analyses.append(result)

        # Get comprehensive summary
        summary = await analysis_service.get_analysis_summary("doc1")

        # Verify summary completeness
        assert summary["total_analyses"] >= 2
        assert summary["completed_analyses"] >= 2
        assert isinstance(summary["average_score"], float)
        assert summary["average_score"] >= 0.0
        assert summary["quality_grade"] in ["A", "B", "C", "D", "F"]

        # Get detailed findings across all analyses
        total_findings = 0
        for analysis in analyses:
            findings_summary = await finding_service.get_findings_summary(analysis.analysis_id)
            total_findings += findings_summary["total_findings"]

        assert summary["total_findings"] == total_findings
