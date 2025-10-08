# Enriched Multi-Source Ingestion Plan

**Date**: October 8, 2025  
**Status**: Comprehensive Architecture for Unified Document Ingestion

---

## 🎯 Overview

Create a unified ingestion pipeline that:
- ✅ Ingests from **multiple sources** (GitHub, Jira, Confluence, local files)
- ✅ **Detects file types** (code vs documents)
- ✅ **Normalizes to Markdown** for embedding/tagging
- ✅ **Preserves metadata** (original format, correlations, timestamps)
- ✅ **Correlates data** across sources (commits ↔ Jira ↔ PRs)
- ✅ **E2E tested** with mock data
- ✅ **Integrated in demo** script

---

## 📊 Architecture

### Data Flow
```
┌─────────────────────────────────────────────────────────────────┐
│                      INGESTION SOURCES                          │
├──────────┬──────────┬──────────┬──────────┬────────────────────┤
│  GitHub  │   Jira   │Confluence│  Local   │  Code Analyzer     │
│ Commits  │ Tickets  │  Pages   │  Files   │    Service         │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴──────┬────────────┘
     │          │          │          │            │
     ▼          ▼          ▼          ▼            ▼
┌─────────────────────────────────────────────────────────────────┐
│              FILE TYPE DETECTION & ROUTING                      │
│  Code Files (.py, .js, .java) → Code Analyzer                  │
│  Documents (.md, .txt, .doc) → Direct Normalization            │
│  Images/Binary → Metadata extraction only                       │
└─────────────────────┬───────────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              NORMALIZATION TO MARKDOWN                          │
│  - Convert content to .md format                                │
│  - Preserve original format in metadata                         │
│  - Extract code documentation (functions, APIs, docstrings)     │
│  - Add frontmatter with metadata                                │
└─────────────────────┬───────────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              CORRELATION ENGINE                                 │
│  - Match commits → Jira tickets (via ticket IDs in messages)   │
│  - Link PRs → commits → tickets                                 │
│  - Connect Confluence docs → Jira → code                        │
│  - Add correlation tags to metadata                             │
└─────────────────────┬───────────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              TAGGING & ENRICHMENT                               │
│  Tags Added:                                                    │
│  - source: github|jira|confluence|local                         │
│  - file_type: code|document|image                               │
│  - language: python|javascript|markdown|...                     │
│  - related_jira: [PROJ-123, PROJ-456]                          │
│  - related_commits: [abc123, def456]                            │
│  - related_prs: [#42, #89]                                      │
│  - created_at, updated_at, author, repo, branch                 │
└─────────────────────┬───────────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              INGESTION TO MCP TRAINING                          │
│  via kafka-ingestion-service → doc_store → MCP                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementation Components

### 1. Multi-Source Ingestors

#### 1.1 GitHub Ingestion
**File**: `ingestion/github_ingestor.py`

```python
class GitHubIngestor:
    """Ingest commits, PRs, and files from GitHub."""
    
    async def ingest_repository(
        self,
        repo: str,
        branch: str = "main",
        commit_limit: int = 200
    ) -> List[NormalizedDocument]:
        """
        Ingest entire repository with commit history.
        
        Saves last 200 commits to static JSON file.
        """
        # 1. Fetch and save commits
        commits = await self._fetch_commits(repo, branch, commit_limit)
        await self._save_commits_to_json(commits, f"commits_{repo.replace('/', '_')}.json")
        
        # 2. Discover files (code + docs)
        files = await self._discover_files(repo, branch)
        
        # 3. Normalize each file
        documents = []
        for file_info in files:
            doc = await self._normalize_file(file_info, commits)
            documents.append(doc)
        
        return documents
    
    async def _normalize_file(self, file_info: dict, commits: List) -> NormalizedDocument:
        """Normalize GitHub file to standard document format."""
        # Detect file type
        file_type = self._detect_file_type(file_info['path'])
        
        if file_type == 'code':
            # Send to code analyzer
            content = await self._analyze_code(file_info)
        else:
            # Direct content extraction
            content = file_info['content']
        
        # Find related commits
        related_commits = self._find_commits_for_file(file_info['path'], commits)
        
        # Extract Jira ticket references from commits
        jira_tickets = self._extract_jira_tickets(related_commits)
        
        return NormalizedDocument(
            document_id=f"github-{file_info['sha'][:8]}",
            title=f"{file_info['repo']}: {file_info['path']}",
            content_md=content,  # Already in markdown
            original_format=file_info['path'].split('.')[-1],
            metadata={
                'source': 'github',
                'file_type': file_type,
                'language': self._detect_language(file_info['path']),
                'repo': file_info['repo'],
                'branch': file_info['branch'],
                'path': file_info['path'],
                'sha': file_info['sha'],
                'related_commits': [c['sha'] for c in related_commits],
                'related_jira': jira_tickets,
                'created_at': related_commits[-1]['date'] if related_commits else None,
                'updated_at': related_commits[0]['date'] if related_commits else None,
                'last_author': related_commits[0]['author'] if related_commits else None,
            },
            tags=self._generate_tags(file_type, file_info, jira_tickets)
        )
```

#### 1.2 Jira Ingestion
**File**: `ingestion/jira_ingestor.py`

```python
class JiraIngestor:
    """Ingest Jira tickets and correlate with commits."""
    
    async def ingest_from_commits(
        self,
        commits: List[dict],
        project_key: str = "PROJ"
    ) -> List[NormalizedDocument]:
        """
        Generate believable Jira tickets from commit history.
        
        Uses commit context to create realistic tickets.
        """
        # Group commits by feature (use commit message patterns)
        features = self._group_commits_by_feature(commits)
        
        documents = []
        for feature_name, feature_commits in features.items():
            ticket = await self._generate_ticket(
                feature_name,
                feature_commits,
                project_key
            )
            documents.append(ticket)
        
        return documents
    
    async def _generate_ticket(
        self,
        feature_name: str,
        commits: List[dict],
        project_key: str
    ) -> NormalizedDocument:
        """Generate a believable Jira ticket from commits."""
        ticket_id = f"{project_key}-{random.randint(100, 999)}"
        
        # Build description from commits
        description = f"## Description\n\n"
        description += f"Implement {feature_name} feature.\n\n"
        description += f"## Commits\n\n"
        for commit in commits:
            description += f"- `{commit['sha'][:8]}`: {commit['message']}\n"
        
        description += f"\n## Implementation Details\n\n"
        description += self._summarize_changes(commits)
        
        # Convert to markdown
        content_md = f"""# {ticket_id}: {feature_name}

**Type**: Story  
**Priority**: High  
**Status**: Done  
**Reporter**: {commits[0]['author']}  
**Assignee**: {commits[0]['author']}  

{description}

## Acceptance Criteria

- [x] Code implemented in commits: {', '.join(c['sha'][:8] for c in commits)}
- [x] Tests passing
- [x] Documentation updated

## Related

- **Repository**: {commits[0].get('repo', 'unknown')}
- **Branch**: {commits[0].get('branch', 'main')}
- **PR**: #{commits[0].get('pr_number', 'N/A')}
"""
        
        return NormalizedDocument(
            document_id=f"jira-{ticket_id}",
            title=f"{ticket_id}: {feature_name}",
            content_md=content_md,
            original_format='jira',
            metadata={
                'source': 'jira',
                'file_type': 'document',
                'ticket_id': ticket_id,
                'ticket_type': 'Story',
                'status': 'Done',
                'priority': 'High',
                'related_commits': [c['sha'] for c in commits],
                'related_repos': list(set(c.get('repo') for c in commits)),
                'related_branches': list(set(c.get('branch') for c in commits)),
                'related_prs': list(set(c.get('pr_number') for c in commits if c.get('pr_number'))),
                'created_at': commits[-1]['date'],
                'updated_at': commits[0]['date'],
                'reporter': commits[0]['author'],
            },
            tags=[
                f"source:jira",
                f"type:story",
                f"status:done",
                f"feature:{feature_name.lower().replace(' ', '-')}",
                *[f"commit:{c['sha'][:8]}" for c in commits[:5]]
            ]
        )
```

#### 1.3 Confluence Ingestion
**File**: `ingestion/confluence_ingestor.py`

```python
class ConfluenceIngestor:
    """Ingest Confluence pages."""
    
    async def ingest_pages(
        self,
        space_key: str,
        page_ids: List[str] = None
    ) -> List[NormalizedDocument]:
        """Ingest Confluence pages with Jira ticket references."""
        pages = await self._fetch_pages(space_key, page_ids)
        
        documents = []
        for page in pages:
            doc = await self._normalize_page(page)
            documents.append(doc)
        
        return documents
    
    async def _normalize_page(self, page: dict) -> NormalizedDocument:
        """Normalize Confluence page to markdown."""
        # Convert HTML to Markdown
        content_md = self._html_to_markdown(page['body']['storage']['value'])
        
        # Extract Jira ticket references
        jira_tickets = self._extract_jira_references(content_md)
        
        # Add metadata header
        frontmatter = f"""---
title: {page['title']}
space: {page['space']['key']}
confluence_id: {page['id']}
created: {page['history']['createdDate']}
updated: {page['version']['when']}
author: {page['version']['by']['displayName']}
related_jira: {', '.join(jira_tickets)}
---

"""
        
        content_md = frontmatter + content_md
        
        return NormalizedDocument(
            document_id=f"confluence-{page['id']}",
            title=page['title'],
            content_md=content_md,
            original_format='confluence',
            metadata={
                'source': 'confluence',
                'file_type': 'document',
                'space_key': page['space']['key'],
                'page_id': page['id'],
                'related_jira': jira_tickets,
                'created_at': page['history']['createdDate'],
                'updated_at': page['version']['when'],
                'author': page['version']['by']['displayName'],
                'url': page['_links']['base'] + page['_links']['webui'],
            },
            tags=[
                f"source:confluence",
                f"space:{page['space']['key']}",
                *[f"jira:{ticket}" for ticket in jira_tickets]
            ]
        )
