"""Build Cache Optimizer - Docker layer caching and build optimization.

Optimizes Docker builds by intelligently managing layer caching, dependency ordering,
and multi-stage build strategies for faster rebuilds and smaller images.
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DockerLayer:
    """Represents a Docker image layer."""

    instruction: str
    content_hash: str
    size_estimate: int = 0
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class CacheOptimization:
    """Optimization suggestion for Docker build caching."""

    type: str  # "layer_order", "multi_stage", "dependency_separation", etc.
    description: str
    dockerfile_changes: List[str]
    estimated_savings: str
    priority: int  # 1-10, higher is more important


class BuildCacheOptimizer:
    """Optimizes Docker builds for better caching and faster rebuilds."""

    def __init__(self, service_path: str = None):
        self.service_path = Path(service_path) if service_path else Path.cwd()
        self.dockerfile_path = self._find_dockerfile()
        self.optimizations: List[CacheOptimization] = []

    def _find_dockerfile(self) -> Optional[Path]:
        """Find the Dockerfile in the service directory."""
        for name in ["Dockerfile", "dockerfile", "Dockerfile.dev", "Dockerfile.prod"]:
            path = self.service_path / name
            if path.exists():
                return path
        return None

    def analyze_build_cache(self) -> Dict[str, Any]:
        """Analyze the current Dockerfile for cache optimization opportunities."""
        if not self.dockerfile_path:
            return {"error": "No Dockerfile found"}

        try:
            with open(self.dockerfile_path, "r") as f:
                content = f.read()

            lines = content.split("\n")
            layers = self._parse_dockerfile_layers(lines)
            optimizations = self._analyze_layer_ordering(layers)

            # Additional analyses
            multi_stage_opportunities = self._analyze_multi_stage_opportunities(layers)
            optimizations.extend(multi_stage_opportunities)

            dependency_opportunities = self._analyze_dependency_separation(layers)
            optimizations.extend(dependency_opportunities)

            context_opportunities = self._analyze_build_context(layers)
            optimizations.extend(context_opportunities)

            self.optimizations = sorted(optimizations, key=lambda x: x.priority, reverse=True)

            return {
                "dockerfile_path": str(self.dockerfile_path),
                "layers_analyzed": len(layers),
                "optimizations_found": len(self.optimizations),
                "optimizations": [
                    {
                        "type": opt.type,
                        "description": opt.description,
                        "estimated_savings": opt.estimated_savings,
                        "priority": opt.priority,
                    }
                    for opt in self.optimizations[:10]  # Top 10 optimizations
                ],
                "cache_efficiency_score": self._calculate_cache_efficiency_score(layers),
            }

        except Exception as e:
            logger.error(f"Error analyzing build cache: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

    def _parse_dockerfile_layers(self, lines: List[str]) -> List[DockerLayer]:
        """Parse Dockerfile into layers for analysis."""
        layers = []
        current_layer_content = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check if this starts a new layer
            if any(
                line.upper().startswith(cmd)
                for cmd in [
                    "FROM",
                    "RUN",
                    "COPY",
                    "ADD",
                    "WORKDIR",
                    "ENV",
                    "ARG",
                    "EXPOSE",
                    "VOLUME",
                    "USER",
                    "CMD",
                    "ENTRYPOINT",
                ]
            ):
                # Save previous layer if it exists
                if current_layer_content:
                    layer = self._create_layer_from_content(current_layer_content)
                    if layer:
                        layers.append(layer)

                current_layer_content = [line]
            else:
                # Continue current layer
                current_layer_content.append(line)

        # Don't forget the last layer
        if current_layer_content:
            layer = self._create_layer_from_content(current_layer_content)
            if layer:
                layers.append(layer)

        return layers

    def _create_layer_from_content(self, content: List[str]) -> Optional[DockerLayer]:
        """Create a DockerLayer from raw content."""
        if not content:
            return None

        instruction = content[0].upper()
        full_content = "\n".join(content)

        # Calculate content hash for cache invalidation analysis
        content_hash = hashlib.sha256(full_content.encode()).hexdigest()[:16]

        # Estimate layer size based on instruction type
        size_estimate = self._estimate_layer_size(instruction, content)

        # Analyze dependencies
        dependencies = self._analyze_layer_dependencies(instruction, content)

        return DockerLayer(
            instruction=instruction, content_hash=content_hash, size_estimate=size_estimate, dependencies=dependencies
        )

    def _estimate_layer_size(self, instruction: str, content: List[str]) -> int:
        """Estimate the size impact of a layer."""
        if instruction == "COPY" or instruction == "ADD":
            # Estimate based on file paths mentioned
            total_size = 0
            for line in content:
                parts = line.split()
                if len(parts) >= 3:
                    # COPY source dest or ADD source dest
                    source = parts[1]
                    if source.startswith("./") or "/" in source or "*" in source:
                        # Try to calculate actual size if file exists
                        try:
                            source_path = self.service_path / source.lstrip("./")
                            if source_path.exists():
                                if source_path.is_file():
                                    total_size += source_path.stat().st_size
                                elif source_path.is_dir():
                                    total_size += sum(f.stat().st_size for f in source_path.rglob("*") if f.is_file())
                        except (OSError, ValueError):
                            # Fallback: estimate based on common file types
                            if any(ext in source for ext in [".py", ".js", ".ts", ".java"]):
                                total_size += 100 * 1024  # 100KB per source file
                            elif any(ext in source for ext in ["requirements.txt", "package.json"]):
                                total_size += 10 * 1024  # 10KB for dep files
                            else:
                                total_size += 50 * 1024  # 50KB default
            return total_size

        elif instruction == "RUN":
            # RUN commands typically add packages/binaries
            run_content = " ".join(content).lower()
            if "pip install" in run_content or "npm install" in run_content:
                return 50 * 1024 * 1024  # 50MB for dependencies
            elif "apt-get" in run_content or "yum" in run_content:
                return 100 * 1024 * 1024  # 100MB for system packages
            else:
                return 10 * 1024 * 1024  # 10MB for other RUN commands

        return 0  # Other instructions typically don't add size

    def _analyze_layer_dependencies(self, instruction: str, content: List[str]) -> List[str]:
        """Analyze what this layer depends on."""
        dependencies = []

        if instruction in ["COPY", "ADD"]:
            # Depends on source files
            for line in content:
                parts = line.split()
                if len(parts) >= 2:
                    source = parts[1]
                    dependencies.append(f"file:{source}")

        elif instruction == "RUN":
            run_content = " ".join(content).lower()
            if "pip install" in run_content:
                dependencies.append("lang:python")
            if "npm install" in run_content or "yarn" in run_content:
                dependencies.append("lang:javascript")
            if "go build" in run_content or "go mod" in run_content:
                dependencies.append("lang:go")

        elif instruction == "FROM":
            # Depends on base image
            for line in content:
                if line.upper().startswith("FROM"):
                    parts = line.split()
                    if len(parts) >= 2:
                        dependencies.append(f"image:{parts[1]}")

        return dependencies

    def _analyze_layer_ordering(self, layers: List[DockerLayer]) -> List[CacheOptimization]:
        """Analyze layer ordering for optimal caching."""
        optimizations = []

        # Find COPY/ADD instructions that could be reordered
        copy_layers = []
        run_layers = []

        for i, layer in enumerate(layers):
            if layer.instruction in ["COPY", "ADD"]:
                copy_layers.append((i, layer))
            elif layer.instruction == "RUN":
                run_layers.append((i, layer))

        # Check if large COPY layers come before RUN layers that don't depend on them
        for copy_idx, copy_layer in copy_layers:
            copy_deps = set(copy_layer.dependencies)

            # Look for RUN layers that come before this COPY but don't depend on its files
            for run_idx, run_layer in run_layers:
                if run_idx < copy_idx:
                    set(run_layer.dependencies)

                    # If RUN doesn't depend on files that COPY provides, suggest reordering
                    file_deps = {dep for dep in copy_deps if dep.startswith("file:")}
                    if file_deps and not any(dep in file_deps for dep in run_layer.dependencies):
                        optimizations.append(
                            CacheOptimization(
                                type="layer_order",
                                description=f"Consider moving COPY layer (files: {list(file_deps)[:3]}) before unrelated RUN layers",
                                dockerfile_changes=[
                                    f"Move COPY instruction at line ~{copy_idx * 3} to earlier in Dockerfile",
                                    f"Ensure RUN layers that don't depend on copied files come after COPY layers they don't need",
                                ],
                                estimated_savings="15-30% faster rebuilds when source files change",
                                priority=8,
                            )
                        )
                        break

        # Check for multiple RUN apt-get/pip install that could be combined
        install_runs = []
        for idx, layer in enumerate(layers):
            if layer.instruction == "RUN":
                run_content = " ".join(
                    layer.instruction + " " + "\n".join([layer.instruction] if hasattr(layer, "content") else [])
                ).lower()
                if "apt-get install" in run_content or "pip install" in run_content:
                    install_runs.append(idx)

        if len(install_runs) > 1:
            optimizations.append(
                CacheOptimization(
                    type="combine_installs",
                    description=f"Found {len(install_runs)} separate package installations that could be combined",
                    dockerfile_changes=[
                        f"Combine {len(install_runs)} RUN apt-get/pip install commands into fewer layers",
                        "Use && to chain installation commands in single RUN instruction",
                    ],
                    estimated_savings="20-40% reduction in image layers and potential rebuild time",
                    priority=7,
                )
            )

        return optimizations

    def _analyze_multi_stage_opportunities(self, layers: List[DockerLayer]) -> List[CacheOptimization]:
        """Analyze opportunities for multi-stage builds."""
        optimizations = []

        # Check if there are development dependencies that could be separated
        has_dev_deps = False
        has_build_tools = False

        for layer in layers:
            if layer.instruction == "RUN":
                run_content = " ".join([layer.instruction]).lower()
                if "pip install" in run_content and ("dev" in run_content or "test" in run_content):
                    has_dev_deps = True
                if any(tool in run_content for tool in ["gcc", "build-essential", "git", "curl"]):
                    has_build_tools = True

        if has_dev_deps or has_build_tools:
            optimizations.append(
                CacheOptimization(
                    type="multi_stage",
                    description="Consider multi-stage build to separate build dependencies from runtime image",
                    dockerfile_changes=[
                        "Create separate build stage with development dependencies and build tools",
                        "Copy only runtime artifacts to final stage",
                        "Use 'AS build' and 'FROM build' pattern",
                    ],
                    estimated_savings="30-60% reduction in final image size and attack surface",
                    priority=9,
                )
            )

        # Check for large intermediate files that could be cleaned up
        total_size = sum(layer.size_estimate for layer in layers)
        if total_size > 500 * 1024 * 1024:  # 500MB
            optimizations.append(
                CacheOptimization(
                    type="artifact_cleanup",
                    description="Large build artifacts detected - consider cleanup in multi-stage builds",
                    dockerfile_changes=[
                        "Add cleanup commands (rm, apt-get clean, pip cache purge) before final stage",
                        "Use .dockerignore to exclude build artifacts from context",
                    ],
                    estimated_savings="40-70% reduction in final image size",
                    priority=8,
                )
            )

        return optimizations

    def _analyze_dependency_separation(self, layers: List[DockerLayer]) -> List[CacheOptimization]:
        """Analyze opportunities to separate frequently changing dependencies."""
        optimizations = []

        # Find COPY of dependency files
        dep_file_layers = []
        for idx, layer in enumerate(layers):
            if layer.instruction in ["COPY", "ADD"]:
                deps = [dep for dep in layer.dependencies if dep.startswith("file:")]
                for dep in deps:
                    if any(
                        dep_file in dep for dep_file in ["requirements.txt", "package.json", "go.mod", "Cargo.toml"]
                    ):
                        dep_file_layers.append((idx, layer, dep))

        # Check if dependency files are copied with application code
        for dep_idx, dep_layer, dep_file in dep_file_layers:
            # Look for subsequent COPY layers that might copy application code
            app_code_found = False
            for check_idx in range(dep_idx + 1, len(layers)):
                check_layer = layers[check_idx]
                if check_layer.instruction in ["COPY", "ADD"]:
                    check_deps = [dep for dep in check_layer.dependencies if dep.startswith("file:")]
                    # Check if it copies source code files
                    if any(".py" in dep or ".js" in dep or ".java" in dep for dep in check_deps):
                        app_code_found = True
                        break

            if app_code_found:
                optimizations.append(
                    CacheOptimization(
                        type="dependency_separation",
                        description="Dependency files copied together with application code - separate for better caching",
                        dockerfile_changes=[
                            f"Copy {dep_file} separately before copying application source code",
                            "Install dependencies in separate layer before copying source files",
                            "This prevents dependency reinstallation when only source code changes",
                        ],
                        estimated_savings="50-80% faster rebuilds when only source code changes",
                        priority=10,  # Highest priority - this is usually the biggest win
                    )
                )
                break

        return optimizations

    def _analyze_build_context(self, layers: List[DockerLayer]) -> List[CacheOptimization]:
        """Analyze build context optimization opportunities."""
        optimizations = []

        # Check for .dockerignore file
        dockerignore_path = self.service_path / ".dockerignore"
        if not dockerignore_path.exists():
            optimizations.append(
                CacheOptimization(
                    type="dockerignore",
                    description="No .dockerignore file found - build context may include unnecessary files",
                    dockerfile_changes=[
                        "Create .dockerignore file in service directory",
                        "Exclude common unnecessary files: __pycache__/, *.pyc, .git/, node_modules/, *.log",
                    ],
                    estimated_savings="20-50% reduction in build context size and transfer time",
                    priority=6,
                )
            )

        # Check for large files in potential build context
        large_files = []
        try:
            for root, dirs, files in os.walk(self.service_path):
                for file in files:
                    file_path = Path(root) / file
                    try:
                        size = file_path.stat().st_size
                        if size > 50 * 1024 * 1024:  # 50MB
                            rel_path = file_path.relative_to(self.service_path)
                            large_files.append((str(rel_path), size / (1024 * 1024)))
                    except OSError:
                        pass
        except Exception:
            pass

        if large_files:
            optimizations.append(
                CacheOptimization(
                    type="large_files",
                    description=f"Found {len(large_files)} large files that may slow down builds",
                    dockerfile_changes=[
                        "Add large files to .dockerignore if not needed in build",
                        f"Consider excluding files: {', '.join([f'{name} ({size:.1f}MB)' for name, size in large_files[:3]])}",
                    ],
                    estimated_savings="Significant reduction in build time and context transfer",
                    priority=7,
                )
            )

        return optimizations

    def _calculate_cache_efficiency_score(self, layers: List[DockerLayer]) -> float:
        """Calculate a cache efficiency score from 0-100."""
        if not layers:
            return 0.0

        score = 100.0

        # Penalize for each layer that could invalidate frequently changing content
        copy_count = sum(1 for layer in layers if layer.instruction in ["COPY", "ADD"])
        run_count = sum(1 for layer in layers if layer.instruction == "RUN")

        # Prefer COPY layers early, RUN layers that install deps before source code
        # This is a simplified scoring - in practice this would be more sophisticated
        if copy_count > run_count * 2:
            score -= 20  # Too many COPY layers might indicate poor ordering

        # Check if there are dependency files mixed with source code
        has_dep_separation_penalty = False
        for i, layer in enumerate(layers):
            if layer.instruction in ["COPY", "ADD"]:
                deps = [dep for dep in layer.dependencies if dep.startswith("file:")]
                has_deps = any("requirements.txt" in dep or "package.json" in dep for dep in deps)
                has_source = any(".py" in dep or ".js" in dep for dep in deps)

                if has_deps and has_source and i < len(layers) - 1:
                    # Check if there are more COPY layers after this one
                    remaining_copy = any(l.instruction in ["COPY", "ADD"] for l in layers[i + 1 :])
                    if remaining_copy:
                        has_dep_separation_penalty = True
                        break

        if has_dep_separation_penalty:
            score -= 30

        return max(0.0, min(100.0, score))

    def generate_optimized_dockerfile(self) -> Optional[str]:
        """Generate an optimized version of the Dockerfile."""
        if not self.dockerfile_path or not self.optimizations:
            return None

        try:
            with open(self.dockerfile_path, "r") as f:
                original_content = f.read()

            # For now, just add comments with optimization suggestions
            # A full implementation would rewrite the Dockerfile
            lines = original_content.split("\n")
            optimized_lines = []

            # Add header with optimization suggestions
            optimized_lines.append("# =========================================================================")
            optimized_lines.append("# OPTIMIZED DOCKERFILE - Generated by Build Cache Optimizer")
            optimized_lines.append("# =========================================================================")
            optimized_lines.append(
                f"# Cache Efficiency Score: {self._calculate_cache_efficiency_score(self._parse_dockerfile_layers(lines)):.1f}/100"
            )
            optimized_lines.append("#")
            optimized_lines.append("# Top Optimization Opportunities:")
            for i, opt in enumerate(self.optimizations[:5], 1):
                optimized_lines.append(f"# {i}. {opt.description}")
                optimized_lines.append(f"#    Estimated savings: {opt.estimated_savings}")
            optimized_lines.append("# =========================================================================")
            optimized_lines.append("")

            optimized_lines.extend(lines)

            return "\n".join(optimized_lines)

        except Exception as e:
            logger.error(f"Error generating optimized Dockerfile: {e}")
            return None

    def create_dockerignore_template(self) -> str:
        """Generate a .dockerignore template for the service."""
        template = """# Docker Build Context Exclusions
