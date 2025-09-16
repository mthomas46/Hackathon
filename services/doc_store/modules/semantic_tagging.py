# ============================================================================
# SEMANTIC TAGGING MODULE
# ============================================================================
"""
Advanced semantic tagging and metadata extraction for Doc Store service.

Provides intelligent content analysis, automatic tagging, taxonomy management,
and semantic metadata extraction from document content.
"""

import re
import json
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from services.shared.utilities import utc_now
from .shared_utils import execute_db_query, safe_json_loads


@dataclass
class Tag:
    """Document tag representation."""
    id: str
    document_id: str
    tag: str
    category: str
    confidence: float
    metadata: Dict[str, Any]
    created_at: str


@dataclass
class SemanticEntity:
    """Semantic entity extracted from content."""
    entity_type: str
    entity_value: str
    confidence: float
    start_offset: int
    end_offset: int
    metadata: Dict[str, Any]


@dataclass
class TaxonomyNode:
    """Tag taxonomy node."""
    tag: str
    category: str
    description: str
    parent_tag: Optional[str]
    synonyms: List[str]
    created_at: str
    updated_at: str


class ContentAnalyzer:
    """Analyzes document content for semantic entities and topics."""

    def __init__(self):
        # Programming languages and frameworks
        self.programming_languages = {
            'python', 'javascript', 'typescript', 'java', 'csharp', 'cpp', 'c++', 'c',
            'ruby', 'php', 'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab'
        }

        # Framework and library patterns
        self.frameworks = {
            'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring',
            'express', 'nestjs', 'dotnet', 'rails', 'laravel', 'symfony'
        }

        # Technical domains
        self.technical_domains = {
            'api', 'database', 'frontend', 'backend', 'devops', 'testing',
            'security', 'performance', 'scalability', 'architecture', 'design'
        }

        # Document types
        self.document_types = {
            'readme', 'documentation', 'guide', 'tutorial', 'reference',
            'specification', 'requirements', 'architecture', 'design'
        }

        # Compile regex patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for entity extraction."""
        # Code patterns
        self.code_patterns = [
            (re.compile(r'```(\w+)', re.MULTILINE), 'code_block'),
            (re.compile(r'import\s+(\w+)', re.MULTILINE), 'import'),
            (re.compile(r'from\s+(\w+)\s+import', re.MULTILINE), 'import'),
            (re.compile(r'class\s+(\w+)', re.MULTILINE), 'class_definition'),
            (re.compile(r'def\s+(\w+)', re.MULTILINE), 'function_definition'),
        ]

        # URL patterns
        self.url_pattern = re.compile(r'https?://[^\s<>"]+')

        # Email patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

        # File extension patterns
        self.file_extension_pattern = re.compile(r'\.(\w+)[\s\)\]\}]')

    def analyze_content(self, content: str, metadata: Dict[str, Any]) -> List[SemanticEntity]:
        """Analyze document content for semantic entities."""
        entities = []

        # Extract code-related entities
        code_entities = self._extract_code_entities(content)
        entities.extend(code_entities)

        # Extract URL entities
        url_entities = self._extract_url_entities(content)
        entities.extend(url_entities)

        # Extract email entities
        email_entities = self._extract_email_entities(content)
        entities.extend(email_entities)

        # Extract file extension entities
        file_entities = self._extract_file_entities(content)
        entities.extend(file_entities)

        # Extract technical term entities
        technical_entities = self._extract_technical_entities(content)
        entities.extend(technical_entities)

        return entities

    def _extract_code_entities(self, content: str) -> List[SemanticEntity]:
        """Extract code-related entities."""
        entities = []

        for pattern, entity_type in self.code_patterns:
            matches = pattern.finditer(content)
            for match in matches:
                entity_value = match.group(1)
                start, end = match.span()

                # Determine confidence based on context
                confidence = 0.8 if len(entity_value) > 2 else 0.5

                entities.append(SemanticEntity(
                    entity_type=entity_type,
                    entity_value=entity_value,
                    confidence=confidence,
                    start_offset=start,
                    end_offset=end,
                    metadata={"pattern": pattern.pattern}
                ))

        return entities

    def _extract_url_entities(self, content: str) -> List[SemanticEntity]:
        """Extract URL entities."""
        entities = []

        matches = self.url_pattern.finditer(content)
        for match in matches:
            url = match.group(0)
            start, end = match.span()

            # Categorize URL type
            if 'github.com' in url:
                entity_type = 'github_url'
                confidence = 0.9
            elif 'stackoverflow.com' in url:
                entity_type = 'stackoverflow_url'
                confidence = 0.9
            else:
                entity_type = 'external_url'
                confidence = 0.7

            entities.append(SemanticEntity(
                entity_type=entity_type,
                entity_value=url,
                confidence=confidence,
                start_offset=start,
                end_offset=end,
                metadata={"url_type": entity_type}
            ))

        return entities

    def _extract_email_entities(self, content: str) -> List[SemanticEntity]:
        """Extract email entities."""
        entities = []

        matches = self.email_pattern.finditer(content)
        for match in matches:
            email = match.group(0)
            start, end = match.span()

            entities.append(SemanticEntity(
                entity_type='email',
                entity_value=email,
                confidence=0.95,
                start_offset=start,
                end_offset=end,
                metadata={}
            ))

        return entities

    def _extract_file_entities(self, content: str) -> List[SemanticEntity]:
        """Extract file extension entities."""
        entities = []

        matches = self.file_extension_pattern.finditer(content)
        for match in matches:
            extension = match.group(1).lower()
            start, end = match.span()

            # Map extensions to types
            extension_map = {
                'py': 'python_file',
                'js': 'javascript_file',
                'ts': 'typescript_file',
                'java': 'java_file',
                'cs': 'csharp_file',
                'cpp': 'cpp_file',
                'c': 'c_file',
                'md': 'markdown_file',
                'json': 'json_file',
                'yaml': 'yaml_file',
                'yml': 'yaml_file',
                'xml': 'xml_file',
                'html': 'html_file',
                'css': 'css_file',
                'sql': 'sql_file'
            }

            entity_type = extension_map.get(extension, f'{extension}_file')
            confidence = 0.8 if extension in extension_map else 0.6

            entities.append(SemanticEntity(
                entity_type=entity_type,
                entity_value=extension,
                confidence=confidence,
                start_offset=start,
                end_offset=end,
                metadata={"extension": extension}
            ))

        return entities

    def _extract_technical_entities(self, content: str) -> List[SemanticEntity]:
        """Extract technical domain entities."""
        entities = []
        content_lower = content.lower()

        # Extract programming languages
        for lang in self.programming_languages:
            if lang in content_lower:
                start = content_lower.find(lang)
                end = start + len(lang)

                entities.append(SemanticEntity(
                    entity_type='programming_language',
                    entity_value=lang,
                    confidence=0.85,
                    start_offset=start,
                    end_offset=end,
                    metadata={"language": lang}
                ))

        # Extract frameworks
        for framework in self.frameworks:
            if framework in content_lower:
                start = content_lower.find(framework)
                end = start + len(framework)

                entities.append(SemanticEntity(
                    entity_type='framework',
                    entity_value=framework,
                    confidence=0.8,
                    start_offset=start,
                    end_offset=end,
                    metadata={"framework": framework}
                ))

        # Extract technical domains
        for domain in self.technical_domains:
            if domain in content_lower:
                start = content_lower.find(domain)
                end = start + len(domain)

                entities.append(SemanticEntity(
                    entity_type='technical_domain',
                    entity_value=domain,
                    confidence=0.75,
                    start_offset=start,
                    end_offset=end,
                    metadata={"domain": domain}
                ))

        return entities

    def generate_tags(self, content: str, metadata: Dict[str, Any], entities: List[SemanticEntity]) -> List[Dict[str, Any]]:
        """Generate tags based on content analysis and entities."""
        tags = []

        # Tags from metadata
        if 'type' in metadata:
            tags.append({
                'tag': metadata['type'],
                'category': 'document_type',
                'confidence': 1.0,
                'metadata': {'source': 'metadata'}
            })

        if 'language' in metadata:
            tags.append({
                'tag': metadata['language'],
                'category': 'programming_language',
                'confidence': 1.0,
                'metadata': {'source': 'metadata'}
            })

        if 'source_type' in metadata:
            tags.append({
                'tag': metadata['source_type'],
                'category': 'source_type',
                'confidence': 1.0,
                'metadata': {'source': 'metadata'}
            })

        # Tags from entities
        for entity in entities:
            if entity.confidence > 0.7:  # Only high-confidence entities
                tags.append({
                    'tag': entity.entity_value,
                    'category': entity.entity_type,
                    'confidence': entity.confidence,
                    'metadata': {
                        'source': 'content_analysis',
                        'start_offset': entity.start_offset,
                        'end_offset': entity.end_offset
                    }
                })

        # Content-based tags
        content_lower = content.lower()

        # Document type detection
        for doc_type in self.document_types:
            if doc_type in content_lower:
                tags.append({
                    'tag': doc_type,
                    'category': 'document_type',
                    'confidence': 0.7,
                    'metadata': {'source': 'content_pattern'}
                })

        # Technical domain tags
        word_count = len(content.split())
        if word_count > 1000:
            tags.append({
                'tag': 'long_document',
                'category': 'document_size',
                'confidence': 1.0,
                'metadata': {'word_count': word_count}
            })
        elif word_count < 100:
            tags.append({
                'tag': 'short_document',
                'category': 'document_size',
                'confidence': 1.0,
                'metadata': {'word_count': word_count}
            })

        return tags


