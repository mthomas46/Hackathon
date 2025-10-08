"""
Local file ingestion with universal tagging.

Ingests files from local directories with automatic file type detection,
format normalization, and intelligent tagging.
"""
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from ingestion.models import NormalizedDocument
from ingestion.utils.file_type_detector import FileTypeDetector
from ingestion.utils.markdown_normalizer import MarkdownNormalizer
from ingestion.utils.timestamp_parser import TimestampParser
from ingestion.tagging import UniversalTaggingManager, UniversalTaggingConfig, TagCollection

logger = logging.getLogger(__name__)


class LocalFileIngestor:
    """Ingest files from local directories with intelligent tagging."""
    
    def __init__(
        self,
        tagging_config: Optional[UniversalTaggingConfig] = None,
        enable_tagging: bool = True,
        enable_corpus_analysis: bool = False,
        corpus_analysis_sample_size: int = 20
    ):
        """
        Initialize local file ingestor.
        
        Args:
            tagging_config: Configuration for universal tagging
            enable_tagging: Whether to apply tagging
            enable_corpus_analysis: Whether to perform corpus analysis
            corpus_analysis_sample_size: Number of docs to analyze for contextual tags
        """
        self.enable_tagging = enable_tagging
        self.enable_corpus_analysis = enable_corpus_analysis
        
        if enable_tagging:
            config = tagging_config or UniversalTaggingConfig(
                enable_preprocessing=enable_corpus_analysis,
                preprocessing_sample_size=corpus_analysis_sample_size
            )
            self.tagging_manager = UniversalTaggingManager(config)
        else:
            self.tagging_manager = None
        
        self.file_detector = FileTypeDetector()
        self.markdown_normalizer = MarkdownNormalizer()
        self.timestamp_parser = TimestampParser()
        self.tag_collection: Optional[TagCollection] = None
        self.ingested_documents: List[NormalizedDocument] = []
    
    async def ingest_directory(
        self,
        directory_path: str,
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        user_tags: Optional[List[str]] = None
    ) -> List[NormalizedDocument]:
        """
        Ingest files from a directory.
        
        Args:
            directory_path: Path to directory to ingest
            recursive: Whether to recursively scan subdirectories
            file_patterns: Glob patterns to include (e.g., ['*.md', '*.py'])
            exclude_patterns: Glob patterns to exclude (e.g., ['*.pyc', '__pycache__'])
            user_tags: Additional user-defined tags to apply
        
        Returns:
            List of normalized documents
        """
        logger.info(f"📂 Ingesting files from: {directory_path}")
        
        directory = Path(directory_path)
        if not directory.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return []
        
        if not directory.is_dir():
            logger.error(f"Path is not a directory: {directory_path}")
            return []
        
        # Collect files
        files = self._collect_files(
            directory,
            recursive=recursive,
            file_patterns=file_patterns,
            exclude_patterns=exclude_patterns
        )
        
        logger.info(f"Found {len(files)} files to ingest")
        
        # Process files
        documents = []
        for file_path in files:
            try:
                doc = await self._process_file(file_path)
                if doc:
                    documents.append(doc)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}", exc_info=True)
        
        logger.info(f"✅ Processed {len(documents)} documents")
        
        # Apply universal tagging
        if self.enable_tagging and self.tagging_manager and documents:
            logger.info(f"🏷️  Applying universal tagging...")
            documents, self.tag_collection = await self.tagging_manager.tag_documents(
                documents=documents,
                source_type='local_files',
                user_tags=user_tags
            )
            logger.info(f"✅ Tagged {len(documents)} documents")
        
        self.ingested_documents = documents
        return documents
    
    def _collect_files(
        self,
        directory: Path,
        recursive: bool,
        file_patterns: Optional[List[str]],
        exclude_patterns: Optional[List[str]]
    ) -> List[Path]:
        """Collect files from directory based on patterns."""
        files = []
        
        # Default exclude patterns
        default_excludes = [
            '__pycache__',
            '*.pyc',
            '.git',
            '.DS_Store',
            '*.log',
            'node_modules',
            'venv',
            '.venv',
            '.pytest_cache',
            'htmlcov'
        ]
        
        exclude_patterns = (exclude_patterns or []) + default_excludes
        
        if recursive:
            glob_pattern = '**/*'
        else:
            glob_pattern = '*'
        
        for path in directory.glob(glob_pattern):
            if not path.is_file():
                continue
            
            # Check exclude patterns
            if any(path.match(pattern) for pattern in exclude_patterns):
                continue
            
            # Check include patterns
            if file_patterns:
                if not any(path.match(pattern) for pattern in file_patterns):
                    continue
            
            files.append(path)
        
        return sorted(files)
    
    async def _process_file(self, file_path: Path) -> Optional[NormalizedDocument]:
        """Process a single file into a normalized document."""
        try:
            # Detect file type
            file_type = self.file_detector.detect_file_type(str(file_path))
            
            # Read file content
            content = self._read_file(file_path)
            if not content:
                logger.warning(f"Empty or unreadable file: {file_path}")
                return None
            
            # Normalize to markdown
            if file_type == 'code':
                # Keep code files as-is in code blocks
                normalized_content = f"```{file_path.suffix[1:]}\n{content}\n```"
            elif file_type == 'document':
                # Detect document format and normalize
                if file_path.suffix == '.md':
                    normalized_content = self.markdown_normalizer.normalize(content, 'markdown')
                elif file_path.suffix in ['.html', '.htm']:
                    normalized_content = self.markdown_normalizer.normalize(content, 'html')
                elif file_path.suffix == '.rst':
                    normalized_content = self.markdown_normalizer.normalize(content, 'rst')
                else:
                    normalized_content = self.markdown_normalizer.normalize(content, 'plaintext')
            else:
                # Other file types as plaintext
                normalized_content = self.markdown_normalizer.normalize(content, 'plaintext')
            
            # Extract timestamps
            created_at, updated_at = self._extract_timestamps(file_path)
            
            # Build metadata
            metadata = {
                'source': 'local_files',
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_type': file_type,
                'original_format': file_path.suffix[1:] if file_path.suffix else 'txt',
                'file_size': os.path.getsize(file_path),
                'created_at': created_at,
                'updated_at': updated_at,
                'ingested_at': datetime.utcnow().isoformat()
            }
            
            # Create document
            document = NormalizedDocument(
                document_id=f"local-{file_path.stem}-{hash(str(file_path)) & 0xFFFFFFFF:08x}",
                title=file_path.name,
                content_md=normalized_content,
                original_format=metadata['original_format'],
                metadata=metadata,
                tags=[]  # Will be populated by tagging manager
            )
            
            return document
        
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
            return None
    
    def _read_file(self, file_path: Path) -> Optional[str]:
        """Read file content with encoding fallbacks."""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                return None
        
        logger.warning(f"Could not decode {file_path} with any encoding")
        return None
    
    def _extract_timestamps(self, file_path: Path) -> tuple:
        """Extract created and updated timestamps from file."""
        try:
            stat = os.stat(file_path)
            
            # Created time (ctime on Unix is last metadata change, not creation)
            # Use birthtime on systems that support it
            created_timestamp = getattr(stat, 'st_birthtime', stat.st_ctime)
            created_at = self.timestamp_parser.parse_unix(created_timestamp)
            
            # Modified time
            updated_at = self.timestamp_parser.parse_unix(stat.st_mtime)
            
            return (
                self.timestamp_parser.to_iso(created_at),
                self.timestamp_parser.to_iso(updated_at)
            )
        except Exception as e:
            logger.warning(f"Error extracting timestamps for {file_path}: {e}")
            now = datetime.utcnow().isoformat()
            return (now, now)
    
    def get_tag_collection(self) -> Optional[TagCollection]:
        """Get the tag collection from the last ingestion."""
        return self.tag_collection
    
    def get_ingested_documents(self) -> List[NormalizedDocument]:
        """Get the list of ingested documents."""
        return self.ingested_documents
    
    async def ingest_file(
        self,
        file_path: str,
        user_tags: Optional[List[str]] = None
    ) -> Optional[NormalizedDocument]:
        """
        Ingest a single file.
        
        Args:
            file_path: Path to file to ingest
            user_tags: Additional user-defined tags
        
        Returns:
            Normalized document or None if failed
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            logger.error(f"File does not exist: {file_path}")
            return None
        
        doc = await self._process_file(path)
        
        if doc and self.enable_tagging and self.tagging_manager:
            # Apply tagging to single document
            docs, self.tag_collection = await self.tagging_manager.tag_documents(
                documents=[doc],
                source_type='local_files',
                user_tags=user_tags
            )
            doc = docs[0] if docs else doc
        
        return doc
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about ingested files."""
        if not self.ingested_documents:
            return {}
        
        file_types = {}
        total_size = 0
        
        for doc in self.ingested_documents:
            file_type = doc.metadata.get('file_type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
            total_size += doc.metadata.get('file_size', 0)
        
        return {
            'total_documents': len(self.ingested_documents),
            'file_types': file_types,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'tag_collection': self.tag_collection.to_dict() if self.tag_collection else None
        }