# This file helps reduce build context size and improve build performance

# Version Control
.git
.gitignore
.github

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/
.venv
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.npm
.eslintcache

# IDE and Editor files
.vscode/
.idea/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Documentation and misc
*.md
docs/
README*
CHANGELOG*

# Test files and directories
tests/
test_*.py
*_test.py
conftest.py

# Development configuration
.env
.env.local
.env.development
.env.test
config.local.*
*.local

# Build artifacts
dist/
build/
*.egg-info/
.installed.cfg
*.egg

# Logs
logs/
*.log

# Temporary files
tmp/
temp/
.tmp/

# Database files
*.db
*.sqlite
*.sqlite3

# Large data files (uncomment and modify as needed)
# *.csv
# *.json
# data/
# models/
# *.pkl
# *.h5
"""

        return template


# Convenience functions
def analyze_dockerfile_cache(service_path: str = None) -> Dict[str, Any]:
    """Analyze Dockerfile for cache optimization opportunities."""
    optimizer = BuildCacheOptimizer(service_path)
    return optimizer.analyze_build_cache()


def generate_optimized_dockerfile(service_path: str = None) -> Optional[str]:
    """Generate an optimized version of the Dockerfile."""
    optimizer = BuildCacheOptimizer(service_path)
    optimizer.analyze_build_cache()  # Analyze first to populate optimizations
    return optimizer.generate_optimized_dockerfile()


def create_dockerignore_template() -> str:
    """Generate a .dockerignore template."""
    optimizer = BuildCacheOptimizer()
    return optimizer.create_dockerignore_template()


# CLI integration
def main():
    """CLI interface for build cache optimization."""
    import argparse

    parser = argparse.ArgumentParser(description="Docker Build Cache Optimizer")
    parser.add_argument("--analyze", action="store_true", help="Analyze current Dockerfile for optimizations")
    parser.add_argument("--optimize", action="store_true", help="Generate optimized Dockerfile")
    parser.add_argument("--dockerignore", action="store_true", help="Generate .dockerignore template")
    parser.add_argument("--path", help="Path to service directory (default: current directory)")

    args = parser.parse_args()

    service_path = args.path or os.getcwd()
    optimizer = BuildCacheOptimizer(service_path)

    if args.analyze:
        result = optimizer.analyze_build_cache()
        print(json.dumps(result, indent=2))

    elif args.optimize:
        optimizer.analyze_build_cache()
        optimized = optimizer.generate_optimized_dockerfile()
        if optimized:
            output_path = Path(service_path) / "Dockerfile.optimized"
            with open(output_path, "w") as f:
                f.write(optimized)
            print(f"Optimized Dockerfile written to: {output_path}")
        else:
            print("Failed to generate optimized Dockerfile")

    elif args.dockerignore:
        template = optimizer.create_dockerignore_template()
        output_path = Path(service_path) / ".dockerignore"
        if output_path.exists():
            print(f".dockerignore already exists at: {output_path}")
            response = input("Overwrite? (y/N): ")
            if response.lower() != "y":
                return

        with open(output_path, "w") as f:
            f.write(template)
        print(f".dockerignore template written to: {output_path}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
