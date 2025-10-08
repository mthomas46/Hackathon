# MCP Enhancement Implementation Guide

## 🔍 Root Cause Analysis

### Problem 1: Empty Evergreen Documentation
**Symptom**: Documents show synthetic/fallback content instead of real MCP-generated knowledge.

**Root Cause**: 
```
mcp-provisioner → Creates metadata → Saves to Redis ✅
                   ❌ MISSING: Deploy Docker container
                   ❌ MISSING: Start MCP instance
                   ❌ MISSING: Register with gateway

Result: Gateway has no running instances → Returns 503 → Falls back to synthetic content
```

**Evidence**:
```bash
$ docker ps | grep mcp_
# Only shows mcp-gateway, no actual MCP instances

$ curl localhost:8001/api/v1/gateway/route -d '{"mcp_id": "mcp_123"}'
# Returns: {"error_message": "No available instances for mcp_123", "status_code": 503}
```

---

## 📋 Implementation Checklist

### Phase 1: Fix MCP Deployment (CRITICAL)

#### 1.1 Add Docker SDK Dependency
```bash
cd services/mcp-provisioner
echo "docker==7.0.0" >> requirements.txt
docker-compose build mcp-provisioner
```

#### 1.2 Implement Container Deployment

**File**: `services/mcp-provisioner/application/use_cases/provision_mcp_use_case.py`

Add after line 8:
```python
import docker
from docker.errors import DockerException
```

Add new method before `_parse_resource_limits`:
```python
async def _deploy_docker_container(
    self,
    mcp_instance: MCPInstance
) -> Optional[str]:
    """
    Deploy MCP instance as Docker container.
    
    Returns:
        container_id if successful, None otherwise
    """
    try:
        client = docker.from_env()
        
        # Build container configuration
        container_config = {
            "image": mcp_instance.config.docker_image,
            "name": f"mcp-{mcp_instance.mcp_id}",
            "environment": mcp_instance.metadata.get("environment", {}),
            "mem_limit": f"{mcp_instance.resource_limits.memory_limit_mb}m",
            "cpu_shares": int(mcp_instance.resource_limits.cpu_limit * 1024),
            "ports": {f'{mcp_instance.config.port}/tcp': None},  # Auto-assign external port
            "network": "ams",  # Same network as other services
            "detach": True,
            "labels": {
                "mcp.id": mcp_instance.mcp_id,
                "mcp.tier": str(mcp_instance.config.tier),
                "mcp.client_id": mcp_instance.metadata.get("client_id", "unknown")
            },
            "healthcheck": {
                "test": ["CMD", "curl", "-f", f"http://localhost:{mcp_instance.config.port}/health"],
                "interval": 10_000_000_000,  # 10s
                "timeout": 5_000_000_000,    # 5s
                "retries": 3,
                "start_period": 30_000_000_000  # 30s
            }
        }
        
        logger.info(f"Deploying container for MCP {mcp_instance.mcp_id}")
        container = client.containers.run(**container_config)
        
        # Wait for container to be healthy
        max_wait = 60  # seconds
        for i in range(max_wait):
            container.reload()
            if container.status == "running":
                # Check health
                health = container.attrs.get("State", {}).get("Health", {})
                if health.get("Status") == "healthy":
                    logger.info(f"Container {container.id[:12]} is healthy")
                    return container.id
            
            await asyncio.sleep(1)
        
        logger.warning(f"Container {container.id[:12]} did not become healthy within {max_wait}s")
        return container.id  # Return anyway, let gateway handle unhealthy instances
        
    except DockerException as e:
        logger.error(f"Docker error deploying MCP {mcp_instance.mcp_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error deploying MCP {mcp_instance.mcp_id}: {e}", exc_info=True)
        return None
```

