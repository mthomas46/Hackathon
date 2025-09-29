"""Report Format Value Object"""

from enum import Enum


class ReportFormat(Enum):
    """Enumeration of supported report formats."""

    JSON = "json"
    HTML = "html"
    PDF = "pdf"
    TEXT = "text"
    XML = "xml"

    @property
    def content_type(self) -> str:
        """Get the HTTP content type for this format."""
        content_types = {
            ReportFormat.JSON: "application/json",
            ReportFormat.HTML: "text/html",
            ReportFormat.PDF: "application/pdf",
            ReportFormat.TEXT: "text/plain",
            ReportFormat.XML: "application/xml"
        }
        return content_types[self]

    @property
    def file_extension(self) -> str:
        """Get the file extension for this format."""
        extensions = {
            ReportFormat.JSON: ".json",
            ReportFormat.HTML: ".html",
            ReportFormat.PDF: ".pdf",
            ReportFormat.TEXT: ".txt",
            ReportFormat.XML: ".xml"
        }
        return extensions[self]

    def __str__(self) -> str:
        return self.value
