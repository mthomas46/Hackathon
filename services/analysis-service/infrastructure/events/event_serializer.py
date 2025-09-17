"""Event Serializer - Handles event serialization and deserialization."""

import json
import pickle
import base64
from typing import Any, Dict, Union
from abc import ABC, abstractmethod

from .event_bus import DomainEvent, EventEnvelope


class EventSerializer(ABC):
    """Abstract base class for event serialization."""

    @abstractmethod
    def serialize(self, envelope: EventEnvelope) -> str:
        """Serialize event envelope to string."""
        pass

    @abstractmethod
    def deserialize(self, data: str) -> EventEnvelope:
        """Deserialize string to event envelope."""
        pass

    @abstractmethod
    def get_content_type(self) -> str:
        """Get content type identifier."""
        pass


class JSONEventSerializer(EventSerializer):
    """JSON-based event serializer."""

    def __init__(self, indent: Optional[int] = None, ensure_ascii: bool = False):
        """Initialize JSON serializer."""
        self.indent = indent
        self.ensure_ascii = ensure_ascii

    def serialize(self, envelope: EventEnvelope) -> str:
        """Serialize event envelope to JSON string."""
        data = {
            'event': envelope.event.to_dict(),
            'topic': envelope.topic,
            'partition_key': envelope.partition_key,
            'headers': envelope.headers,
            'retry_count': envelope.retry_count,
            'max_retries': envelope.max_retries
        }

        return json.dumps(data, indent=self.indent, ensure_ascii=self.ensure_ascii, default=self._json_serializer)

    def deserialize(self, data: str) -> EventEnvelope:
        """Deserialize JSON string to event envelope."""
        try:
            parsed = json.loads(data)

            # Reconstruct event
            event_data = parsed['event']
            event = DomainEvent.from_dict(event_data)

            return EventEnvelope(
                event=event,
                topic=parsed['topic'],
                partition_key=parsed.get('partition_key'),
                headers=parsed.get('headers', {}),
                retry_count=parsed.get('retry_count', 0),
                max_retries=parsed.get('max_retries', 3)
            )

        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid JSON event data: {e}") from e

    def get_content_type(self) -> str:
        """Get content type."""
        return "application/json"

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for non-standard types."""
        if hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # Custom objects
            return obj.__dict__
        elif isinstance(obj, bytes):
            return base64.b64encode(obj).decode('ascii')
        else:
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class PickleEventSerializer(EventSerializer):
    """Pickle-based event serializer for Python objects."""

    def __init__(self, protocol: int = pickle.HIGHEST_PROTOCOL):
        """Initialize pickle serializer."""
        self.protocol = protocol

    def serialize(self, envelope: EventEnvelope) -> str:
        """Serialize event envelope to base64-encoded pickle string."""
        data = pickle.dumps(envelope, protocol=self.protocol)
        return base64.b64encode(data).decode('ascii')

    def deserialize(self, data: str) -> EventEnvelope:
        """Deserialize base64-encoded pickle string to event envelope."""
        try:
            decoded = base64.b64decode(data)
            envelope = pickle.loads(decoded)

            if not isinstance(envelope, EventEnvelope):
                raise ValueError("Deserialized object is not an EventEnvelope")

            return envelope

        except (pickle.UnpicklingError, base64.binascii.Error, ValueError) as e:
            raise ValueError(f"Invalid pickle event data: {e}") from e

    def get_content_type(self) -> str:
        """Get content type."""
        return "application/pickle"


class CompressedJSONEventSerializer(JSONEventSerializer):
    """Compressed JSON event serializer."""

    def __init__(self, compression_level: int = 6, **kwargs):
        """Initialize compressed JSON serializer."""
        super().__init__(**kwargs)
        self.compression_level = compression_level

    def serialize(self, envelope: EventEnvelope) -> str:
        """Serialize with compression."""
        import gzip
        import io

        json_data = super().serialize(envelope)
        compressed = io.BytesIO()

        with gzip.GzipFile(fileobj=compressed, mode='wb', compresslevel=self.compression_level) as f:
            f.write(json_data.encode('utf-8'))

        return base64.b64encode(compressed.getvalue()).decode('ascii')

    def deserialize(self, data: str) -> EventEnvelope:
        """Deserialize with decompression."""
        import gzip
        import io

        try:
            compressed_data = base64.b64decode(data)
            decompressed = io.BytesIO(compressed_data)

            with gzip.GzipFile(fileobj=decompressed, mode='rb') as f:
                json_data = f.read().decode('utf-8')

            return super().deserialize(json_data)

        except Exception as e:
            raise ValueError(f"Invalid compressed JSON event data: {e}") from e

    def get_content_type(self) -> str:
        """Get content type."""
        return "application/json+gzip"


class MessagePackEventSerializer(EventSerializer):
    """MessagePack-based event serializer for better performance."""

    def __init__(self):
        """Initialize MessagePack serializer."""
        try:
            import msgpack
            self.msgpack = msgpack
        except ImportError:
            raise ImportError("msgpack package is required for MessagePackEventSerializer")

    def serialize(self, envelope: EventEnvelope) -> str:
        """Serialize event envelope to MessagePack."""
        data = {
            'event': envelope.event.to_dict(),
            'topic': envelope.topic,
            'partition_key': envelope.partition_key,
            'headers': envelope.headers,
            'retry_count': envelope.retry_count,
            'max_retries': envelope.max_retries
        }

        packed = self.msgpack.packb(data, default=self._msgpack_serializer)
        return base64.b64encode(packed).decode('ascii')

    def deserialize(self, data: str) -> EventEnvelope:
        """Deserialize MessagePack to event envelope."""
        try:
            packed = base64.b64decode(data)
            parsed = self.msgpack.unpackb(packed, raw=False)

            # Reconstruct event
            event_data = parsed['event']
            event = DomainEvent.from_dict(event_data)

            return EventEnvelope(
                event=event,
                topic=parsed['topic'],
                partition_key=parsed.get('partition_key'),
                headers=parsed.get('headers', {}),
                retry_count=parsed.get('retry_count', 0),
                max_retries=parsed.get('max_retries', 3)
            )

        except Exception as e:
            raise ValueError(f"Invalid MessagePack event data: {e}") from e

    def get_content_type(self) -> str:
        """Get content type."""
        return "application/msgpack"

    def _msgpack_serializer(self, obj: Any) -> Any:
        """Custom MessagePack serializer."""
        if hasattr(obj, 'isoformat'):  # datetime objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # Custom objects
            return obj.__dict__
        else:
            return str(obj)


class EventSerializerFactory:
    """Factory for creating event serializers."""

    @staticmethod
    def create_serializer(serializer_type: str = "json", **kwargs) -> EventSerializer:
        """Create event serializer instance."""
        serializers = {
            'json': JSONEventSerializer,
            'pickle': PickleEventSerializer,
            'compressed_json': CompressedJSONEventSerializer,
            'msgpack': MessagePackEventSerializer
        }

        if serializer_type not in serializers:
            raise ValueError(f"Unknown serializer type: {serializer_type}")

        return serializers[serializer_type](**kwargs)

    @staticmethod
    def get_available_serializers() -> Dict[str, str]:
        """Get available serializer types and descriptions."""
        return {
            'json': 'JSON-based serialization (human-readable)',
            'pickle': 'Python pickle serialization (Python-only)',
            'compressed_json': 'Compressed JSON (space-efficient)',
            'msgpack': 'MessagePack serialization (high-performance)'
        }


class SchemaVersionedEventSerializer(JSONEventSerializer):
    """Schema-versioned event serializer for backward compatibility."""

    def __init__(self, current_version: str = "1.0", **kwargs):
        """Initialize versioned serializer."""
        super().__init__(**kwargs)
        self.current_version = current_version
        self._migration_handlers: Dict[str, callable] = {}

    def serialize(self, envelope: EventEnvelope) -> str:
        """Serialize with schema version."""
        data = {
            'schema_version': self.current_version,
            'event': envelope.event.to_dict(),
            'topic': envelope.topic,
            'partition_key': envelope.partition_key,
            'headers': envelope.headers,
            'retry_count': envelope.retry_count,
            'max_retries': envelope.max_retries
        }

        return json.dumps(data, indent=self.indent, ensure_ascii=self.ensure_ascii, default=self._json_serializer)

    def deserialize(self, data: str) -> EventEnvelope:
        """Deserialize with schema migration."""
        try:
            parsed = json.loads(data)

            # Handle schema versioning
            schema_version = parsed.get('schema_version', '1.0')
            if schema_version != self.current_version:
                parsed = self._migrate_schema(parsed, schema_version)

            # Reconstruct event
            event_data = parsed['event']
            event = DomainEvent.from_dict(event_data)

            return EventEnvelope(
                event=event,
                topic=parsed['topic'],
                partition_key=parsed.get('partition_key'),
                headers=parsed.get('headers', {}),
                retry_count=parsed.get('retry_count', 0),
                max_retries=parsed.get('max_retries', 3)
            )

        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid versioned JSON event data: {e}") from e

    def add_migration_handler(self, from_version: str, handler: callable) -> None:
        """Add schema migration handler."""
        self._migration_handlers[from_version] = handler

    def _migrate_schema(self, data: Dict[str, Any], from_version: str) -> Dict[str, Any]:
        """Migrate schema from old version to current."""
        if from_version in self._migration_handlers:
            return self._migration_handlers[from_version](data)
        else:
            # Default migration - assume backward compatibility
            return data

    def get_content_type(self) -> str:
        """Get content type."""
        return f"application/json; schema={self.current_version}"