Update the `execute` method after Step 4 (before persist):
```python
# Step 4.5: Deploy Docker container
container_id = await self._deploy_docker_container(mcp_instance)
if container_id:
    logger.info(f"Successfully deployed container {container_id[:12]} for MCP {mcp_id}")
    # Update metadata with container info
    mcp_instance.metadata["container_id"] = container_id
    mcp_instance.metadata["status"] = "deployed"
    # Transition to HOT state since container is running
    from services.mcp_provisioner.domain.value_objects.mcp_state import hot_state
    object.__setattr__(mcp_instance, 'state', hot_state())
else:
    logger.warning(f"Failed to deploy container for MCP {mcp_id}, keeping in COLD state")
    mcp_instance.metadata["status"] = "deployment_failed"

# Step 5: Persist the instance
```

#### 1.3 Test Deployment
```bash
# Rebuild and restart provisioner
docker-compose build mcp-provisioner
docker-compose up -d mcp-provisioner

# Run demo
python3 demo_mcp_lifecycle.py

# Verify MCP container is running
docker ps | grep "mcp-mcp_"
# Should see: mcp-mcp_<id>  hackathon-mcp:latest  ...  Up X seconds (healthy)

# Test query
curl -X POST localhost:8001/api/v1/gateway/route \
  -H "Content-Type: application/json" \
  -d '{
    "mcp_id": "mcp_<id_from_demo>",
    "method": "POST",
    "path": "/api/query",
    "body": {"query": "What is the MCP ecosystem?"}
  }'
# Should return real response, not 503
```

---

### Phase 2: Add Timestamp Tracking

#### 2.1 Enhance Document Collection

**File**: `demo_mcp_lifecycle.py`

Update `collect_documents` method (around line 180):
```python
async def collect_documents(self):
    """Collect 50 documents with timestamp metadata."""
    self.print_header("PHASE 3: DOCUMENT COLLECTION")
    
    # ... existing code ...
    
    for idx, doc_file in enumerate(sample_docs, 1):
        try:
            # Get file timestamps
            stat = doc_file.stat()
            created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
            updated_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            # Try to extract Git commit date if in a Git repo
            git_date = await self._get_git_commit_date(doc_file)
            if git_date:
                updated_at = git_date  # Prefer Git date over filesystem
            
            event = {
                "event_type": "document.created",
                "timestamp": datetime.now().isoformat(),
                "correlation_id": self.correlation_id,
                "payload": {
                    "document_id": f"doc_{doc_file.stem}_{idx:03d}",
                    "title": doc_file.stem.replace('_', ' ').title(),
                    "source": "confluence",
                    "path": str(doc_file),
                    "file_size": stat.st_size,
                    "created_at": created_at,    # NEW
                    "updated_at": updated_at,    # NEW
                    "format": doc_file.suffix
                }
            }
            self.documents.append(event)
```

Add helper method:
```python
async def _get_git_commit_date(self, file_path: Path) -> Optional[str]:
    """Get last commit date for a file from Git."""
    try:
        result = await asyncio.create_subprocess_exec(
            'git', 'log', '-1', '--format=%aI', str(file_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=file_path.parent
        )
        stdout, _ = await result.communicate()
        if result.returncode == 0 and stdout:
            return stdout.decode().strip()
    except:
        pass
    return None
```

#### 2.2 Update Ingestion Payload

Update `ingest_documents` method (around line 270):
```python
ingest_payload = {
    "document_id": event['payload']['document_id'],
    "title": event['payload']['title'],
    "content": content[:1000],
    "source": "confluence",
    "metadata": {
        **event['payload'],  # Include all payload fields
        "created_at": event['payload'].get('created_at'),  # NEW
        "updated_at": event['payload'].get('updated_at'),  # NEW
        "ingested_at": datetime.now().isoformat()
    }
}
```

---

### Phase 3: GitHub Integration

#### 3.1 Create GitHub Collector

**New File**: `services/mock-data-generator/github_collector.py`

