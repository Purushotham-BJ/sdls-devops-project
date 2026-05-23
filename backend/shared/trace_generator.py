import uuid
import time

def generate_trace_id():
    """Generate a unique trace ID for distributed request tracking."""
    return str(uuid.uuid4()).replace("-", "")[:16].upper()

def generate_span_id():
    """Generate a span ID for individual service operations."""
    return str(uuid.uuid4()).replace("-", "")[:8].upper()

def get_current_timestamp():
    """Return ISO format timestamp."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
