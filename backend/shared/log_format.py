from datetime import datetime, timezone

def create_log(trace_id, service_name, status, message, response_time=0, extra=None):
    """
    Create a structured log entry in standard format.
    
    Args:
        trace_id: Unique identifier propagated across all services
        service_name: Name of the service generating the log
        status: SUCCESS, ERROR, WARNING, or INFO
        message: Human-readable log message
        response_time: Time taken in milliseconds
        extra: Optional dict of additional fields
    
    Returns:
        dict: Structured log entry
    """
    log = {
        "trace_id": trace_id,
        "service_name": service_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status.upper(),
        "message": message,
        "response_time": response_time
    }
    if extra:
        log.update(extra)
    return log