```python
"""GitHub document collector for commits, docs, and code files."""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import httpx

class GitHubDocumentCollector:
    def __init__(self, github_token: Optional[str] = None):
        self.token = github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"
    
    async def collect_commits(
        self,
        repo: str,  # e.g., "owner/repo"
        branch: str = "main",
        limit: int = 100
    ) -> List[Dict]:
        """Collect and normalize commit history."""
        documents = []
        
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/repos/{repo}/commits"
            params = {"sha": branch, "per_page": min(limit, 100)}
            
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            commits = response.json()
            
            for commit in commits[:limit]:
                # Normalize commit into document
                doc = {
                    "document_id": f"commit-{commit['sha'][:8]}",
                    "title": f"Commit: {commit['commit']['message'].split(chr(10))[0][:100]}",
                    "content": self._format_commit_document(commit),
                    "source": "github",
                    "metadata": {
                        "type": "git_commit",
                        "repo": repo,
                        "branch": branch,
                        "sha": commit['sha'],
                        "author": commit['commit']['author']['name'],
                        "author_email": commit['commit']['author']['email'],
                        "created_at": commit['commit']['author']['date'],
                        "updated_at": commit['commit']['author']['date'],
                        "url": commit['html_url']
                    }
                }
                documents.append(doc)
        
        return documents
    
    def _format_commit_document(self, commit: Dict) -> str:
        """Format commit into markdown document."""
        return f"""# Commit: {commit['sha'][:8]}

**Author**: {commit['commit']['author']['name']} <{commit['commit']['author']['email']}>  
**Date**: {commit['commit']['author']['date']}  
**URL**: {commit['html_url']}

## Commit Message

{commit['commit']['message']}

## Changes

Files changed: {len(commit.get('files', []))}

---

*This document was automatically generated from Git commit history.*
"""
    
    async def collect_documentation_files(
        self,
        repo: str,
        branch: str = "main",
        paths: List[str] = ["docs/", "README.md", "*.md"]
    ) -> List[Dict]:
        """Collect documentation files from repository."""
        documents = []
        
        async with httpx.AsyncClient() as client:
            # Get repository tree
            url = f"{self.base_url}/repos/{repo}/git/trees/{branch}?recursive=1"
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            
            tree = response.json()
            
            # Filter for documentation files
            doc_files = [
                item for item in tree['tree']
                if item['type'] == 'blob' and self._is_doc_file(item['path'])
            ]
            
            # Fetch content for each file
            for file_item in doc_files:
                try:
                    content = await self._fetch_file_content(client, repo, file_item['path'], branch)
                    
                    # Get commit info for this file
                    commit_info = await self._get_last_commit(client, repo, file_item['path'], branch)
                    
                    doc = {
                        "document_id": f"github-{repo.replace('/', '-')}-{Path(file_item['path']).stem}",
                        "title": f"{repo}: {file_item['path']}",
                        "content": content,
                        "source": "github",
                        "metadata": {
                            "type": "documentation_file",
                            "repo": repo,
                            "branch": branch,
                            "path": file_item['path'],
                            "created_at": commit_info.get('created_at'),
                            "updated_at": commit_info.get('updated_at'),
                            "last_commit": commit_info.get('sha'),
                            "author": commit_info.get('author')
                        }
                    }
                    documents.append(doc)
                except Exception as e:
                    print(f"Error fetching {file_item['path']}: {e}")
        
        return documents
    
    def _is_doc_file(self, path: str) -> bool:
        """Check if file is a documentation file."""
        doc_extensions = ['.md', '.rst', '.txt']
        doc_dirs = ['docs/', 'documentation/', 'wiki/']
        doc_files = ['README', 'CHANGELOG', 'CONTRIBUTING', 'LICENSE']
        
        path_lower = path.lower()
        
        # Check extension
        if any(path_lower.endswith(ext) for ext in doc_extensions):
            return True
        
        # Check if in docs directory
        if any(path_lower.startswith(dir) for dir in doc_dirs):
            return True
        
        # Check common doc filenames
        if any(name.lower() in path_lower for name in doc_files):
            return True
        
        return False
    
    async def _fetch_file_content(
        self,
        client: httpx.AsyncClient,
        repo: str,
        path: str,
        branch: str
    ) -> str:
        """Fetch file content from GitHub."""
        url = f"{self.base_url}/repos/{repo}/contents/{path}"
        params = {"ref": branch}
        
        response = await client.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        
        import base64
        content_b64 = response.json()['content']
        return base64.b64decode(content_b64).decode('utf-8', errors='ignore')
    
    async def _get_last_commit(
        self,
        client: httpx.AsyncClient,
        repo: str,
        path: str,
        branch: str
    ) -> Dict:
        """Get last commit info for a file."""
        url = f"{self.base_url}/repos/{repo}/commits"
        params = {"path": path, "sha": branch, "per_page": 1}
        
        try:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            commits = response.json()
            if commits:
                commit = commits[0]
                return {
                    "sha": commit['sha'],
                    "author": commit['commit']['author']['name'],
                    "created_at": commit['commit']['author']['date'],
                    "updated_at": commit['commit']['author']['date']
                }
        except:
            pass
        
        return {}
```

