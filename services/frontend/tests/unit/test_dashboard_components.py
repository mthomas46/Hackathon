"""Unit Tests for Dashboard Components in Frontend Service.

This module tests dashboard component functionality including:
- Component rendering and state management
- Data visualization and interactivity
- Real-time data integration
- User customization and preferences
- Performance optimization and caching

Tests cover the complete dashboard infrastructure within the Frontend service.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

from modules.ui_handlers.main_handlers import MainUIHandler
from modules.data_browser import DataBrowser


class TestComponentRendering:
    """Test Component Rendering functionality."""

    @pytest.fixture
    def ui_handler(self, mock_api_client, mock_websocket_manager):
        """Create UI handler instance."""
        return MainUIHandler(
            api_client=mock_api_client,
            websocket_manager=mock_websocket_manager
        )

    def test_dashboard_initial_render(self, ui_handler):
        """Test initial dashboard rendering."""
        render_config = {
            "dashboard_id": "main_dashboard",
            "layout": "grid",
            "theme": "dark",
            "components": [
                {"type": "services_overview", "position": {"x": 0, "y": 0, "width": 6, "height": 4}},
                {"type": "recent_activity", "position": {"x": 6, "y": 0, "width": 6, "height": 4}},
                {"type": "performance_metrics", "position": {"x": 0, "y": 4, "width": 12, "height": 4}}
            ],
            "user_preferences": {
                "auto_refresh": True,
                "refresh_interval": 30,
                "compact_view": False
            }
        }

        render_result = ui_handler.render_dashboard(render_config)

        assert render_result["success"] is True
        assert "rendered_html" in render_result
        assert "component_states" in render_result
        assert "render_performance" in render_result

        # Should render all specified components
        assert len(render_result["component_states"]) == len(render_config["components"])

        # Should include performance metrics
        performance = render_result["render_performance"]
        assert "total_render_time_ms" in performance
        assert "component_render_times" in performance

    def test_component_state_management(self, ui_handler):
        """Test component state management."""
        component_id = "services_table"
        initial_state = {
            "sort_column": "name",
            "sort_direction": "asc",
            "filters": {},
            "page": 1,
            "page_size": 25,
            "selected_rows": []
        }

        # Set initial state
        set_result = ui_handler.set_component_state(component_id, initial_state)
        assert set_result["success"] is True

        # Update state
        updates = {
            "sort_column": "status",
            "filters": {"status": ["healthy"]},
            "selected_rows": ["interpreter", "orchestrator"]
        }

        update_result = ui_handler.update_component_state(component_id, updates)
        assert update_result["success"] is True

        # Get current state
        current_state = ui_handler.get_component_state(component_id)
        assert current_state["success"] is True

        state_data = current_state["state"]
        assert state_data["sort_column"] == "status"
        assert state_data["filters"]["status"] == ["healthy"]
        assert set(state_data["selected_rows"]) == set(updates["selected_rows"])

    def test_component_data_binding(self, ui_handler):
        """Test component data binding and updates."""
        component_config = {
            "component_id": "services_status_chart",
            "data_source": "service_monitoring",
            "data_bindings": {
                "services": "$.services[*]",
                "status_distribution": "$.status_summary",
                "response_times": "$.services[*].response_time_ms"
            },
            "update_triggers": ["service_status_changed", "periodic_refresh"]
        }

        # Test data binding with sample data
        sample_data = {
            "services": [
                {"name": "interpreter", "status": "healthy", "response_time_ms": 245},
                {"name": "orchestrator", "status": "degraded", "response_time_ms": 450},
                {"name": "doc_store", "status": "healthy", "response_time_ms": 180}
            ],
            "status_summary": {"healthy": 2, "degraded": 1, "down": 0}
        }

        binding_result = ui_handler.bind_component_data(component_config, sample_data)

        assert binding_result["success"] is True
        assert "bound_data" in binding_result
        assert "binding_validation" in binding_result

        bound_data = binding_result["bound_data"]

        # Should extract services array
        assert len(bound_data["services"]) == 3

        # Should extract status distribution
        assert bound_data["status_distribution"]["healthy"] == 2

        # Should extract response times array
        assert len(bound_data["response_times"]) == 3
        assert 180 in bound_data["response_times"]
        assert 245 in bound_data["response_times"]
        assert 450 in bound_data["response_times"]

    def test_component_interactivity_handling(self, ui_handler):
        """Test component interactivity handling."""
        component_id = "interactive_table"
        interaction_events = [
            {
                "event_type": "row_click",
                "event_data": {"row_id": "interpreter", "column": "status"},
                "timestamp": datetime.now()
            },
            {
                "event_type": "filter_change",
                "event_data": {"filter_type": "status", "value": "healthy"},
                "timestamp": datetime.now()
            },
            {
                "event_type": "sort_change",
                "event_data": {"column": "name", "direction": "desc"},
                "timestamp": datetime.now()
            }
        ]

        for event in interaction_events:
            interaction_result = ui_handler.handle_component_interaction(component_id, event)

            assert interaction_result["success"] is True
            assert interaction_result["interaction_processed"] is True
            assert "side_effects" in interaction_result

            # Should trigger appropriate side effects
            side_effects = interaction_result["side_effects"]

            if event["event_type"] == "row_click":
                assert any("navigation" in str(effect) for effect in side_effects)
            elif event["event_type"] == "filter_change":
                assert any("data_refresh" in str(effect) for effect in side_effects)
            elif event["event_type"] == "sort_change":
                assert any("state_update" in str(effect) for effect in side_effects)

    def test_component_performance_optimization(self, ui_handler):
        """Test component performance optimization."""
        component_config = {
            "component_id": "performance_test_component",
            "optimization_settings": {
                "virtual_scrolling": True,
                "lazy_loading": True,
                "data_caching": True,
                "render_throttling": True
            },
            "performance_targets": {
                "initial_render_time_ms": 500,
                "update_time_ms": 100,
                "memory_usage_mb": 50
            }
        }

        optimization_result = ui_handler.optimize_component_performance(component_config)

        assert optimization_result["success"] is True
        assert "optimization_applied" in optimization_result
        assert "performance_metrics" in optimization_result

        optimizations = optimization_result["optimization_applied"]
        assert optimizations["virtual_scrolling"] is True
        assert optimizations["lazy_loading"] is True
        assert optimizations["data_caching"] is True

        metrics = optimization_result["performance_metrics"]
        assert "optimization_overhead_ms" in metrics
        assert "memory_savings_mb" in metrics
        assert "render_improvement_percentage" in metrics

    def test_component_error_handling_and_recovery(self, ui_handler):
        """Test component error handling and recovery."""
        component_id = "error_prone_component"

        # Simulate various component errors
        error_scenarios = [
            {
                "error_type": "data_loading_failed",
                "error_details": {"reason": "api_timeout", "endpoint": "/api/services"},
                "expected_recovery": "show_retry_option"
            },
            {
                "error_type": "render_error",
                "error_details": {"reason": "invalid_template", "component": "chart_widget"},
                "expected_recovery": "show_fallback_view"
            },
            {
                "error_type": "state_corruption",
                "error_details": {"reason": "concurrent_modification", "component_state": "sort_options"},
                "expected_recovery": "reset_to_defaults"
            }
        ]

        for scenario in error_scenarios:
            error_context = {
                "component_id": component_id,
                "error": scenario,
                "timestamp": datetime.now(),
                "user_impact": "medium"
            }

            recovery_result = ui_handler.handle_component_error(error_context)

            assert recovery_result["success"] is True
            assert recovery_result["error_handled"] is True
            assert "recovery_strategy" in recovery_result
            assert recovery_result["recovery_strategy"] == scenario["expected_recovery"]

            # Should provide user-friendly error message
            assert "user_message" in recovery_result
            assert len(recovery_result["user_message"]) > 0

            # Should log error for debugging
            assert "error_logged" in recovery_result
            assert recovery_result["error_logged"] is True


class TestDataVisualization:
    """Test Data Visualization functionality."""

    @pytest.fixture
    def data_browser(self, mock_api_client, mock_data_browser):
        """Create data browser instance."""
        return DataBrowser(
            api_client=mock_api_client,
            data_source=mock_data_browser
        )

    def test_chart_data_preparation(self, data_browser):
        """Test chart data preparation and formatting."""
        raw_data = {
            "time_series": [
                {"timestamp": "2024-01-01T10:00:00", "value": 100, "category": "requests"},
                {"timestamp": "2024-01-01T10:05:00", "value": 120, "category": "requests"},
                {"timestamp": "2024-01-01T10:10:00", "value": 95, "category": "requests"}
            ],
            "categories": [
                {"name": "healthy", "count": 8, "percentage": 80.0},
                {"name": "degraded", "count": 2, "percentage": 20.0}
            ]
        }

        chart_configs = [
            {
                "chart_type": "line",
                "data_source": "time_series",
                "x_axis": "timestamp",
                "y_axis": "value",
                "group_by": "category"
            },
            {
                "chart_type": "pie",
                "data_source": "categories",
                "label_field": "name",
                "value_field": "count"
            }
        ]

        for config in chart_configs:
            chart_data = data_browser.prepare_chart_data(raw_data, config)

            assert chart_data["success"] is True
            assert "formatted_data" in chart_data
            assert "chart_metadata" in chart_data

            formatted_data = chart_data["formatted_data"]

            if config["chart_type"] == "line":
                assert "datasets" in formatted_data
                assert len(formatted_data["datasets"]) > 0
                assert "labels" in formatted_data
            elif config["chart_type"] == "pie":
                assert "labels" in formatted_data
                assert "data" in formatted_data
                assert len(formatted_data["labels"]) == len(raw_data["categories"])

    def test_table_data_formatting(self, data_browser):
        """Test table data formatting and presentation."""
        table_data = {
            "columns": [
                {"key": "name", "label": "Service Name", "sortable": True},
                {"key": "status", "label": "Status", "sortable": True},
                {"key": "response_time", "label": "Response Time", "sortable": True, "unit": "ms"},
                {"key": "uptime", "label": "Uptime", "sortable": True, "unit": "%"}
            ],
            "rows": [
                {"name": "interpreter", "status": "healthy", "response_time": 245, "uptime": 99.7},
                {"name": "orchestrator", "status": "degraded", "response_time": 450, "uptime": 98.2},
                {"name": "doc_store", "status": "healthy", "response_time": 180, "uptime": 99.9}
            ],
            "pagination": {
                "current_page": 1,
                "total_pages": 3,
                "page_size": 10,
                "total_rows": 25
            }
        }

        formatting_config = {
            "table_id": "services_table",
            "styling": {
                "striped": True,
                "hover": True,
                "bordered": False
            },
            "responsive": True,
            "export_formats": ["csv", "json", "pdf"]
        }

        formatted_table = data_browser.format_table_data(table_data, formatting_config)

        assert formatted_table["success"] is True
        assert "html_table" in formatted_table
        assert "table_metadata" in formatted_table

        # Should include table structure
        html_table = formatted_table["html_table"]
        assert "<table" in html_table
        assert "<thead" in html_table
        assert "<tbody" in html_table

        # Should include all columns
        for column in table_data["columns"]:
            assert column["label"] in html_table

        # Should include all rows
        for row in table_data["rows"]:
            assert row["name"] in html_table

    def test_dashboard_widget_customization(self, data_browser):
        """Test dashboard widget customization."""
        widget_config = {
            "widget_id": "custom_metrics_chart",
            "base_type": "line_chart",
            "customizations": {
                "colors": {
                    "primary": "#4A90E2",
                    "secondary": "#F5A623",
                    "background": "#2C3E50"
                },
                "layout": {
                    "show_legend": True,
                    "legend_position": "top",
                    "show_grid": False,
                    "show_tooltips": True
                },
                "data_display": {
                    "show_data_labels": False,
                    "animate_transitions": True,
                    "highlight_on_hover": True
                }
            },
            "user_preferences": {
                "theme": "dark",
                "compact_mode": True,
                "auto_refresh": True
            }
        }

        customization_result = data_browser.apply_widget_customization(widget_config)

        assert customization_result["success"] is True
        assert "customized_widget" in customization_result
        assert "applied_customizations" in customization_result

        customized = customization_result["customized_widget"]

        # Should apply color customizations
        assert customized["colors"]["primary"] == "#4A90E2"

        # Should apply layout preferences
        assert customized["layout"]["show_legend"] is True
        assert customized["layout"]["legend_position"] == "top"

        # Should merge user preferences
        assert customized["theme"] == "dark"
        assert customized["compact_mode"] is True

    def test_real_time_data_integration(self, data_browser):
        """Test real-time data integration in visualizations."""
        visualization_config = {
            "visualization_id": "realtime_metrics_dashboard",
            "data_sources": [
                {
                    "source_id": "service_metrics",
                    "update_interval_seconds": 5,
                    "data_mapping": {
                        "x_axis": "timestamp",
                        "y_axis": "response_time",
                        "group_by": "service_name"
                    }
                },
                {
                    "source_id": "system_health",
                    "update_interval_seconds": 10,
                    "data_mapping": {
                        "metric_name": "cpu_usage",
                        "threshold": 80,
                        "alert_when": "above_threshold"
                    }
                }
            ],
            "realtime_features": {
                "live_updates": True,
                "smooth_transitions": True,
                "data_buffering": True,
                "connection_recovery": True
            }
        }

        realtime_setup = data_browser.setup_realtime_data_integration(visualization_config)

        assert realtime_setup["success"] is True
        assert "realtime_configuration" in realtime_setup
        assert "data_streams" in realtime_setup

        realtime_config = realtime_setup["realtime_configuration"]
        assert realtime_config["live_updates"] is True
        assert realtime_config["connection_recovery"] is True

        data_streams = realtime_setup["data_streams"]
        assert len(data_streams) == len(visualization_config["data_sources"])

        # Verify stream configurations
        for stream in data_streams:
            assert "stream_id" in stream
            assert "update_interval_seconds" in stream
            assert "status" in stream
            assert stream["status"] == "initialized"

    def test_visualization_performance_monitoring(self, data_browser):
        """Test visualization performance monitoring."""
        performance_data = {
            "render_times": [120, 145, 98, 167, 134, 112, 156, 143, 128, 139],
            "update_times": [45, 52, 38, 67, 41, 49, 55, 43, 46, 51],
            "memory_usage": [45.2, 46.8, 44.1, 47.5, 45.9, 46.2, 45.7, 46.4, 45.8, 46.1],
            "data_processing_times": [12, 15, 8, 22, 14, 11, 18, 13, 16, 10]
        }

        monitoring_result = data_browser.monitor_visualization_performance(performance_data)

        assert monitoring_result["success"] is True
        assert "performance_metrics" in monitoring_result
        assert "performance_analysis" in monitoring_result
        assert "optimization_recommendations" in monitoring_result

        metrics = monitoring_result["performance_metrics"]

        # Should calculate statistics
        assert "render_time_avg_ms" in metrics
        assert "render_time_p95_ms" in metrics
        assert "memory_usage_avg_mb" in metrics

        # Should analyze performance trends
        analysis = monitoring_result["performance_analysis"]
        assert "performance_trend" in analysis
        assert "bottleneck_identified" in analysis

        # Should provide optimization recommendations
        recommendations = monitoring_result["optimization_recommendations"]
        assert len(recommendations) > 0

        # Common recommendations based on performance data
        rec_types = [rec["type"] for rec in recommendations]
        expected_recs = ["caching", "render_optimization", "memory_management", "data_processing"]
        assert any(rec in " ".join(rec_types).lower() for rec in expected_recs)

    def test_data_export_and_download(self, data_browser):
        """Test data export and download functionality."""
        export_requests = [
            {
                "data_source": "services_table",
                "format": "csv",
                "filters": {"status": "healthy"},
                "include_metadata": True
            },
            {
                "data_source": "performance_metrics",
                "format": "json",
                "date_range": {"start": "2024-01-01", "end": "2024-01-07"},
                "aggregation": "daily"
            },
            {
                "data_source": "logs",
                "format": "pdf",
                "filters": {"level": ["ERROR", "WARN"]},
                "include_charts": True
            }
        ]

        for export_request in export_requests:
            export_result = data_browser.export_visualization_data(export_request)

            assert export_result["success"] is True
            assert "export_id" in export_result
            assert "download_url" in export_result
            assert "file_size_bytes" in export_result
            assert "expires_at" in export_result

            # Verify format-specific handling
            if export_request["format"] == "csv":
                assert "csv_headers" in export_result
                assert len(export_result["csv_headers"]) > 0
            elif export_request["format"] == "json":
                assert "json_schema" in export_result
            elif export_request["format"] == "pdf":
                assert "page_count" in export_result
                if export_request.get("include_charts"):
                    assert "charts_included" in export_result
                    assert export_result["charts_included"] > 0

    def test_accessibility_compliance(self, data_browser):
        """Test accessibility compliance in visualizations."""
        accessibility_config = {
            "compliance_standard": "WCAG_2_1_AA",
            "features": {
                "keyboard_navigation": True,
                "screen_reader_support": True,
                "high_contrast_support": True,
                "text_alternatives": True,
                "focus_indicators": True
            },
            "testing_mode": True
        }

        compliance_result = data_browser.check_accessibility_compliance(accessibility_config)

        assert compliance_result["success"] is True
        assert "compliance_score" in compliance_result
        assert "accessibility_issues" in compliance_result
        assert "remediation_suggestions" in compliance_result

        # Should achieve high compliance score
        assert compliance_result["compliance_score"] >= 0.85

        # Should identify any issues
        issues = compliance_result["accessibility_issues"]
        assert isinstance(issues, list)

        # Should provide remediation suggestions
        suggestions = compliance_result["remediation_suggestions"]
        assert len(suggestions) >= 0

        # Verify specific accessibility features
        if accessibility_config["features"]["screen_reader_support"]:
            assert any("aria" in str(suggestion).lower() for suggestion in suggestions)

    def test_visualization_theme_and_styling(self, data_browser):
        """Test visualization theme and styling customization."""
        theme_config = {
            "theme_name": "enterprise_dark",
            "color_palette": {
                "primary": "#4A90E2",
                "secondary": "#F5A623",
                "success": "#7ED321",
                "warning": "#F5A623",
                "error": "#D0021B",
                "background": "#2C3E50",
                "surface": "#34495E",
                "text": "#ECF0F1"
            },
            "typography": {
                "font_family": "Inter, system-ui, sans-serif",
                "font_size_base": "14px",
                "line_height": 1.5,
                "heading_scale": [2.0, 1.5, 1.25, 1.0]
            },
            "spacing": {
                "unit": "8px",
                "scale": [0.5, 1, 2, 3, 4, 6, 8, 12]
            },
            "border_radius": "4px",
            "shadows": {
                "small": "0 1px 3px rgba(0,0,0,0.12)",
                "medium": "0 4px 6px rgba(0,0,0,0.16)",
                "large": "0 10px 25px rgba(0,0,0,0.19)"
            }
        }

        theme_result = data_browser.apply_visualization_theme(theme_config)

        assert theme_result["success"] is True
        assert "applied_theme" in theme_result
        assert "theme_validation" in theme_result

        applied_theme = theme_result["applied_theme"]

        # Should apply color palette
        assert applied_theme["colors"]["primary"] == "#4A90E2"

        # Should apply typography settings
        assert "Inter" in applied_theme["typography"]["font_family"]

        # Should validate theme consistency
        validation = theme_result["theme_validation"]
        assert validation["color_contrast_passed"] is True
        assert validation["readability_passed"] is True

    def test_dashboard_layout_management(self, data_browser):
        """Test dashboard layout management and responsiveness."""
        layout_config = {
            "dashboard_id": "responsive_dashboard",
            "layout_engine": "css_grid",
            "breakpoints": {
                "mobile": {"max_width": 768, "columns": 1},
                "tablet": {"min_width": 769, "max_width": 1024, "columns": 2},
                "desktop": {"min_width": 1025, "columns": 3}
            },
            "components": [
                {
                    "id": "header_widget",
                    "type": "header",
                    "layout": {
                        "grid_area": "header",
                        "min_height": "80px"
                    }
                },
                {
                    "id": "services_grid",
                    "type": "services_overview",
                    "layout": {
                        "grid_area": "main",
                        "min_height": "400px"
                    }
                },
                {
                    "id": "sidebar_metrics",
                    "type": "metrics_panel",
                    "layout": {
                        "grid_area": "sidebar",
                        "min_width": "300px"
                    }
                }
            ],
            "responsive_rules": {
                "mobile": {
                    "header_widget": {"full_width": True},
                    "sidebar_metrics": {"hidden": True},
                    "services_grid": {"stacked": True}
                }
            }
        }

        layout_result = data_browser.configure_dashboard_layout(layout_config)

        assert layout_result["success"] is True
        assert "layout_configuration" in layout_result
        assert "responsive_breakpoints" in layout_result
        assert "component_positions" in layout_result

        layout_config_result = layout_result["layout_configuration"]
        assert layout_config_result["layout_engine"] == "css_grid"

        breakpoints = layout_result["responsive_breakpoints"]
        assert "mobile" in breakpoints
        assert "tablet" in breakpoints
        assert "desktop" in breakpoints

        component_positions = layout_result["component_positions"]
        assert len(component_positions) == len(layout_config["components"])

        # Verify component positioning
        for component in component_positions:
            assert "grid_area" in component
            assert "responsive_rules" in component

    def test_visualization_data_caching_and_invalidation(self, data_browser):
        """Test visualization data caching and invalidation."""
        cache_config = {
            "cache_strategy": "intelligent",
            "ttl_seconds": {
                "real_time_data": 30,
                "historical_data": 300,
                "static_metadata": 3600
            },
            "invalidation_triggers": [
                "data_source_changed",
                "user_preferences_updated",
                "time_window_expired",
                "manual_refresh"
            ],
            "cache_compression": True,
            "memory_limit_mb": 100
        }

        cache_setup = data_browser.setup_data_caching(cache_config)

        assert cache_setup["success"] is True
        assert "cache_configuration" in cache_setup
        assert "cache_performance" in cache_setup

        cache_perf = cache_setup["cache_performance"]
        assert "hit_rate_target" in cache_perf
        assert "memory_efficiency" in cache_perf

        # Test cache invalidation
        invalidation_result = data_browser.invalidate_visualization_cache("data_source_changed")

        assert invalidation_result["success"] is True
        assert "invalidated_entries" in invalidation_result
        assert "cache_cleared_mb" in invalidation_result

        # Test cache retrieval
        cache_key = "dashboard_services_overview"
        cache_retrieval = data_browser.get_cached_visualization_data(cache_key)

        assert cache_retrieval["cache_hit"] in [True, False]
        if cache_retrieval["cache_hit"]:
            assert "cached_data" in cache_retrieval
            assert "cache_age_seconds" in cache_retrieval
