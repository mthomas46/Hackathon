# MCP Training Pipeline - Detailed Design

## Overview

The MCP Training Pipeline is a distributed system that extracts knowledge from various ecosystem data sources, processes it through normalization and embedding stages, and loads it into MCP instances. The pipeline is designed for horizontal scalability, fault tolerance, and incremental training capabilities.

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                    Training Coordinator (Port 5700)                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Job Scheduler │ Worker Manager │ Progress Tracker │ Monitor  │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                              ↓ (Celery Tasks)
┌────────────────────────────────────────────────────────────────────┐
│                     Worker Pool (Distributed)                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │  Extraction     │→│  Normalization   │→│  Embedding &     │  │
│  │  Workers (10)   │  │  Workers (5)     │  │  Tagging (5)     │  │
│  │                 │  │                  │  │                  │  │
│  │ • GitHub        │  │ • Markdown       │  │ • Chunking       │  │
│  │ • Confluence    │  │   Normalizer     │  │ • Embeddings     │  │
│  │ • Jira          │  │ • Code Parser    │  │ • Auto-tagging   │  │
│  │ • FullStory     │  │ • Link Resolver  │  │ • Entity Extract │  │
│  │ • Logs          │  │ • Metadata       │  │ • Relationships  │  │
│  │ • Datastores    │  │ • Scope Class    │  │ • Validation     │  │
│  └─────────────────┘  └──────────────────┘  └──────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│                        Loading Stage                                │
│  ┌──────────────────┐              ┌──────────────────┐            │
│  │  ChromaDB Loader │              │  Neo4j Loader    │            │
│  │  (Vectors)       │              │  (Graph)         │            │
│  └──────────────────┘              └──────────────────┘            │
└────────────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────────────┐
│                       Target MCP Instance                           │
│  ChromaDB (embeddings) + Neo4j (relationships) + Config            │
└────────────────────────────────────────────────────────────────────┘
```

---

## Service: Training Coordinator

### Responsibilities

1. **Job Management:**
   - Receive training requests (via API or scheduled)
   - Create training job with unique ID
   - Break job into phases and tasks
   - Distribute tasks to worker pool via Celery
   - Track progress and status

2. **Resource Management:**
   - Monitor worker health and capacity
   - Auto-scale workers based on queue depth
   - Handle worker failures and retries

3. **Quality Assurance:**
   - Validate extracted data before normalization
   - Validate embeddings before loading
   - Collect quality metrics (coverage, accuracy)

4. **Metadata & Lineage:**
   - Track data sources for each training job
   - Record timestamps, versions, and configurations
   - Enable data lineage tracking

### API Endpoints

```python
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from enum import Enum

app = FastAPI(title="MCP Training Coordinator", version="1.0")

class DataSourceType(str, Enum):
    GITHUB = "github"
    CONFLUENCE = "confluence"
    JIRA = "jira"
    FULLSTORY = "fullstory"
    LOGS = "logs"
    DATASTORE = "datastore"

class DataSource(BaseModel):
    type: DataSourceType
    config: Dict  # Source-specific configuration
    filters: Optional[Dict] = None

class TrainingJobRequest(BaseModel):
    mcp_id: str
    tier: int  # 0=Client, 1=Project, 2=Team, 3=Company, 4=Ecosystem
    data_sources: List[DataSource]
    training_params: Dict
    incremental: bool = False
    priority: str = "normal"  # low, normal, high, critical

class TrainingJobStatus(str, Enum):
    QUEUED = "queued"
    EXTRACTING = "extracting"
    NORMALIZING = "normalizing"
    EMBEDDING = "embedding"
    LOADING = "loading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@app.post("/training/jobs", response_model=Dict)
