# Test package initializer (empty)
"""Tests package index: expose helpers for convenience imports."""

# Import helpers from shared location
try:
    from services.shared.tests.helpers.assertions import assert_basic_ok_json, assert_has_keys, assert_list_of_dicts  # noqa: F401
except ImportError:
    # Fallback: define basic assertion functions if helpers not available
    def assert_basic_ok_json(data):
        assert isinstance(data, dict)
        assert "status" in data

    def assert_has_keys(data, keys):
        assert isinstance(data, dict)
        for key in keys:
            assert key in data

    def assert_list_of_dicts(data):
        assert isinstance(data, list)
        for item in data:
            assert isinstance(item, dict)
