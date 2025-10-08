"""
Unit tests for file type detector.
"""
import pytest
from ingestion.utils.file_type_detector import FileTypeDetector, FileTypeResult


class TestFileTypeDetector:
    """Unit tests for file type detection."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.detector = FileTypeDetector()
    
    # Python files
    def test_detect_python_file(self):
        """Test Python file detection."""
        result = self.detector.detect('example.py')
        
        assert result.file_type == 'code'
        assert result.language == 'python'
        assert result.should_analyze_code is True
    
    def test_detect_python_pyx_file(self):
        """Test Cython file detection."""
        result = self.detector.detect('module.pyx')
        
        assert result.file_type == 'code'
        assert result.language == 'python'
        assert result.should_analyze_code is True
    
    # JavaScript/TypeScript files
    def test_detect_javascript_file(self):
        """Test JavaScript file detection."""
        result = self.detector.detect('app.js')
        
        assert result.file_type == 'code'
        assert result.language == 'javascript'
        assert result.should_analyze_code is True
    
    def test_detect_typescript_file(self):
        """Test TypeScript file detection."""
        result = self.detector.detect('component.ts')
        
        assert result.file_type == 'code'
        assert result.language == 'typescript'
        assert result.should_analyze_code is True
    
    def test_detect_tsx_file(self):
        """Test TSX file detection."""
        result = self.detector.detect('Component.tsx')
        
        assert result.file_type == 'code'
        assert result.language == 'typescript'
        assert result.should_analyze_code is True
    
    # Web files
    def test_detect_html_file(self):
        """Test HTML file detection."""
        result = self.detector.detect('index.html')
        
        assert result.file_type == 'code'
        assert result.language == 'html'
        assert result.should_analyze_code is True
    
    def test_detect_css_file(self):
        """Test CSS file detection."""
        result = self.detector.detect('styles.css')
        
        assert result.file_type == 'code'
        assert result.language == 'css'
        assert result.should_analyze_code is True
    
    # Document files
    def test_detect_markdown_file(self):
        """Test Markdown file detection."""
        result = self.detector.detect('README.md')
        
        assert result.file_type == 'document'
        assert result.language == 'markdown'
        assert result.should_analyze_code is False
    
    def test_detect_text_file(self):
        """Test text file detection."""
        result = self.detector.detect('notes.txt')
        
        assert result.file_type == 'document'
        assert result.language == 'text'
        assert result.should_analyze_code is False
    
    # Office documents
    def test_detect_pdf_file(self):
        """Test PDF file detection."""
        result = self.detector.detect('document.pdf')
        
        assert result.file_type == 'office'
        assert result.language == 'pdf'
        assert result.should_analyze_code is False
    
    def test_detect_word_file(self):
        """Test Word document detection."""
        result = self.detector.detect('report.docx')
        
        assert result.file_type == 'office'
        assert result.language == 'word'
        assert result.should_analyze_code is False
    
    # Image files
    def test_detect_image_file(self):
        """Test image file detection."""
        result = self.detector.detect('diagram.png')
        
        assert result.file_type == 'image'
        assert result.language is None
        assert result.should_analyze_code is False
    
    def test_detect_jpg_file(self):
        """Test JPEG file detection."""
        result = self.detector.detect('photo.jpg')
        
        assert result.file_type == 'image'
        assert result.language is None
        assert result.should_analyze_code is False
    
    # Data files
    def test_detect_json_file(self):
        """Test JSON file detection."""
        result = self.detector.detect('data.json')
        
        assert result.file_type == 'data'
        assert result.language == 'json'
        assert result.should_analyze_code is False
    
    def test_detect_csv_file(self):
        """Test CSV file detection."""
        result = self.detector.detect('export.csv')
        
        assert result.file_type == 'data'
        assert result.language == 'csv'
        assert result.should_analyze_code is False
    
    # Special files
    def test_detect_makefile(self):
        """Test Makefile detection."""
        result = self.detector.detect('Makefile')
        
        assert result.file_type == 'code'
        assert result.language == 'makefile'
        assert result.should_analyze_code is True
    
    def test_detect_dockerfile(self):
        """Test Dockerfile detection."""
        result = self.detector.detect('Dockerfile')
        
        assert result.file_type == 'code'
        assert result.language == 'dockerfile'
        assert result.should_analyze_code is True
    
    def test_detect_gitignore(self):
        """Test .gitignore detection."""
        result = self.detector.detect('.gitignore')
        
        assert result.file_type == 'document'
        assert result.language == 'text'
        assert result.should_analyze_code is False
    
    # Parameterized tests for multiple file types
    @pytest.mark.parametrize('filename,expected_type,expected_lang', [
        ('main.py', 'code', 'python'),
        ('app.js', 'code', 'javascript'),
        ('Style.css', 'code', 'css'),
        ('Config.java', 'code', 'java'),
        ('main.go', 'code', 'go'),
        ('lib.rs', 'code', 'rust'),
        ('script.rb', 'code', 'ruby'),
        ('query.sql', 'code', 'sql'),
        ('config.yml', 'code', 'yaml'),
        ('notes.txt', 'document', 'text'),
        ('doc.pdf', 'office', 'pdf'),
        ('data.json', 'data', 'json'),
        ('image.jpg', 'image', None),
    ])
    def test_detect_multiple_file_types(self, filename, expected_type, expected_lang):
        """Test detection of various file types."""
        result = self.detector.detect(filename)
        assert result.file_type == expected_type
        assert result.language == expected_lang
    
    # Unknown files
    def test_detect_unknown_extension(self):
        """Test handling of unknown file extensions."""
        result = self.detector.detect('file.xyz')
        
        assert result.file_type == 'unknown'
        assert result.language is None
        assert result.should_analyze_code is False
    
    # Content-based detection
    def test_detect_with_python_shebang(self):
        """Test detection from shebang."""
        content = b'#!/usr/bin/env python3\nprint("hello")'
        result = self.detector.detect('script', content=content)
        
        assert result.file_type == 'code'
        assert result.language == 'python'
        assert result.should_analyze_code is True
    
    def test_detect_with_bash_shebang(self):
        """Test bash script detection from shebang."""
        content = b'#!/bin/bash\necho "hello"'
        result = self.detector.detect('script', content=content)
        
        assert result.file_type == 'code'
        assert result.language == 'shell'
        assert result.should_analyze_code is True
    
    def test_detect_binary_content(self):
        """Test binary file detection."""
        content = b'\x89PNG\r\n\x1a\n\x00\x00\x00'  # PNG header
        result = self.detector.detect('unknown', content=content)
        
        assert result.file_type == 'unknown'
        assert result.language is None
    
    # Helper methods
    def test_is_code_file(self):
        """Test is_code_file helper."""
        assert self.detector.is_code_file('main.py') is True
        assert self.detector.is_code_file('README.md') is False
        assert self.detector.is_code_file('image.png') is False
    
    def test_is_document_file(self):
        """Test is_document_file helper."""
        assert self.detector.is_document_file('README.md') is True
        assert self.detector.is_document_file('report.pdf') is True
        assert self.detector.is_document_file('main.py') is False
        assert self.detector.is_document_file('image.png') is False
    
    def test_should_analyze(self):
        """Test should_analyze helper."""
        assert self.detector.should_analyze('main.py') is True
        assert self.detector.should_analyze('app.js') is True
        assert self.detector.should_analyze('README.md') is False
        assert self.detector.should_analyze('image.png') is False
    
    # Case sensitivity
    def test_case_insensitive_extension(self):
        """Test that extensions are case-insensitive."""
        result1 = self.detector.detect('FILE.PY')
        result2 = self.detector.detect('file.py')
        
        assert result1.file_type == result2.file_type
        assert result1.language == result2.language
    
    # Path handling
    def test_detect_with_path(self):
        """Test detection with full file path."""
        result = self.detector.detect('/path/to/file.py')
        
        assert result.file_type == 'code'
        assert result.language == 'python'
    
    # Result to_dict
    def test_result_to_dict(self):
        """Test FileTypeResult.to_dict()."""
        result = FileTypeResult(
            file_type='code',
            language='python',
            should_analyze_code=True,
            mime_type='text/x-python'
        )
        
        d = result.to_dict()
        
        assert d['file_type'] == 'code'
        assert d['language'] == 'python'
        assert d['should_analyze_code'] is True
        assert d['mime_type'] == 'text/x-python'