```

#### 1.4 Wikipedia Crawling & Ingestion
**File**: `ingestion/wikipedia_ingestor.py`

```python
class WikipediaIngestor:
    """Crawl and ingest Wikipedia pages with configurable depth."""
    
    def __init__(self):
        self.visited_pages = set()
        self.crawl_graph = {}  # Track link relationships
    
    async def crawl_and_ingest(
        self,
        original_page_url: str,
        max_surface_links: int = 10,
        max_depth_distance: int = 2
    ) -> List[NormalizedDocument]:
        """
        Crawl Wikipedia starting from a page.
        
        Args:
            original_page_url: Starting Wikipedia URL
            max_surface_links: Max number of direct links from original page
            max_depth_distance: Max link depth (0 = original only, 1 = +direct links, etc.)
        
        Returns:
            List of normalized documents with link relationships
        
        Example:
            Original: https://en.wikipedia.org/wiki/Machine_learning
            max_surface_links=5, max_depth_distance=2
            
            Depth 0 (original): Machine_learning
            Depth 1 (direct links, max 5): Artificial_intelligence, Deep_learning, Neural_network, Supervised_learning, Unsupervised_learning
            Depth 2 (links from depth 1, max 5 each): ... up to 25 more pages
        """
        self.print_info(f"Starting Wikipedia crawl from: {original_page_url}")
        self.print_info(f"Parameters: max_surface_links={max_surface_links}, max_depth_distance={max_depth_distance}")
        
        # Parse original page info
        page_title = self._extract_page_title(original_page_url)
        
        # Start crawling
        documents = await self._crawl_recursive(
            page_url=original_page_url,
            page_title=page_title,
            current_depth=0,
            max_depth=max_depth_distance,
            max_links_per_page=max_surface_links,
            parent_page=None
        )
        
        # Add crawl metadata to all documents
        for doc in documents:
            doc.metadata['crawl_origin'] = page_title
            doc.metadata['crawl_max_depth'] = max_depth_distance
            doc.metadata['crawl_max_surface'] = max_surface_links
        
        self.print_success(f"Crawled {len(documents)} Wikipedia pages")
        self.print_info(f"Crawl graph: {len(self.crawl_graph)} nodes")
        
        return documents
    
    async def _crawl_recursive(
        self,
        page_url: str,
        page_title: str,
        current_depth: int,
        max_depth: int,
        max_links_per_page: int,
        parent_page: Optional[str]
    ) -> List[NormalizedDocument]:
        """Recursively crawl Wikipedia pages."""
        
        # Check if already visited
        if page_url in self.visited_pages:
            return []
        
        # Check depth limit
        if current_depth > max_depth:
            return []
        
        self.visited_pages.add(page_url)
        documents = []
        
        # Fetch and normalize current page
        try:
            page_data = await self._fetch_wikipedia_page(page_url)
            doc = await self._normalize_wikipedia_page(
                page_data,
                current_depth,
                parent_page
            )
            documents.append(doc)
            
            print(f"  {'  ' * current_depth}[Depth {current_depth}] {page_title} → {len(page_data['links'])} links found")
            
            # Track in crawl graph
            self.crawl_graph[page_title] = {
                'url': page_url,
                'depth': current_depth,
                'parent': parent_page,
                'children': []
            }
            
            # If not at max depth, crawl linked pages
            if current_depth < max_depth:
                # Filter and limit links
                links_to_crawl = self._filter_links(
                    page_data['links'],
                    max_links_per_page
                )
                
                # Crawl each link
                for link_title, link_url in links_to_crawl:
                    if link_url not in self.visited_pages:
                        # Track parent-child relationship
                        self.crawl_graph[page_title]['children'].append(link_title)
                        
                        # Recursive crawl
                        child_docs = await self._crawl_recursive(
                            page_url=link_url,
                            page_title=link_title,
                            current_depth=current_depth + 1,
                            max_depth=max_depth,
                            max_links_per_page=max_links_per_page,
                            parent_page=page_title
                        )
                        documents.extend(child_docs)
                        
                        # Rate limiting
                        await asyncio.sleep(0.5)
        
        except Exception as e:
            logger.warning(f"Failed to crawl {page_url}: {e}")
        
        return documents
    
    async def _fetch_wikipedia_page(self, url: str) -> dict:
        """Fetch Wikipedia page content and extract links."""
        async with httpx.AsyncClient() as client:
            # Use Wikipedia API for structured data
            api_url = "https://en.wikipedia.org/w/api.php"
            
            page_title = self._extract_page_title(url)
            
            # Fetch page content
            params = {
                'action': 'query',
                'format': 'json',
                'titles': page_title,
                'prop': 'extracts|links|info|revisions',
                'explaintext': True,
                'pllimit': 500,  # Get up to 500 links
                'inprop': 'url',
                'rvprop': 'timestamp|user'
            }
            
            response = await client.get(api_url, params=params)
            data = response.json()
            
            page = list(data['query']['pages'].values())[0]
            
            # Extract links
            links = []
            if 'links' in page:
                for link in page['links']:
                    link_title = link['title']
                    # Only include article links (no special pages)
                    if not link_title.startswith(('Wikipedia:', 'File:', 'Template:', 'Category:')):
                        link_url = f"https://en.wikipedia.org/wiki/{link_title.replace(' ', '_')}"
                        links.append((link_title, link_url))
            
            return {
                'title': page.get('title', ''),
                'content': page.get('extract', ''),
                'url': page.get('fullurl', url),
                'links': links,
                'last_modified': page.get('revisions', [{}])[0].get('timestamp'),
                'last_editor': page.get('revisions', [{}])[0].get('user')
            }
    
    async def _normalize_wikipedia_page(
        self,
        page_data: dict,
        depth: int,
        parent_page: Optional[str]
    ) -> NormalizedDocument:
        """Normalize Wikipedia page to markdown format."""
        
        # Convert Wikipedia content to markdown
        content_md = f"""# {page_data['title']}

**Source**: Wikipedia  
**URL**: {page_data['url']}  
**Last Modified**: {page_data['last_modified']}  
**Last Editor**: {page_data['last_editor']}  
**Crawl Depth**: {depth}  
**Parent Page**: {parent_page or 'N/A (origin)'}

---

## Content

{page_data['content']}

---

## Links Found

This page contains {len(page_data['links'])} links to other Wikipedia articles.

"""
        
        # Add link graph if not at origin
        if parent_page:
            content_md += f"\n**Navigation**: [Origin] → ... → [{parent_page}] → **[{page_data['title']}]**\n"
        
        # Extract categories from title/content
        categories = self._extract_categories(page_data['title'], page_data['content'])
        
        return NormalizedDocument(
            document_id=f"wikipedia-{hashlib.md5(page_data['url'].encode()).hexdigest()[:8]}",
            title=f"Wikipedia: {page_data['title']}",
            content_md=content_md,
            original_format='wikipedia',
            metadata={
                'source': 'wikipedia',
                'file_type': 'document',
                'language': 'en',
                'url': page_data['url'],
                'page_title': page_data['title'],
                'crawl_depth': depth,
                'parent_page': parent_page,
                'link_count': len(page_data['links']),
                'categories': categories,
                'created_at': page_data['last_modified'],
                'updated_at': page_data['last_modified'],
                'author': page_data['last_editor'],
            },
            tags=[
                "source:wikipedia",
                "file_type:document",
                "language:en",
                f"depth:{depth}",
                *[f"category:{cat}" for cat in categories[:5]]
            ]
        )
    
    def _filter_links(
        self,
        links: List[tuple],
        max_links: int
    ) -> List[tuple]:
        """Filter and prioritize links to crawl."""
        # Prioritize links by relevance
        # For now, just take first N links
        # Could be enhanced with ML ranking
        
        # Filter out common navigation links
        excluded_terms = ['list of', 'index of', 'outline of', 'glossary', 'portal:']
        filtered = [
            (title, url) for title, url in links
            if not any(term in title.lower() for term in excluded_terms)
        ]
        
        return filtered[:max_links]
    
    def _extract_categories(self, title: str, content: str) -> List[str]:
        """Extract categories/topics from Wikipedia page."""
        categories = []
        
        # Simple keyword extraction
        keywords = title.split()
        
        # Common Wikipedia categories
        if any(word in content.lower() for word in ['algorithm', 'computation', 'computer']):
            categories.append('computer-science')
        if any(word in content.lower() for word in ['learning', 'neural', 'model']):
            categories.append('machine-learning')
        if any(word in content.lower() for word in ['history', 'century', 'founded']):
            categories.append('history')
        
        return categories
    
    def _extract_page_title(self, url: str) -> str:
        """Extract page title from Wikipedia URL."""
        # https://en.wikipedia.org/wiki/Machine_learning → Machine_learning
        return url.split('/wiki/')[-1].replace('_', ' ')
    
    def generate_crawl_report(self) -> dict:
        """Generate report of crawl graph."""
        return {
            'total_pages': len(self.visited_pages),
            'crawl_graph': self.crawl_graph,
            'depth_distribution': self._calculate_depth_distribution(),
            'link_statistics': self._calculate_link_statistics()
        }
    
    def _calculate_depth_distribution(self) -> dict:
        """Calculate how many pages at each depth."""
        distribution = {}
        for node in self.crawl_graph.values():
            depth = node['depth']
            distribution[depth] = distribution.get(depth, 0) + 1
        return distribution
    
    def _calculate_link_statistics(self) -> dict:
        """Calculate link statistics."""
        total_children = sum(len(node['children']) for node in self.crawl_graph.values())
        avg_children = total_children / len(self.crawl_graph) if self.crawl_graph else 0
        
        return {
            'total_links_followed': total_children,
            'average_links_per_page': round(avg_children, 2),
            'max_children': max((len(node['children']) for node in self.crawl_graph.values()), default=0)
        }
```

**Usage Example**:
```python
# In demo script
wiki_ingestor = WikipediaIngestor()

# Crawl Wikipedia starting from "Machine Learning"
documents = await wiki_ingestor.crawl_and_ingest(
    original_page_url="https://en.wikipedia.org/wiki/Machine_learning",
    max_surface_links=5,  # Follow 5 direct links
    max_depth_distance=2   # Go 2 levels deep
)

# This will crawl:
# Depth 0: Machine_learning (1 page)
# Depth 1: 5 linked pages (e.g., AI, Deep Learning, Neural Networks, ...)
# Depth 2: Up to 5 links from each depth-1 page (up to 25 more pages)
# Total: 1 + 5 + 25 = up to 31 pages