async def create_training_job(
    request: TrainingJobRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new training job
    """
    # 1. Validate request
    if not validate_mcp_id(request.mcp_id):
        raise HTTPException(400, "Invalid MCP ID")
    
    # 2. Create job record
    job = create_job_record(request)
    
    # 3. Start async training pipeline
    background_tasks.add_task(execute_training_pipeline, job)
    
    return {
        "job_id": job.id,
        "status": "queued",
        "estimated_duration": estimate_duration(request),
        "message": "Training job queued successfully"
    }

@app.get("/training/jobs/{job_id}", response_model=Dict)
async def get_job_status(job_id: str):
    """
    Get status and progress of a training job
    """
    job = get_job_from_db(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    return {
        "job_id": job.id,
        "status": job.status,
        "progress": job.progress_percent,
        "phase": job.current_phase,
        "started_at": job.started_at,
        "estimated_completion": job.estimated_completion,
        "stats": {
            "documents_extracted": job.stats.documents_extracted,
            "documents_normalized": job.stats.documents_normalized,
            "embeddings_created": job.stats.embeddings_created,
            "relationships_created": job.stats.relationships_created
        },
        "errors": job.errors
    }

@app.delete("/training/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a running training job
    """
    job = get_job_from_db(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    
    if job.status in [TrainingJobStatus.COMPLETED, TrainingJobStatus.FAILED]:
        raise HTTPException(400, "Cannot cancel completed/failed job")
    
    cancel_celery_tasks(job)
    update_job_status(job_id, TrainingJobStatus.CANCELLED)
    
    return {"message": "Job cancelled successfully"}

@app.get("/training/jobs", response_model=List[Dict])
async def list_jobs(
    status: Optional[TrainingJobStatus] = None,
    mcp_id: Optional[str] = None,
    limit: int = 50
):
    """
    List training jobs with optional filters
    """
    jobs = query_jobs(status=status, mcp_id=mcp_id, limit=limit)
    return [job.to_dict() for job in jobs]
```

### Training Pipeline Execution

```python
from celery import chain, group
import asyncio

async def execute_training_pipeline(job: TrainingJob):
    """
    Execute the full training pipeline for a job
    """
    try:
        # Update status
        update_job_status(job.id, TrainingJobStatus.EXTRACTING)
        
        # Phase 1: Extraction (parallel per source)
        extraction_tasks = []
        for source in job.data_sources:
            if source.type == DataSourceType.GITHUB:
                task = extract_github.s(job.id, source.config)
            elif source.type == DataSourceType.CONFLUENCE:
                task = extract_confluence.s(job.id, source.config)
            elif source.type == DataSourceType.JIRA:
                task = extract_jira.s(job.id, source.config)
            # ... other sources
            extraction_tasks.append(task)
        
        extraction_result = group(extraction_tasks).apply_async()
        extraction_result.get()  # Wait for all to complete
        
        # Phase 2: Normalization (parallel per document)
        update_job_status(job.id, TrainingJobStatus.NORMALIZING)
        raw_docs = get_extracted_documents(job.id)
        
        normalization_tasks = [
            normalize_document.s(job.id, doc) for doc in raw_docs
        ]
        normalization_result = group(normalization_tasks).apply_async()
        normalization_result.get()
        
        # Phase 3: Embedding & Tagging (parallel per normalized doc)
        update_job_status(job.id, TrainingJobStatus.EMBEDDING)
        normalized_docs = get_normalized_documents(job.id)
        
        embedding_tasks = [
            create_embeddings.s(job.id, doc, job.training_params)
            for doc in normalized_docs
        ]
        embedding_result = group(embedding_tasks).apply_async()
        embedding_result.get()
        
        # Phase 4: Loading (sequential for data consistency)
        update_job_status(job.id, TrainingJobStatus.LOADING)
        processed_data = get_processed_data(job.id)
        
        # Load into ChromaDB
        await load_to_chromadb(job.mcp_id, processed_data.embeddings)
        
        # Load into Neo4j
        await load_to_neo4j(job.mcp_id, processed_data.relationships)
        
        # Update MCP config
        await update_mcp_config(job.mcp_id, processed_data.metadata)
        
        # Complete
        update_job_status(job.id, TrainingJobStatus.COMPLETED)
        cleanup_temp_data(job.id)
        
    except Exception as e:
        logger.error(f"Training job {job.id} failed: {e}")
        update_job_status(job.id, TrainingJobStatus.FAILED)
        record_error(job.id, str(e))
```

---

## Worker Type 1: Extraction Workers

### GitHub Extractor

```python
from celery import Task
from github import Github
import ast
import json

@celery_app.task(bind=True, name="extract_github")
def extract_github(self: Task, job_id: str, config: dict) -> dict:
    """
    Extract knowledge from GitHub repositories
    
    Extracts:
    - Code files (Python, JS, Java, etc.)
    - README files
    - Commit messages
    - Pull request descriptions and comments
    - Issues and discussions
    """
    try:
        gh = Github(config.get("token"))
        
        results = {
            "job_id": job_id,
            "source": "github",
            "documents": []
        }
        
        for repo_name in config.get("repos", []):
            repo = gh.get_repo(repo_name)
            
            # Extract code patterns
            for branch in config.get("branches", ["main"]):
                contents = repo.get_contents("", ref=branch)
                
                while contents:
                    file_content = contents.pop(0)
                    
                    if file_content.type == "dir":
                        contents.extend(repo.get_contents(file_content.path, ref=branch))
                    else:
                        # Process file
                        if file_content.path.endswith(('.py', '.js', '.ts', '.java')):
                            doc = extract_code_file(repo, file_content, branch)
                            results["documents"].append(doc)
                        
                        elif file_content.path.endswith('.md'):
                            doc = extract_markdown_file(repo, file_content, branch)
                            results["documents"].append(doc)
            
            # Extract commits (for patterns and decisions)
            commits = repo.get_commits(since=config.get("since"))
            for commit in commits:
                doc = {
                    "type": "commit",
                    "repo": repo_name,
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date.isoformat(),
                    "files_changed": [f.filename for f in commit.files],
                    "raw_content": commit.commit.message
                }
                results["documents"].append(doc)
            
            # Extract PRs (for team collaboration patterns)
            pulls = repo.get_pulls(state="closed")
            for pr in pulls[:100]:  # Limit to recent 100
                doc = {
                    "type": "pull_request",
                    "repo": repo_name,
                    "number": pr.number,
                    "title": pr.title,
                    "body": pr.body or "",
                    "author": pr.user.login,
                    "merged": pr.merged,
                    "comments_count": pr.comments,
                    "created_at": pr.created_at.isoformat(),
                    "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                    "raw_content": f"# {pr.title}\n\n{pr.body or ''}"
                }
                results["documents"].append(doc)
        
        # Store results
        store_extraction_results(job_id, "github", results)
        
        return {
            "status": "success",
            "documents_extracted": len(results["documents"])
        }
        
    except Exception as e:
        logger.error(f"GitHub extraction failed for job {job_id}: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)

def extract_code_file(repo, file_content, branch):
    """
    Extract code patterns and documentation from code files
    """
    try:
        content = file_content.decoded_content.decode('utf-8')
        
        # Parse Python AST for patterns
        if file_content.path.endswith('.py'):
            tree = ast.parse(content)
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        else:
            functions = []
            classes = []
        
        return {
            "type": "code_file",
            "repo": repo.name,
            "path": file_content.path,
            "language": get_language(file_content.path),
            "size": file_content.size,
            "functions": functions,
            "classes": classes,
            "raw_content": content,
            "metadata": {
                "branch": branch,
                "last_modified": file_content.last_modified
            }
        }
    except Exception as e:
        logger.warning(f"Failed to parse {file_content.path}: {e}")
        return None
```

### Confluence Extractor

```python
from atlassian import Confluence

@celery_app.task(bind=True, name="extract_confluence")
def extract_confluence(self: Task, job_id: str, config: dict) -> dict:
    """
    Extract knowledge from Confluence spaces
    
    Extracts:
    - Page content (markdown)
    - Page comments
    - Attachments (PDFs, docs)
    - Page hierarchy and relationships
    - Page metadata (labels, author, dates)
    """
    try:
        confluence = Confluence(
            url=config.get("url"),
            username=config.get("username"),
            password=config.get("api_token")
        )
        
        results = {
            "job_id": job_id,
            "source": "confluence",
            "documents": []
        }
        
        for space_key in config.get("spaces", []):
            # Get all pages in space
            pages = confluence.get_all_pages_from_space(
                space_key,
                start=0,
                limit=1000,
                expand='body.storage,version,metadata.labels'
            )
            
            for page in pages:
                # Extract page content
                doc = {
                    "type": "confluence_page",
                    "space": space_key,
                    "page_id": page['id'],
                    "title": page['title'],
                    "content": confluence.convert_to_markdown(page['body']['storage']['value']),
                    "author": page['version']['by']['displayName'],
                    "created_date": page['version']['when'],
                    "labels": [label['name'] for label in page['metadata']['labels']['results']],
                    "raw_content": page['body']['storage']['value'],
                    "metadata": {
                        "version": page['version']['number'],
                        "url": f"{config['url']}/pages/viewpage.action?pageId={page['id']}"
                    }
                }
                
                # Filter by labels if specified
                if labels := config.get("labels"):
                    if any(label in doc['labels'] for label in labels):
                        results["documents"].append(doc)
                else:
                    results["documents"].append(doc)
                
                # Extract comments
                comments = confluence.get_page_comments(page['id'])
                for comment in comments.get('results', []):
                    comment_doc = {
                        "type": "confluence_comment",
                        "space": space_key,
                        "page_id": page['id'],
                        "page_title": page['title'],
                        "author": comment['version']['by']['displayName'],
                        "created_date": comment['version']['when'],
                        "content": comment['body']['storage']['value'],
                        "raw_content": comment['body']['storage']['value']
                    }
                    results["documents"].append(comment_doc)
        
        store_extraction_results(job_id, "confluence", results)
        
        return {
            "status": "success",
            "documents_extracted": len(results["documents"])
        }
        
    except Exception as e:
        logger.error(f"Confluence extraction failed for job {job_id}: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
```

### Jira Extractor

```python
from jira import JIRA

@celery_app.task(bind=True, name="extract_jira")
def extract_jira(self: Task, job_id: str, config: dict) -> dict:
    """
    Extract knowledge from Jira projects
    
    Extracts:
    - Issue descriptions and comments
    - Sprint data
    - Issue relationships (blocks, depends on)
    - Work log patterns
    - Velocity and estimation data
    """
    try:
        jira = JIRA(
            server=config.get("url"),
            basic_auth=(config.get("username"), config.get("api_token"))
        )
        
        results = {
            "job_id": job_id,
            "source": "jira",
            "documents": []
        }
        
        for project_key in config.get("projects", []):
            # JQL query
            jql = f"project = {project_key}"
            if issue_types := config.get("issue_types"):
                jql += f" AND issuetype IN ({','.join(issue_types)})"
            
            issues = jira.search_issues(jql, maxResults=1000, expand='changelog')
            
            for issue in issues:
                doc = {
                    "type": "jira_issue",
                    "project": project_key,
                    "issue_key": issue.key,
                    "issue_type": issue.fields.issuetype.name,
                    "title": issue.fields.summary,
                    "description": issue.fields.description or "",
                    "status": issue.fields.status.name,
                    "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                    "reporter": issue.fields.reporter.displayName,
                    "created": issue.fields.created,
                    "updated": issue.fields.updated,
                    "priority": issue.fields.priority.name if issue.fields.priority else None,
                    "labels": issue.fields.labels,
                    "story_points": getattr(issue.fields, 'customfield_10016', None),  # Example custom field
                    "raw_content": f"# {issue.fields.summary}\n\n{issue.fields.description or ''}",
                    "metadata": {
                        "url": f"{config['url']}/browse/{issue.key}"
                    }
                }
                results["documents"].append(doc)
                
                # Extract comments
                for comment in issue.fields.comment.comments:
                    comment_doc = {
                        "type": "jira_comment",
                        "project": project_key,
                        "issue_key": issue.key,
                        "author": comment.author.displayName,
                        "created": comment.created,
                        "body": comment.body,
                        "raw_content": comment.body
                    }
                    results["documents"].append(comment_doc)
        
        store_extraction_results(job_id, "jira", results)
        
        return {
            "status": "success",
            "documents_extracted": len(results["documents"])
        }
        
    except Exception as e:
        logger.error(f"Jira extraction failed for job {job_id}: {e}")
        raise self.retry(exc=e, countdown=60, max_retries=3)
```

---

## Worker Type 2: Normalization Workers

```python
import markdown
import re
from bs4 import BeautifulSoup

@celery_app.task(bind=True, name="normalize_document")
def normalize_document(self: Task, job_id: str, document: dict) -> dict:
    """
    Normalize extracted document into clean markdown format
    
    Steps:
    1. Convert to markdown if needed
    2. Clean HTML/formatting
    3. Extract metadata
    4. Classify scope (tier)
    5. Resolve links and references
    """
    try:
        # Step 1: Convert to markdown
        if document["type"] in ["confluence_page", "jira_issue"]:
            md_content = html_to_markdown(document["raw_content"])
        elif document["type"] == "code_file":
            md_content = code_to_markdown(document)
        elif document["type"] in ["commit", "pull_request"]:
            md_content = document["raw_content"]
        else:
            md_content = document.get("raw_content", "")
        
        # Step 2: Clean content
        cleaned_content = clean_markdown(md_content)
        
        # Step 3: Extract metadata
        metadata = extract_metadata(document)
        
        # Step 4: Classify scope
        scope_tiers = classify_scope(document, cleaned_content)
        
        # Step 5: Resolve links
        resolved_content = resolve_links(cleaned_content, document)
        
        normalized = {
            "job_id": job_id,
            "document_id": generate_doc_id(document),
            "type": document["type"],
            "content": resolved_content,
            "metadata": metadata,
            "scope_tiers": scope_tiers,  # [0, 1, 3] means Client, Project, Company
            "word_count": len(resolved_content.split()),
            "source": document.get("repo") or document.get("space") or document.get("project"),
            "timestamp": metadata.get("created_date") or metadata.get("date")
        }
        
        # Store normalized document
        store_normalized_document(job_id, normalized)
        
        return {
            "status": "success",
            "document_id": normalized["document_id"]
        }
        
    except Exception as e:
        logger.error(f"Normalization failed for document: {e}")
        raise self.retry(exc=e, countdown=30, max_retries=3)

def classify_scope(document: dict, content: str) -> List[int]:
    """
    Classify which MCP tier(s) this document belongs to
    
    Rules:
    - Client tier (0): Mentions client name, client-specific terms
    - Project tier (1): Mentions project name, project-specific features
    - Team tier (2): Mentions team name, team practices, coding patterns
    - Company tier (3): Mentions company standards, processes, templates
    - Ecosystem tier (4): Generic patterns, universal knowledge
    """
    tiers = []
    
    # Simple keyword-based classification (can be enhanced with LLM)
    content_lower = content.lower()
    
    # Check for client indicators
    if any(keyword in content_lower for keyword in ["client", "acme", "customer-specific"]):
        tiers.append(0)
    
    # Check for project indicators
    if any(keyword in content_lower for keyword in ["project alpha", "sprint", "epic"]):
        tiers.append(1)
    
    # Check for team indicators
    if any(keyword in content_lower for keyword in ["team", "pair programming", "code review"]):
        tiers.append(2)
    
    # Check for company indicators
    if any(keyword in content_lower for keyword in ["company policy", "standard", "template"]):
        tiers.append(3)
    
    # Default to ecosystem if no specific tier found
    if not tiers:
        tiers.append(4)
    
    return tiers

def code_to_markdown(document: dict) -> str:
    """
    Convert code file to markdown with syntax highlighting
    """
    language = document.get("language", "python")
    code = document["raw_content"]
    
    md = f"# File: {document['path']}\n\n"
    md += f"**Language:** {language}  \n"
    md += f"**Repository:** {document['repo']}  \n"
    
    if document.get("functions"):
        md += f"**Functions:** {', '.join(document['functions'])}  \n"
    if document.get("classes"):
        md += f"**Classes:** {', '.join(document['classes'])}  \n"
    
    md += f"\n```{language}\n{code}\n```\n"
    
    return md

def clean_markdown(md_content: str) -> str:
    """
    Clean markdown content
    """
    # Remove excessive whitespace
    cleaned = re.sub(r'\n{3,}', '\n\n', md_content)
    
    # Remove HTML comments
    cleaned = re.sub(r'<!--.*?-->', '', cleaned, flags=re.DOTALL)
    
    # Normalize headers
    cleaned = re.sub(r'^#{7,}', '######', cleaned, flags=re.MULTILINE)
    
    return cleaned.strip()

def resolve_links(content: str, document: dict) -> str:
    """
    Resolve relative links to absolute URLs
    """
    # GitHub links
    if "repo" in document:
        base_url = f"https://github.com/{document['repo']}/blob/main"
        content = re.sub(
            r'\[([^\]]+)\]\(([^http][^\)]+)\)',
            f'[\\1]({base_url}/\\2)',
            content
        )
    
    # Confluence links
    if "space" in document and "confluence" in document.get("type", ""):
        base_url = document["metadata"].get("url", "")
        # Confluence link resolution logic here
    
    return content
```

---

## Worker Type 3: Embedding & Tagging Workers

```python
import ollama
from typing import List

@celery_app.task(bind=True, name="create_embeddings")
def create_embeddings(self: Task, job_id: str, document: dict, training_params: dict) -> dict:
    """
    Create embeddings, tags, entities, and relationships for a normalized document
    
    Steps:
    1. Chunk document
    2. Generate embeddings
    3. Auto-tag using LLM
    4. Extract entities
    5. Build relationships
    6. Validate quality
    """
    try:
        chunk_size = training_params.get("chunk_size", 500)
        chunk_overlap = training_params.get("chunk_overlap", 50)
        embedding_model = training_params.get("embedding_model", "nomic-embed-text")
        
        # Step 1: Chunk document
        chunks = chunk_text(document["content"], chunk_size, chunk_overlap)
        
        # Step 2: Generate embeddings
        embeddings = []
        for i, chunk in enumerate(chunks):
            embedding = ollama.embeddings(
                model=embedding_model,
                prompt=chunk
            )
            embeddings.append({
                "chunk_id": f"{document['document_id']}_chunk_{i}",
                "text": chunk,
                "embedding": embedding["embedding"],
                "metadata": {
                    "document_id": document["document_id"],
                    "chunk_index": i,
                    "scope_tiers": document["scope_tiers"],
                    "source": document["source"],
                    "timestamp": document["timestamp"]
                }
            })
        
        # Step 3: Auto-tag using LLM
        tags = generate_tags_with_llm(document["content"], embedding_model)
        
        # Step 4: Extract entities
        entities = extract_entities(document["content"])
        
        # Step 5: Build relationships
        relationships = build_relationships(document, entities)
        
        # Step 6: Validate quality
        quality_score = validate_quality(embeddings, tags, entities)
        
        if quality_score < 0.5:
            logger.warning(f"Low quality score {quality_score} for document {document['document_id']}")
        
        processed = {
            "job_id": job_id,
            "document_id": document["document_id"],
            "embeddings": embeddings,
            "tags": tags,
            "entities": entities,
            "relationships": relationships,
            "quality_score": quality_score
        }
        
        # Store processed data
        store_processed_data(job_id, processed)
        
        return {
            "status": "success",
            "document_id": document["document_id"],
            "chunks_created": len(embeddings),
            "quality_score": quality_score
        }
        
    except Exception as e:
        logger.error(f"Embedding creation failed: {e}")
        raise self.retry(exc=e, countdown=30, max_retries=3)

def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Split text into overlapping chunks
    """
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    
    return chunks

def generate_tags_with_llm(content: str, model: str) -> List[str]:
    """
    Use LLM to generate semantic tags
    """
    prompt = f"""
    Read the following document and generate 5-10 semantic tags that describe its content.
    Tags should be lowercase, single words or short phrases (max 3 words).
    
    Document:
    {content[:2000]}  # Truncate for performance
    
    Tags (comma-separated):
    """
    
    response = ollama.generate(model="llama3.2:3b", prompt=prompt)
    tags_text = response["response"].strip()
    
    # Parse tags
    tags = [tag.strip().lower() for tag in tags_text.split(",")]
    
    return tags[:10]  # Max 10 tags

def extract_entities(content: str) -> List[dict]:
    """
    Extract entities (people, technologies, concepts) from content
    """
    entities = []
    
    # Extract people (simple approach - can be enhanced with NER)
    people_pattern = r'@(\w+)|by (\w+ \w+)|author: (\w+ \w+)'
    people_matches = re.findall(people_pattern, content, re.IGNORECASE)
    for match in people_matches:
        person = next(m for m in match if m)
        entities.append({
            "type": "person",
            "value": person,
            "confidence": 0.8
        })
    
    # Extract technologies (keywords)
    tech_keywords = ['python', 'fastapi', 'docker', 'kubernetes', 'postgres', 'redis', 'react', 'typescript']
    for tech in tech_keywords:
        if re.search(rf'\b{tech}\b', content, re.IGNORECASE):
            entities.append({
                "type": "technology",
                "value": tech,
                "confidence": 1.0
            })
    
    # Extract concepts (section headers)
    headers = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
    for header in headers:
        entities.append({
            "type": "concept",
            "value": header.strip(),
            "confidence": 0.9
        })
    
    return entities

def build_relationships(document: dict, entities: List[dict]) -> List[dict]:
    """
    Build relationships for Neo4j graph
    """
    relationships = []
    
    # Document -> Entity relationships
    for entity in entities:
        relationships.append({
            "from_id": document["document_id"],
            "from_type": "document",
            "to_id": entity["value"],
            "to_type": entity["type"],
            "relationship_type": "MENTIONS",
            "metadata": {
                "confidence": entity["confidence"],
                "source": document["source"]
            }
        })
    
    # Document -> Source relationships
    relationships.append({
        "from_id": document["document_id"],
        "from_type": "document",
        "to_id": document["source"],
        "to_type": "source",
        "relationship_type": "FROM_SOURCE",
        "metadata": {
            "timestamp": document["timestamp"]
        }
    })
    
    # Add author relationships if available
    if author := document["metadata"].get("author"):
        relationships.append({
            "from_id": author,
            "from_type": "person",
            "to_id": document["document_id"],
            "to_type": "document",
            "relationship_type": "AUTHORED",
            "metadata": {
                "timestamp": document["timestamp"]
            }
        })
    
    return relationships

def validate_quality(embeddings: List[dict], tags: List[str], entities: List[dict]) -> float:
    """
    Calculate quality score for processed data
    """
    score = 0.0
    
    # Check embedding quality
    if embeddings:
        avg_embedding_length = sum(len(e["embedding"]) for e in embeddings) / len(embeddings)
        if avg_embedding_length > 100:  # Nomic embeddings are typically 768 dims
            score += 0.3
    
    # Check tags quality
    if tags and len(tags) >= 3:
        score += 0.3
    
    # Check entities quality
    if entities and len(entities) >= 2:
        score += 0.2
    
    # Check content length
    if embeddings and sum(len(e["text"].split()) for e in embeddings) > 50:
        score += 0.2
    
    return min(score, 1.0)
```

---

## Loading Stage

### ChromaDB Loader

```python
import chromadb
from chromadb.config import Settings

async def load_to_chromadb(mcp_id: str, embeddings_data: List[dict]):
    """
    Load embeddings into ChromaDB for the target MCP
    """
    # Connect to MCP's ChromaDB instance
    client = chromadb.HttpClient(
        host=f"chromadb-{mcp_id}",
        port=8000,
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Get or create collection
    collection = client.get_or_create_collection(
        name=f"mcp_{mcp_id}_knowledge",
        metadata={"hnsw:space": "cosine"}
    )
    
    # Batch insert embeddings
    batch_size = 100
    for i in range(0, len(embeddings_data), batch_size):
        batch = embeddings_data[i:i + batch_size]
        
        ids = [emb["chunk_id"] for emb in batch]
        embeddings = [emb["embedding"] for emb in batch]
        documents = [emb["text"] for emb in batch]
        metadatas = [emb["metadata"] for emb in batch]
        
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
    
    logger.info(f"Loaded {len(embeddings_data)} embeddings into ChromaDB for MCP {mcp_id}")
```

### Neo4j Loader

```python
from neo4j import GraphDatabase

async def load_to_neo4j(mcp_id: str, relationships_data: List[dict]):
    """
    Load relationships into Neo4j for the target MCP
    """
    driver = GraphDatabase.driver(
        f"bolt://neo4j-{mcp_id}:7687",
        auth=("neo4j", "password")
    )
    
    with driver.session() as session:
        # Create nodes
        nodes = {}
        for rel in relationships_data:
            nodes[rel["from_id"]] = rel["from_type"]
            nodes[rel["to_id"]] = rel["to_type"]
        
        for node_id, node_type in nodes.items():
            session.run(
                f"MERGE (n:{node_type} {{id: $id}})",
                id=node_id
            )
        
        # Create relationships
        for rel in relationships_data:
            session.run(
                f"""
                MATCH (a:{rel['from_type']} {{id: $from_id}})
                MATCH (b:{rel['to_type']} {{id: $to_id}})
                MERGE (a)-[r:{rel['relationship_type']}]->(b)
                SET r += $metadata
                """,
                from_id=rel["from_id"],
                to_id=rel["to_id"],
                metadata=rel["metadata"]
            )
    
    driver.close()
    logger.info(f"Loaded {len(relationships_data)} relationships into Neo4j for MCP {mcp_id}")
```

---

## Incremental Training

```python
async def incremental_training(mcp_id: str, new_data_sources: List[DataSource]):
    """
    Perform incremental training - add new data without full retrain
    
    Steps:
    1. Extract only new documents (since last training)
    2. Normalize and embed new documents
    3. Append to existing ChromaDB and Neo4j
    4. Update metadata with new training timestamp
    """
    # Get last training timestamp
    last_training = get_last_training_timestamp(mcp_id)
    
    # Modify data source configs to filter by timestamp
    for source in new_data_sources:
        source.config["since"] = last_training
    
    # Create incremental training job
    job = TrainingJobRequest(
        mcp_id=mcp_id,
        tier=get_mcp_tier(mcp_id),
        data_sources=new_data_sources,
        training_params=get_default_training_params(),
        incremental=True,
        priority="normal"
    )
    
    # Execute pipeline
    await execute_training_pipeline(job)
```

---

## Monitoring & Metrics

### Training Job Metrics

- **Documents Extracted:** Count per source type
- **Normalization Success Rate:** % of documents successfully normalized
- **Embedding Quality:** Average quality score
- **Processing Time:** Time per phase, total time
- **Worker Utilization:** % of workers actively processing
- **Error Rate:** % of documents that failed processing

### Dashboard Views

- **Active Jobs:** Real-time status of running training jobs
- **Job History:** Past jobs with success/failure rates
- **Worker Pool Health:** Worker status, queue depth, throughput
- **MCP Training Status:** Last trained timestamp per MCP
- **Data Source Coverage:** What % of available data is indexed

---

## Error Handling & Retries

### Retry Strategy

- **Extraction Failures:** Retry 3 times with exponential backoff
- **API Rate Limits:** Exponential backoff (60s, 120s, 300s)
- **Network Errors:** Retry 5 times with 30s delay
- **Validation Failures:** Log and skip document (don't block pipeline)

### Dead Letter Queue

Documents that fail all retries are moved to a Dead Letter Queue for manual review and reprocessing.

---

## Next Steps

1. Implement Training Coordinator service
2. Implement extraction workers (GitHub, Confluence, Jira)
3. Implement normalization workers
4. Implement embedding workers
5. Implement loading stage (ChromaDB, Neo4j)
6. Create monitoring dashboard
7. Test with sample data sources
8. Optimize for performance (parallelization, batching)
9. Add incremental training capability
10. Integrate with MCP Provisioner

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-06  
**Status:** Draft - Detailed Design