#### 3.2 Integrate with Demo

**File**: `demo_mcp_lifecycle.py`

Add new method:
```python
async def collect_github_documents(self, repo: str, branch: str = "main"):
    """Collect documents from GitHub repository."""
    self.print_header(f"GITHUB INGESTION: {repo}")
    
    from services.mock_data_generator.github_collector import GitHubDocumentCollector
    
    collector = GitHubDocumentCollector()
    
    # Collect commits
    self.print_info("Collecting commit history...")
    commits = await collector.collect_commits(repo, branch, limit=50)
    self.print_success(f"Collected {len(commits)} commits")
    
    # Collect documentation files
    self.print_info("Collecting documentation files...")
    doc_files = await collector.collect_documentation_files(repo, branch)
    self.print_success(f"Collected {len(doc_files)} documentation files")
    
    # Add to documents list
    self.documents.extend([{"event_type": "document.created", "payload": doc} for doc in commits + doc_files])
    
    return len(commits) + len(doc_files)
```

Usage in `main`:
```python
# After normal document collection
await demo.collect_github_documents("yourusername/yourrepo", "main")
```

---

### Phase 4: Code Analysis Integration

#### 4.1 Create Code Document Generator

**New File**: `code_document_generator.py`

```python
"""Generate documentation from code analysis."""

from typing import Dict, List
from pathlib import Path
import httpx

class CodeDocumentGenerator:
    def __init__(self, code_analyzer_url: str = "http://localhost:8020"):
        self.code_analyzer_url = code_analyzer_url
    
    async def analyze_and_document_file(
        self,
        file_path: Path,
        content: str
    ) -> Dict:
        """Analyze code file and generate documentation."""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.code_analyzer_url}/api/v1/analysis/analyze",
                json={
                    "source_type": "local",
                    "title": file_path.name,
                    "content": content,
                    "repo": "local",
                    "path": str(file_path),
                    "include_endpoints": True,
                    "include_style_check": True
                }
            )
            
            if response.status_code != 200:
                return None
            
            analysis = response.json()
            
            # Generate documentation from analysis
            doc_content = self._generate_documentation(file_path, content, analysis)
            
            return {
                "document_id": f"code-{file_path.stem}",
                "title": f"Code Analysis: {file_path.name}",
                "content": doc_content,
                "source": "code_analysis",
                "metadata": {
                    "type": "code_analysis",
                    "file_path": str(file_path),
                    "language": self._detect_language(file_path),
                    "quality_score": analysis['result'].get('quality_score'),
                    "endpoints_found": analysis['result'].get('endpoints_found'),
                    "security_issues": analysis['result'].get('security_issues'),
                    "style_violations": analysis['result'].get('style_violations'),
                    "analysis_timestamp": analysis['result'].get('analysis_timestamp')
                }
            }
    
    def _generate_documentation(self, file_path: Path, content: str, analysis: Dict) -> str:
        """Generate comprehensive documentation from analysis results."""
        
        result = analysis.get('result', {})
        endpoints = analysis.get('endpoints_found', [])
        style_violations = analysis.get('style_violations', [])
        
        doc = f"""# File: {file_path}

**Language**: {self._detect_language(file_path)}  
**Lines of Code**: {len(content.splitlines())}  
**Quality Score**: {result.get('quality_score', 'N/A')}/100  
**Analysis Date**: {result.get('analysis_timestamp', 'N/A')}

---

## Overview

This file is part of the codebase and has been automatically analyzed for quality, security, and style compliance.

---

## API Endpoints

"""
        
        if endpoints:
            for endpoint in endpoints:
                doc += f"### {endpoint.get('method', 'UNKNOWN')} `{endpoint.get('path', 'N/A')}`\n\n"
                doc += f"- **Description**: {endpoint.get('description', 'No description')}\n"
                doc += f"- **Line**: {endpoint.get('line_number', 'N/A')}\n\n"
        else:
            doc += "*No API endpoints detected in this file.*\n\n"
        
        doc += "---\n\n## Code Quality\n\n"
        
        if style_violations:
            doc += f"**Style Violations**: {len(style_violations)} found\n\n"
            for violation in style_violations[:10]:  # Top 10
                doc += f"- **Line {violation.get('line', 'N/A')}**: {violation.get('message', 'N/A')}\n"
        else:
            doc += "*No style violations detected.*\n\n"
        
        doc += f"""
---

## Metadata

- **File Size**: {len(content)} bytes
- **Security Issues**: {result.get('security_issues', 0)}
- **Processing Time**: {result.get('processing_time_seconds', 'N/A')}s

---

*This documentation was automatically generated by code-analyzer service.*
"""
        
        return doc
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        ext_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.go': 'Go',
            '.rs': 'Rust',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.cs': 'C#',
            '.cpp': 'C++',
            '.c': 'C'
        }
        return ext_map.get(file_path.suffix.lower(), 'Unknown')
```