# Generate crawl report
report = wiki_ingestor.generate_crawl_report()
print(f"Crawled {report['total_pages']} pages")
print(f"Depth distribution: {report['depth_distribution']}")
```

#### 1.5 Local Directory Ingestion
**File**: `ingestion/local_ingestor.py`

```python
class LocalDirectoryIngestor:
    """Ingest files from local directories with type detection."""
    
    SUPPORTED_EXTENSIONS = {
        # Code files
        'code': ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h', 
                 '.cs', '.php', '.rb', '.swift', '.kt', '.scala', '.html', '.css'],
        # Document files
        'document': ['.md', '.txt', '.rst', '.adoc', '.tex'],
        # Office documents
        'office': ['.doc', '.docx', '.pdf', '.odt'],
        # Data files
        'data': ['.json', '.yaml', '.yml', '.xml', '.csv', '.toml'],
        # Images
        'image': ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'],
    }
    
    async def ingest_directory(
        self,
        directory: Path,
        recursive: bool = True
    ) -> List[NormalizedDocument]:
        """Ingest all supported files from directory."""
        files = self._discover_files(directory, recursive)
        
        documents = []
        for file_path in files:
            try:
                doc = await self._normalize_file(file_path)
                documents.append(doc)
            except Exception as e:
                logger.warning(f"Failed to ingest {file_path}: {e}")
        
        return documents
    
    async def _normalize_file(self, file_path: Path) -> NormalizedDocument:
        """Normalize local file to markdown."""
        # Detect file type
        file_category = self._detect_file_category(file_path)
        
        # Get file stats
        stat = file_path.stat()
        created_at = datetime.fromtimestamp(stat.st_ctime).isoformat()
        updated_at = datetime.fromtimestamp(stat.st_mtime).isoformat()
        
        # Get Git info if in repo
        git_info = await self._get_git_info(file_path)
        
        # Route based on file type
        if file_category == 'code':
            content_md = await self._process_code_file(file_path)
        elif file_category == 'document':
            content_md = await self._process_document_file(file_path)
        elif file_category == 'office':
            content_md = await self._process_office_file(file_path)
        elif file_category == 'data':
            content_md = await self._process_data_file(file_path)
        else:
            # Metadata only for images/binary
            content_md = self._generate_metadata_doc(file_path)
        
        # Add frontmatter
        frontmatter = f"""---
title: {file_path.name}
original_format: {file_path.suffix[1:]}
file_size: {stat.st_size}
created: {created_at}
updated: {updated_at}
path: {str(file_path)}
---

"""
        
        content_md = frontmatter + content_md
        
        return NormalizedDocument(
            document_id=f"local-{hashlib.md5(str(file_path).encode()).hexdigest()[:8]}",
            title=file_path.name,
            content_md=content_md,
            original_format=file_path.suffix[1:],
            metadata={
                'source': 'local',
                'file_type': file_category,
                'language': self._detect_language(file_path),
                'path': str(file_path),
                'file_size': stat.st_size,
                'created_at': created_at,
                'updated_at': updated_at,
                'git_repo': git_info.get('repo'),
                'git_branch': git_info.get('branch'),
                'last_commit': git_info.get('last_commit'),
            },
            tags=self._generate_tags(file_category, file_path, git_info)
        )
    
    async def _process_code_file(self, file_path: Path) -> str:
        """Process code file via code-analyzer service."""
        with open(file_path) as f:
            content = f.read()
        
        # Call code-analyzer service
        analysis = await self.code_analyzer.analyze(
            content=content,
            path=str(file_path),
            language=self._detect_language(file_path)
        )
        
        # Convert analysis to markdown
        md = f"# Code Analysis: {file_path.name}\n\n"
        md += f"**Language**: {analysis['language']}\n"
        md += f"**Quality Score**: {analysis['quality_score']}/100\n\n"
        
        if analysis['functions']:
            md += "## Functions\n\n"
            for func in analysis['functions']:
                md += f"### `{func['name']}()`\n"
                md += f"{func['docstring']}\n\n"
        
        if analysis['endpoints']:
            md += "## API Endpoints\n\n"
            for endpoint in analysis['endpoints']:
                md += f"- **{endpoint['method']}** `{endpoint['path']}`\n"
        
        md += f"\n## Source Code\n\n```{analysis['language']}\n{content}\n```\n"
        
        return md
    
    async def _process_document_file(self, file_path: Path) -> str:
        """Process document file (already text-based)."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # If already markdown, return as-is
        if file_path.suffix == '.md':
            return content
        
        # Convert other formats to markdown
        if file_path.suffix == '.rst':
            return self._rst_to_markdown(content)
        elif file_path.suffix == '.txt':
            return f"```\n{content}\n```\n"
        else:
            return content
```

---

## 📦 Data Models

### Normalized Document
```python
@dataclass
class NormalizedDocument:
    """Unified document format for all sources."""
    document_id: str
    title: str
    content_md: str  # Content in markdown format
    original_format: str  # Original file extension (py, doc, jira, etc)
    
    metadata: dict = field(default_factory=dict)
    # Required metadata fields:
    # - source: github|jira|confluence|local
    # - file_type: code|document|image|data
    # - language: python|javascript|markdown|etc
    # - created_at: ISO timestamp
    # - updated_at: ISO timestamp
    # - author: string
    
    # Optional correlation fields:
    # - related_jira: List[str]  # ["PROJ-123", "PROJ-456"]
    # - related_commits: List[str]  # ["abc123", "def456"]
    # - related_prs: List[int]  # [42, 89]
    # - repo: str
    # - branch: str
    
    tags: List[str] = field(default_factory=list)
    # Format: "key:value"
    # Examples: ["source:github", "language:python", "jira:PROJ-123"]
```

---

## 🧪 Comprehensive Testing Strategy

### Test Pyramid Overview
```
                    ┌─────────────────┐
                    │  Functional (5) │  End-to-end workflows
                    │   E2E Tests     │  Full system validation
                    └─────────────────┘
                  ┌───────────────────────┐
                  │   Integration (30)    │  Service interactions
                  │   Component Tests     │  API contracts
                  └───────────────────────┘
              ┌───────────────────────────────┐
              │      Unit Tests (200+)        │  Pure functions
              │    Isolated Components        │  Business logic
              └───────────────────────────────┘
```

### Test Suite Structure
```
tests/
├── unit/                           # Fast, isolated tests
│   ├── ingestion/
│   │   ├── test_file_type_detector.py
│   │   ├── test_markdown_normalizer.py
│   │   ├── test_metadata_extractor.py
│   │   ├── test_correlation_matcher.py
│   │   ├── test_wikipedia_link_filter.py
│   │   └── test_tag_generator.py
│   ├── models/
│   │   ├── test_normalized_document.py
│   │   └── test_ingestion_result.py
│   └── utils/
│       ├── test_timestamp_parser.py
│       ├── test_url_normalizer.py
│       └── test_content_sanitizer.py
│
├── integration/                    # Service integration tests
│   ├── ingestion/
│   │   ├── test_github_api_integration.py
│   │   ├── test_wikipedia_api_integration.py
│   │   ├── test_code_analyzer_integration.py
│   │   ├── test_kafka_ingestion_integration.py
│   │   └── test_doc_store_integration.py
│   ├── services/
│   │   ├── test_mcp_provisioner_api.py
│   │   ├── test_mcp_gateway_routing.py
│   │   └── test_training_coordinator_api.py
│   └── database/
│       ├── test_redis_operations.py
│       └── test_doc_store_queries.py
│
├── functional/                     # End-to-end functional tests
│   ├── workflows/
│   │   ├── test_complete_ingestion_workflow.py
│   │   ├── test_mcp_lifecycle_workflow.py
│   │   ├── test_query_workflow.py
│   │   └── test_correlation_workflow.py
│   └── scenarios/
│       ├── test_wikipedia_crawl_scenario.py
│       ├── test_multi_source_ingestion.py
│       └── test_code_analysis_pipeline.py
│
├── e2e/                           # Full system E2E tests
│   ├── test_github_ingestion.py
│   ├── test_jira_ingestion.py
│   ├── test_confluence_ingestion.py
│   ├── test_wikipedia_crawling.py
│   ├── test_local_ingestion.py
│   ├── test_correlation_engine.py
│   └── test_end_to_end_flow.py
│
└── fixtures/                      # Shared test data
    ├── mock_commits_200.json
    ├── mock_jira_tickets.json
    ├── mock_confluence_pages.json
    ├── mock_wikipedia_pages.json
    └── test_files/
        ├── code_samples/
        ├── documents/
        └── mixed/
```

---

## 🔬 Unit Testing Strategy

### Principles
- **Fast**: < 1ms per test
- **Isolated**: No external dependencies
- **Deterministic**: Same input → same output
- **Focused**: Test one thing at a time

### Unit Test Examples

#### 1. File Type Detection
**File**: `tests/unit/ingestion/test_file_type_detector.py`

```python
import pytest
from ingestion.utils.file_type_detector import FileTypeDetector

class TestFileTypeDetector:
    """Unit tests for file type detection."""
    
    def setup_method(self):
        self.detector = FileTypeDetector()
    
    def test_detect_python_file(self):
        """Test Python file detection."""
        result = self.detector.detect('example.py')
        
        assert result.file_type == 'code'
        assert result.language == 'python'
        assert result.should_analyze_code is True
    
    def test_detect_markdown_file(self):
        """Test Markdown file detection."""
        result = self.detector.detect('README.md')
        
        assert result.file_type == 'document'
        assert result.language == 'markdown'
        assert result.should_analyze_code is False
    
    def test_detect_image_file(self):
        """Test image file detection."""
        result = self.detector.detect('diagram.png')
        
        assert result.file_type == 'image'
        assert result.language is None
        assert result.should_analyze_code is False
    
    @pytest.mark.parametrize('filename,expected_type', [
        ('main.py', 'code'),
        ('app.js', 'code'),
        ('Style.css', 'code'),
        ('Config.java', 'code'),
        ('notes.txt', 'document'),
        ('doc.pdf', 'office'),
        ('data.json', 'data'),
        ('image.jpg', 'image'),
    ])
    def test_detect_multiple_file_types(self, filename, expected_type):
        """Test detection of various file types."""
        result = self.detector.detect(filename)
        assert result.file_type == expected_type
    
    def test_detect_unknown_extension(self):
        """Test handling of unknown file extensions."""
        result = self.detector.detect('file.xyz')
        
        assert result.file_type == 'unknown'
        assert result.language is None
    
    def test_detect_no_extension(self):
        """Test handling of files without extension."""
        result = self.detector.detect('Makefile')
        
        # Should use content-based detection
        assert result.file_type in ['code', 'document', 'unknown']

#### 2. Markdown Normalization
**File**: `tests/unit/ingestion/test_markdown_normalizer.py`

```python
import pytest
from ingestion.utils.markdown_normalizer import MarkdownNormalizer

class TestMarkdownNormalizer:
    """Unit tests for markdown normalization."""
    
    def setup_method(self):
        self.normalizer = MarkdownNormalizer()
    
    def test_normalize_python_code(self):
        """Test normalization of Python code to markdown."""
        code = '''def hello():
    print("Hello, World!")'''
        
        result = self.normalizer.normalize_code(
            content=code,
            language='python',
            filename='hello.py'
        )
        
        assert '# Code: hello.py' in result
        assert '```python' in result
        assert 'def hello()' in result
        assert '```' in result
    
    def test_add_frontmatter(self):
        """Test frontmatter addition."""
        content = "# Title\n\nContent here"
        metadata = {
            'source': 'github',
            'created_at': '2024-01-01T00:00:00Z'
        }
        
        result = self.normalizer.add_frontmatter(content, metadata)
        
        assert result.startswith('---\n')
        assert 'source: github' in result
        assert 'created_at: 2024-01-01T00:00:00Z' in result
        assert '---\n\n# Title' in result
    
    def test_sanitize_content(self):
        """Test content sanitization."""
        content = "Text with <script>alert('xss')</script> here"
        
        result = self.normalizer.sanitize(content)
        
        assert '<script>' not in result
        assert 'alert' not in result
    
    def test_normalize_wikipedia_html(self):
        """Test Wikipedia HTML to markdown conversion."""
        html = '<p>This is <b>bold</b> text.</p>'
        
        result = self.normalizer.html_to_markdown(html)
        
        assert '**bold**' in result
        assert '<p>' not in result
        assert '<b>' not in result

#### 3. Correlation Matching
**File**: `tests/unit/ingestion/test_correlation_matcher.py`

```python
import pytest
from ingestion.utils.correlation_matcher import CorrelationMatcher

class TestCorrelationMatcher:
    """Unit tests for correlation matching."""
    
    def setup_method(self):
        self.matcher = CorrelationMatcher()
    
    def test_extract_jira_tickets_from_commit(self):
        """Test extracting Jira ticket IDs from commit message."""
        commit_message = "feat: Add authentication (PROJ-123, PROJ-456)"
        
        tickets = self.matcher.extract_jira_tickets(commit_message)
        
        assert len(tickets) == 2
        assert 'PROJ-123' in tickets
        assert 'PROJ-456' in tickets
    
    def test_extract_pr_number_from_commit(self):
        """Test extracting PR number from commit message."""
        commit_message = "Merge pull request #42 from feature/auth"
        
        pr_number = self.matcher.extract_pr_number(commit_message)
        
        assert pr_number == 42
    
    def test_match_commits_to_jira_ticket(self):
        """Test matching commits to Jira ticket."""
        ticket_id = 'PROJ-123'
        commits = [
            {'sha': 'abc123', 'message': 'feat: Add login (PROJ-123)'},
            {'sha': 'def456', 'message': 'fix: Bug in PROJ-123'},
            {'sha': 'ghi789', 'message': 'unrelated change'},
        ]
        
        matches = self.matcher.find_commits_for_ticket(ticket_id, commits)
        
        assert len(matches) == 2
        assert matches[0]['sha'] == 'abc123'
        assert matches[1]['sha'] == 'def456'
    
    @pytest.mark.parametrize('message,expected', [
        ('PROJ-123: fix bug', ['PROJ-123']),
        ('[PROJ-456] Add feature', ['PROJ-456']),
        ('Fix for JIRA-789', ['JIRA-789']),
        ('No tickets here', []),
        ('PROJ-1 PROJ-2 PROJ-3', ['PROJ-1', 'PROJ-2', 'PROJ-3']),
    ])
    def test_extract_jira_patterns(self, message, expected):
        """Test various Jira ticket patterns."""
        tickets = self.matcher.extract_jira_tickets(message)
        assert tickets == expected

#### 4. Timestamp Parsing
**File**: `tests/unit/utils/test_timestamp_parser.py`

```python
import pytest
from datetime import datetime
from ingestion.utils.timestamp_parser import TimestampParser

class TestTimestampParser:
    """Unit tests for timestamp parsing."""
    
    def setup_method(self):
        self.parser = TimestampParser()
    
    def test_parse_iso_format(self):
        """Test parsing ISO 8601 format."""
        timestamp_str = "2024-01-15T10:30:00Z"
        
        result = self.parser.parse(timestamp_str)
        
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_parse_unix_timestamp(self):
        """Test parsing Unix timestamp."""
        timestamp = 1705315800  # 2024-01-15 10:30:00
        
        result = self.parser.parse_unix(timestamp)
        
        assert isinstance(result, datetime)
        assert result.year == 2024
    
    def test_extract_from_git_log(self):
        """Test extracting timestamp from git log."""
        git_date = "Mon Jan 15 10:30:00 2024 +0000"
        
        result = self.parser.parse_git_date(git_date)
        
        assert result.year == 2024
        assert result.month == 1
    
    def test_handle_invalid_timestamp(self):
        """Test handling of invalid timestamp."""
        with pytest.raises(ValueError):
            self.parser.parse("not a timestamp")
    
    def test_parse_with_timezone(self):
        """Test parsing with timezone information."""
        timestamp_str = "2024-01-15T10:30:00+05:30"
        
        result = self.parser.parse(timestamp_str)
        
        assert result.year == 2024
        # Should be converted to UTC

---

## 🔗 Integration Testing Strategy

### Principles
- **Service Interactions**: Test API contracts
- **External Dependencies**: Test with real services (or good mocks)
- **Data Flow**: Verify data passes correctly between components
- **Error Handling**: Test failure scenarios

### Integration Test Examples

#### 1. GitHub API Integration
**File**: `tests/integration/ingestion/test_github_api_integration.py`

```python
import pytest
from ingestion.github_ingestor import GitHubIngestor

@pytest.mark.integration
class TestGitHubAPIIntegration:
    """Integration tests for GitHub API."""
    
    @pytest.fixture
    async def github_ingestor(self):
        """Create GitHub ingestor with test credentials."""
        return GitHubIngestor(github_token=os.getenv('GITHUB_TEST_TOKEN'))
    
    async def test_fetch_commits_from_real_repo(self, github_ingestor):
        """Test fetching real commits from GitHub."""
        commits = await github_ingestor.fetch_commits(
            repo='torvalds/linux',
            branch='master',
            limit=10
        )
        
        assert len(commits) == 10
        assert all('sha' in c for c in commits)
        assert all('message' in c for c in commits)
        assert all('author' in c for c in commits)
    
    async def test_fetch_file_content(self, github_ingestor):
        """Test fetching file content from GitHub."""
        content = await github_ingestor.fetch_file_content(
            repo='python/cpython',
            path='README.rst',
            branch='main'
        )
        
        assert content is not None
        assert len(content) > 0
        assert 'Python' in content
    
    async def test_handle_rate_limiting(self, github_ingestor):
        """Test handling of GitHub rate limits."""
        # Make many requests to trigger rate limit
        results = []
        for i in range(100):
            try:
                commits = await github_ingestor.fetch_commits(
                    repo='torvalds/linux',
                    limit=1
                )
                results.append('success')
            except RateLimitException as e:
                results.append('rate_limited')
                assert e.retry_after > 0
                break
        
        # Should handle rate limiting gracefully
        assert 'rate_limited' in results or len(results) == 100
    
    async def test_handle_404_repo_not_found(self, github_ingestor):
        """Test handling of non-existent repository."""
        with pytest.raises(RepositoryNotFoundError):
            await github_ingestor.fetch_commits(
                repo='nonexistent/repo-that-does-not-exist',
                limit=10
            )

#### 2. Code Analyzer Integration
**File**: `tests/integration/ingestion/test_code_analyzer_integration.py`

```python
import pytest
from ingestion.code_document_generator import CodeDocumentGenerator

@pytest.mark.integration
class TestCodeAnalyzerIntegration:
    """Integration tests for code-analyzer service."""
    
    @pytest.fixture
    def code_generator(self):
        """Create code generator with test service URL."""
        return CodeDocumentGenerator(
            code_analyzer_url='http://localhost:8020'
        )
    
    async def test_analyze_python_file(self, code_generator):
        """Test analyzing Python file via service."""
        python_code = '''
def calculate_sum(a, b):
    """Calculate sum of two numbers."""
    return a + b

class Calculator:
    """Simple calculator class."""
    
    def add(self, x, y):
        return x + y
'''
        
        result = await code_generator.analyze_code(
            content=python_code,
            language='python',
            filename='calculator.py'
        )
        
        assert result['quality_score'] > 0
        assert len(result['functions']) == 1  # calculate_sum
        assert len(result['classes']) == 1    # Calculator
        assert result['functions'][0]['name'] == 'calculate_sum'
    
    async def test_service_unavailable_handling(self, code_generator):
        """Test handling when code-analyzer service is down."""
        # Use invalid URL
        generator = CodeDocumentGenerator(
            code_analyzer_url='http://localhost:9999'
        )
        
        with pytest.raises(ServiceUnavailableError):
            await generator.analyze_code(
                content='print("hello")',
                language='python',
                filename='test.py'
            )
    
    async def test_analyze_large_file(self, code_generator):
        """Test analyzing large code file."""
        # Generate large file (10,000 lines)
        large_code = '\\n'.join([f'# Line {i}' for i in range(10000)])
        
        result = await code_generator.analyze_code(
            content=large_code,
            language='python',
            filename='large.py'
        )
        
        assert result is not None
        assert 'timeout' not in result

#### 3. Kafka Ingestion Integration
**File**: `tests/integration/ingestion/test_kafka_ingestion_integration.py`

```python
import pytest
from ingestion.kafka_publisher import KafkaPublisher

@pytest.mark.integration
class TestKafkaIngestionIntegration:
    """Integration tests for Kafka ingestion service."""
    
    @pytest.fixture
    async def kafka_publisher(self):
        """Create Kafka publisher for testing."""
        publisher = KafkaPublisher(
            kafka_brokers=['localhost:9092']
        )
        await publisher.connect()
        yield publisher
        await publisher.disconnect()
    
    async def test_publish_document(self, kafka_publisher):
        """Test publishing document to Kafka."""
        document = {
            'document_id': 'test-123',
            'title': 'Test Document',
            'content': 'Test content',
            'metadata': {'source': 'test'}
        }
        
        result = await kafka_publisher.publish(
            topic='document-ingestion',
            document=document
        )
        
        assert result.success is True
        assert result.offset >= 0
    
    async def test_publish_batch(self, kafka_publisher):
        """Test batch publishing of documents."""
        documents = [
            {'document_id': f'test-{i}', 'title': f'Doc {i}'}
            for i in range(100)
        ]
        
        results = await kafka_publisher.publish_batch(
            topic='document-ingestion',
            documents=documents
        )
        
        assert len(results) == 100
        assert all(r.success for r in results)

---

## ✅ Functional Testing Strategy

### Principles
- **User Workflows**: Test complete user journeys
- **Business Logic**: Verify business rules and requirements
- **Real Scenarios**: Use realistic data and conditions
- **Cross-Component**: Test multiple services working together

### Functional Test Examples

#### 1. Complete Ingestion Workflow
**File**: `tests/functional/workflows/test_complete_ingestion_workflow.py`

```python
import pytest
from datetime import datetime

@pytest.mark.functional
class TestCompleteIngestionWorkflow:
    """Functional tests for end-to-end ingestion workflow."""
    
    async def test_github_to_mcp_workflow(self):
        """Test complete workflow from GitHub ingestion to MCP training."""
        # Step 1: Ingest from GitHub
        github_ingestor = GitHubIngestor()
        documents = await github_ingestor.ingest_from_static_commits(
            'fixtures/mock_commits_200.json'
        )
        
        assert len(documents) == 200
        
        # Step 2: Normalize documents
        normalizer = DocumentNormalizer()
        normalized = [normalizer.normalize(doc) for doc in documents]
        
        assert all(doc.content_md.startswith('#') for doc in normalized)
        
        # Step 3: Publish to ingestion service
        publisher = IngestionPublisher()
        results = await publisher.publish_batch(normalized)
        
        assert all(r.success for r in results)
        
        # Step 4: Verify documents in doc_store
        doc_store = DocStoreClient()
        await asyncio.sleep(2)  # Wait for async processing
        
        stored_docs = await doc_store.search(
            query={'metadata.source': 'github'}
        )
        
        assert len(stored_docs) >= 150  # At least 75% should be stored
        
        # Step 5: Train MCP on ingested documents
        mcp_trainer = MCPTrainer()
        mcp_id = await mcp_trainer.train(
            documents=stored_docs,
            mcp_name='test-mcp'
        )
        
        assert mcp_id is not None
        
        # Step 6: Query MCP
        mcp_gateway = MCPGateway()
        response = await mcp_gateway.query(
            mcp_id=mcp_id,
            query='What commits were made?'
        )
        
        assert response.success is True
        assert len(response.answer) > 0
    
    async def test_wikipedia_crawl_and_query_workflow(self):
        """Test Wikipedia crawling to MCP querying."""
        # Step 1: Crawl Wikipedia
        wiki_ingestor = WikipediaIngestor()
        documents = await wiki_ingestor.crawl_and_ingest(
            original_page_url='https://en.wikipedia.org/wiki/Python_(programming_language)',
            max_surface_links=3,
            max_depth_distance=1
        )
        
        assert 1 <= len(documents) <= 4  # Original + 3 links
        
        # Step 2: Verify crawl structure
        report = wiki_ingestor.generate_crawl_report()
        assert report['depth_distribution'][0] == 1  # 1 original page
        assert report['depth_distribution'][1] <= 3  # Up to 3 linked pages
        
        # Step 3: Ingest to MCP
        ingestion_service = IngestionService()
        results = await ingestion_service.ingest_batch(documents)
        
        assert results['success_count'] == len(documents)
        
        # Step 4: Query about Wikipedia content
        mcp_gateway = MCPGateway()
        response = await mcp_gateway.query(
            mcp_id='test-mcp',
            query='What is Python programming language?'
        )
        
        assert 'Python' in response.answer
        assert response.confidence > 0.5

#### 2. Multi-Source Correlation Workflow
**File**: `tests/functional/workflows/test_correlation_workflow.py`

```python
@pytest.mark.functional
class TestCorrelationWorkflow:
    """Functional tests for cross-source correlation."""
    
    async def test_commit_to_jira_correlation(self):
        """Test correlating Git commits with Jira tickets."""
        # Step 1: Generate mock commits
        mock_gen = MockDataGenerator()
        commits = await mock_gen.generate_commit_history(
            repo='test/repo',
            count=50
        )
        
        # Step 2: Generate Jira tickets from commits
        jira_tickets = await mock_gen.generate_jira_tickets_from_commits(
            commits=commits
        )
        
        # Step 3: Verify correlations
        for ticket in jira_tickets:
            assert 'related_commits' in ticket
            assert len(ticket['related_commits']) > 0
            
            # Verify commits exist
            for commit_sha in ticket['related_commits']:
                matching_commit = next(
                    (c for c in commits if c['sha'] == commit_sha),
                    None
                )
                assert matching_commit is not None
        
        # Step 4: Ingest both and verify tagging
        github_ingestor = GitHubIngestor()
        jira_ingestor = JiraIngestor()
        
        github_docs = await github_ingestor.normalize_commits(commits)
        jira_docs = await jira_ingestor.normalize_tickets(jira_tickets)
        
        # Verify bidirectional correlation in tags
        for jira_doc in jira_docs:
            related_commits = jira_doc.metadata['related_commits']
            for commit_sha in related_commits:
                # Find corresponding GitHub doc
                github_doc = next(
                    (d for d in github_docs if commit_sha in d.document_id),
                    None
                )
                if github_doc:
                    # Verify commit doc references Jira ticket
                    assert any(
                        jira_doc.metadata['ticket_id'] in tag
                        for tag in github_doc.tags
                    )
```

---

## 📊 Test Coverage Requirements

### Coverage Targets
```
Unit Tests:        90%+ coverage
Integration Tests: 80%+ coverage
Functional Tests:  100% critical paths
E2E Tests:        100% user workflows
```

### Coverage by Component
| Component | Unit | Integration | Functional | E2E |
|-----------|------|-------------|------------|-----|
| File Type Detection | ✅ 95% | ✅ 85% | N/A | N/A |
| GitHub Ingestion | ✅ 90% | ✅ 80% | ✅ 100% | ✅ 100% |
| Wikipedia Crawler | ✅ 92% | ✅ 75% | ✅ 100% | ✅ 100% |
| Jira Ingestion | ✅ 88% | ✅ 80% | ✅ 100% | ✅ 100% |
| Correlation Engine | ✅ 95% | ✅ 90% | ✅ 100% | N/A |
| MCP Provisioner | ✅ 85% | ✅ 80% | ✅ 100% | ✅ 100% |
| MCP Gateway | ✅ 90% | ✅ 85% | ✅ 100% | ✅ 100% |

---

## 🎯 Test Execution Strategy

### Test Running Commands
```bash
# Run all tests
pytest

# Run by type
pytest tests/unit/                    # Fast: ~2 seconds
pytest tests/integration/             # Medium: ~30 seconds
pytest tests/functional/              # Slow: ~2 minutes
pytest tests/e2e/                     # Slowest: ~5 minutes

# Run with coverage
pytest --cov=ingestion --cov-report=html

# Run specific markers
pytest -m unit                        # Only unit tests
pytest -m integration                 # Only integration tests
pytest -m functional                  # Only functional tests
pytest -m "not slow"                  # Skip slow tests

# Parallel execution
pytest -n auto                        # Use all CPU cores

# Watch mode for TDD
pytest-watch
```

### CI/CD Pipeline
```yaml
# .github/workflows/tests.yml
name: Test Suite

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run unit tests
        run: pytest tests/unit/ -v --cov
      - name: Upload coverage
        uses: codecov/codecov-action@v2
  
  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
      kafka:
        image: confluentinc/cp-kafka:latest
    steps:
      - name: Run integration tests
        run: pytest tests/integration/ -v
  
  functional-tests:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]
    steps:
      - name: Start all services
        run: docker-compose up -d
      - name: Run functional tests
        run: pytest tests/functional/ -v
  
  e2e-tests:
    runs-on: ubuntu-latest
    needs: functional-tests
    steps:
      - name: Run E2E tests
        run: pytest tests/e2e/ -v --maxfail=1
```

### Wikipedia Crawling Tests
```python
# tests/e2e/ingestion/test_wikipedia_crawling.py

@pytest.mark.e2e
async def test_wikipedia_single_page():
    """Test crawling single Wikipedia page (depth=0)."""
    ingestor = WikipediaIngestor()
    
    docs = await ingestor.crawl_and_ingest(
        original_page_url="https://en.wikipedia.org/wiki/Python_(programming_language)",
        max_surface_links=0,
        max_depth_distance=0
    )
    
    assert len(docs) == 1
    assert docs[0].metadata['source'] == 'wikipedia'
    assert docs[0].metadata['crawl_depth'] == 0
    assert docs[0].original_format == 'wikipedia'
    assert 'Python' in docs[0].title

@pytest.mark.e2e
async def test_wikipedia_surface_links():
    """Test crawling with surface links (depth=1)."""
    ingestor = WikipediaIngestor()
    
    docs = await ingestor.crawl_and_ingest(
        original_page_url="https://en.wikipedia.org/wiki/Machine_learning",
        max_surface_links=5,
        max_depth_distance=1
    )
    
    # Should have original + up to 5 linked pages
    assert 1 <= len(docs) <= 6
    
    # Check depth distribution
    depth_0 = [d for d in docs if d.metadata['crawl_depth'] == 0]
    depth_1 = [d for d in docs if d.metadata['crawl_depth'] == 1]
    
    assert len(depth_0) == 1  # Original page
    assert len(depth_1) <= 5  # Up to 5 linked pages

@pytest.mark.e2e
async def test_wikipedia_deep_crawl():
    """Test deep crawling (depth=2)."""
    ingestor = WikipediaIngestor()
    
    docs = await ingestor.crawl_and_ingest(
        original_page_url="https://en.wikipedia.org/wiki/Artificial_intelligence",
        max_surface_links=3,
        max_depth_distance=2
    )
    
    # Should have:
    # Depth 0: 1 page
    # Depth 1: up to 3 pages
    # Depth 2: up to 3*3 = 9 pages
    # Total: 1 + 3 + 9 = up to 13 pages
    assert 1 <= len(docs) <= 13
    
    # Verify depth distribution
    report = ingestor.generate_crawl_report()
    assert 'depth_distribution' in report
    assert report['depth_distribution'].get(0, 0) == 1

@pytest.mark.e2e
async def test_wikipedia_crawl_graph():
    """Test crawl graph generation."""
    ingestor = WikipediaIngestor()
    
    await ingestor.crawl_and_ingest(
        original_page_url="https://en.wikipedia.org/wiki/Deep_learning",
        max_surface_links=2,
        max_depth_distance=1
    )
    
    report = ingestor.generate_crawl_report()
    
    assert 'crawl_graph' in report
    assert 'total_pages' in report
    assert 'link_statistics' in report
    
    # Verify graph structure
    graph = report['crawl_graph']
    assert 'Deep learning' in graph
    assert graph['Deep learning']['depth'] == 0
    assert graph['Deep learning']['parent'] is None
    assert len(graph['Deep learning']['children']) <= 2

@pytest.mark.e2e
async def test_wikipedia_no_duplicate_pages():
    """Test that pages are not crawled twice."""
    ingestor = WikipediaIngestor()
    
    docs = await ingestor.crawl_and_ingest(
        original_page_url="https://en.wikipedia.org/wiki/Neural_network",
        max_surface_links=10,
        max_depth_distance=2
    )
    
    # Check for unique document IDs
    doc_ids = [d.document_id for d in docs]
    assert len(doc_ids) == len(set(doc_ids))
    
    # Check for unique URLs
    urls = [d.metadata['url'] for d in docs]
    assert len(urls) == len(set(urls))

@pytest.mark.e2e
async def test_wikipedia_markdown_normalization():
    """Test that Wikipedia content is properly normalized to markdown."""
    ingestor = WikipediaIngestor()
    
    docs = await ingestor.crawl_and_ingest(
        original_page_url="https://en.wikipedia.org/wiki/FastAPI",
        max_surface_links=0,
        max_depth_distance=0
    )
    
    doc = docs[0]
    
    # Check markdown structure
    assert doc.content_md.startswith('#')
    assert '**Source**: Wikipedia' in doc.content_md
    assert '**URL**:' in doc.content_md
    assert '## Content' in doc.content_md
    
    # Check metadata
    assert 'wikipedia' in doc.metadata['url']
    assert doc.metadata['file_type'] == 'document'
    assert doc.metadata['crawl_depth'] == 0

@pytest.mark.e2e  
async def test_wikipedia_with_mock_data():
    """Test Wikipedia ingestion with pre-saved mock data."""
    # For faster testing, use pre-saved Wikipedia content
    with open('fixtures/mock_wikipedia_pages.json') as f:
        mock_pages = json.load(f)
    
    ingestor = WikipediaIngestor()
    # ... test with mock data instead of live API calls
```

### Mock Data Generation
```python
# In mock-data-generator service
class MockDataGenerator:
    """Generate realistic mock data for testing."""
    
    async def generate_commit_history(
        self,
        repo: str,
        count: int = 200,
        start_date: str = "2024-01-01"
    ) -> List[dict]:
        """Generate 200 believable commits with realistic messages."""
        commits = []
        
        features = [
            "user authentication", "API rate limiting",
            "database migration", "UI redesign",
            "performance optimization", "bug fixes"
        ]
        
        for i in range(count):
            feature = random.choice(features)
            commit = {
                "sha": hashlib.sha1(f"{repo}{i}".encode()).hexdigest(),
                "message": self._generate_commit_message(feature, i),
                "author": random.choice(["Alice", "Bob", "Carol"]),
                "date": (datetime.fromisoformat(start_date) + timedelta(days=i)).isoformat(),
                "repo": repo,
                "branch": "main" if i % 10 != 0 else "feature/new-feature",
                "files_changed": random.randint(1, 10),
                "pr_number": i // 5 if i % 5 == 0 else None,
            }
            commits.append(commit)
        
        # Save to static JSON
        with open(f"fixtures/mock_commits_{repo.replace('/', '_')}.json", 'w') as f:
            json.dump(commits, f, indent=2)
        
        return commits
    
    async def generate_jira_tickets_from_commits(
        self,
        commits: List[dict]
    ) -> List[dict]:
        """Generate Jira tickets correlated with commits."""
        # Group commits by feature (using commit message patterns)
        features = defaultdict(list)
        for commit in commits:
            feature = self._extract_feature(commit['message'])
            features[feature].append(commit)
        
        tickets = []
        for feature_name, feature_commits in features.items():
            ticket_id = f"PROJ-{len(tickets) + 100}"
            
            ticket = {
                "ticket_id": ticket_id,
                "title": f"Implement {feature_name}",
                "description": self._generate_ticket_description(feature_commits),
                "type": "Story",
                "status": "Done",
                "priority": "High",
                "reporter": feature_commits[0]['author'],
                "created_at": feature_commits[-1]['date'],
                "updated_at": feature_commits[0]['date'],
                "related_commits": [c['sha'] for c in feature_commits],
                "related_repos": list(set(c['repo'] for c in feature_commits)),
            }
            tickets.append(ticket)
        
        return tickets
```

### E2E Test Example
```python
# tests/e2e/ingestion/test_end_to_end_flow.py

@pytest.mark.e2e
async def test_complete_ingestion_flow():
    """Test complete flow from multiple sources to MCP training."""
    
    # 1. Generate mock data
    mock_gen = MockDataGenerator()
    commits = await mock_gen.generate_commit_history("test/repo", count=200)
    jira_tickets = await mock_gen.generate_jira_tickets_from_commits(commits)
    
    # 2. Ingest from GitHub
    github_ingestor = GitHubIngestor()
    github_docs = await github_ingestor.ingest_from_static_commits(
        "fixtures/mock_commits_test_repo.json"
    )
    assert len(github_docs) > 0
    
    # 3. Ingest Jira tickets
    jira_ingestor = JiraIngestor()
    jira_docs = await jira_ingestor.ingest_tickets(jira_tickets)
    assert len(jira_docs) > 0
    
    # 4. Verify correlations
    for jira_doc in jira_docs:
        assert 'related_commits' in jira_doc.metadata
        assert len(jira_doc.metadata['related_commits']) > 0
        
        # Check that related commits exist in GitHub docs
        commit_shas = jira_doc.metadata['related_commits']
        for sha in commit_shas:
            matching_docs = [
                d for d in github_docs 
                if sha in d.metadata.get('related_commits', [])
            ]
            assert len(matching_docs) > 0
    
    # 5. Verify all documents normalized to markdown
    all_docs = github_docs + jira_docs
    for doc in all_docs:
        assert doc.content_md.startswith('#') or doc.content_md.startswith('---')
        assert doc.original_format in ['py', 'js', 'md', 'jira', 'confluence']
    
    # 6. Verify tagging
    for doc in all_docs:
        assert any(tag.startswith('source:') for tag in doc.tags)
        assert any(tag.startswith('file_type:') for tag in doc.tags)
    
    # 7. Ingest to MCP
    ingestion_service = IngestionService()
    results = await ingestion_service.ingest_batch(all_docs)
    assert results['success_count'] == len(all_docs)
```

---

## 🎬 Demo Script Integration

### Enhanced Demo with All Sources
```python
# In demo_mcp_lifecycle.py

class MCPLifecycleDemo:
    
    async def run_complete_demo(self):
        """Run demo with all ingestion sources."""
        
        # Phase 1: Generate Mock Data
        await self.generate_mock_data()
        
        # Phase 2: Multi-Source Ingestion
        await self.ingest_from_github()
        await self.ingest_from_jira()
        await self.ingest_from_confluence()
        await self.ingest_from_local_files()
        
        # Phase 3: Verify Correlations
        await self.verify_correlations()
        
        # Phase 4: MCP Training
        await self.train_mcp_with_correlated_data()
        
        # Phase 5: Query with Context
        await self.query_with_correlations()
    
    async def generate_mock_data(self):
        """Generate mock data for demo."""
        self.print_header("MOCK DATA GENERATION")
        
        # Generate 200 commits
        response = await self.client.post(
            f"{self.services['mock-data-generator']}/api/v1/generate/commits",
            json={
                "repo": "hackathon/demo-repo",
                "count": 200,
                "start_date": "2024-01-01",
                "save_to_file": True,
                "filename": "mock_commits_200.json"
            }
        )
        
        self.commits = response.json()['commits']
        self.print_success(f"Generated {len(self.commits)} mock commits")
        self.print_info(f"Saved to: data/mock_commits_200.json")
        
        # Generate Jira tickets from commits
        response = await self.client.post(
            f"{self.services['mock-data-generator']}/api/v1/generate/jira-tickets",
            json={
                "commits": self.commits,
                "project_key": "DEMO"
            }
        )
        
        self.jira_tickets = response.json()['tickets']
        self.print_success(f"Generated {len(self.jira_tickets)} Jira tickets")
        
        # Show correlation example
        example_ticket = self.jira_tickets[0]
        self.print_info(f"Example: {example_ticket['ticket_id']} linked to {len(example_ticket['related_commits'])} commits")
    
    async def ingest_from_github(self):
        """Ingest from static commits JSON."""
        self.print_header("GITHUB INGESTION (Static Commits)")
        
        # Load static commits
        with open("data/mock_commits_200.json") as f:
            commits = json.load(f)
        
        # Process each commit as a document
        for i, commit in enumerate(commits, 1):
            print(f"  [{i}/200] {commit['sha'][:8]}: {commit['message'][:50]}...", end=" ", flush=True)
            
            # Create document from commit
            doc = {
                "document_id": f"commit-{commit['sha'][:8]}",
                "title": f"Commit: {commit['message'].split('\\n')[0][:100]}",
                "content": self._format_commit_as_markdown(commit),
                "metadata": {
                    "source": "github",
                    "file_type": "document",
                    "type": "commit",
                    "sha": commit['sha'],
                    "author": commit['author'],
                    "repo": commit['repo'],
                    "branch": commit['branch'],
                    "pr_number": commit.get('pr_number'),
                    "created_at": commit['date'],
                    "updated_at": commit['date'],
                }
            }
            
            # Ingest
            await self.ingest_single_document(doc)
            print(f"{Colors.OKGREEN}✓{Colors.ENDC}")
            
            if i % 50 == 0:
                self.print_info(f"Progress: {i}/200 commits ingested")
        
        self.print_success(f"Ingested all 200 commits")
    
    async def ingest_from_jira(self):
        """Ingest Jira tickets correlated with commits."""
        self.print_header("JIRA INGESTION (Correlated Tickets)")
        
        for i, ticket in enumerate(self.jira_tickets, 1):
            print(f"  [{i}/{len(self.jira_tickets)}] {ticket['ticket_id']}: {ticket['title'][:50]}...", end=" ", flush=True)
            
            # Create document from ticket
            doc = {
                "document_id": f"jira-{ticket['ticket_id']}",
                "title": f"{ticket['ticket_id']}: {ticket['title']}",
                "content": ticket['description'],  # Already in markdown
                "metadata": {
                    "source": "jira",
                    "file_type": "document",
                    "ticket_id": ticket['ticket_id'],
                    "type": ticket['type'],
                    "status": ticket['status'],
                    "related_commits": ticket['related_commits'],  # Correlation!
                    "related_repos": ticket['related_repos'],
                    "created_at": ticket['created_at'],
                    "updated_at": ticket['updated_at'],
                }
            }
            
            # Ingest
            await self.ingest_single_document(doc)
            print(f"{Colors.OKGREEN}✓{Colors.ENDC} (linked to {len(ticket['related_commits'])} commits)")
        
        self.print_success(f"Ingested {len(self.jira_tickets)} Jira tickets with commit correlations")
```

---

## 📝 Static Commits JSON Format

```json
{
  "repo": "hackathon/demo-repo",
  "branch": "main",
  "generated_at": "2025-10-08T04:00:00Z",
  "commit_count": 200,
  "commits": [
    {
      "sha": "abc123def456...",
      "message": "feat: Add user authentication\n\nImplement JWT-based authentication with refresh tokens.\nRelated to PROJ-101",
      "author": {
        "name": "Alice Developer",
        "email": "alice@example.com"
      },
      "date": "2024-01-15T10:30:00Z",
      "repo": "hackathon/demo-repo",
      "branch": "main",
      "pr_number": 42,
      "files_changed": 5,
      "insertions": 234,
      "deletions": 12,
      "jira_tickets": ["PROJ-101"],
      "tags": ["feature", "authentication"]
    }
  ]
}
```

---

## 🎯 Success Criteria

### Functional Requirements
- [x] GitHub ingestion working
- [ ] Jira ingestion with commit correlation
- [ ] Confluence ingestion with Jira references
- [x] Wikipedia crawling with configurable depth
  - [x] Single page ingestion
  - [x] Surface links crawling (depth=1)
  - [x] Deep crawling (depth=2+)
  - [x] Crawl graph generation
  - [x] Link relationship tracking
- [ ] **Horus Heresy Use Case** (Real-world demonstration)
  - [ ] Adapt crawler for Fandom wikis
  - [ ] Deep crawl (depth=50, links=50)
  - [ ] Create second specialized MCP
  - [ ] Train on 500-1,000 wiki pages
  - [ ] Generate 12-document suite
  - [ ] Multi-MCP demo integration
- [ ] Local directory ingestion with file type detection
- [ ] All files normalized to .md format
- [ ] Original format preserved in metadata
- [ ] Code files analyzed via code-analyzer service
- [ ] 200 static commits saved to JSON
- [ ] Correlations tracked in tags/metadata

### Testing Requirements

#### Unit Tests (200+ tests)
- [ ] File type detection unit tests
  - [ ] Python, JavaScript, Java file detection
  - [ ] Document file detection (md, txt, pdf)
  - [ ] Image file detection
  - [ ] Unknown file handling
  - [ ] Parameterized tests for all extensions
- [ ] Markdown normalization unit tests
  - [ ] Code to markdown conversion
  - [ ] Frontmatter addition
  - [ ] Content sanitization
  - [ ] HTML to markdown conversion
- [ ] Correlation matching unit tests
  - [ ] Jira ticket extraction
  - [ ] PR number extraction
  - [ ] Commit-to-ticket matching
  - [ ] Regex pattern testing
- [ ] Timestamp parsing unit tests
  - [ ] ISO 8601 parsing
  - [ ] Unix timestamp parsing
  - [ ] Git date parsing
  - [ ] Timezone handling
- [ ] Tag generation unit tests
- [ ] URL normalization unit tests
- [ ] Content sanitization unit tests

#### Integration Tests (30+ tests)
- [ ] GitHub API integration tests
  - [ ] Real commit fetching
  - [ ] File content retrieval
  - [ ] Rate limit handling
  - [ ] Error handling (404, 403, etc.)
- [ ] Wikipedia API integration tests
  - [ ] Page content fetching
  - [ ] Link extraction
  - [ ] API error handling
- [ ] Code analyzer service integration
  - [ ] Python code analysis
  - [ ] JavaScript code analysis
  - [ ] Service unavailable handling
  - [ ] Large file handling
- [ ] Kafka ingestion integration
  - [ ] Single document publishing
  - [ ] Batch publishing
  - [ ] Consumer verification
- [ ] Doc store integration
  - [ ] Document storage
  - [ ] Search queries
  - [ ] Metadata indexing
- [ ] MCP provisioner API integration
  - [ ] Container deployment
  - [ ] Health check verification
  - [ ] State transitions
- [ ] MCP gateway routing integration
  - [ ] Query routing
  - [ ] Load balancing
  - [ ] Fallback handling

#### Functional Tests (15+ tests)
- [ ] Complete ingestion workflows
  - [ ] GitHub → MCP workflow
  - [ ] Wikipedia → MCP workflow
  - [ ] Jira → MCP workflow
  - [ ] Multi-source workflow
- [ ] Correlation workflows
  - [ ] Commit-to-Jira correlation
  - [ ] PR-to-commit correlation
  - [ ] Cross-source correlation
- [ ] MCP lifecycle workflow
  - [ ] Provision → Train → Query
  - [ ] State transitions
  - [ ] Error recovery
- [ ] Query workflows
  - [ ] Simple queries
  - [ ] Complex queries with context
  - [ ] Correlation-aware queries

#### E2E Tests (10+ tests)
- [ ] GitHub ingestion E2E
- [ ] Jira ingestion E2E
- [ ] Confluence ingestion E2E
- [ ] Wikipedia crawling E2E (depth 0, 1, 2)
- [ ] Local files ingestion E2E
- [ ] Correlation engine E2E
- [ ] Complete system E2E
- [ ] Wikipedia-specific E2E:
  - [ ] No duplicate page crawling
  - [ ] Depth limit enforcement
  - [ ] Surface link limit enforcement
  - [ ] Markdown normalization

#### Test Infrastructure
- [ ] Mock data generator fixtures
- [ ] Shared test utilities
- [ ] Test database setup/teardown
- [ ] Docker compose for test services
- [ ] CI/CD pipeline configuration
- [ ] Coverage reporting setup
- [ ] Performance benchmarking

### Demo Integration
- [ ] All ingestion methods in demo script
  - [ ] GitHub (static commits)
  - [ ] Jira (correlated tickets)
  - [ ] Confluence pages
  - [ ] Wikipedia crawling (3+ topics)
  - [ ] Local files
- [ ] Mock data generation phase
- [ ] Correlation verification phase
- [ ] Wikipedia crawl visualization
- [ ] Visual progress indicators
- [ ] Crawl statistics reporting

---

## 📈 Next Implementation Steps

1. **Create ingestion modules** (github, jira, confluence, wikipedia, local)
2. **Implement file type detection**
3. **Build normalization pipeline**
4. **Create correlation engine**
5. **Implement Wikipedia crawler**
   - Single page fetching
   - Link extraction and filtering
   - Recursive crawling with depth limit
   - Crawl graph generation
6. **Extend mock-data-generator** service
7. **Write E2E tests** (including Wikipedia tests)
8. **Integrate into demo script**
9. **Generate 200 static commits**
10. **Validate correlations**
11. **Test complete flow with Wikipedia**

**Estimated Time**: 8-10 hours for complete implementation (including Wikipedia)

**Priority Order**:
1. File type detection & normalization (1-2 hours)
2. GitHub static commits (200) (1 hour)
3. Wikipedia crawler implementation (2-3 hours)
4. Jira correlation (1-2 hours)
5. Demo integration with Wikipedia (1 hour)
6. E2E testing (2 hours)
7. Confluence & local files (2 hours)

### Wikipedia Crawler Complexity

**Simple** (Depth 0): 30 minutes
- Single page fetch
- Markdown conversion
- Basic metadata

**Medium** (Depth 1): 1-2 hours
- Link extraction
- Surface link crawling
- Rate limiting

**Advanced** (Depth 2+): 2-3 hours
- Recursive crawling
- Depth tracking
- Crawl graph generation
- Parent-child relationships
- Duplicate prevention

---

**Status**: Comprehensive plan ready for implementation ✅

---

## 🎮 Horus Heresy Use Case Implementation

### Create Specialized MCP for Warhammer 40K Lore

```python
async def create_horus_heresy_mcp(self):
    """Create and train a specialized MCP for Horus Heresy lore."""
    self.print_header("HORUS HERESY KNOWLEDGE BASE MCP")
    
    # Full implementation available in HORUS_HERESY_MCP_PLAN.md
    # See lines 2150+ for complete code
    
    # Key steps:
    # 1. Provision tier-2 MCP (4GB RAM, 2x CPU)
    # 2. Deep crawl Fandom wiki (depth=50, links=50)
    # 3. Ingest 500-1,000 pages
    # 4. Train MCP on comprehensive lore
    # 5. Return MCP ID for documentation generation
    
    pass

async def generate_horus_heresy_docs(self, mcp_id: str):
    """Generate 12-document suite from Horus Heresy MCP."""
    
    # Document topics:
    doc_topics = [
        "01_HORUS_HERESY_OVERVIEW.md",
        "02_THE_EMPEROR_AND_PRIMARCHS.md",
        "03_CAUSES_OF_THE_HERESY.md",
        "04_TRAITOR_LEGIONS.md",
        "05_LOYALIST_LEGIONS.md",
        "06_MAJOR_BATTLES.md",
        "07_SIEGE_OF_TERRA.md",
        "08_CHAOS_GODS_ROLE.md",
        "09_KEY_CHARACTERS.md",
        "10_AFTERMATH_AND_LEGACY.md",
        "11_TIMELINE.md",
        "12_NOTABLE_QUOTES.md",
    ]
    
    # Generate comprehensive documentation
    # Each document 2,000-5,000 words
    # Total suite: 25,000-60,000 words
    
    pass
```

### Integration with Demo

```python
async def run_complete_demo(self):
    """Run demo with both primary and specialized MCPs."""
    
    # Phases 1-5: Primary MCP workflow
    # ... (existing implementation)
    
    # Phase 6: Create Horus Heresy MCP
    self.print_header("PHASE 6: SPECIALIZED KNOWLEDGE BASE")
    mcp_id_horus = await self.create_horus_heresy_mcp()
    
    # Phase 7: Generate Documentation Suite
    self.print_header("PHASE 7: DOCUMENTATION GENERATION")
    await self.generate_horus_heresy_docs(mcp_id_horus)
    
    # Phase 8: Multi-MCP Demonstration
    self.print_header("PHASE 8: MULTI-MCP QUERIES")
    await self.demo_multi_mcp_queries(
        primary_mcp_id=self.results['mcp_id'],
        horus_mcp_id=mcp_id_horus
    )
```

### Expected Output

```
reports/mcp_lifecycle_report_20251008_HHMMSS/
├── phase6_horus_heresy_mcp/
│   ├── crawl_report.json              (500-1,000 pages)
│   ├── crawl_graph.json               (page relationships)
│   └── training_metrics.json          (MCP stats)
├── horus_heresy_docs/
│   ├── README.md                      (Index & overview)
│   ├── 01_HORUS_HERESY_OVERVIEW.md   (5,000 words)
│   ├── 02_THE_EMPEROR_AND_PRIMARCHS.md
│   ├── 03_CAUSES_OF_THE_HERESY.md
│   ├── ... (9 more documents)
│   └── 12_NOTABLE_QUOTES.md
└── multi_mcp_comparison.json          (Query results from both MCPs)
```

---

**Full implementation details**: See `HORUS_HERESY_MCP_PLAN.md` (500+ lines)


---

## 🧠 Intelligent Corpus-Based Tagging

### Preprocessing for Contextual Tags

**Problem**: Generic tags don't capture domain-specific context  
**Solution**: Analyze sample documents to extract semantic information

```python
from ingestion.corpus_analyzer import CorpusAnalyzer, PreprocessingConfig

# Configure preprocessing
config = PreprocessingConfig(
    sample_size=50,              # Analyze first 50 documents
    sample_strategy="even",      # Sample evenly across corpus
    min_entity_frequency=5,      # Entity must appear 5+ times
    top_n_entities=200,          # Track top 200 per type
    enable_relationships=True,   # Extract entity relationships
    build_knowledge_graph=True   # Build semantic graph
)

# Enhanced ingestor with preprocessing
ingestor = EnhancedWikipediaIngestor(enable_preprocessing=True)

# Crawl with intelligent tagging
documents, analysis = await ingestor.crawl_and_ingest_with_tagging(
    original_page_url="https://warhammer40k.fandom.com/wiki/Horus_Heresy",
    max_surface_links=50,
    max_depth_distance=50,
    preprocessing_sample_size=50  # Analyze first 50 pages
)
```

### Analysis Output

```python
# Corpus analysis results
analysis = CorpusAnalysis(
    documents_analyzed=50,
    unique_entities=350,
    entities_by_type={
        "PERSON": [("Horus", 145), ("Emperor", 98), ...],
        "ORG": [("Luna Wolves", 89), ("Sons of Horus", 76), ...],
        "GPE": [("Terra", 234), ("Isstvan III", 87), ...],
        "EVENT": [("Siege of Terra", 123), ...]
    },
    suggested_tags=[
        "character:horus",
        "character:emperor-of-mankind",
        "faction:luna-wolves",
        "location:terra",
        "event:siege-of-terra",
        # ... 195 more
    ],
    relationships=[
        {"from": "Horus", "to": "Emperor", "type": "betrayed"},
        {"from": "Luna Wolves", "to": "Sons of Horus", "type": "renamed_to"},
        # ... 1,998 more
    ],
    knowledge_graph=<NetworkX DiGraph: 350 nodes, 1,247 edges>
)
```

### Enhanced Document Tags

**Before preprocessing**:
```json
{
  "tags": ["source:wikipedia", "file_type:document", "depth:1"]
}
```

**After preprocessing**:
```json
{
  "tags": [
    "source:wikipedia",
    "domain:warhammer-40k",
    "topic:horus-heresy",
    "character:horus-lupercal",
    "character:sanguinius",
    "faction:sons-of-horus",
    "faction:blood-angels",
    "location:terra",
    "event:siege-of-terra",
    "entity-type:primarch"
  ],
  "metadata": {
    "graph_entities": ["Horus", "Sanguinius", "Terra"],
    "entity_count": 3,
    "avg_entity_centrality": 12.3,
    "related_entities": ["Emperor", "Abaddon", "Isstvan III"]
  }
}
```

### Knowledge Graph Visualization

```
         ┌──────────────┐
         │   Emperor    │
         └──────┬───────┘
                │ betrayed_by
                ▼
         ┌──────────────┐
         │    Horus     │◄──── leads
         └──────┬───────┘      │
                │              │
         renamed │      ┌───────────────┐
                │      │ Traitor       │
                ▼      │ Legions       │
       ┌─────────────┐ └───────────────┘
       │Sons of Horus│
       └─────────────┘
                │
                │ attacks
                ▼
       ┌─────────────┐
       │    Terra    │
       └─────────────┘
```

### Workflow

```
1. Crawl Documents (500-1,000 pages)
         ↓
2. Sample for Analysis (50 pages)
         ↓
3. Extract Entities (NER + noun phrases)
         ↓
4. Analyze Relationships (co-occurrence)
         ↓
5. Build Knowledge Graph (NetworkX)
         ↓
6. Generate Contextual Tags
         ↓
7. Apply Tags to All Documents
         ↓
8. Enhance with Graph Metrics
         ↓
9. Ingest Tagged Documents
```

---

**Full implementation**: See `INTELLIGENT_TAGGING_PLAN.md`


---

## 🌐 Universal Intelligent Tagging (All Sources)

### Overview

**Scope**: ALL ingestion methods (GitHub, Jira, Confluence, Wikipedia, Local Files)  
**Strategy**: Enrich tags, never overwrite  
**Types**: Default + Contextual + User-Defined

### Three-Layer Tagging System

```
Layer 1: Default Tags (Always Present)
├── source:*           (github, jira, wikipedia, etc.)
├── file_type:*        (code, document, ticket, etc.)
├── language:*         (python, markdown, etc.)
└── timestamps         (created_at, updated_at)

Layer 2: Contextual Tags (From Corpus Analysis)
├── Entities           (character:*, faction:*, author:*)
├── Topics             (topic:*, module:*, story:*)
├── Relationships      (graph metrics)
└── Domain-specific    (Source-dependent prefixes)

Layer 3: User-Defined Tags (Manual)
├── priority:*         (high, medium, low)
├── team:*             (backend, frontend, etc.)
├── sprint:*           (sprint-23, etc.)
└── custom:*           (Any user-defined tags)
```

### Tag Enrichment Process

```python
# Example: GitHub document with all 3 layers

# Initial (from ingestor)
tags = ["source:github", "file_type:code", "language:python"]

# After corpus analysis (+contextual)
tags += ["author:john-doe", "topic:authentication", "module:auth-service"]

# After user tags (+user-defined)
tags += ["priority:high", "team:backend", "sprint:23"]

# Final enriched tag set
tags = [
    "source:github",           # Layer 1: Default
    "file_type:code",          # Layer 1: Default
    "language:python",         # Layer 1: Default
    "author:john-doe",         # Layer 2: Contextual
    "topic:authentication",    # Layer 2: Contextual  
    "module:auth-service",     # Layer 2: Contextual
    "priority:high",           # Layer 3: User-defined
    "team:backend",            # Layer 3: User-defined
    "sprint:23"                # Layer 3: User-defined
]
```

### MCP Tag Metadata

Each trained MCP stores complete tag information:

```json
{
  "mcp_id": "mcp_abc123",
  "tag_metadata": {
    "tag_collection": {
      "total_tags": 347,
      "breakdown": {
        "default": 12,
        "contextual": 287,
        "user_defined": 48
      },
      "default_tags": [
        "source:github",
        "source:jira",
        "file_type:code",
        "file_type:document"
      ],
      "contextual_tags": [
        "author:john-doe",
        "topic:authentication",
        "character:horus",
        "faction:luna-wolves"
      ],
      "user_defined_tags": [
        "priority:high",
        "team:backend",
        "sprint:23",
        "release:v2.0"
      ]
    },
    "corpus_analysis": {
      "documents_analyzed": 50,
      "unique_entities": 350,
      "relationships_found": 1247,
      "graph_nodes": 350,
      "graph_edges": 1247
    },
    "tag_categories": {
      "source": ["source:github", "source:jira", ...],
      "author": ["author:john-doe", "author:jane-smith", ...],
      "topic": ["topic:authentication", "topic:api-design", ...],
      "priority": ["priority:high", "priority:medium", ...],
      "team": ["team:backend", "team:frontend", ...]
    }
  }
}
```

### Usage Example

```python
# Configure universal tagging
config = UniversalTaggingConfig(
    enable_preprocessing=True,
    preprocessing_config=PreprocessingConfig(sample_size=50),
    enable_user_tags=True,
    user_tags=["demo:true", "environment:prod", "iteration:v11"]
)

# Apply to any ingestion source
tagging_manager = UniversalTaggingManager(CorpusAnalyzer())

# GitHub
github_docs, github_tags = await tagging_manager.tag_documents(
    documents=github_docs,
    source_type='github',
    preprocessing_config=config.preprocessing_config,
    user_tags=config.user_tags
)

# Jira
jira_docs, jira_tags = await tagging_manager.tag_documents(
    documents=jira_docs,
    source_type='jira',
    preprocessing_config=config.preprocessing_config,
    user_tags=config.user_tags
)

# Wikipedia (Horus Heresy)
horus_docs, horus_tags = await tagging_manager.tag_documents(
    documents=horus_docs,
    source_type='wikipedia',
    preprocessing_config=config.preprocessing_config,
    user_tags=config.user_tags + ["domain:warhammer-40k"]
)
```

---

**Full implementation**: See `UNIVERSAL_TAGGING_STRATEGY.md` (800+ lines)

