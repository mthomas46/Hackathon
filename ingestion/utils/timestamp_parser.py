"""
Timestamp parsing utility.
"""
from datetime import datetime, timezone
from typing import Optional, Union
import re
from dateutil import parser as dateutil_parser


class TimestampParser:
    """Parse timestamps from various formats."""
    
    # Common date format patterns
    GIT_DATE_PATTERN = re.compile(
        r'([A-Za-z]{3})\s+([A-Za-z]{3})\s+(\d{1,2})\s+(\d{2}):(\d{2}):(\d{2})\s+(\d{4})\s+([+-]\d{4})'
    )
    
    ISO_PATTERN = re.compile(
        r'(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?(?:Z|([+-]\d{2}):(\d{2}))?'
    )
    
    def parse(self, timestamp: Union[str, int, float, datetime]) -> datetime:
        """
        Parse timestamp from various formats.
        
        Args:
            timestamp: Timestamp in various formats (ISO string, unix timestamp, datetime)
        
        Returns:
            datetime object in UTC
        
        Raises:
            ValueError: If timestamp cannot be parsed
        """
        if isinstance(timestamp, datetime):
            return self._ensure_utc(timestamp)
        
        if isinstance(timestamp, (int, float)):
            return self.parse_unix(timestamp)
        
        if isinstance(timestamp, str):
            # Try ISO 8601 first
            try:
                return self.parse_iso(timestamp)
            except ValueError:
                pass
            
            # Try git date format
            try:
                return self.parse_git_date(timestamp)
            except ValueError:
                pass
            
            # Try dateutil parser (handles many formats)
            try:
                dt = dateutil_parser.parse(timestamp)
                return self._ensure_utc(dt)
            except Exception:
                pass
        
        raise ValueError(f"Cannot parse timestamp: {timestamp}")
    
    def parse_iso(self, timestamp_str: str) -> datetime:
        """
        Parse ISO 8601 format timestamp.
        
        Examples:
            2024-01-15T10:30:00Z
            2024-01-15T10:30:00+05:30
            2024-01-15T10:30:00.123456Z
        """
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return self._ensure_utc(dt)
        except ValueError as e:
            raise ValueError(f"Invalid ISO timestamp: {timestamp_str}") from e
    
    def parse_unix(self, timestamp: Union[int, float]) -> datetime:
        """
        Parse Unix timestamp (seconds since epoch).
        
        Args:
            timestamp: Unix timestamp (can be int or float)
        
        Returns:
            datetime in UTC
        """
        try:
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except (ValueError, OSError) as e:
            raise ValueError(f"Invalid unix timestamp: {timestamp}") from e
    
    def parse_git_date(self, date_str: str) -> datetime:
        """
        Parse git log date format.
        
        Example: Mon Jan 15 10:30:00 2024 +0000
        """
        match = self.GIT_DATE_PATTERN.match(date_str)
        if not match:
            raise ValueError(f"Invalid git date format: {date_str}")
        
        # Extract components
        _, month_str, day, hour, minute, second, year, tz_offset = match.groups()
        
        # Month mapping
        months = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
            'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
            'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        month = months[month_str]
        
        # Create datetime
        dt = datetime(
            int(year), month, int(day),
            int(hour), int(minute), int(second),
            tzinfo=timezone.utc
        )
        
        return dt
    
    def parse_wikipedia_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse Wikipedia API timestamp format.
        
        Example: 2024-01-15T10:30:00Z
        """
        return self.parse_iso(timestamp_str)
    
    def parse_github_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse GitHub API timestamp format.
        
        Example: 2024-01-15T10:30:00Z
        """
        return self.parse_iso(timestamp_str)
    
    def parse_jira_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse Jira API timestamp format.
        
        Example: 2024-01-15T10:30:00.000+0000
        """
        return self.parse_iso(timestamp_str)
    
    def to_iso(self, dt: datetime) -> str:
        """Convert datetime to ISO 8601 string."""
        return dt.isoformat()
    
    def to_unix(self, dt: datetime) -> float:
        """Convert datetime to Unix timestamp."""
        return dt.timestamp()
    
    def _ensure_utc(self, dt: datetime) -> datetime:
        """Ensure datetime is in UTC timezone."""
        if dt.tzinfo is None:
            # Assume UTC if no timezone
            return dt.replace(tzinfo=timezone.utc)
        elif dt.tzinfo != timezone.utc:
            # Convert to UTC
            return dt.astimezone(timezone.utc)
        return dt
    
    def extract_created_updated(
        self,
        data: dict,
        created_keys: Optional[list] = None,
        updated_keys: Optional[list] = None
    ) -> tuple[Optional[datetime], Optional[datetime]]:
        """
        Extract created_at and updated_at from dictionary.
        
        Args:
            data: Dictionary containing timestamp data
            created_keys: List of possible keys for created timestamp
            updated_keys: List of possible keys for updated timestamp
        
        Returns:
            Tuple of (created_at, updated_at) as datetime objects
        """
        if created_keys is None:
            created_keys = [
                'created_at', 'createdAt', 'created', 'creation_date',
                'date_created', 'timestamp', 'date', 'published_at'
            ]
        
        if updated_keys is None:
            updated_keys = [
                'updated_at', 'updatedAt', 'updated', 'modified',
                'last_modified', 'modified_at', 'date_modified',
                'last_updated', 'revision_date'
            ]
        
        created_at = None
        updated_at = None
        
        # Try to find created timestamp
        for key in created_keys:
            if key in data and data[key]:
                try:
                    created_at = self.parse(data[key])
                    break
                except ValueError:
                    continue
        
        # Try to find updated timestamp
        for key in updated_keys:
            if key in data and data[key]:
                try:
                    updated_at = self.parse(data[key])
                    break
                except ValueError:
                    continue
        
        return created_at, updated_at
    
    def is_valid_timestamp(self, timestamp: Union[str, int, float]) -> bool:
        """Check if timestamp is valid and parseable."""
        try:
            self.parse(timestamp)
            return True
        except (ValueError, TypeError):
            return False