#### 4.2 Integrate with Demo

Add to `demo_mcp_lifecycle.py`:
```python
async def analyze_code_files(self, directory: Path):
    """Analyze code files and generate documentation."""
    self.print_header("CODE ANALYSIS & DOCUMENTATION")
    
    from code_document_generator import CodeDocumentGenerator
    
    generator = CodeDocumentGenerator(self.services['code-analyzer'])
    
    # Find code files
    code_extensions = ['.py', '.js', '.ts', '.java', '.go']
    code_files = []
    for ext in code_extensions:
        code_files.extend(directory.rglob(f"*{ext}"))
    
    self.print_info(f"Found {len(code_files)} code files")
    
    # Analyze in parallel (batches of 10)
    batch_size = 10
    for i in range(0, len(code_files), batch_size):
        batch = code_files[i:i+batch_size]
        tasks = []
        
        for file_path in batch:
            try:
                with open(file_path) as f:
                    content = f.read()
                tasks.append(generator.analyze_and_document_file(file_path, content))
            except:
                pass
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict):
                self.documents.append({"event_type": "document.created", "payload": result})
        
        print(f"  Analyzed {min(i+batch_size, len(code_files))}/{len(code_files)} files...")
    
    self.print_success(f"Generated documentation for {len(code_files)} code files")
```

---

## 🧪 Testing

### Full Integration Test

```bash
# 1. Rebuild services with Docker support
docker-compose build mcp-provisioner
docker-compose up -d

# 2. Run enhanced demo
python3 demo_mcp_lifecycle.py

# 3. Verify MCP containers are running
docker ps | grep "mcp-mcp_"

# 4. Check logs
docker logs mcp-mcp_<id>

# 5. Test real query
curl -X POST localhost:8001/api/v1/gateway/route \
  -H "Content-Type: application/json" \
  -d '{
    "mcp_id": "mcp_<id>",
    "method": "POST",
    "path": "/api/query",
    "body": {"query": "Explain the MCP provisioning workflow"}
  }'

# 6. Verify evergreen docs have real content
cat docs-evergreen/01_ECOSYSTEM_OVERVIEW.md
# Should contain detailed information, not generic fallback
```

---

## 📊 Expected Results

### Before
- ❌ No MCP containers running
- ❌ Gateway returns 503 errors
- ❌ Evergreen docs with synthetic content
- ❌ No timestamps on documents
- ❌ No GitHub/code integration

### After
- ✅ MCP containers deployed and healthy
- ✅ Gateway routes to running instances
- ✅ Evergreen docs with rich, accurate content
- ✅ All documents timestamped
- ✅ GitHub commits and docs ingested
- ✅ Code files analyzed and documented

---

**Implementation Status**: Ready for Phase 1 (Docker deployment) ✅
