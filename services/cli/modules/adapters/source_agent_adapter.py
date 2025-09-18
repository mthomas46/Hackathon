"""
Source Agent Service Adapter

Comprehensive adapter for the Source Agent service providing unified CLI interface
for document fetching, normalization, code analysis, and source management features.
"""

from typing import List, Tuple, Any, Dict
import time
from .base_service_adapter import BaseServiceAdapter, ServiceInfo, ServiceStatus, CommandResult


class SourceAgentAdapter(BaseServiceAdapter):
    """
    Unified adapter for Source Agent Service
    
    Provides standardized access to:
    - Document fetching and processing
    - Code repository analysis
    - Source normalization
    - Content indexing
    - File processing
    - Repository management
    """
    
    def get_service_info(self) -> ServiceInfo:
        """Get Source Agent Service information"""
        return ServiceInfo(
            name="source-agent",
            port=5000,
            version="1.0.0",
            status=ServiceStatus.HEALTHY,
            description="Document fetching, normalization, and code analysis service",
            features=[
                "Document Fetching",
                "Code Repository Analysis",
                "Source Normalization",
                "Content Indexing",
                "File Processing",
                "Repository Management",
                "Content Extraction",
                "Metadata Analysis"
            ],
            dependencies=["redis", "doc_store"],
            endpoints={
                "health": "/health",
                "fetch": "/fetch",
                "process": "/process",
                "analyze": "/analyze",
                "normalize": "/normalize",
                "index": "/index",
                "repositories": "/repositories",
                "files": "/files",
                "metadata": "/metadata"
            }
        )
    
    async def health_check(self) -> CommandResult:
        """Perform comprehensive health check"""
        try:
            start_time = time.time()
            
            # Test health endpoint
            health_url = f"{self.base_url}/health"
            health_response = await self.clients.get_json(health_url)
            
            execution_time = time.time() - start_time
            
            if health_response and health_response.get('status') == 'healthy':
                return CommandResult(
                    success=True,
                    data=health_response,
                    message="Source Agent is fully operational",
                    execution_time=execution_time
                )
            else:
                return CommandResult(
                    success=False,
                    error="Source Agent health check failed",
                    execution_time=execution_time
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Health check error: {str(e)}"
            )
    
    async def get_available_commands(self) -> List[Tuple[str, str, str]]:
        """Get available Source Agent commands"""
        return [
            ("fetch", "Fetch document from URL or repository", "fetch [url] [options]"),
            ("process", "Process uploaded file or content", "process [file_path] [type]"),
            ("analyze", "Analyze source code or document", "analyze [target] [analysis_type]"),
            ("normalize", "Normalize document format", "normalize [document_id] [format]"),
            ("index", "Index content for search", "index [content_id] [metadata]"),
            ("repositories", "List managed repositories", "repositories"),
            ("files", "List processed files", "files [filter]"),
            ("metadata", "Get document metadata", "metadata [document_id]"),
            ("status", "Get processing status", "status [job_id]"),
            ("health_detailed", "Get detailed health information", "health_detailed")
        ]
    
    async def execute_command(self, command: str, **kwargs) -> CommandResult:
        """Execute Source Agent commands"""
        try:
            start_time = time.time()
            
            if command == "fetch":
                return await self._fetch_document(kwargs)
            elif command == "process":
                return await self._process_content(kwargs)
            elif command == "analyze":
                return await self._analyze_source(kwargs)
            elif command == "normalize":
                return await self._normalize_document(kwargs)
            elif command == "index":
                return await self._index_content(kwargs)
            elif command == "repositories":
                return await self._get_repositories()
            elif command == "files":
                return await self._get_files(kwargs)
            elif command == "metadata":
                return await self._get_metadata(kwargs)
            elif command == "status":
                return await self._get_status(kwargs)
            elif command == "health_detailed":
                return await self.health_check()
            else:
                return CommandResult(
                    success=False,
                    error=f"Unknown command: {command}"
                )
                
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Command execution failed: {str(e)}"
            )
    
    # Private command implementations
    async def _fetch_document(self, params: Dict) -> CommandResult:
        """Fetch document from URL or repository"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/fetch"
            
            payload = {
                "url": params.get("url", "https://example.com/document.md"),
                "type": params.get("type", "markdown"),
                "options": params.get("options", {})
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Document fetched successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Document fetch failed: {str(e)}"
            )
    
    async def _process_content(self, params: Dict) -> CommandResult:
        """Process uploaded file or content"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/process"
            
            payload = {
                "content": params.get("content", "# Sample Document\nThis is a test document."),
                "type": params.get("type", "markdown"),
                "filename": params.get("filename", "document.md")
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Content processed successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Content processing failed: {str(e)}"
            )
    
    async def _analyze_source(self, params: Dict) -> CommandResult:
        """Analyze source code or document"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/analyze"
            
            payload = {
                "target": params.get("target", "sample_code.py"),
                "analysis_type": params.get("analysis_type", "structure"),
                "options": params.get("options", {})
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Source analysis completed",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Source analysis failed: {str(e)}"
            )
    
    async def _normalize_document(self, params: Dict) -> CommandResult:
        """Normalize document format"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/normalize"
            
            payload = {
                "document_id": params.get("document_id", "doc_123"),
                "target_format": params.get("format", "markdown"),
                "options": params.get("options", {})
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Document normalized successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Document normalization failed: {str(e)}"
            )
    
    async def _index_content(self, params: Dict) -> CommandResult:
        """Index content for search"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/index"
            
            payload = {
                "content_id": params.get("content_id", "content_123"),
                "metadata": params.get("metadata", {}),
                "tags": params.get("tags", [])
            }
            
            response = await self.clients.post_json(url, payload)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message="Content indexed successfully",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Content indexing failed: {str(e)}"
            )
    
    async def _get_repositories(self) -> CommandResult:
        """Get managed repositories"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/repositories"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            repo_count = len(response) if isinstance(response, list) else 0
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {repo_count} repositories",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get repositories: {str(e)}"
            )
    
    async def _get_files(self, params: Dict) -> CommandResult:
        """Get processed files"""
        try:
            start_time = time.time()
            url = f"{self.base_url}/files"
            
            # Add query parameters if provided
            query_params = {}
            if params.get("filter"):
                query_params["filter"] = params["filter"]
            if params.get("limit"):
                query_params["limit"] = params["limit"]
            
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            file_count = len(response) if isinstance(response, list) else 0
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved {file_count} files",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get files: {str(e)}"
            )
    
    async def _get_metadata(self, params: Dict) -> CommandResult:
        """Get document metadata"""
        try:
            start_time = time.time()
            document_id = params.get("document_id", "doc_123")
            url = f"{self.base_url}/metadata/{document_id}"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved metadata for document {document_id}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get metadata: {str(e)}"
            )
    
    async def _get_status(self, params: Dict) -> CommandResult:
        """Get processing status"""
        try:
            start_time = time.time()
            job_id = params.get("job_id", "job_123")
            url = f"{self.base_url}/status/{job_id}"
            response = await self.clients.get_json(url)
            execution_time = time.time() - start_time
            
            return CommandResult(
                success=True,
                data=response,
                message=f"Retrieved status for job {job_id}",
                execution_time=execution_time
            )
        except Exception as e:
            return CommandResult(
                success=False,
                error=f"Failed to get status: {str(e)}"
            )