class SemanticTagger:
    """Manages semantic tagging and taxonomy for documents."""

    def __init__(self):
        self.analyzer = ContentAnalyzer()

    async def tag_document(self, document_id: str, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Tag a document with semantic information."""
        try:
            # Analyze content for entities
            entities = self.analyzer.analyze_content(content, metadata)

            # Generate tags
            tags = self.analyzer.generate_tags(content, metadata, entities)

            # Store entities in database
            stored_entities = self._store_entities(document_id, entities)

            # Store tags in database
            stored_tags = self._store_tags(document_id, tags)

            # Invalidate relevant caches
            from .caching import docstore_cache
            await docstore_cache.invalidate(tags=["tags", f"doc:{document_id}"])

            return {
                "document_id": document_id,
                "entities_stored": stored_entities,
                "tags_stored": stored_tags,
                "total_entities": len(entities),
                "total_tags": len(tags)
            }

        except Exception as e:
            return {"error": str(e)}

    def _store_entities(self, document_id: str, entities: List[SemanticEntity]) -> int:
        """Store semantic entities in database."""
        stored = 0

        for entity in entities:
            try:
                entity_id = f"{document_id}:{entity.entity_type}:{entity.entity_value}:{entity.start_offset}"

                execute_db_query("""
                    INSERT OR REPLACE INTO semantic_metadata
                    (id, document_id, entity_type, entity_value, confidence, start_offset, end_offset, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id,
                    document_id,
                    entity.entity_type,
                    entity.entity_value,
                    entity.confidence,
                    entity.start_offset,
                    entity.end_offset,
                    json.dumps(entity.metadata),
                    utc_now().isoformat()
                ))

                stored += 1

            except Exception:
                continue

        return stored

    def _store_tags(self, document_id: str, tags: List[Dict[str, Any]]) -> int:
        """Store tags in database."""
        stored = 0

        for tag_data in tags:
            try:
                tag_id = f"{document_id}:{tag_data['tag']}:{tag_data['category']}"

                execute_db_query("""
                    INSERT OR REPLACE INTO document_tags
                    (id, document_id, tag, category, confidence, metadata, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    tag_id,
                    document_id,
                    tag_data['tag'],
                    tag_data['category'],
                    tag_data['confidence'],
                    json.dumps(tag_data['metadata']),
                    utc_now().isoformat()
                ))

                stored += 1

            except Exception:
                continue

        return stored

    def get_document_tags(self, document_id: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tags for a document."""
        try:
            if category:
                rows = execute_db_query("""
                    SELECT id, tag, category, confidence, metadata, created_at
                    FROM document_tags
                    WHERE document_id = ? AND category = ?
                    ORDER BY confidence DESC
                """, (document_id, category), fetch_all=True)
            else:
                rows = execute_db_query("""
                    SELECT id, tag, category, confidence, metadata, created_at
                    FROM document_tags
                    WHERE document_id = ?
                    ORDER BY confidence DESC
                """, (document_id,), fetch_all=True)

            tags = []
            for row in rows:
                tags.append({
                    "id": row['id'],
                    "tag": row['tag'],
                    "category": row['category'],
                    "confidence": row['confidence'],
                    "metadata": json.loads(row['metadata'] or '{}'),
                    "created_at": row['created_at']
                })

            return tags

        except Exception:
            return []

    def get_tag_statistics(self) -> Dict[str, Any]:
        """Get comprehensive tag statistics."""
        try:
            # Tag category distribution
            category_rows = execute_db_query("""
                SELECT category, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM document_tags
                GROUP BY category
                ORDER BY count DESC
            """, fetch_all=True)

            # Most popular tags
            popular_tags = execute_db_query("""
                SELECT tag, category, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM document_tags
                GROUP BY tag, category
                ORDER BY count DESC
                LIMIT 20
            """, fetch_all=True)

            # Tag coverage (documents with tags vs total)
            tagged_docs = execute_db_query(
                "SELECT COUNT(DISTINCT document_id) FROM document_tags",
                fetch_one=True
            )[0]

            total_docs = execute_db_query("SELECT COUNT(*) FROM documents", fetch_one=True)[0]

            return {
                "total_tags": sum(row['count'] for row in category_rows),
                "total_tagged_documents": tagged_docs,
                "total_documents": total_docs,
                "tag_coverage_percentage": (tagged_docs / total_docs * 100) if total_docs > 0 else 0,
                "category_distribution": [
                    {
                        "category": row['category'],
                        "count": row['count'],
                        "avg_confidence": round(row['avg_confidence'], 3)
                    } for row in category_rows
                ],
                "popular_tags": [
                    {
                        "tag": row['tag'],
                        "category": row['category'],
                        "count": row['count'],
                        "avg_confidence": round(row['avg_confidence'], 3)
                    } for row in popular_tags
                ]
            }

        except Exception as e:
            return {"error": str(e)}

    def search_by_tags(self, tags: List[str], categories: Optional[List[str]] = None,
                      min_confidence: float = 0.0, limit: int = 50) -> List[Dict[str, Any]]:
        """Search documents by tags."""
        try:
            # Build query for documents that have any of the specified tags
            tag_placeholders = ','.join('?' for _ in tags)
            params = tags.copy()

            if categories:
                category_placeholders = ','.join('?' for _ in categories)
                params.extend(categories)
                category_filter = f"AND dt.category IN ({category_placeholders})"
            else:
                category_filter = ""

            query = f"""
                SELECT DISTINCT d.id, d.content, d.metadata, d.created_at,
                       COUNT(dt.id) as tag_matches,
                       AVG(dt.confidence) as avg_tag_confidence
                FROM documents d
                JOIN document_tags dt ON d.id = dt.document_id
                WHERE dt.tag IN ({tag_placeholders})
                {category_filter}
                AND dt.confidence >= ?
                GROUP BY d.id, d.content, d.metadata, d.created_at
                ORDER BY tag_matches DESC, avg_tag_confidence DESC
                LIMIT ?
            """

            params.extend([min_confidence, limit])

            rows = execute_db_query(query, tuple(params), fetch_all=True)

            results = []
            for row in rows:
                results.append({
                    "document_id": row['id'],
                    "content": row['content'],
                    "metadata": json.loads(row['metadata'] or '{}'),
                    "created_at": row['created_at'],
                    "tag_matches": row['tag_matches'],
                    "avg_tag_confidence": round(row['avg_tag_confidence'], 3)
                })

            return results

        except Exception:
            return []


class TagTaxonomy:
    """Manages tag taxonomy and relationships."""

    def create_taxonomy_node(self, tag: str, category: str, description: str = "",
                            parent_tag: Optional[str] = None, synonyms: Optional[List[str]] = None) -> bool:
        """Create a taxonomy node."""
        try:
            execute_db_query("""
                INSERT OR REPLACE INTO tag_taxonomy
                (id, tag, category, description, parent_tag, synonyms, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"taxonomy:{tag}",
                tag,
                category,
                description,
                parent_tag,
                json.dumps(synonyms or []),
                utc_now().isoformat(),
                utc_now().isoformat()
            ))

            return True

        except Exception:
            return False

    def get_taxonomy_tree(self, root_category: Optional[str] = None) -> Dict[str, Any]:
        """Get taxonomy tree structure."""
        try:
            if root_category:
                rows = execute_db_query("""
                    SELECT tag, category, description, parent_tag, synonyms, created_at
                    FROM tag_taxonomy
                    WHERE category = ?
                    ORDER BY tag
                """, (root_category,), fetch_all=True)
            else:
                rows = execute_db_query("""
                    SELECT tag, category, description, parent_tag, synonyms, created_at
                    FROM tag_taxonomy
                    ORDER BY category, tag
                """, fetch_all=True)

            # Build tree structure
            tree = defaultdict(list)
            nodes = {}

            for row in rows:
                node = {
                    "tag": row['tag'],
                    "category": row['category'],
                    "description": row['description'],
                    "parent_tag": row['parent_tag'],
                    "synonyms": json.loads(row['synonyms'] or '[]'),
                    "created_at": row['created_at'],
                    "children": []
                }

                nodes[row['tag']] = node
                tree[row['category']].append(node)

            # Link children to parents
            for node in nodes.values():
                if node['parent_tag'] and node['parent_tag'] in nodes:
                    nodes[node['parent_tag']]['children'].append(node)

            return dict(tree)

        except Exception as e:
            return {"error": str(e)}


# Global instances
semantic_tagger = SemanticTagger()
tag_taxonomy = TagTaxonomy()
