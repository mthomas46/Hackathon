"""Comprehensive tests for CLI TableFormatters."""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add service path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from cli.modules.formatters.table_formatters import TableFormatters


class TestTableFormatters:
    """Test TableFormatters functionality."""

    @pytest.fixture
    def table_formatters(self):
        """Create TableFormatters instance."""
        return TableFormatters()

    @pytest.fixture
    def mock_console(self):
        """Create mock console."""
        return Mock()

    def test_table_formatters_initialization(self, table_formatters):
        """Test TableFormatters initialization."""
        assert table_formatters is not None

    def test_format_service_status_table(self, table_formatters, mock_console):
        """Test service status table formatting."""
        services_data = [
            {"name": "analysis-service", "status": "healthy", "version": "1.0.0"},
            {"name": "doc-store", "status": "unhealthy", "version": "1.0.0"}
        ]

        with patch('rich.table.Table') as mock_table, \
             patch('rich.console.Console') as mock_console_class:

            mock_table_instance = Mock()
            mock_table.return_value = mock_table_instance
            mock_console_class.return_value = mock_console

            result = table_formatters.format_service_status_table(services_data, mock_console)

            # Verify table creation and population
            mock_table.assert_called_once()
            assert mock_table_instance.add_column.call_count >= 2  # At least name and status columns

    def test_format_service_status_table_empty(self, table_formatters, mock_console):
        """Test service status table formatting with empty data."""
        services_data = []

        with patch('rich.table.Table') as mock_table, \
             patch('rich.console.Console') as mock_console_class:

            mock_table_instance = Mock()
            mock_table.return_value = mock_table_instance
            mock_console_class.return_value = mock_console

            result = table_formatters.format_service_status_table(services_data, mock_console)

            # Should handle empty data gracefully
            mock_table.assert_called_once()

    def test_format_document_table(self, table_formatters, mock_console):
        """Test document table formatting."""
        documents_data = [
            {"id": "doc1", "title": "Document 1", "status": "active", "size": 1024},
            {"id": "doc2", "title": "Document 2", "status": "archived", "size": 2048}
        ]

        with patch('rich.table.Table') as mock_table, \
             patch('rich.console.Console') as mock_console_class:

            mock_table_instance = Mock()
            mock_table.return_value = mock_table_instance
            mock_console_class.return_value = mock_console

            result = table_formatters.format_document_table(documents_data, mock_console)

            mock_table.assert_called_once()
            assert mock_table_instance.add_column.call_count >= 3  # id, title, status columns

    def test_format_workflow_table(self, table_formatters, mock_console):
        """Test workflow table formatting."""
        workflows_data = [
            {"id": "wf1", "name": "Analysis Workflow", "status": "running", "created": "2024-01-01"},
            {"id": "wf2", "name": "Report Workflow", "status": "completed", "created": "2024-01-02"}
        ]

        with patch('rich.table.Table') as mock_table, \
             patch('rich.console.Console') as mock_console_class:

            mock_table_instance = Mock()
            mock_table.return_value = mock_table_instance
            mock_console_class.return_value = mock_console

            result = table_formatters.format_workflow_table(workflows_data, mock_console)

            mock_table.assert_called_once()

    def test_format_prompt_table(self, table_formatters, mock_console):
        """Test prompt table formatting."""
        prompts_data = [
            {"id": "p1", "name": "Analysis Prompt", "category": "analysis", "created": "2024-01-01"},
            {"id": "p2", "name": "Summary Prompt", "category": "summary", "created": "2024-01-02"}
        ]

        with patch('rich.table.Table') as mock_table, \
             patch('rich.console.Console') as mock_console_class:

            mock_table_instance = Mock()
            mock_table.return_value = mock_table_instance
            mock_console_class.return_value = mock_console

            result = table_formatters.format_prompt_table(prompts_data, mock_console)

            mock_table.assert_called_once()
            assert mock_table_instance.add_column.call_count >= 3

    def test_format_metrics_table(self, table_formatters, mock_console):
        """Test metrics table formatting."""
        metrics_data = [
            {"name": "cpu_usage", "value": "45%", "status": "normal"},
            {"name": "memory_usage", "value": "2.1GB", "status": "warning"},
            {"name": "disk_usage", "value": "85%", "status": "critical"}
        ]

        with patch('rich.table.Table') as mock_table, \
             patch('rich.console.Console') as mock_console_class:

            mock_table_instance = Mock()
            mock_table.return_value = mock_table_instance
            mock_console_class.return_value = mock_console

            result = table_formatters.format_metrics_table(metrics_data, mock_console)

            mock_table.assert_called_once()

    def test_format_error_table(self, table_formatters, mock_console):
        """Test error table formatting."""
        errors_data = [
            {"service": "analysis-service", "error": "Connection timeout", "timestamp": "2024-01-01T10:00:00Z"},
            {"service": "doc-store", "error": "Database error", "timestamp": "2024-01-01T10:05:00Z"}
        ]

        with patch('rich.table.Table') as mock_table, \
             patch('rich.console.Console') as mock_console_class:

            mock_table_instance = Mock()
            mock_table.return_value = mock_table_instance
            mock_console_class.return_value = mock_console

            result = table_formatters.format_error_table(errors_data, mock_console)

            mock_table.assert_called_once()

    def test_format_bulk_operation_table(self, table_formatters, mock_console):
        """Test bulk operation table formatting."""
        operations_data = [
            {"id": "op1", "type": "document_import", "status": "running", "progress": "45%", "items_processed": 450},
            {"id": "op2", "type": "data_export", "status": "completed", "progress": "100%", "items_processed": 1000}
        ]

        with patch('rich.table.Table') as mock_table, \
             patch('rich.console.Console') as mock_console_class:

            mock_table_instance = Mock()
            mock_table.return_value = mock_table_instance
            mock_console_class.return_value = mock_console

            result = table_formatters.format_bulk_operation_table(operations_data, mock_console)

            mock_table.assert_called_once()

    def test_create_table_with_custom_columns(self, table_formatters):
        """Test creating table with custom columns."""
        columns = [
            ("Name", "name", "string"),
            ("Status", "status", "string"),
            ("Count", "count", "number")
        ]

        with patch('rich.table.Table') as mock_table:
            mock_table_instance = Mock()
            mock_table.return_value = mock_table_instance

            result = table_formatters.create_table_with_columns(columns)

            mock_table.assert_called_once()
            assert mock_table_instance.add_column.call_count == len(columns)

    def test_add_data_rows_to_table(self, table_formatters):
        """Test adding data rows to table."""
        table_mock = Mock()
        data = [
            {"name": "Item 1", "value": 100},
            {"name": "Item 2", "value": 200}
        ]

        table_formatters.add_data_rows_to_table(table_mock, data)

        assert table_mock.add_row.call_count == len(data)

    def test_format_cell_value_string(self, table_formatters):
        """Test formatting string cell values."""
        result = table_formatters.format_cell_value("test_string", "string")
        assert result == "test_string"

    def test_format_cell_value_number(self, table_formatters):
        """Test formatting number cell values."""
        result = table_formatters.format_cell_value(1234, "number")
        assert result == "1,234"  # Should format with commas

    def test_format_cell_value_boolean(self, table_formatters):
        """Test formatting boolean cell values."""
        result_true = table_formatters.format_cell_value(True, "boolean")
        result_false = table_formatters.format_cell_value(False, "boolean")

        assert "✓" in result_true or "Yes" in result_true
        assert "✗" in result_false or "No" in result_false

    def test_format_cell_value_datetime(self, table_formatters):
        """Test formatting datetime cell values."""
        from datetime import datetime
        dt = datetime(2024, 1, 1, 10, 30, 0)

        result = table_formatters.format_cell_value(dt, "datetime")
        assert "2024" in result and "10:30" in result

    def test_format_cell_value_unknown_type(self, table_formatters):
        """Test formatting unknown cell value types."""
        result = table_formatters.format_cell_value({"complex": "object"}, "unknown")
        assert result == "{'complex': 'object'}"

    def test_get_status_style_healthy(self, table_formatters):
        """Test status style for healthy status."""
        style = table_formatters.get_status_style("healthy")
        assert "green" in style or "success" in style

    def test_get_status_style_unhealthy(self, table_formatters):
        """Test status style for unhealthy status."""
        style = table_formatters.get_status_style("unhealthy")
        assert "red" in style or "error" in style

    def test_get_status_style_warning(self, table_formatters):
        """Test status style for warning status."""
        style = table_formatters.get_status_style("warning")
        assert "yellow" in style or "warning" in style

    def test_get_status_style_unknown(self, table_formatters):
        """Test status style for unknown status."""
        style = table_formatters.get_status_style("unknown")
        assert style == ""  # Default style

    def test_get_column_width_auto(self, table_formatters):
        """Test automatic column width calculation."""
        data = [
            {"name": "Short"},
            {"name": "Much Longer Name Here"}
        ]

        width = table_formatters.get_column_width(data, "name")
        assert width >= len("Much Longer Name Here")

    def test_get_column_width_fixed(self, table_formatters):
        """Test fixed column width."""
        width = table_formatters.get_column_width([], "test", max_width=20)
        assert width <= 20

    def test_sort_table_data(self, table_formatters):
        """Test table data sorting."""
        data = [
            {"name": "Zebra", "value": 1},
            {"name": "Apple", "value": 3},
            {"name": "Banana", "value": 2}
        ]

        sorted_data = table_formatters.sort_table_data(data, "name", "asc")
        assert sorted_data[0]["name"] == "Apple"
        assert sorted_data[1]["name"] == "Banana"
        assert sorted_data[2]["name"] == "Zebra"

    def test_sort_table_data_desc(self, table_formatters):
        """Test table data sorting in descending order."""
        data = [
            {"name": "Apple", "value": 1},
            {"name": "Zebra", "value": 2}
        ]

        sorted_data = table_formatters.sort_table_data(data, "name", "desc")
        assert sorted_data[0]["name"] == "Zebra"
        assert sorted_data[1]["name"] == "Apple"

    def test_pagination_info_calculation(self, table_formatters):
        """Test pagination info calculation."""
        total_items = 150
        page_size = 25
        current_page = 2

        info = table_formatters.get_pagination_info(total_items, page_size, current_page)

        assert info["total_items"] == 150
        assert info["total_pages"] == 6
        assert info["current_page"] == 2
        assert info["start_item"] == 26
        assert info["end_item"] == 50

    def test_export_table_to_csv(self, table_formatters):
        """Test table export to CSV format."""
        data = [
            {"name": "Item 1", "value": 100},
            {"name": "Item 2", "value": 200}
        ]

        csv_content = table_formatters.export_table_to_csv(data)

        assert "name,value" in csv_content
        assert "Item 1,100" in csv_content
        assert "Item 2,200" in csv_content

    def test_export_table_to_json(self, table_formatters):
        """Test table export to JSON format."""
        data = [
            {"name": "Item 1", "value": 100},
            {"name": "Item 2", "value": 200}
        ]

        json_content = table_formatters.export_table_to_json(data)

        assert '"name": "Item 1"' in json_content
        assert '"value": 100' in json_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
