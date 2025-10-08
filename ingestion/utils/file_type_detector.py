"""
File type detection utility.
"""
from dataclasses import dataclass
from typing import Optional
import mimetypes
import os


@dataclass
class FileTypeResult:
    """Result of file type detection."""
    
    file_type: str  # 'code', 'document', 'image', 'office', 'data', 'unknown'
    language: Optional[str] = None  # Programming language for code files
    should_analyze_code: bool = False
    mime_type: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'file_type': self.file_type,
            'language': self.language,
            'should_analyze_code': self.should_analyze_code,
            'mime_type': self.mime_type,
        }


class FileTypeDetector:
    """Detect file types and programming languages."""
    
    # File extension mappings
    CODE_EXTENSIONS = {
        # Python
        '.py': 'python',
        '.pyw': 'python',
        '.pyx': 'python',
        
        # JavaScript/TypeScript
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.mjs': 'javascript',
        
        # Web
        '.html': 'html',
        '.htm': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        
        # Java/JVM
        '.java': 'java',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.groovy': 'groovy',
        
        # C/C++
        '.c': 'c',
        '.h': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.hpp': 'cpp',
        '.hxx': 'cpp',
        
        # C#
        '.cs': 'csharp',
        
        # Go
        '.go': 'go',
        
        # Rust
        '.rs': 'rust',
        
        # Ruby
        '.rb': 'ruby',
        '.rake': 'ruby',
        
        # PHP
        '.php': 'php',
        
        # Shell
        '.sh': 'shell',
        '.bash': 'bash',
        '.zsh': 'zsh',
        
        # SQL
        '.sql': 'sql',
        
        # R
        '.r': 'r',
        '.R': 'r',
        
        # Swift
        '.swift': 'swift',
        
        # Kotlin
        '.kts': 'kotlin',
        
        # Perl
        '.pl': 'perl',
        '.pm': 'perl',
        
        # Lua
        '.lua': 'lua',
        
        # Haskell
        '.hs': 'haskell',
        
        # Elm
        '.elm': 'elm',
        
        # YAML/Config
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.conf': 'config',
        '.cfg': 'config',
        
        # Makefile
        '.mk': 'makefile',
    }
    
    DOCUMENT_EXTENSIONS = {
        '.md': 'markdown',
        '.markdown': 'markdown',
        '.txt': 'text',
        '.text': 'text',
        '.rst': 'restructuredtext',
        '.adoc': 'asciidoc',
        '.tex': 'latex',
        '.org': 'org-mode',
    }
    
    OFFICE_EXTENSIONS = {
        '.doc': 'word',
        '.docx': 'word',
        '.pdf': 'pdf',
        '.xls': 'excel',
        '.xlsx': 'excel',
        '.ppt': 'powerpoint',
        '.pptx': 'powerpoint',
        '.odt': 'opendocument',
        '.ods': 'opendocument',
        '.odp': 'opendocument',
    }
    
    IMAGE_EXTENSIONS = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp',
        '.ico', '.tiff', '.tif', '.psd', '.ai', '.eps'
    }
    
    DATA_EXTENSIONS = {
        '.json': 'json',
        '.xml': 'xml',
        '.csv': 'csv',
        '.tsv': 'tsv',
        '.parquet': 'parquet',
        '.avro': 'avro',
        '.proto': 'protobuf',
    }
    
    SPECIAL_FILES = {
        'Makefile': ('code', 'makefile', True),
        'Dockerfile': ('code', 'dockerfile', True),
        'Jenkinsfile': ('code', 'groovy', True),
        'Vagrantfile': ('code', 'ruby', True),
        'Rakefile': ('code', 'ruby', True),
        'Gemfile': ('code', 'ruby', True),
        'Podfile': ('code', 'ruby', True),
        '.gitignore': ('document', 'text', False),
        '.dockerignore': ('document', 'text', False),
        'README': ('document', 'text', False),
        'LICENSE': ('document', 'text', False),
        'CHANGELOG': ('document', 'text', False),
        'TODO': ('document', 'text', False),
    }
    
    def detect(self, filename: str, content: Optional[bytes] = None) -> FileTypeResult:
        """
        Detect file type from filename and optionally content.
        
        Args:
            filename: Name of the file
            content: Optional file content for content-based detection
        
        Returns:
            FileTypeResult with detected information
        """
        # Get base filename (no path)
        basename = os.path.basename(filename)
        
        # Check special files first (Makefile, Dockerfile, etc.)
        if basename in self.SPECIAL_FILES:
            file_type, language, analyze = self.SPECIAL_FILES[basename]
            return FileTypeResult(
                file_type=file_type,
                language=language,
                should_analyze_code=analyze,
                mime_type=mimetypes.guess_type(filename)[0]
            )
        
        # Get extension
        _, ext = os.path.splitext(filename)
        ext_lower = ext.lower()
        
        # Check code files
        if ext_lower in self.CODE_EXTENSIONS:
            language = self.CODE_EXTENSIONS[ext_lower]
            return FileTypeResult(
                file_type='code',
                language=language,
                should_analyze_code=True,
                mime_type=mimetypes.guess_type(filename)[0]
            )
        
        # Check documents
        if ext_lower in self.DOCUMENT_EXTENSIONS:
            language = self.DOCUMENT_EXTENSIONS[ext_lower]
            return FileTypeResult(
                file_type='document',
                language=language,
                should_analyze_code=False,
                mime_type=mimetypes.guess_type(filename)[0]
            )
        
        # Check office documents
        if ext_lower in self.OFFICE_EXTENSIONS:
            doc_type = self.OFFICE_EXTENSIONS[ext_lower]
            return FileTypeResult(
                file_type='office',
                language=doc_type,
                should_analyze_code=False,
                mime_type=mimetypes.guess_type(filename)[0]
            )
        
        # Check images
        if ext_lower in self.IMAGE_EXTENSIONS:
            return FileTypeResult(
                file_type='image',
                language=None,
                should_analyze_code=False,
                mime_type=mimetypes.guess_type(filename)[0]
            )
        
        # Check data files
        if ext_lower in self.DATA_EXTENSIONS:
            data_format = self.DATA_EXTENSIONS[ext_lower]
            return FileTypeResult(
                file_type='data',
                language=data_format,
                should_analyze_code=False,
                mime_type=mimetypes.guess_type(filename)[0]
            )
        
        # Content-based detection if content provided
        if content:
            return self._detect_from_content(filename, content)
        
        # Unknown type
        return FileTypeResult(
            file_type='unknown',
            language=None,
            should_analyze_code=False,
            mime_type=mimetypes.guess_type(filename)[0]
        )
    
    def _detect_from_content(self, filename: str, content: bytes) -> FileTypeResult:
        """Detect file type from content (for files without extensions)."""
        try:
            # Try to decode as text
            text = content.decode('utf-8', errors='strict')
            
            # Check for shebang
            if text.startswith('#!'):
                first_line = text.split('\n')[0]
                if 'python' in first_line:
                    return FileTypeResult('code', 'python', True)
                elif 'bash' in first_line or 'sh' in first_line:
                    return FileTypeResult('code', 'shell', True)
                elif 'node' in first_line:
                    return FileTypeResult('code', 'javascript', True)
                elif 'ruby' in first_line:
                    return FileTypeResult('code', 'ruby', True)
            
            # Appears to be text
            return FileTypeResult(
                file_type='document',
                language='text',
                should_analyze_code=False
            )
        except UnicodeDecodeError:
            # Binary file
            return FileTypeResult(
                file_type='unknown',
                language=None,
                should_analyze_code=False
            )
    
    def is_code_file(self, filename: str) -> bool:
        """Quick check if file is a code file."""
        result = self.detect(filename)
        return result.file_type == 'code'
    
    def is_document_file(self, filename: str) -> bool:
        """Quick check if file is a document file."""
        result = self.detect(filename)
        return result.file_type in ('document', 'office')
    
    def should_analyze(self, filename: str) -> bool:
        """Quick check if file should be analyzed by code-analyzer."""
        result = self.detect(filename)
        return result.should_analyze_code

