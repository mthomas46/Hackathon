"""
Unit tests for timestamp parser.
"""
import pytest
from datetime import datetime, timezone
from ingestion.utils.timestamp_parser import TimestampParser


class TestTimestampParser:
    """Unit tests for timestamp parsing."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.parser = TimestampParser()
    
    # ISO 8601 format
    def test_parse_iso_format(self):
        """Test parsing ISO 8601 format."""
        timestamp_str = "2024-01-15T10:30:00Z"
        
        result = self.parser.parse(timestamp_str)
        
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 0
        assert result.tzinfo == timezone.utc
    
    def test_parse_iso_with_timezone(self):
        """Test parsing ISO with timezone offset."""
        timestamp_str = "2024-01-15T10:30:00+05:30"
        
        result = self.parser.parse(timestamp_str)
        
        assert isinstance(result, datetime)
        assert result.tzinfo == timezone.utc  # Should be converted to UTC
    
    def test_parse_iso_with_microseconds(self):
        """Test parsing ISO with microseconds."""
        timestamp_str = "2024-01-15T10:30:00.123456Z"
        
        result = self.parser.parse(timestamp_str)
        
        assert result.microsecond == 123456
    
    # Unix timestamp
    def test_parse_unix_timestamp(self):
        """Test parsing Unix timestamp."""
        timestamp = 1705315800  # 2024-01-15 10:30:00 UTC
        
        result = self.parser.parse_unix(timestamp)
        
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
    
    def test_parse_unix_timestamp_float(self):
        """Test parsing Unix timestamp with decimals."""
        timestamp = 1705315800.5
        
        result = self.parser.parse_unix(timestamp)
        
        assert isinstance(result, datetime)
        assert result.microsecond > 0
    
    # Git date format
    def test_extract_from_git_log(self):
        """Test extracting timestamp from git log."""
        git_date = "Mon Jan 15 10:30:00 2024 +0000"
        
        result = self.parser.parse_git_date(git_date)
        
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
    
    # Wikipedia timestamp
    def test_parse_wikipedia_timestamp(self):
        """Test parsing Wikipedia API timestamp."""
        timestamp_str = "2024-01-15T10:30:00Z"
        
        result = self.parser.parse_wikipedia_timestamp(timestamp_str)
        
        assert result.year == 2024
        assert result.month == 1
    
    # GitHub timestamp
    def test_parse_github_timestamp(self):
        """Test parsing GitHub API timestamp."""
        timestamp_str = "2024-01-15T10:30:00Z"
        
        result = self.parser.parse_github_timestamp(timestamp_str)
        
        assert result.year == 2024
        assert result.month == 1
    
    # Jira timestamp
    def test_parse_jira_timestamp(self):
        """Test parsing Jira API timestamp."""
        timestamp_str = "2024-01-15T10:30:00.000+0000"
        
        result = self.parser.parse_jira_timestamp(timestamp_str)
        
        assert result.year == 2024
        assert result.month == 1
    
    # Error handling
    def test_handle_invalid_timestamp(self):
        """Test handling of invalid timestamp."""
        with pytest.raises(ValueError):
            self.parser.parse("not a timestamp")
    
    def test_handle_invalid_unix_timestamp(self):
        """Test handling of invalid Unix timestamp."""
        with pytest.raises(ValueError):
            # Very large timestamp (year 10000+) should fail
            self.parser.parse_unix(999999999999999)
    
    # Datetime input
    def test_parse_datetime_object(self):
        """Test parsing datetime object."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        
        result = self.parser.parse(dt)
        
        assert result == dt
        assert result.tzinfo == timezone.utc
    
    # Integer/float input
    def test_parse_integer_timestamp(self):
        """Test parsing integer as Unix timestamp."""
        timestamp = 1705315800
        
        result = self.parser.parse(timestamp)
        
        assert isinstance(result, datetime)
        assert result.year == 2024
    
    # Conversion methods
    def test_to_iso(self):
        """Test converting datetime to ISO string."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        
        iso_str = self.parser.to_iso(dt)
        
        assert "2024-01-15" in iso_str
        assert "10:30:00" in iso_str
    
    def test_to_unix(self):
        """Test converting datetime to Unix timestamp."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        
        unix_ts = self.parser.to_unix(dt)
        
        assert isinstance(unix_ts, float)
        assert unix_ts > 0
    
    # Extract created/updated
    def test_extract_created_updated_standard_keys(self):
        """Test extracting created/updated from standard keys."""
        data = {
            'created_at': '2024-01-15T10:30:00Z',
            'updated_at': '2024-01-16T12:00:00Z'
        }
        
        created, updated = self.parser.extract_created_updated(data)
        
        assert created is not None
        assert updated is not None
        assert created.day == 15
        assert updated.day == 16
    
    def test_extract_created_updated_alternative_keys(self):
        """Test extracting with alternative key names."""
        data = {
            'createdAt': '2024-01-15T10:30:00Z',
            'last_modified': '2024-01-16T12:00:00Z'
        }
        
        created, updated = self.parser.extract_created_updated(data)
        
        assert created is not None
        assert updated is not None
    
    def test_extract_created_updated_missing_keys(self):
        """Test extracting when keys are missing."""
        data = {}
        
        created, updated = self.parser.extract_created_updated(data)
        
        assert created is None
        assert updated is None
    
    def test_extract_created_updated_custom_keys(self):
        """Test extracting with custom key lists."""
        data = {
            'publish_date': '2024-01-15T10:30:00Z',
            'revision_date': '2024-01-16T12:00:00Z'
        }
        
        created, updated = self.parser.extract_created_updated(
            data,
            created_keys=['publish_date'],
            updated_keys=['revision_date']
        )
        
        assert created is not None
        assert updated is not None
    
    # Validation
    def test_is_valid_timestamp_valid(self):
        """Test validation of valid timestamp."""
        assert self.parser.is_valid_timestamp("2024-01-15T10:30:00Z") is True
        assert self.parser.is_valid_timestamp(1705315800) is True
    
    def test_is_valid_timestamp_invalid(self):
        """Test validation of invalid timestamp."""
        assert self.parser.is_valid_timestamp("not a timestamp") is False
        assert self.parser.is_valid_timestamp("") is False
    
    # Timezone handling
    def test_ensure_utc_no_timezone(self):
        """Test UTC conversion for naive datetime."""
        dt = datetime(2024, 1, 15, 10, 30, 0)  # No timezone
        
        result = self.parser.parse(dt)
        
        assert result.tzinfo == timezone.utc
    
    def test_ensure_utc_different_timezone(self):
        """Test UTC conversion from different timezone."""
        # This test verifies the _ensure_utc method handles timezone conversion
        dt_naive = datetime(2024, 1, 15, 10, 30, 0)
        result = self.parser._ensure_utc(dt_naive)
        
        assert result.tzinfo == timezone.utc
    
    # Parameterized tests
    @pytest.mark.parametrize('timestamp_str,expected_year', [
        ('2024-01-15T10:30:00Z', 2024),
        ('2023-06-20T15:45:30Z', 2023),
        ('2025-12-31T23:59:59Z', 2025),
    ])
    def test_parse_multiple_iso_timestamps(self, timestamp_str, expected_year):
        """Test parsing multiple ISO timestamps."""
        result = self.parser.parse(timestamp_str)
        assert result.year == expected_year
    
    @pytest.mark.parametrize('unix_ts,expected_year', [
        (1705315800, 2024),  # Jan 2024
        (1687273530, 2023),  # Jun 2023
        (1736000000, 2025),  # Jan 2025
    ])
    def test_parse_multiple_unix_timestamps(self, unix_ts, expected_year):
        """Test parsing multiple Unix timestamps."""
        result = self.parser.parse_unix(unix_ts)
        assert result.year == expected_year

