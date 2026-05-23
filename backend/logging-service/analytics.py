"""
Analytics Engine - computes metrics from stored logs.
"""
from mongo_handler import (
    get_total_count, get_error_count, get_stats_by_service,
    get_recent_errors, get_hourly_counts, get_db, get_distinct_traces
)
from constants import LOGS_COLLECTION


def get_overview():
    """High-level summary for the dashboard home page."""
    total  = get_total_count()
    errors = get_error_count()
    services = get_stats_by_service()

    return {
        "total_requests":  total,
        "total_errors":    errors,
        "success_count":   total - errors,
        "error_rate":      round((errors / total * 100) if total else 0, 2),
        "active_services": len(services),
    }


def get_service_breakdown():
    """Per-service stats with failure percentage."""
    rows = get_stats_by_service()
    result = []
    for r in rows:
        total = r["total"]
        errors = r["errors"]
        result.append({
            "service":       r["_id"],
            "total":         total,
            "errors":        errors,
            "success":       total - errors,
            "error_rate":    round((errors / total * 100) if total else 0, 2),
            "avg_resp_time": round(r["avg_resp"] or 0, 1),
        })
    return result


def get_timeline(hours=24):
    return get_hourly_counts(hours)


def get_most_failing_service():
    rows = get_stats_by_service()
    if not rows:
        return None
    return max(rows, key=lambda r: r["errors"] / max(r["total"], 1))


def get_trace_summary(trace_id: str):
    """
    Reconstruct full request flow for a single trace.
    """
    from mongo_handler import get_logs_by_trace
    logs = get_logs_by_trace(trace_id)
    has_error = any(l["status"] == "ERROR" for l in logs)
    return {
        "trace_id":   trace_id,
        "total_logs": len(logs),
        "status":     "ERROR" if has_error else "SUCCESS",
        "logs":       logs,
        "services":   list({l["service_name"] for l in logs}),
    }
