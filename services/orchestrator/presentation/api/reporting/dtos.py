"""DTOs for Reporting API"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, Optional, List
from datetime import datetime


class GenerateReportRequest(BaseModel):
    """Request to generate a report."""

    report_type: str = Field(..., min_length=1, max_length=100)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    filters: Optional[Dict[str, Any]] = None
    date_range: Optional[Dict[str, str]] = None
    format: str = Field("json", min_length=1, max_length=50)
    include_charts: bool = Field(True)

    @field_validator('report_type')
    @classmethod
    def validate_report_type(cls, v):
        valid_types = ['pr_confidence', 'summarization', 'analytics', 'performance', 'usage', 'health', 'custom']
        if v not in valid_types:
            raise ValueError(f'Report type must be one of: {", ".join(valid_types)}')
        return v

    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        valid_formats = ['json', 'pdf', 'html', 'csv', 'xlsx']
        if v not in valid_formats:
            raise ValueError(f'Format must be one of: {", ".join(valid_formats)}')
        return v


class ReportResponse(BaseModel):
    """Response containing report data."""

    report_id: str
    report_type: str
    title: str
    description: Optional[str]
    parameters: Dict[str, Any]
    data: Dict[str, Any]
    charts: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any]
    generated_at: str
    format: str
    file_size_bytes: Optional[int] = None
    download_url: Optional[str] = None

    class Config:
        from_attributes = True


class ReportSummaryResponse(BaseModel):
    """Response containing report summary."""

    report_id: str
    report_type: str
    title: str
    status: str
    generated_at: str
    parameters: Dict[str, Any]
    file_size_bytes: Optional[int] = None

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Response containing list of reports."""

    reports: List[ReportSummaryResponse]
    total: int
    page: int
    page_size: int

    class Config:
        from_attributes = True


class ReportTemplateResponse(BaseModel):
    """Response containing report template information."""

    template_id: str
    name: str
    description: str
    report_type: str
    parameters_schema: Dict[str, Any]
    default_parameters: Dict[str, Any]
    created_at: str

    class Config:
        from_attributes = True


class ReportTemplatesListResponse(BaseModel):
    """Response containing list of report templates."""

    templates: List[ReportTemplateResponse]
    total: int

    class Config:
        from_attributes = True
